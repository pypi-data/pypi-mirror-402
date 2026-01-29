"""Configuration parsing for validation rules."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

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
from datacheck.exceptions import ConfigurationError


@dataclass
class RuleConfig:
    """Configuration for a single validation rule."""
    rule_type: str
    columns: list[str] | None = None
    severity: str = "error"
    name: str | None = None
    params: dict[str, Any] = field(default_factory=dict)


def load_config(path: str | Path) -> dict[str, Any]:
    """Load configuration from a YAML file.

    Args:
        path: Path to YAML config file

    Returns:
        Parsed configuration dictionary

    Raises:
        ConfigurationError: If file not found or invalid YAML
    """
    path = Path(path)

    if not path.exists():
        raise ConfigurationError(f"Config file not found: {path}")

    try:
        with open(path) as f:
            config = yaml.safe_load(f)
            return config or {}
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML in config file: {e}")


def parse_severity(severity_str: str) -> Severity:
    """Parse severity string to Severity enum.

    Args:
        severity_str: Severity string (error, warning, info)

    Returns:
        Severity enum value
    """
    severity_map = {
        "error": Severity.ERROR,
        "warning": Severity.WARNING,
        "info": Severity.INFO,
    }
    return severity_map.get(severity_str.lower(), Severity.ERROR)


def parse_rule_config(rule_dict: dict[str, Any]) -> RuleConfig:
    """Parse a single rule configuration.

    Args:
        rule_dict: Dictionary with rule configuration

    Returns:
        RuleConfig object
    """
    rule_type = rule_dict.get("type") or rule_dict.get("rule")
    if not rule_type:
        raise ConfigurationError("Rule must have 'type' or 'rule' field")

    columns = rule_dict.get("columns")
    if isinstance(columns, str):
        columns = [columns]

    severity = rule_dict.get("severity", "error")
    name = rule_dict.get("name")

    # Extract rule-specific parameters
    excluded_keys = {"type", "rule", "columns", "severity", "name"}
    params = {k: v for k, v in rule_dict.items() if k not in excluded_keys}

    return RuleConfig(
        rule_type=rule_type,
        columns=columns,
        severity=severity,
        name=name,
        params=params,
    )


def create_rule_from_config(rule_config: RuleConfig) -> Rule:
    """Create a Rule instance from RuleConfig.

    Args:
        rule_config: Rule configuration

    Returns:
        Rule instance

    Raises:
        ConfigurationError: If rule type is unknown
    """
    severity = parse_severity(rule_config.severity)
    rule_type = rule_config.rule_type.lower().replace("_", "").replace("-", "")

    # Map rule types to classes
    if rule_type in ("notnull", "notnulls", "required"):
        return NotNullRule(
            columns=rule_config.columns,
            severity=severity,
            name=rule_config.name or "not_null",
        )

    elif rule_type in ("unique", "distinct"):
        return UniqueRule(
            columns=rule_config.columns,
            severity=severity,
            name=rule_config.name or "unique",
        )

    elif rule_type in ("range", "between"):
        return RangeRule(
            columns=rule_config.columns,
            min_value=rule_config.params.get("min"),
            max_value=rule_config.params.get("max"),
            severity=severity,
            name=rule_config.name or "range",
        )

    elif rule_type in ("regex", "pattern", "match"):
        pattern = rule_config.params.get("pattern", ".*")
        return RegexRule(
            columns=rule_config.columns,
            pattern=pattern,
            severity=severity,
            name=rule_config.name or "regex",
        )

    elif rule_type in ("type", "dtype"):
        expected_type = rule_config.params.get("expected", "string")
        return TypeRule(
            columns=rule_config.columns,
            expected_type=expected_type,
            severity=severity,
            name=rule_config.name or "type",
        )

    elif rule_type in ("enum", "isin", "allowed", "values"):
        values = rule_config.params.get("values", [])
        if isinstance(values, str):
            values = [v.strip() for v in values.split(",")]
        return EnumRule(
            columns=rule_config.columns,
            allowed_values=set(values),
            severity=severity,
            name=rule_config.name or "enum",
        )

    elif rule_type in ("length", "strlen"):
        return LengthRule(
            columns=rule_config.columns,
            min_length=rule_config.params.get("min"),
            max_length=rule_config.params.get("max"),
            severity=severity,
            name=rule_config.name or "length",
        )

    else:
        raise ConfigurationError(f"Unknown rule type: {rule_config.rule_type}")


def parse_rules_config(config: dict[str, Any]) -> list[Rule]:
    """Parse rules from configuration dictionary.

    Args:
        config: Configuration dictionary with 'rules' key

    Returns:
        List of Rule instances
    """
    rules = []

    # Get rules from config
    rules_config = config.get("rules") or config.get("validation", {}).get("rules", [])

    if not rules_config:
        return rules

    for rule_dict in rules_config:
        try:
            rule_config = parse_rule_config(rule_dict)
            rule = create_rule_from_config(rule_config)
            rules.append(rule)
        except ConfigurationError:
            raise
        except Exception as e:
            raise ConfigurationError(f"Error parsing rule: {e}")

    return rules


def generate_config_template() -> str:
    """Generate a template configuration file.

    Returns:
        YAML string with example configuration
    """
    template = """# DataCheck Validation Configuration
# Version: 1.0

# Source configuration (optional)
source:
  type: local  # local, s3, gs, az
  path: data.csv

# Validation rules
rules:
  # Check for null values
  - type: not_null
    columns: [id, name]
    severity: error

  # Check for unique values
  - type: unique
    columns: [id]
    severity: error

  # Check numeric range
  - type: range
    columns: [age]
    min: 0
    max: 150
    severity: warning

  # Check pattern (regex)
  - type: regex
    columns: [email]
    pattern: "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\\\.[a-zA-Z0-9-.]+$"
    severity: error

  # Check allowed values
  - type: enum
    columns: [status]
    values: [active, inactive, pending]
    severity: error

  # Check string length
  - type: length
    columns: [username]
    min: 3
    max: 50
    severity: warning

  # Check data type
  - type: type
    columns: [created_at]
    expected: datetime
    severity: info

# Output configuration
output:
  format: table  # table, json, html
  # file: report.json  # Optional output file
"""
    return template
