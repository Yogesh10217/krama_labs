"""Configuration module for Document Intelligence backend."""

import os
from typing import Tuple
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Production configuration."""

    # API Keys
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # LLM Provider: "gemini" | "openai" | "local"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    LOCAL_LLM_URL: str = os.getenv("LOCAL_LLM_URL", "http://localhost:8080/v1")
    LOCAL_LLM_MODEL: str = os.getenv("LOCAL_LLM_MODEL", "qwen2.5-vl-7b")

    # Model settings
    GEMINI_MODEL: str = "gemini-2.0-flash"
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Deployment mode: "saas" | "onpremise" | "hybrid"
    DEPLOY_MODE: str = os.getenv("DEPLOY_MODE", "saas")

    # Processing settings
    DPI_FOR_PDF: int = 200
    MAX_IMAGE_SIZE: Tuple[int, int] = (1920, 1920)
    OCR_LANGUAGE: str = "en"

    # Confidence thresholds
    HIGH_CONFIDENCE: float = 0.90
    MEDIUM_CONFIDENCE: float = 0.75
    LOW_CONFIDENCE: float = 0.50
    FLAG_THRESHOLD: float = 0.60

    # Grounding
    FUZZY_MATCH_THRESHOLD: int = 75

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    RESULTS_DIR: str = os.getenv("RESULTS_DIR", "results")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "20"))

    @classmethod
    def validate(cls) -> bool:
        if not cls.GOOGLE_API_KEY:
            print("INFO: GOOGLE_API_KEY not set in .env — users must provide their own key via the frontend.")
            return True  # Not fatal — frontend can pass key
        return True
