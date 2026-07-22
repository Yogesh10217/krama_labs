import logging
import os
import tempfile
import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.conversion.registry import registry
from app.core.config import Config
from app.core.exceptions import (
    ConversionFailed,
    ConversionStateInconsistent,
    DocumentAlreadyConverting,
    DocumentContentNotFoundException,
    DocumentNotReadyForConversion,
    PageArtifactMissing,
    UnsupportedConversionFormat,
)
from app.core.logging import request_id_var
from app.db.models.document import Document
from app.db.models.job import Job
from app.db.models.job_stage import JobStage
from app.db.models.page import Page
from app.domain.enums import DocumentStatus, JobStageStatus, JobStatus, JobType, PageStatus
from app.repositories.document import DocumentRepository
from app.repositories.page import PageRepository
from app.storage.base import StorageProvider

logger = logging.getLogger(__name__)


class ConversionService:
    """Orchestrates document conversion and page materialization."""

    def __init__(self, db: Session, storage: StorageProvider) -> None:
        self._db = db
        self._storage = storage
        self._doc_repo = DocumentRepository(db)
        self._page_repo = PageRepository(db)

    def convert_document(self, organization_id: uuid.UUID, document_id: uuid.UUID) -> List[Page]:
        """Tenant-isolated, idempotent document page conversion orchestrator.

        Args:
            organization_id: Organization context.
            document_id: The document to convert.

        Returns:
            List[Page]: Materialized Page records.
        """
        request_id = request_id_var.get()
        logger.info(
            "conversion_started org=%s doc_id=%s request_id=%s",
            organization_id, document_id, request_id,
        )

        # 1. Fetch document tenant-safely
        document = self._doc_repo.get_by_id_and_org(document_id, organization_id)
        if not document:
            # Raise not found to prevent leaking document existence of other tenants
            from app.core.exceptions import NotFoundException
            raise NotFoundException("Document not found.")

        # 2. Check Idempotency
        if document.status == DocumentStatus.CONVERTED:
            pages = self._page_repo.list_by_document_and_org(document.id, organization_id)
            if document.page_count is not None and len(pages) == document.page_count:
                all_exist = True
                for page in pages:
                    if not page.storage_key or not self._storage.exists(page.storage_key):
                        all_exist = False
                        break

                if all_exist:
                    logger.info("conversion_idempotent_match doc_id=%s status=CONVERTED", document.id)
                    return pages

                logger.error(
                    "conversion_state_inconsistent doc_id=%s status=CONVERTED page_count=%d pages_found=%d missing_artifacts=true",
                    document.id, document.page_count, len(pages)
                )
                raise PageArtifactMissing(
                    "Document status is CONVERTED but page artifacts are missing from storage."
                )
            else:
                logger.error(
                    "conversion_state_inconsistent doc_id=%s status=CONVERTED page_count=%s pages_found=%d",
                    document.id, document.page_count, len(pages)
                )
                raise ConversionStateInconsistent(
                    f"Document status is CONVERTED but page count in metadata ({document.page_count}) "
                    f"does not match pages table count ({len(pages)})."
                )

        # 3. State verification
        if document.status == DocumentStatus.CONVERTING:
            raise DocumentAlreadyConverting(f"Document {document.id} is already undergoing conversion.")

        if document.status not in (DocumentStatus.UPLOADED, DocumentStatus.CONVERSION_FAILED):
            raise DocumentNotReadyForConversion(
                f"Document status '{document.status}' is not ready for conversion. Must be UPLOADED or CONVERSION_FAILED."
            )

        # 4. Clean up any partial state from previous failure to ensure clean slate
        self._clean_previous_conversion_attempt(document, organization_id)

        # 5. Locate/Create Job & stage
        job, stage = self._get_or_create_job_and_stage(document)

        # 6. Stream content to secure temp file
        if not document.storage_key:
            raise DocumentContentNotFoundException("Document has no raw storage key.")

        try:
            source_stream = self._storage.open(document.storage_key)
        except Exception as e:
            raise DocumentContentNotFoundException(
                f"Raw content for document {document.id} could not be retrieved from storage: {e}"
            )

        fd, temp_local_path = tempfile.mkstemp(prefix="krama_conv_src_", suffix=f".{document.file_extension}")
        try:
            with os.fdopen(fd, "wb") as temp_file:
                while True:
                    chunk = source_stream.read(Config.UPLOAD_CHUNK_SIZE_BYTES)
                    if not chunk:
                        break
                    temp_file.write(chunk)
        except Exception as e:
            os.unlink(temp_local_path)
            raise ConversionFailed(f"Failed to buffer raw document for conversion: {e}")
        finally:
            source_stream.close()

        # 7. Select converter
        converter = registry.get_converter_for_extension(document.file_extension)
        if not converter:
            if os.path.exists(temp_local_path):
                os.unlink(temp_local_path)
            raise UnsupportedConversionFormat(
                f"No converter registered for file extension '.{document.file_extension}'."
            )

        # 8. Start conversion. Mark status as CONVERTING
        try:
            document.status = DocumentStatus.CONVERTING
            self._db.commit()
        except Exception as e:
            self._db.rollback()
            if os.path.exists(temp_local_path):
                os.unlink(temp_local_path)
            raise ConversionFailed(f"Failed to update document status to CONVERTING: {e}")

        # Set job stage to RUNNING (job remains PENDING)
        stage.status = JobStageStatus.RUNNING
        stage.started_at = datetime.now(timezone.utc)
        stage.error_code = None
        stage.error_message = None
        self._db.flush()

        stored_keys: List[str] = []
        page_records: List[Page] = []

        try:
            # Yield pages incrementally
            for converted_page in converter.convert(temp_local_path):
                page_num = converted_page.page_number
                size_bytes, checksum = converted_page.read_metadata_and_hashes()

                page_key = f"processed/{organization_id}/{document.claim_id}/{document.id}/pages/{page_num:04d}.png"

                try:
                    self._storage.save_stream(page_key, converted_page.stream, content_type="image/png")
                    stored_keys.append(page_key)
                except Exception as e:
                    raise ConversionFailed(f"Failed to store page {page_num} artifact: {e}")
                finally:
                    converted_page.stream.close()

                db_page = Page(
                    document_id=document.id,
                    page_number=page_num,
                    width=converted_page.width,
                    height=converted_page.height,
                    status=PageStatus.PROCESSED,
                    storage_key=page_key,
                    content_type="image/png",
                    checksum=checksum,
                    size_bytes=size_bytes,
                )
                page_records.append(db_page)
                logger.info(
                    "page_rendered doc_id=%s page_num=%d width=%d height=%d",
                    document.id,
                    page_num,
                    converted_page.width,
                    converted_page.height,
                )

            total_pages = len(page_records)
            if total_pages == 0:
                raise ConversionFailed("No pages were materialized from the document.")

            # Create pages
            for p in page_records:
                self._page_repo.create(p)

            # Update metadata
            document.status = DocumentStatus.CONVERTED
            document.page_count = total_pages
            stage.status = JobStageStatus.SUCCEEDED
            stage.completed_at = datetime.now(timezone.utc)
            stage.progress = 100

            self._db.commit()
            logger.info("conversion_completed doc_id=%s page_count=%d", document.id, total_pages)
            return page_records

        except Exception as conv_exc:
            self._db.rollback()
            logger.error(
                "conversion_failed doc_id=%s request_id=%s error=%s",
                document.id,
                request_id,
                type(conv_exc).__name__,
            )

            # Compensate stored page artifacts
            self._compensate_artifacts(stored_keys, document.id)

            # Move status to CONVERSION_FAILED in a separate transaction
            try:
                self._db.rollback()
                fresh_doc = self._doc_repo.get_by_id_and_org(document.id, organization_id)
                if fresh_doc:
                    fresh_doc.status = DocumentStatus.CONVERSION_FAILED

                fresh_stage = self._db.execute(
                    select(JobStage).where(
                        and_(
                            JobStage.job_id == job.id,
                            JobStage.stage_name == "CONVERT",
                        )
                    )
                ).scalar_one_or_none()
                if fresh_stage:
                    fresh_stage.status = JobStageStatus.FAILED
                    fresh_stage.completed_at = datetime.now(timezone.utc)
                    fresh_stage.error_code = getattr(conv_exc, "code", "CONVERSION_FAILED")
                    fresh_stage.error_message = str(conv_exc)[:1024]

                self._db.commit()
            except Exception as update_exc:
                self._db.rollback()
                logger.critical(
                    "conversion_failed_status_update_failed doc_id=%s error=%s",
                    document.id,
                    type(update_exc).__name__,
                )

            raise conv_exc

        finally:
            if os.path.exists(temp_local_path):
                try:
                    os.unlink(temp_local_path)
                except Exception as e:
                    logger.warning("Failed to delete local temp source file: %s", e)

    def _clean_previous_conversion_attempt(self, document: Document, organization_id: uuid.UUID) -> None:
        """Purge any stale metadata or artifacts from prior conversion attempts."""
        pages = self._page_repo.list_by_document_and_org(document.id, organization_id)
        if not pages:
            return

        logger.info("cleaning_stale_pages doc_id=%s count=%d", document.id, len(pages))
        for page in pages:
            if page.storage_key:
                try:
                    self._storage.delete(page.storage_key)
                except Exception as e:
                    logger.warning("Failed to delete stale page artifact: %s. Error: %s", page.storage_key, e)

        self._page_repo.delete_by_document(document.id)
        self._db.flush()

    def _get_or_create_job_and_stage(self, document: Document) -> tuple[Job, JobStage]:
        """Find or construct parent DOCUMENT_PROCESSING job and the CONVERT stage."""
        # Find existing job
        stmt = select(Job).where(
            and_(
                Job.document_id == document.id,
                Job.job_type == JobType.DOCUMENT_PROCESSING,
            )
        )
        job = self._db.execute(stmt).scalar_one_or_none()

        if not job:
            job = Job(
                organization_id=document.organization_id,
                claim_id=document.claim_id,
                document_id=document.id,
                job_type=JobType.DOCUMENT_PROCESSING,
                status=JobStatus.PENDING,
                progress=0,
            )
            self._db.add(job)
            self._db.flush()

        # Find or create stage
        stmt = select(JobStage).where(
            and_(
                JobStage.job_id == job.id,
                JobStage.stage_name == "CONVERT",
            )
        )
        stage = self._db.execute(stmt).scalar_one_or_none()

        if not stage:
            stage = JobStage(
                job_id=job.id,
                stage_name="CONVERT",
                status=JobStageStatus.PENDING,
                sequence=1,
                progress=0,
            )
            self._db.add(stage)
            self._db.flush()

        return job, stage

    def _compensate_artifacts(self, keys: List[str], document_id: uuid.UUID) -> None:
        """Compensate file storage by deleting rendered pages in case of transactional rollback."""
        request_id = request_id_var.get()
        logger.info(
            "conversion_compensation_started doc_id=%s keys_count=%d request_id=%s",
            document_id,
            len(keys),
            request_id,
        )
        for key in keys:
            try:
                self._storage.delete(key)
            except Exception as cleanup_exc:
                logger.error(
                    "conversion_compensation_failed doc_id=%s key=%s request_id=%s error=%s action=manual_orphan_cleanup_required",
                    document_id,
                    key,
                    request_id,
                    type(cleanup_exc).__name__,
                )
