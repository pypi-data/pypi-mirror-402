import asyncio
from typing import Dict, Any, Optional, Union, List
from .sender import WebhookSender
from .storage.base import BaseStorage, WebhookEvent

class SyncWebhookSender:
    """
    Synchronous wrapper for WebhookSender.
    
    This class enables usage of LazyHooks in synchronous environments (scripts, 
    standard Django/Flask views) by managing its own event loop execution.
    
    WARNING: Do NOT use this class if your code is already running inside an 
    asyncio event loop (e.g. FastAPI, Quart). Use WebhookSender instead.
    """
    def __init__(self, signing_secret: str, storage: Union[BaseStorage, str, None] = None, default_timeout: float = 10.0):
        self._sender = WebhookSender(signing_secret, storage, default_timeout)

    def send(self, url: str, payload: Dict[str, Any], schedule_at: Optional[float] = None, headers: Optional[Dict[str, str]] = None, timeout: Optional[float] = None) -> str:
        """
        Sends a webhook synchronously.
        """
        return asyncio.run(self._sender.send(url, payload, schedule_at, headers, timeout))

    def get_pending_events(self, limit: int = 10) -> List[WebhookEvent]:
        """
        Get pending events synchronously.
        Requires storage.
        """
        if not self._sender.storage:
             return []
        return asyncio.run(self._sender.storage.get_pending_events(limit))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Async sender doesn't strictly need close(), but aiohttp session might if we kept one open.
        # Currently WebhookSender opens a session per request, so clean up is automatic.
        pass
