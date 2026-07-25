"""
app/core/logging.py — Backward Compatibility Shim

Phase 11 moved structured logging to app/observability/logging.py.
This module re-exports the symbols that existing code depended on
so no import paths outside this module need to change.

The CorrelationIdMiddleware re-export ensures that any code that
previously imported it from here still works. Phase 11 uses
app/observability/middleware.CorrelationIdMiddleware which is
functionally a superset.
"""

# Re-export Phase 11 structured logging as the canonical implementation
from app.observability.logging import (  # noqa: F401
    setup_logging,
    bind_context,
    clear_context,
    get_logger,
    get_current_context,
    StructuredLogger,
)

# Re-export Phase 11 CorrelationIdMiddleware for any code that
# imported it from app.core.logging
from app.observability.middleware import CorrelationIdMiddleware  # noqa: F401


class _CorrelationIdVar:
    """
    Backward-compat shim for the legacy `request_id_var` ContextVar.

    The old code did: request_id_var.get()  → returned a string
    The new context holds a _LogContext object.
    This shim delegates .get() to return the correlation_id string.
    """

    def get(self, default: str = "-") -> str:
        from app.observability.logging import get_current_context
        return get_current_context().correlation_id

    def set(self, value: str):
        from app.observability.logging import bind_context
        return bind_context(correlation_id=value)

    def reset(self, token) -> None:
        from app.observability.logging import clear_context
        clear_context(token)


# Provide the legacy symbol
request_id_var = _CorrelationIdVar()

__all__ = [
    "setup_logging",
    "bind_context",
    "clear_context",
    "get_logger",
    "get_current_context",
    "StructuredLogger",
    "request_id_var",
    "CorrelationIdMiddleware",
]

