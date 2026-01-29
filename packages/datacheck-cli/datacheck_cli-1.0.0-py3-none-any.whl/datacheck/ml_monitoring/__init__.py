"""ML Monitoring module for DataCheck.

Provides data drift detection, distribution monitoring, and model performance tracking.
"""

from datacheck.ml_monitoring.drift_detector import (
    DriftDetector,
    DriftResult,
    DriftType,
    ColumnDrift,
    detect_drift,
)
from datacheck.ml_monitoring.distribution_monitor import (
    DistributionMonitor,
    DistributionProfile,
    DistributionComparison,
    create_baseline_profile,
)
from datacheck.ml_monitoring.model_tracker import (
    ModelTracker,
    ModelMetrics,
    PredictionLog,
    PerformanceAlert,
)
from datacheck.ml_monitoring.alerts import (
    AlertManager,
    Alert,
    AlertSeverity,
    AlertChannel,
)

__all__ = [
    # Drift detection
    "DriftDetector",
    "DriftResult",
    "DriftType",
    "ColumnDrift",
    "detect_drift",
    # Distribution monitoring
    "DistributionMonitor",
    "DistributionProfile",
    "DistributionComparison",
    "create_baseline_profile",
    # Model tracking
    "ModelTracker",
    "ModelMetrics",
    "PredictionLog",
    "PerformanceAlert",
    # Alerts
    "AlertManager",
    "Alert",
    "AlertSeverity",
    "AlertChannel",
]
