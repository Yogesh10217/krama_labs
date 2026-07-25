"""FastAPI Application Factory for Krama AI backend."""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import Config
from app.core.exceptions import (
    KramaException,
    krama_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)
from app.api.router import api_router, v1_router

# Phase 11: observability layer setup
from app.observability.logging import setup_logging
from app.observability.middleware import (
    CorrelationIdMiddleware,
    RequestLoggingMiddleware,
    RateLimitMiddleware,
    MetricsMiddleware,
    RequestTimingMiddleware,
)
from app.observability.tracing import setup_tracing
from app.observability.circuit_breaker import CircuitBreakerRegistry
from app.security.middleware import SecurityHeadersMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events manager for the application."""
    logger.info(
        "Starting Krama AI Backend (env=%s debug=%s metrics=%s tracing=%s cache=%s)",
        Config.ENV, Config.DEBUG,
        Config.ENABLE_METRICS, Config.ENABLE_TRACING, Config.ENABLE_CACHE,
    )

    # Ensure upload and results directories exist
    os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
    os.makedirs(Config.RESULTS_DIR, exist_ok=True)
    os.makedirs(Config.STORAGE_ROOT, exist_ok=True)

    # Phase 11: Initialize tracing provider
    if Config.ENABLE_TRACING:
        try:
            setup_tracing()
            logger.info("OpenTelemetry tracing initialized (endpoint=%s)", Config.OTLP_ENDPOINT or "console")
        except Exception as exc:
            logger.warning("Tracing setup failed (non-fatal): %s", exc)

    # Phase 11: Pre-create circuit breakers for all known providers
    if Config.ENABLE_CIRCUIT_BREAKER:
        CircuitBreakerRegistry.initialize_defaults()
        logger.info("Circuit breakers initialized for providers: %s", CircuitBreakerRegistry._PROVIDERS)

    # Phase 11: Initialize cache provider
    if Config.ENABLE_CACHE:
        try:
            from app.cache.provider import get_cache_provider
            cache = get_cache_provider()
            logger.info("Cache provider initialized: %s", Config.CACHE_PROVIDER)
        except Exception as exc:
            logger.warning("Cache initialization failed (non-fatal): %s", exc)

    yield

    logger.info("Stopping Krama AI Backend")


def create_app() -> FastAPI:
    """FastAPI application factory."""
    # 1. Setup Phase 11 structured JSON logging (replaces core logging)
    setup_logging()

    # 2. Validate application configuration
    Config.validate()

    app = FastAPI(
        title=Config.APP_NAME,
        description="Production refactored claims processing document intelligence API",
        version=Config.VERSION,
        lifespan=lifespan,
    )

    # ── Middleware stack (Phase 11 — ordered per approved spec) ──────────────
    #
    # Starlette middleware is applied in REVERSE registration order.
    # We register in reverse so the execution order becomes:
    #   Correlation → Logging → Rate Limit → Metrics → Timing → Route → Exception Handler
    #
    # Registration order (last registered = outermost = first to execute):

    # 5. RequestTimingMiddleware  (innermost observability layer)
    app.add_middleware(RequestTimingMiddleware)

    # 4. MetricsMiddleware
    if Config.ENABLE_METRICS:
        app.add_middleware(MetricsMiddleware)

    # 3. RateLimitMiddleware (optional, disabled by default)
    if Config.ENABLE_RATE_LIMIT:
        app.add_middleware(RateLimitMiddleware)

    # 2. RequestLoggingMiddleware
    app.add_middleware(RequestLoggingMiddleware)

    # 1. CorrelationIdMiddleware (outermost — sets correlation_id first)
    app.add_middleware(CorrelationIdMiddleware)

    # SecurityHeadersMiddleware
    app.add_middleware(SecurityHeadersMiddleware)

    # CORS (outermost of all — before our middleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=Config.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 4. Register exception handlers
    app.add_exception_handler(KramaException, krama_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # 5. Register routers
    # Base compatibility routes (e.g. /api/health, /api/process)
    app.include_router(api_router, prefix=Config.API_PREFIX)
    # Future versioned routes (e.g. /api/v1/health, /api/v1/process)
    app.include_router(v1_router, prefix=f"{Config.API_PREFIX}/v1")

    # 6. Mount static files for the frontend landing page (last)
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if os.path.exists(os.path.join(workspace_root, "index.html")):
        app.mount("/", StaticFiles(directory=workspace_root, html=True), name="frontend")
        logger.info("Mounted static frontend from %s", workspace_root)
    else:
        logger.warning("Static index.html not found at workspace root %s", workspace_root)

    return app


# Expose default app symbol for Uvicorn (app.main:app)
app = create_app()


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server via main.py execution")
    uvicorn.run("app.main:app", host=Config.HOST, port=Config.PORT, reload=Config.DEBUG)
