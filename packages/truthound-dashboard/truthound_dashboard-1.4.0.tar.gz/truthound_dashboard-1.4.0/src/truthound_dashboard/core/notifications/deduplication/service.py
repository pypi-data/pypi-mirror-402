"""Main deduplication service.

This module provides the NotificationDeduplicator service that
combines storage, strategies, and policies for complete
deduplication functionality.

Example:
    # Create deduplicator
    deduplicator = NotificationDeduplicator(
        store=InMemoryDeduplicationStore(),
        default_window=TimeWindow(minutes=5),
        policy=DeduplicationPolicy.SEVERITY,
    )

    # Check and record
    fingerprint = deduplicator.generate_fingerprint(
        checkpoint_name="daily_check",
        action_type="slack",
        severity="high",
    )

    if not deduplicator.is_duplicate(fingerprint):
        await send_notification()
        deduplicator.mark_sent(fingerprint)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ...validation_limits import (
    ValidationLimitError,
    get_time_window_limits,
)
from .policies import DeduplicationPolicy, FingerprintConfig, FingerprintGenerator
from .stores import BaseDeduplicationStore, InMemoryDeduplicationStore
from .strategies import BaseWindowStrategy, SlidingWindowStrategy


@dataclass
class TimeWindow:
    """Time window configuration with validation.

    Provides a convenient way to specify window durations with built-in
    validation to prevent DoS attacks from excessive window sizes.

    Validation Limits (configurable via environment variables):
        - Total seconds: 1 to 604800 (7 days)
        - Individual components must be non-negative

    Environment Variables:
        - TRUTHOUND_TIMEWINDOW_MIN: Minimum total duration (default: 1)
        - TRUTHOUND_TIMEWINDOW_MAX: Maximum total duration (default: 604800)

    Attributes:
        seconds: Additional seconds (default: 0).
        minutes: Additional minutes (default: 0).
        hours: Additional hours (default: 0).
        days: Additional days (default: 0).

    Raises:
        ValidationLimitError: If total duration exceeds limits.
        ValueError: If any component is negative.
    """

    seconds: int = 0
    minutes: int = 0
    hours: int = 0
    days: int = 0

    def __post_init__(self) -> None:
        """Validate window configuration after initialization.

        Raises:
            ValueError: If any component is negative.
            ValidationLimitError: If total duration exceeds limits.
        """
        # Validate non-negative values
        if self.seconds < 0:
            raise ValueError(f"seconds must be non-negative, got {self.seconds}")
        if self.minutes < 0:
            raise ValueError(f"minutes must be non-negative, got {self.minutes}")
        if self.hours < 0:
            raise ValueError(f"hours must be non-negative, got {self.hours}")
        if self.days < 0:
            raise ValueError(f"days must be non-negative, got {self.days}")

        # Validate total duration against limits
        total = self.total_seconds
        limits = get_time_window_limits()
        valid, error = limits.validate_total_seconds(total)
        if not valid:
            raise ValidationLimitError(
                error or f"Invalid total duration: {total}",
                parameter="total_seconds",
                value=total,
            )

    @property
    def total_seconds(self) -> int:
        """Get total duration in seconds."""
        return (
            self.seconds
            + self.minutes * 60
            + self.hours * 3600
            + self.days * 86400
        )

    @classmethod
    def from_seconds(cls, seconds: int) -> "TimeWindow":
        """Create from seconds with validation.

        Args:
            seconds: Total duration in seconds.

        Returns:
            TimeWindow instance.

        Raises:
            ValidationLimitError: If seconds exceeds limits.
            ValueError: If seconds is negative.
        """
        if seconds < 0:
            raise ValueError(f"seconds must be non-negative, got {seconds}")

        # Validate against limits before creating
        limits = get_time_window_limits()
        valid, error = limits.validate_total_seconds(seconds)
        if not valid:
            raise ValidationLimitError(
                error or f"Invalid duration: {seconds}",
                parameter="seconds",
                value=seconds,
            )

        return cls(seconds=seconds)

    def __repr__(self) -> str:
        parts = []
        if self.days:
            parts.append(f"{self.days}d")
        if self.hours:
            parts.append(f"{self.hours}h")
        if self.minutes:
            parts.append(f"{self.minutes}m")
        if self.seconds:
            parts.append(f"{self.seconds}s")
        return f"TimeWindow({' '.join(parts) or '0s'})"


class NotificationDeduplicator:
    """Main deduplication service.

    Provides complete deduplication functionality by combining:
    - Storage backend for tracking sent notifications
    - Window strategy for calculating deduplication windows
    - Fingerprint policy for generating unique identifiers

    Thread-safe for concurrent use.

    Example:
        deduplicator = NotificationDeduplicator(
            store=SQLiteDeduplicationStore("dedup.db"),
            default_window=TimeWindow(minutes=5),
            policy=DeduplicationPolicy.SEVERITY,
            strategy=AdaptiveWindowStrategy(),
        )

        # Generate fingerprint
        fp = deduplicator.generate_fingerprint(
            checkpoint_name="check1",
            action_type="slack",
            severity="high",
        )

        # Check if duplicate
        if not deduplicator.is_duplicate(fp):
            send_notification()
            deduplicator.mark_sent(fp)
    """

    def __init__(
        self,
        store: BaseDeduplicationStore | None = None,
        default_window: TimeWindow | None = None,
        policy: DeduplicationPolicy = DeduplicationPolicy.BASIC,
        strategy: BaseWindowStrategy | None = None,
        fingerprint_config: FingerprintConfig | None = None,
    ) -> None:
        """Initialize deduplicator.

        Args:
            store: Storage backend (default: InMemoryDeduplicationStore).
            default_window: Default deduplication window.
            policy: Fingerprint policy.
            strategy: Window strategy (default: SlidingWindowStrategy).
            fingerprint_config: Custom fingerprint config.
        """
        self.store = store or InMemoryDeduplicationStore()
        self.default_window = default_window or TimeWindow(minutes=5)
        self.policy = policy
        self.strategy = strategy or SlidingWindowStrategy(
            window_seconds=self.default_window.total_seconds
        )
        self.fingerprint_generator = FingerprintGenerator(
            policy=policy,
            config=fingerprint_config,
        )

    def generate_fingerprint(
        self,
        checkpoint_name: str | None = None,
        action_type: str | None = None,
        severity: str | None = None,
        issues: list[dict[str, Any]] | None = None,
        timestamp: datetime | None = None,
        **custom_fields: Any,
    ) -> str:
        """Generate a deduplication fingerprint.

        Args:
            checkpoint_name: Name of checkpoint/source.
            action_type: Type of notification channel.
            severity: Severity level.
            issues: List of issues.
            timestamp: Event timestamp.
            **custom_fields: Additional fields.

        Returns:
            Generated fingerprint string.
        """
        return self.fingerprint_generator.generate(
            checkpoint_name=checkpoint_name,
            action_type=action_type,
            severity=severity,
            issues=issues,
            timestamp=timestamp,
            **custom_fields,
        )

    def is_duplicate(
        self,
        fingerprint: str,
        window: TimeWindow | None = None,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Check if a fingerprint is a duplicate.

        Args:
            fingerprint: The fingerprint to check.
            window: Optional window override.
            context: Optional context for strategy.

        Returns:
            True if this is a duplicate notification.
        """
        # Get window duration from strategy
        window_seconds = self.strategy.get_window_seconds(fingerprint, context)

        # Override with explicit window if provided
        if window is not None:
            window_seconds = window.total_seconds

        # Use default if strategy returns 0
        if window_seconds <= 0:
            window_seconds = self.default_window.total_seconds

        # Get window-aligned key
        window_key = self.strategy.get_window_key(fingerprint)

        # Check store
        return self.store.exists(window_key, window_seconds)

    def mark_sent(
        self,
        fingerprint: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Mark a fingerprint as sent.

        Args:
            fingerprint: The fingerprint to record.
            metadata: Optional metadata to store.
        """
        # Get window-aligned key
        window_key = self.strategy.get_window_key(fingerprint)

        # Record in store
        self.store.record(window_key, metadata)

    def check_and_mark(
        self,
        fingerprint: str,
        window: TimeWindow | None = None,
        context: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Atomically check if duplicate and mark as sent if not.

        Args:
            fingerprint: The fingerprint to check.
            window: Optional window override.
            context: Optional context for strategy.
            metadata: Optional metadata to store.

        Returns:
            True if this is NOT a duplicate (notification should be sent).
            False if this IS a duplicate (notification should be skipped).
        """
        if self.is_duplicate(fingerprint, window, context):
            return False

        self.mark_sent(fingerprint, metadata)
        return True

    def get_stats(self) -> dict[str, Any]:
        """Get deduplication statistics.

        Returns:
            Dictionary with statistics.
        """
        return {
            "total_entries": self.store.count(),
            "policy": self.policy.value,
            "default_window_seconds": self.default_window.total_seconds,
            "strategy_type": getattr(self.strategy, "strategy_type", "unknown"),
        }

    def cleanup(self, max_age: TimeWindow | None = None) -> int:
        """Remove expired entries.

        Args:
            max_age: Maximum age of entries to keep.

        Returns:
            Number of entries removed.
        """
        if max_age is None:
            # Default to 24 hours
            max_age = TimeWindow(hours=24)

        return self.store.cleanup(max_age.total_seconds)

    def clear(self) -> None:
        """Clear all deduplication state."""
        self.store.clear()


def deduplicated(
    policy: DeduplicationPolicy = DeduplicationPolicy.BASIC,
    window: TimeWindow | None = None,
):
    """Decorator for deduplicating async functions.

    Creates a deduplicator and checks for duplicates before
    executing the decorated function.

    Args:
        policy: Deduplication policy.
        window: Deduplication window.

    Example:
        @deduplicated(
            policy=DeduplicationPolicy.SEVERITY,
            window=TimeWindow(minutes=10),
        )
        async def send_slack_notification(
            checkpoint_name: str,
            severity: str,
            message: str,
        ):
            await slack.post(message)
    """
    import functools

    # Create shared deduplicator
    deduplicator = NotificationDeduplicator(
        policy=policy,
        default_window=window or TimeWindow(minutes=5),
    )

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate fingerprint from kwargs
            fingerprint = deduplicator.generate_fingerprint(**kwargs)

            # Check and mark
            if not deduplicator.check_and_mark(fingerprint):
                # Duplicate - skip execution
                return None

            # Execute function
            return await func(*args, **kwargs)

        return wrapper

    return decorator
