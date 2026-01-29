"""Airflow operators for DataCheck validation.

Provides custom operators for running data quality checks in Airflow DAGs.
"""

from typing import Any
from collections.abc import Sequence
from pathlib import Path

try:
    from airflow.models import BaseOperator
    from airflow.utils.decorators import apply_defaults
    from airflow.exceptions import AirflowException

    AIRFLOW_AVAILABLE = True
except ImportError:
    # Create mock classes for testing without Airflow
    AIRFLOW_AVAILABLE = False

    import logging

    class BaseOperator:
        """Mock BaseOperator for when Airflow is not installed."""

        def __init__(self, task_id: str, **kwargs):
            self.task_id = task_id
            self.log = logging.getLogger(f"datacheck.{task_id}")
            for key, value in kwargs.items():
                setattr(self, key, value)

        def execute(self, context: dict[str, Any]) -> Any:
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


class DataCheckOperator(BaseOperator):
    """Base operator for DataCheck operations.

    This operator provides common functionality for all DataCheck operators.

    Attributes:
        file_path: Path to the data file to validate
        config_path: Path to the validation configuration file
        fail_on_error: Whether to fail the task on validation errors
        push_results: Whether to push results to XCom
    """

    template_fields: Sequence[str] = ("file_path", "config_path")
    template_ext: Sequence[str] = (".yaml", ".yml", ".json")
    ui_color = "#4CAF50"
    ui_fgcolor = "#FFFFFF"

    @apply_defaults
    def __init__(
        self,
        file_path: str,
        config_path: str | None = None,
        fail_on_error: bool = True,
        push_results: bool = True,
        datacheck_conn_id: str = "datacheck_default",
        **kwargs,
    ):
        """Initialize DataCheckOperator.

        Args:
            file_path: Path to the data file to validate
            config_path: Path to the validation configuration file
            fail_on_error: Whether to fail the task on validation errors
            push_results: Whether to push results to XCom
            datacheck_conn_id: Airflow connection ID for DataCheck API
            **kwargs: Additional arguments passed to BaseOperator
        """
        super().__init__(**kwargs)
        self.file_path = file_path
        self.config_path = config_path
        self.fail_on_error = fail_on_error
        self.push_results = push_results
        self.datacheck_conn_id = datacheck_conn_id

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute the DataCheck validation.

        Args:
            context: Airflow context dictionary

        Returns:
            Validation results dictionary

        Raises:
            AirflowException: If validation fails and fail_on_error is True
        """
        from datacheck.validation import Validator
        import pandas as pd

        self.log.info(f"Running DataCheck validation on: {self.file_path}")

        # Load data using pandas directly
        try:
            file_path = Path(self.file_path)
            if file_path.suffix == ".csv":
                df = pd.read_csv(file_path)
            elif file_path.suffix == ".parquet":
                df = pd.read_parquet(file_path)
            else:
                df = pd.read_csv(file_path)
        except Exception as e:
            raise AirflowException(f"Failed to load data file: {e}")

        # Run validation
        validator = Validator()
        try:
            result = validator.validate(df)
        except Exception as e:
            raise AirflowException(f"Validation error: {e}")

        # Prepare results - use pass_rate as quality score
        results = {
            "file_path": self.file_path,
            "passed": result.passed,
            "pass_rate": result.pass_rate,
            "quality_score": result.pass_rate,  # Use pass_rate as quality metric
            "total_rules": result.rules_run,
            "passed_rules": result.rules_passed,
            "failed_rules": result.rules_failed,
            "total_rows": len(df),
            "timestamp": context.get("ts"),
        }

        # Push results to XCom if enabled
        if self.push_results:
            context["ti"].xcom_push(key="validation_results", value=results)
            context["ti"].xcom_push(key="quality_score", value=result.pass_rate)
            context["ti"].xcom_push(key="passed", value=result.passed)

        # Log results
        self.log.info(f"Validation completed - Pass rate: {result.pass_rate:.1f}%")

        # Fail if validation failed and fail_on_error is True
        if not result.passed and self.fail_on_error:
            failed_rules = [r.rule_name for r in result.results if not r.passed]
            raise AirflowException(
                f"Data quality validation failed. "
                f"Failed rules: {', '.join(failed_rules)}"
            )

        return results


class DataCheckValidateOperator(DataCheckOperator):
    """Operator for running comprehensive data validation.

    Extends DataCheckOperator with additional validation options.
    """

    template_fields: Sequence[str] = ("file_path", "config_path", "rules")
    ui_color = "#2196F3"

    @apply_defaults
    def __init__(
        self,
        file_path: str,
        rules: list[dict[str, Any]] | None = None,
        min_quality_score: float = 0.0,
        min_pass_rate: float = 0.0,
        **kwargs,
    ):
        """Initialize DataCheckValidateOperator.

        Args:
            file_path: Path to the data file to validate
            rules: List of validation rules to apply
            min_quality_score: Minimum quality score required to pass
            min_pass_rate: Minimum pass rate required to pass
            **kwargs: Additional arguments passed to DataCheckOperator
        """
        super().__init__(file_path=file_path, **kwargs)
        self.rules = rules or []
        self.min_quality_score = min_quality_score
        self.min_pass_rate = min_pass_rate

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute validation with additional quality thresholds.

        Args:
            context: Airflow context dictionary

        Returns:
            Validation results dictionary

        Raises:
            AirflowException: If validation fails quality thresholds
        """
        from datacheck.validation import Validator
        import pandas as pd

        self.log.info(f"Running comprehensive validation on: {self.file_path}")

        # Load data using pandas directly
        try:
            file_path = Path(self.file_path)
            if file_path.suffix == ".csv":
                df = pd.read_csv(file_path)
            elif file_path.suffix == ".parquet":
                df = pd.read_parquet(file_path)
            else:
                df = pd.read_csv(file_path)
        except Exception as e:
            raise AirflowException(f"Failed to load data file: {e}")

        # Run validation
        validator = Validator()
        result = validator.validate(df)

        # Prepare results - use pass_rate as quality score
        quality_score = result.pass_rate  # Use pass_rate as quality metric
        results = {
            "file_path": self.file_path,
            "passed": result.passed,
            "pass_rate": result.pass_rate,
            "quality_score": quality_score,
            "total_rules": result.rules_run,
            "passed_rules": result.rules_passed,
            "failed_rules": result.rules_failed,
            "total_rows": len(df),
            "timestamp": context.get("ts"),
            "met_quality_threshold": quality_score >= self.min_quality_score,
            "met_pass_rate_threshold": result.pass_rate >= self.min_pass_rate,
        }

        # Push results to XCom
        if self.push_results:
            context["ti"].xcom_push(key="validation_results", value=results)

        # Check thresholds
        threshold_failed = False
        if quality_score < self.min_quality_score:
            self.log.warning(
                f"Quality score {quality_score:.1f} below threshold "
                f"{self.min_quality_score}"
            )
            threshold_failed = True

        if result.pass_rate < self.min_pass_rate:
            self.log.warning(
                f"Pass rate {result.pass_rate:.1f}% below threshold "
                f"{self.min_pass_rate}%"
            )
            threshold_failed = True

        if threshold_failed and self.fail_on_error:
            raise AirflowException(
                f"Validation did not meet quality thresholds. "
                f"Quality score: {quality_score:.1f} "
                f"(min: {self.min_quality_score}), "
                f"Pass rate: {result.pass_rate:.1f}% "
                f"(min: {self.min_pass_rate}%)"
            )

        return results


class DataCheckSchemaOperator(BaseOperator):
    """Operator for validating data against a schema.

    Validates that data conforms to an expected schema definition.
    """

    template_fields: Sequence[str] = ("file_path", "schema_path")
    ui_color = "#9C27B0"
    ui_fgcolor = "#FFFFFF"

    @apply_defaults
    def __init__(
        self,
        file_path: str,
        schema_path: str | None = None,
        schema: dict[str, Any] | None = None,
        strict: bool = False,
        fail_on_error: bool = True,
        push_results: bool = True,
        **kwargs,
    ):
        """Initialize DataCheckSchemaOperator.

        Args:
            file_path: Path to the data file to validate
            schema_path: Path to the schema file
            schema: Schema definition as a dictionary
            strict: Whether to enforce strict schema matching
            fail_on_error: Whether to fail the task on schema errors
            push_results: Whether to push results to XCom
            **kwargs: Additional arguments passed to BaseOperator
        """
        super().__init__(**kwargs)
        self.file_path = file_path
        self.schema_path = schema_path
        self.schema = schema
        self.strict = strict
        self.fail_on_error = fail_on_error
        self.push_results = push_results

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute schema validation.

        Args:
            context: Airflow context dictionary

        Returns:
            Schema validation results

        Raises:
            AirflowException: If schema validation fails
        """
        import pandas as pd
        import yaml

        self.log.info(f"Validating schema for: {self.file_path}")

        # Load data using pandas directly
        try:
            file_path = Path(self.file_path)
            if file_path.suffix == ".csv":
                df = pd.read_csv(file_path)
            elif file_path.suffix == ".parquet":
                df = pd.read_parquet(file_path)
            else:
                df = pd.read_csv(file_path)
        except Exception as e:
            raise AirflowException(f"Failed to load data file: {e}")

        # Load schema
        schema = self.schema
        if self.schema_path and not schema:
            try:
                with open(self.schema_path) as f:
                    schema = yaml.safe_load(f)
            except Exception as e:
                raise AirflowException(f"Failed to load schema: {e}")

        if not schema:
            raise AirflowException("No schema provided")

        # Validate schema
        errors = []
        expected_columns = schema.get("columns", {})

        # Check for required columns
        for col_name, col_spec in expected_columns.items():
            if col_name not in df.columns:
                if col_spec.get("required", True):
                    errors.append(f"Missing required column: {col_name}")
            else:
                # Check data type
                expected_type = col_spec.get("type")
                if expected_type:
                    actual_type = str(df[col_name].dtype)
                    if not self._types_compatible(expected_type, actual_type):
                        errors.append(
                            f"Column '{col_name}' type mismatch: "
                            f"expected {expected_type}, got {actual_type}"
                        )

        # Check for extra columns in strict mode
        if self.strict:
            extra_cols = set(df.columns) - set(expected_columns.keys())
            if extra_cols:
                errors.append(f"Unexpected columns: {', '.join(extra_cols)}")

        # Prepare results
        passed = len(errors) == 0
        results = {
            "file_path": self.file_path,
            "passed": passed,
            "errors": errors,
            "columns_checked": len(expected_columns),
            "actual_columns": list(df.columns),
            "timestamp": context.get("ts"),
        }

        # Push results to XCom
        if self.push_results:
            context["ti"].xcom_push(key="schema_results", value=results)
            context["ti"].xcom_push(key="schema_passed", value=passed)

        # Log results
        if passed:
            self.log.info("Schema validation passed")
        else:
            for error in errors:
                self.log.error(error)

        # Fail if validation failed
        if not passed and self.fail_on_error:
            raise AirflowException(
                f"Schema validation failed with {len(errors)} errors"
            )

        return results

    def _types_compatible(self, expected: str, actual: str) -> bool:
        """Check if types are compatible.

        Args:
            expected: Expected type name
            actual: Actual pandas dtype string

        Returns:
            True if types are compatible
        """
        type_mappings = {
            "string": ["object", "string", "str"],
            "integer": ["int64", "int32", "int16", "int8", "Int64", "Int32"],
            "float": ["float64", "float32", "Float64"],
            "boolean": ["bool", "boolean"],
            "datetime": ["datetime64[ns]", "datetime64"],
            "date": ["datetime64[ns]", "object"],
        }

        expected_lower = expected.lower()
        actual_lower = actual.lower()

        if expected_lower in type_mappings:
            return any(t.lower() in actual_lower for t in type_mappings[expected_lower])

        return expected_lower in actual_lower


class DataCheckDriftOperator(BaseOperator):
    """Operator for detecting data drift.

    Compares current data against a baseline to detect distribution drift.
    """

    template_fields: Sequence[str] = ("current_path", "baseline_path")
    ui_color = "#FF9800"
    ui_fgcolor = "#FFFFFF"

    @apply_defaults
    def __init__(
        self,
        current_path: str,
        baseline_path: str,
        columns: list[str] | None = None,
        threshold: float = 0.1,
        method: str = "psi",
        fail_on_drift: bool = True,
        push_results: bool = True,
        **kwargs,
    ):
        """Initialize DataCheckDriftOperator.

        Args:
            current_path: Path to current data file
            baseline_path: Path to baseline data file
            columns: Columns to check for drift (None = all numeric)
            threshold: Drift threshold (0.0 to 1.0)
            method: Drift detection method ('psi', 'ks', 'wasserstein')
            fail_on_drift: Whether to fail the task on drift detection
            push_results: Whether to push results to XCom
            **kwargs: Additional arguments passed to BaseOperator
        """
        super().__init__(**kwargs)
        self.current_path = current_path
        self.baseline_path = baseline_path
        self.columns = columns
        self.threshold = threshold
        self.method = method
        self.fail_on_drift = fail_on_drift
        self.push_results = push_results

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute drift detection.

        Args:
            context: Airflow context dictionary

        Returns:
            Drift detection results

        Raises:
            AirflowException: If drift is detected and fail_on_drift is True
        """
        from datacheck.ml_monitoring import DriftDetector
        import pandas as pd

        self.log.info(f"Checking drift: {self.current_path} vs {self.baseline_path}")

        # Load data using pandas directly
        try:
            current_path = Path(self.current_path)
            baseline_path = Path(self.baseline_path)

            if current_path.suffix == ".csv":
                current_df = pd.read_csv(current_path)
            elif current_path.suffix == ".parquet":
                current_df = pd.read_parquet(current_path)
            else:
                current_df = pd.read_csv(current_path)

            if baseline_path.suffix == ".csv":
                baseline_df = pd.read_csv(baseline_path)
            elif baseline_path.suffix == ".parquet":
                baseline_df = pd.read_parquet(baseline_path)
            else:
                baseline_df = pd.read_csv(baseline_path)
        except Exception as e:
            raise AirflowException(f"Failed to load data: {e}")

        # Initialize drift detector
        detector = DriftDetector(
            method=self.method,
            psi_threshold=self.threshold,
        )

        # Set baseline data
        detector.set_baseline(baseline_df)

        # Run drift detection
        drift_result = detector.detect(current_df, columns=self.columns)

        # Prepare results
        results = {
            "current_path": self.current_path,
            "baseline_path": self.baseline_path,
            "drift_detected": drift_result.drift_detected,
            "drift_score": drift_result.overall_drift_score,
            "drifted_columns": drift_result.columns_with_drift,
            "method": self.method,
            "threshold": self.threshold,
            "timestamp": context.get("ts"),
        }

        # Push results to XCom
        if self.push_results:
            context["ti"].xcom_push(key="drift_results", value=results)
            context["ti"].xcom_push(key="drift_detected", value=drift_result.drift_detected)
            context["ti"].xcom_push(key="drift_score", value=drift_result.overall_drift_score)

        # Log results
        self.log.info(f"Drift score: {drift_result.overall_drift_score:.4f}")
        if drift_result.columns_with_drift:
            self.log.warning(
                f"Drift detected in columns: {', '.join(drift_result.columns_with_drift)}"
            )

        # Fail if drift detected
        if drift_result.drift_detected and self.fail_on_drift:
            raise AirflowException(
                f"Data drift detected! Score: {drift_result.overall_drift_score:.4f} "
                f"(threshold: {self.threshold}). "
                f"Drifted columns: {', '.join(drift_result.columns_with_drift)}"
            )

        return results
