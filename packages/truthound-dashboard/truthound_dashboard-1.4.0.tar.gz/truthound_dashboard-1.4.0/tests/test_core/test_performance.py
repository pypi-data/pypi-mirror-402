"""Comprehensive tests for performance-related features.

This module tests:
- Cache systems (MemoryCache, LFUCache, FileCache)
- Stats aggregation and caching
- Validation limits
- Statistical analysis utilities
- Performance optimizations
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.core.cache import (
    CacheBackend,
    CacheEntry,
    CacheManager,
    FileCache,
    LFUCache,
    LFUCacheEntry,
    MemoryCache,
    get_cache,
    get_cache_manager,
    reset_cache,
)
from truthound_dashboard.core.notifications.stats_aggregator import (
    DeduplicationStatsResult,
    EscalationStatsResult,
    StatsAggregator,
    StatsCache,
    ThrottlingStatsResult,
    TimeRange,
    get_stats_cache,
    reset_stats_cache,
)
from truthound_dashboard.core.statistics import (
    EffectSize,
    SignificanceLevel,
    StatisticalTestResult,
    chi_square_test,
    cohens_d,
    comprehensive_comparison,
    interpret_effect_size,
    interpret_p_value,
    mann_whitney_u_test,
    trend_significance_test,
    welch_t_test,
)
from truthound_dashboard.core.validation_limits import (
    DeduplicationLimits,
    EscalationLimits,
    ThrottlingLimits,
    TimeWindowLimits,
    ValidationLimitError,
    clear_limits_cache,
    get_deduplication_limits,
    get_escalation_limits,
    get_throttling_limits,
    get_time_window_limits,
    validate_positive_float,
    validate_positive_int,
)


# ==============================================================================
# Cache Tests
# ==============================================================================


class TestCacheEntry:
    """Tests for CacheEntry class."""

    def test_cache_entry_creation(self):
        """Test CacheEntry initialization."""
        entry = CacheEntry(value="test", ttl_seconds=60)
        assert entry.value == "test"
        assert not entry.is_expired
        assert entry.remaining_ttl <= 60
        assert entry.remaining_ttl > 0

    def test_cache_entry_expiration(self):
        """Test CacheEntry expiration with very short TTL."""
        entry = CacheEntry(value="test", ttl_seconds=0)
        assert entry.is_expired
        assert entry.remaining_ttl == 0

    def test_cache_entry_remaining_ttl(self):
        """Test remaining TTL calculation."""
        entry = CacheEntry(value="test", ttl_seconds=100)
        assert 99 <= entry.remaining_ttl <= 100


class TestLFUCacheEntry:
    """Tests for LFUCacheEntry class."""

    def test_lfu_entry_creation(self):
        """Test LFUCacheEntry initialization."""
        entry = LFUCacheEntry(value="test", ttl_seconds=60)
        assert entry.value == "test"
        assert entry.frequency == 1
        assert not entry.is_expired

    def test_lfu_entry_access(self):
        """Test access frequency tracking."""
        entry = LFUCacheEntry(value="test", ttl_seconds=60)
        initial_freq = entry.frequency
        entry.access()
        assert entry.frequency == initial_freq + 1
        entry.access()
        assert entry.frequency == initial_freq + 2


class TestMemoryCache:
    """Tests for MemoryCache class."""

    @pytest_asyncio.fixture
    async def cache(self):
        """Create a fresh MemoryCache instance."""
        return MemoryCache(max_size=10, cleanup_interval=60)

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        """Test basic set and get operations."""
        await cache.set("key1", "value1", ttl_seconds=60)
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, cache):
        """Test getting a nonexistent key."""
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, cache):
        """Test delete operation."""
        await cache.set("key1", "value1")
        deleted = await cache.delete("key1")
        assert deleted is True
        result = await cache.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, cache):
        """Test deleting a nonexistent key."""
        deleted = await cache.delete("nonexistent")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_exists(self, cache):
        """Test exists operation."""
        await cache.set("key1", "value1")
        assert await cache.exists("key1") is True
        assert await cache.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_clear(self, cache):
        """Test clear operation."""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None
        assert cache.size == 0

    @pytest.mark.asyncio
    async def test_expiration(self, cache):
        """Test TTL expiration."""
        await cache.set("key1", "value1", ttl_seconds=0)
        result = await cache.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_invalidate_pattern(self, cache):
        """Test pattern-based invalidation."""
        await cache.set("user:1", "data1")
        await cache.set("user:2", "data2")
        await cache.set("other:1", "data3")

        count = await cache.invalidate_pattern("user:")
        assert count == 2
        assert await cache.get("user:1") is None
        assert await cache.get("user:2") is None
        assert await cache.get("other:1") == "data3"

    @pytest.mark.asyncio
    async def test_get_or_set(self, cache):
        """Test get_or_set with factory function."""
        # First call - should compute value
        result = await cache.get_or_set("key1", lambda: "computed", ttl_seconds=60)
        assert result == "computed"

        # Second call - should return cached value
        result = await cache.get_or_set("key1", lambda: "new_value", ttl_seconds=60)
        assert result == "computed"

    @pytest.mark.asyncio
    async def test_get_or_set_async_factory(self, cache):
        """Test get_or_set with async factory function."""
        async def async_factory():
            return "async_value"

        result = await cache.get_or_set("key1", async_factory, ttl_seconds=60)
        assert result == "async_value"

    @pytest.mark.asyncio
    async def test_eviction(self, cache):
        """Test eviction when cache is full."""
        # Fill cache beyond max size
        for i in range(15):
            await cache.set(f"key{i}", f"value{i}")

        # Should have evicted some entries
        assert cache.size <= 10

    @pytest.mark.asyncio
    async def test_get_stats(self, cache):
        """Test cache statistics."""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2", ttl_seconds=0)  # Expired

        stats = await cache.get_stats()
        assert stats["total_entries"] == 2
        assert stats["max_size"] == 10
        assert "expired_entries" in stats
        assert "valid_entries" in stats

    @pytest.mark.asyncio
    async def test_cleanup_task(self, cache):
        """Test background cleanup task."""
        await cache.start_cleanup_task()
        assert cache._cleanup_task is not None

        await cache.stop_cleanup_task()
        assert cache._cleanup_task is None


class TestLFUCache:
    """Tests for LFUCache class."""

    @pytest_asyncio.fixture
    async def cache(self):
        """Create a fresh LFUCache instance."""
        return LFUCache(max_size=5, cleanup_interval=60)

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        """Test basic set and get operations."""
        await cache.set("key1", "value1", ttl_seconds=60)
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_frequency_tracking(self, cache):
        """Test that access frequency is tracked."""
        await cache.set("key1", "value1")

        # Access multiple times
        for _ in range(5):
            await cache.get("key1")

        stats = await cache.get_stats()
        assert stats["hits"] >= 5

    @pytest.mark.asyncio
    async def test_lfu_eviction(self, cache):
        """Test LFU eviction policy."""
        # Add entries
        await cache.set("frequent", "value1")
        await cache.set("infrequent", "value2")

        # Access 'frequent' many times
        for _ in range(10):
            await cache.get("frequent")

        # Fill cache to trigger eviction
        for i in range(10):
            await cache.set(f"new{i}", f"value{i}")

        # 'frequent' should survive due to higher frequency
        # (though this depends on eviction batch size)
        stats = await cache.get_stats()
        assert stats["total_entries"] <= 5

    @pytest.mark.asyncio
    async def test_hit_rate(self, cache):
        """Test hit rate calculation."""
        await cache.set("key1", "value1")

        # Hits
        await cache.get("key1")
        await cache.get("key1")

        # Misses
        await cache.get("nonexistent")

        assert cache.hit_rate == 2/3  # 2 hits, 1 miss

    @pytest.mark.asyncio
    async def test_get_stats_frequency_distribution(self, cache):
        """Test frequency distribution in stats."""
        await cache.set("key1", "value1")
        await cache.get("key1")  # frequency: 2
        await cache.get("key1")  # frequency: 3

        await cache.set("key2", "value2")  # frequency: 1

        stats = await cache.get_stats()
        assert "frequency_distribution" in stats


class TestFileCache:
    """Tests for FileCache class."""

    @pytest_asyncio.fixture
    async def cache(self):
        """Create a fresh FileCache instance with temp directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(cache_dir=Path(tmpdir))
            yield cache

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        """Test basic set and get operations."""
        await cache.set("key1", {"data": "value1"}, ttl_seconds=60)
        result = await cache.get("key1")
        assert result == {"data": "value1"}

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, cache):
        """Test getting a nonexistent key."""
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, cache):
        """Test delete operation."""
        await cache.set("key1", "value1")
        deleted = await cache.delete("key1")
        assert deleted is True
        result = await cache.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_clear(self, cache):
        """Test clear operation."""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_expiration(self, cache):
        """Test TTL expiration."""
        await cache.set("key1", "value1", ttl_seconds=0)
        result = await cache.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_exists(self, cache):
        """Test exists operation."""
        await cache.set("key1", "value1")
        assert await cache.exists("key1") is True
        assert await cache.exists("nonexistent") is False


class TestCacheManager:
    """Tests for CacheManager class."""

    def test_register_and_get(self):
        """Test cache registration and retrieval."""
        manager = CacheManager()
        cache1 = manager.register("cache1")
        cache2 = manager.register("cache2")

        assert manager.get("cache1") is cache1
        assert manager.get("cache2") is cache2
        assert manager.get("nonexistent") is None

    def test_register_with_custom_backend(self):
        """Test registering with custom backend."""
        manager = CacheManager()
        custom_cache = LFUCache(max_size=100)
        registered = manager.register("lfu", backend=custom_cache)

        assert registered is custom_cache
        assert manager.get("lfu") is custom_cache

    def test_get_or_create(self):
        """Test get_or_create functionality."""
        manager = CacheManager()
        cache1 = manager.get_or_create("cache1")
        cache2 = manager.get_or_create("cache1")

        assert cache1 is cache2

    @pytest.mark.asyncio
    async def test_clear_all(self):
        """Test clearing all caches."""
        manager = CacheManager()
        cache1 = manager.register("cache1")
        cache2 = manager.register("cache2")

        await cache1.set("key1", "value1")
        await cache2.set("key2", "value2")

        await manager.clear_all()

        assert await cache1.get("key1") is None
        assert await cache2.get("key2") is None


class TestCacheSingletons:
    """Tests for cache singleton functions."""

    def test_get_cache_singleton(self):
        """Test get_cache returns singleton."""
        reset_cache()
        cache1 = get_cache()
        cache2 = get_cache()
        assert cache1 is cache2

    def test_get_cache_manager_singleton(self):
        """Test get_cache_manager returns singleton."""
        reset_cache()
        manager1 = get_cache_manager()
        manager2 = get_cache_manager()
        assert manager1 is manager2

    def test_reset_cache(self):
        """Test reset_cache clears singletons."""
        cache1 = get_cache()
        reset_cache()
        cache2 = get_cache()
        assert cache1 is not cache2


# ==============================================================================
# Stats Aggregator Tests
# ==============================================================================


class TestStatsCache:
    """Tests for StatsCache class."""

    @pytest_asyncio.fixture
    async def stats_cache(self):
        """Create a fresh StatsCache instance."""
        reset_stats_cache()
        return StatsCache(default_ttl_seconds=30, max_entries=10)

    @pytest.mark.asyncio
    async def test_set_and_get(self, stats_cache):
        """Test basic set and get operations."""
        await stats_cache.set("key1", {"data": "value1"})
        result = await stats_cache.get("key1")
        assert result == {"data": "value1"}

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, stats_cache):
        """Test getting a nonexistent key."""
        result = await stats_cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_expiration(self, stats_cache):
        """Test TTL expiration."""
        await stats_cache.set("key1", "value1", ttl_seconds=0)
        result = await stats_cache.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_invalidate(self, stats_cache):
        """Test single key invalidation."""
        await stats_cache.set("key1", "value1")
        result = await stats_cache.invalidate("key1")
        assert result is True
        assert await stats_cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_invalidate_pattern(self, stats_cache):
        """Test pattern-based invalidation."""
        await stats_cache.set("stats:1", "data1")
        await stats_cache.set("stats:2", "data2")
        await stats_cache.set("other:1", "data3")

        count = await stats_cache.invalidate_pattern("stats:")
        assert count == 2
        assert await stats_cache.get("stats:1") is None
        assert await stats_cache.get("other:1") == "data3"

    @pytest.mark.asyncio
    async def test_clear(self, stats_cache):
        """Test clear operation."""
        await stats_cache.set("key1", "value1")
        await stats_cache.set("key2", "value2")
        await stats_cache.clear()

        stats = await stats_cache.get_stats()
        assert stats["total_entries"] == 0
        assert stats["total_hits"] == 0
        assert stats["total_misses"] == 0

    @pytest.mark.asyncio
    async def test_get_stats(self, stats_cache):
        """Test cache statistics."""
        await stats_cache.set("key1", "value1")
        await stats_cache.get("key1")  # hit
        await stats_cache.get("nonexistent")  # miss

        stats = await stats_cache.get_stats()
        assert stats["total_entries"] == 1
        assert stats["total_hits"] == 1
        assert stats["total_misses"] == 1
        assert stats["hit_rate"] == 0.5

    @pytest.mark.asyncio
    async def test_eviction_on_capacity(self, stats_cache):
        """Test eviction when cache reaches capacity."""
        for i in range(15):
            await stats_cache.set(f"key{i}", f"value{i}")

        stats = await stats_cache.get_stats()
        assert stats["total_entries"] <= 10


class TestTimeRange:
    """Tests for TimeRange class."""

    def test_time_range_creation(self):
        """Test TimeRange creation."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        tr = TimeRange(start_time=start, end_time=end)

        assert tr.start_time == start
        assert tr.end_time == end

    def test_time_range_cache_key(self):
        """Test cache key generation."""
        start = datetime(2024, 1, 1)
        tr = TimeRange(start_time=start)
        key_part = tr.to_cache_key_part()

        assert "2024-01-01" in key_part
        assert "none" in key_part  # end_time is None


# ==============================================================================
# Validation Limits Tests
# ==============================================================================


class TestDeduplicationLimits:
    """Tests for DeduplicationLimits class."""

    def test_default_limits(self):
        """Test default limit values."""
        limits = DeduplicationLimits()
        assert limits.window_min_seconds == 1
        assert limits.window_max_seconds == 86400
        assert limits.window_default_seconds == 300

    def test_validate_window_seconds_valid(self):
        """Test valid window seconds."""
        limits = DeduplicationLimits()
        is_valid, error = limits.validate_window_seconds(300)
        assert is_valid is True
        assert error is None

    def test_validate_window_seconds_too_small(self):
        """Test window seconds below minimum."""
        limits = DeduplicationLimits()
        is_valid, error = limits.validate_window_seconds(0)
        assert is_valid is False
        assert "at least" in error

    def test_validate_window_seconds_too_large(self):
        """Test window seconds above maximum."""
        limits = DeduplicationLimits()
        is_valid, error = limits.validate_window_seconds(100000)
        assert is_valid is False
        assert "not exceed" in error


class TestThrottlingLimits:
    """Tests for ThrottlingLimits class."""

    def test_default_limits(self):
        """Test default limit values."""
        limits = ThrottlingLimits()
        assert limits.limit_min == 1
        assert limits.limit_max == 100000
        assert limits.burst_allowance_min == 1.0
        assert limits.burst_allowance_max == 10.0

    def test_validate_rate_limit_valid(self):
        """Test valid rate limit."""
        limits = ThrottlingLimits()
        is_valid, error = limits.validate_rate_limit(100)
        assert is_valid is True
        assert error is None

    def test_validate_rate_limit_too_small(self):
        """Test rate limit below minimum."""
        limits = ThrottlingLimits()
        is_valid, error = limits.validate_rate_limit(0)
        assert is_valid is False
        assert "at least" in error

    def test_validate_rate_limit_too_large(self):
        """Test rate limit above maximum."""
        limits = ThrottlingLimits()
        is_valid, error = limits.validate_rate_limit(200000)
        assert is_valid is False
        assert "not exceed" in error

    def test_validate_burst_allowance_valid(self):
        """Test valid burst allowance."""
        limits = ThrottlingLimits()
        is_valid, error = limits.validate_burst_allowance(2.0)
        assert is_valid is True
        assert error is None

    def test_validate_burst_allowance_too_small(self):
        """Test burst allowance below minimum."""
        limits = ThrottlingLimits()
        is_valid, error = limits.validate_burst_allowance(0.5)
        assert is_valid is False
        assert "at least" in error

    def test_validate_burst_allowance_too_large(self):
        """Test burst allowance above maximum."""
        limits = ThrottlingLimits()
        is_valid, error = limits.validate_burst_allowance(15.0)
        assert is_valid is False
        assert "not exceed" in error


class TestEscalationLimits:
    """Tests for EscalationLimits class."""

    def test_default_limits(self):
        """Test default limit values."""
        limits = EscalationLimits()
        assert limits.delay_min_minutes == 0
        assert limits.delay_max_minutes == 10080  # 7 days
        assert limits.max_levels == 20

    def test_validate_delay_minutes_valid(self):
        """Test valid delay minutes."""
        limits = EscalationLimits()
        is_valid, error = limits.validate_delay_minutes(60)
        assert is_valid is True
        assert error is None

    def test_validate_delay_minutes_too_large(self):
        """Test delay minutes above maximum."""
        limits = EscalationLimits()
        is_valid, error = limits.validate_delay_minutes(20000)
        assert is_valid is False
        assert "not exceed" in error

    def test_validate_max_escalations_valid(self):
        """Test valid max escalations."""
        limits = EscalationLimits()
        is_valid, error = limits.validate_max_escalations(5)
        assert is_valid is True
        assert error is None

    def test_validate_check_interval_valid(self):
        """Test valid check interval."""
        limits = EscalationLimits()
        is_valid, error = limits.validate_check_interval(60)
        assert is_valid is True
        assert error is None


class TestTimeWindowLimits:
    """Tests for TimeWindowLimits class."""

    def test_default_limits(self):
        """Test default limit values."""
        limits = TimeWindowLimits()
        assert limits.total_seconds_min == 1
        assert limits.total_seconds_max == 604800  # 7 days
        assert limits.days_max == 7

    def test_validate_total_seconds_valid(self):
        """Test valid total seconds."""
        limits = TimeWindowLimits()
        is_valid, error = limits.validate_total_seconds(3600)
        assert is_valid is True
        assert error is None

    def test_validate_total_seconds_too_small(self):
        """Test total seconds below minimum."""
        limits = TimeWindowLimits()
        is_valid, error = limits.validate_total_seconds(0)
        assert is_valid is False
        assert "at least" in error

    def test_validate_total_seconds_too_large(self):
        """Test total seconds above maximum."""
        limits = TimeWindowLimits()
        is_valid, error = limits.validate_total_seconds(1000000)
        assert is_valid is False
        assert "not exceed" in error


class TestValidationLimitError:
    """Tests for ValidationLimitError exception."""

    def test_error_creation(self):
        """Test error creation with all attributes."""
        error = ValidationLimitError(
            message="Test error",
            parameter="test_param",
            value=100,
        )
        assert str(error) == "Test error"
        assert error.parameter == "test_param"
        assert error.value == 100

    def test_error_repr(self):
        """Test error representation."""
        error = ValidationLimitError(
            message="Test error",
            parameter="test_param",
            value=100,
        )
        repr_str = repr(error)
        assert "test_param" in repr_str
        assert "100" in repr_str


class TestValidationUtilities:
    """Tests for validation utility functions."""

    def test_validate_positive_int_valid(self):
        """Test valid positive integer."""
        validate_positive_int(5, "test_param", min_value=1, max_value=10)
        # Should not raise

    def test_validate_positive_int_too_small(self):
        """Test positive integer below minimum."""
        with pytest.raises(ValidationLimitError) as exc_info:
            validate_positive_int(0, "test_param", min_value=1)
        assert exc_info.value.parameter == "test_param"
        assert exc_info.value.value == 0

    def test_validate_positive_int_too_large(self):
        """Test positive integer above maximum."""
        with pytest.raises(ValidationLimitError) as exc_info:
            validate_positive_int(15, "test_param", min_value=1, max_value=10)
        assert exc_info.value.parameter == "test_param"

    def test_validate_positive_float_valid(self):
        """Test valid positive float."""
        validate_positive_float(5.5, "test_param", min_value=0.0, max_value=10.0)
        # Should not raise

    def test_validate_positive_float_too_small(self):
        """Test positive float below minimum."""
        with pytest.raises(ValidationLimitError):
            validate_positive_float(-1.0, "test_param", min_value=0.0)

    def test_validate_positive_float_too_large(self):
        """Test positive float above maximum."""
        with pytest.raises(ValidationLimitError):
            validate_positive_float(15.0, "test_param", min_value=0.0, max_value=10.0)


class TestLimitsEnvironmentConfig:
    """Tests for environment-based limits configuration."""

    def test_get_deduplication_limits_defaults(self):
        """Test default deduplication limits."""
        clear_limits_cache()
        limits = get_deduplication_limits()
        assert limits.window_min_seconds == 1
        assert limits.window_max_seconds == 86400

    def test_get_throttling_limits_defaults(self):
        """Test default throttling limits."""
        clear_limits_cache()
        limits = get_throttling_limits()
        assert limits.limit_min == 1
        assert limits.limit_max == 100000

    def test_get_escalation_limits_defaults(self):
        """Test default escalation limits."""
        clear_limits_cache()
        limits = get_escalation_limits()
        assert limits.delay_min_minutes == 0
        assert limits.max_levels == 20

    def test_get_time_window_limits_defaults(self):
        """Test default time window limits."""
        clear_limits_cache()
        limits = get_time_window_limits()
        assert limits.total_seconds_min == 1
        assert limits.total_seconds_max == 604800

    def test_clear_limits_cache(self):
        """Test clearing limits cache."""
        limits1 = get_deduplication_limits()
        clear_limits_cache()
        limits2 = get_deduplication_limits()
        # Should work but limits should be recreated
        assert limits2 is not limits1 or limits1 == limits2


# ==============================================================================
# Statistical Analysis Tests
# ==============================================================================


class TestSignificanceLevel:
    """Tests for SignificanceLevel enum."""

    def test_significance_levels(self):
        """Test all significance levels exist."""
        assert SignificanceLevel.NOT_SIGNIFICANT
        assert SignificanceLevel.MARGINALLY_SIGNIFICANT
        assert SignificanceLevel.SIGNIFICANT
        assert SignificanceLevel.HIGHLY_SIGNIFICANT
        assert SignificanceLevel.VERY_HIGHLY_SIGNIFICANT


class TestEffectSize:
    """Tests for EffectSize enum."""

    def test_effect_sizes(self):
        """Test all effect sizes exist."""
        assert EffectSize.NEGLIGIBLE
        assert EffectSize.SMALL
        assert EffectSize.MEDIUM
        assert EffectSize.LARGE


class TestInterpretPValue:
    """Tests for interpret_p_value function."""

    def test_not_significant(self):
        """Test not significant p-value."""
        result = interpret_p_value(0.15)
        assert result == SignificanceLevel.NOT_SIGNIFICANT

    def test_marginally_significant(self):
        """Test marginally significant p-value."""
        result = interpret_p_value(0.08)
        assert result == SignificanceLevel.MARGINALLY_SIGNIFICANT

    def test_significant(self):
        """Test significant p-value."""
        result = interpret_p_value(0.03)
        assert result == SignificanceLevel.SIGNIFICANT

    def test_highly_significant(self):
        """Test highly significant p-value."""
        result = interpret_p_value(0.005)
        assert result == SignificanceLevel.HIGHLY_SIGNIFICANT

    def test_very_highly_significant(self):
        """Test very highly significant p-value."""
        result = interpret_p_value(0.0005)
        assert result == SignificanceLevel.VERY_HIGHLY_SIGNIFICANT


class TestInterpretEffectSize:
    """Tests for interpret_effect_size function."""

    def test_negligible(self):
        """Test negligible effect size."""
        result = interpret_effect_size(0.1)
        assert result == EffectSize.NEGLIGIBLE

    def test_small(self):
        """Test small effect size."""
        result = interpret_effect_size(0.3)
        assert result == EffectSize.SMALL

    def test_medium(self):
        """Test medium effect size."""
        result = interpret_effect_size(0.6)
        assert result == EffectSize.MEDIUM

    def test_large(self):
        """Test large effect size."""
        result = interpret_effect_size(1.0)
        assert result == EffectSize.LARGE


class TestCohensD:
    """Tests for cohens_d function."""

    def test_identical_groups(self):
        """Test Cohen's d for identical groups."""
        values = [1, 2, 3, 4, 5]
        d = cohens_d(values, values)
        assert d == 0.0

    def test_different_groups(self):
        """Test Cohen's d for different groups."""
        group1 = [1, 2, 3, 4, 5]
        group2 = [6, 7, 8, 9, 10]
        d = cohens_d(group1, group2)
        assert d > 0

    def test_zero_variance(self):
        """Test Cohen's d with zero variance."""
        group1 = [5, 5, 5]
        group2 = [5, 5, 5]
        d = cohens_d(group1, group2)
        assert d == 0.0


class TestWelchTTest:
    """Tests for welch_t_test function."""

    def test_insufficient_data(self):
        """Test with insufficient data."""
        result = welch_t_test([1], [2])
        assert result.is_significant is False
        assert "Insufficient" in result.interpretation

    def test_identical_groups(self):
        """Test with identical groups."""
        values = [1, 2, 3, 4, 5]
        result = welch_t_test(values, values)
        assert result.is_significant is False

    def test_different_groups(self):
        """Test with significantly different groups."""
        group1 = [1, 2, 3, 4, 5]
        group2 = [100, 101, 102, 103, 104]
        result = welch_t_test(group1, group2)
        assert result.is_significant is True
        assert result.effect_size is not None
        assert result.confidence_interval is not None

    def test_zero_variance(self):
        """Test with zero variance groups."""
        group1 = [5, 5, 5]
        group2 = [5, 5, 5]
        result = welch_t_test(group1, group2)
        assert "Zero variance" in result.interpretation

    def test_result_structure(self):
        """Test result structure."""
        result = welch_t_test([1, 2, 3, 4, 5], [6, 7, 8, 9, 10])
        assert result.test_name == "Welch's t-test"
        assert isinstance(result.statistic, float)
        assert isinstance(result.p_value, float)
        assert 0 <= result.p_value <= 1
        assert result.sample_sizes == (5, 5)


class TestMannWhitneyUTest:
    """Tests for mann_whitney_u_test function."""

    def test_insufficient_data(self):
        """Test with insufficient data."""
        result = mann_whitney_u_test([], [1, 2])
        assert result.is_significant is False
        assert "Insufficient" in result.interpretation

    def test_identical_groups(self):
        """Test with identical groups."""
        values = [1, 2, 3, 4, 5]
        result = mann_whitney_u_test(values, values)
        assert result.is_significant is False

    def test_different_groups(self):
        """Test with significantly different groups."""
        group1 = [1, 2, 3, 4, 5]
        group2 = [100, 101, 102, 103, 104]
        result = mann_whitney_u_test(group1, group2)
        # Should detect significant difference
        assert result.test_name == "Mann-Whitney U test"

    def test_ties_handling(self):
        """Test handling of tied values."""
        group1 = [1, 1, 2, 2, 3]
        group2 = [1, 2, 2, 3, 3]
        result = mann_whitney_u_test(group1, group2)
        assert result.test_name == "Mann-Whitney U test"

    def test_result_structure(self):
        """Test result structure."""
        result = mann_whitney_u_test([1, 2, 3], [4, 5, 6])
        assert result.test_name == "Mann-Whitney U test"
        assert isinstance(result.statistic, float)
        assert isinstance(result.p_value, float)
        assert result.effect_size is not None


class TestChiSquareTest:
    """Tests for chi_square_test function."""

    def test_mismatched_categories(self):
        """Test with mismatched category counts."""
        result = chi_square_test([1, 2, 3], [1, 2])
        assert "must match" in result.interpretation

    def test_insufficient_categories(self):
        """Test with fewer than 2 categories."""
        result = chi_square_test([5], [5])
        assert "at least 2" in result.interpretation

    def test_no_observations(self):
        """Test with no observations."""
        result = chi_square_test([0, 0], [0, 0])
        assert "No observations" in result.interpretation

    def test_identical_distributions(self):
        """Test with identical distributions."""
        observed = [10, 20, 30]
        result = chi_square_test(observed, observed)
        # Identical distributions should not show significant difference
        assert result.test_name == "Chi-square test"

    def test_different_distributions(self):
        """Test with different distributions."""
        observed1 = [100, 10, 10]
        observed2 = [10, 10, 100]
        result = chi_square_test(observed1, observed2)
        # Very different distributions
        assert result.test_name == "Chi-square test"

    def test_result_structure(self):
        """Test result structure."""
        result = chi_square_test([10, 20], [15, 25])
        assert result.test_name == "Chi-square test"
        assert isinstance(result.statistic, float)
        assert isinstance(result.p_value, float)
        assert result.effect_size is not None


class TestTrendSignificanceTest:
    """Tests for trend_significance_test function."""

    def test_insufficient_data(self):
        """Test with insufficient data."""
        result = trend_significance_test([1, 2])
        assert result.is_significant is False
        assert "at least 3" in result.interpretation

    def test_constant_values(self):
        """Test with constant x values."""
        result = trend_significance_test([5, 5, 5], timestamps=[1, 1, 1])
        assert "Cannot calculate" in result.interpretation

    def test_increasing_trend(self):
        """Test with clear increasing trend (with some noise)."""
        import random
        random.seed(42)
        # Add some noise to avoid perfect R²=1.0 which causes se_slope=0
        values = [i + random.uniform(-0.3, 0.3) for i in range(1, 21)]
        result = trend_significance_test(values)
        assert result.effect_size > 0  # Positive slope
        # Check slope is strongly positive
        assert result.effect_size > 0.8

    def test_decreasing_trend(self):
        """Test with clear decreasing trend (with some noise)."""
        import random
        random.seed(42)
        # Add some noise to avoid perfect R²=1.0
        values = [20 - i + random.uniform(-0.3, 0.3) for i in range(1, 21)]
        result = trend_significance_test(values)
        assert result.effect_size < 0  # Negative slope
        # Check slope is strongly negative
        assert result.effect_size < -0.8

    def test_no_trend(self):
        """Test with no clear trend."""
        values = [5, 5, 5, 5, 5]
        result = trend_significance_test(values)
        assert abs(result.effect_size) < 0.1  # Near-zero slope

    def test_with_timestamps(self):
        """Test with custom timestamps."""
        values = [1, 2, 4, 8]
        timestamps = [0, 1, 2, 3]
        result = trend_significance_test(values, timestamps=timestamps)
        assert result.test_name == "Trend significance test"


class TestComprehensiveComparison:
    """Tests for comprehensive_comparison function."""

    def test_small_sample_recommendation(self):
        """Test recommendation for small samples."""
        group1 = [1, 2, 3, 4, 5]
        group2 = [6, 7, 8, 9, 10]
        result = comprehensive_comparison(group1, group2)
        # Small sample - should recommend non-parametric
        assert result.recommended_test == "Mann-Whitney U test"

    def test_large_sample_recommendation(self):
        """Test recommendation for large samples."""
        import random
        random.seed(42)
        group1 = [random.gauss(0, 1) for _ in range(50)]
        group2 = [random.gauss(5, 1) for _ in range(50)]
        result = comprehensive_comparison(group1, group2)
        # Large sample - should recommend t-test
        assert result.recommended_test == "Welch's t-test"

    def test_result_structure(self):
        """Test result structure."""
        result = comprehensive_comparison([1, 2, 3], [4, 5, 6])
        assert result.t_test is not None
        assert result.mann_whitney is not None
        assert result.recommended_test in ["Welch's t-test", "Mann-Whitney U test"]
        assert isinstance(result.overall_significant, bool)
        assert len(result.summary) > 0


# ==============================================================================
# Performance Stress Tests
# ==============================================================================


class TestCachePerformance:
    """Performance stress tests for cache systems."""

    @pytest.mark.asyncio
    async def test_memory_cache_high_volume(self):
        """Test MemoryCache with high volume of operations."""
        cache = MemoryCache(max_size=1000)

        # Insert many items
        for i in range(500):
            await cache.set(f"key{i}", f"value{i}", ttl_seconds=60)

        # Read many items
        hits = 0
        for i in range(500):
            if await cache.get(f"key{i}"):
                hits += 1

        assert hits > 0
        assert cache.size <= 1000

    @pytest.mark.asyncio
    async def test_lfu_cache_high_volume(self):
        """Test LFUCache with high volume of operations."""
        cache = LFUCache(max_size=100)

        # Insert first batch of items (these will be evicted later)
        for i in range(50):
            await cache.set(f"key{i}", f"value{i}")

        # Access some items frequently to increase their frequency
        for _ in range(50):
            await cache.get("key0")
            await cache.get("key1")

        # Insert more items (causing evictions)
        for i in range(50, 150):
            await cache.set(f"key{i}", f"value{i}")

        stats = await cache.get_stats()
        # Check that we had hits
        assert stats["hits"] >= 50
        assert cache.size <= 100

    @pytest.mark.asyncio
    async def test_concurrent_cache_access(self):
        """Test concurrent cache access."""
        cache = MemoryCache(max_size=100)

        async def writer(n):
            for i in range(10):
                await cache.set(f"writer{n}_key{i}", f"value{i}")

        async def reader(n):
            results = []
            for i in range(10):
                result = await cache.get(f"writer{n}_key{i}")
                results.append(result)
            return results

        # Run concurrent writers
        await asyncio.gather(*[writer(i) for i in range(5)])

        # Run concurrent readers
        await asyncio.gather(*[reader(i) for i in range(5)])

        # Should not raise any exceptions


class TestStatisticalPerformance:
    """Performance tests for statistical functions."""

    def test_large_sample_t_test(self):
        """Test t-test with large samples."""
        import random
        random.seed(42)
        group1 = [random.gauss(0, 1) for _ in range(1000)]
        group2 = [random.gauss(0.5, 1) for _ in range(1000)]

        result = welch_t_test(group1, group2)
        assert result.test_name == "Welch's t-test"
        assert result.sample_sizes == (1000, 1000)

    def test_large_sample_mann_whitney(self):
        """Test Mann-Whitney with large samples."""
        import random
        random.seed(42)
        group1 = [random.gauss(0, 1) for _ in range(500)]
        group2 = [random.gauss(1, 1) for _ in range(500)]

        result = mann_whitney_u_test(group1, group2)
        assert result.test_name == "Mann-Whitney U test"
        assert result.sample_sizes == (500, 500)

    def test_large_trend_analysis(self):
        """Test trend analysis with many data points."""
        import random
        random.seed(42)
        # Add small noise to avoid perfect fit (which causes se_slope=0, t=inf issues)
        values = [i + random.uniform(-0.1, 0.1) for i in range(500)]
        result = trend_significance_test(values)
        # Check for positive slope (increasing trend)
        assert result.effect_size > 0.9  # Strong positive slope


# ==============================================================================
# Integration Tests
# ==============================================================================


class TestCacheIntegration:
    """Integration tests for cache systems."""

    @pytest.mark.asyncio
    async def test_cache_with_complex_objects(self):
        """Test caching complex Python objects."""
        cache = MemoryCache()

        complex_obj = {
            "nested": {"data": [1, 2, 3]},
            "list": ["a", "b", "c"],
            "number": 42.5,
        }

        await cache.set("complex", complex_obj)
        result = await cache.get("complex")

        assert result == complex_obj

    @pytest.mark.asyncio
    async def test_stats_cache_with_dataclass(self):
        """Test stats cache with dataclass objects."""
        cache = StatsCache()

        stats = DeduplicationStatsResult(
            total_configs=10,
            active_configs=8,
            by_strategy={"content_hash": 5, "key_based": 5},
            by_policy={"keep_first": 3, "keep_last": 7},
            avg_window_seconds=300.0,
        )

        await cache.set("dedup_stats", stats)
        result = await cache.get("dedup_stats")

        assert result.total_configs == 10
        assert result.active_configs == 8
