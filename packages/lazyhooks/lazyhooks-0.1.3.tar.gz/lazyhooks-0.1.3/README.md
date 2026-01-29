# LazyHooks

A lightweight, standalone Python package for sending and receiving webhooks with optional persistence.

>**[Full Documentation & Examples on GitHub](https://github.com/StackTactician/LazyHooks)**

## Features

- **Simple API**: Send webhooks with minimal boilerplate.
- **Async First**: Built on `asyncio` and `aiohttp` for high performance.
- **Secure**: Built-in HMAC-SHA256 signing and verification.
- **Reliable**: Optional `SQLite` storage to persist and retry failed webhooks.

## Installation

```bash
pip install lazyhooks
```

## Quick Start

### Sending a Webhook (Fire & Forget)

```python
import asyncio
from lazyhooks import WebhookSender

async def main():
    sender = WebhookSender(signing_secret="super-secret")
    await sender.send(
        url="https://example.com/webhook",
        payload={"event": "user.created", "id": 123}
    )

asyncio.run(main())
```

### Receiving a Webhook

```python
from lazyhooks import verify_signature

# In your Flask/FastAPI/Django handler:
def handle_webhook(request):
    signature = request.headers.get("X-Hub-Signature-256")
    body = request.body
    
    if verify_signature(body, signature, "super-secret"):
        # Process webhook
        return "OK", 200
    else:
        return "Invalid Signature", 401
```

## Links

- **GitHub**: [https://github.com/StackTactician/LazyHooks](https://github.com/StackTactician/LazyHooks)
- **Issues**: [https://github.com/StackTactician/LazyHooks/issues](https://github.com/StackTactician/LazyHooks/issues)
- **Documentation**: See the GitHub repo for full docs, advanced usage, and examples.

