"""Throttler implementations.

This module provides 5 throttler types:

- TokenBucketThrottler: Smooth rate limiting with burst support
- FixedWindowThrottler: Simple counter per fixed window
- SlidingWindowThrottler: More accurate sliding window counter
- CompositeThrottler: Combines multiple throttlers
- NoOpThrottler: Pass-through for testing

Each throttler implements the allow() method to check if a
notification should be sent.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar

from ...validation_limits import get_throttling_limits
from .stores import BaseThrottlingStore, InMemoryThrottlingStore, ThrottlingEntry


@dataclass
class ThrottleResult:
    """Result of a throttle check.

    Attributes:
        allowed: Whether the request is allowed.
        remaining: Remaining requests in current period.
        limit: Total limit for the period.
        retry_after: Seconds until next allowed request (if not allowed).
        throttler_type: Which throttler made the decision.
    """

    allowed: bool
    remaining: int = 0
    limit: int = 0
    retry_after: float = 0.0
    throttler_type: str = "unknown"


class ThrottlerRegistry:
    """Registry for throttler types.

    Provides plugin architecture for custom throttler implementations.
    """

    _throttlers: ClassVar[dict[str, type["BaseThrottler"]]] = {}

    @classmethod
    def register(cls, throttler_type: str):
        """Decorator to register a throttler type."""

        def decorator(throttler_class: type["BaseThrottler"]) -> type["BaseThrottler"]:
            throttler_class.throttler_type = throttler_type
            cls._throttlers[throttler_type] = throttler_class
            return throttler_class

        return decorator

    @classmethod
    def get(cls, throttler_type: str) -> type["BaseThrottler"] | None:
        """Get a registered throttler class by type."""
        return cls._throttlers.get(throttler_type)

    @classmethod
    def list_types(cls) -> list[str]:
        """Get list of registered throttler types."""
        return list(cls._throttlers.keys())


class BaseThrottler(ABC):
    """Abstract base class for throttlers.

    All throttlers must implement the allow() method to
    determine if a request should be permitted.
    """

    throttler_type: ClassVar[str] = "base"

    @abstractmethod
    def allow(self, key: str) -> ThrottleResult:
        """Check if a request is allowed.

        Args:
            key: Unique key for rate limiting (e.g., channel ID).

        Returns:
            ThrottleResult indicating if allowed.
        """
        ...

    @abstractmethod
    def reset(self, key: str) -> None:
        """Reset throttling state for a key.

        Args:
            key: Key to reset.
        """
        ...


@ThrottlerRegistry.register("token_bucket")
class TokenBucketThrottler(BaseThrottler):
    """Token bucket throttler with validation.

    Implements the token bucket algorithm for smooth rate limiting
    with support for bursts.

    Tokens are added at a constant rate up to a maximum capacity.
    Each request consumes one token. Requests are allowed as long
    as tokens are available.

    Validation:
        - capacity must be between 1 and 100000 (configurable).
        - refill_rate must be between 0.001 and 10000 (reasonable range).

    Attributes:
        capacity: Maximum tokens (burst capacity).
        refill_rate: Tokens added per second.
        store: Storage backend.
    """

    def __init__(
        self,
        capacity: float = 10.0,
        refill_rate: float = 1.0,
        store: BaseThrottlingStore | None = None,
    ) -> None:
        """Initialize token bucket throttler with validation.

        Args:
            capacity: Maximum token capacity.
            refill_rate: Tokens refilled per second.
            store: Storage backend.

        Raises:
            ValueError: If capacity or refill_rate are invalid.
        """
        limits = get_throttling_limits()

        # Validate capacity
        if capacity < limits.limit_min:
            raise ValueError(
                f"capacity must be at least {limits.limit_min}, got {capacity}"
            )
        if capacity > limits.limit_max:
            raise ValueError(
                f"capacity must not exceed {limits.limit_max}, got {capacity}"
            )

        # Validate refill_rate
        if refill_rate < 0.001:
            raise ValueError(
                f"refill_rate must be at least 0.001, got {refill_rate}"
            )
        if refill_rate > 10000:
            raise ValueError(
                f"refill_rate must not exceed 10000, got {refill_rate}"
            )

        self.capacity = capacity
        self.refill_rate = refill_rate
        self.store = store or InMemoryThrottlingStore()

    def allow(self, key: str) -> ThrottleResult:
        """Check if request is allowed using token bucket."""
        now = time.time()
        entry = self.store.get(key)

        if entry is None:
            # Initialize with full bucket
            entry = ThrottlingEntry(
                key=key,
                tokens=self.capacity - 1,  # Consume one for this request
                last_refill=now,
            )
            self.store.set(entry)
            return ThrottleResult(
                allowed=True,
                remaining=int(entry.tokens),
                limit=int(self.capacity),
                throttler_type=self.throttler_type,
            )

        # Calculate token refill
        elapsed = now - entry.last_refill
        new_tokens = min(
            self.capacity,
            entry.tokens + elapsed * self.refill_rate,
        )

        if new_tokens < 1:
            # Not enough tokens
            wait_time = (1 - new_tokens) / self.refill_rate
            return ThrottleResult(
                allowed=False,
                remaining=0,
                limit=int(self.capacity),
                retry_after=wait_time,
                throttler_type=self.throttler_type,
            )

        # Consume token
        entry.tokens = new_tokens - 1
        entry.last_refill = now
        self.store.set(entry)

        return ThrottleResult(
            allowed=True,
            remaining=int(entry.tokens),
            limit=int(self.capacity),
            throttler_type=self.throttler_type,
        )

    def reset(self, key: str) -> None:
        """Reset to full bucket."""
        entry = ThrottlingEntry(
            key=key,
            tokens=self.capacity,
            last_refill=time.time(),
        )
        self.store.set(entry)


@ThrottlerRegistry.register("fixed_window")
class FixedWindowThrottler(BaseThrottler):
    """Fixed window throttler with validation.

    Simple counter-based rate limiting with fixed time windows.
    All requests within a window share the same counter.

    Validation:
        - limit must be between 1 and 100000 (configurable).
        - window_seconds must be between 1 and 86400 (configurable).

    Attributes:
        limit: Maximum requests per window.
        window_seconds: Window duration in seconds.
        store: Storage backend.
    """

    def __init__(
        self,
        limit: int = 10,
        window_seconds: int = 60,
        store: BaseThrottlingStore | None = None,
    ) -> None:
        """Initialize fixed window throttler with validation.

        Args:
            limit: Maximum requests per window.
            window_seconds: Window duration.
            store: Storage backend.

        Raises:
            ValueError: If limit or window_seconds are invalid.
        """
        limits = get_throttling_limits()

        # Validate limit
        valid, error = limits.validate_rate_limit(limit, "limit")
        if not valid:
            raise ValueError(error)

        # Validate window_seconds
        valid, error = limits.validate_window_seconds(window_seconds)
        if not valid:
            raise ValueError(error)

        self.limit = limit
        self.window_seconds = window_seconds
        self.store = store or InMemoryThrottlingStore()

    def allow(self, key: str) -> ThrottleResult:
        """Check if request is allowed using fixed window."""
        now = time.time()
        window_start = int(now // self.window_seconds) * self.window_seconds

        # Increment and get count
        count = self.store.increment(key, window_start)

        if count > self.limit:
            # Over limit
            window_end = window_start + self.window_seconds
            retry_after = window_end - now
            return ThrottleResult(
                allowed=False,
                remaining=0,
                limit=self.limit,
                retry_after=retry_after,
                throttler_type=self.throttler_type,
            )

        return ThrottleResult(
            allowed=True,
            remaining=self.limit - count,
            limit=self.limit,
            throttler_type=self.throttler_type,
        )

    def reset(self, key: str) -> None:
        """Reset counter for key."""
        now = time.time()
        window_start = int(now // self.window_seconds) * self.window_seconds
        entry = ThrottlingEntry(key=key, count=0, window_start=window_start)
        self.store.set(entry)


@ThrottlerRegistry.register("sliding_window")
class SlidingWindowThrottler(BaseThrottler):
    """Sliding window throttler with validation.

    More accurate than fixed window by interpolating between
    the current and previous window.

    Uses weighted average of current and previous window counts
    to approximate a true sliding window.

    Validation:
        - limit must be between 1 and 100000 (configurable).
        - window_seconds must be between 1 and 86400 (configurable).

    Attributes:
        limit: Maximum requests per window.
        window_seconds: Window duration in seconds.
        store: Storage backend.
    """

    def __init__(
        self,
        limit: int = 10,
        window_seconds: int = 60,
        store: BaseThrottlingStore | None = None,
    ) -> None:
        """Initialize sliding window throttler with validation.

        Args:
            limit: Maximum requests per window.
            window_seconds: Window duration.
            store: Storage backend.

        Raises:
            ValueError: If limit or window_seconds are invalid.
        """
        limits = get_throttling_limits()

        # Validate limit
        valid, error = limits.validate_rate_limit(limit, "limit")
        if not valid:
            raise ValueError(error)

        # Validate window_seconds
        valid, error = limits.validate_window_seconds(window_seconds)
        if not valid:
            raise ValueError(error)

        self.limit = limit
        self.window_seconds = window_seconds
        self.store = store or InMemoryThrottlingStore()

    def allow(self, key: str) -> ThrottleResult:
        """Check if request is allowed using sliding window."""
        now = time.time()
        current_window = int(now // self.window_seconds) * self.window_seconds
        prev_window = current_window - self.window_seconds

        # Get current and previous window entries
        current_entry = self.store.get(f"{key}:{current_window}")
        prev_entry = self.store.get(f"{key}:{prev_window}")

        current_count = current_entry.count if current_entry else 0
        prev_count = prev_entry.count if prev_entry else 0

        # Calculate weighted count
        elapsed_in_window = now - current_window
        prev_weight = 1 - (elapsed_in_window / self.window_seconds)
        weighted_count = current_count + (prev_count * prev_weight)

        if weighted_count >= self.limit:
            # Over limit - estimate retry time
            retry_after = self.window_seconds - elapsed_in_window
            return ThrottleResult(
                allowed=False,
                remaining=0,
                limit=self.limit,
                retry_after=retry_after,
                throttler_type=self.throttler_type,
            )

        # Increment current window
        self.store.increment(f"{key}:{current_window}", current_window)

        remaining = max(0, int(self.limit - weighted_count - 1))
        return ThrottleResult(
            allowed=True,
            remaining=remaining,
            limit=self.limit,
            throttler_type=self.throttler_type,
        )

    def reset(self, key: str) -> None:
        """Reset counters for key."""
        now = time.time()
        current_window = int(now // self.window_seconds) * self.window_seconds
        prev_window = current_window - self.window_seconds

        entry = ThrottlingEntry(key=f"{key}:{current_window}", count=0, window_start=current_window)
        self.store.set(entry)
        entry = ThrottlingEntry(key=f"{key}:{prev_window}", count=0, window_start=prev_window)
        self.store.set(entry)


@ThrottlerRegistry.register("composite")
class CompositeThrottler(BaseThrottler):
    """Composite throttler combining multiple throttlers.

    Checks all configured throttlers and only allows if ALL
    throttlers permit the request.

    Useful for implementing multi-level rate limits
    (e.g., per-minute AND per-hour limits).

    Attributes:
        throttlers: List of throttlers to check.
    """

    def __init__(self, throttlers: list[BaseThrottler] | None = None) -> None:
        """Initialize composite throttler.

        Args:
            throttlers: List of throttlers to combine.
        """
        self.throttlers = throttlers or []

    def add(self, throttler: BaseThrottler) -> "CompositeThrottler":
        """Add a throttler to the composite.

        Args:
            throttler: Throttler to add.

        Returns:
            Self for chaining.
        """
        self.throttlers.append(throttler)
        return self

    def allow(self, key: str) -> ThrottleResult:
        """Check if ALL throttlers allow the request."""
        if not self.throttlers:
            return ThrottleResult(
                allowed=True,
                throttler_type=self.throttler_type,
            )

        max_retry = 0.0
        min_remaining = float("inf")
        total_limit = 0

        for throttler in self.throttlers:
            result = throttler.allow(key)

            if not result.allowed:
                # Denied - return immediately with max retry time
                if result.retry_after > max_retry:
                    max_retry = result.retry_after
                    denied_result = result

                return ThrottleResult(
                    allowed=False,
                    remaining=0,
                    limit=result.limit,
                    retry_after=max_retry,
                    throttler_type=f"composite:{result.throttler_type}",
                )

            # Track minimums
            if result.remaining < min_remaining:
                min_remaining = result.remaining
            total_limit = max(total_limit, result.limit)

        return ThrottleResult(
            allowed=True,
            remaining=int(min_remaining) if min_remaining != float("inf") else 0,
            limit=total_limit,
            throttler_type=self.throttler_type,
        )

    def reset(self, key: str) -> None:
        """Reset all throttlers."""
        for throttler in self.throttlers:
            throttler.reset(key)


@ThrottlerRegistry.register("noop")
class NoOpThrottler(BaseThrottler):
    """No-operation throttler.

    Always allows requests. Useful for testing or
    disabling throttling without code changes.
    """

    def allow(self, key: str) -> ThrottleResult:
        """Always allow."""
        return ThrottleResult(
            allowed=True,
            remaining=999999,
            limit=999999,
            throttler_type=self.throttler_type,
        )

    def reset(self, key: str) -> None:
        """No-op."""
        pass


class NotificationThrottler:
    """Main throttling service for notifications.

    Provides a high-level API for throttling notifications
    with support for global and per-channel limits.

    Example:
        throttler = NotificationThrottler(
            global_throttler=FixedWindowThrottler(limit=100, window_seconds=3600),
            channel_throttlers={
                "slack": TokenBucketThrottler(capacity=10, refill_rate=1),
            },
        )

        result = throttler.allow("slack-channel-1")
        if result.allowed:
            send_notification()
    """

    def __init__(
        self,
        global_throttler: BaseThrottler | None = None,
        channel_throttlers: dict[str, BaseThrottler] | None = None,
        default_throttler: BaseThrottler | None = None,
    ) -> None:
        """Initialize notification throttler.

        Args:
            global_throttler: Optional global rate limiter.
            channel_throttlers: Per-channel type throttlers.
            default_throttler: Default for channels without specific throttler.
        """
        self.global_throttler = global_throttler
        self.channel_throttlers = channel_throttlers or {}
        self.default_throttler = default_throttler

    def allow(
        self,
        channel_id: str,
        channel_type: str | None = None,
    ) -> ThrottleResult:
        """Check if notification to channel is allowed.

        Args:
            channel_id: Unique channel identifier.
            channel_type: Channel type (e.g., 'slack', 'email').

        Returns:
            ThrottleResult indicating if allowed.
        """
        # Check global throttler
        if self.global_throttler:
            result = self.global_throttler.allow("global")
            if not result.allowed:
                return ThrottleResult(
                    allowed=False,
                    remaining=result.remaining,
                    limit=result.limit,
                    retry_after=result.retry_after,
                    throttler_type=f"global:{result.throttler_type}",
                )

        # Get channel-specific throttler
        throttler = None
        if channel_type and channel_type in self.channel_throttlers:
            throttler = self.channel_throttlers[channel_type]
        elif self.default_throttler:
            throttler = self.default_throttler

        # Check channel throttler
        if throttler:
            result = throttler.allow(channel_id)
            if not result.allowed:
                return ThrottleResult(
                    allowed=False,
                    remaining=result.remaining,
                    limit=result.limit,
                    retry_after=result.retry_after,
                    throttler_type=f"channel:{result.throttler_type}",
                )
            return result

        # No throttling configured
        return ThrottleResult(
            allowed=True,
            remaining=999999,
            limit=999999,
            throttler_type="none",
        )

    def set_channel_throttler(
        self,
        channel_type: str,
        throttler: BaseThrottler,
    ) -> None:
        """Set throttler for a channel type.

        Args:
            channel_type: Channel type (e.g., 'slack').
            throttler: Throttler to use.
        """
        self.channel_throttlers[channel_type] = throttler

    def get_stats(self) -> dict[str, Any]:
        """Get throttling statistics.

        Returns:
            Dictionary with stats.
        """
        return {
            "has_global": self.global_throttler is not None,
            "channel_types": list(self.channel_throttlers.keys()),
            "has_default": self.default_throttler is not None,
        }
