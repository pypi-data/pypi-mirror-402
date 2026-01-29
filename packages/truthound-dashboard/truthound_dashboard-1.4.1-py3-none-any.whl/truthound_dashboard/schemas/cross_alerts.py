"""Cross-alert correlation schemas.

This module defines schemas for cross-feature integration between
Anomaly Detection and Drift Monitoring alerts.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from .base import BaseSchema, IDMixin, TimestampMixin, ListResponseWrapper


# =============================================================================
# Enums and Types
# =============================================================================

AlertType = Literal["anomaly", "drift"]
CorrelationStrength = Literal["strong", "moderate", "weak", "none"]
TriggerDirection = Literal["anomaly_to_drift", "drift_to_anomaly", "bidirectional"]


# =============================================================================
# Cross-Alert Correlation Schemas
# =============================================================================


class CorrelatedAlert(BaseSchema):
    """A single alert that is part of a correlation."""

    alert_id: str = Field(..., description="Alert ID")
    alert_type: AlertType = Field(..., description="Type of alert (anomaly or drift)")
    source_id: str = Field(..., description="Related source ID")
    source_name: str | None = Field(default=None, description="Source name for display")
    severity: str = Field(..., description="Alert severity level")
    message: str = Field(..., description="Alert message")
    created_at: datetime = Field(..., description="When the alert was created")

    # Type-specific fields
    anomaly_rate: float | None = Field(
        default=None,
        description="Anomaly rate (for anomaly alerts)",
    )
    anomaly_count: int | None = Field(
        default=None,
        description="Number of anomalies (for anomaly alerts)",
    )
    drift_percentage: float | None = Field(
        default=None,
        description="Drift percentage (for drift alerts)",
    )
    drifted_columns: list[str] | None = Field(
        default=None,
        description="Drifted columns (for drift alerts)",
    )


class CrossAlertCorrelation(IDMixin, TimestampMixin, BaseSchema):
    """A correlation between anomaly and drift alerts."""

    source_id: str = Field(..., description="Primary source ID")
    source_name: str | None = Field(default=None, description="Source name")

    # Correlation details
    correlation_strength: CorrelationStrength = Field(
        default="moderate",
        description="Strength of the correlation",
    )
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score of the correlation (0-1)",
    )
    time_delta_seconds: int = Field(
        default=0,
        description="Time difference between alerts in seconds",
    )

    # Related alerts
    anomaly_alert: CorrelatedAlert | None = Field(
        default=None,
        description="The anomaly alert in this correlation",
    )
    drift_alert: CorrelatedAlert | None = Field(
        default=None,
        description="The drift alert in this correlation",
    )

    # Analysis
    common_columns: list[str] = Field(
        default_factory=list,
        description="Columns affected by both anomaly and drift",
    )
    suggested_action: str | None = Field(
        default=None,
        description="Suggested remediation action",
    )
    notes: str | None = Field(
        default=None,
        description="Additional notes about the correlation",
    )


class CrossAlertCorrelationListResponse(ListResponseWrapper[CrossAlertCorrelation]):
    """Paginated list of cross-alert correlations."""

    pass


# =============================================================================
# Auto-Trigger Configuration Schemas
# =============================================================================


class AutoTriggerThresholds(BaseSchema):
    """Thresholds for auto-triggering checks."""

    # Anomaly thresholds
    anomaly_rate_threshold: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Minimum anomaly rate to trigger drift check",
    )
    anomaly_count_threshold: int = Field(
        default=10,
        ge=1,
        description="Minimum anomaly count to trigger drift check",
    )

    # Drift thresholds
    drift_percentage_threshold: float = Field(
        default=10.0,
        ge=0.0,
        le=100.0,
        description="Minimum drift percentage to trigger anomaly check",
    )
    drift_columns_threshold: int = Field(
        default=2,
        ge=1,
        description="Minimum drifted columns to trigger anomaly check",
    )


class AutoTriggerConfig(IDMixin, TimestampMixin, BaseSchema):
    """Configuration for auto-triggering cross-feature checks."""

    source_id: str | None = Field(
        default=None,
        description="Source ID (None for global config)",
    )

    # Enable/disable flags
    enabled: bool = Field(
        default=True,
        description="Whether auto-triggering is enabled",
    )
    trigger_drift_on_anomaly: bool = Field(
        default=True,
        description="Trigger drift check when anomaly detected",
    )
    trigger_anomaly_on_drift: bool = Field(
        default=True,
        description="Trigger anomaly check when drift detected",
    )

    # Thresholds
    thresholds: AutoTriggerThresholds = Field(
        default_factory=AutoTriggerThresholds,
        description="Trigger thresholds",
    )

    # Notification preferences
    notify_on_correlation: bool = Field(
        default=True,
        description="Send notification when correlation detected",
    )
    notification_channel_ids: list[str] | None = Field(
        default=None,
        description="Notification channel IDs",
    )

    # Cooldown to prevent alert storms
    cooldown_seconds: int = Field(
        default=300,
        ge=0,
        description="Minimum time between auto-triggered checks (seconds)",
    )
    last_anomaly_trigger_at: datetime | None = Field(
        default=None,
        description="Last time anomaly check was auto-triggered",
    )
    last_drift_trigger_at: datetime | None = Field(
        default=None,
        description="Last time drift check was auto-triggered",
    )


class AutoTriggerConfigCreate(BaseSchema):
    """Schema for creating auto-trigger configuration."""

    source_id: str | None = Field(default=None)
    enabled: bool = Field(default=True)
    trigger_drift_on_anomaly: bool = Field(default=True)
    trigger_anomaly_on_drift: bool = Field(default=True)
    thresholds: AutoTriggerThresholds | None = Field(default=None)
    notify_on_correlation: bool = Field(default=True)
    notification_channel_ids: list[str] | None = Field(default=None)
    cooldown_seconds: int = Field(default=300, ge=0)


class AutoTriggerConfigUpdate(BaseSchema):
    """Schema for updating auto-trigger configuration."""

    enabled: bool | None = Field(default=None)
    trigger_drift_on_anomaly: bool | None = Field(default=None)
    trigger_anomaly_on_drift: bool | None = Field(default=None)
    thresholds: AutoTriggerThresholds | None = Field(default=None)
    notify_on_correlation: bool | None = Field(default=None)
    notification_channel_ids: list[str] | None = Field(default=None)
    cooldown_seconds: int | None = Field(default=None, ge=0)


# =============================================================================
# Auto-Trigger Event Schemas
# =============================================================================


class AutoTriggerEvent(IDMixin, TimestampMixin, BaseSchema):
    """Record of an auto-triggered check."""

    source_id: str = Field(..., description="Source ID")
    trigger_type: TriggerDirection = Field(
        ...,
        description="Direction of the trigger",
    )

    # Trigger source
    trigger_alert_id: str = Field(..., description="ID of the alert that triggered this")
    trigger_alert_type: AlertType = Field(..., description="Type of triggering alert")

    # Result
    result_id: str | None = Field(
        default=None,
        description="ID of the resulting detection/comparison",
    )
    correlation_found: bool = Field(
        default=False,
        description="Whether a correlation was found",
    )
    correlation_id: str | None = Field(
        default=None,
        description="ID of the correlation if found",
    )

    # Status
    status: Literal["pending", "running", "completed", "failed", "skipped"] = Field(
        default="pending",
        description="Status of the auto-triggered check",
    )
    error_message: str | None = Field(
        default=None,
        description="Error message if failed",
    )
    skipped_reason: str | None = Field(
        default=None,
        description="Reason if skipped (e.g., cooldown)",
    )


class AutoTriggerEventListResponse(ListResponseWrapper[AutoTriggerEvent]):
    """Paginated list of auto-trigger events."""

    pass


# =============================================================================
# Summary Schemas
# =============================================================================


class CrossAlertSummary(BaseSchema):
    """Summary of cross-alert correlations."""

    total_correlations: int = Field(
        default=0,
        description="Total number of correlations",
    )
    strong_correlations: int = Field(
        default=0,
        description="Number of strong correlations",
    )
    moderate_correlations: int = Field(
        default=0,
        description="Number of moderate correlations",
    )
    weak_correlations: int = Field(
        default=0,
        description="Number of weak correlations",
    )

    # Recent activity
    recent_correlations_24h: int = Field(
        default=0,
        description="Correlations in the last 24 hours",
    )
    recent_auto_triggers_24h: int = Field(
        default=0,
        description="Auto-triggers in the last 24 hours",
    )

    # Top affected sources
    top_affected_sources: list[dict] = Field(
        default_factory=list,
        description="Sources with most correlations",
    )

    # Auto-trigger stats
    auto_trigger_enabled: bool = Field(
        default=True,
        description="Whether auto-triggering is enabled globally",
    )
    anomaly_to_drift_triggers: int = Field(
        default=0,
        description="Count of anomaly-to-drift triggers",
    )
    drift_to_anomaly_triggers: int = Field(
        default=0,
        description="Count of drift-to-anomaly triggers",
    )
