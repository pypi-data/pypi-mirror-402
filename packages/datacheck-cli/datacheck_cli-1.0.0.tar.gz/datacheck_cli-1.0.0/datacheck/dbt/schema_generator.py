"""Generate dbt schema.yml files from DataCheck validation rules."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from datacheck.validation.rules import (
    Rule,
    NotNullRule,
    UniqueRule,
    RangeRule,
    RegexRule,
    EnumRule,
)


@dataclass
class DbtTestConfig:
    """Configuration for a dbt test."""
    name: str
    config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> str | dict[str, Any]:
        """Convert to dbt YAML format."""
        if not self.config:
            return self.name
        return {self.name: self.config}


# Alias for backwards compatibility
TestConfig = DbtTestConfig


@dataclass
class ColumnSchema:
    """Schema for a dbt column."""
    name: str
    description: str = ""
    data_type: str | None = None
    tests: list[TestConfig] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dbt YAML format."""
        result: dict[str, Any] = {"name": self.name}

        if self.description:
            result["description"] = self.description

        if self.data_type:
            result["data_type"] = self.data_type

        if self.tests:
            result["tests"] = [t.to_dict() for t in self.tests]

        if self.meta:
            result["meta"] = self.meta

        return result


@dataclass
class ModelSchema:
    """Schema for a dbt model."""
    name: str
    description: str = ""
    columns: list[ColumnSchema] = field(default_factory=list)
    tests: list[TestConfig] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dbt YAML format."""
        result: dict[str, Any] = {"name": self.name}

        if self.description:
            result["description"] = self.description

        if self.columns:
            result["columns"] = [c.to_dict() for c in self.columns]

        if self.tests:
            result["tests"] = [t.to_dict() for t in self.tests]

        if self.meta:
            result["meta"] = self.meta

        if self.config:
            result["config"] = self.config

        return result

    def add_column(self, column: ColumnSchema) -> "ModelSchema":
        """Add a column to the model."""
        self.columns.append(column)
        return self

    def get_column(self, name: str) -> ColumnSchema | None:
        """Get a column by name."""
        for col in self.columns:
            if col.name == name:
                return col
        return None

    def get_or_create_column(self, name: str) -> ColumnSchema:
        """Get a column by name or create it if it doesn't exist."""
        col = self.get_column(name)
        if col is None:
            col = ColumnSchema(name=name)
            self.columns.append(col)
        return col


class SchemaGenerator:
    """Generate dbt schema.yml from DataCheck rules."""

    def __init__(self, version: int = 2):
        """Initialize schema generator.

        Args:
            version: dbt schema version (default: 2)
        """
        self.version = version
        self.models: list[ModelSchema] = []
        self.sources: list[dict[str, Any]] = []

    def add_model(self, model: ModelSchema) -> "SchemaGenerator":
        """Add a model schema.

        Args:
            model: Model schema to add

        Returns:
            Self for chaining
        """
        self.models.append(model)
        return self

    def create_model_from_rules(
        self,
        model_name: str,
        rules: list[Rule],
        description: str = "",
    ) -> ModelSchema:
        """Create a model schema from DataCheck rules.

        Args:
            model_name: Name of the dbt model
            rules: DataCheck validation rules
            description: Model description

        Returns:
            ModelSchema with tests derived from rules
        """
        model = ModelSchema(name=model_name, description=description)

        for rule in rules:
            self._add_rule_to_model(model, rule)

        self.models.append(model)
        return model

    def _add_rule_to_model(self, model: ModelSchema, rule: Rule) -> None:
        """Add a rule's tests to a model schema."""
        columns = rule.columns or []

        if isinstance(rule, NotNullRule):
            for col_name in columns:
                col = model.get_or_create_column(col_name)
                col.tests.append(TestConfig(name="not_null"))

        elif isinstance(rule, UniqueRule):
            if len(columns) == 1:
                col = model.get_or_create_column(columns[0])
                col.tests.append(TestConfig(name="unique"))
            elif len(columns) > 1:
                # Composite unique constraint - model-level test
                model.tests.append(TestConfig(
                    name="dbt_utils.unique_combination_of_columns",
                    config={"combination_of_columns": columns},
                ))

        elif isinstance(rule, RangeRule):
            for col_name in columns:
                col = model.get_or_create_column(col_name)
                config = {}
                if rule.min_value is not None:
                    config["min_value"] = rule.min_value
                if rule.max_value is not None:
                    config["max_value"] = rule.max_value

                if config:
                    col.tests.append(TestConfig(
                        name="dbt_utils.accepted_range",
                        config=config,
                    ))

        elif isinstance(rule, EnumRule):
            for col_name in columns:
                col = model.get_or_create_column(col_name)
                col.tests.append(TestConfig(
                    name="accepted_values",
                    config={"values": list(rule.allowed_values)},
                ))

        elif isinstance(rule, RegexRule):
            for col_name in columns:
                col = model.get_or_create_column(col_name)
                col.tests.append(TestConfig(
                    name="dbt_expectations.expect_column_values_to_match_regex",
                    config={"regex": rule.pattern},
                ))

    def generate_yaml(self) -> str:
        """Generate schema.yml content.

        Returns:
            YAML string
        """
        schema = {"version": self.version}

        if self.models:
            schema["models"] = [m.to_dict() for m in self.models]

        if self.sources:
            schema["sources"] = self.sources

        return yaml.dump(schema, default_flow_style=False, sort_keys=False)

    def save(self, path: str | Path) -> None:
        """Save schema to file.

        Args:
            path: Output path for schema.yml
        """
        path = Path(path)
        path.write_text(self.generate_yaml())

    @classmethod
    def from_datacheck_config(
        cls,
        config: dict[str, Any],
        model_name: str = "model",
    ) -> "SchemaGenerator":
        """Create schema generator from DataCheck config.

        Args:
            config: DataCheck configuration dictionary
            model_name: Name for the dbt model

        Returns:
            SchemaGenerator instance
        """
        from datacheck.validation.config import parse_rules_config

        generator = cls()
        rules = parse_rules_config(config)

        if rules:
            generator.create_model_from_rules(model_name, rules)

        return generator


def generate_schema_from_rules(
    rules: list[Rule],
    model_name: str = "model",
    description: str = "",
) -> str:
    """Convenience function to generate schema YAML from rules.

    Args:
        rules: DataCheck validation rules
        model_name: Name for the dbt model
        description: Model description

    Returns:
        YAML string
    """
    generator = SchemaGenerator()
    generator.create_model_from_rules(model_name, rules, description)
    return generator.generate_yaml()
