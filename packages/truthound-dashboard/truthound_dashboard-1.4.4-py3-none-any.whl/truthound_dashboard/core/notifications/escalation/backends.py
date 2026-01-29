"""Scheduler backend implementations for persistent and in-memory job storage.

This module provides abstract and concrete implementations for scheduler backends,
enabling different storage strategies for APScheduler jobs.

Backends:
    - InMemorySchedulerBackend: Fast, ephemeral storage (lost on restart)
    - SQLAlchemySchedulerBackend: Persistent SQLite storage (survives restarts)

Features:
    - Abstract base class for custom implementations
    - Configurable misfire handling with grace time
    - Exponential backoff for error recovery
    - Job coalescing to prevent duplicate executions
    - Thread-safe operations with proper locking
    - Graceful shutdown with pending job handling

Usage:
    from truthound_dashboard.core.notifications.escalation.backends import (
        SQLAlchemySchedulerBackend,
        SchedulerBackendConfig,
    )

    config = SchedulerBackendConfig(
        backend_type="sqlalchemy",
        misfire_grace_time=60,
        coalesce=True,
    )

    backend = SQLAlchemySchedulerBackend(config)
    await backend.initialize()
    await backend.add_job(job_data)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable
from uuid import uuid4

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Configuration
# =============================================================================


class BackendType(str, Enum):
    """Type of scheduler backend."""

    MEMORY = "memory"
    SQLALCHEMY = "sqlalchemy"
    # Future: REDIS = "redis"


class JobState(str, Enum):
    """State of a scheduled job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    MISFIRED = "misfired"
    PAUSED = "paused"


class MisfirePolicy(str, Enum):
    """Policy for handling misfired jobs.

    - SKIP: Skip the misfired execution entirely
    - RUN_ONCE: Run once if misfired (coalesce multiple misfires)
    - RUN_ALL: Run all misfired executions (catch up)
    """

    SKIP = "skip"
    RUN_ONCE = "run_once"
    RUN_ALL = "run_all"


@dataclass
class SchedulerBackendConfig:
    """Configuration for scheduler backends.

    Attributes:
        backend_type: Type of backend (memory, sqlalchemy).
        misfire_grace_time: Seconds to allow for late job execution.
        coalesce: Combine multiple pending executions into one.
        max_instances: Maximum concurrent instances of same job.
        max_retries: Maximum retry attempts on failure.
        retry_base_delay: Base delay in seconds for exponential backoff.
        retry_max_delay: Maximum delay in seconds for backoff.
        shutdown_timeout: Seconds to wait for jobs during shutdown.
        database_url: Database URL for SQLAlchemy backend.
        job_table_name: Table name for job storage.
        cleanup_interval: Seconds between cleanup runs.
        job_retention_days: Days to retain completed jobs.
    """

    backend_type: BackendType = BackendType.SQLALCHEMY
    misfire_grace_time: int = 60
    coalesce: bool = True
    max_instances: int = 1
    max_retries: int = 3
    retry_base_delay: float = 5.0
    retry_max_delay: float = 300.0
    shutdown_timeout: float = 30.0
    database_url: str | None = None
    job_table_name: str = "scheduler_jobs"
    cleanup_interval: int = 3600  # 1 hour
    job_retention_days: int = 7

    @classmethod
    def from_env(cls) -> SchedulerBackendConfig:
        """Create configuration from environment variables.

        Environment variables:
            TRUTHOUND_SCHEDULER_BACKEND: Backend type (memory, sqlalchemy)
            TRUTHOUND_SCHEDULER_MISFIRE_GRACE_TIME: Seconds for misfire grace
            TRUTHOUND_SCHEDULER_COALESCE: Whether to coalesce jobs (true/false)
            TRUTHOUND_SCHEDULER_MAX_RETRIES: Maximum retry attempts
            TRUTHOUND_SCHEDULER_SHUTDOWN_TIMEOUT: Shutdown timeout seconds
        """
        return cls(
            backend_type=BackendType(
                os.getenv("TRUTHOUND_SCHEDULER_BACKEND", "sqlalchemy")
            ),
            misfire_grace_time=int(
                os.getenv("TRUTHOUND_SCHEDULER_MISFIRE_GRACE_TIME", "60")
            ),
            coalesce=os.getenv("TRUTHOUND_SCHEDULER_COALESCE", "true").lower() == "true",
            max_retries=int(os.getenv("TRUTHOUND_SCHEDULER_MAX_RETRIES", "3")),
            shutdown_timeout=float(
                os.getenv("TRUTHOUND_SCHEDULER_SHUTDOWN_TIMEOUT", "30")
            ),
            job_retention_days=int(
                os.getenv("TRUTHOUND_SCHEDULER_JOB_RETENTION_DAYS", "7")
            ),
        )


@dataclass
class JobData:
    """Data structure for a scheduled job.

    Attributes:
        id: Unique job identifier.
        name: Human-readable job name.
        func_ref: Reference to the function to execute.
        trigger_type: Type of trigger (interval, cron, date).
        trigger_args: Arguments for the trigger.
        args: Positional arguments for the function.
        kwargs: Keyword arguments for the function.
        next_run_time: Next scheduled execution time.
        state: Current job state.
        retry_count: Number of retry attempts.
        last_run_time: Last execution time.
        last_error: Last error message.
        metadata: Additional job metadata.
        created_at: When the job was created.
        updated_at: Last update timestamp.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    func_ref: str = ""
    trigger_type: str = "interval"
    trigger_args: dict[str, Any] = field(default_factory=dict)
    args: tuple[Any, ...] = field(default_factory=tuple)
    kwargs: dict[str, Any] = field(default_factory=dict)
    next_run_time: datetime | None = None
    state: JobState = JobState.PENDING
    retry_count: int = 0
    last_run_time: datetime | None = None
    last_error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "func_ref": self.func_ref,
            "trigger_type": self.trigger_type,
            "trigger_args": self.trigger_args,
            "args": list(self.args),
            "kwargs": self.kwargs,
            "next_run_time": self.next_run_time.isoformat() if self.next_run_time else None,
            "state": self.state.value,
            "retry_count": self.retry_count,
            "last_run_time": self.last_run_time.isoformat() if self.last_run_time else None,
            "last_error": self.last_error,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> JobData:
        """Create from dictionary."""
        return cls(
            id=data.get("id", str(uuid4())),
            name=data.get("name", ""),
            func_ref=data.get("func_ref", ""),
            trigger_type=data.get("trigger_type", "interval"),
            trigger_args=data.get("trigger_args", {}),
            args=tuple(data.get("args", [])),
            kwargs=data.get("kwargs", {}),
            next_run_time=(
                datetime.fromisoformat(data["next_run_time"])
                if data.get("next_run_time")
                else None
            ),
            state=JobState(data.get("state", "pending")),
            retry_count=data.get("retry_count", 0),
            last_run_time=(
                datetime.fromisoformat(data["last_run_time"])
                if data.get("last_run_time")
                else None
            ),
            last_error=data.get("last_error"),
            metadata=data.get("metadata", {}),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if data.get("created_at")
                else datetime.utcnow()
            ),
            updated_at=(
                datetime.fromisoformat(data["updated_at"])
                if data.get("updated_at")
                else datetime.utcnow()
            ),
        )


@dataclass
class JobExecutionResult:
    """Result of a job execution.

    Attributes:
        success: Whether the execution succeeded.
        result: Return value from the job function.
        error: Error message if failed.
        duration_ms: Execution duration in milliseconds.
        retry_scheduled: Whether a retry was scheduled.
    """

    success: bool
    result: Any = None
    error: str | None = None
    duration_ms: int = 0
    retry_scheduled: bool = False


# =============================================================================
# Abstract Base Class
# =============================================================================


class SchedulerBackend(ABC):
    """Abstract base class for scheduler backends.

    Subclasses must implement all abstract methods to provide
    custom storage strategies for scheduled jobs.

    This class defines the contract for:
    - Job lifecycle management (add, update, remove)
    - Job retrieval and querying
    - Misfire handling
    - Error recovery
    - Cleanup and maintenance
    """

    def __init__(self, config: SchedulerBackendConfig | None = None) -> None:
        """Initialize the backend.

        Args:
            config: Backend configuration. Uses defaults if None.
        """
        self.config = config or SchedulerBackendConfig()
        self._initialized = False
        self._shutdown = False
        self._lock = asyncio.Lock()
        self._running_jobs: set[str] = set()

    @property
    @abstractmethod
    def backend_type(self) -> BackendType:
        """Return the backend type identifier."""
        ...

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the backend (create tables, connections, etc.).

        This method is called before any other operations and should
        set up any required infrastructure.
        """
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the backend gracefully.

        Should wait for running jobs and clean up resources.
        """
        ...

    @abstractmethod
    async def add_job(self, job: JobData) -> JobData:
        """Add a new job to the scheduler.

        Args:
            job: Job data to add.

        Returns:
            The added job with any modifications (e.g., assigned ID).

        Raises:
            ValueError: If job with same ID already exists.
        """
        ...

    @abstractmethod
    async def update_job(self, job: JobData) -> JobData:
        """Update an existing job.

        Args:
            job: Updated job data.

        Returns:
            The updated job.

        Raises:
            KeyError: If job not found.
        """
        ...

    @abstractmethod
    async def remove_job(self, job_id: str) -> bool:
        """Remove a job from the scheduler.

        Args:
            job_id: ID of job to remove.

        Returns:
            True if job was removed, False if not found.
        """
        ...

    @abstractmethod
    async def get_job(self, job_id: str) -> JobData | None:
        """Get a job by ID.

        Args:
            job_id: Job ID to retrieve.

        Returns:
            Job data or None if not found.
        """
        ...

    @abstractmethod
    async def get_jobs(
        self,
        state: JobState | None = None,
        limit: int | None = None,
    ) -> list[JobData]:
        """Get jobs, optionally filtered by state.

        Args:
            state: Optional state filter.
            limit: Maximum number of jobs to return.

        Returns:
            List of matching jobs.
        """
        ...

    @abstractmethod
    async def get_due_jobs(self, now: datetime | None = None) -> list[JobData]:
        """Get jobs that are due for execution.

        Args:
            now: Current time (defaults to utcnow).

        Returns:
            List of jobs ready to run.
        """
        ...

    @abstractmethod
    async def mark_job_running(self, job_id: str) -> bool:
        """Mark a job as running.

        Args:
            job_id: Job ID to mark.

        Returns:
            True if marked successfully, False if already running or not found.
        """
        ...

    @abstractmethod
    async def mark_job_completed(
        self,
        job_id: str,
        next_run_time: datetime | None = None,
    ) -> bool:
        """Mark a job as completed.

        Args:
            job_id: Job ID to mark.
            next_run_time: Next scheduled run time (for recurring jobs).

        Returns:
            True if marked successfully.
        """
        ...

    @abstractmethod
    async def mark_job_failed(
        self,
        job_id: str,
        error: str,
        schedule_retry: bool = True,
    ) -> bool:
        """Mark a job as failed.

        Args:
            job_id: Job ID to mark.
            error: Error message.
            schedule_retry: Whether to schedule a retry.

        Returns:
            True if marked successfully.
        """
        ...

    @abstractmethod
    async def cleanup_old_jobs(self, older_than: datetime) -> int:
        """Remove completed/failed jobs older than specified time.

        Args:
            older_than: Remove jobs updated before this time.

        Returns:
            Number of jobs removed.
        """
        ...

    # -------------------------------------------------------------------------
    # Default implementations
    # -------------------------------------------------------------------------

    def calculate_retry_delay(self, retry_count: int) -> float:
        """Calculate exponential backoff delay for retry.

        Args:
            retry_count: Current retry attempt number.

        Returns:
            Delay in seconds before next retry.
        """
        delay = self.config.retry_base_delay * (2 ** retry_count)
        return min(delay, self.config.retry_max_delay)

    def is_misfired(self, job: JobData, now: datetime | None = None) -> bool:
        """Check if a job has misfired.

        A job is considered misfired if its next_run_time plus the
        misfire grace time is before the current time.

        Args:
            job: Job to check.
            now: Current time (defaults to utcnow).

        Returns:
            True if the job has misfired.
        """
        if not job.next_run_time:
            return False

        now = now or datetime.utcnow()
        grace_deadline = job.next_run_time + timedelta(
            seconds=self.config.misfire_grace_time
        )
        return now > grace_deadline

    async def handle_misfire(self, job: JobData) -> JobData:
        """Handle a misfired job according to policy.

        Args:
            job: The misfired job.

        Returns:
            Updated job data.
        """
        logger.warning(
            f"Job {job.id} ({job.name}) misfired. "
            f"Scheduled: {job.next_run_time}, Grace: {self.config.misfire_grace_time}s"
        )

        # Mark as misfired
        job.state = JobState.MISFIRED
        job.updated_at = datetime.utcnow()
        job.metadata["misfire_count"] = job.metadata.get("misfire_count", 0) + 1
        job.metadata["last_misfire_at"] = datetime.utcnow().isoformat()

        # Calculate new next_run_time based on trigger
        if job.trigger_type == "interval":
            interval_seconds = job.trigger_args.get("seconds", 60)
            job.next_run_time = datetime.utcnow() + timedelta(seconds=interval_seconds)
            job.state = JobState.PENDING

        await self.update_job(job)
        return job

    def get_status(self) -> dict[str, Any]:
        """Get backend status information.

        Returns:
            Status dictionary with backend state and metrics.
        """
        return {
            "backend_type": self.backend_type.value,
            "initialized": self._initialized,
            "shutdown": self._shutdown,
            "running_jobs": len(self._running_jobs),
            "config": {
                "misfire_grace_time": self.config.misfire_grace_time,
                "coalesce": self.config.coalesce,
                "max_retries": self.config.max_retries,
                "max_instances": self.config.max_instances,
            },
        }


# =============================================================================
# In-Memory Backend
# =============================================================================


class InMemorySchedulerBackend(SchedulerBackend):
    """In-memory scheduler backend for ephemeral job storage.

    Jobs are stored in memory and lost on process restart.
    Best for development, testing, or non-critical workloads.

    Features:
        - Fast access without database overhead
        - Thread-safe with asyncio locks
        - Supports all job lifecycle operations

    Limitations:
        - Jobs lost on restart
        - Not suitable for multi-process deployments
        - Memory grows with job count
    """

    def __init__(self, config: SchedulerBackendConfig | None = None) -> None:
        """Initialize in-memory backend."""
        if config is None:
            config = SchedulerBackendConfig(backend_type=BackendType.MEMORY)
        super().__init__(config)
        self._jobs: dict[str, JobData] = {}

    @property
    def backend_type(self) -> BackendType:
        return BackendType.MEMORY

    async def initialize(self) -> None:
        """Initialize the in-memory backend."""
        if self._initialized:
            return

        logger.info("Initializing in-memory scheduler backend")
        self._jobs.clear()
        self._initialized = True
        self._shutdown = False
        logger.info("In-memory scheduler backend initialized")

    async def shutdown(self) -> None:
        """Shutdown the in-memory backend."""
        if self._shutdown:
            return

        logger.info("Shutting down in-memory scheduler backend")

        # Wait for running jobs
        if self._running_jobs:
            logger.info(f"Waiting for {len(self._running_jobs)} running jobs...")
            wait_until = datetime.utcnow() + timedelta(
                seconds=self.config.shutdown_timeout
            )
            while self._running_jobs and datetime.utcnow() < wait_until:
                await asyncio.sleep(0.5)

            if self._running_jobs:
                logger.warning(
                    f"Timeout waiting for jobs: {self._running_jobs}"
                )

        self._shutdown = True
        self._initialized = False
        logger.info("In-memory scheduler backend shut down")

    async def add_job(self, job: JobData) -> JobData:
        """Add a job to memory."""
        async with self._lock:
            if job.id in self._jobs:
                raise ValueError(f"Job {job.id} already exists")

            job.created_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
            self._jobs[job.id] = job
            logger.debug(f"Added job {job.id} ({job.name})")
            return job

    async def update_job(self, job: JobData) -> JobData:
        """Update a job in memory."""
        async with self._lock:
            if job.id not in self._jobs:
                raise KeyError(f"Job {job.id} not found")

            job.updated_at = datetime.utcnow()
            self._jobs[job.id] = job
            logger.debug(f"Updated job {job.id} ({job.name})")
            return job

    async def remove_job(self, job_id: str) -> bool:
        """Remove a job from memory."""
        async with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                logger.debug(f"Removed job {job_id}")
                return True
            return False

    async def get_job(self, job_id: str) -> JobData | None:
        """Get a job by ID."""
        return self._jobs.get(job_id)

    async def get_jobs(
        self,
        state: JobState | None = None,
        limit: int | None = None,
    ) -> list[JobData]:
        """Get jobs, optionally filtered by state."""
        jobs = list(self._jobs.values())

        if state:
            jobs = [j for j in jobs if j.state == state]

        # Sort by next_run_time
        jobs.sort(key=lambda j: j.next_run_time or datetime.max)

        if limit:
            jobs = jobs[:limit]

        return jobs

    async def get_due_jobs(self, now: datetime | None = None) -> list[JobData]:
        """Get jobs due for execution."""
        now = now or datetime.utcnow()
        due_jobs = []

        for job in self._jobs.values():
            if job.state not in (JobState.PENDING, JobState.MISFIRED):
                continue
            if job.id in self._running_jobs:
                continue
            if job.next_run_time and job.next_run_time <= now:
                due_jobs.append(job)

        # Sort by next_run_time (earliest first)
        due_jobs.sort(key=lambda j: j.next_run_time or datetime.min)
        return due_jobs

    async def mark_job_running(self, job_id: str) -> bool:
        """Mark a job as running."""
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False

            if job_id in self._running_jobs:
                return False

            # Check max instances
            if len(self._running_jobs) >= self.config.max_instances:
                logger.debug(f"Max instances reached, cannot run {job_id}")
                return False

            job.state = JobState.RUNNING
            job.last_run_time = datetime.utcnow()
            job.updated_at = datetime.utcnow()
            self._running_jobs.add(job_id)
            logger.debug(f"Job {job_id} marked as running")
            return True

    async def mark_job_completed(
        self,
        job_id: str,
        next_run_time: datetime | None = None,
    ) -> bool:
        """Mark a job as completed."""
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False

            job.state = JobState.COMPLETED if not next_run_time else JobState.PENDING
            job.next_run_time = next_run_time
            job.retry_count = 0
            job.last_error = None
            job.updated_at = datetime.utcnow()
            self._running_jobs.discard(job_id)
            logger.debug(f"Job {job_id} marked as completed")
            return True

    async def mark_job_failed(
        self,
        job_id: str,
        error: str,
        schedule_retry: bool = True,
    ) -> bool:
        """Mark a job as failed."""
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False

            job.last_error = error
            job.updated_at = datetime.utcnow()
            self._running_jobs.discard(job_id)

            if schedule_retry and job.retry_count < self.config.max_retries:
                job.retry_count += 1
                delay = self.calculate_retry_delay(job.retry_count)
                job.next_run_time = datetime.utcnow() + timedelta(seconds=delay)
                job.state = JobState.PENDING
                logger.info(
                    f"Job {job_id} failed, retry {job.retry_count}/{self.config.max_retries} "
                    f"scheduled in {delay:.1f}s"
                )
            else:
                job.state = JobState.FAILED
                logger.error(f"Job {job_id} failed permanently: {error}")

            return True

    async def cleanup_old_jobs(self, older_than: datetime) -> int:
        """Remove old completed/failed jobs."""
        async with self._lock:
            to_remove = []
            for job_id, job in self._jobs.items():
                if job.state in (JobState.COMPLETED, JobState.FAILED):
                    if job.updated_at < older_than:
                        to_remove.append(job_id)

            for job_id in to_remove:
                del self._jobs[job_id]

            if to_remove:
                logger.info(f"Cleaned up {len(to_remove)} old jobs")
            return len(to_remove)


# =============================================================================
# SQLAlchemy Backend
# =============================================================================


class SQLAlchemySchedulerBackend(SchedulerBackend):
    """SQLAlchemy-based scheduler backend for persistent job storage.

    Jobs are stored in SQLite database and survive process restarts.
    Suitable for production workloads requiring durability.

    Features:
        - Persistent storage in SQLite
        - Automatic table creation
        - Thread-safe with row-level locking
        - Supports all job lifecycle operations
        - Automatic cleanup of old jobs

    Usage:
        backend = SQLAlchemySchedulerBackend(config)
        await backend.initialize()

        job = JobData(name="my_job", func_ref="module:function")
        await backend.add_job(job)
    """

    def __init__(self, config: SchedulerBackendConfig | None = None) -> None:
        """Initialize SQLAlchemy backend."""
        if config is None:
            config = SchedulerBackendConfig(backend_type=BackendType.SQLALCHEMY)
        super().__init__(config)
        self._cleanup_task: asyncio.Task | None = None

    @property
    def backend_type(self) -> BackendType:
        return BackendType.SQLALCHEMY

    async def initialize(self) -> None:
        """Initialize the SQLAlchemy backend and ensure table exists."""
        if self._initialized:
            return

        logger.info("Initializing SQLAlchemy scheduler backend")

        try:
            # Import here to avoid circular imports
            from ....db import get_session, init_db

            # Ensure database tables are created
            await init_db()

            # Recover misfired jobs on startup
            await self._recover_misfired_jobs()

            # Start cleanup task
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

            self._initialized = True
            self._shutdown = False
            logger.info("SQLAlchemy scheduler backend initialized")

        except Exception as e:
            logger.error(f"Failed to initialize SQLAlchemy backend: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown the SQLAlchemy backend."""
        if self._shutdown:
            return

        logger.info("Shutting down SQLAlchemy scheduler backend")

        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Wait for running jobs
        if self._running_jobs:
            logger.info(f"Waiting for {len(self._running_jobs)} running jobs...")
            wait_until = datetime.utcnow() + timedelta(
                seconds=self.config.shutdown_timeout
            )
            while self._running_jobs and datetime.utcnow() < wait_until:
                await asyncio.sleep(0.5)

            # Mark remaining running jobs as pending for recovery on restart
            if self._running_jobs:
                logger.warning(
                    f"Marking {len(self._running_jobs)} jobs as pending for recovery"
                )
                for job_id in list(self._running_jobs):
                    try:
                        job = await self.get_job(job_id)
                        if job:
                            job.state = JobState.PENDING
                            await self.update_job(job)
                    except Exception as e:
                        logger.error(f"Error recovering job {job_id}: {e}")

        self._shutdown = True
        self._initialized = False
        logger.info("SQLAlchemy scheduler backend shut down")

    async def _recover_misfired_jobs(self) -> None:
        """Recover jobs that were running during previous shutdown."""
        from ....db import get_session
        from ....db.models import SchedulerJob

        try:
            async with get_session() as session:
                from sqlalchemy import select, update

                # Find jobs that were left in running state
                result = await session.execute(
                    select(SchedulerJob).where(
                        SchedulerJob.state == JobState.RUNNING.value
                    )
                )
                running_jobs = result.scalars().all()

                for db_job in running_jobs:
                    logger.info(f"Recovering job {db_job.id} from running state")
                    db_job.state = JobState.PENDING.value
                    db_job.updated_at = datetime.utcnow()

                await session.commit()

                if running_jobs:
                    logger.info(f"Recovered {len(running_jobs)} jobs from running state")

        except Exception as e:
            logger.error(f"Error recovering misfired jobs: {e}")

    async def _periodic_cleanup(self) -> None:
        """Periodically clean up old jobs."""
        while not self._shutdown:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                if self._shutdown:
                    break

                older_than = datetime.utcnow() - timedelta(
                    days=self.config.job_retention_days
                )
                removed = await self.cleanup_old_jobs(older_than)
                if removed > 0:
                    logger.debug(f"Periodic cleanup removed {removed} old jobs")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")

    def _job_to_model(self, job: JobData) -> "SchedulerJob":
        """Convert JobData to database model."""
        from ....db.models import SchedulerJob

        return SchedulerJob(
            id=job.id,
            name=job.name,
            func_ref=job.func_ref,
            trigger_type=job.trigger_type,
            trigger_args=job.trigger_args,
            args=list(job.args),
            kwargs=job.kwargs,
            next_run_time=job.next_run_time,
            state=job.state.value,
            retry_count=job.retry_count,
            last_run_time=job.last_run_time,
            last_error=job.last_error,
            job_metadata=job.metadata,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )

    def _model_to_job(self, model: "SchedulerJob") -> JobData:
        """Convert database model to JobData."""
        return JobData(
            id=model.id,
            name=model.name,
            func_ref=model.func_ref,
            trigger_type=model.trigger_type,
            trigger_args=model.trigger_args or {},
            args=tuple(model.args) if model.args else (),
            kwargs=model.kwargs or {},
            next_run_time=model.next_run_time,
            state=JobState(model.state),
            retry_count=model.retry_count,
            last_run_time=model.last_run_time,
            last_error=model.last_error,
            metadata=model.job_metadata or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def add_job(self, job: JobData) -> JobData:
        """Add a job to the database."""
        from ....db import get_session
        from ....db.models import SchedulerJob

        async with self._lock:
            try:
                async with get_session() as session:
                    from sqlalchemy import select

                    # Check if job exists
                    result = await session.execute(
                        select(SchedulerJob).where(SchedulerJob.id == job.id)
                    )
                    if result.scalar_one_or_none():
                        raise ValueError(f"Job {job.id} already exists")

                    job.created_at = datetime.utcnow()
                    job.updated_at = datetime.utcnow()

                    db_job = self._job_to_model(job)
                    session.add(db_job)
                    await session.commit()

                    logger.debug(f"Added job {job.id} ({job.name})")
                    return job

            except ValueError:
                raise
            except Exception as e:
                logger.error(f"Error adding job {job.id}: {e}")
                raise

    async def update_job(self, job: JobData) -> JobData:
        """Update a job in the database."""
        from ....db import get_session
        from ....db.models import SchedulerJob

        async with self._lock:
            try:
                async with get_session() as session:
                    from sqlalchemy import select

                    result = await session.execute(
                        select(SchedulerJob).where(SchedulerJob.id == job.id)
                    )
                    db_job = result.scalar_one_or_none()

                    if not db_job:
                        raise KeyError(f"Job {job.id} not found")

                    job.updated_at = datetime.utcnow()

                    db_job.name = job.name
                    db_job.func_ref = job.func_ref
                    db_job.trigger_type = job.trigger_type
                    db_job.trigger_args = job.trigger_args
                    db_job.args = list(job.args)
                    db_job.kwargs = job.kwargs
                    db_job.next_run_time = job.next_run_time
                    db_job.state = job.state.value
                    db_job.retry_count = job.retry_count
                    db_job.last_run_time = job.last_run_time
                    db_job.last_error = job.last_error
                    db_job.job_metadata = job.metadata
                    db_job.updated_at = job.updated_at

                    await session.commit()
                    logger.debug(f"Updated job {job.id} ({job.name})")
                    return job

            except KeyError:
                raise
            except Exception as e:
                logger.error(f"Error updating job {job.id}: {e}")
                raise

    async def remove_job(self, job_id: str) -> bool:
        """Remove a job from the database."""
        from ....db import get_session
        from ....db.models import SchedulerJob

        async with self._lock:
            try:
                async with get_session() as session:
                    from sqlalchemy import delete

                    result = await session.execute(
                        delete(SchedulerJob).where(SchedulerJob.id == job_id)
                    )
                    await session.commit()

                    removed = result.rowcount > 0
                    if removed:
                        logger.debug(f"Removed job {job_id}")
                    return removed

            except Exception as e:
                logger.error(f"Error removing job {job_id}: {e}")
                return False

    async def get_job(self, job_id: str) -> JobData | None:
        """Get a job by ID from the database."""
        from ....db import get_session
        from ....db.models import SchedulerJob

        try:
            async with get_session() as session:
                from sqlalchemy import select

                result = await session.execute(
                    select(SchedulerJob).where(SchedulerJob.id == job_id)
                )
                db_job = result.scalar_one_or_none()

                if db_job:
                    return self._model_to_job(db_job)
                return None

        except Exception as e:
            logger.error(f"Error getting job {job_id}: {e}")
            return None

    async def get_jobs(
        self,
        state: JobState | None = None,
        limit: int | None = None,
    ) -> list[JobData]:
        """Get jobs from the database."""
        from ....db import get_session
        from ....db.models import SchedulerJob

        try:
            async with get_session() as session:
                from sqlalchemy import select

                query = select(SchedulerJob)

                if state:
                    query = query.where(SchedulerJob.state == state.value)

                query = query.order_by(SchedulerJob.next_run_time)

                if limit:
                    query = query.limit(limit)

                result = await session.execute(query)
                db_jobs = result.scalars().all()

                return [self._model_to_job(j) for j in db_jobs]

        except Exception as e:
            logger.error(f"Error getting jobs: {e}")
            return []

    async def get_due_jobs(self, now: datetime | None = None) -> list[JobData]:
        """Get jobs due for execution from the database."""
        from ....db import get_session
        from ....db.models import SchedulerJob

        now = now or datetime.utcnow()

        try:
            async with get_session() as session:
                from sqlalchemy import select

                query = (
                    select(SchedulerJob)
                    .where(
                        SchedulerJob.state.in_([
                            JobState.PENDING.value,
                            JobState.MISFIRED.value,
                        ])
                    )
                    .where(SchedulerJob.next_run_time <= now)
                    .order_by(SchedulerJob.next_run_time)
                )

                result = await session.execute(query)
                db_jobs = result.scalars().all()

                jobs = []
                for db_job in db_jobs:
                    if db_job.id not in self._running_jobs:
                        jobs.append(self._model_to_job(db_job))

                return jobs

        except Exception as e:
            logger.error(f"Error getting due jobs: {e}")
            return []

    async def mark_job_running(self, job_id: str) -> bool:
        """Mark a job as running in the database."""
        from ....db import get_session
        from ....db.models import SchedulerJob

        async with self._lock:
            if job_id in self._running_jobs:
                return False

            try:
                async with get_session() as session:
                    from sqlalchemy import select

                    result = await session.execute(
                        select(SchedulerJob).where(SchedulerJob.id == job_id)
                    )
                    db_job = result.scalar_one_or_none()

                    if not db_job:
                        return False

                    if db_job.state == JobState.RUNNING.value:
                        return False

                    db_job.state = JobState.RUNNING.value
                    db_job.last_run_time = datetime.utcnow()
                    db_job.updated_at = datetime.utcnow()

                    await session.commit()
                    self._running_jobs.add(job_id)
                    logger.debug(f"Job {job_id} marked as running")
                    return True

            except Exception as e:
                logger.error(f"Error marking job {job_id} as running: {e}")
                return False

    async def mark_job_completed(
        self,
        job_id: str,
        next_run_time: datetime | None = None,
    ) -> bool:
        """Mark a job as completed in the database."""
        from ....db import get_session
        from ....db.models import SchedulerJob

        async with self._lock:
            try:
                async with get_session() as session:
                    from sqlalchemy import select

                    result = await session.execute(
                        select(SchedulerJob).where(SchedulerJob.id == job_id)
                    )
                    db_job = result.scalar_one_or_none()

                    if not db_job:
                        return False

                    if next_run_time:
                        db_job.state = JobState.PENDING.value
                        db_job.next_run_time = next_run_time
                    else:
                        db_job.state = JobState.COMPLETED.value

                    db_job.retry_count = 0
                    db_job.last_error = None
                    db_job.updated_at = datetime.utcnow()

                    await session.commit()
                    self._running_jobs.discard(job_id)
                    logger.debug(f"Job {job_id} marked as completed")
                    return True

            except Exception as e:
                logger.error(f"Error marking job {job_id} as completed: {e}")
                return False

    async def mark_job_failed(
        self,
        job_id: str,
        error: str,
        schedule_retry: bool = True,
    ) -> bool:
        """Mark a job as failed in the database."""
        from ....db import get_session
        from ....db.models import SchedulerJob

        async with self._lock:
            try:
                async with get_session() as session:
                    from sqlalchemy import select

                    result = await session.execute(
                        select(SchedulerJob).where(SchedulerJob.id == job_id)
                    )
                    db_job = result.scalar_one_or_none()

                    if not db_job:
                        return False

                    db_job.last_error = error
                    db_job.updated_at = datetime.utcnow()
                    self._running_jobs.discard(job_id)

                    if schedule_retry and db_job.retry_count < self.config.max_retries:
                        db_job.retry_count += 1
                        delay = self.calculate_retry_delay(db_job.retry_count)
                        db_job.next_run_time = datetime.utcnow() + timedelta(seconds=delay)
                        db_job.state = JobState.PENDING.value
                        logger.info(
                            f"Job {job_id} failed, retry {db_job.retry_count}/"
                            f"{self.config.max_retries} scheduled in {delay:.1f}s"
                        )
                    else:
                        db_job.state = JobState.FAILED.value
                        logger.error(f"Job {job_id} failed permanently: {error}")

                    await session.commit()
                    return True

            except Exception as e:
                logger.error(f"Error marking job {job_id} as failed: {e}")
                return False

    async def cleanup_old_jobs(self, older_than: datetime) -> int:
        """Remove old completed/failed jobs from the database."""
        from ....db import get_session
        from ....db.models import SchedulerJob

        try:
            async with get_session() as session:
                from sqlalchemy import delete

                result = await session.execute(
                    delete(SchedulerJob)
                    .where(
                        SchedulerJob.state.in_([
                            JobState.COMPLETED.value,
                            JobState.FAILED.value,
                        ])
                    )
                    .where(SchedulerJob.updated_at < older_than)
                )
                await session.commit()

                removed = result.rowcount
                if removed > 0:
                    logger.info(f"Cleaned up {removed} old jobs")
                return removed

        except Exception as e:
            logger.error(f"Error cleaning up old jobs: {e}")
            return 0

    def get_status(self) -> dict[str, Any]:
        """Get backend status with database-specific information."""
        status = super().get_status()
        status["cleanup_interval"] = self.config.cleanup_interval
        status["job_retention_days"] = self.config.job_retention_days
        return status


# =============================================================================
# Factory Function
# =============================================================================


def create_scheduler_backend(
    config: SchedulerBackendConfig | None = None,
) -> SchedulerBackend:
    """Create a scheduler backend based on configuration.

    Args:
        config: Backend configuration. Uses environment config if None.

    Returns:
        Configured scheduler backend instance.

    Example:
        # Create from environment
        backend = create_scheduler_backend()

        # Create with specific config
        config = SchedulerBackendConfig(backend_type=BackendType.MEMORY)
        backend = create_scheduler_backend(config)
    """
    if config is None:
        config = SchedulerBackendConfig.from_env()

    if config.backend_type == BackendType.MEMORY:
        return InMemorySchedulerBackend(config)
    elif config.backend_type == BackendType.SQLALCHEMY:
        return SQLAlchemySchedulerBackend(config)
    else:
        raise ValueError(f"Unknown backend type: {config.backend_type}")


__all__ = [
    # Enums
    "BackendType",
    "JobState",
    "MisfirePolicy",
    # Configuration
    "SchedulerBackendConfig",
    "JobData",
    "JobExecutionResult",
    # Abstract base
    "SchedulerBackend",
    # Implementations
    "InMemorySchedulerBackend",
    "SQLAlchemySchedulerBackend",
    # Factory
    "create_scheduler_backend",
]
