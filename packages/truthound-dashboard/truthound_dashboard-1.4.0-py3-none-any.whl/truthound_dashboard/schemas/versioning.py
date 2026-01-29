"""Versioning schemas for validation result versioning.

Defines request/response models for the versioning API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from .base import BaseSchema


# Versioning strategy types
VersioningStrategyType = Literal["incremental", "semantic", "timestamp", "gitlike"]


class VersionInfoResponse(BaseSchema):
    """Version information response."""

    version_id: str = Field(..., description="Unique version identifier")
    version_number: str = Field(..., description="Human-readable version number")
    validation_id: str = Field(..., description="Associated validation ID")
    source_id: str = Field(..., description="Associated source ID")
    strategy: VersioningStrategyType = Field(..., description="Versioning strategy used")
    created_at: datetime = Field(..., description="Version creation timestamp")
    parent_version_id: str | None = Field(None, description="Parent version ID")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    content_hash: str | None = Field(None, description="Hash of validation content")


class VersionListResponse(BaseSchema):
    """Response for listing versions."""

    success: bool = Field(default=True)
    data: list[VersionInfoResponse] = Field(..., description="List of versions")
    total: int = Field(..., description="Total number of versions")
    source_id: str = Field(..., description="Source ID for these versions")


class IssueChange(BaseSchema):
    """Represents a changed issue between versions."""

    key: str = Field(..., description="Issue key (column:issue_type)")
    from_issue: dict[str, Any] = Field(..., alias="from", description="Original issue")
    to_issue: dict[str, Any] = Field(..., alias="to", description="New issue")

    class Config:
        populate_by_name = True


class VersionDiffResponse(BaseSchema):
    """Version comparison/diff response."""

    from_version: VersionInfoResponse = Field(..., description="Source version")
    to_version: VersionInfoResponse = Field(..., description="Target version")
    issues_added: list[dict[str, Any]] = Field(
        default_factory=list, description="Issues added in target version"
    )
    issues_removed: list[dict[str, Any]] = Field(
        default_factory=list, description="Issues removed in target version"
    )
    issues_changed: list[dict[str, Any]] = Field(
        default_factory=list, description="Issues that changed between versions"
    )
    summary_changes: dict[str, Any] = Field(
        default_factory=dict, description="Summary of changes"
    )
    has_changes: bool = Field(..., description="Whether there are any changes")


class VersionCompareRequest(BaseSchema):
    """Request to compare two versions."""

    from_version_id: str = Field(..., description="Source version ID to compare from")
    to_version_id: str = Field(..., description="Target version ID to compare to")


class VersionHistoryResponse(BaseSchema):
    """Response for version history chain."""

    success: bool = Field(default=True)
    data: list[VersionInfoResponse] = Field(..., description="Version history chain")
    depth: int = Field(..., description="Depth of history returned")


class CreateVersionRequest(BaseSchema):
    """Request to create a new version for a validation."""

    validation_id: str = Field(..., description="Validation ID to version")
    strategy: VersioningStrategyType | None = Field(
        None, description="Versioning strategy (defaults to incremental)"
    )
    metadata: dict[str, Any] | None = Field(
        None, description="Additional version metadata"
    )


class CreateVersionResponse(BaseSchema):
    """Response after creating a version."""

    success: bool = Field(default=True)
    data: VersionInfoResponse = Field(..., description="Created version info")
    message: str = Field(..., description="Success message")


# Rollback schemas
class RollbackRequest(BaseSchema):
    """Request to rollback to a previous version."""

    target_version_id: str = Field(..., description="Version ID to rollback to")
    create_new_validation: bool = Field(
        default=True,
        description="Whether to create a new validation record for the rollback"
    )


class RollbackResponse(BaseSchema):
    """Response after a rollback operation."""

    success: bool = Field(default=True)
    source_id: str = Field(..., description="Source ID that was rolled back")
    from_version: VersionInfoResponse | None = Field(
        None, description="Version rolled back from"
    )
    to_version: VersionInfoResponse | None = Field(
        None, description="Version rolled back to"
    )
    new_validation_id: str | None = Field(
        None, description="ID of the new validation created (if any)"
    )
    message: str = Field(..., description="Status message")
    rolled_back_at: datetime = Field(..., description="When rollback was performed")


class RollbackAvailabilityResponse(BaseSchema):
    """Response for checking rollback availability."""

    success: bool = Field(default=True)
    can_rollback: bool = Field(..., description="Whether rollback is available")
    current_version_id: str | None = Field(
        None, description="Current active version ID"
    )
    available_versions: int = Field(
        ..., description="Number of available versions"
    )
    rollback_targets: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of versions available for rollback"
    )
