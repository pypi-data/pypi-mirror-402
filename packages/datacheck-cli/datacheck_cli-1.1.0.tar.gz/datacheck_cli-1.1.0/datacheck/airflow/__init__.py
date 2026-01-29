"""Airflow integration for DataCheck.

Provides custom operators for integrating DataCheck data quality
validation into Airflow pipelines.

Note: This is a simplified integration focused on core operators.
For complex workflows, consider using the CLI via BashOperator.
"""

from datacheck.airflow.operators import (
    DataCheckOperator,
    DataCheckValidateOperator,
    DataCheckSchemaOperator,
)

__all__ = [
    # Operators
    "DataCheckOperator",
    "DataCheckValidateOperator",
    "DataCheckSchemaOperator",
]
