"""Validations API endpoints.

This module provides endpoints for running and managing validations.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query

from truthound_dashboard.schemas import (
    ValidationListItem,
    ValidationListResponse,
    ValidationResponse,
    ValidationRunRequest,
)
from truthound_dashboard.schemas.validators import configs_to_truthound_format

from .deps import SourceServiceDep, ValidationServiceDep

router = APIRouter()


@router.post(
    "/sources/{source_id}/validate",
    response_model=ValidationResponse,
    summary="Run validation",
    description="Run validation on a data source",
)
async def run_validation(
    service: ValidationServiceDep,
    source_id: Annotated[str, Path(description="Source ID to validate")],
    request: ValidationRunRequest,
) -> ValidationResponse:
    """Run validation on a data source.

    Supports all th.check() parameters for maximum flexibility:
    - validators: Specific validators to run
    - schema_path: Path to schema YAML file
    - auto_schema: Auto-learn and cache schema
    - columns: Specific columns to validate
    - min_severity: Minimum severity to report
    - strict: Raise exception on failures
    - parallel: Use parallel execution
    - max_workers: Max threads for parallel
    - pushdown: Enable query pushdown for SQL

    Args:
        service: Injected validation service.
        source_id: Source to validate.
        request: Validation options.

    Returns:
        Validation result.

    Raises:
        HTTPException: 404 if source not found.
    """
    try:
        # Determine validators and params based on request mode
        validators: list[str] | None = None
        validator_params: dict | None = None

        if request.validator_configs:
            # Advanced mode: use validator_configs (takes precedence)
            validators, validator_params = configs_to_truthound_format(
                request.validator_configs
            )
        elif request.validators:
            # Simple mode: use validator names list (backward compatible)
            validators = request.validators

        # Convert custom validators to internal format
        custom_validators = None
        if request.custom_validators:
            custom_validators = [
                {
                    "validator_id": cv.validator_id,
                    "column": cv.column,
                    "params": cv.params or {},
                }
                for cv in request.custom_validators
            ]

        validation = await service.run_validation(
            source_id,
            validators=validators,
            validator_params=validator_params,
            custom_validators=custom_validators,
            schema_path=request.schema_path,
            auto_schema=request.auto_schema,
            columns=request.columns,
            min_severity=request.min_severity,
            strict=request.strict,
            parallel=request.parallel,
            max_workers=request.max_workers,
            pushdown=request.pushdown,
        )
        return ValidationResponse.from_model(validation)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/{validation_id}",
    response_model=ValidationResponse,
    summary="Get validation",
    description="Get a specific validation result by ID",
)
async def get_validation(
    service: ValidationServiceDep,
    validation_id: Annotated[str, Path(description="Validation ID")],
) -> ValidationResponse:
    """Get a specific validation result.

    Args:
        service: Injected validation service.
        validation_id: Validation unique identifier.

    Returns:
        Validation details with issues.

    Raises:
        HTTPException: 404 if validation not found.
    """
    validation = await service.get_validation(validation_id)
    if validation is None:
        raise HTTPException(status_code=404, detail="Validation not found")
    return ValidationResponse.from_model(validation)


@router.get(
    "/sources/{source_id}/validations",
    response_model=ValidationListResponse,
    summary="List source validations",
    description="Get validation history for a source",
)
async def list_source_validations(
    service: ValidationServiceDep,
    source_service: SourceServiceDep,
    source_id: Annotated[str, Path(description="Source ID")],
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum items")] = 20,
) -> ValidationListResponse:
    """List validation history for a source.

    Args:
        service: Injected validation service.
        source_service: Injected source service.
        source_id: Source to get validations for.
        limit: Maximum validations to return.

    Returns:
        List of validation summaries.

    Raises:
        HTTPException: 404 if source not found.
    """
    # Verify source exists
    source = await source_service.get_by_id(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    validations = await service.list_for_source(source_id, limit=limit)

    return ValidationListResponse(
        data=[ValidationListItem.from_model(v) for v in validations],
        total=len(validations),
        limit=limit,
    )
