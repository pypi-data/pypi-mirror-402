"""Convert between DataCheck rules and dbt tests."""
from dataclasses import dataclass, field
from typing import Any

from datacheck.validation.rules import (
    Rule,
    Severity,
    NotNullRule,
    UniqueRule,
    RangeRule,
    RegexRule,
    TypeRule,
    EnumRule,
    LengthRule,
)


@dataclass
class DbtTest:
    """Representation of a dbt test."""
    name: str
    column: str | None = None
    model: str | None = None
    config: dict[str, Any] = field(default_factory=dict)
    severity: str = "error"
    tags: list[str] = field(default_factory=list)

    def to_yaml_dict(self) -> str | dict[str, Any]:
        """Convert to dbt YAML format for schema.yml."""
        if not self.config and not self.severity != "error" and not self.tags:
            return self.name

        result: dict[str, Any] = {self.name: {}}

        if self.config:
            result[self.name].update(self.config)

        if self.severity != "error":
            result[self.name]["severity"] = self.severity

        if self.tags:
            result[self.name]["tags"] = self.tags

        # If only the test name with empty config, simplify
        if not result[self.name]:
            return self.name

        return result

    def to_sql(self) -> str:
        """Generate dbt test SQL for custom tests.

        Returns:
            SQL string for a singular test
        """
        if self.name == "not_null":
            return f"""
-- Test: {self.name}
-- Column: {self.column}
select *
from {{{{ ref('{self.model}') }}}}
where {self.column} is null
"""
        elif self.name == "unique":
            return f"""
-- Test: {self.name}
-- Column: {self.column}
select {self.column}, count(*) as n
from {{{{ ref('{self.model}') }}}}
group by {self.column}
having count(*) > 1
"""
        elif self.name == "accepted_values":
            values = self.config.get("values", [])
            values_str = ", ".join(f"'{v}'" for v in values)
            return f"""
-- Test: {self.name}
-- Column: {self.column}
select *
from {{{{ ref('{self.model}') }}}}
where {self.column} not in ({values_str})
"""
        else:
            return f"-- Custom test: {self.name}\n-- Implement test logic here"


class TestConverter:
    """Convert between DataCheck rules and dbt tests."""

    # Mapping from DataCheck rule types to dbt test names
    RULE_TO_DBT_MAP = {
        "NotNullRule": "not_null",
        "UniqueRule": "unique",
        "EnumRule": "accepted_values",
        "RangeRule": "dbt_utils.accepted_range",
        "RegexRule": "dbt_expectations.expect_column_values_to_match_regex",
        "LengthRule": "dbt_expectations.expect_column_value_lengths_to_be_between",
        "TypeRule": "dbt_expectations.expect_column_values_to_be_of_type",
    }

    # Mapping from dbt test names to DataCheck rule classes
    DBT_TO_RULE_MAP = {
        "not_null": NotNullRule,
        "unique": UniqueRule,
        "accepted_values": EnumRule,
        "relationships": None,  # Foreign key - not directly supported
    }

    @classmethod
    def rule_to_dbt_tests(cls, rule: Rule) -> list[DbtTest]:
        """Convert a DataCheck rule to dbt tests.

        Args:
            rule: DataCheck validation rule

        Returns:
            List of DbtTest instances
        """
        tests = []
        columns = rule.columns or []
        severity = rule.severity.value if hasattr(rule, "severity") else "error"

        if isinstance(rule, NotNullRule):
            for col in columns:
                tests.append(DbtTest(
                    name="not_null",
                    column=col,
                    severity=severity,
                ))

        elif isinstance(rule, UniqueRule):
            if len(columns) == 1:
                tests.append(DbtTest(
                    name="unique",
                    column=columns[0],
                    severity=severity,
                ))
            elif len(columns) > 1:
                # Composite unique - use dbt_utils
                tests.append(DbtTest(
                    name="dbt_utils.unique_combination_of_columns",
                    config={"combination_of_columns": columns},
                    severity=severity,
                ))

        elif isinstance(rule, EnumRule):
            for col in columns:
                tests.append(DbtTest(
                    name="accepted_values",
                    column=col,
                    config={"values": list(rule.allowed_values)},
                    severity=severity,
                ))

        elif isinstance(rule, RangeRule):
            for col in columns:
                config = {}
                if rule.min_value is not None:
                    config["min_value"] = rule.min_value
                if rule.max_value is not None:
                    config["max_value"] = rule.max_value

                tests.append(DbtTest(
                    name="dbt_utils.accepted_range",
                    column=col,
                    config=config,
                    severity=severity,
                ))

        elif isinstance(rule, RegexRule):
            for col in columns:
                tests.append(DbtTest(
                    name="dbt_expectations.expect_column_values_to_match_regex",
                    column=col,
                    config={"regex": rule.pattern},
                    severity=severity,
                ))

        elif isinstance(rule, LengthRule):
            for col in columns:
                config = {}
                if rule.min_length is not None:
                    config["min_value"] = rule.min_length
                if rule.max_length is not None:
                    config["max_value"] = rule.max_length

                tests.append(DbtTest(
                    name="dbt_expectations.expect_column_value_lengths_to_be_between",
                    column=col,
                    config=config,
                    severity=severity,
                ))

        elif isinstance(rule, TypeRule):
            for col in columns:
                tests.append(DbtTest(
                    name="dbt_expectations.expect_column_values_to_be_of_type",
                    column=col,
                    config={"column_type": rule.expected_type},
                    severity=severity,
                ))

        return tests

    @classmethod
    def dbt_test_to_rule(cls, test: DbtTest) -> Rule | None:
        """Convert a dbt test to a DataCheck rule.

        Args:
            test: DbtTest instance

        Returns:
            DataCheck Rule or None if not convertible
        """
        test_name = test.name.split(".")[-1]  # Handle namespaced tests
        severity = Severity.ERROR if test.severity == "error" else Severity.WARNING

        if test_name == "not_null":
            return NotNullRule(
                columns=[test.column] if test.column else None,
                severity=severity,
            )

        elif test_name == "unique":
            return UniqueRule(
                columns=[test.column] if test.column else None,
                severity=severity,
            )

        elif test_name == "accepted_values":
            values = test.config.get("values", [])
            return EnumRule(
                columns=[test.column] if test.column else None,
                allowed_values=set(values),
                severity=severity,
            )

        elif test_name in ("accepted_range", "expect_column_values_to_be_between"):
            return RangeRule(
                columns=[test.column] if test.column else None,
                min_value=test.config.get("min_value"),
                max_value=test.config.get("max_value"),
                severity=severity,
            )

        elif test_name == "expect_column_values_to_match_regex":
            pattern = test.config.get("regex", ".*")
            return RegexRule(
                columns=[test.column] if test.column else None,
                pattern=pattern,
                severity=severity,
            )

        elif test_name == "expect_column_value_lengths_to_be_between":
            return LengthRule(
                columns=[test.column] if test.column else None,
                min_length=test.config.get("min_value"),
                max_length=test.config.get("max_value"),
                severity=severity,
            )

        return None

    @classmethod
    def rules_to_dbt_tests(cls, rules: list[Rule]) -> list[DbtTest]:
        """Convert multiple rules to dbt tests.

        Args:
            rules: List of DataCheck rules

        Returns:
            List of DbtTest instances
        """
        tests = []
        for rule in rules:
            tests.extend(cls.rule_to_dbt_tests(rule))
        return tests

    @classmethod
    def dbt_tests_to_rules(cls, tests: list[DbtTest]) -> list[Rule]:
        """Convert multiple dbt tests to rules.

        Args:
            tests: List of DbtTest instances

        Returns:
            List of DataCheck Rules
        """
        rules = []
        for test in tests:
            rule = cls.dbt_test_to_rule(test)
            if rule:
                rules.append(rule)
        return rules


def convert_rule_to_dbt_test(rule: Rule) -> list[DbtTest]:
    """Convenience function to convert a rule to dbt tests.

    Args:
        rule: DataCheck rule

    Returns:
        List of DbtTest instances
    """
    return TestConverter.rule_to_dbt_tests(rule)


def convert_dbt_test_to_rule(test: DbtTest) -> Rule | None:
    """Convenience function to convert a dbt test to a rule.

    Args:
        test: DbtTest instance

    Returns:
        DataCheck Rule or None
    """
    return TestConverter.dbt_test_to_rule(test)
