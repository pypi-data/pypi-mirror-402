"""Metrics collection infrastructure for advanced notifications.

This module provides an extensible metrics collection system for tracking
notification-related events and statistics across different components.

Architecture:
    - MetricsCollector: Abstract base for collecting metrics
    - InMemoryMetricsCollector: Thread-safe in-memory implementation
    - MetricsRegistry: Singleton registry for managing collectors

The design supports future extension to Redis-based or other distributed
storage backends while maintaining a consistent interface.

Example:
    # Get or create a collector for a component
    registry = MetricsRegistry.get_instance()
    collector = registry.get_collector("deduplication")

    # Record events and counters
    await collector.record_event("duplicate_detected", {"fingerprint": "abc123"})
    await collector.increment("duplicates_blocked")

    # Get aggregated stats
    stats = await collector.get_stats()
"""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar


class MetricType(str, Enum):
    """Types of metrics that can be collected."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    EVENT = "event"


@dataclass
class MetricEvent:
    """A recorded metric event.

    Attributes:
        event_type: Type identifier for the event.
        timestamp: When the event occurred.
        metadata: Additional event-specific data.
    """

    event_type: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class MetricSnapshot:
    """A snapshot of all collected metrics.

    Attributes:
        counters: Current counter values.
        events: Recent events (limited by retention).
        event_counts: Total count per event type.
        last_reset: When metrics were last reset.
        collected_at: When this snapshot was taken.
    """

    counters: dict[str, int]
    events: list[MetricEvent]
    event_counts: dict[str, int]
    last_reset: datetime | None
    collected_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert snapshot to dictionary for serialization."""
        return {
            "counters": self.counters,
            "events": [e.to_dict() for e in self.events],
            "event_counts": self.event_counts,
            "last_reset": self.last_reset.isoformat() if self.last_reset else None,
            "collected_at": self.collected_at.isoformat(),
        }


class MetricsCollector(ABC):
    """Abstract base class for metrics collection.

    Each collector manages metrics for a specific component (e.g.,
    deduplication, throttling, escalation) and provides methods for
    recording events, incrementing counters, and retrieving statistics.

    Implementations must be thread-safe for use in async contexts.

    Example:
        class RedisMetricsCollector(MetricsCollector):
            async def record_event(self, event_type: str, metadata: dict) -> None:
                # Store in Redis stream
                await self.redis.xadd(f"metrics:{self.component}", {...})
    """

    def __init__(self, component: str, max_events: int = 1000) -> None:
        """Initialize the collector.

        Args:
            component: Name of the component being monitored.
            max_events: Maximum number of events to retain.
        """
        self.component = component
        self.max_events = max_events

    @abstractmethod
    async def record_event(
        self,
        event_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record a metric event.

        Args:
            event_type: Type identifier for the event.
            metadata: Optional event-specific data.
        """
        ...

    @abstractmethod
    async def increment(self, metric: str, value: int = 1) -> None:
        """Increment a counter metric.

        Args:
            metric: Name of the counter.
            value: Amount to increment by (default 1).
        """
        ...

    @abstractmethod
    async def decrement(self, metric: str, value: int = 1) -> None:
        """Decrement a counter metric.

        Args:
            metric: Name of the counter.
            value: Amount to decrement by (default 1).
        """
        ...

    @abstractmethod
    async def set_gauge(self, metric: str, value: float) -> None:
        """Set a gauge metric to a specific value.

        Args:
            metric: Name of the gauge.
            value: Value to set.
        """
        ...

    @abstractmethod
    async def get_counter(self, metric: str) -> int:
        """Get current counter value.

        Args:
            metric: Name of the counter.

        Returns:
            Current counter value (0 if not set).
        """
        ...

    @abstractmethod
    async def get_stats(self) -> MetricSnapshot:
        """Get aggregated statistics.

        Returns:
            MetricSnapshot with current metrics state.
        """
        ...

    @abstractmethod
    async def reset(self) -> None:
        """Reset all metrics to initial state."""
        ...


class InMemoryMetricsCollector(MetricsCollector):
    """In-memory metrics collector with async-safe operations.

    Provides thread-safe metrics collection suitable for
    single-process deployments and development/testing.

    All operations use an async lock to ensure consistency
    in concurrent contexts.

    Note: Data is lost on process restart.

    Attributes:
        component: Name of the component being monitored.
        max_events: Maximum number of events to retain.
    """

    def __init__(self, component: str, max_events: int = 1000) -> None:
        """Initialize in-memory collector.

        Args:
            component: Name of the component being monitored.
            max_events: Maximum number of events to retain.
        """
        super().__init__(component, max_events)
        self._counters: dict[str, int] = defaultdict(int)
        self._gauges: dict[str, float] = {}
        self._events: list[MetricEvent] = []
        self._event_counts: dict[str, int] = defaultdict(int)
        self._last_reset: datetime | None = None
        self._lock = asyncio.Lock()

    async def record_event(
        self,
        event_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record a metric event.

        Events are stored in a circular buffer limited by max_events.
        Older events are discarded when the limit is reached.

        Args:
            event_type: Type identifier for the event.
            metadata: Optional event-specific data.
        """
        event = MetricEvent(
            event_type=event_type,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
        )

        async with self._lock:
            self._events.append(event)
            self._event_counts[event_type] += 1

            # Trim events if exceeding limit
            if len(self._events) > self.max_events:
                self._events = self._events[-self.max_events :]

    async def increment(self, metric: str, value: int = 1) -> None:
        """Increment a counter metric.

        Args:
            metric: Name of the counter.
            value: Amount to increment by (default 1).
        """
        async with self._lock:
            self._counters[metric] += value

    async def decrement(self, metric: str, value: int = 1) -> None:
        """Decrement a counter metric.

        Args:
            metric: Name of the counter.
            value: Amount to decrement by (default 1).
        """
        async with self._lock:
            self._counters[metric] -= value

    async def set_gauge(self, metric: str, value: float) -> None:
        """Set a gauge metric to a specific value.

        Args:
            metric: Name of the gauge.
            value: Value to set.
        """
        async with self._lock:
            self._gauges[metric] = value

    async def get_counter(self, metric: str) -> int:
        """Get current counter value.

        Args:
            metric: Name of the counter.

        Returns:
            Current counter value (0 if not set).
        """
        async with self._lock:
            return self._counters.get(metric, 0)

    async def get_gauge(self, metric: str) -> float | None:
        """Get current gauge value.

        Args:
            metric: Name of the gauge.

        Returns:
            Current gauge value or None if not set.
        """
        async with self._lock:
            return self._gauges.get(metric)

    async def get_events(
        self,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[MetricEvent]:
        """Get recent events, optionally filtered by type.

        Args:
            event_type: Optional filter for specific event type.
            limit: Maximum events to return.

        Returns:
            List of matching events (newest first).
        """
        async with self._lock:
            events = self._events
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            return list(reversed(events[-limit:]))

    async def get_stats(self) -> MetricSnapshot:
        """Get aggregated statistics.

        Returns:
            MetricSnapshot with current metrics state.
        """
        async with self._lock:
            return MetricSnapshot(
                counters=dict(self._counters),
                events=list(self._events[-100:]),  # Last 100 events in snapshot
                event_counts=dict(self._event_counts),
                last_reset=self._last_reset,
            )

    async def reset(self) -> None:
        """Reset all metrics to initial state."""
        async with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._events.clear()
            self._event_counts.clear()
            self._last_reset = datetime.utcnow()


class MetricsRegistry:
    """Singleton registry for managing metrics collectors.

    Provides centralized access to collectors for different components.
    Uses lazy initialization to create collectors on first access.

    The registry pattern ensures all parts of the application share
    the same collector instances, enabling consistent metrics aggregation.

    Usage:
        # Get the singleton instance
        registry = MetricsRegistry.get_instance()

        # Get or create a collector
        dedup_metrics = registry.get_collector("deduplication")
        throttle_metrics = registry.get_collector("throttling")

        # Get all collectors
        all_collectors = registry.list_collectors()

        # Get combined stats
        combined = await registry.get_all_stats()

    Thread Safety:
        The registry uses an async lock for collector creation to prevent
        race conditions when multiple coroutines request the same collector.
    """

    _instance: ClassVar[MetricsRegistry | None] = None
    _instance_lock: ClassVar[asyncio.Lock | None] = None

    # Component names for standard collectors
    DEDUPLICATION = "deduplication"
    THROTTLING = "throttling"
    ESCALATION = "escalation"
    ROUTING = "routing"
    DISPATCHER = "dispatcher"

    def __init__(self) -> None:
        """Initialize the registry.

        Note: Use get_instance() instead of direct instantiation.
        """
        self._collectors: dict[str, MetricsCollector] = {}
        self._collector_factory = InMemoryMetricsCollector
        self._lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> MetricsRegistry:
        """Get the singleton registry instance.

        Creates a new instance if none exists.

        Returns:
            The singleton MetricsRegistry instance.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance.

        Primarily useful for testing to ensure a clean state.
        """
        cls._instance = None

    def set_collector_factory(
        self,
        factory: type[MetricsCollector],
    ) -> None:
        """Set the factory for creating new collectors.

        Allows switching to a different collector implementation
        (e.g., Redis-based) without changing consumer code.

        Args:
            factory: Class to use for creating collectors.

        Example:
            # Switch to Redis-based collectors
            registry.set_collector_factory(RedisMetricsCollector)
        """
        self._collector_factory = factory

    async def get_collector(
        self,
        component: str,
        max_events: int = 1000,
    ) -> MetricsCollector:
        """Get or create a collector for a component.

        If a collector for the component doesn't exist, creates one
        using the configured factory.

        Args:
            component: Name of the component.
            max_events: Maximum events for new collectors.

        Returns:
            MetricsCollector for the component.
        """
        async with self._lock:
            if component not in self._collectors:
                self._collectors[component] = self._collector_factory(
                    component=component,
                    max_events=max_events,
                )
            return self._collectors[component]

    def get_collector_sync(
        self,
        component: str,
        max_events: int = 1000,
    ) -> MetricsCollector:
        """Synchronous version of get_collector.

        Creates collectors without async lock. Use with caution in
        concurrent contexts - prefer get_collector() when possible.

        Args:
            component: Name of the component.
            max_events: Maximum events for new collectors.

        Returns:
            MetricsCollector for the component.
        """
        if component not in self._collectors:
            self._collectors[component] = self._collector_factory(
                component=component,
                max_events=max_events,
            )
        return self._collectors[component]

    def list_collectors(self) -> list[str]:
        """List all registered component names.

        Returns:
            List of component names with collectors.
        """
        return list(self._collectors.keys())

    async def get_all_stats(self) -> dict[str, MetricSnapshot]:
        """Get stats from all registered collectors.

        Returns:
            Dictionary mapping component names to their snapshots.
        """
        results = {}
        for component, collector in self._collectors.items():
            results[component] = await collector.get_stats()
        return results

    async def reset_all(self) -> None:
        """Reset all collectors.

        Clears metrics for all registered components.
        """
        for collector in self._collectors.values():
            await collector.reset()

    def remove_collector(self, component: str) -> bool:
        """Remove a collector from the registry.

        Args:
            component: Name of the component.

        Returns:
            True if removed, False if not found.
        """
        if component in self._collectors:
            del self._collectors[component]
            return True
        return False
