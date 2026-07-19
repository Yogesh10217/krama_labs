"""Structured logging and correlation ID tracking system."""

import logging
import uuid
import re
from contextvars import ContextVar
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import Config

# Context variable to hold the request ID for the current execution context
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

# Patterns for sensitive keys to redact from logs
SENSITIVE_PATTERNS = [
    (re.compile(r'(api_key|token|password|auth|authorization|secret|key)["\s:]+["\']?([^"\',\s&]+)["\']?', re.IGNORECASE), r'\1: "***REDACTED***"'),
    (re.compile(r'(AIzaSy[A-Za-z0-9_\-]{33})'), '"***REDACTED_GEMINI_KEY***"'),
    (re.compile(r'(sk-[a-zA-Z0-9]{48})'), '"***REDACTED_OPENAI_KEY***"')
]


def redact_sensitive_info(msg: str) -> str:
    """Scan and redact secrets from the log message."""
    if not isinstance(msg, str):
        return msg
    for pattern, replacement in SENSITIVE_PATTERNS:
        msg = pattern.sub(replacement, msg)
    return msg


class RequestIdFilter(logging.Filter):
    """Filter that adds request_id to logging records from ContextVar."""

    def filter(self, record):
        record.request_id = request_id_var.get()
        # Redact message content if it contains sensitive details
        if isinstance(record.msg, str):
            record.msg = redact_sensitive_info(record.msg)
        return True


def setup_logging():
    """Configure core logging settings."""
    log_level = logging.DEBUG if Config.DEBUG else logging.INFO
    
    # Custom logger setup
    root_logger = logging.getLogger()
    
    # Avoid duplicate handlers if already configured
    if root_logger.handlers:
        for handler in list(root_logger.handlers):
            root_logger.removeHandler(handler)

    handler = logging.StreamHandler()
    
    # Format includes timestamp, log level, request_id, logger name and message
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(request_id)s] [%(name)s:%(lineno)d] %(message)s"
    )
    handler.setFormatter(formatter)
    
    # Apply filter to add request_id
    req_id_filter = RequestIdFilter()
    handler.addFilter(req_id_filter)
    
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)
    
    # Silence third-party logging noise slightly
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware to extract/generate X-Request-ID and propagate it."""

    async def dispatch(self, request: Request, call_next):
        # Extract existing request ID header or generate a new one
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            # Generate a short unique ID
            request_id = str(uuid.uuid4())

        # Set request ID in the context variable
        token = request_id_var.set(request_id)
        
        try:
            response: Response = await call_next(request)
            # Inject request ID into response headers
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            # Reset context variable to avoid leakages
            request_id_var.reset(token)
