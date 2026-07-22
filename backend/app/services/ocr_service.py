import logging
import os
import tempfile
import uuid
import json
from datetime import datetime, timezone
from typing import List, Tuple

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.core.config import Config
from app.core.exceptions import (
    KramaException,
    DocumentNotReadyForConversion,
    DocumentNotReadyForOCR,
    PageArtifactMissing,
)
from app.storage.base import StorageError

from app.core.logging import request_id_var
from app.db.models.document import Document
from app.db.models.page import Page
from app.db.models.ocr import OCRPageResult, OCRRegion
from app.domain.enums import DocumentStatus, PageStatus
from app.ocr.base import OCRInput, OCRRegionResult
from app.ocr.registry import get_ocr_engine
from app.ocr.normalizer import normalize_regions
from app.ocr.layout import assign_reading_order, build_full_text
from app.ocr.schemas import OCRArtifact, OCRRegionArtifact
from app.repositories.document import DocumentRepository
from app.repositories.page import PageRepository
from app.storage.base import StorageProvider

logger = logging.getLogger(__name__)


class OCRServiceError(KramaException):
    def __init__(self, message: str, code: str = "OCR_FAILED"):
        super().__init__(message, code=code, status_code=500)


class OCRService:
    """Orchestrates document-level and page-level OCR operations."""

    def __init__(self, db: Session, storage: StorageProvider) -> None:
        self._db = db
        self._storage = storage
        self._doc_repo = DocumentRepository(db)
        self._page_repo = PageRepository(db)

    def process_document(self, organization_id: uuid.UUID, document_id: uuid.UUID) -> dict:
        """Run OCR on all unprocessed pages of a document.
        
        Supports partial retries by only processing pages without an OCR result.
        Commits per-page to ensure progress is saved incrementally.
        
        Args:
            organization_id: Organization context.
            document_id: The document to process.
            
        Returns:
            Dict summarizing the operation (page_count, completed, failed, total_regions).
        """
        request_id = request_id_var.get()
        logger.info(
            "ocr_document_started org=%s doc_id=%s request_id=%s",
            organization_id, document_id, request_id,
        )

        document = self._doc_repo.get_by_id_and_org(document_id, organization_id)
        if not document:
            from app.core.exceptions import NotFoundException
            raise NotFoundException("Document not found.")

        if document.status not in (DocumentStatus.CONVERTED, DocumentStatus.OCR_PARTIAL):
            raise DocumentNotReadyForOCR(
                f"Document status must be CONVERTED or OCR_PARTIAL to run OCR. Current: {document.status}"
            )

        pages = self._page_repo.list_by_document_and_org(document.id, organization_id)
        if not pages:
            raise OCRServiceError("Document has no pages to process.")

        completed = 0
        failed = 0
        total_regions = 0

        engine = get_ocr_engine()

        for page in pages:
            # Check if this page already has a result
            stmt = select(OCRPageResult).where(OCRPageResult.page_id == page.id)
            existing = self._db.execute(stmt).scalar_one_or_none()
            if existing:
                completed += 1
                total_regions += existing.region_count
                continue

            try:
                result = self._process_page(document, page, engine)
                completed += 1
                total_regions += result.region_count
            except Exception as e:
                logger.error(
                    "ocr_page_failed doc_id=%s page_num=%s error=%s",
                    document.id, page.page_number, type(e).__name__
                )
                failed += 1
                page.status = PageStatus.OCR_FAILED
                self._db.commit()

        if completed == len(pages) and failed == 0:
            document.status = DocumentStatus.OCR_COMPLETED
            self._db.commit()
        elif failed > 0:
            document.status = DocumentStatus.OCR_PARTIAL
            self._db.commit()

        logger.info(
            "ocr_document_finished doc_id=%s completed=%d failed=%d total_regions=%d",
            document.id, completed, failed, total_regions
        )

        return {
            "document_id": document.id,
            "status": document.status.value,
            "page_count": len(pages),
            "ocr_pages_completed": completed,
            "ocr_pages_failed": failed,
            "total_regions": total_regions,
        }

    def process_page(self, organization_id: uuid.UUID, page_id: uuid.UUID) -> OCRPageResult:
        """Run OCR on a single page directly.
        
        If an OCR result already exists, it is deleted (and its artifact is deleted)
        before re-processing.
        """
        stmt = select(Page).join(Document).where(
            and_(
                Page.id == page_id,
                Document.organization_id == organization_id
            )
        )
        page = self._db.execute(stmt).scalar_one_or_none()
        if not page:
            from app.core.exceptions import NotFoundException
            raise NotFoundException("Page not found.")

        document = self._doc_repo.get_by_id_and_org(page.document_id, organization_id)
        if not document:
            from app.core.exceptions import NotFoundException
            raise NotFoundException("Document not found.")

        # Clean up existing result if any
        stmt_existing = select(OCRPageResult).where(OCRPageResult.page_id == page.id)
        existing = self._db.execute(stmt_existing).scalar_one_or_none()
        if existing:
            if existing.artifact_storage_key:
                try:
                    self._storage.delete(existing.artifact_storage_key)
                except Exception as e:
                    logger.warning("Failed to delete old OCR artifact: %s", e)
            self._db.delete(existing)
            self._db.flush()

        engine = get_ocr_engine()
        
        try:
            return self._process_page(document, page, engine)
        except Exception as e:
            raise OCRServiceError(f"Page OCR processing failed: {e}")

    def _process_page(self, document: Document, page: Page, engine) -> OCRPageResult:
        """Internal page OCR pipeline with transaction isolation."""
        if not page.storage_key or not self._storage.exists(page.storage_key):
            raise PageArtifactMissing(f"Canonical PNG missing for page {page.page_number}")

        # 1. Stream canonical PNG to temp file
        try:
            source_stream = self._storage.open(page.storage_key)
        except StorageError as e:
            raise PageArtifactMissing(f"Failed to read page {page.page_number} artifact: {e}")

        fd, temp_local_path = tempfile.mkstemp(prefix="krama_ocr_src_", suffix=".png")
        try:
            with os.fdopen(fd, "wb") as temp_file:
                while True:
                    chunk = source_stream.read(Config.UPLOAD_CHUNK_SIZE_BYTES)
                    if not chunk:
                        break
                    temp_file.write(chunk)
        except Exception as e:
            os.unlink(temp_local_path)
            raise OCRServiceError(f"Failed to buffer page {page.page_number} for OCR: {e}")
        finally:
            source_stream.close()

        # 2. Run engine
        try:
            ocr_input = OCRInput(
                content=b"",  # Avoid loading bytes into memory, we use temp_path
                width=page.width or 0,
                height=page.height or 0,
                content_type="image/png",
                temp_path=temp_local_path,
            )
            raw_result = engine.recognize(ocr_input)
        finally:
            if os.path.exists(temp_local_path):
                try:
                    os.unlink(temp_local_path)
                except OSError:
                    pass

        # 3. Normalize & Layout Analysis
        normalized_regions = normalize_regions(raw_result.regions)
        ordered_regions = assign_reading_order(normalized_regions)
        full_text = build_full_text(ordered_regions)

        region_count = len(ordered_regions)
        avg_conf = sum(r.confidence for _, r in ordered_regions) / region_count if region_count > 0 else 0.0

        # 4. Generate Canonical JSON Artifact
        artifact_key = f"artifacts/{document.organization_id}/{document.claim_id}/{document.id}/ocr/{page.page_number:04d}.json"
        
        region_artifacts = []
        for r_index, (reading_order, region) in enumerate(ordered_regions):
            region_artifacts.append(OCRRegionArtifact(
                region_index=r_index,
                reading_order=reading_order,
                text=region.text,
                confidence=region.confidence,
                bounding_box={
                    "x1": region.bbox[0],
                    "y1": region.bbox[1],
                    "x2": region.bbox[2],
                    "y2": region.bbox[3],
                },
                polygon=region.polygon,
                region_type=region.region_type,
            ))

        artifact = OCRArtifact(
            page_id=str(page.id),
            page_number=page.page_number,
            engine=raw_result.engine,
            engine_version=raw_result.engine_version,
            language=raw_result.language,
            page_width=page.width or 0,
            page_height=page.height or 0,
            full_text=full_text,
            average_confidence=avg_conf,
            region_count=region_count,
            regions=region_artifacts,
        )

        artifact_json = artifact.model_dump_json(indent=2).encode("utf-8")

        # Write to storage
        import io
        try:
            self._storage.save_stream(artifact_key, io.BytesIO(artifact_json), content_type="application/json")
        except StorageError as e:
            raise OCRServiceError(f"Failed to persist OCR artifact for page {page.page_number}: {e}")

        # 5. Persist to Database (Transaction)
        try:
            return self._persist_page_result(
                page=page,
                raw_result=raw_result,
                ordered_regions=ordered_regions,
                full_text=full_text,
                region_count=region_count,
                avg_conf=avg_conf,
                artifact_key=artifact_key,
            )
        except Exception as db_exc:
            self._db.rollback()
            page.status = PageStatus.OCR_FAILED
            self._db.commit()
            
            # Attempt to compensate stored artifact
            try:
                self._storage.delete(artifact_key)
            except Exception:
                pass
            raise OCRServiceError(f"Failed to persist OCR database records: {db_exc}")

    def _persist_page_result(self, page, raw_result, ordered_regions, full_text, region_count, avg_conf, artifact_key) -> OCRPageResult:
        """Internal method for persisting OCR results to the database. Extracted for testability."""
        db_result = OCRPageResult(
            page_id=page.id,
            engine=raw_result.engine,
            engine_version=raw_result.engine_version,
            language=raw_result.language,
            full_text=full_text,
            region_count=region_count,
            average_confidence=avg_conf,
            processing_time_ms=raw_result.processing_time_ms,
            artifact_storage_key=artifact_key,
        )
        self._db.add(db_result)
        self._db.flush()

        for r_index, (reading_order, region) in enumerate(ordered_regions):
            db_region = OCRRegion(
                ocr_result_id=db_result.id,
                region_index=r_index,
                reading_order=reading_order,
                text=region.text,
                confidence=region.confidence,
                x1=region.bbox[0],
                y1=region.bbox[1],
                x2=region.bbox[2],
                y2=region.bbox[3],
                polygon_json=json.dumps(region.polygon) if region.polygon else None,
                region_type=region.region_type,
            )
            self._db.add(db_region)
        
        page.status = PageStatus.OCR_COMPLETED
        
        # Commit this page's transaction
        self._db.commit()
        
        # Refresh to get IDs
        self._db.refresh(db_result)
        return db_result
