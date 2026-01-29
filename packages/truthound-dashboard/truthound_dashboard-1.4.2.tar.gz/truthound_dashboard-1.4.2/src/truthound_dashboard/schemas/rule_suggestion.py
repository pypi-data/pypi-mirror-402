"""Rule suggestion Pydantic schemas.

This module defines schemas for automatic rule generation
from profile data, including suggestions and application.

Features:
    - Strictness levels (loose, medium, strict)
    - Preset templates (default, comprehensive, minimal, etc.)
    - Multiple export formats (yaml, json, python, toml)
    - Category-based filtering
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field

from .base import BaseSchema


# =============================================================================
# Enums for Rule Generation Options
# =============================================================================


class StrictnessLevel(str, Enum):
    """Strictness level for rule generation.

    Determines how permissive or strict generated rules will be.
    """

    LOOSE = "loose"  # Permissive thresholds, fewer rules
    MEDIUM = "medium"  # Balanced defaults (recommended)
    STRICT = "strict"  # Tight thresholds, comprehensive rules


class RulePreset(str, Enum):
    """Preset templates for rule generation.

    Pre-configured combinations of categories and settings.
    """

    DEFAULT = "default"  # General purpose
    STRICT = "strict"  # Production data
    LOOSE = "loose"  # Development/testing
    MINIMAL = "minimal"  # Essential rules only
    COMPREHENSIVE = "comprehensive"  # All available rules
    CI_CD = "ci_cd"  # Optimized for CI/CD pipelines
    SCHEMA_ONLY = "schema_only"  # Structure validation only
    FORMAT_ONLY = "format_only"  # Format/pattern rules only
    CROSS_COLUMN = "cross_column"  # Focus on cross-column relationships
    DATA_INTEGRITY = "data_integrity"  # Comprehensive data integrity


class RuleExportFormat(str, Enum):
    """Export format for generated rules."""

    YAML = "yaml"  # Human-readable (default)
    JSON = "json"  # Machine-readable
    PYTHON = "python"  # Executable Python code
    TOML = "toml"  # Config-friendly


class RuleCategory(str, Enum):
    """Categories of validation rules."""

    SCHEMA = "schema"  # Column existence, type constraints
    STATISTICS = "stats"  # Range, threshold rules
    PATTERN = "pattern"  # Regex, format rules
    COMPLETENESS = "completeness"  # Null ratio rules
    UNIQUENESS = "uniqueness"  # Primary key, unique constraints
    DISTRIBUTION = "distribution"  # Allowed values, cardinality
    RELATIONSHIP = "relationship"  # Cross-column relationships
    MULTI_COLUMN = "multi_column"  # Multi-column validations


class CrossColumnRuleType(str, Enum):
    """Types of cross-column validation rules."""

    # Composite Key Rules
    COMPOSITE_KEY = "composite_key"  # Multi-column uniqueness

    # Arithmetic Relationships
    COLUMN_SUM = "column_sum"  # columns sum to target
    COLUMN_PRODUCT = "column_product"  # columns multiply to target
    COLUMN_DIFFERENCE = "column_difference"  # a - b = expected
    COLUMN_RATIO = "column_ratio"  # a / b = expected
    COLUMN_PERCENTAGE = "column_percentage"  # percentage relationship

    # Comparison Relationships
    COLUMN_COMPARISON = "column_comparison"  # a > b, a < b, etc.
    COLUMN_CHAIN_COMPARISON = "column_chain_comparison"  # a < b < c

    # Dependency Relationships
    COLUMN_DEPENDENCY = "column_dependency"  # functional dependency
    COLUMN_IMPLICATION = "column_implication"  # if A then B
    COLUMN_COEXISTENCE = "column_coexistence"  # all null or all non-null
    COLUMN_MUTUAL_EXCLUSIVITY = "column_mutual_exclusivity"  # at most one non-null

    # Statistical Relationships
    COLUMN_CORRELATION = "column_correlation"  # correlation between columns

    # Referential Integrity
    REFERENTIAL_INTEGRITY = "referential_integrity"  # foreign key validation


# =============================================================================
# Suggested Rule Schemas
# =============================================================================


class SuggestedRule(BaseSchema):
    """A single suggested validation rule."""

    column: str = Field(..., description="Target column name (or primary column for multi-column rules)")
    validator_name: str = Field(..., description="Validator to apply")
    params: dict[str, Any] = Field(
        default_factory=dict, description="Validator parameters"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0)",
    )
    reason: str = Field(..., description="Why this rule is suggested")
    severity_suggestion: str = Field(
        default="medium",
        description="Suggested severity level",
    )
    category: RuleCategory | str = Field(
        default=RuleCategory.SCHEMA,
        description="Rule category",
    )
    # Cross-column rule fields
    is_cross_column: bool = Field(
        default=False,
        description="Whether this is a cross-column rule",
    )
    related_columns: list[str] = Field(
        default_factory=list,
        description="Additional columns involved in cross-column rules",
    )
    cross_column_type: CrossColumnRuleType | None = Field(
        default=None,
        description="Type of cross-column relationship (if applicable)",
    )


class CrossColumnRuleSuggestion(BaseSchema):
    """A suggested cross-column validation rule with detailed relationship info."""

    id: str = Field(default_factory=lambda: "", description="Unique suggestion ID")
    rule_type: CrossColumnRuleType = Field(..., description="Type of cross-column rule")
    columns: list[str] = Field(..., description="Columns involved in the relationship")
    validator_name: str = Field(..., description="Validator to apply")
    params: dict[str, Any] = Field(
        default_factory=dict, description="Validator parameters"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0)",
    )
    reason: str = Field(..., description="Why this rule is suggested")
    severity_suggestion: str = Field(
        default="medium",
        description="Suggested severity level (high, medium, low)",
    )
    evidence: dict[str, Any] = Field(
        default_factory=dict,
        description="Statistical evidence supporting the suggestion",
    )
    sample_violations: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Sample rows that would violate this rule",
    )


class RuleSuggestionRequest(BaseSchema):
    """Request to generate rule suggestions."""

    use_latest_profile: bool = Field(
        default=True,
        description="Use the latest profile for suggestions",
    )
    profile_id: str | None = Field(
        default=None,
        description="Specific profile ID to use (if not latest)",
    )
    min_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for suggestions",
    )

    # Advanced options
    strictness: StrictnessLevel = Field(
        default=StrictnessLevel.MEDIUM,
        description="Strictness level for generated rules",
    )
    preset: RulePreset | None = Field(
        default=None,
        description="Preset template to use (overrides category settings)",
    )
    include_categories: list[RuleCategory] | None = Field(
        default=None,
        description="Only include rules from these categories",
    )
    exclude_categories: list[RuleCategory] | None = Field(
        default=None,
        description="Exclude rules from these categories",
    )
    include_types: list[str] | None = Field(
        default=None,
        description="Only suggest rules for these validator types",
    )
    exclude_columns: list[str] | None = Field(
        default=None,
        description="Columns to exclude from suggestions",
    )

    # Cross-column rule options
    enable_cross_column: bool = Field(
        default=True,
        description="Enable cross-column rule suggestions",
    )
    include_cross_column_types: list[CrossColumnRuleType] | None = Field(
        default=None,
        description="Only include these cross-column rule types",
    )
    exclude_cross_column_types: list[CrossColumnRuleType] | None = Field(
        default=None,
        description="Exclude these cross-column rule types",
    )
    sample_data_rows: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="Number of sample data rows to analyze for cross-column rules",
    )


class RuleSuggestionResponse(BaseSchema):
    """Response containing suggested rules."""

    source_id: str = Field(..., description="Source ID")
    source_name: str = Field(..., description="Source name")
    profile_id: str = Field(..., description="Profile ID used for suggestions")
    suggestions: list[SuggestedRule] = Field(
        default_factory=list, description="List of single-column suggested rules"
    )
    cross_column_suggestions: list[CrossColumnRuleSuggestion] = Field(
        default_factory=list, description="List of cross-column suggested rules"
    )
    total_suggestions: int = Field(default=0, description="Total suggestions count (single + cross-column)")
    high_confidence_count: int = Field(
        default=0, description="Suggestions with confidence >= 0.8"
    )
    cross_column_count: int = Field(
        default=0, description="Number of cross-column suggestions"
    )
    generated_at: datetime = Field(..., description="When suggestions were generated")

    # Generation settings used
    strictness: StrictnessLevel = Field(
        default=StrictnessLevel.MEDIUM,
        description="Strictness level used for generation",
    )
    preset: RulePreset | None = Field(
        default=None,
        description="Preset template used (if any)",
    )
    categories_included: list[RuleCategory] = Field(
        default_factory=list,
        description="Rule categories included in suggestions",
    )

    # Category breakdown
    by_category: dict[str, int] = Field(
        default_factory=dict,
        description="Count of suggestions by category",
    )

    # Cross-column breakdown
    by_cross_column_type: dict[str, int] = Field(
        default_factory=dict,
        description="Count of cross-column suggestions by type",
    )


# =============================================================================
# Apply Rules Schemas
# =============================================================================


class ApplyRulesRequest(BaseSchema):
    """Request to apply selected rule suggestions."""

    suggestions: list[SuggestedRule] = Field(
        ..., description="Selected suggestions to apply"
    )
    create_new_rule: bool = Field(
        default=True,
        description="Create a new rule set (vs updating existing)",
    )
    rule_name: str | None = Field(
        default=None,
        description="Name for the new rule set",
    )
    rule_description: str | None = Field(
        default=None,
        description="Description for the new rule set",
    )


class ApplyRulesResponse(BaseSchema):
    """Response after applying rule suggestions."""

    source_id: str = Field(..., description="Source ID")
    rule_id: str = Field(..., description="Created/updated rule ID")
    rule_name: str = Field(..., description="Rule name")
    applied_count: int = Field(..., description="Number of rules applied")
    validators: list[str] = Field(
        default_factory=list, description="Applied validator names"
    )
    created_at: datetime = Field(..., description="When rule was created/updated")


# =============================================================================
# Suggestion Statistics
# =============================================================================


class SuggestionStats(BaseSchema):
    """Statistics about rule suggestions for a source."""

    source_id: str = Field(..., description="Source ID")
    last_suggestion_at: datetime | None = Field(
        default=None, description="Last suggestion generation time"
    )
    total_suggestions_generated: int = Field(
        default=0, description="Total suggestions ever generated"
    )
    total_suggestions_applied: int = Field(
        default=0, description="Total suggestions applied"
    )
    suggestion_types: dict[str, int] = Field(
        default_factory=dict,
        description="Count of suggestions by validator type",
    )


# =============================================================================
# Export Schemas
# =============================================================================


class ExportRulesRequest(BaseSchema):
    """Request to export generated rules in various formats."""

    suggestions: list[SuggestedRule] = Field(
        ..., description="Rules to export"
    )
    format: RuleExportFormat = Field(
        default=RuleExportFormat.YAML,
        description="Export format",
    )
    include_metadata: bool = Field(
        default=True,
        description="Include generation metadata in export",
    )
    rule_name: str = Field(
        default="auto_generated_rules",
        description="Name for the exported rule set",
    )
    description: str | None = Field(
        default=None,
        description="Description for the rule set",
    )


class ExportRulesResponse(BaseSchema):
    """Response containing exported rules content."""

    content: str = Field(..., description="Exported content in requested format")
    format: RuleExportFormat = Field(..., description="Export format used")
    filename: str = Field(..., description="Suggested filename")
    rule_count: int = Field(..., description="Number of rules exported")
    generated_at: datetime = Field(..., description="When export was generated")


# =============================================================================
# Preset Configuration
# =============================================================================


class PresetInfo(BaseSchema):
    """Information about a rule generation preset."""

    name: RulePreset = Field(..., description="Preset name")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="What this preset does")
    strictness: StrictnessLevel = Field(..., description="Default strictness")
    categories: list[RuleCategory] = Field(
        default_factory=list,
        description="Categories included in this preset",
    )
    recommended_for: str = Field(
        default="",
        description="Use case this preset is recommended for",
    )


class PresetsResponse(BaseSchema):
    """Response listing available presets."""

    presets: list[PresetInfo] = Field(
        default_factory=list, description="Available presets"
    )
    strictness_levels: list[str] = Field(
        default_factory=list, description="Available strictness levels"
    )
    categories: list[str] = Field(
        default_factory=list, description="Available categories"
    )
    export_formats: list[str] = Field(
        default_factory=list, description="Available export formats"
    )
