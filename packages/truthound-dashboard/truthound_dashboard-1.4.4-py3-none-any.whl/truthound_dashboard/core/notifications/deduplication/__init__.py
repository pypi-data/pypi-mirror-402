"""Notification deduplication system.

This module provides a flexible deduplication system to prevent
sending duplicate notifications within configurable time windows.

Features:
    - 4 window strategies (sliding, tumbling, session, adaptive)
    - 6 deduplication policies (none, basic, severity, issue_based, strict, custom)
    - Pluggable storage backends (in-memory, SQLite, Redis, Redis Streams)
    - Fingerprint-based duplicate detection
    - Factory function for easy store creation

Example:
    from truthound_dashboard.core.notifications.deduplication import (
        NotificationDeduplicator,
        InMemoryDeduplicationStore,
        DeduplicationPolicy,
        TimeWindow,
    )

    # Create deduplicator
    deduplicator = NotificationDeduplicator(
        store=InMemoryDeduplicationStore(),
        default_window=TimeWindow(seconds=300),
        policy=DeduplicationPolicy.SEVERITY,
    )

    # Generate fingerprint and check
    fingerprint = deduplicator.generate_fingerprint(
        checkpoint_name="daily_check",
        action_type="slack",
        severity="high",
    )

    if not deduplicator.is_duplicate(fingerprint):
        await send_notification()
        deduplicator.mark_sent(fingerprint)

Redis Store Example:
    from truthound_dashboard.core.notifications.deduplication import (
        RedisDeduplicationStore,
        REDIS_AVAILABLE,
    )

    if REDIS_AVAILABLE:
        store = RedisDeduplicationStore(
            redis_url="redis://localhost:6379/0",
            key_prefix="myapp:dedup:",
            default_ttl=3600,
        )
        # Use store with NotificationDeduplicator

Redis Streams Store Example (Production):
    from truthound_dashboard.core.notifications.deduplication import (
        RedisStreamsDeduplicationStore,
        create_deduplication_store,
        DeduplicationStoreType,
        REDIS_AVAILABLE,
    )

    # Using factory function (recommended)
    store = create_deduplication_store("redis_streams")

    # Or direct instantiation with full configuration
    if REDIS_AVAILABLE:
        store = RedisStreamsDeduplicationStore(
            redis_url="redis://myredis:6379/1",
            default_ttl=7200,
            max_connections=20,
            enable_fallback=True,  # Falls back to InMemory on Redis failure
        )

        # Health check
        health = await store.health_check_async()
        print(f"Healthy: {health['healthy']}, Mode: {health.get('mode')}")

        # Get metrics
        metrics = store.get_metrics()
        print(f"Hit rate: {metrics['hit_rate']}%")

Factory Function Example:
    from truthound_dashboard.core.notifications.deduplication import (
        create_deduplication_store,
    )

    # Auto-detect from environment variables
    store = create_deduplication_store()

    # Explicit type with configuration
    store = create_deduplication_store(
        "redis_streams",
        default_ttl=3600,
        enable_fallback=True,
    )
"""

from .policies import DeduplicationPolicy, FingerprintGenerator
from .service import NotificationDeduplicator, TimeWindow
from .stores import (
    REDIS_AVAILABLE,
    BaseDeduplicationStore,
    DeduplicationMetrics,
    DeduplicationStoreType,
    InMemoryDeduplicationStore,
    RedisDeduplicationStore,
    RedisStreamsDeduplicationStore,
    SQLiteDeduplicationStore,
    create_deduplication_store,
)
from .strategies import (
    AdaptiveWindowStrategy,
    BaseWindowStrategy,
    SessionWindowStrategy,
    SlidingWindowStrategy,
    StrategyRegistry,
    TumblingWindowStrategy,
)

__all__ = [
    # Stores
    "BaseDeduplicationStore",
    "InMemoryDeduplicationStore",
    "SQLiteDeduplicationStore",
    "RedisDeduplicationStore",
    "RedisStreamsDeduplicationStore",
    "DeduplicationMetrics",
    "DeduplicationStoreType",
    "create_deduplication_store",
    "REDIS_AVAILABLE",
    # Strategies
    "BaseWindowStrategy",
    "SlidingWindowStrategy",
    "TumblingWindowStrategy",
    "SessionWindowStrategy",
    "AdaptiveWindowStrategy",
    "StrategyRegistry",
    # Policies
    "DeduplicationPolicy",
    "FingerprintGenerator",
    # Service
    "NotificationDeduplicator",
    "TimeWindow",
]
