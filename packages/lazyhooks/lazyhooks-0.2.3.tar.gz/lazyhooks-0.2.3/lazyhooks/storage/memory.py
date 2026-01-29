import time
from typing import List, Optional, Dict
from .base import BaseStorage, WebhookEvent

class InMemoryStorage(BaseStorage):
    """
    Ephemeral in-memory storage for testing or non-persistent use.
    Events are lost when the process exits.
    """
    def __init__(self):
        self._events: Dict[str, WebhookEvent] = {}

    async def add_event(self, event: WebhookEvent) -> None:
        self._events[event.id] = event

    async def get_pending_events(self, limit: int = 100) -> List[WebhookEvent]:
        now = time.time()
        pending = []
        for event in self._events.values():
            if event.status in ("pending", "failed") and event.next_retry_at <= now:
                pending.append(event)
            if len(pending) >= limit:
                break
        return pending

    async def update_event(self, event: WebhookEvent) -> None:
        if event.id in self._events:
            self._events[event.id] = event

    async def get_event(self, event_id: str) -> Optional[WebhookEvent]:
        return self._events.get(event_id)
