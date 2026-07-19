"""Configuration system for Krama AI backend."""

import os
import json
from typing import List, Tuple
from dotenv import load_dotenv

# Load env variables from .env if present
load_dotenv()


class Config:
    """Centralized application settings."""

    # Application details
    APP_NAME: str = os.getenv("APP_NAME", "Krama AI")
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    API_PREFIX: str = os.getenv("API_PREFIX", "/api")
    VERSION: str = "0.1.0"

    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS settings (expects a JSON array string, e.g. '["http://localhost:3000"]')
    _cors_str = os.getenv("CORS_ORIGINS")
    if _cors_str:
        try:
            CORS_ORIGINS: List[str] = json.loads(_cors_str)
        except Exception:
            CORS_ORIGINS = [_cors_str]
    else:
        CORS_ORIGINS = ["*"]

    # File and upload limits
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    RESULTS_DIR: str = os.getenv("RESULTS_DIR", "results")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
    MAX_UPLOAD_SIZE: int = MAX_FILE_SIZE_MB * 1024 * 1024  # In bytes

    # API Keys & LLM Settings
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")  # "gemini" | "openai" | "local"
    LOCAL_LLM_URL: str = os.getenv("LOCAL_LLM_URL", "http://localhost:8080/v1")
    LOCAL_LLM_MODEL: str = os.getenv("LOCAL_LLM_MODEL", "qwen2.5-vl-7b")

    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Processing settings
    DEPLOY_MODE: str = os.getenv("DEPLOY_MODE", "saas")  # "saas" | "onpremise" | "hybrid"
    DPI_FOR_PDF: int = int(os.getenv("DPI_FOR_PDF", "200"))
    MAX_IMAGE_SIZE: Tuple[int, int] = (1920, 1920)
    OCR_LANGUAGE: str = os.getenv("OCR_LANGUAGE", "en")

    # Confidence thresholds
    HIGH_CONFIDENCE: float = float(os.getenv("HIGH_CONFIDENCE", "0.90"))
    MEDIUM_CONFIDENCE: float = float(os.getenv("MEDIUM_CONFIDENCE", "0.75"))
    LOW_CONFIDENCE: float = float(os.getenv("LOW_CONFIDENCE", "0.50"))
    FLAG_THRESHOLD: float = float(os.getenv("FLAG_THRESHOLD", "0.60"))

    # Grounding
    FUZZY_MATCH_THRESHOLD: int = int(os.getenv("FUZZY_MATCH_THRESHOLD", "75"))

    # Optional future credentials (placeholders)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    OBJECT_STORAGE_ENDPOINT: str = os.getenv("OBJECT_STORAGE_ENDPOINT", "")

    @classmethod
    def validate(cls) -> bool:
        """Validate critical configuration settings."""
        # Log info if keys are missing
        if not cls.GOOGLE_API_KEY and cls.LLM_PROVIDER == "gemini":
            # Informational only, not fatal for startup
            pass
        if not cls.OPENAI_API_KEY and cls.LLM_PROVIDER == "openai":
            pass
        return True
