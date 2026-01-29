"""Model performance tracking module.

Provides capabilities for tracking ML model predictions and performance metrics.
"""

from dataclasses import dataclass, field
from typing import Any
from enum import Enum
import pandas as pd
import numpy as np
from datetime import datetime
import json
from pathlib import Path


class MetricType(Enum):
    """Type of performance metric."""

    # Classification
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    AUC_ROC = "auc_roc"
    LOG_LOSS = "log_loss"

    # Regression
    MAE = "mae"
    MSE = "mse"
    RMSE = "rmse"
    R2 = "r2"
    MAPE = "mape"

    # Custom
    CUSTOM = "custom"


@dataclass
class ModelMetrics:
    """Container for model performance metrics."""

    model_name: str
    model_version: str
    metrics: dict[str, float]
    timestamp: datetime = field(default_factory=datetime.now)
    sample_size: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "metrics": self.metrics,
            "timestamp": self.timestamp.isoformat(),
            "sample_size": self.sample_size,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelMetrics":
        """Create from dictionary."""
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class PredictionLog:
    """Log of model predictions for monitoring."""

    model_name: str
    model_version: str
    predictions: list[Any]
    actuals: list[Any] | None = None
    features: pd.DataFrame | None = None
    timestamps: list[datetime] | None = None
    prediction_probabilities: list[list[float]] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __len__(self) -> int:
        """Return number of predictions."""
        return len(self.predictions)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert to DataFrame."""
        data = {
            "prediction": self.predictions,
        }

        if self.actuals:
            data["actual"] = self.actuals

        if self.timestamps:
            data["timestamp"] = self.timestamps

        df = pd.DataFrame(data)

        if self.features is not None:
            df = pd.concat([df, self.features.reset_index(drop=True)], axis=1)

        return df


@dataclass
class PerformanceAlert:
    """Alert for performance degradation."""

    alert_id: str
    model_name: str
    model_version: str
    metric_name: str
    current_value: float
    threshold_value: float
    baseline_value: float | None = None
    severity: str = "warning"  # warning, critical
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "threshold_value": self.threshold_value,
            "baseline_value": self.baseline_value,
            "severity": self.severity,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class ModelTracker:
    """Tracker for ML model performance.

    Tracks predictions, calculates metrics, and detects performance degradation.
    """

    def __init__(
        self,
        model_name: str,
        model_version: str = "1.0.0",
        storage_path: str | None = None,
    ):
        """Initialize model tracker.

        Args:
            model_name: Name of the model being tracked
            model_version: Version of the model
            storage_path: Path to store metrics history
        """
        self.model_name = model_name
        self.model_version = model_version
        self.storage_path = Path(storage_path) if storage_path else None

        self._prediction_logs: list[PredictionLog] = []
        self._metrics_history: list[ModelMetrics] = []
        self._baseline_metrics: ModelMetrics | None = None
        self._thresholds: dict[str, dict[str, float]] = {}
        self._alerts: list[PerformanceAlert] = []
        self._alert_counter = 0

    def log_predictions(
        self,
        predictions: list[Any],
        actuals: list[Any] | None = None,
        features: pd.DataFrame | None = None,
        timestamps: list[datetime] | None = None,
        prediction_probabilities: list[list[float]] | None = None,
    ) -> PredictionLog:
        """Log model predictions.

        Args:
            predictions: List of predictions
            actuals: List of actual values (for performance calculation)
            features: DataFrame of input features
            timestamps: Timestamps for each prediction
            prediction_probabilities: Class probabilities for classification

        Returns:
            PredictionLog object
        """
        log = PredictionLog(
            model_name=self.model_name,
            model_version=self.model_version,
            predictions=predictions,
            actuals=actuals,
            features=features,
            timestamps=timestamps,
            prediction_probabilities=prediction_probabilities,
        )

        self._prediction_logs.append(log)

        # Calculate metrics if actuals provided
        if actuals:
            metrics = self.calculate_metrics(predictions, actuals)
            self._check_thresholds(metrics)

        return log

    def calculate_metrics(
        self,
        predictions: list[Any],
        actuals: list[Any],
        task_type: str = "auto",
    ) -> ModelMetrics:
        """Calculate performance metrics.

        Args:
            predictions: List of predictions
            actuals: List of actual values
            task_type: 'classification', 'regression', or 'auto'

        Returns:
            ModelMetrics object
        """
        predictions = np.array(predictions)
        actuals = np.array(actuals)

        # Detect task type
        if task_type == "auto":
            unique_actuals = np.unique(actuals)
            if len(unique_actuals) <= 10 and all(
                isinstance(a, int | np.integer | str | bool) for a in actuals[:100]
            ):
                task_type = "classification"
            else:
                task_type = "regression"

        if task_type == "classification":
            metrics = self._calculate_classification_metrics(predictions, actuals)
        else:
            metrics = self._calculate_regression_metrics(predictions, actuals)

        model_metrics = ModelMetrics(
            model_name=self.model_name,
            model_version=self.model_version,
            metrics=metrics,
            sample_size=len(predictions),
        )

        self._metrics_history.append(model_metrics)

        return model_metrics

    def _calculate_classification_metrics(
        self,
        predictions: np.ndarray,
        actuals: np.ndarray,
    ) -> dict[str, float]:
        """Calculate classification metrics."""
        metrics = {}

        # Accuracy
        metrics["accuracy"] = float(np.mean(predictions == actuals))

        # Get unique classes
        classes = np.unique(np.concatenate([predictions, actuals]))

        if len(classes) == 2:
            # Binary classification
            pos_class = classes[1]

            tp = np.sum((predictions == pos_class) & (actuals == pos_class))
            fp = np.sum((predictions == pos_class) & (actuals != pos_class))
            fn = np.sum((predictions != pos_class) & (actuals == pos_class))

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

            metrics["precision"] = float(precision)
            metrics["recall"] = float(recall)
            metrics["f1_score"] = float(
                2 * precision * recall / (precision + recall)
                if (precision + recall) > 0 else 0.0
            )
        else:
            # Multi-class: macro average
            precisions = []
            recalls = []

            for cls in classes:
                tp = np.sum((predictions == cls) & (actuals == cls))
                fp = np.sum((predictions == cls) & (actuals != cls))
                fn = np.sum((predictions != cls) & (actuals == cls))

                precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

                precisions.append(precision)
                recalls.append(recall)

            metrics["precision_macro"] = float(np.mean(precisions))
            metrics["recall_macro"] = float(np.mean(recalls))
            metrics["f1_score_macro"] = float(
                2 * metrics["precision_macro"] * metrics["recall_macro"] /
                (metrics["precision_macro"] + metrics["recall_macro"])
                if (metrics["precision_macro"] + metrics["recall_macro"]) > 0 else 0.0
            )

        return metrics

    def _calculate_regression_metrics(
        self,
        predictions: np.ndarray,
        actuals: np.ndarray,
    ) -> dict[str, float]:
        """Calculate regression metrics."""
        predictions = predictions.astype(float)
        actuals = actuals.astype(float)

        errors = predictions - actuals

        metrics = {
            "mae": float(np.mean(np.abs(errors))),
            "mse": float(np.mean(errors ** 2)),
            "rmse": float(np.sqrt(np.mean(errors ** 2))),
        }

        # R-squared
        ss_res = np.sum(errors ** 2)
        ss_tot = np.sum((actuals - np.mean(actuals)) ** 2)
        metrics["r2"] = float(1 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0

        # MAPE (avoid division by zero)
        non_zero_mask = actuals != 0
        if np.any(non_zero_mask):
            mape = np.mean(np.abs(errors[non_zero_mask] / actuals[non_zero_mask])) * 100
            metrics["mape"] = float(mape)

        return metrics

    def set_baseline(self, metrics: ModelMetrics | None = None) -> ModelMetrics:
        """Set baseline metrics for comparison.

        Args:
            metrics: Specific metrics to use as baseline (default: latest)

        Returns:
            Baseline metrics
        """
        if metrics:
            self._baseline_metrics = metrics
        elif self._metrics_history:
            self._baseline_metrics = self._metrics_history[-1]
        else:
            raise ValueError("No metrics available for baseline")

        return self._baseline_metrics

    def set_threshold(
        self,
        metric_name: str,
        warning_threshold: float | None = None,
        critical_threshold: float | None = None,
        direction: str = "lower_is_worse",
    ) -> None:
        """Set alerting thresholds for a metric.

        Args:
            metric_name: Name of the metric
            warning_threshold: Threshold for warning alert
            critical_threshold: Threshold for critical alert
            direction: 'lower_is_worse' or 'higher_is_worse'
        """
        self._thresholds[metric_name] = {
            "warning": warning_threshold,
            "critical": critical_threshold,
            "direction": direction,
        }

    def _check_thresholds(self, metrics: ModelMetrics) -> list[PerformanceAlert]:
        """Check metrics against thresholds."""
        new_alerts = []

        for metric_name, value in metrics.metrics.items():
            if metric_name not in self._thresholds:
                continue

            threshold_config = self._thresholds[metric_name]
            direction = threshold_config["direction"]

            for level in ["critical", "warning"]:
                threshold = threshold_config.get(level)
                if threshold is None:
                    continue

                triggered = False
                if direction == "lower_is_worse" and value < threshold:
                    triggered = True
                elif direction == "higher_is_worse" and value > threshold:
                    triggered = True

                if triggered:
                    self._alert_counter += 1
                    alert = PerformanceAlert(
                        alert_id=f"alert_{self._alert_counter}",
                        model_name=self.model_name,
                        model_version=self.model_version,
                        metric_name=metric_name,
                        current_value=value,
                        threshold_value=threshold,
                        baseline_value=self._baseline_metrics.metrics.get(metric_name)
                        if self._baseline_metrics else None,
                        severity=level,
                        message=f"{metric_name} ({value:.4f}) crossed {level} threshold ({threshold:.4f})",
                    )
                    new_alerts.append(alert)
                    self._alerts.append(alert)
                    break  # Only trigger highest severity

        return new_alerts

    def get_metrics_history(
        self,
        since: datetime | None = None,
        limit: int | None = None,
    ) -> list[ModelMetrics]:
        """Get metrics history.

        Args:
            since: Only return metrics after this timestamp
            limit: Maximum number of records to return

        Returns:
            List of ModelMetrics
        """
        history = self._metrics_history

        if since:
            history = [m for m in history if m.timestamp >= since]

        if limit:
            history = history[-limit:]

        return history

    def get_alerts(
        self,
        severity: str | None = None,
        since: datetime | None = None,
    ) -> list[PerformanceAlert]:
        """Get alerts.

        Args:
            severity: Filter by severity ('warning' or 'critical')
            since: Only return alerts after this timestamp

        Returns:
            List of alerts
        """
        alerts = self._alerts

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        if since:
            alerts = [a for a in alerts if a.timestamp >= since]

        return alerts

    def get_prediction_logs(
        self,
        limit: int | None = None,
    ) -> list[PredictionLog]:
        """Get prediction logs.

        Args:
            limit: Maximum number of logs to return

        Returns:
            List of PredictionLog
        """
        logs = self._prediction_logs

        if limit:
            logs = logs[-limit:]

        return logs

    def performance_report(self) -> dict[str, Any]:
        """Generate performance report.

        Returns:
            Dictionary with performance summary
        """
        report = {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "total_predictions": sum(len(log) for log in self._prediction_logs),
            "metrics_records": len(self._metrics_history),
            "alerts_count": len(self._alerts),
        }

        if self._metrics_history:
            latest = self._metrics_history[-1]
            report["latest_metrics"] = latest.metrics
            report["latest_timestamp"] = latest.timestamp.isoformat()

        if self._baseline_metrics:
            report["baseline_metrics"] = self._baseline_metrics.metrics

        if self._alerts:
            report["recent_alerts"] = [
                a.to_dict() for a in self._alerts[-5:]
            ]

        return report

    def save_history(self, filepath: str | None = None) -> str:
        """Save metrics history to file.

        Args:
            filepath: Path to save (default: storage_path/metrics_history.json)

        Returns:
            Path where data was saved
        """
        if filepath is None:
            if self.storage_path is None:
                raise ValueError("No filepath provided and no storage_path set")
            filepath = str(self.storage_path / "metrics_history.json")

        data = {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "metrics_history": [m.to_dict() for m in self._metrics_history],
            "baseline_metrics": self._baseline_metrics.to_dict() if self._baseline_metrics else None,
            "alerts": [a.to_dict() for a in self._alerts],
        }

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        return filepath

    def load_history(self, filepath: str) -> None:
        """Load metrics history from file.

        Args:
            filepath: Path to load from
        """
        with open(filepath) as f:
            data = json.load(f)

        self._metrics_history = [
            ModelMetrics.from_dict(m) for m in data.get("metrics_history", [])
        ]

        if data.get("baseline_metrics"):
            self._baseline_metrics = ModelMetrics.from_dict(data["baseline_metrics"])
