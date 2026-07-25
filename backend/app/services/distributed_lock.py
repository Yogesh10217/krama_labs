from contextlib import contextmanager
from typing import Generator
import time
from app.core.config import Config

class DistributedLock:
    """
    A simple distributed lock using Redis.
    Falls back to a no-op if Redis is not configured.
    """
    def __init__(self, redis_client=None):
        self.redis = redis_client
        
    @contextmanager
    def acquire(self, lock_name: str, acquire_timeout: int = 10, lock_timeout: int = 60) -> Generator[bool, None, None]:
        if not self.redis:
            # Fallback for dev mode
            yield True
            return
            
        lock_key = f"lock:{lock_name}"
        identifier = str(time.time())
        end = time.time() + acquire_timeout
        acquired = False
        
        try:
            while time.time() < end:
                if self.redis.set(lock_key, identifier, nx=True, ex=lock_timeout):
                    acquired = True
                    break
                time.sleep(0.1)
                
            yield acquired
            
        finally:
            if acquired:
                # Use Lua script to safely release lock
                lua_script = """
                if redis.call("get",KEYS[1]) == ARGV[1] then
                    return redis.call("del",KEYS[1])
                else
                    return 0
                end
                """
                self.redis.eval(lua_script, 1, lock_key, identifier)
