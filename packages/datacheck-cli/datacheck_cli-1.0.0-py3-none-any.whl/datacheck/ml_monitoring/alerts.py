"""Alert management module for ML monitoring.

Provides alerting capabilities for drift detection and performance degradation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from collections.abc import Callable
from datetime import datetime
import json
import logging
from pathlib import Path


logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Severity levels for alerts."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Available alert channels."""

    LOG = "log"
    FILE = "file"
    WEBHOOK = "webhook"
    CALLBACK = "callback"


@dataclass
class Alert:
    """Alert representation."""

    alert_id: str
    title: str
    message: str
    severity: AlertSeverity
    source: str  # Component that generated the alert
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    acknowledged_at: datetime | None = None
    acknowledged_by: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "title": self.title,
            "message": self.message,
            "severity": self.severity.value,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "acknowledged": self.acknowledged,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "acknowledged_by": self.acknowledged_by,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Alert":
        """Create from dictionary."""
        data = data.copy()
        if "severity" in data and isinstance(data["severity"], str):
            data["severity"] = AlertSeverity(data["severity"])
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        if "acknowledged_at" in data and isinstance(data["acknowledged_at"], str):
            data["acknowledged_at"] = datetime.fromisoformat(data["acknowledged_at"])
        return cls(**data)

    def acknowledge(self, by: str | None = None) -> None:
        """Mark alert as acknowledged."""
        self.acknowledged = True
        self.acknowledged_at = datetime.now()
        self.acknowledged_by = by


class AlertManager:
    """Manager for ML monitoring alerts.

    Handles alert creation, routing, and notification.
    """

    def __init__(
        self,
        name: str = "default",
        storage_path: str | None = None,
    ):
        """Initialize alert manager.

        Args:
            name: Name for this alert manager instance
            storage_path: Path to store alert history
        """
        self.name = name
        self.storage_path = Path(storage_path) if storage_path else None

        self._alerts: list[Alert] = []
        self._alert_counter = 0
        self._channels: dict[AlertChannel, list[Any]] = {
            AlertChannel.LOG: [],
            AlertChannel.FILE: [],
            AlertChannel.WEBHOOK: [],
            AlertChannel.CALLBACK: [],
        }
        self._callbacks: list[Callable[[Alert], None]] = []
        self._filters: list[Callable[[Alert], bool]] = []

        # Default: enable logging
        self._log_enabled = True

    def create_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity | str = AlertSeverity.WARNING,
        source: str = "unknown",
        metadata: dict[str, Any] | None = None,
    ) -> Alert:
        """Create and dispatch a new alert.

        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity
            source: Source component
            metadata: Additional metadata

        Returns:
            Created Alert object
        """
        if isinstance(severity, str):
            severity = AlertSeverity(severity)

        self._alert_counter += 1
        alert = Alert(
            alert_id=f"{self.name}_{self._alert_counter}",
            title=title,
            message=message,
            severity=severity,
            source=source,
            metadata=metadata or {},
        )

        # Apply filters
        for filter_fn in self._filters:
            if not filter_fn(alert):
                return alert  # Alert filtered out

        self._alerts.append(alert)
        self._dispatch_alert(alert)

        return alert

    def _dispatch_alert(self, alert: Alert) -> None:
        """Dispatch alert to all configured channels."""
        # Log channel
        if self._log_enabled:
            self._log_alert(alert)

        # File channel
        for filepath in self._channels[AlertChannel.FILE]:
            self._write_alert_to_file(alert, filepath)

        # Webhook channel
        for webhook_url in self._channels[AlertChannel.WEBHOOK]:
            self._send_webhook(alert, webhook_url)

        # Callback channel
        for callback in self._callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

    def _log_alert(self, alert: Alert) -> None:
        """Log alert to standard logging."""
        log_level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.CRITICAL: logging.CRITICAL,
        }.get(alert.severity, logging.WARNING)

        logger.log(
            log_level,
            f"[{alert.source}] {alert.title}: {alert.message}",
        )

    def _write_alert_to_file(self, alert: Alert, filepath: str) -> None:
        """Write alert to file."""
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)

            # Append to JSON lines format
            with open(path, 'a') as f:
                f.write(json.dumps(alert.to_dict(), default=str) + "\n")
        except Exception as e:
            logger.error(f"Failed to write alert to file: {e}")

    def _send_webhook(self, alert: Alert, webhook_url: str) -> None:
        """Send alert via webhook."""
        try:
            import urllib.request
            import urllib.error

            data = json.dumps(alert.to_dict(), default=str).encode('utf-8')
            req = urllib.request.Request(
                webhook_url,
                data=data,
                headers={'Content-Type': 'application/json'},
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status != 200:
                    logger.warning(f"Webhook returned status {response.status}")

        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")

    def add_file_channel(self, filepath: str) -> None:
        """Add file output channel.

        Args:
            filepath: Path to write alerts
        """
        self._channels[AlertChannel.FILE].append(filepath)

    def add_webhook_channel(self, webhook_url: str) -> None:
        """Add webhook output channel.

        Args:
            webhook_url: URL to POST alerts to
        """
        self._channels[AlertChannel.WEBHOOK].append(webhook_url)

    def add_callback(self, callback: Callable[[Alert], None]) -> None:
        """Add callback function for alerts.

        Args:
            callback: Function to call with each alert
        """
        self._callbacks.append(callback)

    def add_filter(self, filter_fn: Callable[[Alert], bool]) -> None:
        """Add alert filter.

        Args:
            filter_fn: Function that returns True to allow alert, False to filter
        """
        self._filters.append(filter_fn)

    def set_logging_enabled(self, enabled: bool) -> None:
        """Enable or disable logging channel.

        Args:
            enabled: Whether to enable logging
        """
        self._log_enabled = enabled

    def get_alerts(
        self,
        severity: AlertSeverity | None = None,
        source: str | None = None,
        since: datetime | None = None,
        unacknowledged_only: bool = False,
        limit: int | None = None,
    ) -> list[Alert]:
        """Get alerts with optional filtering.

        Args:
            severity: Filter by severity
            source: Filter by source
            since: Only return alerts after this timestamp
            unacknowledged_only: Only return unacknowledged alerts
            limit: Maximum number to return

        Returns:
            List of matching alerts
        """
        alerts = self._alerts

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        if source:
            alerts = [a for a in alerts if a.source == source]

        if since:
            alerts = [a for a in alerts if a.timestamp >= since]

        if unacknowledged_only:
            alerts = [a for a in alerts if not a.acknowledged]

        if limit:
            alerts = alerts[-limit:]

        return alerts

    def acknowledge_alert(
        self,
        alert_id: str,
        by: str | None = None,
    ) -> bool:
        """Acknowledge an alert.

        Args:
            alert_id: ID of alert to acknowledge
            by: User/system acknowledging

        Returns:
            True if alert was found and acknowledged
        """
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.acknowledge(by)
                return True
        return False

    def acknowledge_all(
        self,
        by: str | None = None,
        severity: AlertSeverity | None = None,
    ) -> int:
        """Acknowledge all matching alerts.

        Args:
            by: User/system acknowledging
            severity: Only acknowledge alerts of this severity

        Returns:
            Number of alerts acknowledged
        """
        count = 0
        for alert in self._alerts:
            if alert.acknowledged:
                continue
            if severity and alert.severity != severity:
                continue
            alert.acknowledge(by)
            count += 1
        return count

    def clear_alerts(
        self,
        before: datetime | None = None,
        acknowledged_only: bool = True,
    ) -> int:
        """Clear old alerts.

        Args:
            before: Clear alerts before this timestamp
            acknowledged_only: Only clear acknowledged alerts

        Returns:
            Number of alerts cleared
        """
        original_count = len(self._alerts)

        def should_keep(alert: Alert) -> bool:
            if before and alert.timestamp >= before:
                return True
            if acknowledged_only and not alert.acknowledged:
                return True
            return False

        self._alerts = [a for a in self._alerts if should_keep(a)]

        return original_count - len(self._alerts)

    def summary(self) -> dict[str, Any]:
        """Get alert summary.

        Returns:
            Summary dictionary
        """
        by_severity = {}
        for sev in AlertSeverity:
            by_severity[sev.value] = len([
                a for a in self._alerts if a.severity == sev
            ])

        by_source = {}
        for alert in self._alerts:
            by_source[alert.source] = by_source.get(alert.source, 0) + 1

        return {
            "total_alerts": len(self._alerts),
            "unacknowledged": len([a for a in self._alerts if not a.acknowledged]),
            "by_severity": by_severity,
            "by_source": by_source,
        }

    def save_alerts(self, filepath: str | None = None) -> str:
        """Save alerts to file.

        Args:
            filepath: Path to save (default: storage_path/alerts.json)

        Returns:
            Path where alerts were saved
        """
        if filepath is None:
            if self.storage_path is None:
                raise ValueError("No filepath provided and no storage_path set")
            filepath = str(self.storage_path / "alerts.json")

        data = {
            "name": self.name,
            "alert_counter": self._alert_counter,
            "alerts": [a.to_dict() for a in self._alerts],
        }

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        return filepath

    def load_alerts(self, filepath: str) -> None:
        """Load alerts from file.

        Args:
            filepath: Path to load from
        """
        with open(filepath) as f:
            data = json.load(f)

        self._alert_counter = data.get("alert_counter", 0)
        self._alerts = [Alert.from_dict(a) for a in data.get("alerts", [])]


def create_drift_alert(
    alert_manager: AlertManager,
    column: str,
    drift_score: float,
    threshold: float,
    test_method: str = "unknown",
) -> Alert:
    """Convenience function to create drift alert.

    Args:
        alert_manager: AlertManager to use
        column: Column with drift
        drift_score: Detected drift score
        threshold: Threshold that was exceeded
        test_method: Statistical test used

    Returns:
        Created Alert
    """
    severity = AlertSeverity.CRITICAL if drift_score > threshold * 2 else AlertSeverity.WARNING

    return alert_manager.create_alert(
        title=f"Data Drift Detected: {column}",
        message=f"Column '{column}' shows significant drift (score: {drift_score:.4f}, threshold: {threshold:.4f})",
        severity=severity,
        source="drift_detector",
        metadata={
            "column": column,
            "drift_score": drift_score,
            "threshold": threshold,
            "test_method": test_method,
        },
    )


def create_performance_alert(
    alert_manager: AlertManager,
    model_name: str,
    metric_name: str,
    current_value: float,
    threshold: float,
    baseline_value: float | None = None,
) -> Alert:
    """Convenience function to create performance alert.

    Args:
        alert_manager: AlertManager to use
        model_name: Name of the model
        metric_name: Metric that triggered alert
        current_value: Current metric value
        threshold: Threshold that was crossed
        baseline_value: Optional baseline value

    Returns:
        Created Alert
    """
    if baseline_value:
        change_pct = ((current_value - baseline_value) / abs(baseline_value)) * 100
        message = f"Model '{model_name}' {metric_name} degraded to {current_value:.4f} ({change_pct:+.1f}% from baseline)"
    else:
        message = f"Model '{model_name}' {metric_name} ({current_value:.4f}) crossed threshold ({threshold:.4f})"

    return alert_manager.create_alert(
        title=f"Performance Degradation: {model_name}",
        message=message,
        severity=AlertSeverity.WARNING,
        source="model_tracker",
        metadata={
            "model_name": model_name,
            "metric_name": metric_name,
            "current_value": current_value,
            "threshold": threshold,
            "baseline_value": baseline_value,
        },
    )
