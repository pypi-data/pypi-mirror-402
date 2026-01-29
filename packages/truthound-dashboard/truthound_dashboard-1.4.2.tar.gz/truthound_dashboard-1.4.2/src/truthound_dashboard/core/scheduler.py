"""Validation scheduler with notification integration and maintenance.

This module provides scheduled validation execution with automatic
notification dispatch on failures, plus scheduled database maintenance.

The scheduler:
1. Runs scheduled validations based on flexible trigger types
2. Supports cron, interval, data change, composite, event, and webhook triggers
3. Triggers notifications on validation failures
4. Updates schedule run timestamps
5. Runs periodic database maintenance (cleanup, vacuum)
6. Provides per-schedule check intervals and priority-based evaluation
7. Supports webhook triggers from external data pipelines
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from truthound_dashboard.db import Schedule, Source, TriggerType, get_session

from .maintenance import get_maintenance_manager
from .notifications.dispatcher import create_dispatcher
from .services import ValidationService
from .truthound_adapter import get_adapter
from .triggers import TriggerFactory, TriggerContext, TriggerEvaluation

logger = logging.getLogger(__name__)


class ValidationScheduler:
    """Scheduler for automated validation runs with notifications.

    Manages scheduled validation jobs using APScheduler and integrates
    with the notification system to alert on failures.

    Supports multiple trigger types:
    - Cron: Traditional cron expressions
    - Interval: Fixed time intervals
    - DataChange: Profile-based change detection
    - Composite: Combined triggers with AND/OR logic
    - Event: Response to system events
    - Manual: API-only execution
    - Webhook: External webhook triggers

    Also manages scheduled database maintenance tasks.

    Features:
    - Per-schedule check intervals (overrides global default)
    - Priority-based trigger evaluation (1=highest, 10=lowest)
    - Cooldown support to prevent rapid re-triggering
    - Trigger monitoring and status tracking

    Usage:
        scheduler = ValidationScheduler()
        await scheduler.start()
        # ... on shutdown ...
        await scheduler.stop()
    """

    # Default maintenance schedule: daily at 3:00 AM
    DEFAULT_MAINTENANCE_CRON = "0 3 * * *"
    # Alternative: run maintenance every 24 hours
    MAINTENANCE_INTERVAL_HOURS = 24
    # Data change trigger check interval (base interval for checker loop)
    DATA_CHANGE_CHECK_INTERVAL_SECONDS = 60  # 1 minute (reduced for better responsiveness)
    # Default per-schedule check interval
    DEFAULT_SCHEDULE_CHECK_INTERVAL_MINUTES = 5

    def __init__(
        self,
        *,
        maintenance_enabled: bool = True,
        maintenance_cron: str | None = None,
        data_change_check_interval: int | None = None,
    ) -> None:
        """Initialize the scheduler.

        Args:
            maintenance_enabled: Whether to enable scheduled maintenance.
            maintenance_cron: Cron expression for maintenance schedule.
                Defaults to daily at 3:00 AM.
            data_change_check_interval: Interval in seconds for the checker loop.
                Individual schedules can have their own check intervals.
        """
        self._scheduler = AsyncIOScheduler()
        self._jobs: dict[str, str] = {}  # schedule_id -> job_id mapping
        self._maintenance_enabled = maintenance_enabled
        self._maintenance_cron = maintenance_cron or self.DEFAULT_MAINTENANCE_CRON
        self._maintenance_job_id = "system_maintenance"
        self._data_change_job_id = "data_change_check"
        self._data_change_check_interval = (
            data_change_check_interval or self.DATA_CHANGE_CHECK_INTERVAL_SECONDS
        )

        # Trigger monitoring state
        self._trigger_check_times: dict[str, datetime] = {}  # schedule_id -> last_check_at
        self._trigger_trigger_times: dict[str, datetime] = {}  # schedule_id -> last_triggered_at
        self._trigger_check_counts: dict[str, int] = {}  # schedule_id -> check_count
        self._trigger_trigger_counts: dict[str, int] = {}  # schedule_id -> trigger_count
        self._last_checker_run: datetime | None = None
        self._checker_running = False

    async def start(self) -> None:
        """Start the scheduler and load existing schedules."""
        logger.info("Starting validation scheduler")
        self._scheduler.start()
        await self._load_schedules()

        # Start maintenance schedule if enabled
        if self._maintenance_enabled:
            self._schedule_maintenance()

        # Start data change trigger checker
        self._schedule_data_change_checker()

    async def stop(self) -> None:
        """Stop the scheduler."""
        logger.info("Stopping validation scheduler")
        self._scheduler.shutdown(wait=False)

    def _schedule_maintenance(self) -> None:
        """Schedule periodic database maintenance."""
        try:
            trigger = CronTrigger.from_crontab(self._maintenance_cron)
            self._scheduler.add_job(
                self._run_maintenance,
                trigger=trigger,
                id=self._maintenance_job_id,
                name="Database Maintenance",
                replace_existing=True,
            )
            logger.info(
                f"Scheduled database maintenance: {self._maintenance_cron}"
            )
        except Exception as e:
            logger.error(f"Failed to schedule maintenance: {e}")

    def enable_maintenance(self, cron: str | None = None) -> None:
        """Enable scheduled maintenance.

        Args:
            cron: Optional cron expression override.
        """
        self._maintenance_enabled = True
        if cron:
            self._maintenance_cron = cron
        self._schedule_maintenance()

    def disable_maintenance(self) -> None:
        """Disable scheduled maintenance."""
        self._maintenance_enabled = False
        try:
            self._scheduler.remove_job(self._maintenance_job_id)
            logger.info("Disabled scheduled maintenance")
        except Exception:
            pass  # Job may not exist

    def get_maintenance_next_run(self) -> datetime | None:
        """Get next scheduled maintenance run time.

        Returns:
            Next run datetime or None if disabled.
        """
        if not self._maintenance_enabled:
            return None
        try:
            job = self._scheduler.get_job(self._maintenance_job_id)
            if job:
                return job.next_run_time
        except Exception:
            pass
        return None

    async def _run_maintenance(self) -> None:
        """Execute scheduled database maintenance."""
        logger.info("Running scheduled database maintenance")

        manager = get_maintenance_manager()

        if not manager.config.enabled:
            logger.info("Maintenance is disabled in configuration")
            return

        try:
            report = await manager.run_cleanup()

            logger.info(
                f"Maintenance completed: {report.total_deleted} records deleted "
                f"in {report.total_duration_ms}ms "
                f"(vacuum: {report.vacuum_performed})"
            )

            if not report.success:
                failed_tasks = [r.task_name for r in report.results if not r.success]
                logger.warning(f"Some maintenance tasks failed: {failed_tasks}")

        except Exception as e:
            logger.error(f"Maintenance failed: {e}")

    async def _load_schedules(self) -> None:
        """Load active schedules from database."""
        async with get_session() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(Schedule).where(Schedule.is_active == True)
            )
            schedules = result.scalars().all()

            for schedule in schedules:
                self.add_schedule(schedule)

    def add_schedule(self, schedule: Schedule) -> None:
        """Add a schedule to the scheduler.

        Supports multiple trigger types:
        - Cron/Interval: Traditional APScheduler triggers
        - DataChange/Composite/Event: Evaluated by periodic checker

        Args:
            schedule: Schedule model to add.
        """
        if schedule.id in self._jobs:
            self.remove_schedule(schedule.id)

        trigger_type = schedule.effective_trigger_type

        # Manual and event triggers don't need APScheduler jobs
        if trigger_type in (TriggerType.MANUAL, TriggerType.EVENT):
            logger.info(
                f"Schedule {schedule.name} uses {trigger_type.value} trigger - "
                "no APScheduler job needed"
            )
            return

        # Data change and composite triggers are handled by periodic checker
        if trigger_type in (TriggerType.DATA_CHANGE, TriggerType.COMPOSITE):
            logger.info(
                f"Schedule {schedule.name} uses {trigger_type.value} trigger - "
                "will be checked periodically"
            )
            return

        try:
            # Create APScheduler trigger based on type
            if trigger_type == TriggerType.CRON:
                cron_expr = schedule.effective_cron_expression
                if not cron_expr:
                    logger.error(f"Cron schedule {schedule.id} missing expression")
                    return
                ap_trigger = CronTrigger.from_crontab(cron_expr)
                trigger_desc = cron_expr

            elif trigger_type == TriggerType.INTERVAL:
                config = schedule.trigger_config or {}
                seconds = config.get("seconds", 0)
                minutes = config.get("minutes", 0)
                hours = config.get("hours", 0)
                days = config.get("days", 0)

                total_seconds = seconds + minutes * 60 + hours * 3600 + days * 86400
                if total_seconds <= 0:
                    total_seconds = 3600  # Default to 1 hour

                ap_trigger = IntervalTrigger(seconds=total_seconds)
                trigger_desc = f"every {total_seconds}s"

            else:
                # Fallback for unknown types - try as cron
                cron_expr = schedule.cron_expression or "0 0 * * *"
                ap_trigger = CronTrigger.from_crontab(cron_expr)
                trigger_desc = cron_expr

            job = self._scheduler.add_job(
                self._run_validation,
                trigger=ap_trigger,
                args=[schedule.id],
                id=f"schedule_{schedule.id}",
                name=f"Validation: {schedule.name}",
                replace_existing=True,
            )
            self._jobs[schedule.id] = job.id
            logger.info(f"Added schedule: {schedule.name} ({trigger_desc})")

        except Exception as e:
            logger.error(f"Failed to add schedule {schedule.id}: {e}")

    def remove_schedule(self, schedule_id: str) -> None:
        """Remove a schedule from the scheduler.

        Args:
            schedule_id: Schedule ID to remove.
        """
        job_id = self._jobs.pop(schedule_id, None)
        if job_id:
            try:
                self._scheduler.remove_job(job_id)
                logger.info(f"Removed schedule: {schedule_id}")
            except Exception as e:
                logger.error(f"Failed to remove schedule {schedule_id}: {e}")

    def update_schedule(self, schedule: Schedule) -> None:
        """Update a schedule in the scheduler.

        Args:
            schedule: Updated schedule model.
        """
        if schedule.is_active:
            self.add_schedule(schedule)
        else:
            self.remove_schedule(schedule.id)

    async def _run_validation(self, schedule_id: str) -> None:
        """Execute a scheduled validation.

        Args:
            schedule_id: ID of the schedule to run.
        """
        logger.info(f"Running scheduled validation: {schedule_id}")

        async with get_session() as session:
            from sqlalchemy import select

            # Get schedule
            result = await session.execute(
                select(Schedule).where(Schedule.id == schedule_id)
            )
            schedule = result.scalar_one_or_none()

            if schedule is None:
                logger.error(f"Schedule not found: {schedule_id}")
                return

            if not schedule.is_active:
                logger.info(f"Schedule is inactive: {schedule_id}")
                return

            # Get source
            result = await session.execute(
                select(Source).where(Source.id == schedule.source_id)
            )
            source = result.scalar_one_or_none()

            if source is None:
                logger.error(f"Source not found for schedule: {schedule_id}")
                return

            # Run validation
            validation_service = ValidationService(session)
            config = schedule.config or {}

            try:
                validation = await validation_service.run_validation(
                    schedule.source_id,
                    validators=config.get("validators"),
                    schema_path=config.get("schema_path"),
                    auto_schema=config.get("auto_schema", False),
                )

                # Update schedule run time
                schedule.mark_run(self._get_next_run(schedule.cron_expression))
                await session.commit()

                logger.info(
                    f"Validation completed for schedule {schedule_id}: "
                    f"passed={validation.passed}"
                )

                # Send notifications if failed and notifications are enabled
                if schedule.notify_on_failure and not validation.passed:
                    await self._send_failure_notification(
                        session=session,
                        source=source,
                        schedule=schedule,
                        validation=validation,
                    )

            except Exception as e:
                logger.error(f"Validation failed for schedule {schedule_id}: {e}")

                # Send error notification
                if schedule.notify_on_failure:
                    await self._send_error_notification(
                        session=session,
                        source=source,
                        schedule=schedule,
                        error_message=str(e),
                    )

    async def _send_failure_notification(
        self,
        session: Any,
        source: Source,
        schedule: Schedule,
        validation: Any,
    ) -> None:
        """Send notification for validation failure.

        Args:
            session: Database session.
            source: Source that was validated.
            schedule: Schedule that triggered the validation.
            validation: Validation result.
        """
        dispatcher = create_dispatcher(session)

        try:
            results = await dispatcher.notify_schedule_failed(
                source_id=source.id,
                source_name=source.name,
                schedule_id=schedule.id,
                schedule_name=schedule.name,
                validation_id=validation.id,
                error_message=f"Validation failed with {validation.total_issues or 0} issues",
            )
            await session.commit()

            success_count = sum(1 for r in results if r.success)
            logger.info(
                f"Sent {success_count}/{len(results)} failure notifications "
                f"for schedule {schedule.id}"
            )
        except Exception as e:
            logger.error(f"Failed to send notifications: {e}")

    async def _send_error_notification(
        self,
        session: Any,
        source: Source,
        schedule: Schedule,
        error_message: str,
    ) -> None:
        """Send notification for validation error.

        Args:
            session: Database session.
            source: Source that was validated.
            schedule: Schedule that triggered the validation.
            error_message: Error message.
        """
        dispatcher = create_dispatcher(session)

        try:
            results = await dispatcher.notify_schedule_failed(
                source_id=source.id,
                source_name=source.name,
                schedule_id=schedule.id,
                schedule_name=schedule.name,
                error_message=error_message,
            )
            await session.commit()

            success_count = sum(1 for r in results if r.success)
            logger.info(
                f"Sent {success_count}/{len(results)} error notifications "
                f"for schedule {schedule.id}"
            )
        except Exception as e:
            logger.error(f"Failed to send error notifications: {e}")

    def _get_next_run(self, cron_expression: str) -> datetime | None:
        """Calculate next run time from cron expression.

        Args:
            cron_expression: Cron expression.

        Returns:
            Next run datetime or None if invalid.
        """
        try:
            trigger = CronTrigger.from_crontab(cron_expression)
            return trigger.get_next_fire_time(None, datetime.utcnow())
        except Exception:
            return None

    def _schedule_data_change_checker(self) -> None:
        """Schedule periodic checker for data change and composite triggers."""
        try:
            self._scheduler.add_job(
                self._check_data_change_triggers,
                trigger=IntervalTrigger(seconds=self._data_change_check_interval),
                id=self._data_change_job_id,
                name="Data Change Trigger Checker",
                replace_existing=True,
            )
            logger.info(
                f"Scheduled data change checker: every {self._data_change_check_interval}s"
            )
        except Exception as e:
            logger.error(f"Failed to schedule data change checker: {e}")

    async def _check_data_change_triggers(self) -> None:
        """Check all data change and composite triggers.

        This runs periodically to evaluate triggers that can't be
        handled by APScheduler's built-in triggers.

        Features:
        - Per-schedule check intervals (respects check_interval_minutes)
        - Priority-based evaluation (lower priority number = higher priority)
        - Cooldown support (prevents rapid re-triggering)
        """
        self._checker_running = True
        self._last_checker_run = datetime.utcnow()
        logger.debug("Checking data change triggers")

        try:
            async with get_session() as session:
                from sqlalchemy import select

                # Get schedules with data change or composite triggers
                result = await session.execute(
                    select(Schedule)
                    .where(Schedule.is_active == True)
                    .where(
                        Schedule.trigger_type.in_([
                            TriggerType.DATA_CHANGE.value,
                            TriggerType.COMPOSITE.value,
                        ])
                    )
                )
                schedules = result.scalars().all()

                if not schedules:
                    logger.debug("No data change/composite schedules to check")
                    return

                # Filter schedules that are due for checking
                now = datetime.utcnow()
                schedules_to_check = []

                for schedule in schedules:
                    if self._is_schedule_due_for_check(schedule, now):
                        schedules_to_check.append(schedule)

                if not schedules_to_check:
                    logger.debug("No schedules due for check")
                    return

                # Sort by priority (lower number = higher priority)
                schedules_to_check.sort(
                    key=lambda s: self._get_schedule_priority(s)
                )

                logger.info(
                    f"Checking {len(schedules_to_check)}/{len(schedules)} "
                    "data change/composite schedules (sorted by priority)"
                )

                for schedule in schedules_to_check:
                    await self._evaluate_and_run_if_needed(session, schedule)
        finally:
            self._checker_running = False

    def _is_schedule_due_for_check(self, schedule: Schedule, now: datetime) -> bool:
        """Check if a schedule is due for evaluation.

        Args:
            schedule: Schedule to check.
            now: Current timestamp.

        Returns:
            True if schedule should be checked.
        """
        schedule_id = schedule.id
        last_check = self._trigger_check_times.get(schedule_id)

        # First check - always due
        if last_check is None:
            return True

        # Get per-schedule check interval
        config = schedule.trigger_config or {}
        check_interval_minutes = config.get(
            "check_interval_minutes",
            self.DEFAULT_SCHEDULE_CHECK_INTERVAL_MINUTES
        )

        # Calculate if due
        next_check = last_check + timedelta(minutes=check_interval_minutes)
        return now >= next_check

    def _get_schedule_priority(self, schedule: Schedule) -> int:
        """Get priority for a schedule (lower = higher priority).

        Args:
            schedule: Schedule to get priority for.

        Returns:
            Priority value (1-10, default 5).
        """
        config = schedule.trigger_config or {}
        return config.get("priority", 5)

    def _is_in_cooldown(self, schedule: Schedule, now: datetime) -> bool:
        """Check if schedule is in cooldown period.

        Args:
            schedule: Schedule to check.
            now: Current timestamp.

        Returns:
            True if in cooldown.
        """
        schedule_id = schedule.id
        last_triggered = self._trigger_trigger_times.get(schedule_id)

        if last_triggered is None:
            return False

        config = schedule.trigger_config or {}
        cooldown_minutes = config.get("cooldown_minutes", 15)

        if cooldown_minutes <= 0:
            return False

        cooldown_end = last_triggered + timedelta(minutes=cooldown_minutes)
        return now < cooldown_end

    def _get_cooldown_remaining(self, schedule: Schedule, now: datetime) -> int:
        """Get remaining cooldown time in seconds.

        Args:
            schedule: Schedule to check.
            now: Current timestamp.

        Returns:
            Remaining cooldown seconds (0 if not in cooldown).
        """
        schedule_id = schedule.id
        last_triggered = self._trigger_trigger_times.get(schedule_id)

        if last_triggered is None:
            return 0

        config = schedule.trigger_config or {}
        cooldown_minutes = config.get("cooldown_minutes", 15)

        if cooldown_minutes <= 0:
            return 0

        cooldown_end = last_triggered + timedelta(minutes=cooldown_minutes)
        remaining = (cooldown_end - now).total_seconds()
        return max(0, int(remaining))

    async def _evaluate_and_run_if_needed(
        self, session: Any, schedule: Schedule
    ) -> None:
        """Evaluate a schedule's trigger and run validation if needed.

        Args:
            session: Database session.
            schedule: Schedule to evaluate.
        """
        schedule_id = schedule.id
        now = datetime.utcnow()

        # Update check tracking
        self._trigger_check_times[schedule_id] = now
        self._trigger_check_counts[schedule_id] = (
            self._trigger_check_counts.get(schedule_id, 0) + 1
        )

        try:
            # Check cooldown first
            if self._is_in_cooldown(schedule, now):
                remaining = self._get_cooldown_remaining(schedule, now)
                logger.debug(
                    f"Schedule {schedule.name} in cooldown ({remaining}s remaining)"
                )
                return

            # Get profile data for data change triggers
            profile_data = None
            baseline_profile = None

            if schedule.trigger_type == TriggerType.DATA_CHANGE.value:
                # Check if auto_profile is enabled
                config = schedule.trigger_config or {}
                if config.get("auto_profile", True):
                    # Run a fresh profile before comparison
                    await self._run_profile_if_needed(session, schedule.source_id)

                profile_data, baseline_profile = await self._get_profile_data(
                    session, schedule.source_id
                )

            # Evaluate trigger
            evaluation = await TriggerFactory.evaluate_schedule(
                schedule,
                profile_data=profile_data,
                baseline_profile=baseline_profile,
            )

            # Update schedule with evaluation result
            schedule.update_trigger_result(evaluation.to_dict())

            if evaluation.should_trigger:
                logger.info(
                    f"Trigger fired for schedule {schedule.name}: {evaluation.reason}"
                )
                # Update trigger tracking
                self._trigger_trigger_times[schedule_id] = now
                self._trigger_trigger_counts[schedule_id] = (
                    self._trigger_trigger_counts.get(schedule_id, 0) + 1
                )
                # Run validation in background
                asyncio.create_task(self._run_validation(schedule.id))
            else:
                logger.debug(
                    f"Trigger not fired for schedule {schedule.name}: {evaluation.reason}"
                )

            await session.commit()

        except Exception as e:
            logger.error(f"Error evaluating schedule {schedule.id}: {e}")

    async def _run_profile_if_needed(
        self, session: Any, source_id: str
    ) -> None:
        """Run a profile for a source if needed for data change detection.

        Args:
            session: Database session.
            source_id: Source ID to profile.
        """
        from sqlalchemy import select
        from truthound_dashboard.db import Profile

        try:
            # Check if we have a recent profile (within last check interval)
            result = await session.execute(
                select(Profile)
                .where(Profile.source_id == source_id)
                .order_by(Profile.created_at.desc())
                .limit(1)
            )
            latest_profile = result.scalar_one_or_none()

            # Skip if recent profile exists (within 1 minute)
            if latest_profile:
                profile_age = datetime.utcnow() - latest_profile.created_at
                if profile_age.total_seconds() < 60:
                    logger.debug(f"Recent profile exists for source {source_id}")
                    return

            # Run profile using adapter
            adapter = get_adapter()
            result = await session.execute(
                select(Source).where(Source.id == source_id)
            )
            source = result.scalar_one_or_none()

            if source and source.connection_string:
                logger.debug(f"Running auto-profile for source {source_id}")
                await adapter.profile(source.connection_string)

        except Exception as e:
            logger.warning(f"Auto-profile failed for source {source_id}: {e}")

    async def _get_profile_data(
        self, session: Any, source_id: str
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """Get current and baseline profile data for a source.

        Args:
            session: Database session.
            source_id: Source ID.

        Returns:
            Tuple of (current_profile, baseline_profile).
        """
        from sqlalchemy import select
        from truthound_dashboard.db import Profile

        try:
            # Get the two most recent profiles
            result = await session.execute(
                select(Profile)
                .where(Profile.source_id == source_id)
                .order_by(Profile.created_at.desc())
                .limit(2)
            )
            profiles = result.scalars().all()

            if len(profiles) == 0:
                return None, None
            elif len(profiles) == 1:
                return profiles[0].profile_json, None
            else:
                return profiles[0].profile_json, profiles[1].profile_json

        except Exception as e:
            logger.error(f"Error getting profile data for source {source_id}: {e}")
            return None, None

    async def trigger_event(
        self,
        event_type: str,
        source_id: str | None = None,
        event_data: dict[str, Any] | None = None,
    ) -> list[str]:
        """Trigger event-based schedules.

        Called when system events occur (e.g., schema change, drift detected).

        Args:
            event_type: Type of event (e.g., "schema_changed", "drift_detected").
            source_id: Optional source ID related to the event.
            event_data: Additional event data.

        Returns:
            List of schedule IDs that were triggered.
        """
        triggered_schedules = []

        async with get_session() as session:
            from sqlalchemy import select

            # Get event trigger schedules
            result = await session.execute(
                select(Schedule)
                .where(Schedule.is_active == True)
                .where(Schedule.trigger_type == TriggerType.EVENT.value)
            )
            schedules = result.scalars().all()

            full_event_data = {
                "type": event_type,
                "source_id": source_id,
                **(event_data or {}),
            }

            for schedule in schedules:
                evaluation = await TriggerFactory.evaluate_schedule(
                    schedule,
                    event_data=full_event_data,
                )

                if evaluation.should_trigger:
                    logger.info(
                        f"Event '{event_type}' triggered schedule {schedule.name}"
                    )
                    asyncio.create_task(self._run_validation(schedule.id))
                    triggered_schedules.append(schedule.id)

        return triggered_schedules

    async def trigger_webhook(
        self,
        source: str,
        event_type: str = "data_updated",
        payload: dict[str, Any] | None = None,
        schedule_id: str | None = None,
        source_id: str | None = None,
        signature: str | None = None,
    ) -> dict[str, Any]:
        """Process incoming webhook trigger.

        Args:
            source: Source identifier (e.g., "airflow", "dagster").
            event_type: Type of event.
            payload: Additional payload data.
            schedule_id: Specific schedule to trigger (optional).
            source_id: Data source ID to filter (optional).
            signature: HMAC signature for verification (optional).

        Returns:
            Result dictionary with triggered schedules.
        """
        request_id = str(uuid.uuid4())[:8]
        triggered_schedules = []
        now = datetime.utcnow()

        logger.info(f"Webhook received from '{source}' (request_id={request_id})")

        async with get_session() as session:
            from sqlalchemy import select

            # Build query for webhook triggers
            query = (
                select(Schedule)
                .where(Schedule.is_active == True)
                .where(Schedule.trigger_type == TriggerType.WEBHOOK.value)
            )

            # Filter by specific schedule if provided
            if schedule_id:
                query = query.where(Schedule.id == schedule_id)

            # Filter by source ID if provided
            if source_id:
                query = query.where(Schedule.source_id == source_id)

            result = await session.execute(query)
            schedules = result.scalars().all()

            for schedule in schedules:
                # Verify signature if required
                config = schedule.trigger_config or {}
                webhook_secret = config.get("webhook_secret")
                require_signature = config.get("require_signature", False)

                signature_valid = True
                if require_signature and webhook_secret:
                    signature_valid = self._verify_webhook_signature(
                        payload or {},
                        signature,
                        webhook_secret,
                    )

                # Check cooldown
                if self._is_in_cooldown(schedule, now):
                    logger.debug(
                        f"Schedule {schedule.name} in cooldown, skipping webhook"
                    )
                    continue

                # Evaluate webhook trigger
                evaluation = await TriggerFactory.evaluate_schedule(
                    schedule,
                    custom_data={
                        "webhook_data": {
                            "source": source,
                            "event_type": event_type,
                            "payload": payload or {},
                            "signature_valid": signature_valid,
                        }
                    },
                )

                if evaluation.should_trigger:
                    logger.info(
                        f"Webhook triggered schedule {schedule.name} "
                        f"(request_id={request_id})"
                    )
                    # Update trigger tracking
                    self._trigger_trigger_times[schedule.id] = now
                    self._trigger_trigger_counts[schedule.id] = (
                        self._trigger_trigger_counts.get(schedule.id, 0) + 1
                    )
                    asyncio.create_task(self._run_validation(schedule.id))
                    triggered_schedules.append(schedule.id)

        return {
            "accepted": True,
            "triggered_schedules": triggered_schedules,
            "message": (
                f"Triggered {len(triggered_schedules)} schedule(s)"
                if triggered_schedules
                else "No matching schedules triggered"
            ),
            "request_id": request_id,
        }

    def _verify_webhook_signature(
        self,
        payload: dict[str, Any],
        signature: str | None,
        secret: str,
    ) -> bool:
        """Verify webhook HMAC signature.

        Args:
            payload: Request payload.
            signature: Provided signature (X-Webhook-Signature header).
            secret: Webhook secret key.

        Returns:
            True if signature is valid.
        """
        if not signature:
            return False

        try:
            import json
            payload_bytes = json.dumps(payload, sort_keys=True).encode()
            expected = hmac.new(
                secret.encode(),
                payload_bytes,
                hashlib.sha256,
            ).hexdigest()
            return hmac.compare_digest(signature, expected)
        except Exception as e:
            logger.warning(f"Webhook signature verification failed: {e}")
            return False

    def get_trigger_monitoring_status(self) -> dict[str, Any]:
        """Get current trigger monitoring status.

        Returns:
            Dictionary with monitoring stats and schedule statuses.
        """
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)

        # Count checks and triggers in last hour
        checks_last_hour = sum(
            1 for t in self._trigger_check_times.values()
            if t >= one_hour_ago
        )
        triggers_last_hour = sum(
            1 for t in self._trigger_trigger_times.values()
            if t >= one_hour_ago
        )

        return {
            "checker_running": self._checker_running,
            "checker_interval_seconds": self._data_change_check_interval,
            "last_checker_run_at": (
                self._last_checker_run.isoformat()
                if self._last_checker_run else None
            ),
            "total_schedules_tracked": len(self._trigger_check_times),
            "checks_last_hour": checks_last_hour,
            "triggers_last_hour": triggers_last_hour,
        }

    async def get_trigger_check_statuses(self) -> list[dict[str, Any]]:
        """Get detailed status for each tracked trigger.

        Returns:
            List of trigger status dictionaries.
        """
        now = datetime.utcnow()
        statuses = []

        async with get_session() as session:
            from sqlalchemy import select

            # Get all active data change/composite/webhook schedules
            result = await session.execute(
                select(Schedule)
                .where(Schedule.is_active == True)
                .where(
                    Schedule.trigger_type.in_([
                        TriggerType.DATA_CHANGE.value,
                        TriggerType.COMPOSITE.value,
                        TriggerType.WEBHOOK.value,
                    ])
                )
            )
            schedules = result.scalars().all()

            for schedule in schedules:
                schedule_id = schedule.id
                config = schedule.trigger_config or {}

                last_check = self._trigger_check_times.get(schedule_id)
                last_triggered = self._trigger_trigger_times.get(schedule_id)
                check_interval = config.get(
                    "check_interval_minutes",
                    self.DEFAULT_SCHEDULE_CHECK_INTERVAL_MINUTES,
                )

                # Calculate next check time
                next_check = None
                if last_check:
                    next_check = last_check + timedelta(minutes=check_interval)

                statuses.append({
                    "schedule_id": schedule_id,
                    "schedule_name": schedule.name,
                    "trigger_type": schedule.trigger_type,
                    "last_check_at": last_check.isoformat() if last_check else None,
                    "next_check_at": next_check.isoformat() if next_check else None,
                    "last_triggered_at": (
                        last_triggered.isoformat() if last_triggered else None
                    ),
                    "check_count": self._trigger_check_counts.get(schedule_id, 0),
                    "trigger_count": self._trigger_trigger_counts.get(schedule_id, 0),
                    "is_due_for_check": self._is_schedule_due_for_check(schedule, now),
                    "priority": self._get_schedule_priority(schedule),
                    "cooldown_remaining_seconds": self._get_cooldown_remaining(
                        schedule, now
                    ),
                })

        # Sort by priority
        statuses.sort(key=lambda s: s["priority"])
        return statuses


# Singleton instance
_scheduler: ValidationScheduler | None = None


def get_scheduler() -> ValidationScheduler:
    """Get the singleton scheduler instance.

    Returns:
        ValidationScheduler instance.
    """
    global _scheduler
    if _scheduler is None:
        _scheduler = ValidationScheduler()
    return _scheduler


async def start_scheduler() -> None:
    """Start the validation scheduler."""
    scheduler = get_scheduler()
    await scheduler.start()


async def stop_scheduler() -> None:
    """Stop the validation scheduler."""
    scheduler = get_scheduler()
    await scheduler.stop()
