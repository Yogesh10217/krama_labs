"""Configuration system for Krama AI backend."""

import os
from typing import Optional
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

    # Legacy Directories
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    RESULTS_DIR: str = os.getenv("RESULTS_DIR", "./results")
    
    # CORS settings (expects a JSON array string, e.g. '["http://localhost:3000"]')
    _cors_str = os.getenv("CORS_ORIGINS")
    if _cors_str:
        try:
            CORS_ORIGINS: List[str] = json.loads(_cors_str)
        except Exception:
            CORS_ORIGINS = [_cors_str]
    else:
        CORS_ORIGINS = ["*"]

    # Phase 2: Ingestion & Upload
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
    MAX_BATCH_FILES: int = int(os.getenv("MAX_BATCH_FILES", "20"))
    MAX_BATCH_TOTAL_SIZE_MB: int = int(os.getenv("MAX_BATCH_TOTAL_SIZE_MB", "100"))
    UPLOAD_CHUNK_SIZE_BYTES: int = 1024 * 1024  # 1 MB chunk

    # Phase 3: Document Conversion & Limits
    MAX_DOCUMENT_PAGES: int = int(os.getenv("MAX_DOCUMENT_PAGES", "500"))
    MAX_PAGE_WIDTH: int = int(os.getenv("MAX_PAGE_WIDTH", "20000"))
    MAX_PAGE_HEIGHT: int = int(os.getenv("MAX_PAGE_HEIGHT", "20000"))
    MAX_PAGE_PIXELS: int = int(os.getenv("MAX_PAGE_PIXELS", "100000000")) # 100M pixels
    PDF_RENDER_DPI: int = int(os.getenv("PDF_RENDER_DPI", "200"))

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

    # Phase 4: OCR Configuration
    OCR_PROVIDER: str = os.getenv("OCR_PROVIDER", "paddle")
    
    # Extraction Config
    EXTRACTION_PROVIDER: str = os.getenv("EXTRACTION_PROVIDER", "rules")
    EXTRACTION_FALLBACK_ORDER: str = os.getenv("EXTRACTION_FALLBACK_ORDER", "rule,ollama,gemini,openai")
    EXTRACTION_TIMEOUT_SECONDS: int = int(os.getenv("EXTRACTION_TIMEOUT_SECONDS", "30"))
    EXTRACTION_RETRY_COUNT: int = int(os.getenv("EXTRACTION_RETRY_COUNT", "3"))

    # Provider Configs
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")
    
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")

    # Validation Config
    VALIDATION_PROVIDER: str = os.getenv("VALIDATION_PROVIDER", "rules")
    CLASSIFICATION_PROVIDER: str = os.getenv("CLASSIFICATION_PROVIDER", "rules")
    
    # Validation Configuration
    VALIDATION_FUZZY_THRESHOLD: float = float(os.getenv("VALIDATION_FUZZY_THRESHOLD", "85.0"))
    OCR_LANG: str = os.getenv("OCR_LANG", "en")
    OCR_USE_GPU: bool = os.getenv("OCR_USE_GPU", "False").lower() in ("true", "1", "yes")
    OCR_MIN_CONFIDENCE: float = float(os.getenv("OCR_MIN_CONFIDENCE", "0.0"))


    # Grounding
    FUZZY_MATCH_THRESHOLD: int = int(os.getenv("FUZZY_MATCH_THRESHOLD", "75"))

    # Phase 9: Workflow & Review Configuration
    AUTO_APPROVAL_THRESHOLD: float = float(os.getenv("AUTO_APPROVAL_THRESHOLD", "0.95"))
    REQUIRE_REVIEW_FOR_DOCUMENT_TYPES: str = os.getenv("REQUIRE_REVIEW_FOR_DOCUMENT_TYPES", "")
    CRITICAL_FIELDS: str = os.getenv("CRITICAL_FIELDS", "total,invoice_number,aadhaar_number,pan_number")

    # Phase 10: Async Job Execution Configuration
    JOB_QUEUE_PROVIDER: str = os.getenv("JOB_QUEUE_PROVIDER", "inmemory")
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_BACKOFF_SECONDS: int = int(os.getenv("RETRY_BACKOFF_SECONDS", "2"))
    JOB_TIMEOUT_SECONDS: int = int(os.getenv("JOB_TIMEOUT_SECONDS", "300"))
    MAX_CONCURRENT_WORKERS: int = int(os.getenv("MAX_CONCURRENT_WORKERS", "4"))
    QUEUE_NAME: str = os.getenv("QUEUE_NAME", "document-intelligence")
    WORKER_HEARTBEAT_INTERVAL_SECONDS: int = int(os.getenv("WORKER_HEARTBEAT_INTERVAL_SECONDS", "30"))
    JOB_STALE_AFTER_SECONDS: int = int(os.getenv("JOB_STALE_AFTER_SECONDS", "120"))

    # Database Settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./krama_dev.db")
    DATABASE_ECHO: bool = os.getenv("DATABASE_ECHO", "False").lower() in ("true", "1", "yes")
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))

    # ─── Phase 2: Storage Provider ───────────────────────────────────────────────
    # STORAGE_PROVIDER: which provider to use. Only "local" is active.
    STORAGE_PROVIDER: str = os.getenv("STORAGE_PROVIDER", "local")
    # STORAGE_ROOT: base directory for local filesystem storage (provider-neutral key prefix).
    # IMPORTANT: In Docker/production, mount a persistent volume here.
    # Do not rely on ephemeral container storage.
    STORAGE_ROOT: str = os.getenv("STORAGE_ROOT", "./storage")

    # ─── Phase 2: Upload Limits ──────────────────────────────────────────────────
    # Maximum size per individual uploaded file (in MB).
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
    # Maximum number of files accepted in a single batch upload request.
    MAX_BATCH_FILES: int = int(os.getenv("MAX_BATCH_FILES", "20"))
    # Maximum combined uncompressed size of all files in a batch (in MB).
    MAX_BATCH_TOTAL_SIZE_MB: int = int(os.getenv("MAX_BATCH_TOTAL_SIZE_MB", "500"))
    # Chunk size for streaming uploads in bytes (default 1 MB).
    UPLOAD_CHUNK_SIZE_BYTES: int = int(os.getenv("UPLOAD_CHUNK_SIZE_BYTES", "1048576"))

    # Derived bytes limits (not overridable separately, computed from MB settings).
    @classmethod
    def max_upload_size_bytes(cls) -> int:
        return cls.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @classmethod
    def max_batch_total_size_bytes(cls) -> int:
        return cls.MAX_BATCH_TOTAL_SIZE_MB * 1024 * 1024

    # Optional future credentials (placeholders)
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    OBJECT_STORAGE_ENDPOINT: str = os.getenv("OBJECT_STORAGE_ENDPOINT", "")

    # ─── Phase 11: Observability Feature Flags ───────────────────────────────────
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "True").lower() in ("true", "1", "yes")
    ENABLE_TRACING: bool = os.getenv("ENABLE_TRACING", "True").lower() in ("true", "1", "yes")
    ENABLE_CACHE: bool = os.getenv("ENABLE_CACHE", "True").lower() in ("true", "1", "yes")
    ENABLE_RATE_LIMIT: bool = os.getenv("ENABLE_RATE_LIMIT", "False").lower() in ("true", "1", "yes")
    ENABLE_CIRCUIT_BREAKER: bool = os.getenv("ENABLE_CIRCUIT_BREAKER", "True").lower() in ("true", "1", "yes")

    # ─── Phase 11: Prometheus ────────────────────────────────────────────────────
    PROMETHEUS_NAMESPACE: str = os.getenv("PROMETHEUS_NAMESPACE", "krama")
    PROMETHEUS_MULTIPROC_DIR: str = os.getenv("PROMETHEUS_MULTIPROC_DIR", "")

    # ─── Phase 11: OpenTelemetry Tracing ─────────────────────────────────────────
    OTLP_ENDPOINT: str = os.getenv("OTLP_ENDPOINT", "")
    OTLP_INSECURE: bool = os.getenv("OTLP_INSECURE", "True").lower() in ("true", "1", "yes")
    OTEL_SERVICE_NAME: str = os.getenv("OTEL_SERVICE_NAME", "krama-ai-backend")

    # ─── Phase 11: Cache ─────────────────────────────────────────────────────────
    # Supported: "inmemory" | "redis"
    CACHE_PROVIDER: str = os.getenv("CACHE_PROVIDER", "inmemory")
    # Default TTL in seconds for cached values
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))
    # Per-category TTL overrides (seconds)
    CACHE_TTL_PROVIDER_HEALTH: int = int(os.getenv("CACHE_TTL_PROVIDER_HEALTH", "30"))
    CACHE_TTL_MODEL_LIST: int = int(os.getenv("CACHE_TTL_MODEL_LIST", "600"))
    CACHE_TTL_CONFIG: int = int(os.getenv("CACHE_TTL_CONFIG", "3600"))
    CACHE_TTL_PROMPT_TEMPLATES: int = int(os.getenv("CACHE_TTL_PROMPT_TEMPLATES", "3600"))
    CACHE_TTL_CLASSIFICATION_SCHEMAS: int = int(os.getenv("CACHE_TTL_CLASSIFICATION_SCHEMAS", "3600"))

    # ─── Phase 11: Rate Limiting ─────────────────────────────────────────────────
    # Requests allowed per RATE_LIMIT_WINDOW seconds (per-organization / per-IP)
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    # Burst: extra requests above the steady-state limit before throttling
    RATE_LIMIT_BURST: int = int(os.getenv("RATE_LIMIT_BURST", "20"))

    # ─── Phase 11: Circuit Breaker ───────────────────────────────────────────────
    CB_FAILURE_THRESHOLD: int = int(os.getenv("CB_FAILURE_THRESHOLD", "5"))
    CB_RECOVERY_TIMEOUT: int = int(os.getenv("CB_RECOVERY_TIMEOUT", "60"))
    CB_HALF_OPEN_MAX_CALLS: int = int(os.getenv("CB_HALF_OPEN_MAX_CALLS", "3"))

    # ─── Phase 11: Slow-request / slow-stage thresholds (ms) ────────────────────
    SLOW_REQUEST_THRESHOLD_MS: int = int(os.getenv("SLOW_REQUEST_THRESHOLD_MS", "2000"))
    SLOW_STAGE_THRESHOLD_MS: int = int(os.getenv("SLOW_STAGE_THRESHOLD_MS", "5000"))
    SLOW_PROVIDER_THRESHOLD_MS: int = int(os.getenv("SLOW_PROVIDER_THRESHOLD_MS", "3000"))

    # ─── Phase 12: Security & Authentication ─────────────────────────────────────
    ENABLE_AUTH: bool = os.getenv("ENABLE_AUTH", "False").lower() in ("true", "1", "yes")
    ENABLE_RBAC: bool = os.getenv("ENABLE_RBAC", "False").lower() in ("true", "1", "yes")
    ENABLE_API_KEYS: bool = os.getenv("ENABLE_API_KEYS", "False").lower() in ("true", "1", "yes")
    ENABLE_REDIS: bool = os.getenv("ENABLE_REDIS", "False").lower() in ("true", "1", "yes")
    ENABLE_SECRET_PROVIDER: bool = os.getenv("ENABLE_SECRET_PROVIDER", "False").lower() in ("true", "1", "yes")

    # JWT Settings
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES", "30"))
    JWT_REFRESH_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7"))

    # Secret Provider Settings
    SECRET_PROVIDER: str = os.getenv("SECRET_PROVIDER", "environment")  # "environment" | "vault"
    VAULT_URL: str = os.getenv("VAULT_URL", "http://localhost:8200")
    VAULT_TOKEN: str = os.getenv("VAULT_TOKEN", "")

    # Security Limits
    MAX_REQUEST_BODY_SIZE_MB: int = int(os.getenv("MAX_REQUEST_BODY_SIZE_MB", "50"))
    SECURITY_HEADERS_ENABLED: bool = os.getenv("SECURITY_HEADERS_ENABLED", "True").lower() in ("true", "1", "yes")

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
