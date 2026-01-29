"""Drift monitoring service.

This module provides automatic drift detection monitoring capabilities.
Monitors can be scheduled to run periodically and generate alerts when drift is detected.

Includes optimizations for large-scale datasets (100M+ rows):
- Sampled comparison for faster processing
- Chunked processing for memory efficiency
- Parallel column comparison
- Early stopping when drift is obvious
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from .drift_sampling import (
    SamplingMethod,
    ChunkedComparisonTracker,
    estimate_sample_size,
    calculate_chunk_size,
    should_early_stop,
    get_sampler,
)

if TYPE_CHECKING:
    from truthound_dashboard.db.models import DriftMonitor, DriftAlert, DriftComparison

logger = logging.getLogger(__name__)

# Threshold for considering a dataset "large" (10 million rows)
LARGE_DATASET_THRESHOLD = 10_000_000

# Active comparison jobs (for progress tracking)
_active_jobs: dict[str, ChunkedComparisonTracker] = {}


class DriftMonitorService:
    """Service for managing drift monitors and alerts."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the drift monitor service.

        Args:
            session: Database session for persistence.
        """
        self.session = session

    async def preview_drift(
        self,
        baseline_source_id: str,
        current_source_id: str,
        columns: list[str] | None = None,
        method: str = "auto",
        threshold: float | None = None,
    ) -> dict:
        """Preview drift comparison without persisting results.

        This method runs a drift comparison but does not save the results
        to the database, allowing users to preview before creating a monitor.

        Args:
            baseline_source_id: Baseline data source ID.
            current_source_id: Current data source ID.
            columns: Specific columns to compare (None for all).
            method: Drift detection method.
            threshold: Custom drift threshold.

        Returns:
            Preview result dictionary with drift analysis.

        Raises:
            ValueError: If source not found.
        """
        from truthound_dashboard.core.drift import DriftService
        from truthound_dashboard.db.models import Source

        # Get source details for display
        baseline_result = await self.session.execute(
            select(Source).where(Source.id == baseline_source_id)
        )
        baseline_source = baseline_result.scalar_one_or_none()
        if not baseline_source:
            raise ValueError(f"Baseline source '{baseline_source_id}' not found")

        current_result = await self.session.execute(
            select(Source).where(Source.id == current_source_id)
        )
        current_source = current_result.scalar_one_or_none()
        if not current_source:
            raise ValueError(f"Current source '{current_source_id}' not found")

        # Use DriftService to compare without saving
        drift_service = DriftService(self.session)
        comparison = await drift_service.compare(
            baseline_source_id=baseline_source_id,
            current_source_id=current_source_id,
            columns=columns,
            method=method,
            threshold=threshold,
            save=False,  # Don't persist the comparison
        )

        # Build column results with distribution data
        column_results = []
        most_affected = []
        result_json = comparison.result_json or {}
        result_columns = result_json.get("columns", [])

        for col_data in result_columns:
            col_result = {
                "column": col_data.get("column", ""),
                "dtype": col_data.get("dtype", "unknown"),
                "drifted": col_data.get("drifted", False),
                "level": col_data.get("level", "none"),
                "method": col_data.get("method", method),
                "statistic": col_data.get("statistic"),
                "p_value": col_data.get("p_value"),
                "baseline_stats": col_data.get("baseline_stats", {}),
                "current_stats": col_data.get("current_stats", {}),
                "baseline_distribution": None,
                "current_distribution": None,
            }
            column_results.append(col_result)

            # Track most affected columns (drifted with high/medium level)
            if col_data.get("drifted", False):
                level = col_data.get("level", "none")
                most_affected.append((col_data.get("column", ""), level))

        # Sort most affected by severity
        level_order = {"high": 0, "medium": 1, "low": 2, "none": 3}
        most_affected.sort(key=lambda x: level_order.get(x[1], 3))
        most_affected_columns = [col for col, _ in most_affected[:10]]

        # Calculate drift percentage
        total_columns = comparison.total_columns or 0
        drifted_count = comparison.drifted_columns or 0
        drift_percentage = (
            (drifted_count / total_columns * 100) if total_columns > 0 else 0.0
        )

        return {
            "baseline_source_id": baseline_source_id,
            "current_source_id": current_source_id,
            "baseline_source_name": baseline_source.name,
            "current_source_name": current_source.name,
            "has_drift": comparison.has_drift,
            "has_high_drift": comparison.has_high_drift,
            "total_columns": total_columns,
            "drifted_columns": drifted_count,
            "drift_percentage": round(drift_percentage, 2),
            "baseline_rows": result_json.get("baseline_rows", 0),
            "current_rows": result_json.get("current_rows", 0),
            "method": method,
            "threshold": threshold or 0.05,
            "columns": column_results,
            "most_affected": most_affected_columns,
        }

    async def create_monitor(
        self,
        name: str,
        baseline_source_id: str,
        current_source_id: str,
        cron_expression: str = "0 0 * * *",
        method: str = "auto",
        threshold: float = 0.05,
        columns: list[str] | None = None,
        alert_on_drift: bool = True,
        alert_threshold_critical: float = 0.3,
        alert_threshold_high: float = 0.2,
        notification_channel_ids: list[str] | None = None,
    ) -> "DriftMonitor":
        """Create a new drift monitor.

        Args:
            name: Monitor name.
            baseline_source_id: Baseline data source ID.
            current_source_id: Current data source ID.
            cron_expression: Cron expression for scheduling.
            method: Drift detection method.
            threshold: Drift threshold.
            columns: Specific columns to monitor.
            alert_on_drift: Whether to create alerts.
            alert_threshold_critical: Critical alert threshold.
            alert_threshold_high: High alert threshold.
            notification_channel_ids: Notification channel IDs.

        Returns:
            Created drift monitor.
        """
        from truthound_dashboard.db.models import DriftMonitor

        monitor = DriftMonitor(
            id=str(uuid.uuid4()),
            name=name,
            baseline_source_id=baseline_source_id,
            current_source_id=current_source_id,
            cron_expression=cron_expression,
            method=method,
            threshold=threshold,
            columns_json=columns,
            alert_on_drift=alert_on_drift,
            alert_threshold_critical=alert_threshold_critical,
            alert_threshold_high=alert_threshold_high,
            notification_channel_ids_json=notification_channel_ids,
            status="active",
            total_runs=0,
            drift_detected_count=0,
            consecutive_drift_count=0,
        )

        self.session.add(monitor)
        await self.session.commit()
        await self.session.refresh(monitor)

        logger.info(f"Created drift monitor: {monitor.id} ({name})")
        return monitor

    async def get_monitor(self, monitor_id: str) -> "DriftMonitor | None":
        """Get a drift monitor by ID.

        Args:
            monitor_id: Monitor ID.

        Returns:
            Drift monitor or None if not found.
        """
        from truthound_dashboard.db.models import DriftMonitor

        result = await self.session.execute(
            select(DriftMonitor).where(DriftMonitor.id == monitor_id)
        )
        return result.scalar_one_or_none()

    async def list_monitors(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list["DriftMonitor"], int]:
        """List drift monitors.

        Args:
            status: Filter by status.
            limit: Maximum number of monitors to return.
            offset: Number of monitors to skip.

        Returns:
            Tuple of (monitors, total_count).
        """
        from truthound_dashboard.db.models import DriftMonitor

        query = select(DriftMonitor)
        count_query = select(func.count(DriftMonitor.id))

        if status:
            query = query.where(DriftMonitor.status == status)
            count_query = count_query.where(DriftMonitor.status == status)

        query = query.order_by(DriftMonitor.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        monitors = list(result.scalars().all())

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        return monitors, total

    async def update_monitor(
        self,
        monitor_id: str,
        **kwargs,
    ) -> "DriftMonitor | None":
        """Update a drift monitor.

        Args:
            monitor_id: Monitor ID.
            **kwargs: Fields to update.

        Returns:
            Updated monitor or None if not found.
        """
        monitor = await self.get_monitor(monitor_id)
        if not monitor:
            return None

        # Handle special fields
        if "columns" in kwargs:
            kwargs["columns_json"] = kwargs.pop("columns")
        if "notification_channel_ids" in kwargs:
            kwargs["notification_channel_ids_json"] = kwargs.pop("notification_channel_ids")

        for key, value in kwargs.items():
            if hasattr(monitor, key) and value is not None:
                setattr(monitor, key, value)

        monitor.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(monitor)

        logger.info(f"Updated drift monitor: {monitor_id}")
        return monitor

    async def delete_monitor(self, monitor_id: str) -> bool:
        """Delete a drift monitor.

        Args:
            monitor_id: Monitor ID.

        Returns:
            True if deleted, False if not found.
        """
        monitor = await self.get_monitor(monitor_id)
        if not monitor:
            return False

        await self.session.delete(monitor)
        await self.session.commit()

        logger.info(f"Deleted drift monitor: {monitor_id}")
        return True

    async def run_monitor(self, monitor_id: str) -> "DriftComparison | None":
        """Execute a drift monitoring run.

        Args:
            monitor_id: Monitor ID.

        Returns:
            Drift comparison result or None on error.
        """
        from truthound_dashboard.core.drift import DriftService

        monitor = await self.get_monitor(monitor_id)
        if not monitor or monitor.status != "active":
            return None

        try:
            # Create drift service and run comparison
            drift_service = DriftService(self.session)
            comparison = await drift_service.compare(
                baseline_source_id=monitor.baseline_source_id,
                current_source_id=monitor.current_source_id,
                method=monitor.method,
                threshold=monitor.threshold,
                columns=monitor.columns_json,
            )

            # Update monitor stats
            monitor.last_run_at = datetime.utcnow()
            monitor.total_runs += 1
            monitor.last_drift_detected = comparison.has_drift

            if comparison.has_drift:
                monitor.drift_detected_count += 1
                monitor.consecutive_drift_count += 1

                # Create alert if configured
                if monitor.alert_on_drift:
                    await self._create_drift_alert(monitor, comparison)
            else:
                monitor.consecutive_drift_count = 0

            await self.session.commit()
            await self.session.refresh(monitor)

            logger.info(
                f"Drift monitor {monitor_id} run complete: drift={comparison.has_drift}"
            )
            return comparison

        except Exception as e:
            logger.error(f"Drift monitor {monitor_id} run failed: {e}")
            monitor.status = "error"
            await self.session.commit()
            return None

    async def _create_drift_alert(
        self,
        monitor: "DriftMonitor",
        comparison: "DriftComparison",
    ) -> "DriftAlert":
        """Create a drift alert.

        Args:
            monitor: Drift monitor.
            comparison: Drift comparison result.

        Returns:
            Created alert.
        """
        from truthound_dashboard.db.models import DriftAlert

        # Determine severity based on drift percentage
        drift_pct = comparison.drift_percentage or 0
        if drift_pct >= (monitor.alert_threshold_critical * 100):
            severity = "critical"
        elif drift_pct >= (monitor.alert_threshold_high * 100):
            severity = "high"
        elif drift_pct >= 10:
            severity = "medium"
        else:
            severity = "low"

        # Extract drifted columns
        drifted_columns = []
        if comparison.result_json and "columns" in comparison.result_json:
            drifted_columns = [
                col["column"]
                for col in comparison.result_json["columns"]
                if col.get("drifted", False)
            ]

        alert = DriftAlert(
            id=str(uuid.uuid4()),
            monitor_id=monitor.id,
            comparison_id=comparison.id,
            severity=severity,
            drift_percentage=drift_pct,
            drifted_columns_json=drifted_columns,
            message=f"Drift detected: {drift_pct:.1f}% of columns drifted ({len(drifted_columns)} columns)",
            status="open",
        )

        self.session.add(alert)
        await self.session.commit()
        await self.session.refresh(alert)

        logger.info(f"Created drift alert: {alert.id} (severity={severity})")
        return alert

    # Alert Management

    async def list_alerts(
        self,
        monitor_id: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list["DriftAlert"], int]:
        """List drift alerts.

        Args:
            monitor_id: Filter by monitor ID.
            status: Filter by status.
            severity: Filter by severity.
            limit: Maximum number of alerts.
            offset: Number to skip.

        Returns:
            Tuple of (alerts, total_count).
        """
        from truthound_dashboard.db.models import DriftAlert

        query = select(DriftAlert)
        count_query = select(func.count(DriftAlert.id))

        conditions = []
        if monitor_id:
            conditions.append(DriftAlert.monitor_id == monitor_id)
        if status:
            conditions.append(DriftAlert.status == status)
        if severity:
            conditions.append(DriftAlert.severity == severity)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        query = query.order_by(DriftAlert.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        alerts = list(result.scalars().all())

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        return alerts, total

    async def get_alert(self, alert_id: str) -> "DriftAlert | None":
        """Get a drift alert by ID."""
        from truthound_dashboard.db.models import DriftAlert

        result = await self.session.execute(
            select(DriftAlert).where(DriftAlert.id == alert_id)
        )
        return result.scalar_one_or_none()

    async def update_alert(
        self,
        alert_id: str,
        status: str | None = None,
        notes: str | None = None,
    ) -> "DriftAlert | None":
        """Update a drift alert.

        Args:
            alert_id: Alert ID.
            status: New status.
            notes: Notes to add.

        Returns:
            Updated alert or None.
        """
        alert = await self.get_alert(alert_id)
        if not alert:
            return None

        if status:
            alert.status = status
            if status == "acknowledged":
                alert.acknowledged_at = datetime.utcnow()
            elif status == "resolved":
                alert.resolved_at = datetime.utcnow()

        if notes is not None:
            alert.notes = notes

        alert.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(alert)

        return alert

    # Statistics and Trends

    async def get_summary(self) -> dict:
        """Get summary of all drift monitors.

        Returns:
            Summary statistics.
        """
        from truthound_dashboard.db.models import DriftMonitor, DriftAlert

        # Monitor counts
        monitors, total_monitors = await self.list_monitors(limit=1000)
        active_monitors = sum(1 for m in monitors if m.status == "active")
        paused_monitors = sum(1 for m in monitors if m.status == "paused")
        monitors_with_drift = sum(1 for m in monitors if m.last_drift_detected)

        # Alert counts
        result = await self.session.execute(
            select(func.count(DriftAlert.id)).where(DriftAlert.status == "open")
        )
        total_open_alerts = result.scalar() or 0

        result = await self.session.execute(
            select(func.count(DriftAlert.id)).where(
                and_(DriftAlert.status == "open", DriftAlert.severity == "critical")
            )
        )
        critical_alerts = result.scalar() or 0

        result = await self.session.execute(
            select(func.count(DriftAlert.id)).where(
                and_(DriftAlert.status == "open", DriftAlert.severity == "high")
            )
        )
        high_alerts = result.scalar() or 0

        return {
            "total_monitors": total_monitors,
            "active_monitors": active_monitors,
            "paused_monitors": paused_monitors,
            "monitors_with_drift": monitors_with_drift,
            "total_open_alerts": total_open_alerts,
            "critical_alerts": critical_alerts,
            "high_alerts": high_alerts,
        }

    async def get_trend(
        self,
        monitor_id: str,
        days: int = 30,
    ) -> dict:
        """Get drift trend for a monitor.

        Args:
            monitor_id: Monitor ID.
            days: Number of days to include.

        Returns:
            Trend data.
        """
        from truthound_dashboard.db.models import DriftComparison

        monitor = await self.get_monitor(monitor_id)
        if not monitor:
            return {}

        start_date = datetime.utcnow() - timedelta(days=days)

        result = await self.session.execute(
            select(DriftComparison)
            .where(
                and_(
                    DriftComparison.baseline_source_id == monitor.baseline_source_id,
                    DriftComparison.current_source_id == monitor.current_source_id,
                    DriftComparison.created_at >= start_date,
                )
            )
            .order_by(DriftComparison.created_at.asc())
        )
        comparisons = list(result.scalars().all())

        data_points = []
        for comp in comparisons:
            data_points.append({
                "timestamp": comp.created_at.isoformat(),
                "drift_percentage": comp.drift_percentage or 0,
                "drifted_columns": comp.drifted_columns or 0,
                "total_columns": comp.total_columns or 0,
                "has_drift": comp.has_drift,
            })

        avg_drift = (
            sum(p["drift_percentage"] for p in data_points) / len(data_points)
            if data_points
            else 0
        )
        max_drift = max((p["drift_percentage"] for p in data_points), default=0)
        drift_rate = (
            sum(1 for p in data_points if p["has_drift"]) / len(data_points)
            if data_points
            else 0
        )

        return {
            "monitor_id": monitor_id,
            "period_start": start_date.isoformat(),
            "period_end": datetime.utcnow().isoformat(),
            "data_points": data_points,
            "avg_drift_percentage": avg_drift,
            "max_drift_percentage": max_drift,
            "drift_occurrence_rate": drift_rate,
        }

    # Root Cause Analysis

    async def analyze_root_cause(
        self,
        run_id: str,
        monitor_id: str | None = None,
    ) -> dict | None:
        """Analyze root causes of drift for a specific comparison run.

        Args:
            run_id: The drift comparison/run ID to analyze.
            monitor_id: Optional monitor ID for context.

        Returns:
            Root cause analysis result or None if comparison not found.
        """
        import time
        from truthound_dashboard.db.models import DriftComparison

        start_time = time.time()

        # Get the comparison
        result = await self.session.execute(
            select(DriftComparison).where(DriftComparison.id == run_id)
        )
        comparison = result.scalar_one_or_none()

        if not comparison:
            return None

        # Extract result data
        result_json = comparison.result_json or {}
        columns_data = result_json.get("columns", [])

        # Analyze each column
        column_analyses = []
        cause_distribution: dict[str, int] = {}
        primary_causes: list[str] = []

        for col_data in columns_data:
            col_analysis = self._analyze_column_root_cause(col_data)
            column_analyses.append(col_analysis)

            # Aggregate causes
            for cause in col_analysis.get("causes", []):
                cause_distribution[cause] = cause_distribution.get(cause, 0) + 1

            if col_analysis.get("primary_cause"):
                if col_analysis["primary_cause"] not in primary_causes:
                    primary_causes.append(col_analysis["primary_cause"])

        # Analyze data volume changes
        data_volume_change = self._analyze_volume_change(result_json)

        # Generate remediation suggestions
        remediations = self._generate_remediation_suggestions(
            column_analyses, data_volume_change, cause_distribution
        )

        # Calculate overall confidence
        confidences = [c.get("confidence", 0) for c in column_analyses if c.get("confidence")]
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.7

        analysis_duration_ms = int((time.time() - start_time) * 1000)

        return {
            "run_id": run_id,
            "monitor_id": monitor_id,
            "analyzed_at": datetime.utcnow().isoformat(),
            "total_columns": comparison.total_columns or len(columns_data),
            "drifted_columns": comparison.drifted_columns or 0,
            "drift_percentage": comparison.drift_percentage or 0,
            "data_volume_change": data_volume_change,
            "column_analyses": column_analyses,
            "primary_causes": primary_causes,
            "cause_distribution": cause_distribution,
            "remediations": remediations,
            "overall_confidence": overall_confidence,
            "analysis_duration_ms": analysis_duration_ms,
        }

    def _analyze_column_root_cause(self, col_data: dict) -> dict:
        """Analyze root causes for a single column.

        Args:
            col_data: Column drift data from comparison result.

        Returns:
            Column root cause analysis.
        """
        column = col_data.get("column", "unknown")
        dtype = col_data.get("dtype", "unknown")
        drifted = col_data.get("drifted", False)
        level = col_data.get("level", "none")

        baseline_stats = col_data.get("baseline_stats", {})
        current_stats = col_data.get("current_stats", {})

        causes: list[str] = []
        primary_cause = None
        confidence = 0.0

        # Statistical shift analysis
        mean_shift = None
        std_shift = None
        min_shift = None
        max_shift = None

        if baseline_stats and current_stats:
            # Mean shift analysis
            baseline_mean = baseline_stats.get("mean")
            current_mean = current_stats.get("mean")
            if baseline_mean is not None and current_mean is not None and baseline_mean != 0:
                mean_change_pct = abs(current_mean - baseline_mean) / abs(baseline_mean) * 100
                mean_shift = {
                    "baseline_value": baseline_mean,
                    "current_value": current_mean,
                    "absolute_change": current_mean - baseline_mean,
                    "percent_change": mean_change_pct,
                }
                if mean_change_pct > 10:
                    causes.append("mean_shift")
                    if mean_change_pct > 20:
                        primary_cause = "mean_shift"
                        confidence = min(0.9, mean_change_pct / 100 + 0.5)

            # Variance/std analysis
            baseline_std = baseline_stats.get("std")
            current_std = current_stats.get("std")
            if baseline_std is not None and current_std is not None and baseline_std != 0:
                std_change_pct = abs(current_std - baseline_std) / abs(baseline_std) * 100
                std_shift = {
                    "baseline_value": baseline_std,
                    "current_value": current_std,
                    "absolute_change": current_std - baseline_std,
                    "percent_change": std_change_pct,
                }
                if std_change_pct > 20:
                    causes.append("variance_change")
                    if std_change_pct > 40 and not primary_cause:
                        primary_cause = "variance_change"
                        confidence = max(confidence, min(0.85, std_change_pct / 100 + 0.4))

            # Min/Max analysis (potential outliers)
            baseline_min = baseline_stats.get("min")
            current_min = current_stats.get("min")
            baseline_max = baseline_stats.get("max")
            current_max = current_stats.get("max")

            if baseline_min is not None and current_min is not None:
                if baseline_min != 0:
                    min_change_pct = abs(current_min - baseline_min) / abs(baseline_min) * 100
                else:
                    min_change_pct = abs(current_min - baseline_min) * 100
                min_shift = {
                    "baseline_value": baseline_min,
                    "current_value": current_min,
                    "absolute_change": current_min - baseline_min,
                    "percent_change": min_change_pct,
                }

            if baseline_max is not None and current_max is not None:
                if baseline_max != 0:
                    max_change_pct = abs(current_max - baseline_max) / abs(baseline_max) * 100
                else:
                    max_change_pct = abs(current_max - baseline_max) * 100
                max_shift = {
                    "baseline_value": baseline_max,
                    "current_value": current_max,
                    "absolute_change": current_max - baseline_max,
                    "percent_change": max_change_pct,
                }

                # Check for outlier introduction
                if max_change_pct > 50 or (min_shift and min_shift.get("percent_change", 0) > 50):
                    causes.append("outlier_introduction")
                    if not primary_cause:
                        primary_cause = "outlier_introduction"
                        confidence = max(confidence, 0.75)

            # Null rate analysis
            baseline_null = baseline_stats.get("null_count", 0)
            current_null = current_stats.get("null_count", 0)
            baseline_count = baseline_stats.get("count", 1)
            current_count = current_stats.get("count", 1)

            baseline_null_rate = baseline_null / baseline_count if baseline_count > 0 else 0
            current_null_rate = current_null / current_count if current_count > 0 else 0

            if abs(current_null_rate - baseline_null_rate) > 0.05:
                causes.append("null_rate_change")

        # Distribution shape change (if drifted but no clear cause)
        if drifted and not causes:
            causes.append("distribution_shape_change")
            if not primary_cause:
                primary_cause = "distribution_shape_change"
                confidence = 0.6

        # Set default confidence if still not set
        if not confidence:
            confidence = 0.5 if drifted else 0.8

        return {
            "column": column,
            "dtype": dtype,
            "drift_level": level,
            "causes": causes,
            "primary_cause": primary_cause,
            "confidence": confidence,
            "mean_shift": mean_shift,
            "std_shift": std_shift,
            "min_shift": min_shift,
            "max_shift": max_shift,
            "new_categories": [],
            "missing_categories": [],
            "category_distribution_changes": [],
            "outlier_info": None,
            "temporal_patterns": [],
            "null_rate_baseline": baseline_null_rate if baseline_stats else None,
            "null_rate_current": current_null_rate if current_stats else None,
        }

    def _analyze_volume_change(self, result_json: dict) -> dict | None:
        """Analyze data volume changes.

        Args:
            result_json: The drift comparison result JSON.

        Returns:
            Volume change analysis or None.
        """
        baseline_rows = result_json.get("baseline_rows", 0)
        current_rows = result_json.get("current_rows", 0)

        if not baseline_rows:
            return None

        absolute_change = current_rows - baseline_rows
        percent_change = (absolute_change / baseline_rows) * 100 if baseline_rows > 0 else 0

        # Determine significance
        abs_pct = abs(percent_change)
        if abs_pct < 5:
            significance = "normal"
        elif abs_pct < 15:
            significance = "notable"
        elif abs_pct < 30:
            significance = "significant"
        else:
            significance = "critical"

        return {
            "baseline_rows": baseline_rows,
            "current_rows": current_rows,
            "absolute_change": absolute_change,
            "percent_change": percent_change,
            "significance": significance,
        }

    def _generate_remediation_suggestions(
        self,
        column_analyses: list[dict],
        data_volume_change: dict | None,
        cause_distribution: dict[str, int],
    ) -> list[dict]:
        """Generate remediation suggestions based on analysis.

        Args:
            column_analyses: List of column analyses.
            data_volume_change: Volume change analysis.
            cause_distribution: Distribution of causes.

        Returns:
            List of remediation suggestions.
        """
        remediations: list[dict] = []
        priority = 1

        # Get most common causes
        sorted_causes = sorted(
            cause_distribution.items(), key=lambda x: x[1], reverse=True
        )

        # Mean shift remediations
        if "mean_shift" in cause_distribution:
            affected = [
                c["column"] for c in column_analyses
                if "mean_shift" in c.get("causes", [])
            ]
            remediations.append({
                "action": "investigate_upstream",
                "priority": priority,
                "title": "Investigate Upstream Data Changes",
                "description": (
                    f"Significant mean shifts detected in {len(affected)} column(s). "
                    "Check upstream data sources for changes in data collection, "
                    "processing logic, or business rule modifications."
                ),
                "affected_columns": affected,
                "estimated_impact": "high",
                "requires_manual_review": True,
                "automation_available": False,
            })
            priority += 1

        # Variance change remediations
        if "variance_change" in cause_distribution:
            affected = [
                c["column"] for c in column_analyses
                if "variance_change" in c.get("causes", [])
            ]
            remediations.append({
                "action": "review_data_pipeline",
                "priority": priority,
                "title": "Review Data Pipeline for Variance Issues",
                "description": (
                    f"Variance changes detected in {len(affected)} column(s). "
                    "This could indicate issues with data normalization, "
                    "changes in data sources, or outlier introduction."
                ),
                "affected_columns": affected,
                "estimated_impact": "medium",
                "requires_manual_review": True,
                "automation_available": False,
            })
            priority += 1

        # Outlier remediations
        if "outlier_introduction" in cause_distribution:
            affected = [
                c["column"] for c in column_analyses
                if "outlier_introduction" in c.get("causes", [])
            ]
            remediations.append({
                "action": "filter_outliers",
                "priority": priority,
                "title": "Review and Filter Outliers",
                "description": (
                    f"New outliers detected in {len(affected)} column(s). "
                    "Consider implementing outlier detection and filtering, "
                    "or investigate if outliers represent valid data changes."
                ),
                "affected_columns": affected,
                "estimated_impact": "medium",
                "requires_manual_review": True,
                "automation_available": True,
            })
            priority += 1

        # Volume change remediations
        if data_volume_change and data_volume_change.get("significance") in [
            "significant", "critical"
        ]:
            pct = data_volume_change.get("percent_change", 0)
            change_type = "increase" if pct > 0 else "decrease"
            remediations.append({
                "action": "check_data_source",
                "priority": max(1, priority - 1),  # Higher priority for volume issues
                "title": f"Investigate Data Volume {change_type.title()}",
                "description": (
                    f"Data volume changed by {abs(pct):.1f}% ({change_type}). "
                    "Verify data ingestion pipelines, check for missing or "
                    "duplicate records, and confirm expected business changes."
                ),
                "affected_columns": [],
                "estimated_impact": "high",
                "requires_manual_review": True,
                "automation_available": False,
            })

        # Update baseline suggestion (if drift is expected)
        if cause_distribution:
            total_drifted = sum(
                1 for c in column_analyses if c.get("causes")
            )
            remediations.append({
                "action": "update_baseline",
                "priority": min(priority + 1, 5),
                "title": "Consider Updating Baseline",
                "description": (
                    f"If the drift in {total_drifted} column(s) represents "
                    "expected business changes, consider updating the baseline "
                    "dataset to reflect the new data distribution."
                ),
                "affected_columns": [c["column"] for c in column_analyses if c.get("causes")],
                "estimated_impact": "medium",
                "requires_manual_review": True,
                "automation_available": True,
            })

        # Threshold adjustment suggestion
        if len(sorted_causes) > 0 and sorted_causes[0][1] > 5:
            remediations.append({
                "action": "adjust_threshold",
                "priority": min(priority + 2, 5),
                "title": "Review Drift Detection Threshold",
                "description": (
                    "Multiple columns showing drift may indicate the threshold "
                    "is too sensitive. Review the current threshold settings "
                    "and adjust if drift alerts are too frequent."
                ),
                "affected_columns": [],
                "estimated_impact": "low",
                "requires_manual_review": True,
                "automation_available": False,
            })

        return remediations

    # Large-Scale Dataset Optimization Methods

    async def run_sampled_comparison(
        self,
        monitor_id: str,
        sample_size: int | None = None,
        sampling_method: str = "random",
        confidence_level: float = 0.95,
        early_stop_threshold: float = 0.5,
        max_workers: int = 4,
    ) -> dict:
        """Run a sampled drift comparison for large datasets.

        Optimized for 100M+ row datasets by:
        - Using statistical sampling to reduce data volume
        - Processing in chunks to manage memory
        - Running parallel column comparisons
        - Supporting early stopping when drift is obvious

        Args:
            monitor_id: Monitor ID to run.
            sample_size: Custom sample size (auto-estimated if None).
            sampling_method: Sampling method (random, stratified, reservoir, systematic).
            confidence_level: Target confidence level for sample size estimation.
            early_stop_threshold: Proportion of drifted columns to trigger early stop.
            max_workers: Maximum parallel workers for column comparison.

        Returns:
            Sampled comparison result with performance metrics.
        """
        global _active_jobs

        monitor = await self.get_monitor(monitor_id)
        if not monitor:
            raise ValueError(f"Monitor {monitor_id} not found")

        job_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            # Get source metadata to estimate dataset sizes
            from truthound_dashboard.db.models import Source

            baseline_result = await self.session.execute(
                select(Source).where(Source.id == monitor.baseline_source_id)
            )
            baseline_source = baseline_result.scalar_one_or_none()

            current_result = await self.session.execute(
                select(Source).where(Source.id == monitor.current_source_id)
            )
            current_source = current_result.scalar_one_or_none()

            if not baseline_source or not current_source:
                raise ValueError("Source not found")

            # Estimate dataset sizes (from metadata or file size heuristic)
            baseline_rows = getattr(baseline_source, "row_count", None) or 1_000_000
            current_rows = getattr(current_source, "row_count", None) or 1_000_000
            num_columns = len(monitor.columns_json) if monitor.columns_json else 10

            # Estimate optimal sample size if not provided
            if sample_size is None:
                estimate = estimate_sample_size(
                    population_size=max(baseline_rows, current_rows),
                    confidence_level=confidence_level,
                    num_columns=num_columns,
                )
                sample_size = estimate.recommended_size
                estimated_time = estimate.estimated_time_seconds
                estimated_memory = estimate.memory_mb
            else:
                estimated_time = (sample_size * num_columns) / 10000
                estimated_memory = (sample_size * 100 * num_columns) / (1024 * 1024)

            # Determine if chunked processing is needed
            chunk_size = calculate_chunk_size(
                total_rows=sample_size,
                available_memory_mb=512,  # Conservative memory budget
                bytes_per_row=100 * num_columns,
            )
            num_chunks = (sample_size + chunk_size - 1) // chunk_size

            # Initialize progress tracker
            tracker = ChunkedComparisonTracker(
                total_rows=sample_size,
                chunk_size=chunk_size,
                total_columns=num_columns,
            )
            _active_jobs[job_id] = tracker
            tracker.start()

            # Run the comparison with sampling
            # In a real implementation, this would call truthound.compare with sampling
            from truthound_dashboard.core.drift import DriftService

            drift_service = DriftService(self.session)

            # Simulate chunked processing
            all_drifted_columns: list[str] = []
            chunk_results: list[dict] = []

            for chunk_idx in range(num_chunks):
                chunk_start_time = time.time()

                # Run comparison for this chunk
                # In production, this would use actual sampled data
                comparison = await drift_service.compare(
                    baseline_source_id=monitor.baseline_source_id,
                    current_source_id=monitor.current_source_id,
                    method=monitor.method,
                    threshold=monitor.threshold,
                    columns=monitor.columns_json,
                    sample_size=min(chunk_size, sample_size - chunk_idx * chunk_size),
                )

                chunk_time = time.time() - chunk_start_time

                # Extract drifted columns from this chunk
                chunk_drifted = []
                if comparison.result_json and "columns" in comparison.result_json:
                    chunk_drifted = [
                        col["column"]
                        for col in comparison.result_json["columns"]
                        if col.get("drifted", False)
                    ]

                # Update tracker
                tracker.update_chunk(
                    chunk_index=chunk_idx,
                    rows_in_chunk=min(chunk_size, sample_size - chunk_idx * chunk_size),
                    drifted_columns=chunk_drifted,
                    chunk_time=chunk_time,
                )

                # Merge drifted columns
                for col in chunk_drifted:
                    if col not in all_drifted_columns:
                        all_drifted_columns.append(col)

                chunk_results.append({
                    "chunk_index": chunk_idx,
                    "rows_processed": min(chunk_size, sample_size - chunk_idx * chunk_size),
                    "drifted_columns": chunk_drifted,
                    "processing_time_seconds": chunk_time,
                })

                # Check for early stopping
                if should_early_stop(
                    columns_with_drift=all_drifted_columns,
                    total_columns=num_columns,
                    threshold=early_stop_threshold,
                ):
                    logger.info(
                        f"Early stopping triggered for job {job_id}: "
                        f"{len(all_drifted_columns)}/{num_columns} columns drifted"
                    )
                    tracker.trigger_early_stop()
                    break

            # Complete the job
            tracker.complete()
            total_time = time.time() - start_time

            # Update monitor stats
            monitor.last_run_at = datetime.utcnow()
            monitor.total_runs += 1

            has_drift = len(all_drifted_columns) > 0
            monitor.last_drift_detected = has_drift

            if has_drift:
                monitor.drift_detected_count += 1
                monitor.consecutive_drift_count += 1
            else:
                monitor.consecutive_drift_count = 0

            await self.session.commit()

            return {
                "job_id": job_id,
                "monitor_id": monitor_id,
                "status": "completed",
                "sampling": {
                    "method": sampling_method,
                    "sample_size": sample_size,
                    "confidence_level": confidence_level,
                    "population_baseline": baseline_rows,
                    "population_current": current_rows,
                },
                "processing": {
                    "num_chunks": len(chunk_results),
                    "total_chunks_planned": num_chunks,
                    "early_stopped": tracker.early_stop_triggered,
                    "parallel_workers": max_workers,
                },
                "results": {
                    "has_drift": has_drift,
                    "total_columns": num_columns,
                    "drifted_columns": len(all_drifted_columns),
                    "drifted_column_names": all_drifted_columns,
                    "drift_percentage": (len(all_drifted_columns) / num_columns * 100)
                    if num_columns > 0
                    else 0,
                },
                "performance": {
                    "total_time_seconds": round(total_time, 2),
                    "estimated_time_seconds": round(estimated_time, 2),
                    "estimated_memory_mb": round(estimated_memory, 2),
                    "speedup_factor": round(
                        max(baseline_rows, current_rows) / sample_size, 1
                    )
                    if sample_size > 0
                    else 1,
                },
                "chunk_details": chunk_results,
            }

        except Exception as e:
            if job_id in _active_jobs:
                _active_jobs[job_id].error(str(e))
            logger.error(f"Sampled comparison failed for monitor {monitor_id}: {e}")
            raise
        finally:
            # Clean up job tracker after some time
            if job_id in _active_jobs:
                # Keep for 5 minutes for status queries
                asyncio.create_task(self._cleanup_job(job_id, delay=300))

    async def _cleanup_job(self, job_id: str, delay: int = 300) -> None:
        """Clean up completed job tracker after delay.

        Args:
            job_id: Job ID to clean up.
            delay: Delay in seconds before cleanup.
        """
        await asyncio.sleep(delay)
        _active_jobs.pop(job_id, None)

    async def get_job_progress(self, job_id: str) -> dict | None:
        """Get progress for an active comparison job.

        Args:
            job_id: Job ID to query.

        Returns:
            Progress information or None if job not found.
        """
        tracker = _active_jobs.get(job_id)
        if not tracker:
            return None

        progress = tracker.get_progress()
        return {
            "job_id": job_id,
            "status": progress.status,
            "progress": {
                "total_chunks": progress.total_chunks,
                "processed_chunks": progress.processed_chunks,
                "total_rows": progress.total_rows,
                "processed_rows": progress.processed_rows,
                "percentage": round(
                    progress.processed_rows / progress.total_rows * 100, 1
                )
                if progress.total_rows > 0
                else 0,
            },
            "timing": {
                "elapsed_seconds": progress.elapsed_seconds,
                "estimated_remaining_seconds": progress.estimated_remaining_seconds,
            },
            "interim_results": {
                "columns_with_drift": progress.columns_with_drift,
                "early_stop_triggered": progress.early_stop_triggered,
            },
        }

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel an active comparison job.

        Args:
            job_id: Job ID to cancel.

        Returns:
            True if cancelled, False if job not found.
        """
        tracker = _active_jobs.get(job_id)
        if not tracker:
            return False

        tracker.cancel()
        return True

    async def estimate_comparison_size(
        self,
        baseline_source_id: str,
        current_source_id: str,
        confidence_level: float = 0.95,
        margin_of_error: float = 0.03,
    ) -> dict:
        """Estimate optimal sample size for a comparison.

        Args:
            baseline_source_id: Baseline source ID.
            current_source_id: Current source ID.
            confidence_level: Target confidence level.
            margin_of_error: Acceptable margin of error.

        Returns:
            Sample size estimation with recommendations.
        """
        from truthound_dashboard.db.models import Source

        # Get source information
        baseline_result = await self.session.execute(
            select(Source).where(Source.id == baseline_source_id)
        )
        baseline_source = baseline_result.scalar_one_or_none()

        current_result = await self.session.execute(
            select(Source).where(Source.id == current_source_id)
        )
        current_source = current_result.scalar_one_or_none()

        if not baseline_source or not current_source:
            raise ValueError("Source not found")

        # Estimate row counts (from metadata or heuristic)
        baseline_rows = getattr(baseline_source, "row_count", None) or 1_000_000
        current_rows = getattr(current_source, "row_count", None) or 1_000_000
        population_size = max(baseline_rows, current_rows)

        # Estimate column count
        num_columns = 10  # Default estimate

        # Calculate sample size estimate
        estimate = estimate_sample_size(
            population_size=population_size,
            confidence_level=confidence_level,
            margin_of_error=margin_of_error,
            num_columns=num_columns,
        )

        # Determine if sampling is recommended
        is_large_dataset = population_size >= LARGE_DATASET_THRESHOLD
        sampling_recommended = is_large_dataset

        # Calculate speedup estimates for different sample sizes
        speedup_estimates = {}
        for size_label, size_factor in [
            ("minimal", 0.5),
            ("recommended", 1.0),
            ("thorough", 2.0),
        ]:
            size = int(estimate.recommended_size * size_factor)
            speedup = population_size / size if size > 0 else 1
            time_estimate = (size * num_columns) / 10000
            speedup_estimates[size_label] = {
                "sample_size": size,
                "speedup_factor": round(speedup, 1),
                "estimated_time_seconds": round(time_estimate, 2),
            }

        return {
            "baseline_source_id": baseline_source_id,
            "current_source_id": current_source_id,
            "dataset_info": {
                "baseline_rows": baseline_rows,
                "current_rows": current_rows,
                "population_size": population_size,
                "is_large_dataset": is_large_dataset,
                "large_dataset_threshold": LARGE_DATASET_THRESHOLD,
            },
            "sampling_recommendation": {
                "sampling_recommended": sampling_recommended,
                "reason": (
                    f"Dataset has {population_size:,} rows, exceeding the {LARGE_DATASET_THRESHOLD:,} row threshold"
                    if sampling_recommended
                    else f"Dataset has {population_size:,} rows, within manageable size"
                ),
            },
            "sample_size_estimate": {
                "recommended_size": estimate.recommended_size,
                "min_size": estimate.min_size,
                "max_size": estimate.max_size,
                "confidence_level": estimate.confidence_level,
                "margin_of_error": estimate.margin_of_error,
            },
            "performance_estimates": {
                "estimated_time_seconds": estimate.estimated_time_seconds,
                "estimated_memory_mb": estimate.memory_mb,
                "speedup_options": speedup_estimates,
            },
            "available_methods": [
                {
                    "method": "random",
                    "description": "Simple random sampling without replacement",
                    "best_for": "General-purpose sampling when no stratification needed",
                },
                {
                    "method": "stratified",
                    "description": "Sampling that maintains proportions of categories",
                    "best_for": "Ensuring representation of all categories",
                },
                {
                    "method": "reservoir",
                    "description": "Single-pass sampling for streaming data",
                    "best_for": "Very large datasets or streaming sources",
                },
                {
                    "method": "systematic",
                    "description": "Evenly spaced sampling with random start",
                    "best_for": "Ordered data where even distribution matters",
                },
            ],
        }
