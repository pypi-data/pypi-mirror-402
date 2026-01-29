"""Pydantic schemas for Unified Alerts.

Provides schemas for aggregating alerts from all sources:
- Model monitoring alerts
- Drift monitoring alerts
- Anomaly detection alerts
- Validation failures
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


class AlertSource(str, Enum):
    """Sources of alerts in the unified system."""

    MODEL = "model"
    DRIFT = "drift"
    ANOMALY = "anomaly"
    VALIDATION = "validation"


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(str, Enum):
    """Alert status values."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    IGNORED = "ignored"


# =============================================================================
# Unified Alert Schemas
# =============================================================================


class UnifiedAlertBase(BaseSchema):
    """Base unified alert schema."""

    source: AlertSource = Field(..., description="Alert source type")
    source_id: str = Field(..., description="Source-specific alert ID")
    source_name: str = Field(..., description="Name of the source (model, source, etc.)")
    severity: AlertSeverity = Field(..., description="Alert severity")
    status: AlertStatus = Field(default=AlertStatus.OPEN, description="Alert status")
    title: str = Field(..., description="Alert title", min_length=1, max_length=500)
    message: str = Field(..., description="Alert message/description")
    details: dict[str, Any] = Field(default_factory=dict, description="Source-specific details")


class UnifiedAlertResponse(UnifiedAlertBase, IDMixin, TimestampMixin):
    """Schema for unified alert response."""

    acknowledged_at: datetime | None = Field(None, description="When acknowledged")
    acknowledged_by: str | None = Field(None, description="Who acknowledged")
    resolved_at: datetime | None = Field(None, description="When resolved")
    resolved_by: str | None = Field(None, description="Who resolved")
    related_alert_ids: list[str] = Field(default_factory=list, description="IDs of related alerts")


class UnifiedAlertListResponse(ListResponseWrapper):
    """List response for unified alerts."""

    items: list[UnifiedAlertResponse]


# =============================================================================
# Alert Summary Schemas
# =============================================================================


class AlertCountBySeverity(BaseModel):
    """Alert counts by severity."""

    critical: int = Field(default=0, description="Critical alerts")
    high: int = Field(default=0, description="High severity alerts")
    medium: int = Field(default=0, description="Medium severity alerts")
    low: int = Field(default=0, description="Low severity alerts")
    info: int = Field(default=0, description="Info alerts")


class AlertCountBySource(BaseModel):
    """Alert counts by source."""

    model: int = Field(default=0, description="Model monitoring alerts")
    drift: int = Field(default=0, description="Drift monitoring alerts")
    anomaly: int = Field(default=0, description="Anomaly detection alerts")
    validation: int = Field(default=0, description="Validation failure alerts")


class AlertCountByStatus(BaseModel):
    """Alert counts by status."""

    open: int = Field(default=0, description="Open alerts")
    acknowledged: int = Field(default=0, description="Acknowledged alerts")
    resolved: int = Field(default=0, description="Resolved alerts")
    ignored: int = Field(default=0, description="Ignored alerts")


class AlertTrendPoint(BaseModel):
    """Single point in alert trend data."""

    timestamp: datetime = Field(..., description="Time point")
    count: int = Field(default=0, description="Alert count at this time")


class AlertSummary(BaseSchema):
    """Summary statistics for alerts."""

    total_alerts: int = Field(default=0, description="Total active alerts")
    active_alerts: int = Field(default=0, description="Non-resolved alerts")
    by_severity: AlertCountBySeverity = Field(
        default_factory=AlertCountBySeverity,
        description="Counts by severity",
    )
    by_source: AlertCountBySource = Field(
        default_factory=AlertCountBySource,
        description="Counts by source",
    )
    by_status: AlertCountByStatus = Field(
        default_factory=AlertCountByStatus,
        description="Counts by status",
    )
    trend_24h: list[AlertTrendPoint] = Field(
        default_factory=list,
        description="Alert trend over last 24 hours",
    )
    top_sources: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Top sources with most alerts",
    )


# =============================================================================
# Alert Correlation Schemas
# =============================================================================


class AlertCorrelation(BaseSchema):
    """Correlation between alerts."""

    alert_id: str = Field(..., description="Primary alert ID")
    related_alerts: list[UnifiedAlertResponse] = Field(
        default_factory=list,
        description="Related alerts",
    )
    correlation_type: str = Field(..., description="Type of correlation")
    correlation_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Correlation confidence score",
    )
    common_factors: list[str] = Field(
        default_factory=list,
        description="Common factors between alerts",
    )


class AlertCorrelationResponse(BaseSchema):
    """Response for alert correlation query."""

    correlations: list[AlertCorrelation] = Field(
        default_factory=list,
        description="List of correlations",
    )
    total_correlated: int = Field(default=0, description="Total correlated alerts")


# =============================================================================
# Request/Action Schemas
# =============================================================================


class AcknowledgeAlertRequest(BaseModel):
    """Request to acknowledge an alert."""

    actor: str = Field(..., description="Who is acknowledging", min_length=1)
    message: str = Field(default="", description="Optional acknowledgement message")


class ResolveAlertRequest(BaseModel):
    """Request to resolve an alert."""

    actor: str = Field(..., description="Who is resolving", min_length=1)
    message: str = Field(default="", description="Resolution message")


class BulkAlertActionRequest(BaseModel):
    """Request for bulk alert actions."""

    alert_ids: list[str] = Field(..., description="Alert IDs to act on", min_length=1)
    actor: str = Field(..., description="Who is performing the action")
    message: str = Field(default="", description="Optional message")


class BulkAlertActionResponse(BaseModel):
    """Response for bulk alert actions."""

    success_count: int = Field(default=0, description="Number of successful updates")
    failed_count: int = Field(default=0, description="Number of failed updates")
    failed_ids: list[str] = Field(default_factory=list, description="IDs that failed")
