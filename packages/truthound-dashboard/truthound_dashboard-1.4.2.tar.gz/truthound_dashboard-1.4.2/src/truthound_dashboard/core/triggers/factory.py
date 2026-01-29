"""Trigger factory for creating and managing triggers.

Provides a high-level API for creating triggers from configuration
and integrating with the scheduler.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from truthound_dashboard.db import Schedule
from truthound_dashboard.schemas.triggers import (
    TriggerType,
    parse_trigger_config,
)

from .base import (
    BaseTrigger,
    TriggerContext,
    TriggerEvaluation,
    TriggerRegistry,
)

# Import evaluators to register them
from . import evaluators  # noqa: F401

logger = logging.getLogger(__name__)


class TriggerFactory:
    """Factory for creating and managing trigger instances.

    Provides methods to:
    - Create triggers from Schedule models
    - Create triggers from raw configuration
    - Evaluate triggers with proper context
    - Get trigger metadata and descriptions
    """

    @classmethod
    def from_schedule(cls, schedule: Schedule) -> BaseTrigger | None:
        """Create a trigger from a Schedule model.

        Handles both new trigger_config and legacy cron_expression fields.

        Args:
            schedule: Schedule model instance.

        Returns:
            BaseTrigger instance or None if creation fails.
        """
        trigger_type = schedule.trigger_type or TriggerType.CRON.value

        # Build config from schedule
        if schedule.trigger_config:
            config = schedule.trigger_config.copy()
        else:
            config = {}

        # Handle legacy cron_expression field
        if trigger_type == TriggerType.CRON.value:
            if "expression" not in config and schedule.cron_expression:
                config["expression"] = schedule.cron_expression

        return cls.create(trigger_type, config)

    @classmethod
    def create(
        cls, trigger_type: str, config: dict[str, Any]
    ) -> BaseTrigger | None:
        """Create a trigger from type and configuration.

        Args:
            trigger_type: Type identifier string.
            config: Trigger-specific configuration.

        Returns:
            BaseTrigger instance or None if creation fails.
        """
        try:
            # Normalize type to lowercase
            trigger_type = trigger_type.lower()

            trigger = TriggerRegistry.create(trigger_type, config)
            if trigger is None:
                logger.warning(f"Unknown trigger type: {trigger_type}")
            return trigger

        except ValueError as e:
            logger.error(f"Invalid trigger config for {trigger_type}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to create trigger {trigger_type}: {e}")
            return None

    @classmethod
    def create_from_dict(cls, data: dict[str, Any]) -> BaseTrigger | None:
        """Create a trigger from a dictionary with type and config.

        Args:
            data: Dictionary with 'type' and optional config fields.

        Returns:
            BaseTrigger instance or None if creation fails.
        """
        trigger_type = data.get("type")
        if not trigger_type:
            logger.error("Trigger data missing 'type' field")
            return None

        # Extract config (all fields except 'type')
        config = {k: v for k, v in data.items() if k != "type"}

        return cls.create(trigger_type, config)

    @classmethod
    async def evaluate_schedule(
        cls,
        schedule: Schedule,
        *,
        profile_data: dict[str, Any] | None = None,
        baseline_profile: dict[str, Any] | None = None,
        event_data: dict[str, Any] | None = None,
        force_trigger: bool = False,
    ) -> TriggerEvaluation:
        """Evaluate a schedule's trigger.

        Args:
            schedule: Schedule to evaluate.
            profile_data: Current profile data (for data change triggers).
            baseline_profile: Baseline profile for comparison.
            event_data: Event data (for event triggers).
            force_trigger: Force trigger regardless of conditions.

        Returns:
            TriggerEvaluation with result.
        """
        trigger = cls.from_schedule(schedule)

        if trigger is None:
            return TriggerEvaluation(
                should_trigger=False,
                reason=f"Failed to create trigger: {schedule.trigger_type}",
                details={"error": "trigger_creation_failed"},
            )

        context = TriggerContext(
            schedule_id=schedule.id,
            source_id=schedule.source_id,
            last_run_at=schedule.last_run_at,
            trigger_count=schedule.trigger_count,
            profile_data=profile_data,
            baseline_profile=baseline_profile,
            event_data=event_data,
            custom_data={"force_trigger": force_trigger},
        )

        try:
            return await trigger.evaluate(context)
        except Exception as e:
            logger.error(f"Trigger evaluation failed for schedule {schedule.id}: {e}")
            return TriggerEvaluation(
                should_trigger=False,
                reason=f"Evaluation error: {str(e)}",
                details={"error": str(e)},
            )

    @classmethod
    def get_trigger_types(cls) -> list[dict[str, Any]]:
        """Get information about all registered trigger types.

        Returns:
            List of trigger type information dictionaries.
        """
        types = []
        for trigger_type in TriggerRegistry.list_types():
            trigger_class = TriggerRegistry.get(trigger_type)
            if trigger_class:
                types.append({
                    "type": trigger_type,
                    "name": trigger_type.replace("_", " ").title(),
                    "description": _get_type_description(trigger_type),
                    "config_schema": _get_config_schema(trigger_type),
                })
        return types

    @classmethod
    def validate_config(
        cls, trigger_type: str, config: dict[str, Any]
    ) -> tuple[bool, str | None]:
        """Validate trigger configuration without creating the trigger.

        Args:
            trigger_type: Type identifier.
            config: Configuration to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        try:
            trigger = cls.create(trigger_type, config)
            if trigger is None:
                return False, f"Unknown trigger type: {trigger_type}"
            return True, None
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    @classmethod
    def get_next_run_time(
        cls,
        schedule: Schedule,
        from_time: datetime | None = None,
    ) -> datetime | None:
        """Calculate the next run time for a schedule.

        Args:
            schedule: Schedule to check.
            from_time: Base time for calculation (defaults to now).

        Returns:
            Next run datetime or None.
        """
        trigger = cls.from_schedule(schedule)
        if trigger is None:
            return None

        context = TriggerContext(
            schedule_id=schedule.id,
            source_id=schedule.source_id,
            last_run_at=schedule.last_run_at,
            trigger_count=schedule.trigger_count,
            current_time=from_time or datetime.utcnow(),
        )

        return trigger.get_next_evaluation_time(context)


def _get_type_description(trigger_type: str) -> str:
    """Get description for a trigger type."""
    descriptions = {
        "cron": "Schedule using cron expressions (e.g., '0 0 * * *' for daily at midnight)",
        "interval": "Run at fixed time intervals (e.g., every 6 hours)",
        "data_change": "Trigger when data profile changes by a threshold percentage",
        "composite": "Combine multiple triggers with AND/OR logic",
        "event": "Trigger in response to system events (e.g., schema changes)",
        "manual": "Only run when manually triggered via API",
    }
    return descriptions.get(trigger_type, "Unknown trigger type")


def _get_config_schema(trigger_type: str) -> dict[str, Any]:
    """Get configuration schema for a trigger type."""
    schemas = {
        "cron": {
            "expression": {
                "type": "string",
                "required": True,
                "description": "Cron expression (minute hour day month weekday)",
                "examples": ["0 0 * * *", "0 */6 * * *", "0 8 * * 1-5"],
            },
            "timezone": {
                "type": "string",
                "required": False,
                "default": "UTC",
                "description": "Timezone for scheduling",
            },
        },
        "interval": {
            "seconds": {
                "type": "integer",
                "required": False,
                "min": 1,
                "description": "Interval in seconds",
            },
            "minutes": {
                "type": "integer",
                "required": False,
                "min": 1,
                "description": "Interval in minutes",
            },
            "hours": {
                "type": "integer",
                "required": False,
                "min": 1,
                "description": "Interval in hours",
            },
            "days": {
                "type": "integer",
                "required": False,
                "min": 1,
                "description": "Interval in days",
            },
        },
        "data_change": {
            "change_threshold": {
                "type": "number",
                "required": False,
                "default": 0.05,
                "min": 0.0,
                "max": 1.0,
                "description": "Minimum change percentage to trigger (0.0-1.0)",
            },
            "metrics": {
                "type": "array",
                "items": "string",
                "required": False,
                "default": ["row_count", "null_percentage", "distinct_count"],
                "description": "Metrics to monitor for changes",
            },
            "check_interval_minutes": {
                "type": "integer",
                "required": False,
                "default": 60,
                "min": 1,
                "description": "How often to check for changes",
            },
        },
        "composite": {
            "operator": {
                "type": "string",
                "required": False,
                "default": "and",
                "enum": ["and", "or"],
                "description": "How to combine triggers",
            },
            "triggers": {
                "type": "array",
                "items": "object",
                "required": True,
                "min_items": 2,
                "description": "List of trigger configurations to combine",
            },
        },
        "event": {
            "event_types": {
                "type": "array",
                "items": "string",
                "required": True,
                "description": "Event types that trigger execution",
                "enum": [
                    "validation_completed",
                    "validation_failed",
                    "schema_changed",
                    "drift_detected",
                    "profile_updated",
                    "source_created",
                    "source_updated",
                ],
            },
            "source_filter": {
                "type": "array",
                "items": "string",
                "required": False,
                "description": "Optional source IDs to filter events",
            },
        },
        "manual": {},
    }
    return schemas.get(trigger_type, {})
