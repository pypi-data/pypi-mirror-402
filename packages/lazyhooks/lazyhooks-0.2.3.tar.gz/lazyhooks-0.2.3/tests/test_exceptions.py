import pytest
import aiohttp
import asyncio
from unittest.mock import AsyncMock, patch
from lazyhooks import WebhookSender
from lazyhooks.exceptions import (
    WebhookRateLimitError, WebhookNotFoundError, WebhookServerError, 
    WebhookTimeoutError, WebhookNetworkError, InvalidSignatureError, ExpiredTimestampError
)
from lazyhooks.receiver import verify_signature
import time

@pytest.mark.asyncio
async def test_sender_rate_limit_error():
    sender = WebhookSender("secret")
    
    # Mock aiohttp session
    with patch("aiohttp.ClientSession.post") as mock_post:
        # Create a mock context manager that returns our mock response
        mock_resp = AsyncMock()
        mock_resp.status = 429
        mock_resp.headers = {"Retry-After": "120"}
        mock_resp.text.return_value = "Reduce rate"
        
        # Configure the context manager to return the mock response
        mock_post.return_value.__aenter__.return_value = mock_resp
        
        # Expect WebhookRateLimitError
        with pytest.raises(WebhookRateLimitError) as exc:
            await sender.send("http://test.com/429", {"a": 1})
        
        err = exc.value
        assert err.status_code == 429
        assert err.retry_after == 120.0
        assert err.is_retryable is True

@pytest.mark.asyncio
async def test_sender_timeout_error():
    sender = WebhookSender("secret")
    
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.side_effect = asyncio.TimeoutError
        
        with pytest.raises(WebhookTimeoutError) as exc:
            await sender.send("http://test.com/timeout", {})
            
        assert exc.value.timeout is not None

def test_receiver_signature_errors():
    # Valid
    body = b'{}'
    ts = str(int(time.time()))
    # Mock signature creation would be needed or just fail verification
    
    # Test Missing Headers
    with pytest.raises(InvalidSignatureError, match="Missing"):
        verify_signature(body, "", "secret", ts)

    # Test Expired
    old_ts = str(int(time.time()) - 1000)
    with pytest.raises(ExpiredTimestampError, match="expired"):
        # Sig format must be valid enough to pass first check if we reached timestamp check?
        # Actually timestamp check is first in our impl.
        verify_signature(body, "v1=dummy", "secret", old_ts)
