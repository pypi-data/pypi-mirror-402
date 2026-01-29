import pytest
import time
import hmac
import hashlib
import json
import asyncio
from lazyhooks.receiver import WebhookReceiver, verify_signature

SECRET = "test-secret"

def generate_signature(secret, body, timestamp):
    to_sign = f"{timestamp}.".encode() + body
    return hmac.new(secret.encode(), to_sign, hashlib.sha256).hexdigest()

def test_verify_signature_valid():
    body = b'{"hello": "world"}'
    timestamp = str(int(time.time()))
    sig = generate_signature(SECRET, body, int(timestamp))
    header = f"v1={sig}"
    
    assert verify_signature(body, header, SECRET, timestamp)

def test_verify_signature_invalid_secret():
    body = b'{"hello": "world"}'
    timestamp = str(int(time.time()))
    sig = generate_signature("wrong-secret", body, int(timestamp))
    header = f"v1={sig}"
    
    assert not verify_signature(body, header, SECRET, timestamp)

def test_verify_signature_expired():
    body = b'{"hello": "world"}'
    timestamp = str(int(time.time()) - 600) # 10 mins ago
    sig = generate_signature(SECRET, body, int(timestamp))
    header = f"v1={sig}"
    
    assert not verify_signature(body, header, SECRET, timestamp)

def test_receiver_routing():
    receiver = WebhookReceiver(SECRET)
    received_events = []

    @receiver.on("user.created")
    async def handle_user(event):
        received_events.append(event)
    
    payload = {"event": "user.created", "id": 123}
    
    async def run():
        await receiver.process_event(payload)

    asyncio.run(run())
    
    assert len(received_events) == 1
    assert received_events[0]["id"] == 123

def test_receiver_middleware():
    receiver = WebhookReceiver(SECRET)
    log = []

    @receiver.middleware
    async def mw1(event, next_handler):
        log.append("mw1_start")
        await next_handler(event)
        log.append("mw1_end")

    @receiver.on("test")
    async def handler(event):
        log.append("handler")

    async def run():
        await receiver.process_event({"event": "test"})

    asyncio.run(run())
    
    assert log == ["mw1_start", "handler", "mw1_end"]

def test_receiver_wildcard():
    receiver = WebhookReceiver(SECRET)
    hits = []

    @receiver.on("payment.*")
    async def handle_payment(event):
        hits.append(event["type"])

    async def run():
        await receiver.process_event({"event": "payment.success", "type": "success"})
        await receiver.process_event({"event": "payment.failed", "type": "failed"})
        await receiver.process_event({"event": "other.event", "type": "other"})

    asyncio.run(run())

    assert "success" in hits
    assert "failed" in hits
    assert "other" not in hits

def test_sync_handler_mixed():
    """Test sync handler called via async process_event."""
    receiver = WebhookReceiver(SECRET)
    results = []

    @receiver.on("sync.event")
    def handle_sync(event):
        results.append("sync")
    
    @receiver.on("async.event")
    async def handle_async(event):
        results.append("async")

    async def run():
        await receiver.process_event({"event": "sync.event"})
        await receiver.process_event({"event": "async.event"})
    
    asyncio.run(run())
    
    assert results == ["sync", "async"]

def test_process_event_sync():
    """Test fully synchronous usage via process_event_sync."""
    receiver = WebhookReceiver(SECRET)
    results = []

    @receiver.on("sync.event")
    def handle_sync(event):
        results.append(event["val"])

    receiver.process_event_sync({"event": "sync.event", "val": 1})
    
    assert results == [1]

def test_process_event_sync_with_async_handler():
    """Test process_event_sync calling an async handler (via internal loop)."""
    receiver = WebhookReceiver(SECRET)
    results = []

    @receiver.on("async.event")
    async def handle_async(event):
        results.append(event["val"])

    receiver.process_event_sync({"event": "async.event", "val": 2})
    
    assert results == [2]

def test_sync_middleware():
    """Test sync middleware with both sync and async handlers."""
    receiver = WebhookReceiver(SECRET)
    log = []

    @receiver.middleware
    def sync_mw(event, next_handler):
        log.append("mw_start")
        # next_handler is async, so we must await it if we were async, 
        # but we are sync. So we return the awaitable.
        return next_handler(event)
        # Note: Sync middleware CANNOT execute code *after* await next_handler() 
        # because it can't await. It can only wrap or pre-process.
        # UNLESS it returns a new coroutine that does post-processing?
        # But 'def' returning coroutine is tricky without async def.
        # This test verifies pre-processing works.

    @receiver.on("test")
    async def handler(event):
        log.append("handler")

    receiver.process_event_sync({"event": "test"})
    
    assert log == ["mw_start", "handler"]
