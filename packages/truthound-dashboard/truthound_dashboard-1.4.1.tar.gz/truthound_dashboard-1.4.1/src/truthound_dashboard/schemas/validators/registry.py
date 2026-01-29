"""Validator registry.

Central registry combining all validator categories with metadata and lookup functions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .base import ValidatorCategory, ValidatorDefinition

# Import all validator category modules
from .schema_validators import SCHEMA_VALIDATORS
from .completeness_validators import COMPLETENESS_VALIDATORS
from .uniqueness_validators import UNIQUENESS_VALIDATORS
from .distribution_validators import DISTRIBUTION_VALIDATORS
from .string_validators import STRING_VALIDATORS
from .datetime_validators import DATETIME_VALIDATORS
from .aggregate_validators import AGGREGATE_VALIDATORS
from .cross_table_validators import CROSS_TABLE_VALIDATORS
from .multi_column_validators import MULTI_COLUMN_VALIDATORS
from .query_validators import QUERY_VALIDATORS
from .table_validators import TABLE_VALIDATORS
from .geospatial_validators import GEOSPATIAL_VALIDATORS
from .drift_validators import DRIFT_VALIDATORS
from .anomaly_validators import ANOMALY_VALIDATORS
from .privacy_validators import PRIVACY_VALIDATORS


@dataclass
class CategoryInfo:
    """Metadata for a validator category."""

    value: str
    label: str
    description: str
    icon: str | None = None
    color: str | None = None
    requires_extra: str | None = None
    validator_count: int = 0


# Category metadata with UI information
CATEGORY_INFO: list[CategoryInfo] = [
    # Core validators (no extra dependencies)
    CategoryInfo(
        value="schema",
        label="Schema",
        description="Validate structure, columns, and data types",
        icon="layout",
        color="#3b82f6",  # blue
    ),
    CategoryInfo(
        value="completeness",
        label="Completeness",
        description="Check for null values and missing data",
        icon="check-circle",
        color="#22c55e",  # green
    ),
    CategoryInfo(
        value="uniqueness",
        label="Uniqueness",
        description="Detect duplicates and validate keys",
        icon="fingerprint",
        color="#8b5cf6",  # purple
    ),
    CategoryInfo(
        value="distribution",
        label="Distribution",
        description="Validate value ranges and distributions",
        icon="bar-chart",
        color="#f59e0b",  # amber
    ),
    # Format validators
    CategoryInfo(
        value="string",
        label="String",
        description="Pattern matching and format validation",
        icon="type",
        color="#06b6d4",  # cyan
    ),
    CategoryInfo(
        value="datetime",
        label="Datetime",
        description="Date/time format and range validation",
        icon="calendar",
        color="#ec4899",  # pink
    ),
    # Statistical validators
    CategoryInfo(
        value="aggregate",
        label="Aggregate",
        description="Statistical aggregate checks (mean, sum, etc.)",
        icon="calculator",
        color="#6366f1",  # indigo
    ),
    CategoryInfo(
        value="drift",
        label="Drift",
        description="Distribution change detection between datasets",
        icon="trending-up",
        color="#ef4444",  # red
        requires_extra="drift",
    ),
    CategoryInfo(
        value="anomaly",
        label="Anomaly",
        description="ML-based outlier and anomaly detection",
        icon="alert-triangle",
        color="#f97316",  # orange
        requires_extra="anomaly",
    ),
    # Relational validators
    CategoryInfo(
        value="cross_table",
        label="Cross-Table",
        description="Multi-table relationships and foreign keys",
        icon="link",
        color="#14b8a6",  # teal
    ),
    CategoryInfo(
        value="multi_column",
        label="Multi-Column",
        description="Column relationships and calculations",
        icon="columns",
        color="#84cc16",  # lime
    ),
    CategoryInfo(
        value="query",
        label="Query",
        description="Expression-based custom validation",
        icon="code",
        color="#a855f7",  # violet
    ),
    # Domain validators
    CategoryInfo(
        value="table",
        label="Table",
        description="Table metadata and structure validation",
        icon="table",
        color="#0ea5e9",  # sky
    ),
    CategoryInfo(
        value="geospatial",
        label="Geospatial",
        description="Geographic coordinate validation",
        icon="map-pin",
        color="#10b981",  # emerald
    ),
    CategoryInfo(
        value="privacy",
        label="Privacy",
        description="PII detection and compliance (GDPR, CCPA)",
        icon="shield",
        color="#dc2626",  # red-600
    ),
]


def _build_registry() -> list[ValidatorDefinition]:
    """Build the complete validator registry from all categories."""
    return [
        *SCHEMA_VALIDATORS,
        *COMPLETENESS_VALIDATORS,
        *UNIQUENESS_VALIDATORS,
        *DISTRIBUTION_VALIDATORS,
        *STRING_VALIDATORS,
        *DATETIME_VALIDATORS,
        *AGGREGATE_VALIDATORS,
        *CROSS_TABLE_VALIDATORS,
        *MULTI_COLUMN_VALIDATORS,
        *QUERY_VALIDATORS,
        *TABLE_VALIDATORS,
        *GEOSPATIAL_VALIDATORS,
        *DRIFT_VALIDATORS,
        *ANOMALY_VALIDATORS,
        *PRIVACY_VALIDATORS,
    ]


# Complete validator registry
VALIDATOR_REGISTRY: list[ValidatorDefinition] = _build_registry()


def _update_category_counts() -> None:
    """Update validator counts in category info."""
    category_counts: dict[str, int] = {}
    for validator in VALIDATOR_REGISTRY:
        cat = validator.category.value
        category_counts[cat] = category_counts.get(cat, 0) + 1

    for cat_info in CATEGORY_INFO:
        cat_info.validator_count = category_counts.get(cat_info.value, 0)


# Update counts on module load
_update_category_counts()


def get_validator_by_name(name: str) -> ValidatorDefinition | None:
    """Get a validator definition by name.

    Args:
        name: Validator name (case-insensitive).

    Returns:
        ValidatorDefinition if found, None otherwise.
    """
    name_lower = name.lower()
    for validator in VALIDATOR_REGISTRY:
        if validator.name.lower() == name_lower:
            return validator
    return None


def get_validators_by_category(
    category: ValidatorCategory | str,
) -> list[ValidatorDefinition]:
    """Get all validators in a category.

    Args:
        category: Validator category (enum or string value).

    Returns:
        List of validator definitions.
    """
    if isinstance(category, str):
        category_value = category
    else:
        category_value = category.value

    return [v for v in VALIDATOR_REGISTRY if v.category.value == category_value]


def search_validators(
    query: str,
    category: ValidatorCategory | str | None = None,
    include_experimental: bool = False,
    include_deprecated: bool = False,
) -> list[ValidatorDefinition]:
    """Search validators by name, description, or tags.

    Args:
        query: Search query string.
        category: Optional category filter.
        include_experimental: Include experimental validators.
        include_deprecated: Include deprecated validators.

    Returns:
        List of matching validator definitions.
    """
    query_lower = query.lower()
    results = []

    for validator in VALIDATOR_REGISTRY:
        # Apply filters
        if not include_experimental and validator.experimental:
            continue
        if not include_deprecated and validator.deprecated:
            continue
        if category:
            cat_value = category if isinstance(category, str) else category.value
            if validator.category.value != cat_value:
                continue

        # Search in name, display_name, description, and tags
        if (
            query_lower in validator.name.lower()
            or query_lower in validator.display_name.lower()
            or query_lower in validator.description.lower()
            or any(query_lower in tag for tag in validator.tags)
        ):
            results.append(validator)

    return results


def get_category_info(category: ValidatorCategory | str) -> CategoryInfo | None:
    """Get category metadata.

    Args:
        category: Category enum or string value.

    Returns:
        CategoryInfo if found, None otherwise.
    """
    cat_value = category if isinstance(category, str) else category.value
    for info in CATEGORY_INFO:
        if info.value == cat_value:
            return info
    return None


def get_validators_requiring_extra(extra: Literal["drift", "anomaly"]) -> list[ValidatorDefinition]:
    """Get validators that require an optional dependency.

    Args:
        extra: Required extra package ('drift' or 'anomaly').

    Returns:
        List of validators requiring the specified extra.
    """
    return [v for v in VALIDATOR_REGISTRY if v.requires_extra == extra]


def get_validator_stats() -> dict[str, int]:
    """Get statistics about the validator registry.

    Returns:
        Dict with category names as keys and validator counts as values.
    """
    stats: dict[str, int] = {}
    for validator in VALIDATOR_REGISTRY:
        cat = validator.category.value
        stats[cat] = stats.get(cat, 0) + 1
    stats["total"] = len(VALIDATOR_REGISTRY)
    return stats
