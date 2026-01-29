"""
Cache Validation Metrics Tracker

This module provides metrics tracking and alerting for cache validation.
It tracks validation statistics and sends batched Slack notifications when
mismatches exceed a configured threshold.

Features:
- Thread-safe metrics tracking (gevent-compatible)
- Batched Slack notifications to prevent spam
- Configurable thresholds and channels
- Detailed mismatch reporting
"""

from datetime import datetime
from flask import current_app


def _create_lock():
    """
    Create a gevent-compatible lock.

    Uses gevent's RLock when available (for gunicorn + gevent workers),
    falls back to threading.Lock for non-gevent environments.

    This ensures the lock cooperates with gevent's greenlet scheduling
    and doesn't block the entire worker.
    """
    try:
        from gevent.lock import RLock
        return RLock()
    except ImportError:
        import threading
        return threading.Lock()


class CacheValidationMetrics:
    """
    Track cache validation metrics and send batched Slack notifications.

    This class is thread-safe and tracks:
    - Total number of validations performed
    - Number of mismatches detected
    - Detailed information about each mismatch

    When the number of mismatches reaches a configured threshold,
    it sends a consolidated Slack notification and resets the counters.

    Configuration (via Flask app.config):
    - CACHE_VALIDATION_SLACK_ENABLED: Enable/disable Slack notifications (default: True)
    - CACHE_VALIDATION_SLACK_THRESHOLD: Number of mismatches before alerting (default: 10)
    - CACHE_VALIDATION_SLACK_CHANNEL: Slack channel name (default: "cache-alerts")
    """

    def __init__(self):
        """Initialize metrics tracker with gevent-compatible thread safety."""
        self.total_validations = 0
        self.mismatches = 0
        self.mismatch_details = []
        self._lock = _create_lock()  # Gevent-compatible lock for concurrent requests
    
    def record_validation(self, matched: bool, details: dict = None):
        """
        Record a validation result and check if threshold is reached.
        
        Args:
            matched: True if cached data matches fresh data, False otherwise
            details: Dictionary with mismatch details (only needed if matched=False)
                Expected keys:
                - api_path: API endpoint path
                - params: Request parameters
                - cache_key: Cache key that was validated
                - timestamp: ISO format timestamp
                - cached_data_preview: Preview of cached data
                - fresh_data_preview: Preview of fresh data
        
        Thread-safe: Uses lock to prevent race conditions.
        """
        with self._lock:
            self.total_validations += 1
            
            if not matched:
                self.mismatches += 1
                
                # Store mismatch details
                if details:
                    self.mismatch_details.append(details)
                
                # Check if we've reached the threshold
                threshold = current_app.config.get('CACHE_VALIDATION_SLACK_THRESHOLD', 10)
                
                if self.mismatches >= int(threshold):
                    # Send batch alert and reset
                    self._send_batch_alert()
    
    def _send_batch_alert(self):
        """
        Send consolidated Slack notification about cache mismatches.
        
        Uses send_notification_message() from notification_center to send
        a formatted alert via Kafka to Slack.
        
        The alert includes:
        - Summary statistics (total validations, mismatches, rate)
        - Recent mismatch examples (last 5)
        - Timestamp and environment information
        
        After sending, resets the metrics counters.
        """
        # Check if Slack notifications are enabled
        slack_enabled = current_app.config.get('CACHE_VALIDATION_SLACK_ENABLED', True)
        
        if not slack_enabled:
            print(f"[Cache Validation] Slack disabled, skipping alert for {self.mismatches} mismatches")
            self.reset()
            return
        
        try:
            from wedeliver_core_plus.helpers.kafka_producers.notification_center import send_notification_message
            
            # Calculate mismatch rate
            mismatch_rate = (self.mismatches / self.total_validations * 100) if self.total_validations > 0 else 0
            
            # Build detailed message
            message = (
                f"🚨 *Cache Validation Alert*\n\n"
                f"*Summary:*\n"
                f"• Total Validations: {self.total_validations:,}\n"
                f"• Mismatches Found: {self.mismatches}\n"
                f"• Mismatch Rate: {mismatch_rate:.2f}%\n\n"
            )
            
            # Add recent mismatch examples (last 5)
            if self.mismatch_details:
                message += f"*Recent Mismatches (last {min(5, len(self.mismatch_details))}):*\n"
                
                for i, detail in enumerate(self.mismatch_details[-5:], 1):
                    message += (
                        f"\n{i}. API: `{detail.get('api_path', 'unknown')}`\n"
                        f"   Params: `{detail.get('params', {})}`\n"
                        f"   Time: {detail.get('timestamp', 'unknown')}\n"
                    )
                    
                    # Add data previews if available
                    if detail.get('cached_data_preview'):
                        message += f"   Cached: `{detail['cached_data_preview'][:100]}...`\n"
                    if detail.get('fresh_data_preview'):
                        message += f"   Fresh: `{detail['fresh_data_preview'][:100]}...`\n"
            
            # Get channel from config
            channel = current_app.config.get('CACHE_VALIDATION_SLACK_CHANNEL', 'cache-alerts')
            
            # Send via Kafka to Slack
            send_notification_message(
                message=message,
                channel=channel,
                title="Cache Validation Alert",
                color="#ff9900",  # Orange for warnings
                emoji=":warning:",
                prefix_channel=True,  # Add env prefix (eng-production-cache-alerts)
                prefix_title=True,    # Add service name to title
                prefix_message=True   # Add node/env/date to message
            )
            
            print(f"[Cache Validation] Sent Slack alert for {self.mismatches} mismatches")
            
        except Exception as e:
            print(f"[Cache Validation] Failed to send Slack alert: {e}")
        
        finally:
            # Always reset after attempting to send
            self.reset()
    
    def get_metrics(self):
        """
        Get current metrics for monitoring/debugging.
        
        Returns:
            dict: Current metrics including:
                - total_validations: Total number of validations performed
                - mismatches: Number of mismatches detected
                - mismatch_rate: Percentage of validations that were mismatches
                - recent_mismatches: List of recent mismatch details (last 10)
        
        Thread-safe: Uses lock to ensure consistent read.
        """
        with self._lock:
            return {
                "total_validations": self.total_validations,
                "mismatches": self.mismatches,
                "mismatch_rate": (self.mismatches / self.total_validations * 100) if self.total_validations > 0 else 0,
                "recent_mismatches": self.mismatch_details[-10:]  # Last 10
            }
    
    def reset(self):
        """
        Reset metrics counters and mismatch details.
        
        Called automatically after sending batch alerts.
        Can also be called manually via admin endpoint.
        
        Thread-safe: Uses lock to ensure atomic reset.
        """
        with self._lock:
            self.total_validations = 0
            self.mismatches = 0
            self.mismatch_details = []
            print("[Cache Validation] Metrics reset")

