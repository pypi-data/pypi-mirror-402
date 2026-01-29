"""Unified Alerts Service.

Aggregates alerts from all monitoring systems:
- Model monitoring alerts
- Drift monitoring alerts
- Anomaly detection alerts (generated from high anomaly rates)
- Validation failures

Provides unified view, correlation, and management.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import (
    AnomalyDetection,
    BaseRepository,
    DriftAlert,
    DriftMonitor,
    ModelAlert,
    MonitoredModel,
    Source,
    Validation,
)
from ..schemas.unified_alerts import (
    AlertCorrelation,
    AlertCountBySource,
    AlertCountBySeverity,
    AlertCountByStatus,
    AlertSeverity,
    AlertSource,
    AlertStatus,
    AlertSummary,
    AlertTrendPoint,
    UnifiedAlertResponse,
)


# =============================================================================
# Helper functions
# =============================================================================


def _generate_alert_id(source: AlertSource, source_id: str) -> str:
    """Generate a unified alert ID from source info."""
    return f"{source.value}:{source_id}"


def _parse_alert_id(unified_id: str) -> tuple[AlertSource, str]:
    """Parse a unified alert ID into source and original ID."""
    parts = unified_id.split(":", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid unified alert ID: {unified_id}")
    return AlertSource(parts[0]), parts[1]


def _map_model_severity(severity: str) -> AlertSeverity:
    """Map model monitoring severity to unified severity."""
    mapping = {
        "critical": AlertSeverity.CRITICAL,
        "warning": AlertSeverity.HIGH,
        "info": AlertSeverity.INFO,
    }
    return mapping.get(severity.lower(), AlertSeverity.MEDIUM)


def _map_drift_severity(severity: str) -> AlertSeverity:
    """Map drift severity to unified severity."""
    mapping = {
        "critical": AlertSeverity.CRITICAL,
        "high": AlertSeverity.HIGH,
        "medium": AlertSeverity.MEDIUM,
        "low": AlertSeverity.LOW,
        "info": AlertSeverity.INFO,
    }
    return mapping.get(severity.lower(), AlertSeverity.MEDIUM)


def _map_drift_status(status: str) -> AlertStatus:
    """Map drift status to unified status."""
    mapping = {
        "open": AlertStatus.OPEN,
        "acknowledged": AlertStatus.ACKNOWLEDGED,
        "resolved": AlertStatus.RESOLVED,
        "ignored": AlertStatus.IGNORED,
    }
    return mapping.get(status.lower(), AlertStatus.OPEN)


# =============================================================================
# Unified Alerts Service
# =============================================================================


class UnifiedAlertsService:
    """Service for unified alert management.

    Aggregates alerts from multiple sources and provides
    a unified interface for querying and managing them.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the service.

        Args:
            session: Database session.
        """
        self.session = session

    async def get_all_alerts(
        self,
        *,
        source: AlertSource | None = None,
        severity: AlertSeverity | None = None,
        status: AlertStatus | None = None,
        source_name: str | None = None,
        time_range_hours: int | None = 24,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[UnifiedAlertResponse], int]:
        """Get all alerts from all sources.

        Args:
            source: Filter by alert source.
            severity: Filter by severity.
            status: Filter by status.
            source_name: Filter by source name (partial match).
            time_range_hours: Filter by time range.
            offset: Pagination offset.
            limit: Pagination limit.

        Returns:
            Tuple of (alerts, total count).
        """
        alerts: list[UnifiedAlertResponse] = []
        cutoff = None
        if time_range_hours:
            cutoff = datetime.utcnow() - timedelta(hours=time_range_hours)

        # Gather alerts from all sources
        if source is None or source == AlertSource.MODEL:
            model_alerts = await self._get_model_alerts(
                severity=severity,
                status=status,
                cutoff=cutoff,
            )
            alerts.extend(model_alerts)

        if source is None or source == AlertSource.DRIFT:
            drift_alerts = await self._get_drift_alerts(
                severity=severity,
                status=status,
                cutoff=cutoff,
            )
            alerts.extend(drift_alerts)

        if source is None or source == AlertSource.ANOMALY:
            anomaly_alerts = await self._get_anomaly_alerts(
                severity=severity,
                status=status,
                cutoff=cutoff,
            )
            alerts.extend(anomaly_alerts)

        if source is None or source == AlertSource.VALIDATION:
            validation_alerts = await self._get_validation_alerts(
                severity=severity,
                status=status,
                cutoff=cutoff,
            )
            alerts.extend(validation_alerts)

        # Filter by source name if provided
        if source_name:
            source_name_lower = source_name.lower()
            alerts = [a for a in alerts if source_name_lower in a.source_name.lower()]

        # Sort by created_at descending
        alerts.sort(key=lambda a: a.created_at, reverse=True)

        # Get total and paginate
        total = len(alerts)
        paginated = alerts[offset : offset + limit]

        return paginated, total

    async def get_alert_by_id(self, alert_id: str) -> UnifiedAlertResponse | None:
        """Get a specific unified alert by ID.

        Args:
            alert_id: Unified alert ID.

        Returns:
            Alert if found, None otherwise.
        """
        try:
            source, source_id = _parse_alert_id(alert_id)
        except ValueError:
            return None

        if source == AlertSource.MODEL:
            return await self._get_single_model_alert(source_id)
        elif source == AlertSource.DRIFT:
            return await self._get_single_drift_alert(source_id)
        elif source == AlertSource.ANOMALY:
            return await self._get_single_anomaly_alert(source_id)
        elif source == AlertSource.VALIDATION:
            return await self._get_single_validation_alert(source_id)

        return None

    async def get_alert_summary(self, time_range_hours: int = 24) -> AlertSummary:
        """Get summary statistics for alerts.

        Args:
            time_range_hours: Time range for summary.

        Returns:
            Alert summary.
        """
        alerts, total = await self.get_all_alerts(
            time_range_hours=time_range_hours,
            limit=10000,  # Get all for stats
        )

        # Count by severity
        by_severity = AlertCountBySeverity()
        for alert in alerts:
            if alert.severity == AlertSeverity.CRITICAL:
                by_severity.critical += 1
            elif alert.severity == AlertSeverity.HIGH:
                by_severity.high += 1
            elif alert.severity == AlertSeverity.MEDIUM:
                by_severity.medium += 1
            elif alert.severity == AlertSeverity.LOW:
                by_severity.low += 1
            elif alert.severity == AlertSeverity.INFO:
                by_severity.info += 1

        # Count by source
        by_source = AlertCountBySource()
        for alert in alerts:
            if alert.source == AlertSource.MODEL:
                by_source.model += 1
            elif alert.source == AlertSource.DRIFT:
                by_source.drift += 1
            elif alert.source == AlertSource.ANOMALY:
                by_source.anomaly += 1
            elif alert.source == AlertSource.VALIDATION:
                by_source.validation += 1

        # Count by status
        by_status = AlertCountByStatus()
        active_count = 0
        for alert in alerts:
            if alert.status == AlertStatus.OPEN:
                by_status.open += 1
                active_count += 1
            elif alert.status == AlertStatus.ACKNOWLEDGED:
                by_status.acknowledged += 1
                active_count += 1
            elif alert.status == AlertStatus.RESOLVED:
                by_status.resolved += 1
            elif alert.status == AlertStatus.IGNORED:
                by_status.ignored += 1

        # Generate trend data (hourly for last 24h)
        trend = []
        now = datetime.utcnow()
        for hours_ago in range(24, -1, -1):
            point_time = now - timedelta(hours=hours_ago)
            point_start = point_time.replace(minute=0, second=0, microsecond=0)
            point_end = point_start + timedelta(hours=1)
            count = sum(
                1
                for a in alerts
                if point_start <= a.created_at < point_end
            )
            trend.append(AlertTrendPoint(timestamp=point_start, count=count))

        # Top sources with most alerts
        source_counts: dict[str, int] = {}
        for alert in alerts:
            key = alert.source_name
            source_counts[key] = source_counts.get(key, 0) + 1

        top_sources = sorted(
            [{"name": k, "count": v} for k, v in source_counts.items()],
            key=lambda x: x["count"],
            reverse=True,
        )[:5]

        return AlertSummary(
            total_alerts=total,
            active_alerts=active_count,
            by_severity=by_severity,
            by_source=by_source,
            by_status=by_status,
            trend_24h=trend,
            top_sources=top_sources,
        )

    async def acknowledge_alert(
        self,
        alert_id: str,
        actor: str,
        message: str = "",
    ) -> UnifiedAlertResponse | None:
        """Acknowledge an alert.

        Args:
            alert_id: Unified alert ID.
            actor: Who is acknowledging.
            message: Optional message.

        Returns:
            Updated alert if found.
        """
        try:
            source, source_id = _parse_alert_id(alert_id)
        except ValueError:
            return None

        now = datetime.utcnow()

        if source == AlertSource.MODEL:
            result = await self.session.execute(
                select(ModelAlert).where(ModelAlert.id == source_id)
            )
            alert = result.scalar_one_or_none()
            if alert:
                alert.acknowledged = True
                alert.acknowledged_by = actor
                alert.acknowledged_at = now
                await self.session.commit()
                return await self._get_single_model_alert(source_id)

        elif source == AlertSource.DRIFT:
            result = await self.session.execute(
                select(DriftAlert).where(DriftAlert.id == source_id)
            )
            alert = result.scalar_one_or_none()
            if alert:
                alert.status = "acknowledged"
                alert.acknowledged_by = actor
                alert.acknowledged_at = now
                if message:
                    alert.notes = message
                await self.session.commit()
                return await self._get_single_drift_alert(source_id)

        elif source == AlertSource.VALIDATION:
            # Validation alerts are read-only status derived from results
            return await self._get_single_validation_alert(source_id)

        elif source == AlertSource.ANOMALY:
            # Anomaly alerts are derived from detection results (read-only)
            return await self._get_single_anomaly_alert(source_id)

        return None

    async def resolve_alert(
        self,
        alert_id: str,
        actor: str = "",
        message: str = "",
    ) -> UnifiedAlertResponse | None:
        """Resolve an alert.

        Args:
            alert_id: Unified alert ID.
            actor: Who is resolving.
            message: Optional resolution message.

        Returns:
            Updated alert if found.
        """
        try:
            source, source_id = _parse_alert_id(alert_id)
        except ValueError:
            return None

        now = datetime.utcnow()

        if source == AlertSource.MODEL:
            result = await self.session.execute(
                select(ModelAlert).where(ModelAlert.id == source_id)
            )
            alert = result.scalar_one_or_none()
            if alert:
                alert.resolved = True
                alert.resolved_at = now
                await self.session.commit()
                return await self._get_single_model_alert(source_id)

        elif source == AlertSource.DRIFT:
            result = await self.session.execute(
                select(DriftAlert).where(DriftAlert.id == source_id)
            )
            alert = result.scalar_one_or_none()
            if alert:
                alert.status = "resolved"
                alert.resolved_at = now
                if message:
                    alert.notes = message
                await self.session.commit()
                return await self._get_single_drift_alert(source_id)

        # Validation and anomaly alerts are derived/read-only
        return None

    async def bulk_acknowledge(
        self,
        alert_ids: list[str],
        actor: str,
        message: str = "",
    ) -> tuple[int, int, list[str]]:
        """Bulk acknowledge alerts.

        Args:
            alert_ids: List of alert IDs.
            actor: Who is acknowledging.
            message: Optional message.

        Returns:
            Tuple of (success_count, failed_count, failed_ids).
        """
        success = 0
        failed_ids = []

        for alert_id in alert_ids:
            result = await self.acknowledge_alert(alert_id, actor, message)
            if result:
                success += 1
            else:
                failed_ids.append(alert_id)

        return success, len(failed_ids), failed_ids

    async def bulk_resolve(
        self,
        alert_ids: list[str],
        actor: str,
        message: str = "",
    ) -> tuple[int, int, list[str]]:
        """Bulk resolve alerts.

        Args:
            alert_ids: List of alert IDs.
            actor: Who is resolving.
            message: Optional message.

        Returns:
            Tuple of (success_count, failed_count, failed_ids).
        """
        success = 0
        failed_ids = []

        for alert_id in alert_ids:
            result = await self.resolve_alert(alert_id, actor, message)
            if result:
                success += 1
            else:
                failed_ids.append(alert_id)

        return success, len(failed_ids), failed_ids

    async def get_alert_correlations(
        self,
        alert_id: str,
        time_window_hours: int = 1,
    ) -> list[AlertCorrelation]:
        """Get correlated alerts for a given alert.

        Looks for alerts from:
        - Same source (data source, model)
        - Similar time frame

        Args:
            alert_id: Alert to find correlations for.
            time_window_hours: Time window for correlation.

        Returns:
            List of correlations.
        """
        alert = await self.get_alert_by_id(alert_id)
        if not alert:
            return []

        correlations = []

        # Time window for correlation
        time_start = alert.created_at - timedelta(hours=time_window_hours)
        time_end = alert.created_at + timedelta(hours=time_window_hours)

        # Get all alerts in time window
        all_alerts, _ = await self.get_all_alerts(
            time_range_hours=time_window_hours * 2 + 24,  # Generous window
            limit=1000,
        )

        # Filter to time window and exclude self
        window_alerts = [
            a for a in all_alerts
            if time_start <= a.created_at <= time_end and a.id != alert_id
        ]

        # Group by source name (same data source/model)
        same_source_alerts = [
            a for a in window_alerts
            if a.source_name == alert.source_name
        ]
        if same_source_alerts:
            correlations.append(
                AlertCorrelation(
                    alert_id=alert_id,
                    related_alerts=same_source_alerts[:10],  # Limit
                    correlation_type="same_source",
                    correlation_score=0.9,
                    common_factors=[f"Same source: {alert.source_name}"],
                )
            )

        # Group by similar severity in time window
        same_severity_alerts = [
            a for a in window_alerts
            if a.severity == alert.severity and a not in same_source_alerts
        ]
        if same_severity_alerts:
            correlations.append(
                AlertCorrelation(
                    alert_id=alert_id,
                    related_alerts=same_severity_alerts[:10],
                    correlation_type="temporal_severity",
                    correlation_score=0.6,
                    common_factors=[
                        f"Same severity: {alert.severity.value}",
                        f"Within {time_window_hours}h window",
                    ],
                )
            )

        return correlations

    # =========================================================================
    # Private methods for fetching from each source
    # =========================================================================

    async def _get_model_alerts(
        self,
        severity: AlertSeverity | None = None,
        status: AlertStatus | None = None,
        cutoff: datetime | None = None,
    ) -> list[UnifiedAlertResponse]:
        """Get alerts from model monitoring."""
        filters = []
        if cutoff:
            filters.append(ModelAlert.created_at >= cutoff)
        if status:
            if status == AlertStatus.OPEN:
                filters.append(ModelAlert.acknowledged == False)
                filters.append(ModelAlert.resolved == False)
            elif status == AlertStatus.ACKNOWLEDGED:
                filters.append(ModelAlert.acknowledged == True)
                filters.append(ModelAlert.resolved == False)
            elif status == AlertStatus.RESOLVED:
                filters.append(ModelAlert.resolved == True)

        query = select(ModelAlert)
        if filters:
            query = query.where(and_(*filters))

        result = await self.session.execute(query)
        alerts = result.scalars().all()

        # Get model names
        model_ids = {a.model_id for a in alerts}
        model_names = {}
        if model_ids:
            models_result = await self.session.execute(
                select(MonitoredModel).where(MonitoredModel.id.in_(model_ids))
            )
            for model in models_result.scalars():
                model_names[model.id] = model.name

        unified = []
        for alert in alerts:
            alert_severity = _map_model_severity(alert.severity)
            if severity and alert_severity != severity:
                continue

            alert_status = AlertStatus.OPEN
            if alert.resolved:
                alert_status = AlertStatus.RESOLVED
            elif alert.acknowledged:
                alert_status = AlertStatus.ACKNOWLEDGED

            unified.append(
                UnifiedAlertResponse(
                    id=_generate_alert_id(AlertSource.MODEL, alert.id),
                    source=AlertSource.MODEL,
                    source_id=alert.id,
                    source_name=model_names.get(alert.model_id, "Unknown Model"),
                    severity=alert_severity,
                    status=alert_status,
                    title=f"Model Alert: {alert.message[:50]}",
                    message=alert.message,
                    details={
                        "rule_id": alert.rule_id,
                        "metric_value": alert.metric_value,
                        "threshold_value": alert.threshold_value,
                    },
                    acknowledged_at=alert.acknowledged_at,
                    acknowledged_by=alert.acknowledged_by,
                    resolved_at=alert.resolved_at,
                    created_at=alert.created_at,
                    updated_at=alert.updated_at,
                )
            )

        return unified

    async def _get_drift_alerts(
        self,
        severity: AlertSeverity | None = None,
        status: AlertStatus | None = None,
        cutoff: datetime | None = None,
    ) -> list[UnifiedAlertResponse]:
        """Get alerts from drift monitoring."""
        filters = []
        if cutoff:
            filters.append(DriftAlert.created_at >= cutoff)
        if status:
            filters.append(DriftAlert.status == status.value)

        query = select(DriftAlert)
        if filters:
            query = query.where(and_(*filters))

        result = await self.session.execute(query)
        alerts = result.scalars().all()

        # Get monitor names
        monitor_ids = {a.monitor_id for a in alerts}
        monitor_names = {}
        if monitor_ids:
            monitors_result = await self.session.execute(
                select(DriftMonitor).where(DriftMonitor.id.in_(monitor_ids))
            )
            for monitor in monitors_result.scalars():
                monitor_names[monitor.id] = monitor.name

        unified = []
        for alert in alerts:
            alert_severity = _map_drift_severity(alert.severity)
            if severity and alert_severity != severity:
                continue

            unified.append(
                UnifiedAlertResponse(
                    id=_generate_alert_id(AlertSource.DRIFT, alert.id),
                    source=AlertSource.DRIFT,
                    source_id=alert.id,
                    source_name=monitor_names.get(alert.monitor_id, "Unknown Monitor"),
                    severity=alert_severity,
                    status=_map_drift_status(alert.status),
                    title=f"Drift Alert: {alert.drift_percentage:.1f}% drift detected",
                    message=alert.message,
                    details={
                        "comparison_id": alert.comparison_id,
                        "drift_percentage": alert.drift_percentage,
                        "drifted_columns": alert.drifted_columns,
                    },
                    acknowledged_at=alert.acknowledged_at,
                    acknowledged_by=alert.acknowledged_by,
                    resolved_at=alert.resolved_at,
                    created_at=alert.created_at,
                    updated_at=alert.updated_at,
                )
            )

        return unified

    async def _get_anomaly_alerts(
        self,
        severity: AlertSeverity | None = None,
        status: AlertStatus | None = None,
        cutoff: datetime | None = None,
    ) -> list[UnifiedAlertResponse]:
        """Get alerts derived from anomaly detection results.

        Creates alerts when anomaly rate exceeds thresholds.
        """
        filters = [AnomalyDetection.status == "success"]
        if cutoff:
            filters.append(AnomalyDetection.created_at >= cutoff)

        query = select(AnomalyDetection).where(and_(*filters))
        result = await self.session.execute(query)
        detections = result.scalars().all()

        # Get source names
        source_ids = {d.source_id for d in detections}
        source_names = {}
        if source_ids:
            sources_result = await self.session.execute(
                select(Source).where(Source.id.in_(source_ids))
            )
            for source in sources_result.scalars():
                source_names[source.id] = source.name

        unified = []
        for detection in detections:
            # Only create alerts for high anomaly rates
            if not detection.anomaly_rate or detection.anomaly_rate < 0.1:
                continue

            # Determine severity based on anomaly rate
            if detection.anomaly_rate >= 0.3:
                alert_severity = AlertSeverity.CRITICAL
            elif detection.anomaly_rate >= 0.2:
                alert_severity = AlertSeverity.HIGH
            elif detection.anomaly_rate >= 0.1:
                alert_severity = AlertSeverity.MEDIUM
            else:
                continue

            if severity and alert_severity != severity:
                continue

            # Anomaly alerts are always open (derived state)
            if status and status != AlertStatus.OPEN:
                continue

            pct = detection.anomaly_rate * 100
            unified.append(
                UnifiedAlertResponse(
                    id=_generate_alert_id(AlertSource.ANOMALY, detection.id),
                    source=AlertSource.ANOMALY,
                    source_id=detection.id,
                    source_name=source_names.get(detection.source_id, "Unknown Source"),
                    severity=alert_severity,
                    status=AlertStatus.OPEN,
                    title=f"High Anomaly Rate: {pct:.1f}%",
                    message=f"Anomaly detection found {detection.anomaly_count} anomalies "
                    f"out of {detection.total_rows} rows ({pct:.1f}% rate) "
                    f"using {detection.algorithm} algorithm.",
                    details={
                        "algorithm": detection.algorithm,
                        "anomaly_count": detection.anomaly_count,
                        "total_rows": detection.total_rows,
                        "anomaly_rate": detection.anomaly_rate,
                        "columns_analyzed": detection.columns_analyzed,
                    },
                    created_at=detection.created_at,
                    updated_at=detection.updated_at,
                )
            )

        return unified

    async def _get_validation_alerts(
        self,
        severity: AlertSeverity | None = None,
        status: AlertStatus | None = None,
        cutoff: datetime | None = None,
    ) -> list[UnifiedAlertResponse]:
        """Get alerts from validation failures."""
        filters = [Validation.status == "failed"]
        if cutoff:
            filters.append(Validation.created_at >= cutoff)

        query = select(Validation).where(and_(*filters))
        result = await self.session.execute(query)
        validations = result.scalars().all()

        # Get source names
        source_ids = {v.source_id for v in validations}
        source_names = {}
        if source_ids:
            sources_result = await self.session.execute(
                select(Source).where(Source.id.in_(source_ids))
            )
            for source in sources_result.scalars():
                source_names[source.id] = source.name

        unified = []
        for validation in validations:
            # Determine severity based on critical/high issue counts
            issues = validation.issues or []
            critical_count = sum(1 for i in issues if i.get("severity") == "critical")
            high_count = sum(1 for i in issues if i.get("severity") == "high")

            if critical_count > 0:
                alert_severity = AlertSeverity.CRITICAL
            elif high_count > 0:
                alert_severity = AlertSeverity.HIGH
            else:
                alert_severity = AlertSeverity.MEDIUM

            if severity and alert_severity != severity:
                continue

            # Validation alerts are always open (derived state)
            if status and status != AlertStatus.OPEN:
                continue

            unified.append(
                UnifiedAlertResponse(
                    id=_generate_alert_id(AlertSource.VALIDATION, validation.id),
                    source=AlertSource.VALIDATION,
                    source_id=validation.id,
                    source_name=source_names.get(validation.source_id, "Unknown Source"),
                    severity=alert_severity,
                    status=AlertStatus.OPEN,
                    title=f"Validation Failed: {len(issues)} issues",
                    message=f"Validation failed with {critical_count} critical, "
                    f"{high_count} high severity issues. "
                    f"Pass rate: {validation.pass_rate:.1f}%",
                    details={
                        "pass_rate": validation.pass_rate,
                        "total_issues": len(issues),
                        "critical_issues": critical_count,
                        "high_issues": high_count,
                    },
                    created_at=validation.created_at,
                    updated_at=validation.updated_at,
                )
            )

        return unified

    async def _get_single_model_alert(self, source_id: str) -> UnifiedAlertResponse | None:
        """Get a single model monitoring alert."""
        alerts = await self._get_model_alerts()
        for alert in alerts:
            if alert.source_id == source_id:
                return alert
        return None

    async def _get_single_drift_alert(self, source_id: str) -> UnifiedAlertResponse | None:
        """Get a single drift alert."""
        alerts = await self._get_drift_alerts()
        for alert in alerts:
            if alert.source_id == source_id:
                return alert
        return None

    async def _get_single_anomaly_alert(self, source_id: str) -> UnifiedAlertResponse | None:
        """Get a single anomaly alert."""
        alerts = await self._get_anomaly_alerts()
        for alert in alerts:
            if alert.source_id == source_id:
                return alert
        return None

    async def _get_single_validation_alert(self, source_id: str) -> UnifiedAlertResponse | None:
        """Get a single validation alert."""
        alerts = await self._get_validation_alerts()
        for alert in alerts:
            if alert.source_id == source_id:
                return alert
        return None
