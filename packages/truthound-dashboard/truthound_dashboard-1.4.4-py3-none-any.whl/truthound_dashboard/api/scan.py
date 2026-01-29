"""PII scan API endpoints.

This module provides endpoints for running PII scans using th.scan().
Detects personally identifiable information and checks compliance with
privacy regulations (GDPR, CCPA, LGPD).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query

from truthound_dashboard.schemas import (
    PIIScanListItem,
    PIIScanListResponse,
    PIIScanRequest,
    PIIScanResponse,
)

from .deps import PIIScanServiceDep, SourceServiceDep

router = APIRouter()


@router.post(
    "/sources/{source_id}/scan",
    response_model=PIIScanResponse,
    summary="Run PII scan",
    description="Scan data source for personally identifiable information (PII)",
)
async def run_pii_scan(
    service: PIIScanServiceDep,
    source_id: Annotated[str, Path(description="Source ID to scan")],
    request: PIIScanRequest,
) -> PIIScanResponse:
    """Run PII scan on a data source.

    Supports all th.scan() parameters for maximum flexibility:
    - columns: Specific columns to scan
    - regulations: Privacy regulations to check (gdpr, ccpa, lgpd)
    - min_confidence: Confidence threshold for PII detection

    Args:
        service: Injected PII scan service.
        source_id: Source to scan.
        request: Scan options.

    Returns:
        PII scan result with findings and violations.

    Raises:
        HTTPException: 404 if source not found.
    """
    try:
        scan = await service.run_scan(
            source_id,
            columns=request.columns,
            regulations=request.regulations,
            min_confidence=request.min_confidence,
        )
        return PIIScanResponse.from_model(scan)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/{scan_id}",
    response_model=PIIScanResponse,
    summary="Get PII scan",
    description="Get a specific PII scan result by ID",
)
async def get_pii_scan(
    service: PIIScanServiceDep,
    scan_id: Annotated[str, Path(description="Scan ID")],
) -> PIIScanResponse:
    """Get a specific PII scan result.

    Args:
        service: Injected PII scan service.
        scan_id: Scan unique identifier.

    Returns:
        PII scan details with findings and violations.

    Raises:
        HTTPException: 404 if scan not found.
    """
    scan = await service.get_scan(scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="PII scan not found")
    return PIIScanResponse.from_model(scan)


@router.get(
    "/sources/{source_id}/scans",
    response_model=PIIScanListResponse,
    summary="List source PII scans",
    description="Get PII scan history for a source",
)
async def list_source_pii_scans(
    service: PIIScanServiceDep,
    source_service: SourceServiceDep,
    source_id: Annotated[str, Path(description="Source ID")],
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum items")] = 20,
) -> PIIScanListResponse:
    """List PII scan history for a source.

    Args:
        service: Injected PII scan service.
        source_service: Injected source service.
        source_id: Source to get scans for.
        limit: Maximum scans to return.

    Returns:
        List of PII scan summaries.

    Raises:
        HTTPException: 404 if source not found.
    """
    # Verify source exists
    source = await source_service.get_by_id(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    scans = await service.list_for_source(source_id, limit=limit)

    return PIIScanListResponse(
        data=[PIIScanListItem.from_model(s) for s in scans],
        total=len(scans),
        limit=limit,
    )


@router.get(
    "/sources/{source_id}/scans/latest",
    response_model=PIIScanResponse,
    summary="Get latest PII scan",
    description="Get the most recent PII scan for a source",
)
async def get_latest_pii_scan(
    service: PIIScanServiceDep,
    source_service: SourceServiceDep,
    source_id: Annotated[str, Path(description="Source ID")],
) -> PIIScanResponse:
    """Get the most recent PII scan for a source.

    Args:
        service: Injected PII scan service.
        source_service: Injected source service.
        source_id: Source to get latest scan for.

    Returns:
        Latest PII scan result.

    Raises:
        HTTPException: 404 if source or scan not found.
    """
    # Verify source exists
    source = await source_service.get_by_id(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    scan = await service.get_latest_for_source(source_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="No PII scans found for source")

    return PIIScanResponse.from_model(scan)
