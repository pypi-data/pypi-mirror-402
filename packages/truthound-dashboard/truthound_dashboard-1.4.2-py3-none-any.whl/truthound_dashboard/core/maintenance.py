"""Database maintenance and cleanup tasks.

This module provides automated database maintenance operations including:
- Cleanup of old validation records
- Removal of stale profile data
- Notification log cleanup
- Database optimization (VACUUM)

The maintenance system uses a configurable strategy pattern allowing
custom cleanup policies.

Example:
    manager = get_maintenance_manager()
    await manager.run_cleanup()
    await manager.vacuum()
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from sqlalchemy import delete, func, select, text

from truthound_dashboard.config import get_settings
from truthound_dashboard.db import get_session
from truthound_dashboard.db.models import (
    NotificationLog,
    Profile,
    Source,
    Validation,
)

logger = logging.getLogger(__name__)


class RetentionPolicyType(str, Enum):
    """Types of retention policies."""

    TIME = "time"  # Time-based retention (days)
    COUNT = "count"  # Count-based retention (keep N records)
    SIZE = "size"  # Size-based retention (keep under N bytes)
    STATUS = "status"  # Status-based retention (keep passed/failed)
    TAG = "tag"  # Tag-based retention (keep/remove by tag)
    COMPOSITE = "composite"  # Combination of multiple policies


@dataclass
class RetentionPolicy:
    """Individual retention policy definition.

    Attributes:
        policy_type: Type of retention policy.
        value: Policy value (days, count, bytes, status, or tag).
        target: What this policy applies to (validations, profiles, etc).
        priority: Policy priority (higher = applied first).
        enabled: Whether this policy is active.
    """

    policy_type: RetentionPolicyType
    value: Any
    target: str = "validations"
    priority: int = 0
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "policy_type": self.policy_type.value if isinstance(self.policy_type, Enum) else self.policy_type,
            "value": self.value,
            "target": self.target,
            "priority": self.priority,
            "enabled": self.enabled,
        }


@dataclass
class CleanupResult:
    """Result of a cleanup operation.

    Attributes:
        task_name: Name of the cleanup task.
        records_deleted: Number of records deleted.
        duration_ms: Duration in milliseconds.
        success: Whether the operation succeeded.
        error: Error message if failed.
    """

    task_name: str
    records_deleted: int = 0
    duration_ms: int = 0
    success: bool = True
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_name": self.task_name,
            "records_deleted": self.records_deleted,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error": self.error,
        }


@dataclass
class MaintenanceConfig:
    """Configuration for maintenance tasks.

    Supports 6 retention policy types:
    - Time: Keep records for N days
    - Count: Keep N most recent records
    - Size: Keep total storage under N bytes
    - Status: Different retention for passed/failed validations
    - Tag: Protect or delete records by tag
    - Composite: Combine multiple policies

    Attributes:
        validation_retention_days: Days to keep validation records (Time policy).
        profile_keep_per_source: Number of profiles to keep per source (Count policy).
        notification_log_retention_days: Days to keep notification logs (Time policy).
        run_vacuum: Whether to run VACUUM after cleanup.
        enabled: Whether automatic maintenance is enabled.
        max_storage_mb: Maximum storage in MB for validations (Size policy).
        keep_failed_validations: Whether to keep failed validations longer (Status policy).
        failed_retention_days: Days to keep failed validations (Status policy).
        protected_tags: Tags to never delete (Tag policy).
        delete_tags: Tags to delete after standard retention (Tag policy).
        policies: List of custom retention policies (Composite).
    """

    validation_retention_days: int = 90
    profile_keep_per_source: int = 5
    notification_log_retention_days: int = 30
    run_vacuum: bool = True
    enabled: bool = True
    # Size-based retention
    max_storage_mb: int | None = None  # None = no limit
    # Status-based retention
    keep_failed_validations: bool = True  # Keep failed longer for debugging
    failed_retention_days: int = 180  # Days to keep failed validations
    # Tag-based retention
    protected_tags: list[str] = field(default_factory=list)  # Tags to never delete
    delete_tags: list[str] = field(default_factory=list)  # Tags to delete after retention
    # Custom policies (Composite)
    policies: list[RetentionPolicy] = field(default_factory=list)

    def get_active_policies(self) -> list[RetentionPolicy]:
        """Get all active retention policies sorted by priority.

        Returns:
            List of RetentionPolicy sorted by priority (highest first).
        """
        active: list[RetentionPolicy] = []

        # Time policy for validations
        active.append(RetentionPolicy(
            policy_type=RetentionPolicyType.TIME,
            value=self.validation_retention_days,
            target="validations",
            priority=10,
        ))

        # Count policy for profiles
        active.append(RetentionPolicy(
            policy_type=RetentionPolicyType.COUNT,
            value=self.profile_keep_per_source,
            target="profiles",
            priority=10,
        ))

        # Time policy for notification logs
        active.append(RetentionPolicy(
            policy_type=RetentionPolicyType.TIME,
            value=self.notification_log_retention_days,
            target="notification_logs",
            priority=10,
        ))

        # Size policy if configured
        if self.max_storage_mb is not None:
            active.append(RetentionPolicy(
                policy_type=RetentionPolicyType.SIZE,
                value=self.max_storage_mb * 1024 * 1024,  # Convert to bytes
                target="validations",
                priority=20,
            ))

        # Status policy if keeping failed validations longer
        if self.keep_failed_validations:
            active.append(RetentionPolicy(
                policy_type=RetentionPolicyType.STATUS,
                value={"status": "failed", "retention_days": self.failed_retention_days},
                target="validations",
                priority=15,
            ))

        # Tag policy for protected tags
        if self.protected_tags:
            active.append(RetentionPolicy(
                policy_type=RetentionPolicyType.TAG,
                value={"protect": self.protected_tags},
                target="validations",
                priority=100,  # Highest priority - never delete
            ))

        # Tag policy for delete tags
        if self.delete_tags:
            active.append(RetentionPolicy(
                policy_type=RetentionPolicyType.TAG,
                value={"delete": self.delete_tags},
                target="validations",
                priority=5,  # Lower priority
            ))

        # Add custom policies
        active.extend([p for p in self.policies if p.enabled])

        # Sort by priority (descending)
        return sorted(active, key=lambda p: p.priority, reverse=True)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "validation_retention_days": self.validation_retention_days,
            "profile_keep_per_source": self.profile_keep_per_source,
            "notification_log_retention_days": self.notification_log_retention_days,
            "run_vacuum": self.run_vacuum,
            "enabled": self.enabled,
            "max_storage_mb": self.max_storage_mb,
            "keep_failed_validations": self.keep_failed_validations,
            "failed_retention_days": self.failed_retention_days,
            "protected_tags": self.protected_tags,
            "delete_tags": self.delete_tags,
            "active_policies": [p.to_dict() for p in self.get_active_policies()],
        }


class CleanupStrategy(ABC):
    """Abstract base class for cleanup strategies.

    Subclass this to implement custom cleanup logic.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get strategy name."""
        ...

    @abstractmethod
    async def execute(self, config: MaintenanceConfig) -> CleanupResult:
        """Execute cleanup strategy.

        Args:
            config: Maintenance configuration.

        Returns:
            CleanupResult with operation details.
        """
        ...


class ValidationCleanupStrategy(CleanupStrategy):
    """Cleanup strategy for old validation records."""

    @property
    def name(self) -> str:
        return "validation_cleanup"

    async def execute(self, config: MaintenanceConfig) -> CleanupResult:
        """Remove validation records older than retention period."""
        start_time = datetime.utcnow()

        try:
            cutoff = datetime.utcnow() - timedelta(
                days=config.validation_retention_days
            )

            async with get_session() as session:
                # Count records to delete
                count_result = await session.execute(
                    select(func.count(Validation.id)).where(
                        Validation.created_at < cutoff
                    )
                )
                count = count_result.scalar() or 0

                # Delete old records
                if count > 0:
                    await session.execute(
                        delete(Validation).where(Validation.created_at < cutoff)
                    )

                duration = int(
                    (datetime.utcnow() - start_time).total_seconds() * 1000
                )

                logger.info(
                    f"Validation cleanup: deleted {count} records "
                    f"older than {config.validation_retention_days} days"
                )

                return CleanupResult(
                    task_name=self.name,
                    records_deleted=count,
                    duration_ms=duration,
                    success=True,
                )

        except Exception as e:
            duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            logger.error(f"Validation cleanup failed: {e}")
            return CleanupResult(
                task_name=self.name,
                duration_ms=duration,
                success=False,
                error=str(e),
            )


class ProfileCleanupStrategy(CleanupStrategy):
    """Cleanup strategy for keeping only recent profiles per source."""

    @property
    def name(self) -> str:
        return "profile_cleanup"

    async def execute(self, config: MaintenanceConfig) -> CleanupResult:
        """Keep only the most recent N profiles per source."""
        start_time = datetime.utcnow()
        total_deleted = 0

        try:
            async with get_session() as session:
                # Get all source IDs
                sources_result = await session.execute(select(Source.id))
                source_ids = [row[0] for row in sources_result]

                for source_id in source_ids:
                    # Get IDs of profiles to keep
                    keep_result = await session.execute(
                        select(Profile.id)
                        .where(Profile.source_id == source_id)
                        .order_by(Profile.created_at.desc())
                        .limit(config.profile_keep_per_source)
                    )
                    keep_ids = [row[0] for row in keep_result]

                    if not keep_ids:
                        continue

                    # Count and delete excess profiles
                    count_result = await session.execute(
                        select(func.count(Profile.id))
                        .where(Profile.source_id == source_id)
                        .where(Profile.id.not_in(keep_ids))
                    )
                    count = count_result.scalar() or 0

                    if count > 0:
                        await session.execute(
                            delete(Profile)
                            .where(Profile.source_id == source_id)
                            .where(Profile.id.not_in(keep_ids))
                        )
                        total_deleted += count

            duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            logger.info(
                f"Profile cleanup: deleted {total_deleted} records, "
                f"keeping {config.profile_keep_per_source} per source"
            )

            return CleanupResult(
                task_name=self.name,
                records_deleted=total_deleted,
                duration_ms=duration,
                success=True,
            )

        except Exception as e:
            duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            logger.error(f"Profile cleanup failed: {e}")
            return CleanupResult(
                task_name=self.name,
                duration_ms=duration,
                success=False,
                error=str(e),
            )


class NotificationLogCleanupStrategy(CleanupStrategy):
    """Cleanup strategy for old notification logs."""

    @property
    def name(self) -> str:
        return "notification_log_cleanup"

    async def execute(self, config: MaintenanceConfig) -> CleanupResult:
        """Remove notification logs older than retention period."""
        start_time = datetime.utcnow()

        try:
            cutoff = datetime.utcnow() - timedelta(
                days=config.notification_log_retention_days
            )

            async with get_session() as session:
                # Count records to delete
                count_result = await session.execute(
                    select(func.count(NotificationLog.id)).where(
                        NotificationLog.created_at < cutoff
                    )
                )
                count = count_result.scalar() or 0

                # Delete old records
                if count > 0:
                    await session.execute(
                        delete(NotificationLog).where(
                            NotificationLog.created_at < cutoff
                        )
                    )

                duration = int(
                    (datetime.utcnow() - start_time).total_seconds() * 1000
                )

                logger.info(
                    f"Notification log cleanup: deleted {count} records "
                    f"older than {config.notification_log_retention_days} days"
                )

                return CleanupResult(
                    task_name=self.name,
                    records_deleted=count,
                    duration_ms=duration,
                    success=True,
                )

        except Exception as e:
            duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            logger.error(f"Notification log cleanup failed: {e}")
            return CleanupResult(
                task_name=self.name,
                duration_ms=duration,
                success=False,
                error=str(e),
            )


class SizeBasedCleanupStrategy(CleanupStrategy):
    """Cleanup strategy based on total storage size.

    Removes oldest validations when total storage exceeds limit.
    """

    @property
    def name(self) -> str:
        return "size_based_cleanup"

    async def execute(self, config: MaintenanceConfig) -> CleanupResult:
        """Remove validations if total storage exceeds limit."""
        start_time = datetime.utcnow()
        total_deleted = 0

        if config.max_storage_mb is None:
            return CleanupResult(
                task_name=self.name,
                records_deleted=0,
                duration_ms=0,
                success=True,
            )

        max_bytes = config.max_storage_mb * 1024 * 1024

        try:
            async with get_session() as session:
                # Estimate current storage (based on result_json size)
                # In production, you might track actual file sizes
                size_result = await session.execute(
                    select(func.sum(func.length(Validation.result_json)))
                )
                current_size = size_result.scalar() or 0

                if current_size <= max_bytes:
                    duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                    return CleanupResult(
                        task_name=self.name,
                        records_deleted=0,
                        duration_ms=duration,
                        success=True,
                    )

                # Calculate how much to delete (aim for 80% of max)
                target_size = int(max_bytes * 0.8)
                bytes_to_free = current_size - target_size

                # Get validations ordered by created_at, delete oldest first
                validations_result = await session.execute(
                    select(Validation.id, func.length(Validation.result_json))
                    .order_by(Validation.created_at.asc())
                )

                freed_bytes = 0
                ids_to_delete = []

                for val_id, size in validations_result:
                    if freed_bytes >= bytes_to_free:
                        break
                    ids_to_delete.append(val_id)
                    freed_bytes += size or 0

                if ids_to_delete:
                    await session.execute(
                        delete(Validation).where(Validation.id.in_(ids_to_delete))
                    )
                    total_deleted = len(ids_to_delete)

            duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            logger.info(
                f"Size-based cleanup: deleted {total_deleted} records, "
                f"freed ~{freed_bytes / 1024 / 1024:.2f} MB"
            )

            return CleanupResult(
                task_name=self.name,
                records_deleted=total_deleted,
                duration_ms=duration,
                success=True,
            )

        except Exception as e:
            duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            logger.error(f"Size-based cleanup failed: {e}")
            return CleanupResult(
                task_name=self.name,
                duration_ms=duration,
                success=False,
                error=str(e),
            )


class StatusBasedCleanupStrategy(CleanupStrategy):
    """Cleanup strategy based on validation status.

    Applies different retention rules for passed vs failed validations.
    Failed validations are kept longer for debugging purposes.
    """

    @property
    def name(self) -> str:
        return "status_based_cleanup"

    async def execute(self, config: MaintenanceConfig) -> CleanupResult:
        """Remove validations based on status-specific retention."""
        start_time = datetime.utcnow()
        total_deleted = 0

        if not config.keep_failed_validations:
            return CleanupResult(
                task_name=self.name,
                records_deleted=0,
                duration_ms=0,
                success=True,
            )

        try:
            # Standard cutoff for passed validations
            passed_cutoff = datetime.utcnow() - timedelta(
                days=config.validation_retention_days
            )
            # Extended cutoff for failed validations
            failed_cutoff = datetime.utcnow() - timedelta(
                days=config.failed_retention_days
            )

            async with get_session() as session:
                # Delete old passed validations (use standard retention)
                passed_count_result = await session.execute(
                    select(func.count(Validation.id)).where(
                        Validation.passed == True,  # noqa: E712
                        Validation.created_at < passed_cutoff,
                    )
                )
                passed_count = passed_count_result.scalar() or 0

                if passed_count > 0:
                    await session.execute(
                        delete(Validation).where(
                            Validation.passed == True,  # noqa: E712
                            Validation.created_at < passed_cutoff,
                        )
                    )
                    total_deleted += passed_count

                # Delete old failed validations (use extended retention)
                failed_count_result = await session.execute(
                    select(func.count(Validation.id)).where(
                        Validation.passed == False,  # noqa: E712
                        Validation.created_at < failed_cutoff,
                    )
                )
                failed_count = failed_count_result.scalar() or 0

                if failed_count > 0:
                    await session.execute(
                        delete(Validation).where(
                            Validation.passed == False,  # noqa: E712
                            Validation.created_at < failed_cutoff,
                        )
                    )
                    total_deleted += failed_count

            duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            logger.info(
                f"Status-based cleanup: deleted {passed_count} passed, "
                f"{failed_count} failed validations"
            )

            return CleanupResult(
                task_name=self.name,
                records_deleted=total_deleted,
                duration_ms=duration,
                success=True,
            )

        except Exception as e:
            duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            logger.error(f"Status-based cleanup failed: {e}")
            return CleanupResult(
                task_name=self.name,
                duration_ms=duration,
                success=False,
                error=str(e),
            )


class TagBasedCleanupStrategy(CleanupStrategy):
    """Cleanup strategy based on validation tags.

    Protects tagged validations or deletes them based on configuration.
    Tags can be stored in validation metadata or a separate tags table.
    """

    @property
    def name(self) -> str:
        return "tag_based_cleanup"

    async def execute(self, config: MaintenanceConfig) -> CleanupResult:
        """Handle tag-based retention rules."""
        start_time = datetime.utcnow()
        total_deleted = 0

        if not config.protected_tags and not config.delete_tags:
            return CleanupResult(
                task_name=self.name,
                records_deleted=0,
                duration_ms=0,
                success=True,
            )

        try:
            async with get_session() as session:
                # Handle delete_tags: remove validations with these tags
                # that are past standard retention
                if config.delete_tags:
                    cutoff = datetime.utcnow() - timedelta(
                        days=config.validation_retention_days
                    )

                    for tag in config.delete_tags:
                        # Tags stored in result_json metadata
                        # This is a simplified approach; production might use a tags table
                        count_result = await session.execute(
                            select(func.count(Validation.id)).where(
                                Validation.created_at < cutoff,
                                Validation.result_json.contains(f'"tag": "{tag}"'),
                            )
                        )
                        count = count_result.scalar() or 0

                        if count > 0:
                            await session.execute(
                                delete(Validation).where(
                                    Validation.created_at < cutoff,
                                    Validation.result_json.contains(f'"tag": "{tag}"'),
                                )
                            )
                            total_deleted += count

                            logger.info(f"Tag cleanup: deleted {count} validations with tag '{tag}'")

            duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            logger.info(f"Tag-based cleanup: deleted {total_deleted} total records")

            return CleanupResult(
                task_name=self.name,
                records_deleted=total_deleted,
                duration_ms=duration,
                success=True,
            )

        except Exception as e:
            duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            logger.error(f"Tag-based cleanup failed: {e}")
            return CleanupResult(
                task_name=self.name,
                duration_ms=duration,
                success=False,
                error=str(e),
            )


@dataclass
class MaintenanceReport:
    """Report of a complete maintenance run.

    Attributes:
        started_at: When maintenance started.
        completed_at: When maintenance completed.
        results: List of cleanup results.
        vacuum_performed: Whether VACUUM was run.
    """

    started_at: datetime
    completed_at: datetime | None = None
    results: list[CleanupResult] = field(default_factory=list)
    vacuum_performed: bool = False
    vacuum_error: str | None = None

    @property
    def total_deleted(self) -> int:
        """Get total records deleted across all tasks."""
        return sum(r.records_deleted for r in self.results)

    @property
    def total_duration_ms(self) -> int:
        """Get total duration in milliseconds."""
        if self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds() * 1000)
        return 0

    @property
    def success(self) -> bool:
        """Check if all tasks succeeded."""
        return all(r.success for r in self.results) and self.vacuum_error is None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "started_at": self.started_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "results": [r.to_dict() for r in self.results],
            "total_deleted": self.total_deleted,
            "total_duration_ms": self.total_duration_ms,
            "vacuum_performed": self.vacuum_performed,
            "vacuum_error": self.vacuum_error,
            "success": self.success,
        }


class MaintenanceManager:
    """Manager for database maintenance operations.

    Coordinates cleanup strategies and provides a unified interface
    for maintenance tasks.

    Usage:
        manager = MaintenanceManager()
        manager.register_strategy(ValidationCleanupStrategy())
        report = await manager.run_cleanup()
    """

    def __init__(self, config: MaintenanceConfig | None = None) -> None:
        """Initialize maintenance manager.

        Args:
            config: Maintenance configuration. Uses defaults if not provided.
        """
        self._config = config or MaintenanceConfig()
        self._strategies: list[CleanupStrategy] = []

    @property
    def config(self) -> MaintenanceConfig:
        """Get maintenance configuration."""
        return self._config

    def register_strategy(self, strategy: CleanupStrategy) -> None:
        """Register a cleanup strategy.

        Args:
            strategy: Cleanup strategy to register.
        """
        self._strategies.append(strategy)

    def register_default_strategies(self) -> None:
        """Register all default cleanup strategies.

        Registers 6 types of cleanup strategies:
        - Time-based: ValidationCleanupStrategy, NotificationLogCleanupStrategy
        - Count-based: ProfileCleanupStrategy
        - Size-based: SizeBasedCleanupStrategy
        - Status-based: StatusBasedCleanupStrategy
        - Tag-based: TagBasedCleanupStrategy
        """
        self._strategies = [
            # Time-based policies
            ValidationCleanupStrategy(),
            NotificationLogCleanupStrategy(),
            # Count-based policy
            ProfileCleanupStrategy(),
            # Size-based policy
            SizeBasedCleanupStrategy(),
            # Status-based policy
            StatusBasedCleanupStrategy(),
            # Tag-based policy
            TagBasedCleanupStrategy(),
        ]

    async def run_cleanup(self) -> MaintenanceReport:
        """Run all registered cleanup strategies.

        Returns:
            MaintenanceReport with all results.
        """
        if not self._config.enabled:
            logger.info("Maintenance is disabled")
            return MaintenanceReport(
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )

        report = MaintenanceReport(started_at=datetime.utcnow())

        for strategy in self._strategies:
            try:
                result = await strategy.execute(self._config)
                report.results.append(result)
            except Exception as e:
                logger.error(f"Strategy {strategy.name} failed: {e}")
                report.results.append(
                    CleanupResult(
                        task_name=strategy.name,
                        success=False,
                        error=str(e),
                    )
                )

        # Run VACUUM if configured
        if self._config.run_vacuum:
            try:
                await self.vacuum()
                report.vacuum_performed = True
            except Exception as e:
                report.vacuum_error = str(e)
                logger.error(f"VACUUM failed: {e}")

        report.completed_at = datetime.utcnow()

        logger.info(
            f"Maintenance completed: {report.total_deleted} records deleted "
            f"in {report.total_duration_ms}ms"
        )

        return report

    async def vacuum(self) -> None:
        """Run SQLite VACUUM to reclaim space."""
        from truthound_dashboard.db.database import get_engine

        logger.info("Running database VACUUM")

        engine = get_engine()
        async with engine.begin() as conn:
            # VACUUM cannot run in a transaction, so we need raw connection
            await conn.execute(text("VACUUM"))

        logger.info("Database VACUUM completed")

    async def run_task(self, task_name: str) -> CleanupResult | None:
        """Run a specific cleanup task by name.

        Args:
            task_name: Name of the task to run.

        Returns:
            CleanupResult or None if task not found.
        """
        for strategy in self._strategies:
            if strategy.name == task_name:
                return await strategy.execute(self._config)
        return None


# Singleton instance
_manager: MaintenanceManager | None = None


def get_maintenance_manager() -> MaintenanceManager:
    """Get maintenance manager singleton.

    Returns:
        MaintenanceManager with default strategies registered.
    """
    global _manager
    if _manager is None:
        _manager = MaintenanceManager()
        _manager.register_default_strategies()
    return _manager


def reset_maintenance_manager() -> None:
    """Reset maintenance manager singleton (for testing)."""
    global _manager
    _manager = None


# Convenience functions for scheduled tasks
async def cleanup_old_validations(days: int | None = None) -> CleanupResult:
    """Cleanup old validation records.

    Args:
        days: Override retention days. Uses config default if not specified.

    Returns:
        CleanupResult with operation details.
    """
    manager = get_maintenance_manager()
    if days is not None:
        manager.config.validation_retention_days = days
    return await ValidationCleanupStrategy().execute(manager.config)


async def cleanup_old_profiles(keep_per_source: int | None = None) -> CleanupResult:
    """Cleanup old profile records.

    Args:
        keep_per_source: Override profiles to keep. Uses config default if not specified.

    Returns:
        CleanupResult with operation details.
    """
    manager = get_maintenance_manager()
    if keep_per_source is not None:
        manager.config.profile_keep_per_source = keep_per_source
    return await ProfileCleanupStrategy().execute(manager.config)


async def cleanup_notification_logs(days: int | None = None) -> CleanupResult:
    """Cleanup old notification logs.

    Args:
        days: Override retention days. Uses config default if not specified.

    Returns:
        CleanupResult with operation details.
    """
    manager = get_maintenance_manager()
    if days is not None:
        manager.config.notification_log_retention_days = days
    return await NotificationLogCleanupStrategy().execute(manager.config)


async def vacuum_database() -> None:
    """Run database VACUUM."""
    manager = get_maintenance_manager()
    await manager.vacuum()
