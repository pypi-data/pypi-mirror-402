"""Notification throttling system.

This module provides rate limiting for notifications to prevent
overwhelming recipients during incidents or high-frequency events.

Features:
    - 5 throttler types (TokenBucket, FixedWindow, SlidingWindow, Composite, NoOp)
    - Fluent builder API for configuration
    - Per-channel and global throttling
    - Burst allowance support

Example:
    from truthound_dashboard.core.notifications.throttling import (
        ThrottlerBuilder,
        TokenBucketThrottler,
    )

    # Using builder
    throttler = (
        ThrottlerBuilder()
        .with_per_minute_limit(10)
        .with_per_hour_limit(100)
        .with_burst_allowance(1.5)
        .build()
    )

    # Check if allowed
    result = throttler.allow("slack-channel")
    if result.allowed:
        send_notification()
    else:
        print(f"Retry after {result.retry_after} seconds")
"""

from .builder import ThrottlerBuilder
from .stores import (
    REDIS_AVAILABLE,
    BaseThrottlingStore,
    InMemoryThrottlingStore,
    RedisThrottlingStore,
    SQLiteThrottlingStore,
    ThrottlingEntry,
    ThrottlingMetrics,
    ThrottlingStoreType,
    create_throttling_store,
)
from .throttlers import (
    BaseThrottler,
    CompositeThrottler,
    FixedWindowThrottler,
    NoOpThrottler,
    NotificationThrottler,
    SlidingWindowThrottler,
    ThrottleResult,
    ThrottlerRegistry,
    TokenBucketThrottler,
)

__all__ = [
    # Throttlers
    "BaseThrottler",
    "TokenBucketThrottler",
    "FixedWindowThrottler",
    "SlidingWindowThrottler",
    "CompositeThrottler",
    "NoOpThrottler",
    "ThrottlerRegistry",
    "ThrottleResult",
    # Service
    "NotificationThrottler",
    # Builder
    "ThrottlerBuilder",
    # Stores
    "BaseThrottlingStore",
    "InMemoryThrottlingStore",
    "SQLiteThrottlingStore",
    "RedisThrottlingStore",
    "ThrottlingEntry",
    "ThrottlingMetrics",
    "ThrottlingStoreType",
    "create_throttling_store",
    "REDIS_AVAILABLE",
]
