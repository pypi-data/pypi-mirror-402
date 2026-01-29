"""Escalation scheduler service with APScheduler integration.

This module provides automatic escalation checking via APScheduler,
triggering escalations when incidents reach their scheduled escalation time.

Features:
    - Periodic checking of pending escalations
    - Configurable check interval
    - Abstract handler interface for extensibility
    - Multiple escalation strategy support
    - Integration with notification dispatcher
    - **Persistent job storage (SQLAlchemy backend)**
    - **Configurable misfire handling with grace time**
    - **Error recovery with exponential backoff**
    - **Job coalescing to avoid duplicate executions**
    - **Graceful shutdown handling**

Usage:
    from truthound_dashboard.core.notifications.escalation.scheduler import (
        EscalationSchedulerService,
        get_escalation_scheduler,
        start_escalation_scheduler,
        stop_escalation_scheduler,
    )

    # Start the scheduler with persistent backend
    scheduler = get_escalation_scheduler()
    await scheduler.start()

    # Or use convenience functions
    await start_escalation_scheduler()
"""

from __future__ import annotations

import asyncio
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ...validation_limits import get_escalation_limits, ValidationLimitError
from ....db import get_session
from ....db.models import (
    EscalationIncidentModel,
    EscalationPolicyModel,
    EscalationStateEnum,
    NotificationChannel,
)
from ..dispatcher import create_dispatcher
from .backends import (
    BackendType,
    JobData,
    JobState,
    SchedulerBackend,
    SchedulerBackendConfig,
    create_scheduler_backend,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class EscalationSchedulerConfig:
    """Configuration for the escalation scheduler with validation.

    Validation:
        - check_interval_seconds: Must be between 10 and 3600 (configurable).
        - max_escalations_per_check: Must be between 1 and 1000.
        - retry_delay_seconds: Must be between 1 and 3600.
        - max_retries: Must be between 0 and 10.

    DoS Prevention:
        - Minimum check interval prevents excessive CPU usage.
        - Maximum escalations per check prevents memory exhaustion.
        - Maximum retry attempts prevents infinite retry loops.

    Environment Variables:
        - TRUTHOUND_ESCALATION_CHECK_INTERVAL_MIN
        - TRUTHOUND_ESCALATION_CHECK_INTERVAL_MAX

    Attributes:
        check_interval_seconds: How often to check for pending escalations.
        max_escalations_per_check: Maximum escalations to process per check.
        retry_on_failure: Whether to retry failed escalations.
        retry_delay_seconds: Delay before retrying failed escalation.
        enabled: Whether the scheduler is enabled.
        backend_type: Type of scheduler backend (memory, sqlalchemy).
        misfire_grace_time: Seconds to allow for late job execution.
        coalesce: Combine multiple pending executions into one.
        max_retries: Maximum retry attempts on failure.
        shutdown_timeout: Seconds to wait for jobs during shutdown.
    """

    check_interval_seconds: int = 60
    max_escalations_per_check: int = 100
    retry_on_failure: bool = True
    retry_delay_seconds: int = 300
    enabled: bool = True
    backend_type: BackendType = BackendType.SQLALCHEMY
    misfire_grace_time: int = 60
    coalesce: bool = True
    max_retries: int = 3
    shutdown_timeout: float = 30.0

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        limits = get_escalation_limits()

        # Validate check_interval_seconds
        valid, error = limits.validate_check_interval(self.check_interval_seconds)
        if not valid:
            raise ValidationLimitError(
                error or f"Invalid check_interval_seconds: {self.check_interval_seconds}",
                parameter="check_interval_seconds",
                value=self.check_interval_seconds,
            )

        # Validate max_escalations_per_check (1-1000)
        if self.max_escalations_per_check < 1:
            raise ValidationLimitError(
                f"max_escalations_per_check must be at least 1, "
                f"got {self.max_escalations_per_check}",
                parameter="max_escalations_per_check",
                value=self.max_escalations_per_check,
            )
        if self.max_escalations_per_check > 1000:
            raise ValidationLimitError(
                f"max_escalations_per_check must not exceed 1000, "
                f"got {self.max_escalations_per_check}",
                parameter="max_escalations_per_check",
                value=self.max_escalations_per_check,
            )

        # Validate retry_delay_seconds (1-3600)
        if self.retry_delay_seconds < 1:
            raise ValidationLimitError(
                f"retry_delay_seconds must be at least 1, "
                f"got {self.retry_delay_seconds}",
                parameter="retry_delay_seconds",
                value=self.retry_delay_seconds,
            )
        if self.retry_delay_seconds > 3600:
            raise ValidationLimitError(
                f"retry_delay_seconds must not exceed 3600, "
                f"got {self.retry_delay_seconds}",
                parameter="retry_delay_seconds",
                value=self.retry_delay_seconds,
            )

        # Validate max_retries (0-10)
        if self.max_retries < 0:
            raise ValidationLimitError(
                f"max_retries must be non-negative, "
                f"got {self.max_retries}",
                parameter="max_retries",
                value=self.max_retries,
            )
        if self.max_retries > 10:
            raise ValidationLimitError(
                f"max_retries must not exceed 10, "
                f"got {self.max_retries}",
                parameter="max_retries",
                value=self.max_retries,
            )

        # Validate misfire_grace_time (1-3600)
        if self.misfire_grace_time < 1:
            raise ValidationLimitError(
                f"misfire_grace_time must be at least 1, "
                f"got {self.misfire_grace_time}",
                parameter="misfire_grace_time",
                value=self.misfire_grace_time,
            )
        if self.misfire_grace_time > 3600:
            raise ValidationLimitError(
                f"misfire_grace_time must not exceed 3600, "
                f"got {self.misfire_grace_time}",
                parameter="misfire_grace_time",
                value=self.misfire_grace_time,
            )

        # Validate shutdown_timeout (1-300)
        if self.shutdown_timeout < 1:
            raise ValidationLimitError(
                f"shutdown_timeout must be at least 1, "
                f"got {self.shutdown_timeout}",
                parameter="shutdown_timeout",
                value=self.shutdown_timeout,
            )
        if self.shutdown_timeout > 300:
            raise ValidationLimitError(
                f"shutdown_timeout must not exceed 300, "
                f"got {self.shutdown_timeout}",
                parameter="shutdown_timeout",
                value=self.shutdown_timeout,
            )

    @classmethod
    def from_env(cls) -> EscalationSchedulerConfig:
        """Create configuration from environment variables with validation.

        Environment variables:
            TRUTHOUND_ESCALATION_CHECK_INTERVAL: Check interval in seconds
            TRUTHOUND_ESCALATION_MAX_PER_CHECK: Max escalations per check
            TRUTHOUND_ESCALATION_ENABLED: Enable/disable scheduler (true/false)
            TRUTHOUND_ESCALATION_BACKEND: Backend type (memory, sqlalchemy)
            TRUTHOUND_ESCALATION_MISFIRE_GRACE: Misfire grace time in seconds
            TRUTHOUND_ESCALATION_COALESCE: Enable job coalescing (true/false)
            TRUTHOUND_ESCALATION_MAX_RETRIES: Maximum retry attempts

        Raises:
            ValidationLimitError: If any configuration value is invalid.
        """
        return cls(
            check_interval_seconds=int(
                os.getenv("TRUTHOUND_ESCALATION_CHECK_INTERVAL", "60")
            ),
            max_escalations_per_check=int(
                os.getenv("TRUTHOUND_ESCALATION_MAX_PER_CHECK", "100")
            ),
            enabled=os.getenv("TRUTHOUND_ESCALATION_ENABLED", "true").lower() == "true",
            backend_type=BackendType(
                os.getenv("TRUTHOUND_ESCALATION_BACKEND", "sqlalchemy")
            ),
            misfire_grace_time=int(
                os.getenv("TRUTHOUND_ESCALATION_MISFIRE_GRACE", "60")
            ),
            coalesce=os.getenv("TRUTHOUND_ESCALATION_COALESCE", "true").lower() == "true",
            max_retries=int(os.getenv("TRUTHOUND_ESCALATION_MAX_RETRIES", "3")),
            shutdown_timeout=float(
                os.getenv("TRUTHOUND_ESCALATION_SHUTDOWN_TIMEOUT", "30")
            ),
        )


# =============================================================================
# Abstract Escalation Handler
# =============================================================================


class EscalationHandler(ABC):
    """Abstract base class for escalation handlers.

    Implement this class to define custom escalation behavior.
    Handlers are called when an incident needs to be escalated.

    Example:
        class SlackEscalationHandler(EscalationHandler):
            def __init__(self, webhook_url: str):
                self.webhook_url = webhook_url

            @property
            def handler_type(self) -> str:
                return "slack"

            async def handle_escalation(
                self,
                incident: EscalationIncidentModel,
                policy: EscalationPolicyModel,
                level: int,
                targets: list[dict],
            ) -> EscalationResult:
                # Send Slack notification
                ...
                return EscalationResult(success=True, message="Sent to Slack")

            async def can_handle(self, channel_type: str) -> bool:
                return channel_type == "slack"
    """

    @property
    @abstractmethod
    def handler_type(self) -> str:
        """Return the handler type identifier."""
        ...

    @abstractmethod
    async def handle_escalation(
        self,
        incident: EscalationIncidentModel,
        policy: EscalationPolicyModel,
        level: int,
        targets: list[dict[str, Any]],
    ) -> "EscalationResult":
        """Handle an escalation event.

        Args:
            incident: The escalation incident.
            policy: The escalation policy.
            level: The new escalation level.
            targets: List of target configurations for this level.

        Returns:
            EscalationResult indicating success or failure.
        """
        ...

    @abstractmethod
    async def can_handle(self, channel_type: str) -> bool:
        """Check if this handler can handle the given channel type.

        Args:
            channel_type: The notification channel type.

        Returns:
            True if this handler can handle the channel type.
        """
        ...


@dataclass
class EscalationResult:
    """Result of an escalation attempt.

    Attributes:
        success: Whether the escalation succeeded.
        message: Status message.
        notifications_sent: Number of notifications sent.
        metadata: Additional result data.
    """

    success: bool
    message: str = ""
    notifications_sent: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Built-in Handlers
# =============================================================================


class DefaultEscalationHandler(EscalationHandler):
    """Default escalation handler using the notification dispatcher.

    This handler uses the existing notification system to send
    escalation notifications through configured channels.
    """

    @property
    def handler_type(self) -> str:
        return "default"

    async def handle_escalation(
        self,
        incident: EscalationIncidentModel,
        policy: EscalationPolicyModel,
        level: int,
        targets: list[dict[str, Any]],
    ) -> EscalationResult:
        """Send escalation notifications via dispatcher."""
        notifications_sent = 0
        errors: list[str] = []

        async with get_session() as session:
            dispatcher = create_dispatcher(session)

            for target in targets:
                try:
                    channel_type = target.get("channel", "email")
                    channel_id = target.get("channel_id")
                    identifier = target.get("identifier", "")
                    target_type = target.get("type", "user")

                    # Build notification message
                    message = self._build_escalation_message(
                        incident=incident,
                        policy=policy,
                        level=level,
                        target=target,
                    )

                    # Use dispatcher to send notification
                    # Note: This uses the existing notification infrastructure
                    results = await dispatcher.dispatch(
                        channel_ids=[channel_id] if channel_id else None,
                        subject=f"[ESCALATION L{level}] {incident.incident_ref}",
                        message=message,
                        metadata={
                            "escalation": True,
                            "incident_id": incident.id,
                            "policy_id": policy.id,
                            "level": level,
                            "target_type": target_type,
                            "target_identifier": identifier,
                        },
                    )

                    for result in results:
                        if result.success:
                            notifications_sent += 1
                        else:
                            errors.append(f"Failed to notify {identifier}: {result.error_message}")

                except Exception as e:
                    errors.append(f"Error notifying target: {e}")
                    logger.error(f"Escalation notification error: {e}")

            await session.commit()

        success = notifications_sent > 0 or len(targets) == 0
        message = f"Sent {notifications_sent} notifications"
        if errors:
            message += f"; Errors: {'; '.join(errors[:3])}"

        return EscalationResult(
            success=success,
            message=message,
            notifications_sent=notifications_sent,
            metadata={"errors": errors},
        )

    async def can_handle(self, channel_type: str) -> bool:
        """Default handler can handle any channel type."""
        return True

    def _build_escalation_message(
        self,
        incident: EscalationIncidentModel,
        policy: EscalationPolicyModel,
        level: int,
        target: dict[str, Any],
    ) -> str:
        """Build escalation notification message."""
        context = incident.context or {}

        message_parts = [
            f"ESCALATION ALERT - Level {level}",
            "",
            f"Incident: {incident.incident_ref}",
            f"Policy: {policy.name}",
            f"State: {incident.state}",
            f"Escalation Count: {incident.escalation_count}",
            "",
        ]

        if context:
            message_parts.append("Context:")
            for key, value in context.items():
                message_parts.append(f"  {key}: {value}")
            message_parts.append("")

        message_parts.extend([
            f"Created: {incident.created_at.isoformat()}",
            f"Target: {target.get('identifier', 'N/A')} ({target.get('type', 'N/A')})",
        ])

        # Add custom message template if defined in policy level
        levels = policy.levels or []
        for level_config in levels:
            if level_config.get("level") == level:
                template = level_config.get("message_template")
                if template:
                    message_parts.extend(["", "---", template])
                break

        return "\n".join(message_parts)


class LoggingEscalationHandler(EscalationHandler):
    """Escalation handler that only logs escalations.

    Useful for testing and debugging.
    """

    @property
    def handler_type(self) -> str:
        return "logging"

    async def handle_escalation(
        self,
        incident: EscalationIncidentModel,
        policy: EscalationPolicyModel,
        level: int,
        targets: list[dict[str, Any]],
    ) -> EscalationResult:
        """Log the escalation."""
        logger.info(
            f"Escalation triggered: incident={incident.id}, "
            f"policy={policy.name}, level={level}, targets={len(targets)}"
        )
        for target in targets:
            logger.info(
                f"  Target: type={target.get('type')}, "
                f"identifier={target.get('identifier')}, "
                f"channel={target.get('channel')}"
            )

        return EscalationResult(
            success=True,
            message=f"Logged escalation to level {level}",
            notifications_sent=len(targets),
        )

    async def can_handle(self, channel_type: str) -> bool:
        """Logging handler can handle any channel type."""
        return True


# =============================================================================
# Escalation Strategy
# =============================================================================


class EscalationStrategy(ABC):
    """Abstract base class for escalation strategies.

    Strategies determine how and when escalations should proceed.
    """

    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Return the strategy name."""
        ...

    @abstractmethod
    async def should_escalate(
        self,
        incident: EscalationIncidentModel,
        policy: EscalationPolicyModel,
    ) -> bool:
        """Determine if an incident should be escalated.

        Args:
            incident: The escalation incident.
            policy: The escalation policy.

        Returns:
            True if escalation should proceed.
        """
        ...

    @abstractmethod
    async def get_next_level(
        self,
        incident: EscalationIncidentModel,
        policy: EscalationPolicyModel,
    ) -> int | None:
        """Get the next escalation level.

        Args:
            incident: The escalation incident.
            policy: The escalation policy.

        Returns:
            Next level number or None if no more levels.
        """
        ...


class TimeBasedEscalationStrategy(EscalationStrategy):
    """Time-based escalation strategy.

    Escalates when the scheduled escalation time has passed.
    This is the default strategy that respects `next_escalation_at`.
    """

    @property
    def strategy_name(self) -> str:
        return "time_based"

    async def should_escalate(
        self,
        incident: EscalationIncidentModel,
        policy: EscalationPolicyModel,
    ) -> bool:
        """Check if escalation time has passed."""
        if not incident.next_escalation_at:
            return False

        # Don't escalate resolved or acknowledged incidents
        if incident.state in (
            EscalationStateEnum.RESOLVED.value,
            EscalationStateEnum.ACKNOWLEDGED.value,
        ):
            return False

        return datetime.utcnow() >= incident.next_escalation_at

    async def get_next_level(
        self,
        incident: EscalationIncidentModel,
        policy: EscalationPolicyModel,
    ) -> int | None:
        """Get the next level based on current level."""
        current_level = incident.current_level
        levels = policy.levels or []

        # Find next level
        for level_config in levels:
            if level_config.get("level", 0) == current_level + 1:
                return current_level + 1

        return None


class ImmediateEscalationStrategy(EscalationStrategy):
    """Immediate escalation strategy.

    Always escalates immediately without waiting.
    Useful for critical incidents.
    """

    @property
    def strategy_name(self) -> str:
        return "immediate"

    async def should_escalate(
        self,
        incident: EscalationIncidentModel,
        policy: EscalationPolicyModel,
    ) -> bool:
        """Always return True for active incidents."""
        return incident.state not in (
            EscalationStateEnum.RESOLVED.value,
        )

    async def get_next_level(
        self,
        incident: EscalationIncidentModel,
        policy: EscalationPolicyModel,
    ) -> int | None:
        """Get the next level, skipping to max if needed."""
        current_level = incident.current_level
        max_level = max(
            (l.get("level", 0) for l in policy.levels or []),
            default=0,
        )

        if current_level < max_level:
            return current_level + 1
        return None


# =============================================================================
# Main Scheduler Service
# =============================================================================


class EscalationSchedulerService:
    """Service for scheduling automatic escalation checks.

    This service uses APScheduler with a configurable backend to
    periodically check for incidents that need escalation and
    processes them accordingly.

    Features:
    - Configurable check interval
    - Multiple handler support
    - Multiple strategy support
    - Metrics and status tracking
    - Thread-safe operations
    - **Persistent job storage (SQLAlchemy backend)**
    - **Automatic job recovery on restart**
    - **Configurable misfire handling**
    - **Exponential backoff for failures**
    - **Graceful shutdown with job persistence**

    Usage:
        service = EscalationSchedulerService()
        await service.start()

        # Later...
        await service.stop()
    """

    DEFAULT_JOB_ID = "escalation_checker"

    def __init__(
        self,
        config: EscalationSchedulerConfig | None = None,
        scheduler: AsyncIOScheduler | None = None,
        backend: SchedulerBackend | None = None,
    ) -> None:
        """Initialize the escalation scheduler service.

        Args:
            config: Service configuration.
            scheduler: Optional existing APScheduler instance.
            backend: Optional custom scheduler backend.
        """
        self.config = config or EscalationSchedulerConfig.from_env()
        self._scheduler = scheduler or AsyncIOScheduler()
        self._owns_scheduler = scheduler is None
        self._handlers: list[EscalationHandler] = []
        self._strategy: EscalationStrategy = TimeBasedEscalationStrategy()
        self._running = False
        self._last_check_at: datetime | None = None
        self._check_count = 0
        self._escalation_count = 0
        self._error_count = 0
        self._misfire_count = 0
        self._lock = asyncio.Lock()

        # Initialize backend
        if backend:
            self._backend = backend
        else:
            backend_config = SchedulerBackendConfig(
                backend_type=self.config.backend_type,
                misfire_grace_time=self.config.misfire_grace_time,
                coalesce=self.config.coalesce,
                max_retries=self.config.max_retries,
                shutdown_timeout=self.config.shutdown_timeout,
            )
            self._backend = create_scheduler_backend(backend_config)

        # Register default handler
        self.register_handler(DefaultEscalationHandler())

    @property
    def is_running(self) -> bool:
        """Check if the scheduler is running."""
        return self._running

    @property
    def backend(self) -> SchedulerBackend:
        """Get the scheduler backend."""
        return self._backend

    def register_handler(self, handler: EscalationHandler) -> None:
        """Register an escalation handler.

        Args:
            handler: The handler to register.
        """
        self._handlers.append(handler)
        logger.debug(f"Registered escalation handler: {handler.handler_type}")

    def unregister_handler(self, handler_type: str) -> bool:
        """Unregister an escalation handler by type.

        Args:
            handler_type: The handler type to unregister.

        Returns:
            True if handler was found and removed.
        """
        for handler in self._handlers[:]:
            if handler.handler_type == handler_type:
                self._handlers.remove(handler)
                logger.debug(f"Unregistered escalation handler: {handler_type}")
                return True
        return False

    def set_strategy(self, strategy: EscalationStrategy) -> None:
        """Set the escalation strategy.

        Args:
            strategy: The strategy to use.
        """
        self._strategy = strategy
        logger.debug(f"Set escalation strategy: {strategy.strategy_name}")

    async def start(self) -> None:
        """Start the escalation scheduler."""
        if self._running:
            logger.warning("Escalation scheduler already running")
            return

        if not self.config.enabled:
            logger.info("Escalation scheduler is disabled")
            return

        logger.info("Starting escalation scheduler")

        # Initialize backend
        await self._backend.initialize()
        logger.info(f"Using scheduler backend: {self._backend.backend_type.value}")

        # Register the checker job with backend for persistence
        job_data = JobData(
            id=self.DEFAULT_JOB_ID,
            name="Escalation Checker",
            func_ref="truthound_dashboard.core.notifications.escalation.scheduler:_check_and_escalate",
            trigger_type="interval",
            trigger_args={"seconds": self.config.check_interval_seconds},
            next_run_time=datetime.utcnow() + timedelta(
                seconds=self.config.check_interval_seconds
            ),
            state=JobState.PENDING,
        )

        try:
            # Check if job exists (recovery scenario)
            existing = await self._backend.get_job(self.DEFAULT_JOB_ID)
            if existing:
                logger.info("Recovered existing escalation checker job")
                # Update next_run_time if it was in the past
                if existing.next_run_time and existing.next_run_time < datetime.utcnow():
                    if self._backend.is_misfired(existing):
                        self._misfire_count += 1
                        logger.warning("Escalation checker job misfired, rescheduling")
                    existing.next_run_time = datetime.utcnow()
                    existing.state = JobState.PENDING
                    await self._backend.update_job(existing)
            else:
                await self._backend.add_job(job_data)
                logger.debug("Created escalation checker job")
        except ValueError:
            # Job already exists
            logger.debug("Escalation checker job already registered")

        # Schedule the checker job with APScheduler
        self._scheduler.add_job(
            self._check_and_escalate,
            trigger=IntervalTrigger(seconds=self.config.check_interval_seconds),
            id=self.DEFAULT_JOB_ID,
            name="Escalation Checker",
            replace_existing=True,
            misfire_grace_time=self.config.misfire_grace_time,
            coalesce=self.config.coalesce,
        )

        # Start scheduler if we own it
        if self._owns_scheduler and not self._scheduler.running:
            self._scheduler.start()

        self._running = True
        logger.info(
            f"Escalation scheduler started "
            f"(interval: {self.config.check_interval_seconds}s, "
            f"backend: {self._backend.backend_type.value})"
        )

    async def stop(self) -> None:
        """Stop the escalation scheduler gracefully."""
        if not self._running:
            return

        logger.info("Stopping escalation scheduler")

        try:
            self._scheduler.remove_job(self.DEFAULT_JOB_ID)
        except Exception:
            pass  # Job may not exist

        # Shutdown scheduler if we own it
        if self._owns_scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=False)

        # Shutdown backend (handles pending job persistence)
        await self._backend.shutdown()

        self._running = False
        logger.info("Escalation scheduler stopped")

    async def _check_and_escalate(self) -> None:
        """Check for and process pending escalations.

        This is the main job that runs periodically.
        """
        async with self._lock:
            self._last_check_at = datetime.utcnow()
            self._check_count += 1

            logger.debug(f"Checking for pending escalations (check #{self._check_count})")

            # Mark job as running in backend
            await self._backend.mark_job_running(self.DEFAULT_JOB_ID)

            try:
                async with get_session() as session:
                    from sqlalchemy import select

                    # Get pending escalations
                    now = datetime.utcnow()
                    query = (
                        select(EscalationIncidentModel)
                        .where(
                            EscalationIncidentModel.state.in_([
                                EscalationStateEnum.TRIGGERED.value,
                                EscalationStateEnum.ESCALATED.value,
                            ])
                        )
                        .where(EscalationIncidentModel.next_escalation_at <= now)
                        .limit(self.config.max_escalations_per_check)
                    )

                    result = await session.execute(query)
                    incidents = result.scalars().all()

                    if not incidents:
                        logger.debug("No pending escalations found")
                    else:
                        logger.info(f"Found {len(incidents)} incidents due for escalation")

                        for incident in incidents:
                            await self._process_incident(session, incident)

                    await session.commit()

                # Mark job as completed with next run time
                next_run = datetime.utcnow() + timedelta(
                    seconds=self.config.check_interval_seconds
                )
                await self._backend.mark_job_completed(self.DEFAULT_JOB_ID, next_run)

            except Exception as e:
                self._error_count += 1
                logger.error(f"Error checking escalations: {e}")
                # Mark job as failed (will retry with exponential backoff)
                await self._backend.mark_job_failed(
                    self.DEFAULT_JOB_ID,
                    str(e),
                    schedule_retry=self.config.retry_on_failure,
                )

    async def _process_incident(
        self,
        session: Any,
        incident: EscalationIncidentModel,
    ) -> None:
        """Process a single incident for escalation.

        Args:
            session: Database session.
            incident: The incident to process.
        """
        try:
            # Get the policy
            from sqlalchemy import select

            result = await session.execute(
                select(EscalationPolicyModel)
                .where(EscalationPolicyModel.id == incident.policy_id)
            )
            policy = result.scalar_one_or_none()

            if not policy:
                logger.error(f"Policy not found for incident {incident.id}")
                return

            if not policy.is_active:
                logger.debug(f"Policy {policy.id} is inactive, skipping")
                return

            # Check escalation strategy
            if not await self._strategy.should_escalate(incident, policy):
                logger.debug(f"Strategy says don't escalate incident {incident.id}")
                return

            # Get next level
            next_level = await self._strategy.get_next_level(incident, policy)
            if next_level is None:
                logger.debug(f"No more levels for incident {incident.id}")
                # Clear next_escalation_at since we're at max level
                incident.next_escalation_at = None
                return

            # Check if escalation is allowed using model method
            if not incident.can_escalate(policy.max_escalations):
                logger.warning(
                    f"Incident {incident.id} cannot escalate: "
                    f"count={incident.escalation_count}, max={policy.max_escalations}, "
                    f"state={incident.state}"
                )
                incident.next_escalation_at = None
                return

            # Get targets for the next level
            targets = self._get_level_targets(policy, next_level)
            if not targets:
                logger.warning(f"No targets for level {next_level} in policy {policy.id}")

            # Execute escalation through handlers
            await self._execute_escalation(incident, policy, next_level, targets)

            # Calculate next escalation time
            further_level = self._get_level_config(policy, next_level + 1)
            next_escalation_at: datetime | None = None
            if further_level:
                delay_minutes = further_level.get("delay_minutes", 15)
                next_escalation_at = datetime.utcnow() + timedelta(minutes=delay_minutes)

            # Use model's escalate method for atomic state update
            if not incident.escalate(
                next_level=next_level,
                next_escalation_at=next_escalation_at,
                max_escalations=policy.max_escalations,
            ):
                logger.warning(f"Escalation blocked for incident {incident.id}")
                return

            self._escalation_count += 1
            logger.info(
                f"Escalated incident {incident.id} to level {next_level}"
            )

        except Exception as e:
            self._error_count += 1
            logger.error(f"Error processing incident {incident.id}: {e}")

    async def _execute_escalation(
        self,
        incident: EscalationIncidentModel,
        policy: EscalationPolicyModel,
        level: int,
        targets: list[dict[str, Any]],
    ) -> None:
        """Execute escalation through registered handlers.

        Args:
            incident: The incident being escalated.
            policy: The escalation policy.
            level: The new level.
            targets: Targets for this level.
        """
        for handler in self._handlers:
            try:
                # Group targets by channel type
                for target in targets:
                    channel_type = target.get("channel", "email")
                    if await handler.can_handle(channel_type):
                        result = await handler.handle_escalation(
                            incident=incident,
                            policy=policy,
                            level=level,
                            targets=[target],
                        )
                        if not result.success:
                            logger.warning(
                                f"Handler {handler.handler_type} failed: {result.message}"
                            )
                        break  # Only use first matching handler

            except Exception as e:
                logger.error(
                    f"Handler {handler.handler_type} error: {e}"
                )

    def _get_level_targets(
        self,
        policy: EscalationPolicyModel,
        level: int,
    ) -> list[dict[str, Any]]:
        """Get targets for a specific escalation level.

        Args:
            policy: The escalation policy.
            level: The level number.

        Returns:
            List of target configurations.
        """
        level_config = self._get_level_config(policy, level)
        if not level_config:
            return []
        return level_config.get("targets", [])

    def _get_level_config(
        self,
        policy: EscalationPolicyModel,
        level: int,
    ) -> dict[str, Any] | None:
        """Get configuration for a specific level.

        Args:
            policy: The escalation policy.
            level: The level number.

        Returns:
            Level configuration or None.
        """
        for level_config in policy.levels or []:
            if level_config.get("level") == level:
                return level_config
        return None

    async def trigger_immediate_check(self) -> dict[str, Any]:
        """Trigger an immediate escalation check.

        Returns:
            Check result including number of escalations processed.
        """
        if not self._running:
            return {
                "success": False,
                "message": "Scheduler is not running",
            }

        escalations_before = self._escalation_count
        await self._check_and_escalate()
        escalations_processed = self._escalation_count - escalations_before

        return {
            "success": True,
            "message": f"Processed {escalations_processed} escalations",
            "escalations_processed": escalations_processed,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_status(self) -> dict[str, Any]:
        """Get current scheduler status.

        Returns:
            Status dictionary with metrics.
        """
        next_run: datetime | None = None
        if self._running:
            try:
                job = self._scheduler.get_job(self.DEFAULT_JOB_ID)
                if job:
                    next_run = job.next_run_time
            except Exception:
                pass

        backend_status = self._backend.get_status()

        return {
            "running": self._running,
            "enabled": self.config.enabled,
            "check_interval_seconds": self.config.check_interval_seconds,
            "last_check_at": self._last_check_at.isoformat() if self._last_check_at else None,
            "next_check_at": next_run.isoformat() if next_run else None,
            "check_count": self._check_count,
            "escalation_count": self._escalation_count,
            "error_count": self._error_count,
            "misfire_count": self._misfire_count,
            "handlers": [h.handler_type for h in self._handlers],
            "strategy": self._strategy.strategy_name,
            "backend": backend_status,
        }

    def reset_metrics(self) -> None:
        """Reset scheduler metrics."""
        self._check_count = 0
        self._escalation_count = 0
        self._error_count = 0
        self._misfire_count = 0


# =============================================================================
# Singleton Instance Management
# =============================================================================

_scheduler_service: EscalationSchedulerService | None = None


def get_escalation_scheduler(
    config: EscalationSchedulerConfig | None = None,
) -> EscalationSchedulerService:
    """Get the singleton escalation scheduler instance.

    Args:
        config: Optional configuration (only used on first call).

    Returns:
        The EscalationSchedulerService instance.
    """
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = EscalationSchedulerService(config=config)
    return _scheduler_service


def reset_escalation_scheduler() -> None:
    """Reset the singleton scheduler instance.

    Useful for testing or reconfiguration.
    """
    global _scheduler_service
    _scheduler_service = None


async def start_escalation_scheduler() -> None:
    """Start the escalation scheduler."""
    scheduler = get_escalation_scheduler()
    await scheduler.start()


async def stop_escalation_scheduler() -> None:
    """Stop the escalation scheduler."""
    scheduler = get_escalation_scheduler()
    await scheduler.stop()
