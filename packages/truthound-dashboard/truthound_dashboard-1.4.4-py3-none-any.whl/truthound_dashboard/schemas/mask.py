"""Pydantic schemas for data masking (th.mask) operations.

Provides schemas for masking requests, responses, and history.
Supports three masking strategies: redact, hash, fake.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import Field

from .base import BaseSchema, IDMixin, TimestampMixin


class MaskingStrategy(str, Enum):
    """Masking strategy options.

    - redact: Replace values with asterisks (e.g., "john@example.com" -> "****")
    - hash: Replace values with SHA256 hash (deterministic, can be used for joins)
    - fake: Replace values with realistic fake data (e.g., "john@example.com" -> "alice@test.org")
    """

    REDACT = "redact"
    HASH = "hash"
    FAKE = "fake"


MaskingStrategyLiteral = Literal["redact", "hash", "fake"]


class MaskStatus(str, Enum):
    """Status of a masking operation."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ERROR = "error"


class MaskRequest(BaseSchema):
    """Request body for running a masking operation.

    Attributes:
        columns: Optional list of columns to mask. If None, auto-detects PII.
        strategy: Masking strategy to use. Defaults to "redact".
        output_format: Output file format. Defaults to "csv".
    """

    columns: list[str] | None = Field(
        default=None,
        description="Columns to mask. If not specified, auto-detects PII columns.",
    )
    strategy: MaskingStrategyLiteral = Field(
        default="redact",
        description="Masking strategy: 'redact' (asterisks), 'hash' (SHA256), 'fake' (realistic data)",
    )
    output_format: Literal["csv", "parquet", "json"] = Field(
        default="csv",
        description="Output file format",
    )


class MaskSummary(BaseSchema):
    """Summary of a masking operation.

    Attributes:
        source_id: ID of the source that was masked.
        source_name: Name of the source.
        status: Current status of the operation.
        strategy: Masking strategy used.
        columns_masked: Number of columns that were masked.
        row_count: Number of rows processed.
        duration_ms: Operation duration in milliseconds.
    """

    source_id: str
    source_name: str | None = None
    status: str
    strategy: str
    columns_masked: int
    row_count: int | None = None
    duration_ms: int | None = None


class MaskResponse(BaseSchema, IDMixin, TimestampMixin):
    """Response for a masking operation.

    Attributes:
        id: Unique identifier for the masking operation.
        source_id: ID of the source that was masked.
        status: Current status (pending, running, success, failed, error).
        strategy: Masking strategy used.
        output_path: Path to the masked output file.
        columns_masked: List of columns that were masked.
        auto_detected: Whether PII columns were auto-detected.
        row_count: Number of rows processed.
        column_count: Total number of columns.
        duration_ms: Operation duration in milliseconds.
        error_message: Error message if operation failed.
        started_at: When the operation started.
        completed_at: When the operation completed.
    """

    source_id: str
    status: str
    strategy: str
    output_path: str | None = None
    columns_masked: list[str] | None = None
    auto_detected: bool = False
    row_count: int | None = None
    column_count: int | None = None
    duration_ms: int | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @classmethod
    def from_db(cls, db_mask: object) -> MaskResponse:
        """Create response from database model.

        Args:
            db_mask: DataMask database model instance.

        Returns:
            MaskResponse instance.
        """
        return cls(
            id=db_mask.id,
            source_id=db_mask.source_id,
            status=db_mask.status,
            strategy=db_mask.strategy,
            output_path=db_mask.output_path,
            columns_masked=db_mask.columns_masked,
            auto_detected=db_mask.auto_detected,
            row_count=db_mask.row_count,
            column_count=db_mask.column_count,
            duration_ms=db_mask.duration_ms,
            error_message=db_mask.error_message,
            started_at=db_mask.started_at,
            completed_at=db_mask.completed_at,
            created_at=db_mask.created_at,
            updated_at=getattr(db_mask, "updated_at", None),
        )


class MaskListItem(BaseSchema, IDMixin):
    """List item for masking operations.

    Attributes:
        id: Unique identifier.
        source_id: ID of the source.
        source_name: Name of the source.
        status: Current status.
        strategy: Masking strategy used.
        columns_masked: Number of columns masked.
        row_count: Number of rows processed.
        duration_ms: Operation duration in milliseconds.
        created_at: When the operation was created.
    """

    source_id: str
    source_name: str | None = None
    status: str
    strategy: str
    columns_masked: int = 0
    row_count: int | None = None
    duration_ms: int | None = None
    created_at: datetime

    @classmethod
    def from_db(cls, db_mask: object, source_name: str | None = None) -> MaskListItem:
        """Create list item from database model.

        Args:
            db_mask: DataMask database model instance.
            source_name: Optional source name.

        Returns:
            MaskListItem instance.
        """
        return cls(
            id=db_mask.id,
            source_id=db_mask.source_id,
            source_name=source_name or getattr(db_mask.source, "name", None),
            status=db_mask.status,
            strategy=db_mask.strategy,
            columns_masked=len(db_mask.columns_masked) if db_mask.columns_masked else 0,
            row_count=db_mask.row_count,
            duration_ms=db_mask.duration_ms,
            created_at=db_mask.created_at,
        )


class MaskListResponse(BaseSchema):
    """Response for listing masking operations.

    Attributes:
        data: List of masking operation items.
        total: Total number of items.
        limit: Maximum items per page.
    """

    data: list[MaskListItem]
    total: int
    limit: int = 20
