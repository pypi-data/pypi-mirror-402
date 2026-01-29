"""Versioning API endpoints.

Provides endpoints for validation result version management:
- List versions for a source
- Get specific version details
- Compare two versions
- Get version history chain
- Create new versions
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query

from truthound_dashboard.core.versioning import (
    VersioningStrategy,
    get_version_manager,
)
from truthound_dashboard.schemas.versioning import (
    CreateVersionRequest,
    CreateVersionResponse,
    RollbackAvailabilityResponse,
    RollbackRequest,
    RollbackResponse,
    VersionCompareRequest,
    VersionDiffResponse,
    VersionHistoryResponse,
    VersionInfoResponse,
    VersionListResponse,
)
from truthound_dashboard.api.deps import ValidationServiceDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/versions", tags=["versioning"])


def _version_info_to_response(version_info) -> VersionInfoResponse:
    """Convert VersionInfo dataclass to response model."""
    return VersionInfoResponse(
        version_id=version_info.version_id,
        version_number=version_info.version_number,
        validation_id=version_info.validation_id,
        source_id=version_info.source_id,
        strategy=version_info.strategy.value,
        created_at=version_info.created_at,
        parent_version_id=version_info.parent_version_id,
        metadata=version_info.metadata,
        content_hash=version_info.content_hash,
    )


@router.get(
    "/sources/{source_id}",
    response_model=VersionListResponse,
    summary="List versions for a source",
    description="Get all validation result versions for a data source, ordered by creation time (newest first).",
)
async def list_source_versions(
    source_id: Annotated[str, Path(description="Source ID")],
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum versions to return")] = 20,
) -> VersionListResponse:
    """List all versions for a source."""
    manager = get_version_manager()
    versions = await manager.list_versions(source_id=source_id, limit=limit)

    return VersionListResponse(
        success=True,
        data=[_version_info_to_response(v) for v in versions],
        total=len(versions),
        source_id=source_id,
    )


@router.get(
    "/{version_id}",
    response_model=VersionInfoResponse,
    summary="Get version details",
    description="Get detailed information about a specific version.",
)
async def get_version(
    version_id: Annotated[str, Path(description="Version ID")],
) -> VersionInfoResponse:
    """Get a specific version by ID."""
    manager = get_version_manager()
    version = await manager.get_version(version_id)

    if not version:
        raise HTTPException(status_code=404, detail=f"Version not found: {version_id}")

    return _version_info_to_response(version)


@router.get(
    "/sources/{source_id}/latest",
    response_model=VersionInfoResponse,
    summary="Get latest version",
    description="Get the most recent version for a data source.",
)
async def get_latest_version(
    source_id: Annotated[str, Path(description="Source ID")],
) -> VersionInfoResponse:
    """Get the latest version for a source."""
    manager = get_version_manager()
    version = await manager.get_latest_version(source_id)

    if not version:
        raise HTTPException(
            status_code=404,
            detail=f"No versions found for source: {source_id}"
        )

    return _version_info_to_response(version)


@router.post(
    "/compare",
    response_model=VersionDiffResponse,
    summary="Compare two versions",
    description="Compare two validation result versions and get detailed differences.",
)
async def compare_versions(
    request: VersionCompareRequest,
    validation_service: ValidationServiceDep,
) -> VersionDiffResponse:
    """Compare two versions and return differences."""
    manager = get_version_manager()

    # Get versions first to check they exist
    from_version = await manager.get_version(request.from_version_id)
    to_version = await manager.get_version(request.to_version_id)

    if not from_version:
        raise HTTPException(
            status_code=404,
            detail=f"From version not found: {request.from_version_id}"
        )
    if not to_version:
        raise HTTPException(
            status_code=404,
            detail=f"To version not found: {request.to_version_id}"
        )

    # Try to get validation results for comparison
    from_result = None
    to_result = None

    try:
        from_validation = await validation_service.get_validation(from_version.validation_id)
        if from_validation and from_validation.result_json:
            from_result = from_validation.result_json
    except Exception:
        pass

    try:
        to_validation = await validation_service.get_validation(to_version.validation_id)
        if to_validation and to_validation.result_json:
            to_result = to_validation.result_json
    except Exception:
        pass

    # Compare versions
    diff = await manager.compare_versions(
        from_version_id=request.from_version_id,
        to_version_id=request.to_version_id,
        from_result=from_result,
        to_result=to_result,
    )

    return VersionDiffResponse(
        from_version=_version_info_to_response(diff.from_version),
        to_version=_version_info_to_response(diff.to_version),
        issues_added=diff.issues_added,
        issues_removed=diff.issues_removed,
        issues_changed=diff.issues_changed,
        summary_changes=diff.summary_changes,
        has_changes=diff.has_changes,
    )


@router.get(
    "/{version_id}/history",
    response_model=VersionHistoryResponse,
    summary="Get version history",
    description="Get the version history chain starting from a specific version.",
)
async def get_version_history(
    version_id: Annotated[str, Path(description="Starting version ID")],
    depth: Annotated[int, Query(ge=1, le=50, description="Maximum history depth")] = 10,
) -> VersionHistoryResponse:
    """Get version history chain."""
    manager = get_version_manager()

    # Check version exists
    version = await manager.get_version(version_id)
    if not version:
        raise HTTPException(status_code=404, detail=f"Version not found: {version_id}")

    history = await manager.get_version_history(version_id=version_id, depth=depth)

    return VersionHistoryResponse(
        success=True,
        data=[_version_info_to_response(v) for v in history],
        depth=len(history),
    )


@router.post(
    "/",
    response_model=CreateVersionResponse,
    summary="Create a version",
    description="Create a new version for a validation result.",
)
async def create_version(
    request: CreateVersionRequest,
    validation_service: ValidationServiceDep,
) -> CreateVersionResponse:
    """Create a new version for a validation."""
    # Get validation to verify it exists
    validation = await validation_service.get_validation(request.validation_id)
    if not validation:
        raise HTTPException(
            status_code=404,
            detail=f"Validation not found: {request.validation_id}"
        )

    manager = get_version_manager()

    # Parse strategy
    strategy = None
    if request.strategy:
        strategy = VersioningStrategy(request.strategy)

    # Create version
    version = await manager.create_version(
        validation_id=request.validation_id,
        source_id=validation.source_id,
        result_json=validation.result_json,
        strategy=strategy,
        metadata=request.metadata,
    )

    return CreateVersionResponse(
        success=True,
        data=_version_info_to_response(version),
        message=f"Created version {version.version_number} for validation {request.validation_id}",
    )


@router.get(
    "/sources/{source_id}/rollback-availability",
    response_model=RollbackAvailabilityResponse,
    summary="Check rollback availability",
    description="Check if rollback is available for a source and list available targets.",
)
async def check_rollback_availability(
    source_id: Annotated[str, Path(description="Source ID")],
) -> RollbackAvailabilityResponse:
    """Check if rollback is available for a source."""
    manager = get_version_manager()
    availability = await manager.can_rollback(source_id)

    return RollbackAvailabilityResponse(
        success=True,
        can_rollback=availability["can_rollback"],
        current_version_id=availability["current_version_id"],
        available_versions=availability["available_versions"],
        rollback_targets=availability["rollback_targets"],
    )


@router.post(
    "/sources/{source_id}/rollback",
    response_model=RollbackResponse,
    summary="Rollback to a previous version",
    description="Rollback a source to a previous validation result version.",
)
async def rollback_to_version(
    source_id: Annotated[str, Path(description="Source ID")],
    request: RollbackRequest,
) -> RollbackResponse:
    """Rollback to a previous version."""
    manager = get_version_manager()

    # Perform rollback
    result = await manager.rollback_to_version(
        source_id=source_id,
        target_version_id=request.target_version_id,
        create_new_validation=request.create_new_validation,
    )

    if not result.success:
        raise HTTPException(
            status_code=400,
            detail=result.message,
        )

    return RollbackResponse(
        success=result.success,
        source_id=result.source_id,
        from_version=_version_info_to_response(result.from_version) if result.from_version else None,
        to_version=_version_info_to_response(result.to_version) if result.to_version else None,
        new_validation_id=result.new_validation_id,
        message=result.message,
        rolled_back_at=result.rolled_back_at,
    )
