"""Validation rules for DataCheck."""
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from collections.abc import Callable

import pandas as pd


class Severity(Enum):
    """Severity levels for validation rules."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class RuleResult:
    """Result of a single rule validation."""
    rule_name: str
    column: str | None
    passed: bool
    severity: Severity
    message: str
    failed_count: int = 0
    total_count: int = 0
    failed_rows: list[int] = field(default_factory=list)
    failed_values: list[Any] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        """Calculate pass rate as percentage."""
        if self.total_count == 0:
            return 100.0
        return ((self.total_count - self.failed_count) / self.total_count) * 100


class Rule(ABC):
    """Abstract base class for validation rules."""

    def __init__(
        self,
        name: str,
        columns: list[str] | None = None,
        severity: Severity = Severity.ERROR,
        description: str | None = None,
    ):
        """Initialize rule.

        Args:
            name: Rule name/identifier
            columns: Columns to apply rule to (None for all columns)
            severity: Severity level for failures
            description: Optional description of the rule
        """
        self.name = name
        self.columns = columns
        self.severity = severity
        self.description = description or self._default_description()

    @abstractmethod
    def _default_description(self) -> str:
        """Return default description for the rule."""
        pass

    @abstractmethod
    def validate(self, df: pd.DataFrame) -> list[RuleResult]:
        """Validate the dataframe against this rule.

        Args:
            df: DataFrame to validate

        Returns:
            List of RuleResult objects
        """
        pass

    def _get_columns(self, df: pd.DataFrame) -> list[str]:
        """Get columns to validate."""
        if self.columns:
            return [c for c in self.columns if c in df.columns]
        return list(df.columns)


class NotNullRule(Rule):
    """Rule to check for null/missing values."""

    def __init__(
        self,
        columns: list[str] | None = None,
        severity: Severity = Severity.ERROR,
        name: str = "not_null",
    ):
        super().__init__(name=name, columns=columns, severity=severity)

    def _default_description(self) -> str:
        return "Check that values are not null"

    def validate(self, df: pd.DataFrame) -> list[RuleResult]:
        results = []
        for col in self._get_columns(df):
            null_mask = df[col].isna()
            failed_count = null_mask.sum()
            total_count = len(df)
            failed_rows = df.index[null_mask].tolist()[:100]  # Limit to 100 rows

            results.append(RuleResult(
                rule_name=self.name,
                column=col,
                passed=failed_count == 0,
                severity=self.severity,
                message=f"Column '{col}' has {failed_count} null values" if failed_count > 0 else f"Column '{col}' has no null values",
                failed_count=failed_count,
                total_count=total_count,
                failed_rows=failed_rows,
            ))
        return results


class UniqueRule(Rule):
    """Rule to check for unique values."""

    def __init__(
        self,
        columns: list[str] | None = None,
        severity: Severity = Severity.ERROR,
        name: str = "unique",
    ):
        super().__init__(name=name, columns=columns, severity=severity)

    def _default_description(self) -> str:
        return "Check that values are unique"

    def validate(self, df: pd.DataFrame) -> list[RuleResult]:
        results = []
        for col in self._get_columns(df):
            duplicates = df[col].duplicated(keep=False)
            failed_count = duplicates.sum()
            total_count = len(df)
            failed_rows = df.index[duplicates].tolist()[:100]
            failed_values = df.loc[duplicates, col].unique().tolist()[:20]

            results.append(RuleResult(
                rule_name=self.name,
                column=col,
                passed=failed_count == 0,
                severity=self.severity,
                message=f"Column '{col}' has {failed_count} duplicate values" if failed_count > 0 else f"Column '{col}' has all unique values",
                failed_count=failed_count,
                total_count=total_count,
                failed_rows=failed_rows,
                failed_values=failed_values,
            ))
        return results


class RangeRule(Rule):
    """Rule to check values are within a range."""

    def __init__(
        self,
        columns: list[str] | None = None,
        min_value: int | float | None = None,
        max_value: int | float | None = None,
        severity: Severity = Severity.ERROR,
        name: str = "range",
    ):
        self.min_value = min_value
        self.max_value = max_value
        super().__init__(name=name, columns=columns, severity=severity)

    def _default_description(self) -> str:
        parts = []
        if self.min_value is not None:
            parts.append(f">= {self.min_value}")
        if self.max_value is not None:
            parts.append(f"<= {self.max_value}")
        return f"Check that values are {' and '.join(parts)}"

    def validate(self, df: pd.DataFrame) -> list[RuleResult]:
        results = []
        for col in self._get_columns(df):
            # Skip non-numeric columns
            if not pd.api.types.is_numeric_dtype(df[col]):
                continue

            mask = pd.Series([False] * len(df), index=df.index)

            if self.min_value is not None:
                mask |= df[col] < self.min_value
            if self.max_value is not None:
                mask |= df[col] > self.max_value

            # Exclude null values from failure count
            mask &= df[col].notna()

            failed_count = mask.sum()
            total_count = df[col].notna().sum()
            failed_rows = df.index[mask].tolist()[:100]
            failed_values = df.loc[mask, col].tolist()[:20]

            range_str = []
            if self.min_value is not None:
                range_str.append(f"min={self.min_value}")
            if self.max_value is not None:
                range_str.append(f"max={self.max_value}")

            results.append(RuleResult(
                rule_name=self.name,
                column=col,
                passed=failed_count == 0,
                severity=self.severity,
                message=f"Column '{col}' has {failed_count} values out of range ({', '.join(range_str)})" if failed_count > 0 else f"Column '{col}' values are within range",
                failed_count=failed_count,
                total_count=total_count,
                failed_rows=failed_rows,
                failed_values=failed_values,
            ))
        return results


class RegexRule(Rule):
    """Rule to check values match a regex pattern."""

    def __init__(
        self,
        columns: list[str] | None = None,
        pattern: str = ".*",
        severity: Severity = Severity.ERROR,
        name: str = "regex",
    ):
        self.pattern = pattern
        self._compiled = re.compile(pattern)
        super().__init__(name=name, columns=columns, severity=severity)

    def _default_description(self) -> str:
        return f"Check that values match pattern: {self.pattern}"

    def validate(self, df: pd.DataFrame) -> list[RuleResult]:
        results = []
        for col in self._get_columns(df):
            # Convert to string for regex matching
            str_col = df[col].astype(str)

            # Check which values don't match
            mask = ~str_col.str.match(self._compiled, na=False)
            # Exclude actual null values from failure
            mask &= df[col].notna()

            failed_count = mask.sum()
            total_count = df[col].notna().sum()
            failed_rows = df.index[mask].tolist()[:100]
            failed_values = df.loc[mask, col].tolist()[:20]

            results.append(RuleResult(
                rule_name=self.name,
                column=col,
                passed=failed_count == 0,
                severity=self.severity,
                message=f"Column '{col}' has {failed_count} values not matching pattern '{self.pattern}'" if failed_count > 0 else f"Column '{col}' values match pattern",
                failed_count=failed_count,
                total_count=total_count,
                failed_rows=failed_rows,
                failed_values=failed_values,
            ))
        return results


class TypeRule(Rule):
    """Rule to check column data types."""

    VALID_TYPES = {
        "string": (str, object),
        "int": (int, "int64", "int32"),
        "float": (float, "float64", "float32"),
        "bool": (bool, "bool"),
        "datetime": ("datetime64[ns]",),
    }

    def __init__(
        self,
        columns: list[str] | None = None,
        expected_type: str = "string",
        severity: Severity = Severity.ERROR,
        name: str = "type",
    ):
        self.expected_type = expected_type.lower()
        super().__init__(name=name, columns=columns, severity=severity)

    def _default_description(self) -> str:
        return f"Check that column type is {self.expected_type}"

    def validate(self, df: pd.DataFrame) -> list[RuleResult]:
        results = []
        for col in self._get_columns(df):
            actual_type = str(df[col].dtype)
            passed = False

            if self.expected_type == "string":
                passed = actual_type == "object" or actual_type.startswith("string")
            elif self.expected_type == "int":
                passed = "int" in actual_type.lower()
            elif self.expected_type == "float":
                passed = "float" in actual_type.lower()
            elif self.expected_type == "bool":
                passed = actual_type == "bool"
            elif self.expected_type == "datetime":
                passed = "datetime" in actual_type.lower()

            results.append(RuleResult(
                rule_name=self.name,
                column=col,
                passed=passed,
                severity=self.severity,
                message=f"Column '{col}' has type '{actual_type}', expected '{self.expected_type}'" if not passed else f"Column '{col}' has correct type",
                failed_count=0 if passed else len(df),
                total_count=len(df),
            ))
        return results


class EnumRule(Rule):
    """Rule to check values are in an allowed set."""

    def __init__(
        self,
        columns: list[str] | None = None,
        allowed_values: set[Any] | None = None,
        severity: Severity = Severity.ERROR,
        name: str = "enum",
    ):
        self.allowed_values = set(allowed_values) if allowed_values else set()
        super().__init__(name=name, columns=columns, severity=severity)

    def _default_description(self) -> str:
        values_str = ", ".join(str(v) for v in list(self.allowed_values)[:5])
        if len(self.allowed_values) > 5:
            values_str += ", ..."
        return f"Check that values are in: [{values_str}]"

    def validate(self, df: pd.DataFrame) -> list[RuleResult]:
        results = []
        for col in self._get_columns(df):
            mask = ~df[col].isin(self.allowed_values)
            # Exclude null values
            mask &= df[col].notna()

            failed_count = mask.sum()
            total_count = df[col].notna().sum()
            failed_rows = df.index[mask].tolist()[:100]
            failed_values = df.loc[mask, col].unique().tolist()[:20]

            results.append(RuleResult(
                rule_name=self.name,
                column=col,
                passed=failed_count == 0,
                severity=self.severity,
                message=f"Column '{col}' has {failed_count} values not in allowed set" if failed_count > 0 else f"Column '{col}' values are all valid",
                failed_count=failed_count,
                total_count=total_count,
                failed_rows=failed_rows,
                failed_values=failed_values,
            ))
        return results


class LengthRule(Rule):
    """Rule to check string length."""

    def __init__(
        self,
        columns: list[str] | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        severity: Severity = Severity.ERROR,
        name: str = "length",
    ):
        self.min_length = min_length
        self.max_length = max_length
        super().__init__(name=name, columns=columns, severity=severity)

    def _default_description(self) -> str:
        parts = []
        if self.min_length is not None:
            parts.append(f"min_length={self.min_length}")
        if self.max_length is not None:
            parts.append(f"max_length={self.max_length}")
        return f"Check string length ({', '.join(parts)})"

    def validate(self, df: pd.DataFrame) -> list[RuleResult]:
        results = []
        for col in self._get_columns(df):
            str_lengths = df[col].astype(str).str.len()

            mask = pd.Series([False] * len(df), index=df.index)

            if self.min_length is not None:
                mask |= str_lengths < self.min_length
            if self.max_length is not None:
                mask |= str_lengths > self.max_length

            # Exclude null values
            mask &= df[col].notna()

            failed_count = mask.sum()
            total_count = df[col].notna().sum()
            failed_rows = df.index[mask].tolist()[:100]
            failed_values = df.loc[mask, col].tolist()[:20]

            length_str = []
            if self.min_length is not None:
                length_str.append(f"min={self.min_length}")
            if self.max_length is not None:
                length_str.append(f"max={self.max_length}")

            results.append(RuleResult(
                rule_name=self.name,
                column=col,
                passed=failed_count == 0,
                severity=self.severity,
                message=f"Column '{col}' has {failed_count} values with invalid length ({', '.join(length_str)})" if failed_count > 0 else f"Column '{col}' values have valid length",
                failed_count=failed_count,
                total_count=total_count,
                failed_rows=failed_rows,
                failed_values=failed_values,
            ))
        return results


class CustomRule(Rule):
    """Rule using a custom validation function."""

    def __init__(
        self,
        columns: list[str] | None = None,
        func: Callable[[pd.Series], pd.Series] | None = None,
        severity: Severity = Severity.ERROR,
        name: str = "custom",
        description: str | None = None,
    ):
        """Initialize custom rule.

        Args:
            columns: Columns to apply rule to
            func: Function that takes a Series and returns boolean Series (True=valid)
            severity: Severity level
            name: Rule name
            description: Rule description
        """
        self.func = func or (lambda x: pd.Series([True] * len(x), index=x.index))
        super().__init__(name=name, columns=columns, severity=severity, description=description)

    def _default_description(self) -> str:
        return "Custom validation rule"

    def validate(self, df: pd.DataFrame) -> list[RuleResult]:
        results = []
        for col in self._get_columns(df):
            try:
                valid_mask = self.func(df[col])
                mask = ~valid_mask
                # Exclude null values
                mask &= df[col].notna()

                failed_count = mask.sum()
                total_count = df[col].notna().sum()
                failed_rows = df.index[mask].tolist()[:100]
                failed_values = df.loc[mask, col].tolist()[:20]

                results.append(RuleResult(
                    rule_name=self.name,
                    column=col,
                    passed=failed_count == 0,
                    severity=self.severity,
                    message=f"Column '{col}' has {failed_count} values failing custom validation" if failed_count > 0 else f"Column '{col}' passed custom validation",
                    failed_count=failed_count,
                    total_count=total_count,
                    failed_rows=failed_rows,
                    failed_values=failed_values,
                ))
            except Exception as e:
                results.append(RuleResult(
                    rule_name=self.name,
                    column=col,
                    passed=False,
                    severity=self.severity,
                    message=f"Column '{col}' custom validation error: {e}",
                    failed_count=len(df),
                    total_count=len(df),
                ))
        return results
