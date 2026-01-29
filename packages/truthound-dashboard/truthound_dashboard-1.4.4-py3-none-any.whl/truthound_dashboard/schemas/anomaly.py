"""Anomaly detection Pydantic schemas.

This module defines schemas for ML-based anomaly detection API operations.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import Field

from .base import BaseSchema, IDMixin, ListResponseWrapper


# =============================================================================
# Enums and Types
# =============================================================================


class AnomalyAlgorithm(str, Enum):
    """Supported anomaly detection algorithms."""

    ISOLATION_FOREST = "isolation_forest"
    LOF = "lof"
    ONE_CLASS_SVM = "one_class_svm"
    DBSCAN = "dbscan"
    STATISTICAL = "statistical"
    AUTOENCODER = "autoencoder"


class AnomalyStatus(str, Enum):
    """Status of an anomaly detection run."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


# Algorithm categories for UI grouping
AlgorithmCategory = Literal["tree", "density", "svm", "clustering", "statistical", "neural"]


# =============================================================================
# Algorithm Configuration Schemas
# =============================================================================


class IsolationForestConfig(BaseSchema):
    """Configuration for Isolation Forest algorithm."""

    n_estimators: int = Field(
        default=100,
        ge=10,
        le=500,
        description="Number of isolation trees",
    )
    contamination: float = Field(
        default=0.1,
        ge=0.01,
        le=0.5,
        description="Expected proportion of anomalies in the dataset",
    )
    max_samples: int | str = Field(
        default="auto",
        description="Number of samples to draw (int or 'auto')",
    )
    random_state: int | None = Field(
        default=42,
        description="Random seed for reproducibility",
    )


class LOFConfig(BaseSchema):
    """Configuration for Local Outlier Factor algorithm."""

    n_neighbors: int = Field(
        default=20,
        ge=5,
        le=100,
        description="Number of neighbors for LOF computation",
    )
    contamination: float = Field(
        default=0.1,
        ge=0.01,
        le=0.5,
        description="Expected proportion of anomalies",
    )
    algorithm: Literal["auto", "ball_tree", "kd_tree", "brute"] = Field(
        default="auto",
        description="Algorithm for nearest neighbors",
    )


class OneClassSVMConfig(BaseSchema):
    """Configuration for One-Class SVM algorithm."""

    kernel: Literal["rbf", "linear", "poly", "sigmoid"] = Field(
        default="rbf",
        description="Kernel type for SVM",
    )
    nu: float = Field(
        default=0.1,
        ge=0.01,
        le=0.5,
        description="Upper bound on fraction of anomalies",
    )
    gamma: str | float = Field(
        default="scale",
        description="Kernel coefficient ('scale', 'auto', or float)",
    )


class DBSCANConfig(BaseSchema):
    """Configuration for DBSCAN algorithm."""

    eps: float = Field(
        default=0.5,
        ge=0.01,
        le=10.0,
        description="Maximum distance between samples in a cluster",
    )
    min_samples: int = Field(
        default=5,
        ge=2,
        le=50,
        description="Minimum samples in a core neighborhood",
    )
    metric: Literal["euclidean", "manhattan", "cosine"] = Field(
        default="euclidean",
        description="Distance metric",
    )


class StatisticalConfig(BaseSchema):
    """Configuration for Statistical anomaly detection."""

    method: Literal["zscore", "iqr", "mad"] = Field(
        default="zscore",
        description="Statistical method (z-score, IQR, or MAD)",
    )
    threshold: float = Field(
        default=3.0,
        ge=1.0,
        le=5.0,
        description="Threshold for anomaly detection (e.g., 3 std devs)",
    )


class AutoencoderConfig(BaseSchema):
    """Configuration for Autoencoder-based detection."""

    encoding_dim: int = Field(
        default=32,
        ge=8,
        le=256,
        description="Dimension of the encoding layer",
    )
    epochs: int = Field(
        default=50,
        ge=10,
        le=200,
        description="Number of training epochs",
    )
    threshold_percentile: float = Field(
        default=95,
        ge=90,
        le=99,
        description="Percentile for anomaly threshold",
    )
    batch_size: int = Field(
        default=32,
        ge=8,
        le=256,
        description="Training batch size",
    )


# =============================================================================
# Request Schemas
# =============================================================================


class AnomalyDetectionRequest(BaseSchema):
    """Request to run anomaly detection."""

    algorithm: AnomalyAlgorithm = Field(
        default=AnomalyAlgorithm.ISOLATION_FOREST,
        description="Detection algorithm to use",
    )
    columns: list[str] | None = Field(
        default=None,
        description="Columns to analyze (None = all numeric columns)",
    )
    config: dict[str, Any] | None = Field(
        default=None,
        description="Algorithm-specific configuration",
    )
    sample_size: int | None = Field(
        default=None,
        ge=100,
        description="Sample size for large datasets",
    )


# =============================================================================
# Result Schemas
# =============================================================================


class AnomalyRecord(BaseSchema):
    """Single anomaly record."""

    row_index: int = Field(..., description="Row index in the dataset")
    anomaly_score: float = Field(
        ...,
        description="Anomaly score (higher = more anomalous)",
    )
    column_values: dict[str, Any] = Field(
        default_factory=dict,
        description="Values of analyzed columns for this row",
    )
    is_anomaly: bool = Field(..., description="Whether classified as anomaly")


class ColumnAnomalySummary(BaseSchema):
    """Anomaly summary for a single column."""

    column: str = Field(..., description="Column name")
    dtype: str = Field(..., description="Data type")
    anomaly_count: int = Field(..., description="Number of anomalies in this column")
    anomaly_rate: float = Field(..., description="Rate of anomalies (0-1)")
    mean_anomaly_score: float = Field(..., description="Mean anomaly score")
    min_value: float | None = Field(default=None, description="Minimum value")
    max_value: float | None = Field(default=None, description="Maximum value")
    top_anomaly_indices: list[int] = Field(
        default_factory=list,
        description="Row indices of top anomalies",
    )


class AnomalyDetectionResponse(IDMixin, BaseSchema):
    """Response for anomaly detection results."""

    source_id: str = Field(..., description="Source ID that was analyzed")
    status: AnomalyStatus = Field(..., description="Detection status")
    algorithm: AnomalyAlgorithm = Field(..., description="Algorithm used")
    config: dict[str, Any] | None = Field(
        default=None,
        description="Configuration used",
    )

    # Results
    total_rows: int | None = Field(default=None, description="Total rows analyzed")
    anomaly_count: int | None = Field(default=None, description="Number of anomalies found")
    anomaly_rate: float | None = Field(
        default=None,
        description="Rate of anomalies (0-1)",
    )
    columns_analyzed: list[str] | None = Field(
        default=None,
        description="Columns that were analyzed",
    )
    column_summaries: list[ColumnAnomalySummary] | None = Field(
        default=None,
        description="Per-column anomaly summaries",
    )
    anomalies: list[AnomalyRecord] | None = Field(
        default=None,
        description="Top anomaly records (limited to 100)",
    )

    # Timing
    duration_ms: int | None = Field(default=None, description="Execution time in ms")
    error_message: str | None = Field(default=None, description="Error message if failed")

    # Timestamps
    created_at: str = Field(..., description="When detection was created")
    started_at: str | None = Field(default=None, description="When detection started")
    completed_at: str | None = Field(default=None, description="When detection completed")


class AnomalyDetectionListResponse(ListResponseWrapper[AnomalyDetectionResponse]):
    """Paginated anomaly detection list response."""

    pass


# =============================================================================
# Batch Detection Schemas
# =============================================================================


class BatchDetectionStatus(str, Enum):
    """Status of a batch anomaly detection job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    ERROR = "error"
    CANCELLED = "cancelled"


class BatchDetectionRequest(BaseSchema):
    """Request to run batch anomaly detection across multiple sources."""

    source_ids: list[str] = Field(
        ...,
        min_length=1,
        description="List of source IDs to run detection on",
    )
    name: str | None = Field(
        default=None,
        max_length=255,
        description="Optional name for this batch job",
    )
    algorithm: AnomalyAlgorithm = Field(
        default=AnomalyAlgorithm.ISOLATION_FOREST,
        description="Detection algorithm to use for all sources",
    )
    config: dict[str, Any] | None = Field(
        default=None,
        description="Algorithm-specific configuration",
    )
    sample_size: int | None = Field(
        default=None,
        ge=100,
        description="Sample size for large datasets",
    )


class BatchSourceResult(BaseSchema):
    """Result for a single source in a batch job."""

    source_id: str = Field(..., description="Source ID")
    source_name: str | None = Field(default=None, description="Source name")
    detection_id: str | None = Field(default=None, description="Detection ID if completed")
    status: str = Field(..., description="Status: pending, running, success, error")
    anomaly_count: int | None = Field(default=None, description="Number of anomalies found")
    anomaly_rate: float | None = Field(default=None, description="Rate of anomalies (0-1)")
    total_rows: int | None = Field(default=None, description="Total rows analyzed")
    error_message: str | None = Field(default=None, description="Error message if failed")


class BatchDetectionResponse(IDMixin, BaseSchema):
    """Response for batch anomaly detection job."""

    name: str | None = Field(default=None, description="Job name")
    status: BatchDetectionStatus = Field(..., description="Batch job status")
    algorithm: AnomalyAlgorithm = Field(..., description="Algorithm used")
    config: dict[str, Any] | None = Field(default=None, description="Configuration used")

    # Progress
    total_sources: int = Field(..., description="Total number of sources")
    completed_sources: int = Field(..., description="Number of completed sources")
    failed_sources: int = Field(default=0, description="Number of failed sources")
    progress_percent: float = Field(..., description="Progress percentage (0-100)")
    current_source_id: str | None = Field(
        default=None,
        description="Currently processing source ID",
    )

    # Aggregate results
    total_anomalies: int = Field(default=0, description="Total anomalies found")
    total_rows_analyzed: int = Field(default=0, description="Total rows analyzed")
    average_anomaly_rate: float = Field(
        default=0.0,
        description="Average anomaly rate across sources",
    )

    # Per-source results
    results: list[BatchSourceResult] | None = Field(
        default=None,
        description="Results for each source",
    )

    # Timing
    duration_ms: int | None = Field(default=None, description="Total execution time in ms")
    error_message: str | None = Field(default=None, description="Error message if failed")

    # Timestamps
    created_at: str = Field(..., description="When batch job was created")
    started_at: str | None = Field(default=None, description="When batch job started")
    completed_at: str | None = Field(default=None, description="When batch job completed")


class BatchDetectionListResponse(ListResponseWrapper[BatchDetectionResponse]):
    """Paginated batch detection list response."""

    pass


# =============================================================================
# Algorithm Comparison Schemas
# =============================================================================


class AlgorithmComparisonRequest(BaseSchema):
    """Request to compare multiple anomaly detection algorithms."""

    algorithms: list[AnomalyAlgorithm] = Field(
        ...,
        min_length=2,
        max_length=6,
        description="List of algorithms to compare (2-6 algorithms)",
    )
    columns: list[str] | None = Field(
        default=None,
        description="Columns to analyze (None = all numeric columns)",
    )
    config: dict[str, dict[str, Any]] | None = Field(
        default=None,
        description="Algorithm-specific configurations keyed by algorithm name",
    )
    sample_size: int | None = Field(
        default=None,
        ge=100,
        description="Sample size for large datasets",
    )


class AlgorithmComparisonResultItem(BaseSchema):
    """Single algorithm result within a comparison."""

    algorithm: AnomalyAlgorithm = Field(..., description="Algorithm name")
    display_name: str = Field(..., description="Human-readable algorithm name")
    status: AnomalyStatus = Field(..., description="Execution status")
    anomaly_count: int | None = Field(default=None, description="Number of anomalies found")
    anomaly_rate: float | None = Field(default=None, description="Rate of anomalies (0-1)")
    duration_ms: int | None = Field(default=None, description="Execution time in ms")
    error_message: str | None = Field(default=None, description="Error message if failed")
    anomaly_indices: list[int] = Field(
        default_factory=list,
        description="Row indices flagged as anomalies",
    )


class AgreementLevel(str, Enum):
    """Level of agreement among algorithms."""

    ALL = "all"
    MAJORITY = "majority"
    SOME = "some"
    ONE = "one"


class AgreementRecord(BaseSchema):
    """A row with its agreement information across algorithms."""

    row_index: int = Field(..., description="Row index in the dataset")
    detected_by: list[AnomalyAlgorithm] = Field(
        ...,
        description="Algorithms that flagged this row as anomaly",
    )
    detection_count: int = Field(..., description="Number of algorithms that detected this row")
    agreement_level: AgreementLevel = Field(..., description="Level of agreement")
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score based on agreement (0-1)",
    )
    column_values: dict[str, Any] = Field(
        default_factory=dict,
        description="Values of analyzed columns for this row",
    )


class AgreementSummary(BaseSchema):
    """Summary of algorithm agreement."""

    total_algorithms: int = Field(..., description="Number of algorithms compared")
    total_unique_anomalies: int = Field(
        ...,
        description="Total unique rows flagged by at least one algorithm",
    )
    all_agree_count: int = Field(
        ...,
        description="Rows flagged by all algorithms",
    )
    majority_agree_count: int = Field(
        ...,
        description="Rows flagged by majority (>50%) of algorithms",
    )
    some_agree_count: int = Field(
        ...,
        description="Rows flagged by at least 2 algorithms",
    )
    one_only_count: int = Field(
        ...,
        description="Rows flagged by only 1 algorithm",
    )
    agreement_matrix: list[list[int]] = Field(
        default_factory=list,
        description="Pairwise overlap matrix between algorithms",
    )


class AlgorithmComparisonResult(IDMixin, BaseSchema):
    """Response for algorithm comparison results."""

    source_id: str = Field(..., description="Source ID that was analyzed")
    status: AnomalyStatus = Field(..., description="Overall comparison status")
    total_rows: int | None = Field(default=None, description="Total rows analyzed")
    columns_analyzed: list[str] | None = Field(
        default=None,
        description="Columns that were analyzed",
    )

    # Individual algorithm results
    algorithm_results: list[AlgorithmComparisonResultItem] = Field(
        default_factory=list,
        description="Results from each algorithm",
    )

    # Agreement analysis
    agreement_summary: AgreementSummary | None = Field(
        default=None,
        description="Summary of agreement between algorithms",
    )
    agreement_records: list[AgreementRecord] | None = Field(
        default=None,
        description="Records with their agreement information (limited to top 100)",
    )

    # Timing
    total_duration_ms: int | None = Field(
        default=None,
        description="Total execution time in ms",
    )
    error_message: str | None = Field(default=None, description="Error message if failed")

    # Timestamps
    created_at: str = Field(..., description="When comparison was created")
    completed_at: str | None = Field(default=None, description="When comparison completed")


class AlgorithmComparisonListResponse(ListResponseWrapper[AlgorithmComparisonResult]):
    """Paginated algorithm comparison list response."""

    pass


# =============================================================================
# Algorithm Info Schemas
# =============================================================================


class AlgorithmParameter(BaseSchema):
    """Parameter definition for an algorithm."""

    name: str = Field(..., description="Parameter name")
    label: str = Field(..., description="Display label")
    type: Literal["integer", "float", "string", "select", "boolean"] = Field(
        ...,
        description="Parameter type",
    )
    default: Any = Field(..., description="Default value")
    min_value: float | None = Field(default=None, description="Minimum value (for numeric)")
    max_value: float | None = Field(default=None, description="Maximum value (for numeric)")
    options: list[str] | None = Field(default=None, description="Options for select type")
    description: str = Field(..., description="Parameter description")


class AlgorithmInfo(BaseSchema):
    """Information about an anomaly detection algorithm."""

    name: AnomalyAlgorithm = Field(..., description="Algorithm identifier")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Algorithm description")
    category: AlgorithmCategory = Field(..., description="Algorithm category")
    parameters: list[AlgorithmParameter] = Field(
        default_factory=list,
        description="Configurable parameters",
    )
    pros: list[str] = Field(default_factory=list, description="Algorithm advantages")
    cons: list[str] = Field(default_factory=list, description="Algorithm limitations")
    best_for: str = Field(..., description="Best use case description")
    requires_scaling: bool = Field(
        default=True,
        description="Whether data scaling is recommended",
    )


class AlgorithmListResponse(BaseSchema):
    """Response containing all available algorithms."""

    algorithms: list[AlgorithmInfo] = Field(
        ...,
        description="Available anomaly detection algorithms",
    )
    total: int = Field(..., description="Total number of algorithms")


# =============================================================================
# Helper function to get algorithm info
# =============================================================================


def get_algorithm_info_list() -> list[AlgorithmInfo]:
    """Get information about all supported algorithms."""
    return [
        AlgorithmInfo(
            name=AnomalyAlgorithm.ISOLATION_FOREST,
            display_name="Isolation Forest",
            description="Tree-based algorithm that isolates anomalies by random partitioning. "
            "Works by building trees that isolate observations - anomalies require fewer "
            "partitions to isolate.",
            category="tree",
            parameters=[
                AlgorithmParameter(
                    name="n_estimators",
                    label="Number of Trees",
                    type="integer",
                    default=100,
                    min_value=10,
                    max_value=500,
                    description="Number of isolation trees in the ensemble",
                ),
                AlgorithmParameter(
                    name="contamination",
                    label="Contamination",
                    type="float",
                    default=0.1,
                    min_value=0.01,
                    max_value=0.5,
                    description="Expected proportion of anomalies in the dataset",
                ),
            ],
            pros=["Fast training and prediction", "Scales well to large datasets", "No distribution assumptions"],
            cons=["May miss clustered anomalies", "Sensitive to contamination parameter"],
            best_for="Large datasets with global anomalies, high-dimensional data",
            requires_scaling=False,
        ),
        AlgorithmInfo(
            name=AnomalyAlgorithm.LOF,
            display_name="Local Outlier Factor",
            description="Density-based algorithm that compares local density of a point with "
            "its neighbors. Points with substantially lower density are considered outliers.",
            category="density",
            parameters=[
                AlgorithmParameter(
                    name="n_neighbors",
                    label="Number of Neighbors",
                    type="integer",
                    default=20,
                    min_value=5,
                    max_value=100,
                    description="Number of neighbors for local density estimation",
                ),
                AlgorithmParameter(
                    name="contamination",
                    label="Contamination",
                    type="float",
                    default=0.1,
                    min_value=0.01,
                    max_value=0.5,
                    description="Expected proportion of anomalies",
                ),
            ],
            pros=["Detects local anomalies", "Works well with varying densities", "Intuitive interpretation"],
            cons=["Computationally expensive for large datasets", "Sensitive to n_neighbors"],
            best_for="Datasets with varying cluster densities, local outlier detection",
            requires_scaling=True,
        ),
        AlgorithmInfo(
            name=AnomalyAlgorithm.ONE_CLASS_SVM,
            display_name="One-Class SVM",
            description="Support Vector Machine trained only on normal data. Creates a "
            "decision boundary around normal observations, flagging points outside as anomalies.",
            category="svm",
            parameters=[
                AlgorithmParameter(
                    name="kernel",
                    label="Kernel",
                    type="select",
                    default="rbf",
                    options=["rbf", "linear", "poly", "sigmoid"],
                    description="Kernel function for the SVM",
                ),
                AlgorithmParameter(
                    name="nu",
                    label="Nu",
                    type="float",
                    default=0.1,
                    min_value=0.01,
                    max_value=0.5,
                    description="Upper bound on fraction of training errors",
                ),
            ],
            pros=["Effective in high dimensions", "Flexible via kernel choice", "Memory efficient"],
            cons=["Slow for large datasets", "Sensitive to kernel and parameters"],
            best_for="High-dimensional data, when data fits in memory",
            requires_scaling=True,
        ),
        AlgorithmInfo(
            name=AnomalyAlgorithm.DBSCAN,
            display_name="DBSCAN",
            description="Density-based clustering that identifies points not belonging to any "
            "cluster as anomalies. Works by grouping points that are close together.",
            category="clustering",
            parameters=[
                AlgorithmParameter(
                    name="eps",
                    label="Epsilon (eps)",
                    type="float",
                    default=0.5,
                    min_value=0.01,
                    max_value=10.0,
                    description="Maximum distance between two samples in a cluster",
                ),
                AlgorithmParameter(
                    name="min_samples",
                    label="Minimum Samples",
                    type="integer",
                    default=5,
                    min_value=2,
                    max_value=50,
                    description="Minimum samples in a core neighborhood",
                ),
            ],
            pros=["No contamination parameter needed", "Finds arbitrarily shaped clusters", "Robust to noise"],
            cons=["Sensitive to eps parameter", "Struggles with varying densities"],
            best_for="Datasets with clear cluster structure, spatial data",
            requires_scaling=True,
        ),
        AlgorithmInfo(
            name=AnomalyAlgorithm.STATISTICAL,
            display_name="Statistical",
            description="Traditional statistical methods including Z-score (standard deviations "
            "from mean), IQR (interquartile range), and MAD (median absolute deviation).",
            category="statistical",
            parameters=[
                AlgorithmParameter(
                    name="method",
                    label="Method",
                    type="select",
                    default="zscore",
                    options=["zscore", "iqr", "mad"],
                    description="Statistical method for detection",
                ),
                AlgorithmParameter(
                    name="threshold",
                    label="Threshold",
                    type="float",
                    default=3.0,
                    min_value=1.0,
                    max_value=5.0,
                    description="Number of standard deviations/IQR multiplier",
                ),
            ],
            pros=["Simple and interpretable", "Fast computation", "Works on univariate data"],
            cons=["Assumes normal distribution (for z-score)", "May miss complex anomalies"],
            best_for="Univariate data, quick analysis, interpretable results",
            requires_scaling=False,
        ),
        AlgorithmInfo(
            name=AnomalyAlgorithm.AUTOENCODER,
            display_name="Autoencoder",
            description="Neural network that learns to compress and reconstruct data. "
            "Anomalies have high reconstruction error as they differ from normal patterns.",
            category="neural",
            parameters=[
                AlgorithmParameter(
                    name="encoding_dim",
                    label="Encoding Dimension",
                    type="integer",
                    default=32,
                    min_value=8,
                    max_value=256,
                    description="Dimension of the encoding (bottleneck) layer",
                ),
                AlgorithmParameter(
                    name="epochs",
                    label="Training Epochs",
                    type="integer",
                    default=50,
                    min_value=10,
                    max_value=200,
                    description="Number of training epochs",
                ),
                AlgorithmParameter(
                    name="threshold_percentile",
                    label="Threshold Percentile",
                    type="float",
                    default=95,
                    min_value=90,
                    max_value=99,
                    description="Percentile of reconstruction error for anomaly threshold",
                ),
            ],
            pros=["Captures complex patterns", "Learns data representation", "Works with high dimensions"],
            cons=["Requires more data", "Computationally expensive", "Black box"],
            best_for="Complex patterns, large datasets, multivariate anomalies",
            requires_scaling=True,
        ),
    ]


# =============================================================================
# Explainability Schemas
# =============================================================================


class FeatureContribution(BaseSchema):
    """Feature contribution to anomaly score (SHAP value)."""

    feature: str = Field(..., description="Feature/column name")
    value: float = Field(..., description="Actual feature value for this row")
    shap_value: float = Field(
        ...,
        description="SHAP value indicating contribution direction and magnitude",
    )
    contribution: float = Field(
        ...,
        ge=0,
        description="Absolute contribution (|shap_value|)",
    )


class AnomalyExplanationResult(BaseSchema):
    """Explanation for a single anomalous row."""

    row_index: int = Field(..., description="Row index in the dataset")
    anomaly_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Anomaly score for this row",
    )
    feature_contributions: list[FeatureContribution] = Field(
        ...,
        description="Feature contributions sorted by importance",
    )
    total_shap: float = Field(
        ...,
        description="Sum of all SHAP values for this row",
    )
    summary: str = Field(
        ...,
        description="Human-readable summary of why this row is anomalous",
    )


class ExplainabilityRequest(BaseSchema):
    """Request to generate explanations for anomalies."""

    row_indices: list[int] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Row indices to explain (max 100)",
    )
    max_features: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of features to include in explanation",
    )
    sample_background: int = Field(
        default=100,
        ge=10,
        le=500,
        description="Number of background samples for SHAP KernelExplainer",
    )


class ExplainabilityResponse(BaseSchema):
    """Response containing anomaly explanations."""

    detection_id: str = Field(..., description="ID of the anomaly detection run")
    algorithm: str = Field(..., description="Detection algorithm used")
    row_indices: list[int] = Field(..., description="Row indices that were explained")
    feature_names: list[str] = Field(..., description="Feature/column names analyzed")
    explanations: list[AnomalyExplanationResult] = Field(
        ...,
        description="Explanations for each requested row",
    )
    generated_at: str = Field(..., description="When explanations were generated")
    error: str | None = Field(default=None, description="Error message if generation failed")


class CachedExplanationResponse(IDMixin, BaseSchema):
    """Response for a cached explanation from database."""

    detection_id: str = Field(..., description="ID of the anomaly detection run")
    row_index: int = Field(..., description="Row index in the dataset")
    anomaly_score: float = Field(..., description="Anomaly score for this row")
    feature_contributions: list[FeatureContribution] = Field(
        ...,
        description="Feature contributions",
    )
    total_shap: float = Field(..., description="Sum of all SHAP values")
    summary: str = Field(..., description="Human-readable explanation summary")
    generated_at: str | None = Field(
        default=None,
        description="When this explanation was generated",
    )


class CachedExplanationsListResponse(BaseSchema):
    """Response containing list of cached explanations."""

    detection_id: str = Field(..., description="ID of the anomaly detection run")
    explanations: list[CachedExplanationResponse] = Field(
        ...,
        description="Cached explanations",
    )
    total: int = Field(..., description="Total number of explanations")


# =============================================================================
# Streaming Anomaly Detection Schemas
# =============================================================================


class StreamingAlgorithm(str, Enum):
    """Supported streaming anomaly detection algorithms."""

    ZSCORE_ROLLING = "zscore_rolling"
    EXPONENTIAL_MOVING_AVERAGE = "ema"
    ISOLATION_FOREST_INCREMENTAL = "isolation_forest_incremental"
    HALF_SPACE_TREES = "half_space_trees"
    ROBUST_RANDOM_CUT_FOREST = "rrcf"


class StreamingSessionStatus(str, Enum):
    """Status of a streaming session."""

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class StreamingSessionCreate(BaseSchema):
    """Request to create a streaming session."""

    source_id: str | None = Field(
        default=None,
        description="Optional source ID to associate with",
    )
    algorithm: StreamingAlgorithm = Field(
        default=StreamingAlgorithm.ZSCORE_ROLLING,
        description="Streaming detection algorithm",
    )
    window_size: int = Field(
        default=100,
        ge=10,
        le=10000,
        description="Size of the sliding window",
    )
    threshold: float = Field(
        default=3.0,
        ge=1.0,
        le=10.0,
        description="Anomaly detection threshold",
    )
    columns: list[str] | None = Field(
        default=None,
        description="Columns to monitor (None = all numeric)",
    )
    config: dict[str, Any] | None = Field(
        default=None,
        description="Additional algorithm configuration",
    )


class StreamingStatistics(BaseSchema):
    """Rolling statistics for a column."""

    count: int = Field(..., description="Number of data points")
    mean: float = Field(..., description="Rolling mean")
    std: float = Field(..., description="Rolling standard deviation")
    min: float | None = Field(default=None, description="Minimum value")
    max: float | None = Field(default=None, description="Maximum value")
    anomaly_count: int = Field(..., description="Number of anomalies detected")
    anomaly_rate: float = Field(..., description="Rate of anomalies (0-1)")


class StreamingSessionResponse(IDMixin, BaseSchema):
    """Response for a streaming session."""

    source_id: str | None = Field(default=None, description="Associated source ID")
    algorithm: StreamingAlgorithm = Field(..., description="Detection algorithm")
    window_size: int = Field(..., description="Sliding window size")
    threshold: float = Field(..., description="Detection threshold")
    columns: list[str] = Field(..., description="Columns being monitored")
    status: StreamingSessionStatus = Field(..., description="Session status")
    config: dict[str, Any] | None = Field(default=None, description="Algorithm config")
    statistics: dict[str, StreamingStatistics] | None = Field(
        default=None,
        description="Per-column statistics",
    )
    total_points: int = Field(default=0, description="Total data points processed")
    total_alerts: int = Field(default=0, description="Total alerts generated")
    created_at: str = Field(..., description="When session was created")
    started_at: str | None = Field(default=None, description="When session started")
    stopped_at: str | None = Field(default=None, description="When session stopped")


class StreamingSessionListResponse(ListResponseWrapper[StreamingSessionResponse]):
    """Paginated streaming session list response."""

    pass


class StreamingDataPoint(BaseSchema):
    """A single data point to push to streaming session."""

    data: dict[str, Any] = Field(..., description="Column name to value mapping")
    timestamp: str | None = Field(
        default=None,
        description="ISO format timestamp (defaults to now)",
    )


class StreamingDataBatch(BaseSchema):
    """A batch of data points to push."""

    data_points: list[StreamingDataPoint] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of data points",
    )


class StreamingAlert(BaseSchema):
    """An anomaly alert from streaming detection."""

    id: str = Field(..., description="Alert unique identifier")
    session_id: str = Field(..., description="Session that generated this alert")
    timestamp: str = Field(..., description="When anomaly was detected")
    data_point: dict[str, Any] = Field(..., description="The data point that triggered alert")
    anomaly_score: float = Field(..., description="Anomaly score (higher = more anomalous)")
    is_anomaly: bool = Field(..., description="Whether classified as anomaly")
    algorithm: StreamingAlgorithm = Field(..., description="Algorithm that detected it")
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional detection details",
    )


class StreamingAlertListResponse(ListResponseWrapper[StreamingAlert]):
    """Paginated streaming alert list response."""

    pass


class StreamingStatusResponse(BaseSchema):
    """Status response for a streaming session."""

    session_id: str = Field(..., description="Session ID")
    status: StreamingSessionStatus = Field(..., description="Current status")
    total_points: int = Field(..., description="Total data points processed")
    total_alerts: int = Field(..., description="Total alerts generated")
    buffer_utilization: float = Field(
        ...,
        ge=0,
        le=1,
        description="Buffer utilization (0-1)",
    )
    statistics: dict[str, StreamingStatistics] = Field(
        ...,
        description="Per-column statistics",
    )
    recent_alerts: list[StreamingAlert] = Field(
        default_factory=list,
        description="Recent alerts (last 10)",
    )


class StreamingRecentDataResponse(BaseSchema):
    """Response containing recent data points."""

    session_id: str = Field(..., description="Session ID")
    data_points: list[dict[str, Any]] = Field(
        ...,
        description="Recent data points with timestamps",
    )
    total: int = Field(..., description="Total points in response")


class StreamingAlgorithmInfo(BaseSchema):
    """Information about a streaming algorithm."""

    name: StreamingAlgorithm = Field(..., description="Algorithm identifier")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Algorithm description")
    supports_online_learning: bool = Field(
        ...,
        description="Whether algorithm supports online model updates",
    )
    parameters: list[AlgorithmParameter] = Field(
        default_factory=list,
        description="Configurable parameters",
    )
    best_for: str = Field(..., description="Best use case description")


class StreamingAlgorithmListResponse(BaseSchema):
    """Response containing streaming algorithms."""

    algorithms: list[StreamingAlgorithmInfo] = Field(
        ...,
        description="Available streaming algorithms",
    )
    total: int = Field(..., description="Total number of algorithms")


def get_streaming_algorithm_info_list() -> list[StreamingAlgorithmInfo]:
    """Get information about all supported streaming algorithms."""
    return [
        StreamingAlgorithmInfo(
            name=StreamingAlgorithm.ZSCORE_ROLLING,
            display_name="Rolling Z-Score",
            description="Detects anomalies based on rolling z-scores computed over a sliding window. "
            "Simple and effective for stationary data streams.",
            supports_online_learning=True,
            parameters=[
                AlgorithmParameter(
                    name="window_size",
                    label="Window Size",
                    type="integer",
                    default=100,
                    min_value=10,
                    max_value=10000,
                    description="Number of recent points to use for statistics",
                ),
                AlgorithmParameter(
                    name="threshold",
                    label="Z-Score Threshold",
                    type="float",
                    default=3.0,
                    min_value=1.0,
                    max_value=5.0,
                    description="Number of standard deviations for anomaly threshold",
                ),
            ],
            best_for="Simple time series with stationary patterns, quick setup",
        ),
        StreamingAlgorithmInfo(
            name=StreamingAlgorithm.EXPONENTIAL_MOVING_AVERAGE,
            display_name="Exponential Moving Average",
            description="Uses exponentially weighted moving average to track trends and detect "
            "deviations. Adapts quickly to recent changes in the data.",
            supports_online_learning=True,
            parameters=[
                AlgorithmParameter(
                    name="alpha",
                    label="Smoothing Factor (Alpha)",
                    type="float",
                    default=0.1,
                    min_value=0.01,
                    max_value=0.5,
                    description="Weight for recent observations (higher = more responsive)",
                ),
                AlgorithmParameter(
                    name="threshold_multiplier",
                    label="Threshold Multiplier",
                    type="float",
                    default=2.0,
                    min_value=1.0,
                    max_value=5.0,
                    description="Multiplier for deviation threshold",
                ),
            ],
            best_for="Non-stationary data with changing trends, sensor data",
        ),
        StreamingAlgorithmInfo(
            name=StreamingAlgorithm.ISOLATION_FOREST_INCREMENTAL,
            display_name="Incremental Isolation Forest",
            description="Periodically retrains Isolation Forest on recent window data. "
            "Good for detecting global anomalies in multi-dimensional streams.",
            supports_online_learning=False,
            parameters=[
                AlgorithmParameter(
                    name="contamination",
                    label="Contamination",
                    type="float",
                    default=0.1,
                    min_value=0.01,
                    max_value=0.5,
                    description="Expected proportion of anomalies",
                ),
                AlgorithmParameter(
                    name="window_size",
                    label="Training Window",
                    type="integer",
                    default=100,
                    min_value=50,
                    max_value=1000,
                    description="Window size for periodic retraining",
                ),
            ],
            best_for="Multi-dimensional streams, complex patterns",
        ),
        StreamingAlgorithmInfo(
            name=StreamingAlgorithm.HALF_SPACE_TREES,
            display_name="Half-Space Trees",
            description="Streaming variant of Isolation Forest using half-space partitioning. "
            "Efficient for high-dimensional streaming data.",
            supports_online_learning=True,
            parameters=[
                AlgorithmParameter(
                    name="n_trees",
                    label="Number of Trees",
                    type="integer",
                    default=25,
                    min_value=5,
                    max_value=100,
                    description="Number of half-space trees",
                ),
                AlgorithmParameter(
                    name="height",
                    label="Tree Height",
                    type="integer",
                    default=8,
                    min_value=4,
                    max_value=15,
                    description="Maximum depth of each tree",
                ),
            ],
            best_for="High-dimensional streaming data, real-time requirements",
        ),
        StreamingAlgorithmInfo(
            name=StreamingAlgorithm.ROBUST_RANDOM_CUT_FOREST,
            display_name="Robust Random Cut Forest",
            description="Uses collusive displacement for anomaly scoring. "
            "Robust to noise and concept drift in streaming data.",
            supports_online_learning=True,
            parameters=[
                AlgorithmParameter(
                    name="num_trees",
                    label="Number of Trees",
                    type="integer",
                    default=40,
                    min_value=10,
                    max_value=100,
                    description="Number of random cut trees",
                ),
                AlgorithmParameter(
                    name="tree_size",
                    label="Tree Size",
                    type="integer",
                    default=256,
                    min_value=64,
                    max_value=1024,
                    description="Maximum number of points per tree",
                ),
            ],
            best_for="Complex streaming data with concept drift, AWS Kinesis integration",
        ),
    ]
