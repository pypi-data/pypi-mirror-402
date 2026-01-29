"""Pydantic schemas for advanced notification features.

This module provides schemas for:
- Routing rules (11 rule types + combinators)
- Deduplication configuration (4 strategies, 6 policies)
- Throttling configuration
- Escalation policies and incidents
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from .base import BaseSchema, IDMixin, ListResponseWrapper, TimestampMixin
from ..core.validation_limits import (
    get_deduplication_limits,
    get_escalation_limits,
    get_throttling_limits,
)


# =============================================================================
# Enums
# =============================================================================


class RuleType(str, Enum):
    """Available routing rule types."""

    SEVERITY = "severity"
    ISSUE_COUNT = "issue_count"
    PASS_RATE = "pass_rate"
    TIME_WINDOW = "time_window"
    TAG = "tag"
    DATA_ASSET = "data_asset"
    METADATA = "metadata"
    STATUS = "status"
    ERROR = "error"
    ALWAYS = "always"
    NEVER = "never"
    # Combinators
    ALL_OF = "all_of"
    ANY_OF = "any_of"
    NOT = "not"


class DeduplicationStrategy(str, Enum):
    """Deduplication window strategies."""

    SLIDING = "sliding"
    TUMBLING = "tumbling"
    SESSION = "session"
    ADAPTIVE = "adaptive"


class DeduplicationPolicy(str, Enum):
    """Deduplication policies."""

    NONE = "none"
    BASIC = "basic"
    SEVERITY = "severity"
    ISSUE_BASED = "issue_based"
    STRICT = "strict"
    CUSTOM = "custom"


class EscalationState(str, Enum):
    """Escalation incident states."""

    PENDING = "pending"
    TRIGGERED = "triggered"
    ACKNOWLEDGED = "acknowledged"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


class TargetType(str, Enum):
    """Escalation target types."""

    USER = "user"
    GROUP = "group"
    ONCALL = "oncall"
    CHANNEL = "channel"


# =============================================================================
# Routing Rules Schemas
# =============================================================================


class CombinatorType(str, Enum):
    """Available combinator types for combining rules."""

    ALL_OF = "all_of"
    ANY_OF = "any_of"
    NOT = "not"


class RuleConfig(BaseModel):
    """Base configuration for a routing rule."""

    type: str = Field(..., description="Rule type")
    params: dict[str, Any] = Field(default_factory=dict, description="Rule parameters")


class NestedRuleConfig(BaseModel):
    """Nested rule configuration supporting combinators.

    Supports both simple rules and combinator rules (all_of, any_of, not).
    For simple rules, use `type` and `params`.
    For combinator rules, use `type` and `rules` (for all_of/any_of) or `rule` (for not).
    """

    type: str = Field(..., description="Rule type or combinator type")
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="Rule parameters (for non-combinator rules)",
    )
    rules: list["NestedRuleConfig"] | None = Field(
        None,
        description="Nested rules for all_of/any_of combinators",
    )
    rule: "NestedRuleConfig | None" = Field(
        None,
        description="Nested rule for 'not' combinator",
    )

    def is_combinator(self) -> bool:
        """Check if this is a combinator rule."""
        return self.type in (
            CombinatorType.ALL_OF.value,
            CombinatorType.ANY_OF.value,
            CombinatorType.NOT.value,
        )


# Rebuild for self-referencing model
NestedRuleConfig.model_rebuild()


class RuleValidationResult(BaseModel):
    """Result of rule configuration validation."""

    valid: bool = Field(..., description="Whether the configuration is valid")
    errors: list[str] = Field(
        default_factory=list,
        description="List of validation errors",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="List of validation warnings",
    )
    rule_count: int = Field(
        default=0,
        description="Total number of rules (including nested)",
    )
    max_depth: int = Field(
        default=0,
        description="Maximum nesting depth",
    )
    circular_paths: list[str] = Field(
        default_factory=list,
        description="Paths of detected circular references (if any)",
    )


class RoutingRuleBase(BaseSchema):
    """Base routing rule schema."""

    name: str = Field(..., description="Rule name", min_length=1, max_length=255)
    rule_config: dict[str, Any] = Field(..., description="Rule configuration JSON")
    actions: list[str] = Field(..., description="Channel IDs to notify", min_length=1)
    priority: int = Field(default=0, description="Priority (higher = more important)")
    is_active: bool = Field(default=True, description="Whether rule is active")
    stop_on_match: bool = Field(default=False, description="Stop processing after match")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class RoutingRuleCreate(RoutingRuleBase):
    """Schema for creating a routing rule."""

    pass


class RoutingRuleUpdate(BaseSchema):
    """Schema for updating a routing rule."""

    name: str | None = Field(None, description="Rule name", min_length=1, max_length=255)
    rule_config: dict[str, Any] | None = Field(None, description="Rule configuration JSON")
    actions: list[str] | None = Field(None, description="Channel IDs to notify", min_length=1)
    priority: int | None = Field(None, description="Priority")
    is_active: bool | None = Field(None, description="Whether rule is active")
    stop_on_match: bool | None = Field(None, description="Stop processing after match")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")


class RoutingRuleResponse(RoutingRuleBase, IDMixin, TimestampMixin):
    """Schema for routing rule response."""

    pass


class RoutingRuleListResponse(ListResponseWrapper):
    """Schema for routing rule list response."""

    items: list[RoutingRuleResponse]


class RuleTypeInfo(BaseModel):
    """Information about a rule type."""

    type: str = Field(..., description="Rule type identifier")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Rule description")
    param_schema: dict[str, Any] = Field(..., description="Parameter schema")


class RuleTypesResponse(BaseModel):
    """Response for available rule types."""

    rule_types: list[RuleTypeInfo]


# =============================================================================
# Deduplication Schemas
# =============================================================================


class DeduplicationConfigBase(BaseSchema):
    """Base deduplication configuration schema.

    Validation:
        - window_seconds: Must be between 1 and 86400 seconds (24 hours).
          These limits are configurable via environment variables:
          - TRUTHOUND_DEDUP_WINDOW_MIN
          - TRUTHOUND_DEDUP_WINDOW_MAX

    DoS Prevention:
        - Minimum window prevents excessive memory churn from tiny windows.
        - Maximum window prevents memory exhaustion from excessively long windows.
    """

    name: str = Field(..., description="Configuration name", min_length=1, max_length=255)
    strategy: DeduplicationStrategy = Field(
        default=DeduplicationStrategy.SLIDING,
        description="Window strategy",
    )
    policy: DeduplicationPolicy = Field(
        default=DeduplicationPolicy.BASIC,
        description="Deduplication policy",
    )
    window_seconds: int = Field(
        default=300,
        description="Window duration in seconds (1-86400, configurable via env vars)",
        ge=1,
        le=86400,
    )
    is_active: bool = Field(default=True, description="Whether config is active")

    @field_validator("window_seconds")
    @classmethod
    def validate_window_seconds(cls, v: int) -> int:
        """Validate window_seconds against configurable limits.

        Args:
            v: Window duration in seconds.

        Returns:
            Validated window duration.

        Raises:
            ValueError: If window_seconds is outside allowed range.
        """
        limits = get_deduplication_limits()
        valid, error = limits.validate_window_seconds(v)
        if not valid:
            raise ValueError(error)
        return v


class DeduplicationConfigCreate(DeduplicationConfigBase):
    """Schema for creating deduplication config."""

    pass


class DeduplicationConfigUpdate(BaseSchema):
    """Schema for updating deduplication config."""

    name: str | None = Field(None, description="Configuration name")
    strategy: DeduplicationStrategy | None = Field(None, description="Window strategy")
    policy: DeduplicationPolicy | None = Field(None, description="Deduplication policy")
    window_seconds: int | None = Field(None, description="Window duration in seconds")
    is_active: bool | None = Field(None, description="Whether config is active")

    @field_validator("window_seconds")
    @classmethod
    def validate_window_seconds(cls, v: int | None) -> int | None:
        """Validate window_seconds against configurable limits.

        Args:
            v: Window duration in seconds or None.

        Returns:
            Validated window duration or None.

        Raises:
            ValueError: If window_seconds is outside allowed range.
        """
        if v is None:
            return v
        limits = get_deduplication_limits()
        valid, error = limits.validate_window_seconds(v)
        if not valid:
            raise ValueError(error)
        return v


class DeduplicationConfigResponse(DeduplicationConfigBase, IDMixin, TimestampMixin):
    """Schema for deduplication config response."""

    pass


class DeduplicationConfigListResponse(ListResponseWrapper):
    """Schema for deduplication config list response."""

    items: list[DeduplicationConfigResponse]


class DeduplicationStats(BaseModel):
    """Deduplication statistics."""

    total_received: int = Field(default=0, description="Total notifications received")
    total_deduplicated: int = Field(default=0, description="Total notifications deduplicated")
    total_passed: int = Field(default=0, description="Total notifications passed through")
    dedup_rate: float = Field(default=0.0, description="Deduplication rate percentage")
    active_fingerprints: int = Field(default=0, description="Active fingerprints in window")


# =============================================================================
# Throttling Schemas
# =============================================================================


class ThrottlingConfigBase(BaseSchema):
    """Base throttling configuration schema.

    Validation:
        - per_minute: Must be between 1 and 10000 (configurable).
        - per_hour: Must be between 1 and 100000 (configurable).
        - per_day: Must be between 1 and 1000000 (configurable).
        - burst_allowance: Must be between 1.0 and 10.0 (configurable).

    DoS Prevention:
        - Upper limits prevent unreasonable rate limits that could
          consume excessive memory or processing resources.
        - Lower limits ensure at least one notification is allowed.

    Environment Variables:
        - TRUTHOUND_THROTTLE_PER_MINUTE_MAX
        - TRUTHOUND_THROTTLE_PER_HOUR_MAX
        - TRUTHOUND_THROTTLE_PER_DAY_MAX
        - TRUTHOUND_THROTTLE_BURST_MIN
        - TRUTHOUND_THROTTLE_BURST_MAX
    """

    name: str = Field(..., description="Configuration name", min_length=1, max_length=255)
    per_minute: int | None = Field(
        None,
        description="Max notifications per minute (1-10000, configurable)",
        ge=1,
    )
    per_hour: int | None = Field(
        None,
        description="Max notifications per hour (1-100000, configurable)",
        ge=1,
    )
    per_day: int | None = Field(
        None,
        description="Max notifications per day (1-1000000, configurable)",
        ge=1,
    )
    burst_allowance: float = Field(
        default=1.5,
        description="Burst allowance factor (1.0-10.0, configurable)",
        ge=1.0,
        le=10.0,
    )
    channel_id: str | None = Field(None, description="Channel ID (null = global)")
    is_active: bool = Field(default=True, description="Whether config is active")

    @field_validator("per_minute")
    @classmethod
    def validate_per_minute(cls, v: int | None) -> int | None:
        """Validate per_minute against configurable limits.

        Args:
            v: Max notifications per minute or None.

        Returns:
            Validated value or None.

        Raises:
            ValueError: If value exceeds maximum limit.
        """
        if v is None:
            return v
        limits = get_throttling_limits()
        if v > limits.per_minute_max:
            raise ValueError(
                f"per_minute must not exceed {limits.per_minute_max}, got {v}"
            )
        return v

    @field_validator("per_hour")
    @classmethod
    def validate_per_hour(cls, v: int | None) -> int | None:
        """Validate per_hour against configurable limits.

        Args:
            v: Max notifications per hour or None.

        Returns:
            Validated value or None.

        Raises:
            ValueError: If value exceeds maximum limit.
        """
        if v is None:
            return v
        limits = get_throttling_limits()
        if v > limits.per_hour_max:
            raise ValueError(
                f"per_hour must not exceed {limits.per_hour_max}, got {v}"
            )
        return v

    @field_validator("per_day")
    @classmethod
    def validate_per_day(cls, v: int | None) -> int | None:
        """Validate per_day against configurable limits.

        Args:
            v: Max notifications per day or None.

        Returns:
            Validated value or None.

        Raises:
            ValueError: If value exceeds maximum limit.
        """
        if v is None:
            return v
        limits = get_throttling_limits()
        if v > limits.per_day_max:
            raise ValueError(
                f"per_day must not exceed {limits.per_day_max}, got {v}"
            )
        return v

    @field_validator("burst_allowance")
    @classmethod
    def validate_burst_allowance(cls, v: float) -> float:
        """Validate burst_allowance against configurable limits.

        Args:
            v: Burst allowance factor.

        Returns:
            Validated burst allowance.

        Raises:
            ValueError: If value is outside allowed range.
        """
        limits = get_throttling_limits()
        valid, error = limits.validate_burst_allowance(v)
        if not valid:
            raise ValueError(error)
        return v

    @model_validator(mode="after")
    def validate_at_least_one_limit(self) -> "ThrottlingConfigBase":
        """Ensure at least one rate limit is specified.

        Returns:
            Validated model instance.

        Raises:
            ValueError: If no rate limits are specified.
        """
        if (
            self.per_minute is None
            and self.per_hour is None
            and self.per_day is None
        ):
            raise ValueError(
                "At least one rate limit must be specified: per_minute, per_hour, or per_day"
            )
        return self


class ThrottlingConfigCreate(ThrottlingConfigBase):
    """Schema for creating throttling config."""

    pass


class ThrottlingConfigUpdate(BaseSchema):
    """Schema for updating throttling config."""

    name: str | None = Field(None, description="Configuration name")
    per_minute: int | None = Field(None, description="Max notifications per minute", ge=1)
    per_hour: int | None = Field(None, description="Max notifications per hour", ge=1)
    per_day: int | None = Field(None, description="Max notifications per day", ge=1)
    burst_allowance: float | None = Field(None, description="Burst allowance factor")
    channel_id: str | None = Field(None, description="Channel ID")
    is_active: bool | None = Field(None, description="Whether config is active")

    @field_validator("per_minute")
    @classmethod
    def validate_per_minute(cls, v: int | None) -> int | None:
        """Validate per_minute against configurable limits."""
        if v is None:
            return v
        limits = get_throttling_limits()
        if v > limits.per_minute_max:
            raise ValueError(
                f"per_minute must not exceed {limits.per_minute_max}, got {v}"
            )
        return v

    @field_validator("per_hour")
    @classmethod
    def validate_per_hour(cls, v: int | None) -> int | None:
        """Validate per_hour against configurable limits."""
        if v is None:
            return v
        limits = get_throttling_limits()
        if v > limits.per_hour_max:
            raise ValueError(
                f"per_hour must not exceed {limits.per_hour_max}, got {v}"
            )
        return v

    @field_validator("per_day")
    @classmethod
    def validate_per_day(cls, v: int | None) -> int | None:
        """Validate per_day against configurable limits."""
        if v is None:
            return v
        limits = get_throttling_limits()
        if v > limits.per_day_max:
            raise ValueError(
                f"per_day must not exceed {limits.per_day_max}, got {v}"
            )
        return v

    @field_validator("burst_allowance")
    @classmethod
    def validate_burst_allowance(cls, v: float | None) -> float | None:
        """Validate burst_allowance against configurable limits."""
        if v is None:
            return v
        limits = get_throttling_limits()
        valid, error = limits.validate_burst_allowance(v)
        if not valid:
            raise ValueError(error)
        return v


class ThrottlingConfigResponse(ThrottlingConfigBase, IDMixin, TimestampMixin):
    """Schema for throttling config response."""

    pass


class ThrottlingConfigListResponse(ListResponseWrapper):
    """Schema for throttling config list response."""

    items: list[ThrottlingConfigResponse]


class ThrottlingStats(BaseModel):
    """Throttling statistics."""

    total_received: int = Field(default=0, description="Total notifications received")
    total_throttled: int = Field(default=0, description="Total notifications throttled")
    total_passed: int = Field(default=0, description="Total notifications passed through")
    throttle_rate: float = Field(default=0.0, description="Throttle rate percentage")
    current_window_count: int = Field(default=0, description="Count in current window")


# =============================================================================
# Escalation Schemas
# =============================================================================


class EscalationTargetBase(BaseModel):
    """Escalation target schema."""

    type: TargetType = Field(..., description="Target type")
    identifier: str = Field(..., description="Target identifier (email, group name, etc.)")
    channel: str = Field(..., description="Notification channel ID")


class EscalationLevelBase(BaseModel):
    """Escalation level schema.

    Validation:
        - level: Must be at least 1.
        - delay_minutes: Must be between 0 and 10080 (7 days, configurable).
        - targets: At least one target must be specified.

    DoS Prevention:
        - Maximum delay prevents excessively long escalation windows.
        - Configurable via TRUTHOUND_ESCALATION_DELAY_MAX environment variable.
    """

    level: int = Field(..., description="Level number (1 = first)", ge=1)
    delay_minutes: int = Field(
        ...,
        description="Delay before escalating to next level (0-10080 minutes, configurable)",
        ge=0,
    )
    targets: list[EscalationTargetBase] = Field(
        ...,
        description="Targets to notify at this level",
        min_length=1,
    )

    @field_validator("delay_minutes")
    @classmethod
    def validate_delay_minutes(cls, v: int) -> int:
        """Validate delay_minutes against configurable limits.

        Args:
            v: Delay in minutes.

        Returns:
            Validated delay value.

        Raises:
            ValueError: If delay exceeds maximum limit.
        """
        limits = get_escalation_limits()
        valid, error = limits.validate_delay_minutes(v)
        if not valid:
            raise ValueError(error)
        return v


class EscalationPolicyBase(BaseSchema):
    """Base escalation policy schema.

    Validation:
        - levels: Must have at least 1 level and at most 20 levels (configurable).
        - max_escalations: Must be between 1 and 100 (configurable).

    DoS Prevention:
        - Maximum levels prevents excessive escalation chains.
        - Maximum escalations prevents infinite retry loops.

    Environment Variables:
        - TRUTHOUND_ESCALATION_MAX_LEVELS
        - TRUTHOUND_ESCALATION_MAX_ESCALATIONS_MIN
        - TRUTHOUND_ESCALATION_MAX_ESCALATIONS_MAX
    """

    name: str = Field(..., description="Policy name", min_length=1, max_length=255)
    description: str = Field(default="", description="Policy description")
    levels: list[EscalationLevelBase] = Field(
        ...,
        description="Escalation levels (1-20 levels, configurable)",
        min_length=1,
    )
    auto_resolve_on_success: bool = Field(
        default=True,
        description="Auto-resolve when validation passes",
    )
    max_escalations: int = Field(
        default=3,
        description="Maximum escalation attempts (1-100, configurable)",
        ge=1,
    )
    is_active: bool = Field(default=True, description="Whether policy is active")

    @field_validator("levels")
    @classmethod
    def validate_levels(cls, v: list[EscalationLevelBase]) -> list[EscalationLevelBase]:
        """Validate escalation levels against configurable limits.

        Args:
            v: List of escalation levels.

        Returns:
            Validated levels list.

        Raises:
            ValueError: If too many levels or invalid level numbers.
        """
        limits = get_escalation_limits()
        if len(v) > limits.max_levels:
            raise ValueError(
                f"Cannot have more than {limits.max_levels} escalation levels, "
                f"got {len(v)}"
            )

        # Validate level numbers are sequential and start from 1
        level_numbers = [level.level for level in v]
        expected_levels = list(range(1, len(v) + 1))
        if sorted(level_numbers) != expected_levels:
            raise ValueError(
                f"Level numbers must be sequential starting from 1, "
                f"got {sorted(level_numbers)}"
            )

        return v

    @field_validator("max_escalations")
    @classmethod
    def validate_max_escalations(cls, v: int) -> int:
        """Validate max_escalations against configurable limits.

        Args:
            v: Maximum escalation attempts.

        Returns:
            Validated max_escalations value.

        Raises:
            ValueError: If value is outside allowed range.
        """
        limits = get_escalation_limits()
        valid, error = limits.validate_max_escalations(v)
        if not valid:
            raise ValueError(error)
        return v


class EscalationPolicyCreate(EscalationPolicyBase):
    """Schema for creating escalation policy."""

    pass


class EscalationPolicyUpdate(BaseSchema):
    """Schema for updating escalation policy."""

    name: str | None = Field(None, description="Policy name")
    description: str | None = Field(None, description="Policy description")
    levels: list[EscalationLevelBase] | None = Field(None, description="Escalation levels")
    auto_resolve_on_success: bool | None = Field(None, description="Auto-resolve on success")
    max_escalations: int | None = Field(None, description="Maximum escalation attempts", ge=1)
    is_active: bool | None = Field(None, description="Whether policy is active")

    @field_validator("levels")
    @classmethod
    def validate_levels(
        cls, v: list[EscalationLevelBase] | None
    ) -> list[EscalationLevelBase] | None:
        """Validate escalation levels against configurable limits."""
        if v is None:
            return v
        limits = get_escalation_limits()
        if len(v) > limits.max_levels:
            raise ValueError(
                f"Cannot have more than {limits.max_levels} escalation levels, "
                f"got {len(v)}"
            )
        if len(v) > 0:
            level_numbers = [level.level for level in v]
            expected_levels = list(range(1, len(v) + 1))
            if sorted(level_numbers) != expected_levels:
                raise ValueError(
                    f"Level numbers must be sequential starting from 1, "
                    f"got {sorted(level_numbers)}"
                )
        return v

    @field_validator("max_escalations")
    @classmethod
    def validate_max_escalations(cls, v: int | None) -> int | None:
        """Validate max_escalations against configurable limits."""
        if v is None:
            return v
        limits = get_escalation_limits()
        valid, error = limits.validate_max_escalations(v)
        if not valid:
            raise ValueError(error)
        return v


class EscalationPolicyResponse(EscalationPolicyBase, IDMixin, TimestampMixin):
    """Schema for escalation policy response."""

    pass


class EscalationPolicyListResponse(ListResponseWrapper):
    """Schema for escalation policy list response."""

    items: list[EscalationPolicyResponse]


class EscalationEventBase(BaseModel):
    """Escalation event (state transition history)."""

    from_state: str | None = Field(None, description="Previous state")
    to_state: str = Field(..., description="New state")
    actor: str | None = Field(None, description="Who triggered the transition")
    message: str = Field(default="", description="Event message")
    timestamp: datetime = Field(..., description="When the event occurred")


class EscalationIncidentBase(BaseSchema):
    """Base escalation incident schema."""

    policy_id: str = Field(..., description="Escalation policy ID")
    incident_ref: str = Field(..., description="External reference (e.g., validation ID)")
    state: EscalationState = Field(
        default=EscalationState.PENDING,
        description="Current state",
    )
    current_level: int = Field(default=1, description="Current escalation level")
    escalation_count: int = Field(default=0, description="Number of escalations")
    context: dict[str, Any] = Field(default_factory=dict, description="Incident context")
    acknowledged_by: str | None = Field(None, description="Who acknowledged")
    acknowledged_at: datetime | None = Field(None, description="When acknowledged")
    resolved_by: str | None = Field(None, description="Who resolved")
    resolved_at: datetime | None = Field(None, description="When resolved")
    next_escalation_at: datetime | None = Field(None, description="Next escalation time")


class EscalationIncidentResponse(EscalationIncidentBase, IDMixin, TimestampMixin):
    """Schema for escalation incident response."""

    events: list[EscalationEventBase] = Field(
        default_factory=list,
        description="State transition history",
    )


class EscalationIncidentListResponse(ListResponseWrapper):
    """Schema for escalation incident list response."""

    items: list[EscalationIncidentResponse]


class AcknowledgeRequest(BaseModel):
    """Request to acknowledge an incident."""

    actor: str = Field(..., description="Who is acknowledging")
    message: str = Field(default="", description="Acknowledgement message")


class ResolveRequest(BaseModel):
    """Request to resolve an incident."""

    actor: str | None = Field(None, description="Who is resolving (null for auto)")
    message: str = Field(default="", description="Resolution message")


class EscalationStats(BaseModel):
    """Escalation statistics."""

    total_incidents: int = Field(default=0, description="Total incidents")
    by_state: dict[str, int] = Field(default_factory=dict, description="Count by state")
    active_count: int = Field(default=0, description="Active (non-resolved) incidents")
    total_policies: int = Field(default=0, description="Total policies")
    avg_resolution_time_minutes: float | None = Field(
        None,
        description="Average resolution time in minutes",
    )


# =============================================================================
# Enhanced Stats with Time Range and Caching
# =============================================================================


class TimeRangeFilter(BaseModel):
    """Time range filter for stats queries."""

    start_time: datetime | None = Field(
        None,
        description="Start of time range (inclusive)",
    )
    end_time: datetime | None = Field(
        None,
        description="End of time range (exclusive)",
    )


class CacheInfo(BaseModel):
    """Cache information for stats response."""

    cached: bool = Field(default=False, description="Whether result was served from cache")
    cached_at: datetime | None = Field(None, description="When result was cached")
    ttl_seconds: int | None = Field(None, description="Cache TTL in seconds")


class EscalationStatsEnhanced(BaseModel):
    """Enhanced escalation statistics with time range and caching info."""

    total_incidents: int = Field(default=0, description="Total incidents")
    by_state: dict[str, int] = Field(default_factory=dict, description="Count by state")
    active_count: int = Field(default=0, description="Active (non-resolved) incidents")
    total_policies: int = Field(default=0, description="Total policies")
    avg_resolution_time_minutes: float | None = Field(
        None,
        description="Average resolution time in minutes",
    )
    time_range: TimeRangeFilter | None = Field(
        None,
        description="Time range filter applied",
    )
    cache_info: CacheInfo | None = Field(
        None,
        description="Cache information",
    )


class DeduplicationStatsEnhanced(BaseModel):
    """Enhanced deduplication statistics with aggregated config data."""

    # Runtime metrics (from in-memory metrics collector)
    total_received: int = Field(default=0, description="Total notifications received")
    total_deduplicated: int = Field(default=0, description="Total notifications deduplicated")
    total_passed: int = Field(default=0, description="Total notifications passed through")
    dedup_rate: float = Field(default=0.0, description="Deduplication rate percentage")
    active_fingerprints: int = Field(default=0, description="Active fingerprints in window")
    # Config aggregates (from database)
    total_configs: int = Field(default=0, description="Total deduplication configs")
    active_configs: int = Field(default=0, description="Active configs count")
    by_strategy: dict[str, int] = Field(
        default_factory=dict,
        description="Count of configs by strategy",
    )
    by_policy: dict[str, int] = Field(
        default_factory=dict,
        description="Count of configs by policy",
    )
    avg_window_seconds: float = Field(
        default=0.0,
        description="Average window duration in seconds",
    )
    time_range: TimeRangeFilter | None = Field(
        None,
        description="Time range filter applied",
    )
    cache_info: CacheInfo | None = Field(
        None,
        description="Cache information",
    )


class ThrottlingStatsEnhanced(BaseModel):
    """Enhanced throttling statistics with aggregated config data."""

    # Runtime metrics (from in-memory metrics collector)
    total_received: int = Field(default=0, description="Total notifications received")
    total_throttled: int = Field(default=0, description="Total notifications throttled")
    total_passed: int = Field(default=0, description="Total notifications passed through")
    throttle_rate: float = Field(default=0.0, description="Throttle rate percentage")
    current_window_count: int = Field(default=0, description="Count in current window")
    # Config aggregates (from database)
    total_configs: int = Field(default=0, description="Total throttling configs")
    active_configs: int = Field(default=0, description="Active configs count")
    configs_with_per_minute: int = Field(
        default=0,
        description="Configs with per-minute limits",
    )
    configs_with_per_hour: int = Field(
        default=0,
        description="Configs with per-hour limits",
    )
    configs_with_per_day: int = Field(
        default=0,
        description="Configs with per-day limits",
    )
    avg_burst_allowance: float = Field(
        default=0.0,
        description="Average burst allowance",
    )
    time_range: TimeRangeFilter | None = Field(
        None,
        description="Time range filter applied",
    )
    cache_info: CacheInfo | None = Field(
        None,
        description="Cache information",
    )


class StatsCacheStatus(BaseModel):
    """Stats cache status information."""

    total_entries: int = Field(default=0, description="Total cache entries")
    valid_entries: int = Field(default=0, description="Valid (non-expired) entries")
    expired_entries: int = Field(default=0, description="Expired entries")
    max_entries: int = Field(default=100, description="Maximum cache entries")
    default_ttl_seconds: int = Field(default=30, description="Default TTL in seconds")
    total_hits: int = Field(default=0, description="Total cache hits")
    total_misses: int = Field(default=0, description="Total cache misses")
    hit_rate: float = Field(default=0.0, description="Cache hit rate")


# =============================================================================
# Escalation Scheduler Schemas
# =============================================================================


class EscalationSchedulerStatus(BaseModel):
    """Status of the escalation scheduler service."""

    running: bool = Field(..., description="Whether scheduler is running")
    enabled: bool = Field(..., description="Whether scheduler is enabled")
    check_interval_seconds: int = Field(..., description="Check interval in seconds")
    last_check_at: str | None = Field(None, description="Last check timestamp (ISO format)")
    next_check_at: str | None = Field(None, description="Next check timestamp (ISO format)")
    check_count: int = Field(default=0, description="Total checks performed")
    escalation_count: int = Field(default=0, description="Total escalations processed")
    error_count: int = Field(default=0, description="Total errors encountered")
    handlers: list[str] = Field(default_factory=list, description="Registered handler types")
    strategy: str = Field(default="time_based", description="Active escalation strategy")


class EscalationSchedulerConfigRequest(BaseModel):
    """Request to update scheduler configuration.

    Validation:
        - check_interval_seconds: Must be between 10 and 3600 seconds (configurable).
        - max_escalations_per_check: Must be between 1 and 1000.

    DoS Prevention:
        - Minimum interval prevents excessive CPU usage from too-frequent checks.
        - Maximum interval ensures timely escalation processing.

    Environment Variables:
        - TRUTHOUND_ESCALATION_CHECK_INTERVAL_MIN
        - TRUTHOUND_ESCALATION_CHECK_INTERVAL_MAX
    """

    check_interval_seconds: int | None = Field(
        None,
        description="Check interval in seconds (10-3600, configurable)",
        ge=10,
        le=3600,
    )
    max_escalations_per_check: int | None = Field(
        None,
        description="Maximum escalations per check (1-1000)",
        ge=1,
        le=1000,
    )
    enabled: bool | None = Field(None, description="Enable/disable scheduler")

    @field_validator("check_interval_seconds")
    @classmethod
    def validate_check_interval(cls, v: int | None) -> int | None:
        """Validate check_interval_seconds against configurable limits.

        Args:
            v: Check interval in seconds or None.

        Returns:
            Validated interval value or None.

        Raises:
            ValueError: If interval is outside allowed range.
        """
        if v is None:
            return v
        limits = get_escalation_limits()
        valid, error = limits.validate_check_interval(v)
        if not valid:
            raise ValueError(error)
        return v


class EscalationSchedulerAction(BaseModel):
    """Response for scheduler control actions."""

    success: bool = Field(..., description="Whether action succeeded")
    message: str = Field(..., description="Status message")
    action: str = Field(..., description="Action performed")
    timestamp: str = Field(..., description="Action timestamp (ISO format)")


class TriggerCheckResponse(BaseModel):
    """Response for triggered manual check."""

    success: bool = Field(..., description="Whether check succeeded")
    message: str = Field(..., description="Status message")
    escalations_processed: int = Field(default=0, description="Number of escalations processed")
    timestamp: str = Field(..., description="Check timestamp (ISO format)")


# =============================================================================
# Combined Stats
# =============================================================================


class AdvancedNotificationStats(BaseModel):
    """Combined statistics for all advanced notification features."""

    routing: dict[str, int] = Field(
        default_factory=dict,
        description="Routing statistics",
    )
    deduplication: DeduplicationStats = Field(
        default_factory=DeduplicationStats,
        description="Deduplication statistics",
    )
    throttling: ThrottlingStats = Field(
        default_factory=ThrottlingStats,
        description="Throttling statistics",
    )
    escalation: EscalationStats = Field(
        default_factory=EscalationStats,
        description="Escalation statistics",
    )


# =============================================================================
# Config Import/Export Schemas
# =============================================================================


class NotificationConfigBundle(BaseModel):
    """Bundle of notification configurations for import/export.

    Contains all notification configurations in a portable format
    that can be exported as JSON or YAML and imported later.
    """

    version: str = Field(
        default="1.0",
        description="Bundle schema version for compatibility checking",
    )
    exported_at: datetime = Field(
        ...,
        description="Timestamp when the bundle was exported",
    )
    routing_rules: list[RoutingRuleResponse] = Field(
        default_factory=list,
        description="List of routing rule configurations",
    )
    deduplication_configs: list[DeduplicationConfigResponse] = Field(
        default_factory=list,
        description="List of deduplication configurations",
    )
    throttling_configs: list[ThrottlingConfigResponse] = Field(
        default_factory=list,
        description="List of throttling configurations",
    )
    escalation_policies: list[EscalationPolicyResponse] = Field(
        default_factory=list,
        description="List of escalation policy configurations",
    )


class ConfigImportItem(BaseModel):
    """Single item to import with conflict resolution."""

    config_type: Literal["routing_rule", "deduplication", "throttling", "escalation"] = Field(
        ...,
        description="Type of configuration being imported",
    )
    config_id: str = Field(
        ...,
        description="ID of the configuration (for conflict detection)",
    )
    action: Literal["create", "skip", "overwrite"] = Field(
        default="create",
        description="Action to take for this config",
    )


class ConfigImportRequest(BaseModel):
    """Request to import notification configurations.

    Supports selective import with conflict resolution options.
    """

    bundle: NotificationConfigBundle = Field(
        ...,
        description="Configuration bundle to import",
    )
    conflict_resolution: Literal["skip", "overwrite", "rename"] = Field(
        default="skip",
        description="Default conflict resolution strategy",
    )
    selected_items: list[ConfigImportItem] | None = Field(
        None,
        description="Specific items to import (null = import all)",
    )


class ConfigImportConflict(BaseModel):
    """Conflict detected during import preview."""

    config_type: Literal["routing_rule", "deduplication", "throttling", "escalation"] = Field(
        ...,
        description="Type of configuration with conflict",
    )
    config_id: str = Field(
        ...,
        description="ID of the conflicting configuration",
    )
    config_name: str = Field(
        ...,
        description="Name of the conflicting configuration",
    )
    existing_name: str = Field(
        ...,
        description="Name of the existing configuration",
    )
    suggested_action: Literal["skip", "overwrite", "rename"] = Field(
        default="skip",
        description="Suggested resolution action",
    )


class ConfigImportPreview(BaseModel):
    """Preview of import operation before execution."""

    total_configs: int = Field(
        default=0,
        description="Total configurations in bundle",
    )
    new_configs: int = Field(
        default=0,
        description="Number of new configurations to create",
    )
    conflicts: list[ConfigImportConflict] = Field(
        default_factory=list,
        description="List of detected conflicts",
    )
    routing_rules_count: int = Field(default=0, description="Routing rules to import")
    deduplication_configs_count: int = Field(default=0, description="Deduplication configs to import")
    throttling_configs_count: int = Field(default=0, description="Throttling configs to import")
    escalation_policies_count: int = Field(default=0, description="Escalation policies to import")


class ConfigImportResult(BaseModel):
    """Result of configuration import operation."""

    success: bool = Field(
        ...,
        description="Whether the import was successful",
    )
    message: str = Field(
        ...,
        description="Summary message",
    )
    created_count: int = Field(
        default=0,
        description="Number of configurations created",
    )
    skipped_count: int = Field(
        default=0,
        description="Number of configurations skipped",
    )
    overwritten_count: int = Field(
        default=0,
        description="Number of configurations overwritten",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="List of errors encountered",
    )
    created_ids: dict[str, list[str]] = Field(
        default_factory=dict,
        description="IDs of created configurations by type",
    )


class ConfigExportRequest(BaseModel):
    """Request parameters for config export."""

    format: Literal["json", "yaml"] = Field(
        default="json",
        description="Export format (json or yaml)",
    )
    include_routing_rules: bool = Field(
        default=True,
        description="Include routing rules in export",
    )
    include_deduplication: bool = Field(
        default=True,
        description="Include deduplication configs in export",
    )
    include_throttling: bool = Field(
        default=True,
        description="Include throttling configs in export",
    )
    include_escalation: bool = Field(
        default=True,
        description="Include escalation policies in export",
    )


# =============================================================================
# Expression Validation Schemas
# =============================================================================


class ExpressionValidateRequest(BaseModel):
    """Request to validate a Python-like expression.

    This schema is used to validate expressions before saving routing rules.
    """

    expression: str = Field(
        ...,
        description="Python-like expression to validate",
        min_length=1,
        max_length=4096,
    )
    timeout_seconds: float = Field(
        default=1.0,
        description="Maximum evaluation time in seconds",
        ge=0.1,
        le=10.0,
    )


class ExpressionValidateResponse(BaseModel):
    """Response from expression validation.

    Contains validation results and optionally a preview evaluation result.
    """

    valid: bool = Field(
        ...,
        description="Whether the expression is syntactically valid",
    )
    error: str | None = Field(
        default=None,
        description="Error message if validation failed",
    )
    error_line: int | None = Field(
        default=None,
        description="Line number where error occurred (1-indexed)",
    )
    preview_result: bool | None = Field(
        default=None,
        description="Preview evaluation result with sample data",
    )
    preview_error: str | None = Field(
        default=None,
        description="Error during preview evaluation",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal warnings about the expression",
    )
