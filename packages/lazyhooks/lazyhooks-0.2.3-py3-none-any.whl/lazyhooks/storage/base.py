from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class WebhookEvent:
    id: str
    url: str
    payload: Dict[str, Any]
    status: str  # 'pending', 'success', 'failed'
    attempts: int = 0
    created_at: float = 0.0
    next_retry_at: float = 0.0
    last_error: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    timeout: float = 10.0

class BaseStorage(ABC):
    """Abstract base class for webhook persistence."""

    @abstractmethod
    async def add_event(self, event: WebhookEvent) -> None:
        """Save a new event to storage."""
        pass

    @abstractmethod
    async def get_pending_events(self, limit: int = 100) -> List[WebhookEvent]:
        """Retrieve events that are ready to be retried."""
        pass

    @abstractmethod
    async def update_event(self, event: WebhookEvent) -> None:
        """Update the status, attempts, and next_retry_at of an event."""
        pass

    @abstractmethod
    async def get_event(self, event_id: str) -> Optional[WebhookEvent]:
        """Retrieve a single event by ID."""
        pass
