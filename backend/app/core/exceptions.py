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
