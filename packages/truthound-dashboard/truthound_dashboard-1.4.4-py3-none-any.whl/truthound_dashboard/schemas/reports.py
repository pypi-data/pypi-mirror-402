"""Report-related Pydantic schemas.

This module defines schemas for report generation API operations.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import Field

from .base import BaseSchema, IDMixin, ListResponseWrapper, TimestampMixin

# Report format types
ReportFormatType = Literal["html", "csv", "json", "markdown", "pdf", "junit", "excel", "custom"]

# Report theme types
ReportThemeType = Literal["light", "dark", "professional", "minimal", "high_contrast"]


class ReportStatus(str, Enum):
    """Status of report generation."""

    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class ReportGenerateRequest(BaseSchema):
    """Request to generate a validation report.

    All parameters are optional with sensible defaults.
    """

    format: ReportFormatType = Field(
        default="html",
        description="Output format for the report",
    )
    theme: ReportThemeType = Field(
        default="professional",
        description="Visual theme for the report (mainly for HTML)",
    )
    title: str | None = Field(
        default=None,
        description="Custom title for the report. Auto-generated if not provided.",
    )
    include_samples: bool = Field(
        default=True,
        description="Include sample problematic values in the report",
    )
    include_statistics: bool = Field(
        default=True,
        description="Include data statistics section",
    )
    custom_metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional metadata to include in the report",
    )


class ReportMetadataResponse(BaseSchema):
    """Report metadata returned in API responses."""

    title: str = Field(..., description="Report title")
    generated_at: datetime = Field(..., description="Generation timestamp")
    source_name: str | None = Field(default=None, description="Data source name")
    source_id: str | None = Field(default=None, description="Data source ID")
    validation_id: str | None = Field(default=None, description="Validation ID")
    theme: str = Field(..., description="Visual theme used")
    format: str = Field(..., description="Output format")


class ReportResponse(BaseSchema):
    """Response for report generation.

    Contains metadata about the generated report and download info.
    Note: The actual content is returned as a file download, not in this response.
    """

    filename: str = Field(..., description="Suggested filename for download")
    content_type: str = Field(..., description="MIME content type")
    size_bytes: int = Field(..., description="Size of report content in bytes")
    generation_time_ms: int = Field(
        ..., description="Time taken to generate in milliseconds"
    )
    metadata: ReportMetadataResponse = Field(..., description="Report metadata")


class AvailableFormatsResponse(BaseSchema):
    """Response listing available report formats."""

    formats: list[str] = Field(
        ...,
        description="List of available format names",
        examples=[["html", "csv", "json", "markdown"]],
    )
    themes: list[str] = Field(
        ...,
        description="List of available theme names",
        examples=[["light", "dark", "professional", "minimal", "high_contrast"]],
    )


# =============================================================================
# Report History Schemas
# =============================================================================


class GeneratedReportBase(BaseSchema):
    """Base schema for generated report."""

    name: str = Field(max_length=255, description="Report name")
    description: str | None = Field(default=None, description="Report description")
    format: ReportFormatType = Field(default="html", description="Output format")
    theme: ReportThemeType | None = Field(default=None, description="Visual theme")
    locale: str = Field(default="en", max_length=10, description="Language locale")
    config: dict[str, Any] | None = Field(default=None, description="Generation config")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional metadata")


class GeneratedReportCreate(GeneratedReportBase):
    """Schema for creating a generated report record."""

    validation_id: str | None = Field(default=None, description="Associated validation ID")
    source_id: str | None = Field(default=None, description="Associated source ID")
    reporter_id: str | None = Field(default=None, description="Custom reporter ID if used")
    expires_in_days: int | None = Field(
        default=30,
        ge=1,
        le=365,
        description="Days until report expires (1-365)",
    )


class GeneratedReportUpdate(BaseSchema):
    """Schema for updating a generated report record."""

    name: str | None = Field(default=None, max_length=255)
    description: str | None = None
    metadata: dict[str, Any] | None = None


class GeneratedReportResponse(GeneratedReportBase, IDMixin, TimestampMixin):
    """Response schema for generated report."""

    validation_id: str | None = None
    source_id: str | None = None
    reporter_id: str | None = None
    status: ReportStatus = ReportStatus.PENDING
    file_path: str | None = None
    file_size: int | None = None
    content_hash: str | None = None
    error_message: str | None = None
    generation_time_ms: float | None = None
    expires_at: datetime | None = None
    downloaded_count: int = 0
    last_downloaded_at: datetime | None = None

    # Enriched fields (populated in API)
    source_name: str | None = Field(default=None, description="Source name for display")
    reporter_name: str | None = Field(default=None, description="Reporter name for display")
    download_url: str | None = Field(default=None, description="URL to download the report")

    @classmethod
    def from_model(cls, model: Any) -> "GeneratedReportResponse":
        """Create response from database model."""
        return cls(
            id=str(model.id),
            name=model.name,
            description=model.description,
            format=model.format.value if hasattr(model.format, "value") else model.format,
            theme=model.theme,
            locale=model.locale,
            config=model.config,
            metadata=model.metadata,
            validation_id=str(model.validation_id) if model.validation_id else None,
            source_id=str(model.source_id) if model.source_id else None,
            reporter_id=str(model.reporter_id) if model.reporter_id else None,
            status=ReportStatus(model.status.value if hasattr(model.status, "value") else model.status),
            file_path=model.file_path,
            file_size=model.file_size,
            content_hash=model.content_hash,
            error_message=model.error_message,
            generation_time_ms=model.generation_time_ms,
            expires_at=model.expires_at,
            downloaded_count=model.downloaded_count,
            last_downloaded_at=model.last_downloaded_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            source_name=model.source.name if model.source else None,
            reporter_name=model.reporter.display_name if model.reporter else None,
        )


class GeneratedReportListResponse(ListResponseWrapper[GeneratedReportResponse]):
    """Paginated list response for generated reports."""

    pass


class BulkReportGenerateRequest(BaseSchema):
    """Request to generate reports for multiple validations."""

    validation_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of validation IDs (1-100)",
    )
    format: ReportFormatType = Field(default="html", description="Output format")
    theme: ReportThemeType = Field(default="professional", description="Visual theme")
    locale: str = Field(default="en", max_length=10, description="Language locale")
    reporter_id: str | None = Field(default=None, description="Custom reporter ID")
    config: dict[str, Any] | None = Field(default=None, description="Reporter config")
    save_to_history: bool = Field(
        default=True,
        description="Save reports to history",
    )
    expires_in_days: int | None = Field(
        default=30,
        ge=1,
        le=365,
        description="Days until reports expire",
    )


class BulkReportGenerateResponse(BaseSchema):
    """Response for bulk report generation."""

    total: int = Field(..., description="Total reports requested")
    successful: int = Field(..., description="Successfully generated count")
    failed: int = Field(..., description="Failed generation count")
    reports: list[GeneratedReportResponse] = Field(
        default_factory=list,
        description="Generated report records",
    )
    errors: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Error details for failed reports",
    )


class ReportHistoryQuery(BaseSchema):
    """Query parameters for report history."""

    source_id: str | None = Field(default=None, description="Filter by source ID")
    validation_id: str | None = Field(default=None, description="Filter by validation ID")
    reporter_id: str | None = Field(default=None, description="Filter by reporter ID")
    format: ReportFormatType | None = Field(default=None, description="Filter by format")
    status: ReportStatus | None = Field(default=None, description="Filter by status")
    include_expired: bool = Field(
        default=False,
        description="Include expired reports",
    )
    search: str | None = Field(default=None, description="Search by name")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: Literal["asc", "desc"] = Field(default="desc", description="Sort order")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")


class ReportStatistics(BaseSchema):
    """Statistics for generated reports."""

    total_reports: int = Field(..., description="Total reports generated")
    total_size_bytes: int = Field(..., description="Total storage used")
    reports_by_format: dict[str, int] = Field(
        default_factory=dict,
        description="Count by format",
    )
    reports_by_status: dict[str, int] = Field(
        default_factory=dict,
        description="Count by status",
    )
    total_downloads: int = Field(..., description="Total download count")
    avg_generation_time_ms: float | None = Field(
        default=None,
        description="Average generation time",
    )
    expired_count: int = Field(default=0, description="Expired reports count")
    reporters_used: int = Field(default=0, description="Unique reporters used")
