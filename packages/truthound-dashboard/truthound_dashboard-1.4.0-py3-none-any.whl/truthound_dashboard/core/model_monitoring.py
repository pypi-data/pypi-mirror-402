"""Model monitoring service.

This module provides services for ML model monitoring,
including model registration, prediction recording, metrics aggregation,
and alert management with database persistence.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any
import statistics

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.db import BaseRepository
from truthound_dashboard.db.models import (
    AlertSeverityLevel,
    ModelAlert,
    ModelAlertHandler,
    ModelAlertRule,
    ModelMetric,
    ModelPrediction,
    ModelStatus,
    MonitoredModel,
)


# =============================================================================
# Repositories
# =============================================================================


class MonitoredModelRepository(BaseRepository[MonitoredModel]):
    """Repository for MonitoredModel operations."""

    model = MonitoredModel

    async def get_by_name(self, name: str) -> MonitoredModel | None:
        """Get model by name."""
        result = await self.session.execute(
            select(MonitoredModel).where(MonitoredModel.name == name)
        )
        return result.scalar_one_or_none()

    async def get_by_status(
        self,
        status: str,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[MonitoredModel]:
        """Get models by status."""
        result = await self.session.execute(
            select(MonitoredModel)
            .where(MonitoredModel.status == status)
            .order_by(MonitoredModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_active_models(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[MonitoredModel]:
        """Get all active models."""
        return await self.get_by_status(
            ModelStatus.ACTIVE.value, offset=offset, limit=limit
        )

    async def count_by_status(self, status: str) -> int:
        """Count models by status."""
        return await self.count(filters=[MonitoredModel.status == status])


class ModelPredictionRepository(BaseRepository[ModelPrediction]):
    """Repository for ModelPrediction operations."""

    model = ModelPrediction

    async def get_by_model_id(
        self,
        model_id: str,
        *,
        offset: int = 0,
        limit: int = 100,
        since: datetime | None = None,
    ) -> Sequence[ModelPrediction]:
        """Get predictions for a model."""
        query = (
            select(ModelPrediction)
            .where(ModelPrediction.model_id == model_id)
            .order_by(ModelPrediction.recorded_at.desc())
        )

        if since:
            query = query.where(ModelPrediction.recorded_at >= since)

        result = await self.session.execute(
            query.offset(offset).limit(limit)
        )
        return result.scalars().all()

    async def count_by_model(
        self,
        model_id: str,
        since: datetime | None = None,
    ) -> int:
        """Count predictions for a model."""
        filters = [ModelPrediction.model_id == model_id]
        if since:
            filters.append(ModelPrediction.recorded_at >= since)
        return await self.count(filters=filters)

    async def get_latencies(
        self,
        model_id: str,
        since: datetime,
    ) -> list[float]:
        """Get latency values for a model within time range."""
        result = await self.session.execute(
            select(ModelPrediction.latency_ms)
            .where(
                and_(
                    ModelPrediction.model_id == model_id,
                    ModelPrediction.recorded_at >= since,
                    ModelPrediction.latency_ms.isnot(None),
                )
            )
            .order_by(ModelPrediction.recorded_at.desc())
        )
        return [r[0] for r in result.fetchall() if r[0] is not None]


class ModelMetricRepository(BaseRepository[ModelMetric]):
    """Repository for ModelMetric operations."""

    model = ModelMetric

    async def get_by_model_id(
        self,
        model_id: str,
        *,
        metric_type: str | None = None,
        since: datetime | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[ModelMetric]:
        """Get metrics for a model."""
        query = (
            select(ModelMetric)
            .where(ModelMetric.model_id == model_id)
            .order_by(ModelMetric.recorded_at.desc())
        )

        if metric_type:
            query = query.where(ModelMetric.metric_type == metric_type)
        if since:
            query = query.where(ModelMetric.recorded_at >= since)

        result = await self.session.execute(
            query.offset(offset).limit(limit)
        )
        return result.scalars().all()

    async def record_metric(
        self,
        model_id: str,
        metric_type: str,
        metric_name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> ModelMetric:
        """Record a new metric."""
        return await self.create(
            model_id=model_id,
            metric_type=metric_type,
            metric_name=metric_name,
            value=value,
            labels=labels,
        )


class ModelAlertRuleRepository(BaseRepository[ModelAlertRule]):
    """Repository for ModelAlertRule operations."""

    model = ModelAlertRule

    async def get_by_model_id(
        self,
        model_id: str,
        *,
        active_only: bool = False,
    ) -> Sequence[ModelAlertRule]:
        """Get alert rules for a model."""
        query = select(ModelAlertRule).where(ModelAlertRule.model_id == model_id)

        if active_only:
            query = query.where(ModelAlertRule.is_active == True)

        result = await self.session.execute(
            query.order_by(ModelAlertRule.created_at.desc())
        )
        return result.scalars().all()

    async def get_active_rules(self) -> Sequence[ModelAlertRule]:
        """Get all active rules."""
        result = await self.session.execute(
            select(ModelAlertRule)
            .where(ModelAlertRule.is_active == True)
            .order_by(ModelAlertRule.created_at.desc())
        )
        return result.scalars().all()


class ModelAlertHandlerRepository(BaseRepository[ModelAlertHandler]):
    """Repository for ModelAlertHandler operations."""

    model = ModelAlertHandler

    async def get_active_handlers(self) -> Sequence[ModelAlertHandler]:
        """Get all active handlers."""
        result = await self.session.execute(
            select(ModelAlertHandler)
            .where(ModelAlertHandler.is_active == True)
            .order_by(ModelAlertHandler.created_at.desc())
        )
        return result.scalars().all()

    async def get_by_type(
        self,
        handler_type: str,
    ) -> Sequence[ModelAlertHandler]:
        """Get handlers by type."""
        result = await self.session.execute(
            select(ModelAlertHandler)
            .where(ModelAlertHandler.handler_type == handler_type)
            .order_by(ModelAlertHandler.created_at.desc())
        )
        return result.scalars().all()


class ModelAlertRepository(BaseRepository[ModelAlert]):
    """Repository for ModelAlert operations."""

    model = ModelAlert

    async def get_by_model_id(
        self,
        model_id: str,
        *,
        active_only: bool = False,
        severity: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[ModelAlert]:
        """Get alerts for a model."""
        query = (
            select(ModelAlert)
            .where(ModelAlert.model_id == model_id)
            .order_by(ModelAlert.created_at.desc())
        )

        if active_only:
            query = query.where(ModelAlert.resolved == False)
        if severity:
            query = query.where(ModelAlert.severity == severity)

        result = await self.session.execute(
            query.offset(offset).limit(limit)
        )
        return result.scalars().all()

    async def get_active_alerts(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[ModelAlert]:
        """Get all active (unresolved) alerts."""
        result = await self.session.execute(
            select(ModelAlert)
            .where(ModelAlert.resolved == False)
            .order_by(ModelAlert.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_active(self, model_id: str | None = None) -> int:
        """Count active alerts."""
        filters = [ModelAlert.resolved == False]
        if model_id:
            filters.append(ModelAlert.model_id == model_id)
        return await self.count(filters=filters)


# =============================================================================
# Service
# =============================================================================


class ModelMonitoringService:
    """Service for ML model monitoring.

    Provides functionality for:
    - Model registration and management
    - Prediction recording and metrics
    - Alert rules and handlers
    - Dashboard data aggregation
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service.

        Args:
            session: Database session.
        """
        self.session = session
        self.model_repo = MonitoredModelRepository(session)
        self.prediction_repo = ModelPredictionRepository(session)
        self.metric_repo = ModelMetricRepository(session)
        self.rule_repo = ModelAlertRuleRepository(session)
        self.handler_repo = ModelAlertHandlerRepository(session)
        self.alert_repo = ModelAlertRepository(session)

    # =========================================================================
    # Model Registration
    # =========================================================================

    async def register_model(
        self,
        name: str,
        *,
        version: str = "1.0.0",
        description: str | None = None,
        config: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MonitoredModel:
        """Register a new model for monitoring.

        Args:
            name: Model name.
            version: Model version.
            description: Model description.
            config: Monitoring configuration.
            metadata: Additional metadata.

        Returns:
            Created MonitoredModel.
        """
        return await self.model_repo.create(
            name=name,
            version=version,
            description=description,
            config=config or {},
            metadata_json=metadata,
            status=ModelStatus.ACTIVE.value,
            prediction_count=0,
            health_score=100.0,
        )

    async def get_model(self, model_id: str) -> MonitoredModel | None:
        """Get a model by ID."""
        return await self.model_repo.get_by_id(model_id)

    async def get_model_by_name(self, name: str) -> MonitoredModel | None:
        """Get a model by name."""
        return await self.model_repo.get_by_name(name)

    async def list_models(
        self,
        *,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[MonitoredModel], int]:
        """List models with pagination.

        Args:
            status: Optional status filter.
            offset: Number to skip.
            limit: Maximum to return.

        Returns:
            Tuple of (models, total_count).
        """
        filters = []
        if status:
            filters.append(MonitoredModel.status == status)

        models = await self.model_repo.list(
            offset=offset,
            limit=limit,
            filters=filters if filters else None,
        )
        total = await self.model_repo.count(filters=filters if filters else None)

        return models, total

    async def update_model(
        self,
        model_id: str,
        **updates: Any,
    ) -> MonitoredModel | None:
        """Update a model.

        Args:
            model_id: Model ID.
            **updates: Fields to update.

        Returns:
            Updated model or None if not found.
        """
        model = await self.model_repo.get_by_id(model_id)
        if model is None:
            return None

        for key, value in updates.items():
            if hasattr(model, key) and value is not None:
                setattr(model, key, value)

        await self.session.flush()
        return model

    async def delete_model(self, model_id: str) -> bool:
        """Delete a model."""
        return await self.model_repo.delete(model_id)

    async def pause_model(self, model_id: str) -> MonitoredModel | None:
        """Pause model monitoring."""
        model = await self.model_repo.get_by_id(model_id)
        if model:
            model.pause()
            await self.session.flush()
        return model

    async def resume_model(self, model_id: str) -> MonitoredModel | None:
        """Resume model monitoring."""
        model = await self.model_repo.get_by_id(model_id)
        if model:
            model.resume()
            await self.session.flush()
        return model

    # =========================================================================
    # Prediction Recording
    # =========================================================================

    async def record_prediction(
        self,
        model_id: str,
        features: dict[str, Any],
        prediction: Any,
        *,
        actual: Any | None = None,
        latency_ms: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ModelPrediction:
        """Record a model prediction.

        Args:
            model_id: Model ID.
            features: Input features.
            prediction: Model output.
            actual: Actual value (optional).
            latency_ms: Prediction latency.
            metadata: Additional metadata.

        Returns:
            Created ModelPrediction.

        Raises:
            ValueError: If model not found.
        """
        model = await self.model_repo.get_by_id(model_id)
        if model is None:
            raise ValueError(f"Model '{model_id}' not found")

        # Create prediction record
        pred = await self.prediction_repo.create(
            model_id=model_id,
            features=features,
            prediction=prediction,
            actual=actual,
            latency_ms=latency_ms,
            metadata_json=metadata,
        )

        # Update model stats
        model.record_prediction()
        await self.session.flush()

        # Record latency metric if available
        if latency_ms is not None:
            await self.metric_repo.record_metric(
                model_id=model_id,
                metric_type="latency",
                metric_name="latency_ms",
                value=latency_ms,
            )

        return pred

    async def get_predictions(
        self,
        model_id: str,
        *,
        offset: int = 0,
        limit: int = 100,
        hours: int | None = None,
    ) -> Sequence[ModelPrediction]:
        """Get predictions for a model."""
        since = None
        if hours:
            since = datetime.utcnow() - timedelta(hours=hours)

        return await self.prediction_repo.get_by_model_id(
            model_id, offset=offset, limit=limit, since=since
        )

    # =========================================================================
    # Metrics
    # =========================================================================

    async def get_model_metrics(
        self,
        model_id: str,
        hours: int = 24,
    ) -> dict[str, Any]:
        """Get aggregated metrics for a model.

        Args:
            model_id: Model ID.
            hours: Time range in hours.

        Returns:
            Dictionary with metric summaries and time series.
        """
        model = await self.model_repo.get_by_id(model_id)
        if model is None:
            raise ValueError(f"Model '{model_id}' not found")

        cutoff = datetime.utcnow() - timedelta(hours=hours)

        # Get latency data
        latencies = await self.prediction_repo.get_latencies(model_id, cutoff)

        # Get prediction count
        pred_count = await self.prediction_repo.count_by_model(model_id, cutoff)

        metrics = []
        data_points: dict[str, list[dict[str, Any]]] = {}

        # Latency metrics
        if latencies:
            sorted_latencies = sorted(latencies)
            n = len(sorted_latencies)

            metrics.append({
                "name": "latency_ms",
                "type": "latency",
                "count": n,
                "min_value": min(latencies),
                "max_value": max(latencies),
                "avg_value": statistics.mean(latencies),
                "p50_value": sorted_latencies[n // 2] if n > 0 else None,
                "p95_value": sorted_latencies[int(n * 0.95)] if n > 0 else None,
                "p99_value": sorted_latencies[int(n * 0.99)] if n > 0 else None,
                "last_value": latencies[0] if latencies else None,
            })

        # Throughput metric
        metrics.append({
            "name": "throughput",
            "type": "throughput",
            "count": 1,
            "last_value": pred_count / max(hours, 1),
        })

        return {
            "model_id": model_id,
            "model_name": model.name,
            "time_range_hours": hours,
            "metrics": metrics,
            "data_points": data_points,
        }

    async def record_metric(
        self,
        model_id: str,
        metric_type: str,
        metric_name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> ModelMetric:
        """Record a custom metric."""
        return await self.metric_repo.record_metric(
            model_id=model_id,
            metric_type=metric_type,
            metric_name=metric_name,
            value=value,
            labels=labels,
        )

    # =========================================================================
    # Alert Rules
    # =========================================================================

    async def create_alert_rule(
        self,
        model_id: str,
        name: str,
        rule_type: str,
        config: dict[str, Any],
        *,
        severity: str = "warning",
    ) -> ModelAlertRule:
        """Create an alert rule.

        Args:
            model_id: Model ID.
            name: Rule name.
            rule_type: Rule type (threshold, statistical, trend).
            config: Rule configuration.
            severity: Alert severity.

        Returns:
            Created ModelAlertRule.

        Raises:
            ValueError: If model not found.
        """
        model = await self.model_repo.get_by_id(model_id)
        if model is None:
            raise ValueError(f"Model '{model_id}' not found")

        return await self.rule_repo.create(
            model_id=model_id,
            name=name,
            rule_type=rule_type,
            severity=severity,
            config=config,
            is_active=True,
        )

    async def get_alert_rules(
        self,
        model_id: str | None = None,
        active_only: bool = False,
    ) -> Sequence[ModelAlertRule]:
        """Get alert rules."""
        if model_id:
            return await self.rule_repo.get_by_model_id(model_id, active_only=active_only)
        if active_only:
            return await self.rule_repo.get_active_rules()
        return await self.rule_repo.list()

    async def update_alert_rule(
        self,
        rule_id: str,
        **updates: Any,
    ) -> ModelAlertRule | None:
        """Update an alert rule."""
        rule = await self.rule_repo.get_by_id(rule_id)
        if rule is None:
            return None

        for key, value in updates.items():
            if hasattr(rule, key) and value is not None:
                setattr(rule, key, value)

        await self.session.flush()
        return rule

    async def delete_alert_rule(self, rule_id: str) -> bool:
        """Delete an alert rule."""
        return await self.rule_repo.delete(rule_id)

    # =========================================================================
    # Alert Handlers
    # =========================================================================

    async def create_alert_handler(
        self,
        name: str,
        handler_type: str,
        config: dict[str, Any],
    ) -> ModelAlertHandler:
        """Create an alert handler."""
        return await self.handler_repo.create(
            name=name,
            handler_type=handler_type,
            config=config,
            is_active=True,
        )

    async def get_alert_handlers(
        self,
        active_only: bool = False,
    ) -> Sequence[ModelAlertHandler]:
        """Get alert handlers."""
        if active_only:
            return await self.handler_repo.get_active_handlers()
        return await self.handler_repo.list()

    async def update_alert_handler(
        self,
        handler_id: str,
        **updates: Any,
    ) -> ModelAlertHandler | None:
        """Update an alert handler."""
        handler = await self.handler_repo.get_by_id(handler_id)
        if handler is None:
            return None

        for key, value in updates.items():
            if hasattr(handler, key) and value is not None:
                setattr(handler, key, value)

        await self.session.flush()
        return handler

    async def delete_alert_handler(self, handler_id: str) -> bool:
        """Delete an alert handler."""
        return await self.handler_repo.delete(handler_id)

    # =========================================================================
    # Alerts
    # =========================================================================

    async def create_alert(
        self,
        model_id: str,
        rule_id: str,
        message: str,
        *,
        severity: str = "warning",
        metric_value: float | None = None,
        threshold_value: float | None = None,
    ) -> ModelAlert:
        """Create an alert instance."""
        return await self.alert_repo.create(
            model_id=model_id,
            rule_id=rule_id,
            severity=severity,
            message=message,
            metric_value=metric_value,
            threshold_value=threshold_value,
            acknowledged=False,
            resolved=False,
        )

    async def get_alerts(
        self,
        model_id: str | None = None,
        active_only: bool = False,
        severity: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[ModelAlert], int]:
        """Get alerts with pagination."""
        if model_id:
            alerts = await self.alert_repo.get_by_model_id(
                model_id, active_only=active_only, severity=severity,
                offset=offset, limit=limit
            )
            total = await self.alert_repo.count_active(model_id) if active_only else len(alerts)
        else:
            if active_only:
                alerts = await self.alert_repo.get_active_alerts(offset=offset, limit=limit)
                total = await self.alert_repo.count_active()
            else:
                alerts = await self.alert_repo.list(offset=offset, limit=limit)
                total = await self.alert_repo.count()

        return alerts, total

    async def acknowledge_alert(
        self,
        alert_id: str,
        actor: str,
    ) -> ModelAlert | None:
        """Acknowledge an alert."""
        alert = await self.alert_repo.get_by_id(alert_id)
        if alert is None:
            return None

        alert.acknowledge(actor)
        await self.session.flush()
        return alert

    async def resolve_alert(self, alert_id: str) -> ModelAlert | None:
        """Resolve an alert."""
        alert = await self.alert_repo.get_by_id(alert_id)
        if alert is None:
            return None

        alert.resolve()
        await self.session.flush()
        return alert

    # =========================================================================
    # Rule Evaluation
    # =========================================================================

    async def evaluate_rules(self, model_id: str) -> list[ModelAlert]:
        """Evaluate all active rules for a model and create alerts if triggered.

        Args:
            model_id: Model ID.

        Returns:
            List of created alerts.
        """
        model = await self.model_repo.get_by_id(model_id)
        if model is None:
            return []

        rules = await self.rule_repo.get_by_model_id(model_id, active_only=True)
        metrics = await self.get_model_metrics(model_id, hours=1)
        alerts = []

        for rule in rules:
            triggered, value, threshold = self._evaluate_rule(rule, metrics)
            if triggered:
                rule.trigger()
                alert = await self.create_alert(
                    model_id=model_id,
                    rule_id=rule.id,
                    message=f"Rule '{rule.name}' triggered: value={value}, threshold={threshold}",
                    severity=rule.severity,
                    metric_value=value,
                    threshold_value=threshold,
                )
                alerts.append(alert)

        await self.session.flush()
        return alerts

    def _evaluate_rule(
        self,
        rule: ModelAlertRule,
        metrics: dict[str, Any],
    ) -> tuple[bool, float | None, float | None]:
        """Evaluate a single rule against metrics.

        Args:
            rule: Alert rule to evaluate.
            metrics: Aggregated metrics.

        Returns:
            Tuple of (triggered, value, threshold).
        """
        config = rule.config
        rule_type = rule.rule_type

        if rule_type == "threshold":
            metric_name = config.get("metric_name", "latency_ms")
            threshold = config.get("threshold", 0)
            comparison = config.get("comparison", "gt")

            # Find metric value
            value = None
            for m in metrics.get("metrics", []):
                if m.get("name") == metric_name:
                    value = m.get("last_value") or m.get("avg_value")
                    break

            if value is None:
                return False, None, threshold

            # Compare
            if comparison == "gt":
                triggered = value > threshold
            elif comparison == "lt":
                triggered = value < threshold
            elif comparison == "gte":
                triggered = value >= threshold
            elif comparison == "lte":
                triggered = value <= threshold
            elif comparison == "eq":
                triggered = value == threshold
            else:
                triggered = False

            return triggered, value, threshold

        elif rule_type == "statistical":
            # Statistical anomaly detection based on standard deviations
            metric_name = config.get("metric_name", "latency_ms")
            std_devs = config.get("std_devs", 3.0)

            for m in metrics.get("metrics", []):
                if m.get("name") == metric_name:
                    avg = m.get("avg_value")
                    p95 = m.get("p95_value")
                    if avg and p95:
                        # Simple heuristic: if p95 is more than std_devs times avg
                        if p95 > avg * (1 + std_devs * 0.1):
                            return True, p95, avg * (1 + std_devs * 0.1)
                    break

            return False, None, None

        return False, None, None

    # =========================================================================
    # Dashboard Data
    # =========================================================================

    async def get_monitoring_overview(self) -> dict[str, Any]:
        """Get monitoring overview for dashboard.

        Returns:
            Overview statistics.
        """
        models, total_models = await self.list_models()
        cutoff_24h = datetime.utcnow() - timedelta(hours=24)

        # Count predictions in last 24h
        total_predictions = 0
        for model in models:
            count = await self.prediction_repo.count_by_model(model.id, cutoff_24h)
            total_predictions += count

        # Count active alerts
        active_alerts = await self.alert_repo.count_active()

        # Count models by status
        active_count = await self.model_repo.count_by_status(ModelStatus.ACTIVE.value)
        degraded_count = await self.model_repo.count_by_status(ModelStatus.DEGRADED.value)

        # Count models with drift
        models_with_drift = sum(
            1 for m in models
            if (m.current_drift_score or 0) > 0.1
        )

        # Average latency
        all_latencies = []
        for model in models:
            latencies = await self.prediction_repo.get_latencies(model.id, cutoff_24h)
            all_latencies.extend(latencies)

        avg_latency = statistics.mean(all_latencies) if all_latencies else None

        return {
            "total_models": total_models,
            "active_models": active_count,
            "degraded_models": degraded_count,
            "total_predictions_24h": total_predictions,
            "active_alerts": active_alerts,
            "models_with_drift": models_with_drift,
            "avg_latency_ms": avg_latency,
        }

    async def get_model_dashboard(self, model_id: str) -> dict[str, Any]:
        """Get dashboard data for a specific model.

        Args:
            model_id: Model ID.

        Returns:
            Dashboard data dictionary.

        Raises:
            ValueError: If model not found.
        """
        model = await self.model_repo.get_by_id(model_id)
        if model is None:
            raise ValueError(f"Model '{model_id}' not found")

        metrics = await self.get_model_metrics(model_id, hours=24)
        alerts, _ = await self.get_alerts(model_id, active_only=True)

        # Recent predictions count
        cutoff = datetime.utcnow() - timedelta(hours=1)
        recent_predictions = await self.prediction_repo.count_by_model(model_id, cutoff)

        # Health status
        if model.status == ModelStatus.DEGRADED.value:
            health_status = "degraded"
        elif model.status == ModelStatus.ERROR.value:
            health_status = "error"
        elif alerts:
            health_status = "warning"
        else:
            health_status = "healthy"

        return {
            "model": self._model_to_dict(model),
            "metrics": metrics,
            "active_alerts": [self._alert_to_dict(a) for a in alerts],
            "recent_predictions": recent_predictions,
            "health_status": health_status,
        }

    # =========================================================================
    # Helpers
    # =========================================================================

    def _model_to_dict(self, model: MonitoredModel) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": model.id,
            "name": model.name,
            "version": model.version,
            "description": model.description,
            "status": model.status,
            "config": model.config,
            "metadata": model.metadata_json,
            "prediction_count": model.prediction_count,
            "last_prediction_at": model.last_prediction_at.isoformat() if model.last_prediction_at else None,
            "current_drift_score": model.current_drift_score,
            "health_score": model.health_score,
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None,
        }

    def _alert_to_dict(self, alert: ModelAlert) -> dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "id": alert.id,
            "model_id": alert.model_id,
            "rule_id": alert.rule_id,
            "severity": alert.severity,
            "message": alert.message,
            "metric_value": alert.metric_value,
            "threshold_value": alert.threshold_value,
            "acknowledged": alert.acknowledged,
            "acknowledged_by": alert.acknowledged_by,
            "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
            "resolved": alert.resolved,
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
            "updated_at": alert.updated_at.isoformat() if alert.updated_at else None,
        }
