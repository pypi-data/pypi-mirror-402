"""dbt integration for DataCheck."""

from datacheck.dbt.schema_generator import (
    SchemaGenerator,
    ModelSchema,
    ColumnSchema,
    DbtTestConfig,
    TestConfig,  # Alias for backwards compatibility
)
from datacheck.dbt.test_converter import (
    TestConverter,
    DbtTest,
    convert_rule_to_dbt_test,
    convert_dbt_test_to_rule,
)
from datacheck.dbt.project_scanner import (
    DbtProjectScanner,
    DbtModel,
    DbtSource,
)

__all__ = [
    # Schema generation
    "SchemaGenerator",
    "ModelSchema",
    "ColumnSchema",
    "DbtTestConfig",
    "TestConfig",
    # Test conversion
    "TestConverter",
    "DbtTest",
    "convert_rule_to_dbt_test",
    "convert_dbt_test_to_rule",
    # Project scanning
    "DbtProjectScanner",
    "DbtModel",
    "DbtSource",
]
