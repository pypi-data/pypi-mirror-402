"""Airflow hooks for DataCheck.

Provides hooks for connecting to DataCheck API and services.
"""

from typing import Any

# Import requests at module level for test mocking
try:
    import requests
except ImportError:
    requests = None

try:
    from airflow.hooks.base import BaseHook
    from airflow.exceptions import AirflowException

    AIRFLOW_AVAILABLE = True
except ImportError:
    # Create mock classes for testing without Airflow
    AIRFLOW_AVAILABLE = False

    class BaseHook:
        """Mock BaseHook for when Airflow is not installed."""

        def __init__(self, *args, **kwargs):
            pass

        @classmethod
        def get_connection(cls, conn_id: str):
            """Mock get_connection."""
            return type("Connection", (), {
                "host": "localhost",
                "port": 8000,
                "schema": "http",
                "login": None,
                "password": None,
                "extra_dejson": {},
            })()

    class AirflowException(Exception):
        """Mock AirflowException."""

        pass


class DataCheckHook(BaseHook):
    """Hook for connecting to DataCheck API.

    This hook provides methods for interacting with the DataCheck
    REST API from Airflow tasks.

    Attributes:
        conn_id: Airflow connection ID
    """

    conn_name_attr = "datacheck_conn_id"
    default_conn_name = "datacheck_default"
    conn_type = "http"
    hook_name = "DataCheck"

    def __init__(
        self,
        datacheck_conn_id: str = "datacheck_default",
        **kwargs,
    ):
        """Initialize DataCheckHook.

        Args:
            datacheck_conn_id: Airflow connection ID for DataCheck API
            **kwargs: Additional arguments
        """
        super().__init__()
        self.datacheck_conn_id = datacheck_conn_id
        self._session = None

    def get_conn(self):
        """Get connection details.

        Returns:
            Connection object with host, port, etc.
        """
        return self.get_connection(self.datacheck_conn_id)

    @property
    def base_url(self) -> str:
        """Get the base URL for the DataCheck API.

        Returns:
            Base URL string
        """
        conn = self.get_conn()
        schema = conn.schema or "http"
        host = conn.host or "localhost"
        port = conn.port or 8000
        return f"{schema}://{host}:{port}"

    def _get_session(self):
        """Get or create HTTP session.

        Returns:
            requests.Session object
        """
        if self._session is None:
            if requests is None:
                raise AirflowException(
                    "requests library is required for DataCheckHook"
                )
            self._session = requests.Session()

            # Add authentication if configured
            conn = self.get_conn()
            if conn.login and conn.password:
                self._session.auth = (conn.login, conn.password)

            # Add any custom headers from extras
            extra = conn.extra_dejson or {}
            if "headers" in extra:
                self._session.headers.update(extra["headers"])

        return self._session

    def test_connection(self) -> tuple:
        """Test the connection to DataCheck API.

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            response = self._get_session().get(
                f"{self.base_url}/health",
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                return True, f"Connection successful: {data.get('status', 'ok')}"
            else:
                return False, f"Unexpected status code: {response.status_code}"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def get_validation_summary(
        self,
        hours: int = 24,
    ) -> dict[str, Any]:
        """Get validation summary from API.

        Args:
            hours: Number of hours to look back

        Returns:
            Validation summary dictionary
        """
        response = self._get_session().get(
            f"{self.base_url}/api/validations/summary",
            params={"hours": hours},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def get_validations(
        self,
        limit: int = 10,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get recent validations from API.

        Args:
            limit: Maximum number of validations to return
            status: Filter by status ('passed', 'failed')

        Returns:
            List of validation records
        """
        params = {"limit": limit}
        if status:
            params["status"] = status

        response = self._get_session().get(
            f"{self.base_url}/api/validations",
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def get_validation(self, validation_id: int) -> dict[str, Any]:
        """Get validation details.

        Args:
            validation_id: Validation record ID

        Returns:
            Validation details dictionary
        """
        response = self._get_session().get(
            f"{self.base_url}/api/validations/{validation_id}",
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def create_validation(
        self,
        filename: str,
        status: str,
        pass_rate: float | None = None,
        quality_score: float | None = None,
        total_rows: int | None = None,
        total_columns: int | None = None,
        rules_run: int | None = None,
        rules_passed: int | None = None,
        rules_failed: int | None = None,
        duration_seconds: float | None = None,
        source: str = "airflow",
    ) -> dict[str, Any]:
        """Create a validation record.

        Args:
            filename: Name of the validated file
            status: Validation status ('passed', 'failed')
            pass_rate: Pass rate percentage
            quality_score: Quality score
            total_rows: Number of rows validated
            total_columns: Number of columns validated
            rules_run: Number of rules executed
            rules_passed: Number of rules passed
            rules_failed: Number of rules failed
            duration_seconds: Validation duration
            source: Source identifier

        Returns:
            Created validation record
        """
        data = {
            "filename": filename,
            "status": status,
            "source": source,
        }

        # Add optional fields
        if pass_rate is not None:
            data["pass_rate"] = pass_rate
        if quality_score is not None:
            data["quality_score"] = quality_score
        if total_rows is not None:
            data["total_rows"] = total_rows
        if total_columns is not None:
            data["total_columns"] = total_columns
        if rules_run is not None:
            data["rules_run"] = rules_run
        if rules_passed is not None:
            data["rules_passed"] = rules_passed
        if rules_failed is not None:
            data["rules_failed"] = rules_failed
        if duration_seconds is not None:
            data["duration_seconds"] = duration_seconds

        response = self._get_session().post(
            f"{self.base_url}/api/validations",
            json=data,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def get_alerts(
        self,
        hours: int = 24,
        unacknowledged_only: bool = False,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Get alerts from API.

        Args:
            hours: Number of hours to look back
            unacknowledged_only: Only return unacknowledged alerts
            limit: Maximum number of alerts to return

        Returns:
            List of alert records
        """
        response = self._get_session().get(
            f"{self.base_url}/api/alerts",
            params={
                "hours": hours,
                "unacknowledged_only": unacknowledged_only,
                "limit": limit,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def create_alert(
        self,
        title: str,
        message: str,
        severity: str = "warning",
        source: str = "airflow",
        validation_id: int | None = None,
    ) -> dict[str, Any]:
        """Create an alert.

        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity ('info', 'warning', 'error', 'critical')
            source: Source identifier
            validation_id: Optional associated validation ID

        Returns:
            Created alert record
        """
        data = {
            "title": title,
            "message": message,
            "severity": severity,
            "source": source,
        }
        if validation_id is not None:
            data["validation_id"] = validation_id

        response = self._get_session().post(
            f"{self.base_url}/api/alerts",
            json=data,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def acknowledge_alert(self, alert_id: int) -> dict[str, Any]:
        """Acknowledge an alert.

        Args:
            alert_id: Alert ID to acknowledge

        Returns:
            Acknowledgment response
        """
        response = self._get_session().post(
            f"{self.base_url}/api/alerts/{alert_id}/acknowledge",
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def get_trends(
        self,
        hours: int = 24,
        group_by: str = "hour",
    ) -> list[dict[str, Any]]:
        """Get validation trends.

        Args:
            hours: Number of hours to look back
            group_by: Grouping interval ('hour', 'day', 'week')

        Returns:
            List of trend data points
        """
        response = self._get_session().get(
            f"{self.base_url}/api/validations/trends",
            params={
                "hours": hours,
                "group_by": group_by,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def get_top_issues(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get top validation issues.

        Args:
            limit: Maximum number of issues to return

        Returns:
            List of top issue records
        """
        response = self._get_session().get(
            f"{self.base_url}/api/validations/top-issues",
            params={"limit": limit},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def record_metric(
        self,
        name: str,
        value: float,
        source: str = "airflow",
    ) -> dict[str, Any]:
        """Record a metric.

        Args:
            name: Metric name
            value: Metric value
            source: Source identifier

        Returns:
            Response from API
        """
        response = self._get_session().post(
            f"{self.base_url}/api/metrics",
            json={
                "name": name,
                "value": value,
                "source": source,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def close(self):
        """Close the HTTP session."""
        if self._session:
            self._session.close()
            self._session = None
