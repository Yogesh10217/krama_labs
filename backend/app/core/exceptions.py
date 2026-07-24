"""Centralized exception classes and global error handlers for FastAPI."""

import logging
import traceback
from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import request_id_var

logger = logging.getLogger(__name__)


class KramaException(Exception):
    """Base exception for all application/domain errors."""
    
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class NotFoundException(KramaException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, message: str, code: str = "NOT_FOUND"):
        super().__init__(message, code, status.HTTP_404_NOT_FOUND)


class ValidationException(KramaException):
    """Raised for input validation failures."""
    
    def __init__(self, message: str, code: str = "VALIDATION_ERROR"):
        super().__init__(message, code, status.HTTP_400_BAD_REQUEST)


class ServiceUnavailableException(KramaException):
    """Raised when an optional dependency or external API is unavailable."""
    
    def __init__(self, message: str, code: str = "SERVICE_UNAVAILABLE"):
        super().__init__(message, code, status.HTTP_503_SERVICE_UNAVAILABLE)


class ConflictException(KramaException):
    """Raised for resource conflicts, e.g. duplicate unique keys."""
    def __init__(self, message: str, code: str = "CONFLICT"):
        super().__init__(message, code, status.HTTP_409_CONFLICT)


class ForbiddenException(KramaException):
    """Raised when access to a resource is forbidden."""
    def __init__(self, message: str, code: str = "FORBIDDEN"):
        super().__init__(message, code, status.HTTP_403_FORBIDDEN)


# ─── Phase 2: Ingestion-specific exceptions ───────────────────────────────────

class UnsupportedFileTypeException(KramaException):
    """Raised when an uploaded file has an unsupported type."""
    def __init__(self, message: str):
        super().__init__(message, "UNSUPPORTED_FILE_TYPE", status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)


class FileTooLargeException(KramaException):
    """Raised when an uploaded file exceeds the maximum allowed size."""
    def __init__(self, message: str):
        super().__init__(message, "FILE_TOO_LARGE", status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)


class EmptyFileException(KramaException):
    """Raised when an uploaded file contains zero bytes."""
    def __init__(self, message: str = "Uploaded file is empty."):
        super().__init__(message, "EMPTY_FILE", status.HTTP_400_BAD_REQUEST)


class InvalidFileSignatureException(KramaException):
    """Raised when the file's magic bytes do not match expected signatures."""
    def __init__(self, message: str):
        super().__init__(message, "INVALID_FILE_SIGNATURE", status.HTTP_400_BAD_REQUEST)


class ContentTypeMismatchException(KramaException):
    """Raised when declared MIME type strongly conflicts with extension and signature."""
    def __init__(self, message: str):
        super().__init__(message, "CONTENT_TYPE_MISMATCH", status.HTTP_400_BAD_REQUEST)


class InvalidFilenameException(KramaException):
    """Raised when the uploaded filename is invalid or unsafe."""
    def __init__(self, message: str):
        super().__init__(message, "INVALID_FILENAME", status.HTTP_400_BAD_REQUEST)


class DuplicateDocumentException(KramaException):
    """Raised when a document with the same checksum already exists in the same claim."""
    def __init__(self, message: str, existing_document_id: str | None = None):
        super().__init__(message, "DUPLICATE_DOCUMENT", status.HTTP_409_CONFLICT)
        self.existing_document_id = existing_document_id


class BatchLimitExceededException(KramaException):
    """Raised when a batch upload exceeds the configured file or size limit."""
    def __init__(self, message: str):
        super().__init__(message, "BATCH_LIMIT_EXCEEDED", status.HTTP_400_BAD_REQUEST)


class StorageUnavailableException(KramaException):
    """Raised when the storage provider cannot be reached or initialised."""
    def __init__(self, message: str):
        super().__init__(message, "STORAGE_UNAVAILABLE", status.HTTP_503_SERVICE_UNAVAILABLE)


class StorageWriteFailedException(KramaException):
    """Raised when the storage provider fails to write an object."""
    def __init__(self, message: str):
        super().__init__(message, "STORAGE_WRITE_FAILED", status.HTTP_503_SERVICE_UNAVAILABLE)


class DocumentNotReadyForConversion(KramaException):
    """Raised when trying to convert a document that is not in a valid state (e.g. not UPLOADED/CONVERSION_FAILED)."""
    def __init__(self, message: str):
        super().__init__(message, "DOCUMENT_NOT_READY_FOR_CONVERSION", status.HTTP_400_BAD_REQUEST)


class DocumentAlreadyConverting(KramaException):
    """Raised when trying to convert a document that is currently in CONVERTING status."""
    def __init__(self, message: str):
        super().__init__(message, "DOCUMENT_ALREADY_CONVERTING", status.HTTP_409_CONFLICT)


class UnsupportedConversionFormat(KramaException):
    """Raised when the document format has no registered converter."""
    def __init__(self, message: str):
        super().__init__(message, "UNSUPPORTED_CONVERSION_FORMAT", status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)


class ConversionFailed(KramaException):
    """Raised when the conversion engine fails to process a document or page."""
    def __init__(self, message: str):
        super().__init__(message, "CONVERSION_FAILED", status.HTTP_500_INTERNAL_SERVER_ERROR)


class CorruptedDocument(KramaException):
    """Raised when the document is malformed or corrupted and cannot be opened."""
    def __init__(self, message: str):
        super().__init__(message, "CORRUPTED_DOCUMENT", status.HTTP_400_BAD_REQUEST)


class EncryptedDocument(KramaException):
    """Raised when the document is password-protected or encrypted."""
    def __init__(self, message: str):
        super().__init__(message, "ENCRYPTED_DOCUMENT", status.HTTP_400_BAD_REQUEST)


class DocumentPageLimitExceeded(KramaException):
    """Raised when the page count exceeds the configured maximum page limit."""
    def __init__(self, message: str):
        super().__init__(message, "DOCUMENT_PAGE_LIMIT_EXCEEDED", status.HTTP_400_BAD_REQUEST)


class PageDimensionLimitExceeded(KramaException):
    """Raised when a single page's width or height exceeds limits."""
    def __init__(self, message: str):
        super().__init__(message, "PAGE_DIMENSION_LIMIT_EXCEEDED", status.HTTP_400_BAD_REQUEST)


class PagePixelLimitExceeded(KramaException):
    """Raised when a single page's total pixels exceed maximum limit (decompression bomb protection)."""
    def __init__(self, message: str):
        super().__init__(message, "PAGE_PIXEL_LIMIT_EXCEEDED", status.HTTP_400_BAD_REQUEST)


class PageArtifactMissing(KramaException):
    """Raised when a page record exists but its physical PNG file is missing from storage."""
    def __init__(self, message: str):
        super().__init__(message, "PAGE_ARTIFACT_MISSING", status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConversionStateInconsistent(KramaException):
    """Raised when a document is marked as converted but page counts or records don't match."""
    def __init__(self, message: str):
        super().__init__(message, "CONVERSION_STATE_INCONSISTENT", status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentContentNotFoundException(KramaException):
    """Raised when a document's content is not found in storage."""
    def __init__(self, message: str = "Document content not found in storage."):
        super().__init__(message, "DOCUMENT_CONTENT_NOT_FOUND", status.HTTP_404_NOT_FOUND)


class DocumentNotReadyForOCR(KramaException):
    def __init__(self, message: str = "Document is not ready for OCR"):
        super().__init__(message, "DOCUMENT_NOT_READY_FOR_OCR", status.HTTP_400_BAD_REQUEST)


class OCRProviderUnavailableException(ServiceUnavailableException):
    """Raised when the OCR provider is not installed or unavailable."""
    def __init__(self, message: str = "Configured OCR provider is not available."):
        super().__init__(message, "OCR_PROVIDER_UNAVAILABLE")


class DocumentNotReadyForExtractionException(KramaException):
    def __init__(self, document_id: str, status: str):
        super().__init__(
            status_code=400,
            code="DOCUMENT_NOT_READY_FOR_EXTRACTION",
            message=f"Document {document_id} cannot be extracted in status {status}."
        )


class ExtractionFailedException(KramaException):
    def __init__(self, document_id: str, detail: str):
        super().__init__(
            status_code=500,
            code="EXTRACTION_FAILED",
            message=f"Extraction failed for document {document_id}: {detail}"
        )

class ValidationFailedException(KramaException):
    def __init__(self, document_id: str, detail: str):
        super().__init__(
            status_code=500,
            code="VALIDATION_FAILED",
            message=f"Validation failed for document {document_id}: {detail}"
        )

class DocumentNotReadyForValidationException(KramaException):
    def __init__(self, document_id: str, status: str):
        super().__init__(
            status_code=400,
            code="DOCUMENT_NOT_READY_FOR_VALIDATION",
            message=f"Document {document_id} cannot be validated in status {status}."
        )

# ─── Phase 9: Workflow & Review Exceptions ─────────────────────────────────────

class ReviewSessionNotFoundException(NotFoundException):
    def __init__(self, document_id: str):
        super().__init__(
            message=f"Review session for document {document_id} was not found.",
            code="REVIEW_SESSION_NOT_FOUND"
        )

class ConcurrentReviewConflictException(ConflictException):
    def __init__(self, message: str = "Review session was modified by another user. Please reload and retry."):
        super().__init__(
            message=message,
            code="CONCURRENT_REVIEW_CONFLICT"
        )

class ReviewStateInvalidException(KramaException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="REVIEW_STATE_INVALID",
            status_code=status.HTTP_400_BAD_REQUEST
        )


def make_error_response(code: str, message: str, status_code: int) -> JSONResponse:
    """Helper to construct standard JSON error response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id_var.get()
            }
        }
    )


async def krama_exception_handler(request: Request, exc: KramaException) -> JSONResponse:
    """Handle custom application exceptions."""
    logger.error(f"Domain error [{exc.code}]: {exc.message}")
    return make_error_response(exc.code, exc.message, exc.status_code)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle standard FastAPI/Starlette HTTP exceptions."""
    logger.error(f"HTTP exception [{exc.status_code}]: {exc.detail}")
    
    # Map status codes to custom error codes
    code = "HTTP_ERROR"
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        code = "NOT_FOUND"
    elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
        code = "UNAUTHORIZED"
    elif exc.status_code == status.HTTP_403_FORBIDDEN:
        code = "FORBIDDEN"
    elif exc.status_code == status.HTTP_400_BAD_REQUEST:
        code = "BAD_REQUEST"
        
    return make_error_response(code, str(exc.detail), exc.status_code)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request body/parameter validation errors."""
    # Build a concise error message from the validation errors
    errors = exc.errors()
    details = []
    for err in errors:
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "Unknown error")
        details.append(f"{loc}: {msg}")
    
    error_message = "; ".join(details)
    logger.error(f"Request validation failed: {error_message}")
    
    return make_error_response("VALIDATION_ERROR", f"Validation failed: {error_message}", status.HTTP_422_UNPROCESSABLE_ENTITY)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unhandled exceptions."""
    tb = traceback.format_exc()
    logger.critical(f"Unhandled server exception: {exc}\n{tb}")
    
    # Do not leak stack traces in response
    return make_error_response(
        "INTERNAL_SERVER_ERROR",
        "An unexpected error occurred on the server.",
        status.HTTP_500_INTERNAL_SERVER_ERROR
    )
