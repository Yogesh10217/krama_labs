"""
app/observability/tracing.py — Phase 11 OpenTelemetry Distributed Tracing

Span hierarchy (per approved spec):
  HTTP Request → Job → Worker → Pipeline → Stage → Provider

Every span includes resource attributes:
  service.name, service.version, deployment.environment

Every span includes context attributes:
  correlation_id, document_id, organization_id

Setup:
  - OTLP exporter when OTLP_ENDPOINT is set
  - ConsoleSpanExporter when DEBUG=True and no endpoint configured
  - NoOp when ENABLE_TRACING=False

Business services are NEVER aware of this module.
"""

from __future__ import annotations

import functools
import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, Generator, Optional

try:
    from opentelemetry import trace  # type: ignore
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION  # type: ignore
    from opentelemetry.sdk.trace import TracerProvider  # type: ignore
    from opentelemetry.sdk.trace.export import (  # type: ignore
        BatchSpanProcessor,
        ConsoleSpanExporter,
        SimpleSpanProcessor,
    )
    from opentelemetry.trace import StatusCode, NonRecordingSpan  # type: ignore
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator  # type: ignore
    from opentelemetry.propagators.b3 import B3Format  # type: ignore
    from opentelemetry.propagate import set_global_textmap  # type: ignore
    from opentelemetry.baggage.propagation import W3CBaggagePropagator  # type: ignore
    from opentelemetry.propagators.composite import CompositePropagator  # type: ignore
    _HAS_OTEL = True
except ImportError:
    _HAS_OTEL = False

from app.core.config import Config


# ---------------------------------------------------------------------------
# No-op stubs — used when opentelemetry-sdk is not installed
# ---------------------------------------------------------------------------

class _NoOpSpan:
    def set_attribute(self, *a, **kw): pass
    def set_status(self, *a, **kw): pass
    def record_exception(self, *a, **kw): pass
    def end(self): pass
    def __enter__(self): return self
    def __exit__(self, *a): pass


class _NoOpTracer:
    def start_span(self, name: str, **kwargs) -> _NoOpSpan:
        return _NoOpSpan()

    def start_as_current_span(self, name: str, **kwargs):
        return _NoOpSpanCtx()


class _NoOpSpanCtx:
    def __enter__(self): return _NoOpSpan()
    def __exit__(self, *a): pass


# ---------------------------------------------------------------------------
# Tracer provider setup
# ---------------------------------------------------------------------------

_tracer_provider: Any = None


def setup_tracing() -> None:
    """
    Initialize the OpenTelemetry tracer provider.
    Must be called once during application startup.
    """
    global _tracer_provider

    if not Config.ENABLE_TRACING:
        return

    if not _HAS_OTEL:
        import logging
        logging.getLogger(__name__).warning(
            "opentelemetry-sdk not installed. Tracing disabled."
        )
        return

    resource = Resource.create({
        SERVICE_NAME:    Config.OTEL_SERVICE_NAME,
        SERVICE_VERSION: Config.VERSION,
        "deployment.environment": Config.ENV,
        "service.namespace":      "krama-ai",
    })

    provider = TracerProvider(resource=resource)

    if Config.OTLP_ENDPOINT:
        # OTLP gRPC exporter — production mode
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter  # type: ignore
            otlp_exporter = OTLPSpanExporter(
                endpoint=Config.OTLP_ENDPOINT,
                insecure=Config.OTLP_INSECURE,
            )
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(
                "Failed to init OTLP exporter (%s). Falling back to console.", exc
            )
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    else:
        # Development: simple console exporter (only when DEBUG)
        if Config.DEBUG:
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    _tracer_provider = provider

    # Set global propagator: W3C TraceContext + Baggage
    set_global_textmap(CompositePropagator([
        TraceContextTextMapPropagator(),
        W3CBaggagePropagator(),
    ]))


def get_tracer(name: str = "krama-ai") -> Any:
    """Return a named tracer. Falls back to NoOp tracer if OTel not available."""
    if not Config.ENABLE_TRACING or not _HAS_OTEL:
        return _NoOpTracer()
    return trace.get_tracer(name, Config.VERSION)


# ---------------------------------------------------------------------------
# Context helpers
# ---------------------------------------------------------------------------

def extract_trace_context(headers: Dict[str, str]) -> Any:
    """Extract OTel trace context from inbound HTTP headers."""
    if not _HAS_OTEL:
        return None
    from opentelemetry.propagate import extract
    return extract(headers)


def inject_trace_context(headers: Dict[str, str]) -> None:
    """Inject current trace context into outbound HTTP headers."""
    if not _HAS_OTEL:
        return
    from opentelemetry.propagate import inject
    inject(headers)


def get_current_trace_id() -> str:
    """Return current trace ID as hex string, or '-' if no active span."""
    if not _HAS_OTEL:
        return "-"
    try:
        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx and ctx.is_valid:
            return format(ctx.trace_id, "032x")
    except Exception:
        pass
    return "-"


def get_current_span_id() -> str:
    """Return current span ID as hex string, or '-' if no active span."""
    if not _HAS_OTEL:
        return "-"
    try:
        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx and ctx.is_valid:
            return format(ctx.span_id, "016x")
    except Exception:
        pass
    return "-"


# ---------------------------------------------------------------------------
# Span decorator
# ---------------------------------------------------------------------------

def traced(
    span_name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
    record_exception: bool = True,
):
    """
    Decorator that wraps a function in an OTel span.

    Usage:
        @traced("pipeline.ocr", attributes={"component": "ocr"})
        def run_ocr(doc_id: str) -> ...:
            ...
    """
    def decorator(fn: Callable) -> Callable:
        name = span_name or fn.__qualname__
        attrs = attributes or {}

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(name) as span:
                # Set static attributes
                for k, v in attrs.items():
                    span.set_attribute(k, str(v))
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    if record_exception:
                        span.record_exception(exc)
                    if _HAS_OTEL:
                        span.set_status(StatusCode.ERROR, str(exc))
                    raise
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Span context manager helpers
# ---------------------------------------------------------------------------

@contextmanager
def span(
    name: str,
    *,
    correlation_id: str = "-",
    document_id: str = "-",
    organization_id: str = "-",
    extra_attributes: Optional[Dict[str, Any]] = None,
) -> Generator[Any, None, None]:
    """
    Context manager for a named span with standard Krama attributes.

    Usage:
        with span("pipeline.convert", correlation_id=ctx.correlation_id) as s:
            s.set_attribute("doc.pages", 12)
            do_convert()
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as sp:
        sp.set_attribute("krama.correlation_id",  correlation_id)
        sp.set_attribute("krama.document_id",     document_id)
        sp.set_attribute("krama.organization_id", organization_id)
        if extra_attributes:
            for k, v in extra_attributes.items():
                sp.set_attribute(k, str(v))
        try:
            yield sp
        except Exception as exc:
            sp.record_exception(exc)
            if _HAS_OTEL:
                sp.set_status(StatusCode.ERROR, str(exc))
            raise
