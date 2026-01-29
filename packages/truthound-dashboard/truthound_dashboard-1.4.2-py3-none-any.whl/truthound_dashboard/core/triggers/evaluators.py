"""Trigger evaluator implementations.

Provides concrete implementations for all trigger types:
- CronTrigger: Cron expression based scheduling
- IntervalTrigger: Fixed time interval scheduling
- DataChangeTrigger: Profile-based change detection
- CompositeTrigger: Combine multiple triggers
- EventTrigger: Respond to system events
- ManualTrigger: API-only execution
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from apscheduler.triggers.cron import CronTrigger as APCronTrigger
from apscheduler.triggers.interval import IntervalTrigger as APIntervalTrigger

from .base import (
    BaseTrigger,
    TriggerContext,
    TriggerEvaluation,
    TriggerRegistry,
)

logger = logging.getLogger(__name__)


@TriggerRegistry.register("cron")
class CronTrigger(BaseTrigger):
    """Cron expression based trigger.

    Uses standard cron format: minute hour day month weekday

    Config:
        expression: Cron expression string
        timezone: Optional timezone (default: UTC)
    """

    def _validate_config(self) -> None:
        """Validate cron configuration."""
        expression = self.config.get("expression")
        if not expression:
            raise ValueError("Cron trigger requires 'expression' field")

        # Validate by attempting to parse
        try:
            APCronTrigger.from_crontab(expression)
        except Exception as e:
            raise ValueError(f"Invalid cron expression: {e}")

    async def evaluate(self, context: TriggerContext) -> TriggerEvaluation:
        """Evaluate if cron trigger should fire.

        For cron triggers, we check if we're past the scheduled time
        since the last run.
        """
        expression = self.config.get("expression")
        trigger = APCronTrigger.from_crontab(expression)

        # Get next fire time from last run (or from epoch if never run)
        base_time = context.last_run_at or datetime(2000, 1, 1)
        next_fire = trigger.get_next_fire_time(None, base_time)

        if next_fire is None:
            return TriggerEvaluation(
                should_trigger=False,
                reason="No upcoming scheduled time",
            )

        should_trigger = context.current_time >= next_fire

        return TriggerEvaluation(
            should_trigger=should_trigger,
            reason=(
                f"Scheduled time reached ({next_fire.isoformat()})"
                if should_trigger
                else f"Waiting for scheduled time ({next_fire.isoformat()})"
            ),
            next_evaluation_at=next_fire if not should_trigger else None,
            details={
                "expression": expression,
                "next_fire_time": next_fire.isoformat(),
            },
        )

    def get_next_evaluation_time(
        self, context: TriggerContext
    ) -> datetime | None:
        """Get next cron fire time."""
        expression = self.config.get("expression")
        try:
            trigger = APCronTrigger.from_crontab(expression)
            return trigger.get_next_fire_time(None, context.current_time)
        except Exception:
            return None

    def get_description(self) -> str:
        """Get human-readable description."""
        return f"Cron: {self.config.get('expression', 'not configured')}"


@TriggerRegistry.register("interval")
class IntervalTrigger(BaseTrigger):
    """Fixed time interval trigger.

    Config:
        seconds: Interval in seconds
        minutes: Interval in minutes
        hours: Interval in hours
        days: Interval in days
    """

    def _validate_config(self) -> None:
        """Validate interval configuration."""
        has_interval = any(
            self.config.get(key)
            for key in ["seconds", "minutes", "hours", "days"]
        )
        if not has_interval:
            raise ValueError(
                "Interval trigger requires at least one of: seconds, minutes, hours, days"
            )

    def _get_total_seconds(self) -> int:
        """Calculate total interval in seconds."""
        total = 0
        total += self.config.get("seconds", 0)
        total += self.config.get("minutes", 0) * 60
        total += self.config.get("hours", 0) * 3600
        total += self.config.get("days", 0) * 86400
        return total or 3600  # Default to 1 hour

    async def evaluate(self, context: TriggerContext) -> TriggerEvaluation:
        """Evaluate if interval trigger should fire."""
        interval_seconds = self._get_total_seconds()

        # If never run, trigger immediately
        if context.last_run_at is None:
            return TriggerEvaluation(
                should_trigger=True,
                reason="First run (never executed before)",
                details={"interval_seconds": interval_seconds},
            )

        # Calculate next run time
        next_run = context.last_run_at + timedelta(seconds=interval_seconds)
        should_trigger = context.current_time >= next_run

        return TriggerEvaluation(
            should_trigger=should_trigger,
            reason=(
                f"Interval elapsed ({interval_seconds}s since last run)"
                if should_trigger
                else f"Waiting for interval ({(next_run - context.current_time).seconds}s remaining)"
            ),
            next_evaluation_at=next_run if not should_trigger else None,
            details={
                "interval_seconds": interval_seconds,
                "next_run": next_run.isoformat(),
            },
        )

    def get_next_evaluation_time(
        self, context: TriggerContext
    ) -> datetime | None:
        """Get next interval fire time."""
        if context.last_run_at is None:
            return context.current_time
        return context.last_run_at + timedelta(seconds=self._get_total_seconds())

    def get_description(self) -> str:
        """Get human-readable description."""
        parts = []
        if self.config.get("days"):
            parts.append(f"{self.config['days']}d")
        if self.config.get("hours"):
            parts.append(f"{self.config['hours']}h")
        if self.config.get("minutes"):
            parts.append(f"{self.config['minutes']}m")
        if self.config.get("seconds"):
            parts.append(f"{self.config['seconds']}s")
        return f"Every {' '.join(parts)}" if parts else "Interval: not configured"


@TriggerRegistry.register("data_change")
class DataChangeTrigger(BaseTrigger):
    """Data change detection trigger.

    Triggers when profile metrics change by more than a threshold.

    Config:
        change_threshold: Minimum change percentage (0.0-1.0)
        metrics: List of metrics to monitor
        check_interval_minutes: How often to check
    """

    DEFAULT_METRICS = ["row_count", "null_percentage", "distinct_count"]

    def _validate_config(self) -> None:
        """Validate data change configuration."""
        threshold = self.config.get("change_threshold", 0.05)
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("change_threshold must be between 0.0 and 1.0")

    async def evaluate(self, context: TriggerContext) -> TriggerEvaluation:
        """Evaluate if data has changed enough to trigger.

        Compares current profile against baseline and checks if
        any monitored metrics have changed beyond the threshold.
        """
        threshold = self.config.get("change_threshold", 0.05)
        metrics = self.config.get("metrics", self.DEFAULT_METRICS)

        # Need both profiles to compare
        if context.profile_data is None:
            return TriggerEvaluation(
                should_trigger=False,
                reason="No current profile data available",
                details={"error": "missing_current_profile"},
            )

        if context.baseline_profile is None:
            # First profile - trigger to establish baseline
            return TriggerEvaluation(
                should_trigger=True,
                reason="First profile (no baseline to compare)",
                details={"reason": "no_baseline"},
            )

        # Calculate changes for each metric
        changes = {}
        max_change = 0.0
        triggered_metrics = []

        for metric in metrics:
            current = self._get_metric_value(context.profile_data, metric)
            baseline = self._get_metric_value(context.baseline_profile, metric)

            if current is None or baseline is None:
                continue

            # Calculate percentage change
            if baseline == 0:
                change = 1.0 if current != 0 else 0.0
            else:
                change = abs(current - baseline) / abs(baseline)

            changes[metric] = {
                "current": current,
                "baseline": baseline,
                "change": change,
            }

            if change >= threshold:
                triggered_metrics.append(metric)
                max_change = max(max_change, change)

        should_trigger = len(triggered_metrics) > 0

        return TriggerEvaluation(
            should_trigger=should_trigger,
            reason=(
                f"Data change detected: {', '.join(triggered_metrics)} changed by >= {threshold*100:.0f}%"
                if should_trigger
                else f"No significant changes (max: {max_change*100:.1f}%, threshold: {threshold*100:.0f}%)"
            ),
            details={
                "threshold": threshold,
                "max_change": max_change,
                "changes": changes,
                "triggered_metrics": triggered_metrics,
            },
            confidence=max_change if should_trigger else 1.0 - max_change,
        )

    def _get_metric_value(
        self, profile: dict[str, Any], metric: str
    ) -> float | None:
        """Extract metric value from profile data."""
        # Handle top-level metrics
        if metric in profile:
            return float(profile[metric])

        # Handle nested column metrics
        if "columns" in profile:
            for col in profile["columns"]:
                if metric in col:
                    return float(col[metric])

        # Handle summary metrics
        if "summary" in profile and metric in profile["summary"]:
            return float(profile["summary"][metric])

        return None

    def get_description(self) -> str:
        """Get human-readable description."""
        threshold = self.config.get("change_threshold", 0.05)
        return f"Data change >= {threshold * 100:.0f}%"


@TriggerRegistry.register("composite")
class CompositeTrigger(BaseTrigger):
    """Composite trigger that combines multiple triggers.

    Config:
        operator: "and" or "or"
        triggers: List of trigger configurations
    """

    def _validate_config(self) -> None:
        """Validate composite configuration."""
        operator = self.config.get("operator", "and").lower()
        if operator not in ("and", "or"):
            raise ValueError("Composite operator must be 'and' or 'or'")

        triggers = self.config.get("triggers", [])
        if len(triggers) < 2:
            raise ValueError("Composite trigger requires at least 2 sub-triggers")

        # Validate sub-triggers don't contain composites (prevent nesting)
        for trigger in triggers:
            if trigger.get("type") == "composite":
                raise ValueError("Nested composite triggers are not supported")

    async def evaluate(self, context: TriggerContext) -> TriggerEvaluation:
        """Evaluate composite trigger based on operator."""
        operator = self.config.get("operator", "and").lower()
        trigger_configs = self.config.get("triggers", [])

        sub_results = []

        for trigger_config in trigger_configs:
            trigger_type = trigger_config.get("type")
            trigger = TriggerRegistry.create(trigger_type, trigger_config)

            if trigger is None:
                sub_results.append({
                    "type": trigger_type,
                    "should_trigger": False,
                    "reason": f"Unknown trigger type: {trigger_type}",
                })
                continue

            result = await trigger.evaluate(context)
            sub_results.append({
                "type": trigger_type,
                "should_trigger": result.should_trigger,
                "reason": result.reason,
            })

        # Apply operator logic
        if operator == "and":
            should_trigger = all(r["should_trigger"] for r in sub_results)
            reason = "All conditions met" if should_trigger else "Not all conditions met"
        else:  # or
            should_trigger = any(r["should_trigger"] for r in sub_results)
            reason = "At least one condition met" if should_trigger else "No conditions met"

        triggered_count = sum(1 for r in sub_results if r["should_trigger"])

        return TriggerEvaluation(
            should_trigger=should_trigger,
            reason=f"{reason} ({triggered_count}/{len(sub_results)} triggers)",
            details={
                "operator": operator,
                "sub_results": sub_results,
                "triggered_count": triggered_count,
                "total_count": len(sub_results),
            },
        )

    def get_description(self) -> str:
        """Get human-readable description."""
        operator = self.config.get("operator", "and").upper()
        triggers = self.config.get("triggers", [])
        return f"Composite: {len(triggers)} triggers ({operator})"


@TriggerRegistry.register("event")
class EventTrigger(BaseTrigger):
    """Event-based trigger.

    Triggers in response to specific system events.

    Config:
        event_types: List of event types to respond to
        source_filter: Optional list of source IDs to filter
    """

    VALID_EVENTS = {
        "validation_completed",
        "validation_failed",
        "schema_changed",
        "drift_detected",
        "profile_updated",
        "source_created",
        "source_updated",
    }

    def _validate_config(self) -> None:
        """Validate event configuration."""
        event_types = self.config.get("event_types", [])
        if not event_types:
            raise ValueError("Event trigger requires 'event_types' list")

        invalid_events = set(event_types) - self.VALID_EVENTS
        if invalid_events:
            raise ValueError(f"Invalid event types: {invalid_events}")

    async def evaluate(self, context: TriggerContext) -> TriggerEvaluation:
        """Evaluate if event matches configured types."""
        event_types = set(self.config.get("event_types", []))
        source_filter = self.config.get("source_filter")

        # Check if there's event data in context
        if context.event_data is None:
            return TriggerEvaluation(
                should_trigger=False,
                reason="No event data in context",
            )

        event_type = context.event_data.get("type")
        event_source = context.event_data.get("source_id")

        # Check event type match
        if event_type not in event_types:
            return TriggerEvaluation(
                should_trigger=False,
                reason=f"Event type '{event_type}' not in configured types",
                details={"event_type": event_type, "configured_types": list(event_types)},
            )

        # Check source filter if configured
        if source_filter and event_source not in source_filter:
            return TriggerEvaluation(
                should_trigger=False,
                reason=f"Event source '{event_source}' not in filter",
                details={"event_source": event_source, "filter": source_filter},
            )

        return TriggerEvaluation(
            should_trigger=True,
            reason=f"Event '{event_type}' matched",
            details={
                "event_type": event_type,
                "event_source": event_source,
                "event_data": context.event_data,
            },
        )

    def get_description(self) -> str:
        """Get human-readable description."""
        events = self.config.get("event_types", [])
        return f"Events: {', '.join(events[:2])}{'...' if len(events) > 2 else ''}"


@TriggerRegistry.register("manual")
class ManualTrigger(BaseTrigger):
    """Manual-only trigger.

    Only triggers when explicitly invoked via API.
    """

    def _validate_config(self) -> None:
        """No validation needed for manual trigger."""
        pass

    async def evaluate(self, context: TriggerContext) -> TriggerEvaluation:
        """Manual triggers never auto-fire."""
        # Check if manual trigger was requested via context
        force_trigger = context.custom_data.get("force_trigger", False)

        return TriggerEvaluation(
            should_trigger=force_trigger,
            reason=(
                "Manually triggered via API"
                if force_trigger
                else "Manual trigger only (use API to execute)"
            ),
            details={"manual_only": True},
        )

    def get_description(self) -> str:
        """Get human-readable description."""
        return "Manual trigger only"


@TriggerRegistry.register("webhook")
class WebhookTrigger(BaseTrigger):
    """Webhook-based trigger.

    Triggers when receiving webhook requests from external systems.

    Config:
        webhook_secret: Optional secret for HMAC validation
        allowed_sources: List of allowed source identifiers
        payload_filters: JSON path filters for payload matching
        require_signature: Whether to require signature validation
    """

    def _validate_config(self) -> None:
        """Validate webhook configuration."""
        # Webhook config is optional, but if require_signature is True,
        # webhook_secret must be provided
        if self.config.get("require_signature") and not self.config.get("webhook_secret"):
            raise ValueError(
                "webhook_secret is required when require_signature is True"
            )

    async def evaluate(self, context: TriggerContext) -> TriggerEvaluation:
        """Evaluate if webhook trigger should fire.

        Checks:
        1. Webhook data exists in context
        2. Source is in allowed_sources (if configured)
        3. Payload matches filters (if configured)
        4. Signature is valid (if required)
        """
        # Check for webhook data in context
        webhook_data = context.custom_data.get("webhook_data")
        if webhook_data is None:
            return TriggerEvaluation(
                should_trigger=False,
                reason="No webhook data in context",
                details={"waiting_for_webhook": True},
            )

        source = webhook_data.get("source", "")
        payload = webhook_data.get("payload", {})
        signature_valid = webhook_data.get("signature_valid", True)

        # Check signature if required
        require_signature = self.config.get("require_signature", False)
        if require_signature and not signature_valid:
            return TriggerEvaluation(
                should_trigger=False,
                reason="Invalid webhook signature",
                details={"error": "invalid_signature", "source": source},
            )

        # Check allowed sources
        allowed_sources = self.config.get("allowed_sources")
        if allowed_sources and source not in allowed_sources:
            return TriggerEvaluation(
                should_trigger=False,
                reason=f"Source '{source}' not in allowed sources",
                details={
                    "source": source,
                    "allowed_sources": allowed_sources,
                },
            )

        # Check payload filters
        payload_filters = self.config.get("payload_filters", {})
        if payload_filters:
            filters_match = self._check_payload_filters(payload, payload_filters)
            if not filters_match:
                return TriggerEvaluation(
                    should_trigger=False,
                    reason="Payload does not match filters",
                    details={
                        "source": source,
                        "filters": payload_filters,
                    },
                )

        return TriggerEvaluation(
            should_trigger=True,
            reason=f"Webhook received from '{source}'",
            details={
                "source": source,
                "event_type": webhook_data.get("event_type", "unknown"),
                "payload_keys": list(payload.keys()) if payload else [],
            },
        )

    def _check_payload_filters(
        self, payload: dict[str, Any], filters: dict[str, Any]
    ) -> bool:
        """Check if payload matches the configured filters.

        Simple key-value matching. For nested paths, use dot notation.
        """
        for key, expected_value in filters.items():
            # Support dot notation for nested keys
            parts = key.split(".")
            value = payload
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = None
                    break

            if value != expected_value:
                return False

        return True

    def get_description(self) -> str:
        """Get human-readable description."""
        allowed = self.config.get("allowed_sources", [])
        if allowed:
            return f"Webhook: {', '.join(allowed[:2])}{'...' if len(allowed) > 2 else ''}"
        return "Webhook trigger"
