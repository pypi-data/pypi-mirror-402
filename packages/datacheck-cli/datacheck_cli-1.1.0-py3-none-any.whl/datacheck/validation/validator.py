"""Validator and reporting for DataCheck."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import json

import pandas as pd

from datacheck.validation.rules import Rule, RuleResult, Severity


@dataclass
class ValidationResult:
    """Result of validating a single column or table-level check."""
    column: str | None
    rule_name: str
    passed: bool
    severity: Severity
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    """Complete validation report for a dataset."""
    timestamp: str
    source: str
    total_rows: int
    total_columns: int
    rules_run: int
    rules_passed: int
    rules_failed: int
    errors: int
    warnings: int
    results: list[RuleResult]

    @property
    def passed(self) -> bool:
        """Return True if all error-level rules passed."""
        return self.errors == 0

    @property
    def pass_rate(self) -> float:
        """Calculate overall pass rate."""
        if self.rules_run == 0:
            return 100.0
        return (self.rules_passed / self.rules_run) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "timestamp": self.timestamp,
            "source": self.source,
            "summary": {
                "total_rows": int(self.total_rows),
                "total_columns": int(self.total_columns),
                "rules_run": int(self.rules_run),
                "rules_passed": int(self.rules_passed),
                "rules_failed": int(self.rules_failed),
                "errors": int(self.errors),
                "warnings": int(self.warnings),
                "pass_rate": float(self.pass_rate),
                "passed": bool(self.passed),
            },
            "results": [
                {
                    "rule_name": r.rule_name,
                    "column": r.column,
                    "passed": bool(r.passed),
                    "severity": r.severity.value,
                    "message": r.message,
                    "failed_count": int(r.failed_count),
                    "total_count": int(r.total_count),
                    "pass_rate": float(r.pass_rate),
                }
                for r in self.results
            ],
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert report to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def get_failed_results(self) -> list[RuleResult]:
        """Get only failed results."""
        return [r for r in self.results if not r.passed]

    def get_errors(self) -> list[RuleResult]:
        """Get only error-level failures."""
        return [r for r in self.results if not r.passed and r.severity == Severity.ERROR]

    def get_warnings(self) -> list[RuleResult]:
        """Get only warning-level failures."""
        return [r for r in self.results if not r.passed and r.severity == Severity.WARNING]


class Validator:
    """Main validator class that runs rules against data."""

    def __init__(self, rules: list[Rule] | None = None):
        """Initialize validator.

        Args:
            rules: List of validation rules to apply
        """
        self.rules: list[Rule] = rules or []

    def add_rule(self, rule: Rule) -> "Validator":
        """Add a rule to the validator.

        Args:
            rule: Rule to add

        Returns:
            Self for chaining
        """
        self.rules.append(rule)
        return self

    def add_rules(self, rules: list[Rule]) -> "Validator":
        """Add multiple rules to the validator.

        Args:
            rules: List of rules to add

        Returns:
            Self for chaining
        """
        self.rules.extend(rules)
        return self

    def clear_rules(self) -> "Validator":
        """Clear all rules.

        Returns:
            Self for chaining
        """
        self.rules = []
        return self

    def validate(
        self,
        df: pd.DataFrame,
        source: str = "unknown",
    ) -> ValidationReport:
        """Validate a DataFrame against all rules.

        Args:
            df: DataFrame to validate
            source: Source identifier for reporting

        Returns:
            ValidationReport with all results
        """
        all_results: list[RuleResult] = []

        # Run each rule
        for rule in self.rules:
            results = rule.validate(df)
            all_results.extend(results)

        # Calculate summary statistics
        rules_run = len(all_results)
        rules_passed = sum(1 for r in all_results if r.passed)
        rules_failed = rules_run - rules_passed

        errors = sum(
            1 for r in all_results
            if not r.passed and r.severity == Severity.ERROR
        )
        warnings = sum(
            1 for r in all_results
            if not r.passed and r.severity == Severity.WARNING
        )

        return ValidationReport(
            timestamp=datetime.now().isoformat(),
            source=source,
            total_rows=len(df),
            total_columns=len(df.columns),
            rules_run=rules_run,
            rules_passed=rules_passed,
            rules_failed=rules_failed,
            errors=errors,
            warnings=warnings,
            results=all_results,
        )

    def validate_column(
        self,
        df: pd.DataFrame,
        column: str,
        source: str = "unknown",
    ) -> ValidationReport:
        """Validate a single column.

        Args:
            df: DataFrame containing the column
            column: Column name to validate
            source: Source identifier

        Returns:
            ValidationReport for the column
        """
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")

        # Filter rules to those that apply to this column
        column_rules = []
        for rule in self.rules:
            if rule.columns is None or column in rule.columns:
                # Create a copy of the rule with just this column
                rule_copy = type(rule).__new__(type(rule))
                rule_copy.__dict__.update(rule.__dict__)
                rule_copy.columns = [column]
                column_rules.append(rule_copy)

        # Create a temporary validator with filtered rules
        temp_validator = Validator(rules=column_rules)
        return temp_validator.validate(df, source=source)

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "Validator":
        """Create a validator from a configuration dictionary.

        Args:
            config: Configuration dictionary with rules

        Returns:
            Configured Validator instance
        """
        from datacheck.validation.config import parse_rules_config

        rules = parse_rules_config(config)
        return cls(rules=rules)
