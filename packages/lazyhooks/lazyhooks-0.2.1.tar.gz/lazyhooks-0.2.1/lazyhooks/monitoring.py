import logging
from typing import Optional, Dict, Any

# --- Optional Imports ---

try:
    import structlog
    HAS_STRUCTLOG = True
except ImportError:
    HAS_STRUCTLOG = False

try:
    import sentry_sdk
    HAS_SENTRY = True
except ImportError:
    HAS_SENTRY = False

try:
    from prometheus_client import Counter, Histogram, Gauge
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False


# --- Monitoring Adapter ---

class MonitoringAdapter:
    """
    Adapter to handle optional monitoring integrations (Logging, Metrics, Error Tracking).
    Gracefully degrades if libraries are not installed.
    """
    def __init__(self, logger: Optional[Any] = None):
        # 1. Logging Setup
        if logger:
            self.logger = logger
        elif HAS_STRUCTLOG:
            self.logger = structlog.get_logger("lazyhooks")
        else:
            self.logger = logging.getLogger("lazyhooks")
            
        # 2. Metrics Setup
        self.metrics = None
        if HAS_PROMETHEUS:
            self._init_prometheus()

    def _init_prometheus(self):
        # Define metrics only once
        try:
             # Check if already registered? 
             # Prometheus client usually handles duplicates by raising error or returning existing if same registry.
             # We assume standard registry. 
             self.metrics = {
                 "sent": Counter(
                     'lazyhooks_webhooks_sent_total',
                     'Total webhooks sent',
                     ['destination', 'status']
                 ),
                 "duration": Histogram(
                     'lazyhooks_webhook_duration_seconds',
                     'Webhook delivery time',
                     ['destination']
                 ),
                 "retry": Counter(
                     'lazyhooks_webhooks_retried_total',
                     'Total webhook retries',
                     ['destination']
                 )
             }
        except ValueError:
             # Likely already registered, ignore re-creation
             pass

    def log_attempt(self, event_id: str, url: str, attempt: int):
        if HAS_STRUCTLOG:
            self.logger.info("webhook.sending", id=event_id, url=url, attempt=attempt)
        else:
            self.logger.info(f"Sending webhook {event_id} to {url} (attempt {attempt})")

    def log_success(self, event_id: str, url: str, attempt: int, duration: float, status_code: int = 200):
        if HAS_STRUCTLOG:
            self.logger.info("webhook.success", id=event_id, url=url, duration=duration, status=status_code)
        else:
            self.logger.info(f"Webhook {event_id} sent to {url} in {duration:.3f}s (status {status_code})")
        
        if self.metrics:
            self.metrics["sent"].labels(destination=url, status="success").inc()
            self.metrics["duration"].labels(destination=url).observe(duration)

    def log_failure(self, event_id: str, url: str, attempt: int, error: str):
        if HAS_STRUCTLOG:
            self.logger.error("webhook.failed", id=event_id, url=url, attempt=attempt, error=error)
        else:
            self.logger.error(f"Webhook {event_id} failed to {url}: {error}")

        if self.metrics:
            self.metrics["sent"].labels(destination=url, status="failure").inc()
        
        # Sentry reporting
        if HAS_SENTRY:
            with sentry_sdk.push_scope() as scope:
                scope.set_tag("webhook.destination", url)
                scope.set_tag("webhook.id", event_id)
                scope.set_extra("attempt", attempt)
                sentry_sdk.capture_message(f"Webhook failed to {url}: {error}", level="error")

    def log_retry(self, event_id: str, url: str, next_retry: float):
        if HAS_STRUCTLOG:
            self.logger.warning("webhook.retry_scheduled", id=event_id, url=url, next_retry=next_retry)
        else:
            self.logger.warning(f"Webhook {event_id} scheduled for retry at {next_retry}")
            
        if self.metrics:
            self.metrics["retry"].labels(destination=url).inc()
