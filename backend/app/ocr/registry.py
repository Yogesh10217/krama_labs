"""OCR engine registry and factory.

Resolves the configured OCR_PROVIDER to a concrete OCREngine instance.
Supports lazy initialization - engines are created on first request.
"""
import logging
from typing import Optional
from app.ocr.base import OCREngine
from app.core.config import Config
from app.core.exceptions import OCRProviderUnavailableException

logger = logging.getLogger(__name__)

# Module-level engine cache for process-local lazy singleton
_engine_cache: dict[str, OCREngine] = {}


def get_ocr_engine(provider: Optional[str] = None) -> OCREngine:
    """Get or create the OCR engine for the given provider.
    
    Args:
        provider: Engine name (e.g. 'paddle'). Defaults to Config.OCR_PROVIDER.
    
    Returns:
        OCREngine instance.
    
    Raises:
        ImportError: If the provider's dependencies are not installed.
        ValueError: If the provider name is not recognized.
    """
    provider = provider or getattr(Config, "OCR_PROVIDER", "paddle")
    
    if provider in _engine_cache:
        return _engine_cache[provider]
    
    try:
        engine = _create_engine(provider)
        _engine_cache[provider] = engine
        return engine
    except ImportError as e:
        logger.error(f"Failed to initialize OCR provider '{provider}': {e}")
        raise OCRProviderUnavailableException(f"OCR provider '{provider}' is not available: {e}")


def _create_engine(provider: str) -> OCREngine:
    """Instantiate an OCR engine by provider name."""
    if provider == "paddle":
        from app.ocr.paddle_engine import PaddleOCREngine
        return PaddleOCREngine(
            lang=getattr(Config, "OCR_LANG", "en"),
            use_gpu=getattr(Config, "OCR_USE_GPU", False),
        )
    else:
        raise ValueError(f"Unknown OCR provider: '{provider}'. Supported: paddle")


def clear_engine_cache() -> None:
    """Clear cached engines. Useful for testing."""
    _engine_cache.clear()
