"""Storage backends for escalation state.

This module provides storage backends for persisting escalation
policies and incidents.

Storage Backends:
    - InMemoryEscalationStore: Simple in-memory storage
    - SQLiteEscalationStore: Persistent SQLite storage
    - RedisEscalationStore: Redis-based storage for distributed deployments
"""

from __future__ import annotations

import json
import logging
import os
import random
import sqlite3
import threading
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .models import EscalationIncident, EscalationPolicy, EscalationState

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


class BaseEscalationStore(ABC):
    """Abstract base class for escalation storage."""

    # Policy operations
    @abstractmethod
    def save_policy(self, policy: EscalationPolicy) -> str:
        """Save or update a policy."""
        ...

    @abstractmethod
    def get_policy(self, policy_id: str) -> EscalationPolicy | None:
        """Get policy by ID."""
        ...

    @abstractmethod
    def get_policy_by_name(self, name: str) -> EscalationPolicy | None:
        """Get policy by name."""
        ...

    @abstractmethod
    def list_policies(self, active_only: bool = True) -> list[EscalationPolicy]:
        """List all policies."""
        ...

    @abstractmethod
    def delete_policy(self, policy_id: str) -> bool:
        """Delete a policy."""
        ...

    # Incident operations
    @abstractmethod
    def save_incident(self, incident: EscalationIncident) -> str:
        """Save or update an incident."""
        ...

    @abstractmethod
    def get_incident(self, incident_id: str) -> EscalationIncident | None:
        """Get incident by ID."""
        ...

    @abstractmethod
    def get_incident_by_ref(self, incident_ref: str) -> EscalationIncident | None:
        """Get incident by external reference."""
        ...

    @abstractmethod
    def list_incidents(
        self,
        policy_id: str | None = None,
        states: list[EscalationState] | None = None,
    ) -> list[EscalationIncident]:
        """List incidents with optional filters."""
        ...

    @abstractmethod
    def get_pending_escalations(self) -> list[EscalationIncident]:
        """Get incidents due for escalation."""
        ...


class InMemoryEscalationStore(BaseEscalationStore):
    """In-memory escalation storage.

    Simple thread-safe storage suitable for development
    and testing.
    """

    def __init__(self) -> None:
        """Initialize in-memory store."""
        self._policies: dict[str, EscalationPolicy] = {}
        self._incidents: dict[str, EscalationIncident] = {}
        self._policy_counter = 0
        self._incident_counter = 0
        self._lock = threading.RLock()

    def _generate_policy_id(self) -> str:
        """Generate unique policy ID."""
        self._policy_counter += 1
        return f"policy-{self._policy_counter}"

    def _generate_incident_id(self) -> str:
        """Generate unique incident ID."""
        self._incident_counter += 1
        return f"incident-{self._incident_counter}"

    def save_policy(self, policy: EscalationPolicy) -> str:
        """Save or update a policy."""
        with self._lock:
            if not policy.id:
                policy.id = self._generate_policy_id()
            self._policies[policy.id] = policy
            return policy.id

    def get_policy(self, policy_id: str) -> EscalationPolicy | None:
        """Get policy by ID."""
        with self._lock:
            return self._policies.get(policy_id)

    def get_policy_by_name(self, name: str) -> EscalationPolicy | None:
        """Get policy by name."""
        with self._lock:
            for policy in self._policies.values():
                if policy.name == name:
                    return policy
            return None

    def list_policies(self, active_only: bool = True) -> list[EscalationPolicy]:
        """List all policies."""
        with self._lock:
            policies = list(self._policies.values())
            if active_only:
                policies = [p for p in policies if p.is_active]
            return policies

    def delete_policy(self, policy_id: str) -> bool:
        """Delete a policy."""
        with self._lock:
            if policy_id in self._policies:
                del self._policies[policy_id]
                return True
            return False

    def save_incident(self, incident: EscalationIncident) -> str:
        """Save or update an incident."""
        with self._lock:
            if not incident.id:
                incident.id = self._generate_incident_id()
            incident.updated_at = datetime.utcnow()
            self._incidents[incident.id] = incident
            return incident.id

    def get_incident(self, incident_id: str) -> EscalationIncident | None:
        """Get incident by ID."""
        with self._lock:
            return self._incidents.get(incident_id)

    def get_incident_by_ref(self, incident_ref: str) -> EscalationIncident | None:
        """Get incident by external reference."""
        with self._lock:
            for incident in self._incidents.values():
                if incident.incident_ref == incident_ref:
                    return incident
            return None

    def list_incidents(
        self,
        policy_id: str | None = None,
        states: list[EscalationState] | None = None,
    ) -> list[EscalationIncident]:
        """List incidents with optional filters."""
        with self._lock:
            incidents = list(self._incidents.values())

            if policy_id:
                incidents = [i for i in incidents if i.policy_id == policy_id]

            if states:
                incidents = [i for i in incidents if i.state in states]

            return incidents

    def get_pending_escalations(self) -> list[EscalationIncident]:
        """Get incidents due for escalation."""
        now = datetime.utcnow()
        active_states = [
            EscalationState.TRIGGERED,
            EscalationState.ESCALATED,
        ]

        with self._lock:
            return [
                i for i in self._incidents.values()
                if i.state in active_states
                and i.next_escalation_at
                and i.next_escalation_at <= now
            ]


class SQLiteEscalationStore(BaseEscalationStore):
    """SQLite-based persistent escalation storage."""

    def __init__(self, db_path: str | Path = "escalation.db") -> None:
        """Initialize SQLite store."""
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

        # Policies table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS escalation_policies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                levels TEXT NOT NULL,
                auto_resolve_on_success INTEGER NOT NULL DEFAULT 1,
                max_escalations INTEGER NOT NULL DEFAULT 3,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Incidents table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS escalation_incidents (
                id TEXT PRIMARY KEY,
                policy_id TEXT NOT NULL,
                incident_ref TEXT NOT NULL UNIQUE,
                state TEXT NOT NULL,
                current_level INTEGER NOT NULL DEFAULT 0,
                context TEXT,
                acknowledged_by TEXT,
                acknowledged_at TEXT,
                resolved_by TEXT,
                resolved_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                next_escalation_at TEXT,
                escalation_count INTEGER NOT NULL DEFAULT 0,
                events TEXT,
                FOREIGN KEY (policy_id) REFERENCES escalation_policies(id)
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_incident_state
            ON escalation_incidents(state)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_incident_next_escalation
            ON escalation_incidents(next_escalation_at)
        """)

        conn.commit()

    def save_policy(self, policy: EscalationPolicy) -> str:
        """Save or update a policy."""
        conn = self._get_connection()
        now = datetime.utcnow().isoformat()

        if not policy.id:
            import uuid
            policy.id = str(uuid.uuid4())

        levels_json = json.dumps([l.to_dict() for l in policy.levels])

        conn.execute(
            """
            INSERT OR REPLACE INTO escalation_policies
            (id, name, description, levels, auto_resolve_on_success,
             max_escalations, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                policy.id,
                policy.name,
                policy.description,
                levels_json,
                1 if policy.auto_resolve_on_success else 0,
                policy.max_escalations,
                1 if policy.is_active else 0,
                now,
                now,
            ),
        )
        conn.commit()
        return policy.id

    def get_policy(self, policy_id: str) -> EscalationPolicy | None:
        """Get policy by ID."""
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT * FROM escalation_policies WHERE id = ?",
            (policy_id,),
        )
        row = cursor.fetchone()
        return self._row_to_policy(row) if row else None

    def get_policy_by_name(self, name: str) -> EscalationPolicy | None:
        """Get policy by name."""
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT * FROM escalation_policies WHERE name = ?",
            (name,),
        )
        row = cursor.fetchone()
        return self._row_to_policy(row) if row else None

    def list_policies(self, active_only: bool = True) -> list[EscalationPolicy]:
        """List all policies."""
        conn = self._get_connection()
        if active_only:
            cursor = conn.execute(
                "SELECT * FROM escalation_policies WHERE is_active = 1"
            )
        else:
            cursor = conn.execute("SELECT * FROM escalation_policies")

        return [self._row_to_policy(row) for row in cursor.fetchall()]

    def delete_policy(self, policy_id: str) -> bool:
        """Delete a policy."""
        conn = self._get_connection()
        cursor = conn.execute(
            "DELETE FROM escalation_policies WHERE id = ?",
            (policy_id,),
        )
        conn.commit()
        return cursor.rowcount > 0

    def _row_to_policy(self, row: sqlite3.Row) -> EscalationPolicy:
        """Convert database row to policy."""
        from .models import EscalationLevel

        levels_data = json.loads(row["levels"])
        levels = [EscalationLevel.from_dict(l) for l in levels_data]

        return EscalationPolicy(
            id=row["id"],
            name=row["name"],
            description=row["description"] or "",
            levels=levels,
            auto_resolve_on_success=bool(row["auto_resolve_on_success"]),
            max_escalations=row["max_escalations"],
            is_active=bool(row["is_active"]),
        )

    def save_incident(self, incident: EscalationIncident) -> str:
        """Save or update an incident."""
        conn = self._get_connection()
        now = datetime.utcnow().isoformat()

        if not incident.id:
            import uuid
            incident.id = str(uuid.uuid4())

        incident.updated_at = datetime.utcnow()

        conn.execute(
            """
            INSERT OR REPLACE INTO escalation_incidents
            (id, policy_id, incident_ref, state, current_level, context,
             acknowledged_by, acknowledged_at, resolved_by, resolved_at,
             created_at, updated_at, next_escalation_at, escalation_count, events)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                incident.id,
                incident.policy_id,
                incident.incident_ref,
                incident.state.value,
                incident.current_level,
                json.dumps(incident.context),
                incident.acknowledged_by,
                incident.acknowledged_at.isoformat() if incident.acknowledged_at else None,
                incident.resolved_by,
                incident.resolved_at.isoformat() if incident.resolved_at else None,
                incident.created_at.isoformat(),
                incident.updated_at.isoformat(),
                incident.next_escalation_at.isoformat() if incident.next_escalation_at else None,
                incident.escalation_count,
                json.dumps([e.to_dict() for e in incident.events]),
            ),
        )
        conn.commit()
        return incident.id

    def get_incident(self, incident_id: str) -> EscalationIncident | None:
        """Get incident by ID."""
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT * FROM escalation_incidents WHERE id = ?",
            (incident_id,),
        )
        row = cursor.fetchone()
        return self._row_to_incident(row) if row else None

    def get_incident_by_ref(self, incident_ref: str) -> EscalationIncident | None:
        """Get incident by external reference."""
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT * FROM escalation_incidents WHERE incident_ref = ?",
            (incident_ref,),
        )
        row = cursor.fetchone()
        return self._row_to_incident(row) if row else None

    def list_incidents(
        self,
        policy_id: str | None = None,
        states: list[EscalationState] | None = None,
    ) -> list[EscalationIncident]:
        """List incidents with optional filters."""
        conn = self._get_connection()

        query = "SELECT * FROM escalation_incidents WHERE 1=1"
        params: list[Any] = []

        if policy_id:
            query += " AND policy_id = ?"
            params.append(policy_id)

        if states:
            placeholders = ",".join("?" * len(states))
            query += f" AND state IN ({placeholders})"
            params.extend(s.value for s in states)

        cursor = conn.execute(query, params)
        return [self._row_to_incident(row) for row in cursor.fetchall()]

    def get_pending_escalations(self) -> list[EscalationIncident]:
        """Get incidents due for escalation."""
        now = datetime.utcnow().isoformat()
        conn = self._get_connection()
        cursor = conn.execute(
            """
            SELECT * FROM escalation_incidents
            WHERE state IN (?, ?)
            AND next_escalation_at IS NOT NULL
            AND next_escalation_at <= ?
            """,
            (EscalationState.TRIGGERED.value, EscalationState.ESCALATED.value, now),
        )
        return [self._row_to_incident(row) for row in cursor.fetchall()]

    def _row_to_incident(self, row: sqlite3.Row) -> EscalationIncident:
        """Convert database row to incident."""
        from .models import EscalationEvent

        events_data = json.loads(row["events"]) if row["events"] else []
        events = [EscalationEvent.from_dict(e) for e in events_data]

        return EscalationIncident(
            id=row["id"],
            policy_id=row["policy_id"],
            incident_ref=row["incident_ref"],
            state=EscalationState(row["state"]),
            current_level=row["current_level"],
            context=json.loads(row["context"]) if row["context"] else {},
            acknowledged_by=row["acknowledged_by"],
            acknowledged_at=datetime.fromisoformat(row["acknowledged_at"]) if row["acknowledged_at"] else None,
            resolved_by=row["resolved_by"],
            resolved_at=datetime.fromisoformat(row["resolved_at"]) if row["resolved_at"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            next_escalation_at=datetime.fromisoformat(row["next_escalation_at"]) if row["next_escalation_at"] else None,
            escalation_count=row["escalation_count"],
            events=events,
        )

    def close(self) -> None:
        """Close database connection."""
        if hasattr(self._local, "connection"):
            self._local.connection.close()
            del self._local.connection


# ============================================================================
# Redis Escalation Store
# ============================================================================


@dataclass
class EscalationMetrics:
    """Metrics for escalation store operations.

    Attributes:
        policy_saves: Number of policy save operations.
        policy_gets: Number of policy get operations.
        policy_deletes: Number of policy delete operations.
        incident_saves: Number of incident save operations.
        incident_gets: Number of incident get operations.
        state_transitions: Number of state transitions.
        errors: Number of Redis errors encountered.
        fallbacks: Number of times fallback to InMemory was used.
        reconnections: Number of successful reconnections.
        pubsub_publishes: Number of Pub/Sub messages published.
        avg_latency_ms: Average operation latency in milliseconds.
    """

    policy_saves: int = 0
    policy_gets: int = 0
    policy_deletes: int = 0
    incident_saves: int = 0
    incident_gets: int = 0
    state_transitions: int = 0
    errors: int = 0
    fallbacks: int = 0
    reconnections: int = 0
    pubsub_publishes: int = 0
    total_operations: int = 0
    total_latency_ms: float = 0.0

    @property
    def avg_latency_ms(self) -> float:
        """Calculate average operation latency."""
        if self.total_operations == 0:
            return 0.0
        return self.total_latency_ms / self.total_operations

    def record_latency(self, latency_ms: float) -> None:
        """Record an operation's latency."""
        self.total_operations += 1
        self.total_latency_ms += latency_ms

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "policy_saves": self.policy_saves,
            "policy_gets": self.policy_gets,
            "policy_deletes": self.policy_deletes,
            "incident_saves": self.incident_saves,
            "incident_gets": self.incident_gets,
            "state_transitions": self.state_transitions,
            "errors": self.errors,
            "fallbacks": self.fallbacks,
            "reconnections": self.reconnections,
            "pubsub_publishes": self.pubsub_publishes,
            "total_operations": self.total_operations,
            "avg_latency_ms": round(self.avg_latency_ms, 3),
        }


class RedisEscalationStore(BaseEscalationStore):
    """Production-ready Redis-based escalation store for distributed deployments.

    Uses Redis for robust distributed escalation state management with:
        - Connection pool management with configurable pool size
        - Automatic reconnection with exponential backoff
        - Proper JSON serialization/deserialization of incident objects
        - Transaction support for atomic state updates (MULTI/EXEC and Lua scripts)
        - Pub/Sub for real-time incident updates
        - TTL management for completed/resolved incidents (auto-cleanup)
        - Index structures for efficient queries (by state, policy_id, created_at)
        - Graceful degradation (fallback to InMemory on Redis failure)
        - Health check endpoint support
        - Comprehensive metrics (operations, latency, errors)

    Configuration via environment variables:
        TRUTHOUND_ESCALATION_REDIS_URL: Redis connection URL (default: redis://localhost:6379/0)
        TRUTHOUND_ESCALATION_REDIS_PREFIX: Key prefix (default: truthound:escalation:)
        TRUTHOUND_ESCALATION_REDIS_POOL_SIZE: Connection pool size (default: 10)
        TRUTHOUND_ESCALATION_REDIS_SOCKET_TIMEOUT: Socket timeout (default: 5.0)
        TRUTHOUND_ESCALATION_REDIS_CONNECT_TIMEOUT: Connection timeout (default: 5.0)
        TRUTHOUND_ESCALATION_REDIS_MAX_RETRIES: Max retry attempts (default: 3)
        TRUTHOUND_ESCALATION_REDIS_RETRY_BASE_DELAY: Base delay for exponential backoff (default: 1.0)
        TRUTHOUND_ESCALATION_REDIS_RESOLVED_TTL: TTL in seconds for resolved incidents (default: 86400 = 24h)
        TRUTHOUND_ESCALATION_FALLBACK_ENABLED: Enable fallback to InMemory (default: true)
        TRUTHOUND_ESCALATION_PUBSUB_ENABLED: Enable Pub/Sub notifications (default: true)

    Example:
        # Basic usage
        store = RedisEscalationStore()

        # Custom configuration
        store = RedisEscalationStore(
            redis_url="redis://myredis:6379/1",
            max_connections=20,
            resolved_ttl=3600,  # 1 hour
            enable_fallback=True,
        )

        # With context manager
        async with RedisEscalationStore() as store:
            policy_id = await store.save_policy_async(policy)
            incident_id = await store.save_incident_async(incident)

    Note: Requires the 'redis' optional dependency.
          Install with: pip install truthound-dashboard[redis]
    """

    # Redis key patterns
    KEY_POLICY = "policy:{policy_id}"
    KEY_POLICY_INDEX = "policies:all"
    KEY_POLICY_BY_NAME = "policies:name:{name}"
    KEY_POLICY_ACTIVE = "policies:active"

    KEY_INCIDENT = "incident:{incident_id}"
    KEY_INCIDENT_INDEX = "incidents:all"
    KEY_INCIDENT_BY_REF = "incidents:ref:{incident_ref}"
    KEY_INCIDENT_BY_POLICY = "incidents:policy:{policy_id}"
    KEY_INCIDENT_BY_STATE = "incidents:state:{state}"
    KEY_INCIDENT_BY_CREATED = "incidents:created"  # Sorted set
    KEY_INCIDENT_PENDING = "incidents:pending_escalation"  # Sorted set by next_escalation_at

    # Pub/Sub channels
    CHANNEL_INCIDENT_UPDATE = "escalation:incidents:updates"
    CHANNEL_POLICY_UPDATE = "escalation:policies:updates"

    # Lua script for atomic incident state transition
    LUA_STATE_TRANSITION = """
    local incident_key = KEYS[1]
    local old_state_key = KEYS[2]
    local new_state_key = KEYS[3]
    local pending_key = KEYS[4]
    local incident_id = ARGV[1]
    local new_state = ARGV[2]
    local updated_data = ARGV[3]
    local next_escalation_score = ARGV[4]

    -- Get current incident
    local current = redis.call('GET', incident_key)
    if not current then
        return {err = 'incident_not_found'}
    end

    -- Update incident data
    redis.call('SET', incident_key, updated_data)

    -- Update state indices
    redis.call('SREM', old_state_key, incident_id)
    redis.call('SADD', new_state_key, incident_id)

    -- Update pending escalation sorted set
    if new_state == 'resolved' or new_state == 'acknowledged' then
        redis.call('ZREM', pending_key, incident_id)
    elseif next_escalation_score ~= '' then
        redis.call('ZADD', pending_key, next_escalation_score, incident_id)
    end

    return 'OK'
    """

    def __init__(
        self,
        redis_url: str | None = None,
        key_prefix: str | None = None,
        max_connections: int | None = None,
        socket_timeout: float | None = None,
        socket_connect_timeout: float | None = None,
        max_retries: int | None = None,
        retry_base_delay: float | None = None,
        resolved_ttl: int | None = None,
        enable_fallback: bool | None = None,
        enable_pubsub: bool | None = None,
        logger: Any | None = None,
    ) -> None:
        """Initialize Redis escalation store.

        All parameters can be configured via environment variables if not
        explicitly provided.

        Args:
            redis_url: Redis connection URL.
            key_prefix: Prefix for all Redis keys.
            max_connections: Maximum connections in the pool.
            socket_timeout: Socket timeout in seconds.
            socket_connect_timeout: Connection timeout in seconds.
            max_retries: Maximum retry attempts for reconnection.
            retry_base_delay: Base delay for exponential backoff.
            resolved_ttl: TTL in seconds for resolved/completed incidents.
            enable_fallback: Enable fallback to InMemory on Redis failure.
            enable_pubsub: Enable Pub/Sub notifications for state changes.
            logger: Custom logger instance.

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
            "TRUTHOUND_ESCALATION_REDIS_URL", "redis://localhost:6379/0"
        )
        self.key_prefix = key_prefix or os.getenv(
            "TRUTHOUND_ESCALATION_REDIS_PREFIX", "truthound:escalation:"
        )
        self.max_connections = max_connections or int(
            os.getenv("TRUTHOUND_ESCALATION_REDIS_POOL_SIZE", "10")
        )
        self.socket_timeout = socket_timeout or float(
            os.getenv("TRUTHOUND_ESCALATION_REDIS_SOCKET_TIMEOUT", "5.0")
        )
        self.socket_connect_timeout = socket_connect_timeout or float(
            os.getenv("TRUTHOUND_ESCALATION_REDIS_CONNECT_TIMEOUT", "5.0")
        )
        self.max_retries = max_retries or int(
            os.getenv("TRUTHOUND_ESCALATION_REDIS_MAX_RETRIES", "3")
        )
        self.retry_base_delay = retry_base_delay or float(
            os.getenv("TRUTHOUND_ESCALATION_REDIS_RETRY_BASE_DELAY", "1.0")
        )
        self.resolved_ttl = resolved_ttl or int(
            os.getenv("TRUTHOUND_ESCALATION_REDIS_RESOLVED_TTL", "86400")
        )

        fallback_env = os.getenv("TRUTHOUND_ESCALATION_FALLBACK_ENABLED", "true")
        self.enable_fallback = (
            enable_fallback
            if enable_fallback is not None
            else fallback_env.lower() == "true"
        )

        pubsub_env = os.getenv("TRUTHOUND_ESCALATION_PUBSUB_ENABLED", "true")
        self.enable_pubsub = (
            enable_pubsub
            if enable_pubsub is not None
            else pubsub_env.lower() == "true"
        )

        # Logger setup
        self._logger = logger or logging.getLogger(__name__)

        # Connection pool for sync client
        self._pool: "redis.ConnectionPool | None" = None
        self._client: "redis.Redis | None" = None

        # Connection pool for async client
        self._async_pool: "redis.asyncio.ConnectionPool | None" = None
        self._async_client: "redis.asyncio.Redis | None" = None

        # Locks for thread-safe initialization
        self._lock = threading.Lock()
        self._async_lock: Any = None  # Created lazily for asyncio

        # Fallback store for graceful degradation
        self._fallback_store: InMemoryEscalationStore | None = None
        self._using_fallback = False

        # Connection state tracking
        self._connected = False
        self._retry_count = 0
        self._last_error: Exception | None = None
        self._last_error_time: float | None = None

        # Metrics
        self._metrics = EscalationMetrics()

        # Lua script SHA (registered on first use)
        self._state_transition_sha: str | None = None

    def _get_key(self, pattern: str, **kwargs: str) -> str:
        """Get full Redis key from pattern.

        Args:
            pattern: Key pattern with placeholders.
            **kwargs: Values to substitute in pattern.

        Returns:
            Full Redis key with prefix.
        """
        key = pattern.format(**kwargs) if kwargs else pattern
        return f"{self.key_prefix}{key}"

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

    def _get_fallback_store(self) -> InMemoryEscalationStore:
        """Get or create fallback in-memory store.

        Returns:
            InMemoryEscalationStore instance.
        """
        if self._fallback_store is None:
            self._fallback_store = InMemoryEscalationStore()
        return self._fallback_store

    def _calculate_backoff_delay(self) -> float:
        """Calculate exponential backoff delay.

        Returns:
            Delay in seconds.
        """
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
            f"Attempting async Redis reconnection in {delay:.2f}s "
            f"(attempt {self._retry_count + 1}/{self.max_retries})"
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

    def _register_lua_scripts(self, client: "redis.Redis") -> None:
        """Register Lua scripts with Redis.

        Args:
            client: Redis client instance.
        """
        if self._state_transition_sha is None:
            self._state_transition_sha = client.script_load(self.LUA_STATE_TRANSITION)

    async def _register_lua_scripts_async(
        self, client: "redis.asyncio.Redis"
    ) -> None:
        """Register Lua scripts with Redis asynchronously.

        Args:
            client: Async Redis client instance.
        """
        if self._state_transition_sha is None:
            self._state_transition_sha = await client.script_load(
                self.LUA_STATE_TRANSITION
            )

    def _serialize_policy(self, policy: EscalationPolicy) -> str:
        """Serialize policy to JSON string.

        Args:
            policy: Policy to serialize.

        Returns:
            JSON string.
        """
        return json.dumps(policy.to_dict())

    def _deserialize_policy(self, data: str) -> EscalationPolicy:
        """Deserialize policy from JSON string.

        Args:
            data: JSON string.

        Returns:
            EscalationPolicy instance.
        """
        return EscalationPolicy.from_dict(json.loads(data))

    def _serialize_incident(self, incident: EscalationIncident) -> str:
        """Serialize incident to JSON string.

        Args:
            incident: Incident to serialize.

        Returns:
            JSON string.
        """
        return json.dumps(incident.to_dict())

    def _deserialize_incident(self, data: str) -> EscalationIncident:
        """Deserialize incident from JSON string.

        Args:
            data: JSON string.

        Returns:
            EscalationIncident instance.
        """
        return EscalationIncident.from_dict(json.loads(data))

    def _publish_incident_update(
        self,
        client: "redis.Redis",
        incident: EscalationIncident,
        event_type: str,
    ) -> None:
        """Publish incident update via Pub/Sub.

        Args:
            client: Redis client.
            incident: Updated incident.
            event_type: Type of event (created, updated, state_changed, etc.).
        """
        if not self.enable_pubsub:
            return

        try:
            message = json.dumps({
                "event_type": event_type,
                "incident_id": incident.id,
                "incident_ref": incident.incident_ref,
                "policy_id": incident.policy_id,
                "state": incident.state.value,
                "current_level": incident.current_level,
                "timestamp": datetime.utcnow().isoformat(),
            })
            channel = self._get_key(self.CHANNEL_INCIDENT_UPDATE)
            client.publish(channel, message)
            self._metrics.pubsub_publishes += 1
        except Exception as e:
            self._logger.warning(f"Failed to publish incident update: {e}")

    async def _publish_incident_update_async(
        self,
        client: "redis.asyncio.Redis",
        incident: EscalationIncident,
        event_type: str,
    ) -> None:
        """Publish incident update via Pub/Sub asynchronously.

        Args:
            client: Async Redis client.
            incident: Updated incident.
            event_type: Type of event.
        """
        if not self.enable_pubsub:
            return

        try:
            message = json.dumps({
                "event_type": event_type,
                "incident_id": incident.id,
                "incident_ref": incident.incident_ref,
                "policy_id": incident.policy_id,
                "state": incident.state.value,
                "current_level": incident.current_level,
                "timestamp": datetime.utcnow().isoformat(),
            })
            channel = self._get_key(self.CHANNEL_INCIDENT_UPDATE)
            await client.publish(channel, message)
            self._metrics.pubsub_publishes += 1
        except Exception as e:
            self._logger.warning(f"Failed to publish incident update: {e}")

    # =========================================================================
    # Policy Operations
    # =========================================================================

    def save_policy(self, policy: EscalationPolicy) -> str:
        """Save or update a policy.

        Args:
            policy: Policy to save.

        Returns:
            Policy ID.
        """
        start_time = time.time()

        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().save_policy(policy)

        try:
            client = self.client

            # Generate ID if not present
            if not policy.id:
                policy.id = str(uuid.uuid4())

            # Use pipeline for atomicity
            pipe = client.pipeline()

            # Store policy
            policy_key = self._get_key(self.KEY_POLICY, policy_id=policy.id)
            pipe.set(policy_key, self._serialize_policy(policy))

            # Update indices
            index_key = self._get_key(self.KEY_POLICY_INDEX)
            pipe.sadd(index_key, policy.id)

            name_key = self._get_key(self.KEY_POLICY_BY_NAME, name=policy.name)
            pipe.set(name_key, policy.id)

            active_key = self._get_key(self.KEY_POLICY_ACTIVE)
            if policy.is_active:
                pipe.sadd(active_key, policy.id)
            else:
                pipe.srem(active_key, policy.id)

            pipe.execute()

            self._metrics.policy_saves += 1
            latency_ms = (time.time() - start_time) * 1000
            self._metrics.record_latency(latency_ms)

            return policy.id

        except Exception as e:
            self._handle_redis_error(e, "save_policy")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                self._logger.warning("Falling back to InMemory store")
                return self._get_fallback_store().save_policy(policy)

            raise

    async def save_policy_async(self, policy: EscalationPolicy) -> str:
        """Save or update a policy asynchronously.

        Args:
            policy: Policy to save.

        Returns:
            Policy ID.
        """
        start_time = time.time()

        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().save_policy(policy)

        try:
            client = await self.get_async_client()

            # Generate ID if not present
            if not policy.id:
                policy.id = str(uuid.uuid4())

            # Use pipeline for atomicity
            pipe = client.pipeline()

            # Store policy
            policy_key = self._get_key(self.KEY_POLICY, policy_id=policy.id)
            pipe.set(policy_key, self._serialize_policy(policy))

            # Update indices
            index_key = self._get_key(self.KEY_POLICY_INDEX)
            pipe.sadd(index_key, policy.id)

            name_key = self._get_key(self.KEY_POLICY_BY_NAME, name=policy.name)
            pipe.set(name_key, policy.id)

            active_key = self._get_key(self.KEY_POLICY_ACTIVE)
            if policy.is_active:
                pipe.sadd(active_key, policy.id)
            else:
                pipe.srem(active_key, policy.id)

            await pipe.execute()

            self._metrics.policy_saves += 1
            latency_ms = (time.time() - start_time) * 1000
            self._metrics.record_latency(latency_ms)

            return policy.id

        except Exception as e:
            self._handle_redis_error(e, "save_policy_async")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                return self._get_fallback_store().save_policy(policy)

            raise

    def get_policy(self, policy_id: str) -> EscalationPolicy | None:
        """Get policy by ID.

        Args:
            policy_id: Policy ID.

        Returns:
            Policy if found, None otherwise.
        """
        start_time = time.time()

        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().get_policy(policy_id)

        try:
            client = self.client
            policy_key = self._get_key(self.KEY_POLICY, policy_id=policy_id)
            data = client.get(policy_key)

            self._metrics.policy_gets += 1
            latency_ms = (time.time() - start_time) * 1000
            self._metrics.record_latency(latency_ms)

            if not data:
                return None

            return self._deserialize_policy(data)

        except Exception as e:
            self._handle_redis_error(e, "get_policy")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                return self._get_fallback_store().get_policy(policy_id)

            raise

    async def get_policy_async(self, policy_id: str) -> EscalationPolicy | None:
        """Get policy by ID asynchronously.

        Args:
            policy_id: Policy ID.

        Returns:
            Policy if found, None otherwise.
        """
        start_time = time.time()

        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().get_policy(policy_id)

        try:
            client = await self.get_async_client()
            policy_key = self._get_key(self.KEY_POLICY, policy_id=policy_id)
            data = await client.get(policy_key)

            self._metrics.policy_gets += 1
            latency_ms = (time.time() - start_time) * 1000
            self._metrics.record_latency(latency_ms)

            if not data:
                return None

            return self._deserialize_policy(data)

        except Exception as e:
            self._handle_redis_error(e, "get_policy_async")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                return self._get_fallback_store().get_policy(policy_id)

            raise

    def get_policy_by_name(self, name: str) -> EscalationPolicy | None:
        """Get policy by name.

        Args:
            name: Policy name.

        Returns:
            Policy if found, None otherwise.
        """
        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().get_policy_by_name(name)

        try:
            client = self.client
            name_key = self._get_key(self.KEY_POLICY_BY_NAME, name=name)
            policy_id = client.get(name_key)

            if not policy_id:
                return None

            return self.get_policy(policy_id)

        except Exception as e:
            self._handle_redis_error(e, "get_policy_by_name")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                return self._get_fallback_store().get_policy_by_name(name)

            raise

    async def get_policy_by_name_async(self, name: str) -> EscalationPolicy | None:
        """Get policy by name asynchronously.

        Args:
            name: Policy name.

        Returns:
            Policy if found, None otherwise.
        """
        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().get_policy_by_name(name)

        try:
            client = await self.get_async_client()
            name_key = self._get_key(self.KEY_POLICY_BY_NAME, name=name)
            policy_id = await client.get(name_key)

            if not policy_id:
                return None

            return await self.get_policy_async(policy_id)

        except Exception as e:
            self._handle_redis_error(e, "get_policy_by_name_async")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                return self._get_fallback_store().get_policy_by_name(name)

            raise

    def list_policies(self, active_only: bool = True) -> list[EscalationPolicy]:
        """List all policies.

        Args:
            active_only: If True, only return active policies.

        Returns:
            List of policies.
        """
        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().list_policies(active_only)

        try:
            client = self.client

            if active_only:
                index_key = self._get_key(self.KEY_POLICY_ACTIVE)
            else:
                index_key = self._get_key(self.KEY_POLICY_INDEX)

            policy_ids = client.smembers(index_key)
            policies = []

            for policy_id in policy_ids:
                policy = self.get_policy(policy_id)
                if policy:
                    policies.append(policy)

            return policies

        except Exception as e:
            self._handle_redis_error(e, "list_policies")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                return self._get_fallback_store().list_policies(active_only)

            raise

    async def list_policies_async(
        self, active_only: bool = True
    ) -> list[EscalationPolicy]:
        """List all policies asynchronously.

        Args:
            active_only: If True, only return active policies.

        Returns:
            List of policies.
        """
        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().list_policies(active_only)

        try:
            client = await self.get_async_client()

            if active_only:
                index_key = self._get_key(self.KEY_POLICY_ACTIVE)
            else:
                index_key = self._get_key(self.KEY_POLICY_INDEX)

            policy_ids = await client.smembers(index_key)
            policies = []

            for policy_id in policy_ids:
                policy = await self.get_policy_async(policy_id)
                if policy:
                    policies.append(policy)

            return policies

        except Exception as e:
            self._handle_redis_error(e, "list_policies_async")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                return self._get_fallback_store().list_policies(active_only)

            raise

    def delete_policy(self, policy_id: str) -> bool:
        """Delete a policy.

        Args:
            policy_id: Policy ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().delete_policy(policy_id)

        try:
            client = self.client

            # Get policy first to get name for index cleanup
            policy = self.get_policy(policy_id)
            if not policy:
                return False

            pipe = client.pipeline()

            # Delete policy
            policy_key = self._get_key(self.KEY_POLICY, policy_id=policy_id)
            pipe.delete(policy_key)

            # Remove from indices
            index_key = self._get_key(self.KEY_POLICY_INDEX)
            pipe.srem(index_key, policy_id)

            name_key = self._get_key(self.KEY_POLICY_BY_NAME, name=policy.name)
            pipe.delete(name_key)

            active_key = self._get_key(self.KEY_POLICY_ACTIVE)
            pipe.srem(active_key, policy_id)

            pipe.execute()

            self._metrics.policy_deletes += 1
            return True

        except Exception as e:
            self._handle_redis_error(e, "delete_policy")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                return self._get_fallback_store().delete_policy(policy_id)

            raise

    async def delete_policy_async(self, policy_id: str) -> bool:
        """Delete a policy asynchronously.

        Args:
            policy_id: Policy ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().delete_policy(policy_id)

        try:
            client = await self.get_async_client()

            # Get policy first to get name for index cleanup
            policy = await self.get_policy_async(policy_id)
            if not policy:
                return False

            pipe = client.pipeline()

            # Delete policy
            policy_key = self._get_key(self.KEY_POLICY, policy_id=policy_id)
            pipe.delete(policy_key)

            # Remove from indices
            index_key = self._get_key(self.KEY_POLICY_INDEX)
            pipe.srem(index_key, policy_id)

            name_key = self._get_key(self.KEY_POLICY_BY_NAME, name=policy.name)
            pipe.delete(name_key)

            active_key = self._get_key(self.KEY_POLICY_ACTIVE)
            pipe.srem(active_key, policy_id)

            await pipe.execute()

            self._metrics.policy_deletes += 1
            return True

        except Exception as e:
            self._handle_redis_error(e, "delete_policy_async")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                return self._get_fallback_store().delete_policy(policy_id)

            raise

    # =========================================================================
    # Incident Operations
    # =========================================================================

    def save_incident(self, incident: EscalationIncident) -> str:
        """Save or update an incident.

        Args:
            incident: Incident to save.

        Returns:
            Incident ID.
        """
        start_time = time.time()

        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().save_incident(incident)

        try:
            client = self.client
            is_new = not incident.id

            # Generate ID if not present
            if not incident.id:
                incident.id = str(uuid.uuid4())

            incident.updated_at = datetime.utcnow()

            # Use pipeline for atomicity
            pipe = client.pipeline()

            # Store incident
            incident_key = self._get_key(self.KEY_INCIDENT, incident_id=incident.id)
            pipe.set(incident_key, self._serialize_incident(incident))

            # Set TTL for resolved incidents
            if incident.state == EscalationState.RESOLVED and self.resolved_ttl > 0:
                pipe.expire(incident_key, self.resolved_ttl)

            # Update indices
            index_key = self._get_key(self.KEY_INCIDENT_INDEX)
            pipe.sadd(index_key, incident.id)

            ref_key = self._get_key(
                self.KEY_INCIDENT_BY_REF, incident_ref=incident.incident_ref
            )
            pipe.set(ref_key, incident.id)

            policy_key = self._get_key(
                self.KEY_INCIDENT_BY_POLICY, policy_id=incident.policy_id
            )
            pipe.sadd(policy_key, incident.id)

            # Update state index (remove from other states first)
            for state in EscalationState:
                state_key = self._get_key(self.KEY_INCIDENT_BY_STATE, state=state.value)
                if state == incident.state:
                    pipe.sadd(state_key, incident.id)
                else:
                    pipe.srem(state_key, incident.id)

            # Update created_at sorted set
            created_key = self._get_key(self.KEY_INCIDENT_BY_CREATED)
            created_score = incident.created_at.timestamp()
            pipe.zadd(created_key, {incident.id: created_score})

            # Update pending escalation sorted set
            pending_key = self._get_key(self.KEY_INCIDENT_PENDING)
            if incident.state in [EscalationState.TRIGGERED, EscalationState.ESCALATED]:
                if incident.next_escalation_at:
                    score = incident.next_escalation_at.timestamp()
                    pipe.zadd(pending_key, {incident.id: score})
                else:
                    pipe.zrem(pending_key, incident.id)
            else:
                pipe.zrem(pending_key, incident.id)

            pipe.execute()

            # Publish update
            event_type = "created" if is_new else "updated"
            self._publish_incident_update(client, incident, event_type)

            self._metrics.incident_saves += 1
            latency_ms = (time.time() - start_time) * 1000
            self._metrics.record_latency(latency_ms)

            return incident.id

        except Exception as e:
            self._handle_redis_error(e, "save_incident")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                self._logger.warning("Falling back to InMemory store")
                return self._get_fallback_store().save_incident(incident)

            raise

    async def save_incident_async(self, incident: EscalationIncident) -> str:
        """Save or update an incident asynchronously.

        Args:
            incident: Incident to save.

        Returns:
            Incident ID.
        """
        start_time = time.time()

        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().save_incident(incident)

        try:
            client = await self.get_async_client()
            is_new = not incident.id

            # Generate ID if not present
            if not incident.id:
                incident.id = str(uuid.uuid4())

            incident.updated_at = datetime.utcnow()

            # Use pipeline for atomicity
            pipe = client.pipeline()

            # Store incident
            incident_key = self._get_key(self.KEY_INCIDENT, incident_id=incident.id)
            pipe.set(incident_key, self._serialize_incident(incident))

            # Set TTL for resolved incidents
            if incident.state == EscalationState.RESOLVED and self.resolved_ttl > 0:
                pipe.expire(incident_key, self.resolved_ttl)

            # Update indices
            index_key = self._get_key(self.KEY_INCIDENT_INDEX)
            pipe.sadd(index_key, incident.id)

            ref_key = self._get_key(
                self.KEY_INCIDENT_BY_REF, incident_ref=incident.incident_ref
            )
            pipe.set(ref_key, incident.id)

            policy_key = self._get_key(
                self.KEY_INCIDENT_BY_POLICY, policy_id=incident.policy_id
            )
            pipe.sadd(policy_key, incident.id)

            # Update state index
            for state in EscalationState:
                state_key = self._get_key(self.KEY_INCIDENT_BY_STATE, state=state.value)
                if state == incident.state:
                    pipe.sadd(state_key, incident.id)
                else:
                    pipe.srem(state_key, incident.id)

            # Update created_at sorted set
            created_key = self._get_key(self.KEY_INCIDENT_BY_CREATED)
            created_score = incident.created_at.timestamp()
            pipe.zadd(created_key, {incident.id: created_score})

            # Update pending escalation sorted set
            pending_key = self._get_key(self.KEY_INCIDENT_PENDING)
            if incident.state in [EscalationState.TRIGGERED, EscalationState.ESCALATED]:
                if incident.next_escalation_at:
                    score = incident.next_escalation_at.timestamp()
                    pipe.zadd(pending_key, {incident.id: score})
                else:
                    pipe.zrem(pending_key, incident.id)
            else:
                pipe.zrem(pending_key, incident.id)

            await pipe.execute()

            # Publish update
            event_type = "created" if is_new else "updated"
            await self._publish_incident_update_async(client, incident, event_type)

            self._metrics.incident_saves += 1
            latency_ms = (time.time() - start_time) * 1000
            self._metrics.record_latency(latency_ms)

            return incident.id

        except Exception as e:
            self._handle_redis_error(e, "save_incident_async")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                return self._get_fallback_store().save_incident(incident)

            raise

    def get_incident(self, incident_id: str) -> EscalationIncident | None:
        """Get incident by ID.

        Args:
            incident_id: Incident ID.

        Returns:
            Incident if found, None otherwise.
        """
        start_time = time.time()

        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().get_incident(incident_id)

        try:
            client = self.client
            incident_key = self._get_key(self.KEY_INCIDENT, incident_id=incident_id)
            data = client.get(incident_key)

            self._metrics.incident_gets += 1
            latency_ms = (time.time() - start_time) * 1000
            self._metrics.record_latency(latency_ms)

            if not data:
                return None

            return self._deserialize_incident(data)

        except Exception as e:
            self._handle_redis_error(e, "get_incident")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                return self._get_fallback_store().get_incident(incident_id)

            raise

    async def get_incident_async(self, incident_id: str) -> EscalationIncident | None:
        """Get incident by ID asynchronously.

        Args:
            incident_id: Incident ID.

        Returns:
            Incident if found, None otherwise.
        """
        start_time = time.time()

        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().get_incident(incident_id)

        try:
            client = await self.get_async_client()
            incident_key = self._get_key(self.KEY_INCIDENT, incident_id=incident_id)
            data = await client.get(incident_key)

            self._metrics.incident_gets += 1
            latency_ms = (time.time() - start_time) * 1000
            self._metrics.record_latency(latency_ms)

            if not data:
                return None

            return self._deserialize_incident(data)

        except Exception as e:
            self._handle_redis_error(e, "get_incident_async")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                return self._get_fallback_store().get_incident(incident_id)

            raise

    def get_incident_by_ref(self, incident_ref: str) -> EscalationIncident | None:
        """Get incident by external reference.

        Args:
            incident_ref: External reference.

        Returns:
            Incident if found, None otherwise.
        """
        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().get_incident_by_ref(incident_ref)

        try:
            client = self.client
            ref_key = self._get_key(self.KEY_INCIDENT_BY_REF, incident_ref=incident_ref)
            incident_id = client.get(ref_key)

            if not incident_id:
                return None

            return self.get_incident(incident_id)

        except Exception as e:
            self._handle_redis_error(e, "get_incident_by_ref")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                return self._get_fallback_store().get_incident_by_ref(incident_ref)

            raise

    async def get_incident_by_ref_async(
        self, incident_ref: str
    ) -> EscalationIncident | None:
        """Get incident by external reference asynchronously.

        Args:
            incident_ref: External reference.

        Returns:
            Incident if found, None otherwise.
        """
        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().get_incident_by_ref(incident_ref)

        try:
            client = await self.get_async_client()
            ref_key = self._get_key(self.KEY_INCIDENT_BY_REF, incident_ref=incident_ref)
            incident_id = await client.get(ref_key)

            if not incident_id:
                return None

            return await self.get_incident_async(incident_id)

        except Exception as e:
            self._handle_redis_error(e, "get_incident_by_ref_async")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                return self._get_fallback_store().get_incident_by_ref(incident_ref)

            raise

    def list_incidents(
        self,
        policy_id: str | None = None,
        states: list[EscalationState] | None = None,
    ) -> list[EscalationIncident]:
        """List incidents with optional filters.

        Args:
            policy_id: Filter by policy ID.
            states: Filter by states.

        Returns:
            List of incidents.
        """
        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().list_incidents(policy_id, states)

        try:
            client = self.client
            incident_ids: set[str] = set()

            # Get IDs based on filters
            if policy_id:
                policy_key = self._get_key(
                    self.KEY_INCIDENT_BY_POLICY, policy_id=policy_id
                )
                incident_ids = client.smembers(policy_key)
            elif states:
                # Get incidents from state indices and intersect
                for i, state in enumerate(states):
                    state_key = self._get_key(
                        self.KEY_INCIDENT_BY_STATE, state=state.value
                    )
                    state_ids = client.smembers(state_key)
                    if i == 0:
                        incident_ids = state_ids
                    else:
                        incident_ids = incident_ids.union(state_ids)
            else:
                index_key = self._get_key(self.KEY_INCIDENT_INDEX)
                incident_ids = client.smembers(index_key)

            # Fetch incidents
            incidents = []
            for incident_id in incident_ids:
                incident = self.get_incident(incident_id)
                if incident:
                    # Apply additional filters if needed
                    if states and incident.state not in states:
                        continue
                    if policy_id and incident.policy_id != policy_id:
                        continue
                    incidents.append(incident)

            return incidents

        except Exception as e:
            self._handle_redis_error(e, "list_incidents")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                return self._get_fallback_store().list_incidents(policy_id, states)

            raise

    async def list_incidents_async(
        self,
        policy_id: str | None = None,
        states: list[EscalationState] | None = None,
    ) -> list[EscalationIncident]:
        """List incidents with optional filters asynchronously.

        Args:
            policy_id: Filter by policy ID.
            states: Filter by states.

        Returns:
            List of incidents.
        """
        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().list_incidents(policy_id, states)

        try:
            client = await self.get_async_client()
            incident_ids: set[str] = set()

            # Get IDs based on filters
            if policy_id:
                policy_key = self._get_key(
                    self.KEY_INCIDENT_BY_POLICY, policy_id=policy_id
                )
                incident_ids = await client.smembers(policy_key)
            elif states:
                # Get incidents from state indices and union
                for i, state in enumerate(states):
                    state_key = self._get_key(
                        self.KEY_INCIDENT_BY_STATE, state=state.value
                    )
                    state_ids = await client.smembers(state_key)
                    if i == 0:
                        incident_ids = state_ids
                    else:
                        incident_ids = incident_ids.union(state_ids)
            else:
                index_key = self._get_key(self.KEY_INCIDENT_INDEX)
                incident_ids = await client.smembers(index_key)

            # Fetch incidents
            incidents = []
            for incident_id in incident_ids:
                incident = await self.get_incident_async(incident_id)
                if incident:
                    # Apply additional filters if needed
                    if states and incident.state not in states:
                        continue
                    if policy_id and incident.policy_id != policy_id:
                        continue
                    incidents.append(incident)

            return incidents

        except Exception as e:
            self._handle_redis_error(e, "list_incidents_async")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                return self._get_fallback_store().list_incidents(policy_id, states)

            raise

    def get_pending_escalations(self) -> list[EscalationIncident]:
        """Get incidents due for escalation.

        Returns:
            List of incidents due for escalation.
        """
        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().get_pending_escalations()

        try:
            client = self.client
            now = datetime.utcnow().timestamp()

            # Get incident IDs from pending sorted set where score <= now
            pending_key = self._get_key(self.KEY_INCIDENT_PENDING)
            incident_ids = client.zrangebyscore(pending_key, "-inf", now)

            incidents = []
            for incident_id in incident_ids:
                incident = self.get_incident(incident_id)
                if incident and incident.state in [
                    EscalationState.TRIGGERED,
                    EscalationState.ESCALATED,
                ]:
                    incidents.append(incident)

            return incidents

        except Exception as e:
            self._handle_redis_error(e, "get_pending_escalations")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                return self._get_fallback_store().get_pending_escalations()

            raise

    async def get_pending_escalations_async(self) -> list[EscalationIncident]:
        """Get incidents due for escalation asynchronously.

        Returns:
            List of incidents due for escalation.
        """
        if self._using_fallback and self.enable_fallback:
            return self._get_fallback_store().get_pending_escalations()

        try:
            client = await self.get_async_client()
            now = datetime.utcnow().timestamp()

            # Get incident IDs from pending sorted set where score <= now
            pending_key = self._get_key(self.KEY_INCIDENT_PENDING)
            incident_ids = await client.zrangebyscore(pending_key, "-inf", now)

            incidents = []
            for incident_id in incident_ids:
                incident = await self.get_incident_async(incident_id)
                if incident and incident.state in [
                    EscalationState.TRIGGERED,
                    EscalationState.ESCALATED,
                ]:
                    incidents.append(incident)

            return incidents

        except Exception as e:
            self._handle_redis_error(e, "get_pending_escalations_async")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                return self._get_fallback_store().get_pending_escalations()

            raise

    # =========================================================================
    # Atomic State Transition
    # =========================================================================

    def transition_state(
        self,
        incident_id: str,
        new_state: EscalationState,
        **updates: Any,
    ) -> EscalationIncident | None:
        """Atomically transition incident state using Lua script.

        This ensures that state transitions are atomic and consistent,
        even under concurrent access.

        Args:
            incident_id: Incident ID.
            new_state: New state to transition to.
            **updates: Additional fields to update on the incident.

        Returns:
            Updated incident if successful, None if not found.
        """
        start_time = time.time()

        if self._using_fallback and self.enable_fallback:
            incident = self._get_fallback_store().get_incident(incident_id)
            if not incident:
                return None
            old_state = incident.state
            incident.state = new_state
            for key, value in updates.items():
                if hasattr(incident, key):
                    setattr(incident, key, value)
            self._get_fallback_store().save_incident(incident)
            return incident

        try:
            client = self.client
            self._register_lua_scripts(client)

            # Get current incident
            incident = self.get_incident(incident_id)
            if not incident:
                return None

            old_state = incident.state

            # Update incident
            incident.state = new_state
            incident.updated_at = datetime.utcnow()
            for key, value in updates.items():
                if hasattr(incident, key):
                    setattr(incident, key, value)

            # Prepare keys and args for Lua script
            incident_key = self._get_key(self.KEY_INCIDENT, incident_id=incident_id)
            old_state_key = self._get_key(
                self.KEY_INCIDENT_BY_STATE, state=old_state.value
            )
            new_state_key = self._get_key(
                self.KEY_INCIDENT_BY_STATE, state=new_state.value
            )
            pending_key = self._get_key(self.KEY_INCIDENT_PENDING)

            next_escalation_score = ""
            if incident.next_escalation_at and new_state in [
                EscalationState.TRIGGERED,
                EscalationState.ESCALATED,
            ]:
                next_escalation_score = str(incident.next_escalation_at.timestamp())

            # Execute Lua script
            result = client.evalsha(
                self._state_transition_sha,
                4,  # Number of keys
                incident_key,
                old_state_key,
                new_state_key,
                pending_key,
                incident_id,
                new_state.value,
                self._serialize_incident(incident),
                next_escalation_score,
            )

            if result == "OK":
                # Set TTL for resolved incidents
                if new_state == EscalationState.RESOLVED and self.resolved_ttl > 0:
                    client.expire(incident_key, self.resolved_ttl)

                # Publish state change
                self._publish_incident_update(client, incident, "state_changed")

                self._metrics.state_transitions += 1
                latency_ms = (time.time() - start_time) * 1000
                self._metrics.record_latency(latency_ms)

                return incident

            return None

        except Exception as e:
            self._handle_redis_error(e, "transition_state")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                # Fallback to non-atomic operation
                incident = self._get_fallback_store().get_incident(incident_id)
                if incident:
                    incident.state = new_state
                    for key, value in updates.items():
                        if hasattr(incident, key):
                            setattr(incident, key, value)
                    self._get_fallback_store().save_incident(incident)
                return incident

            raise

    async def transition_state_async(
        self,
        incident_id: str,
        new_state: EscalationState,
        **updates: Any,
    ) -> EscalationIncident | None:
        """Atomically transition incident state using Lua script asynchronously.

        Args:
            incident_id: Incident ID.
            new_state: New state to transition to.
            **updates: Additional fields to update on the incident.

        Returns:
            Updated incident if successful, None if not found.
        """
        start_time = time.time()

        if self._using_fallback and self.enable_fallback:
            incident = self._get_fallback_store().get_incident(incident_id)
            if not incident:
                return None
            incident.state = new_state
            for key, value in updates.items():
                if hasattr(incident, key):
                    setattr(incident, key, value)
            self._get_fallback_store().save_incident(incident)
            return incident

        try:
            client = await self.get_async_client()
            await self._register_lua_scripts_async(client)

            # Get current incident
            incident = await self.get_incident_async(incident_id)
            if not incident:
                return None

            old_state = incident.state

            # Update incident
            incident.state = new_state
            incident.updated_at = datetime.utcnow()
            for key, value in updates.items():
                if hasattr(incident, key):
                    setattr(incident, key, value)

            # Prepare keys and args for Lua script
            incident_key = self._get_key(self.KEY_INCIDENT, incident_id=incident_id)
            old_state_key = self._get_key(
                self.KEY_INCIDENT_BY_STATE, state=old_state.value
            )
            new_state_key = self._get_key(
                self.KEY_INCIDENT_BY_STATE, state=new_state.value
            )
            pending_key = self._get_key(self.KEY_INCIDENT_PENDING)

            next_escalation_score = ""
            if incident.next_escalation_at and new_state in [
                EscalationState.TRIGGERED,
                EscalationState.ESCALATED,
            ]:
                next_escalation_score = str(incident.next_escalation_at.timestamp())

            # Execute Lua script
            result = await client.evalsha(
                self._state_transition_sha,
                4,
                incident_key,
                old_state_key,
                new_state_key,
                pending_key,
                incident_id,
                new_state.value,
                self._serialize_incident(incident),
                next_escalation_score,
            )

            if result == "OK":
                # Set TTL for resolved incidents
                if new_state == EscalationState.RESOLVED and self.resolved_ttl > 0:
                    await client.expire(incident_key, self.resolved_ttl)

                # Publish state change
                await self._publish_incident_update_async(
                    client, incident, "state_changed"
                )

                self._metrics.state_transitions += 1
                latency_ms = (time.time() - start_time) * 1000
                self._metrics.record_latency(latency_ms)

                return incident

            return None

        except Exception as e:
            self._handle_redis_error(e, "transition_state_async")

            if self.enable_fallback:
                self._using_fallback = True
                self._metrics.fallbacks += 1
                incident = self._get_fallback_store().get_incident(incident_id)
                if incident:
                    incident.state = new_state
                    for key, value in updates.items():
                        if hasattr(incident, key):
                            setattr(incident, key, value)
                    self._get_fallback_store().save_incident(incident)
                return incident

            raise

    # =========================================================================
    # Pub/Sub Subscription
    # =========================================================================

    async def subscribe_to_updates(
        self,
    ) -> "redis.asyncio.client.PubSub":
        """Subscribe to incident update channel.

        Returns a Pub/Sub instance that can be used to listen for updates.

        Returns:
            Async Pub/Sub instance subscribed to the incident updates channel.

        Example:
            pubsub = await store.subscribe_to_updates()
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    print(f"Incident {data['incident_id']} changed to {data['state']}")
        """
        client = await self.get_async_client()
        pubsub = client.pubsub()
        channel = self._get_key(self.CHANNEL_INCIDENT_UPDATE)
        await pubsub.subscribe(channel)
        return pubsub

    # =========================================================================
    # Cleanup Operations
    # =========================================================================

    def cleanup_resolved_incidents(self, max_age_seconds: int | None = None) -> int:
        """Clean up old resolved incidents.

        Args:
            max_age_seconds: Maximum age in seconds. Uses resolved_ttl if not provided.

        Returns:
            Number of incidents cleaned up.
        """
        if self._using_fallback and self.enable_fallback:
            # InMemory store doesn't have cleanup
            return 0

        try:
            client = self.client
            max_age = max_age_seconds or self.resolved_ttl
            cutoff = datetime.utcnow() - timedelta(seconds=max_age)
            cutoff_score = cutoff.timestamp()

            # Get resolved incidents created before cutoff
            resolved_key = self._get_key(
                self.KEY_INCIDENT_BY_STATE, state=EscalationState.RESOLVED.value
            )
            resolved_ids = client.smembers(resolved_key)

            cleaned = 0
            for incident_id in resolved_ids:
                incident = self.get_incident(incident_id)
                if incident and incident.resolved_at:
                    if incident.resolved_at.timestamp() < cutoff_score:
                        self._delete_incident(client, incident)
                        cleaned += 1

            return cleaned

        except Exception as e:
            self._handle_redis_error(e, "cleanup_resolved_incidents")
            return 0

    async def cleanup_resolved_incidents_async(
        self, max_age_seconds: int | None = None
    ) -> int:
        """Clean up old resolved incidents asynchronously.

        Args:
            max_age_seconds: Maximum age in seconds.

        Returns:
            Number of incidents cleaned up.
        """
        if self._using_fallback and self.enable_fallback:
            return 0

        try:
            client = await self.get_async_client()
            max_age = max_age_seconds or self.resolved_ttl
            cutoff = datetime.utcnow() - timedelta(seconds=max_age)
            cutoff_score = cutoff.timestamp()

            # Get resolved incidents
            resolved_key = self._get_key(
                self.KEY_INCIDENT_BY_STATE, state=EscalationState.RESOLVED.value
            )
            resolved_ids = await client.smembers(resolved_key)

            cleaned = 0
            for incident_id in resolved_ids:
                incident = await self.get_incident_async(incident_id)
                if incident and incident.resolved_at:
                    if incident.resolved_at.timestamp() < cutoff_score:
                        await self._delete_incident_async(client, incident)
                        cleaned += 1

            return cleaned

        except Exception as e:
            self._handle_redis_error(e, "cleanup_resolved_incidents_async")
            return 0

    def _delete_incident(
        self, client: "redis.Redis", incident: EscalationIncident
    ) -> None:
        """Delete incident and all its indices.

        Args:
            client: Redis client.
            incident: Incident to delete.
        """
        pipe = client.pipeline()

        # Delete incident
        incident_key = self._get_key(self.KEY_INCIDENT, incident_id=incident.id)
        pipe.delete(incident_key)

        # Remove from indices
        index_key = self._get_key(self.KEY_INCIDENT_INDEX)
        pipe.srem(index_key, incident.id)

        ref_key = self._get_key(
            self.KEY_INCIDENT_BY_REF, incident_ref=incident.incident_ref
        )
        pipe.delete(ref_key)

        policy_key = self._get_key(
            self.KEY_INCIDENT_BY_POLICY, policy_id=incident.policy_id
        )
        pipe.srem(policy_key, incident.id)

        for state in EscalationState:
            state_key = self._get_key(self.KEY_INCIDENT_BY_STATE, state=state.value)
            pipe.srem(state_key, incident.id)

        created_key = self._get_key(self.KEY_INCIDENT_BY_CREATED)
        pipe.zrem(created_key, incident.id)

        pending_key = self._get_key(self.KEY_INCIDENT_PENDING)
        pipe.zrem(pending_key, incident.id)

        pipe.execute()

    async def _delete_incident_async(
        self, client: "redis.asyncio.Redis", incident: EscalationIncident
    ) -> None:
        """Delete incident and all its indices asynchronously.

        Args:
            client: Async Redis client.
            incident: Incident to delete.
        """
        pipe = client.pipeline()

        # Delete incident
        incident_key = self._get_key(self.KEY_INCIDENT, incident_id=incident.id)
        pipe.delete(incident_key)

        # Remove from indices
        index_key = self._get_key(self.KEY_INCIDENT_INDEX)
        pipe.srem(index_key, incident.id)

        ref_key = self._get_key(
            self.KEY_INCIDENT_BY_REF, incident_ref=incident.incident_ref
        )
        pipe.delete(ref_key)

        policy_key = self._get_key(
            self.KEY_INCIDENT_BY_POLICY, policy_id=incident.policy_id
        )
        pipe.srem(policy_key, incident.id)

        for state in EscalationState:
            state_key = self._get_key(self.KEY_INCIDENT_BY_STATE, state=state.value)
            pipe.srem(state_key, incident.id)

        created_key = self._get_key(self.KEY_INCIDENT_BY_CREATED)
        pipe.zrem(created_key, incident.id)

        pending_key = self._get_key(self.KEY_INCIDENT_PENDING)
        pipe.zrem(pending_key, incident.id)

        await pipe.execute()

    # =========================================================================
    # Health Check & Metrics
    # =========================================================================

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
            result["fallback_policies"] = len(
                self._get_fallback_store().list_policies(active_only=False)
            )
            result["fallback_incidents"] = len(
                self._get_fallback_store().list_incidents()
            )
            return result

        try:
            client = self.client
            ping_ok = client.ping()

            if ping_ok:
                result["healthy"] = True
                result["mode"] = "redis"

                # Get counts
                index_key = self._get_key(self.KEY_POLICY_INDEX)
                result["policies"] = client.scard(index_key)

                incident_index_key = self._get_key(self.KEY_INCIDENT_INDEX)
                result["incidents"] = client.scard(incident_index_key)

                pending_key = self._get_key(self.KEY_INCIDENT_PENDING)
                result["pending_escalations"] = client.zcard(pending_key)

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
        """Perform health check asynchronously.

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
            result["fallback_policies"] = len(
                self._get_fallback_store().list_policies(active_only=False)
            )
            result["fallback_incidents"] = len(
                self._get_fallback_store().list_incidents()
            )
            return result

        try:
            client = await self.get_async_client()
            ping_ok = await client.ping()

            if ping_ok:
                result["healthy"] = True
                result["mode"] = "redis"

                # Get counts
                index_key = self._get_key(self.KEY_POLICY_INDEX)
                result["policies"] = await client.scard(index_key)

                incident_index_key = self._get_key(self.KEY_INCIDENT_INDEX)
                result["incidents"] = await client.scard(incident_index_key)

                pending_key = self._get_key(self.KEY_INCIDENT_PENDING)
                result["pending_escalations"] = await client.zcard(pending_key)

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
        self._metrics = EscalationMetrics()

    # =========================================================================
    # Connection Management
    # =========================================================================

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
        """Close all connections and pools asynchronously."""
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

    def __enter__(self) -> "RedisEscalationStore":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit, closes connections."""
        self.close()

    async def __aenter__(self) -> "RedisEscalationStore":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit, closes connections."""
        await self.close_async()


# ============================================================================
# Factory Function
# ============================================================================


class EscalationStoreType:
    """Store type constants."""

    MEMORY = "memory"
    SQLITE = "sqlite"
    REDIS = "redis"


def create_escalation_store(
    store_type: str | None = None,
    **kwargs: Any,
) -> BaseEscalationStore:
    """Factory function to create appropriate escalation store.

    Selects the store type based on configuration or environment variables.

    Environment variables:
        TRUTHOUND_ESCALATION_STORE_TYPE: Store type (memory, sqlite, redis)
        TRUTHOUND_ESCALATION_SQLITE_PATH: SQLite database path
        TRUTHOUND_ESCALATION_REDIS_URL: Redis connection URL (enables redis)

    Args:
        store_type: Explicit store type override. If None, auto-detects.
        **kwargs: Additional arguments passed to the store constructor.

    Returns:
        Configured BaseEscalationStore instance.

    Example:
        # Auto-detect based on environment
        store = create_escalation_store()

        # Explicit type
        store = create_escalation_store("redis", resolved_ttl=7200)

        # SQLite with custom path
        store = create_escalation_store("sqlite", db_path="/tmp/escalation.db")
    """
    logger = logging.getLogger(__name__)

    # Determine store type
    if store_type is None:
        store_type = os.getenv("TRUTHOUND_ESCALATION_STORE_TYPE")

    # Auto-detect if still None
    if store_type is None:
        redis_url = os.getenv("TRUTHOUND_ESCALATION_REDIS_URL")
        if redis_url and REDIS_AVAILABLE:
            store_type = EscalationStoreType.REDIS
            logger.info(
                "Auto-detected Redis store from TRUTHOUND_ESCALATION_REDIS_URL"
            )
        elif os.getenv("TRUTHOUND_ESCALATION_SQLITE_PATH"):
            store_type = EscalationStoreType.SQLITE
            logger.info(
                "Auto-detected SQLite store from TRUTHOUND_ESCALATION_SQLITE_PATH"
            )
        else:
            store_type = EscalationStoreType.MEMORY
            logger.info("Using default InMemory store")

    # Normalize store type
    store_type = store_type.lower().strip()

    # Create store based on type
    if store_type == EscalationStoreType.MEMORY:
        logger.info("Creating InMemory escalation store")
        return InMemoryEscalationStore()

    elif store_type == EscalationStoreType.SQLITE:
        db_path = kwargs.pop("db_path", None) or os.getenv(
            "TRUTHOUND_ESCALATION_SQLITE_PATH", "escalation.db"
        )
        logger.info(f"Creating SQLite escalation store at {db_path}")
        return SQLiteEscalationStore(db_path=db_path)

    elif store_type == EscalationStoreType.REDIS:
        if not REDIS_AVAILABLE:
            logger.warning(
                "Redis not available, falling back to InMemory store. "
                "Install with: pip install truthound-dashboard[redis]"
            )
            return InMemoryEscalationStore()

        logger.info("Creating Redis escalation store")
        return RedisEscalationStore(**kwargs)

    else:
        logger.warning(
            f"Unknown store type '{store_type}', falling back to InMemory store"
        )
        return InMemoryEscalationStore()
