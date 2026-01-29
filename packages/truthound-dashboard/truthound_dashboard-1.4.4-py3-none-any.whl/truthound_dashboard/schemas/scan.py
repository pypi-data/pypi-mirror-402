"""PII scan-related Pydantic schemas.

This module defines schemas for PII scan API operations using th.scan().

The scan functionality detects personally identifiable information (PII)
in datasets and checks compliance with privacy regulations (GDPR, CCPA, LGPD).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import Field

from .base import BaseSchema, IDMixin, ListResponseWrapper


class Regulation(str, Enum):
    """Supported privacy regulations for compliance checking."""

    GDPR = "gdpr"
    CCPA = "ccpa"
    LGPD = "lgpd"


# Type alias for regulation literal
RegulationLiteral = Literal["gdpr", "ccpa", "lgpd"]

# PII type categories commonly detected
PII_TYPES = [
    "email",
    "phone",
    "ssn",
    "credit_card",
    "ip_address",
    "date_of_birth",
    "address",
    "name",
    "passport",
    "driver_license",
    "national_id",
    "bank_account",
    "medical_record",
    "biometric",
]


class PIIScanRequest(BaseSchema):
    """Request to run PII scan on a data source.

    This schema maps to truthound's th.scan() parameters for maximum flexibility.
    All optional parameters default to None to use truthound's defaults.
    """

    # Column filtering
    columns: list[str] | None = Field(
        default=None,
        description="Columns to scan. If None, all columns are scanned.",
        examples=[["email", "phone", "ssn"]],
    )

    # Regulation compliance checking
    regulations: list[RegulationLiteral] | None = Field(
        default=None,
        description="Privacy regulations to check compliance: gdpr, ccpa, lgpd",
        examples=[["gdpr", "ccpa"]],
    )

    # Confidence threshold
    min_confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for PII detection (0.0-1.0)",
        examples=[0.8, 0.9],
    )


class PIIFinding(BaseSchema):
    """Single PII finding detected in a column.

    Represents one type of PII detected within a specific column,
    including confidence score and sample information.
    """

    column: str = Field(..., description="Column where PII was detected")
    pii_type: str = Field(
        ...,
        description="Type of PII detected",
        examples=["email", "ssn", "phone", "credit_card"],
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for this detection (0.0-1.0)",
    )
    sample_count: int = Field(
        ...,
        ge=0,
        description="Number of values matching this PII type",
    )
    sample_values: list[str] | None = Field(
        default=None,
        description="Sample values that matched (redacted for privacy)",
    )


class RegulationViolation(BaseSchema):
    """Regulation compliance violation.

    Represents a violation of a specific privacy regulation
    detected in the scanned data.
    """

    regulation: RegulationLiteral = Field(
        ...,
        description="Violated regulation",
    )
    column: str = Field(
        ...,
        description="Column with violation",
    )
    pii_type: str = Field(
        ...,
        description="Type of PII causing the violation",
    )
    message: str = Field(
        ...,
        description="Human-readable violation description",
    )
    severity: Literal["low", "medium", "high", "critical"] = Field(
        default="high",
        description="Severity level of the violation",
    )


class PIIScanSummary(BaseSchema):
    """Summary statistics for a PII scan run."""

    total_columns_scanned: int = Field(
        default=0,
        ge=0,
        description="Total number of columns scanned",
    )
    columns_with_pii: int = Field(
        default=0,
        ge=0,
        description="Number of columns containing PII",
    )
    total_findings: int = Field(
        default=0,
        ge=0,
        description="Total number of PII findings",
    )
    has_violations: bool = Field(
        default=False,
        description="Whether any regulation violations were found",
    )
    total_violations: int = Field(
        default=0,
        ge=0,
        description="Total number of regulation violations",
    )


class PIIScanResponse(IDMixin, PIIScanSummary):
    """Full PII scan response with all details."""

    source_id: str = Field(..., description="Source that was scanned")
    status: Literal["pending", "running", "success", "failed", "error"] = Field(
        ...,
        description="Current scan status",
    )

    # Data statistics
    row_count: int | None = Field(default=None, description="Number of rows scanned")
    column_count: int | None = Field(default=None, description="Number of columns")

    # Scan configuration used
    min_confidence: float = Field(
        default=0.8,
        description="Confidence threshold used for this scan",
    )
    regulations_checked: list[str] | None = Field(
        default=None,
        description="Regulations that were checked",
    )

    # Findings (full details)
    findings: list[PIIFinding] = Field(
        default_factory=list,
        description="List of PII findings",
    )

    # Regulation violations
    violations: list[RegulationViolation] = Field(
        default_factory=list,
        description="List of regulation violations",
    )

    # Error info (if status is 'error')
    error_message: str | None = Field(
        default=None,
        description="Error message if scan failed",
    )

    # Timing
    duration_ms: int | None = Field(
        default=None,
        ge=0,
        description="Scan duration in milliseconds",
    )
    started_at: datetime | None = Field(default=None, description="Start timestamp")
    completed_at: datetime | None = Field(
        default=None,
        description="Completion timestamp",
    )
    created_at: datetime = Field(..., description="Record creation timestamp")

    @classmethod
    def from_model(cls, scan: Any) -> PIIScanResponse:
        """Create response from model.

        Args:
            scan: PIIScan model instance.

        Returns:
            PIIScanResponse instance.
        """
        findings = []
        if scan.result_json and "findings" in scan.result_json:
            findings = [
                PIIFinding(**finding) for finding in scan.result_json["findings"]
            ]

        violations = []
        if scan.result_json and "violations" in scan.result_json:
            violations = [
                RegulationViolation(**violation)
                for violation in scan.result_json["violations"]
            ]

        return cls(
            id=scan.id,
            source_id=scan.source_id,
            status=scan.status,
            total_columns_scanned=scan.total_columns_scanned or 0,
            columns_with_pii=scan.columns_with_pii or 0,
            total_findings=scan.total_findings or 0,
            has_violations=scan.has_violations or False,
            total_violations=scan.total_violations or 0,
            row_count=scan.row_count,
            column_count=scan.column_count,
            min_confidence=scan.min_confidence or 0.8,
            regulations_checked=scan.regulations_checked,
            findings=findings,
            violations=violations,
            error_message=scan.error_message,
            duration_ms=scan.duration_ms,
            started_at=scan.started_at,
            completed_at=scan.completed_at,
            created_at=scan.created_at,
        )


class PIIScanListItem(IDMixin, PIIScanSummary):
    """PII scan list item (without full findings/violations)."""

    source_id: str
    status: Literal["pending", "running", "success", "failed", "error"]
    row_count: int | None = None
    column_count: int | None = None
    min_confidence: float = 0.8
    regulations_checked: list[str] | None = None
    duration_ms: int | None = None
    created_at: datetime

    @classmethod
    def from_model(cls, scan: Any) -> PIIScanListItem:
        """Create list item from model.

        Args:
            scan: PIIScan model instance.

        Returns:
            PIIScanListItem instance.
        """
        return cls(
            id=scan.id,
            source_id=scan.source_id,
            status=scan.status,
            total_columns_scanned=scan.total_columns_scanned or 0,
            columns_with_pii=scan.columns_with_pii or 0,
            total_findings=scan.total_findings or 0,
            has_violations=scan.has_violations or False,
            total_violations=scan.total_violations or 0,
            row_count=scan.row_count,
            column_count=scan.column_count,
            min_confidence=scan.min_confidence or 0.8,
            regulations_checked=scan.regulations_checked,
            duration_ms=scan.duration_ms,
            created_at=scan.created_at,
        )


class PIIScanListResponse(ListResponseWrapper[PIIScanListItem]):
    """Paginated PII scan list response."""

    pass
