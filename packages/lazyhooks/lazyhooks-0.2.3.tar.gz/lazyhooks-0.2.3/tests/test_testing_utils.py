import pytest
from lazyhooks.testing import create_webhook_request, MockWebhookSender
from lazyhooks.testing.fixtures import mock_webhook_sender, signed_payload_factory

def test_create_webhook_request_structure():
    data = {"foo": "bar"}
    req = create_webhook_request(data, "secret")
    
    assert req["json"] == data
    assert "headers" in req
    assert "X-Lh-Signature" in req["headers"]
    assert "X-Lh-Timestamp" in req["headers"]
    assert req["headers"]["X-Lh-Signature"].startswith("v1=")

@pytest.mark.asyncio
async def test_mock_sender_behavior():
    sender = MockWebhookSender()
    assert sender.call_count == 0
    
    await sender.send("http://test.com", {"a": 1})
    
    assert sender.call_count == 1
    call = sender.last_call
    assert call["url"] == "http://test.com"
    assert call["payload"] == {"a": 1}

# Test fixtures if they were implicitly imported by pytest (manual check here)
@pytest.mark.asyncio
async def test_fixtures_direct_use(mock_webhook_sender, signed_payload_factory):
    # Test sender fixture
    await mock_webhook_sender.send("url", {})
    assert mock_webhook_sender.call_count == 1
    
    # Test factory fixture
    req = signed_payload_factory({"a": 1}, "secret")
    assert req["json"] == {"a": 1}
