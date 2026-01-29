"""Airflow sensors for DataCheck.

Provides sensors for waiting on data quality conditions.
"""

from typing import Any
from collections.abc import Sequence

# Import requests at module level for test mocking
try:
    import requests
except ImportError:
    requests = None

try:
    from airflow.sensors.base import BaseSensorOperator
    from airflow.utils.decorators import apply_defaults
    from airflow.exceptions import AirflowException

    AIRFLOW_AVAILABLE = True
except ImportError:
    # Create mock classes for testing without Airflow
    AIRFLOW_AVAILABLE = False

    import logging

    class BaseSensorOperator:
        """Mock BaseSensorOperator for when Airflow is not installed."""

        def __init__(self, task_id: str, **kwargs):
            self.task_id = task_id
            self.log = logging.getLogger(f"datacheck.sensor.{task_id}")
            self.poke_interval = kwargs.get("poke_interval", 60)
            self.timeout = kwargs.get("timeout", 3600)
            self.mode = kwargs.get("mode", "poke")
            for key, value in kwargs.items():
                setattr(self, key, value)

        def poke(self, context: dict[str, Any]) -> bool:
            raise NotImplementedError

        def __rshift__(self, other):
            """Support >> operator for task dependencies."""
            return other

        def __lshift__(self, other):
            """Support << operator for task dependencies."""
            return self

    def apply_defaults(func):
        """Mock decorator."""
        return func

    class AirflowException(Exception):
        """Mock AirflowException."""

        pass


class DataCheckQualitySensor(BaseSensorOperator):
    """Sensor that waits for data quality to meet specified thresholds.

    This sensor monitors a data file and waits until it meets the
    specified quality thresholds before proceeding.

    Attributes:
        file_path: Path to the data file to monitor
        min_quality_score: Minimum quality score required
        min_pass_rate: Minimum pass rate required
        config_path: Path to validation configuration
    """

    template_fields: Sequence[str] = ("file_path", "config_path")
    ui_color = "#4CAF50"
    ui_fgcolor = "#FFFFFF"

    @apply_defaults
    def __init__(
        self,
        file_path: str,
        min_quality_score: float = 90.0,
        min_pass_rate: float = 95.0,
        config_path: str | None = None,
        **kwargs,
    ):
        """Initialize DataCheckQualitySensor.

        Args:
            file_path: Path to the data file to monitor
            min_quality_score: Minimum quality score required (0-100)
            min_pass_rate: Minimum pass rate required (0-100)
            config_path: Path to validation configuration
            **kwargs: Additional arguments passed to BaseSensorOperator
        """
        super().__init__(**kwargs)
        self.file_path = file_path
        self.min_quality_score = min_quality_score
        self.min_pass_rate = min_pass_rate
        self.config_path = config_path

    def poke(self, context: dict[str, Any]) -> bool:
        """Check if data quality meets thresholds.

        Args:
            context: Airflow context dictionary

        Returns:
            True if quality thresholds are met, False otherwise
        """
        from datacheck.validation import Validator
        from pathlib import Path
        import pandas as pd

        self.log.info(f"Checking data quality for: {self.file_path}")

        # Check if file exists
        if not Path(self.file_path).exists():
            self.log.info(f"File does not exist yet: {self.file_path}")
            return False

        try:
            # Load data using pandas directly
            file_path = Path(self.file_path)
            if file_path.suffix == ".csv":
                df = pd.read_csv(file_path)
            elif file_path.suffix == ".parquet":
                df = pd.read_parquet(file_path)
            else:
                df = pd.read_csv(file_path)

            # Run validation
            validator = Validator()
            result = validator.validate(df)

            # Use pass_rate as quality score
            quality_score = result.pass_rate

            # Log current quality
            self.log.info(
                f"Current quality - Score: {quality_score:.1f}, "
                f"Pass rate: {result.pass_rate:.1f}%"
            )

            # Check thresholds
            meets_quality = quality_score >= self.min_quality_score
            meets_pass_rate = result.pass_rate >= self.min_pass_rate

            if meets_quality and meets_pass_rate:
                self.log.info("Data quality thresholds met!")
                return True
            else:
                if not meets_quality:
                    self.log.info(
                        f"Quality score {quality_score:.1f} < "
                        f"{self.min_quality_score}"
                    )
                if not meets_pass_rate:
                    self.log.info(
                        f"Pass rate {result.pass_rate:.1f}% < {self.min_pass_rate}%"
                    )
                return False

        except Exception as e:
            self.log.warning(f"Error checking data quality: {e}")
            return False


class DataCheckAlertSensor(BaseSensorOperator):
    """Sensor that waits for DataCheck alerts to be resolved.

    This sensor monitors the DataCheck API for unresolved alerts
    and waits until all alerts are acknowledged.

    Attributes:
        api_url: DataCheck API URL
        severity_filter: Only monitor alerts of this severity or higher
        source_filter: Only monitor alerts from this source
    """

    template_fields: Sequence[str] = ("api_url", "source_filter")
    ui_color = "#F44336"
    ui_fgcolor = "#FFFFFF"

    SEVERITY_LEVELS = {
        "info": 0,
        "warning": 1,
        "error": 2,
        "critical": 3,
    }

    @apply_defaults
    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        severity_filter: str = "warning",
        source_filter: str | None = None,
        max_alerts: int = 0,
        check_hours: int = 24,
        **kwargs,
    ):
        """Initialize DataCheckAlertSensor.

        Args:
            api_url: DataCheck API URL
            severity_filter: Minimum severity to monitor ('info', 'warning', 'error', 'critical')
            source_filter: Only monitor alerts from this source
            max_alerts: Maximum unacknowledged alerts allowed (0 = none)
            check_hours: Hours to look back for alerts
            **kwargs: Additional arguments passed to BaseSensorOperator
        """
        super().__init__(**kwargs)
        self.api_url = api_url
        self.severity_filter = severity_filter
        self.source_filter = source_filter
        self.max_alerts = max_alerts
        self.check_hours = check_hours

    def poke(self, context: dict[str, Any]) -> bool:
        """Check if there are unresolved alerts.

        Args:
            context: Airflow context dictionary

        Returns:
            True if no blocking alerts, False if alerts need attention
        """
        if requests is None:
            self.log.warning("requests library not available, skipping API check")
            return True

        self.log.info(f"Checking for unresolved alerts at: {self.api_url}")

        try:
            # Query alerts API
            response = requests.get(
                f"{self.api_url}/api/alerts",
                params={
                    "hours": self.check_hours,
                    "unacknowledged_only": True,
                },
                timeout=30,
            )
            response.raise_for_status()
            alerts = response.json()

            # Filter by severity
            min_severity = self.SEVERITY_LEVELS.get(self.severity_filter, 1)
            filtered_alerts = [
                a for a in alerts
                if self.SEVERITY_LEVELS.get(a.get("severity", "info"), 0) >= min_severity
            ]

            # Filter by source if specified
            if self.source_filter:
                filtered_alerts = [
                    a for a in filtered_alerts
                    if a.get("source") == self.source_filter
                ]

            alert_count = len(filtered_alerts)

            # Log alert status
            if alert_count > 0:
                self.log.info(f"Found {alert_count} unacknowledged alerts")
                for alert in filtered_alerts[:5]:  # Show first 5
                    self.log.info(
                        f"  - [{alert.get('severity', 'unknown').upper()}] "
                        f"{alert.get('title', 'Unknown')}"
                    )
                if alert_count > 5:
                    self.log.info(f"  ... and {alert_count - 5} more")
            else:
                self.log.info("No unacknowledged alerts found")

            # Check against threshold
            return alert_count <= self.max_alerts

        except Exception as e:
            self.log.warning(f"Error checking alerts: {e}")
            # Return True to avoid blocking pipeline on API errors
            return True


class DataCheckFileSensor(BaseSensorOperator):
    """Sensor that waits for a data file to be available and valid.

    This sensor checks if a file exists and contains valid data
    before proceeding.

    Attributes:
        file_path: Path to the data file
        min_rows: Minimum number of rows required
        required_columns: List of columns that must be present
    """

    template_fields: Sequence[str] = ("file_path",)
    ui_color = "#2196F3"
    ui_fgcolor = "#FFFFFF"

    @apply_defaults
    def __init__(
        self,
        file_path: str,
        min_rows: int = 1,
        required_columns: Sequence[str] | None = None,
        check_not_empty: bool = True,
        **kwargs,
    ):
        """Initialize DataCheckFileSensor.

        Args:
            file_path: Path to the data file
            min_rows: Minimum number of rows required
            required_columns: List of columns that must be present
            check_not_empty: Whether to check that file is not empty
            **kwargs: Additional arguments passed to BaseSensorOperator
        """
        super().__init__(**kwargs)
        self.file_path = file_path
        self.min_rows = min_rows
        self.required_columns = list(required_columns) if required_columns else []
        self.check_not_empty = check_not_empty

    def poke(self, context: dict[str, Any]) -> bool:
        """Check if file is available and valid.

        Args:
            context: Airflow context dictionary

        Returns:
            True if file is valid, False otherwise
        """
        from pathlib import Path
        import pandas as pd

        self.log.info(f"Checking file: {self.file_path}")

        # Check if file exists
        path = Path(self.file_path)
        if not path.exists():
            self.log.info(f"File does not exist: {self.file_path}")
            return False

        # Check file size
        if self.check_not_empty and path.stat().st_size == 0:
            self.log.info(f"File is empty: {self.file_path}")
            return False

        try:
            # Load data using pandas directly
            if path.suffix == ".csv":
                df = pd.read_csv(path)
            elif path.suffix == ".parquet":
                df = pd.read_parquet(path)
            else:
                df = pd.read_csv(path)

            # Check row count
            if len(df) < self.min_rows:
                self.log.info(
                    f"File has {len(df)} rows, need at least {self.min_rows}"
                )
                return False

            # Check required columns
            if self.required_columns:
                missing = set(self.required_columns) - set(df.columns)
                if missing:
                    self.log.info(f"Missing required columns: {missing}")
                    return False

            self.log.info(
                f"File is valid: {len(df)} rows, {len(df.columns)} columns"
            )
            return True

        except Exception as e:
            self.log.info(f"Error reading file: {e}")
            return False
