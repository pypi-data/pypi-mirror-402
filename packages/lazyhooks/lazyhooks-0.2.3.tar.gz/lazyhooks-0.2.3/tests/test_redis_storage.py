import pytest
import json
import sys
from unittest.mock import MagicMock, AsyncMock, patch
from lazyhooks.storage.base import WebhookEvent
import lazyhooks.storage.redis as redis_mod

@pytest.fixture
def mock_redis():
    # Patch HAS_REDIS to True so __init__ doesn't raise ImportError
    with patch("lazyhooks.storage.redis.HAS_REDIS", True):
        # Patch the 'redis' symbol in the module. create=True is needed if it wasn't imported.
        with patch("lazyhooks.storage.redis.redis", create=True) as mock_redis_lib:
            mock_client = AsyncMock()
            # process pipeline is NOT awaitable, it returns a pipeline object synchronously
            # which is then used in 'async with'. 
            # So we must override the auto-created AsyncMock child.
            mock_client.pipeline = MagicMock()
            
            # The pipeline context manager yields a pipe object
            pipe_mock = AsyncMock()
            # Pipeline commands (hset, zadd, etc) are SYNCHRONOUS (they return the pipeline or None)
            # Only execute() is async.
            pipe_mock.hset = MagicMock()
            pipe_mock.zadd = MagicMock()
            pipe_mock.expire = MagicMock()
            pipe_mock.zrem = MagicMock()
            pipe_mock.hgetall = MagicMock()
            # execute remains AsyncMock (awaitable)
            
            mock_client.pipeline.return_value.__aenter__.return_value = pipe_mock
            
            mock_redis_lib.from_url.return_value = mock_client
            # Because from_url is mocked on the 'redis' object which is what we patched
            yield mock_client

@pytest.mark.asyncio
async def test_redis_add_event(mock_redis):
    storage = redis_mod.RedisStorage("redis://localhost")
    event = WebhookEvent(
        id="evt_1", url="http://test.com", payload={"a": 1},
        status="pending", created_at=100.0, next_retry_at=100.0
    )
    
    
    # Setup pipeline mock
    # The fixture already configured mock_redis.pipeline...__aenter__ -> pipe_mock
    # We need to grab that pipe_mock to assert on it.
    pipe = mock_redis.pipeline.return_value.__aenter__.return_value
    
    await storage.add_event(event)
    
    # Verification
    # Check hset called
    assert pipe.hset.called
    call_args = pipe.hset.call_args
    assert call_args[0][0] == "lazyhooks:events:evt_1"
    assert json.loads(call_args[1]["mapping"]["payload"]) == {"a": 1}
    
    # Check zadd called (since status is pending)
    pipe.zadd.assert_called_with("lazyhooks:pending", {"evt_1": 100.0})
    
    # Check execute called
    assert pipe.execute.called

@pytest.mark.asyncio
async def test_redis_get_pending(mock_redis):
    storage = redis_mod.RedisStorage("redis://localhost")
    
    # Mock zrangebyscore return
    mock_redis.zrangebyscore.return_value = ["evt_1"]
    
    # Mock pipeline execution results
    # 1. zrem result (ignored)
    # 2. hgetall result for evt_1
    raw_event = {
        "id": "evt_1",
        "url": "http://test.com",
        "payload": '{"a": 1}',
        "status": "pending",
        "attempts": "0",
        "created_at": "100.0",
        "next_retry_at": "100.0",
        "last_error": "",
        "headers": "",
        "timeout": "10.0"
    }
    
    pipe = mock_redis.pipeline.return_value.__aenter__.return_value
    pipe.execute.return_value = [1, raw_event]
    
    events = await storage.get_pending_events()
    
    assert len(events) == 1
    assert events[0].id == "evt_1"
    assert events[0].status == "processing" # We override this in memory
    
    # Verify pipeline logic
    pipe.zrem.assert_called_with("lazyhooks:pending", "evt_1")
    pipe.hgetall.assert_called_with("lazyhooks:events:evt_1")

@pytest.mark.asyncio
async def test_redis_update_event(mock_redis):
    storage = redis_mod.RedisStorage("redis://localhost")
    event = WebhookEvent(
        id="evt_1", url="http://test.com", payload={},
        status="success", next_retry_at=0.0
    )
    
    pipe = mock_redis.pipeline.return_value.__aenter__.return_value
    
    await storage.update_event(event)
    
    # Check status update
    assert pipe.hset.called
    assert pipe.hset.call_args[1]["mapping"]["status"] == "success"
    
    # Check removal from pending
    pipe.zrem.assert_called_with("lazyhooks:pending", "evt_1")
    
    # Ensure add NOT called
    assert not pipe.zadd.called
