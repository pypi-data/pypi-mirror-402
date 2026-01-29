"""Airflow integration for DataCheck.

Provides custom operators, sensors, and DAG utilities for
integrating DataCheck data quality validation into Airflow pipelines.
"""

from datacheck.airflow.operators import (
    DataCheckOperator,
    DataCheckValidateOperator,
    DataCheckSchemaOperator,
    DataCheckDriftOperator,
)
from datacheck.airflow.sensors import (
    DataCheckQualitySensor,
    DataCheckAlertSensor,
    DataCheckFileSensor,
)
from datacheck.airflow.hooks import DataCheckHook
from datacheck.airflow.dag_factory import (
    create_validation_dag,
    create_monitoring_dag,
    create_schema_validation_dag,
)

__all__ = [
    # Operators
    "DataCheckOperator",
    "DataCheckValidateOperator",
    "DataCheckSchemaOperator",
    "DataCheckDriftOperator",
    # Sensors
    "DataCheckQualitySensor",
    "DataCheckAlertSensor",
    "DataCheckFileSensor",
    # Hooks
    "DataCheckHook",
    # DAG Factory
    "create_validation_dag",
    "create_monitoring_dag",
    "create_schema_validation_dag",
]
