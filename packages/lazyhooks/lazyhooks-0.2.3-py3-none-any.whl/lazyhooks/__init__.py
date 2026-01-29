"""
LazyHooks: A lightweight, standalone Python package for sending and receiving webhooks with optional persistence.
"""

from .sender import WebhookSender
from .receiver import WebhookReceiver, verify_signature
from .sync import SyncWebhookSender
from .exceptions import (
    WebhookError, WebhookDeliveryError, WebhookVerificationError, 
    InvalidSignatureError, ExpiredTimestampError
)
from .presets import development, production, strict, high_volume

__all__ = [
    "WebhookSender", 
    "WebhookReceiver", 
    "verify_signature", 
    "SyncWebhookSender",
    "WebhookError",
    "WebhookDeliveryError",
    "WebhookVerificationError",
    "InvalidSignatureError",
    "ExpiredTimestampError",
    "development",
    "production",
    "strict",
    "high_volume"
]
__version__ = "0.2.3"
