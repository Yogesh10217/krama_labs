"""
app/cache/keys.py — Phase 11 Cache Key Definitions

Typed cache key constants with per-category TTL policies.
Explicit invalidation policy per category documented inline.

Document data MUST NOT use these keys. Never add document_id-based keys here.
"""

from __future__ import annotations

from app.core.config import Config


class CacheKey:
    """
    Typed cache key constants.

    All keys are module-level strings or callable builders so callers
    never construct raw strings. This ensures consistent key naming
    across the codebase.
    """

    # ── Provider health ────────────────────────────────────────────────────
    # Invalidation: expire automatically after CACHE_TTL_PROVIDER_HEALTH (30s)
    # Manual invalidation: call cache.delete(PROVIDER_HEALTH(provider)) when
    #   circuit breaker state changes.
    PROVIDER_HEALTH          = staticmethod(lambda provider: f"provider_health:{provider}")

    # ── Model lists ────────────────────────────────────────────────────────
    # Invalidation: expire automatically after CACHE_TTL_MODEL_LIST (600s).
    # Manual invalidation: cache.delete(MODEL_LIST(provider)) after a provider
    #   upgrade or when the model list API returns an empty list.
    MODEL_LIST               = staticmethod(lambda provider: f"model_list:{provider}")

    # ── Application config ─────────────────────────────────────────────────
    # Invalidation: expire after CACHE_TTL_CONFIG (3600s).
    # Manual invalidation: cache.delete(CONFIG) on runtime config reload.
    CONFIG                   = "config:global"

    # ── Prompt templates ───────────────────────────────────────────────────
    # Invalidation: expire after CACHE_TTL_PROMPT_TEMPLATES (3600s).
    # Manual invalidation: cache.delete(PROMPT_TEMPLATE(name)) when template
    #   is updated in the data store.
    PROMPT_TEMPLATE          = staticmethod(lambda name: f"prompt_template:{name}")
    PROMPT_TEMPLATES_ALL     = "prompt_templates:all"

    # ── Classification schemas ─────────────────────────────────────────────
    # Invalidation: expire after CACHE_TTL_CLASSIFICATION_SCHEMAS (3600s).
    # Manual invalidation: cache.delete(CLASSIFICATION_SCHEMA(doc_type)) when
    #   schema definition changes.
    CLASSIFICATION_SCHEMA    = staticmethod(lambda doc_type: f"classification_schema:{doc_type}")
    CLASSIFICATION_SCHEMAS_ALL = "classification_schemas:all"


class CacheTTL:
    """
    Per-category TTL values sourced from Config.
    Call CacheTTL.for_key(key) to get the TTL for a given key prefix.
    """

    PROVIDER_HEALTH           = Config.CACHE_TTL_PROVIDER_HEALTH
    MODEL_LIST                = Config.CACHE_TTL_MODEL_LIST
    CONFIG                    = Config.CACHE_TTL_CONFIG
    PROMPT_TEMPLATES          = Config.CACHE_TTL_PROMPT_TEMPLATES
    CLASSIFICATION_SCHEMAS    = Config.CACHE_TTL_CLASSIFICATION_SCHEMAS
    DEFAULT                   = Config.CACHE_TTL

    @classmethod
    def for_key(cls, key: str) -> int:
        """Return appropriate TTL for a cache key based on its prefix."""
        if key.startswith("provider_health:"):
            return cls.PROVIDER_HEALTH
        if key.startswith("model_list:"):
            return cls.MODEL_LIST
        if key.startswith("config:"):
            return cls.CONFIG
        if key.startswith("prompt_template"):
            return cls.PROMPT_TEMPLATES
        if key.startswith("classification_schema"):
            return cls.CLASSIFICATION_SCHEMAS
        return cls.DEFAULT
