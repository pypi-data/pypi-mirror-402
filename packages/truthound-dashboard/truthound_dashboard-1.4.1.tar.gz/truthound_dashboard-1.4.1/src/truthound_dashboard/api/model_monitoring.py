"""API endpoints for ML Model Monitoring.

Provides REST API for:
- Model registration and management
- Prediction recording and metrics
- Alert rules and handlers
- Dashboard data

All data is persisted to the database.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.model_monitoring import ModelMonitoringService
from ..db import get_session
from ..schemas.base import DataResponse
from ..schemas.model_monitoring import (
    AcknowledgeAlertRequest,
    AlertHandlerListResponse,
    AlertHandlerResponse,
    AlertInstance,
    AlertListResponse,
    AlertRuleListResponse,
    AlertRuleResponse,
    AlertSeverity,
    CreateAlertHandlerRequest,
    CreateAlertRuleRequest,
    MetricsResponse,
    MetricSummary,
    ModelDashboardData,
    ModelStatus,
    MonitoringOverview,
    RecordPredictionRequest,
    RecordPredictionResponse,
    RegisteredModelListResponse,
    RegisteredModelResponse,
    RegisterModelRequest,
    UpdateAlertHandlerRequest,
    UpdateAlertRuleRequest,
    UpdateModelRequest,
)

router = APIRouter(prefix="/model-monitoring", tags=["model-monitoring"])


def get_service(session: AsyncSession = Depends(get_session)) -> ModelMonitoringService:
    """Get model monitoring service instance."""
    return ModelMonitoringService(session)


# =============================================================================
# Model Registration Endpoints
# =============================================================================


@router.get("/models", response_model=DataResponse[RegisteredModelListResponse])
async def list_models(
    status: ModelStatus | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: ModelMonitoringService = Depends(get_service),
):
    """List all registered models."""
    status_filter = status.value if status else None
    models, total = await service.list_models(
        status=status_filter, offset=offset, limit=limit
    )

    items = [
        RegisteredModelResponse(
            id=m.id,
            name=m.name,
            version=m.version,
            description=m.description or "",
            status=ModelStatus(m.status),
            config=m.config,
            metadata=m.metadata_json or {},
            prediction_count=m.prediction_count,
            last_prediction_at=m.last_prediction_at,
            current_drift_score=m.current_drift_score,
            health_score=m.health_score,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
        for m in models
    ]

    return DataResponse(
        data=RegisteredModelListResponse(
            items=items,
            total=total,
            offset=offset,
            limit=limit,
        )
    )


@router.post("/models", response_model=DataResponse[RegisteredModelResponse])
async def register_model(
    request: RegisterModelRequest,
    service: ModelMonitoringService = Depends(get_service),
):
    """Register a new model for monitoring."""
    model = await service.register_model(
        name=request.name,
        version=request.version,
        description=request.description,
        config=request.config.model_dump() if request.config else None,
        metadata=request.metadata,
    )

    return DataResponse(
        data=RegisteredModelResponse(
            id=model.id,
            name=model.name,
            version=model.version,
            description=model.description or "",
            status=ModelStatus(model.status),
            config=model.config,
            metadata=model.metadata_json or {},
            prediction_count=model.prediction_count,
            last_prediction_at=model.last_prediction_at,
            current_drift_score=model.current_drift_score,
            health_score=model.health_score,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
    )


@router.get("/models/{model_id}", response_model=DataResponse[RegisteredModelResponse])
async def get_model(
    model_id: str,
    service: ModelMonitoringService = Depends(get_service),
):
    """Get a registered model by ID."""
    model = await service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    return DataResponse(
        data=RegisteredModelResponse(
            id=model.id,
            name=model.name,
            version=model.version,
            description=model.description or "",
            status=ModelStatus(model.status),
            config=model.config,
            metadata=model.metadata_json or {},
            prediction_count=model.prediction_count,
            last_prediction_at=model.last_prediction_at,
            current_drift_score=model.current_drift_score,
            health_score=model.health_score,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
    )


@router.put("/models/{model_id}", response_model=DataResponse[RegisteredModelResponse])
async def update_model(
    model_id: str,
    request: UpdateModelRequest,
    service: ModelMonitoringService = Depends(get_service),
):
    """Update a registered model."""
    updates = {}
    if request.name is not None:
        updates["name"] = request.name
    if request.version is not None:
        updates["version"] = request.version
    if request.description is not None:
        updates["description"] = request.description
    if request.status is not None:
        updates["status"] = request.status.value
    if request.config is not None:
        updates["config"] = request.config.model_dump()
    if request.metadata is not None:
        updates["metadata_json"] = request.metadata

    model = await service.update_model(model_id, **updates)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    return DataResponse(
        data=RegisteredModelResponse(
            id=model.id,
            name=model.name,
            version=model.version,
            description=model.description or "",
            status=ModelStatus(model.status),
            config=model.config,
            metadata=model.metadata_json or {},
            prediction_count=model.prediction_count,
            last_prediction_at=model.last_prediction_at,
            current_drift_score=model.current_drift_score,
            health_score=model.health_score,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
    )


@router.delete("/models/{model_id}")
async def delete_model(
    model_id: str,
    service: ModelMonitoringService = Depends(get_service),
):
    """Delete a registered model."""
    deleted = await service.delete_model(model_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Model not found")

    return {"success": True, "message": "Model deleted"}


@router.post("/models/{model_id}/pause")
async def pause_model(
    model_id: str,
    service: ModelMonitoringService = Depends(get_service),
):
    """Pause monitoring for a model."""
    model = await service.pause_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    return {"success": True, "message": "Model monitoring paused"}


@router.post("/models/{model_id}/resume")
async def resume_model(
    model_id: str,
    service: ModelMonitoringService = Depends(get_service),
):
    """Resume monitoring for a model."""
    model = await service.resume_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    return {"success": True, "message": "Model monitoring resumed"}


# =============================================================================
# Prediction Recording Endpoints
# =============================================================================


@router.post(
    "/models/{model_id}/predictions",
    response_model=DataResponse[RecordPredictionResponse],
)
async def record_prediction(
    model_id: str,
    request: RecordPredictionRequest,
    service: ModelMonitoringService = Depends(get_service),
):
    """Record a model prediction."""
    try:
        prediction = await service.record_prediction(
            model_id=model_id,
            features=request.features,
            prediction=request.prediction,
            actual=request.actual,
            latency_ms=request.latency_ms,
            metadata=request.metadata,
        )

        return DataResponse(
            data=RecordPredictionResponse(
                id=prediction.id,
                model_id=model_id,
                recorded_at=prediction.recorded_at,
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/models/{model_id}/metrics", response_model=DataResponse[MetricsResponse])
async def get_model_metrics(
    model_id: str,
    hours: int = Query(24, ge=1, le=168),
    service: ModelMonitoringService = Depends(get_service),
):
    """Get metrics for a model."""
    try:
        metrics_data = await service.get_model_metrics(model_id, hours)

        return DataResponse(
            data=MetricsResponse(
                model_id=metrics_data["model_id"],
                model_name=metrics_data["model_name"],
                time_range_hours=metrics_data["time_range_hours"],
                metrics=[MetricSummary(**m) for m in metrics_data["metrics"]],
                data_points=metrics_data["data_points"],
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# Alert Rule Endpoints
# =============================================================================


@router.get("/rules", response_model=DataResponse[AlertRuleListResponse])
async def list_alert_rules(
    model_id: str | None = None,
    active_only: bool = False,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: ModelMonitoringService = Depends(get_service),
):
    """List all alert rules."""
    rules = await service.get_alert_rules(model_id=model_id, active_only=active_only)

    # Apply pagination
    total = len(rules)
    paginated = list(rules)[offset : offset + limit]

    items = [
        AlertRuleResponse(
            id=r.id,
            name=r.name,
            model_id=r.model_id,
            rule_type=r.rule_type,
            severity=AlertSeverity(r.severity),
            config=r.config,
            is_active=r.is_active,
            last_triggered_at=r.last_triggered_at,
            trigger_count=r.trigger_count,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in paginated
    ]

    return DataResponse(
        data=AlertRuleListResponse(
            items=items,
            total=total,
            offset=offset,
            limit=limit,
        )
    )


@router.post("/rules", response_model=DataResponse[AlertRuleResponse])
async def create_alert_rule(
    request: CreateAlertRuleRequest,
    service: ModelMonitoringService = Depends(get_service),
):
    """Create a new alert rule."""
    try:
        rule = await service.create_alert_rule(
            model_id=request.model_id,
            name=request.name,
            rule_type=request.rule_type.value,
            config=request.config,
            severity=request.severity.value,
        )

        return DataResponse(
            data=AlertRuleResponse(
                id=rule.id,
                name=rule.name,
                model_id=rule.model_id,
                rule_type=rule.rule_type,
                severity=AlertSeverity(rule.severity),
                config=rule.config,
                is_active=rule.is_active,
                last_triggered_at=rule.last_triggered_at,
                trigger_count=rule.trigger_count,
                created_at=rule.created_at,
                updated_at=rule.updated_at,
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/rules/{rule_id}", response_model=DataResponse[AlertRuleResponse])
async def get_alert_rule(
    rule_id: str,
    service: ModelMonitoringService = Depends(get_service),
):
    """Get an alert rule by ID."""
    rules = await service.get_alert_rules()
    rule = next((r for r in rules if r.id == rule_id), None)

    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    return DataResponse(
        data=AlertRuleResponse(
            id=rule.id,
            name=rule.name,
            model_id=rule.model_id,
            rule_type=rule.rule_type,
            severity=AlertSeverity(rule.severity),
            config=rule.config,
            is_active=rule.is_active,
            last_triggered_at=rule.last_triggered_at,
            trigger_count=rule.trigger_count,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
        )
    )


@router.put("/rules/{rule_id}", response_model=DataResponse[AlertRuleResponse])
async def update_alert_rule(
    rule_id: str,
    request: UpdateAlertRuleRequest,
    service: ModelMonitoringService = Depends(get_service),
):
    """Update an alert rule."""
    updates = {}
    if request.name is not None:
        updates["name"] = request.name
    if request.severity is not None:
        updates["severity"] = request.severity.value
    if request.config is not None:
        updates["config"] = request.config
    if request.is_active is not None:
        updates["is_active"] = request.is_active

    rule = await service.update_alert_rule(rule_id, **updates)
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    return DataResponse(
        data=AlertRuleResponse(
            id=rule.id,
            name=rule.name,
            model_id=rule.model_id,
            rule_type=rule.rule_type,
            severity=AlertSeverity(rule.severity),
            config=rule.config,
            is_active=rule.is_active,
            last_triggered_at=rule.last_triggered_at,
            trigger_count=rule.trigger_count,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
        )
    )


@router.delete("/rules/{rule_id}")
async def delete_alert_rule(
    rule_id: str,
    service: ModelMonitoringService = Depends(get_service),
):
    """Delete an alert rule."""
    deleted = await service.delete_alert_rule(rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    return {"success": True, "message": "Alert rule deleted"}


# =============================================================================
# Alert Handler Endpoints
# =============================================================================


@router.get("/handlers", response_model=DataResponse[AlertHandlerListResponse])
async def list_alert_handlers(
    active_only: bool = False,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: ModelMonitoringService = Depends(get_service),
):
    """List all alert handlers."""
    handlers = await service.get_alert_handlers(active_only=active_only)

    # Apply pagination
    total = len(handlers)
    paginated = list(handlers)[offset : offset + limit]

    items = [
        AlertHandlerResponse(
            id=h.id,
            name=h.name,
            handler_type=h.handler_type,
            config=h.config,
            is_active=h.is_active,
            last_sent_at=h.last_sent_at,
            send_count=h.send_count,
            failure_count=h.failure_count,
            created_at=h.created_at,
            updated_at=h.updated_at,
        )
        for h in paginated
    ]

    return DataResponse(
        data=AlertHandlerListResponse(
            items=items,
            total=total,
            offset=offset,
            limit=limit,
        )
    )


@router.post("/handlers", response_model=DataResponse[AlertHandlerResponse])
async def create_alert_handler(
    request: CreateAlertHandlerRequest,
    service: ModelMonitoringService = Depends(get_service),
):
    """Create a new alert handler."""
    handler = await service.create_alert_handler(
        name=request.name,
        handler_type=request.handler_type.value,
        config=request.config,
    )

    return DataResponse(
        data=AlertHandlerResponse(
            id=handler.id,
            name=handler.name,
            handler_type=handler.handler_type,
            config=handler.config,
            is_active=handler.is_active,
            last_sent_at=handler.last_sent_at,
            send_count=handler.send_count,
            failure_count=handler.failure_count,
            created_at=handler.created_at,
            updated_at=handler.updated_at,
        )
    )


@router.put("/handlers/{handler_id}", response_model=DataResponse[AlertHandlerResponse])
async def update_alert_handler(
    handler_id: str,
    request: UpdateAlertHandlerRequest,
    service: ModelMonitoringService = Depends(get_service),
):
    """Update an alert handler."""
    updates = {}
    if request.name is not None:
        updates["name"] = request.name
    if request.config is not None:
        updates["config"] = request.config
    if request.is_active is not None:
        updates["is_active"] = request.is_active

    handler = await service.update_alert_handler(handler_id, **updates)
    if not handler:
        raise HTTPException(status_code=404, detail="Alert handler not found")

    return DataResponse(
        data=AlertHandlerResponse(
            id=handler.id,
            name=handler.name,
            handler_type=handler.handler_type,
            config=handler.config,
            is_active=handler.is_active,
            last_sent_at=handler.last_sent_at,
            send_count=handler.send_count,
            failure_count=handler.failure_count,
            created_at=handler.created_at,
            updated_at=handler.updated_at,
        )
    )


@router.delete("/handlers/{handler_id}")
async def delete_alert_handler(
    handler_id: str,
    service: ModelMonitoringService = Depends(get_service),
):
    """Delete an alert handler."""
    deleted = await service.delete_alert_handler(handler_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Alert handler not found")

    return {"success": True, "message": "Alert handler deleted"}


# =============================================================================
# Alert Instance Endpoints
# =============================================================================


@router.get("/alerts", response_model=DataResponse[AlertListResponse])
async def list_alerts(
    model_id: str | None = None,
    active_only: bool = False,
    severity: AlertSeverity | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: ModelMonitoringService = Depends(get_service),
):
    """List alerts."""
    severity_filter = severity.value if severity else None
    alerts, total = await service.get_alerts(
        model_id=model_id,
        active_only=active_only,
        severity=severity_filter,
        offset=offset,
        limit=limit,
    )

    items = [
        AlertInstance(
            id=a.id,
            rule_id=a.rule_id,
            model_id=a.model_id,
            severity=AlertSeverity(a.severity),
            message=a.message,
            metric_value=a.metric_value,
            threshold_value=a.threshold_value,
            acknowledged=a.acknowledged,
            acknowledged_by=a.acknowledged_by,
            acknowledged_at=a.acknowledged_at,
            resolved=a.resolved,
            resolved_at=a.resolved_at,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in alerts
    ]

    return DataResponse(
        data=AlertListResponse(
            items=items,
            total=total,
            offset=offset,
            limit=limit,
        )
    )


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    request: AcknowledgeAlertRequest,
    service: ModelMonitoringService = Depends(get_service),
):
    """Acknowledge an alert."""
    alert = await service.acknowledge_alert(alert_id, request.actor)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if alert.acknowledged:
        return DataResponse(
            data=AlertInstance(
                id=alert.id,
                rule_id=alert.rule_id,
                model_id=alert.model_id,
                severity=AlertSeverity(alert.severity),
                message=alert.message,
                metric_value=alert.metric_value,
                threshold_value=alert.threshold_value,
                acknowledged=alert.acknowledged,
                acknowledged_by=alert.acknowledged_by,
                acknowledged_at=alert.acknowledged_at,
                resolved=alert.resolved,
                resolved_at=alert.resolved_at,
                created_at=alert.created_at,
                updated_at=alert.updated_at,
            )
        )


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    service: ModelMonitoringService = Depends(get_service),
):
    """Resolve an alert."""
    alert = await service.resolve_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return DataResponse(
        data=AlertInstance(
            id=alert.id,
            rule_id=alert.rule_id,
            model_id=alert.model_id,
            severity=AlertSeverity(alert.severity),
            message=alert.message,
            metric_value=alert.metric_value,
            threshold_value=alert.threshold_value,
            acknowledged=alert.acknowledged,
            acknowledged_by=alert.acknowledged_by,
            acknowledged_at=alert.acknowledged_at,
            resolved=alert.resolved,
            resolved_at=alert.resolved_at,
            created_at=alert.created_at,
            updated_at=alert.updated_at,
        )
    )


# =============================================================================
# Dashboard Endpoints
# =============================================================================


@router.get("/overview", response_model=DataResponse[MonitoringOverview])
async def get_monitoring_overview(
    service: ModelMonitoringService = Depends(get_service),
):
    """Get monitoring overview for dashboard."""
    overview = await service.get_monitoring_overview()

    return DataResponse(
        data=MonitoringOverview(
            total_models=overview["total_models"],
            active_models=overview["active_models"],
            degraded_models=overview["degraded_models"],
            total_predictions_24h=overview["total_predictions_24h"],
            active_alerts=overview["active_alerts"],
            models_with_drift=overview["models_with_drift"],
            avg_latency_ms=overview["avg_latency_ms"],
        )
    )


@router.get("/models/{model_id}/dashboard", response_model=DataResponse[ModelDashboardData])
async def get_model_dashboard(
    model_id: str,
    service: ModelMonitoringService = Depends(get_service),
):
    """Get dashboard data for a specific model."""
    try:
        dashboard = await service.get_model_dashboard(model_id)

        model_data = dashboard["model"]
        metrics_data = dashboard["metrics"]

        return DataResponse(
            data=ModelDashboardData(
                model=RegisteredModelResponse(
                    id=model_data["id"],
                    name=model_data["name"],
                    version=model_data["version"],
                    description=model_data["description"] or "",
                    status=ModelStatus(model_data["status"]),
                    config=model_data["config"],
                    metadata=model_data["metadata"] or {},
                    prediction_count=model_data["prediction_count"],
                    last_prediction_at=model_data["last_prediction_at"],
                    current_drift_score=model_data["current_drift_score"],
                    health_score=model_data["health_score"],
                    created_at=model_data["created_at"],
                    updated_at=model_data["updated_at"],
                ),
                metrics=MetricsResponse(
                    model_id=metrics_data["model_id"],
                    model_name=metrics_data["model_name"],
                    time_range_hours=metrics_data["time_range_hours"],
                    metrics=[MetricSummary(**m) for m in metrics_data["metrics"]],
                    data_points=metrics_data["data_points"],
                ),
                active_alerts=[
                    AlertInstance(
                        id=a["id"],
                        rule_id=a["rule_id"],
                        model_id=a["model_id"],
                        severity=AlertSeverity(a["severity"]),
                        message=a["message"],
                        metric_value=a["metric_value"],
                        threshold_value=a["threshold_value"],
                        acknowledged=a["acknowledged"],
                        acknowledged_by=a["acknowledged_by"],
                        acknowledged_at=a["acknowledged_at"],
                        resolved=a["resolved"],
                        resolved_at=a["resolved_at"],
                        created_at=a["created_at"],
                        updated_at=a["updated_at"],
                    )
                    for a in dashboard["active_alerts"]
                ],
                recent_predictions=dashboard["recent_predictions"],
                health_status=dashboard["health_status"],
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/models/{model_id}/evaluate-rules")
async def evaluate_model_rules(
    model_id: str,
    service: ModelMonitoringService = Depends(get_service),
):
    """Evaluate all active rules for a model and create alerts if triggered."""
    alerts = await service.evaluate_rules(model_id)

    return DataResponse(
        data={
            "model_id": model_id,
            "alerts_created": len(alerts),
            "alert_ids": [a.id for a in alerts],
        }
    )
