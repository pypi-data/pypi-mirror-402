"""Pydantic schemas for ML Model Monitoring.

Provides schemas for:
- Model registration and management
- Performance metrics (latency, throughput, error rates)
- Data quality metrics (null rates, type violations)
- Drift detection integration
- Alert rules and handlers
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

from .base import BaseSchema, IDMixin, ListResponseWrapper, TimestampMixin


# =============================================================================
# Enums
# =============================================================================


class ModelStatus(str, Enum):
    """Model monitoring status."""

    ACTIVE = "active"
    PAUSED = "paused"
    DEGRADED = "degraded"
    ERROR = "error"


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class MetricType(str, Enum):
    """Types of metrics collected."""

    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    NULL_RATE = "null_rate"
    TYPE_VIOLATION = "type_violation"
    DRIFT_SCORE = "drift_score"
    CUSTOM = "custom"


class AlertRuleType(str, Enum):
    """Types of alert rules."""

    THRESHOLD = "threshold"
    STATISTICAL = "statistical"
    TREND = "trend"


class AlertHandlerType(str, Enum):
    """Types of alert handlers."""

    SLACK = "slack"
    WEBHOOK = "webhook"
    EMAIL = "email"


# =============================================================================
# Model Registration Schemas
# =============================================================================


class ModelConfigBase(BaseSchema):
    """Configuration for model monitoring."""

    enable_drift_detection: bool = Field(default=True, description="Enable drift detection")
    enable_quality_metrics: bool = Field(default=True, description="Enable quality metrics")
    enable_performance_metrics: bool = Field(default=True, description="Enable performance metrics")
    sample_rate: float = Field(default=1.0, description="Sampling rate for metrics", ge=0.0, le=1.0)
    drift_threshold: float = Field(default=0.1, description="Threshold for drift detection", ge=0.0, le=1.0)
    drift_window_size: int = Field(default=1000, description="Window size for drift detection", ge=100)


class RegisteredModelBase(BaseSchema):
    """Base schema for registered model."""

    name: str = Field(..., description="Model name/identifier", min_length=1, max_length=255)
    version: str = Field(default="1.0.0", description="Model version")
    description: str = Field(default="", description="Model description")
    status: ModelStatus = Field(default=ModelStatus.ACTIVE, description="Monitoring status")
    config: ModelConfigBase = Field(default_factory=ModelConfigBase, description="Monitoring config")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class RegisterModelRequest(RegisteredModelBase):
    """Request to register a model for monitoring."""

    pass


class UpdateModelRequest(BaseSchema):
    """Request to update model registration."""

    name: str | None = Field(None, description="Model name")
    version: str | None = Field(None, description="Model version")
    description: str | None = Field(None, description="Model description")
    status: ModelStatus | None = Field(None, description="Monitoring status")
    config: ModelConfigBase | None = Field(None, description="Monitoring config")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")


class RegisteredModelResponse(RegisteredModelBase, IDMixin, TimestampMixin):
    """Response for registered model."""

    prediction_count: int = Field(default=0, description="Total predictions")
    last_prediction_at: datetime | None = Field(None, description="Last prediction timestamp")
    current_drift_score: float | None = Field(None, description="Current drift score")
    health_score: float = Field(default=100.0, description="Model health score (0-100)")


class RegisteredModelListResponse(ListResponseWrapper):
    """List response for registered models."""

    items: list[RegisteredModelResponse]


# =============================================================================
# Metrics Schemas
# =============================================================================


class MetricDataPoint(BaseModel):
    """Single metric data point."""

    timestamp: datetime = Field(..., description="Measurement timestamp")
    value: float = Field(..., description="Metric value")
    labels: dict[str, str] = Field(default_factory=dict, description="Metric labels")


class MetricSummary(BaseModel):
    """Summary statistics for a metric."""

    name: str = Field(..., description="Metric name")
    type: MetricType = Field(..., description="Metric type")
    count: int = Field(default=0, description="Number of observations")
    min_value: float | None = Field(None, description="Minimum value")
    max_value: float | None = Field(None, description="Maximum value")
    avg_value: float | None = Field(None, description="Average value")
    p50_value: float | None = Field(None, description="50th percentile")
    p95_value: float | None = Field(None, description="95th percentile")
    p99_value: float | None = Field(None, description="99th percentile")
    last_value: float | None = Field(None, description="Most recent value")


class RecordPredictionRequest(BaseModel):
    """Request to record a model prediction."""

    features: dict[str, Any] = Field(..., description="Input features")
    prediction: Any = Field(..., description="Model prediction output")
    actual: Any | None = Field(None, description="Actual value (for accuracy tracking)")
    latency_ms: float | None = Field(None, description="Prediction latency in ms", ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class RecordPredictionResponse(BaseModel):
    """Response for recorded prediction."""

    id: str = Field(..., description="Prediction ID")
    model_id: str = Field(..., description="Model ID")
    recorded_at: datetime = Field(..., description="Recording timestamp")


class MetricsResponse(BaseModel):
    """Response containing model metrics."""

    model_id: str = Field(..., description="Model ID")
    model_name: str = Field(..., description="Model name")
    time_range_hours: int = Field(default=24, description="Time range for metrics")
    metrics: list[MetricSummary] = Field(default_factory=list, description="Metric summaries")
    data_points: dict[str, list[MetricDataPoint]] = Field(
        default_factory=dict,
        description="Time series data points by metric name",
    )


# =============================================================================
# Alert Rule Schemas
# =============================================================================


class ThresholdRuleConfig(BaseModel):
    """Configuration for threshold-based alert rule."""

    metric_name: str = Field(..., description="Metric to monitor")
    threshold: float = Field(..., description="Threshold value")
    comparison: Literal["gt", "lt", "gte", "lte", "eq"] = Field(
        default="gt",
        description="Comparison operator",
    )
    duration_seconds: int = Field(
        default=0,
        description="Condition must persist for this duration",
        ge=0,
    )


class StatisticalRuleConfig(BaseModel):
    """Configuration for statistical alert rule."""

    metric_name: str = Field(..., description="Metric to monitor")
    std_devs: float = Field(default=3.0, description="Standard deviations for anomaly", ge=1.0)
    window_size: int = Field(default=100, description="Window size for baseline", ge=10)


class AlertRuleBase(BaseSchema):
    """Base schema for alert rules."""

    name: str = Field(..., description="Rule name", min_length=1, max_length=255)
    model_id: str = Field(..., description="Model ID this rule applies to")
    rule_type: AlertRuleType = Field(..., description="Type of alert rule")
    severity: AlertSeverity = Field(default=AlertSeverity.WARNING, description="Alert severity")
    config: dict[str, Any] = Field(..., description="Rule-specific configuration")
    is_active: bool = Field(default=True, description="Whether rule is active")


class CreateAlertRuleRequest(AlertRuleBase):
    """Request to create an alert rule."""

    pass


class UpdateAlertRuleRequest(BaseSchema):
    """Request to update an alert rule."""

    name: str | None = Field(None, description="Rule name")
    severity: AlertSeverity | None = Field(None, description="Alert severity")
    config: dict[str, Any] | None = Field(None, description="Rule configuration")
    is_active: bool | None = Field(None, description="Whether rule is active")


class AlertRuleResponse(AlertRuleBase, IDMixin, TimestampMixin):
    """Response for alert rule."""

    last_triggered_at: datetime | None = Field(None, description="Last trigger time")
    trigger_count: int = Field(default=0, description="Total triggers")


class AlertRuleListResponse(ListResponseWrapper):
    """List response for alert rules."""

    items: list[AlertRuleResponse]


# =============================================================================
# Alert Handler Schemas
# =============================================================================


class SlackHandlerConfig(BaseModel):
    """Configuration for Slack alert handler."""

    webhook_url: str = Field(..., description="Slack webhook URL")
    channel: str | None = Field(None, description="Override channel")
    username: str = Field(default="Truthound", description="Bot username")


class WebhookHandlerConfig(BaseModel):
    """Configuration for webhook alert handler."""

    url: str = Field(..., description="Webhook URL")
    method: Literal["POST", "PUT"] = Field(default="POST", description="HTTP method")
    headers: dict[str, str] = Field(default_factory=dict, description="Custom headers")


class AlertHandlerBase(BaseSchema):
    """Base schema for alert handlers."""

    name: str = Field(..., description="Handler name", min_length=1, max_length=255)
    handler_type: AlertHandlerType = Field(..., description="Type of handler")
    config: dict[str, Any] = Field(..., description="Handler-specific configuration")
    is_active: bool = Field(default=True, description="Whether handler is active")


class CreateAlertHandlerRequest(AlertHandlerBase):
    """Request to create an alert handler."""

    pass


class UpdateAlertHandlerRequest(BaseSchema):
    """Request to update an alert handler."""

    name: str | None = Field(None, description="Handler name")
    config: dict[str, Any] | None = Field(None, description="Handler configuration")
    is_active: bool | None = Field(None, description="Whether handler is active")


class AlertHandlerResponse(AlertHandlerBase, IDMixin, TimestampMixin):
    """Response for alert handler."""

    last_sent_at: datetime | None = Field(None, description="Last alert sent time")
    send_count: int = Field(default=0, description="Total alerts sent")
    failure_count: int = Field(default=0, description="Total failures")


class AlertHandlerListResponse(ListResponseWrapper):
    """List response for alert handlers."""

    items: list[AlertHandlerResponse]


# =============================================================================
# Alert Instance Schemas
# =============================================================================


class AlertInstance(BaseModel, TimestampMixin):
    """An instance of a triggered alert."""

    id: str = Field(..., description="Alert instance ID")
    rule_id: str = Field(..., description="Rule that triggered")
    model_id: str = Field(..., description="Model ID")
    severity: AlertSeverity = Field(..., description="Alert severity")
    message: str = Field(..., description="Alert message")
    metric_value: float | None = Field(None, description="Metric value that triggered")
    threshold_value: float | None = Field(None, description="Threshold value")
    acknowledged: bool = Field(default=False, description="Whether acknowledged")
    acknowledged_by: str | None = Field(None, description="Who acknowledged")
    acknowledged_at: datetime | None = Field(None, description="When acknowledged")
    resolved: bool = Field(default=False, description="Whether resolved")
    resolved_at: datetime | None = Field(None, description="When resolved")


class AlertListResponse(ListResponseWrapper):
    """List response for alerts."""

    items: list[AlertInstance]


class AcknowledgeAlertRequest(BaseModel):
    """Request to acknowledge an alert."""

    actor: str = Field(..., description="Who is acknowledging")


# =============================================================================
# Dashboard Schemas
# =============================================================================


class ModelDashboardData(BaseModel):
    """Dashboard data for a single model."""

    model: RegisteredModelResponse = Field(..., description="Model information")
    metrics: MetricsResponse = Field(..., description="Current metrics")
    active_alerts: list[AlertInstance] = Field(default_factory=list, description="Active alerts")
    recent_predictions: int = Field(default=0, description="Predictions in last hour")
    health_status: str = Field(default="healthy", description="Overall health status")


class MonitoringOverview(BaseModel):
    """Overview of all monitored models."""

    total_models: int = Field(default=0, description="Total registered models")
    active_models: int = Field(default=0, description="Models actively receiving predictions")
    degraded_models: int = Field(default=0, description="Models in degraded state")
    total_predictions_24h: int = Field(default=0, description="Total predictions in 24h")
    active_alerts: int = Field(default=0, description="Currently active alerts")
    models_with_drift: int = Field(default=0, description="Models with detected drift")
    avg_latency_ms: float | None = Field(None, description="Average latency across all models")
