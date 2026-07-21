"""Phase 2 Ingestion Service.

Orchestrates the complete document ingestion pipeline:

    UploadFile received
        → Generate Document UUID
        → Stream to temporary file (chunk by chunk)
            ├── Count bytes (enforce MAX_UPLOAD_SIZE_MB)
            ├── Compute SHA-256 incrementally
            └── Capture first N bytes for signature validation
        → Validate: empty, extension, MIME, signature
        → Duplicate check (claim_id + checksum)
        → Generate provider-neutral storage key
        → Move temp file to final storage location
        → DB Transaction:
            ├── Create Document (status=UPLOADED)
            ├── flush
            ├── Create Job (status=PENDING)
            └── commit
        → On DB failure: delete stored file (compensation)
        → Return (Document, Job)

Key design principles:
- File is read ONCE during streaming.
- No arbitrary file load into RAM.
- Temporary files use unique server-generated names.
- Temporary files are ALWAYS cleaned up (success, failure, or exception).
- Storage keys are provider-neutral logical paths.
- Absolute filesystem paths are never stored in the database.
- Document and Job creation share a single DB transaction.
- Compensation is logged explicitly; failures are not silently suppressed.
- No OCR, no AI, no background workers are invoked.

Phase 3 note: Page materialization and pipeline stage creation are not done here.
"""
import hashlib
import logging
import os
import uuid
import tempfile
from pathlib import Path
from typing import Optional, Tuple

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import Config
from app.core.exceptions import (
    EmptyFileException,
    UnsupportedFileTypeException,
    InvalidFileSignatureException,
    ContentTypeMismatchException,
    InvalidFilenameException,
    FileTooLargeException,
    DuplicateDocumentException,
    StorageWriteFailedException,
)
from app.core.logging import request_id_var
from app.db.models.document import Document
from app.db.models.job import Job
from app.domain.enums import DocumentStatus, JobType, JobStatus
from app.repositories.document import DocumentRepository
from app.repositories.job import JobRepository
from app.services.claim_service import ClaimService
from app.services.file_policy import (
    MAX_SIGNATURE_BYTES,
    policy_for_extension,
    policy_for_signature,
    is_strong_mime_mismatch,
    SUPPORTED_EXTENSIONS,
)
from app.storage.base import StorageProvider, StorageError

logger = logging.getLogger(__name__)

# Maximum length for normalised filename (stored for display only).
MAX_FILENAME_DISPLAY_LENGTH = 255


def _sanitize_filename(filename: str) -> str:
    """Return a safe display filename by removing control characters and limiting length.

    This name is ONLY used for display metadata (original_filename column).
    It is NEVER used as a filesystem path.

    Raises:
        InvalidFilenameException: If filename is empty after sanitization.
    """
    if not filename:
        raise InvalidFilenameException("Filename is missing or empty.")

    # Strip null bytes and common control characters.
    sanitized = "".join(c for c in filename if ord(c) >= 32 and c != "\x00")
    # Trim whitespace.
    sanitized = sanitized.strip()

    if not sanitized:
        raise InvalidFilenameException("Filename contains only control characters or whitespace.")

    # Truncate to a safe display length.
    if len(sanitized) > MAX_FILENAME_DISPLAY_LENGTH:
        # Preserve extension when truncating.
        ext = Path(sanitized).suffix
        stem = sanitized[: MAX_FILENAME_DISPLAY_LENGTH - len(ext)]
        sanitized = stem + ext

    return sanitized


def _extract_extension(filename: str) -> str:
    """Return normalised file extension (lowercase, no leading dot)."""
    return Path(filename).suffix.lower().lstrip(".")


def _generate_storage_key(
    organization_id: uuid.UUID,
    claim_id: uuid.UUID,
    document_id: uuid.UUID,
    extension: str,
) -> str:
    """Generate a provider-neutral logical storage key.

    Format: raw/{org_id}/{claim_id}/{doc_id}/source.{ext}

    This key is stored in Document.storage_key.
    LocalStorageProvider maps it to a physical path under STORAGE_ROOT.
    Future S3/MinIO providers will use it as an object key.
    """
    safe_ext = extension.lower().lstrip(".") or "bin"
    return f"raw/{organization_id}/{claim_id}/{document_id}/source.{safe_ext}"


class IngestionResult:
    """Carries the result of a successful single-document ingestion."""
    def __init__(self, document: Document, job: Job) -> None:
        self.document = document
        self.job = job


class IngestionService:
    """Orchestrates single-document and batch document ingestion.

    This service is stateless per-request. Instantiate with an active DB session
    and a configured StorageProvider.
    """

    def __init__(self, db: Session, storage: StorageProvider) -> None:
        self._db = db
        self._storage = storage
        self._doc_repo = DocumentRepository(db)
        self._job_repo = JobRepository(db)
        self._claim_service = ClaimService(db)

    # ─── Public API ────────────────────────────────────────────────────────────

    async def ingest_document(
        self,
        organization_id: uuid.UUID,
        claim_id: uuid.UUID,
        upload: UploadFile,
    ) -> IngestionResult:
        """Ingest a single uploaded file.

        This is the core primitive reused by batch ingestion.

        Args:
            organization_id: Tenant identifier.
            claim_id: The claim this document belongs to.
            upload: FastAPI UploadFile from the request.

        Returns:
            IngestionResult with the created Document and Job.

        Raises:
            InvalidFilenameException, EmptyFileException, FileTooLargeException,
            UnsupportedFileTypeException, InvalidFileSignatureException,
            ContentTypeMismatchException, DuplicateDocumentException,
            StorageWriteFailedException, NotFoundException.
        """
        request_id = request_id_var.get()
        logger.info(
            "upload_started org=%s claim=%s request_id=%s",
            organization_id, claim_id, request_id,
        )

        # 1. Validate claim ownership (raises NotFoundException for cross-tenant).
        self._claim_service.get_claim(claim_id, organization_id)

        # 2. Sanitize display filename (never used as a path).
        raw_filename = upload.filename or ""
        display_filename = _sanitize_filename(raw_filename)
        extension = _extract_extension(display_filename)

        # 3. Validate extension early (before streaming).
        if extension not in SUPPORTED_EXTENSIONS:
            raise UnsupportedFileTypeException(
                f"File type '.{extension}' is not supported. "
                f"Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}."
            )

        ext_policy = policy_for_extension(extension)

        # 4. Generate Document UUID now so we can build the storage key later.
        document_id = uuid.uuid4()

        # 5. Stream upload to a temporary file, computing hash and enforcing size limit.
        tmp_path, size_bytes, checksum_hex, file_header = await self._stream_to_temp(upload)

        try:
            # 6. Post-stream validations.
            if size_bytes == 0:
                raise EmptyFileException()

            # 7. Validate file signature.
            sig_policy = policy_for_signature(file_header)
            if sig_policy is None:
                raise InvalidFileSignatureException(
                    f"File signature does not match any supported format. "
                    f"Expected one of: PDF, PNG, JPEG, TIFF."
                )

            # 8. Validate MIME type against extension policy.
            declared_mime = (upload.content_type or "").lower().strip()
            if is_strong_mime_mismatch(declared_mime, ext_policy):
                raise ContentTypeMismatchException(
                    f"Declared Content-Type '{declared_mime}' conflicts strongly "
                    f"with file extension '.{extension}' and file signature. "
                    f"Upload rejected."
                )

            # Verify signature matches extension (e.g., extension=.pdf but signature is PNG → reject).
            if sig_policy is not ext_policy:
                raise InvalidFileSignatureException(
                    f"File signature matches '{sig_policy.label}' but extension "
                    f"indicates '{ext_policy.label}'. Upload rejected."
                )

            logger.info(
                "upload_validated doc_id=%s ext=%s size=%d sha256=%s",
                document_id, extension, size_bytes, checksum_hex[:16] + "...",
            )

            # 9. Duplicate check: same bytes + same claim → reject.
            existing = self._doc_repo.find_active_by_checksum_in_claim(claim_id, checksum_hex)
            if existing:
                raise DuplicateDocumentException(
                    f"A document with the same content already exists in this claim.",
                    existing_document_id=str(existing.id),
                )

            # 10. Generate provider-neutral storage key.
            storage_key = _generate_storage_key(organization_id, claim_id, document_id, extension)

            # 11. Move temporary file to final storage via the provider.
            # We open the temp file and stream it through the provider's save_stream.
            # LocalStorageProvider will then do its own atomic rename internally.
            try:
                with open(tmp_path, "rb") as tmp_stream:
                    self._storage.save_stream(storage_key, tmp_stream, content_type=declared_mime or None)
            except StorageError as exc:
                raise StorageWriteFailedException(
                    f"Failed to store document. Storage reported: {exc.code}"
                ) from exc

            logger.info("storage_write_completed doc_id=%s key=%s", document_id, storage_key)

            # 12. Persist Document + Job in a single transaction.
            # Compensation: if commit fails, delete the stored file.
            normalized_mime = declared_mime if declared_mime else None
            document, job = self._persist_document_and_job(
                organization_id=organization_id,
                claim_id=claim_id,
                document_id=document_id,
                display_filename=display_filename,
                content_type=normalized_mime,
                extension=extension,
                size_bytes=size_bytes,
                checksum=checksum_hex,
                storage_key=storage_key,
            )

            logger.info(
                "upload_completed doc_id=%s job_id=%s",
                document.id, job.id,
            )
            return IngestionResult(document=document, job=job)

        finally:
            # Always clean up the temporary file regardless of outcome.
            _cleanup_temp(tmp_path)

    async def ingest_many(
        self,
        organization_id: uuid.UUID,
        claim_id: uuid.UUID,
        uploads: list[UploadFile],
    ) -> list:
        """Ingest multiple files independently.

        Each file is an independent ingestion unit. A failure in one does NOT
        roll back successfully committed others.

        Returns a list of (UploadFile, IngestionResult | KramaException) tuples
        preserving original request order.
        """
        results = []
        for upload in uploads:
            try:
                result = await self.ingest_document(organization_id, claim_id, upload)
                results.append((upload, result))
            except Exception as exc:
                results.append((upload, exc))
        return results

    # ─── Internal helpers ───────────────────────────────────────────────────────

    async def _stream_to_temp(
        self, upload: UploadFile
    ) -> Tuple[str, int, str, bytes]:
        """Stream UploadFile to a temporary file.

        During the single streaming pass:
        - Counts total bytes.
        - Computes SHA-256 incrementally.
        - Captures the first MAX_SIGNATURE_BYTES for magic-byte validation.
        - Enforces MAX_UPLOAD_SIZE_MB.

        Returns:
            (tmp_path, total_bytes, sha256_hex, file_header)

        Raises:
            FileTooLargeException: If the stream exceeds the configured limit.
        """
        max_bytes = Config.max_upload_size_bytes()
        chunk_size = Config.UPLOAD_CHUNK_SIZE_BYTES
        hasher = hashlib.sha256()
        total_bytes = 0
        file_header = b""

        # Use a secure temporary file in the system's temp directory.
        fd, tmp_path = tempfile.mkstemp(prefix="krama_upload_", suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as tmp_file:
                while True:
                    chunk = await upload.read(chunk_size)
                    if not chunk:
                        break
                    total_bytes += len(chunk)
                    if total_bytes > max_bytes:
                        raise FileTooLargeException(
                            f"File size exceeds the maximum allowed "
                            f"{Config.MAX_UPLOAD_SIZE_MB} MB."
                        )
                    hasher.update(chunk)
                    if len(file_header) < MAX_SIGNATURE_BYTES:
                        file_header += chunk[: MAX_SIGNATURE_BYTES - len(file_header)]
                    tmp_file.write(chunk)
        except FileTooLargeException:
            _cleanup_temp(tmp_path)
            raise
        except Exception as exc:
            _cleanup_temp(tmp_path)
            raise StorageWriteFailedException(
                f"Failed to buffer upload: {exc}"
            ) from exc

        return tmp_path, total_bytes, hasher.hexdigest(), file_header

    def _persist_document_and_job(
        self,
        organization_id: uuid.UUID,
        claim_id: uuid.UUID,
        document_id: uuid.UUID,
        display_filename: str,
        content_type: Optional[str],
        extension: str,
        size_bytes: int,
        checksum: str,
        storage_key: str,
    ) -> Tuple[Document, Job]:
        """Create Document and Job records in a single atomic DB transaction.

        If the commit fails, we attempt to delete the already-stored file as
        compensation and re-raise the database exception.

        Raises:
            Exception: The original database exception after compensation attempt.
        """
        request_id = request_id_var.get()

        document = Document(
            id=document_id,
            organization_id=organization_id,
            claim_id=claim_id,
            original_filename=display_filename,
            content_type=content_type,
            file_extension=extension,
            size_bytes=size_bytes,
            checksum=checksum,
            storage_key=storage_key,
            status=DocumentStatus.UPLOADED,
            page_count=None,  # Phase 3 will populate this.
        )
        self._doc_repo.create(document)
        logger.info("document_created doc_id=%s", document_id)

        job = Job(
            organization_id=organization_id,
            claim_id=claim_id,
            document_id=document_id,
            job_type=JobType.DOCUMENT_PROCESSING,
            status=JobStatus.PENDING,
            progress=0,
        )
        self._job_repo.create(job)
        logger.info("job_created job_id=%s", job.id)

        try:
            self._db.commit()
        except Exception as db_exc:
            # DB transaction failed — attempt to remove the already-stored file.
            self._db.rollback()
            logger.error(
                "upload_failed: DB commit failed after storage. "
                "Attempting storage compensation. "
                "doc_id=%s storage_key=<redacted> request_id=%s",
                document_id, request_id,
            )
            self._compensate_storage(storage_key, document_id, request_id)
            raise db_exc

        return document, job

    def _compensate_storage(
        self,
        storage_key: str,
        document_id: uuid.UUID,
        request_id: str,
    ) -> None:
        """Attempt to delete a stored file after a database failure.

        Logs both success and failure of the compensation attempt.
        Does NOT raise — the original DB exception must propagate.
        Physical storage paths are NEVER logged.
        """
        logger.info(
            "storage_compensation_attempted doc_id=%s request_id=%s",
            document_id, request_id,
        )
        try:
            self._storage.delete(storage_key)
            logger.info(
                "storage_compensation_succeeded doc_id=%s request_id=%s",
                document_id, request_id,
            )
        except Exception as cleanup_exc:
            # Log structured error but do NOT suppress — the original exception
            # propagates to the caller.
            logger.error(
                "storage_compensation_failed doc_id=%s request_id=%s "
                "cleanup_error=%s "
                "action=manual_orphan_cleanup_required",
                document_id, request_id, type(cleanup_exc).__name__,
            )


def _cleanup_temp(tmp_path: str) -> None:
    """Remove a temporary file, logging any failure."""
    try:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    except Exception as exc:
        logger.warning("Failed to remove temporary file. error=%s", type(exc).__name__)
