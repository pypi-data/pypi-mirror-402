import pytest
from lazyhooks.testing import MockWebhookSender, create_webhook_request
from lazyhooks.receiver import WebhookReceiver

@pytest.fixture
def mock_webhook_sender():
    """Fixture providing a MockWebhookSender instance."""
    return MockWebhookSender()

@pytest.fixture
def webhook_receiver_factory():
    """
    Fixture returning a factory function to create a WebhookReceiver 
    with a specific secret.
    """
    def _create(secret="test-secret"):
        return WebhookReceiver(signing_secret=secret)
    return _create

@pytest.fixture
def signed_payload_factory():
    """
    Fixture returning a helper to generate signed requests.
    Usage: signed_payload_factory({"foo": "bar"}, secret="...")
    """
    return create_webhook_request
