"""Source-related Pydantic schemas.

This module defines schemas for data source API operations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field, field_validator

from .base import BaseSchema, IDMixin, ListResponseWrapper, TimestampMixin

# Supported source types - must match SourceType enum in connections.py
SourceType = Literal[
    "file",
    "postgresql",
    "mysql",
    "sqlite",
    "snowflake",
    "bigquery",
    "redshift",
    "databricks",
    "oracle",
    "sqlserver",
    "spark",
]

# Source type categories for UI grouping
SourceCategory = Literal["file", "database", "warehouse", "bigdata"]

# Field types for dynamic form rendering
FieldType = Literal["text", "password", "number", "select", "boolean", "file_path", "textarea"]


class SourceBase(BaseSchema):
    """Base source schema with common fields."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable source name",
        examples=["Sales Data", "User Events"],
    )
    type: SourceType = Field(
        ...,
        description="Data source type",
        examples=["file", "postgresql"],
    )
    config: dict[str, Any] = Field(
        ...,
        description="Source-specific configuration",
        examples=[{"path": "/data/sales.csv"}],
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional source description",
    )


class SourceCreate(SourceBase):
    """Schema for creating a new source."""

    @field_validator("config")
    @classmethod
    def validate_config(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate configuration has required fields."""
        if not v:
            raise ValueError("Config cannot be empty")
        return v


class SourceUpdate(BaseSchema):
    """Schema for updating an existing source."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="New source name",
    )
    config: dict[str, Any] | None = Field(
        default=None,
        description="New source configuration",
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="New description",
    )
    is_active: bool | None = Field(
        default=None,
        description="Whether source is active",
    )


class SourceResponse(SourceBase, IDMixin, TimestampMixin):
    """Schema for source responses."""

    is_active: bool = Field(default=True, description="Whether source is active")
    last_validated_at: datetime | None = Field(
        default=None,
        description="Last validation timestamp",
    )

    # Computed properties from relationships
    has_schema: bool = Field(default=False, description="Whether schema exists")
    latest_validation_status: str | None = Field(
        default=None,
        description="Status of latest validation",
    )

    @classmethod
    def from_model(cls, source: Any) -> SourceResponse:
        """Create response from model with computed fields.

        Args:
            source: Source model instance.

        Returns:
            SourceResponse with computed fields.
        """
        return cls(
            id=source.id,
            name=source.name,
            type=source.type,
            config=source.config,
            description=source.description,
            is_active=source.is_active,
            created_at=source.created_at,
            updated_at=source.updated_at,
            last_validated_at=source.last_validated_at,
            has_schema=source.latest_schema is not None,
            latest_validation_status=(
                source.latest_validation.status if source.latest_validation else None
            ),
        )


class SourceListResponse(ListResponseWrapper[SourceResponse]):
    """Paginated source list response."""

    pass


class SourceSummary(BaseSchema):
    """Minimal source summary for lists."""

    id: str
    name: str
    type: SourceType
    is_active: bool
    last_validated_at: datetime | None = None


# =============================================================================
# Source Type Definition Schemas (for dynamic form rendering)
# =============================================================================


class FieldOption(BaseSchema):
    """Option for select/multi-select fields."""

    value: str
    label: str


class FieldDefinitionSchema(BaseSchema):
    """Definition of a configuration field for dynamic form rendering."""

    name: str = Field(..., description="Field identifier")
    label: str = Field(..., description="Display label")
    type: FieldType = Field(default="text", description="Input field type")
    required: bool = Field(default=False, description="Whether field is required")
    placeholder: str = Field(default="", description="Input placeholder text")
    description: str = Field(default="", description="Help text for the field")
    default: Any = Field(default=None, description="Default value")
    options: list[FieldOption] | None = Field(
        default=None,
        description="Options for select fields",
    )
    min_value: int | None = Field(default=None, description="Minimum value for numbers")
    max_value: int | None = Field(default=None, description="Maximum value for numbers")
    depends_on: str | None = Field(
        default=None,
        description="Field this depends on for conditional rendering",
    )
    depends_value: Any = Field(
        default=None,
        description="Value of depends_on field that enables this field",
    )


class SourceTypeDefinitionSchema(BaseSchema):
    """Complete definition of a source type for dynamic form rendering."""

    type: SourceType = Field(..., description="Source type identifier")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="Type description")
    icon: str = Field(..., description="Icon identifier for UI")
    category: SourceCategory = Field(..., description="Source category")
    fields: list[FieldDefinitionSchema] = Field(
        ...,
        description="Configuration fields",
    )
    required_fields: list[str] = Field(
        default_factory=list,
        description="List of required field names",
    )
    optional_fields: list[str] = Field(
        default_factory=list,
        description="List of optional field names",
    )
    docs_url: str = Field(default="", description="Documentation URL")


class SourceTypeCategorySchema(BaseSchema):
    """Category for grouping source types."""

    value: str = Field(..., description="Category identifier")
    label: str = Field(..., description="Display label")
    description: str = Field(default="", description="Category description")


class SourceTypesResponse(BaseSchema):
    """Response containing all source types and categories."""

    types: list[SourceTypeDefinitionSchema] = Field(
        ...,
        description="All available source types",
    )
    categories: list[SourceTypeCategorySchema] = Field(
        ...,
        description="Source type categories",
    )


class TestConnectionRequest(BaseSchema):
    """Request to test a source connection before creating."""

    type: SourceType = Field(..., description="Source type")
    config: dict[str, Any] = Field(..., description="Connection configuration")


class TestConnectionResponse(BaseSchema):
    """Response from connection test."""

    success: bool = Field(..., description="Whether connection was successful")
    message: str | None = Field(default=None, description="Success message")
    error: str | None = Field(default=None, description="Error message if failed")
