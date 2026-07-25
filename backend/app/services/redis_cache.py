import json
from typing import Any, Optional
import redis
from app.services.cache_interface import CacheInterface
from app.core.config import Config

class RedisCache(CacheInterface):
    def __init__(self):
        # Fallback for local development if redis URL is missing
        if not Config.REDIS_URL:
            self._client = None
            self._local_cache = {}
        else:
            self._client = redis.from_url(Config.REDIS_URL, decode_responses=True)

    def get(self, key: str) -> Optional[Any]:
        if not self._client:
            val = self._local_cache.get(key)
            return json.loads(val) if val else None
            
        val = self._client.get(key)
        if val:
            return json.loads(val)
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        val_str = json.dumps(value)
        if not self._client:
            self._local_cache[key] = val_str
            return
            
        if ttl:
            self._client.setex(key, ttl, val_str)
        else:
            self._client.set(key, val_str)

    def delete(self, key: str) -> None:
        if not self._client:
            self._local_cache.pop(key, None)
            return
            
        self._client.delete(key)

    def clear(self) -> None:
        if not self._client:
            self._local_cache.clear()
            return
            
        self._client.flushdb()
