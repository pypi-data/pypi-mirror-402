from lazyhooks import development, production, strict, high_volume
from lazyhooks.sender import WebhookSender
from lazyhooks.storage.redis import RedisStorage

def test_development_preset():
    sender = development("dev-secret")
    assert sender.signing_secret == "dev-secret"
    assert sender.storage is None
    assert sender.default_timeout == 5.0
    # Overrides
    sender2 = development("dev-secret", default_timeout=2.0)
    assert sender2.default_timeout == 2.0

def test_production_preset():
    url = "redis://localhost:6379/0"
    sender = production("prod-secret", url)
    assert isinstance(sender.storage, RedisStorage)
    assert sender.default_timeout == 10.0
    assert len(sender.retry_delays) == 4

def test_strict_preset():
    url = "redis://localhost:6379/0"
    sender = strict("strict-secret", url)
    assert sender.default_timeout == 30.0
    assert len(sender.retry_delays) == 10  # 10 retries

def test_high_volume_preset():
    url = "redis://localhost:6379/0"
    sender = high_volume("vol-secret", url)
    assert sender.default_timeout == 5.0
    assert len(sender.retry_delays) == 3   # 3 retries
