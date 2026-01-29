"""API module for DataCheck web dashboard.

Provides FastAPI-based REST API for monitoring data quality.
"""

from datacheck.api.app import create_app, app
from datacheck.api.database import Database
from datacheck.api.models import (
    ValidationSummary,
    ValidationDetail,
    ValidationResult,
    RuleResult,
    TrendData,
    TopIssue,
)

__all__ = [
    "create_app",
    "app",
    "Database",
    "ValidationSummary",
    "ValidationDetail",
    "ValidationResult",
    "RuleResult",
    "TrendData",
    "TopIssue",
]
