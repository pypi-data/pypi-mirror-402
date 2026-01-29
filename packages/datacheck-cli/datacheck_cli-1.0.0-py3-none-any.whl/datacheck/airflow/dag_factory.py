"""DAG factory for DataCheck.

Provides utilities for creating DataCheck DAGs programmatically.
"""

from typing import Any
from collections.abc import Callable
from datetime import datetime, timedelta

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    from airflow.operators.dummy import DummyOperator
    from airflow.utils.task_group import TaskGroup

    AIRFLOW_AVAILABLE = True
except ImportError:
    # Create mock classes for testing without Airflow
    AIRFLOW_AVAILABLE = False

    class DAG:
        """Mock DAG for when Airflow is not installed."""

        def __init__(self, dag_id: str, **kwargs):
            self.dag_id = dag_id
            self.default_args = kwargs.get("default_args", {})
            self.schedule_interval = kwargs.get("schedule_interval")
            self.start_date = kwargs.get("start_date")
            self.catchup = kwargs.get("catchup", False)
            self.tags = kwargs.get("tags", [])
            self.description = kwargs.get("description")
            self._tasks = []

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    class MockTaskMixin:
        """Mixin to support task dependency operators."""

        def __rshift__(self, other):
            """Support >> operator for task dependencies."""
            return other

        def __lshift__(self, other):
            """Support << operator for task dependencies."""
            return self

    class DummyOperator(MockTaskMixin):
        """Mock DummyOperator."""

        def __init__(self, task_id: str, **kwargs):
            self.task_id = task_id

    class PythonOperator(MockTaskMixin):
        """Mock PythonOperator."""

        def __init__(self, task_id: str, python_callable: Callable, **kwargs):
            self.task_id = task_id
            self.python_callable = python_callable

    class TaskGroup(MockTaskMixin):
        """Mock TaskGroup."""

        def __init__(self, group_id: str, **kwargs):
            self.group_id = group_id

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass


from datacheck.airflow.operators import (
    DataCheckValidateOperator,
    DataCheckSchemaOperator,
    DataCheckDriftOperator,
)
from datacheck.airflow.sensors import DataCheckFileSensor


# Default DAG arguments
DEFAULT_ARGS = {
    "owner": "datacheck",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


def create_validation_dag(
    dag_id: str,
    file_paths: list[str],
    schedule_interval: str | None = "@daily",
    start_date: datetime | None = None,
    config_path: str | None = None,
    min_quality_score: float = 80.0,
    min_pass_rate: float = 90.0,
    fail_on_error: bool = True,
    default_args: dict[str, Any] | None = None,
    tags: list[str] | None = None,
    description: str | None = None,
    **kwargs,
) -> DAG:
    """Create a DAG for validating multiple data files.

    This factory creates a complete DAG with validation tasks for
    each file, including quality checks and error handling.

    Args:
        dag_id: Unique identifier for the DAG
        file_paths: List of file paths to validate
        schedule_interval: Cron expression or preset (@daily, @hourly, etc.)
        start_date: DAG start date (defaults to yesterday)
        config_path: Path to validation configuration file
        min_quality_score: Minimum quality score required
        min_pass_rate: Minimum pass rate required
        fail_on_error: Whether to fail the DAG on validation errors
        default_args: Custom default arguments for tasks
        tags: Tags for the DAG
        description: DAG description
        **kwargs: Additional DAG arguments

    Returns:
        Configured Airflow DAG

    Example:
        >>> dag = create_validation_dag(
        ...     dag_id="data_quality_checks",
        ...     file_paths=[
        ...         "/data/sales.csv",
        ...         "/data/customers.parquet",
        ...     ],
        ...     min_quality_score=90.0,
        ...     schedule_interval="0 6 * * *",
        ... )
    """
    # Set defaults
    if start_date is None:
        start_date = datetime.now() - timedelta(days=1)

    if default_args is None:
        default_args = DEFAULT_ARGS.copy()

    if tags is None:
        tags = ["datacheck", "data-quality"]

    if description is None:
        description = f"DataCheck validation DAG for {len(file_paths)} files"

    # Create DAG
    dag = DAG(
        dag_id=dag_id,
        default_args=default_args,
        description=description,
        schedule_interval=schedule_interval,
        start_date=start_date,
        catchup=False,
        tags=tags,
        **kwargs,
    )

    with dag:
        # Start task
        start = DummyOperator(task_id="start")

        # Create validation tasks for each file
        validation_tasks = []
        for i, file_path in enumerate(file_paths):
            # Extract filename for task ID
            file_name = file_path.split("/")[-1].replace(".", "_")
            task_id = f"validate_{file_name}_{i}"

            # Create file sensor
            sensor = DataCheckFileSensor(
                task_id=f"wait_for_{file_name}_{i}",
                file_path=file_path,
                poke_interval=60,
                timeout=3600,
                mode="poke",
            )

            # Create validation task
            validate = DataCheckValidateOperator(
                task_id=task_id,
                file_path=file_path,
                config_path=config_path,
                min_quality_score=min_quality_score,
                min_pass_rate=min_pass_rate,
                fail_on_error=fail_on_error,
            )

            # Set dependencies
            start >> sensor >> validate
            validation_tasks.append(validate)

        # End task
        end = DummyOperator(task_id="end")

        # Connect all validation tasks to end
        for task in validation_tasks:
            task >> end

    return dag


def create_monitoring_dag(
    dag_id: str,
    current_path: str,
    baseline_path: str,
    schedule_interval: str | None = "@daily",
    start_date: datetime | None = None,
    drift_threshold: float = 0.1,
    drift_method: str = "psi",
    config_path: str | None = None,
    min_quality_score: float = 80.0,
    alert_on_drift: bool = True,
    default_args: dict[str, Any] | None = None,
    tags: list[str] | None = None,
    description: str | None = None,
    **kwargs,
) -> DAG:
    """Create a DAG for monitoring data quality and drift.

    This factory creates a complete monitoring DAG that validates
    data quality and checks for data drift.

    Args:
        dag_id: Unique identifier for the DAG
        current_path: Path to current data file
        baseline_path: Path to baseline data file for drift comparison
        schedule_interval: Cron expression or preset
        start_date: DAG start date
        drift_threshold: Threshold for drift detection
        drift_method: Method for drift detection ('psi', 'ks', 'wasserstein')
        config_path: Path to validation configuration
        min_quality_score: Minimum quality score required
        alert_on_drift: Whether to create alerts on drift detection
        default_args: Custom default arguments
        tags: Tags for the DAG
        description: DAG description
        **kwargs: Additional DAG arguments

    Returns:
        Configured Airflow DAG

    Example:
        >>> dag = create_monitoring_dag(
        ...     dag_id="data_monitoring",
        ...     current_path="/data/current/sales.csv",
        ...     baseline_path="/data/baseline/sales.csv",
        ...     drift_threshold=0.15,
        ...     schedule_interval="0 */4 * * *",
        ... )
    """
    # Set defaults
    if start_date is None:
        start_date = datetime.now() - timedelta(days=1)

    if default_args is None:
        default_args = DEFAULT_ARGS.copy()

    if tags is None:
        tags = ["datacheck", "monitoring", "drift-detection"]

    if description is None:
        description = "DataCheck monitoring DAG with drift detection"

    # Create DAG
    dag = DAG(
        dag_id=dag_id,
        default_args=default_args,
        description=description,
        schedule_interval=schedule_interval,
        start_date=start_date,
        catchup=False,
        tags=tags,
        **kwargs,
    )

    with dag:
        # Start task
        start = DummyOperator(task_id="start")

        # Wait for current data file
        wait_for_data = DataCheckFileSensor(
            task_id="wait_for_current_data",
            file_path=current_path,
            poke_interval=60,
            timeout=3600,
            mode="poke",
        )

        # Validate current data
        validate = DataCheckValidateOperator(
            task_id="validate_data",
            file_path=current_path,
            config_path=config_path,
            min_quality_score=min_quality_score,
            fail_on_error=False,  # Continue to drift check even if validation fails
        )

        # Check for drift
        drift_check = DataCheckDriftOperator(
            task_id="check_drift",
            current_path=current_path,
            baseline_path=baseline_path,
            threshold=drift_threshold,
            method=drift_method,
            fail_on_drift=False,  # Don't fail, just report
        )

        # Alert task (Python operator for flexibility)
        def _send_alerts(**context):
            """Send alerts based on validation and drift results."""
            ti = context["ti"]

            # Get validation results
            validation_results = ti.xcom_pull(
                task_ids="validate_data",
                key="validation_results",
            )

            # Get drift results
            drift_results = ti.xcom_pull(
                task_ids="check_drift",
                key="drift_results",
            )

            alerts = []

            # Check validation results
            if validation_results:
                if not validation_results.get("met_quality_threshold", True):
                    alerts.append({
                        "title": "Quality Score Below Threshold",
                        "message": (
                            f"Quality score {validation_results.get('quality_score', 0):.1f} "
                            f"is below the minimum threshold"
                        ),
                        "severity": "warning",
                    })

                if not validation_results.get("met_pass_rate_threshold", True):
                    alerts.append({
                        "title": "Pass Rate Below Threshold",
                        "message": (
                            f"Pass rate {validation_results.get('pass_rate', 0):.1f}% "
                            f"is below the minimum threshold"
                        ),
                        "severity": "warning",
                    })

            # Check drift results
            if drift_results and drift_results.get("drift_detected"):
                drifted_cols = drift_results.get("drifted_columns", [])
                alerts.append({
                    "title": "Data Drift Detected",
                    "message": (
                        f"Drift detected with score {drift_results.get('drift_score', 0):.4f}. "
                        f"Affected columns: {', '.join(drifted_cols)}"
                    ),
                    "severity": "error" if len(drifted_cols) > 3 else "warning",
                })

            # Log and optionally send alerts
            for alert in alerts:
                print(f"[{alert['severity'].upper()}] {alert['title']}: {alert['message']}")

            # Push alerts to XCom for downstream processing
            ti.xcom_push(key="alerts", value=alerts)

            return len(alerts)

        process_alerts = PythonOperator(
            task_id="process_alerts",
            python_callable=_send_alerts,
            provide_context=True,
        )

        # End task
        end = DummyOperator(task_id="end")

        # Set dependencies
        start >> wait_for_data >> validate >> drift_check >> process_alerts >> end

    return dag


def create_schema_validation_dag(
    dag_id: str,
    file_path: str,
    schema_path: str,
    schedule_interval: str | None = "@daily",
    start_date: datetime | None = None,
    strict: bool = False,
    fail_on_error: bool = True,
    default_args: dict[str, Any] | None = None,
    tags: list[str] | None = None,
    **kwargs,
) -> DAG:
    """Create a DAG for schema validation.

    Args:
        dag_id: Unique identifier for the DAG
        file_path: Path to the data file to validate
        schema_path: Path to the schema definition file
        schedule_interval: Cron expression or preset
        start_date: DAG start date
        strict: Whether to enforce strict schema matching
        fail_on_error: Whether to fail on schema errors
        default_args: Custom default arguments
        tags: Tags for the DAG
        **kwargs: Additional DAG arguments

    Returns:
        Configured Airflow DAG
    """
    # Set defaults
    if start_date is None:
        start_date = datetime.now() - timedelta(days=1)

    if default_args is None:
        default_args = DEFAULT_ARGS.copy()

    if tags is None:
        tags = ["datacheck", "schema-validation"]

    # Create DAG
    dag = DAG(
        dag_id=dag_id,
        default_args=default_args,
        description=f"Schema validation for {file_path}",
        schedule_interval=schedule_interval,
        start_date=start_date,
        catchup=False,
        tags=tags,
        **kwargs,
    )

    with dag:
        # Start
        start = DummyOperator(task_id="start")

        # Wait for file
        wait_for_file = DataCheckFileSensor(
            task_id="wait_for_file",
            file_path=file_path,
            poke_interval=60,
            timeout=3600,
        )

        # Validate schema
        validate_schema = DataCheckSchemaOperator(
            task_id="validate_schema",
            file_path=file_path,
            schema_path=schema_path,
            strict=strict,
            fail_on_error=fail_on_error,
        )

        # End
        end = DummyOperator(task_id="end")

        # Dependencies
        start >> wait_for_file >> validate_schema >> end

    return dag
