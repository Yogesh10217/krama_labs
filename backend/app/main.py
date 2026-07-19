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
from app.core.logging import setup_logging, CorrelationIdMiddleware
from app.core.exceptions import (
    KramaException,
    krama_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)
from app.api.router import api_router, v1_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events manager for the application."""
    logger.info(f"Starting Krama AI Backend (env: {Config.ENV}, debug: {Config.DEBUG})")
    
    # Ensure upload and results directories exist
    os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
    os.makedirs(Config.RESULTS_DIR, exist_ok=True)
    
    yield
    
    logger.info("Stopping Krama AI Backend")


def create_app() -> FastAPI:
    """FastAPI application factory."""
    # 1. Setup centralized logging
    setup_logging()

    # 2. Validate application configuration
    Config.validate()

    app = FastAPI(
        title=Config.APP_NAME,
        description="Production refactored claims processing document intelligence API",
        version=Config.VERSION,
        lifespan=lifespan,
    )

    # 3. Add middlewares (Logging/Request-ID correlation first, then CORS)
    app.add_middleware(CorrelationIdMiddleware)
    
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
        logger.info(f"Mounted static frontend from {workspace_root}")
    else:
        logger.warning(f"Static index.html not found at workspace root {workspace_root}")

    return app


# Expose default app symbol for Uvicorn (app.main:app)
app = create_app()


if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server via main.py execution")
    uvicorn.run("app.main:app", host=Config.HOST, port=Config.PORT, reload=Config.DEBUG)
