"""Profile-related Pydantic schemas.

This module defines schemas for data profiling API operations.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import Field

from .base import BaseSchema


# =============================================================================
# Sampling Strategy Enums and Types
# =============================================================================


class SamplingStrategy(str, Enum):
    """Sampling strategies for data profiling.

    Supports 8+ strategies from truthound profiler:
    - NONE: Profile all data (for small datasets < 100K rows)
    - HEAD: First N rows (for quick previews)
    - RANDOM: Random sampling (general purpose)
    - SYSTEMATIC: Every Nth row (for ordered data)
    - STRATIFIED: Maintain distribution across categories
    - RESERVOIR: Streaming-friendly sampling
    - ADAPTIVE: Auto-select based on data characteristics (default)
    - HASH: Deterministic sampling for reproducibility
    """

    NONE = "none"
    HEAD = "head"
    RANDOM = "random"
    SYSTEMATIC = "systematic"
    STRATIFIED = "stratified"
    RESERVOIR = "reservoir"
    ADAPTIVE = "adaptive"
    HASH = "hash"


# Literal type for API validation
SamplingStrategyType = Literal[
    "none", "head", "random", "systematic", "stratified", "reservoir", "adaptive", "hash"
]


class SamplingConfig(BaseSchema):
    """Advanced sampling configuration for profiling.

    Provides fine-grained control over sampling behavior for large datasets.
    """

    strategy: SamplingStrategyType = Field(
        default="adaptive",
        description="Sampling strategy to use. 'adaptive' auto-selects based on data size.",
    )
    sample_size: int | None = Field(
        default=None,
        ge=100,
        description="Target sample size. If None, auto-estimated based on confidence level.",
    )
    confidence_level: float = Field(
        default=0.95,
        ge=0.80,
        le=0.99,
        description="Statistical confidence level for sample size estimation (0.80-0.99).",
    )
    margin_of_error: float = Field(
        default=0.03,
        ge=0.01,
        le=0.10,
        description="Acceptable margin of error for statistical estimates (0.01-0.10).",
    )
    strata_column: str | None = Field(
        default=None,
        description="Column for stratified sampling to maintain distribution.",
    )
    seed: int | None = Field(
        default=None,
        description="Random seed for reproducible sampling results.",
    )


# =============================================================================
# Pattern Detection Configuration
# =============================================================================


class PatternType(str, Enum):
    """Supported data pattern types for detection."""

    EMAIL = "email"
    PHONE = "phone"
    UUID = "uuid"
    URL = "url"
    IP_ADDRESS = "ip_address"
    CREDIT_CARD = "credit_card"
    DATE = "date"
    DATETIME = "datetime"
    KOREAN_RRN = "korean_rrn"
    KOREAN_PHONE = "korean_phone"
    SSN = "ssn"
    POSTAL_CODE = "postal_code"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    CUSTOM = "custom"


class PatternDetectionConfig(BaseSchema):
    """Configuration for pattern detection during profiling.

    Enables automatic detection of common data patterns like
    emails, phone numbers, UUIDs, etc.
    """

    enabled: bool = Field(
        default=True,
        description="Enable pattern detection during profiling.",
    )
    sample_size: int = Field(
        default=1000,
        ge=100,
        le=100000,
        description="Number of values to sample for pattern detection.",
    )
    min_confidence: float = Field(
        default=0.8,
        ge=0.5,
        le=1.0,
        description="Minimum confidence threshold for pattern matches (0.5-1.0).",
    )
    patterns_to_detect: list[str] | None = Field(
        default=None,
        description="Specific patterns to detect. If None, detects all supported patterns.",
    )


# =============================================================================
# Profile Request Schema (Enhanced)
# =============================================================================


class ProfileRequest(BaseSchema):
    """Request schema for data profiling.

    Provides comprehensive configuration for profiling operations including
    sampling strategies, pattern detection, and statistical analysis options.
    """

    # Basic sampling (backward compatible)
    sample_size: int | None = Field(
        default=None,
        ge=1,
        description="Maximum number of rows to sample for profiling. "
        "If None, profiles all data. For advanced sampling, use 'sampling' config.",
        examples=[10000, 50000, 100000],
    )

    # Advanced sampling configuration
    sampling: SamplingConfig | None = Field(
        default=None,
        description="Advanced sampling configuration. If provided, overrides sample_size.",
    )

    # Pattern detection configuration
    pattern_detection: PatternDetectionConfig | None = Field(
        default=None,
        description="Pattern detection configuration. If None, uses default settings.",
    )

    # Additional profiling options
    include_histograms: bool = Field(
        default=True,
        description="Include value distribution histograms in the profile.",
    )
    include_correlations: bool = Field(
        default=False,
        description="Include column correlation analysis (increases processing time).",
    )
    include_cardinality: bool = Field(
        default=True,
        description="Include cardinality estimates for high-cardinality columns.",
    )


# =============================================================================
# Pattern Detection Results
# =============================================================================


class DetectedPattern(BaseSchema):
    """A detected data pattern in a column."""

    pattern_type: str = Field(
        ...,
        description="Type of pattern detected (email, phone, uuid, etc.)",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score of the pattern match (0-1).",
    )
    match_count: int = Field(
        ...,
        ge=0,
        description="Number of values matching this pattern.",
    )
    match_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of non-null values matching this pattern.",
    )
    sample_matches: list[str] | None = Field(
        default=None,
        description="Sample values matching this pattern (masked for sensitive data).",
    )


class HistogramBucket(BaseSchema):
    """A bucket in a value distribution histogram."""

    bucket: str = Field(..., description="Bucket label (range or category)")
    count: int = Field(..., ge=0, description="Count of values in this bucket")
    percentage: float = Field(..., ge=0.0, le=100.0, description="Percentage of total")


# =============================================================================
# Column Profile Schema (Enhanced)
# =============================================================================


class ColumnProfile(BaseSchema):
    """Profile information for a single column.

    Includes basic statistics, pattern detection results, and distribution data.
    """

    # Basic identification
    name: str = Field(..., description="Column name")
    dtype: str = Field(..., description="Physical data type (string, int64, float64, etc.)")

    # Inferred semantic type (NEW)
    inferred_type: str | None = Field(
        default=None,
        description="Inferred semantic type based on pattern detection "
        "(email, phone, uuid, url, date, currency, etc.)",
    )

    # Completeness metrics
    null_pct: str = Field(default="0%", description="Percentage of null values")
    null_count: int | None = Field(default=None, description="Count of null values")

    # Uniqueness metrics
    unique_pct: str = Field(default="0%", description="Percentage of unique values")
    distinct_count: int | None = Field(
        default=None,
        description="Count of distinct values",
    )
    is_unique: bool | None = Field(
        default=None,
        description="Whether all non-null values are unique",
    )

    # Value range (for numeric/date columns)
    min: Any | None = Field(default=None, description="Minimum value")
    max: Any | None = Field(default=None, description="Maximum value")

    # Statistical measures (for numeric columns)
    mean: float | None = Field(default=None, description="Mean value (numeric columns)")
    std: float | None = Field(default=None, description="Standard deviation (numeric)")
    median: float | None = Field(default=None, description="Median value (numeric)")
    q1: float | None = Field(default=None, description="25th percentile (Q1)")
    q3: float | None = Field(default=None, description="75th percentile (Q3)")
    skewness: float | None = Field(default=None, description="Skewness of distribution")
    kurtosis: float | None = Field(default=None, description="Kurtosis of distribution")

    # String-specific metrics
    min_length: int | None = Field(default=None, description="Minimum string length")
    max_length: int | None = Field(default=None, description="Maximum string length")
    avg_length: float | None = Field(default=None, description="Average string length")

    # Pattern detection results (NEW)
    patterns: list[DetectedPattern] | None = Field(
        default=None,
        description="Detected data patterns (email, phone, uuid, etc.)",
    )
    primary_pattern: str | None = Field(
        default=None,
        description="The most prevalent detected pattern type",
    )

    # Distribution data
    most_common: list[dict[str, Any]] | None = Field(
        default=None,
        description="Most common values with counts",
    )
    histogram: list[HistogramBucket] | None = Field(
        default=None,
        description="Value distribution histogram",
    )

    # Cardinality estimate for high-cardinality columns
    cardinality_estimate: int | None = Field(
        default=None,
        description="Estimated cardinality using HyperLogLog (for high-cardinality columns)",
    )


# =============================================================================
# Sampling Metadata for Response
# =============================================================================


class SamplingMetadata(BaseSchema):
    """Metadata about sampling used during profiling."""

    strategy_used: str = Field(..., description="Sampling strategy that was applied")
    sample_size: int = Field(..., description="Actual sample size used")
    total_rows: int = Field(..., description="Total rows in the dataset")
    sampling_ratio: float = Field(..., description="Ratio of sampled to total rows")
    seed: int | None = Field(default=None, description="Random seed used (if applicable)")
    confidence_level: float | None = Field(
        default=None, description="Confidence level achieved"
    )
    margin_of_error: float | None = Field(
        default=None, description="Estimated margin of error"
    )


# =============================================================================
# Profile Response Schema (Enhanced)
# =============================================================================


class ProfileResponse(BaseSchema):
    """Data profiling response with enhanced statistics and pattern detection."""

    source: str = Field(..., description="Source path/identifier")
    row_count: int = Field(..., ge=0, description="Total number of rows")
    column_count: int = Field(..., ge=0, description="Total number of columns")
    size_bytes: int = Field(..., ge=0, description="Data size in bytes")
    columns: list[ColumnProfile] = Field(
        default_factory=list,
        description="Profile for each column",
    )

    # Sampling metadata (NEW)
    sampling: SamplingMetadata | None = Field(
        default=None,
        description="Information about sampling applied during profiling",
    )

    # Pattern detection summary (NEW)
    detected_patterns_summary: dict[str, int] | None = Field(
        default=None,
        description="Summary of detected patterns across all columns {pattern_type: count}",
    )

    # Profiling metadata (NEW)
    profiled_at: str | None = Field(
        default=None,
        description="ISO timestamp when profiling was performed",
    )
    profiling_duration_ms: int | None = Field(
        default=None,
        description="Time taken to profile in milliseconds",
    )

    # Computed properties
    @property
    def size_human(self) -> str:
        """Get human-readable size."""
        size = self.size_bytes
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    @classmethod
    def _build_column_profile(cls, col: dict[str, Any]) -> ColumnProfile:
        """Build a ColumnProfile from column data dict.

        Args:
            col: Column data dictionary from adapter or database.

        Returns:
            ColumnProfile instance with all available fields.
        """
        # Build patterns list if present
        patterns = None
        if col.get("patterns"):
            patterns = [
                DetectedPattern(
                    pattern_type=p.get("pattern_type", p.get("type", "unknown")),
                    confidence=p.get("confidence", 0.0),
                    match_count=p.get("match_count", 0),
                    match_percentage=p.get("match_percentage", 0.0),
                    sample_matches=p.get("sample_matches"),
                )
                for p in col["patterns"]
            ]

        # Build histogram if present
        histogram = None
        if col.get("histogram"):
            histogram = [
                HistogramBucket(
                    bucket=h.get("bucket", ""),
                    count=h.get("count", 0),
                    percentage=h.get("percentage", 0.0),
                )
                for h in col["histogram"]
            ]

        return ColumnProfile(
            name=col["name"],
            dtype=col["dtype"],
            inferred_type=col.get("inferred_type"),
            null_pct=col.get("null_pct", "0%"),
            null_count=col.get("null_count"),
            unique_pct=col.get("unique_pct", "0%"),
            distinct_count=col.get("distinct_count"),
            is_unique=col.get("is_unique"),
            min=col.get("min"),
            max=col.get("max"),
            mean=col.get("mean"),
            std=col.get("std"),
            median=col.get("median"),
            q1=col.get("q1"),
            q3=col.get("q3"),
            skewness=col.get("skewness"),
            kurtosis=col.get("kurtosis"),
            min_length=col.get("min_length"),
            max_length=col.get("max_length"),
            avg_length=col.get("avg_length"),
            patterns=patterns,
            primary_pattern=col.get("primary_pattern"),
            most_common=col.get("most_common"),
            histogram=histogram,
            cardinality_estimate=col.get("cardinality_estimate"),
        )

    @classmethod
    def from_result(cls, result: Any) -> ProfileResponse:
        """Create response from adapter result or Profile model.

        Args:
            result: ProfileResult from adapter or Profile model.

        Returns:
            ProfileResponse instance.
        """
        # Handle Profile model (from database)
        if hasattr(result, "profile_json"):
            profile_json = result.profile_json
            source_name = profile_json.get("source", result.source_id)
            columns_data = profile_json.get("columns", [])
            columns = [cls._build_column_profile(col) for col in columns_data]

            # Build sampling metadata if present
            sampling = None
            if profile_json.get("sampling"):
                s = profile_json["sampling"]
                sampling = SamplingMetadata(
                    strategy_used=s.get("strategy_used", "none"),
                    sample_size=s.get("sample_size", result.row_count or 0),
                    total_rows=s.get("total_rows", result.row_count or 0),
                    sampling_ratio=s.get("sampling_ratio", 1.0),
                    seed=s.get("seed"),
                    confidence_level=s.get("confidence_level"),
                    margin_of_error=s.get("margin_of_error"),
                )

            return cls(
                source=source_name,
                row_count=result.row_count or 0,
                column_count=result.column_count or 0,
                size_bytes=result.size_bytes or 0,
                columns=columns,
                sampling=sampling,
                detected_patterns_summary=profile_json.get("detected_patterns_summary"),
                profiled_at=profile_json.get("profiled_at"),
                profiling_duration_ms=profile_json.get("profiling_duration_ms"),
            )

        # Handle ProfileResult (from adapter)
        columns = [cls._build_column_profile(col) for col in result.columns]

        # Build sampling metadata if present
        sampling = None
        if hasattr(result, "sampling") and result.sampling:
            s = result.sampling
            sampling = SamplingMetadata(
                strategy_used=getattr(s, "strategy_used", "none"),
                sample_size=getattr(s, "sample_size", result.row_count),
                total_rows=getattr(s, "total_rows", result.row_count),
                sampling_ratio=getattr(s, "sampling_ratio", 1.0),
                seed=getattr(s, "seed", None),
                confidence_level=getattr(s, "confidence_level", None),
                margin_of_error=getattr(s, "margin_of_error", None),
            )

        return cls(
            source=result.source,
            row_count=result.row_count,
            column_count=result.column_count,
            size_bytes=result.size_bytes,
            columns=columns,
            sampling=sampling,
            detected_patterns_summary=getattr(result, "detected_patterns_summary", None),
            profiled_at=getattr(result, "profiled_at", None),
            profiling_duration_ms=getattr(result, "profiling_duration_ms", None),
        )
