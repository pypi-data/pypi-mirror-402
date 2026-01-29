"""Validation limits and configuration for time-based parameters.

This module provides centralized validation constants and utilities
for preventing DoS attacks and ensuring reasonable configuration values
across deduplication, throttling, and escalation features.

All limits are configurable via environment variables to support
different deployment scenarios (development, staging, production).

Environment Variables:
    TRUTHOUND_DEDUP_WINDOW_MIN: Minimum deduplication window (seconds)
    TRUTHOUND_DEDUP_WINDOW_MAX: Maximum deduplication window (seconds)
    TRUTHOUND_THROTTLE_LIMIT_MIN: Minimum throttle rate limit
    TRUTHOUND_THROTTLE_LIMIT_MAX: Maximum throttle rate limit
    TRUTHOUND_THROTTLE_WINDOW_MIN: Minimum throttle window (seconds)
    TRUTHOUND_THROTTLE_WINDOW_MAX: Maximum throttle window (seconds)
    TRUTHOUND_ESCALATION_DELAY_MIN: Minimum escalation delay (minutes)
    TRUTHOUND_ESCALATION_DELAY_MAX: Maximum escalation delay (minutes)
    TRUTHOUND_ESCALATION_CHECK_INTERVAL_MIN: Min scheduler check interval (seconds)
    TRUTHOUND_ESCALATION_CHECK_INTERVAL_MAX: Max scheduler check interval (seconds)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any


# =============================================================================
# Default Validation Limits
# =============================================================================


@dataclass(frozen=True)
class DeduplicationLimits:
    """Validation limits for deduplication configuration.

    Attributes:
        window_min_seconds: Minimum window size (prevents too-small windows).
        window_max_seconds: Maximum window size (prevents memory exhaustion).
        window_default_seconds: Default window size if not specified.
    """

    window_min_seconds: int = 1
    window_max_seconds: int = 86400  # 24 hours
    window_default_seconds: int = 300  # 5 minutes

    def validate_window_seconds(self, value: int) -> tuple[bool, str | None]:
        """Validate window_seconds value.

        Args:
            value: Window duration in seconds.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if value < self.window_min_seconds:
            return (
                False,
                f"window_seconds must be at least {self.window_min_seconds} second(s), "
                f"got {value}",
            )
        if value > self.window_max_seconds:
            return (
                False,
                f"window_seconds must not exceed {self.window_max_seconds} seconds "
                f"({self.window_max_seconds // 3600} hours), got {value}",
            )
        return (True, None)


@dataclass(frozen=True)
class ThrottlingLimits:
    """Validation limits for throttling configuration.

    Attributes:
        limit_min: Minimum rate limit value (prevents zero/negative limits).
        limit_max: Maximum rate limit value (prevents unreasonable limits).
        window_min_seconds: Minimum window size for custom throttlers.
        window_max_seconds: Maximum window size for custom throttlers.
        burst_allowance_min: Minimum burst allowance factor.
        burst_allowance_max: Maximum burst allowance factor.
        per_minute_max: Maximum notifications per minute.
        per_hour_max: Maximum notifications per hour.
        per_day_max: Maximum notifications per day.
    """

    limit_min: int = 1
    limit_max: int = 100000  # Allow high limits for batch systems
    window_min_seconds: int = 1
    window_max_seconds: int = 86400  # 24 hours
    burst_allowance_min: float = 1.0
    burst_allowance_max: float = 10.0
    per_minute_max: int = 10000
    per_hour_max: int = 100000
    per_day_max: int = 1000000

    def validate_rate_limit(
        self,
        value: int,
        limit_name: str = "rate limit",
    ) -> tuple[bool, str | None]:
        """Validate a rate limit value.

        Args:
            value: Rate limit value.
            limit_name: Name of the limit for error messages.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if value < self.limit_min:
            return (
                False,
                f"{limit_name} must be at least {self.limit_min}, got {value}",
            )
        if value > self.limit_max:
            return (
                False,
                f"{limit_name} must not exceed {self.limit_max}, got {value}",
            )
        return (True, None)

    def validate_window_seconds(self, value: int) -> tuple[bool, str | None]:
        """Validate window_seconds for throttling.

        Args:
            value: Window duration in seconds.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if value < self.window_min_seconds:
            return (
                False,
                f"window_seconds must be at least {self.window_min_seconds} second(s), "
                f"got {value}",
            )
        if value > self.window_max_seconds:
            return (
                False,
                f"window_seconds must not exceed {self.window_max_seconds} seconds, "
                f"got {value}",
            )
        return (True, None)

    def validate_burst_allowance(self, value: float) -> tuple[bool, str | None]:
        """Validate burst allowance factor.

        Args:
            value: Burst allowance factor.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if value < self.burst_allowance_min:
            return (
                False,
                f"burst_allowance must be at least {self.burst_allowance_min}, "
                f"got {value}",
            )
        if value > self.burst_allowance_max:
            return (
                False,
                f"burst_allowance must not exceed {self.burst_allowance_max}, "
                f"got {value}",
            )
        return (True, None)


@dataclass(frozen=True)
class EscalationLimits:
    """Validation limits for escalation configuration.

    Attributes:
        delay_min_minutes: Minimum delay between escalation levels.
        delay_max_minutes: Maximum delay between escalation levels.
        max_levels: Maximum number of escalation levels.
        max_escalations_min: Minimum value for max_escalations.
        max_escalations_max: Maximum value for max_escalations.
        check_interval_min_seconds: Minimum scheduler check interval.
        check_interval_max_seconds: Maximum scheduler check interval.
    """

    delay_min_minutes: int = 0
    delay_max_minutes: int = 10080  # 7 days
    max_levels: int = 20
    max_escalations_min: int = 1
    max_escalations_max: int = 100
    check_interval_min_seconds: int = 10
    check_interval_max_seconds: int = 3600  # 1 hour

    def validate_delay_minutes(self, value: int) -> tuple[bool, str | None]:
        """Validate escalation delay in minutes.

        Args:
            value: Delay in minutes.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if value < self.delay_min_minutes:
            return (
                False,
                f"delay_minutes must be at least {self.delay_min_minutes}, got {value}",
            )
        if value > self.delay_max_minutes:
            return (
                False,
                f"delay_minutes must not exceed {self.delay_max_minutes} minutes "
                f"({self.delay_max_minutes // 1440} days), got {value}",
            )
        return (True, None)

    def validate_max_escalations(self, value: int) -> tuple[bool, str | None]:
        """Validate max_escalations value.

        Args:
            value: Maximum escalation attempts.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if value < self.max_escalations_min:
            return (
                False,
                f"max_escalations must be at least {self.max_escalations_min}, "
                f"got {value}",
            )
        if value > self.max_escalations_max:
            return (
                False,
                f"max_escalations must not exceed {self.max_escalations_max}, "
                f"got {value}",
            )
        return (True, None)

    def validate_check_interval(self, value: int) -> tuple[bool, str | None]:
        """Validate scheduler check interval in seconds.

        Args:
            value: Check interval in seconds.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if value < self.check_interval_min_seconds:
            return (
                False,
                f"check_interval_seconds must be at least "
                f"{self.check_interval_min_seconds} seconds, got {value}",
            )
        if value > self.check_interval_max_seconds:
            return (
                False,
                f"check_interval_seconds must not exceed "
                f"{self.check_interval_max_seconds} seconds, got {value}",
            )
        return (True, None)


@dataclass(frozen=True)
class TimeWindowLimits:
    """Validation limits for TimeWindow class.

    These limits apply to the service-level TimeWindow dataclass
    used in the deduplication service.

    Attributes:
        total_seconds_min: Minimum total duration.
        total_seconds_max: Maximum total duration.
        days_max: Maximum days component.
        hours_max: Maximum hours component.
        minutes_max: Maximum minutes component.
        seconds_max: Maximum seconds component.
    """

    total_seconds_min: int = 1
    total_seconds_max: int = 604800  # 7 days
    days_max: int = 7
    hours_max: int = 168  # 7 * 24
    minutes_max: int = 10080  # 7 * 24 * 60
    seconds_max: int = 604800  # 7 * 24 * 60 * 60

    def validate_total_seconds(self, value: int) -> tuple[bool, str | None]:
        """Validate total duration in seconds.

        Args:
            value: Total duration in seconds.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if value < self.total_seconds_min:
            return (
                False,
                f"Total duration must be at least {self.total_seconds_min} second(s), "
                f"got {value}",
            )
        if value > self.total_seconds_max:
            return (
                False,
                f"Total duration must not exceed {self.total_seconds_max} seconds "
                f"({self.total_seconds_max // 86400} days), got {value}",
            )
        return (True, None)


# =============================================================================
# Configuration Loader
# =============================================================================


@lru_cache(maxsize=1)
def get_deduplication_limits() -> DeduplicationLimits:
    """Get deduplication validation limits from environment.

    Returns:
        DeduplicationLimits instance with values from environment or defaults.
    """
    return DeduplicationLimits(
        window_min_seconds=int(os.getenv("TRUTHOUND_DEDUP_WINDOW_MIN", "1")),
        window_max_seconds=int(os.getenv("TRUTHOUND_DEDUP_WINDOW_MAX", "86400")),
        window_default_seconds=int(os.getenv("TRUTHOUND_DEDUP_WINDOW_DEFAULT", "300")),
    )


@lru_cache(maxsize=1)
def get_throttling_limits() -> ThrottlingLimits:
    """Get throttling validation limits from environment.

    Returns:
        ThrottlingLimits instance with values from environment or defaults.
    """
    return ThrottlingLimits(
        limit_min=int(os.getenv("TRUTHOUND_THROTTLE_LIMIT_MIN", "1")),
        limit_max=int(os.getenv("TRUTHOUND_THROTTLE_LIMIT_MAX", "100000")),
        window_min_seconds=int(os.getenv("TRUTHOUND_THROTTLE_WINDOW_MIN", "1")),
        window_max_seconds=int(os.getenv("TRUTHOUND_THROTTLE_WINDOW_MAX", "86400")),
        burst_allowance_min=float(
            os.getenv("TRUTHOUND_THROTTLE_BURST_MIN", "1.0")
        ),
        burst_allowance_max=float(
            os.getenv("TRUTHOUND_THROTTLE_BURST_MAX", "10.0")
        ),
        per_minute_max=int(os.getenv("TRUTHOUND_THROTTLE_PER_MINUTE_MAX", "10000")),
        per_hour_max=int(os.getenv("TRUTHOUND_THROTTLE_PER_HOUR_MAX", "100000")),
        per_day_max=int(os.getenv("TRUTHOUND_THROTTLE_PER_DAY_MAX", "1000000")),
    )


@lru_cache(maxsize=1)
def get_escalation_limits() -> EscalationLimits:
    """Get escalation validation limits from environment.

    Returns:
        EscalationLimits instance with values from environment or defaults.
    """
    return EscalationLimits(
        delay_min_minutes=int(os.getenv("TRUTHOUND_ESCALATION_DELAY_MIN", "0")),
        delay_max_minutes=int(os.getenv("TRUTHOUND_ESCALATION_DELAY_MAX", "10080")),
        max_levels=int(os.getenv("TRUTHOUND_ESCALATION_MAX_LEVELS", "20")),
        max_escalations_min=int(
            os.getenv("TRUTHOUND_ESCALATION_MAX_ESCALATIONS_MIN", "1")
        ),
        max_escalations_max=int(
            os.getenv("TRUTHOUND_ESCALATION_MAX_ESCALATIONS_MAX", "100")
        ),
        check_interval_min_seconds=int(
            os.getenv("TRUTHOUND_ESCALATION_CHECK_INTERVAL_MIN", "10")
        ),
        check_interval_max_seconds=int(
            os.getenv("TRUTHOUND_ESCALATION_CHECK_INTERVAL_MAX", "3600")
        ),
    )


@lru_cache(maxsize=1)
def get_time_window_limits() -> TimeWindowLimits:
    """Get TimeWindow validation limits from environment.

    Returns:
        TimeWindowLimits instance with values from environment or defaults.
    """
    return TimeWindowLimits(
        total_seconds_min=int(os.getenv("TRUTHOUND_TIMEWINDOW_MIN", "1")),
        total_seconds_max=int(os.getenv("TRUTHOUND_TIMEWINDOW_MAX", "604800")),
        days_max=int(os.getenv("TRUTHOUND_TIMEWINDOW_DAYS_MAX", "7")),
    )


def clear_limits_cache() -> None:
    """Clear the cached limit instances.

    Useful for testing when environment variables change.
    """
    get_deduplication_limits.cache_clear()
    get_throttling_limits.cache_clear()
    get_escalation_limits.cache_clear()
    get_time_window_limits.cache_clear()


# =============================================================================
# Validation Exception
# =============================================================================


class ValidationLimitError(ValueError):
    """Exception raised when validation limits are violated.

    This exception provides detailed information about the
    validation failure, including the parameter name, value,
    and the limit that was exceeded.

    Attributes:
        parameter: Name of the parameter that failed validation.
        value: The invalid value.
        message: Detailed error message.
    """

    def __init__(
        self,
        message: str,
        parameter: str | None = None,
        value: Any = None,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Error message.
            parameter: Name of invalid parameter.
            value: The invalid value.
        """
        self.parameter = parameter
        self.value = value
        self.message = message
        super().__init__(message)

    def __repr__(self) -> str:
        return f"ValidationLimitError(parameter={self.parameter!r}, value={self.value!r})"


# =============================================================================
# Utility Functions
# =============================================================================


def validate_positive_int(
    value: int,
    name: str,
    min_value: int = 1,
    max_value: int | None = None,
) -> None:
    """Validate a positive integer parameter.

    Args:
        value: Value to validate.
        name: Parameter name for error messages.
        min_value: Minimum allowed value.
        max_value: Maximum allowed value (optional).

    Raises:
        ValidationLimitError: If validation fails.
    """
    if value < min_value:
        raise ValidationLimitError(
            f"{name} must be at least {min_value}, got {value}",
            parameter=name,
            value=value,
        )
    if max_value is not None and value > max_value:
        raise ValidationLimitError(
            f"{name} must not exceed {max_value}, got {value}",
            parameter=name,
            value=value,
        )


def validate_positive_float(
    value: float,
    name: str,
    min_value: float = 0.0,
    max_value: float | None = None,
) -> None:
    """Validate a positive float parameter.

    Args:
        value: Value to validate.
        name: Parameter name for error messages.
        min_value: Minimum allowed value.
        max_value: Maximum allowed value (optional).

    Raises:
        ValidationLimitError: If validation fails.
    """
    if value < min_value:
        raise ValidationLimitError(
            f"{name} must be at least {min_value}, got {value}",
            parameter=name,
            value=value,
        )
    if max_value is not None and value > max_value:
        raise ValidationLimitError(
            f"{name} must not exceed {max_value}, got {value}",
            parameter=name,
            value=value,
        )
