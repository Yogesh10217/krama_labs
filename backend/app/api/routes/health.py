"""Health check endpoints for the backend."""

import os
import logging
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.core.config import Config

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/live", status_code=status.HTTP_200_OK)
async def live():
    """Liveness probe: verifies if the server process is alive."""
    return {"status": "ok", "service": Config.APP_NAME}


@router.get("/ready", status_code=status.HTTP_200_OK)
async def ready():
    """Readiness probe: verifies if required resources are ready for requests."""
    checks = {}
    
    # 1. Config Validation
    try:
        Config.validate()
        checks["config"] = True
    except Exception as e:
        logger.error(f"Readiness check failed - Config invalid: {e}")
        checks["config"] = False
        
    # 2. Directory Access Checks
    for name, directory in [("upload_dir", Config.UPLOAD_DIR), ("results_dir", Config.RESULTS_DIR)]:
        try:
            os.makedirs(directory, exist_ok=True)
            # Try to write a temp check file
            test_file = os.path.join(directory, ".readiness_test")
            with open(test_file, "w") as f:
                f.write("ready")
            os.remove(test_file)
            checks[name] = True
        except Exception as e:
            logger.error(f"Readiness check failed - Directory '{directory}' inaccessible: {e}")
            checks[name] = False

    # Check overall readiness
    is_ready = all(checks.values())
    if is_ready:
        return {
            "status": "ready",
            "service": Config.APP_NAME,
            "checks": checks
        }
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "service": Config.APP_NAME,
                "checks": checks
            }
        )


@router.get("/health", status_code=status.HTTP_200_OK)
async def health():
    """Health check: provides diagnostic metadata about service features and options."""
    # Check if optional modules are installed
    has_paddleocr = False
    try:
        import paddleocr
        has_paddleocr = True
    except ImportError:
        pass

    has_pymupdf = False
    try:
        import fitz
        has_pymupdf = True
    except ImportError:
        pass

    has_genai = False
    try:
        import google.generativeai
        has_genai = True
    except ImportError:
        pass

    has_openai = False
    try:
        import openai
        has_openai = True
    except ImportError:
        pass

    return {
        "status": "healthy",
        "service": Config.APP_NAME,
        "version": Config.VERSION,
        "environment": Config.ENV,
        "features": {
            "ocr_engine": "PaddleOCR v4" if has_paddleocr else "unavailable",
            "pdf_converter": "PyMuPDF" if has_pymupdf else "unavailable",
            "vlm_gemini": "available" if has_genai else "unavailable",
            "llm_openai": "available" if has_openai else "unavailable",
            "chat_feature": "enabled" if (Config.GOOGLE_API_KEY or Config.OPENAI_API_KEY) else "offline_only",
            "llm_provider": Config.LLM_PROVIDER,
            "deploy_mode": Config.DEPLOY_MODE
        }
    }
