"""Profile comparison Pydantic schemas.

This module defines schemas for profile comparison,
including time-series trends and version-to-version comparison.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field

from .base import BaseSchema


class TrendDirection(str, Enum):
    """Direction of metric trend."""

    UP = "up"
    DOWN = "down"
    STABLE = "stable"


# =============================================================================
# Profile Summary Schemas
# =============================================================================


class ProfileSummary(BaseSchema):
    """Summary of a profile for listing."""

    id: str = Field(..., description="Profile ID")
    source_id: str = Field(..., description="Source ID")
    row_count: int = Field(..., description="Number of rows")
    column_count: int = Field(..., description="Number of columns")
    size_bytes: int = Field(default=0, description="Data size in bytes")
    created_at: datetime = Field(..., description="When profile was created")


class ProfileListResponse(BaseSchema):
    """List response for profiles."""

    profiles: list[ProfileSummary] = Field(
        default_factory=list, description="List of profiles"
    )
    total: int = Field(default=0, description="Total count")
    source_id: str = Field(..., description="Source ID")


# =============================================================================
# Column Comparison Schemas
# =============================================================================


class StatisticalTestInfo(BaseSchema):
    """Information about statistical significance test results."""

    test_name: str = Field(..., description="Name of the statistical test used")
    p_value: float = Field(..., description="P-value from the test")
    is_significant: bool = Field(..., description="Whether result is significant at alpha=0.05")
    effect_size: float | None = Field(default=None, description="Effect size (Cohen's d or r)")
    interpretation: str = Field(default="", description="Human-readable interpretation")


class ColumnComparison(BaseSchema):
    """Comparison result for a single column metric."""

    column: str = Field(..., description="Column name")
    metric: str = Field(..., description="Metric name (e.g., null_pct, unique_pct)")
    baseline_value: Any = Field(..., description="Value in baseline profile")
    current_value: Any = Field(..., description="Value in current profile")
    change: float | None = Field(
        default=None, description="Absolute change in value"
    )
    change_pct: float | None = Field(
        default=None, description="Percentage change"
    )
    is_significant: bool = Field(
        default=False, description="Whether change is statistically significant"
    )
    trend: TrendDirection = Field(
        default=TrendDirection.STABLE, description="Direction of change"
    )
    statistical_test: dict[str, Any] | None = Field(
        default=None,
        description="Statistical test results (test_name, p_value, effect_size, interpretation)"
    )


class ColumnComparisonSummary(BaseSchema):
    """Summary of changes for a single column."""

    column: str = Field(..., description="Column name")
    metrics_changed: int = Field(default=0, description="Number of metrics changed")
    significant_changes: int = Field(
        default=0, description="Number of significant changes"
    )
    comparisons: list[ColumnComparison] = Field(
        default_factory=list, description="Individual metric comparisons"
    )


# =============================================================================
# Profile Comparison Schemas
# =============================================================================


class ProfileComparisonRequest(BaseSchema):
    """Request to compare two profiles."""

    baseline_profile_id: str = Field(..., description="Baseline profile ID")
    current_profile_id: str = Field(..., description="Current profile ID")
    significance_threshold: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Threshold for significant change detection",
    )


class ProfileComparisonResponse(BaseSchema):
    """Response containing profile comparison results."""

    source_id: str = Field(..., description="Source ID")
    source_name: str = Field(..., description="Source name")
    baseline_profile_id: str = Field(..., description="Baseline profile ID")
    current_profile_id: str = Field(..., description="Current profile ID")
    baseline_timestamp: datetime = Field(..., description="Baseline profile timestamp")
    current_timestamp: datetime = Field(..., description="Current profile timestamp")
    row_count_change: int = Field(default=0, description="Change in row count")
    row_count_change_pct: float = Field(
        default=0.0, description="Percentage change in row count"
    )
    column_count_change: int = Field(default=0, description="Change in column count")
    column_comparisons: list[ColumnComparison] = Field(
        default_factory=list, description="Per-column metric comparisons"
    )
    significant_changes: int = Field(
        default=0, description="Number of significant changes"
    )
    summary: dict[str, Any] = Field(
        default_factory=dict, description="Summary statistics"
    )
    compared_at: datetime = Field(..., description="When comparison was performed")


# =============================================================================
# Profile Trend Schemas
# =============================================================================


class ProfileTrendPoint(BaseSchema):
    """A single point in profile trend data."""

    timestamp: datetime = Field(..., description="Profile timestamp")
    profile_id: str = Field(..., description="Profile ID")
    row_count: int = Field(..., description="Row count at this point")
    column_count: int = Field(default=0, description="Column count")
    avg_null_pct: float = Field(default=0.0, description="Average null percentage")
    avg_unique_pct: float = Field(default=0.0, description="Average unique percentage")
    size_bytes: int = Field(default=0, description="Data size in bytes")


class ColumnTrend(BaseSchema):
    """Trend data for a specific column metric."""

    column: str = Field(..., description="Column name")
    metric: str = Field(..., description="Metric name")
    values: list[tuple[datetime, float]] = Field(
        default_factory=list, description="Time-value pairs"
    )
    trend_direction: TrendDirection = Field(
        default=TrendDirection.STABLE, description="Overall trend direction"
    )
    change_pct: float = Field(
        default=0.0, description="Overall percentage change"
    )
    min_value: float | None = Field(default=None, description="Minimum value in period")
    max_value: float | None = Field(default=None, description="Maximum value in period")
    avg_value: float | None = Field(default=None, description="Average value in period")


class ProfileTrendRequest(BaseSchema):
    """Request for profile trend data."""

    period: str = Field(
        default="30d",
        description="Time period (e.g., 7d, 30d, 90d)",
    )
    granularity: str = Field(
        default="daily",
        description="Data granularity (hourly, daily, weekly)",
    )
    columns: list[str] | None = Field(
        default=None,
        description="Specific columns to include in trends",
    )
    metrics: list[str] | None = Field(
        default=None,
        description="Specific metrics to include (null_pct, unique_pct, etc.)",
    )


class ProfileTrendResponse(BaseSchema):
    """Response containing profile trend data."""

    source_id: str = Field(..., description="Source ID")
    source_name: str = Field(..., description="Source name")
    period: str = Field(..., description="Time period analyzed")
    granularity: str = Field(..., description="Data granularity")
    data_points: list[ProfileTrendPoint] = Field(
        default_factory=list, description="Overall trend points"
    )
    column_trends: list[ColumnTrend] = Field(
        default_factory=list, description="Per-column trends"
    )
    total_profiles: int = Field(default=0, description="Total profiles in period")
    row_count_trend: TrendDirection = Field(
        default=TrendDirection.STABLE, description="Overall row count trend"
    )
    summary: dict[str, Any] = Field(
        default_factory=dict, description="Summary statistics"
    )


# =============================================================================
# Latest Comparison Shortcut
# =============================================================================


class LatestComparisonResponse(BaseSchema):
    """Response for comparing latest profile with previous."""

    source_id: str = Field(..., description="Source ID")
    has_previous: bool = Field(
        ..., description="Whether a previous profile exists"
    )
    comparison: ProfileComparisonResponse | None = Field(
        default=None, description="Comparison result (if previous exists)"
    )
