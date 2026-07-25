"""
app/cache/provider.py — Phase 11 Cache Provider Abstraction

Abstract interface + implementations:
  InMemoryCache — active, thread-safe, TTL-aware dict-based cache
  RedisCache    — interface-only stub (Redis not connected in Phase 11)

Factory:
  get_cache_provider() — returns singleton based on CACHE_PROVIDER config

Document data MUST NOT be cached here.
Only system-level metadata caching is permitted.
"""

from __future__ import annotations

import threading
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

from app.core.config import Config


# ---------------------------------------------------------------------------
# Abstract interface
# ---------------------------------------------------------------------------

class CacheProvider(ABC):
    """
    Abstract cache interface. All implementations must be thread-safe.

    Type contract:
      get() returns None on miss or expired entry.
      set() with ttl=None uses the cache's default TTL.
    """

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Return cached value or None on miss."""

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store value with optional TTL (seconds)."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove a cache entry."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all entries."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Return True if key exists and has not expired."""

    @abstractmethod
    def stats(self) -> Dict[str, Any]:
        """Return cache statistics (hits, misses, size, etc.)."""

    def get_or_set(self, key: str, factory, ttl: Optional[int] = None) -> Any:
        """
        Get cached value, or compute and cache it via factory().

        factory is called with no arguments. Its return value is stored.
        This is a convenience wrapper — subclasses may override for atomicity.
        """
        value = self.get(key)
        if value is not None:
            return value
        value = factory()
        if value is not None:
            self.set(key, value, ttl=ttl)
        return value


# ---------------------------------------------------------------------------
# InMemoryCache — active implementation
# ---------------------------------------------------------------------------

class _CacheEntry:
    __slots__ = ("value", "expires_at")

    def __init__(self, value: Any, ttl: int) -> None:
        self.value      = value
        self.expires_at = time.monotonic() + ttl

    def is_expired(self) -> bool:
        return time.monotonic() > self.expires_at


class InMemoryCache(CacheProvider):
    """
    Thread-safe in-process cache with TTL eviction.

    Eviction: lazy (expired entries are removed on access).
    Not suitable for multi-process deployments — each process has its own
    cache state. For multi-process, switch to RedisCache.
    """

    def __init__(self, default_ttl: int = 300) -> None:
        self._default_ttl   = default_ttl
        self._store:         Dict[str, _CacheEntry] = {}
        self._lock           = threading.Lock()
        self._hits           = 0
        self._misses         = 0
        self._sets           = 0
        self._deletes        = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None
            if entry.is_expired():
                del self._store[key]
                self._misses += 1
                return None
            self._hits += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        effective_ttl = ttl if ttl is not None else self._default_ttl
        with self._lock:
            self._store[key] = _CacheEntry(value, effective_ttl)
            self._sets += 1

    def delete(self, key: str) -> None:
        with self._lock:
            if key in self._store:
                del self._store[key]
                self._deletes += 1

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def exists(self, key: str) -> bool:
        with self._lock:
            entry = self._store.get(key)
            if entry is None or entry.is_expired():
                return False
            return True

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            # Count live vs expired entries
            now   = time.monotonic()
            live  = sum(1 for e in self._store.values() if not e.is_expired())
            total = len(self._store)
        return {
            "provider":  "inmemory",
            "size":      live,
            "total":     total,
            "hits":      self._hits,
            "misses":    self._misses,
            "sets":      self._sets,
            "deletes":   self._deletes,
            "hit_rate":  (
                round(self._hits / (self._hits + self._misses), 4)
                if (self._hits + self._misses) > 0 else 0.0
            ),
        }


# ---------------------------------------------------------------------------
# RedisCache — interface stub (Phase 11: not connected)
# ---------------------------------------------------------------------------

class RedisCache(CacheProvider):
    """
    Redis-backed cache — interface stub for Phase 11.

    This class satisfies the CacheProvider contract but does not connect
    to Redis. Activate by setting CACHE_PROVIDER=redis and providing
    REDIS_URL in the environment. Full Redis implementation is Phase 12+.
    """

    def __init__(self) -> None:
        import logging
        logging.getLogger(__name__).warning(
            "RedisCache is an interface stub. "
            "Set CACHE_PROVIDER=inmemory or implement the Redis backend."
        )
        self._fallback = InMemoryCache(default_ttl=Config.CACHE_TTL)

    def get(self, key: str) -> Optional[Any]:
        return self._fallback.get(key)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self._fallback.set(key, value, ttl=ttl)

    def delete(self, key: str) -> None:
        self._fallback.delete(key)

    def clear(self) -> None:
        self._fallback.clear()

    def exists(self, key: str) -> bool:
        return self._fallback.exists(key)

    def stats(self) -> Dict[str, Any]:
        stats = self._fallback.stats()
        stats["provider"] = "redis_stub"
        return stats


# ---------------------------------------------------------------------------
# Singleton + factory
# ---------------------------------------------------------------------------

_provider_instance: Optional[CacheProvider] = None
_provider_lock = threading.Lock()


def get_cache_provider() -> CacheProvider:
    """
    Return the singleton CacheProvider based on CACHE_PROVIDER config.

    Supported: "inmemory" | "redis"
    """
    global _provider_instance
    if _provider_instance is None:
        with _provider_lock:
            if _provider_instance is None:
                if Config.CACHE_PROVIDER == "redis":
                    _provider_instance = RedisCache()
                else:
                    _provider_instance = InMemoryCache(default_ttl=Config.CACHE_TTL)
    return _provider_instance


def reset_cache_provider() -> None:
    """Reset the singleton (test utility only)."""
    global _provider_instance
    with _provider_lock:
        _provider_instance = None
