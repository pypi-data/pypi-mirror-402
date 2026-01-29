"""Validator configuration schemas.

This module provides backward compatibility for the validators subpackage.
All types and functions are re-exported from the validators module.

For new code, prefer importing directly from truthound_dashboard.schemas.validators:

    from truthound_dashboard.schemas.validators import (
        VALIDATOR_REGISTRY,
        ValidatorDefinition,
        ValidatorConfig,
        get_validator_by_name,
    )
"""

from __future__ import annotations

# Re-export all public symbols from the validators subpackage
from truthound_dashboard.schemas.validators import (
    # Base types
    ParameterDefinition,
    ParameterType,
    ValidatorCategory,
    ValidatorConfig,
    ValidatorConfigList,
    ValidatorDefinition,
    # Utility functions
    configs_to_truthound_format,
    has_custom_params,
    merge_severity_overrides,
    # Registry
    VALIDATOR_REGISTRY,
    get_validator_by_name,
    get_validators_by_category,
    search_validators,
    get_category_info,
    CATEGORY_INFO,
)

__all__ = [
    # Base types
    "ParameterDefinition",
    "ParameterType",
    "ValidatorCategory",
    "ValidatorConfig",
    "ValidatorConfigList",
    "ValidatorDefinition",
    # Utility functions
    "configs_to_truthound_format",
    "has_custom_params",
    "merge_severity_overrides",
    # Registry
    "VALIDATOR_REGISTRY",
    "get_validator_by_name",
    "get_validators_by_category",
    "search_validators",
    "get_category_info",
    "CATEGORY_INFO",
]
