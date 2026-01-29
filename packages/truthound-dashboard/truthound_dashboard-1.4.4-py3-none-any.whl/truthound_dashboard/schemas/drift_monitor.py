"""Drift monitoring schemas.

This module defines schemas for automatic drift monitoring operations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from .base import BaseSchema, IDMixin, ListResponseWrapper, TimestampMixin

# Drift monitoring status
DriftMonitorStatus = Literal["active", "paused", "error"]

# Drift alert severity levels
DriftAlertSeverity = Literal["critical", "high", "medium", "low", "info"]

# Alert status
AlertStatus = Literal["open", "acknowledged", "resolved", "ignored"]


class DriftMonitorBase(BaseSchema):
    """Base drift monitor schema."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Monitor name",
        examples=["Daily Sales Drift Check"],
    )
    baseline_source_id: str = Field(
        ...,
        description="Baseline data source ID",
    )
    current_source_id: str = Field(
        ...,
        description="Current data source ID to compare",
    )
    cron_expression: str = Field(
        default="0 0 * * *",
        description="Cron expression for monitoring schedule",
        examples=["0 0 * * *", "0 */6 * * *"],
    )
    method: str = Field(
        default="auto",
        description="Drift detection method",
        examples=["auto", "ks", "psi", "chi2"],
    )
    threshold: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Drift threshold",
    )
    columns: list[str] | None = Field(
        default=None,
        description="Specific columns to monitor (null for all)",
    )
    alert_on_drift: bool = Field(
        default=True,
        description="Whether to create alerts when drift is detected",
    )
    alert_threshold_critical: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Drift percentage threshold for critical alerts",
    )
    alert_threshold_high: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Drift percentage threshold for high alerts",
    )
    notification_channel_ids: list[str] | None = Field(
        default=None,
        description="Notification channel IDs for alerts",
    )


class DriftMonitorCreate(DriftMonitorBase):
    """Schema for creating a drift monitor."""

    pass


class DriftMonitorUpdate(BaseSchema):
    """Schema for updating a drift monitor."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    cron_expression: str | None = Field(default=None)
    method: str | None = Field(default=None)
    threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    columns: list[str] | None = Field(default=None)
    alert_on_drift: bool | None = Field(default=None)
    alert_threshold_critical: float | None = Field(default=None, ge=0.0, le=1.0)
    alert_threshold_high: float | None = Field(default=None, ge=0.0, le=1.0)
    notification_channel_ids: list[str] | None = Field(default=None)
    status: DriftMonitorStatus | None = Field(default=None)


class DriftMonitorResponse(DriftMonitorBase, IDMixin, TimestampMixin):
    """Schema for drift monitor response."""

    status: DriftMonitorStatus = Field(
        default="active",
        description="Monitor status",
    )
    last_run_at: datetime | None = Field(
        default=None,
        description="Last monitoring run timestamp",
    )
    last_drift_detected: bool | None = Field(
        default=None,
        description="Whether drift was detected in last run",
    )
    total_runs: int = Field(
        default=0,
        description="Total number of monitoring runs",
    )
    drift_detected_count: int = Field(
        default=0,
        description="Number of runs with drift detected",
    )
    consecutive_drift_count: int = Field(
        default=0,
        description="Number of consecutive runs with drift",
    )


class DriftMonitorListResponse(ListResponseWrapper):
    """List response for drift monitors."""

    data: list[DriftMonitorResponse]


# Drift Alert Schemas


class DriftAlertBase(BaseSchema):
    """Base drift alert schema."""

    monitor_id: str = Field(
        ...,
        description="Associated drift monitor ID",
    )
    comparison_id: str = Field(
        ...,
        description="Drift comparison ID that triggered the alert",
    )
    severity: DriftAlertSeverity = Field(
        ...,
        description="Alert severity level",
    )
    drift_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Drift percentage that triggered the alert",
    )
    drifted_columns: list[str] = Field(
        default_factory=list,
        description="List of columns with drift",
    )
    message: str = Field(
        ...,
        description="Alert message",
    )


class DriftAlertResponse(DriftAlertBase, IDMixin, TimestampMixin):
    """Schema for drift alert response."""

    status: AlertStatus = Field(
        default="open",
        description="Alert status",
    )
    acknowledged_at: datetime | None = Field(
        default=None,
        description="When the alert was acknowledged",
    )
    acknowledged_by: str | None = Field(
        default=None,
        description="User who acknowledged the alert",
    )
    resolved_at: datetime | None = Field(
        default=None,
        description="When the alert was resolved",
    )
    notes: str | None = Field(
        default=None,
        description="Notes about the alert",
    )


class DriftAlertListResponse(ListResponseWrapper):
    """List response for drift alerts."""

    data: list[DriftAlertResponse]


class DriftAlertUpdate(BaseSchema):
    """Schema for updating a drift alert."""

    status: AlertStatus | None = Field(default=None)
    notes: str | None = Field(default=None, max_length=2000)


# Drift Trend Schemas


class DriftTrendPoint(BaseSchema):
    """Single point in drift trend data."""

    timestamp: datetime
    drift_percentage: float
    drifted_columns: int
    total_columns: int
    has_drift: bool


class DriftTrendResponse(BaseSchema):
    """Drift trend over time."""

    monitor_id: str
    period_start: datetime
    period_end: datetime
    data_points: list[DriftTrendPoint]
    avg_drift_percentage: float
    max_drift_percentage: float
    drift_occurrence_rate: float


# Monitor Summary Schemas


class DriftMonitorSummary(BaseSchema):
    """Summary of all drift monitors."""

    total_monitors: int
    active_monitors: int
    paused_monitors: int
    monitors_with_drift: int
    total_open_alerts: int
    critical_alerts: int
    high_alerts: int


# Root Cause Analysis Types
RootCauseType = Literal[
    "mean_shift",
    "variance_change",
    "new_categories",
    "missing_categories",
    "outlier_introduction",
    "data_volume_change",
    "temporal_pattern",
    "distribution_shape_change",
    "null_rate_change",
]

RemediationActionType = Literal[
    "investigate_upstream",
    "update_baseline",
    "adjust_threshold",
    "review_data_pipeline",
    "check_data_source",
    "normalize_values",
    "filter_outliers",
    "retrain_model",
    "acknowledge_expected_change",
]


# Root Cause Analysis Schemas


class StatisticalShift(BaseSchema):
    """Statistical shift details for a column."""

    baseline_value: float = Field(..., description="Value in baseline dataset")
    current_value: float = Field(..., description="Value in current dataset")
    absolute_change: float = Field(..., description="Absolute change")
    percent_change: float = Field(..., description="Percentage change")


class CategoryChange(BaseSchema):
    """Category change details for categorical columns."""

    category: str = Field(..., description="Category name")
    baseline_count: int = Field(default=0, description="Count in baseline")
    current_count: int = Field(default=0, description="Count in current")
    baseline_percentage: float = Field(default=0, description="Percentage in baseline")
    current_percentage: float = Field(default=0, description="Percentage in current")


class OutlierInfo(BaseSchema):
    """Information about detected outliers."""

    count: int = Field(..., description="Number of outliers")
    percentage: float = Field(..., description="Percentage of total")
    sample_values: list[float | str] = Field(
        default_factory=list, description="Sample outlier values"
    )
    threshold_method: str = Field(default="iqr", description="Method used to detect outliers")


class TemporalPattern(BaseSchema):
    """Temporal pattern information."""

    pattern_type: str = Field(
        ...,
        description="Type of temporal pattern",
        examples=["weekly_seasonality", "monthly_trend", "recent_spike"],
    )
    affected_period: str = Field(
        ..., description="Period affected by the pattern"
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence in pattern detection"
    )


class ColumnRootCause(BaseSchema):
    """Root cause analysis for a single column."""

    column: str = Field(..., description="Column name")
    dtype: str = Field(..., description="Column data type")
    drift_level: str = Field(
        ...,
        description="Drift severity level",
        examples=["none", "low", "medium", "high"],
    )
    causes: list[RootCauseType] = Field(
        default_factory=list, description="Detected root causes"
    )
    primary_cause: RootCauseType | None = Field(
        default=None, description="Primary root cause"
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence score for analysis"
    )

    # Statistical shifts
    mean_shift: StatisticalShift | None = Field(
        default=None, description="Mean shift details"
    )
    std_shift: StatisticalShift | None = Field(
        default=None, description="Standard deviation shift details"
    )
    min_shift: StatisticalShift | None = Field(
        default=None, description="Min value shift details"
    )
    max_shift: StatisticalShift | None = Field(
        default=None, description="Max value shift details"
    )

    # Categorical changes
    new_categories: list[CategoryChange] = Field(
        default_factory=list, description="New categories in current"
    )
    missing_categories: list[CategoryChange] = Field(
        default_factory=list, description="Missing categories from baseline"
    )
    category_distribution_changes: list[CategoryChange] = Field(
        default_factory=list, description="Significant distribution changes"
    )

    # Outliers
    outlier_info: OutlierInfo | None = Field(
        default=None, description="Outlier information"
    )

    # Temporal
    temporal_patterns: list[TemporalPattern] = Field(
        default_factory=list, description="Detected temporal patterns"
    )

    # Null rate
    null_rate_baseline: float | None = Field(
        default=None, description="Null rate in baseline"
    )
    null_rate_current: float | None = Field(
        default=None, description="Null rate in current"
    )


class RemediationSuggestion(BaseSchema):
    """Suggested remediation action."""

    action: RemediationActionType = Field(..., description="Recommended action type")
    priority: int = Field(
        default=1, ge=1, le=5, description="Priority (1=highest, 5=lowest)"
    )
    title: str = Field(..., description="Short title for the action")
    description: str = Field(..., description="Detailed description of the action")
    affected_columns: list[str] = Field(
        default_factory=list, description="Columns this action applies to"
    )
    estimated_impact: str = Field(
        default="medium",
        description="Expected impact of taking this action",
        examples=["high", "medium", "low"],
    )
    requires_manual_review: bool = Field(
        default=True, description="Whether manual review is needed"
    )
    automation_available: bool = Field(
        default=False, description="Whether this action can be automated"
    )


class DataVolumeChange(BaseSchema):
    """Data volume change summary."""

    baseline_rows: int = Field(..., description="Number of rows in baseline")
    current_rows: int = Field(..., description="Number of rows in current")
    absolute_change: int = Field(..., description="Absolute row count change")
    percent_change: float = Field(..., description="Percentage change in rows")
    significance: str = Field(
        default="normal",
        description="Significance of volume change",
        examples=["normal", "notable", "significant", "critical"],
    )


class RootCauseAnalysis(BaseSchema):
    """Complete root cause analysis for a drift run."""

    run_id: str = Field(..., description="Drift comparison/run ID")
    monitor_id: str | None = Field(
        default=None, description="Associated monitor ID if applicable"
    )
    analyzed_at: datetime = Field(..., description="When analysis was performed")

    # Summary
    total_columns: int = Field(..., description="Total columns analyzed")
    drifted_columns: int = Field(..., description="Number of drifted columns")
    drift_percentage: float = Field(
        ..., ge=0.0, le=100.0, description="Percentage of columns with drift"
    )

    # Volume change
    data_volume_change: DataVolumeChange | None = Field(
        default=None, description="Data volume change summary"
    )

    # Per-column analysis
    column_analyses: list[ColumnRootCause] = Field(
        default_factory=list, description="Root cause analysis per column"
    )

    # Aggregated causes
    primary_causes: list[RootCauseType] = Field(
        default_factory=list, description="Primary causes across all columns"
    )
    cause_distribution: dict[str, int] = Field(
        default_factory=dict, description="Count of each cause type"
    )

    # Remediation suggestions
    remediations: list[RemediationSuggestion] = Field(
        default_factory=list, description="Suggested remediation actions"
    )

    # Confidence and metadata
    overall_confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Overall confidence in analysis"
    )
    analysis_duration_ms: int = Field(
        default=0, description="Analysis duration in milliseconds"
    )


class RootCauseAnalysisResponse(BaseSchema):
    """Response wrapper for root cause analysis."""

    success: bool = Field(default=True)
    data: RootCauseAnalysis


# Drift Preview Schemas


class DriftPreviewRequest(BaseSchema):
    """Request body for drift preview."""

    baseline_source_id: str = Field(
        ...,
        description="Baseline data source ID",
    )
    current_source_id: str = Field(
        ...,
        description="Current data source ID to compare",
    )
    columns: list[str] | None = Field(
        default=None,
        description="Specific columns to compare (null for all)",
    )
    method: str = Field(
        default="auto",
        description="Drift detection method",
        examples=["auto", "ks", "psi", "chi2", "js", "kl", "wasserstein", "cvm", "anderson"],
    )
    threshold: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Custom drift threshold",
    )


class ColumnDistributionData(BaseSchema):
    """Distribution data for a column."""

    values: list[float] = Field(
        default_factory=list,
        description="Binned values for histogram",
    )
    bins: list[str] = Field(
        default_factory=list,
        description="Bin labels or category names",
    )
    counts: list[int] = Field(
        default_factory=list,
        description="Count per bin",
    )
    percentages: list[float] = Field(
        default_factory=list,
        description="Percentage per bin",
    )


class ColumnPreviewResult(BaseSchema):
    """Drift preview result for a single column."""

    column: str = Field(..., description="Column name")
    dtype: str = Field(..., description="Data type")
    drifted: bool = Field(..., description="Whether drift was detected")
    level: str = Field(
        default="none",
        description="Drift level (high, medium, low, none)",
    )
    method: str = Field(..., description="Detection method used")
    statistic: float | None = Field(None, description="Test statistic value")
    p_value: float | None = Field(None, description="P-value")

    # Statistics
    baseline_stats: dict = Field(
        default_factory=dict,
        description="Baseline statistics (mean, std, min, max, etc.)",
    )
    current_stats: dict = Field(
        default_factory=dict,
        description="Current statistics (mean, std, min, max, etc.)",
    )

    # Distribution data for charts
    baseline_distribution: ColumnDistributionData | None = Field(
        default=None,
        description="Baseline distribution data for visualization",
    )
    current_distribution: ColumnDistributionData | None = Field(
        default=None,
        description="Current distribution data for visualization",
    )


class DriftPreviewData(BaseSchema):
    """Drift preview result data."""

    baseline_source_id: str = Field(..., description="Baseline source ID")
    current_source_id: str = Field(..., description="Current source ID")
    baseline_source_name: str | None = Field(None, description="Baseline source name")
    current_source_name: str | None = Field(None, description="Current source name")

    # Summary metrics
    has_drift: bool = Field(..., description="Whether any drift was detected")
    has_high_drift: bool = Field(
        default=False,
        description="Whether high-severity drift was detected",
    )
    total_columns: int = Field(..., description="Total columns compared")
    drifted_columns: int = Field(
        default=0,
        description="Number of columns with drift",
    )
    drift_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Percentage of columns with drift",
    )

    # Row counts
    baseline_rows: int = Field(default=0, description="Number of baseline rows")
    current_rows: int = Field(default=0, description="Number of current rows")

    # Configuration used
    method: str = Field(default="auto", description="Detection method used")
    threshold: float = Field(default=0.05, description="Threshold used")

    # Per-column results
    columns: list[ColumnPreviewResult] = Field(
        default_factory=list,
        description="Per-column drift results",
    )

    # Most affected columns (sorted by drift severity)
    most_affected: list[str] = Field(
        default_factory=list,
        description="List of most affected columns (sorted by severity)",
    )


class DriftPreviewResponse(BaseSchema):
    """Response for drift preview."""

    success: bool = Field(default=True)
    data: DriftPreviewData


# Large-Scale Dataset Optimization Schemas


# Sampling method types
SamplingMethodType = Literal["random", "stratified", "reservoir", "systematic"]


class SamplingConfig(BaseSchema):
    """Configuration for sampled drift comparison."""

    method: SamplingMethodType = Field(
        default="random",
        description="Sampling method to use",
    )
    sample_size: int | None = Field(
        default=None,
        ge=100,
        description="Sample size (auto-estimated if null)",
    )
    confidence_level: float = Field(
        default=0.95,
        ge=0.80,
        le=0.99,
        description="Target confidence level for sample size estimation",
    )
    margin_of_error: float = Field(
        default=0.03,
        ge=0.01,
        le=0.10,
        description="Acceptable margin of error",
    )
    strata_column: str | None = Field(
        default=None,
        description="Column for stratified sampling",
    )
    seed: int | None = Field(
        default=None,
        description="Random seed for reproducibility",
    )
    early_stop_threshold: float = Field(
        default=0.5,
        ge=0.1,
        le=1.0,
        description="Proportion of drifted columns to trigger early stopping",
    )
    max_workers: int = Field(
        default=4,
        ge=1,
        le=16,
        description="Maximum parallel workers for column comparison",
    )


class SampledComparisonRequest(BaseSchema):
    """Request for sampled drift comparison."""

    monitor_id: str = Field(..., description="Monitor ID to run with sampling")
    sampling: SamplingConfig = Field(
        default_factory=SamplingConfig,
        description="Sampling configuration",
    )


class SampleSizeEstimate(BaseSchema):
    """Estimated sample size for drift detection."""

    recommended_size: int = Field(
        ..., description="Recommended sample size for target confidence"
    )
    min_size: int = Field(
        ..., description="Minimum sample size for basic detection"
    )
    max_size: int = Field(
        ..., description="Maximum useful sample size (diminishing returns beyond)"
    )
    confidence_level: float = Field(
        ..., description="Target confidence level"
    )
    margin_of_error: float = Field(
        ..., description="Expected margin of error at recommended size"
    )
    estimated_time_seconds: float = Field(
        ..., description="Estimated processing time in seconds"
    )
    memory_mb: float = Field(
        ..., description="Estimated memory usage in MB"
    )


class SpeedupOption(BaseSchema):
    """Speedup option for different sample sizes."""

    sample_size: int = Field(..., description="Sample size for this option")
    speedup_factor: float = Field(..., description="Expected speedup factor")
    estimated_time_seconds: float = Field(..., description="Estimated time in seconds")


class DatasetInfo(BaseSchema):
    """Information about dataset sizes."""

    baseline_rows: int = Field(..., description="Number of rows in baseline")
    current_rows: int = Field(..., description="Number of rows in current")
    population_size: int = Field(..., description="Larger of baseline/current rows")
    is_large_dataset: bool = Field(..., description="Whether dataset exceeds threshold")
    large_dataset_threshold: int = Field(..., description="Row count threshold")


class SamplingRecommendation(BaseSchema):
    """Sampling recommendation for a dataset."""

    sampling_recommended: bool = Field(..., description="Whether sampling is recommended")
    reason: str = Field(..., description="Reason for recommendation")


class SamplingMethod(BaseSchema):
    """Description of a sampling method."""

    method: str = Field(..., description="Method identifier")
    description: str = Field(..., description="Method description")
    best_for: str = Field(..., description="Ideal use case")


class SampleSizeEstimateResponse(BaseSchema):
    """Response for sample size estimation."""

    baseline_source_id: str
    current_source_id: str
    dataset_info: DatasetInfo
    sampling_recommendation: SamplingRecommendation
    sample_size_estimate: SampleSizeEstimate
    performance_estimates: dict = Field(
        ..., description="Performance estimates with speedup options"
    )
    available_methods: list[SamplingMethod]


class ChunkedComparisonProgress(BaseSchema):
    """Progress tracking for chunked comparison operations."""

    total_chunks: int = Field(..., description="Total number of chunks to process")
    processed_chunks: int = Field(..., description="Number of chunks processed")
    total_rows: int = Field(..., description="Total rows to process")
    processed_rows: int = Field(..., description="Rows processed so far")
    current_chunk: int = Field(..., description="Current chunk being processed")
    percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Completion percentage",
    )


class ChunkedComparisonTiming(BaseSchema):
    """Timing information for chunked comparison."""

    elapsed_seconds: float = Field(..., description="Time elapsed since start")
    estimated_remaining_seconds: float = Field(..., description="Estimated time remaining")


class ChunkedComparisonInterimResults(BaseSchema):
    """Interim results for chunked comparison."""

    columns_with_drift: list[str] = Field(
        default_factory=list,
        description="Columns detected with drift so far",
    )
    early_stop_triggered: bool = Field(
        default=False,
        description="Whether early stopping was triggered",
    )


class JobProgressResponse(BaseSchema):
    """Response for job progress query."""

    job_id: str = Field(..., description="Job identifier")
    status: str = Field(
        ...,
        description="Job status (running, completed, cancelled, error)",
    )
    progress: ChunkedComparisonProgress
    timing: ChunkedComparisonTiming
    interim_results: ChunkedComparisonInterimResults


class SamplingInfo(BaseSchema):
    """Sampling information for comparison result."""

    method: str = Field(..., description="Sampling method used")
    sample_size: int = Field(..., description="Sample size used")
    confidence_level: float = Field(..., description="Confidence level")
    population_baseline: int = Field(..., description="Baseline population size")
    population_current: int = Field(..., description="Current population size")


class ProcessingInfo(BaseSchema):
    """Processing information for comparison result."""

    num_chunks: int = Field(..., description="Number of chunks processed")
    total_chunks_planned: int = Field(..., description="Total chunks planned")
    early_stopped: bool = Field(..., description="Whether early stopped")
    parallel_workers: int = Field(..., description="Number of parallel workers")


class ComparisonResults(BaseSchema):
    """Results of sampled comparison."""

    has_drift: bool = Field(..., description="Whether drift was detected")
    total_columns: int = Field(..., description="Total columns compared")
    drifted_columns: int = Field(..., description="Number of drifted columns")
    drifted_column_names: list[str] = Field(
        default_factory=list,
        description="Names of drifted columns",
    )
    drift_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Percentage of columns with drift",
    )


class PerformanceMetrics(BaseSchema):
    """Performance metrics for comparison."""

    total_time_seconds: float = Field(..., description="Total processing time")
    estimated_time_seconds: float = Field(..., description="Originally estimated time")
    estimated_memory_mb: float = Field(..., description="Estimated memory usage")
    speedup_factor: float = Field(..., description="Speedup vs full dataset")


class ChunkDetail(BaseSchema):
    """Details for a single processed chunk."""

    chunk_index: int = Field(..., description="Chunk index")
    rows_processed: int = Field(..., description="Rows in this chunk")
    drifted_columns: list[str] = Field(
        default_factory=list,
        description="Columns with drift in this chunk",
    )
    processing_time_seconds: float = Field(..., description="Time to process chunk")


class SampledComparisonResult(BaseSchema):
    """Complete result of sampled comparison."""

    job_id: str = Field(..., description="Job identifier")
    monitor_id: str = Field(..., description="Monitor identifier")
    status: str = Field(..., description="Completion status")
    sampling: SamplingInfo
    processing: ProcessingInfo
    results: ComparisonResults
    performance: PerformanceMetrics
    chunk_details: list[ChunkDetail] = Field(
        default_factory=list,
        description="Details for each processed chunk",
    )


class SampledComparisonResponse(BaseSchema):
    """Response for sampled comparison."""

    success: bool = Field(default=True)
    data: SampledComparisonResult
