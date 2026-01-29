import time
from typing import Optional, Dict, Any

class WebhookError(Exception):
    """Base exception for all webhook errors."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message)
        self.message = message
        self.timestamp = kwargs.get('timestamp', time.time())
        self.webhook_id = kwargs.get('webhook_id')
        self.url = kwargs.get('url')
        self.attempt = kwargs.get('attempt', 1)
        # Store any extra context
        self.context = kwargs

    def to_dict(self) -> Dict[str, Any]:
        """Convert error details to dictionary for logging/monitoring."""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'webhook_id': self.webhook_id,
            'url': self.url,
            'attempt': self.attempt,
            'timestamp': self.timestamp,
            **{k: v for k, v in self.context.items() if k not in ['timestamp', 'webhook_id', 'url', 'attempt']}
        }

class WebhookConfigurationError(WebhookError):
    """Invalid configuration (signing secret, storage URL, etc)."""
    pass

class WebhookDeliveryError(WebhookError):
    """Base for errors occurring during delivery attempt."""
    pass

class WebhookNetworkError(WebhookDeliveryError):
    """Network level errors (DNS, Timeout, Connection refused)."""
    pass

class WebhookTimeoutError(WebhookNetworkError):
    """Request timed out."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, **kwargs)
        self.timeout = kwargs.get('timeout')

class WebhookHTTPError(WebhookDeliveryError):
    """
    HTTP error response from server.
    Includes status_code, and potentially response body/headers.
    """
    def __init__(self, message: str, status_code: int, **kwargs):
        super().__init__(message, **kwargs)
        self.status_code = status_code
        self.response_body = kwargs.get('response_body')
        self.response_headers = kwargs.get('response_headers', {})

    @property
    def is_retryable(self) -> bool:
        """ByType, 5xx are retryable, 4xx are usually not (except 429)."""
        return self.status_code >= 500

class WebhookClientError(WebhookHTTPError):
    """4xx Client Errors."""
    pass

class WebhookBadRequestError(WebhookClientError):
    """400 Bad Request."""
    pass

class WebhookUnauthorizedError(WebhookClientError):
    """401 Unauthorized."""
    pass

class WebhookNotFoundError(WebhookClientError):
    """404 Not Found."""
    pass

class WebhookRateLimitError(WebhookClientError):
    """429 Too Many Requests."""
    def __init__(self, message: str, **kwargs):
        # Remove status_code if provided in kwargs to avoid conflict with our hardcoded 429
        kwargs.pop('status_code', None)
        super().__init__(message, status_code=429, **kwargs)
        # Parse Retry-After
        headers = kwargs.get('response_headers', {})
        retry_val = headers.get('Retry-After') or headers.get('retry-after')
        self.retry_after = 60 # Default
        if retry_val:
            try:
                self.retry_after = float(retry_val)
            except ValueError:
                pass
    
    @property
    def is_retryable(self) -> bool:
        return True

class WebhookServerError(WebhookHTTPError):
    """5xx Server Errors."""
    pass

class WebhookVerificationError(WebhookError):
    """Errors verifying incoming webhooks."""
    pass

class InvalidSignatureError(WebhookVerificationError):
    """Signature mismatch."""
    pass

class ExpiredTimestampError(WebhookVerificationError):
    """Timestamp outside tolerance window."""
    pass
