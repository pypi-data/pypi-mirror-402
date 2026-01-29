"""Schema evolution Pydantic schemas.

This module defines schemas for schema evolution detection,
version tracking, and change notifications.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field

from .base import BaseSchema, IDMixin, TimestampMixin


class SchemaChangeType(str, Enum):
    """Type of schema change."""

    COLUMN_ADDED = "column_added"
    COLUMN_REMOVED = "column_removed"
    TYPE_CHANGED = "type_changed"
    NULLABLE_CHANGED = "nullable_changed"
    CONSTRAINT_CHANGED = "constraint_changed"
    COLUMN_RENAMED = "column_renamed"


class SchemaChangeSeverity(str, Enum):
    """Severity level of schema change."""

    BREAKING = "breaking"
    WARNING = "warning"
    NON_BREAKING = "non_breaking"


# =============================================================================
# Schema Version Schemas
# =============================================================================


class SchemaVersionBase(BaseSchema):
    """Base schema for schema version."""

    version_number: int = Field(..., description="Sequential version number")
    column_count: int = Field(..., description="Number of columns in this version")
    columns: list[str] = Field(
        default_factory=list, description="List of column names"
    )


class SchemaVersionResponse(SchemaVersionBase, IDMixin, TimestampMixin):
    """Schema version response."""

    source_id: str = Field(..., description="Source ID")
    schema_id: str = Field(..., description="Schema record ID")
    schema_hash: str = Field(..., description="SHA256 hash of schema structure")
    column_snapshot: dict[str, Any] = Field(
        default_factory=dict, description="Full column definitions"
    )


class SchemaVersionSummary(BaseSchema):
    """Summary of a schema version for lists."""

    id: str = Field(..., description="Version ID")
    version_number: int = Field(..., description="Version number")
    column_count: int = Field(..., description="Number of columns")
    created_at: datetime = Field(..., description="When version was created")


class SchemaVersionListResponse(BaseSchema):
    """List response for schema versions."""

    versions: list[SchemaVersionSummary] = Field(
        default_factory=list, description="List of schema versions"
    )
    total: int = Field(default=0, description="Total count")
    source_id: str = Field(..., description="Source ID")


# =============================================================================
# Schema Change Schemas
# =============================================================================


class SchemaChangeBase(BaseSchema):
    """Base schema for individual change."""

    change_type: SchemaChangeType = Field(..., description="Type of change")
    column_name: str = Field(..., description="Affected column name")
    old_value: str | None = Field(default=None, description="Previous value")
    new_value: str | None = Field(default=None, description="New value")
    severity: SchemaChangeSeverity = Field(
        default=SchemaChangeSeverity.NON_BREAKING,
        description="Severity of the change",
    )


class SchemaChangeResponse(SchemaChangeBase, IDMixin):
    """Response schema for a single schema change."""

    source_id: str = Field(..., description="Source ID")
    from_version_id: str | None = Field(
        default=None, description="Previous version ID"
    )
    to_version_id: str = Field(..., description="New version ID")
    description: str = Field(..., description="Human-readable description")
    created_at: datetime = Field(..., description="When change was detected")


class SchemaChangeListResponse(BaseSchema):
    """List response for schema changes."""

    changes: list[SchemaChangeResponse] = Field(
        default_factory=list, description="List of changes"
    )
    total: int = Field(default=0, description="Total count")
    source_id: str = Field(..., description="Source ID")


# =============================================================================
# Schema Evolution Detection Schemas
# =============================================================================


class SchemaEvolutionRequest(BaseSchema):
    """Request to detect schema changes."""

    force_relearn: bool = Field(
        default=False,
        description="Force re-learning schema even if unchanged",
    )


class SchemaEvolutionResponse(BaseSchema):
    """Response for schema evolution detection."""

    source_id: str = Field(..., description="Source ID")
    source_name: str = Field(..., description="Source name")
    from_version: int | None = Field(
        default=None, description="Previous version number"
    )
    to_version: int = Field(..., description="New version number")
    has_changes: bool = Field(..., description="Whether changes were detected")
    total_changes: int = Field(default=0, description="Total number of changes")
    breaking_changes: int = Field(default=0, description="Number of breaking changes")
    changes: list[SchemaChangeResponse] = Field(
        default_factory=list, description="List of detected changes"
    )
    detected_at: datetime = Field(..., description="When detection was performed")


class SchemaEvolutionSummary(BaseSchema):
    """Summary of schema evolution for a source."""

    source_id: str = Field(..., description="Source ID")
    current_version: int = Field(..., description="Current version number")
    total_versions: int = Field(..., description="Total number of versions")
    total_changes: int = Field(..., description="Total changes across all versions")
    breaking_changes: int = Field(..., description="Total breaking changes")
    last_change_at: datetime | None = Field(
        default=None, description="Last change timestamp"
    )
