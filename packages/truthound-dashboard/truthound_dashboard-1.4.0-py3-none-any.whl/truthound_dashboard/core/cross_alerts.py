"""Cross-alert correlation service.

This module provides services for cross-feature integration between
Anomaly Detection and Drift Monitoring alerts.

When anomaly rates spike, it automatically checks for drift and vice versa.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from truthound_dashboard.db.models import (
        AnomalyDetection,
        DriftAlert,
        DriftComparison,
        Source,
    )

logger = logging.getLogger(__name__)


# In-memory config storage (would be DB in production)
_global_config: dict[str, Any] = {
    "enabled": True,
    "trigger_drift_on_anomaly": True,
    "trigger_anomaly_on_drift": True,
    "thresholds": {
        "anomaly_rate_threshold": 0.1,
        "anomaly_count_threshold": 10,
        "drift_percentage_threshold": 10.0,
        "drift_columns_threshold": 2,
    },
    "notify_on_correlation": True,
    "notification_channel_ids": None,
    "cooldown_seconds": 300,
    "last_anomaly_trigger_at": None,
    "last_drift_trigger_at": None,
}

_source_configs: dict[str, dict[str, Any]] = {}
_correlations: list[dict[str, Any]] = []
_auto_trigger_events: list[dict[str, Any]] = []


class CrossAlertService:
    """Service for cross-alert correlation between anomaly and drift detection.

    Provides functionality for:
    - Finding correlated alerts between anomaly and drift detection
    - Auto-triggering drift checks when anomalies spike
    - Auto-triggering anomaly checks when drift is detected
    - Managing auto-trigger configuration
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service.

        Args:
            session: Database session.
        """
        self.session = session

    # =========================================================================
    # Correlation Analysis
    # =========================================================================

    async def correlate_anomaly_drift(
        self,
        source_id: str,
        *,
        time_window_hours: int = 24,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Find correlated anomaly and drift alerts for a source.

        Args:
            source_id: Data source ID.
            time_window_hours: Time window to look for correlations.
            limit: Maximum correlations to return.

        Returns:
            List of correlation dictionaries.
        """
        from truthound_dashboard.db.models import (
            AnomalyDetection,
            DriftAlert,
            DriftComparison,
            Source,
        )

        # Get source info
        result = await self.session.execute(
            select(Source).where(Source.id == source_id)
        )
        source = result.scalar_one_or_none()
        source_name = source.name if source else None

        # Time window
        since = datetime.utcnow() - timedelta(hours=time_window_hours)

        # Get recent anomaly detections
        anomaly_result = await self.session.execute(
            select(AnomalyDetection)
            .where(
                and_(
                    AnomalyDetection.source_id == source_id,
                    AnomalyDetection.created_at >= since,
                    AnomalyDetection.status == "success",
                )
            )
            .order_by(AnomalyDetection.created_at.desc())
            .limit(100)
        )
        anomaly_detections = list(anomaly_result.scalars().all())

        # Get recent drift alerts for this source
        drift_result = await self.session.execute(
            select(DriftAlert)
            .where(
                and_(
                    DriftAlert.created_at >= since,
                )
            )
            .order_by(DriftAlert.created_at.desc())
            .limit(100)
        )
        drift_alerts = list(drift_result.scalars().all())

        # Filter drift alerts related to this source
        related_drift_alerts = []
        for alert in drift_alerts:
            # Get the comparison to check source IDs
            comp_result = await self.session.execute(
                select(DriftComparison).where(DriftComparison.id == alert.comparison_id)
            )
            comparison = comp_result.scalar_one_or_none()
            if comparison and (
                comparison.baseline_source_id == source_id
                or comparison.current_source_id == source_id
            ):
                related_drift_alerts.append((alert, comparison))

        # Find correlations
        correlations = []
        for detection in anomaly_detections:
            if detection.anomaly_rate is None or detection.anomaly_rate < 0.01:
                continue

            for alert, comparison in related_drift_alerts:
                # Check time proximity
                time_delta = abs(
                    (detection.created_at - alert.created_at).total_seconds()
                )

                # Only correlate if within 2 hours of each other
                if time_delta > 7200:
                    continue

                # Calculate correlation strength
                strength = self._calculate_correlation_strength(
                    detection, alert, time_delta
                )

                if strength == "none":
                    continue

                # Find common columns
                anomaly_cols = detection.columns_analyzed or []
                drift_cols = alert.drifted_columns_json or []
                common_cols = list(set(anomaly_cols) & set(drift_cols))

                correlation = {
                    "id": str(uuid.uuid4()),
                    "source_id": source_id,
                    "source_name": source_name,
                    "correlation_strength": strength,
                    "confidence_score": self._calculate_confidence(
                        detection, alert, common_cols, time_delta
                    ),
                    "time_delta_seconds": int(time_delta),
                    "anomaly_alert": {
                        "alert_id": detection.id,
                        "alert_type": "anomaly",
                        "source_id": source_id,
                        "source_name": source_name,
                        "severity": self._anomaly_severity(detection.anomaly_rate),
                        "message": f"Detected {detection.anomaly_count} anomalies ({detection.anomaly_rate * 100:.1f}% rate)",
                        "created_at": detection.created_at.isoformat(),
                        "anomaly_rate": detection.anomaly_rate,
                        "anomaly_count": detection.anomaly_count,
                        "drift_percentage": None,
                        "drifted_columns": None,
                    },
                    "drift_alert": {
                        "alert_id": alert.id,
                        "alert_type": "drift",
                        "source_id": source_id,
                        "source_name": source_name,
                        "severity": alert.severity,
                        "message": alert.message,
                        "created_at": alert.created_at.isoformat(),
                        "anomaly_rate": None,
                        "anomaly_count": None,
                        "drift_percentage": alert.drift_percentage,
                        "drifted_columns": alert.drifted_columns_json,
                    },
                    "common_columns": common_cols,
                    "suggested_action": self._suggest_action(strength, common_cols),
                    "notes": None,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                }
                correlations.append(correlation)

        # Sort by confidence score and limit
        correlations.sort(key=lambda x: x["confidence_score"], reverse=True)
        return correlations[:limit]

    def _calculate_correlation_strength(
        self,
        detection: "AnomalyDetection",
        alert: "DriftAlert",
        time_delta: float,
    ) -> str:
        """Calculate correlation strength between anomaly and drift.

        Args:
            detection: Anomaly detection result.
            alert: Drift alert.
            time_delta: Time difference in seconds.

        Returns:
            Correlation strength: strong, moderate, weak, or none.
        """
        score = 0

        # Time proximity (closer = stronger)
        if time_delta < 600:  # 10 minutes
            score += 3
        elif time_delta < 1800:  # 30 minutes
            score += 2
        elif time_delta < 3600:  # 1 hour
            score += 1

        # Anomaly severity
        rate = detection.anomaly_rate or 0
        if rate > 0.2:
            score += 3
        elif rate > 0.1:
            score += 2
        elif rate > 0.05:
            score += 1

        # Drift severity
        if alert.severity == "critical":
            score += 3
        elif alert.severity == "high":
            score += 2
        elif alert.severity == "medium":
            score += 1

        # Drift percentage
        drift_pct = alert.drift_percentage or 0
        if drift_pct > 30:
            score += 2
        elif drift_pct > 15:
            score += 1

        # Determine strength
        if score >= 8:
            return "strong"
        elif score >= 5:
            return "moderate"
        elif score >= 2:
            return "weak"
        return "none"

    def _calculate_confidence(
        self,
        detection: "AnomalyDetection",
        alert: "DriftAlert",
        common_cols: list[str],
        time_delta: float,
    ) -> float:
        """Calculate confidence score for correlation.

        Args:
            detection: Anomaly detection result.
            alert: Drift alert.
            common_cols: Columns affected by both.
            time_delta: Time difference in seconds.

        Returns:
            Confidence score between 0 and 1.
        """
        confidence = 0.5  # Base confidence

        # Time proximity bonus
        if time_delta < 300:
            confidence += 0.2
        elif time_delta < 1800:
            confidence += 0.1

        # Common columns bonus
        if len(common_cols) > 3:
            confidence += 0.2
        elif len(common_cols) > 0:
            confidence += 0.1

        # Severity bonus
        rate = detection.anomaly_rate or 0
        if rate > 0.15 and alert.severity in ("critical", "high"):
            confidence += 0.15

        return min(confidence, 1.0)

    def _anomaly_severity(self, rate: float | None) -> str:
        """Determine anomaly severity from rate."""
        if rate is None:
            return "low"
        if rate > 0.2:
            return "critical"
        if rate > 0.1:
            return "high"
        if rate > 0.05:
            return "medium"
        return "low"

    def _suggest_action(self, strength: str, common_cols: list[str]) -> str:
        """Suggest action based on correlation.

        Args:
            strength: Correlation strength.
            common_cols: Common affected columns.

        Returns:
            Suggested action string.
        """
        if strength == "strong":
            if common_cols:
                cols = ", ".join(common_cols[:3])
                return f"Investigate upstream changes affecting columns: {cols}"
            return "Investigate upstream data pipeline for recent changes"
        elif strength == "moderate":
            return "Review data quality and consider updating baseline"
        else:
            return "Monitor for recurring patterns"

    # =========================================================================
    # Auto-Trigger Operations
    # =========================================================================

    async def auto_trigger_drift_on_anomaly(
        self,
        detection_id: str,
    ) -> dict[str, Any] | None:
        """Auto-trigger drift check when anomaly detection shows high rate.

        Args:
            detection_id: Anomaly detection ID.

        Returns:
            Trigger event result or None if skipped.
        """
        from truthound_dashboard.db.models import AnomalyDetection, DriftMonitor
        from truthound_dashboard.core.drift_monitor import DriftMonitorService

        # Get detection
        result = await self.session.execute(
            select(AnomalyDetection).where(AnomalyDetection.id == detection_id)
        )
        detection = result.scalar_one_or_none()

        if not detection:
            return None

        # Get config
        config = self.get_config(detection.source_id)
        if not config.get("enabled") or not config.get("trigger_drift_on_anomaly"):
            return self._create_skip_event(
                detection.source_id,
                "anomaly_to_drift",
                detection_id,
                "anomaly",
                "Auto-trigger disabled",
            )

        # Check thresholds
        thresholds = config.get("thresholds", {})
        rate_threshold = thresholds.get("anomaly_rate_threshold", 0.1)
        count_threshold = thresholds.get("anomaly_count_threshold", 10)

        rate = detection.anomaly_rate or 0
        count = detection.anomaly_count or 0

        if rate < rate_threshold and count < count_threshold:
            return self._create_skip_event(
                detection.source_id,
                "anomaly_to_drift",
                detection_id,
                "anomaly",
                f"Below thresholds (rate: {rate:.2f} < {rate_threshold}, count: {count} < {count_threshold})",
            )

        # Check cooldown
        cooldown = config.get("cooldown_seconds", 300)
        last_trigger = config.get("last_anomaly_trigger_at")
        if last_trigger:
            if isinstance(last_trigger, str):
                last_trigger = datetime.fromisoformat(last_trigger)
            elapsed = (datetime.utcnow() - last_trigger).total_seconds()
            if elapsed < cooldown:
                return self._create_skip_event(
                    detection.source_id,
                    "anomaly_to_drift",
                    detection_id,
                    "anomaly",
                    f"Cooldown active ({int(cooldown - elapsed)}s remaining)",
                )

        # Find a drift monitor for this source
        monitor_result = await self.session.execute(
            select(DriftMonitor)
            .where(
                or_(
                    DriftMonitor.baseline_source_id == detection.source_id,
                    DriftMonitor.current_source_id == detection.source_id,
                )
            )
            .limit(1)
        )
        monitor = monitor_result.scalar_one_or_none()

        event = {
            "id": str(uuid.uuid4()),
            "source_id": detection.source_id,
            "trigger_type": "anomaly_to_drift",
            "trigger_alert_id": detection_id,
            "trigger_alert_type": "anomaly",
            "result_id": None,
            "correlation_found": False,
            "correlation_id": None,
            "status": "pending",
            "error_message": None,
            "skipped_reason": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        if not monitor:
            event["status"] = "skipped"
            event["skipped_reason"] = "No drift monitor configured for this source"
            _auto_trigger_events.append(event)
            return event

        try:
            # Run the drift monitor
            event["status"] = "running"
            drift_service = DriftMonitorService(self.session)
            comparison = await drift_service.run_monitor(monitor.id)

            if comparison:
                event["status"] = "completed"
                event["result_id"] = comparison.id

                # Check for correlation
                if comparison.has_drift:
                    correlations = await self.correlate_anomaly_drift(
                        detection.source_id, time_window_hours=1
                    )
                    if correlations:
                        event["correlation_found"] = True
                        event["correlation_id"] = correlations[0]["id"]
            else:
                event["status"] = "failed"
                event["error_message"] = "Drift monitor run failed"

        except Exception as e:
            event["status"] = "failed"
            event["error_message"] = str(e)
            logger.error(f"Auto-trigger drift check failed: {e}")

        # Update last trigger time
        self._update_config(
            detection.source_id,
            {"last_anomaly_trigger_at": datetime.utcnow().isoformat()},
        )

        _auto_trigger_events.append(event)
        return event

    async def auto_trigger_anomaly_on_drift(
        self,
        monitor_id: str,
    ) -> dict[str, Any] | None:
        """Auto-trigger anomaly check when drift is detected.

        Args:
            monitor_id: Drift monitor ID.

        Returns:
            Trigger event result or None if skipped.
        """
        from truthound_dashboard.db.models import DriftMonitor, DriftAlert
        from truthound_dashboard.core.anomaly import AnomalyDetectionService

        # Get monitor
        result = await self.session.execute(
            select(DriftMonitor).where(DriftMonitor.id == monitor_id)
        )
        monitor = result.scalar_one_or_none()

        if not monitor:
            return None

        source_id = monitor.current_source_id

        # Get latest alert for this monitor
        alert_result = await self.session.execute(
            select(DriftAlert)
            .where(DriftAlert.monitor_id == monitor_id)
            .order_by(DriftAlert.created_at.desc())
            .limit(1)
        )
        alert = alert_result.scalar_one_or_none()

        if not alert:
            return None

        # Get config
        config = self.get_config(source_id)
        if not config.get("enabled") or not config.get("trigger_anomaly_on_drift"):
            return self._create_skip_event(
                source_id,
                "drift_to_anomaly",
                alert.id,
                "drift",
                "Auto-trigger disabled",
            )

        # Check thresholds
        thresholds = config.get("thresholds", {})
        drift_threshold = thresholds.get("drift_percentage_threshold", 10.0)
        cols_threshold = thresholds.get("drift_columns_threshold", 2)

        drift_pct = alert.drift_percentage or 0
        cols_count = len(alert.drifted_columns_json or [])

        if drift_pct < drift_threshold and cols_count < cols_threshold:
            return self._create_skip_event(
                source_id,
                "drift_to_anomaly",
                alert.id,
                "drift",
                f"Below thresholds (drift: {drift_pct:.1f}% < {drift_threshold}%, cols: {cols_count} < {cols_threshold})",
            )

        # Check cooldown
        cooldown = config.get("cooldown_seconds", 300)
        last_trigger = config.get("last_drift_trigger_at")
        if last_trigger:
            if isinstance(last_trigger, str):
                last_trigger = datetime.fromisoformat(last_trigger)
            elapsed = (datetime.utcnow() - last_trigger).total_seconds()
            if elapsed < cooldown:
                return self._create_skip_event(
                    source_id,
                    "drift_to_anomaly",
                    alert.id,
                    "drift",
                    f"Cooldown active ({int(cooldown - elapsed)}s remaining)",
                )

        event = {
            "id": str(uuid.uuid4()),
            "source_id": source_id,
            "trigger_type": "drift_to_anomaly",
            "trigger_alert_id": alert.id,
            "trigger_alert_type": "drift",
            "result_id": None,
            "correlation_found": False,
            "correlation_id": None,
            "status": "pending",
            "error_message": None,
            "skipped_reason": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        try:
            # Run anomaly detection
            event["status"] = "running"
            anomaly_service = AnomalyDetectionService(self.session)

            detection = await anomaly_service.create_detection(
                source_id=source_id,
                algorithm="isolation_forest",
                columns=alert.drifted_columns_json,
            )
            detection = await anomaly_service.run_detection(detection.id)

            event["status"] = "completed"
            event["result_id"] = detection.id

            # Check for correlation
            if detection.anomaly_count and detection.anomaly_count > 0:
                correlations = await self.correlate_anomaly_drift(
                    source_id, time_window_hours=1
                )
                if correlations:
                    event["correlation_found"] = True
                    event["correlation_id"] = correlations[0]["id"]

        except Exception as e:
            event["status"] = "failed"
            event["error_message"] = str(e)
            logger.error(f"Auto-trigger anomaly check failed: {e}")

        # Update last trigger time
        self._update_config(
            source_id,
            {"last_drift_trigger_at": datetime.utcnow().isoformat()},
        )

        _auto_trigger_events.append(event)
        return event

    def _create_skip_event(
        self,
        source_id: str,
        trigger_type: str,
        alert_id: str,
        alert_type: str,
        reason: str,
    ) -> dict[str, Any]:
        """Create a skipped trigger event."""
        event = {
            "id": str(uuid.uuid4()),
            "source_id": source_id,
            "trigger_type": trigger_type,
            "trigger_alert_id": alert_id,
            "trigger_alert_type": alert_type,
            "result_id": None,
            "correlation_found": False,
            "correlation_id": None,
            "status": "skipped",
            "error_message": None,
            "skipped_reason": reason,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        _auto_trigger_events.append(event)
        return event

    # =========================================================================
    # Configuration Management
    # =========================================================================

    def get_config(self, source_id: str | None = None) -> dict[str, Any]:
        """Get auto-trigger configuration.

        Args:
            source_id: Source ID for source-specific config, None for global.

        Returns:
            Configuration dictionary.
        """
        if source_id and source_id in _source_configs:
            # Merge source config with global defaults
            config = _global_config.copy()
            config.update(_source_configs[source_id])
            return config
        return _global_config.copy()

    def update_config(
        self,
        source_id: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Update auto-trigger configuration.

        Args:
            source_id: Source ID for source-specific config, None for global.
            **kwargs: Configuration fields to update.

        Returns:
            Updated configuration.
        """
        return self._update_config(source_id, kwargs)

    def _update_config(
        self,
        source_id: str | None,
        updates: dict[str, Any],
    ) -> dict[str, Any]:
        """Internal method to update config."""
        if source_id:
            if source_id not in _source_configs:
                _source_configs[source_id] = {}
            for key, value in updates.items():
                if value is not None:
                    _source_configs[source_id][key] = value
            return self.get_config(source_id)
        else:
            for key, value in updates.items():
                if value is not None:
                    _global_config[key] = value
            return _global_config.copy()

    # =========================================================================
    # Query Operations
    # =========================================================================

    async def get_correlations(
        self,
        source_id: str | None = None,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """Get correlation records.

        Args:
            source_id: Filter by source ID.
            limit: Maximum to return.
            offset: Number to skip.

        Returns:
            Tuple of (correlations, total_count).
        """
        if source_id:
            filtered = [c for c in _correlations if c.get("source_id") == source_id]
        else:
            filtered = _correlations.copy()

        total = len(filtered)
        paginated = filtered[offset : offset + limit]
        return paginated, total

    async def get_auto_trigger_events(
        self,
        source_id: str | None = None,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """Get auto-trigger event records.

        Args:
            source_id: Filter by source ID.
            limit: Maximum to return.
            offset: Number to skip.

        Returns:
            Tuple of (events, total_count).
        """
        if source_id:
            filtered = [
                e for e in _auto_trigger_events if e.get("source_id") == source_id
            ]
        else:
            filtered = _auto_trigger_events.copy()

        # Sort by created_at desc
        filtered.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        total = len(filtered)
        paginated = filtered[offset : offset + limit]
        return paginated, total

    async def get_summary(self) -> dict[str, Any]:
        """Get cross-alert summary statistics.

        Returns:
            Summary dictionary.
        """
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)

        # Count correlations by strength
        strong = sum(1 for c in _correlations if c.get("correlation_strength") == "strong")
        moderate = sum(1 for c in _correlations if c.get("correlation_strength") == "moderate")
        weak = sum(1 for c in _correlations if c.get("correlation_strength") == "weak")

        # Recent activity
        recent_correlations = sum(
            1 for c in _correlations
            if c.get("created_at") and datetime.fromisoformat(c["created_at"]) >= last_24h
        )
        recent_triggers = sum(
            1 for e in _auto_trigger_events
            if e.get("created_at") and datetime.fromisoformat(e["created_at"]) >= last_24h
        )

        # Trigger counts by type
        anomaly_to_drift = sum(
            1 for e in _auto_trigger_events
            if e.get("trigger_type") == "anomaly_to_drift"
        )
        drift_to_anomaly = sum(
            1 for e in _auto_trigger_events
            if e.get("trigger_type") == "drift_to_anomaly"
        )

        # Top affected sources
        source_counts: dict[str, int] = {}
        for c in _correlations:
            sid = c.get("source_id")
            if sid:
                source_counts[sid] = source_counts.get(sid, 0) + 1

        top_sources = [
            {"source_id": sid, "source_name": c.get("source_name"), "count": cnt}
            for sid, cnt in sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            for c in _correlations if c.get("source_id") == sid
        ][:5]

        return {
            "total_correlations": len(_correlations),
            "strong_correlations": strong,
            "moderate_correlations": moderate,
            "weak_correlations": weak,
            "recent_correlations_24h": recent_correlations,
            "recent_auto_triggers_24h": recent_triggers,
            "top_affected_sources": top_sources,
            "auto_trigger_enabled": _global_config.get("enabled", True),
            "anomaly_to_drift_triggers": anomaly_to_drift,
            "drift_to_anomaly_triggers": drift_to_anomaly,
        }
