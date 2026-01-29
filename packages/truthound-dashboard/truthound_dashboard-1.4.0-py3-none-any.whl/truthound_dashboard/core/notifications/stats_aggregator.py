"""Stats aggregation service for notification subsystems.

This module provides efficient stats aggregation using SQLAlchemy
aggregate queries instead of fetching all records. Includes caching
layer for frequently accessed statistics.

The StatsAggregator follows the Repository pattern with caching
to optimize database queries for stats endpoints.

Example:
    aggregator = StatsAggregator(session)

    # Get escalation stats with time range filter
    stats = await aggregator.get_escalation_stats(
        start_time=datetime(2024, 1, 1),
        end_time=datetime(2024, 12, 31),
    )

    # Get deduplication stats with caching (default 30s TTL)
    stats = await aggregator.get_deduplication_stats(use_cache=True)
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.models import (
    DeduplicationConfig,
    EscalationIncidentModel,
    EscalationPolicyModel,
    EscalationStateEnum,
    ThrottlingConfig,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CacheStrategy(str, Enum):
    """Cache strategy options."""

    NONE = "none"
    MEMORY = "memory"
    LFU = "lfu"


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with TTL.

    Attributes:
        value: Cached value.
        expires_at: Expiration timestamp.
        created_at: Creation timestamp.
        hit_count: Number of cache hits.
    """

    value: T
    expires_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)
    hit_count: int = 0

    @property
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        return datetime.utcnow() >= self.expires_at

    @property
    def remaining_ttl_seconds(self) -> float:
        """Get remaining TTL in seconds."""
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.total_seconds())


class StatsCache:
    """Thread-safe in-memory cache for stats with TTL.

    Provides configurable caching with support for:
    - TTL-based expiration
    - Pattern-based invalidation
    - Cache statistics
    """

    def __init__(
        self,
        default_ttl_seconds: int = 30,
        max_entries: int = 100,
    ) -> None:
        """Initialize stats cache.

        Args:
            default_ttl_seconds: Default TTL for cache entries.
            max_entries: Maximum number of cache entries.
        """
        self._cache: dict[str, CacheEntry[Any]] = {}
        self._lock = asyncio.Lock()
        self._default_ttl = default_ttl_seconds
        self._max_entries = max_entries
        self._total_hits = 0
        self._total_misses = 0

    async def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found/expired.
        """
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._total_misses += 1
                return None

            if entry.is_expired:
                del self._cache[key]
                self._total_misses += 1
                return None

            entry.hit_count += 1
            self._total_hits += 1
            return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> None:
        """Set value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl_seconds: TTL in seconds. Uses default if None.
        """
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)

        async with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self._max_entries and key not in self._cache:
                await self._evict_oldest_unlocked()

            self._cache[key] = CacheEntry(
                value=value,
                expires_at=expires_at,
            )

    async def _evict_oldest_unlocked(self) -> None:
        """Evict oldest entry (must be called with lock held)."""
        if not self._cache:
            return

        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].created_at,
        )
        del self._cache[oldest_key]

    async def invalidate(self, key: str) -> bool:
        """Invalidate a specific key.

        Args:
            key: Cache key to invalidate.

        Returns:
            True if key was invalidated.
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def invalidate_pattern(self, prefix: str) -> int:
        """Invalidate all keys with given prefix.

        Args:
            prefix: Key prefix to match.

        Returns:
            Number of keys invalidated.
        """
        async with self._lock:
            keys_to_remove = [k for k in self._cache if k.startswith(prefix)]
            for key in keys_to_remove:
                del self._cache[key]
            return len(keys_to_remove)

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            self._total_hits = 0
            self._total_misses = 0

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics.
        """
        async with self._lock:
            valid_entries = sum(1 for e in self._cache.values() if not e.is_expired)
            total = self._total_hits + self._total_misses
            hit_rate = self._total_hits / total if total > 0 else 0.0

            return {
                "total_entries": len(self._cache),
                "valid_entries": valid_entries,
                "expired_entries": len(self._cache) - valid_entries,
                "max_entries": self._max_entries,
                "default_ttl_seconds": self._default_ttl,
                "total_hits": self._total_hits,
                "total_misses": self._total_misses,
                "hit_rate": hit_rate,
            }


# Global stats cache singleton
_stats_cache: StatsCache | None = None


def get_stats_cache(
    default_ttl_seconds: int = 30,
    max_entries: int = 100,
) -> StatsCache:
    """Get or create stats cache singleton.

    Args:
        default_ttl_seconds: Default TTL for new cache.
        max_entries: Maximum entries for new cache.

    Returns:
        StatsCache instance.
    """
    global _stats_cache
    if _stats_cache is None:
        _stats_cache = StatsCache(
            default_ttl_seconds=default_ttl_seconds,
            max_entries=max_entries,
        )
    return _stats_cache


def reset_stats_cache() -> None:
    """Reset stats cache singleton (for testing)."""
    global _stats_cache
    _stats_cache = None


@dataclass
class TimeRange:
    """Time range filter for stats queries.

    Attributes:
        start_time: Start of time range (inclusive).
        end_time: End of time range (exclusive).
    """

    start_time: datetime | None = None
    end_time: datetime | None = None

    def to_cache_key_part(self) -> str:
        """Generate cache key part for this time range."""
        start_str = self.start_time.isoformat() if self.start_time else "none"
        end_str = self.end_time.isoformat() if self.end_time else "none"
        return f"{start_str}_{end_str}"


@dataclass
class EscalationStatsResult:
    """Escalation statistics result.

    Attributes:
        total_incidents: Total number of incidents.
        by_state: Count by state.
        active_count: Non-resolved incidents count.
        total_policies: Total policies count.
        avg_resolution_time_seconds: Average resolution time in seconds.
        time_range: Time range filter applied.
        cached: Whether result was served from cache.
        cached_at: When result was cached (if cached).
    """

    total_incidents: int
    by_state: dict[str, int]
    active_count: int
    total_policies: int
    avg_resolution_time_seconds: float | None
    time_range: TimeRange | None = None
    cached: bool = False
    cached_at: datetime | None = None


@dataclass
class DeduplicationStatsResult:
    """Deduplication statistics result.

    Attributes:
        total_configs: Total deduplication configs.
        active_configs: Active configs count.
        by_strategy: Count by strategy.
        by_policy: Count by policy.
        avg_window_seconds: Average window duration.
        time_range: Time range filter applied.
        cached: Whether result was served from cache.
        cached_at: When result was cached (if cached).
    """

    total_configs: int
    active_configs: int
    by_strategy: dict[str, int]
    by_policy: dict[str, int]
    avg_window_seconds: float
    time_range: TimeRange | None = None
    cached: bool = False
    cached_at: datetime | None = None


@dataclass
class ThrottlingStatsResult:
    """Throttling statistics result.

    Attributes:
        total_configs: Total throttling configs.
        active_configs: Active configs count.
        configs_with_per_minute: Configs with per-minute limits.
        configs_with_per_hour: Configs with per-hour limits.
        configs_with_per_day: Configs with per-day limits.
        avg_burst_allowance: Average burst allowance.
        time_range: Time range filter applied.
        cached: Whether result was served from cache.
        cached_at: When result was cached (if cached).
    """

    total_configs: int
    active_configs: int
    configs_with_per_minute: int
    configs_with_per_hour: int
    configs_with_per_day: int
    avg_burst_allowance: float
    time_range: TimeRange | None = None
    cached: bool = False
    cached_at: datetime | None = None


class StatsAggregator:
    """Efficient stats aggregation service with caching.

    Uses SQLAlchemy aggregate queries (COUNT, AVG, GROUP BY) instead
    of fetching all records. Includes optional caching layer.

    Example:
        aggregator = StatsAggregator(session, cache_ttl_seconds=60)

        # Get stats with caching
        stats = await aggregator.get_escalation_stats(use_cache=True)

        # Get stats with time range filter
        stats = await aggregator.get_escalation_stats(
            time_range=TimeRange(
                start_time=datetime(2024, 1, 1),
                end_time=datetime(2024, 6, 30),
            )
        )
    """

    def __init__(
        self,
        session: AsyncSession,
        cache: StatsCache | None = None,
        cache_ttl_seconds: int = 30,
    ) -> None:
        """Initialize stats aggregator.

        Args:
            session: Database session.
            cache: Stats cache instance. Uses global singleton if None.
            cache_ttl_seconds: Default cache TTL in seconds.
        """
        self._session = session
        self._cache = cache or get_stats_cache()
        self._cache_ttl = cache_ttl_seconds

    def _generate_cache_key(
        self,
        prefix: str,
        time_range: TimeRange | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate cache key for stats query.

        Args:
            prefix: Key prefix (e.g., "escalation_stats").
            time_range: Optional time range filter.
            **kwargs: Additional key components.

        Returns:
            Cache key string.
        """
        parts = [prefix]

        if time_range:
            parts.append(time_range.to_cache_key_part())
        else:
            parts.append("all_time")

        for key, value in sorted(kwargs.items()):
            parts.append(f"{key}={value}")

        key_string = ":".join(parts)
        # Use hash for long keys
        if len(key_string) > 100:
            key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]
            return f"{prefix}:{key_hash}"
        return key_string

    # =========================================================================
    # Escalation Stats
    # =========================================================================

    async def get_escalation_stats(
        self,
        time_range: TimeRange | None = None,
        use_cache: bool = True,
        cache_ttl_seconds: int | None = None,
    ) -> EscalationStatsResult:
        """Get escalation statistics using efficient aggregate queries.

        Args:
            time_range: Optional time range filter.
            use_cache: Whether to use caching.
            cache_ttl_seconds: Cache TTL override.

        Returns:
            EscalationStatsResult with aggregated statistics.
        """
        cache_key = self._generate_cache_key("escalation_stats", time_range)
        ttl = cache_ttl_seconds if cache_ttl_seconds is not None else self._cache_ttl

        # Try cache first
        if use_cache:
            cached = await self._cache.get(cache_key)
            if cached is not None:
                cached.cached = True
                return cached

        # Build base query with time range filter
        base_query = select(EscalationIncidentModel)
        if time_range:
            if time_range.start_time:
                base_query = base_query.where(
                    EscalationIncidentModel.created_at >= time_range.start_time
                )
            if time_range.end_time:
                base_query = base_query.where(
                    EscalationIncidentModel.created_at < time_range.end_time
                )

        # Query 1: Total count
        count_query = select(func.count(EscalationIncidentModel.id))
        if time_range:
            if time_range.start_time:
                count_query = count_query.where(
                    EscalationIncidentModel.created_at >= time_range.start_time
                )
            if time_range.end_time:
                count_query = count_query.where(
                    EscalationIncidentModel.created_at < time_range.end_time
                )
        result = await self._session.execute(count_query)
        total_incidents = result.scalar() or 0

        # Query 2: Count by state (GROUP BY)
        state_count_query = select(
            EscalationIncidentModel.state,
            func.count(EscalationIncidentModel.id).label("count"),
        ).group_by(EscalationIncidentModel.state)
        if time_range:
            if time_range.start_time:
                state_count_query = state_count_query.where(
                    EscalationIncidentModel.created_at >= time_range.start_time
                )
            if time_range.end_time:
                state_count_query = state_count_query.where(
                    EscalationIncidentModel.created_at < time_range.end_time
                )
        result = await self._session.execute(state_count_query)
        by_state: dict[str, int] = {}
        active_count = 0
        for row in result:
            state = row.state
            count = row.count
            by_state[state] = count
            if state != EscalationStateEnum.RESOLVED.value:
                active_count += count

        # Query 3: Average resolution time for resolved incidents
        avg_resolution_query = select(
            func.avg(
                func.julianday(EscalationIncidentModel.resolved_at)
                - func.julianday(EscalationIncidentModel.created_at)
            ).label("avg_days")
        ).where(
            EscalationIncidentModel.state == EscalationStateEnum.RESOLVED.value,
            EscalationIncidentModel.resolved_at.isnot(None),
        )
        if time_range:
            if time_range.start_time:
                avg_resolution_query = avg_resolution_query.where(
                    EscalationIncidentModel.created_at >= time_range.start_time
                )
            if time_range.end_time:
                avg_resolution_query = avg_resolution_query.where(
                    EscalationIncidentModel.created_at < time_range.end_time
                )
        result = await self._session.execute(avg_resolution_query)
        avg_days = result.scalar()
        # Convert days to seconds
        avg_resolution_seconds = avg_days * 86400 if avg_days else None

        # Query 4: Total policies count
        policies_count_query = select(func.count(EscalationPolicyModel.id))
        result = await self._session.execute(policies_count_query)
        total_policies = result.scalar() or 0

        # Build result
        stats_result = EscalationStatsResult(
            total_incidents=total_incidents,
            by_state=by_state,
            active_count=active_count,
            total_policies=total_policies,
            avg_resolution_time_seconds=avg_resolution_seconds,
            time_range=time_range,
            cached=False,
            cached_at=None,
        )

        # Cache result
        if use_cache:
            stats_result.cached_at = datetime.utcnow()
            await self._cache.set(cache_key, stats_result, ttl)

        return stats_result

    # =========================================================================
    # Deduplication Stats
    # =========================================================================

    async def get_deduplication_stats(
        self,
        time_range: TimeRange | None = None,
        use_cache: bool = True,
        cache_ttl_seconds: int | None = None,
    ) -> DeduplicationStatsResult:
        """Get deduplication configuration statistics.

        Args:
            time_range: Optional time range filter.
            use_cache: Whether to use caching.
            cache_ttl_seconds: Cache TTL override.

        Returns:
            DeduplicationStatsResult with aggregated statistics.
        """
        cache_key = self._generate_cache_key("deduplication_stats", time_range)
        ttl = cache_ttl_seconds if cache_ttl_seconds is not None else self._cache_ttl

        # Try cache first
        if use_cache:
            cached = await self._cache.get(cache_key)
            if cached is not None:
                cached.cached = True
                return cached

        # Query 1: Total and active count
        count_query = select(
            func.count(DeduplicationConfig.id).label("total"),
            func.sum(
                func.cast(DeduplicationConfig.is_active == True, func.Integer)
            ).label("active"),
        )
        if time_range:
            if time_range.start_time:
                count_query = count_query.where(
                    DeduplicationConfig.created_at >= time_range.start_time
                )
            if time_range.end_time:
                count_query = count_query.where(
                    DeduplicationConfig.created_at < time_range.end_time
                )
        result = await self._session.execute(count_query)
        row = result.first()
        total_configs = row.total if row else 0
        active_configs = int(row.active or 0) if row else 0

        # Query 2: Count by strategy (GROUP BY)
        strategy_query = select(
            DeduplicationConfig.strategy,
            func.count(DeduplicationConfig.id).label("count"),
        ).group_by(DeduplicationConfig.strategy)
        if time_range:
            if time_range.start_time:
                strategy_query = strategy_query.where(
                    DeduplicationConfig.created_at >= time_range.start_time
                )
            if time_range.end_time:
                strategy_query = strategy_query.where(
                    DeduplicationConfig.created_at < time_range.end_time
                )
        result = await self._session.execute(strategy_query)
        by_strategy = {row.strategy: row.count for row in result}

        # Query 3: Count by policy (GROUP BY)
        policy_query = select(
            DeduplicationConfig.policy,
            func.count(DeduplicationConfig.id).label("count"),
        ).group_by(DeduplicationConfig.policy)
        if time_range:
            if time_range.start_time:
                policy_query = policy_query.where(
                    DeduplicationConfig.created_at >= time_range.start_time
                )
            if time_range.end_time:
                policy_query = policy_query.where(
                    DeduplicationConfig.created_at < time_range.end_time
                )
        result = await self._session.execute(policy_query)
        by_policy = {row.policy: row.count for row in result}

        # Query 4: Average window seconds
        avg_window_query = select(
            func.avg(DeduplicationConfig.window_seconds).label("avg_window")
        )
        if time_range:
            if time_range.start_time:
                avg_window_query = avg_window_query.where(
                    DeduplicationConfig.created_at >= time_range.start_time
                )
            if time_range.end_time:
                avg_window_query = avg_window_query.where(
                    DeduplicationConfig.created_at < time_range.end_time
                )
        result = await self._session.execute(avg_window_query)
        avg_window = result.scalar() or 0.0

        # Build result
        stats_result = DeduplicationStatsResult(
            total_configs=total_configs,
            active_configs=active_configs,
            by_strategy=by_strategy,
            by_policy=by_policy,
            avg_window_seconds=float(avg_window),
            time_range=time_range,
            cached=False,
            cached_at=None,
        )

        # Cache result
        if use_cache:
            stats_result.cached_at = datetime.utcnow()
            await self._cache.set(cache_key, stats_result, ttl)

        return stats_result

    # =========================================================================
    # Throttling Stats
    # =========================================================================

    async def get_throttling_stats(
        self,
        time_range: TimeRange | None = None,
        use_cache: bool = True,
        cache_ttl_seconds: int | None = None,
    ) -> ThrottlingStatsResult:
        """Get throttling configuration statistics.

        Args:
            time_range: Optional time range filter.
            use_cache: Whether to use caching.
            cache_ttl_seconds: Cache TTL override.

        Returns:
            ThrottlingStatsResult with aggregated statistics.
        """
        cache_key = self._generate_cache_key("throttling_stats", time_range)
        ttl = cache_ttl_seconds if cache_ttl_seconds is not None else self._cache_ttl

        # Try cache first
        if use_cache:
            cached = await self._cache.get(cache_key)
            if cached is not None:
                cached.cached = True
                return cached

        # Query 1: Total, active, and limit counts
        count_query = select(
            func.count(ThrottlingConfig.id).label("total"),
            func.sum(
                func.cast(ThrottlingConfig.is_active == True, func.Integer)
            ).label("active"),
            func.sum(
                func.cast(ThrottlingConfig.per_minute.isnot(None), func.Integer)
            ).label("with_per_minute"),
            func.sum(
                func.cast(ThrottlingConfig.per_hour.isnot(None), func.Integer)
            ).label("with_per_hour"),
            func.sum(
                func.cast(ThrottlingConfig.per_day.isnot(None), func.Integer)
            ).label("with_per_day"),
            func.avg(ThrottlingConfig.burst_allowance).label("avg_burst"),
        )
        if time_range:
            if time_range.start_time:
                count_query = count_query.where(
                    ThrottlingConfig.created_at >= time_range.start_time
                )
            if time_range.end_time:
                count_query = count_query.where(
                    ThrottlingConfig.created_at < time_range.end_time
                )

        result = await self._session.execute(count_query)
        row = result.first()

        total_configs = row.total if row else 0
        active_configs = int(row.active or 0) if row else 0
        configs_with_per_minute = int(row.with_per_minute or 0) if row else 0
        configs_with_per_hour = int(row.with_per_hour or 0) if row else 0
        configs_with_per_day = int(row.with_per_day or 0) if row else 0
        avg_burst = float(row.avg_burst or 0.0) if row else 0.0

        # Build result
        stats_result = ThrottlingStatsResult(
            total_configs=total_configs,
            active_configs=active_configs,
            configs_with_per_minute=configs_with_per_minute,
            configs_with_per_hour=configs_with_per_hour,
            configs_with_per_day=configs_with_per_day,
            avg_burst_allowance=avg_burst,
            time_range=time_range,
            cached=False,
            cached_at=None,
        )

        # Cache result
        if use_cache:
            stats_result.cached_at = datetime.utcnow()
            await self._cache.set(cache_key, stats_result, ttl)

        return stats_result

    # =========================================================================
    # Batch Aggregation
    # =========================================================================

    async def get_all_stats(
        self,
        time_range: TimeRange | None = None,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """Get all notification stats in a single call.

        Executes stats queries in parallel for better performance.

        Args:
            time_range: Optional time range filter.
            use_cache: Whether to use caching.

        Returns:
            Dictionary with all stats results.
        """
        # Run all stats queries in parallel
        escalation_task = self.get_escalation_stats(time_range, use_cache)
        deduplication_task = self.get_deduplication_stats(time_range, use_cache)
        throttling_task = self.get_throttling_stats(time_range, use_cache)

        escalation_stats, deduplication_stats, throttling_stats = await asyncio.gather(
            escalation_task,
            deduplication_task,
            throttling_task,
        )

        return {
            "escalation": escalation_stats,
            "deduplication": deduplication_stats,
            "throttling": throttling_stats,
            "time_range": {
                "start_time": time_range.start_time.isoformat()
                if time_range and time_range.start_time
                else None,
                "end_time": time_range.end_time.isoformat()
                if time_range and time_range.end_time
                else None,
            },
        }

    # =========================================================================
    # Cache Management
    # =========================================================================

    async def invalidate_escalation_cache(self) -> int:
        """Invalidate all escalation stats cache entries.

        Returns:
            Number of entries invalidated.
        """
        return await self._cache.invalidate_pattern("escalation_stats")

    async def invalidate_deduplication_cache(self) -> int:
        """Invalidate all deduplication stats cache entries.

        Returns:
            Number of entries invalidated.
        """
        return await self._cache.invalidate_pattern("deduplication_stats")

    async def invalidate_throttling_cache(self) -> int:
        """Invalidate all throttling stats cache entries.

        Returns:
            Number of entries invalidated.
        """
        return await self._cache.invalidate_pattern("throttling_stats")

    async def invalidate_all_cache(self) -> None:
        """Invalidate all stats cache entries."""
        await self._cache.clear()

    async def get_cache_stats(self) -> dict[str, Any]:
        """Get stats cache statistics.

        Returns:
            Dictionary with cache statistics.
        """
        return await self._cache.get_stats()
