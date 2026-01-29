"""Scan dbt projects to extract models and sources."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import re

import yaml


@dataclass
class DbtColumn:
    """Representation of a dbt column."""
    name: str
    description: str = ""
    data_type: str | None = None
    tests: list[dict[str, Any]] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class DbtModel:
    """Representation of a dbt model."""
    name: str
    path: Path | None = None
    description: str = ""
    columns: list[DbtColumn] = field(default_factory=list)
    tests: list[dict[str, Any]] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)
    raw_sql: str | None = None

    def get_column(self, name: str) -> DbtColumn | None:
        """Get a column by name."""
        for col in self.columns:
            if col.name == name:
                return col
        return None

    def get_referenced_models(self) -> list[str]:
        """Extract model references from SQL."""
        if not self.raw_sql:
            return []

        # Find {{ ref('model_name') }} patterns
        pattern = r"\{\{\s*ref\(['\"]([^'\"]+)['\"]\)\s*\}\}"
        return re.findall(pattern, self.raw_sql)

    def get_referenced_sources(self) -> list[tuple]:
        """Extract source references from SQL."""
        if not self.raw_sql:
            return []

        # Find {{ source('source_name', 'table_name') }} patterns
        pattern = r"\{\{\s*source\(['\"]([^'\"]+)['\"],\s*['\"]([^'\"]+)['\"]\)\s*\}\}"
        return re.findall(pattern, self.raw_sql)


@dataclass
class DbtSource:
    """Representation of a dbt source."""
    name: str
    database: str | None = None
    schema_name: str | None = None
    tables: list[dict[str, Any]] = field(default_factory=list)
    description: str = ""
    meta: dict[str, Any] = field(default_factory=dict)
    freshness: dict[str, Any] | None = None


@dataclass
class DbtProject:
    """Representation of a dbt project."""
    name: str
    version: str
    project_path: Path
    models: list[DbtModel] = field(default_factory=list)
    sources: list[DbtSource] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)


class DbtProjectScanner:
    """Scan a dbt project directory."""

    def __init__(self, project_path: str | Path):
        """Initialize scanner.

        Args:
            project_path: Path to dbt project root
        """
        self.project_path = Path(project_path)
        self.project: DbtProject | None = None

    def scan(self) -> DbtProject:
        """Scan the dbt project.

        Returns:
            DbtProject with models and sources
        """
        # Read dbt_project.yml
        project_file = self.project_path / "dbt_project.yml"
        if not project_file.exists():
            raise FileNotFoundError(f"dbt_project.yml not found in {self.project_path}")

        with open(project_file) as f:
            project_config = yaml.safe_load(f)

        self.project = DbtProject(
            name=project_config.get("name", "unknown"),
            version=project_config.get("version", "0.0.0"),
            project_path=self.project_path,
            config=project_config,
        )

        # Scan models
        self._scan_models()

        # Scan schema files
        self._scan_schema_files()

        return self.project

    def _scan_models(self) -> None:
        """Scan model SQL files."""
        models_path = self.project_path / "models"
        if not models_path.exists():
            return

        for sql_file in models_path.rglob("*.sql"):
            # Skip if it's a test file
            if sql_file.parent.name == "tests":
                continue

            model_name = sql_file.stem
            raw_sql = sql_file.read_text()

            model = DbtModel(
                name=model_name,
                path=sql_file,
                raw_sql=raw_sql,
            )

            self.project.models.append(model)

    def _scan_schema_files(self) -> None:
        """Scan schema.yml files for model metadata."""
        models_path = self.project_path / "models"
        if not models_path.exists():
            return

        for schema_file in models_path.rglob("*.yml"):
            self._parse_schema_file(schema_file)

        for schema_file in models_path.rglob("*.yaml"):
            self._parse_schema_file(schema_file)

    def _parse_schema_file(self, schema_file: Path) -> None:
        """Parse a schema.yml file."""
        with open(schema_file) as f:
            schema = yaml.safe_load(f)

        if not schema:
            return

        # Parse models
        if "models" in schema:
            for model_dict in schema["models"]:
                self._update_model_from_schema(model_dict)

        # Parse sources
        if "sources" in schema:
            for source_dict in schema["sources"]:
                source = DbtSource(
                    name=source_dict.get("name", "unknown"),
                    database=source_dict.get("database"),
                    schema_name=source_dict.get("schema"),
                    tables=source_dict.get("tables", []),
                    description=source_dict.get("description", ""),
                    meta=source_dict.get("meta", {}),
                    freshness=source_dict.get("freshness"),
                )
                self.project.sources.append(source)

    def _update_model_from_schema(self, model_dict: dict[str, Any]) -> None:
        """Update a model with schema information."""
        model_name = model_dict.get("name")
        if not model_name:
            return

        # Find existing model or create new one
        model = None
        for m in self.project.models:
            if m.name == model_name:
                model = m
                break

        if model is None:
            model = DbtModel(name=model_name)
            self.project.models.append(model)

        # Update model properties
        model.description = model_dict.get("description", model.description)
        model.config = model_dict.get("config", model.config)
        model.meta = model_dict.get("meta", model.meta)
        model.tests = model_dict.get("tests", model.tests)

        # Parse columns
        for col_dict in model_dict.get("columns", []):
            col = DbtColumn(
                name=col_dict.get("name", ""),
                description=col_dict.get("description", ""),
                data_type=col_dict.get("data_type"),
                tests=col_dict.get("tests", []),
                meta=col_dict.get("meta", {}),
            )
            model.columns.append(col)

    def get_model(self, name: str) -> DbtModel | None:
        """Get a model by name.

        Args:
            name: Model name

        Returns:
            DbtModel or None
        """
        if not self.project:
            return None

        for model in self.project.models:
            if model.name == name:
                return model
        return None

    def get_source(self, name: str) -> DbtSource | None:
        """Get a source by name.

        Args:
            name: Source name

        Returns:
            DbtSource or None
        """
        if not self.project:
            return None

        for source in self.project.sources:
            if source.name == name:
                return source
        return None

    def extract_tests_for_model(self, model_name: str) -> list[dict[str, Any]]:
        """Extract all tests for a model.

        Args:
            model_name: Name of the model

        Returns:
            List of test configurations
        """
        model = self.get_model(model_name)
        if not model:
            return []

        tests = list(model.tests)

        # Add column-level tests
        for col in model.columns:
            for test in col.tests:
                if isinstance(test, str):
                    tests.append({"name": test, "column": col.name})
                elif isinstance(test, dict):
                    test_name = list(test.keys())[0]
                    test_config = test[test_name] or {}
                    tests.append({
                        "name": test_name,
                        "column": col.name,
                        "config": test_config,
                    })

        return tests

    def generate_datacheck_config(self, model_name: str) -> dict[str, Any]:
        """Generate DataCheck config from dbt model tests.

        Args:
            model_name: Name of the model

        Returns:
            DataCheck configuration dictionary
        """

        tests = self.extract_tests_for_model(model_name)
        rules_config = []

        for test_info in tests:
            test_name = test_info.get("name", "")
            column = test_info.get("column")
            config = test_info.get("config", {})

            # Map dbt tests to DataCheck rules
            if test_name == "not_null":
                rules_config.append({
                    "type": "not_null",
                    "columns": [column] if column else [],
                })
            elif test_name == "unique":
                rules_config.append({
                    "type": "unique",
                    "columns": [column] if column else [],
                })
            elif test_name == "accepted_values":
                rules_config.append({
                    "type": "enum",
                    "columns": [column] if column else [],
                    "values": config.get("values", []),
                })
            elif "accepted_range" in test_name:
                rule_config = {
                    "type": "range",
                    "columns": [column] if column else [],
                }
                if "min_value" in config:
                    rule_config["min"] = config["min_value"]
                if "max_value" in config:
                    rule_config["max"] = config["max_value"]
                rules_config.append(rule_config)

        return {"rules": rules_config}
