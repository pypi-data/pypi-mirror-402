# LazyHooks

A lightweight, standalone Python package for sending and receiving webhooks with optional persistence.


## Features

- **Simple API**: Send webhooks with minimal boilerplate.
- **Async First**: Built on `asyncio` and `aiohttp` for high performance.
- **Secure**: HMAC-SHA256 signing with **Timestamp Replay Protection**.
- **Reliable**: Optional `SQLite` storage to persist and retry failed webhooks.

## Security

LazyHooks prioritizes security by design:

- **Replay Protection**: All webhooks include a timestamp. Requests older than 5 minutes are rejected.
- **HMAC-SHA256**: Signatures verify both the **body and the timestamp** (`timestamp.body`) to prevent tampering.
- **Constant-Time Verification**: Prevents timing attacks.
- **SQL Injection Safe**: Parameterized queries.

> **headers**: 
> - `X-Lh-Timestamp`: Unix timestamp of the request.
> - `X-Lh-Signature`: `v1=...` (HMAC of `timestamp.body`)

## Documentation

### 🔰 Beginner Tutorials (Start Here!)
1. **[What are Webhooks?](docs/tutorials/01_what_are_webhooks.md)**: The basics explained simply.
2. **[Installation](docs/tutorials/02_installation.md)**: Quick setup guide.
3. **[Your First Webhook](docs/tutorials/03_your_first_webhook.md)**: Send "Hello World" in 2 minutes.
4. **[Receiving Webhooks](docs/tutorials/04_receiving_webhooks.md)**: Listen for events securely.
5. **[Testing with Tunnels](docs/tutorials/05_testing_with_tunnels.md)**: Go live with ngrok.

### 📚 Core Documentation

- **[Getting Started](docs/getting_started.md)**: Installation and quick examples.
- **[Sending Webhooks](docs/sending_webhooks.md)**: Sending usage.
- **[Receiving Webhooks](docs/receiving_webhooks.md)**: Receiver usage.
- **[Storage & Retries](docs/storage_and_retries.md)**: Persistence and reliability.
- **[Security](docs/security.md)**: Security details.
- **[Comparisons](docs/comparisons.md)**: Alternatives analysis.
- **[API Reference](docs/api_reference.md)**: API docs.

## Quick Example

### Sending

```python
import asyncio
from lazyhooks import WebhookSender

async def main():
    sender = WebhookSender(signing_secret="super-secret")
    await sender.send("https://example.com/webhook", {"event": "hello"})

asyncio.run(main())
```

### Receiving

```python
from lazyhooks import verify_signature

def handle_webhook(request):
    timestamp = request.headers.get("X-Lh-Timestamp")
    signature = request.headers.get("X-Lh-Signature")
    body = request.body
    
    if verify_signature(body, signature, "super-secret", timestamp):
        return "OK", 200
    else:
        return "Invalid Signature or Timestamp", 401
```

## Links

- **PyPI**: [https://pypi.org/project/lazyhooks](https://pypi.org/project/lazyhooks)
- **Issues**: [https://github.com/StackTactician/LazyHooks/issues](https://github.com/StackTactician/LazyHooks/issues)
- **Documentation**: See the GitHub repo for full docs, advanced usage, and examples.
