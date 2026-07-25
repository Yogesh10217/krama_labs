import time
from typing import Tuple
from app.core.config import Config

class RateLimiter:
    """
    Token bucket rate limiter using Redis.
    """
    def __init__(self, redis_client=None):
        self.redis = redis_client

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        """
        Returns (is_allowed, remaining_requests)
        """
        if not self.redis:
            return True, max_requests
            
        current_time = int(time.time())
        window_start = current_time - window_seconds
        
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(current_time): current_time})
        pipe.expire(key, window_seconds)
        
        _, request_count, _, _ = pipe.execute()
        
        # request_count is the number of requests before this one was added
        if request_count > max_requests:
            return False, 0
            
        return True, max_requests - request_count
