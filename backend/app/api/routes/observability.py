"""
app/api/routes/observability.py — Phase 11 Observability API Endpoints

Endpoints:
  GET /metrics              — Prometheus text format
  GET /observability/status — JSON observability runtime snapshot

/metrics is compatible with Prometheus scraping and Grafana dashboards.
/observability/status returns configuration + runtime state including:
  - Observability feature flags
  - Cache provider and statistics
  - Circuit breaker states for all registered providers
  - Logging and tracing configuration
"""

import logging
from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse, JSONResponse

from app.core.config import Config

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/metrics",
    response_class=PlainTextResponse,
    tags=["Observability"],
    summary="Prometheus metrics endpoint",
    description=(
        "Exposes all Krama AI metrics in Prometheus text format (CONTENT_TYPE_LATEST). "
        "Compatible with Prometheus, Grafana, and OpenTelemetry Collector. "
        "Scrape interval: 15s recommended."
    ),
)
async def prometheus_metrics() -> PlainTextResponse:
    """Return all registered Prometheus metrics in text exposition format."""
    if not Config.ENABLE_METRICS:
        return PlainTextResponse(
            content="# metrics disabled (ENABLE_METRICS=False)\n",
            media_type="text/plain",
        )
    try:
        from app.observability.metrics import get_prometheus_output
        content, content_type = get_prometheus_output()
        return PlainTextResponse(content=content, media_type=content_type)
    except Exception as exc:
        logger.error("Failed to generate Prometheus output: %s", exc)
        return PlainTextResponse(
            content=f"# error generating metrics: {exc}\n",
            media_type="text/plain",
            status_code=500,
        )


@router.get(
    "/observability/status",
    tags=["Observability"],
    summary="Observability runtime status",
    description=(
        "Returns a structured JSON snapshot of the observability layer's "
        "configuration and runtime state. Includes cache statistics, "
        "circuit breaker states, and feature flag status."
    ),
)
async def observability_status() -> JSONResponse:
    """
    Return structured configuration and runtime state of the observability layer.

    Includes:
      - Feature flags (metrics, tracing, cache, rate_limit, circuit_breaker)
      - Logging configuration (format, level)
      - Tracing configuration (endpoint, service name)
      - Cache provider and live statistics
      - Circuit breaker states for all registered providers
      - Rate limit configuration
    """
    status: dict = {
        "service":     Config.APP_NAME,
        "version":     Config.VERSION,
        "environment": Config.ENV,

        "feature_flags": {
            "metrics":         Config.ENABLE_METRICS,
            "tracing":         Config.ENABLE_TRACING,
            "cache":           Config.ENABLE_CACHE,
            "rate_limit":      Config.ENABLE_RATE_LIMIT,
            "circuit_breaker": Config.ENABLE_CIRCUIT_BREAKER,
        },

        "logging": {
            "format":    "json",
            "level":     "DEBUG" if Config.DEBUG else "INFO",
            "namespace": Config.PROMETHEUS_NAMESPACE,
        },

        "tracing": {
            "enabled":       Config.ENABLE_TRACING,
            "service_name":  Config.OTEL_SERVICE_NAME,
            "otlp_endpoint": Config.OTLP_ENDPOINT or "console (debug only)",
            "propagator":    "W3C TraceContext + W3C Baggage",
        },

        "metrics": {
            "enabled":   Config.ENABLE_METRICS,
            "namespace": Config.PROMETHEUS_NAMESPACE,
            "endpoint":  "/metrics",
        },

        "rate_limit": {
            "enabled":          Config.ENABLE_RATE_LIMIT,
            "requests_per_window": Config.RATE_LIMIT_REQUESTS,
            "window_seconds":   Config.RATE_LIMIT_WINDOW,
            "burst":            Config.RATE_LIMIT_BURST,
            "key_strategies":   ["organization", "api_key", "ip"],
        },

        "slow_thresholds_ms": {
            "request":  Config.SLOW_REQUEST_THRESHOLD_MS,
            "stage":    Config.SLOW_STAGE_THRESHOLD_MS,
            "provider": Config.SLOW_PROVIDER_THRESHOLD_MS,
        },
    }

    # Cache statistics
    if Config.ENABLE_CACHE:
        try:
            from app.cache.provider import get_cache_provider
            cache = get_cache_provider()
            status["cache"] = {
                "enabled":  True,
                "provider": Config.CACHE_PROVIDER,
                "ttl":      Config.CACHE_TTL,
                "ttl_overrides": {
                    "provider_health":        Config.CACHE_TTL_PROVIDER_HEALTH,
                    "model_list":             Config.CACHE_TTL_MODEL_LIST,
                    "config":                 Config.CACHE_TTL_CONFIG,
                    "prompt_templates":       Config.CACHE_TTL_PROMPT_TEMPLATES,
                    "classification_schemas": Config.CACHE_TTL_CLASSIFICATION_SCHEMAS,
                },
                "stats": cache.stats(),
            }
        except Exception as exc:
            status["cache"] = {"enabled": True, "error": str(exc)}
    else:
        status["cache"] = {"enabled": False}

    # Circuit breaker states
    if Config.ENABLE_CIRCUIT_BREAKER:
        try:
            from app.observability.circuit_breaker import CircuitBreakerRegistry
            status["circuit_breakers"] = {
                "enabled":   True,
                "config": {
                    "failure_threshold":    Config.CB_FAILURE_THRESHOLD,
                    "recovery_timeout_s":   Config.CB_RECOVERY_TIMEOUT,
                    "half_open_max_calls":  Config.CB_HALF_OPEN_MAX_CALLS,
                },
                "providers": CircuitBreakerRegistry.snapshot(),
            }
        except Exception as exc:
            status["circuit_breakers"] = {"enabled": True, "error": str(exc)}
    else:
        status["circuit_breakers"] = {"enabled": False}

    return JSONResponse(content=status)
