"""Maintenance and retention policy schemas.

This module defines schemas for maintenance and retention policy API operations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from .base import BaseSchema


class RetentionPolicyConfig(BaseSchema):
    """Configuration for data retention policies.

    Defines how long different types of data are retained.
    """

    validation_retention_days: int = Field(
        default=90,
        ge=1,
        le=3650,
        description="Days to keep validation records (1-3650)",
    )
    profile_keep_per_source: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Number of profile records to keep per source (1-100)",
    )
    notification_log_retention_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Days to keep notification logs (1-365)",
    )
    run_vacuum: bool = Field(
        default=True,
        description="Run SQLite VACUUM after cleanup to reclaim space",
    )
    enabled: bool = Field(
        default=True,
        description="Whether automatic maintenance is enabled",
    )


class RetentionPolicyResponse(RetentionPolicyConfig):
    """Response with current retention policy configuration."""

    pass


class CleanupResultItem(BaseSchema):
    """Result of a single cleanup task."""

    task_name: str = Field(..., description="Name of the cleanup task")
    records_deleted: int = Field(
        default=0, ge=0, description="Number of records deleted"
    )
    duration_ms: int = Field(default=0, ge=0, description="Duration in milliseconds")
    success: bool = Field(default=True, description="Whether the task succeeded")
    error: str | None = Field(default=None, description="Error message if failed")


class MaintenanceReportResponse(BaseSchema):
    """Response for maintenance run results."""

    started_at: datetime = Field(..., description="When maintenance started")
    completed_at: datetime | None = Field(
        default=None, description="When maintenance completed"
    )
    results: list[CleanupResultItem] = Field(
        default_factory=list, description="Results of each cleanup task"
    )
    total_deleted: int = Field(
        default=0, ge=0, description="Total records deleted across all tasks"
    )
    total_duration_ms: int = Field(
        default=0, ge=0, description="Total duration in milliseconds"
    )
    vacuum_performed: bool = Field(
        default=False, description="Whether VACUUM was run"
    )
    vacuum_error: str | None = Field(
        default=None, description="VACUUM error message if failed"
    )
    success: bool = Field(default=True, description="Whether all tasks succeeded")


class CleanupTriggerRequest(BaseSchema):
    """Request to trigger manual cleanup."""

    tasks: list[str] | None = Field(
        default=None,
        description=(
            "Specific tasks to run. If None, all tasks are run. "
            "Available: validation_cleanup, profile_cleanup, notification_log_cleanup"
        ),
        examples=[["validation_cleanup", "profile_cleanup"]],
    )
    run_vacuum: bool = Field(
        default=False,
        description="Run VACUUM after cleanup (may take time for large databases)",
    )


class MaintenanceStatusResponse(BaseSchema):
    """Response with maintenance system status."""

    enabled: bool = Field(..., description="Whether automatic maintenance is enabled")
    last_run_at: datetime | None = Field(
        default=None, description="Timestamp of last maintenance run"
    )
    next_scheduled_at: datetime | None = Field(
        default=None, description="Timestamp of next scheduled run"
    )
    config: RetentionPolicyConfig = Field(
        ..., description="Current retention policy configuration"
    )
    available_tasks: list[str] = Field(
        ..., description="List of available cleanup tasks"
    )


class CacheStatsResponse(BaseSchema):
    """Response with cache statistics."""

    total_entries: int = Field(..., ge=0, description="Total entries in cache")
    expired_entries: int = Field(..., ge=0, description="Number of expired entries")
    valid_entries: int = Field(..., ge=0, description="Number of valid entries")
    max_size: int = Field(..., ge=0, description="Maximum cache size")
    hit_rate: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Cache hit rate (0-1) if available",
    )


class CacheClearRequest(BaseSchema):
    """Request to clear cache."""

    pattern: str | None = Field(
        default=None,
        description="Optional pattern to match keys to clear (prefix match)",
        examples=["validation:", "source:"],
    )
    namespace: str | None = Field(
        default=None,
        description="Specific cache namespace to clear",
    )
