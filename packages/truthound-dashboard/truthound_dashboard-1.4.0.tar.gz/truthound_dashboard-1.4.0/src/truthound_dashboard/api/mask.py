"""Data masking API endpoints.

Provides endpoints for running th.mask() operations with three strategies:
- redact: Replace values with asterisks
- hash: Replace values with SHA256 hash
- fake: Replace values with realistic fake data
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from truthound_dashboard.schemas import (
    MaskListItem,
    MaskListResponse,
    MaskRequest,
    MaskResponse,
)

from .deps import MaskServiceDep

router = APIRouter(prefix="/masks", tags=["masks"])


@router.post(
    "/sources/{source_id}/mask",
    response_model=MaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run data masking",
    description="""
Run data masking on a source using th.mask().

Supports three masking strategies:
- **redact**: Replace values with asterisks (default)
- **hash**: Replace values with SHA256 hash (deterministic, can be used for joins)
- **fake**: Replace values with realistic fake data

If `columns` is not specified, PII columns are auto-detected.
""",
)
async def run_mask(
    source_id: str,
    request: MaskRequest,
    service: MaskServiceDep,
) -> MaskResponse:
    """Run data masking on a source.

    Args:
        source_id: Source ID to mask.
        request: Masking options.
        service: Mask service dependency.

    Returns:
        MaskResponse with operation details.

    Raises:
        HTTPException: If source not found or masking fails.
    """
    try:
        mask = await service.run_mask(
            source_id,
            columns=request.columns,
            strategy=request.strategy,
            output_format=request.output_format,
        )
        return MaskResponse.from_db(mask)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Masking failed: {e}",
        ) from e


@router.get(
    "/{mask_id}",
    response_model=MaskResponse,
    summary="Get mask operation by ID",
)
async def get_mask(
    mask_id: str,
    service: MaskServiceDep,
) -> MaskResponse:
    """Get a masking operation by ID.

    Args:
        mask_id: Mask operation ID.
        service: Mask service dependency.

    Returns:
        MaskResponse with operation details.

    Raises:
        HTTPException: If mask operation not found.
    """
    mask = await service.get_mask(mask_id)
    if mask is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mask operation '{mask_id}' not found",
        )
    return MaskResponse.from_db(mask)


@router.get(
    "/sources/{source_id}/masks",
    response_model=MaskListResponse,
    summary="List mask operations for a source",
)
async def list_masks(
    source_id: str,
    service: MaskServiceDep,
    limit: int = 20,
) -> MaskListResponse:
    """List masking operations for a source.

    Args:
        source_id: Source ID.
        service: Mask service dependency.
        limit: Maximum number of results (default: 20).

    Returns:
        MaskListResponse with list of operations.
    """
    masks = await service.list_for_source(source_id, limit=limit)
    return MaskListResponse(
        data=[MaskListItem.from_db(m) for m in masks],
        total=len(masks),
        limit=limit,
    )


@router.get(
    "/sources/{source_id}/masks/latest",
    response_model=MaskResponse,
    summary="Get latest mask operation for a source",
)
async def get_latest_mask(
    source_id: str,
    service: MaskServiceDep,
) -> MaskResponse:
    """Get the most recent masking operation for a source.

    Args:
        source_id: Source ID.
        service: Mask service dependency.

    Returns:
        MaskResponse with operation details.

    Raises:
        HTTPException: If no mask operations found for source.
    """
    mask = await service.get_latest_for_source(source_id)
    if mask is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No mask operations found for source '{source_id}'",
        )
    return MaskResponse.from_db(mask)
