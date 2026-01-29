"""Storage backends for deduplication state.

This module provides storage backends for tracking sent notifications
and detecting duplicates.

Storage Backends:
    - InMemoryDeduplicationStore: Simple in-memory storage (development)
    - SQLiteDeduplicationStore: Persistent SQLite storage (production)
    - RedisDeduplicationStore: Redis-based storage (distributed deployments)

Each store tracks fingerprints with timestamps and supports
automatic cleanup of expired entries.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
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


@dataclass
class DeduplicationEntry:
    """A stored deduplication entry.

    Attributes:
        fingerprint: Unique fingerprint identifying the notification.
        first_seen: When this fingerprint was first seen.
        last_seen: When this fingerprint was last seen.
        count: Number of times this fingerprint was seen.
        metadata: Additional entry metadata.
    """

    fingerprint: str
    first_seen: datetime
    last_seen: datetime
    count: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_expired(self, window_seconds: int) -> bool:
        """Check if entry has expired based on window."""
        expiry = self.last_seen + timedelta(seconds=window_seconds)
        return datetime.utcnow() > expiry


class BaseDeduplicationStore(ABC):
    """Abstract base class for deduplication storage.

    All stores must implement methods for checking, recording,
    and cleaning up deduplication entries.
    """

    @abstractmethod
    def exists(self, fingerprint: str, window_seconds: int) -> bool:
        """Check if fingerprint exists within window.

        Args:
            fingerprint: The fingerprint to check.
            window_seconds: Time window in seconds.

        Returns:
            True if fingerprint exists and is not expired.
        """
        ...

    @abstractmethod
    def record(self, fingerprint: str, metadata: dict[str, Any] | None = None) -> None:
        """Record a fingerprint as sent.

        Args:
            fingerprint: The fingerprint to record.
            metadata: Optional metadata to store.
        """
        ...

    @abstractmethod
    def get(self, fingerprint: str) -> DeduplicationEntry | None:
        """Get entry by fingerprint.

        Args:
            fingerprint: The fingerprint to look up.

        Returns:
            Entry if found, None otherwise.
        """
        ...

    @abstractmethod
    def cleanup(self, max_age_seconds: int) -> int:
        """Remove expired entries.

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

    @abstractmethod
    def count(self) -> int:
        """Get total entry count."""
        ...


class InMemoryDeduplicationStore(BaseDeduplicationStore):
    """In-memory deduplication storage.

    Simple thread-safe in-memory storage suitable for
    development and single-process deployments.

    Note: Data is lost on process restart.
    """

    def __init__(self) -> None:
        """Initialize in-memory store."""
        self._entries: dict[str, DeduplicationEntry] = {}
        self._lock = threading.RLock()

    def exists(self, fingerprint: str, window_seconds: int) -> bool:
        """Check if fingerprint exists within window."""
        with self._lock:
            entry = self._entries.get(fingerprint)
            if entry is None:
                return False
            return not entry.is_expired(window_seconds)

    def record(self, fingerprint: str, metadata: dict[str, Any] | None = None) -> None:
        """Record a fingerprint."""
        now = datetime.utcnow()
        with self._lock:
            if fingerprint in self._entries:
                entry = self._entries[fingerprint]
                entry.last_seen = now
                entry.count += 1
                if metadata:
                    entry.metadata.update(metadata)
            else:
                self._entries[fingerprint] = DeduplicationEntry(
                    fingerprint=fingerprint,
                    first_seen=now,
                    last_seen=now,
                    count=1,
                    metadata=metadata or {},
                )

    def get(self, fingerprint: str) -> DeduplicationEntry | None:
        """Get entry by fingerprint."""
        with self._lock:
            return self._entries.get(fingerprint)

    def cleanup(self, max_age_seconds: int) -> int:
        """Remove expired entries."""
        cutoff = datetime.utcnow() - timedelta(seconds=max_age_seconds)
        removed = 0

        with self._lock:
            expired = [
                fp for fp, entry in self._entries.items()
                if entry.last_seen < cutoff
            ]
            for fp in expired:
                del self._entries[fp]
                removed += 1

        return removed

    def clear(self) -> None:
        """Clear all entries."""
        with self._lock:
            self._entries.clear()

    def count(self) -> int:
        """Get total entry count."""
        with self._lock:
            return len(self._entries)


class SQLiteDeduplicationStore(BaseDeduplicationStore):
    """SQLite-based persistent deduplication storage.

    Provides durable storage that survives process restarts.
    Thread-safe using connection pooling.

    Attributes:
        db_path: Path to SQLite database file.
    """

    def __init__(self, db_path: str | Path = "deduplication.db") -> None:
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
            CREATE TABLE IF NOT EXISTS deduplication_entries (
                fingerprint TEXT PRIMARY KEY,
                first_seen REAL NOT NULL,
                last_seen REAL NOT NULL,
                count INTEGER NOT NULL DEFAULT 1,
                metadata TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_dedup_last_seen
            ON deduplication_entries(last_seen)
        """)
        conn.commit()

    def exists(self, fingerprint: str, window_seconds: int) -> bool:
        """Check if fingerprint exists within window."""
        conn = self._get_connection()
        cutoff = time.time() - window_seconds

        cursor = conn.execute(
            """
            SELECT 1 FROM deduplication_entries
            WHERE fingerprint = ? AND last_seen >= ?
            """,
            (fingerprint, cutoff),
        )
        return cursor.fetchone() is not None

    def record(self, fingerprint: str, metadata: dict[str, Any] | None = None) -> None:
        """Record a fingerprint."""
        import json

        now = time.time()
        conn = self._get_connection()

        # Try to update existing
        cursor = conn.execute(
            """
            UPDATE deduplication_entries
            SET last_seen = ?, count = count + 1
            WHERE fingerprint = ?
            """,
            (now, fingerprint),
        )

        if cursor.rowcount == 0:
            # Insert new entry
            metadata_json = json.dumps(metadata) if metadata else None
            conn.execute(
                """
                INSERT INTO deduplication_entries
                (fingerprint, first_seen, last_seen, count, metadata)
                VALUES (?, ?, ?, 1, ?)
                """,
                (fingerprint, now, now, metadata_json),
            )

        conn.commit()

    def get(self, fingerprint: str) -> DeduplicationEntry | None:
        """Get entry by fingerprint."""
        import json

        conn = self._get_connection()
        cursor = conn.execute(
            """
            SELECT fingerprint, first_seen, last_seen, count, metadata
            FROM deduplication_entries
            WHERE fingerprint = ?
            """,
            (fingerprint,),
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

        return DeduplicationEntry(
            fingerprint=row["fingerprint"],
            first_seen=datetime.fromtimestamp(row["first_seen"]),
            last_seen=datetime.fromtimestamp(row["last_seen"]),
            count=row["count"],
            metadata=metadata,
        )

    def cleanup(self, max_age_seconds: int) -> int:
        """Remove expired entries."""
        conn = self._get_connection()
        cutoff = time.time() - max_age_seconds

        cursor = conn.execute(
            """
            DELETE FROM deduplication_entries
            WHERE last_seen < ?
            """,
            (cutoff,),
        )
        conn.commit()

        return cursor.rowcount

    def clear(self) -> None:
        """Clear all entries."""
        conn = self._get_connection()
        conn.execute("DELETE FROM deduplication_entries")
        conn.commit()

    def count(self) -> int:
        """Get total entry count."""
        conn = self._get_connection()
        cursor = conn.execute("SELECT COUNT(*) FROM deduplication_entries")
        return cursor.fetchone()[0]

    def close(self) -> None:
        """Close database connection."""
        if hasattr(self._local, "connection"):
            self._local.connection.close()
            del self._local.connection


class RedisDeduplicationStore(BaseDeduplicationStore):
    """Redis-based deduplication store for distributed deployments.

    Uses Redis strings with TTL for automatic expiration.
    Supports both sync and async Redis clients with connection pooling.

    This store is ideal for:
        - Multi-process deployments
        - Distributed systems
        - High-concurrency scenarios
        - Deployments requiring shared state

    Note: Requires the 'redis' optional dependency.
          Install with: pip install truthound-dashboard[redis]

    Attributes:
        redis_url: Redis connection URL.
        key_prefix: Prefix for all Redis keys.
        default_ttl: Default TTL in seconds for entries.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        key_prefix: str = "truthound:dedup:",
        default_ttl: int = 3600,  # 1 hour
        max_connections: int = 10,
        socket_timeout: float = 5.0,
        socket_connect_timeout: float = 5.0,
        retry_on_timeout: bool = True,
    ) -> None:
        """Initialize Redis store.

        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379/0).
            key_prefix: Prefix for all deduplication keys.
            default_ttl: Default TTL in seconds for entries.
            max_connections: Maximum connections in the pool.
            socket_timeout: Socket timeout in seconds.
            socket_connect_timeout: Connection timeout in seconds.
            retry_on_timeout: Whether to retry on timeout.

        Raises:
            ImportError: If redis package is not installed.
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "Redis support requires the 'redis' package. "
                "Install with: pip install truthound-dashboard[redis] "
                "or pip install redis"
            )

        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        self.max_connections = max_connections
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.retry_on_timeout = retry_on_timeout

        # Connection pool for sync client
        self._pool: redis.ConnectionPool | None = None
        self._client: redis.Redis | None = None

        # Connection pool for async client
        self._async_pool: redis.asyncio.ConnectionPool | None = None
        self._async_client: redis.asyncio.Redis | None = None

        # Lock for thread-safe initialization
        self._lock = threading.Lock()

    def _get_key(self, fingerprint: str) -> str:
        """Get full Redis key for fingerprint.

        Args:
            fingerprint: The fingerprint string.

        Returns:
            Full Redis key with prefix.
        """
        return f"{self.key_prefix}{fingerprint}"

    def _create_pool(self) -> redis.ConnectionPool:
        """Create a connection pool for sync client.

        Returns:
            Configured connection pool.
        """
        return redis.ConnectionPool.from_url(
            self.redis_url,
            max_connections=self.max_connections,
            socket_timeout=self.socket_timeout,
            socket_connect_timeout=self.socket_connect_timeout,
            retry_on_timeout=self.retry_on_timeout,
        )

    async def _create_async_pool(self) -> redis.asyncio.ConnectionPool:
        """Create a connection pool for async client.

        Returns:
            Configured async connection pool.
        """
        return redis.asyncio.ConnectionPool.from_url(
            self.redis_url,
            max_connections=self.max_connections,
            socket_timeout=self.socket_timeout,
            socket_connect_timeout=self.socket_connect_timeout,
            retry_on_timeout=self.retry_on_timeout,
        )

    @property
    def client(self) -> redis.Redis:
        """Get sync Redis client with connection pooling.

        Creates the connection pool and client on first access.

        Returns:
            Redis client instance.
        """
        if self._client is None:
            with self._lock:
                if self._client is None:
                    self._pool = self._create_pool()
                    self._client = redis.Redis(connection_pool=self._pool)
        return self._client

    async def get_async_client(self) -> redis.asyncio.Redis:
        """Get async Redis client with connection pooling.

        Creates the async connection pool and client on first access.

        Returns:
            Async Redis client instance.
        """
        if self._async_client is None:
            self._async_pool = await self._create_async_pool()
            self._async_client = redis.asyncio.Redis(
                connection_pool=self._async_pool
            )
        return self._async_client

    def exists(self, fingerprint: str, window_seconds: int) -> bool:
        """Check if fingerprint exists in Redis.

        Note: Redis handles expiration via TTL, so window_seconds is not
        used here. The entry either exists (not expired) or doesn't.

        Args:
            fingerprint: The fingerprint to check.
            window_seconds: Time window (unused, TTL handles expiration).

        Returns:
            True if fingerprint exists and hasn't expired.
        """
        key = self._get_key(fingerprint)
        return self.client.exists(key) > 0

    async def exists_async(self, fingerprint: str, window_seconds: int) -> bool:
        """Async check if fingerprint exists in Redis.

        Args:
            fingerprint: The fingerprint to check.
            window_seconds: Time window (unused, TTL handles expiration).

        Returns:
            True if fingerprint exists and hasn't expired.
        """
        client = await self.get_async_client()
        key = self._get_key(fingerprint)
        return await client.exists(key) > 0

    def record(self, fingerprint: str, metadata: dict[str, Any] | None = None) -> None:
        """Record fingerprint with TTL.

        Stores the fingerprint with metadata and sets TTL for auto-expiration.
        If the fingerprint already exists, updates metadata and resets TTL.

        Args:
            fingerprint: The fingerprint to record.
            metadata: Optional metadata to store with the entry.
        """
        key = self._get_key(fingerprint)
        now = time.time()

        # Get existing entry to preserve first_seen and increment count
        existing = self.client.get(key)
        if existing:
            try:
                data = json.loads(existing)
                data["last_seen"] = now
                data["count"] = data.get("count", 1) + 1
                if metadata:
                    data["metadata"].update(metadata)
            except (json.JSONDecodeError, KeyError):
                data = {
                    "first_seen": now,
                    "last_seen": now,
                    "count": 1,
                    "metadata": metadata or {},
                }
        else:
            data = {
                "first_seen": now,
                "last_seen": now,
                "count": 1,
                "metadata": metadata or {},
            }

        value = json.dumps(data)
        self.client.setex(key, self.default_ttl, value)

    async def record_async(
        self, fingerprint: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """Async record fingerprint with TTL.

        Args:
            fingerprint: The fingerprint to record.
            metadata: Optional metadata to store with the entry.
        """
        client = await self.get_async_client()
        key = self._get_key(fingerprint)
        now = time.time()

        # Get existing entry to preserve first_seen and increment count
        existing = await client.get(key)
        if existing:
            try:
                data = json.loads(existing)
                data["last_seen"] = now
                data["count"] = data.get("count", 1) + 1
                if metadata:
                    data["metadata"].update(metadata)
            except (json.JSONDecodeError, KeyError):
                data = {
                    "first_seen": now,
                    "last_seen": now,
                    "count": 1,
                    "metadata": metadata or {},
                }
        else:
            data = {
                "first_seen": now,
                "last_seen": now,
                "count": 1,
                "metadata": metadata or {},
            }

        value = json.dumps(data)
        await client.setex(key, self.default_ttl, value)

    def get(self, fingerprint: str) -> DeduplicationEntry | None:
        """Get entry by fingerprint.

        Args:
            fingerprint: The fingerprint to look up.

        Returns:
            Entry if found, None otherwise.
        """
        key = self._get_key(fingerprint)
        data = self.client.get(key)

        if data is None:
            return None

        try:
            parsed = json.loads(data)
            return DeduplicationEntry(
                fingerprint=fingerprint,
                first_seen=datetime.fromtimestamp(parsed["first_seen"]),
                last_seen=datetime.fromtimestamp(parsed["last_seen"]),
                count=parsed.get("count", 1),
                metadata=parsed.get("metadata", {}),
            )
        except (json.JSONDecodeError, KeyError):
            return None

    async def get_async(self, fingerprint: str) -> DeduplicationEntry | None:
        """Async get entry by fingerprint.

        Args:
            fingerprint: The fingerprint to look up.

        Returns:
            Entry if found, None otherwise.
        """
        client = await self.get_async_client()
        key = self._get_key(fingerprint)
        data = await client.get(key)

        if data is None:
            return None

        try:
            parsed = json.loads(data)
            return DeduplicationEntry(
                fingerprint=fingerprint,
                first_seen=datetime.fromtimestamp(parsed["first_seen"]),
                last_seen=datetime.fromtimestamp(parsed["last_seen"]),
                count=parsed.get("count", 1),
                metadata=parsed.get("metadata", {}),
            )
        except (json.JSONDecodeError, KeyError):
            return None

    def count(self) -> int:
        """Count entries (approximate using SCAN).

        Uses SCAN to iterate through keys without blocking Redis.

        Returns:
            Approximate count of deduplication entries.
        """
        count = 0
        cursor = 0
        pattern = f"{self.key_prefix}*"

        while True:
            cursor, keys = self.client.scan(cursor, match=pattern, count=100)
            count += len(keys)
            if cursor == 0:
                break

        return count

    async def count_async(self) -> int:
        """Async count entries.

        Returns:
            Approximate count of deduplication entries.
        """
        client = await self.get_async_client()
        count = 0
        cursor = 0
        pattern = f"{self.key_prefix}*"

        while True:
            cursor, keys = await client.scan(cursor, match=pattern, count=100)
            count += len(keys)
            if cursor == 0:
                break

        return count

    def cleanup(self, max_age_seconds: int) -> int:
        """Redis handles expiration via TTL, no manual cleanup needed.

        This method is a no-op for Redis as TTL handles expiration automatically.

        Args:
            max_age_seconds: Maximum age (unused for Redis).

        Returns:
            Always returns 0 as Redis handles expiration.
        """
        # Redis handles expiration automatically via TTL
        return 0

    def clear(self) -> None:
        """Clear all deduplication keys.

        Uses SCAN to find and delete all keys with the dedup prefix.
        This is done in batches to avoid blocking Redis.
        """
        pattern = f"{self.key_prefix}*"
        cursor = 0

        while True:
            cursor, keys = self.client.scan(cursor, match=pattern, count=100)
            if keys:
                self.client.delete(*keys)
            if cursor == 0:
                break

    async def clear_async(self) -> None:
        """Async clear all deduplication keys."""
        client = await self.get_async_client()
        pattern = f"{self.key_prefix}*"
        cursor = 0

        while True:
            cursor, keys = await client.scan(cursor, match=pattern, count=100)
            if keys:
                await client.delete(*keys)
            if cursor == 0:
                break

    def health_check(self) -> bool:
        """Check Redis connection health.

        Performs a PING command to verify connectivity.

        Returns:
            True if Redis is reachable, False otherwise.
        """
        try:
            return self.client.ping()
        except Exception:
            return False

    async def health_check_async(self) -> bool:
        """Async check Redis connection health.

        Returns:
            True if Redis is reachable, False otherwise.
        """
        try:
            client = await self.get_async_client()
            return await client.ping()
        except Exception:
            return False

    def get_info(self) -> dict[str, Any]:
        """Get Redis server information.

        Returns:
            Dictionary containing Redis server info.
        """
        try:
            info = self.client.info()
            return {
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "uptime_in_seconds": info.get("uptime_in_seconds"),
                "db0": info.get("db0", {}),
            }
        except Exception as e:
            return {"error": str(e)}

    def set_ttl(self, fingerprint: str, ttl_seconds: int) -> bool:
        """Set custom TTL for a specific fingerprint.

        Args:
            fingerprint: The fingerprint to update.
            ttl_seconds: New TTL in seconds.

        Returns:
            True if TTL was set, False if key doesn't exist.
        """
        key = self._get_key(fingerprint)
        return self.client.expire(key, ttl_seconds)

    def get_ttl(self, fingerprint: str) -> int:
        """Get remaining TTL for a fingerprint.

        Args:
            fingerprint: The fingerprint to check.

        Returns:
            TTL in seconds, -1 if no TTL, -2 if key doesn't exist.
        """
        key = self._get_key(fingerprint)
        return self.client.ttl(key)

    def close(self) -> None:
        """Close all connections and pools.

        Should be called when the store is no longer needed
        to release resources.
        """
        if self._client is not None:
            self._client.close()
            self._client = None

        if self._pool is not None:
            self._pool.disconnect()
            self._pool = None

        # Note: Async client/pool should be closed in async context
        # using close_async() method

    async def close_async(self) -> None:
        """Async close all connections and pools."""
        if self._async_client is not None:
            await self._async_client.close()
            self._async_client = None

        if self._async_pool is not None:
            await self._async_pool.disconnect()
            self._async_pool = None

    def __enter__(self) -> "RedisDeduplicationStore":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit, closes connections."""
        self.close()

    async def __aenter__(self) -> "RedisDeduplicationStore":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit, closes connections."""
        await self.close_async()


# ============================================================================
# Redis Streams Deduplication Store
# ============================================================================


@dataclass
class DeduplicationMetrics:
    """Metrics for deduplication store operations.

    Attributes:
        hits: Number of duplicate detections (cache hits).
        misses: Number of non-duplicate entries (cache misses).
        records: Number of fingerprints recorded.
        errors: Number of Redis errors encountered.
        fallbacks: Number of times fallback to InMemory was used.
        reconnections: Number of successful reconnections.
    """

    hits: int = 0
    misses: int = 0
    records: int = 0
    errors: int = 0
    fallbacks: int = 0
    reconnections: int = 0

    def to_dict(self) -> dict[str, int]:
        """Convert metrics to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "records": self.records,
            "errors": self.errors,
            "fallbacks": self.fallbacks,
            "reconnections": self.reconnections,
            "total_checks": self.hits + self.misses,
            "hit_rate": round(self.hits / max(1, self.hits + self.misses) * 100, 2),
        }


class RedisStreamsDeduplicationStore(BaseDeduplicationStore):
    """Production-ready Redis Streams based deduplication store.

    Uses Redis Streams for robust distributed deduplication with:
        - Connection pool management with configurable pool size
        - Automatic reconnection with exponential backoff
        - TTL management for stream entries (auto-cleanup)
        - Consumer groups for distributed deduplication
        - Graceful degradation (fallback to InMemory on Redis failure)
        - Health check endpoint support
        - Comprehensive metrics collection

    Configuration via environment variables:
        TRUTHOUND_DEDUP_REDIS_URL: Redis connection URL (default: redis://localhost:6379/0)
        TRUTHOUND_DEDUP_REDIS_PREFIX: Key prefix (default: truthound:dedup:streams:)
        TRUTHOUND_DEDUP_REDIS_TTL: Default TTL in seconds (default: 3600)
        TRUTHOUND_DEDUP_REDIS_POOL_SIZE: Connection pool size (default: 10)
        TRUTHOUND_DEDUP_REDIS_SOCKET_TIMEOUT: Socket timeout (default: 5.0)
        TRUTHOUND_DEDUP_REDIS_CONNECT_TIMEOUT: Connection timeout (default: 5.0)
        TRUTHOUND_DEDUP_REDIS_MAX_RETRIES: Max retry attempts (default: 3)
        TRUTHOUND_DEDUP_REDIS_RETRY_BASE_DELAY: Base delay for exponential backoff (default: 1.0)
        TRUTHOUND_DEDUP_REDIS_CONSUMER_GROUP: Consumer group name (default: truthound-dedup)
        TRUTHOUND_DEDUP_REDIS_CONSUMER_NAME: Consumer name (default: auto-generated)
        TRUTHOUND_DEDUP_REDIS_STREAM_MAX_LEN: Max stream length (default: 100000)
        TRUTHOUND_DEDUP_FALLBACK_ENABLED: Enable fallback to InMemory (default: true)

    Example:
        # Basic usage
        store = RedisStreamsDeduplicationStore()

        # Custom configuration
        store = RedisStreamsDeduplicationStore(
            redis_url="redis://myredis:6379/1",
            default_ttl=7200,
            max_connections=20,
            enable_fallback=True,
        )

        # With context manager
        async with RedisStreamsDeduplicationStore() as store:
            if not await store.exists_async("fingerprint", 300):
                await store.record_async("fingerprint", {"key": "value"})

    Note: Requires the 'redis' optional dependency.
          Install with: pip install truthound-dashboard[redis]
    """

    # Stream entry field names
    FIELD_FINGERPRINT = "fingerprint"
    FIELD_FIRST_SEEN = "first_seen"
    FIELD_LAST_SEEN = "last_seen"
    FIELD_COUNT = "count"
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
        consumer_group: str | None = None,
        consumer_name: str | None = None,
        stream_max_len: int | None = None,
        enable_fallback: bool | None = None,
        logger: Any | None = None,
    ) -> None:
        """Initialize Redis Streams deduplication store.

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
            consumer_group: Consumer group name for stream processing.
            consumer_name: Consumer name (auto-generated if not provided).
            stream_max_len: Maximum stream length (MAXLEN).
            enable_fallback: Enable fallback to InMemory on Redis failure.
            logger: Custom logger instance.

        Raises:
            ImportError: If redis package is not installed.
        """
        import logging
        import os
        import uuid

        if not REDIS_AVAILABLE:
            raise ImportError(
                "Redis support requires the 'redis' package. "
                "Install with: pip install truthound-dashboard[redis] "
                "or pip install redis"
            )

        # Configuration from environment or parameters
        self.redis_url = redis_url or os.getenv(
            "TRUTHOUND_DEDUP_REDIS_URL", "redis://localhost:6379/0"
        )
        self.key_prefix = key_prefix or os.getenv(
            "TRUTHOUND_DEDUP_REDIS_PREFIX", "truthound:dedup:streams:"
        )
        self.default_ttl = default_ttl or int(
            os.getenv("TRUTHOUND_DEDUP_REDIS_TTL", "3600")
        )
        self.max_connections = max_connections or int(
            os.getenv("TRUTHOUND_DEDUP_REDIS_POOL_SIZE", "10")
        )
        self.socket_timeout = socket_timeout or float(
            os.getenv("TRUTHOUND_DEDUP_REDIS_SOCKET_TIMEOUT", "5.0")
        )
        self.socket_connect_timeout = socket_connect_timeout or float(
            os.getenv("TRUTHOUND_DEDUP_REDIS_CONNECT_TIMEOUT", "5.0")
        )
        self.max_retries = max_retries or int(
            os.getenv("TRUTHOUND_DEDUP_REDIS_MAX_RETRIES", "3")
        )
        self.retry_base_delay = retry_base_delay or float(
            os.getenv("TRUTHOUND_DEDUP_REDIS_RETRY_BASE_DELAY", "1.0")
        )
        self.consumer_group = consumer_group or os.getenv(
            "TRUTHOUND_DEDUP_REDIS_CONSUMER_GROUP", "truthound-dedup"
        )
        self.consumer_name = consumer_name or os.getenv(
            "TRUTHOUND_DEDUP_REDIS_CONSUMER_NAME", f"consumer-{uuid.uuid4().hex[:8]}"
        )
        self.stream_max_len = stream_max_len or int(
            os.getenv("TRUTHOUND_DEDUP_REDIS_STREAM_MAX_LEN", "100000")
        )

        fallback_env = os.getenv("TRUTHOUND_DEDUP_FALLBACK_ENABLED", "true")
        self.enable_fallback = (
            enable_fallback
            if enable_fallback is not None
            else fallback_env.lower() == "true"
        )

        # Logger setup
        self._logger = logger or logging.getLogger(__name__)

        # Connection pool for sync client
        self._pool: redis.ConnectionPool | None = None
        self._client: redis.Redis | None = None

        # Connection pool for async client
        self._async_pool: redis.asyncio.ConnectionPool | None = None
        self._async_client: redis.asyncio.Redis | None = None

        # Locks for thread-safe initialization
        self._lock = threading.Lock()
        self._async_lock: Any = None  # Created lazily for asyncio

        # Fallback store for graceful degradation
        self._fallback_store: InMemoryDeduplicationStore | None = None
        self._using_fallback = False

        # Connection state tracking
        self._connected = False
        self._retry_count = 0
        self._last_error: Exception | None = None
        self._last_error_time: float | None = None

        # Metrics
        self._metrics = DeduplicationMetrics()

        # Index tracking key (for fast lookups)
        self._index_key = f"{self.key_prefix}index"

        # Stream key
        self._stream_key = f"{self.key_prefix}stream"

    def _get_key(self, fingerprint: str) -> str:
        """Get full Redis key for fingerprint.

        Args:
            fingerprint: The fingerprint string.

        Returns:
            Full Redis key with prefix.
        """
        return f"{self.key_prefix}fp:{fingerprint}"

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

    def _get_fallback_store(self) -> InMemoryDeduplicationStore:
        """Get or create fallback in-memory store.

        Returns:
            InMemoryDeduplicationStore instance.
        """
        if self._fallback_store is None:
            self._fallback_store = InMemoryDeduplicationStore()
        return self._fallback_store

    def _calculate_backoff_delay(self) -> float:
        """Calculate exponential backoff delay.

        Returns:
            Delay in seconds.
        """
        import random

        # Exponential backoff with jitter
        delay = self.retry_base_delay * (2**self._retry_count)
        # Add jitter (up to 25% of delay)
        jitter = delay * random.uniform(0, 0.25)
        return min(delay + jitter, 60.0)  # Cap at 60 seconds

    def _handle_redis_error(self, error: Exception, operation: str) -> None:
        """Handle Redis errors with logging and metrics.

        Args:
            error: The exception that occurred.
            operation: Name of the operation that failed.
        """
        self._metrics.errors += 1
        self._last_error = error
        self._last_error_time = time.time()
        self._connected = False

        self._logger.error(
            f"Redis error during {operation}: {error}",
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
            self._logger.warning(
                f"Max retries ({self.max_retries}) reached, using fallback"
            )
            return False

        delay = self._calculate_backoff_delay()
        self._logger.info(
            f"Attempting Redis reconnection in {delay:.2f}s (attempt {self._retry_count + 1}/{self.max_retries})"
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
                self._metrics.reconnections += 1
                self._logger.info("Redis reconnection successful")
                return True
        except Exception as e:
            self._logger.warning(f"Reconnection attempt failed: {e}")

        return False

    async def _try_reconnect_async(self) -> bool:
        """Attempt to reconnect to Redis asynchronously.

        Returns:
            True if reconnection successful, False otherwise.
        """
        import asyncio

        if self._retry_count >= self.max_retries:
            self._logger.warning(
                f"Max retries ({self.max_retries}) reached, using fallback"
            )
            return False

        delay = self._calculate_backoff_delay()
        self._logger.info(
            f"Attempting async Redis reconnection in {delay:.2f}s (attempt {self._retry_count + 1}/{self.max_retries})"
        )

        await asyncio.sleep(delay)
        self._retry_count += 1

        try:
            # Close existing connections
            if self._async_client:
                try:
                    await self._async_client.close()
                except Exception:
                    pass
                self._async_client = None

            if self._async_pool:
                try:
                    await self._async_pool.disconnect()
                except Exception:
                    pass
                self._async_pool = None

            # Create new connection
            self._async_pool = await self._create_async_pool()
            self._async_client = redis.asyncio.Redis(connection_pool=self._async_pool)

            # Test connection
            if await self._async_client.ping():
                self._connected = True
                self._retry_count = 0
                self._using_fallback = False
                self._metrics.reconnections += 1
                self._logger.info("Async Redis reconnection successful")
                return True
        except Exception as e:
            self._logger.warning(f"Async reconnection attempt failed: {e}")

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
                        self._logger.debug("Redis sync client connected")
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
        import asyncio

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
                        self._logger.debug("Redis async client connected")
                    except Exception as e:
                        self._handle_redis_error(e, "async_client_init")
                        raise
        return self._async_client

    async def _ensure_consumer_group(self, client: "redis.asyncio.Redis") -> None:
        """Ensure consumer group exists for stream.

        Args:
            client: Redis async client.
        """
        try:
            await client.xgroup_create(
                self._stream_key,
                self.consumer_group,
                id="0",
                mkstream=True,
            )
            self._logger.debug(f"Created consumer group: {self.consumer_group}")
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
            # Group already exists, which is fine

    def _serialize_entry(
        self,
        fingerprint: str,
        first_seen: float,
        last_seen: float,
        count: int,
        metadata: dict[str, Any] | None,
    ) -> dict[str, str]:
        """Serialize entry for Redis storage.

        Args:
            fingerprint: The fingerprint.
            first_seen: First seen timestamp.
            last_seen: Last seen timestamp.
            count: Occurrence count.
            metadata: Optional metadata.

        Returns:
            Dictionary suitable for Redis.
        """
        return {
            self.FIELD_FINGERPRINT: fingerprint,
            self.FIELD_FIRST_SEEN: str(first_seen),
            self.FIELD_LAST_SEEN: str(last_seen),
            self.FIELD_COUNT: str(count),
            self.FIELD_METADATA: json.dumps(metadata or {}),
        }

    def _deserialize_entry(
        self, fingerprint: str, data: dict[str, str]
    ) -> DeduplicationEntry:
        """Deserialize entry from Redis storage.

        Args:
            fingerprint: The fingerprint.
            data: Dictionary from Redis.

        Returns:
            DeduplicationEntry instance.
        """
        metadata = {}
        if data.get(self.FIELD_METADATA):
            try:
                metadata = json.loads(data[self.FIELD_METADATA])
            except json.JSONDecodeError:
                pass

        return DeduplicationEntry(
            fingerprint=fingerprint,
            first_seen=datetime.fromtimestamp(float(data.get(self.FIELD_FIRST_SEEN, 0))),
            last_seen=datetime.fromtimestamp(float(data.get(self.FIELD_LAST_SEEN, 0))),
            count=int(data.get(self.FIELD_COUNT, 1)),
            metadata=metadata,
        )

    def exists(self, fingerprint: str, window_seconds: int) -> bool:
        """Check if fingerprint exists within window.

        Falls back to InMemory store on Redis failure if enabled.

        Args:
            fingerprint: The fingerprint to check.
            window_seconds: Time window in seconds.

        Returns:
            True if fingerprint exists and is not expired.
        """
        # Use fallback if already in fallback mode
        if self._using_fallback and self.enable_fallback:
            result = self._get_fallback_store().exists(fingerprint, window_seconds)
            if result:
                self._metrics.hits += 1
            else:
                self._metrics.misses += 1
            return result

        try:
            key = self._get_key(fingerprint)
            data = self.client.hgetall(key)

            if not data:
                self._metrics.misses += 1
                return False

            # Check if expired based on window
            last_seen = float(data.get(self.FIELD_LAST_SEEN, 0))
            cutoff = time.time() - window_seconds

            if last_seen >= cutoff:
                self._metrics.hits += 1
                return True
            else:
                self._metrics.misses += 1
                return False

        except Exception as e:
            self._handle_redis_error(e, "exists")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                self._logger.warning("Falling back to InMemory store")
                result = self._get_fallback_store().exists(fingerprint, window_seconds)
                if result:
                    self._metrics.hits += 1
                else:
                    self._metrics.misses += 1
                return result

            raise

    async def exists_async(self, fingerprint: str, window_seconds: int) -> bool:
        """Async check if fingerprint exists within window.

        Falls back to InMemory store on Redis failure if enabled.

        Args:
            fingerprint: The fingerprint to check.
            window_seconds: Time window in seconds.

        Returns:
            True if fingerprint exists and is not expired.
        """
        # Use fallback if already in fallback mode
        if self._using_fallback and self.enable_fallback:
            result = self._get_fallback_store().exists(fingerprint, window_seconds)
            if result:
                self._metrics.hits += 1
            else:
                self._metrics.misses += 1
            return result

        try:
            client = await self.get_async_client()
            key = self._get_key(fingerprint)
            data = await client.hgetall(key)

            if not data:
                self._metrics.misses += 1
                return False

            # Check if expired based on window
            last_seen = float(data.get(self.FIELD_LAST_SEEN, 0))
            cutoff = time.time() - window_seconds

            if last_seen >= cutoff:
                self._metrics.hits += 1
                return True
            else:
                self._metrics.misses += 1
                return False

        except Exception as e:
            self._handle_redis_error(e, "exists_async")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                self._logger.warning("Falling back to InMemory store")
                result = self._get_fallback_store().exists(fingerprint, window_seconds)
                if result:
                    self._metrics.hits += 1
                else:
                    self._metrics.misses += 1
                return result

            raise

    def record(self, fingerprint: str, metadata: dict[str, Any] | None = None) -> None:
        """Record a fingerprint with automatic TTL and stream logging.

        Args:
            fingerprint: The fingerprint to record.
            metadata: Optional metadata to store.
        """
        # Use fallback if already in fallback mode
        if self._using_fallback and self.enable_fallback:
            self._get_fallback_store().record(fingerprint, metadata)
            self._metrics.records += 1
            return

        try:
            key = self._get_key(fingerprint)
            now = time.time()
            client = self.client

            # Use pipeline for atomicity
            pipe = client.pipeline()

            # Get existing entry
            existing = client.hgetall(key)

            if existing:
                # Update existing entry
                first_seen = float(existing.get(self.FIELD_FIRST_SEEN, now))
                count = int(existing.get(self.FIELD_COUNT, 0)) + 1
                old_metadata = {}
                if existing.get(self.FIELD_METADATA):
                    try:
                        old_metadata = json.loads(existing[self.FIELD_METADATA])
                    except json.JSONDecodeError:
                        pass
                if metadata:
                    old_metadata.update(metadata)
                final_metadata = old_metadata
            else:
                first_seen = now
                count = 1
                final_metadata = metadata or {}

            # Store entry as hash
            entry_data = self._serialize_entry(
                fingerprint, first_seen, now, count, final_metadata
            )
            pipe.hset(key, mapping=entry_data)
            pipe.expire(key, self.default_ttl)

            # Add to index set for tracking
            pipe.sadd(self._index_key, fingerprint)
            pipe.expire(self._index_key, self.default_ttl * 2)

            # Add to stream for audit/replay (with MAXLEN for auto-trimming)
            stream_entry = {
                "fingerprint": fingerprint,
                "timestamp": str(now),
                "action": "record",
                "count": str(count),
            }
            pipe.xadd(
                self._stream_key,
                stream_entry,
                maxlen=self.stream_max_len,
                approximate=True,
            )

            pipe.execute()
            self._metrics.records += 1

        except Exception as e:
            self._handle_redis_error(e, "record")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                self._logger.warning("Falling back to InMemory store")
                self._get_fallback_store().record(fingerprint, metadata)
                self._metrics.records += 1
                return

            raise

    async def record_async(
        self, fingerprint: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """Async record a fingerprint with automatic TTL and stream logging.

        Args:
            fingerprint: The fingerprint to record.
            metadata: Optional metadata to store.
        """
        # Use fallback if already in fallback mode
        if self._using_fallback and self.enable_fallback:
            self._get_fallback_store().record(fingerprint, metadata)
            self._metrics.records += 1
            return

        try:
            client = await self.get_async_client()
            key = self._get_key(fingerprint)
            now = time.time()

            # Ensure consumer group exists
            await self._ensure_consumer_group(client)

            # Use pipeline for atomicity
            pipe = client.pipeline()

            # Get existing entry
            existing = await client.hgetall(key)

            if existing:
                # Update existing entry
                first_seen = float(existing.get(self.FIELD_FIRST_SEEN, now))
                count = int(existing.get(self.FIELD_COUNT, 0)) + 1
                old_metadata = {}
                if existing.get(self.FIELD_METADATA):
                    try:
                        old_metadata = json.loads(existing[self.FIELD_METADATA])
                    except json.JSONDecodeError:
                        pass
                if metadata:
                    old_metadata.update(metadata)
                final_metadata = old_metadata
            else:
                first_seen = now
                count = 1
                final_metadata = metadata or {}

            # Store entry as hash
            entry_data = self._serialize_entry(
                fingerprint, first_seen, now, count, final_metadata
            )
            pipe.hset(key, mapping=entry_data)
            pipe.expire(key, self.default_ttl)

            # Add to index set for tracking
            pipe.sadd(self._index_key, fingerprint)
            pipe.expire(self._index_key, self.default_ttl * 2)

            # Add to stream for audit/replay (with MAXLEN for auto-trimming)
            stream_entry = {
                "fingerprint": fingerprint,
                "timestamp": str(now),
                "action": "record",
                "count": str(count),
            }
            pipe.xadd(
                self._stream_key,
                stream_entry,
                maxlen=self.stream_max_len,
                approximate=True,
            )

            await pipe.execute()
            self._metrics.records += 1

        except Exception as e:
            self._handle_redis_error(e, "record_async")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                self._logger.warning("Falling back to InMemory store")
                self._get_fallback_store().record(fingerprint, metadata)
                self._metrics.records += 1
                return

            raise

    def get(self, fingerprint: str) -> DeduplicationEntry | None:
        """Get entry by fingerprint.

        Args:
            fingerprint: The fingerprint to look up.

        Returns:
            Entry if found, None otherwise.
        """
        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().get(fingerprint)

        try:
            key = self._get_key(fingerprint)
            data = self.client.hgetall(key)

            if not data:
                return None

            return self._deserialize_entry(fingerprint, data)

        except Exception as e:
            self._handle_redis_error(e, "get")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                return self._get_fallback_store().get(fingerprint)

            raise

    async def get_async(self, fingerprint: str) -> DeduplicationEntry | None:
        """Async get entry by fingerprint.

        Args:
            fingerprint: The fingerprint to look up.

        Returns:
            Entry if found, None otherwise.
        """
        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().get(fingerprint)

        try:
            client = await self.get_async_client()
            key = self._get_key(fingerprint)
            data = await client.hgetall(key)

            if not data:
                return None

            return self._deserialize_entry(fingerprint, data)

        except Exception as e:
            self._handle_redis_error(e, "get_async")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                return self._get_fallback_store().get(fingerprint)

            raise

    def cleanup(self, max_age_seconds: int) -> int:
        """Remove expired entries.

        Redis handles TTL automatically, but this method can be used
        to perform explicit cleanup of old stream entries.

        Args:
            max_age_seconds: Maximum age of entries to keep.

        Returns:
            Number of entries removed.
        """
        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().cleanup(max_age_seconds)

        try:
            client = self.client
            cutoff = time.time() - max_age_seconds
            removed = 0

            # Get all fingerprints from index
            fingerprints = client.smembers(self._index_key)

            for fp in fingerprints:
                key = self._get_key(fp)
                data = client.hgetall(key)

                if not data:
                    # Entry expired, remove from index
                    client.srem(self._index_key, fp)
                    removed += 1
                elif float(data.get(self.FIELD_LAST_SEEN, 0)) < cutoff:
                    # Entry is old, delete it
                    client.delete(key)
                    client.srem(self._index_key, fp)
                    removed += 1

            # Trim stream to remove old entries
            stream_info = client.xinfo_stream(self._stream_key)
            if stream_info and stream_info.get("length", 0) > 0:
                # Get first entry timestamp
                first_entry = client.xrange(self._stream_key, count=1)
                if first_entry:
                    entry_id = first_entry[0][0]
                    # Stream ID format: timestamp-sequence
                    entry_ts = int(entry_id.split("-")[0]) / 1000
                    if entry_ts < cutoff:
                        # Trim old entries
                        cutoff_id = f"{int(cutoff * 1000)}-0"
                        trimmed = client.xtrim(
                            self._stream_key, minid=cutoff_id, approximate=True
                        )
                        removed += trimmed

            return removed

        except Exception as e:
            self._handle_redis_error(e, "cleanup")

            if self.enable_fallback:
                self._using_fallback = True
                return self._get_fallback_store().cleanup(max_age_seconds)

            raise

    async def cleanup_async(self, max_age_seconds: int) -> int:
        """Async remove expired entries.

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

            # Get all fingerprints from index
            fingerprints = await client.smembers(self._index_key)

            for fp in fingerprints:
                key = self._get_key(fp)
                data = await client.hgetall(key)

                if not data:
                    # Entry expired, remove from index
                    await client.srem(self._index_key, fp)
                    removed += 1
                elif float(data.get(self.FIELD_LAST_SEEN, 0)) < cutoff:
                    # Entry is old, delete it
                    await client.delete(key)
                    await client.srem(self._index_key, fp)
                    removed += 1

            # Trim stream to remove old entries
            try:
                stream_info = await client.xinfo_stream(self._stream_key)
                if stream_info and stream_info.get("length", 0) > 0:
                    # Trim old entries
                    cutoff_id = f"{int(cutoff * 1000)}-0"
                    trimmed = await client.xtrim(
                        self._stream_key, minid=cutoff_id, approximate=True
                    )
                    removed += trimmed
            except redis.ResponseError:
                # Stream might not exist
                pass

            return removed

        except Exception as e:
            self._handle_redis_error(e, "cleanup_async")

            if self.enable_fallback:
                self._using_fallback = True
                return self._get_fallback_store().cleanup(max_age_seconds)

            raise

    def clear(self) -> None:
        """Clear all deduplication entries."""
        if self._using_fallback and self.enable_fallback:
            self._get_fallback_store().clear()
            return

        try:
            client = self.client

            # Get all fingerprints from index
            fingerprints = client.smembers(self._index_key)

            if fingerprints:
                # Delete all entry keys
                keys_to_delete = [self._get_key(fp) for fp in fingerprints]
                client.delete(*keys_to_delete)

            # Delete index
            client.delete(self._index_key)

            # Delete stream
            client.delete(self._stream_key)

        except Exception as e:
            self._handle_redis_error(e, "clear")

            if self.enable_fallback:
                self._using_fallback = True
                self._get_fallback_store().clear()
                return

            raise

    async def clear_async(self) -> None:
        """Async clear all deduplication entries."""
        if self._using_fallback and self.enable_fallback:
            self._get_fallback_store().clear()
            return

        try:
            client = await self.get_async_client()

            # Get all fingerprints from index
            fingerprints = await client.smembers(self._index_key)

            if fingerprints:
                # Delete all entry keys
                keys_to_delete = [self._get_key(fp) for fp in fingerprints]
                await client.delete(*keys_to_delete)

            # Delete index
            await client.delete(self._index_key)

            # Delete stream
            await client.delete(self._stream_key)

        except Exception as e:
            self._handle_redis_error(e, "clear_async")

            if self.enable_fallback:
                self._using_fallback = True
                self._get_fallback_store().clear()
                return

            raise

    def count(self) -> int:
        """Get total entry count.

        Returns:
            Number of deduplication entries.
        """
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
        """Async get total entry count.

        Returns:
            Number of deduplication entries.
        """
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
        result = {
            "healthy": False,
            "connected": self._connected,
            "using_fallback": self._using_fallback,
            "redis_url": self._mask_url(self.redis_url),
            "metrics": self._metrics.to_dict(),
        }

        if self._using_fallback and self.enable_fallback:
            result["healthy"] = True
            result["mode"] = "fallback"
            result["fallback_entries"] = self._get_fallback_store().count()
            return result

        try:
            client = self.client
            ping_ok = client.ping()

            if ping_ok:
                result["healthy"] = True
                result["mode"] = "redis"
                result["entries"] = self.count()

                # Get stream info
                try:
                    stream_info = client.xinfo_stream(self._stream_key)
                    result["stream"] = {
                        "length": stream_info.get("length", 0),
                        "first_entry": stream_info.get("first-entry"),
                        "last_entry": stream_info.get("last-entry"),
                    }
                except redis.ResponseError:
                    result["stream"] = {"length": 0}

                # Get Redis info
                info = client.info(section="server")
                result["redis_info"] = {
                    "version": info.get("redis_version"),
                    "uptime_seconds": info.get("uptime_in_seconds"),
                }

        except Exception as e:
            result["error"] = str(e)
            if self._last_error_time:
                result["last_error_time"] = datetime.fromtimestamp(
                    self._last_error_time
                ).isoformat()

        return result

    async def health_check_async(self) -> dict[str, Any]:
        """Async perform health check and return status.

        Returns:
            Dictionary with health status information.
        """
        result = {
            "healthy": False,
            "connected": self._connected,
            "using_fallback": self._using_fallback,
            "redis_url": self._mask_url(self.redis_url),
            "metrics": self._metrics.to_dict(),
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

                # Get stream info
                try:
                    stream_info = await client.xinfo_stream(self._stream_key)
                    result["stream"] = {
                        "length": stream_info.get("length", 0),
                        "first_entry": stream_info.get("first-entry"),
                        "last_entry": stream_info.get("last-entry"),
                    }
                except redis.ResponseError:
                    result["stream"] = {"length": 0}

                # Get Redis info
                info = await client.info(section="server")
                result["redis_info"] = {
                    "version": info.get("redis_version"),
                    "uptime_seconds": info.get("uptime_in_seconds"),
                }

        except Exception as e:
            result["error"] = str(e)
            if self._last_error_time:
                result["last_error_time"] = datetime.fromtimestamp(
                    self._last_error_time
                ).isoformat()

        return result

    def _mask_url(self, url: str) -> str:
        """Mask sensitive parts of Redis URL.

        Args:
            url: Redis URL to mask.

        Returns:
            Masked URL string.
        """
        import re

        # Mask password if present
        return re.sub(r"://[^:]+:[^@]+@", "://***:***@", url)

    def get_metrics(self) -> dict[str, Any]:
        """Get current metrics.

        Returns:
            Dictionary with metrics data.
        """
        return self._metrics.to_dict()

    def reset_metrics(self) -> None:
        """Reset all metrics to zero."""
        self._metrics = DeduplicationMetrics()

    async def read_stream(
        self,
        count: int = 100,
        block_ms: int = 0,
    ) -> list[dict[str, Any]]:
        """Read entries from the deduplication stream.

        Useful for audit logging or replaying events.

        Args:
            count: Maximum number of entries to read.
            block_ms: Block timeout in milliseconds (0 = no blocking).

        Returns:
            List of stream entries.
        """
        try:
            client = await self.get_async_client()

            # Ensure consumer group exists
            await self._ensure_consumer_group(client)

            # Read from stream using consumer group
            entries = await client.xreadgroup(
                self.consumer_group,
                self.consumer_name,
                {self._stream_key: ">"},
                count=count,
                block=block_ms,
            )

            result = []
            if entries:
                for stream_name, messages in entries:
                    for msg_id, fields in messages:
                        result.append(
                            {
                                "id": msg_id,
                                "stream": stream_name,
                                "fields": fields,
                            }
                        )

                        # Acknowledge the message
                        await client.xack(
                            self._stream_key, self.consumer_group, msg_id
                        )

            return result

        except Exception as e:
            self._handle_redis_error(e, "read_stream")
            return []

    async def get_pending_messages(self) -> dict[str, Any]:
        """Get information about pending messages in consumer group.

        Returns:
            Dictionary with pending message information.
        """
        try:
            client = await self.get_async_client()

            pending = await client.xpending(self._stream_key, self.consumer_group)

            return {
                "pending_count": pending.get("pending", 0),
                "min_id": pending.get("min"),
                "max_id": pending.get("max"),
                "consumers": pending.get("consumers", {}),
            }

        except Exception as e:
            self._handle_redis_error(e, "get_pending_messages")
            return {"pending_count": 0, "error": str(e)}

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

    def __enter__(self) -> "RedisStreamsDeduplicationStore":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit, closes connections."""
        self.close()

    async def __aenter__(self) -> "RedisStreamsDeduplicationStore":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit, closes connections."""
        await self.close_async()


# ============================================================================
# Factory Function
# ============================================================================


class DeduplicationStoreType:
    """Store type constants."""

    MEMORY = "memory"
    SQLITE = "sqlite"
    REDIS = "redis"
    REDIS_STREAMS = "redis_streams"


def create_deduplication_store(
    store_type: str | None = None,
    **kwargs: Any,
) -> BaseDeduplicationStore:
    """Factory function to create appropriate deduplication store.

    Selects the store type based on configuration or environment variables.

    Environment variables:
        TRUTHOUND_DEDUP_STORE_TYPE: Store type (memory, sqlite, redis, redis_streams)
        TRUTHOUND_DEDUP_SQLITE_PATH: SQLite database path
        TRUTHOUND_DEDUP_REDIS_URL: Redis connection URL (enables redis/redis_streams)

    Args:
        store_type: Explicit store type override. If None, auto-detects.
        **kwargs: Additional arguments passed to the store constructor.

    Returns:
        Configured BaseDeduplicationStore instance.

    Example:
        # Auto-detect based on environment
        store = create_deduplication_store()

        # Explicit type
        store = create_deduplication_store("redis_streams", default_ttl=7200)

        # SQLite with custom path
        store = create_deduplication_store("sqlite", db_path="/tmp/dedup.db")
    """
    import logging
    import os

    logger = logging.getLogger(__name__)

    # Determine store type
    if store_type is None:
        store_type = os.getenv("TRUTHOUND_DEDUP_STORE_TYPE")

    # Auto-detect if still None
    if store_type is None:
        redis_url = os.getenv("TRUTHOUND_DEDUP_REDIS_URL")
        if redis_url and REDIS_AVAILABLE:
            store_type = DeduplicationStoreType.REDIS_STREAMS
            logger.info(
                f"Auto-detected Redis Streams store from TRUTHOUND_DEDUP_REDIS_URL"
            )
        elif os.getenv("TRUTHOUND_DEDUP_SQLITE_PATH"):
            store_type = DeduplicationStoreType.SQLITE
            logger.info("Auto-detected SQLite store from TRUTHOUND_DEDUP_SQLITE_PATH")
        else:
            store_type = DeduplicationStoreType.MEMORY
            logger.info("Using default InMemory store")

    # Normalize store type
    store_type = store_type.lower().strip()

    # Create store based on type
    if store_type == DeduplicationStoreType.MEMORY:
        logger.info("Creating InMemory deduplication store")
        return InMemoryDeduplicationStore()

    elif store_type == DeduplicationStoreType.SQLITE:
        db_path = kwargs.pop("db_path", None) or os.getenv(
            "TRUTHOUND_DEDUP_SQLITE_PATH", "deduplication.db"
        )
        logger.info(f"Creating SQLite deduplication store at {db_path}")
        return SQLiteDeduplicationStore(db_path=db_path)

    elif store_type == DeduplicationStoreType.REDIS:
        if not REDIS_AVAILABLE:
            logger.warning(
                "Redis not available, falling back to InMemory store. "
                "Install with: pip install truthound-dashboard[redis]"
            )
            return InMemoryDeduplicationStore()

        logger.info("Creating Redis deduplication store (simple)")
        return RedisDeduplicationStore(**kwargs)

    elif store_type == DeduplicationStoreType.REDIS_STREAMS:
        if not REDIS_AVAILABLE:
            logger.warning(
                "Redis not available, falling back to InMemory store. "
                "Install with: pip install truthound-dashboard[redis]"
            )
            return InMemoryDeduplicationStore()

        logger.info("Creating Redis Streams deduplication store (production)")
        return RedisStreamsDeduplicationStore(**kwargs)

    else:
        logger.warning(
            f"Unknown store type '{store_type}', falling back to InMemory store"
        )
        return InMemoryDeduplicationStore()
