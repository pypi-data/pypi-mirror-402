"""Trigger system schemas for advanced scheduling.

This module provides schemas for different trigger types:
- Cron: Traditional cron-based scheduling
- Interval: Fixed time interval scheduling
- DataChange: Trigger when data changes by threshold
- Composite: Combine multiple triggers with AND/OR logic

Following truthound library's scheduling capabilities from Phase 7.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TriggerType(str, Enum):
    """Supported trigger types."""

    CRON = "cron"
    INTERVAL = "interval"
    DATA_CHANGE = "data_change"
    COMPOSITE = "composite"
    EVENT = "event"
    MANUAL = "manual"
    WEBHOOK = "webhook"  # External webhook triggers


class TriggerOperator(str, Enum):
    """Operator for composite triggers."""

    AND = "and"
    OR = "or"


class BaseTriggerConfig(BaseModel):
    """Base configuration for all trigger types."""

    model_config = ConfigDict(extra="forbid")

    type: TriggerType = Field(..., description="Trigger type")
    enabled: bool = Field(default=True, description="Whether trigger is enabled")
    description: str | None = Field(default=None, description="Optional description")


class CronTriggerConfig(BaseTriggerConfig):
    """Cron-based trigger configuration.

    Uses standard cron expression format: minute hour day month weekday

    Example:
        "0 0 * * *"  - Daily at midnight
        "0 */6 * * *"  - Every 6 hours
        "0 8 * * 1-5"  - Weekdays at 8am
    """

    type: Literal[TriggerType.CRON] = TriggerType.CRON
    expression: str = Field(
        ...,
        description="Cron expression (minute hour day month weekday)",
        examples=["0 0 * * *", "0 */6 * * *", "0 8 * * 1-5"],
    )
    timezone: str = Field(default="UTC", description="Timezone for cron schedule")

    @field_validator("expression")
    @classmethod
    def validate_cron_expression(cls, v: str) -> str:
        """Validate cron expression format."""
        parts = v.split()
        if len(parts) != 5:
            raise ValueError(
                "Cron expression must have 5 parts: minute hour day month weekday"
            )
        return v


class IntervalTriggerConfig(BaseTriggerConfig):
    """Interval-based trigger configuration.

    Triggers at fixed time intervals.

    Example:
        seconds=3600 - Every hour
        minutes=30 - Every 30 minutes
        hours=6 - Every 6 hours
    """

    type: Literal[TriggerType.INTERVAL] = TriggerType.INTERVAL
    seconds: int | None = Field(default=None, ge=1, description="Interval in seconds")
    minutes: int | None = Field(default=None, ge=1, description="Interval in minutes")
    hours: int | None = Field(default=None, ge=1, description="Interval in hours")
    days: int | None = Field(default=None, ge=1, description="Interval in days")

    @field_validator("seconds", "minutes", "hours", "days", mode="after")
    @classmethod
    def at_least_one_interval(cls, v: int | None, info) -> int | None:
        """Ensure at least one interval is specified."""
        return v

    def get_total_seconds(self) -> int:
        """Calculate total interval in seconds."""
        total = 0
        if self.seconds:
            total += self.seconds
        if self.minutes:
            total += self.minutes * 60
        if self.hours:
            total += self.hours * 3600
        if self.days:
            total += self.days * 86400
        return total or 3600  # Default to 1 hour


class DataChangeTriggerConfig(BaseTriggerConfig):
    """Data change trigger configuration.

    Triggers when profile changes exceed a threshold percentage.
    Monitors row count, column statistics, or schema changes.

    Example:
        change_threshold=0.05 - Trigger when >= 5% change detected
        metrics=["row_count", "null_percentage"] - What to monitor
    """

    type: Literal[TriggerType.DATA_CHANGE] = TriggerType.DATA_CHANGE
    change_threshold: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Minimum change percentage to trigger (0.0-1.0)",
    )
    metrics: list[str] = Field(
        default_factory=lambda: ["row_count", "null_percentage", "distinct_count"],
        description="Metrics to monitor for changes",
    )
    baseline_profile_id: str | None = Field(
        default=None, description="Specific baseline profile ID to compare against"
    )
    use_latest_baseline: bool = Field(
        default=True, description="Use the most recent profile as baseline"
    )
    check_interval_minutes: int = Field(
        default=60, ge=1, description="How often to check for changes (minutes)"
    )
    priority: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Evaluation priority (1=highest, 10=lowest)",
    )
    auto_profile: bool = Field(
        default=True,
        description="Automatically run profile before comparison",
    )
    cooldown_minutes: int = Field(
        default=15,
        ge=0,
        description="Minimum time between triggers (prevents rapid re-triggering)",
    )

    @field_validator("metrics")
    @classmethod
    def validate_metrics(cls, v: list[str]) -> list[str]:
        """Validate metric names."""
        valid_metrics = {
            "row_count",
            "column_count",
            "null_percentage",
            "distinct_count",
            "mean",
            "std",
            "min",
            "max",
            "schema_hash",
        }
        for metric in v:
            if metric not in valid_metrics:
                raise ValueError(
                    f"Invalid metric: {metric}. Valid: {valid_metrics}"
                )
        return v


class EventTriggerConfig(BaseTriggerConfig):
    """Event-based trigger configuration.

    Triggers in response to specific system events.

    Example:
        event_types=["schema_changed", "drift_detected"]
    """

    type: Literal[TriggerType.EVENT] = TriggerType.EVENT
    event_types: list[str] = Field(
        ...,
        min_length=1,
        description="Event types that trigger execution",
    )
    source_filter: list[str] | None = Field(
        default=None, description="Optional source IDs to filter events"
    )

    @field_validator("event_types")
    @classmethod
    def validate_event_types(cls, v: list[str]) -> list[str]:
        """Validate event type names."""
        valid_events = {
            "validation_completed",
            "validation_failed",
            "schema_changed",
            "drift_detected",
            "profile_updated",
            "source_created",
            "source_updated",
        }
        for event in v:
            if event not in valid_events:
                raise ValueError(f"Invalid event type: {event}. Valid: {valid_events}")
        return v


class CompositeTriggerConfig(BaseTriggerConfig):
    """Composite trigger configuration.

    Combines multiple triggers with AND/OR logic.

    Example (AND):
        triggers=[CronTrigger, DataChangeTrigger]
        operator="and"
        -> Triggers only when both conditions are met

    Example (OR):
        triggers=[IntervalTrigger, EventTrigger]
        operator="or"
        -> Triggers when any condition is met
    """

    type: Literal[TriggerType.COMPOSITE] = TriggerType.COMPOSITE
    operator: TriggerOperator = Field(
        default=TriggerOperator.AND,
        description="How to combine triggers (and/or)",
    )
    triggers: list[dict[str, Any]] = Field(
        ...,
        min_length=2,
        description="List of trigger configurations to combine",
    )

    @field_validator("triggers")
    @classmethod
    def validate_triggers(cls, v: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate nested trigger configurations."""
        if len(v) < 2:
            raise ValueError("Composite trigger requires at least 2 triggers")

        for trigger in v:
            if "type" not in trigger:
                raise ValueError("Each trigger must have a 'type' field")
            # Prevent deeply nested composites for simplicity
            if trigger.get("type") == TriggerType.COMPOSITE:
                raise ValueError("Nested composite triggers are not supported")

        return v


class ManualTriggerConfig(BaseTriggerConfig):
    """Manual trigger configuration.

    Only triggers when explicitly invoked via API.
    """

    type: Literal[TriggerType.MANUAL] = TriggerType.MANUAL


class WebhookTriggerConfig(BaseTriggerConfig):
    """Webhook trigger configuration.

    Triggers when an external system sends a webhook request.
    Supports secret-based authentication and payload validation.

    Example:
        webhook_secret="my_secret_key"
        allowed_sources=["airflow", "dagster", "prefect"]
    """

    type: Literal[TriggerType.WEBHOOK] = TriggerType.WEBHOOK
    webhook_secret: str | None = Field(
        default=None,
        description="Secret key for webhook authentication (HMAC-SHA256)",
    )
    allowed_sources: list[str] | None = Field(
        default=None,
        description="Optional list of allowed source identifiers",
    )
    payload_filters: dict[str, Any] | None = Field(
        default=None,
        description="JSON path filters to match against payload",
    )
    require_signature: bool = Field(
        default=False,
        description="Require X-Webhook-Signature header validation",
    )


# Union type for all trigger configurations
TriggerConfig = (
    CronTriggerConfig
    | IntervalTriggerConfig
    | DataChangeTriggerConfig
    | EventTriggerConfig
    | CompositeTriggerConfig
    | ManualTriggerConfig
    | WebhookTriggerConfig
)


class TriggerState(BaseModel):
    """Current state of a trigger."""

    model_config = ConfigDict(from_attributes=True)

    type: TriggerType
    enabled: bool
    last_triggered_at: datetime | None = None
    next_trigger_at: datetime | None = None
    trigger_count: int = 0
    last_check_result: dict[str, Any] | None = None
    error: str | None = None


class TriggerEvaluationResult(BaseModel):
    """Result of evaluating a trigger condition."""

    should_trigger: bool = Field(..., description="Whether trigger condition is met")
    reason: str = Field(..., description="Explanation of the evaluation result")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional details about the evaluation"
    )
    next_check_at: datetime | None = Field(
        default=None, description="Suggested next check time"
    )


# =============================================================================
# Request/Response schemas
# =============================================================================


class TriggerConfigCreate(BaseModel):
    """Schema for creating trigger configuration."""

    model_config = ConfigDict(extra="forbid")

    type: TriggerType
    config: dict[str, Any] = Field(..., description="Trigger-specific configuration")

    def to_trigger_config(self) -> TriggerConfig:
        """Convert to specific trigger config type."""
        config_with_type = {"type": self.type, **self.config}

        match self.type:
            case TriggerType.CRON:
                return CronTriggerConfig(**config_with_type)
            case TriggerType.INTERVAL:
                return IntervalTriggerConfig(**config_with_type)
            case TriggerType.DATA_CHANGE:
                return DataChangeTriggerConfig(**config_with_type)
            case TriggerType.EVENT:
                return EventTriggerConfig(**config_with_type)
            case TriggerType.COMPOSITE:
                return CompositeTriggerConfig(**config_with_type)
            case TriggerType.MANUAL:
                return ManualTriggerConfig(**config_with_type)
            case TriggerType.WEBHOOK:
                return WebhookTriggerConfig(**config_with_type)
            case _:
                raise ValueError(f"Unknown trigger type: {self.type}")


class TriggerResponse(BaseModel):
    """Response schema for trigger information."""

    model_config = ConfigDict(from_attributes=True)

    type: TriggerType
    config: dict[str, Any]
    state: TriggerState | None = None


def parse_trigger_config(data: dict[str, Any]) -> TriggerConfig:
    """Parse trigger configuration from dict.

    Args:
        data: Dictionary containing trigger configuration.

    Returns:
        Appropriate TriggerConfig subclass instance.

    Raises:
        ValueError: If trigger type is invalid or config is malformed.
    """
    trigger_type = data.get("type")
    if not trigger_type:
        raise ValueError("Trigger config must have 'type' field")

    try:
        trigger_type_enum = TriggerType(trigger_type)
    except ValueError:
        raise ValueError(f"Invalid trigger type: {trigger_type}")

    match trigger_type_enum:
        case TriggerType.CRON:
            return CronTriggerConfig(**data)
        case TriggerType.INTERVAL:
            return IntervalTriggerConfig(**data)
        case TriggerType.DATA_CHANGE:
            return DataChangeTriggerConfig(**data)
        case TriggerType.EVENT:
            return EventTriggerConfig(**data)
        case TriggerType.COMPOSITE:
            return CompositeTriggerConfig(**data)
        case TriggerType.MANUAL:
            return ManualTriggerConfig(**data)
        case TriggerType.WEBHOOK:
            return WebhookTriggerConfig(**data)
        case _:
            raise ValueError(f"Unknown trigger type: {trigger_type}")


# =============================================================================
# Trigger Monitoring Schemas
# =============================================================================


class TriggerCheckStatus(BaseModel):
    """Status of a single trigger check."""

    schedule_id: str
    schedule_name: str
    trigger_type: TriggerType
    last_check_at: datetime | None = None
    next_check_at: datetime | None = None
    last_triggered_at: datetime | None = None
    check_count: int = 0
    trigger_count: int = 0
    last_evaluation: TriggerEvaluationResult | None = None
    is_due_for_check: bool = False
    priority: int = 5
    cooldown_remaining_seconds: int = 0


class TriggerMonitoringStats(BaseModel):
    """Aggregated statistics for trigger monitoring."""

    total_schedules: int = 0
    active_data_change_triggers: int = 0
    active_webhook_triggers: int = 0
    active_composite_triggers: int = 0
    total_checks_last_hour: int = 0
    total_triggers_last_hour: int = 0
    average_check_interval_seconds: float = 0.0
    next_scheduled_check_at: datetime | None = None


class TriggerMonitoringResponse(BaseModel):
    """Response for trigger monitoring status endpoint."""

    stats: TriggerMonitoringStats
    schedules: list[TriggerCheckStatus] = Field(default_factory=list)
    checker_running: bool = False
    checker_interval_seconds: int = 300
    last_checker_run_at: datetime | None = None


class WebhookTriggerRequest(BaseModel):
    """Request schema for incoming webhook triggers."""

    source: str = Field(..., description="Source identifier (e.g., 'airflow', 'dagster')")
    event_type: str = Field(
        default="data_updated",
        description="Type of event (data_updated, job_completed, etc.)",
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional event payload data",
    )
    schedule_id: str | None = Field(
        default=None,
        description="Specific schedule to trigger (optional)",
    )
    source_id: str | None = Field(
        default=None,
        description="Data source ID to trigger (optional)",
    )
    timestamp: datetime | None = Field(
        default=None,
        description="Event timestamp (defaults to now)",
    )


class WebhookTriggerResponse(BaseModel):
    """Response schema for webhook trigger endpoint."""

    accepted: bool
    triggered_schedules: list[str] = Field(default_factory=list)
    message: str
    request_id: str
