"""Pydantic models for DataCheck API.

Defines request/response schemas for the REST API.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Any
from datetime import datetime
from enum import Enum
import re


class ValidationStatus(str, Enum):
    """Validation status enum."""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    UNKNOWN = "unknown"


class AlertSeverity(str, Enum):
    """Alert severity enum."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class RuleResult(BaseModel):
    """Result of a single validation rule."""

    id: int
    rule_name: str
    rule_type: str | None = None
    column_name: str | None = None
    status: ValidationStatus
    passed_rows: int = 0
    failed_rows: int = 0
    error_message: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    """Complete validation result."""

    id: int
    filename: str
    source: str | None = None
    status: ValidationStatus
    pass_rate: float | None = None
    quality_score: float | None = None
    total_rows: int | None = None
    total_columns: int | None = None
    rules_run: int | None = None
    rules_passed: int | None = None
    rules_failed: int | None = None
    timestamp: datetime
    duration_seconds: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ValidationDetail(BaseModel):
    """Detailed validation result with rules."""

    id: int
    filename: str
    source: str | None = None
    status: ValidationStatus
    pass_rate: float | None = None
    quality_score: float | None = None
    total_rows: int | None = None
    total_columns: int | None = None
    rules_run: int | None = None
    rules_passed: int | None = None
    rules_failed: int | None = None
    timestamp: datetime
    duration_seconds: float | None = None
    rules: list[RuleResult] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ValidationSummary(BaseModel):
    """Summary of validation statistics."""

    total_checks: int = 0
    pass_rate: float = 0.0
    quality_score: str = "Unknown"
    passed: int = 0
    failed: int = 0
    total_rows_checked: int = 0


class TrendData(BaseModel):
    """Trend data point."""

    period: str
    pass_rate: float
    count: int
    avg_quality: float | None = None


class TopIssue(BaseModel):
    """Common validation issue."""

    rule_name: str
    rule_type: str | None = None
    column_name: str | None = None
    failure_count: int
    avg_failed_rows: float


class Alert(BaseModel):
    """Alert record."""

    id: int
    validation_id: int | None = None
    severity: AlertSeverity
    title: str
    message: str
    source: str | None = None
    timestamp: datetime
    acknowledged: bool = False
    acknowledged_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AlertCreate(BaseModel):
    """Schema for creating an alert."""

    validation_id: int | None = None
    severity: AlertSeverity = AlertSeverity.INFO
    title: str = Field(..., max_length=200)
    message: str = Field(..., max_length=2000)
    source: str | None = Field(None, max_length=200)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator('title', 'message')
    @classmethod
    def validate_text_fields(cls, v: str) -> str:
        """Validate text fields to prevent injection and control characters."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")

        # Prevent null bytes
        if '\x00' in v:
            raise ValueError("Field cannot contain null bytes")

        # Prevent control characters (except newlines and tabs for message)
        if any(ord(c) < 32 and c not in '\n\t' for c in v):
            raise ValueError("Field cannot contain control characters")

        return v.strip()

    @field_validator('source')
    @classmethod
    def validate_source(cls, v: str | None) -> str | None:
        """Validate source field length and format."""
        if v is None:
            return v

        # Prevent null bytes (check before stripping)
        if '\x00' in v:
            raise ValueError("Source cannot contain null bytes")

        # Prevent control characters (check before stripping)
        if any(ord(c) < 32 for c in v):
            raise ValueError("Source cannot contain control characters")

        v = v.strip()
        if not v:
            return None

        return v


class ValidationCreate(BaseModel):
    """Schema for creating a validation record."""

    filename: str = Field(..., max_length=500)
    source: str | None = Field(None, max_length=200)
    status: ValidationStatus
    pass_rate: float | None = None
    quality_score: float | None = None
    total_rows: int | None = None
    total_columns: int | None = None
    rules_run: int | None = None
    rules_passed: int | None = None
    rules_failed: int | None = None
    duration_seconds: float | None = None
    config_hash: str | None = Field(None, max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Validate filename to prevent path traversal and injection attacks."""
        if not v or not v.strip():
            raise ValueError("Filename cannot be empty")

        # Prevent path traversal
        if '..' in v:
            raise ValueError("Filename cannot contain '..' (path traversal)")

        # Prevent null bytes
        if '\x00' in v:
            raise ValueError("Filename cannot contain null bytes")

        # Prevent absolute paths (Unix and Windows)
        if v.startswith('/') or (len(v) > 1 and v[1] == ':'):
            raise ValueError("Filename cannot be an absolute path")

        # Prevent control characters
        if any(ord(c) < 32 for c in v):
            raise ValueError("Filename cannot contain control characters")

        return v.strip()

    @field_validator('source')
    @classmethod
    def validate_source(cls, v: str | None) -> str | None:
        """Validate source field length and format."""
        if v is None:
            return v

        # Prevent null bytes (check before stripping)
        if '\x00' in v:
            raise ValueError("Source cannot contain null bytes")

        # Prevent control characters (check before stripping)
        if any(ord(c) < 32 for c in v):
            raise ValueError("Source cannot contain control characters")

        v = v.strip()
        if not v:
            return None

        return v


class RuleResultCreate(BaseModel):
    """Schema for creating a rule result."""

    validation_id: int
    rule_name: str = Field(..., max_length=200)
    rule_type: str | None = Field(None, max_length=100)
    column_name: str | None = Field(None, max_length=200)
    status: ValidationStatus
    passed_rows: int = 0
    failed_rows: int = 0
    error_message: str | None = Field(None, max_length=1000)
    details: dict[str, Any] = Field(default_factory=dict)

    @field_validator('rule_name', 'rule_type', 'column_name', 'error_message')
    @classmethod
    def validate_text_fields(cls, v: str | None) -> str | None:
        """Validate text fields to prevent injection and control characters."""
        if v is None:
            return v

        v = v.strip()
        if not v:
            return None

        # Prevent null bytes
        if '\x00' in v:
            raise ValueError("Field cannot contain null bytes")

        # Prevent control characters (except newlines and tabs for error_message)
        if any(ord(c) < 32 and c not in '\n\t' for c in v):
            raise ValueError("Field cannot contain control characters")

        return v


class MetricCreate(BaseModel):
    """Schema for creating a metric."""

    name: str = Field(..., max_length=100)
    value: float
    source: str | None = Field(None, max_length=200)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate metric name format."""
        if not v or not v.strip():
            raise ValueError("Metric name cannot be empty")

        # Prevent null bytes (check before stripping)
        if '\x00' in v:
            raise ValueError("Metric name cannot contain null bytes")

        v = v.strip()

        # Metric names should follow common naming conventions
        # Allow alphanumeric, underscores, dots, and hyphens
        if not re.match(r'^[a-zA-Z0-9._-]+$', v):
            raise ValueError(
                "Metric name can only contain alphanumeric characters, "
                "underscores, dots, and hyphens"
            )

        return v

    @field_validator('source')
    @classmethod
    def validate_source(cls, v: str | None) -> str | None:
        """Validate source field length and format."""
        if v is None:
            return v

        # Prevent null bytes (check before stripping)
        if '\x00' in v:
            raise ValueError("Source cannot contain null bytes")

        # Prevent control characters (check before stripping)
        if any(ord(c) < 32 for c in v):
            raise ValueError("Source cannot contain control characters")

        v = v.strip()
        if not v:
            return None

        return v


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    database: str


class APIInfo(BaseModel):
    """API information response."""

    name: str
    version: str
    status: str
    endpoints: list[str]
