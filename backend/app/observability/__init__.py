"""
app/observability/__init__.py

Phase 11 observability package.
Exposes: structured logging, Prometheus metrics, OpenTelemetry tracing,
         health model, cache, circuit breakers, and middleware.

Business services import NOTHING from this package.
Observability is applied via middleware, decorators, and DI.
"""

from app.observability.logging import (
    get_logger,
    bind_context,
    clear_context,
    StructuredLogger,
)
from app.observability.metrics import get_metrics_registry, KramaMetrics
from app.observability.tracing import get_tracer, setup_tracing
from app.observability.circuit_breaker import CircuitBreakerRegistry, get_circuit_breaker

__all__ = [
    "get_logger",
    "bind_context",
    "clear_context",
    "StructuredLogger",
    "get_metrics_registry",
    "KramaMetrics",
    "get_tracer",
    "setup_tracing",
    "CircuitBreakerRegistry",
    "get_circuit_breaker",
]
