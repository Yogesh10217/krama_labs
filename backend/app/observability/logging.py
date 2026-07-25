"""
app/observability/logging.py — Phase 11 Structured JSON Logging

Every log record includes the full context envelope:
  timestamp, level, correlation_id, organization_id, document_id,
  job_id, worker_id, stage, event, message, duration_ms, exception,
  service_name, service_version, environment, host, thread, process_id

Design principles:
  - Structured JSON output for log aggregators (Loki, CloudWatch, Datadog).
  - Context propagation via Python ContextVars (thread-safe, async-safe).
  - Business services are NEVER aware of this module.
  - Sensitive keys are redacted at the handler level.
"""

import logging
import os
import re
import socket
import threading
import uuid
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

# pythonjsonlogger is an optional dependency; fall back gracefully.
try:
    from pythonjsonlogger import jsonlogger  # type: ignore
    _HAS_JSON_LOGGER = True
except ImportError:
    _HAS_JSON_LOGGER = False

from app.core.config import Config

# ---------------------------------------------------------------------------
# Log context — propagated through the entire request / job lifecycle
# ---------------------------------------------------------------------------

@dataclass
class _LogContext:
    correlation_id: str = "-"
    organization_id: str = "-"
    document_id: str = "-"
    job_id: str = "-"
    worker_id: str = "-"
    stage: str = "-"
    event: str = "-"
    duration_ms: Optional[float] = None
    extra: Dict[str, Any] = field(default_factory=dict)


_context_var: ContextVar[_LogContext] = ContextVar("log_context", default=_LogContext())


def bind_context(**kwargs) -> Token:
    """
    Bind log context fields for the current async/thread context.
    Returns a token that can be used with clear_context() to restore
    the previous context (important for middleware).
    """
    current = _context_var.get()
    updated = _LogContext(
        correlation_id=kwargs.get("correlation_id", current.correlation_id),
        organization_id=kwargs.get("organization_id", current.organization_id),
        document_id=kwargs.get("document_id", current.document_id),
        job_id=kwargs.get("job_id", current.job_id),
        worker_id=kwargs.get("worker_id", current.worker_id),
        stage=kwargs.get("stage", current.stage),
        event=kwargs.get("event", current.event),
        duration_ms=kwargs.get("duration_ms", current.duration_ms),
        extra={**current.extra, **kwargs.get("extra", {})},
    )
    return _context_var.set(updated)


def clear_context(token: Token) -> None:
    """Restore previous log context (call in finally blocks)."""
    _context_var.reset(token)


def get_current_context() -> _LogContext:
    return _context_var.get()


# ---------------------------------------------------------------------------
# Sensitive key redaction
# ---------------------------------------------------------------------------

_SENSITIVE_PATTERNS = [
    (re.compile(
        r'(api_key|token|password|auth|authorization|secret|key)["\s:]+(["\']?)([^"\',\s&]+)\2',
        re.IGNORECASE,
    ), r'\1: "***REDACTED***"'),
    (re.compile(r'AIzaSy[A-Za-z0-9_\-]{33}'), '"***REDACTED_GEMINI_KEY***"'),
    (re.compile(r'sk-[a-zA-Z0-9]{48}'),        '"***REDACTED_OPENAI_KEY***"'),
]


def _redact(msg: str) -> str:
    if not isinstance(msg, str):
        return msg
    for pattern, replacement in _SENSITIVE_PATTERNS:
        msg = pattern.sub(replacement, msg)
    return msg


# ---------------------------------------------------------------------------
# Custom log filter — injects context fields into every LogRecord
# ---------------------------------------------------------------------------

_SERVICE_HOST = socket.gethostname()
_PID = os.getpid()


class _ContextFilter(logging.Filter):
    """Injects structured context fields into every LogRecord."""

    def filter(self, record: logging.LogRecord) -> bool:
        ctx = _context_var.get()
        record.correlation_id   = ctx.correlation_id
        record.organization_id  = ctx.organization_id
        record.document_id      = ctx.document_id
        record.job_id           = ctx.job_id
        record.worker_id        = ctx.worker_id
        record.stage            = ctx.stage
        record.event            = ctx.event
        record.duration_ms      = ctx.duration_ms

        # Service identity fields
        record.service_name     = Config.APP_NAME
        record.service_version  = Config.VERSION
        record.environment      = Config.ENV
        record.host             = _SERVICE_HOST
        record.thread_name      = threading.current_thread().name
        record.process_id       = _PID

        # Redact sensitive info from message
        if isinstance(record.msg, str):
            record.msg = _redact(record.msg)

        return True


# ---------------------------------------------------------------------------
# JSON formatter — produces structured log records
# ---------------------------------------------------------------------------

class _KramaJsonFormatter(logging.Formatter):
    """
    JSON log formatter.

    Falls back to readable text when python-json-logger is unavailable.
    Each record is one JSON line with all context fields.
    """

    # Fields always included in the JSON envelope
    _ENVELOPE_FIELDS = [
        "timestamp", "level", "message",
        "correlation_id", "organization_id", "document_id",
        "job_id", "worker_id", "stage", "event", "duration_ms",
        "service_name", "service_version", "environment",
        "host", "thread_name", "process_id",
        "logger", "module", "line",
    ]

    @staticmethod
    def _format_timestamp(record: logging.LogRecord) -> str:
        """Return ISO 8601 timestamp with milliseconds, e.g. 2026-07-25T08:00:00.123Z"""
        import datetime
        dt = datetime.datetime.fromtimestamp(record.created, tz=datetime.timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(record.msecs):03d}Z"

    def format(self, record: logging.LogRecord) -> str:
        import json

        # Format the base message (handles %s-style formatting)
        message = record.getMessage()

        log_obj: Dict[str, Any] = {
            "timestamp":        self._format_timestamp(record),
            "level":            record.levelname,
            "message":          message,
            "correlation_id":   getattr(record, "correlation_id", "-"),
            "organization_id":  getattr(record, "organization_id", "-"),
            "document_id":      getattr(record, "document_id", "-"),
            "job_id":           getattr(record, "job_id", "-"),
            "worker_id":        getattr(record, "worker_id", "-"),
            "stage":            getattr(record, "stage", "-"),
            "event":            getattr(record, "event", "-"),
            "duration_ms":      getattr(record, "duration_ms", None),
            "service_name":     getattr(record, "service_name", Config.APP_NAME),
            "service_version":  getattr(record, "service_version", Config.VERSION),
            "environment":      getattr(record, "environment", Config.ENV),
            "host":             getattr(record, "host", _SERVICE_HOST),
            "thread_name":      getattr(record, "thread_name", threading.current_thread().name),
            "process_id":       getattr(record, "process_id", _PID),
            "logger":           record.name,
            "module":           record.module,
            "line":             record.lineno,
        }

        # Attach exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        elif record.exc_text:
            log_obj["exception"] = record.exc_text

        # Remove None values for cleaner output
        log_obj = {k: v for k, v in log_obj.items() if v is not None}

        return json.dumps(log_obj, default=str, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Public setup function
# ---------------------------------------------------------------------------

def setup_logging() -> None:
    """
    Configure the root logger with structured JSON output.

    Call this once at application startup (before any log calls).
    Replaces the previous setup_logging() in app/core/logging.py.
    """
    log_level = logging.DEBUG if Config.DEBUG else logging.INFO

    root_logger = logging.getLogger()

    # Remove existing handlers to avoid duplicates on reload
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(_KramaJsonFormatter())
    handler.addFilter(_ContextFilter())
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Tame noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.DEBUG if Config.DATABASE_ECHO else logging.WARNING
    )


# ---------------------------------------------------------------------------
# StructuredLogger — thin wrapper that pre-binds context
# ---------------------------------------------------------------------------

class StructuredLogger:
    """
    Thin wrapper around stdlib logger that supports structured context binding.

    Usage:
        logger = StructuredLogger(__name__)
        logger.info("stage_complete", stage="ocr", duration_ms=123.4)

    The event kwarg is stored in the context for that log call only.
    """

    def __init__(self, name: str) -> None:
        self._logger = logging.getLogger(name)

    def _log(self, level: int, msg: str, **ctx_kwargs) -> None:
        extra_bind: Dict[str, Any] = {}
        if "event" in ctx_kwargs:
            extra_bind["event"] = ctx_kwargs.pop("event")
        if "stage" in ctx_kwargs:
            extra_bind["stage"] = ctx_kwargs.pop("stage")
        if "duration_ms" in ctx_kwargs:
            extra_bind["duration_ms"] = ctx_kwargs.pop("duration_ms")

        if extra_bind:
            token = bind_context(**extra_bind)
            try:
                self._logger.log(level, msg, **ctx_kwargs)
            finally:
                clear_context(token)
        else:
            self._logger.log(level, msg, **ctx_kwargs)

    def debug(self, msg: str, **kwargs)   -> None: self._log(logging.DEBUG,    msg, **kwargs)
    def info(self, msg: str, **kwargs)    -> None: self._log(logging.INFO,     msg, **kwargs)
    def warning(self, msg: str, **kwargs) -> None: self._log(logging.WARNING,  msg, **kwargs)
    def error(self, msg: str, **kwargs)   -> None: self._log(logging.ERROR,    msg, **kwargs)
    def critical(self, msg: str, **kwargs)-> None: self._log(logging.CRITICAL, msg, **kwargs)

    def exception(self, msg: str, **kwargs) -> None:
        kwargs.setdefault("exc_info", True)
        self._log(logging.ERROR, msg, **kwargs)


def get_logger(name: str) -> StructuredLogger:
    """Return a StructuredLogger for the given module name."""
    return StructuredLogger(name)
