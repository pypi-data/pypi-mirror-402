"""Storage backends for throttling state.

This module provides storage backends for tracking rate limit
counters and token buckets.

Storage Backends:
    - InMemoryThrottlingStore: Simple in-memory storage with TTL and LRU eviction
    - SQLiteThrottlingStore: Persistent SQLite storage
    - RedisThrottlingStore: Redis-based storage for distributed deployments

Features:
    - TTL-based automatic expiration of old entries
    - LRU eviction when max entries exceeded
    - Periodic background cleanup task
    - Configurable cleanup interval and max entries
    - Memory usage metrics
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sqlite3
import threading
import time
import weakref
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Optional Redis dependency
try:
    import redis
    import redis.asyncio

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None  # type: ignore[assignment]

if TYPE_CHECKING:
    import redis as redis_sync
    import redis.asyncio as redis_async


logger = logging.getLogger(__name__)


@dataclass
class ThrottlingEntry:
    """A stored throttling entry.

    Attributes:
        key: Unique key identifying the throttled entity.
        count: Current count within the window.
        window_start: Start of the current window.
        tokens: Current token count (for token bucket).
        last_refill: Last token refill time.
        last_accessed: Last access timestamp for LRU tracking.
    """

    key: str
    count: int = 0
    window_start: float = 0.0
    tokens: float = 0.0
    last_refill: float = 0.0
    last_accessed: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ThrottlingMetrics:
    """Metrics for throttling store operations.

    Attributes:
        total_entries: Current number of entries.
        peak_entries: Maximum entries ever stored.
        expired_removed: Number of entries removed by TTL expiration.
        lru_evicted: Number of entries evicted by LRU policy.
        cleanup_runs: Number of cleanup cycles executed.
        last_cleanup_time: Timestamp of last cleanup.
        last_cleanup_removed: Entries removed in last cleanup.
        memory_bytes_estimate: Estimated memory usage in bytes.
    """

    total_entries: int = 0
    peak_entries: int = 0
    expired_removed: int = 0
    lru_evicted: int = 0
    cleanup_runs: int = 0
    last_cleanup_time: float = 0.0
    last_cleanup_removed: int = 0
    memory_bytes_estimate: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "total_entries": self.total_entries,
            "peak_entries": self.peak_entries,
            "expired_removed": self.expired_removed,
            "lru_evicted": self.lru_evicted,
            "cleanup_runs": self.cleanup_runs,
            "last_cleanup_time": self.last_cleanup_time,
            "last_cleanup_removed": self.last_cleanup_removed,
            "memory_bytes_estimate": self.memory_bytes_estimate,
        }


class BaseThrottlingStore(ABC):
    """Abstract base class for throttling storage.

    All stores must implement methods for getting and updating
    throttling state.
    """

    @abstractmethod
    def get(self, key: str) -> ThrottlingEntry | None:
        """Get entry by key.

        Args:
            key: The throttling key.

        Returns:
            Entry if found, None otherwise.
        """
        ...

    @abstractmethod
    def set(self, entry: ThrottlingEntry) -> None:
        """Set or update an entry.

        Args:
            entry: The entry to store.
        """
        ...

    @abstractmethod
    def increment(self, key: str, window_start: float) -> int:
        """Increment counter and return new count.

        If the entry doesn't exist or window has changed,
        creates a new entry with count=1.

        Args:
            key: The throttling key.
            window_start: Start of current window.

        Returns:
            New count value.
        """
        ...

    @abstractmethod
    def cleanup(self, max_age_seconds: int) -> int:
        """Remove old entries.

        Args:
            max_age_seconds: Maximum age of entries to keep.

        Returns:
            Number of entries removed.
        """
        ...

    @abstractmethod
    def clear(self) -> None:
        """Clear all entries."""
        ...

    def get_metrics(self) -> dict[str, Any]:
        """Get store metrics.

        Returns:
            Dictionary with metrics data.
        """
        return {}


class InMemoryThrottlingStore(BaseThrottlingStore):
    """In-memory throttling storage with TTL and LRU eviction.

    Thread-safe storage suitable for development and single-process
    deployments with automatic memory management.

    Features:
        - TTL-based automatic expiration of old entries
        - LRU eviction when max entries exceeded
        - Periodic background cleanup task
        - Configurable cleanup interval and max entries
        - Memory usage metrics

    Configuration via environment variables:
        TRUTHOUND_THROTTLE_MAX_ENTRIES: Maximum entries (default: 10000)
        TRUTHOUND_THROTTLE_DEFAULT_TTL: Default TTL in seconds (default: 3600)
        TRUTHOUND_THROTTLE_CLEANUP_INTERVAL: Cleanup interval in seconds (default: 60)
        TRUTHOUND_THROTTLE_LRU_EVICTION_PERCENT: Percent to evict on overflow (default: 10)

    Example:
        # Basic usage
        store = InMemoryThrottlingStore()

        # Custom configuration
        store = InMemoryThrottlingStore(
            max_entries=50000,
            default_ttl=7200,
            cleanup_interval=120,
        )

        # With background cleanup
        await store.start_background_cleanup()
        # ... use store ...
        await store.stop_background_cleanup()
    """

    # Track all instances for proper cleanup
    _instances: weakref.WeakSet["InMemoryThrottlingStore"] = weakref.WeakSet()

    def __init__(
        self,
        max_entries: int | None = None,
        default_ttl: int | None = None,
        cleanup_interval: int | None = None,
        lru_eviction_percent: int | None = None,
        auto_start_cleanup: bool = False,
    ) -> None:
        """Initialize in-memory store with memory management.

        Args:
            max_entries: Maximum number of entries before LRU eviction.
            default_ttl: Default TTL in seconds for entries.
            cleanup_interval: Interval in seconds between cleanup runs.
            lru_eviction_percent: Percentage of entries to evict on overflow.
            auto_start_cleanup: Whether to auto-start background cleanup.
        """
        # Configuration from environment or parameters
        self.max_entries = max_entries or int(
            os.getenv("TRUTHOUND_THROTTLE_MAX_ENTRIES", "10000")
        )
        self.default_ttl = default_ttl or int(
            os.getenv("TRUTHOUND_THROTTLE_DEFAULT_TTL", "3600")
        )
        self.cleanup_interval = cleanup_interval or int(
            os.getenv("TRUTHOUND_THROTTLE_CLEANUP_INTERVAL", "60")
        )
        self.lru_eviction_percent = lru_eviction_percent or int(
            os.getenv("TRUTHOUND_THROTTLE_LRU_EVICTION_PERCENT", "10")
        )

        # Use OrderedDict for LRU tracking
        self._entries: OrderedDict[str, ThrottlingEntry] = OrderedDict()
        self._lock = threading.RLock()

        # Background cleanup task
        self._cleanup_task: asyncio.Task[None] | None = None
        self._cleanup_running = False
        self._shutdown_event: asyncio.Event | None = None

        # Metrics
        self._metrics = ThrottlingMetrics()

        # Track instance for cleanup
        InMemoryThrottlingStore._instances.add(self)

        # Auto-start background cleanup if requested
        self._auto_start_cleanup = auto_start_cleanup

    def get(self, key: str) -> ThrottlingEntry | None:
        """Get entry by key and update access time for LRU."""
        with self._lock:
            entry = self._entries.get(key)
            if entry is not None:
                # Update access time
                entry.last_accessed = time.time()
                # Move to end for LRU (most recently used)
                self._entries.move_to_end(key)
            return entry

    def set(self, entry: ThrottlingEntry) -> None:
        """Set or update an entry with LRU tracking."""
        entry.last_accessed = time.time()

        with self._lock:
            # Check if we need to evict entries
            if len(self._entries) >= self.max_entries and entry.key not in self._entries:
                self._evict_lru()

            # Set entry
            self._entries[entry.key] = entry
            # Move to end for LRU
            self._entries.move_to_end(entry.key)

            # Update metrics
            self._metrics.total_entries = len(self._entries)
            if self._metrics.total_entries > self._metrics.peak_entries:
                self._metrics.peak_entries = self._metrics.total_entries
            self._update_memory_estimate()

    def increment(self, key: str, window_start: float) -> int:
        """Increment counter and return new count."""
        with self._lock:
            entry = self._entries.get(key)

            if entry is None or entry.window_start != window_start:
                # Check if we need to evict
                if len(self._entries) >= self.max_entries and key not in self._entries:
                    self._evict_lru()

                # New window
                entry = ThrottlingEntry(
                    key=key,
                    count=1,
                    window_start=window_start,
                    last_accessed=time.time(),
                )
                self._entries[key] = entry

                # Update metrics
                self._metrics.total_entries = len(self._entries)
                if self._metrics.total_entries > self._metrics.peak_entries:
                    self._metrics.peak_entries = self._metrics.total_entries

                return 1

            # Same window, increment
            entry.count += 1
            entry.last_accessed = time.time()
            # Move to end for LRU
            self._entries.move_to_end(key)

            return entry.count

    def cleanup(self, max_age_seconds: int) -> int:
        """Remove old entries based on TTL."""
        cutoff = time.time() - max_age_seconds
        removed = 0

        with self._lock:
            # Collect expired keys
            expired = [
                key for key, entry in self._entries.items()
                if entry.window_start < cutoff and entry.last_refill < cutoff
            ]

            # Remove expired entries
            for key in expired:
                del self._entries[key]
                removed += 1

            # Update metrics
            self._metrics.expired_removed += removed
            self._metrics.total_entries = len(self._entries)
            self._metrics.cleanup_runs += 1
            self._metrics.last_cleanup_time = time.time()
            self._metrics.last_cleanup_removed = removed
            self._update_memory_estimate()

        if removed > 0:
            logger.debug(f"Throttling store cleanup: removed {removed} expired entries")

        return removed

    def _evict_lru(self) -> None:
        """Evict least recently used entries.

        Called when max_entries is reached. Evicts a percentage
        of entries based on lru_eviction_percent.
        """
        evict_count = max(1, int(len(self._entries) * self.lru_eviction_percent / 100))

        # Remove oldest entries (at the beginning of OrderedDict)
        for _ in range(evict_count):
            if not self._entries:
                break
            # popitem(last=False) removes from beginning (oldest)
            self._entries.popitem(last=False)
            self._metrics.lru_evicted += 1

        self._metrics.total_entries = len(self._entries)

        logger.debug(f"Throttling store LRU eviction: evicted {evict_count} entries")

    def _update_memory_estimate(self) -> None:
        """Estimate memory usage of stored entries."""
        # Rough estimate: key (~50 bytes) + entry object (~200 bytes)
        entry_size_estimate = 250
        self._metrics.memory_bytes_estimate = len(self._entries) * entry_size_estimate

    def clear(self) -> None:
        """Clear all entries."""
        with self._lock:
            self._entries.clear()
            self._metrics.total_entries = 0
            self._update_memory_estimate()

    def get_metrics(self) -> dict[str, Any]:
        """Get store metrics."""
        with self._lock:
            self._metrics.total_entries = len(self._entries)
            self._update_memory_estimate()
            return self._metrics.to_dict()

    def count(self) -> int:
        """Get total entry count."""
        with self._lock:
            return len(self._entries)

    # =========================================================================
    # Background Cleanup
    # =========================================================================

    async def start_background_cleanup(self) -> None:
        """Start background cleanup task.

        Creates an asyncio task that periodically runs cleanup
        to remove expired entries.
        """
        if self._cleanup_task is not None and not self._cleanup_task.done():
            logger.warning("Background cleanup already running")
            return

        self._cleanup_running = True
        self._shutdown_event = asyncio.Event()
        self._cleanup_task = asyncio.create_task(self._background_cleanup_loop())
        logger.info(
            f"Started throttling store background cleanup "
            f"(interval={self.cleanup_interval}s, ttl={self.default_ttl}s)"
        )

    async def stop_background_cleanup(self) -> None:
        """Stop background cleanup task."""
        if not self._cleanup_running:
            return

        self._cleanup_running = False

        if self._shutdown_event:
            self._shutdown_event.set()

        if self._cleanup_task:
            try:
                # Wait for task to complete with timeout
                await asyncio.wait_for(self._cleanup_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass

        self._cleanup_task = None
        self._shutdown_event = None
        logger.info("Stopped throttling store background cleanup")

    async def _background_cleanup_loop(self) -> None:
        """Background task that periodically runs cleanup."""
        while self._cleanup_running:
            try:
                # Wait for cleanup interval or shutdown
                if self._shutdown_event:
                    try:
                        await asyncio.wait_for(
                            self._shutdown_event.wait(),
                            timeout=self.cleanup_interval,
                        )
                        # If we get here, shutdown was requested
                        break
                    except asyncio.TimeoutError:
                        # Timeout means it's time to cleanup
                        pass

                # Run cleanup
                removed = self.cleanup(self.default_ttl)
                if removed > 0:
                    logger.debug(
                        f"Background cleanup: removed {removed} expired entries, "
                        f"{self.count()} remaining"
                    )

            except asyncio.CancelledError:
                logger.debug("Background cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in background cleanup: {e}")
                # Continue running despite errors
                await asyncio.sleep(self.cleanup_interval)

    def __del__(self) -> None:
        """Cleanup on deletion."""
        # Note: Cannot await in __del__, so just flag for cleanup
        self._cleanup_running = False

    # =========================================================================
    # Context Manager Support
    # =========================================================================

    async def __aenter__(self) -> "InMemoryThrottlingStore":
        """Async context manager entry."""
        if self._auto_start_cleanup:
            await self.start_background_cleanup()
        return self

    async def __aexit__(
        self, exc_type: Any, exc_val: Any, exc_tb: Any
    ) -> None:
        """Async context manager exit."""
        await self.stop_background_cleanup()


class SQLiteThrottlingStore(BaseThrottlingStore):
    """SQLite-based persistent throttling storage.

    Provides durable storage that survives process restarts.
    """

    def __init__(self, db_path: str | Path = "throttling.db") -> None:
        """Initialize SQLite store.

        Args:
            db_path: Path to database file.
        """
        self.db_path = Path(db_path)
        self._local = threading.local()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, "connection"):
            self._local.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection

    def _init_db(self) -> None:
        """Initialize database schema."""
        conn = self._get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS throttling_entries (
                key TEXT PRIMARY KEY,
                count INTEGER NOT NULL DEFAULT 0,
                window_start REAL NOT NULL,
                tokens REAL NOT NULL DEFAULT 0,
                last_refill REAL NOT NULL DEFAULT 0,
                last_accessed REAL NOT NULL DEFAULT 0,
                metadata TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_throttle_window
            ON throttling_entries(window_start)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_throttle_accessed
            ON throttling_entries(last_accessed)
        """)
        conn.commit()

    def get(self, key: str) -> ThrottlingEntry | None:
        """Get entry by key."""
        conn = self._get_connection()
        now = time.time()

        # Update last_accessed
        cursor = conn.execute(
            """
            UPDATE throttling_entries
            SET last_accessed = ?
            WHERE key = ?
            RETURNING key, count, window_start, tokens, last_refill, last_accessed, metadata
            """,
            (now, key),
        )
        row = cursor.fetchone()

        if row is None:
            # Fall back to SELECT if UPDATE returned nothing
            cursor = conn.execute(
                """
                SELECT key, count, window_start, tokens, last_refill, last_accessed, metadata
                FROM throttling_entries
                WHERE key = ?
                """,
                (key,),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        metadata = {}
        if row["metadata"]:
            try:
                metadata = json.loads(row["metadata"])
            except json.JSONDecodeError:
                pass

        return ThrottlingEntry(
            key=row["key"],
            count=row["count"],
            window_start=row["window_start"],
            tokens=row["tokens"],
            last_refill=row["last_refill"],
            last_accessed=row["last_accessed"],
            metadata=metadata,
        )

    def set(self, entry: ThrottlingEntry) -> None:
        """Set or update an entry."""
        conn = self._get_connection()
        metadata_json = json.dumps(entry.metadata) if entry.metadata else None
        now = time.time()

        conn.execute(
            """
            INSERT OR REPLACE INTO throttling_entries
            (key, count, window_start, tokens, last_refill, last_accessed, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.key,
                entry.count,
                entry.window_start,
                entry.tokens,
                entry.last_refill,
                now,
                metadata_json,
            ),
        )
        conn.commit()

    def increment(self, key: str, window_start: float) -> int:
        """Increment counter and return new count."""
        conn = self._get_connection()
        now = time.time()

        # Check if entry exists and is in same window
        cursor = conn.execute(
            """
            SELECT count, window_start FROM throttling_entries
            WHERE key = ?
            """,
            (key,),
        )
        row = cursor.fetchone()

        if row is None or row["window_start"] != window_start:
            # New window
            conn.execute(
                """
                INSERT OR REPLACE INTO throttling_entries
                (key, count, window_start, tokens, last_refill, last_accessed)
                VALUES (?, 1, ?, 0, 0, ?)
                """,
                (key, window_start, now),
            )
            conn.commit()
            return 1

        # Same window, increment
        conn.execute(
            """
            UPDATE throttling_entries
            SET count = count + 1, last_accessed = ?
            WHERE key = ?
            """,
            (now, key),
        )
        conn.commit()

        return row["count"] + 1

    def cleanup(self, max_age_seconds: int) -> int:
        """Remove old entries."""
        conn = self._get_connection()
        cutoff = time.time() - max_age_seconds

        cursor = conn.execute(
            """
            DELETE FROM throttling_entries
            WHERE window_start < ? AND last_refill < ?
            """,
            (cutoff, cutoff),
        )
        conn.commit()

        return cursor.rowcount

    def clear(self) -> None:
        """Clear all entries."""
        conn = self._get_connection()
        conn.execute("DELETE FROM throttling_entries")
        conn.commit()

    def count(self) -> int:
        """Get total entry count."""
        conn = self._get_connection()
        cursor = conn.execute("SELECT COUNT(*) FROM throttling_entries")
        return cursor.fetchone()[0]

    def get_metrics(self) -> dict[str, Any]:
        """Get store metrics."""
        return {
            "total_entries": self.count(),
            "db_path": str(self.db_path),
        }

    def close(self) -> None:
        """Close database connection."""
        if hasattr(self._local, "connection"):
            self._local.connection.close()
            del self._local.connection


class RedisThrottlingStore(BaseThrottlingStore):
    """Redis-based throttling store for distributed deployments.

    Uses Redis for shared throttling state across multiple processes
    or containers. Supports both sync and async operations with
    connection pooling.

    Features:
        - Connection pool management with configurable pool size
        - Automatic reconnection with exponential backoff
        - TTL management for automatic expiration
        - Graceful degradation (fallback to InMemory on Redis failure)
        - Health check endpoint support
        - Comprehensive metrics collection
        - Async support for high-performance applications

    Configuration via environment variables:
        TRUTHOUND_THROTTLE_REDIS_URL: Redis connection URL (default: redis://localhost:6379/0)
        TRUTHOUND_THROTTLE_REDIS_PREFIX: Key prefix (default: truthound:throttle:)
        TRUTHOUND_THROTTLE_REDIS_TTL: Default TTL in seconds (default: 3600)
        TRUTHOUND_THROTTLE_REDIS_POOL_SIZE: Connection pool size (default: 10)
        TRUTHOUND_THROTTLE_REDIS_SOCKET_TIMEOUT: Socket timeout (default: 5.0)
        TRUTHOUND_THROTTLE_REDIS_CONNECT_TIMEOUT: Connection timeout (default: 5.0)
        TRUTHOUND_THROTTLE_REDIS_MAX_RETRIES: Max retry attempts (default: 3)
        TRUTHOUND_THROTTLE_REDIS_RETRY_BASE_DELAY: Base delay for exponential backoff (default: 1.0)
        TRUTHOUND_THROTTLE_FALLBACK_ENABLED: Enable fallback to InMemory (default: true)

    Example:
        # Basic usage
        store = RedisThrottlingStore()

        # Custom configuration
        store = RedisThrottlingStore(
            redis_url="redis://myredis:6379/1",
            default_ttl=7200,
            max_connections=20,
        )

        # With context manager
        async with RedisThrottlingStore() as store:
            result = throttler.allow("channel-1")

    Note: Requires the 'redis' optional dependency.
          Install with: pip install truthound-dashboard[redis]
    """

    # Hash field names
    FIELD_COUNT = "count"
    FIELD_WINDOW_START = "window_start"
    FIELD_TOKENS = "tokens"
    FIELD_LAST_REFILL = "last_refill"
    FIELD_LAST_ACCESSED = "last_accessed"
    FIELD_METADATA = "metadata"

    def __init__(
        self,
        redis_url: str | None = None,
        key_prefix: str | None = None,
        default_ttl: int | None = None,
        max_connections: int | None = None,
        socket_timeout: float | None = None,
        socket_connect_timeout: float | None = None,
        max_retries: int | None = None,
        retry_base_delay: float | None = None,
        enable_fallback: bool | None = None,
    ) -> None:
        """Initialize Redis throttling store.

        All parameters can be configured via environment variables if not
        explicitly provided.

        Args:
            redis_url: Redis connection URL.
            key_prefix: Prefix for all Redis keys.
            default_ttl: Default TTL in seconds for entries.
            max_connections: Maximum connections in the pool.
            socket_timeout: Socket timeout in seconds.
            socket_connect_timeout: Connection timeout in seconds.
            max_retries: Maximum retry attempts for reconnection.
            retry_base_delay: Base delay for exponential backoff.
            enable_fallback: Enable fallback to InMemory on Redis failure.

        Raises:
            ImportError: If redis package is not installed.
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "Redis support requires the 'redis' package. "
                "Install with: pip install truthound-dashboard[redis] "
                "or pip install redis"
            )

        # Configuration from environment or parameters
        self.redis_url = redis_url or os.getenv(
            "TRUTHOUND_THROTTLE_REDIS_URL", "redis://localhost:6379/0"
        )
        self.key_prefix = key_prefix or os.getenv(
            "TRUTHOUND_THROTTLE_REDIS_PREFIX", "truthound:throttle:"
        )
        self.default_ttl = default_ttl or int(
            os.getenv("TRUTHOUND_THROTTLE_REDIS_TTL", "3600")
        )
        self.max_connections = max_connections or int(
            os.getenv("TRUTHOUND_THROTTLE_REDIS_POOL_SIZE", "10")
        )
        self.socket_timeout = socket_timeout or float(
            os.getenv("TRUTHOUND_THROTTLE_REDIS_SOCKET_TIMEOUT", "5.0")
        )
        self.socket_connect_timeout = socket_connect_timeout or float(
            os.getenv("TRUTHOUND_THROTTLE_REDIS_CONNECT_TIMEOUT", "5.0")
        )
        self.max_retries = max_retries or int(
            os.getenv("TRUTHOUND_THROTTLE_REDIS_MAX_RETRIES", "3")
        )
        self.retry_base_delay = retry_base_delay or float(
            os.getenv("TRUTHOUND_THROTTLE_REDIS_RETRY_BASE_DELAY", "1.0")
        )

        fallback_env = os.getenv("TRUTHOUND_THROTTLE_FALLBACK_ENABLED", "true")
        self.enable_fallback = (
            enable_fallback
            if enable_fallback is not None
            else fallback_env.lower() == "true"
        )

        # Connection pool for sync client
        self._pool: redis.ConnectionPool | None = None
        self._client: redis.Redis | None = None

        # Connection pool for async client
        self._async_pool: redis.asyncio.ConnectionPool | None = None
        self._async_client: redis.asyncio.Redis | None = None

        # Locks for thread-safe initialization
        self._lock = threading.Lock()
        self._async_lock: asyncio.Lock | None = None

        # Fallback store for graceful degradation
        self._fallback_store: InMemoryThrottlingStore | None = None
        self._using_fallback = False

        # Connection state tracking
        self._connected = False
        self._retry_count = 0
        self._last_error: Exception | None = None
        self._last_error_time: float | None = None

        # Metrics
        self._metrics = ThrottlingMetrics()
        self._redis_errors = 0
        self._fallback_count = 0
        self._reconnections = 0

        # Index tracking key
        self._index_key = f"{self.key_prefix}index"

    def _get_key(self, key: str) -> str:
        """Get full Redis key for throttling entry.

        Args:
            key: The throttling key.

        Returns:
            Full Redis key with prefix.
        """
        return f"{self.key_prefix}entry:{key}"

    def _create_pool(self) -> "redis.ConnectionPool":
        """Create a connection pool for sync client.

        Returns:
            Configured connection pool.
        """
        return redis.ConnectionPool.from_url(
            self.redis_url,
            max_connections=self.max_connections,
            socket_timeout=self.socket_timeout,
            socket_connect_timeout=self.socket_connect_timeout,
            retry_on_timeout=True,
            decode_responses=True,
        )

    async def _create_async_pool(self) -> "redis.asyncio.ConnectionPool":
        """Create a connection pool for async client.

        Returns:
            Configured async connection pool.
        """
        return redis.asyncio.ConnectionPool.from_url(
            self.redis_url,
            max_connections=self.max_connections,
            socket_timeout=self.socket_timeout,
            socket_connect_timeout=self.socket_connect_timeout,
            retry_on_timeout=True,
            decode_responses=True,
        )

    def _get_fallback_store(self) -> InMemoryThrottlingStore:
        """Get or create fallback in-memory store.

        Returns:
            InMemoryThrottlingStore instance.
        """
        if self._fallback_store is None:
            self._fallback_store = InMemoryThrottlingStore()
        return self._fallback_store

    def _calculate_backoff_delay(self) -> float:
        """Calculate exponential backoff delay.

        Returns:
            Delay in seconds.
        """
        import random

        # Exponential backoff with jitter
        delay = self.retry_base_delay * (2 ** self._retry_count)
        # Add jitter (up to 25% of delay)
        jitter = delay * random.uniform(0, 0.25)
        return min(delay + jitter, 60.0)  # Cap at 60 seconds

    def _handle_redis_error(self, error: Exception, operation: str) -> None:
        """Handle Redis errors with logging and metrics.

        Args:
            error: The exception that occurred.
            operation: Name of the operation that failed.
        """
        self._redis_errors += 1
        self._last_error = error
        self._last_error_time = time.time()
        self._connected = False

        logger.error(
            f"Redis throttling store error during {operation}: {error}",
            extra={
                "operation": operation,
                "error_type": type(error).__name__,
                "retry_count": self._retry_count,
            },
        )

    def _try_reconnect_sync(self) -> bool:
        """Attempt to reconnect to Redis synchronously.

        Returns:
            True if reconnection successful, False otherwise.
        """
        if self._retry_count >= self.max_retries:
            logger.warning(
                f"Max retries ({self.max_retries}) reached, using fallback"
            )
            return False

        delay = self._calculate_backoff_delay()
        logger.info(
            f"Attempting Redis reconnection in {delay:.2f}s "
            f"(attempt {self._retry_count + 1}/{self.max_retries})"
        )

        time.sleep(delay)
        self._retry_count += 1

        try:
            # Close existing connections
            if self._client:
                try:
                    self._client.close()
                except Exception:
                    pass
                self._client = None

            if self._pool:
                try:
                    self._pool.disconnect()
                except Exception:
                    pass
                self._pool = None

            # Create new connection
            self._pool = self._create_pool()
            self._client = redis.Redis(connection_pool=self._pool)

            # Test connection
            if self._client.ping():
                self._connected = True
                self._retry_count = 0
                self._using_fallback = False
                self._reconnections += 1
                logger.info("Redis throttling store reconnection successful")
                return True
        except Exception as e:
            logger.warning(f"Reconnection attempt failed: {e}")

        return False

    @property
    def client(self) -> "redis.Redis":
        """Get sync Redis client with connection pooling.

        Creates the connection pool and client on first access.
        Handles reconnection on failure.

        Returns:
            Redis client instance.
        """
        if self._client is None or not self._connected:
            with self._lock:
                if self._client is None or not self._connected:
                    try:
                        self._pool = self._create_pool()
                        self._client = redis.Redis(connection_pool=self._pool)
                        # Test connection
                        self._client.ping()
                        self._connected = True
                        self._retry_count = 0
                        logger.debug("Redis throttling store sync client connected")
                    except Exception as e:
                        self._handle_redis_error(e, "client_init")
                        raise
        return self._client

    async def get_async_client(self) -> "redis.asyncio.Redis":
        """Get async Redis client with connection pooling.

        Creates the async connection pool and client on first access.

        Returns:
            Async Redis client instance.
        """
        if self._async_lock is None:
            self._async_lock = asyncio.Lock()

        if self._async_client is None or not self._connected:
            async with self._async_lock:
                if self._async_client is None or not self._connected:
                    try:
                        self._async_pool = await self._create_async_pool()
                        self._async_client = redis.asyncio.Redis(
                            connection_pool=self._async_pool
                        )
                        # Test connection
                        await self._async_client.ping()
                        self._connected = True
                        self._retry_count = 0
                        logger.debug("Redis throttling store async client connected")
                    except Exception as e:
                        self._handle_redis_error(e, "async_client_init")
                        raise
        return self._async_client

    def _serialize_entry(self, entry: ThrottlingEntry) -> dict[str, str]:
        """Serialize entry for Redis storage.

        Args:
            entry: The entry to serialize.

        Returns:
            Dictionary suitable for Redis HSET.
        """
        return {
            self.FIELD_COUNT: str(entry.count),
            self.FIELD_WINDOW_START: str(entry.window_start),
            self.FIELD_TOKENS: str(entry.tokens),
            self.FIELD_LAST_REFILL: str(entry.last_refill),
            self.FIELD_LAST_ACCESSED: str(entry.last_accessed),
            self.FIELD_METADATA: json.dumps(entry.metadata) if entry.metadata else "{}",
        }

    def _deserialize_entry(self, key: str, data: dict[str, str]) -> ThrottlingEntry:
        """Deserialize entry from Redis storage.

        Args:
            key: The throttling key.
            data: Dictionary from Redis HGETALL.

        Returns:
            ThrottlingEntry instance.
        """
        metadata = {}
        if data.get(self.FIELD_METADATA):
            try:
                metadata = json.loads(data[self.FIELD_METADATA])
            except json.JSONDecodeError:
                pass

        return ThrottlingEntry(
            key=key,
            count=int(data.get(self.FIELD_COUNT, 0)),
            window_start=float(data.get(self.FIELD_WINDOW_START, 0)),
            tokens=float(data.get(self.FIELD_TOKENS, 0)),
            last_refill=float(data.get(self.FIELD_LAST_REFILL, 0)),
            last_accessed=float(data.get(self.FIELD_LAST_ACCESSED, 0)),
            metadata=metadata,
        )

    def get(self, key: str) -> ThrottlingEntry | None:
        """Get entry by key.

        Falls back to InMemory store on Redis failure if enabled.

        Args:
            key: The throttling key.

        Returns:
            Entry if found, None otherwise.
        """
        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().get(key)

        try:
            redis_key = self._get_key(key)
            now = time.time()

            # Get and update last_accessed atomically
            pipe = self.client.pipeline()
            pipe.hgetall(redis_key)
            pipe.hset(redis_key, self.FIELD_LAST_ACCESSED, str(now))
            pipe.expire(redis_key, self.default_ttl)
            results = pipe.execute()

            data = results[0]
            if not data:
                return None

            return self._deserialize_entry(key, data)

        except Exception as e:
            self._handle_redis_error(e, "get")

            if self.enable_fallback:
                self._using_fallback = True
                self._fallback_count += 1
                logger.warning("Falling back to InMemory throttling store")
                return self._get_fallback_store().get(key)

            raise

    async def get_async(self, key: str) -> ThrottlingEntry | None:
        """Async get entry by key.

        Args:
            key: The throttling key.

        Returns:
            Entry if found, None otherwise.
        """
        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().get(key)

        try:
            client = await self.get_async_client()
            redis_key = self._get_key(key)
            now = time.time()

            # Get and update last_accessed atomically
            pipe = client.pipeline()
            pipe.hgetall(redis_key)
            pipe.hset(redis_key, self.FIELD_LAST_ACCESSED, str(now))
            pipe.expire(redis_key, self.default_ttl)
            results = await pipe.execute()

            data = results[0]
            if not data:
                return None

            return self._deserialize_entry(key, data)

        except Exception as e:
            self._handle_redis_error(e, "get_async")

            if self.enable_fallback:
                self._using_fallback = True
                self._fallback_count += 1
                logger.warning("Falling back to InMemory throttling store")
                return self._get_fallback_store().get(key)

            raise

    def set(self, entry: ThrottlingEntry) -> None:
        """Set or update an entry.

        Args:
            entry: The entry to store.
        """
        if self._using_fallback and self.enable_fallback:
            self._get_fallback_store().set(entry)
            return

        try:
            redis_key = self._get_key(entry.key)
            entry.last_accessed = time.time()

            pipe = self.client.pipeline()
            pipe.hset(redis_key, mapping=self._serialize_entry(entry))
            pipe.expire(redis_key, self.default_ttl)
            pipe.sadd(self._index_key, entry.key)
            pipe.expire(self._index_key, self.default_ttl * 2)
            pipe.execute()

        except Exception as e:
            self._handle_redis_error(e, "set")

            if self.enable_fallback:
                self._using_fallback = True
                self._fallback_count += 1
                logger.warning("Falling back to InMemory throttling store")
                self._get_fallback_store().set(entry)
                return

            raise

    async def set_async(self, entry: ThrottlingEntry) -> None:
        """Async set or update an entry.

        Args:
            entry: The entry to store.
        """
        if self._using_fallback and self.enable_fallback:
            self._get_fallback_store().set(entry)
            return

        try:
            client = await self.get_async_client()
            redis_key = self._get_key(entry.key)
            entry.last_accessed = time.time()

            pipe = client.pipeline()
            pipe.hset(redis_key, mapping=self._serialize_entry(entry))
            pipe.expire(redis_key, self.default_ttl)
            pipe.sadd(self._index_key, entry.key)
            pipe.expire(self._index_key, self.default_ttl * 2)
            await pipe.execute()

        except Exception as e:
            self._handle_redis_error(e, "set_async")

            if self.enable_fallback:
                self._using_fallback = True
                self._fallback_count += 1
                logger.warning("Falling back to InMemory throttling store")
                self._get_fallback_store().set(entry)
                return

            raise

    def increment(self, key: str, window_start: float) -> int:
        """Increment counter and return new count.

        Uses Lua script for atomic check-and-increment.

        Args:
            key: The throttling key.
            window_start: Start of current window.

        Returns:
            New count value.
        """
        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().increment(key, window_start)

        # Lua script for atomic increment with window check
        lua_script = """
        local key = KEYS[1]
        local index_key = KEYS[2]
        local window_start = tonumber(ARGV[1])
        local now = tonumber(ARGV[2])
        local ttl = tonumber(ARGV[3])
        local raw_key = ARGV[4]

        -- Get current window_start
        local current_window = redis.call('HGET', key, 'window_start')

        if current_window == false or tonumber(current_window) ~= window_start then
            -- New window, reset count to 1
            redis.call('HMSET', key,
                'count', 1,
                'window_start', window_start,
                'tokens', 0,
                'last_refill', 0,
                'last_accessed', now,
                'metadata', '{}'
            )
            redis.call('EXPIRE', key, ttl)
            redis.call('SADD', index_key, raw_key)
            redis.call('EXPIRE', index_key, ttl * 2)
            return 1
        else
            -- Same window, increment
            local new_count = redis.call('HINCRBY', key, 'count', 1)
            redis.call('HSET', key, 'last_accessed', now)
            redis.call('EXPIRE', key, ttl)
            return new_count
        end
        """

        try:
            redis_key = self._get_key(key)
            now = time.time()

            result = self.client.eval(
                lua_script,
                2,  # number of keys
                redis_key,
                self._index_key,
                str(window_start),
                str(now),
                str(self.default_ttl),
                key,
            )

            return int(result)

        except Exception as e:
            self._handle_redis_error(e, "increment")

            if self.enable_fallback:
                self._using_fallback = True
                self._fallback_count += 1
                logger.warning("Falling back to InMemory throttling store")
                return self._get_fallback_store().increment(key, window_start)

            raise

    async def increment_async(self, key: str, window_start: float) -> int:
        """Async increment counter and return new count.

        Args:
            key: The throttling key.
            window_start: Start of current window.

        Returns:
            New count value.
        """
        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().increment(key, window_start)

        # Lua script for atomic increment
        lua_script = """
        local key = KEYS[1]
        local index_key = KEYS[2]
        local window_start = tonumber(ARGV[1])
        local now = tonumber(ARGV[2])
        local ttl = tonumber(ARGV[3])
        local raw_key = ARGV[4]

        local current_window = redis.call('HGET', key, 'window_start')

        if current_window == false or tonumber(current_window) ~= window_start then
            redis.call('HMSET', key,
                'count', 1,
                'window_start', window_start,
                'tokens', 0,
                'last_refill', 0,
                'last_accessed', now,
                'metadata', '{}'
            )
            redis.call('EXPIRE', key, ttl)
            redis.call('SADD', index_key, raw_key)
            redis.call('EXPIRE', index_key, ttl * 2)
            return 1
        else
            local new_count = redis.call('HINCRBY', key, 'count', 1)
            redis.call('HSET', key, 'last_accessed', now)
            redis.call('EXPIRE', key, ttl)
            return new_count
        end
        """

        try:
            client = await self.get_async_client()
            redis_key = self._get_key(key)
            now = time.time()

            result = await client.eval(
                lua_script,
                2,
                redis_key,
                self._index_key,
                str(window_start),
                str(now),
                str(self.default_ttl),
                key,
            )

            return int(result)

        except Exception as e:
            self._handle_redis_error(e, "increment_async")

            if self.enable_fallback:
                self._using_fallback = True
                self._fallback_count += 1
                logger.warning("Falling back to InMemory throttling store")
                return self._get_fallback_store().increment(key, window_start)

            raise

    def cleanup(self, max_age_seconds: int) -> int:
        """Remove old entries.

        Redis handles TTL automatically, but this method can force
        cleanup of entries older than max_age_seconds.

        Args:
            max_age_seconds: Maximum age of entries to keep.

        Returns:
            Number of entries removed.
        """
        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().cleanup(max_age_seconds)

        try:
            cutoff = time.time() - max_age_seconds
            removed = 0

            # Get all keys from index
            keys = self.client.smembers(self._index_key)

            for key in keys:
                redis_key = self._get_key(key)
                data = self.client.hgetall(redis_key)

                if not data:
                    # Entry expired, remove from index
                    self.client.srem(self._index_key, key)
                    removed += 1
                elif float(data.get(self.FIELD_WINDOW_START, 0)) < cutoff:
                    # Entry is old, delete it
                    self.client.delete(redis_key)
                    self.client.srem(self._index_key, key)
                    removed += 1

            return removed

        except Exception as e:
            self._handle_redis_error(e, "cleanup")

            if self.enable_fallback:
                self._using_fallback = True
                return self._get_fallback_store().cleanup(max_age_seconds)

            raise

    async def cleanup_async(self, max_age_seconds: int) -> int:
        """Async remove old entries.

        Args:
            max_age_seconds: Maximum age of entries to keep.

        Returns:
            Number of entries removed.
        """
        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().cleanup(max_age_seconds)

        try:
            client = await self.get_async_client()
            cutoff = time.time() - max_age_seconds
            removed = 0

            # Get all keys from index
            keys = await client.smembers(self._index_key)

            for key in keys:
                redis_key = self._get_key(key)
                data = await client.hgetall(redis_key)

                if not data:
                    await client.srem(self._index_key, key)
                    removed += 1
                elif float(data.get(self.FIELD_WINDOW_START, 0)) < cutoff:
                    await client.delete(redis_key)
                    await client.srem(self._index_key, key)
                    removed += 1

            return removed

        except Exception as e:
            self._handle_redis_error(e, "cleanup_async")

            if self.enable_fallback:
                self._using_fallback = True
                return self._get_fallback_store().cleanup(max_age_seconds)

            raise

    def clear(self) -> None:
        """Clear all throttling entries."""
        if self._using_fallback and self.enable_fallback:
            self._get_fallback_store().clear()
            return

        try:
            # Get all keys from index
            keys = self.client.smembers(self._index_key)

            if keys:
                # Delete all entry keys
                redis_keys = [self._get_key(k) for k in keys]
                self.client.delete(*redis_keys)

            # Delete index
            self.client.delete(self._index_key)

        except Exception as e:
            self._handle_redis_error(e, "clear")

            if self.enable_fallback:
                self._using_fallback = True
                self._get_fallback_store().clear()
                return

            raise

    async def clear_async(self) -> None:
        """Async clear all throttling entries."""
        if self._using_fallback and self.enable_fallback:
            self._get_fallback_store().clear()
            return

        try:
            client = await self.get_async_client()

            # Get all keys from index
            keys = await client.smembers(self._index_key)

            if keys:
                redis_keys = [self._get_key(k) for k in keys]
                await client.delete(*redis_keys)

            await client.delete(self._index_key)

        except Exception as e:
            self._handle_redis_error(e, "clear_async")

            if self.enable_fallback:
                self._using_fallback = True
                self._get_fallback_store().clear()
                return

            raise

    def count(self) -> int:
        """Get total entry count."""
        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().count()

        try:
            return self.client.scard(self._index_key)

        except Exception as e:
            self._handle_redis_error(e, "count")

            if self.enable_fallback:
                self._using_fallback = True
                return self._get_fallback_store().count()

            raise

    async def count_async(self) -> int:
        """Async get total entry count."""
        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().count()

        try:
            client = await self.get_async_client()
            return await client.scard(self._index_key)

        except Exception as e:
            self._handle_redis_error(e, "count_async")

            if self.enable_fallback:
                self._using_fallback = True
                return self._get_fallback_store().count()

            raise

    def health_check(self) -> dict[str, Any]:
        """Perform health check and return status.

        Returns:
            Dictionary with health status information.
        """
        import re

        result = {
            "healthy": False,
            "connected": self._connected,
            "using_fallback": self._using_fallback,
            "redis_url": re.sub(r"://[^:]+:[^@]+@", "://***:***@", self.redis_url),
        }

        if self._using_fallback and self.enable_fallback:
            result["healthy"] = True
            result["mode"] = "fallback"
            result["fallback_entries"] = self._get_fallback_store().count()
            return result

        try:
            ping_ok = self.client.ping()

            if ping_ok:
                result["healthy"] = True
                result["mode"] = "redis"
                result["entries"] = self.count()

                # Get Redis info
                info = self.client.info(section="server")
                result["redis_info"] = {
                    "version": info.get("redis_version"),
                    "uptime_seconds": info.get("uptime_in_seconds"),
                }

        except Exception as e:
            result["error"] = str(e)
            if self._last_error_time:
                from datetime import datetime
                result["last_error_time"] = datetime.fromtimestamp(
                    self._last_error_time
                ).isoformat()

        return result

    async def health_check_async(self) -> dict[str, Any]:
        """Async perform health check and return status.

        Returns:
            Dictionary with health status information.
        """
        import re

        result = {
            "healthy": False,
            "connected": self._connected,
            "using_fallback": self._using_fallback,
            "redis_url": re.sub(r"://[^:]+:[^@]+@", "://***:***@", self.redis_url),
        }

        if self._using_fallback and self.enable_fallback:
            result["healthy"] = True
            result["mode"] = "fallback"
            result["fallback_entries"] = self._get_fallback_store().count()
            return result

        try:
            client = await self.get_async_client()
            ping_ok = await client.ping()

            if ping_ok:
                result["healthy"] = True
                result["mode"] = "redis"
                result["entries"] = await self.count_async()

                info = await client.info(section="server")
                result["redis_info"] = {
                    "version": info.get("redis_version"),
                    "uptime_seconds": info.get("uptime_in_seconds"),
                }

        except Exception as e:
            result["error"] = str(e)
            if self._last_error_time:
                from datetime import datetime
                result["last_error_time"] = datetime.fromtimestamp(
                    self._last_error_time
                ).isoformat()

        return result

    def get_metrics(self) -> dict[str, Any]:
        """Get store metrics.

        Returns:
            Dictionary with metrics data.
        """
        metrics = {
            "redis_errors": self._redis_errors,
            "fallback_count": self._fallback_count,
            "reconnections": self._reconnections,
            "connected": self._connected,
            "using_fallback": self._using_fallback,
        }

        if self._using_fallback and self._fallback_store:
            metrics["fallback_metrics"] = self._fallback_store.get_metrics()
        else:
            try:
                metrics["total_entries"] = self.count()
            except Exception:
                metrics["total_entries"] = -1

        return metrics

    def close(self) -> None:
        """Close all connections and pools."""
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None

        if self._pool is not None:
            try:
                self._pool.disconnect()
            except Exception:
                pass
            self._pool = None

        self._connected = False

    async def close_async(self) -> None:
        """Async close all connections and pools."""
        if self._async_client is not None:
            try:
                await self._async_client.close()
            except Exception:
                pass
            self._async_client = None

        if self._async_pool is not None:
            try:
                await self._async_pool.disconnect()
            except Exception:
                pass
            self._async_pool = None

        self._connected = False

    def __enter__(self) -> "RedisThrottlingStore":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit, closes connections."""
        self.close()

    async def __aenter__(self) -> "RedisThrottlingStore":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit, closes connections."""
        await self.close_async()


# =============================================================================
# Factory Function
# =============================================================================


class ThrottlingStoreType:
    """Store type constants."""

    MEMORY = "memory"
    SQLITE = "sqlite"
    REDIS = "redis"


def create_throttling_store(
    store_type: str | None = None,
    **kwargs: Any,
) -> BaseThrottlingStore:
    """Factory function to create appropriate throttling store.

    Selects the store type based on configuration or environment variables.

    Environment variables:
        TRUTHOUND_THROTTLE_STORE_TYPE: Store type (memory, sqlite, redis)
        TRUTHOUND_THROTTLE_SQLITE_PATH: SQLite database path
        TRUTHOUND_THROTTLE_REDIS_URL: Redis connection URL (enables redis)

    Args:
        store_type: Explicit store type override. If None, auto-detects.
        **kwargs: Additional arguments passed to the store constructor.

    Returns:
        Configured BaseThrottlingStore instance.

    Example:
        # Auto-detect based on environment
        store = create_throttling_store()

        # Explicit type
        store = create_throttling_store("redis", default_ttl=7200)

        # SQLite with custom path
        store = create_throttling_store("sqlite", db_path="/tmp/throttle.db")
    """
    # Determine store type
    if store_type is None:
        store_type = os.getenv("TRUTHOUND_THROTTLE_STORE_TYPE")

    # Auto-detect if still None
    if store_type is None:
        redis_url = os.getenv("TRUTHOUND_THROTTLE_REDIS_URL")
        if redis_url and REDIS_AVAILABLE:
            store_type = ThrottlingStoreType.REDIS
            logger.info(
                "Auto-detected Redis throttling store from TRUTHOUND_THROTTLE_REDIS_URL"
            )
        elif os.getenv("TRUTHOUND_THROTTLE_SQLITE_PATH"):
            store_type = ThrottlingStoreType.SQLITE
            logger.info("Auto-detected SQLite store from TRUTHOUND_THROTTLE_SQLITE_PATH")
        else:
            store_type = ThrottlingStoreType.MEMORY
            logger.info("Using default InMemory throttling store")

    # Normalize store type
    store_type = store_type.lower().strip()

    # Create store based on type
    if store_type == ThrottlingStoreType.MEMORY:
        logger.info("Creating InMemory throttling store")
        return InMemoryThrottlingStore(**kwargs)

    elif store_type == ThrottlingStoreType.SQLITE:
        db_path = kwargs.pop("db_path", None) or os.getenv(
            "TRUTHOUND_THROTTLE_SQLITE_PATH", "throttling.db"
        )
        logger.info(f"Creating SQLite throttling store at {db_path}")
        return SQLiteThrottlingStore(db_path=db_path)

    elif store_type == ThrottlingStoreType.REDIS:
        if not REDIS_AVAILABLE:
            logger.warning(
                "Redis not available, falling back to InMemory store. "
                "Install with: pip install truthound-dashboard[redis]"
            )
            return InMemoryThrottlingStore(**kwargs)

        logger.info("Creating Redis throttling store")
        return RedisThrottlingStore(**kwargs)

    else:
        logger.warning(
            f"Unknown store type '{store_type}', falling back to InMemory store"
        )
        return InMemoryThrottlingStore(**kwargs)
