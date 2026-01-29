from typing import Optional, List, Dict, Any
from .sender import WebhookSender

def development(signing_secret: str, **overrides) -> WebhookSender:
    """
    Development preset:
    - In-memory storage (no persistence)
    - Fails fast (1 retry)
    - Short timeout (5s)
    - Good for: Local dev, debugging, tests
    """
    config = {
        "signing_secret": signing_secret,
        "storage": None,
        "default_timeout": 5.0,
        "retry_delays": [1]
    }
    # If user provides overrides, apply them
    config.update(overrides)
    return WebhookSender(**config)

def production(signing_secret: str, redis_url: str, **overrides) -> WebhookSender:
    """
    Production preset:
    - Redis storage
    - Standard retries (5 attempts: 1m, 5m, 30m, 1h)
    - Standard timeout (10s)
    - Good for: Most applications
    """
    config = {
        "signing_secret": signing_secret,
        "storage": redis_url,
        "default_timeout": 10.0,
        "retry_delays": [60, 300, 1800, 3600]
    }
    config.update(overrides)
    return WebhookSender(**config)

def strict(signing_secret: str, redis_url: str, **overrides) -> WebhookSender:
    """
    Strict preset:
    - Redis storage
    - Aggressive retries (10 attempts over ~24h)
    - Long timeout (30s)
    - Good for: Payments, critical compliance events
    """
    # 10 retries: 1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h
    delays = [60, 300, 900, 1800, 3600, 7200, 14400, 21600, 28800, 43200]
    
    config = {
        "signing_secret": signing_secret,
        "storage": redis_url,
        "default_timeout": 30.0,
        "retry_delays": delays
    }
    config.update(overrides)
    return WebhookSender(**config)

def high_volume(signing_secret: str, redis_url: str, **overrides) -> WebhookSender:
    """
    High Volume preset:
    - Redis storage
    - Fewer retries (3 attempts) to prevent backlog
    - Short timeout (5s) to free up connections
    - Good for: High throughput, non-critical notifications
    """
    config = {
        "signing_secret": signing_secret,
        "storage": redis_url,
        "default_timeout": 5.0,
        "retry_delays": [30, 60, 300] # Quick retries
    }
    config.update(overrides)
    return WebhookSender(**config)
