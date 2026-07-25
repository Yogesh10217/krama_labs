import json
from datetime import datetime, timezone
from typing import List, Dict, Any
from app.core.config import Config

class WorkerRegistry:
    """
    Tracks active worker nodes using Redis heartbeat.
    """
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.registry_key = "krama:workers"

    def register_worker(self, worker_id: str, metadata: Dict[str, Any], ttl: int = 30) -> None:
        if not self.redis:
            return
            
        now = datetime.now(timezone.utc).isoformat()
        metadata["last_heartbeat"] = now
        
        self.redis.hset(self.registry_key, worker_id, json.dumps(metadata))
        # Use a separate expiring key for TTL
        self.redis.setex(f"worker_ttl:{worker_id}", ttl, "1")

    def get_active_workers(self) -> List[Dict[str, Any]]:
        if not self.redis:
            return []
            
        workers_raw = self.redis.hgetall(self.registry_key)
        active_workers = []
        
        for worker_id, meta_str in workers_raw.items():
            # Check if TTL key exists
            if self.redis.exists(f"worker_ttl:{worker_id}"):
                active_workers.append(json.loads(meta_str))
            else:
                # Clean up dead worker
                self.redis.hdel(self.registry_key, worker_id)
                
        return active_workers
