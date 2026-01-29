"""API endpoints for Unified Alerts.

Provides REST API for:
- Listing all alerts from all sources
- Alert summary and statistics
- Acknowledging and resolving alerts
- Alert correlation queries
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.unified_alerts import UnifiedAlertsService
from ..db import get_session
from ..schemas.base import DataResponse
from ..schemas.unified_alerts import (
    AcknowledgeAlertRequest,
    AlertCorrelation,
    AlertCorrelationResponse,
    AlertSeverity,
    AlertSource,
    AlertStatus,
    AlertSummary,
    BulkAlertActionRequest,
    BulkAlertActionResponse,
    ResolveAlertRequest,
    UnifiedAlertListResponse,
    UnifiedAlertResponse,
)

router = APIRouter(prefix="/alerts", tags=["alerts"])


def get_service(session: AsyncSession = Depends(get_session)) -> UnifiedAlertsService:
    """Get unified alerts service instance."""
    return UnifiedAlertsService(session)


# =============================================================================
# Alert List Endpoints
# =============================================================================


@router.get("", response_model=DataResponse[UnifiedAlertListResponse])
async def list_alerts(
    source: AlertSource | None = None,
    severity: AlertSeverity | None = None,
    status: AlertStatus | None = None,
    source_name: str | None = Query(None, description="Filter by source name (partial match)"),
    time_range_hours: int | None = Query(24, ge=1, le=720, description="Time range in hours"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: UnifiedAlertsService = Depends(get_service),
):
    """List all unified alerts from all sources.

    Aggregates alerts from:
    - Model monitoring
    - Drift monitoring
    - Anomaly detection
    - Validation failures
    """
    alerts, total = await service.get_all_alerts(
        source=source,
        severity=severity,
        status=status,
        source_name=source_name,
        time_range_hours=time_range_hours,
        offset=offset,
        limit=limit,
    )

    return DataResponse(
        data=UnifiedAlertListResponse(
            items=alerts,
            total=total,
            offset=offset,
            limit=limit,
        )
    )


@router.get("/summary", response_model=DataResponse[AlertSummary])
async def get_alert_summary(
    time_range_hours: int = Query(24, ge=1, le=720, description="Time range for summary"),
    service: UnifiedAlertsService = Depends(get_service),
):
    """Get alert summary statistics.

    Returns counts by severity, source, status, and trend data.
    """
    summary = await service.get_alert_summary(time_range_hours=time_range_hours)
    return DataResponse(data=summary)


@router.get("/count")
async def get_alert_count(
    status: AlertStatus | None = Query(None, description="Filter by status"),
    service: UnifiedAlertsService = Depends(get_service),
):
    """Get quick alert count (for badges).

    Returns just the count of alerts matching the criteria.
    """
    _, total = await service.get_all_alerts(
        status=status,
        time_range_hours=24,
        limit=1,  # We only need the count
    )

    return DataResponse(
        data={
            "count": total,
            "status_filter": status.value if status else "all",
        }
    )


@router.get("/{alert_id}", response_model=DataResponse[UnifiedAlertResponse])
async def get_alert(
    alert_id: str,
    service: UnifiedAlertsService = Depends(get_service),
):
    """Get a specific alert by unified ID."""
    alert = await service.get_alert_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return DataResponse(data=alert)


# =============================================================================
# Alert Action Endpoints
# =============================================================================


@router.post("/{alert_id}/acknowledge", response_model=DataResponse[UnifiedAlertResponse])
async def acknowledge_alert(
    alert_id: str,
    request: AcknowledgeAlertRequest,
    service: UnifiedAlertsService = Depends(get_service),
):
    """Acknowledge an alert.

    Note: Not all alert types support acknowledgement.
    Validation and anomaly alerts are derived from their source data.
    """
    alert = await service.acknowledge_alert(alert_id, request.actor, request.message)
    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found or not eligible for acknowledgement",
        )

    return DataResponse(data=alert)


@router.post("/{alert_id}/resolve", response_model=DataResponse[UnifiedAlertResponse])
async def resolve_alert(
    alert_id: str,
    request: ResolveAlertRequest,
    service: UnifiedAlertsService = Depends(get_service),
):
    """Resolve an alert.

    Note: Not all alert types support resolution.
    Validation and anomaly alerts are derived from their source data.
    """
    alert = await service.resolve_alert(alert_id, request.actor, request.message)
    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found or not eligible for resolution",
        )

    return DataResponse(data=alert)


# =============================================================================
# Bulk Action Endpoints
# =============================================================================


@router.post("/bulk/acknowledge", response_model=DataResponse[BulkAlertActionResponse])
async def bulk_acknowledge_alerts(
    request: BulkAlertActionRequest,
    service: UnifiedAlertsService = Depends(get_service),
):
    """Bulk acknowledge multiple alerts."""
    success, failed, failed_ids = await service.bulk_acknowledge(
        request.alert_ids,
        request.actor,
        request.message,
    )

    return DataResponse(
        data=BulkAlertActionResponse(
            success_count=success,
            failed_count=failed,
            failed_ids=failed_ids,
        )
    )


@router.post("/bulk/resolve", response_model=DataResponse[BulkAlertActionResponse])
async def bulk_resolve_alerts(
    request: BulkAlertActionRequest,
    service: UnifiedAlertsService = Depends(get_service),
):
    """Bulk resolve multiple alerts."""
    success, failed, failed_ids = await service.bulk_resolve(
        request.alert_ids,
        request.actor,
        request.message,
    )

    return DataResponse(
        data=BulkAlertActionResponse(
            success_count=success,
            failed_count=failed,
            failed_ids=failed_ids,
        )
    )


# =============================================================================
# Correlation Endpoints
# =============================================================================


@router.get("/{alert_id}/correlations", response_model=DataResponse[AlertCorrelationResponse])
async def get_alert_correlations(
    alert_id: str,
    time_window_hours: int = Query(1, ge=1, le=24, description="Correlation time window"),
    service: UnifiedAlertsService = Depends(get_service),
):
    """Get correlated alerts for a given alert.

    Finds alerts that are related by:
    - Same source (data source, model)
    - Similar time frame
    - Similar severity
    """
    correlations = await service.get_alert_correlations(
        alert_id,
        time_window_hours=time_window_hours,
    )

    total_correlated = sum(len(c.related_alerts) for c in correlations)

    return DataResponse(
        data=AlertCorrelationResponse(
            correlations=correlations,
            total_correlated=total_correlated,
        )
    )
