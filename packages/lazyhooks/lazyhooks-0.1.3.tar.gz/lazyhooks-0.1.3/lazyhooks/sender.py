import asyncio
import hmac
import hashlib
import json
import time
import uuid
import aiohttp
from typing import Dict, Any, Optional
from .storage.base import BaseStorage, WebhookEvent

class WebhookSender:
    def __init__(self, signing_secret: str, storage: Optional[BaseStorage] = None, default_timeout: float = 10.0):
        self.signing_secret = signing_secret
        self.storage = storage
        self.default_timeout = default_timeout
        self.retry_delays = [60, 300, 1800, 3600]

    def _sign_payload(self, payload_body: bytes) -> str:
        return hmac.new(
            self.signing_secret.encode(),
            payload_body,
            hashlib.sha256
        ).hexdigest()

    async def send(self, url: str, payload: Dict[str, Any], schedule_at: Optional[float] = None, headers: Optional[Dict[str, str]] = None, timeout: Optional[float] = None) -> str:
        """
        Sends a webhook. Returns the Event ID.
        :param schedule_at: Timestamp (float) to schedule the webhook for. Requires storage.
        :param headers: Optional dictionary of custom headers.
        :param timeout: Optional timeout in seconds (overrides default).
        """
        if schedule_at and not self.storage:
            raise ValueError("Storage is currently required for scheduled webhooks.")

        event_id = str(uuid.uuid4())
        now = time.time()
        
        next_try = schedule_at if schedule_at else now
        
        final_timeout = timeout if timeout is not None else self.default_timeout

        event = WebhookEvent(
            id=event_id,
            url=url,
            payload=payload,
            status="pending",
            created_at=now,
            next_retry_at=next_try,
            headers=headers,
            timeout=final_timeout
        )

        if self.storage:
            await self.storage.add_event(event)

        if not schedule_at:
            await self._attempt_delivery(event)
        
        return event_id

    async def _attempt_delivery(self, event: WebhookEvent):
        payload_bytes = json.dumps(event.payload).encode()
        signature = self._sign_payload(payload_bytes)
        
        headers = {
            "Content-Type": "application/json",
            "X-Hub-Signature-256": f"sha256={signature}",
            "User-Agent": "LazyHooks-Webhook/0.1.0"
        }
        
        if event.headers:
            headers.update(event.headers)

        try:
            timeout = aiohttp.ClientTimeout(total=event.timeout)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(event.url, data=payload_bytes, headers=headers) as resp:
                    resp.raise_for_status()
                    event.status = "success"
                    event.last_error = None
                    if self.storage:
                        await self.storage.update_event(event)
                    
        except Exception as e:
            event.attempts += 1
            event.last_error = str(e)
            
            if event.attempts <= len(self.retry_delays):
                delay = self.retry_delays[event.attempts - 1]
                event.status = "failed"
                event.next_retry_at = time.time() + delay
            else:
                event.status = "dead"
            
            if self.storage:
                await self.storage.update_event(event)
            else:
                raise e

    async def retry_worker(self):
        """
        Background task to process pending retries.
        Should be run as a task: asyncio.create_task(sender.retry_worker())
        """
        if not self.storage:
            print("Warning: retry_worker called but no storage configured.")
            return

        while True:
            try:
                events = await self.storage.get_pending_events(limit=10)
                if not events:
                    await asyncio.sleep(5)
                    continue
                
                tasks = []
                for event in events:
                    tasks.append(self._attempt_delivery(event))
                
                if tasks:
                    await asyncio.gather(*tasks)
                    
            except Exception as e:
                print(f"Error in retry worker: {e}")
                await asyncio.sleep(5)

    def send_sync(self, url: str, payload: Dict[str, Any], **kwargs) -> str:
        """
        Synchronous wrapper for send().
        Creates a temporary event loop if none is running.
        WARNING: Do not use this if you are already running inside an asyncio loop.
        """
        return asyncio.run(self.send(url, payload, **kwargs))
