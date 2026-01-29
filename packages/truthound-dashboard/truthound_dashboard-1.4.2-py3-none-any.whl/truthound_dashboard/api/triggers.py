"""Trigger monitoring and webhook API endpoints.

This module provides endpoints for:
- Trigger monitoring status
- Webhook trigger reception
- Trigger status queries
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException

from truthound_dashboard.core.scheduler import get_scheduler
from truthound_dashboard.schemas.triggers import (
    TriggerCheckStatus,
    TriggerMonitoringResponse,
    TriggerMonitoringStats,
    WebhookTriggerRequest,
    WebhookTriggerResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/triggers", tags=["triggers"])


@router.get(
    "/monitoring",
    response_model=TriggerMonitoringResponse,
    summary="Get trigger monitoring status",
)
async def get_trigger_monitoring() -> TriggerMonitoringResponse:
    """Get current trigger monitoring status.

    Returns:
        Trigger monitoring stats and schedule statuses.
    """
    scheduler = get_scheduler()
    status = scheduler.get_trigger_monitoring_status()
    schedules = await scheduler.get_trigger_check_statuses()

    # Calculate aggregate stats
    active_data_change = sum(
        1 for s in schedules if s["trigger_type"] == "data_change"
    )
    active_webhook = sum(
        1 for s in schedules if s["trigger_type"] == "webhook"
    )
    active_composite = sum(
        1 for s in schedules if s["trigger_type"] == "composite"
    )

    # Calculate average check interval
    check_intervals = [
        s.get("check_interval_minutes", 5) * 60 for s in schedules
    ]
    avg_interval = (
        sum(check_intervals) / len(check_intervals)
        if check_intervals
        else 300.0
    )

    # Find next scheduled check
    next_checks = [
        s["next_check_at"] for s in schedules if s.get("next_check_at")
    ]
    next_check = min(next_checks) if next_checks else None

    stats = TriggerMonitoringStats(
        total_schedules=len(schedules),
        active_data_change_triggers=active_data_change,
        active_webhook_triggers=active_webhook,
        active_composite_triggers=active_composite,
        total_checks_last_hour=status.get("checks_last_hour", 0),
        total_triggers_last_hour=status.get("triggers_last_hour", 0),
        average_check_interval_seconds=avg_interval,
        next_scheduled_check_at=next_check,
    )

    schedule_statuses = [
        TriggerCheckStatus(**s) for s in schedules
    ]

    return TriggerMonitoringResponse(
        stats=stats,
        schedules=schedule_statuses,
        checker_running=status.get("checker_running", False),
        checker_interval_seconds=status.get("checker_interval_seconds", 300),
        last_checker_run_at=status.get("last_checker_run_at"),
    )


@router.get(
    "/schedules/{schedule_id}/status",
    summary="Get trigger status for a specific schedule",
)
async def get_schedule_trigger_status(schedule_id: str) -> dict[str, Any]:
    """Get trigger status for a specific schedule.

    Args:
        schedule_id: Schedule ID to query.

    Returns:
        Trigger status for the schedule.
    """
    scheduler = get_scheduler()
    schedules = await scheduler.get_trigger_check_statuses()

    for schedule in schedules:
        if schedule["schedule_id"] == schedule_id:
            return schedule

    raise HTTPException(
        status_code=404,
        detail=f"Schedule {schedule_id} not found or not using monitored trigger type",
    )


@router.post(
    "/webhook",
    response_model=WebhookTriggerResponse,
    summary="Receive webhook trigger",
)
async def receive_webhook(
    request: WebhookTriggerRequest,
    x_webhook_signature: str | None = Header(
        default=None, description="HMAC-SHA256 signature for verification"
    ),
) -> WebhookTriggerResponse:
    """Receive and process an incoming webhook trigger.

    This endpoint is called by external systems (Airflow, Dagster, Prefect, etc.)
    to trigger validations when data pipelines complete.

    Args:
        request: Webhook trigger request.
        x_webhook_signature: Optional signature for verification.

    Returns:
        Webhook trigger response with triggered schedules.
    """
    scheduler = get_scheduler()

    result = await scheduler.trigger_webhook(
        source=request.source,
        event_type=request.event_type,
        payload=request.payload,
        schedule_id=request.schedule_id,
        source_id=request.source_id,
        signature=x_webhook_signature,
    )

    return WebhookTriggerResponse(
        accepted=result["accepted"],
        triggered_schedules=result["triggered_schedules"],
        message=result["message"],
        request_id=result["request_id"],
    )


@router.post(
    "/webhook/test",
    summary="Test webhook configuration",
)
async def test_webhook(
    source: str = "test",
    event_type: str = "test_event",
) -> dict[str, Any]:
    """Test webhook endpoint without triggering any schedules.

    Useful for verifying connectivity and configuration.

    Args:
        source: Test source name.
        event_type: Test event type.

    Returns:
        Test result.
    """
    return {
        "success": True,
        "message": "Webhook endpoint is accessible",
        "received": {
            "source": source,
            "event_type": event_type,
        },
    }
