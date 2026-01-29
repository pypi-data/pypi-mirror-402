"""Validators API endpoints.

This module provides API endpoints for validator discovery and configuration.
Includes both built-in truthound validators and user-defined custom validators.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.core.plugins import CustomValidatorExecutor
from truthound_dashboard.core.plugins.registry import plugin_registry
from truthound_dashboard.core.plugins.validator_executor import ValidatorContext

from ..schemas.validators import (
    VALIDATOR_REGISTRY,
    CustomValidatorExecuteRequest,
    CustomValidatorExecuteResponse,
    UnifiedValidatorDefinition,
    UnifiedValidatorListResponse,
    ValidatorCategory,
    ValidatorDefinition,
    ValidatorSource,
    get_validator_by_name,
    get_validators_by_category,
    search_validators,
)
from .deps import SourceServiceDep, get_session

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependencies
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get(
    "/validators",
    response_model=list[ValidatorDefinition],
    summary="List built-in validators",
    description="Returns all built-in validators with their parameter definitions.",
)
async def list_validators(
    category: ValidatorCategory | None = Query(
        default=None, description="Filter by category"
    ),
    search: str | None = Query(
        default=None, description="Search by name, description, or tags"
    ),
) -> list[ValidatorDefinition]:
    """List built-in validators, optionally filtered.

    Args:
        category: Optional category filter.
        search: Optional search query.

    Returns:
        List of validator definitions.
    """
    if search:
        return search_validators(search)
    if category:
        return get_validators_by_category(category)
    return VALIDATOR_REGISTRY


@router.get(
    "/validators/unified",
    response_model=UnifiedValidatorListResponse,
    summary="List all validators (built-in + custom)",
    description="Returns unified list of both built-in and custom validators.",
)
async def list_unified_validators(
    session: SessionDep,
    category: str | None = Query(
        default=None, description="Filter by category"
    ),
    source: ValidatorSource | None = Query(
        default=None, description="Filter by source (builtin or custom)"
    ),
    search: str | None = Query(
        default=None, description="Search by name, description, or tags"
    ),
    enabled_only: bool = Query(
        default=False, description="Only return enabled validators"
    ),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> UnifiedValidatorListResponse:
    """List all validators (built-in + custom).

    This endpoint provides a unified view of all available validators,
    combining truthound's built-in validators with user-defined custom validators.

    Args:
        session: Database session.
        category: Optional category filter.
        source: Optional source filter (builtin or custom).
        search: Optional search query.
        enabled_only: Only return enabled validators.
        offset: Pagination offset.
        limit: Pagination limit.

    Returns:
        Unified list of validators with metadata.
    """
    unified_validators: list[UnifiedValidatorDefinition] = []

    # 1. Get built-in validators
    builtin_count = 0
    if source is None or source == ValidatorSource.BUILTIN:
        builtin_validators = VALIDATOR_REGISTRY

        # Apply filters
        if search:
            search_lower = search.lower()
            builtin_validators = [
                v for v in builtin_validators
                if (
                    search_lower in v.name.lower()
                    or search_lower in v.display_name.lower()
                    or search_lower in v.description.lower()
                    or any(search_lower in tag.lower() for tag in v.tags)
                )
            ]

        if category:
            builtin_validators = [
                v for v in builtin_validators
                if v.category.value == category
            ]

        for v in builtin_validators:
            unified_validators.append(UnifiedValidatorDefinition.from_builtin(v))
        builtin_count = len(builtin_validators)

    # 2. Get custom validators
    custom_count = 0
    if source is None or source == ValidatorSource.CUSTOM:
        custom_validators, total_custom = await plugin_registry.list_validators(
            session=session,
            category=category,
            enabled_only=enabled_only,
            search=search,
            offset=0,
            limit=500,  # Get all for now, apply pagination later
        )
        for cv in custom_validators:
            unified_validators.append(UnifiedValidatorDefinition.from_custom(cv))
        custom_count = len(custom_validators)

    # Calculate category summary
    category_counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {"builtin": 0, "custom": 0}
    )
    for v in unified_validators:
        category_counts[v.category][v.source.value] += 1

    categories = [
        {
            "name": cat,
            "label": cat.replace("_", " ").title(),
            "builtin_count": counts["builtin"],
            "custom_count": counts["custom"],
            "total": counts["builtin"] + counts["custom"],
        }
        for cat, counts in sorted(category_counts.items())
    ]

    # Apply pagination
    total = len(unified_validators)
    paginated = unified_validators[offset : offset + limit]

    return UnifiedValidatorListResponse(
        data=paginated,
        total=total,
        builtin_count=builtin_count,
        custom_count=custom_count,
        categories=categories,
    )


@router.get(
    "/validators/categories",
    response_model=list[dict[str, str]],
    summary="List validator categories",
    description="Returns all validator categories with their labels.",
)
async def list_categories() -> list[dict[str, str]]:
    """List all validator categories.

    Returns:
        List of category objects with value and label.
    """
    return [
        {"value": c.value, "label": c.value.replace("_", " ").title()}
        for c in ValidatorCategory
    ]


@router.get(
    "/validators/{name}",
    response_model=ValidatorDefinition | None,
    summary="Get validator by name",
    description="Returns a single validator definition by its name.",
)
async def get_validator(name: str) -> ValidatorDefinition | None:
    """Get a validator by name.

    Args:
        name: Validator name.

    Returns:
        Validator definition if found.
    """
    return get_validator_by_name(name)


# =============================================================================
# Custom Validator Execution Endpoints
# =============================================================================


@router.post(
    "/validators/custom/{validator_id}/execute",
    response_model=CustomValidatorExecuteResponse,
    summary="Execute custom validator",
    description="Execute a custom validator against a data source column.",
)
async def execute_custom_validator(
    session: SessionDep,
    source_service: SourceServiceDep,
    validator_id: Annotated[str, Path(description="Custom validator ID")],
    request: CustomValidatorExecuteRequest,
) -> CustomValidatorExecuteResponse:
    """Execute a custom validator on a specific data source and column.

    This endpoint allows direct execution of a custom validator without
    going through the full validation pipeline. Useful for testing and
    one-off validations.

    Args:
        session: Database session.
        source_service: Source service for data access.
        validator_id: ID of the custom validator.
        request: Execution request with source_id, column_name, and params.

    Returns:
        Execution result with validation status and issues.

    Raises:
        HTTPException: 404 if validator or source not found.
    """
    # Get the custom validator
    validator = await plugin_registry.get_validator(session, validator_id=validator_id)
    if not validator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Custom validator {validator_id} not found",
        )

    if not validator.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Custom validator {validator.name} is disabled",
        )

    # Get the data source
    source = await source_service.get_by_id(request.source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data source {request.source_id} not found",
        )

    # Load data from source
    try:
        import polars as pl

        # Read data based on source type
        if source.type == "csv":
            df = pl.read_csv(source.path)
        elif source.type == "parquet":
            df = pl.read_parquet(source.path)
        elif source.type == "json":
            df = pl.read_json(source.path)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported source type: {source.type}",
            )

        # Check if column exists
        if request.column_name not in df.columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Column '{request.column_name}' not found in source",
            )

        # Apply sample size if specified
        if request.sample_size and request.sample_size < len(df):
            df = df.sample(request.sample_size)

        # Get column values
        column_values = df[request.column_name].to_list()

        # Get column schema info
        column_schema = {
            "dtype": str(df[request.column_name].dtype),
            "null_count": df[request.column_name].null_count(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load data from source: {e}")
        return CustomValidatorExecuteResponse(
            success=False,
            error=f"Failed to load data: {str(e)}",
        )

    # Create execution context
    context = ValidatorContext(
        column_name=request.column_name,
        column_values=column_values,
        parameters=request.param_values,
        schema=column_schema,
        row_count=len(column_values),
    )

    # Execute the validator
    executor = CustomValidatorExecutor()
    result = await executor.execute(
        validator=validator,
        context=context,
        session=session,
        source_id=request.source_id,
    )

    await session.commit()

    return CustomValidatorExecuteResponse(
        success=True,
        passed=result.passed,
        execution_time_ms=result.execution_time_ms,
        issues=result.issues,
        message=result.message,
        details=result.details,
    )


@router.post(
    "/validators/custom/{validator_id}/execute-preview",
    response_model=CustomValidatorExecuteResponse,
    summary="Preview custom validator execution",
    description="Execute a custom validator on sample data for preview.",
)
async def preview_custom_validator_execution(
    session: SessionDep,
    validator_id: Annotated[str, Path(description="Custom validator ID")],
    test_data: dict[str, Any],
) -> CustomValidatorExecuteResponse:
    """Preview custom validator execution with provided test data.

    This endpoint allows testing a saved custom validator with arbitrary
    test data without needing a data source.

    Args:
        session: Database session.
        validator_id: ID of the custom validator.
        test_data: Test data containing column_name, values, and params.

    Returns:
        Execution result with validation status and issues.
    """
    # Get the custom validator
    validator = await plugin_registry.get_validator(session, validator_id=validator_id)
    if not validator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Custom validator {validator_id} not found",
        )

    # Create context from test data
    context = ValidatorContext(
        column_name=test_data.get("column_name", "test_column"),
        column_values=test_data.get("values", []),
        parameters=test_data.get("params", {}),
        schema=test_data.get("schema", {}),
        row_count=len(test_data.get("values", [])),
    )

    # Execute the validator (without logging)
    executor = CustomValidatorExecutor(log_executions=False)
    result = await executor.execute(
        validator=validator,
        context=context,
        session=None,
    )

    return CustomValidatorExecuteResponse(
        success=True,
        passed=result.passed,
        execution_time_ms=result.execution_time_ms,
        issues=result.issues,
        message=result.message,
        details=result.details,
    )
