"""Fluent builder for throttler configuration.

This module provides a builder pattern for easily configuring
multi-level rate limiting with a fluent API.

Example:
    throttler = (
        ThrottlerBuilder()
        .with_per_minute_limit(10)
        .with_per_hour_limit(100)
        .with_per_day_limit(500)
        .with_burst_allowance(1.5)
        .build()
    )

    result = throttler.allow("channel-1")
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .stores import BaseThrottlingStore, InMemoryThrottlingStore
from .throttlers import (
    BaseThrottler,
    CompositeThrottler,
    FixedWindowThrottler,
    NotificationThrottler,
    TokenBucketThrottler,
)

if TYPE_CHECKING:
    from typing import Self


class ThrottlerBuilder:
    """Fluent builder for creating throttlers.

    Provides a convenient API for configuring multi-level
    rate limiting with various algorithms.

    Example:
        # Simple per-minute limit
        throttler = (
            ThrottlerBuilder()
            .with_per_minute_limit(10)
            .build()
        )

        # Multi-level limits with burst
        throttler = (
            ThrottlerBuilder()
            .with_per_minute_limit(10)
            .with_per_hour_limit(100)
            .with_burst_allowance(1.5)
            .build()
        )

        # Token bucket for smooth limiting
        throttler = (
            ThrottlerBuilder()
            .with_token_bucket(capacity=10, refill_rate=1)
            .build()
        )
    """

    def __init__(self) -> None:
        """Initialize builder."""
        self._per_second: int | None = None
        self._per_minute: int | None = None
        self._per_hour: int | None = None
        self._per_day: int | None = None
        self._burst_allowance: float = 1.0
        self._token_bucket_capacity: float | None = None
        self._token_bucket_rate: float | None = None
        self._store: BaseThrottlingStore | None = None
        self._throttlers: list[BaseThrottler] = []

    def with_per_second_limit(self, limit: int) -> "Self":
        """Set per-second limit.

        Args:
            limit: Maximum requests per second.

        Returns:
            Self for chaining.
        """
        self._per_second = limit
        return self

    def with_per_minute_limit(self, limit: int) -> "Self":
        """Set per-minute limit.

        Args:
            limit: Maximum requests per minute.

        Returns:
            Self for chaining.
        """
        self._per_minute = limit
        return self

    def with_per_hour_limit(self, limit: int) -> "Self":
        """Set per-hour limit.

        Args:
            limit: Maximum requests per hour.

        Returns:
            Self for chaining.
        """
        self._per_hour = limit
        return self

    def with_per_day_limit(self, limit: int) -> "Self":
        """Set per-day limit.

        Args:
            limit: Maximum requests per day.

        Returns:
            Self for chaining.
        """
        self._per_day = limit
        return self

    def with_burst_allowance(self, factor: float) -> "Self":
        """Set burst allowance factor.

        Multiplies the limit to allow temporary bursts.
        For example, 1.5 allows 150% of normal rate for short periods.

        Args:
            factor: Burst multiplier (1.0 = no burst allowed).

        Returns:
            Self for chaining.
        """
        self._burst_allowance = max(1.0, factor)
        return self

    def with_token_bucket(
        self,
        capacity: float,
        refill_rate: float,
    ) -> "Self":
        """Configure token bucket algorithm.

        Args:
            capacity: Maximum tokens (burst capacity).
            refill_rate: Tokens added per second.

        Returns:
            Self for chaining.
        """
        self._token_bucket_capacity = capacity
        self._token_bucket_rate = refill_rate
        return self

    def with_store(self, store: BaseThrottlingStore) -> "Self":
        """Set storage backend.

        Args:
            store: Storage backend to use.

        Returns:
            Self for chaining.
        """
        self._store = store
        return self

    def add_throttler(self, throttler: BaseThrottler) -> "Self":
        """Add a custom throttler to the composite.

        Args:
            throttler: Custom throttler to add.

        Returns:
            Self for chaining.
        """
        self._throttlers.append(throttler)
        return self

    def build(self) -> BaseThrottler:
        """Build the throttler.

        Creates a CompositeThrottler if multiple limits are
        configured, or a single throttler for simple configs.

        Returns:
            Configured throttler.
        """
        store = self._store or InMemoryThrottlingStore()
        throttlers: list[BaseThrottler] = list(self._throttlers)

        # Add token bucket if configured
        if self._token_bucket_capacity and self._token_bucket_rate:
            throttlers.append(
                TokenBucketThrottler(
                    capacity=self._token_bucket_capacity * self._burst_allowance,
                    refill_rate=self._token_bucket_rate,
                    store=store,
                )
            )

        # Add window-based throttlers
        if self._per_second:
            throttlers.append(
                FixedWindowThrottler(
                    limit=int(self._per_second * self._burst_allowance),
                    window_seconds=1,
                    store=store,
                )
            )

        if self._per_minute:
            throttlers.append(
                FixedWindowThrottler(
                    limit=int(self._per_minute * self._burst_allowance),
                    window_seconds=60,
                    store=store,
                )
            )

        if self._per_hour:
            throttlers.append(
                FixedWindowThrottler(
                    limit=int(self._per_hour * self._burst_allowance),
                    window_seconds=3600,
                    store=store,
                )
            )

        if self._per_day:
            throttlers.append(
                FixedWindowThrottler(
                    limit=int(self._per_day * self._burst_allowance),
                    window_seconds=86400,
                    store=store,
                )
            )

        # Return appropriate throttler
        if not throttlers:
            # No limits configured - use simple token bucket default
            return TokenBucketThrottler(
                capacity=100,
                refill_rate=10,
                store=store,
            )

        if len(throttlers) == 1:
            return throttlers[0]

        return CompositeThrottler(throttlers=throttlers)

    def build_notification_throttler(
        self,
        global_limits: bool = True,
    ) -> NotificationThrottler:
        """Build a NotificationThrottler service.

        Args:
            global_limits: Apply limits globally (vs per-channel).

        Returns:
            Configured NotificationThrottler.
        """
        throttler = self.build()

        if global_limits:
            return NotificationThrottler(
                global_throttler=throttler,
            )
        else:
            return NotificationThrottler(
                default_throttler=throttler,
            )


def configure_global_throttling(
    per_minute: int | None = None,
    per_hour: int | None = None,
    per_day: int | None = None,
    burst_allowance: float = 1.5,
) -> NotificationThrottler:
    """Configure global notification throttling.

    Convenience function for common throttling setup.

    Args:
        per_minute: Max notifications per minute.
        per_hour: Max notifications per hour.
        per_day: Max notifications per day.
        burst_allowance: Burst factor.

    Returns:
        Configured NotificationThrottler.
    """
    builder = ThrottlerBuilder()

    if per_minute:
        builder.with_per_minute_limit(per_minute)
    if per_hour:
        builder.with_per_hour_limit(per_hour)
    if per_day:
        builder.with_per_day_limit(per_day)

    builder.with_burst_allowance(burst_allowance)

    return builder.build_notification_throttler(global_limits=True)
