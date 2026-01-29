"""Profile API endpoints.

This module provides endpoints for data profiling and comparison.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query

from truthound_dashboard.schemas import (
    LatestComparisonResponse,
    ProfileComparisonRequest,
    ProfileComparisonResponse,
    ProfileListResponse,
    ProfileRequest,
    ProfileResponse,
    ProfileTrendRequest,
    ProfileTrendResponse,
)

from .deps import ProfileComparisonServiceDep, ProfileServiceDep, SourceServiceDep

router = APIRouter()


@router.post(
    "/sources/{source_id}/profile",
    response_model=ProfileResponse,
    summary="Profile source",
    description="Run data profiling on a source with optional sampling and pattern detection",
)
async def profile_source(
    service: ProfileServiceDep,
    source_service: SourceServiceDep,
    source_id: Annotated[str, Path(description="Source ID to profile")],
    request: ProfileRequest | None = None,
) -> ProfileResponse:
    """Run data profiling on a source.

    Supports advanced configuration including:
    - Sampling strategies: none, head, random, systematic, stratified, reservoir, adaptive, hash
    - Pattern detection: email, phone, uuid, url, ip_address, credit_card, etc.
    - Statistical analysis options: histograms, correlations, cardinality

    Args:
        service: Injected profile service.
        source_service: Injected source service.
        source_id: Source to profile.
        request: Optional profiling configuration.

    Returns:
        Profiling result with column statistics, detected patterns, and sampling metadata.

    Raises:
        HTTPException: 404 if source not found, 500 on profiling error.
    """
    # Verify source exists
    source = await source_service.get_by_id(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    # Build profiling kwargs from request
    profile_kwargs: dict = {}

    if request:
        # Handle sampling configuration
        if request.sampling:
            # Advanced sampling config takes precedence
            profile_kwargs["sampling_strategy"] = request.sampling.strategy
            profile_kwargs["sample_size"] = request.sampling.sample_size
            profile_kwargs["confidence_level"] = request.sampling.confidence_level
            profile_kwargs["margin_of_error"] = request.sampling.margin_of_error
            profile_kwargs["strata_column"] = request.sampling.strata_column
            profile_kwargs["seed"] = request.sampling.seed
        elif request.sample_size:
            # Backward compatible simple sample_size
            profile_kwargs["sample_size"] = request.sample_size

        # Handle pattern detection configuration
        if request.pattern_detection:
            profile_kwargs["enable_pattern_detection"] = request.pattern_detection.enabled
            profile_kwargs["pattern_sample_size"] = request.pattern_detection.sample_size
            profile_kwargs["min_pattern_confidence"] = request.pattern_detection.min_confidence
            profile_kwargs["patterns_to_detect"] = request.pattern_detection.patterns_to_detect

        # Additional profiling options
        profile_kwargs["include_histograms"] = request.include_histograms
        profile_kwargs["include_correlations"] = request.include_correlations
        profile_kwargs["include_cardinality"] = request.include_cardinality

    try:
        result = await service.profile_source(source_id, **profile_kwargs)
        return ProfileResponse.from_result(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Profile History and Comparison Endpoints
# =============================================================================


@router.get(
    "/sources/{source_id}/profiles",
    response_model=ProfileListResponse,
    summary="List profiles",
    description="Get profile history for a source.",
)
async def list_profiles(
    source_id: Annotated[str, Path(description="Source ID")],
    comparison_service: ProfileComparisonServiceDep,
    source_service: SourceServiceDep,
    limit: int = Query(default=20, ge=1, le=100, description="Maximum profiles to return"),
    offset: int = Query(default=0, ge=0, description="Number to skip"),
) -> ProfileListResponse:
    """List profile history for a source.

    Args:
        source_id: Source ID.
        comparison_service: Profile comparison service.
        source_service: Source service.
        limit: Maximum profiles to return.
        offset: Number to skip.

    Returns:
        List of profile summaries.
    """
    # Verify source exists
    source = await source_service.get_by_id(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    profiles = await comparison_service.list_profiles(
        source_id, limit=limit, offset=offset
    )

    return ProfileListResponse(
        profiles=profiles,
        total=len(profiles),
        source_id=source_id,
    )


@router.post(
    "/profiles/compare",
    response_model=ProfileComparisonResponse,
    summary="Compare profiles",
    description="Compare two specific profiles.",
)
async def compare_profiles(
    request: ProfileComparisonRequest,
    comparison_service: ProfileComparisonServiceDep,
    profile_service: ProfileServiceDep,
    source_service: SourceServiceDep,
) -> ProfileComparisonResponse:
    """Compare two profiles.

    Args:
        request: Comparison request with profile IDs.
        comparison_service: Profile comparison service.
        profile_service: Profile service.
        source_service: Source service.

    Returns:
        Profile comparison result.
    """
    # Get baseline profile to determine source
    baseline = await profile_service.get(request.baseline_profile_id)
    if baseline is None:
        raise HTTPException(
            status_code=404,
            detail=f"Baseline profile {request.baseline_profile_id} not found",
        )

    # Get source
    source = await source_service.get_by_id(baseline.source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    try:
        result = await comparison_service.compare_profiles(
            source,
            request.baseline_profile_id,
            request.current_profile_id,
            significance_threshold=request.significance_threshold,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/sources/{source_id}/profiles/trend",
    response_model=ProfileTrendResponse,
    summary="Get profile trends",
    description="Get time-series profile trends for a source.",
)
async def get_profile_trend(
    source_id: Annotated[str, Path(description="Source ID")],
    comparison_service: ProfileComparisonServiceDep,
    source_service: SourceServiceDep,
    period: str = Query(default="30d", description="Time period (e.g., 7d, 30d, 90d)"),
    granularity: str = Query(default="daily", description="Data granularity"),
) -> ProfileTrendResponse:
    """Get profile trends for a source.

    Args:
        source_id: Source ID.
        comparison_service: Profile comparison service.
        source_service: Source service.
        period: Time period to analyze.
        granularity: Data granularity.

    Returns:
        Profile trend data.
    """
    # Verify source exists
    source = await source_service.get_by_id(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    result = await comparison_service.get_profile_trend(
        source, period=period, granularity=granularity
    )

    return result


@router.get(
    "/sources/{source_id}/profiles/latest-comparison",
    response_model=LatestComparisonResponse,
    summary="Compare latest profiles",
    description="Compare the latest profile with the previous one.",
)
async def get_latest_profile_comparison(
    source_id: Annotated[str, Path(description="Source ID")],
    comparison_service: ProfileComparisonServiceDep,
    source_service: SourceServiceDep,
) -> LatestComparisonResponse:
    """Compare latest profile with previous.

    Args:
        source_id: Source ID.
        comparison_service: Profile comparison service.
        source_service: Source service.

    Returns:
        Latest comparison result.
    """
    # Verify source exists
    source = await source_service.get_by_id(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    return await comparison_service.get_latest_comparison(source)
