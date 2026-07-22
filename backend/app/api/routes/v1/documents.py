"""V1 Document API routes.

Endpoints:
    POST   /api/v1/claims/{claim_id}/documents        — Register metadata only (Phase 1, preserved).
    GET    /api/v1/claims/{claim_id}/documents        — List documents for a claim.
    GET    /api/v1/documents/{document_id}            — Get document metadata.
    POST   /api/v1/claims/{claim_id}/documents/upload — Single file upload (Phase 2).
    POST   /api/v1/claims/{claim_id}/documents/batch  — Multi-file batch upload (Phase 2).
    GET    /api/v1/documents/{document_id}/content    — Stream raw file content (Phase 2).

Organization context is required for all endpoints via X-Organization-ID header.
"""
import math
import logging
import uuid
from typing import List

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_organization_context
from app.core.config import Config
from app.core.exceptions import (
    BatchLimitExceededException,
    DocumentContentNotFoundException,
    KramaException,
)
from app.db.models.organization import Organization
from app.db.session import get_db
from app.schemas.common import PaginationMetadata
from app.schemas.document import DocumentCreate, DocumentListResponse, DocumentResponse
from app.schemas.ingestion import (
    BatchFileError,
    BatchFileResult,
    BatchUploadResponse,
    SingleUploadResponse,
    UploadedDocumentResponse,
    UploadedJobResponse,
)
from app.schemas.page import ConversionResponse, PageResponse, PageListResponse
from app.services.document_service import DocumentService
from app.services.ingestion_service import IngestionService
from app.services.conversion_service import ConversionService
from app.repositories.page import PageRepository
from app.storage.base import StorageNotFoundError
from app.storage.factory import get_storage_provider
from app.services.ocr_service import OCRService
from app.ocr.schemas import DocumentOCRSummaryResponse


router = APIRouter()
logger = logging.getLogger(__name__)


# ─── Phase 1 preserved: metadata-only registration ───────────────────────────

@router.post(
    "/claims/{claim_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register document metadata only (no file upload)",
    tags=["Documents"],
)
def register_document(
    claim_id: uuid.UUID,
    doc_in: DocumentCreate,
    org: Organization = Depends(get_organization_context),
    db: Session = Depends(get_db),
):
    """Register document metadata without uploading a file.

    Use POST /upload to upload actual file content.
    This endpoint remains available for metadata-only registration workflows.
    """
    service = DocumentService(db)
    return service.register_document(org.id, claim_id, doc_in)


@router.get(
    "/claims/{claim_id}/documents",
    response_model=DocumentListResponse,
    summary="List documents for a claim",
    tags=["Documents"],
)
def list_claim_documents(
    claim_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    org: Organization = Depends(get_organization_context),
    db: Session = Depends(get_db),
):
    service = DocumentService(db)
    skip = (page - 1) * page_size
    items, total_items = service.list_claim_documents(claim_id, org.id, skip=skip, limit=page_size)

    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1
    pagination = PaginationMetadata(
        page=page, page_size=page_size,
        total_items=total_items, total_pages=total_pages,
    )
    return DocumentListResponse(items=items, pagination=pagination)


@router.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    summary="Get document metadata by ID",
    tags=["Documents"],
)
def get_document(
    document_id: uuid.UUID,
    org: Organization = Depends(get_organization_context),
    db: Session = Depends(get_db),
):
    service = DocumentService(db)
    return service.get_document(document_id, org.id)


# ─── Phase 2: Single file upload ─────────────────────────────────────────────

@router.post(
    "/claims/{claim_id}/documents/upload",
    response_model=SingleUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a single document file",
    tags=["Document Ingestion"],
)
async def upload_document(
    claim_id: uuid.UUID,
    file: UploadFile = File(..., description="Document file (PDF, PNG, JPEG, TIFF)"),
    org: Organization = Depends(get_organization_context),
    db: Session = Depends(get_db),
):
    """Stream, validate, store, and register a single document.

    **Supported formats:** PDF, PNG, JPEG/JPG, TIFF/TIF.

    **Validation layers:**
    1. File extension (must be a supported type).
    2. Declared Content-Type (strong mismatches are rejected).
    3. File signature / magic bytes (highest trust).

    **Limits:** `MAX_UPLOAD_SIZE_MB` per file (default 50 MB).

    **Response:** Created document and associated PENDING processing job.

    **Note:** No OCR or processing is performed at this stage.
    """
    storage = get_storage_provider()
    service = IngestionService(db=db, storage=storage)
    result = await service.ingest_document(org.id, claim_id, file)

    return SingleUploadResponse(
        document=UploadedDocumentResponse.model_validate(result.document),
        job=UploadedJobResponse.model_validate(result.job),
    )


# ─── Phase 2: Multi-file batch upload ────────────────────────────────────────

@router.post(
    "/claims/{claim_id}/documents/batch",
    response_model=BatchUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload multiple document files in one request",
    tags=["Document Ingestion"],
)
async def batch_upload_documents(
    claim_id: uuid.UUID,
    files: List[UploadFile] = File(..., description="One or more document files"),
    org: Organization = Depends(get_organization_context),
    db: Session = Depends(get_db),
):
    """Upload multiple files in a single multipart request.

    **Semantics:** Each file is processed independently. A failure for one file
    does NOT affect successfully uploaded files.

    **Limits:**
    - `MAX_BATCH_FILES` files per request (default 20).
    - `MAX_BATCH_TOTAL_SIZE_MB` cumulative size (enforced cumulatively while
      streaming; if exceeded, remaining files are rejected with BATCH_LIMIT_EXCEEDED).

    **HTTP Status:** Always 200. Per-file status is in each `results` entry.

    **ZIP support:** Not available in Phase 2 (future capability).
    """
    # Enforce file count limit before streaming anything.
    if len(files) > Config.MAX_BATCH_FILES:
        raise BatchLimitExceededException(
            f"Batch exceeds the maximum of {Config.MAX_BATCH_FILES} files. "
            f"Received {len(files)}."
        )

    storage = get_storage_provider()
    results: list[BatchFileResult] = []
    total_bytes_ingested = 0
    max_total_bytes = Config.max_batch_total_size_bytes()

    for upload in files:
        safe_display = (upload.filename or "unknown").strip()[:255]

        # Enforce cumulative total size (checked before attempting next file).
        if total_bytes_ingested >= max_total_bytes:
            results.append(BatchFileResult(
                filename=safe_display,
                status="failed",
                error=BatchFileError(
                    code="BATCH_LIMIT_EXCEEDED",
                    message=(
                        f"Batch total size limit of {Config.MAX_BATCH_TOTAL_SIZE_MB} MB exceeded. "
                        f"This file was not processed."
                    ),
                ),
            ))
            continue

        try:
            service = IngestionService(db=db, storage=storage)
            result = await service.ingest_document(org.id, claim_id, upload)
            total_bytes_ingested += result.document.size_bytes or 0
            results.append(BatchFileResult(
                filename=safe_display,
                status="success",
                document_id=result.document.id,
                job_id=result.job.id,
            ))
        except KramaException as exc:
            results.append(BatchFileResult(
                filename=safe_display,
                status="failed",
                error=BatchFileError(code=exc.code, message=exc.message),
            ))
        except Exception:
            # Catch unexpected errors; do not expose internals.
            logger.exception(
                "Unexpected error during batch ingestion of file=%s", safe_display
            )
            results.append(BatchFileResult(
                filename=safe_display,
                status="failed",
                error=BatchFileError(
                    code="INGESTION_FAILED",
                    message="An unexpected error occurred while processing this file.",
                ),
            ))

    succeeded = sum(1 for r in results if r.status == "success")
    failed = len(results) - succeeded

    return BatchUploadResponse(
        total=len(results),
        succeeded=succeeded,
        failed=failed,
        results=results,
    )


# ─── Phase 2: Raw file content retrieval ─────────────────────────────────────

@router.get(
    "/documents/{document_id}/content",
    summary="Stream raw document file content",
    tags=["Document Ingestion"],
)
def get_document_content(
    document_id: uuid.UUID,
    org: Organization = Depends(get_organization_context),
    db: Session = Depends(get_db),
):
    """Stream the raw file content for a document.

    **Security:**
    - Organization context is enforced (tenant isolation).
    - Storage key is never exposed; a safe download filename is used.
    - File is streamed, not loaded entirely into memory.

    **Response:** Streaming binary response with appropriate Content-Type and
    Content-Disposition headers.
    """
    doc_service = DocumentService(db)
    doc = doc_service.get_document(document_id, org.id)

    if not doc.storage_key:
        raise DocumentContentNotFoundException(
            "This document does not have stored file content."
        )

    storage = get_storage_provider()

    if not storage.exists(doc.storage_key):
        raise DocumentContentNotFoundException(
            "Document file content is not available in storage."
        )

    try:
        file_stream = storage.open(doc.storage_key)
    except StorageNotFoundError:
        raise DocumentContentNotFoundException()

    # Build a safe download filename from original_filename.
    import re
    safe_name = re.sub(r'[^\w.\-]', '_', doc.original_filename or "document")
    safe_name = safe_name[:255]

    content_type = doc.content_type or "application/octet-stream"

    def _iter_stream():
        try:
            while True:
                chunk = file_stream.read(Config.UPLOAD_CHUNK_SIZE_BYTES)
                if not chunk:
                    break
                yield chunk
        finally:
            file_stream.close()

    return StreamingResponse(
        content=_iter_stream(),
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{safe_name}"',
        },
    )


# ─── Phase 3: Document Conversion & Page Listing ─────────────────────────────

@router.post(
    "/documents/{document_id}/convert",
    response_model=ConversionResponse,
    status_code=status.HTTP_200_OK,
    summary="Synchronously convert document to canonical page images",
    tags=["Document Conversion"],
)
def convert_document(
    document_id: uuid.UUID,
    org: Organization = Depends(get_organization_context),
    db: Session = Depends(get_db),
):
    """Trigger synchronous rendering of raw document into canonical PNG pages.

    **Note:** This endpoint executes synchronously for development and testing. 
    In production, this will run asynchronously via background workers.

    **Behavior:**
    - Checks document status (must be UPLOADED or CONVERSION_FAILED).
    - Downloads raw content, renders PDF pages or decodes image frames.
    - Saves rendered PNG pages to object storage (processed/ namespace).
    - Creates database Page records.
    - Updates document status to CONVERTED and advances the CONVERT job stage.
    """
    storage = get_storage_provider()
    service = ConversionService(db=db, storage=storage)
    pages = service.convert_document(org.id, document_id)

    # Fetch document to get fresh status and page count
    doc_service = DocumentService(db)
    doc = doc_service.get_document(document_id, org.id)

    return ConversionResponse(
        document_id=doc.id,
        status=doc.status,
        page_count=doc.page_count or 0,
        pages=[PageResponse.model_validate(p) for p in pages],
    )


@router.get(
    "/documents/{document_id}/pages",
    response_model=PageListResponse,
    summary="List all materialized pages for a document",
    tags=["Document Conversion"],
)
def list_document_pages(
    document_id: uuid.UUID,
    org: Organization = Depends(get_organization_context),
    db: Session = Depends(get_db),
):
    """Retrieve metadata of all pages materialized for a document.

    **Security:** Tenant-isolated (requires valid X-Organization-ID).
    """
    # Verify document exists and belongs to the org
    doc_service = DocumentService(db)
    doc_service.get_document(document_id, org.id)

    page_repo = PageRepository(db)
    pages = page_repo.list_by_document_and_org(document_id, org.id)

    return PageListResponse(
        pages=[PageResponse.model_validate(p) for p in pages]
    )


# ─── Phase 4: Document OCR ───────────────────────────────────────────────────

@router.post(
    "/documents/{document_id}/ocr",
    response_model=DocumentOCRSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Synchronously run OCR on all document pages",
    tags=["Document OCR"],
)
def run_document_ocr(
    document_id: uuid.UUID,
    org: Organization = Depends(get_organization_context),
    db: Session = Depends(get_db),
):
    """Run OCR on all unprocessed pages of a document.
    
    Supports partial retries.
    """
    storage = get_storage_provider()
    service = OCRService(db=db, storage=storage)
    result = service.process_document(org.id, document_id)
    return DocumentOCRSummaryResponse(**result)

