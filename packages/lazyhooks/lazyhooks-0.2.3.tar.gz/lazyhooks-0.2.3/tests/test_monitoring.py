import pytest
import sys
import importlib
from unittest.mock import MagicMock, patch
import lazyhooks.monitoring

def test_monitoring_fallback_logger():
    """Test standard logging fallback when structlog missing."""
    # Ensure structlog is NOT present
    with patch.dict("sys.modules"):
        sys.modules.pop("structlog", None)
        importlib.reload(lazyhooks.monitoring)
        
        mock_logger = MagicMock()
        adapter = lazyhooks.monitoring.MonitoringAdapter(logger=mock_logger)
        
        adapter.log_success("evt1", "http://test", 1, 0.5)
        
        assert mock_logger.info.called
        assert "Webhook evt1 sent" in mock_logger.info.call_args[0][0]

def test_monitoring_structlog():
    """Test structlog usage when present."""
    # We need to simulate that structlog IS importable
    mb = MagicMock()
    with patch.dict("sys.modules", {"structlog": mb}):
        importlib.reload(lazyhooks.monitoring)
        
        # Setup mock logger returned by get_logger
        mock_logger = MagicMock()
        mb.get_logger.return_value = mock_logger
        
        adapter = lazyhooks.monitoring.MonitoringAdapter() 
        
        adapter.log_success("evt1", "http://test", 1, 0.5)
        
        # Should call info with kwargs
        mock_logger.info.assert_called_with("webhook.success", id="evt1", url="http://test", duration=0.5, status=200)

def test_monitoring_metrics():
    """Test prometheus metrics when present."""
    mb = MagicMock()
    with patch.dict("sys.modules", {"prometheus_client": mb}):
        importlib.reload(lazyhooks.monitoring)
        
        adapter = lazyhooks.monitoring.MonitoringAdapter(logger=MagicMock())
        
        adapter.log_success("evt1", "http://test", 1, 0.5)
        
        # Verify metric calls (via the mocked module classes)
        # mb.Counter is the class, return_value is the instance
        mock_sent = mb.Counter.return_value
        mock_dur = mb.Histogram.return_value
        
        mock_sent.labels.assert_called_with(destination="http://test", status="success")
        mock_sent.labels.return_value.inc.assert_called()

def test_monitoring_sentry():
    """Test sentry capturing on failure."""
    mb = MagicMock()
    with patch.dict("sys.modules", {"sentry_sdk": mb}):
        importlib.reload(lazyhooks.monitoring)
        
        adapter = lazyhooks.monitoring.MonitoringAdapter(logger=MagicMock())
        
        adapter.log_failure("evt1", "http://test", 1, "Connection Error")
        
        assert mb.push_scope.called
        mb.capture_message.assert_called()
