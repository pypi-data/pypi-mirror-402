import asyncio
import hmac
import hashlib
import json
import time
import uuid
import aiohttp
from typing import Dict, Any, Optional, Union, List
from .storage.base import BaseStorage, WebhookEvent
from .monitoring import MonitoringAdapter
from .exceptions import (
    WebhookError, WebhookNetworkError, WebhookTimeoutError,
    WebhookHTTPError, WebhookClientError, WebhookServerError,
    WebhookRateLimitError, WebhookBadRequestError, WebhookUnauthorizedError,
    WebhookNotFoundError
)

class WebhookSender:
    def __init__(self, signing_secret: str, storage: Union[BaseStorage, str, None] = None, default_timeout: float = 10.0, retry_delays: Optional[List[int]] = None):
        self.signing_secret = signing_secret
        self.default_timeout = default_timeout
        self.retry_delays = retry_delays if retry_delays is not None else [60, 300, 1800, 3600]

        if isinstance(storage, str):
            if storage.startswith("redis://"):
                from .storage.redis import RedisStorage
                self.storage = RedisStorage(storage)
            elif storage.startswith("sqlite://") or storage.endswith(".db"):
                from .storage.sqlite import SQLiteStorage
                path = storage.replace("sqlite://", "")
                self.storage = SQLiteStorage(path)
            else:
                 raise ValueError(f"Unknown storage URL scheme: {storage}")
        else:
            self.storage = storage

        self.monitor = MonitoringAdapter()

    def _sign_payload(self, payload_body: bytes, timestamp: int) -> str:
        # Sign: "timestamp.body"
        to_sign = f"{timestamp}.".encode() + payload_body
        return hmac.new(
            self.signing_secret.encode(),
            to_sign,
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
        timestamp = int(time.time())
        signature = self._sign_payload(payload_bytes, timestamp)
        
        headers = {
            "Content-Type": "application/json",
            "X-Lh-Timestamp": str(timestamp),
            "X-Lh-Signature": f"v1={signature}",
            "User-Agent": "LazyHooks-Webhook/0.2.0"
        }
        
        if event.headers:
            headers.update(event.headers)

        self.monitor.log_attempt(event.id, event.url, event.attempts + 1)
        start_time = time.time()

        try:
            timeout = aiohttp.ClientTimeout(total=event.timeout)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                try:
                    async with session.post(event.url, data=payload_bytes, headers=headers) as resp:
                        duration = time.time() - start_time
                        
                        # Handle HTTP Errors
                        if resp.status >= 400:
                            body = await resp.text()
                            msg = f"HTTP {resp.status}"
                            kwargs = {
                                "status_code": resp.status,
                                "response_body": body,
                                "response_headers": dict(resp.headers),
                                "url": event.url,
                                "webhook_id": event.id,
                                "attempt": event.attempts + 1
                            }
                            
                            if resp.status == 429:
                                raise WebhookRateLimitError(f"Rate limited: {msg}", **kwargs)
                            elif resp.status == 400:
                                raise WebhookBadRequestError(f"Bad Request: {msg}", **kwargs)
                            elif resp.status == 401:
                                raise WebhookUnauthorizedError(f"Unauthorized: {msg}", **kwargs)
                            elif resp.status == 404:
                                raise WebhookNotFoundError(f"Not Found: {msg}", **kwargs)
                            elif 400 <= resp.status < 500:
                                raise WebhookClientError(msg, **kwargs)
                            elif resp.status >= 500:
                                raise WebhookServerError(msg, **kwargs)
                        
                        # Success
                        self.monitor.log_success(event.id, event.url, event.attempts + 1, duration, resp.status)
                        event.status = "success"
                        event.last_error = None
                        if self.storage:
                            await self.storage.update_event(event)
                            
                except asyncio.TimeoutError:
                    raise WebhookTimeoutError(
                        f"Request timeout after {event.timeout}s",
                        timeout=event.timeout,
                        url=event.url,
                        webhook_id=event.id,
                        attempt=event.attempts + 1
                    )
                except aiohttp.ClientError as e:
                    # Catch-all for other aiohttp errors (connection, dns, etc)
                    raise WebhookNetworkError(
                        f"Network error: {str(e)}",
                        url=event.url,
                        webhook_id=event.id,
                        attempt=event.attempts + 1,
                        original_exception=e
                    )

        except WebhookError as e:
            # We caught one of our own typed exceptions
            event.attempts += 1
            event.last_error = e.message
            
            self.monitor.log_failure(event.id, event.url, event.attempts, e.message)
            
            # Determine if retryable
            should_retry = False
            # Network errors are retryable
            if isinstance(e, (WebhookNetworkError, WebhookServerError, WebhookRateLimitError)):
                 should_retry = True
            elif isinstance(e, WebhookClientError):
                 # 4xx (except 429) are generally not retryable
                 should_retry = False
            
            if should_retry and event.attempts <= len(self.retry_delays):
                delay = self.retry_delays[event.attempts - 1]
                
                # Respect Retry-After if present
                if isinstance(e, WebhookRateLimitError) and hasattr(e, 'retry_after'):
                     if e.retry_after > delay:
                         delay = e.retry_after

                event.status = "failed"
                event.next_retry_at = time.time() + delay
                self.monitor.log_retry(event.id, event.url, event.next_retry_at)
            else:
                event.status = "dead"
            
            if self.storage:
                await self.storage.update_event(event)
            else:
                # If no storage, bubbling up the exception allows caller to handle it
                # But we just mutated 'event', which is local.
                # If the user called await sender.send(), they expect it to succeed or fail.
                # If it failed and we have no storage to retry, we MUST raise exceptions so they know.
                raise e

        except Exception as e:
            # Catch-all for unexpected bugs (serialization, etc)
            event.attempts += 1
            event.last_error = f"Unexpected error: {str(e)}"
            self.monitor.log_failure(event.id, event.url, event.attempts, str(e))
            
            if self.storage:
                 # Treat unknown errors as retryable purely for resilience, or deadly?
                 # Let's retry generic errors conservatively
                 if event.attempts <= len(self.retry_delays):
                     delay = self.retry_delays[event.attempts - 1]
                     event.status = "failed"
                     event.next_retry_at = time.time() + delay
                     await self.storage.update_event(event)
                 else:
                     event.status = "dead"
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
