"""Validation-related Pydantic schemas.

This module defines schemas for validation API operations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from .base import BaseSchema, IDMixin, ListResponseWrapper
from .validators import ValidatorConfig

# Validation status types
ValidationStatus = Literal["pending", "running", "success", "failed", "error"]

# Issue severity types
IssueSeverity = Literal["critical", "high", "medium", "low"]


class ValidationIssue(BaseSchema):
    """Single validation issue.

    Represents one issue found during validation, mapping to
    truthound's ValidationIssue dataclass.
    """

    column: str = Field(..., description="Column where issue was found")
    issue_type: str = Field(
        ..., description="Type of issue", examples=["null_values", "type_mismatch"]
    )
    count: int = Field(..., ge=0, description="Number of occurrences")
    severity: IssueSeverity = Field(..., description="Issue severity level")
    details: str | None = Field(default=None, description="Detailed description")
    expected: Any | None = Field(default=None, description="Expected value/type")
    actual: Any | None = Field(default=None, description="Actual value/type found")
    sample_values: list[Any] | None = Field(
        default=None,
        description="Sample problematic values",
    )


class CustomValidatorConfig(BaseSchema):
    """Configuration for running a custom validator."""

    validator_id: str = Field(
        ..., description="ID of the custom validator to run"
    )
    column: str = Field(
        ..., description="Column to validate"
    )
    params: dict[str, Any] | None = Field(
        default=None, description="Parameter values for the validator"
    )


class ValidationRunRequest(BaseSchema):
    """Request to run validation on a source.

    This schema maps to truthound's th.check() parameters for maximum flexibility.
    All optional parameters default to None/False to use truthound's defaults.

    Supports three modes:
    1. Simple mode: Use `validators` list with validator names (backward compatible)
    2. Advanced mode: Use `validator_configs` for per-validator parameter configuration
    3. Custom validators: Use `custom_validators` to include user-defined validators
    """

    # Core validation options - Simple mode (backward compatible)
    validators: list[str] | None = Field(
        default=None,
        description="Specific validators to run by name. If None, all validators are used.",
        examples=[["Null", "Duplicate", "ColumnExists"]],
    )

    # Advanced mode - Per-validator configuration
    validator_configs: list[ValidatorConfig] | None = Field(
        default=None,
        description=(
            "Advanced: Configure individual validators with specific parameters. "
            "Takes precedence over 'validators' list if provided."
        ),
    )

    # Custom validators - User-defined validators
    custom_validators: list[CustomValidatorConfig] | None = Field(
        default=None,
        description=(
            "Custom validators to run alongside built-in validators. "
            "Each config specifies the validator_id, target column, and parameters."
        ),
    )

    schema_path: str | None = Field(
        default=None,
        description="Path to schema YAML file for schema validation",
    )
    auto_schema: bool = Field(
        default=False,
        description="Auto-learn and cache schema for validation",
    )

    # Column filtering
    columns: list[str] | None = Field(
        default=None,
        description="Columns to validate. If None, all columns are validated.",
        examples=[["user_id", "email", "created_at"]],
    )

    # Severity filtering
    min_severity: Literal["low", "medium", "high", "critical"] | None = Field(
        default=None,
        description="Minimum severity level to report. Issues below this level are ignored.",
        examples=["medium"],
    )

    # Execution behavior
    strict: bool = Field(
        default=False,
        description="If True, raise exception on validation failures instead of returning results.",
    )

    # Performance options
    parallel: bool = Field(
        default=False,
        description="If True, uses DAG-based parallel execution for validators.",
    )
    max_workers: int | None = Field(
        default=None,
        ge=1,
        le=32,
        description="Maximum number of worker threads for parallel execution. Only used when parallel=True.",
        examples=[4, 8],
    )
    pushdown: bool | None = Field(
        default=None,
        description="Enable query pushdown optimization for SQL data sources. None uses auto-detection.",
    )


class ValidationSummary(BaseSchema):
    """Summary statistics for a validation run."""

    passed: bool = Field(..., description="Whether validation passed")
    has_critical: bool = Field(default=False, description="Has critical issues")
    has_high: bool = Field(default=False, description="Has high severity issues")
    total_issues: int = Field(default=0, ge=0, description="Total issue count")
    critical_issues: int = Field(default=0, ge=0, description="Critical issue count")
    high_issues: int = Field(default=0, ge=0, description="High severity issue count")
    medium_issues: int = Field(
        default=0, ge=0, description="Medium severity issue count"
    )
    low_issues: int = Field(default=0, ge=0, description="Low severity issue count")


class ValidationResponse(IDMixin, ValidationSummary):
    """Full validation response with all details."""

    source_id: str = Field(..., description="Source that was validated")
    status: ValidationStatus = Field(..., description="Current validation status")

    # Data statistics
    row_count: int | None = Field(default=None, description="Number of rows validated")
    column_count: int | None = Field(default=None, description="Number of columns")

    # Issues list (full details)
    issues: list[ValidationIssue] = Field(
        default_factory=list,
        description="List of validation issues",
    )

    # Error info (if status is 'error')
    error_message: str | None = Field(
        default=None,
        description="Error message if validation failed",
    )

    # Timing
    duration_ms: int | None = Field(
        default=None,
        ge=0,
        description="Validation duration in milliseconds",
    )
    started_at: datetime | None = Field(default=None, description="Start timestamp")
    completed_at: datetime | None = Field(
        default=None, description="Completion timestamp"
    )
    created_at: datetime = Field(..., description="Record creation timestamp")

    @classmethod
    def from_model(cls, validation: Any) -> ValidationResponse:
        """Create response from model.

        Args:
            validation: Validation model instance.

        Returns:
            ValidationResponse instance.
        """
        issues = []
        if validation.result_json and "issues" in validation.result_json:
            issues = [
                ValidationIssue(**issue) for issue in validation.result_json["issues"]
            ]

        return cls(
            id=validation.id,
            source_id=validation.source_id,
            status=validation.status,
            passed=validation.passed or False,
            has_critical=validation.has_critical or False,
            has_high=validation.has_high or False,
            total_issues=validation.total_issues or 0,
            critical_issues=validation.critical_issues or 0,
            high_issues=validation.high_issues or 0,
            medium_issues=validation.medium_issues or 0,
            low_issues=validation.low_issues or 0,
            row_count=validation.row_count,
            column_count=validation.column_count,
            issues=issues,
            error_message=validation.error_message,
            duration_ms=validation.duration_ms,
            started_at=validation.started_at,
            completed_at=validation.completed_at,
            created_at=validation.created_at,
        )


class ValidationListItem(IDMixin, ValidationSummary):
    """Validation list item (without full issues)."""

    source_id: str
    status: ValidationStatus
    row_count: int | None = None
    column_count: int | None = None
    duration_ms: int | None = None
    created_at: datetime

    @classmethod
    def from_model(cls, validation: Any) -> ValidationListItem:
        """Create list item from model.

        Args:
            validation: Validation model instance.

        Returns:
            ValidationListItem instance.
        """
        return cls(
            id=validation.id,
            source_id=validation.source_id,
            status=validation.status,
            passed=validation.passed or False,
            has_critical=validation.has_critical or False,
            has_high=validation.has_high or False,
            total_issues=validation.total_issues or 0,
            critical_issues=validation.critical_issues or 0,
            high_issues=validation.high_issues or 0,
            medium_issues=validation.medium_issues or 0,
            low_issues=validation.low_issues or 0,
            row_count=validation.row_count,
            column_count=validation.column_count,
            duration_ms=validation.duration_ms,
            created_at=validation.created_at,
        )


class ValidationListResponse(ListResponseWrapper[ValidationListItem]):
    """Paginated validation list response."""

    pass
