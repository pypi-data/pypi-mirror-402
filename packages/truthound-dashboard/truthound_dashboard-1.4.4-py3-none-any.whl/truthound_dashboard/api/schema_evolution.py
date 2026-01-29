"""Schema evolution API endpoints.

This module provides endpoints for schema evolution detection,
version tracking, and change history.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from truthound_dashboard.schemas import (
    SchemaChangeListResponse,
    SchemaEvolutionResponse,
    SchemaEvolutionSummary,
    SchemaVersionListResponse,
    SchemaVersionResponse,
)

from .deps import (
    SchemaEvolutionServiceDep,
    SchemaServiceDep,
    SourceServiceDep,
)

router = APIRouter(prefix="/sources", tags=["schema-evolution"])


@router.get(
    "/{source_id}/schema/versions",
    response_model=SchemaVersionListResponse,
    summary="List schema versions",
    description="Get schema version history for a source.",
)
async def list_schema_versions(
    source_id: str,
    evolution_service: SchemaEvolutionServiceDep,
    source_service: SourceServiceDep,
    limit: int = 20,
    offset: int = 0,
) -> SchemaVersionListResponse:
    """List schema versions for a source.

    Args:
        source_id: Source ID.
        evolution_service: Schema evolution service.
        source_service: Source service.
        limit: Maximum versions to return.
        offset: Number to skip.

    Returns:
        List of schema versions.
    """
    # Verify source exists
    source = await source_service.get(source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source {source_id} not found",
        )

    versions = await evolution_service.get_version_history(
        source_id, limit=limit, offset=offset
    )

    return SchemaVersionListResponse(
        versions=versions,
        total=len(versions),
        source_id=source_id,
    )


@router.get(
    "/{source_id}/schema/versions/{version_id}",
    response_model=SchemaVersionResponse,
    summary="Get schema version",
    description="Get a specific schema version by ID.",
)
async def get_schema_version(
    source_id: str,
    version_id: str,
    evolution_service: SchemaEvolutionServiceDep,
    source_service: SourceServiceDep,
) -> SchemaVersionResponse:
    """Get a specific schema version.

    Args:
        source_id: Source ID.
        version_id: Version ID.
        evolution_service: Schema evolution service.
        source_service: Source service.

    Returns:
        Schema version details.
    """
    # Verify source exists
    source = await source_service.get(source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source {source_id} not found",
        )

    version = await evolution_service.get_version(version_id)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version_id} not found",
        )

    return version


@router.get(
    "/{source_id}/schema/changes",
    response_model=SchemaChangeListResponse,
    summary="List schema changes",
    description="Get schema change history for a source.",
)
async def list_schema_changes(
    source_id: str,
    evolution_service: SchemaEvolutionServiceDep,
    source_service: SourceServiceDep,
    limit: int = 50,
    offset: int = 0,
) -> SchemaChangeListResponse:
    """List schema changes for a source.

    Args:
        source_id: Source ID.
        evolution_service: Schema evolution service.
        source_service: Source service.
        limit: Maximum changes to return.
        offset: Number to skip.

    Returns:
        List of schema changes.
    """
    # Verify source exists
    source = await source_service.get(source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source {source_id} not found",
        )

    changes = await evolution_service.get_changes(
        source_id, limit=limit, offset=offset
    )

    return SchemaChangeListResponse(
        changes=changes,
        total=len(changes),
        source_id=source_id,
    )


@router.post(
    "/{source_id}/schema/detect-changes",
    response_model=SchemaEvolutionResponse,
    summary="Detect schema changes",
    description="Manually trigger schema change detection.",
)
async def detect_schema_changes(
    source_id: str,
    evolution_service: SchemaEvolutionServiceDep,
    schema_service: SchemaServiceDep,
    source_service: SourceServiceDep,
) -> SchemaEvolutionResponse:
    """Detect schema changes for a source.

    Args:
        source_id: Source ID.
        evolution_service: Schema evolution service.
        schema_service: Schema service.
        source_service: Source service.

    Returns:
        Schema evolution detection result.
    """
    # Verify source exists
    source = await source_service.get(source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source {source_id} not found",
        )

    # Get current schema
    schema = await schema_service.get_active(source_id)
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active schema found for source {source_id}",
        )

    # Detect changes
    result = await evolution_service.detect_changes(source, schema)

    return result


@router.get(
    "/{source_id}/schema/evolution/summary",
    response_model=SchemaEvolutionSummary,
    summary="Get evolution summary",
    description="Get schema evolution summary for a source.",
)
async def get_evolution_summary(
    source_id: str,
    evolution_service: SchemaEvolutionServiceDep,
    source_service: SourceServiceDep,
) -> SchemaEvolutionSummary:
    """Get schema evolution summary for a source.

    Args:
        source_id: Source ID.
        evolution_service: Schema evolution service.
        source_service: Source service.

    Returns:
        Evolution summary.
    """
    # Verify source exists
    source = await source_service.get(source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source {source_id} not found",
        )

    return await evolution_service.get_evolution_summary(source_id)
