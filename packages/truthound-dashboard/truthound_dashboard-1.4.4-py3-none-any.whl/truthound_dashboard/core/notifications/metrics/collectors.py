"""Specialized metrics collectors for notification subsystems.

This module provides thread-safe metrics collectors for:
- DeduplicationMetrics: Track deduplication rates and active fingerprints
- ThrottlingMetrics: Track throttling rates and window counts
- EscalationMetrics: Track incidents by state and resolution times

All collectors use asyncio.Lock for thread-safe operations.

Example:
    # Create metrics collector
    dedup_metrics = DeduplicationMetrics()

    # Record events
    await dedup_metrics.record_received()
    if is_duplicate:
        await dedup_metrics.record_deduplicated()
    else:
        await dedup_metrics.record_passed()

    # Get statistics
    stats = await dedup_metrics.get_stats()
    print(f"Deduplication rate: {stats['dedup_rate']:.2%}")
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class DeduplicationStats:
    """Statistics from deduplication metrics.

    Attributes:
        total_received: Total notifications received.
        total_deduplicated: Total notifications deduplicated (skipped).
        total_passed: Total notifications passed through.
        dedup_rate: Deduplication rate (0.0 to 1.0).
        active_fingerprints: Number of active fingerprints being tracked.
    """

    total_received: int
    total_deduplicated: int
    total_passed: int
    dedup_rate: float
    active_fingerprints: int

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "total_received": self.total_received,
            "total_deduplicated": self.total_deduplicated,
            "total_passed": self.total_passed,
            "dedup_rate": self.dedup_rate,
            "active_fingerprints": self.active_fingerprints,
        }


class DeduplicationMetrics:
    """Thread-safe metrics collector for deduplication.

    Tracks total notifications received, deduplicated, and passed through
    the deduplication service.

    Example:
        metrics = DeduplicationMetrics()

        # Record a received notification
        await metrics.record_received()

        # Record deduplication decision
        if is_duplicate:
            await metrics.record_deduplicated()
        else:
            await metrics.record_passed()

        # Get current stats
        stats = await metrics.get_stats()
    """

    def __init__(self) -> None:
        """Initialize deduplication metrics."""
        self._lock = asyncio.Lock()
        self._total_received: int = 0
        self._total_deduplicated: int = 0
        self._total_passed: int = 0
        self._active_fingerprints: set[str] = set()

    async def record_received(self, fingerprint: str | None = None) -> None:
        """Record a notification received for deduplication check.

        Args:
            fingerprint: Optional fingerprint to track as active.
        """
        async with self._lock:
            self._total_received += 1
            if fingerprint:
                self._active_fingerprints.add(fingerprint)

    async def record_deduplicated(self, fingerprint: str | None = None) -> None:
        """Record a notification that was deduplicated (skipped).

        Args:
            fingerprint: Optional fingerprint that was deduplicated.
        """
        async with self._lock:
            self._total_deduplicated += 1

    async def record_passed(self, fingerprint: str | None = None) -> None:
        """Record a notification that passed deduplication.

        Args:
            fingerprint: Optional fingerprint that passed.
        """
        async with self._lock:
            self._total_passed += 1

    async def remove_fingerprint(self, fingerprint: str) -> None:
        """Remove a fingerprint from active tracking.

        Args:
            fingerprint: Fingerprint to remove.
        """
        async with self._lock:
            self._active_fingerprints.discard(fingerprint)

    async def clear_fingerprints(self) -> None:
        """Clear all active fingerprints."""
        async with self._lock:
            self._active_fingerprints.clear()

    async def get_stats(self) -> DeduplicationStats:
        """Get current deduplication statistics.

        Returns:
            DeduplicationStats with current metrics.
        """
        async with self._lock:
            total_received = self._total_received
            total_deduplicated = self._total_deduplicated
            total_passed = self._total_passed
            active_fingerprints = len(self._active_fingerprints)

        # Calculate dedup rate
        dedup_rate = 0.0
        if total_received > 0:
            dedup_rate = total_deduplicated / total_received

        return DeduplicationStats(
            total_received=total_received,
            total_deduplicated=total_deduplicated,
            total_passed=total_passed,
            dedup_rate=dedup_rate,
            active_fingerprints=active_fingerprints,
        )

    async def reset(self) -> None:
        """Reset all counters and fingerprints."""
        async with self._lock:
            self._total_received = 0
            self._total_deduplicated = 0
            self._total_passed = 0
            self._active_fingerprints.clear()


@dataclass
class ThrottlingStats:
    """Statistics from throttling metrics.

    Attributes:
        total_received: Total requests received.
        total_throttled: Total requests throttled (rejected).
        total_passed: Total requests passed through.
        throttle_rate: Throttle rate (0.0 to 1.0).
        current_window_count: Number of requests in current window.
    """

    total_received: int
    total_throttled: int
    total_passed: int
    throttle_rate: float
    current_window_count: int

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "total_received": self.total_received,
            "total_throttled": self.total_throttled,
            "total_passed": self.total_passed,
            "throttle_rate": self.throttle_rate,
            "current_window_count": self.current_window_count,
        }


@dataclass
class WindowCount:
    """Tracks counts within a time window.

    Attributes:
        window_start: Start timestamp of the window.
        count: Number of requests in this window.
    """

    window_start: datetime
    count: int = 0


class ThrottlingMetrics:
    """Thread-safe metrics collector for throttling.

    Tracks total requests received, throttled, and passed through
    the throttling service. Also tracks current window counts.

    Example:
        metrics = ThrottlingMetrics(window_seconds=60)

        # Record a received request
        await metrics.record_received()

        # Record throttling decision
        if is_throttled:
            await metrics.record_throttled()
        else:
            await metrics.record_passed()

        # Get current stats
        stats = await metrics.get_stats()
    """

    def __init__(self, window_seconds: int = 60) -> None:
        """Initialize throttling metrics.

        Args:
            window_seconds: Window duration for current_window_count tracking.
        """
        self._lock = asyncio.Lock()
        self._total_received: int = 0
        self._total_throttled: int = 0
        self._total_passed: int = 0
        self._window_seconds = window_seconds
        self._current_window: WindowCount | None = None

    def _get_window_start(self, now: datetime) -> datetime:
        """Get the start of the current window.

        Args:
            now: Current timestamp.

        Returns:
            Window start timestamp.
        """
        # Align to window boundaries
        timestamp = now.timestamp()
        window_start_ts = int(timestamp // self._window_seconds) * self._window_seconds
        return datetime.fromtimestamp(window_start_ts)

    async def record_received(self) -> None:
        """Record a request received for throttle check."""
        async with self._lock:
            self._total_received += 1
            self._increment_window_count()

    async def record_throttled(self) -> None:
        """Record a request that was throttled (rejected)."""
        async with self._lock:
            self._total_throttled += 1

    async def record_passed(self) -> None:
        """Record a request that passed throttling."""
        async with self._lock:
            self._total_passed += 1

    def _increment_window_count(self) -> None:
        """Increment the current window count (must be called with lock held)."""
        now = datetime.utcnow()
        window_start = self._get_window_start(now)

        if self._current_window is None or self._current_window.window_start != window_start:
            # Start new window
            self._current_window = WindowCount(window_start=window_start, count=1)
        else:
            # Increment existing window
            self._current_window.count += 1

    async def get_stats(self) -> ThrottlingStats:
        """Get current throttling statistics.

        Returns:
            ThrottlingStats with current metrics.
        """
        async with self._lock:
            total_received = self._total_received
            total_throttled = self._total_throttled
            total_passed = self._total_passed

            # Get current window count
            now = datetime.utcnow()
            window_start = self._get_window_start(now)
            current_window_count = 0
            if (
                self._current_window is not None
                and self._current_window.window_start == window_start
            ):
                current_window_count = self._current_window.count

        # Calculate throttle rate
        throttle_rate = 0.0
        if total_received > 0:
            throttle_rate = total_throttled / total_received

        return ThrottlingStats(
            total_received=total_received,
            total_throttled=total_throttled,
            total_passed=total_passed,
            throttle_rate=throttle_rate,
            current_window_count=current_window_count,
        )

    async def reset(self) -> None:
        """Reset all counters."""
        async with self._lock:
            self._total_received = 0
            self._total_throttled = 0
            self._total_passed = 0
            self._current_window = None


@dataclass
class EscalationStats:
    """Statistics from escalation metrics.

    Attributes:
        total_incidents: Total incidents tracked.
        by_state: Count of incidents by state.
        active_count: Number of active (non-resolved) incidents.
        avg_resolution_time: Average resolution time in seconds.
    """

    total_incidents: int
    by_state: dict[str, int]
    active_count: int
    avg_resolution_time: float

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "total_incidents": self.total_incidents,
            "by_state": self.by_state,
            "active_count": self.active_count,
            "avg_resolution_time": self.avg_resolution_time,
        }


@dataclass
class IncidentRecord:
    """Record of an incident for metrics tracking.

    Attributes:
        incident_id: Unique incident identifier.
        state: Current incident state.
        created_at: When incident was created.
        resolved_at: When incident was resolved (if applicable).
    """

    incident_id: str
    state: str
    created_at: datetime
    resolved_at: datetime | None = None


class EscalationMetrics:
    """Thread-safe metrics collector for escalation.

    Tracks incidents by state and calculates resolution times.

    Example:
        metrics = EscalationMetrics()

        # Record incident creation
        await metrics.record_incident_created("incident-1")

        # Update incident state
        await metrics.record_state_change("incident-1", "triggered")
        await metrics.record_state_change("incident-1", "acknowledged")

        # Record resolution
        await metrics.record_incident_resolved("incident-1")

        # Get current stats
        stats = await metrics.get_stats()
    """

    def __init__(self) -> None:
        """Initialize escalation metrics."""
        self._lock = asyncio.Lock()
        self._incidents: dict[str, IncidentRecord] = {}
        self._resolution_times: list[float] = []

    async def record_incident_created(
        self,
        incident_id: str,
        initial_state: str = "pending",
    ) -> None:
        """Record a new incident creation.

        Args:
            incident_id: Unique incident identifier.
            initial_state: Initial state of the incident.
        """
        async with self._lock:
            self._incidents[incident_id] = IncidentRecord(
                incident_id=incident_id,
                state=initial_state,
                created_at=datetime.utcnow(),
            )

    async def record_state_change(
        self,
        incident_id: str,
        new_state: str,
    ) -> None:
        """Record an incident state change.

        Args:
            incident_id: Incident identifier.
            new_state: New state of the incident.
        """
        async with self._lock:
            if incident_id in self._incidents:
                self._incidents[incident_id].state = new_state

    async def record_incident_resolved(
        self,
        incident_id: str,
    ) -> None:
        """Record an incident resolution.

        Args:
            incident_id: Incident identifier.
        """
        async with self._lock:
            if incident_id in self._incidents:
                incident = self._incidents[incident_id]
                incident.state = "resolved"
                incident.resolved_at = datetime.utcnow()

                # Calculate resolution time
                resolution_time = (
                    incident.resolved_at - incident.created_at
                ).total_seconds()
                self._resolution_times.append(resolution_time)

    async def remove_incident(self, incident_id: str) -> None:
        """Remove an incident from tracking.

        Args:
            incident_id: Incident identifier.
        """
        async with self._lock:
            self._incidents.pop(incident_id, None)

    async def get_stats(self) -> EscalationStats:
        """Get current escalation statistics.

        Returns:
            EscalationStats with current metrics.
        """
        async with self._lock:
            total_incidents = len(self._incidents)

            # Count by state
            by_state: dict[str, int] = {}
            active_count = 0
            for incident in self._incidents.values():
                state = incident.state
                by_state[state] = by_state.get(state, 0) + 1
                if state != "resolved":
                    active_count += 1

            # Calculate average resolution time
            avg_resolution_time = 0.0
            if self._resolution_times:
                avg_resolution_time = sum(self._resolution_times) / len(
                    self._resolution_times
                )

        return EscalationStats(
            total_incidents=total_incidents,
            by_state=by_state,
            active_count=active_count,
            avg_resolution_time=avg_resolution_time,
        )

    async def reset(self) -> None:
        """Reset all incident tracking and resolution times."""
        async with self._lock:
            self._incidents.clear()
            self._resolution_times.clear()


# Convenience alias for combined metrics
@dataclass
class NotificationMetrics:
    """Combined metrics from all notification subsystems.

    Attributes:
        deduplication: Deduplication statistics.
        throttling: Throttling statistics.
        escalation: Escalation statistics.
    """

    deduplication: DeduplicationStats
    throttling: ThrottlingStats
    escalation: EscalationStats

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "deduplication": self.deduplication.to_dict(),
            "throttling": self.throttling.to_dict(),
            "escalation": self.escalation.to_dict(),
        }


class MetricsCollector:
    """Aggregated metrics collector for notification subsystems.

    Provides a single interface to collect metrics from deduplication,
    throttling, and escalation services.

    Example:
        collector = MetricsCollector()

        # Record deduplication metrics
        await collector.deduplication.record_received()
        await collector.deduplication.record_deduplicated()

        # Record throttling metrics
        await collector.throttling.record_received()
        await collector.throttling.record_passed()

        # Record escalation metrics
        await collector.escalation.record_incident_created("inc-1")

        # Get combined stats
        stats = await collector.get_all_stats()
    """

    def __init__(self, throttling_window_seconds: int = 60) -> None:
        """Initialize metrics collector.

        Args:
            throttling_window_seconds: Window duration for throttling metrics.
        """
        self.deduplication = DeduplicationMetrics()
        self.throttling = ThrottlingMetrics(window_seconds=throttling_window_seconds)
        self.escalation = EscalationMetrics()

    async def get_all_stats(self) -> NotificationMetrics:
        """Get combined statistics from all collectors.

        Returns:
            NotificationMetrics with stats from all subsystems.
        """
        dedup_stats = await self.deduplication.get_stats()
        throttle_stats = await self.throttling.get_stats()
        escalation_stats = await self.escalation.get_stats()

        return NotificationMetrics(
            deduplication=dedup_stats,
            throttling=throttle_stats,
            escalation=escalation_stats,
        )

    async def reset_all(self) -> None:
        """Reset all metrics collectors."""
        await self.deduplication.reset()
        await self.throttling.reset()
        await self.escalation.reset()
