"""Metrics collection infrastructure for notifications.

This module provides metrics collection and aggregation for the
advanced notification system components.

Architecture:
    - Base Infrastructure: Abstract base classes and registry for extensible
      metrics collection (supports future Redis-based implementations).
    - Specialized Collectors: Domain-specific collectors for deduplication,
      throttling, and escalation with pre-defined metrics.

Classes:
    Base Infrastructure:
        BaseMetricsCollector: Abstract base for generic metric collectors
        InMemoryMetricsCollector: In-memory implementation with async locks
        MetricsRegistry: Singleton registry for managing collectors
        MetricEvent: Data class for recorded events
        MetricSnapshot: Data class for metric snapshots
        MetricType: Enum for metric types

    Specialized Collectors:
        DeduplicationMetrics: Track deduplication rates and active fingerprints
        ThrottlingMetrics: Track throttling rates and window counts
        EscalationMetrics: Track incidents by state and resolution times
        MetricsCollector: Aggregated collector for all subsystems

Example:
    # Using the base infrastructure
    from truthound_dashboard.core.notifications.metrics import (
        MetricsRegistry,
        InMemoryMetricsCollector,
    )

    registry = MetricsRegistry.get_instance()
    collector = await registry.get_collector("my_component")
    await collector.record_event("event_happened", {"detail": "value"})
    await collector.increment("counter_name")
    stats = await collector.get_stats()

    # Using specialized collectors
    from truthound_dashboard.core.notifications.metrics import (
        DeduplicationMetrics,
        ThrottlingMetrics,
        EscalationMetrics,
    )

    dedup_metrics = DeduplicationMetrics()
    await dedup_metrics.record_received()
    stats = await dedup_metrics.get_stats()
"""

from .base import (
    InMemoryMetricsCollector,
    MetricEvent,
    MetricSnapshot,
    MetricsCollector as BaseMetricsCollector,
    MetricsRegistry,
    MetricType,
)
from .collectors import (
    DeduplicationMetrics,
    DeduplicationStats,
    EscalationMetrics,
    EscalationStats,
    IncidentRecord,
    MetricsCollector,
    NotificationMetrics,
    ThrottlingMetrics,
    ThrottlingStats,
    WindowCount,
)
from ..stats_aggregator import (
    StatsAggregator,
    StatsCache,
    TimeRange,
    get_stats_cache,
    reset_stats_cache,
    CacheStrategy,
    DeduplicationStatsResult,
    EscalationStatsResult,
    ThrottlingStatsResult,
)

__all__ = [
    # Base infrastructure
    "BaseMetricsCollector",
    "InMemoryMetricsCollector",
    "MetricsRegistry",
    "MetricEvent",
    "MetricSnapshot",
    "MetricType",
    # Specialized collectors
    "DeduplicationMetrics",
    "ThrottlingMetrics",
    "EscalationMetrics",
    "MetricsCollector",
    # Stats dataclasses
    "DeduplicationStats",
    "ThrottlingStats",
    "EscalationStats",
    "NotificationMetrics",
    # Supporting types
    "WindowCount",
    "IncidentRecord",
    # Stats aggregation (efficient DB queries with caching)
    "StatsAggregator",
    "StatsCache",
    "TimeRange",
    "get_stats_cache",
    "reset_stats_cache",
    "CacheStrategy",
    "DeduplicationStatsResult",
    "EscalationStatsResult",
    "ThrottlingStatsResult",
]
