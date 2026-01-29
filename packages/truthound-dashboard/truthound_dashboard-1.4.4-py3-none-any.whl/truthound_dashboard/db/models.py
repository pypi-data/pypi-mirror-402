"""SQLAlchemy database models.

This module defines all database models for the dashboard.
Models use mixins from base.py for consistent behavior.

Models:
    - Source: Data source configuration
    - Schema: Learned schemas from th.learn
    - Rule: Custom validation rules for sources
    - Validation: Validation run results
    - AppSettings: Application-level settings
    - NotificationChannel: Notification channel configuration
    - NotificationRule: Notification trigger rules
    - NotificationLog: Notification delivery log

Phase 5 Models:
    - GlossaryCategory: Business term categories
    - GlossaryTerm: Business glossary terms
    - TermRelationship: Relationships between terms
    - TermHistory: Term change history
    - CatalogAsset: Data catalog assets
    - AssetColumn: Asset column metadata
    - AssetTag: Asset tags
    - Comment: Comments on resources
    - Activity: Activity log
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


# =============================================================================
# Phase 5: Enums
# =============================================================================


class TermStatus(str, Enum):
    """Status of a glossary term."""

    DRAFT = "draft"
    APPROVED = "approved"
    DEPRECATED = "deprecated"


class RelationshipType(str, Enum):
    """Type of relationship between terms."""

    SYNONYM = "synonym"
    RELATED = "related"
    PARENT = "parent"
    CHILD = "child"


class AssetType(str, Enum):
    """Type of catalog asset."""

    TABLE = "table"
    FILE = "file"
    API = "api"


class SensitivityLevel(str, Enum):
    """Sensitivity level for data columns."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class ResourceType(str, Enum):
    """Type of resource for comments and activities."""

    TERM = "term"
    CATEGORY = "category"
    ASSET = "asset"
    COLUMN = "column"


class ActivityAction(str, Enum):
    """Type of activity action."""

    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    COMMENTED = "commented"
    STATUS_CHANGED = "status_changed"
    MAPPED = "mapped"
    UNMAPPED = "unmapped"


# =============================================================================
# Schema Evolution Enums
# =============================================================================


class SchemaChangeType(str, Enum):
    """Type of schema change detected."""

    COLUMN_ADDED = "column_added"
    COLUMN_REMOVED = "column_removed"
    TYPE_CHANGED = "type_changed"


class SchemaChangeSeverity(str, Enum):
    """Severity level of schema change."""

    BREAKING = "breaking"
    NON_BREAKING = "non_breaking"


# =============================================================================
# Schedule Trigger Enums
# =============================================================================


class TriggerType(str, Enum):
    """Type of schedule trigger."""

    CRON = "cron"
    INTERVAL = "interval"
    DATA_CHANGE = "data_change"
    COMPOSITE = "composite"
    EVENT = "event"
    MANUAL = "manual"
    WEBHOOK = "webhook"  # External webhook triggers


class Source(Base, UUIDMixin, TimestampMixin):
    """Data source model.

    Represents a data source that can be validated.
    Supports various types: file, postgresql, mysql, snowflake, bigquery.

    Attributes:
        id: Unique identifier (UUID).
        name: Human-readable name for the source.
        type: Source type (file, postgresql, etc.).
        config: JSON configuration specific to source type.
        is_active: Whether the source is active.
        last_validated_at: Timestamp of last validation.
    """

    __tablename__ = "sources"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_validated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __init__(self, **kwargs: Any) -> None:
        if "is_active" not in kwargs:
            kwargs["is_active"] = True
        super().__init__(**kwargs)

    # Relationships
    schemas: Mapped[list[Schema]] = relationship(
        "Schema",
        back_populates="source",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    rules: Mapped[list[Rule]] = relationship(
        "Rule",
        back_populates="source",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(Rule.created_at)",
    )
    validations: Mapped[list[Validation]] = relationship(
        "Validation",
        back_populates="source",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(Validation.created_at)",
    )
    profiles: Mapped[list[Profile]] = relationship(
        "Profile",
        back_populates="source",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(Profile.created_at)",
    )
    schedules: Mapped[list[Schedule]] = relationship(
        "Schedule",
        back_populates="source",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    # Phase 5: Catalog assets linked to this source
    assets: Mapped[list[CatalogAsset]] = relationship(
        "CatalogAsset",
        back_populates="source",
        lazy="selectin",
    )
    # Generated reports for this source
    generated_reports: Mapped[list["GeneratedReport"]] = relationship(
        "GeneratedReport",
        back_populates="source",
        lazy="selectin",
        order_by="desc(GeneratedReport.created_at)",
    )

    @property
    def source_path(self) -> str | None:
        """Get the data path from config."""
        return self.config.get("path") or self.config.get("connection_string")

    @property
    def latest_schema(self) -> Schema | None:
        """Get the most recent schema."""
        if self.schemas:
            return max(self.schemas, key=lambda s: s.created_at)
        return None

    @property
    def latest_validation(self) -> Validation | None:
        """Get the most recent validation."""
        if self.validations:
            return self.validations[0]
        return None

    @property
    def active_rules(self) -> list[Rule]:
        """Get all active rules for this source."""
        return [r for r in self.rules if r.is_active]

    @property
    def active_rule(self) -> Rule | None:
        """Get the active rule for this source (most recent)."""
        active = self.active_rules
        return active[0] if active else None


class Rule(Base, UUIDMixin, TimestampMixin):
    """Custom validation rules model.

    Stores custom validation rules for data sources in YAML format.
    Rules are used by truthound validators during validation runs.

    Attributes:
        id: Unique identifier (UUID).
        source_id: Reference to parent Source.
        name: Human-readable rule name.
        description: Optional description of the rule.
        rules_yaml: YAML content defining validation rules.
        rules_json: Parsed rules as JSON for programmatic access.
        is_active: Whether this rule set is currently active.
        version: Optional version string for tracking changes.

    Example rules_yaml format:
        columns:
          user_id:
            not_null: true
            unique: true
          email:
            pattern: "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$"
          age:
            min: 0
            max: 150
    """

    __tablename__ = "rules"

    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="Default Rules",
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    rules_yaml: Mapped[str] = mapped_column(Text, nullable=False)
    rules_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    source: Mapped[Source] = relationship("Source", back_populates="rules")

    @property
    def column_rules(self) -> dict[str, Any]:
        """Get column-level rules from JSON."""
        if self.rules_json and "columns" in self.rules_json:
            return self.rules_json["columns"]
        return {}

    @property
    def table_rules(self) -> dict[str, Any]:
        """Get table-level rules from JSON."""
        if self.rules_json and "table" in self.rules_json:
            return self.rules_json["table"]
        return {}

    @property
    def column_count(self) -> int:
        """Get number of columns with rules defined."""
        return len(self.column_rules)

    def deactivate(self) -> None:
        """Mark this rule as inactive."""
        self.is_active = False

    def activate(self) -> None:
        """Mark this rule as active."""
        self.is_active = True


class Schema(Base, UUIDMixin, TimestampMixin):
    """Learned schema model.

    Stores truthound Schema objects (from th.learn) which contain:
    - Column definitions with dtype, nullable, unique, constraints
    - Row count and statistics
    - Version information

    Attributes:
        id: Unique identifier (UUID).
        source_id: Reference to parent Source.
        schema_yaml: YAML representation for display/editing.
        schema_json: Full schema as JSON for programmatic access.
        row_count: Number of rows when schema was learned.
        version: Schema version string.
        is_active: Whether this is the active schema for the source.
    """

    __tablename__ = "schemas"

    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    schema_yaml: Mapped[str] = mapped_column(Text, nullable=False)
    schema_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    source: Mapped[Source] = relationship("Source", back_populates="schemas")

    @property
    def columns(self) -> list[str]:
        """Get list of column names from schema."""
        if self.schema_json and "columns" in self.schema_json:
            return list(self.schema_json["columns"].keys())
        return []


class Validation(Base, UUIDMixin):
    """Validation result model.

    Stores results from th.check validation runs.

    Attributes:
        id: Unique identifier (UUID).
        source_id: Reference to parent Source.
        status: Current status (pending, running, success, failed, error).
        passed: Whether validation passed (no issues).
        has_critical: Whether critical issues were found.
        has_high: Whether high severity issues were found.
        total_issues: Total number of issues found.
        result_json: Full validation result as JSON.
        duration_ms: Validation duration in milliseconds.
    """

    __tablename__ = "validations"

    # Composite index for efficient history queries (source + time ordering)
    __table_args__ = (
        Index("idx_validations_source_created", "source_id", "created_at"),
    )

    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )

    # Validation results summary
    passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_critical: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_high: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    total_issues: Mapped[int | None] = mapped_column(Integer, nullable=True)
    critical_issues: Mapped[int | None] = mapped_column(Integer, nullable=True)
    high_issues: Mapped[int | None] = mapped_column(Integer, nullable=True)
    medium_issues: Mapped[int | None] = mapped_column(Integer, nullable=True)
    low_issues: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Data statistics
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Full result and timing
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    source: Mapped[Source] = relationship("Source", back_populates="validations")
    generated_reports: Mapped[list["GeneratedReport"]] = relationship(
        "GeneratedReport",
        back_populates="validation",
        lazy="selectin",
        order_by="desc(GeneratedReport.created_at)",
    )

    @property
    def issues(self) -> list[dict[str, Any]]:
        """Get list of issues from result JSON."""
        if self.result_json and "issues" in self.result_json:
            return self.result_json["issues"]
        return []

    @property
    def is_complete(self) -> bool:
        """Check if validation has completed (success, failed, or error)."""
        return self.status in ("success", "failed", "error")

    def mark_started(self) -> None:
        """Mark validation as started."""
        self.status = "running"
        self.started_at = datetime.utcnow()

    def mark_completed(
        self,
        passed: bool,
        result: dict[str, Any],
    ) -> None:
        """Mark validation as completed with results."""
        self.status = "success" if passed else "failed"
        self.passed = passed
        self.result_json = result
        self.completed_at = datetime.utcnow()

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)

    def mark_error(self, message: str) -> None:
        """Mark validation as errored."""
        self.status = "error"
        self.error_message = message
        self.completed_at = datetime.utcnow()

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)


class Profile(Base, UUIDMixin, TimestampMixin):
    """Data profile model.

    Stores profiling results from th.profile() for historical tracking.

    Attributes:
        id: Unique identifier (UUID).
        source_id: Reference to parent Source.
        profile_json: Full profile result as JSON.
        row_count: Number of rows profiled.
        column_count: Number of columns.
        size_bytes: Data size in bytes.
    """

    __tablename__ = "profiles"

    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    profile_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    source: Mapped[Source] = relationship("Source", back_populates="profiles")

    @property
    def columns(self) -> list[dict[str, Any]]:
        """Get column profiles from JSON."""
        if self.profile_json and "columns" in self.profile_json:
            return self.profile_json["columns"]
        return []


class Schedule(Base, UUIDMixin, TimestampMixin):
    """Validation schedule model.

    Manages scheduled validation runs with flexible trigger types.
    Supports cron, interval, data change detection, and composite triggers.

    Attributes:
        id: Unique identifier (UUID).
        name: Human-readable schedule name.
        source_id: Reference to Source to validate.
        trigger_type: Type of trigger (cron, interval, data_change, composite).
        trigger_config: JSON configuration specific to trigger type.
        cron_expression: Legacy cron expression (for backward compatibility).
        is_active: Whether schedule is active.
        notify_on_failure: Send notification on validation failure.
        last_run_at: Timestamp of last execution.
        next_run_at: Timestamp of next scheduled run.
        trigger_count: Total number of times this schedule has triggered.
        last_trigger_result: Result of last trigger evaluation.
        config: Additional configuration (validators, schema_path, etc.).
    """

    __tablename__ = "schedules"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # New flexible trigger system
    trigger_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=TriggerType.CRON.value,
        index=True,
    )
    trigger_config: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Trigger-specific configuration (threshold, metrics, etc.)",
    )
    # Legacy field for backward compatibility
    cron_expression: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_on_failure: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Trigger state tracking
    trigger_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_trigger_result: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Result of last trigger evaluation",
    )
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    source: Mapped[Source] = relationship("Source", back_populates="schedules")

    def pause(self) -> None:
        """Pause this schedule."""
        self.is_active = False

    def resume(self) -> None:
        """Resume this schedule."""
        self.is_active = True

    def mark_run(self, next_run: datetime | None = None) -> None:
        """Mark schedule as run and update next run time."""
        self.last_run_at = datetime.utcnow()
        self.next_run_at = next_run
        self.trigger_count += 1

    def update_trigger_result(self, result: dict[str, Any]) -> None:
        """Update the last trigger evaluation result."""
        self.last_trigger_result = result

    @property
    def effective_trigger_type(self) -> TriggerType:
        """Get the effective trigger type.

        Falls back to CRON if trigger_type is not set (legacy schedules).
        """
        try:
            return TriggerType(self.trigger_type)
        except ValueError:
            return TriggerType.CRON

    @property
    def effective_cron_expression(self) -> str | None:
        """Get the effective cron expression.

        For CRON triggers, returns the expression from trigger_config or legacy field.
        """
        if self.trigger_type == TriggerType.CRON.value:
            if self.trigger_config and "expression" in self.trigger_config:
                return self.trigger_config["expression"]
            return self.cron_expression
        return None

    def get_trigger_summary(self) -> str:
        """Get a human-readable summary of the trigger configuration."""
        trigger_type = self.effective_trigger_type

        if trigger_type == TriggerType.CRON:
            expr = self.effective_cron_expression
            return f"Cron: {expr}" if expr else "Cron: (not configured)"

        elif trigger_type == TriggerType.INTERVAL:
            if self.trigger_config:
                parts = []
                if self.trigger_config.get("days"):
                    parts.append(f"{self.trigger_config['days']}d")
                if self.trigger_config.get("hours"):
                    parts.append(f"{self.trigger_config['hours']}h")
                if self.trigger_config.get("minutes"):
                    parts.append(f"{self.trigger_config['minutes']}m")
                if self.trigger_config.get("seconds"):
                    parts.append(f"{self.trigger_config['seconds']}s")
                return f"Every {' '.join(parts)}" if parts else "Interval: (not configured)"
            return "Interval: (not configured)"

        elif trigger_type == TriggerType.DATA_CHANGE:
            threshold = self.trigger_config.get("change_threshold", 0.05) if self.trigger_config else 0.05
            return f"Data change >= {threshold * 100:.0f}%"

        elif trigger_type == TriggerType.COMPOSITE:
            if self.trigger_config:
                operator = self.trigger_config.get("operator", "and").upper()
                count = len(self.trigger_config.get("triggers", []))
                return f"Composite: {count} triggers ({operator})"
            return "Composite: (not configured)"

        elif trigger_type == TriggerType.EVENT:
            if self.trigger_config:
                events = self.trigger_config.get("event_types", [])
                return f"Events: {', '.join(events[:2])}{'...' if len(events) > 2 else ''}"
            return "Event: (not configured)"

        elif trigger_type == TriggerType.MANUAL:
            return "Manual trigger only"

        return f"{trigger_type.value}: (unknown)"


class DriftComparison(Base, UUIDMixin, TimestampMixin):
    """Drift comparison result model.

    Stores results from th.compare() drift detection.

    Attributes:
        id: Unique identifier (UUID).
        baseline_source_id: Reference to baseline Source.
        current_source_id: Reference to current Source.
        has_drift: Whether drift was detected.
        has_high_drift: Whether high-severity drift was detected.
        total_columns: Total columns compared.
        drifted_columns: Number of columns with drift.
        result_json: Full comparison result as JSON.
        config: Comparison configuration (method, threshold, etc.).
    """

    __tablename__ = "drift_comparisons"

    baseline_source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    current_source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    has_drift: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_high_drift: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    total_columns: Mapped[int | None] = mapped_column(Integer, nullable=True)
    drifted_columns: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    baseline_source: Mapped[Source] = relationship(
        "Source",
        foreign_keys=[baseline_source_id],
        backref="baseline_comparisons",
    )
    current_source: Mapped[Source] = relationship(
        "Source",
        foreign_keys=[current_source_id],
        backref="current_comparisons",
    )

    @property
    def drift_percentage(self) -> float:
        """Calculate percentage of columns with drift."""
        if self.total_columns and self.total_columns > 0:
            return (self.drifted_columns or 0) / self.total_columns * 100
        return 0.0

    @property
    def column_results(self) -> list[dict[str, Any]]:
        """Get per-column drift results."""
        if self.result_json and "columns" in self.result_json:
            return self.result_json["columns"]
        return []


class MaskingStrategy(str, Enum):
    """Masking strategy enum."""

    REDACT = "redact"
    HASH = "hash"
    FAKE = "fake"


class DataMask(Base, UUIDMixin):
    """Data masking operation model.

    Stores results from th.mask() data masking operations.
    Supports three strategies: redact (asterisks), hash (SHA256), fake (realistic data).

    Attributes:
        id: Unique identifier (UUID).
        source_id: Reference to parent Source.
        status: Current status (pending, running, success, failed, error).
        strategy: Masking strategy used (redact, hash, fake).
        output_path: Path to the masked output file.
        columns_masked: List of columns that were masked.
        row_count: Number of rows processed.
        column_count: Number of columns in the data.
        auto_detected: Whether PII columns were auto-detected.
        result_json: Full mask result as JSON.
        duration_ms: Operation duration in milliseconds.
    """

    __tablename__ = "data_masks"

    # Composite index for efficient history queries (source + time ordering)
    __table_args__ = (
        Index("idx_data_masks_source_created", "source_id", "created_at"),
    )

    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )

    # Masking configuration
    strategy: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=MaskingStrategy.REDACT.value,
        index=True,
    )
    output_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    columns_masked: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    auto_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Data statistics
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Full result and timing
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    source: Mapped[Source] = relationship(
        "Source",
        backref="data_masks",
    )

    @property
    def is_complete(self) -> bool:
        """Check if masking operation has completed."""
        return self.status in ("success", "failed", "error")

    @property
    def masked_column_count(self) -> int:
        """Get number of columns that were masked."""
        return len(self.columns_masked) if self.columns_masked else 0

    def mark_started(self) -> None:
        """Mark operation as started."""
        self.status = "running"
        self.started_at = datetime.utcnow()

    def mark_completed(
        self,
        result: dict[str, Any],
    ) -> None:
        """Mark operation as completed with results."""
        self.status = "success"
        self.result_json = result
        self.completed_at = datetime.utcnow()

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)

    def mark_error(self, message: str) -> None:
        """Mark operation as errored."""
        self.status = "error"
        self.error_message = message
        self.completed_at = datetime.utcnow()

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)


class PIIScan(Base, UUIDMixin):
    """PII scan result model.

    Stores results from th.scan() PII detection runs.

    Attributes:
        id: Unique identifier (UUID).
        source_id: Reference to parent Source.
        status: Current status (pending, running, success, failed, error).
        total_columns_scanned: Total columns that were scanned.
        columns_with_pii: Number of columns containing PII.
        total_findings: Total number of PII findings.
        has_violations: Whether any regulation violations were found.
        total_violations: Number of regulation violations.
        min_confidence: Confidence threshold used for this scan.
        regulations_checked: List of regulations checked.
        result_json: Full scan result as JSON.
        duration_ms: Scan duration in milliseconds.
    """

    __tablename__ = "pii_scans"

    # Composite index for efficient history queries (source + time ordering)
    __table_args__ = (
        Index("idx_pii_scans_source_created", "source_id", "created_at"),
    )

    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )

    # Scan summary
    total_columns_scanned: Mapped[int | None] = mapped_column(Integer, nullable=True)
    columns_with_pii: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_findings: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_violations: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    total_violations: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Data statistics
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Configuration used
    min_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    regulations_checked: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # Full result and timing
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    source: Mapped[Source] = relationship(
        "Source",
        backref="pii_scans",
    )

    @property
    def findings(self) -> list[dict[str, Any]]:
        """Get list of PII findings from result JSON."""
        if self.result_json and "findings" in self.result_json:
            return self.result_json["findings"]
        return []

    @property
    def violations(self) -> list[dict[str, Any]]:
        """Get list of regulation violations from result JSON."""
        if self.result_json and "violations" in self.result_json:
            return self.result_json["violations"]
        return []

    @property
    def is_complete(self) -> bool:
        """Check if scan has completed (success, failed, or error)."""
        return self.status in ("success", "failed", "error")

    def mark_started(self) -> None:
        """Mark scan as started."""
        self.status = "running"
        self.started_at = datetime.utcnow()

    def mark_completed(
        self,
        has_violations: bool,
        result: dict[str, Any],
    ) -> None:
        """Mark scan as completed with results."""
        self.status = "success" if not has_violations else "failed"
        self.has_violations = has_violations
        self.result_json = result
        self.completed_at = datetime.utcnow()

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)

    def mark_error(self, message: str) -> None:
        """Mark scan as errored."""
        self.status = "error"
        self.error_message = message
        self.completed_at = datetime.utcnow()

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)


class AppSettings(Base):
    """Application settings model.

    Stores key-value configuration that can be modified at runtime.

    Attributes:
        key: Setting key (primary key).
        value: JSON value for the setting.
        description: Human-readable description.
    """

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


# =============================================================================
# Phase 3: Notification Models
# =============================================================================


class NotificationChannel(Base, UUIDMixin, TimestampMixin):
    """Notification channel configuration model.

    Represents a configured notification channel (Slack, Email, Webhook, etc.).
    Uses a polymorphic pattern where channel-specific configuration is stored
    in the 'config' JSON field.

    Attributes:
        id: Unique identifier (UUID).
        type: Channel type (slack, email, webhook, etc.).
        name: Human-readable channel name.
        config: JSON configuration specific to channel type.
        is_active: Whether channel is active.

    Example configs:
        Slack: {"webhook_url": "https://hooks.slack.com/..."}
        Email: {"smtp_host": "...", "smtp_port": 587, "recipients": [...]}
        Webhook: {"url": "...", "headers": {...}, "method": "POST"}
    """

    __tablename__ = "notification_channels"

    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    logs: Mapped[list[NotificationLog]] = relationship(
        "NotificationLog",
        back_populates="channel",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def activate(self) -> None:
        """Activate this channel."""
        self.is_active = True

    def deactivate(self) -> None:
        """Deactivate this channel."""
        self.is_active = False

    def get_config_summary(self) -> str:
        """Get a safe summary of channel configuration (hides sensitive data)."""
        if self.type == "slack":
            url = self.config.get("webhook_url", "")
            return f"Webhook: ...{url[-20:]}" if len(url) > 20 else f"Webhook: {url}"
        elif self.type == "email":
            recipients = self.config.get("recipients", [])
            preview = ", ".join(recipients[:2])
            suffix = "..." if len(recipients) > 2 else ""
            return f"Recipients: {preview}{suffix}"
        elif self.type == "webhook":
            url = self.config.get("url", "")
            return f"URL: {url[:50]}..." if len(url) > 50 else f"URL: {url}"
        return "Configured"


class NotificationRule(Base, UUIDMixin, TimestampMixin):
    """Notification trigger rules model.

    Defines when and how notifications should be triggered based on
    validation events and conditions.

    Attributes:
        id: Unique identifier (UUID).
        name: Human-readable rule name.
        condition: Trigger condition type.
        condition_config: Additional condition configuration.
        channel_ids: List of channel IDs to notify.
        source_ids: Optional list of source IDs to filter (null = all sources).
        is_active: Whether rule is active.

    Condition types:
        - validation_failed: Any validation failure
        - critical_issues: Validation has critical issues
        - high_issues: Validation has high severity issues
        - schedule_failed: Scheduled validation failed
        - drift_detected: Drift detected in comparison
    """

    __tablename__ = "notification_rules"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    condition: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    condition_config: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, default=dict
    )
    channel_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    source_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def activate(self) -> None:
        """Activate this rule."""
        self.is_active = True

    def deactivate(self) -> None:
        """Deactivate this rule."""
        self.is_active = False

    def matches_source(self, source_id: str) -> bool:
        """Check if this rule applies to a given source.

        Args:
            source_id: Source ID to check.

        Returns:
            True if rule applies to this source.
        """
        if self.source_ids is None:
            return True  # Applies to all sources
        return source_id in self.source_ids


class NotificationLog(Base, UUIDMixin):
    """Notification delivery log model.

    Records all notification delivery attempts for auditing and debugging.

    Attributes:
        id: Unique identifier (UUID).
        channel_id: Reference to NotificationChannel.
        rule_id: Optional reference to NotificationRule that triggered this.
        event_type: Type of event that triggered notification.
        event_data: JSON data about the triggering event.
        status: Delivery status (pending, sent, failed).
        error_message: Error message if delivery failed.
        sent_at: Timestamp when notification was sent.
    """

    __tablename__ = "notification_logs"

    # Composite index for efficient queries
    __table_args__ = (
        Index("idx_notification_logs_channel_created", "channel_id", "created_at"),
        Index("idx_notification_logs_status", "status"),
    )

    channel_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("notification_channels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("notification_rules.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    channel: Mapped[NotificationChannel] = relationship(
        "NotificationChannel", back_populates="logs"
    )
    rule: Mapped[NotificationRule | None] = relationship(
        "NotificationRule", backref="logs"
    )

    def mark_sent(self) -> None:
        """Mark notification as successfully sent."""
        self.status = "sent"
        self.sent_at = datetime.utcnow()

    def mark_failed(self, error: str) -> None:
        """Mark notification as failed with error message."""
        self.status = "failed"
        self.error_message = error
        self.sent_at = datetime.utcnow()


# =============================================================================
# Phase 5: Business Glossary Models
# =============================================================================


class GlossaryCategory(Base, UUIDMixin, TimestampMixin):
    """Business glossary category model.

    Provides hierarchical categorization for business terms.
    Categories can be nested (parent-child relationships).

    Attributes:
        id: Unique identifier (UUID).
        name: Category name (unique).
        description: Optional category description.
        parent_id: Optional parent category ID for hierarchy.
    """

    __tablename__ = "glossary_categories"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("glossary_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    parent: Mapped[GlossaryCategory | None] = relationship(
        "GlossaryCategory",
        remote_side="GlossaryCategory.id",
        back_populates="children",
    )
    children: Mapped[list[GlossaryCategory]] = relationship(
        "GlossaryCategory",
        back_populates="parent",
        lazy="selectin",
    )
    terms: Mapped[list[GlossaryTerm]] = relationship(
        "GlossaryTerm",
        back_populates="category",
        lazy="selectin",
    )

    @property
    def term_count(self) -> int:
        """Get number of terms in this category."""
        return len(self.terms)

    @property
    def full_path(self) -> str:
        """Get full category path (e.g., 'Parent > Child')."""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name


class GlossaryTerm(Base, UUIDMixin, TimestampMixin):
    """Business glossary term model.

    Represents a business term with its definition, status, and relationships.

    Attributes:
        id: Unique identifier (UUID).
        name: Term name (unique).
        definition: Term definition (required).
        category_id: Optional category ID.
        status: Term status (draft, approved, deprecated).
        owner_id: Optional owner identifier.
    """

    __tablename__ = "glossary_terms"

    # Composite index for efficient search queries
    __table_args__ = (
        Index("idx_glossary_terms_name_status", "name", "status"),
        Index("idx_glossary_terms_category", "category_id"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    category_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("glossary_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TermStatus.DRAFT.value,
        index=True,
    )
    owner_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    category: Mapped[GlossaryCategory | None] = relationship(
        "GlossaryCategory",
        back_populates="terms",
    )
    history: Mapped[list[TermHistory]] = relationship(
        "TermHistory",
        back_populates="term",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(TermHistory.changed_at)",
    )
    # Relationships where this term is the source
    outgoing_relationships: Mapped[list[TermRelationship]] = relationship(
        "TermRelationship",
        foreign_keys="TermRelationship.source_term_id",
        back_populates="source_term",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    # Relationships where this term is the target
    incoming_relationships: Mapped[list[TermRelationship]] = relationship(
        "TermRelationship",
        foreign_keys="TermRelationship.target_term_id",
        back_populates="target_term",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    # Columns mapped to this term
    mapped_columns: Mapped[list[AssetColumn]] = relationship(
        "AssetColumn",
        back_populates="term",
        lazy="selectin",
    )

    @property
    def synonyms(self) -> list[GlossaryTerm]:
        """Get all synonym terms."""
        result = []
        for rel in self.outgoing_relationships:
            if rel.relationship_type == RelationshipType.SYNONYM.value:
                result.append(rel.target_term)
        for rel in self.incoming_relationships:
            if rel.relationship_type == RelationshipType.SYNONYM.value:
                result.append(rel.source_term)
        return result

    @property
    def related_terms(self) -> list[GlossaryTerm]:
        """Get all related terms (non-synonym relationships)."""
        result = []
        for rel in self.outgoing_relationships:
            if rel.relationship_type == RelationshipType.RELATED.value:
                result.append(rel.target_term)
        for rel in self.incoming_relationships:
            if rel.relationship_type == RelationshipType.RELATED.value:
                result.append(rel.source_term)
        return result

    @property
    def is_approved(self) -> bool:
        """Check if term is approved."""
        return self.status == TermStatus.APPROVED.value

    @property
    def is_deprecated(self) -> bool:
        """Check if term is deprecated."""
        return self.status == TermStatus.DEPRECATED.value

    def approve(self) -> None:
        """Approve this term."""
        self.status = TermStatus.APPROVED.value

    def deprecate(self) -> None:
        """Mark this term as deprecated."""
        self.status = TermStatus.DEPRECATED.value


class TermRelationship(Base, UUIDMixin):
    """Relationship between glossary terms.

    Represents directional relationships between terms such as
    synonyms, related terms, or parent-child relationships.

    Attributes:
        id: Unique identifier (UUID).
        source_term_id: Source term ID.
        target_term_id: Target term ID.
        relationship_type: Type of relationship.
        created_at: When the relationship was created.
    """

    __tablename__ = "term_relationships"

    # Unique constraint to prevent duplicate relationships
    __table_args__ = (
        Index(
            "idx_term_relationships_unique",
            "source_term_id",
            "target_term_id",
            "relationship_type",
            unique=True,
        ),
    )

    source_term_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("glossary_terms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_term_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("glossary_terms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relationship_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    source_term: Mapped[GlossaryTerm] = relationship(
        "GlossaryTerm",
        foreign_keys=[source_term_id],
        back_populates="outgoing_relationships",
    )
    target_term: Mapped[GlossaryTerm] = relationship(
        "GlossaryTerm",
        foreign_keys=[target_term_id],
        back_populates="incoming_relationships",
    )


class TermHistory(Base, UUIDMixin):
    """History of changes to glossary terms.

    Tracks all modifications to term fields for auditing.

    Attributes:
        id: Unique identifier (UUID).
        term_id: Reference to the term.
        field_name: Name of the changed field.
        old_value: Previous value (as string).
        new_value: New value (as string).
        changed_by: User who made the change.
        changed_at: When the change occurred.
    """

    __tablename__ = "term_history"

    # Index for efficient history queries
    __table_args__ = (
        Index("idx_term_history_term_changed", "term_id", "changed_at"),
    )

    term_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("glossary_terms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    term: Mapped[GlossaryTerm] = relationship(
        "GlossaryTerm",
        back_populates="history",
    )


# =============================================================================
# Phase 5: Data Catalog Models
# =============================================================================


class CatalogAsset(Base, UUIDMixin, TimestampMixin):
    """Data catalog asset model.

    Represents a data asset (table, file, API) in the catalog.

    Attributes:
        id: Unique identifier (UUID).
        name: Asset name.
        asset_type: Type of asset (table, file, api).
        source_id: Optional reference to data source.
        description: Optional asset description.
        owner_id: Optional owner identifier.
        quality_score: Computed quality score (0-100).
    """

    __tablename__ = "catalog_assets"

    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_catalog_assets_type", "asset_type"),
        Index("idx_catalog_assets_source", "source_id"),
        Index("idx_catalog_assets_name_type", "name", "asset_type"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    asset_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AssetType.TABLE.value,
    )
    source_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    source: Mapped[Source | None] = relationship(
        "Source",
        back_populates="assets",
    )
    columns: Mapped[list[AssetColumn]] = relationship(
        "AssetColumn",
        back_populates="asset",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="AssetColumn.name",
    )
    tags: Mapped[list[AssetTag]] = relationship(
        "AssetTag",
        back_populates="asset",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def column_count(self) -> int:
        """Get number of columns."""
        return len(self.columns)

    @property
    def tag_names(self) -> list[str]:
        """Get list of tag names."""
        return [tag.tag_name for tag in self.tags]

    @property
    def quality_level(self) -> str:
        """Get quality level based on score."""
        if self.quality_score is None:
            return "unknown"
        if self.quality_score >= 90:
            return "excellent"
        if self.quality_score >= 70:
            return "good"
        if self.quality_score >= 50:
            return "fair"
        return "poor"

    def update_quality_score(self, score: float) -> None:
        """Update the quality score."""
        self.quality_score = min(100.0, max(0.0, score))


class AssetColumn(Base, UUIDMixin, TimestampMixin):
    """Asset column metadata model.

    Represents a column within a data asset with optional term mapping.

    Attributes:
        id: Unique identifier (UUID).
        asset_id: Reference to parent asset.
        name: Column name.
        data_type: Column data type.
        description: Optional column description.
        is_nullable: Whether column allows null values.
        is_primary_key: Whether column is a primary key.
        term_id: Optional mapped glossary term ID.
        sensitivity_level: Data sensitivity classification.
    """

    __tablename__ = "asset_columns"

    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_asset_columns_asset", "asset_id"),
        Index("idx_asset_columns_term", "term_id"),
        Index("idx_asset_columns_sensitivity", "sensitivity_level"),
    )

    asset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("catalog_assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    data_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_nullable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_primary_key: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    term_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("glossary_terms.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    sensitivity_level: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        default=SensitivityLevel.PUBLIC.value,
    )

    # Relationships
    asset: Mapped[CatalogAsset] = relationship(
        "CatalogAsset",
        back_populates="columns",
    )
    term: Mapped[GlossaryTerm | None] = relationship(
        "GlossaryTerm",
        back_populates="mapped_columns",
    )

    @property
    def is_sensitive(self) -> bool:
        """Check if column contains sensitive data."""
        if self.sensitivity_level is None:
            return False
        return self.sensitivity_level in (
            SensitivityLevel.CONFIDENTIAL.value,
            SensitivityLevel.RESTRICTED.value,
        )

    @property
    def has_term_mapping(self) -> bool:
        """Check if column is mapped to a term."""
        return self.term_id is not None

    def map_to_term(self, term_id: str) -> None:
        """Map this column to a glossary term."""
        self.term_id = term_id

    def unmap_term(self) -> None:
        """Remove term mapping from this column."""
        self.term_id = None


class AssetTag(Base, UUIDMixin):
    """Tag for catalog assets.

    Provides flexible tagging for assets with optional values.

    Attributes:
        id: Unique identifier (UUID).
        asset_id: Reference to parent asset.
        tag_name: Tag name/key.
        tag_value: Optional tag value.
        created_at: When the tag was created.
    """

    __tablename__ = "asset_tags"

    # Unique constraint to prevent duplicate tags
    __table_args__ = (
        Index("idx_asset_tags_asset", "asset_id"),
        Index("idx_asset_tags_name", "tag_name"),
        Index(
            "idx_asset_tags_unique",
            "asset_id",
            "tag_name",
            unique=True,
        ),
    )

    asset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("catalog_assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tag_name: Mapped[str] = mapped_column(String(100), nullable=False)
    tag_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    asset: Mapped[CatalogAsset] = relationship(
        "CatalogAsset",
        back_populates="tags",
    )


# =============================================================================
# Phase 5: Collaboration Models
# =============================================================================


class Comment(Base, UUIDMixin, TimestampMixin):
    """Comment on resources (terms, assets, columns).

    Supports threaded comments with replies.

    Attributes:
        id: Unique identifier (UUID).
        resource_type: Type of resource being commented on.
        resource_id: ID of the resource.
        content: Comment content.
        author_id: Optional author identifier.
        parent_id: Optional parent comment ID for replies.
    """

    __tablename__ = "comments"

    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_comments_resource", "resource_type", "resource_id"),
        Index("idx_comments_parent", "parent_id"),
    )

    resource_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    resource_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Relationships
    parent: Mapped[Comment | None] = relationship(
        "Comment",
        remote_side="Comment.id",
        back_populates="replies",
    )
    replies: Mapped[list[Comment]] = relationship(
        "Comment",
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Comment.created_at",
    )

    @property
    def is_reply(self) -> bool:
        """Check if this is a reply to another comment."""
        return self.parent_id is not None

    @property
    def reply_count(self) -> int:
        """Get number of direct replies."""
        return len(self.replies)


class Activity(Base, UUIDMixin):
    """Activity log for tracking changes.

    Records all significant actions on resources for audit trail.

    Attributes:
        id: Unique identifier (UUID).
        resource_type: Type of resource.
        resource_id: ID of the resource.
        action: Type of action performed.
        actor_id: User who performed the action.
        description: Human-readable description.
        metadata: Additional action metadata as JSON.
        created_at: When the activity occurred.
    """

    __tablename__ = "activities"

    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_activities_resource", "resource_type", "resource_id"),
        Index("idx_activities_action", "action"),
        Index("idx_activities_created", "created_at"),
    )

    resource_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    resource_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    actor_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    activity_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    @property
    def resource_key(self) -> str:
        """Get unique resource key."""
        return f"{self.resource_type}:{self.resource_id}"


# =============================================================================
# Schema Evolution Models
# =============================================================================


class SchemaVersion(Base, UUIDMixin, TimestampMixin):
    """Schema version snapshot for evolution tracking.

    Stores a snapshot of schema structure at a point in time
    to enable schema change detection and history tracking.

    Attributes:
        id: Unique identifier (UUID).
        source_id: Reference to parent Source.
        schema_id: Reference to the Schema record.
        version_number: Sequential version number for this source.
        schema_hash: SHA256 hash of normalized schema structure.
        column_snapshot: JSON snapshot of column definitions.
    """

    __tablename__ = "schema_versions"

    __table_args__ = (
        Index("idx_schema_versions_source", "source_id", "version_number"),
        Index("idx_schema_versions_hash", "schema_hash"),
    )

    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    schema_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("schemas.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    schema_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    column_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Relationships
    source: Mapped[Source] = relationship("Source", lazy="selectin")
    schema: Mapped[Schema] = relationship("Schema", lazy="selectin")

    @property
    def column_names(self) -> list[str]:
        """Get list of column names from snapshot."""
        return list(self.column_snapshot.keys())

    @property
    def column_count(self) -> int:
        """Get number of columns in this version."""
        return len(self.column_snapshot)


class SchemaChange(Base, UUIDMixin):
    """Individual schema change record.

    Records a single change detected between two schema versions.

    Attributes:
        id: Unique identifier (UUID).
        source_id: Reference to parent Source.
        from_version_id: Reference to previous SchemaVersion (null for first version).
        to_version_id: Reference to new SchemaVersion.
        change_type: Type of change (column_added, column_removed, type_changed).
        column_name: Name of the affected column.
        old_value: Previous value (for type changes).
        new_value: New value (for type changes or additions).
        severity: Severity of the change (breaking/non_breaking).
        created_at: When the change was detected.
    """

    __tablename__ = "schema_changes"

    __table_args__ = (
        Index("idx_schema_changes_source", "source_id", "created_at"),
        Index("idx_schema_changes_type", "change_type"),
    )

    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_version_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("schema_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    to_version_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("schema_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    change_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )
    column_name: Mapped[str] = mapped_column(String(255), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="non_breaking",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    source: Mapped[Source] = relationship("Source", lazy="selectin")
    from_version: Mapped[SchemaVersion | None] = relationship(
        "SchemaVersion",
        foreign_keys=[from_version_id],
        lazy="selectin",
    )
    to_version: Mapped[SchemaVersion] = relationship(
        "SchemaVersion",
        foreign_keys=[to_version_id],
        lazy="selectin",
    )

    @property
    def is_breaking(self) -> bool:
        """Check if this is a breaking change."""
        return self.severity == "breaking"

    @property
    def description(self) -> str:
        """Generate human-readable description of the change."""
        if self.change_type == "column_added":
            return f"Column '{self.column_name}' added with type {self.new_value}"
        elif self.change_type == "column_removed":
            return f"Column '{self.column_name}' removed (was {self.old_value})"
        elif self.change_type == "type_changed":
            return f"Column '{self.column_name}' type changed from {self.old_value} to {self.new_value}"
        return f"Unknown change on '{self.column_name}'"


# =============================================================================
# Phase 14: Advanced Notification Models
# =============================================================================


class DeduplicationStrategyEnum(str, Enum):
    """Deduplication window strategies."""

    SLIDING = "sliding"
    TUMBLING = "tumbling"
    SESSION = "session"
    ADAPTIVE = "adaptive"


class DeduplicationPolicyEnum(str, Enum):
    """Deduplication policies."""

    NONE = "none"
    BASIC = "basic"
    SEVERITY = "severity"
    ISSUE_BASED = "issue_based"
    STRICT = "strict"
    CUSTOM = "custom"


class EscalationStateEnum(str, Enum):
    """Escalation incident states."""

    PENDING = "pending"
    TRIGGERED = "triggered"
    ACKNOWLEDGED = "acknowledged"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


class TargetTypeEnum(str, Enum):
    """Escalation target types."""

    USER = "user"
    GROUP = "group"
    ONCALL = "oncall"
    CHANNEL = "channel"


class RoutingRuleModel(Base, UUIDMixin, TimestampMixin):
    """Advanced routing rule model.

    Stores rule-based routing configuration for directing
    notifications to appropriate channels based on conditions.

    Attributes:
        id: Unique identifier (UUID).
        name: Human-readable rule name.
        rule_config: JSON configuration defining the rule logic.
        actions: List of channel IDs to notify when rule matches.
        priority: Priority for rule evaluation (higher = evaluated first).
        is_active: Whether rule is active.
        stop_on_match: Stop processing after this rule matches.
        metadata: Additional metadata.
    """

    __tablename__ = "routing_rules"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    rule_config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    actions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    stop_on_match: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    routing_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )

    @property
    def rule_type(self) -> str:
        """Get the rule type from config."""
        return self.rule_config.get("type", "unknown")


class DeduplicationConfig(Base, UUIDMixin, TimestampMixin):
    """Deduplication configuration model.

    Stores configuration for notification deduplication
    to prevent duplicate notifications within time windows.

    Attributes:
        id: Unique identifier (UUID).
        name: Configuration name.
        strategy: Window strategy (sliding, tumbling, session, adaptive).
        policy: Deduplication policy (basic, severity, issue_based, etc.).
        window_seconds: Duration of deduplication window.
        is_active: Whether config is active.
    """

    __tablename__ = "deduplication_configs"

    __table_args__ = (
        Index("idx_dedup_config_is_active", "is_active"),
        Index("idx_dedup_config_strategy", "strategy"),
        Index("idx_dedup_config_policy", "policy"),
        Index("idx_dedup_config_created_at", "created_at"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    strategy: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DeduplicationStrategyEnum.SLIDING.value,
    )
    policy: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DeduplicationPolicyEnum.BASIC.value,
    )
    window_seconds: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ThrottlingConfig(Base, UUIDMixin, TimestampMixin):
    """Throttling configuration model.

    Stores rate limiting configuration for notifications
    to prevent overwhelming notification channels.

    Attributes:
        id: Unique identifier (UUID).
        name: Configuration name.
        per_minute: Max notifications per minute.
        per_hour: Max notifications per hour.
        per_day: Max notifications per day.
        burst_allowance: Factor to allow temporary bursts.
        channel_id: Optional channel ID for per-channel throttling.
        is_active: Whether config is active.
    """

    __tablename__ = "throttling_configs"

    __table_args__ = (
        Index("idx_throttle_config_is_active", "is_active"),
        Index("idx_throttle_config_created_at", "created_at"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    per_minute: Mapped[int | None] = mapped_column(Integer, nullable=True)
    per_hour: Mapped[int | None] = mapped_column(Integer, nullable=True)
    per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    burst_allowance: Mapped[float] = mapped_column(Float, default=1.5, nullable=False)
    channel_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("notification_channels.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    channel: Mapped[NotificationChannel | None] = relationship(
        "NotificationChannel",
        lazy="selectin",
    )


class EscalationPolicyModel(Base, UUIDMixin, TimestampMixin):
    """Escalation policy model.

    Stores multi-level escalation policy configuration
    for handling unacknowledged alerts.

    Attributes:
        id: Unique identifier (UUID).
        name: Policy name.
        description: Policy description.
        levels: JSON array of escalation levels.
        auto_resolve_on_success: Whether to auto-resolve on validation success.
        max_escalations: Maximum number of escalation attempts.
        is_active: Whether policy is active.
    """

    __tablename__ = "escalation_policies"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    levels: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    auto_resolve_on_success: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    max_escalations: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    incidents: Mapped[list[EscalationIncidentModel]] = relationship(
        "EscalationIncidentModel",
        back_populates="policy",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def level_count(self) -> int:
        """Get number of escalation levels."""
        return len(self.levels) if self.levels else 0


class EscalationIncidentModel(Base, UUIDMixin):
    """Escalation incident model.

    Tracks the lifecycle of an escalation from trigger to resolution.

    Attributes:
        id: Unique identifier (UUID).
        policy_id: Reference to escalation policy.
        incident_ref: External reference (e.g., validation ID).
        state: Current incident state.
        current_level: Current escalation level.
        escalation_count: Number of escalation attempts.
        context: JSON context data.
        acknowledged_by: Who acknowledged the incident.
        acknowledged_at: When acknowledged.
        resolved_by: Who resolved the incident.
        resolved_at: When resolved.
        events: JSON array of state transition events.
        next_escalation_at: When next escalation will occur.
    """

    __tablename__ = "escalation_incidents"

    __table_args__ = (
        Index("idx_escalation_incidents_policy", "policy_id"),
        Index("idx_escalation_incidents_ref", "incident_ref"),
        Index("idx_escalation_incidents_state", "state"),
        Index("idx_escalation_incidents_created_at", "created_at"),
        Index("idx_escalation_incidents_state_created", "state", "created_at"),
    )

    policy_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("escalation_policies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    incident_ref: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    state: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=EscalationStateEnum.PENDING.value,
        index=True,
    )
    current_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    escalation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    context: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    acknowledged_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    events: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    next_escalation_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    policy: Mapped[EscalationPolicyModel] = relationship(
        "EscalationPolicyModel",
        back_populates="incidents",
    )

    @property
    def is_active(self) -> bool:
        """Check if incident is active (not resolved)."""
        return self.state != EscalationStateEnum.RESOLVED.value

    @property
    def is_acknowledged(self) -> bool:
        """Check if incident has been acknowledged."""
        return self.state == EscalationStateEnum.ACKNOWLEDGED.value

    @property
    def is_resolved(self) -> bool:
        """Check if incident is resolved."""
        return self.state == EscalationStateEnum.RESOLVED.value

    def can_escalate(self, max_escalations: int) -> bool:
        """Check if incident can be escalated further.

        Args:
            max_escalations: Maximum allowed escalations from policy.

        Returns:
            True if escalation is allowed, False otherwise.
        """
        # Cannot escalate resolved or acknowledged incidents
        if self.state in (
            EscalationStateEnum.RESOLVED.value,
            EscalationStateEnum.ACKNOWLEDGED.value,
        ):
            return False

        # Check escalation count limit
        if self.escalation_count >= max_escalations:
            return False

        return True

    def escalate(
        self,
        next_level: int,
        next_escalation_at: datetime | None,
        max_escalations: int,
    ) -> bool:
        """Attempt to escalate the incident.

        Thread-safe escalation with validation. Returns False if
        escalation is not allowed.

        Args:
            next_level: The new escalation level.
            next_escalation_at: When the next escalation should occur.
            max_escalations: Maximum allowed escalations.

        Returns:
            True if escalation succeeded, False if not allowed.
        """
        if not self.can_escalate(max_escalations):
            return False

        old_state = self.state
        self.state = EscalationStateEnum.ESCALATED.value
        self.current_level = next_level
        self.escalation_count += 1
        self.next_escalation_at = next_escalation_at
        self.updated_at = datetime.utcnow()

        self.add_event(
            from_state=old_state,
            to_state=EscalationStateEnum.ESCALATED.value,
            actor="system",
            message=f"Escalated to level {next_level}",
        )

        return True

    def add_event(
        self,
        from_state: str | None,
        to_state: str,
        actor: str | None = None,
        message: str = "",
    ) -> None:
        """Add a state transition event."""
        event = {
            "from_state": from_state,
            "to_state": to_state,
            "actor": actor,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if self.events is None:
            self.events = []
        self.events.append(event)


# =============================================================================
# Scheduler Job Model (Persistent Job Storage)
# =============================================================================


class SchedulerJobState(str, Enum):
    """State of a scheduled job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    MISFIRED = "misfired"
    PAUSED = "paused"


class SchedulerJob(Base, UUIDMixin):
    """Persistent scheduler job model.

    Stores scheduled jobs for APScheduler with SQLAlchemy backend,
    enabling job persistence across restarts.

    Features:
        - Survives process restarts
        - Supports exponential backoff retries
        - Tracks execution history
        - Enables job recovery on startup

    Attributes:
        id: Unique job identifier (UUID).
        name: Human-readable job name.
        func_ref: Reference to the function to execute (module:function).
        trigger_type: Type of trigger (interval, cron, date).
        trigger_args: Arguments for the trigger configuration.
        args: Positional arguments for the function.
        kwargs: Keyword arguments for the function.
        next_run_time: Next scheduled execution time.
        state: Current job state.
        retry_count: Number of retry attempts.
        last_run_time: Last execution time.
        last_error: Last error message.
        job_metadata: Additional job metadata.
        created_at: When the job was created.
        updated_at: Last update timestamp.
    """

    __tablename__ = "scheduler_jobs"

    __table_args__ = (
        Index("idx_scheduler_jobs_state", "state"),
        Index("idx_scheduler_jobs_next_run", "next_run_time"),
        Index("idx_scheduler_jobs_state_next_run", "state", "next_run_time"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    func_ref: Mapped[str] = mapped_column(String(512), nullable=False)
    trigger_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="interval",
    )
    trigger_args: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    args: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    kwargs: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    next_run_time: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
    )
    state: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=SchedulerJobState.PENDING.value,
        index=True,
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_run_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    job_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    @property
    def is_due(self) -> bool:
        """Check if job is due for execution."""
        if not self.next_run_time:
            return False
        return (
            self.state in (SchedulerJobState.PENDING.value, SchedulerJobState.MISFIRED.value)
            and datetime.utcnow() >= self.next_run_time
        )

    @property
    def is_running(self) -> bool:
        """Check if job is currently running."""
        return self.state == SchedulerJobState.RUNNING.value

    @property
    def is_completed(self) -> bool:
        """Check if job has completed successfully."""
        return self.state == SchedulerJobState.COMPLETED.value

    @property
    def is_failed(self) -> bool:
        """Check if job has failed permanently."""
        return self.state == SchedulerJobState.FAILED.value

    def mark_running(self) -> None:
        """Mark job as running."""
        self.state = SchedulerJobState.RUNNING.value
        self.last_run_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_completed(self, next_run_time: datetime | None = None) -> None:
        """Mark job as completed.

        Args:
            next_run_time: Next scheduled run time (for recurring jobs).
        """
        if next_run_time:
            self.state = SchedulerJobState.PENDING.value
            self.next_run_time = next_run_time
        else:
            self.state = SchedulerJobState.COMPLETED.value
        self.retry_count = 0
        self.last_error = None
        self.updated_at = datetime.utcnow()

    def mark_failed(self, error: str, can_retry: bool = True) -> None:
        """Mark job as failed.

        Args:
            error: Error message.
            can_retry: Whether job can be retried.
        """
        self.last_error = error
        self.updated_at = datetime.utcnow()

        if can_retry:
            self.state = SchedulerJobState.PENDING.value
            self.retry_count += 1
        else:
            self.state = SchedulerJobState.FAILED.value

    def mark_misfired(self) -> None:
        """Mark job as misfired."""
        self.state = SchedulerJobState.MISFIRED.value
        self.updated_at = datetime.utcnow()
        if self.job_metadata is None:
            self.job_metadata = {}
        self.job_metadata["misfire_count"] = self.job_metadata.get("misfire_count", 0) + 1
        self.job_metadata["last_misfire_at"] = datetime.utcnow().isoformat()


# =============================================================================
# Phase 10: Data Lineage Models
# =============================================================================


class LineageNodeType(str, Enum):
    """Type of lineage node."""

    SOURCE = "source"
    TRANSFORM = "transform"
    SINK = "sink"


class LineageEdgeType(str, Enum):
    """Type of lineage edge."""

    DERIVES_FROM = "derives_from"
    TRANSFORMS_TO = "transforms_to"
    JOINS_WITH = "joins_with"
    FILTERS_FROM = "filters_from"


class LineageNode(Base, UUIDMixin, TimestampMixin):
    """Data lineage node model.

    Represents a node in the data lineage graph (source, transformation, or sink).

    Attributes:
        id: Unique identifier (UUID).
        name: Human-readable node name.
        node_type: Type of node (source, transform, sink).
        source_id: Optional reference to a data source.
        metadata_json: Additional metadata for the node.
        position_x: X coordinate for graph visualization.
        position_y: Y coordinate for graph visualization.
    """

    __tablename__ = "lineage_nodes"

    __table_args__ = (
        Index("idx_lineage_nodes_type", "node_type"),
        Index("idx_lineage_nodes_source", "source_id"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    node_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=LineageNodeType.SOURCE.value,
        index=True,
    )
    source_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    position_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    position_y: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    source: Mapped[Source | None] = relationship(
        "Source",
        lazy="selectin",
    )
    outgoing_edges: Mapped[list[LineageEdge]] = relationship(
        "LineageEdge",
        foreign_keys="LineageEdge.source_node_id",
        back_populates="source_node",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    incoming_edges: Mapped[list[LineageEdge]] = relationship(
        "LineageEdge",
        foreign_keys="LineageEdge.target_node_id",
        back_populates="target_node",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def upstream_count(self) -> int:
        """Get number of upstream (incoming) connections."""
        return len(self.incoming_edges)

    @property
    def downstream_count(self) -> int:
        """Get number of downstream (outgoing) connections."""
        return len(self.outgoing_edges)

    @property
    def is_source_type(self) -> bool:
        """Check if this is a source node."""
        return self.node_type == LineageNodeType.SOURCE.value

    @property
    def is_transform_type(self) -> bool:
        """Check if this is a transform node."""
        return self.node_type == LineageNodeType.TRANSFORM.value

    @property
    def is_sink_type(self) -> bool:
        """Check if this is a sink node."""
        return self.node_type == LineageNodeType.SINK.value


class LineageEdge(Base, UUIDMixin):
    """Data lineage edge model.

    Represents a connection (data flow) between two lineage nodes.

    Attributes:
        id: Unique identifier (UUID).
        source_node_id: ID of the source node (origin of data flow).
        target_node_id: ID of the target node (destination of data flow).
        edge_type: Type of relationship.
        metadata_json: Additional metadata for the edge.
        created_at: When the edge was created.
    """

    __tablename__ = "lineage_edges"

    __table_args__ = (
        Index("idx_lineage_edges_source", "source_node_id"),
        Index("idx_lineage_edges_target", "target_node_id"),
        Index(
            "idx_lineage_edges_unique",
            "source_node_id",
            "target_node_id",
            "edge_type",
            unique=True,
        ),
    )

    source_node_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("lineage_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_node_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("lineage_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    edge_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=LineageEdgeType.DERIVES_FROM.value,
        index=True,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    source_node: Mapped[LineageNode] = relationship(
        "LineageNode",
        foreign_keys=[source_node_id],
        back_populates="outgoing_edges",
    )
    target_node: Mapped[LineageNode] = relationship(
        "LineageNode",
        foreign_keys=[target_node_id],
        back_populates="incoming_edges",
    )


# =============================================================================
# OpenLineage Webhook Models
# =============================================================================


class OpenLineageEventType(str, Enum):
    """Types of OpenLineage events that can be emitted."""

    JOB = "job"
    DATASET = "dataset"
    ALL = "all"


class OpenLineageWebhook(Base, UUIDMixin, TimestampMixin):
    """OpenLineage webhook configuration model.

    Stores configuration for emitting OpenLineage events to external endpoints.

    Attributes:
        id: Unique identifier (UUID).
        name: Human-readable name for the webhook.
        url: Target URL for the webhook.
        is_active: Whether the webhook is enabled.
        headers_json: Custom headers as JSON (excluding auth).
        api_key: Optional API key for authentication.
        event_types: Types of events to emit (job, dataset, all).
        batch_size: Number of events per batch.
        timeout_seconds: Request timeout.
        last_sent_at: Timestamp of last successful emission.
        success_count: Total successful emissions.
        failure_count: Total failed emissions.
        last_error: Last error message if any.
    """

    __tablename__ = "openlineage_webhooks"

    __table_args__ = (
        Index("idx_openlineage_webhooks_active", "is_active"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    headers_json: Mapped[dict[str, str] | None] = mapped_column(JSON, nullable=True)
    api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_types: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=OpenLineageEventType.ALL.value,
    )
    batch_size: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=30)

    # Statistics
    last_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    @property
    def headers(self) -> dict[str, str]:
        """Get headers dictionary."""
        return self.headers_json or {}

    @property
    def total_emissions(self) -> int:
        """Get total emission attempts."""
        return self.success_count + self.failure_count

    @property
    def success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.total_emissions == 0:
            return 100.0
        return (self.success_count / self.total_emissions) * 100

    def record_success(self) -> None:
        """Record a successful emission."""
        self.success_count += 1
        self.last_sent_at = datetime.utcnow()
        self.last_error = None

    def record_failure(self, error: str) -> None:
        """Record a failed emission."""
        self.failure_count += 1
        self.last_error = error

    def activate(self) -> None:
        """Enable the webhook."""
        self.is_active = True

    def deactivate(self) -> None:
        """Disable the webhook."""
        self.is_active = False


# =============================================================================
# Phase 10: Anomaly Detection Models
# =============================================================================


class AnomalyAlgorithm(str, Enum):
    """Supported anomaly detection algorithms."""

    ISOLATION_FOREST = "isolation_forest"
    LOF = "lof"
    ONE_CLASS_SVM = "one_class_svm"
    DBSCAN = "dbscan"
    STATISTICAL = "statistical"
    AUTOENCODER = "autoencoder"


class AnomalyDetectionStatus(str, Enum):
    """Status of an anomaly detection run."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


class AnomalyDetection(Base, UUIDMixin):
    """Anomaly detection result model.

    Stores results from ML-based anomaly detection runs.

    Attributes:
        id: Unique identifier (UUID).
        source_id: Reference to parent Source.
        status: Current status (pending, running, success, error).
        algorithm: Detection algorithm used.
        config: Algorithm-specific configuration.
        total_rows: Total rows analyzed.
        anomaly_count: Number of anomalies found.
        anomaly_rate: Rate of anomalies (0-1).
        columns_analyzed: List of columns that were analyzed.
        result_json: Full detection result as JSON.
        duration_ms: Execution time in milliseconds.
        error_message: Error message if failed.
    """

    __tablename__ = "anomaly_detections"

    __table_args__ = (
        Index("idx_anomaly_detections_source_created", "source_id", "created_at"),
        Index("idx_anomaly_detections_status", "status"),
        Index("idx_anomaly_detections_algorithm", "algorithm"),
    )

    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AnomalyDetectionStatus.PENDING.value,
        index=True,
    )

    # Algorithm configuration
    algorithm: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=AnomalyAlgorithm.ISOLATION_FOREST.value,
        index=True,
    )
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Results summary
    total_rows: Mapped[int | None] = mapped_column(Integer, nullable=True)
    anomaly_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    anomaly_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    columns_analyzed: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # Full result and timing
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    source: Mapped[Source] = relationship(
        "Source",
        backref="anomaly_detections",
    )

    @property
    def is_complete(self) -> bool:
        """Check if detection has completed (success or error)."""
        return self.status in (
            AnomalyDetectionStatus.SUCCESS.value,
            AnomalyDetectionStatus.ERROR.value,
        )

    @property
    def anomalies(self) -> list[dict[str, Any]]:
        """Get list of anomaly records from result JSON."""
        if self.result_json and "anomalies" in self.result_json:
            return self.result_json["anomalies"]
        return []

    @property
    def column_summaries(self) -> list[dict[str, Any]]:
        """Get per-column anomaly summaries from result JSON."""
        if self.result_json and "column_summaries" in self.result_json:
            return self.result_json["column_summaries"]
        return []

    def mark_started(self) -> None:
        """Mark detection as started."""
        self.status = AnomalyDetectionStatus.RUNNING.value
        self.started_at = datetime.utcnow()

    def mark_completed(
        self,
        anomaly_count: int,
        anomaly_rate: float,
        result: dict[str, Any],
    ) -> None:
        """Mark detection as completed with results."""
        self.status = AnomalyDetectionStatus.SUCCESS.value
        self.anomaly_count = anomaly_count
        self.anomaly_rate = anomaly_rate
        self.result_json = result
        self.completed_at = datetime.utcnow()

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)

    def mark_error(self, message: str) -> None:
        """Mark detection as errored."""
        self.status = AnomalyDetectionStatus.ERROR.value
        self.error_message = message
        self.completed_at = datetime.utcnow()

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)


class AnomalyExplanation(Base, UUIDMixin):
    """SHAP/LIME explanations for anomaly detection results.

    Stores feature-level explanations for individual anomalous rows,
    providing interpretability for ML-based anomaly detection.

    Attributes:
        id: Unique identifier (UUID).
        detection_id: Reference to parent AnomalyDetection.
        row_index: Row index in the original dataset.
        anomaly_score: Anomaly score for this row.
        feature_contributions: JSON array of feature contributions.
        total_shap: Sum of all SHAP values.
        summary: Human-readable explanation summary.
        generated_at: When the explanation was generated.
    """

    __tablename__ = "anomaly_explanations"

    __table_args__ = (
        Index("idx_anomaly_explanations_detection", "detection_id"),
        Index("idx_anomaly_explanations_row", "detection_id", "row_index"),
    )

    detection_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("anomaly_detections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Row identification
    row_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Anomaly information
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False)

    # SHAP/LIME explanation data
    feature_contributions: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    total_shap: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Human-readable summary
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    # Timestamp
    generated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    detection: Mapped[AnomalyDetection] = relationship(
        "AnomalyDetection",
        backref="explanations",
    )

    @property
    def top_features(self) -> list[str]:
        """Get names of top contributing features."""
        if not self.feature_contributions:
            return []
        return [fc.get("feature", "") for fc in self.feature_contributions[:5]]

    @property
    def contribution_count(self) -> int:
        """Get number of feature contributions stored."""
        return len(self.feature_contributions) if self.feature_contributions else 0


class BatchDetectionStatus(str, Enum):
    """Status of a batch anomaly detection job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"  # Some sources completed with errors
    ERROR = "error"
    CANCELLED = "cancelled"


class AnomalyBatchJob(Base, UUIDMixin, TimestampMixin):
    """Batch anomaly detection job model.

    Stores configuration and results for batch anomaly detection
    across multiple data sources.

    Attributes:
        id: Unique identifier (UUID).
        name: Optional job name.
        status: Current status of the batch job.
        algorithm: Detection algorithm to use.
        config: Algorithm-specific configuration.
        source_ids: List of source IDs to process.
        total_sources: Total number of sources.
        completed_sources: Number of completed sources.
        failed_sources: Number of failed sources.
        total_anomalies: Total anomalies found across all sources.
        results_json: Detection results per source.
        error_message: Error message if job failed.
        duration_ms: Total execution time in milliseconds.
    """

    __tablename__ = "anomaly_batch_jobs"

    __table_args__ = (
        Index("idx_anomaly_batch_jobs_status", "status"),
        Index("idx_anomaly_batch_jobs_created", "created_at"),
    )

    name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=BatchDetectionStatus.PENDING.value,
        index=True,
    )

    # Algorithm configuration
    algorithm: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=AnomalyAlgorithm.ISOLATION_FOREST.value,
    )
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Sources to process
    source_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    # Progress tracking
    total_sources: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_sources: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_sources: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_source_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Aggregate results
    total_anomalies: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_rows_analyzed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Per-source results: {source_id: {detection_id, status, anomaly_count, anomaly_rate, ...}}
    results_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timing
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    @property
    def progress_percent(self) -> float:
        """Get progress as percentage."""
        if self.total_sources == 0:
            return 0.0
        return ((self.completed_sources + self.failed_sources) / self.total_sources) * 100

    @property
    def average_anomaly_rate(self) -> float:
        """Get average anomaly rate across all successful sources."""
        if not self.results_json:
            return 0.0
        rates = [
            r["anomaly_rate"]
            for r in self.results_json.values()
            if r.get("status") == "success" and r.get("anomaly_rate") is not None
        ]
        return sum(rates) / len(rates) if rates else 0.0

    @property
    def is_complete(self) -> bool:
        """Check if batch job has completed."""
        return self.status in (
            BatchDetectionStatus.COMPLETED.value,
            BatchDetectionStatus.PARTIAL.value,
            BatchDetectionStatus.ERROR.value,
            BatchDetectionStatus.CANCELLED.value,
        )

    def mark_started(self) -> None:
        """Mark batch job as started."""
        self.status = BatchDetectionStatus.RUNNING.value
        self.started_at = datetime.utcnow()

    def update_progress(
        self,
        source_id: str,
        detection_id: str,
        status: str,
        anomaly_count: int = 0,
        anomaly_rate: float = 0.0,
        total_rows: int = 0,
        error_message: str | None = None,
    ) -> None:
        """Update progress for a single source."""
        if self.results_json is None:
            self.results_json = {}

        self.results_json[source_id] = {
            "detection_id": detection_id,
            "status": status,
            "anomaly_count": anomaly_count,
            "anomaly_rate": anomaly_rate,
            "total_rows": total_rows,
            "error_message": error_message,
        }

        if status == "success":
            self.completed_sources += 1
            self.total_anomalies += anomaly_count
            self.total_rows_analyzed += total_rows
        elif status == "error":
            self.failed_sources += 1

    def mark_completed(self) -> None:
        """Mark batch job as completed."""
        if self.failed_sources > 0 and self.completed_sources > 0:
            self.status = BatchDetectionStatus.PARTIAL.value
        elif self.failed_sources == self.total_sources:
            self.status = BatchDetectionStatus.ERROR.value
        else:
            self.status = BatchDetectionStatus.COMPLETED.value

        self.completed_at = datetime.utcnow()
        self.current_source_id = None

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)

    def mark_error(self, message: str) -> None:
        """Mark batch job as errored."""
        self.status = BatchDetectionStatus.ERROR.value
        self.error_message = message
        self.completed_at = datetime.utcnow()
        self.current_source_id = None

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)

    def mark_cancelled(self) -> None:
        """Mark batch job as cancelled."""
        self.status = BatchDetectionStatus.CANCELLED.value
        self.completed_at = datetime.utcnow()
        self.current_source_id = None

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)


# =============================================================================
# Phase 10: Model Monitoring Models
# =============================================================================


class ModelStatus(str, Enum):
    """Status of a monitored model."""

    ACTIVE = "active"
    PAUSED = "paused"
    DEGRADED = "degraded"
    ERROR = "error"


class AlertSeverityLevel(str, Enum):
    """Alert severity levels for model monitoring."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class MetricTypeEnum(str, Enum):
    """Types of metrics collected."""

    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    NULL_RATE = "null_rate"
    TYPE_VIOLATION = "type_violation"
    DRIFT_SCORE = "drift_score"
    CUSTOM = "custom"


class AlertRuleTypeEnum(str, Enum):
    """Types of alert rules."""

    THRESHOLD = "threshold"
    STATISTICAL = "statistical"
    TREND = "trend"


class AlertHandlerTypeEnum(str, Enum):
    """Types of alert handlers."""

    SLACK = "slack"
    WEBHOOK = "webhook"
    EMAIL = "email"


class MonitoredModel(Base, UUIDMixin, TimestampMixin):
    """Monitored ML model registration model.

    Represents a registered ML model for monitoring performance,
    drift, and data quality metrics.

    Attributes:
        id: Unique identifier (UUID).
        name: Model name/identifier.
        version: Model version string.
        description: Model description.
        status: Monitoring status (active, paused, degraded, error).
        config: JSON configuration for monitoring settings.
        metadata_json: Additional model metadata.
        prediction_count: Total predictions recorded.
        last_prediction_at: Timestamp of last prediction.
        current_drift_score: Current drift score.
        health_score: Model health score (0-100).
    """

    __tablename__ = "monitored_models"

    __table_args__ = (
        Index("idx_monitored_models_name", "name"),
        Index("idx_monitored_models_status", "status"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0.0")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ModelStatus.ACTIVE.value,
        index=True,
    )
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )
    prediction_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_prediction_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    current_drift_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    health_score: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)

    # Relationships
    predictions: Mapped[list[ModelPrediction]] = relationship(
        "ModelPrediction",
        back_populates="model",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    metrics: Mapped[list[ModelMetric]] = relationship(
        "ModelMetric",
        back_populates="model",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    alert_rules: Mapped[list[ModelAlertRule]] = relationship(
        "ModelAlertRule",
        back_populates="model",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    alerts: Mapped[list[ModelAlert]] = relationship(
        "ModelAlert",
        back_populates="model",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def is_active(self) -> bool:
        """Check if model is actively monitored."""
        return self.status == ModelStatus.ACTIVE.value

    @property
    def is_healthy(self) -> bool:
        """Check if model is in healthy state."""
        return self.health_score >= 70.0

    @property
    def has_drift(self) -> bool:
        """Check if model has significant drift."""
        threshold = self.config.get("drift_threshold", 0.1)
        return (self.current_drift_score or 0.0) > threshold

    def record_prediction(self) -> None:
        """Record a new prediction."""
        self.prediction_count += 1
        self.last_prediction_at = datetime.utcnow()

    def update_drift_score(self, score: float) -> None:
        """Update the drift score."""
        self.current_drift_score = score
        # Update health score based on drift
        if score > 0.3:
            self.status = ModelStatus.DEGRADED.value
            self.health_score = max(0.0, 100.0 - score * 100)
        elif score > 0.1:
            self.health_score = max(50.0, 100.0 - score * 50)

    def pause(self) -> None:
        """Pause monitoring for this model."""
        self.status = ModelStatus.PAUSED.value

    def resume(self) -> None:
        """Resume monitoring for this model."""
        self.status = ModelStatus.ACTIVE.value


class ModelPrediction(Base, UUIDMixin):
    """Model prediction record for monitoring.

    Stores individual predictions made by a model for tracking
    performance and drift over time.

    Attributes:
        id: Unique identifier (UUID).
        model_id: Reference to MonitoredModel.
        features: JSON of input features.
        prediction: The model's output prediction.
        actual: The actual value (if available).
        latency_ms: Prediction latency in milliseconds.
        metadata_json: Additional prediction metadata.
        recorded_at: When the prediction was recorded.
    """

    __tablename__ = "model_predictions"

    __table_args__ = (
        Index("idx_model_predictions_model", "model_id", "recorded_at"),
        Index("idx_model_predictions_time", "recorded_at"),
    )

    model_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("monitored_models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    features: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    prediction: Mapped[Any] = mapped_column(JSON, nullable=False)
    actual: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    model: Mapped[MonitoredModel] = relationship(
        "MonitoredModel",
        back_populates="predictions",
    )

    @property
    def has_actual(self) -> bool:
        """Check if actual value is available."""
        return self.actual is not None


class ModelMetric(Base, UUIDMixin):
    """Model performance metric record.

    Stores aggregated metric values for a monitored model.

    Attributes:
        id: Unique identifier (UUID).
        model_id: Reference to MonitoredModel.
        metric_type: Type of metric (latency, throughput, etc.).
        metric_name: Name of the metric.
        value: Metric value.
        labels: JSON labels for the metric.
        recorded_at: When the metric was recorded.
    """

    __tablename__ = "model_metrics"

    __table_args__ = (
        Index("idx_model_metrics_model", "model_id", "recorded_at"),
        Index("idx_model_metrics_type", "metric_type"),
        Index("idx_model_metrics_name", "metric_name"),
    )

    model_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("monitored_models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metric_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    labels: Mapped[dict[str, str] | None] = mapped_column(JSON, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    model: Mapped[MonitoredModel] = relationship(
        "MonitoredModel",
        back_populates="metrics",
    )


class ModelAlertRule(Base, UUIDMixin, TimestampMixin):
    """Alert rule for model monitoring.

    Defines conditions that trigger alerts for a monitored model.

    Attributes:
        id: Unique identifier (UUID).
        model_id: Reference to MonitoredModel.
        name: Rule name.
        rule_type: Type of rule (threshold, statistical, trend).
        severity: Alert severity level.
        config: Rule-specific configuration.
        is_active: Whether rule is active.
        last_triggered_at: When last triggered.
        trigger_count: Total trigger count.
    """

    __tablename__ = "model_alert_rules"

    __table_args__ = (
        Index("idx_model_alert_rules_model", "model_id"),
        Index("idx_model_alert_rules_type", "rule_type"),
    )

    model_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("monitored_models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    rule_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AlertSeverityLevel.WARNING.value,
    )
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    trigger_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    model: Mapped[MonitoredModel] = relationship(
        "MonitoredModel",
        back_populates="alert_rules",
    )
    alerts: Mapped[list[ModelAlert]] = relationship(
        "ModelAlert",
        back_populates="rule",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def trigger(self) -> None:
        """Record a trigger of this rule."""
        self.last_triggered_at = datetime.utcnow()
        self.trigger_count += 1

    def activate(self) -> None:
        """Activate this rule."""
        self.is_active = True

    def deactivate(self) -> None:
        """Deactivate this rule."""
        self.is_active = False


class ModelAlertHandler(Base, UUIDMixin, TimestampMixin):
    """Alert handler for model monitoring.

    Defines where and how alerts are sent.

    Attributes:
        id: Unique identifier (UUID).
        name: Handler name.
        handler_type: Type of handler (slack, webhook, email).
        config: Handler-specific configuration.
        is_active: Whether handler is active.
        last_sent_at: When last alert was sent.
        send_count: Total alerts sent.
        failure_count: Total send failures.
    """

    __tablename__ = "model_alert_handlers"

    __table_args__ = (Index("idx_model_alert_handlers_type", "handler_type"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    handler_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    send_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def record_send(self, success: bool = True) -> None:
        """Record a send attempt."""
        self.last_sent_at = datetime.utcnow()
        if success:
            self.send_count += 1
        else:
            self.failure_count += 1

    def activate(self) -> None:
        """Activate this handler."""
        self.is_active = True

    def deactivate(self) -> None:
        """Deactivate this handler."""
        self.is_active = False


class ModelAlert(Base, UUIDMixin):
    """Alert instance for model monitoring.

    Represents a triggered alert from an alert rule.

    Attributes:
        id: Unique identifier (UUID).
        model_id: Reference to MonitoredModel.
        rule_id: Reference to ModelAlertRule.
        severity: Alert severity.
        message: Alert message.
        metric_value: Value that triggered the alert.
        threshold_value: Threshold that was exceeded.
        acknowledged: Whether alert is acknowledged.
        acknowledged_by: Who acknowledged.
        acknowledged_at: When acknowledged.
        resolved: Whether alert is resolved.
        resolved_at: When resolved.
        created_at: When alert was created.
    """

    __tablename__ = "model_alerts"

    __table_args__ = (
        Index("idx_model_alerts_model", "model_id", "created_at"),
        Index("idx_model_alerts_rule", "rule_id"),
        Index("idx_model_alerts_resolved", "resolved"),
    )

    model_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("monitored_models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("model_alert_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AlertSeverityLevel.WARNING.value,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    metric_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    threshold_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    acknowledged_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    model: Mapped[MonitoredModel] = relationship(
        "MonitoredModel",
        back_populates="alerts",
    )
    rule: Mapped[ModelAlertRule] = relationship(
        "ModelAlertRule",
        back_populates="alerts",
    )

    @property
    def is_active(self) -> bool:
        """Check if alert is active (not resolved)."""
        return not self.resolved

    def acknowledge(self, by: str) -> None:
        """Acknowledge this alert."""
        self.acknowledged = True
        self.acknowledged_by = by
        self.acknowledged_at = datetime.utcnow()

    def resolve(self) -> None:
        """Resolve this alert."""
        self.resolved = True
        self.resolved_at = datetime.utcnow()


# =============================================================================
# Phase 10: Drift Monitor Models
# =============================================================================


class DriftMonitorStatus(str, Enum):
    """Status of a drift monitor."""

    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"


class DriftAlertStatus(str, Enum):
    """Status of a drift alert."""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class DriftMonitor(Base, UUIDMixin, TimestampMixin):
    """Drift monitoring configuration model.

    Defines a drift monitor that compares baseline and current data sources.

    Attributes:
        id: Unique identifier (UUID).
        name: Monitor name.
        baseline_source_id: Reference to baseline Source.
        current_source_id: Reference to current Source.
        status: Monitor status.
        method: Drift detection method.
        threshold_critical: Critical drift threshold.
        threshold_high: High drift threshold.
        columns: Columns to monitor (None = all).
        schedule_cron: Optional cron expression for scheduling.
        last_run_at: Last run timestamp.
        next_run_at: Next scheduled run.
        config: Additional configuration.
    """

    __tablename__ = "drift_monitors"

    __table_args__ = (
        Index("idx_drift_monitors_status", "status"),
        Index("idx_drift_monitors_baseline", "baseline_source_id"),
        Index("idx_drift_monitors_current", "current_source_id"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    baseline_source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    current_source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DriftMonitorStatus.ACTIVE.value,
        index=True,
    )
    method: Mapped[str] = mapped_column(String(30), nullable=False, default="auto")
    threshold_critical: Mapped[float] = mapped_column(Float, default=0.3, nullable=False)
    threshold_high: Mapped[float] = mapped_column(Float, default=0.1, nullable=False)
    columns: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    schedule_cron: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    baseline_source: Mapped[Source] = relationship(
        "Source",
        foreign_keys=[baseline_source_id],
        lazy="selectin",
    )
    current_source: Mapped[Source] = relationship(
        "Source",
        foreign_keys=[current_source_id],
        lazy="selectin",
    )
    runs: Mapped[list[DriftMonitorRun]] = relationship(
        "DriftMonitorRun",
        back_populates="monitor",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(DriftMonitorRun.created_at)",
    )
    alerts: Mapped[list[DriftAlert]] = relationship(
        "DriftAlert",
        back_populates="monitor",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def is_active(self) -> bool:
        """Check if monitor is active."""
        return self.status == DriftMonitorStatus.ACTIVE.value

    @property
    def latest_run(self) -> DriftMonitorRun | None:
        """Get the most recent run."""
        return self.runs[0] if self.runs else None

    def pause(self) -> None:
        """Pause this monitor."""
        self.status = DriftMonitorStatus.PAUSED.value

    def resume(self) -> None:
        """Resume this monitor."""
        self.status = DriftMonitorStatus.ACTIVE.value

    def mark_run(self, next_run: datetime | None = None) -> None:
        """Mark as run and update next run time."""
        self.last_run_at = datetime.utcnow()
        self.next_run_at = next_run


class DriftMonitorRun(Base, UUIDMixin):
    """Drift monitor execution record.

    Stores results from a drift monitor run.

    Attributes:
        id: Unique identifier (UUID).
        monitor_id: Reference to DriftMonitor.
        status: Run status.
        has_drift: Whether drift was detected.
        max_drift_score: Maximum drift score across columns.
        total_columns: Total columns compared.
        drifted_columns: Number of columns with drift.
        column_results: JSON of per-column results.
        root_cause_analysis: JSON of root cause analysis.
        duration_ms: Run duration in milliseconds.
        error_message: Error message if failed.
        created_at: When run started.
        completed_at: When run completed.
    """

    __tablename__ = "drift_monitor_runs"

    __table_args__ = (
        Index("idx_drift_monitor_runs_monitor", "monitor_id", "created_at"),
        Index("idx_drift_monitor_runs_status", "status"),
    )

    monitor_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("drift_monitors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )
    has_drift: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    max_drift_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_columns: Mapped[int | None] = mapped_column(Integer, nullable=True)
    drifted_columns: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_results: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    root_cause_analysis: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    monitor: Mapped[DriftMonitor] = relationship(
        "DriftMonitor",
        back_populates="runs",
    )

    @property
    def is_complete(self) -> bool:
        """Check if run has completed."""
        return self.status in ("success", "failed", "error")

    @property
    def drift_percentage(self) -> float:
        """Calculate percentage of columns with drift."""
        if self.total_columns and self.total_columns > 0:
            return (self.drifted_columns or 0) / self.total_columns * 100
        return 0.0

    def mark_started(self) -> None:
        """Mark run as started."""
        self.status = "running"
        self.started_at = datetime.utcnow()

    def mark_completed(
        self,
        has_drift: bool,
        max_drift_score: float,
        total_columns: int,
        drifted_columns: int,
        column_results: dict[str, Any],
        root_cause_analysis: dict[str, Any] | None = None,
    ) -> None:
        """Mark run as completed with results."""
        self.status = "success"
        self.has_drift = has_drift
        self.max_drift_score = max_drift_score
        self.total_columns = total_columns
        self.drifted_columns = drifted_columns
        self.column_results = column_results
        self.root_cause_analysis = root_cause_analysis
        self.completed_at = datetime.utcnow()

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)

    def mark_error(self, message: str) -> None:
        """Mark run as errored."""
        self.status = "error"
        self.error_message = message
        self.completed_at = datetime.utcnow()

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)


class DriftAlert(Base, UUIDMixin):
    """Drift alert model.

    Represents an alert triggered by drift detection.

    Attributes:
        id: Unique identifier (UUID).
        monitor_id: Reference to DriftMonitor.
        run_id: Reference to DriftMonitorRun.
        severity: Alert severity (critical, high, medium, low).
        status: Alert status.
        drift_score: Drift score that triggered alert.
        affected_columns: List of affected columns.
        message: Alert message.
        acknowledged_by: Who acknowledged.
        acknowledged_at: When acknowledged.
        resolved_at: When resolved.
        created_at: When alert was created.
    """

    __tablename__ = "drift_alerts"

    __table_args__ = (
        Index("idx_drift_alerts_monitor", "monitor_id", "created_at"),
        Index("idx_drift_alerts_status", "status"),
    )

    monitor_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("drift_monitors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    run_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("drift_monitor_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="high")
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DriftAlertStatus.ACTIVE.value,
        index=True,
    )
    drift_score: Mapped[float] = mapped_column(Float, nullable=False)
    affected_columns: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    acknowledged_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    monitor: Mapped[DriftMonitor] = relationship(
        "DriftMonitor",
        back_populates="alerts",
    )
    run: Mapped[DriftMonitorRun | None] = relationship(
        "DriftMonitorRun",
        lazy="selectin",
    )

    @property
    def is_active(self) -> bool:
        """Check if alert is active."""
        return self.status == DriftAlertStatus.ACTIVE.value

    def acknowledge(self, by: str) -> None:
        """Acknowledge this alert."""
        self.status = DriftAlertStatus.ACKNOWLEDGED.value
        self.acknowledged_by = by
        self.acknowledged_at = datetime.utcnow()

    def resolve(self) -> None:
        """Resolve this alert."""
        self.status = DriftAlertStatus.RESOLVED.value
        self.resolved_at = datetime.utcnow()


# =============================================================================
# Phase 9: Plugin System Models
# =============================================================================


class PluginType(str, Enum):
    """Type of plugin."""

    VALIDATOR = "validator"
    REPORTER = "reporter"
    CONNECTOR = "connector"
    TRANSFORMER = "transformer"


class PluginStatus(str, Enum):
    """Installation status of a plugin."""

    AVAILABLE = "available"
    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    UPDATE_AVAILABLE = "update_available"
    ERROR = "error"


class PluginSource(str, Enum):
    """Source of the plugin."""

    OFFICIAL = "official"
    COMMUNITY = "community"
    LOCAL = "local"
    PRIVATE = "private"


class SecurityLevel(str, Enum):
    """Security level of the plugin."""

    TRUSTED = "trusted"
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    SANDBOXED = "sandboxed"


class Plugin(Base, UUIDMixin, TimestampMixin):
    """Plugin model.

    Represents an installable plugin in the plugin marketplace.

    Attributes:
        id: Unique identifier (UUID).
        name: Plugin name (unique identifier).
        display_name: Human-readable display name.
        description: Plugin description.
        version: Current/installed version.
        latest_version: Latest available version.
        type: Plugin type (validator, reporter, connector, transformer).
        source: Plugin source (official, community, local, private).
        status: Installation status.
        security_level: Security verification level.
        author: Author information (JSON).
        license: License identifier.
        homepage: Plugin homepage URL.
        repository: Repository URL.
        keywords: Search keywords (JSON array).
        categories: Plugin categories (JSON array).
        dependencies: Plugin dependencies (JSON array).
        permissions: Required permissions (JSON array).
        python_version: Required Python version.
        dashboard_version: Required dashboard version.
        icon_url: Plugin icon URL.
        banner_url: Plugin banner URL.
        documentation_url: Documentation URL.
        changelog: Changelog markdown.
        readme: README markdown.
        package_url: URL to download plugin package.
        signature: Plugin signature info (JSON).
        sandbox_config: Sandbox configuration (JSON).
        is_enabled: Whether plugin is enabled.
        install_count: Total installation count.
        rating: Average rating (1-5).
        rating_count: Number of ratings.
        validators_count: Number of validators provided.
        reporters_count: Number of reporters provided.
        installed_at: When plugin was installed.
        last_updated: When plugin was last updated.
    """

    __tablename__ = "plugins"

    __table_args__ = (
        Index("idx_plugins_name", "name", unique=True),
        Index("idx_plugins_type", "type"),
        Index("idx_plugins_source", "source"),
        Index("idx_plugins_status", "status"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    latest_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    type: Mapped[str] = mapped_column(
        SQLEnum(PluginType, native_enum=False, length=20),
        nullable=False,
        index=True,
    )
    source: Mapped[str] = mapped_column(
        SQLEnum(PluginSource, native_enum=False, length=20),
        nullable=False,
        default=PluginSource.COMMUNITY.value,
    )
    status: Mapped[str] = mapped_column(
        SQLEnum(PluginStatus, native_enum=False, length=20),
        nullable=False,
        default=PluginStatus.AVAILABLE.value,
        index=True,
    )
    security_level: Mapped[str] = mapped_column(
        SQLEnum(SecurityLevel, native_enum=False, length=20),
        nullable=False,
        default=SecurityLevel.UNVERIFIED.value,
    )
    author: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    license: Mapped[str | None] = mapped_column(String(50), nullable=True)
    homepage: Mapped[str | None] = mapped_column(String(500), nullable=True)
    repository: Mapped[str | None] = mapped_column(String(500), nullable=True)
    keywords: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    categories: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    dependencies: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    permissions: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    python_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    dashboard_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    icon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    banner_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    documentation_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)
    readme: Mapped[str | None] = mapped_column(Text, nullable=True)
    package_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    signature: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    sandbox_config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    install_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    validators_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reporters_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    installed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_updated: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    custom_validators: Mapped[list["CustomValidator"]] = relationship(
        "CustomValidator",
        back_populates="plugin",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    custom_reporters: Mapped[list["CustomReporter"]] = relationship(
        "CustomReporter",
        back_populates="plugin",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    ratings: Mapped[list["PluginRating"]] = relationship(
        "PluginRating",
        back_populates="plugin",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    signatures: Mapped[list["PluginSignature"]] = relationship(
        "PluginSignature",
        back_populates="plugin",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    hot_reload_config: Mapped["HotReloadConfig | None"] = relationship(
        "HotReloadConfig",
        back_populates="plugin",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )
    hooks: Mapped[list["PluginHook"]] = relationship(
        "PluginHook",
        back_populates="plugin",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def install(self) -> None:
        """Mark plugin as installed."""
        self.status = PluginStatus.INSTALLED.value
        self.installed_at = datetime.utcnow()
        self.install_count += 1

    def enable(self) -> None:
        """Enable the plugin."""
        self.status = PluginStatus.ENABLED.value
        self.is_enabled = True

    def disable(self) -> None:
        """Disable the plugin."""
        self.status = PluginStatus.DISABLED.value
        self.is_enabled = False

    def uninstall(self) -> None:
        """Mark plugin as available (uninstalled)."""
        self.status = PluginStatus.AVAILABLE.value
        self.is_enabled = False
        self.installed_at = None

    def update_rating(self, new_rating: float) -> None:
        """Update average rating with a new rating."""
        if self.rating is None:
            self.rating = new_rating
        else:
            total = self.rating * self.rating_count + new_rating
            self.rating = total / (self.rating_count + 1)
        self.rating_count += 1


class CustomValidator(Base, UUIDMixin, TimestampMixin):
    """Custom validator model.

    Represents a user-defined validator that can be used for data validation.

    Attributes:
        id: Unique identifier (UUID).
        plugin_id: Optional reference to parent plugin.
        name: Validator name (unique).
        display_name: Human-readable display name.
        description: Validator description.
        category: Validator category.
        severity: Default severity (error, warning, info).
        tags: Search/filter tags (JSON array).
        parameters: Parameter definitions (JSON array).
        code: Python code implementing the validator.
        test_cases: Test cases for validation (JSON array).
        is_enabled: Whether validator is enabled.
        is_verified: Whether validator is security-verified.
        usage_count: Number of times validator has been used.
        last_used_at: When validator was last used.
    """

    __tablename__ = "custom_validators"

    __table_args__ = (
        Index("idx_custom_validators_name", "name", unique=True),
        Index("idx_custom_validators_plugin", "plugin_id"),
        Index("idx_custom_validators_category", "category"),
    )

    plugin_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("plugins.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="error")
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    parameters: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    test_cases: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    plugin: Mapped[Plugin | None] = relationship(
        "Plugin",
        back_populates="custom_validators",
    )

    def increment_usage(self) -> None:
        """Increment usage count and update last used timestamp."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()


class CustomReporter(Base, UUIDMixin, TimestampMixin):
    """Custom reporter model.

    Represents a user-defined reporter for generating custom reports.

    Attributes:
        id: Unique identifier (UUID).
        plugin_id: Optional reference to parent plugin.
        name: Reporter name (unique).
        display_name: Human-readable display name.
        description: Reporter description.
        output_formats: Supported output formats (JSON array).
        config_fields: Configuration field definitions (JSON array).
        template: Jinja2 template for HTML/text reports.
        code: Python code for custom report generation.
        preview_image_url: Preview image URL.
        is_enabled: Whether reporter is enabled.
        is_verified: Whether reporter is security-verified.
        usage_count: Number of times reporter has been used.
    """

    __tablename__ = "custom_reporters"

    __table_args__ = (
        Index("idx_custom_reporters_name", "name", unique=True),
        Index("idx_custom_reporters_plugin", "plugin_id"),
    )

    plugin_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("plugins.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    output_formats: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    config_fields: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    template: Mapped[str | None] = mapped_column(Text, nullable=True)
    code: Mapped[str | None] = mapped_column(Text, nullable=True)
    preview_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    plugin: Mapped[Plugin | None] = relationship(
        "Plugin",
        back_populates="custom_reporters",
    )

    def increment_usage(self) -> None:
        """Increment usage count."""
        self.usage_count += 1


class ReportFormatType(str, Enum):
    """Report output format types."""

    HTML = "html"
    PDF = "pdf"
    CSV = "csv"
    JSON = "json"
    MARKDOWN = "markdown"
    JUNIT = "junit"
    EXCEL = "excel"
    CUSTOM = "custom"


class ReportStatus(str, Enum):
    """Status of report generation."""

    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class GeneratedReport(Base, UUIDMixin, TimestampMixin):
    """Generated report history model.

    Stores metadata and content of generated reports for history tracking,
    caching, and audit purposes.

    Attributes:
        id: Unique identifier (UUID).
        validation_id: Reference to the validation run.
        source_id: Reference to the data source.
        reporter_id: Optional reference to custom reporter used.
        name: Human-readable report name.
        description: Optional description.
        format: Report output format (html, pdf, csv, etc.).
        theme: Theme used for HTML/PDF reports.
        locale: Language locale used.
        status: Generation status.
        file_path: Path to stored report file (if persisted).
        file_size: Size of the report file in bytes.
        content_hash: Hash of report content for deduplication.
        config: Configuration used for generation (JSON).
        metadata: Additional metadata (JSON).
        error_message: Error message if generation failed.
        generation_time_ms: Time taken to generate in milliseconds.
        expires_at: When the report expires and can be cleaned up.
        downloaded_count: Number of times the report was downloaded.
        last_downloaded_at: Last download timestamp.
    """

    __tablename__ = "generated_reports"

    __table_args__ = (
        Index("idx_generated_reports_validation", "validation_id"),
        Index("idx_generated_reports_source", "source_id"),
        Index("idx_generated_reports_reporter", "reporter_id"),
        Index("idx_generated_reports_status", "status"),
        Index("idx_generated_reports_format", "format"),
        Index("idx_generated_reports_created", "created_at"),
        Index("idx_generated_reports_expires", "expires_at"),
    )

    validation_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("validations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reporter_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("custom_reporters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    format: Mapped[str] = mapped_column(
        SQLEnum(ReportFormatType), nullable=False, default=ReportFormatType.HTML
    )
    theme: Mapped[str | None] = mapped_column(String(50), nullable=True)
    locale: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    status: Mapped[str] = mapped_column(
        SQLEnum(ReportStatus), nullable=False, default=ReportStatus.PENDING
    )
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    report_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    generation_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    downloaded_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_downloaded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    validation: Mapped["Validation | None"] = relationship(
        "Validation",
        back_populates="generated_reports",
    )
    source: Mapped["Source | None"] = relationship(
        "Source",
        back_populates="generated_reports",
    )
    reporter: Mapped[CustomReporter | None] = relationship(
        "CustomReporter",
        backref="generated_reports",
    )

    def increment_download(self) -> None:
        """Increment download count and update last download timestamp."""
        self.downloaded_count += 1
        self.last_downloaded_at = datetime.utcnow()

    def mark_completed(self, file_path: str, file_size: int, generation_time_ms: float) -> None:
        """Mark report as completed."""
        self.status = ReportStatus.COMPLETED
        self.file_path = file_path
        self.file_size = file_size
        self.generation_time_ms = generation_time_ms

    def mark_failed(self, error_message: str) -> None:
        """Mark report as failed."""
        self.status = ReportStatus.FAILED
        self.error_message = error_message

    def is_expired(self) -> bool:
        """Check if report has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


class PluginRating(Base, UUIDMixin, TimestampMixin):
    """Plugin rating model.

    Stores user ratings and reviews for plugins.

    Attributes:
        id: Unique identifier (UUID).
        plugin_id: Reference to Plugin.
        user_id: User identifier (could be from auth system).
        rating: Rating value (1-5).
        review: Optional review text.
    """

    __tablename__ = "plugin_ratings"

    __table_args__ = (
        Index("idx_plugin_ratings_plugin", "plugin_id"),
        Index("idx_plugin_ratings_user", "user_id"),
    )

    plugin_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("plugins.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    review: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    plugin: Mapped[Plugin] = relationship(
        "Plugin",
        back_populates="ratings",
    )


class PluginExecutionLog(Base, UUIDMixin):
    """Plugin execution log model.

    Tracks plugin executions for monitoring and debugging.

    Attributes:
        id: Unique identifier (UUID).
        plugin_id: Reference to Plugin.
        validator_id: Optional reference to CustomValidator.
        reporter_id: Optional reference to CustomReporter.
        execution_id: Unique execution identifier.
        source_id: Optional reference to data source.
        status: Execution status (pending, running, success, failed, error).
        execution_time_ms: Execution duration in milliseconds.
        memory_used_mb: Memory used in MB.
        result: Execution result (JSON).
        error_message: Error message if failed.
        logs: Execution logs (JSON array).
        started_at: When execution started.
        completed_at: When execution completed.
    """

    __tablename__ = "plugin_execution_logs"

    __table_args__ = (
        Index("idx_plugin_exec_logs_plugin", "plugin_id", "started_at"),
        Index("idx_plugin_exec_logs_status", "status"),
    )

    plugin_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("plugins.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    validator_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("custom_validators.id", ondelete="SET NULL"),
        nullable=True,
    )
    reporter_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("custom_reporters.id", ondelete="SET NULL"),
        nullable=True,
    )
    execution_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    memory_used_mb: Mapped[float | None] = mapped_column(Float, nullable=True)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    logs: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def mark_started(self) -> None:
        """Mark execution as started."""
        self.status = "running"
        self.started_at = datetime.utcnow()

    def mark_completed(
        self,
        result: dict[str, Any] | None = None,
        memory_used_mb: float | None = None,
    ) -> None:
        """Mark execution as completed."""
        self.status = "success"
        self.result = result
        self.memory_used_mb = memory_used_mb
        self.completed_at = datetime.utcnow()
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.execution_time_ms = int(delta.total_seconds() * 1000)

    def mark_failed(self, error_message: str) -> None:
        """Mark execution as failed."""
        self.status = "failed"
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.execution_time_ms = int(delta.total_seconds() * 1000)


# =============================================================================
# Phase 9: Trust Store and Security Models
# =============================================================================


class SignatureAlgorithmType(str, Enum):
    """Supported signature algorithms."""

    HMAC_SHA256 = "hmac_sha256"
    HMAC_SHA512 = "hmac_sha512"
    RSA_SHA256 = "rsa_sha256"
    ED25519 = "ed25519"


class TrustLevelType(str, Enum):
    """Trust levels for signers."""

    TRUSTED = "trusted"
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    REVOKED = "revoked"


class IsolationLevelType(str, Enum):
    """Sandbox isolation levels."""

    NONE = "none"
    PROCESS = "process"
    CONTAINER = "container"


class TrustedSigner(Base, UUIDMixin, TimestampMixin):
    """Trusted signer model for plugin signature verification.

    Represents a trusted entity that can sign plugins.

    Attributes:
        id: Unique identifier (UUID).
        signer_id: Unique signer identifier (e.g., email, domain).
        name: Display name of the signer.
        organization: Organization name.
        email: Contact email.
        public_key: PEM-encoded public key.
        algorithm: Signature algorithm used.
        fingerprint: Key fingerprint for quick identification.
        trust_level: Current trust level.
        plugins_signed: Count of plugins signed.
        expires_at: When the trust expires.
        revoked_at: When the signer was revoked.
        revocation_reason: Reason for revocation.
        metadata: Additional signer metadata (JSON).
    """

    __tablename__ = "trusted_signers"

    __table_args__ = (
        Index("idx_trusted_signers_signer_id", "signer_id", unique=True),
        Index("idx_trusted_signers_fingerprint", "fingerprint"),
        Index("idx_trusted_signers_trust_level", "trust_level"),
    )

    signer_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    public_key: Mapped[str] = mapped_column(Text, nullable=False)
    algorithm: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=SignatureAlgorithmType.ED25519.value,
    )
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    trust_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TrustLevelType.VERIFIED.value,
    )
    plugins_signed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revocation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    signer_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )

    def is_valid(self) -> bool:
        """Check if the signer is currently valid."""
        if self.trust_level == TrustLevelType.REVOKED.value:
            return False
        if self.revoked_at is not None:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

    def revoke(self, reason: str) -> None:
        """Revoke this signer."""
        self.trust_level = TrustLevelType.REVOKED.value
        self.revoked_at = datetime.utcnow()
        self.revocation_reason = reason

    def increment_signed_count(self) -> None:
        """Increment the plugins signed count."""
        self.plugins_signed += 1


class SecurityPolicy(Base, UUIDMixin, TimestampMixin):
    """Security policy model for plugin execution.

    Defines security policies for plugin sandbox execution.

    Attributes:
        id: Unique identifier (UUID).
        name: Policy name.
        description: Policy description.
        is_default: Whether this is the default policy.
        is_active: Whether the policy is active.
        isolation_level: Sandbox isolation level.
        memory_limit_mb: Maximum memory in MB.
        cpu_time_limit_sec: Maximum CPU time in seconds.
        wall_time_limit_sec: Maximum wall clock time in seconds.
        network_enabled: Whether network access is allowed.
        file_read_enabled: Whether file read is allowed.
        file_write_enabled: Whether file write is allowed.
        allowed_modules: List of allowed Python modules.
        blocked_modules: List of blocked Python modules.
        allowed_builtins: List of allowed Python builtins.
        require_signature: Whether plugin signature is required.
        min_trust_level: Minimum trust level required.
        max_processes: Maximum number of processes.
        container_image: Docker image for container isolation.
        extra_options: Additional sandbox options (JSON).
    """

    __tablename__ = "security_policies"

    __table_args__ = (
        Index("idx_security_policies_name", "name", unique=True),
        Index("idx_security_policies_default", "is_default"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    isolation_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=IsolationLevelType.PROCESS.value,
    )
    memory_limit_mb: Mapped[int] = mapped_column(Integer, nullable=False, default=256)
    cpu_time_limit_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    wall_time_limit_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    network_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    file_read_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    file_write_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    allowed_modules: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: [
            "math", "statistics", "decimal", "fractions",
            "random", "re", "json", "datetime",
            "collections", "itertools", "functools",
            "operator", "string", "typing", "dataclasses",
        ],
    )
    blocked_modules: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: [
            "os", "sys", "subprocess", "socket", "shutil",
            "importlib", "ctypes", "multiprocessing",
        ],
    )
    allowed_builtins: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: [
            "abs", "all", "any", "ascii", "bin", "bool", "chr",
            "dict", "divmod", "enumerate", "filter", "float",
            "format", "frozenset", "getattr", "hasattr", "hash",
            "hex", "int", "isinstance", "issubclass", "iter",
            "len", "list", "map", "max", "min", "next", "oct",
            "ord", "pow", "print", "range", "repr", "reversed",
            "round", "set", "slice", "sorted", "str", "sum",
            "tuple", "type", "zip",
        ],
    )
    require_signature: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    min_trust_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TrustLevelType.UNVERIFIED.value,
    )
    max_processes: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    container_image: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="python:3.11-slim",
    )
    extra_options: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    @classmethod
    def get_preset(cls, preset_name: str) -> "SecurityPolicy":
        """Create a security policy from a preset.

        Args:
            preset_name: Name of the preset (development, testing, standard, enterprise, strict).

        Returns:
            SecurityPolicy with preset configuration.
        """
        presets = {
            "development": {
                "isolation_level": IsolationLevelType.NONE.value,
                "network_enabled": True,
                "file_read_enabled": True,
                "file_write_enabled": True,
                "require_signature": False,
                "memory_limit_mb": 1024,
                "wall_time_limit_sec": 300,
            },
            "testing": {
                "isolation_level": IsolationLevelType.PROCESS.value,
                "network_enabled": True,
                "file_read_enabled": True,
                "file_write_enabled": False,
                "require_signature": False,
                "memory_limit_mb": 512,
                "wall_time_limit_sec": 120,
            },
            "standard": {
                "isolation_level": IsolationLevelType.PROCESS.value,
                "network_enabled": False,
                "file_read_enabled": True,
                "file_write_enabled": False,
                "require_signature": False,
                "min_trust_level": TrustLevelType.VERIFIED.value,
                "memory_limit_mb": 256,
                "wall_time_limit_sec": 60,
            },
            "enterprise": {
                "isolation_level": IsolationLevelType.PROCESS.value,
                "network_enabled": False,
                "file_read_enabled": True,
                "file_write_enabled": False,
                "require_signature": True,
                "min_trust_level": TrustLevelType.TRUSTED.value,
                "memory_limit_mb": 512,
                "wall_time_limit_sec": 120,
            },
            "strict": {
                "isolation_level": IsolationLevelType.CONTAINER.value,
                "network_enabled": False,
                "file_read_enabled": False,
                "file_write_enabled": False,
                "require_signature": True,
                "min_trust_level": TrustLevelType.TRUSTED.value,
                "memory_limit_mb": 128,
                "wall_time_limit_sec": 30,
            },
        }

        config = presets.get(preset_name, presets["standard"])
        return cls(
            name=preset_name,
            description=f"{preset_name.capitalize()} security policy preset",
            **config,
        )


class PluginSignature(Base, UUIDMixin, TimestampMixin):
    """Plugin signature model.

    Stores signature information for verified plugins.

    Attributes:
        id: Unique identifier (UUID).
        plugin_id: Reference to Plugin.
        signer_id: Reference to TrustedSigner.
        algorithm: Signature algorithm used.
        signature: Base64-encoded signature.
        signed_hash: Hash of the signed content.
        signed_at: When the signature was created.
        verified_at: When the signature was last verified.
        is_valid: Whether the signature is currently valid.
        metadata: Additional signature metadata.
    """

    __tablename__ = "plugin_signatures"

    __table_args__ = (
        Index("idx_plugin_signatures_plugin", "plugin_id"),
        Index("idx_plugin_signatures_signer", "signer_id"),
    )

    plugin_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("plugins.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    signer_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("trusted_signers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    algorithm: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=SignatureAlgorithmType.ED25519.value,
    )
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    signed_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    signed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    signature_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )

    # Relationships
    plugin: Mapped["Plugin"] = relationship("Plugin", back_populates="signatures")
    signer: Mapped["TrustedSigner"] = relationship("TrustedSigner")

    def mark_verified(self) -> None:
        """Mark the signature as verified."""
        self.verified_at = datetime.utcnow()
        self.is_valid = True

    def invalidate(self) -> None:
        """Invalidate the signature."""
        self.is_valid = False


class HotReloadConfig(Base, UUIDMixin, TimestampMixin):
    """Hot reload configuration model.

    Stores hot reload settings for plugins.

    Attributes:
        id: Unique identifier (UUID).
        plugin_id: Reference to Plugin.
        enabled: Whether hot reload is enabled.
        watch_paths: Paths to watch for changes (JSON array).
        debounce_ms: Debounce time in milliseconds.
        reload_strategy: Reload strategy (graceful, immediate, scheduled).
        max_reload_attempts: Maximum reload attempts before disabling.
        backup_on_reload: Whether to backup before reload.
        last_reload_at: When the last reload occurred.
        reload_count: Total reload count.
        last_error: Last error message.
    """

    __tablename__ = "hot_reload_configs"

    __table_args__ = (
        Index("idx_hot_reload_configs_plugin", "plugin_id", unique=True),
    )

    plugin_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("plugins.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    watch_paths: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    debounce_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=500)
    reload_strategy: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="graceful",
    )
    max_reload_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    backup_on_reload: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_reload_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reload_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    plugin: Mapped["Plugin"] = relationship("Plugin", back_populates="hot_reload_config")

    def record_reload(self, success: bool = True, error: str | None = None) -> None:
        """Record a reload attempt."""
        self.last_reload_at = datetime.utcnow()
        self.reload_count += 1
        if not success:
            self.last_error = error


class PluginHook(Base, UUIDMixin, TimestampMixin):
    """Plugin hook registration model.

    Stores registered hooks for plugins.

    Attributes:
        id: Unique identifier (UUID).
        plugin_id: Reference to Plugin.
        hook_type: Type of hook (pre_validation, post_validation, etc.).
        callback_name: Name of the callback function.
        priority: Hook priority (lower runs first).
        enabled: Whether the hook is enabled.
        last_triggered_at: When the hook was last triggered.
        trigger_count: Total trigger count.
        total_execution_ms: Total execution time in ms.
        last_error: Last error message.
    """

    __tablename__ = "plugin_hooks"

    __table_args__ = (
        Index("idx_plugin_hooks_plugin", "plugin_id"),
        Index("idx_plugin_hooks_type", "hook_type"),
        Index("idx_plugin_hooks_priority", "priority"),
    )

    plugin_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("plugins.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    hook_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    callback_name: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    trigger_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_execution_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    plugin: Mapped["Plugin"] = relationship("Plugin", back_populates="hooks")

    @property
    def average_execution_ms(self) -> float:
        """Calculate average execution time."""
        if self.trigger_count == 0:
            return 0
        return self.total_execution_ms / self.trigger_count

    def record_trigger(self, execution_ms: float, error: str | None = None) -> None:
        """Record a hook trigger."""
        self.last_triggered_at = datetime.utcnow()
        self.trigger_count += 1
        self.total_execution_ms += execution_ms
        if error:
            self.last_error = error
