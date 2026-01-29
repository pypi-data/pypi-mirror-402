import json
import time
import asyncio
from typing import List, Optional, Union
from .base import BaseStorage, WebhookEvent

try:
    import redis.asyncio as redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

class RedisStorage(BaseStorage):
    """
    Redis-backed storage for webhooks using redis-py (asyncio).
    
    Data Schema:
    - events:{id} -> Hash map of event data
    - lazyhooks:pending -> Sorted Set (ZSET) of event IDs scored by next_retry_at
    """
    def __init__(self, url: str, key_prefix: str = "lazyhooks:", ttl: int = 86400):
        if not HAS_REDIS:
            raise ImportError("redis-py is required for RedisStorage. Install with 'pip install redis'.")
        
        self.redis = redis.from_url(url, decode_responses=True)
        self.prefix = key_prefix
        self.ttl = ttl

    async def add_event(self, event: WebhookEvent) -> None:
        event_key = f"{self.prefix}events:{event.id}"
        pending_key = f"{self.prefix}pending"
        
        # Serialize headers and payload
        data = {
            "id": event.id,
            "url": event.url,
            "payload": json.dumps(event.payload),
            "status": event.status,
            "attempts": str(event.attempts),
            "created_at": str(event.created_at),
            "next_retry_at": str(event.next_retry_at),
            "last_error": event.last_error or "",
            "headers": json.dumps(event.headers) if event.headers else "",
            "timeout": str(event.timeout)
        }
        
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.hset(event_key, mapping=data)
            pipe.expire(event_key, self.ttl)
            if event.status in ("pending", "failed"):
                pipe.zadd(pending_key, {event.id: event.next_retry_at})
            await pipe.execute()

    async def get_pending_events(self, limit: int = 100) -> List[WebhookEvent]:
        now = time.time()
        pending_key = f"{self.prefix}pending"
        
        # Get pending events due for retry
        event_ids = await self.redis.zrangebyscore(pending_key, min=0, max=now, start=0, num=limit)
        
        if not event_ids:
            return []

        results = []
        async with self.redis.pipeline(transaction=True) as pipe:
             # Optimistically move them to "processing" state by removing from pending?
             # Or just allow logic to pick them up. The Queue pattern usually grabs them.
             # Here we just read them. The sender will update them to 'success' or new 'failed' time.
             # But if sender crashes, we need them to persist. 
             # For a simple retry worker, we can just leave them in ZSET but update their score?
             # Better: Remove from ZSET so other workers don't pick them up immediately.
             pipe.zrem(pending_key, *event_ids)
             for eid in event_ids:
                 pipe.hgetall(f"{self.prefix}events:{eid}")
             
             responses = await pipe.execute()
             # responses[0] is zrem result
             # responses[1:] are hgetall results
             
             raw_events = responses[1:]
        
        for i, raw in enumerate(raw_events):
            if not raw:
                continue # Expired or gone
            
            # Reconstruct
            try:
                evt = WebhookEvent(
                    id=raw["id"],
                    url=raw["url"],
                    payload=json.loads(raw["payload"]),
                    status="processing", # Mark as in-flight in memory
                    attempts=int(raw["attempts"]),
                    created_at=float(raw["created_at"]),
                    next_retry_at=float(raw["next_retry_at"]),
                    last_error=raw.get("last_error") or None,
                    headers=json.loads(raw["headers"]) if raw.get("headers") else None,
                    timeout=float(raw.get("timeout", 10.0))
                )
                results.append(evt)
            except Exception:
                # Corrupt data?
                continue
                
        return results

    async def update_event(self, event: WebhookEvent) -> None:
        event_key = f"{self.prefix}events:{event.id}"
        pending_key = f"{self.prefix}pending"
        
        data = {
            "status": event.status,
            "attempts": str(event.attempts),
            "next_retry_at": str(event.next_retry_at),
            "last_error": event.last_error or ""
        }
        
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.hset(event_key, mapping=data)
            
            if event.status == "failed":
                # Re-queue for next retry
                pipe.zadd(pending_key, {event.id: event.next_retry_at})
            elif event.status in ("success", "dead"):
                # Ensure it's removed from pending
                pipe.zrem(pending_key, event.id)
                # We do NOT delete the event hash immediately, let TTL handle it
                # so we can inspect logs/status.
            
            await pipe.execute()

    async def get_event(self, event_id: str) -> Optional[WebhookEvent]:
        raw = await self.redis.hgetall(f"{self.prefix}events:{event_id}")
        if not raw:
            return None
            
        return WebhookEvent(
            id=raw["id"],
            url=raw["url"],
            payload=json.loads(raw["payload"]),
            status=raw["status"],
            attempts=int(raw["attempts"]),
            created_at=float(raw["created_at"]),
            next_retry_at=float(raw["next_retry_at"]),
            last_error=raw.get("last_error") or None,
            headers=json.loads(raw["headers"]) if raw.get("headers") else None,
            timeout=float(raw.get("timeout", 10.0))
        )
