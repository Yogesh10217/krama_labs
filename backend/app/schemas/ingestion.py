"""Pydantic schemas for Phase 2 ingestion API responses.

These schemas define the response shape for:
- Single document upload (POST /upload)
- Batch document upload (POST /batch)
- Document content retrieval (GET /content)

Storage keys and physical paths are NEVER exposed to clients.
"""
import uuid
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.domain.enums import DocumentStatus, JobStatus, JobType


class UploadedDocumentResponse(BaseModel):
    """Document portion of a successful upload response."""
    id: uuid.UUID
    claim_id: uuid.UUID
    organization_id: uuid.UUID
    original_filename: str
    content_type: Optional[str] = None
    file_extension: Optional[str] = None
    size_bytes: Optional[int] = None
    checksum: Optional[str] = None
    status: DocumentStatus

    model_config = ConfigDict(from_attributes=True)


class UploadedJobResponse(BaseModel):
    """Job portion of a successful upload response."""
    id: uuid.UUID
    job_type: JobType
    status: JobStatus
    progress: int

    model_config = ConfigDict(from_attributes=True)


class SingleUploadResponse(BaseModel):
    """Response for POST /claims/{claim_id}/documents/upload."""
    document: UploadedDocumentResponse
    job: UploadedJobResponse


class BatchFileError(BaseModel):
    """Error detail for a single failed file in a batch."""
    code: str
    message: str


class BatchFileResult(BaseModel):
    """Per-file result within a batch upload response."""
    filename: str
    status: str  # "success" | "failed"
    document_id: Optional[uuid.UUID] = None
    job_id: Optional[uuid.UUID] = None
    error: Optional[BatchFileError] = None


class BatchUploadResponse(BaseModel):
    """Response for POST /claims/{claim_id}/documents/batch.

    HTTP 200 is returned even when some files fail.
    Each file's outcome is reflected in the 'results' list.
    """
    total: int
    succeeded: int
    failed: int
    results: List[BatchFileResult]
