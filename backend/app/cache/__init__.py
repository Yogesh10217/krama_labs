"""
app/cache/__init__.py — Phase 11 Cache Package

Provides a provider-agnostic cache abstraction.

Active implementations:
  InMemoryCache — thread-safe, TTL-aware (used in dev/test)

Interface-only (requires Redis in env):
  RedisCache    — stub, not connected

Factory: get_cache_provider() respects CACHE_PROVIDER config.

Document data MUST NOT be cached through this layer.
Only system-level metadata is cached:
  provider health, model list, config, prompt templates,
  classification schemas.
"""

from app.cache.provider import CacheProvider, InMemoryCache, RedisCache, get_cache_provider
from app.cache.keys import CacheKey, CacheTTL

__all__ = [
    "CacheProvider",
    "InMemoryCache",
    "RedisCache",
    "get_cache_provider",
    "CacheKey",
    "CacheTTL",
]
