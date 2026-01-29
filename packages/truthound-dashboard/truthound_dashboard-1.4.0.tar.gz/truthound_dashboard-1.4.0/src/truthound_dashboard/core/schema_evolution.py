"""Schema evolution detection service.

This module provides functionality for detecting and tracking
schema changes over time, enabling schema evolution monitoring.

Features:
    - Automatic schema change detection
    - Breaking change identification
    - Version history tracking
    - Notification integration for schema changes
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.db import (
    BaseRepository,
    Schema,
    Source,
)
from truthound_dashboard.db.models import SchemaChange, SchemaVersion
from truthound_dashboard.schemas.schema_evolution import (
    SchemaChangeResponse,
    SchemaChangeSeverity,
    SchemaChangeType,
    SchemaEvolutionResponse,
    SchemaEvolutionSummary,
    SchemaVersionResponse,
    SchemaVersionSummary,
)

logger = logging.getLogger(__name__)


class SchemaVersionRepository(BaseRepository[SchemaVersion]):
    """Repository for SchemaVersion model operations."""

    model = SchemaVersion

    async def get_latest_for_source(self, source_id: str) -> SchemaVersion | None:
        """Get the latest schema version for a source.

        Args:
            source_id: Source ID.

        Returns:
            Latest schema version or None.
        """
        result = await self.session.execute(
            select(SchemaVersion)
            .where(SchemaVersion.source_id == source_id)
            .order_by(SchemaVersion.version_number.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_for_source(
        self,
        source_id: str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[SchemaVersion]:
        """Get schema versions for a source.

        Args:
            source_id: Source ID.
            limit: Maximum to return.
            offset: Number to skip.

        Returns:
            Sequence of schema versions.
        """
        return await self.list(
            offset=offset,
            limit=limit,
            filters=[SchemaVersion.source_id == source_id],
            order_by=[SchemaVersion.version_number.desc()],
        )

    async def get_next_version_number(self, source_id: str) -> int:
        """Get the next version number for a source.

        Args:
            source_id: Source ID.

        Returns:
            Next version number (1 if no previous versions).
        """
        result = await self.session.execute(
            select(func.max(SchemaVersion.version_number)).where(
                SchemaVersion.source_id == source_id
            )
        )
        max_version = result.scalar_one_or_none()
        return (max_version or 0) + 1

    async def get_by_hash(
        self, source_id: str, schema_hash: str
    ) -> SchemaVersion | None:
        """Get schema version by hash.

        Args:
            source_id: Source ID.
            schema_hash: Schema hash.

        Returns:
            Schema version or None.
        """
        result = await self.session.execute(
            select(SchemaVersion)
            .where(SchemaVersion.source_id == source_id)
            .where(SchemaVersion.schema_hash == schema_hash)
            .limit(1)
        )
        return result.scalar_one_or_none()


class SchemaChangeRepository(BaseRepository[SchemaChange]):
    """Repository for SchemaChange model operations."""

    model = SchemaChange

    async def get_for_source(
        self,
        source_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[SchemaChange]:
        """Get schema changes for a source.

        Args:
            source_id: Source ID.
            limit: Maximum to return.
            offset: Number to skip.

        Returns:
            Sequence of schema changes.
        """
        return await self.list(
            offset=offset,
            limit=limit,
            filters=[SchemaChange.source_id == source_id],
            order_by=[SchemaChange.created_at.desc()],
        )

    async def get_for_version(
        self, to_version_id: str
    ) -> Sequence[SchemaChange]:
        """Get changes for a specific version transition.

        Args:
            to_version_id: Target version ID.

        Returns:
            Sequence of changes.
        """
        return await self.list(
            filters=[SchemaChange.to_version_id == to_version_id],
            order_by=[SchemaChange.created_at.desc()],
        )

    async def count_breaking_changes(self, source_id: str) -> int:
        """Count breaking changes for a source.

        Args:
            source_id: Source ID.

        Returns:
            Count of breaking changes.
        """
        result = await self.session.execute(
            select(func.count(SchemaChange.id))
            .where(SchemaChange.source_id == source_id)
            .where(SchemaChange.severity == "breaking")
        )
        return result.scalar_one() or 0


class SchemaEvolutionService:
    """Service for schema evolution detection and tracking.

    This service handles:
    - Schema version creation and tracking
    - Change detection between versions
    - Breaking change identification
    - Automatic notification dispatch for schema changes

    Notifications are sent automatically when:
    - Any schema changes are detected (event_type: schema_changed)
    - Breaking changes are detected (triggers breaking_schema_change rules)
    """

    def __init__(
        self,
        session: AsyncSession,
        *,
        enable_notifications: bool = True,
    ):
        """Initialize service.

        Args:
            session: Database session.
            enable_notifications: Whether to send notifications on schema changes.
        """
        self.session = session
        self.version_repo = SchemaVersionRepository(session)
        self.change_repo = SchemaChangeRepository(session)
        self._enable_notifications = enable_notifications

    def _compute_schema_hash(self, schema_json: dict[str, Any]) -> str:
        """Compute deterministic hash of schema structure.

        Args:
            schema_json: Schema JSON to hash.

        Returns:
            SHA256 hash string.
        """
        # Extract and normalize columns for consistent hashing
        columns = schema_json.get("columns", {})
        normalized = {}
        for col_name, col_def in sorted(columns.items()):
            # Only hash structural properties
            normalized[col_name] = {
                "dtype": col_def.get("dtype"),
                "nullable": col_def.get("nullable"),
            }

        # Create deterministic JSON string
        json_str = json.dumps(normalized, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()

    def _extract_column_snapshot(
        self, schema_json: dict[str, Any]
    ) -> dict[str, Any]:
        """Extract column definitions for snapshot.

        Args:
            schema_json: Full schema JSON.

        Returns:
            Column definitions dictionary.
        """
        columns = schema_json.get("columns", {})
        snapshot = {}
        for col_name, col_def in columns.items():
            snapshot[col_name] = {
                "dtype": col_def.get("dtype"),
                "nullable": col_def.get("nullable"),
                "unique": col_def.get("unique"),
            }
        return snapshot

    # Type compatibility matrix: (old_type, new_type) -> is_compatible
    # Compatible means data can be safely converted without loss
    TYPE_COMPATIBILITY_MATRIX: dict[tuple[str, str], bool] = {
        # Safe widening conversions
        ("int8", "int16"): True,
        ("int8", "int32"): True,
        ("int8", "int64"): True,
        ("int16", "int32"): True,
        ("int16", "int64"): True,
        ("int32", "int64"): True,
        ("float32", "float64"): True,
        ("int8", "float32"): True,
        ("int8", "float64"): True,
        ("int16", "float32"): True,
        ("int16", "float64"): True,
        ("int32", "float64"): True,
        # String conversions (anything can become string)
        ("int8", "string"): True,
        ("int16", "string"): True,
        ("int32", "string"): True,
        ("int64", "string"): True,
        ("float32", "string"): True,
        ("float64", "string"): True,
        ("boolean", "string"): True,
        ("date", "string"): True,
        ("datetime", "string"): True,
        # Same type aliases
        ("integer", "int64"): True,
        ("int64", "integer"): True,
        ("float", "float64"): True,
        ("float64", "float"): True,
        ("str", "string"): True,
        ("string", "str"): True,
        ("bool", "boolean"): True,
        ("boolean", "bool"): True,
    }

    # Types that can be widened (ordered by width)
    TYPE_WIDTH_ORDER: dict[str, int] = {
        "int8": 1, "int16": 2, "int32": 3, "int64": 4, "integer": 4,
        "float32": 5, "float64": 6, "float": 6,
        "string": 10, "str": 10, "text": 10,
    }

    def _normalize_type(self, dtype: str | None) -> str:
        """Normalize type name for comparison.

        Args:
            dtype: Data type string.

        Returns:
            Normalized type name.
        """
        if not dtype:
            return "unknown"

        dtype_lower = dtype.lower().strip()

        # Normalize common aliases
        type_aliases = {
            "int": "int64",
            "integer": "int64",
            "bigint": "int64",
            "smallint": "int16",
            "tinyint": "int8",
            "float": "float64",
            "double": "float64",
            "real": "float32",
            "str": "string",
            "text": "string",
            "varchar": "string",
            "char": "string",
            "bool": "boolean",
            "timestamp": "datetime",
            "timestamptz": "datetime",
        }

        return type_aliases.get(dtype_lower, dtype_lower)

    def _is_type_compatible(self, old_type: str, new_type: str) -> bool:
        """Check if type change is backward compatible (widening).

        Args:
            old_type: Old data type.
            new_type: New data type.

        Returns:
            True if change is compatible (widening conversion).
        """
        old_norm = self._normalize_type(old_type)
        new_norm = self._normalize_type(new_type)

        # Same type is always compatible
        if old_norm == new_norm:
            return True

        # Check explicit compatibility matrix
        if (old_norm, new_norm) in self.TYPE_COMPATIBILITY_MATRIX:
            return self.TYPE_COMPATIBILITY_MATRIX[(old_norm, new_norm)]

        # Check width-based compatibility
        old_width = self.TYPE_WIDTH_ORDER.get(old_norm)
        new_width = self.TYPE_WIDTH_ORDER.get(new_norm)

        if old_width is not None and new_width is not None:
            # Widening is compatible, narrowing is not
            return new_width >= old_width

        return False

    def _get_type_change_severity(
        self, old_type: str, new_type: str
    ) -> SchemaChangeSeverity:
        """Determine severity of a type change.

        Args:
            old_type: Old data type.
            new_type: New data type.

        Returns:
            Severity level of the change.
        """
        old_norm = self._normalize_type(old_type)
        new_norm = self._normalize_type(new_type)

        # Same type = no change
        if old_norm == new_norm:
            return SchemaChangeSeverity.NON_BREAKING

        # Compatible widening conversion
        if self._is_type_compatible(old_type, new_type):
            return SchemaChangeSeverity.NON_BREAKING

        # Narrowing or incompatible conversion = breaking
        return SchemaChangeSeverity.BREAKING

    def _detect_column_changes(
        self,
        old_columns: dict[str, Any],
        new_columns: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Detect changes between two column snapshots.

        Args:
            old_columns: Previous column definitions.
            new_columns: New column definitions.

        Returns:
            List of detected changes.
        """
        changes = []
        old_names = set(old_columns.keys())
        new_names = set(new_columns.keys())

        # Added columns (non-breaking if nullable, warning if not nullable)
        for col_name in new_names - old_names:
            col_def = new_columns[col_name]
            is_nullable = col_def.get("nullable", True)
            severity = (
                SchemaChangeSeverity.NON_BREAKING
                if is_nullable
                else SchemaChangeSeverity.WARNING
            )
            changes.append({
                "change_type": SchemaChangeType.COLUMN_ADDED.value,
                "column_name": col_name,
                "old_value": None,
                "new_value": col_def.get("dtype"),
                "severity": severity.value,
                "details": {
                    "nullable": is_nullable,
                    "reason": (
                        "New column is nullable"
                        if is_nullable
                        else "New non-nullable column may require default value"
                    ),
                },
            })

        # Removed columns (breaking change)
        for col_name in old_names - new_names:
            col_def = old_columns[col_name]
            changes.append({
                "change_type": SchemaChangeType.COLUMN_REMOVED.value,
                "column_name": col_name,
                "old_value": col_def.get("dtype"),
                "new_value": None,
                "severity": SchemaChangeSeverity.BREAKING.value,
                "details": {
                    "reason": "Existing column removed - queries may fail",
                },
            })

        # Check changes in common columns
        for col_name in old_names & new_names:
            old_def = old_columns[col_name]
            new_def = new_columns[col_name]

            old_type = old_def.get("dtype")
            new_type = new_def.get("dtype")

            # Type changes with compatibility analysis
            if old_type != new_type:
                severity = self._get_type_change_severity(old_type, new_type)
                is_compatible = self._is_type_compatible(old_type, new_type)

                changes.append({
                    "change_type": SchemaChangeType.TYPE_CHANGED.value,
                    "column_name": col_name,
                    "old_value": old_type,
                    "new_value": new_type,
                    "severity": severity.value,
                    "details": {
                        "is_compatible": is_compatible,
                        "old_type_normalized": self._normalize_type(old_type),
                        "new_type_normalized": self._normalize_type(new_type),
                        "reason": (
                            "Compatible type widening"
                            if is_compatible
                            else "Incompatible type change - data may be lost"
                        ),
                    },
                })

            # Nullable changes
            old_nullable = old_def.get("nullable", True)
            new_nullable = new_def.get("nullable", True)

            if old_nullable != new_nullable:
                # nullable -> non-nullable is breaking
                # non-nullable -> nullable is safe
                if old_nullable and not new_nullable:
                    severity = SchemaChangeSeverity.BREAKING
                    reason = "Column became non-nullable - existing nulls will cause errors"
                else:
                    severity = SchemaChangeSeverity.NON_BREAKING
                    reason = "Column became nullable - no impact on existing data"

                changes.append({
                    "change_type": SchemaChangeType.NULLABLE_CHANGED.value,
                    "column_name": col_name,
                    "old_value": old_nullable,
                    "new_value": new_nullable,
                    "severity": severity.value,
                    "details": {
                        "reason": reason,
                    },
                })

            # Unique constraint changes
            old_unique = old_def.get("unique", False)
            new_unique = new_def.get("unique", False)

            if old_unique != new_unique:
                if not old_unique and new_unique:
                    severity = SchemaChangeSeverity.WARNING
                    reason = "Unique constraint added - duplicates will be rejected"
                else:
                    severity = SchemaChangeSeverity.NON_BREAKING
                    reason = "Unique constraint removed"

                changes.append({
                    "change_type": SchemaChangeType.CONSTRAINT_CHANGED.value,
                    "column_name": col_name,
                    "old_value": f"unique={old_unique}",
                    "new_value": f"unique={new_unique}",
                    "severity": severity.value,
                    "details": {
                        "constraint_type": "unique",
                        "reason": reason,
                    },
                })

        return changes

    async def create_version(
        self,
        source_id: str,
        schema: Schema,
    ) -> tuple[SchemaVersion, list[SchemaChange]]:
        """Create a new schema version snapshot.

        Args:
            source_id: Source ID.
            schema: Schema record.

        Returns:
            Tuple of (new version, list of changes).
        """
        schema_json = schema.schema_json or {}
        schema_hash = self._compute_schema_hash(schema_json)

        # Check if this exact schema already exists
        existing = await self.version_repo.get_by_hash(source_id, schema_hash)
        if existing:
            return existing, []

        # Get previous version
        previous = await self.version_repo.get_latest_for_source(source_id)
        next_version_number = await self.version_repo.get_next_version_number(
            source_id
        )

        # Create column snapshot
        column_snapshot = self._extract_column_snapshot(schema_json)

        # Create new version
        new_version = await self.version_repo.create(
            source_id=source_id,
            schema_id=schema.id,
            version_number=next_version_number,
            schema_hash=schema_hash,
            column_snapshot=column_snapshot,
        )

        # Detect changes
        changes = []
        if previous:
            detected = self._detect_column_changes(
                previous.column_snapshot,
                column_snapshot,
            )
            for change_data in detected:
                change = await self.change_repo.create(
                    source_id=source_id,
                    from_version_id=previous.id,
                    to_version_id=new_version.id,
                    **change_data,
                )
                changes.append(change)

        await self.session.commit()
        return new_version, changes

    async def _send_schema_change_notification(
        self,
        source: Source,
        from_version: int | None,
        to_version: int,
        total_changes: int,
        breaking_changes: int,
        changes: list[SchemaChange],
    ) -> None:
        """Send notification for schema changes.

        Args:
            source: Source record.
            from_version: Previous version number (None if first version).
            to_version: New version number.
            total_changes: Total number of changes.
            breaking_changes: Number of breaking changes.
            changes: List of change records.
        """
        if not self._enable_notifications:
            return

        try:
            # Import here to avoid circular imports
            from truthound_dashboard.core.notifications.dispatcher import (
                create_dispatcher,
            )

            dispatcher = create_dispatcher(self.session)

            # Format changes for notification
            change_details = [
                {
                    "type": c.change_type,
                    "column": c.column_name,
                    "old_value": c.old_value,
                    "new_value": c.new_value,
                    "breaking": c.is_breaking,
                }
                for c in changes[:10]  # Limit to first 10 for notification
            ]

            results = await dispatcher.notify_schema_changed(
                source_id=source.id,
                source_name=source.name,
                from_version=from_version,
                to_version=to_version,
                total_changes=total_changes,
                breaking_changes=breaking_changes,
                changes=change_details,
            )

            if results:
                successful = sum(1 for r in results if r.success)
                logger.info(
                    f"Schema change notification sent: {successful}/{len(results)} "
                    f"channels (source={source.name}, changes={total_changes})"
                )
        except Exception as e:
            logger.warning(f"Failed to send schema change notification: {e}")

    async def detect_changes(
        self,
        source: Source,
        schema: Schema,
        *,
        notify: bool = True,
    ) -> SchemaEvolutionResponse:
        """Detect schema changes for a source.

        Automatically sends notifications when changes are detected
        (if notifications are enabled and notify=True).

        Args:
            source: Source record.
            schema: Current schema.
            notify: Whether to send notification for this detection.

        Returns:
            Evolution detection response.
        """
        new_version, changes = await self.create_version(source.id, schema)

        # Get previous version info
        versions = await self.version_repo.get_for_source(source.id, limit=2)
        from_version = versions[1].version_number if len(versions) > 1 else None

        # Convert changes to response format
        change_responses = [
            SchemaChangeResponse(
                id=c.id,
                source_id=c.source_id,
                from_version_id=c.from_version_id,
                to_version_id=c.to_version_id,
                change_type=SchemaChangeType(c.change_type),
                column_name=c.column_name,
                old_value=c.old_value,
                new_value=c.new_value,
                severity=SchemaChangeSeverity(c.severity),
                description=c.description,
                created_at=c.created_at,
            )
            for c in changes
        ]

        breaking_count = sum(1 for c in changes if c.is_breaking)

        # Send notification if changes were detected
        if changes and notify:
            await self._send_schema_change_notification(
                source=source,
                from_version=from_version,
                to_version=new_version.version_number,
                total_changes=len(changes),
                breaking_changes=breaking_count,
                changes=changes,
            )

        return SchemaEvolutionResponse(
            source_id=source.id,
            source_name=source.name,
            from_version=from_version,
            to_version=new_version.version_number,
            has_changes=len(changes) > 0,
            total_changes=len(changes),
            breaking_changes=breaking_count,
            changes=change_responses,
            detected_at=datetime.utcnow(),
        )

    async def get_version_history(
        self,
        source_id: str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[SchemaVersionSummary]:
        """Get schema version history for a source.

        Args:
            source_id: Source ID.
            limit: Maximum to return.
            offset: Number to skip.

        Returns:
            List of version summaries.
        """
        versions = await self.version_repo.get_for_source(
            source_id, limit=limit, offset=offset
        )
        return [
            SchemaVersionSummary(
                id=v.id,
                version_number=v.version_number,
                column_count=v.column_count,
                created_at=v.created_at,
            )
            for v in versions
        ]

    async def get_version(self, version_id: str) -> SchemaVersionResponse | None:
        """Get a specific schema version.

        Args:
            version_id: Version ID.

        Returns:
            Version response or None.
        """
        version = await self.version_repo.get_by_id(version_id)
        if not version:
            return None

        return SchemaVersionResponse(
            id=version.id,
            source_id=version.source_id,
            schema_id=version.schema_id,
            version_number=version.version_number,
            column_count=version.column_count,
            columns=version.column_names,
            schema_hash=version.schema_hash,
            column_snapshot=version.column_snapshot,
            created_at=version.created_at,
            updated_at=version.updated_at,
        )

    async def get_changes(
        self,
        source_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[SchemaChangeResponse]:
        """Get schema changes for a source.

        Args:
            source_id: Source ID.
            limit: Maximum to return.
            offset: Number to skip.

        Returns:
            List of change responses.
        """
        changes = await self.change_repo.get_for_source(
            source_id, limit=limit, offset=offset
        )
        return [
            SchemaChangeResponse(
                id=c.id,
                source_id=c.source_id,
                from_version_id=c.from_version_id,
                to_version_id=c.to_version_id,
                change_type=SchemaChangeType(c.change_type),
                column_name=c.column_name,
                old_value=c.old_value,
                new_value=c.new_value,
                severity=SchemaChangeSeverity(c.severity),
                description=c.description,
                created_at=c.created_at,
            )
            for c in changes
        ]

    async def get_evolution_summary(
        self, source_id: str
    ) -> SchemaEvolutionSummary:
        """Get evolution summary for a source.

        Args:
            source_id: Source ID.

        Returns:
            Evolution summary.
        """
        # Get version count
        versions = await self.version_repo.get_for_source(source_id, limit=1)
        latest_version = versions[0] if versions else None

        total_versions = 0
        if latest_version:
            total_versions = latest_version.version_number

        # Get change counts
        changes = await self.change_repo.get_for_source(source_id, limit=1000)
        total_changes = len(changes)
        breaking_changes = await self.change_repo.count_breaking_changes(source_id)

        # Get last change timestamp
        last_change_at = None
        if changes:
            last_change_at = changes[0].created_at

        return SchemaEvolutionSummary(
            source_id=source_id,
            current_version=latest_version.version_number if latest_version else 0,
            total_versions=total_versions,
            total_changes=total_changes,
            breaking_changes=breaking_changes,
            last_change_at=last_change_at,
        )
