"""
LazyHooks: A lightweight, standalone Python package for sending and receiving webhooks with optional persistence.
"""

from .sender import WebhookSender
from .receiver import verify_signature

__all__ = ["WebhookSender", "verify_signature"]
__version__ = "0.1.3"
