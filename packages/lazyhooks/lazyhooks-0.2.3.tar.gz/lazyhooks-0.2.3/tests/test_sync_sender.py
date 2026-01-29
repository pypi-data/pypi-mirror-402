import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from lazyhooks.sync import SyncWebhookSender

@patch("lazyhooks.sync.WebhookSender")
def test_sync_send(MockAsyncSender):
    """Test SyncWebhookSender.send calls async sender via asyncio.run."""
    # Setup mock async sender
    mock_sender_instance = MockAsyncSender.return_value
    mock_sender_instance.send = AsyncMock(return_value="evt_123")
    
    sync_sender = SyncWebhookSender("secret")
    
    # Call sync send
    result = sync_sender.send("http://test.com", {"a": 1})
    
    assert result == "evt_123"
    assert mock_sender_instance.send.called
    mock_sender_instance.send.assert_called_with("http://test.com", {"a": 1}, None, None, None)

@patch("lazyhooks.sync.WebhookSender")
def test_sync_context_manager(MockAsyncSender):
    """Test context manager support."""
    with SyncWebhookSender("secret") as sender:
        assert isinstance(sender, SyncWebhookSender)
    # Nothing really to assert on exit as it's a pass, but ensuring no error is key
