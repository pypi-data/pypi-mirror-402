import json
import time
import hmac
import hashlib
from typing import Dict, Any, Optional

def create_webhook_request(payload: Dict[str, Any], signing_secret: str, timestamp: Optional[int] = None) -> Dict[str, Any]:
    """
    Helper to create a properly signed webhook request structure (headers + body).
    Useful for testing WebhookReceiver.
    
    Returns a dict with 'json' (data) and 'headers' (containing signature).
    """
    if timestamp is None:
        timestamp = int(time.time())
        
    payload_bytes = json.dumps(payload).encode()
    to_sign = f"{timestamp}.".encode() + payload_bytes
    signature = hmac.new(signing_secret.encode(), to_sign, hashlib.sha256).hexdigest()
    
    return {
        "json": payload,
        "headers": {
            "Content-Type": "application/json",
            "X-Lh-Timestamp": str(timestamp),
            "X-Lh-Signature": f"v1={signature}"
        }
    }

class MockWebhookSender:
    """
    Minimal mock for WebhookSender that records calls instead of sending them.
    Has the same interface as the real sender for basic 'send' operations.
    """
    def __init__(self, signing_secret: str = "mock-secret"):
        self.signing_secret = signing_secret
        self.calls = []
        
    async def send(self, url: str, payload: Dict[str, Any], **kwargs):
        """
        Record the call and return a success-like result.
        """
        self.calls.append({
            "url": url,
            "payload": payload,
            "kwargs": kwargs
        })
        
        # Return a simple object mimicking the result if needed, 
        # or just True for success/failure checks if using basic boolean logic
        # For now, we don't return a complex object unless requested.
        return True

    @property
    def call_count(self) -> int:
        return len(self.calls)

    @property
    def last_call(self) -> Optional[Dict[str, Any]]:
        return self.calls[-1] if self.calls else None
