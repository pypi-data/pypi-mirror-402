"""Anomaly detection API endpoints.

This module provides API endpoints for ML-based anomaly detection,
including streaming real-time detection.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, WebSocket, WebSocketDisconnect

from truthound_dashboard.schemas.anomaly import (
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
    AnomalyDetectionListResponse,
    AnomalyStatus,
    AlgorithmListResponse,
    AlgorithmInfo,
    BatchDetectionRequest,
    BatchDetectionResponse,
    BatchDetectionStatus,
    BatchDetectionListResponse,
    BatchSourceResult,
    AlgorithmComparisonRequest,
    AlgorithmComparisonResult,
    AlgorithmComparisonResultItem,
    AgreementSummary,
    AgreementRecord,
    AgreementLevel,
    ExplainabilityRequest,
    ExplainabilityResponse,
    CachedExplanationsListResponse,
    CachedExplanationResponse,
    FeatureContribution,
    AnomalyExplanationResult,
    # Streaming schemas
    StreamingSessionCreate,
    StreamingSessionResponse,
    StreamingSessionListResponse,
    StreamingDataPoint,
    StreamingDataBatch,
    StreamingAlert as StreamingAlertSchema,
    StreamingAlertListResponse,
    StreamingStatusResponse,
    StreamingRecentDataResponse,
    StreamingAlgorithmListResponse,
    StreamingStatistics as StreamingStatisticsSchema,
    StreamingAlgorithm as StreamingAlgorithmSchema,
    StreamingSessionStatus as StreamingStatusSchema,
    get_streaming_algorithm_info_list,
)
from truthound_dashboard.core.streaming_anomaly import (
    StreamingAnomalyDetector,
    StreamingAlgorithm,
    StreamingSessionStatus,
    get_streaming_detector,
)

from .deps import AnomalyDetectionServiceDep, AnomalyExplainerServiceDep

router = APIRouter()


# =============================================================================
# Detection Endpoints
# =============================================================================


@router.post(
    "/sources/{source_id}/anomaly/detect",
    response_model=AnomalyDetectionResponse,
    status_code=201,
    summary="Run anomaly detection",
    description="Run ML-based anomaly detection on a data source",
)
async def run_anomaly_detection(
    service: AnomalyDetectionServiceDep,
    source_id: Annotated[str, Path(description="Source ID")],
    request: AnomalyDetectionRequest,
) -> AnomalyDetectionResponse:
    """Run anomaly detection on a source.

    This creates a detection record and immediately runs the detection.

    Args:
        service: Injected anomaly detection service.
        source_id: Source ID to analyze.
        request: Detection request with algorithm and config.

    Returns:
        Detection results.

    Raises:
        HTTPException: 404 if source not found.
    """
    try:
        # Create the detection record
        detection = await service.create_detection(
            source_id=source_id,
            algorithm=request.algorithm.value,
            columns=request.columns,
            config=request.config,
            sample_size=request.sample_size,
        )

        # Run the detection
        detection = await service.run_detection(detection.id)

        return _detection_to_response(detection)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/anomaly/{detection_id}",
    response_model=AnomalyDetectionResponse,
    summary="Get detection result",
    description="Get a specific anomaly detection result by ID",
)
async def get_detection(
    service: AnomalyDetectionServiceDep,
    detection_id: Annotated[str, Path(description="Detection ID")],
) -> AnomalyDetectionResponse:
    """Get a specific anomaly detection result.

    Args:
        service: Injected anomaly detection service.
        detection_id: Detection unique identifier.

    Returns:
        Detection details.

    Raises:
        HTTPException: 404 if detection not found.
    """
    detection = await service.get_detection(detection_id)
    if detection is None:
        raise HTTPException(status_code=404, detail="Detection not found")
    return _detection_to_response(detection)


@router.get(
    "/sources/{source_id}/anomaly/detections",
    response_model=AnomalyDetectionListResponse,
    summary="List detections",
    description="Get detection history for a source",
)
async def list_detections(
    service: AnomalyDetectionServiceDep,
    source_id: Annotated[str, Path(description="Source ID")],
    offset: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Maximum items to return")
    ] = 50,
) -> AnomalyDetectionListResponse:
    """List detection history for a source.

    Args:
        service: Injected anomaly detection service.
        source_id: Source ID.
        offset: Number of items to skip.
        limit: Maximum items to return.

    Returns:
        Paginated list of detections.
    """
    detections = await service.get_detections_by_source(
        source_id,
        offset=offset,
        limit=limit,
    )
    return AnomalyDetectionListResponse(
        data=[_detection_to_response(d) for d in detections],
        total=len(detections),  # TODO: Get actual total count
        offset=offset,
        limit=limit,
    )


@router.get(
    "/sources/{source_id}/anomaly/latest",
    response_model=AnomalyDetectionResponse,
    summary="Get latest detection",
    description="Get the latest anomaly detection result for a source",
)
async def get_latest_detection(
    service: AnomalyDetectionServiceDep,
    source_id: Annotated[str, Path(description="Source ID")],
) -> AnomalyDetectionResponse:
    """Get the latest detection for a source.

    Args:
        service: Injected anomaly detection service.
        source_id: Source ID.

    Returns:
        Latest detection result.

    Raises:
        HTTPException: 404 if no detections found.
    """
    detection = await service.get_latest_detection(source_id)
    if detection is None:
        raise HTTPException(
            status_code=404,
            detail="No detections found for this source",
        )
    return _detection_to_response(detection)


# =============================================================================
# Algorithm Information Endpoints
# =============================================================================


@router.get(
    "/anomaly/algorithms",
    response_model=AlgorithmListResponse,
    summary="List algorithms",
    description="Get information about available anomaly detection algorithms",
)
async def list_algorithms(
    service: AnomalyDetectionServiceDep,
) -> AlgorithmListResponse:
    """Get information about available algorithms.

    Args:
        service: Injected anomaly detection service.

    Returns:
        List of algorithm information.
    """
    algorithms = service.get_algorithm_info()
    return AlgorithmListResponse(
        algorithms=[AlgorithmInfo(**algo) for algo in algorithms],
        total=len(algorithms),
    )


# =============================================================================
# Explainability Endpoints
# =============================================================================


@router.post(
    "/anomaly/{detection_id}/explain",
    response_model=ExplainabilityResponse,
    summary="Generate anomaly explanations",
    description="Generate SHAP/LIME explanations for specific anomaly rows",
)
async def explain_anomaly(
    explainer_service: AnomalyExplainerServiceDep,
    detection_id: Annotated[str, Path(description="Detection ID")],
    request: ExplainabilityRequest,
) -> ExplainabilityResponse:
    """Generate SHAP/LIME explanations for anomaly rows.

    This uses SHAP (SHapley Additive exPlanations) to provide
    interpretability for ML-based anomaly detection results.

    For tree-based models (Isolation Forest), uses TreeExplainer.
    For other models, uses KernelExplainer as a fallback.

    Args:
        explainer_service: Injected explainer service.
        detection_id: Anomaly detection ID to explain.
        request: Explanation request with row indices and options.

    Returns:
        Explanations with feature contributions for each row.

    Raises:
        HTTPException: 404 if detection not found, 400 if invalid request.
    """
    try:
        result = await explainer_service.explain_anomaly(
            detection_id=detection_id,
            row_indices=request.row_indices,
            max_features=request.max_features,
            sample_background=request.sample_background,
        )

        # Handle error in result
        if "error" in result and result.get("explanations") == []:
            raise HTTPException(status_code=400, detail=result["error"])

        return ExplainabilityResponse(
            detection_id=result.get("detection_id", detection_id),
            algorithm=result.get("algorithm", "unknown"),
            row_indices=result.get("row_indices", request.row_indices),
            feature_names=result.get("feature_names", []),
            explanations=[
                AnomalyExplanationResult(
                    row_index=exp["row_index"],
                    anomaly_score=exp["anomaly_score"],
                    feature_contributions=[
                        FeatureContribution(**fc)
                        for fc in exp["feature_contributions"]
                    ],
                    total_shap=exp["total_shap"],
                    summary=exp["summary"],
                )
                for exp in result.get("explanations", [])
            ],
            generated_at=result.get("generated_at", ""),
            error=result.get("error"),
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/anomaly/{detection_id}/explanations",
    response_model=CachedExplanationsListResponse,
    summary="Get cached explanations",
    description="Get cached SHAP/LIME explanations for a detection",
)
async def get_cached_explanations(
    explainer_service: AnomalyExplainerServiceDep,
    detection_id: Annotated[str, Path(description="Detection ID")],
    row_indices: Annotated[
        str | None,
        Query(description="Comma-separated row indices to filter (optional)")
    ] = None,
) -> CachedExplanationsListResponse:
    """Get cached explanations for a detection.

    Retrieves previously generated explanations from the database.
    Use this to avoid re-computing explanations for the same rows.

    Args:
        explainer_service: Injected explainer service.
        detection_id: Anomaly detection ID.
        row_indices: Optional comma-separated list of row indices to filter.

    Returns:
        List of cached explanations.
    """
    # Parse row indices if provided
    indices_list: list[int] | None = None
    if row_indices:
        try:
            indices_list = [int(i.strip()) for i in row_indices.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid row_indices format. Use comma-separated integers."
            )

    explanations = await explainer_service.get_cached_explanations(
        detection_id=detection_id,
        row_indices=indices_list,
    )

    return CachedExplanationsListResponse(
        detection_id=detection_id,
        explanations=[
            CachedExplanationResponse(
                id=exp["id"],
                detection_id=exp["detection_id"],
                row_index=exp["row_index"],
                anomaly_score=exp["anomaly_score"],
                feature_contributions=[
                    FeatureContribution(**fc)
                    for fc in exp["feature_contributions"]
                ],
                total_shap=exp["total_shap"],
                summary=exp["summary"],
                generated_at=exp.get("generated_at"),
            )
            for exp in explanations
        ],
        total=len(explanations),
    )


# =============================================================================
# Batch Detection Endpoints
# =============================================================================


@router.post(
    "/anomaly/batch",
    response_model=BatchDetectionResponse,
    status_code=201,
    summary="Create batch detection job",
    description="Create a batch anomaly detection job for multiple sources",
)
async def create_batch_detection(
    service: AnomalyDetectionServiceDep,
    request: BatchDetectionRequest,
) -> BatchDetectionResponse:
    """Create a batch anomaly detection job.

    This creates a batch job and immediately starts execution.

    Args:
        service: Injected anomaly detection service.
        request: Batch detection request with source IDs and config.

    Returns:
        Created batch job with initial status.

    Raises:
        HTTPException: 400 if no valid sources.
    """
    try:
        # Create the batch job
        batch_job = await service.create_batch_detection(
            source_ids=request.source_ids,
            name=request.name,
            algorithm=request.algorithm.value,
            config=request.config,
            sample_size=request.sample_size,
        )

        # Start execution in background (for now, run synchronously)
        batch_job = await service.run_batch_detection(batch_job.id)

        return await _batch_job_to_response(service, batch_job)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/anomaly/batch/{batch_id}",
    response_model=BatchDetectionResponse,
    summary="Get batch job status",
    description="Get the status and progress of a batch detection job",
)
async def get_batch_job(
    service: AnomalyDetectionServiceDep,
    batch_id: Annotated[str, Path(description="Batch job ID")],
) -> BatchDetectionResponse:
    """Get a batch detection job status.

    Args:
        service: Injected anomaly detection service.
        batch_id: Batch job unique identifier.

    Returns:
        Batch job details and progress.

    Raises:
        HTTPException: 404 if batch job not found.
    """
    batch_job = await service.get_batch_job(batch_id)
    if batch_job is None:
        raise HTTPException(status_code=404, detail="Batch job not found")
    return await _batch_job_to_response(service, batch_job)


@router.get(
    "/anomaly/batch/{batch_id}/results",
    response_model=list[BatchSourceResult],
    summary="Get batch results",
    description="Get detailed results for each source in a batch job",
)
async def get_batch_results(
    service: AnomalyDetectionServiceDep,
    batch_id: Annotated[str, Path(description="Batch job ID")],
) -> list[BatchSourceResult]:
    """Get detailed results for a batch job.

    Args:
        service: Injected anomaly detection service.
        batch_id: Batch job unique identifier.

    Returns:
        List of results for each source.

    Raises:
        HTTPException: 404 if batch job not found.
    """
    try:
        results = await service.get_batch_results(batch_id)
        return [BatchSourceResult(**r) for r in results]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/anomaly/batch",
    response_model=BatchDetectionListResponse,
    summary="List batch jobs",
    description="List all batch detection jobs",
)
async def list_batch_jobs(
    service: AnomalyDetectionServiceDep,
    offset: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Maximum items to return")
    ] = 50,
) -> BatchDetectionListResponse:
    """List all batch detection jobs.

    Args:
        service: Injected anomaly detection service.
        offset: Number of items to skip.
        limit: Maximum items to return.

    Returns:
        Paginated list of batch jobs.
    """
    batch_jobs = await service.list_batch_jobs(offset=offset, limit=limit)
    responses = []
    for job in batch_jobs:
        responses.append(await _batch_job_to_response(service, job))

    return BatchDetectionListResponse(
        data=responses,
        total=len(responses),  # TODO: Get actual total count
        offset=offset,
        limit=limit,
    )


@router.post(
    "/anomaly/batch/{batch_id}/cancel",
    response_model=BatchDetectionResponse,
    summary="Cancel batch job",
    description="Cancel a running batch detection job",
)
async def cancel_batch_job(
    service: AnomalyDetectionServiceDep,
    batch_id: Annotated[str, Path(description="Batch job ID")],
) -> BatchDetectionResponse:
    """Cancel a running batch job.

    Args:
        service: Injected anomaly detection service.
        batch_id: Batch job unique identifier.

    Returns:
        Updated batch job with cancelled status.

    Raises:
        HTTPException: 404 if batch job not found.
    """
    batch_job = await service.cancel_batch_job(batch_id)
    if batch_job is None:
        raise HTTPException(status_code=404, detail="Batch job not found")
    return await _batch_job_to_response(service, batch_job)


@router.delete(
    "/anomaly/batch/{batch_id}",
    status_code=204,
    summary="Delete batch job",
    description="Delete a batch detection job",
)
async def delete_batch_job(
    service: AnomalyDetectionServiceDep,
    batch_id: Annotated[str, Path(description="Batch job ID")],
) -> None:
    """Delete a batch detection job.

    Args:
        service: Injected anomaly detection service.
        batch_id: Batch job unique identifier.

    Raises:
        HTTPException: 404 if batch job not found.
    """
    deleted = await service.delete_batch_job(batch_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Batch job not found")


# =============================================================================
# Algorithm Comparison Endpoints
# =============================================================================


@router.post(
    "/anomaly/compare",
    response_model=AlgorithmComparisonResult,
    status_code=201,
    summary="Compare algorithms",
    description="Run multiple anomaly detection algorithms and compare results",
)
async def compare_algorithms(
    service: AnomalyDetectionServiceDep,
    request: AlgorithmComparisonRequest,
    source_id: Annotated[str, Query(description="Source ID to analyze")],
) -> AlgorithmComparisonResult:
    """Compare multiple anomaly detection algorithms.

    Runs all specified algorithms on the same data and returns
    a comparison with agreement analysis.

    Args:
        service: Injected anomaly detection service.
        request: Comparison request with algorithms to compare.
        source_id: Source ID to analyze.

    Returns:
        Comparison results with agreement analysis.

    Raises:
        HTTPException: 404 if source not found, 400 if invalid request.
    """
    try:
        # Run comparison
        result = await service.run_comparison(
            source_id=source_id,
            algorithms=[algo.value for algo in request.algorithms],
            columns=request.columns,
            config=request.config,
            sample_size=request.sample_size,
        )

        return _comparison_to_response(result)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/anomaly/compare/{comparison_id}",
    response_model=AlgorithmComparisonResult,
    summary="Get comparison result",
    description="Get a specific algorithm comparison result by ID",
)
async def get_comparison(
    service: AnomalyDetectionServiceDep,
    comparison_id: Annotated[str, Path(description="Comparison ID")],
) -> AlgorithmComparisonResult:
    """Get a specific algorithm comparison result.

    Note: Comparison results are computed on-the-fly and not persisted.
    This endpoint would require storing comparison results to be functional.

    Args:
        service: Injected anomaly detection service.
        comparison_id: Comparison unique identifier.

    Returns:
        Comparison details.

    Raises:
        HTTPException: 404 - comparisons are not persisted.
    """
    # For now, comparisons are not persisted - they are computed on-the-fly
    raise HTTPException(
        status_code=404,
        detail="Comparison results are computed on-the-fly and not persisted. "
        "Please run a new comparison using POST /anomaly/compare",
    )


# =============================================================================
# Helper Functions
# =============================================================================


def _comparison_to_response(result: dict) -> AlgorithmComparisonResult:
    """Convert comparison result dict to response schema."""
    from truthound_dashboard.schemas.anomaly import AnomalyAlgorithm

    # Convert algorithm results
    algorithm_results = []
    for ar in result.get("algorithm_results", []):
        algorithm_results.append(
            AlgorithmComparisonResultItem(
                algorithm=AnomalyAlgorithm(ar["algorithm"]),
                display_name=ar["display_name"],
                status=AnomalyStatus(ar["status"]),
                anomaly_count=ar.get("anomaly_count"),
                anomaly_rate=ar.get("anomaly_rate"),
                duration_ms=ar.get("duration_ms"),
                error_message=ar.get("error_message"),
                anomaly_indices=ar.get("anomaly_indices", []),
            )
        )

    # Convert agreement summary
    agreement_summary = None
    if result.get("agreement_summary"):
        summary_data = result["agreement_summary"]
        agreement_summary = AgreementSummary(
            total_algorithms=summary_data["total_algorithms"],
            total_unique_anomalies=summary_data["total_unique_anomalies"],
            all_agree_count=summary_data["all_agree_count"],
            majority_agree_count=summary_data["majority_agree_count"],
            some_agree_count=summary_data["some_agree_count"],
            one_only_count=summary_data["one_only_count"],
            agreement_matrix=summary_data.get("agreement_matrix", []),
        )

    # Convert agreement records
    agreement_records = None
    if result.get("agreement_records"):
        agreement_records = [
            AgreementRecord(
                row_index=rec["row_index"],
                detected_by=[AnomalyAlgorithm(a) for a in rec["detected_by"]],
                detection_count=rec["detection_count"],
                agreement_level=AgreementLevel(rec["agreement_level"]),
                confidence_score=rec["confidence_score"],
                column_values=rec.get("column_values", {}),
            )
            for rec in result["agreement_records"]
        ]

    return AlgorithmComparisonResult(
        id=result["id"],
        source_id=result["source_id"],
        status=AnomalyStatus(result["status"]),
        total_rows=result.get("total_rows"),
        columns_analyzed=result.get("columns_analyzed"),
        algorithm_results=algorithm_results,
        agreement_summary=agreement_summary,
        agreement_records=agreement_records,
        total_duration_ms=result.get("total_duration_ms"),
        error_message=result.get("error_message"),
        created_at=result["created_at"],
        completed_at=result.get("completed_at"),
    )


async def _batch_job_to_response(service, batch_job) -> BatchDetectionResponse:
    """Convert batch job model to response schema."""
    from truthound_dashboard.schemas.anomaly import (
        AnomalyAlgorithm,
        BatchDetectionStatus,
        BatchSourceResult,
    )

    # Get detailed results with source names
    results = None
    if batch_job.results_json or batch_job.total_sources > 0:
        try:
            results_data = await service.get_batch_results(batch_job.id)
            results = [BatchSourceResult(**r) for r in results_data]
        except ValueError:
            results = None

    return BatchDetectionResponse(
        id=batch_job.id,
        name=batch_job.name,
        status=BatchDetectionStatus(batch_job.status),
        algorithm=AnomalyAlgorithm(batch_job.algorithm),
        config=batch_job.config,
        total_sources=batch_job.total_sources,
        completed_sources=batch_job.completed_sources,
        failed_sources=batch_job.failed_sources,
        progress_percent=batch_job.progress_percent,
        current_source_id=batch_job.current_source_id,
        total_anomalies=batch_job.total_anomalies,
        total_rows_analyzed=batch_job.total_rows_analyzed,
        average_anomaly_rate=batch_job.average_anomaly_rate,
        results=results,
        duration_ms=batch_job.duration_ms,
        error_message=batch_job.error_message,
        created_at=batch_job.created_at.isoformat() if batch_job.created_at else "",
        started_at=batch_job.started_at.isoformat() if batch_job.started_at else None,
        completed_at=batch_job.completed_at.isoformat() if batch_job.completed_at else None,
    )


def _detection_to_response(detection) -> AnomalyDetectionResponse:
    """Convert detection model to response schema."""
    from truthound_dashboard.schemas.anomaly import (
        AnomalyAlgorithm,
        AnomalyStatus,
        AnomalyRecord,
        ColumnAnomalySummary,
    )

    # Parse anomalies if present
    anomalies = None
    if detection.result_json and "anomalies" in detection.result_json:
        anomalies = [
            AnomalyRecord(**a) for a in detection.result_json["anomalies"][:100]
        ]

    # Parse column summaries if present
    column_summaries = None
    if detection.result_json and "column_summaries" in detection.result_json:
        column_summaries = [
            ColumnAnomalySummary(**cs)
            for cs in detection.result_json["column_summaries"]
        ]

    return AnomalyDetectionResponse(
        id=detection.id,
        source_id=detection.source_id,
        status=AnomalyStatus(detection.status),
        algorithm=AnomalyAlgorithm(detection.algorithm),
        config=detection.config,
        total_rows=detection.total_rows,
        anomaly_count=detection.anomaly_count,
        anomaly_rate=detection.anomaly_rate,
        columns_analyzed=detection.columns_analyzed,
        column_summaries=column_summaries,
        anomalies=anomalies,
        duration_ms=detection.duration_ms,
        error_message=detection.error_message,
        created_at=detection.created_at.isoformat() if detection.created_at else "",
        started_at=detection.started_at.isoformat() if detection.started_at else None,
        completed_at=detection.completed_at.isoformat() if detection.completed_at else None,
    )


# =============================================================================
# Streaming Anomaly Detection Endpoints
# =============================================================================


@router.post(
    "/anomaly/streaming/start",
    response_model=StreamingSessionResponse,
    status_code=201,
    summary="Start streaming session",
    description="Create and start a new streaming anomaly detection session",
)
async def start_streaming_session(
    request: StreamingSessionCreate,
) -> StreamingSessionResponse:
    """Start a new streaming anomaly detection session.

    Args:
        request: Session configuration.

    Returns:
        Created and started session.
    """
    detector = get_streaming_detector()

    # Map schema algorithm to core algorithm
    algorithm = StreamingAlgorithm(request.algorithm.value)

    # Create session
    session = await detector.create_session(
        source_id=request.source_id,
        algorithm=algorithm,
        window_size=request.window_size,
        threshold=request.threshold,
        columns=request.columns or [],
        config=request.config,
    )

    # Start the session
    session = await detector.start_session(session.id)

    return _session_to_response(session)


@router.post(
    "/anomaly/streaming/{session_id}/data",
    response_model=StreamingAlertSchema | None,
    summary="Push data point",
    description="Push a data point to a streaming session for anomaly detection",
)
async def push_streaming_data(
    session_id: Annotated[str, Path(description="Session ID")],
    data_point: StreamingDataPoint,
) -> StreamingAlertSchema | None:
    """Push a data point to a streaming session.

    Args:
        session_id: Session ID.
        data_point: Data point to push.

    Returns:
        Alert if anomaly detected, None otherwise.

    Raises:
        HTTPException: 404 if session not found.
    """
    detector = get_streaming_detector()

    # Parse timestamp if provided
    timestamp = None
    if data_point.timestamp:
        try:
            timestamp = datetime.fromisoformat(data_point.timestamp)
        except ValueError:
            pass

    try:
        alert = await detector.push_data_point(
            session_id=session_id,
            data=data_point.data,
            timestamp=timestamp,
        )

        if alert is not None:
            return _alert_to_response(alert)
        return None

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/anomaly/streaming/{session_id}/batch",
    response_model=list[StreamingAlertSchema],
    summary="Push data batch",
    description="Push a batch of data points to a streaming session",
)
async def push_streaming_batch(
    session_id: Annotated[str, Path(description="Session ID")],
    batch: StreamingDataBatch,
) -> list[StreamingAlertSchema]:
    """Push a batch of data points to a streaming session.

    Args:
        session_id: Session ID.
        batch: Batch of data points.

    Returns:
        List of alerts for detected anomalies.

    Raises:
        HTTPException: 404 if session not found.
    """
    detector = get_streaming_detector()

    # Prepare data and timestamps
    data_points = [dp.data for dp in batch.data_points]
    timestamps = []
    for dp in batch.data_points:
        if dp.timestamp:
            try:
                timestamps.append(datetime.fromisoformat(dp.timestamp))
            except ValueError:
                timestamps.append(datetime.utcnow())
        else:
            timestamps.append(datetime.utcnow())

    try:
        alerts = await detector.push_batch(
            session_id=session_id,
            data_points=data_points,
            timestamps=timestamps,
        )

        return [_alert_to_response(alert) for alert in alerts]

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/anomaly/streaming/{session_id}/status",
    response_model=StreamingStatusResponse,
    summary="Get session status",
    description="Get the current status and statistics of a streaming session",
)
async def get_streaming_status(
    session_id: Annotated[str, Path(description="Session ID")],
) -> StreamingStatusResponse:
    """Get streaming session status and statistics.

    Args:
        session_id: Session ID.

    Returns:
        Session status with statistics.

    Raises:
        HTTPException: 404 if session not found.
    """
    detector = get_streaming_detector()

    session = await detector.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    stats = await detector.get_statistics(session_id)
    recent_alerts = await detector.get_alerts(session_id, limit=10)

    return StreamingStatusResponse(
        session_id=session.id,
        status=StreamingStatusSchema(session.status.value),
        total_points=stats.get("total_points", 0),
        total_alerts=stats.get("total_alerts", 0),
        buffer_utilization=stats.get("buffer_utilization", 0),
        statistics={
            col: StreamingStatisticsSchema(**col_stats)
            for col, col_stats in stats.get("columns", {}).items()
        },
        recent_alerts=[_alert_to_response(alert) for alert in recent_alerts],
    )


@router.post(
    "/anomaly/streaming/{session_id}/stop",
    response_model=StreamingSessionResponse,
    summary="Stop streaming session",
    description="Stop a running streaming session",
)
async def stop_streaming_session(
    session_id: Annotated[str, Path(description="Session ID")],
) -> StreamingSessionResponse:
    """Stop a streaming session.

    Args:
        session_id: Session ID to stop.

    Returns:
        Updated session.

    Raises:
        HTTPException: 404 if session not found.
    """
    detector = get_streaming_detector()

    try:
        session = await detector.stop_session(session_id)
        return _session_to_response(session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete(
    "/anomaly/streaming/{session_id}",
    status_code=204,
    summary="Delete streaming session",
    description="Delete a streaming session",
)
async def delete_streaming_session(
    session_id: Annotated[str, Path(description="Session ID")],
) -> None:
    """Delete a streaming session.

    Args:
        session_id: Session ID to delete.

    Raises:
        HTTPException: 404 if session not found.
    """
    detector = get_streaming_detector()

    deleted = await detector.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")


@router.get(
    "/anomaly/streaming/{session_id}/alerts",
    response_model=StreamingAlertListResponse,
    summary="List session alerts",
    description="Get alerts from a streaming session",
)
async def list_streaming_alerts(
    session_id: Annotated[str, Path(description="Session ID")],
    offset: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Maximum items to return")
    ] = 50,
) -> StreamingAlertListResponse:
    """List alerts from a streaming session.

    Args:
        session_id: Session ID.
        offset: Pagination offset.
        limit: Maximum items.

    Returns:
        Paginated list of alerts.

    Raises:
        HTTPException: 404 if session not found.
    """
    detector = get_streaming_detector()

    session = await detector.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    alerts = await detector.get_alerts(session_id, limit=limit, offset=offset)

    return StreamingAlertListResponse(
        data=[_alert_to_response(alert) for alert in alerts],
        total=len(session._alerts),
        offset=offset,
        limit=limit,
    )


@router.get(
    "/anomaly/streaming/{session_id}/data",
    response_model=StreamingRecentDataResponse,
    summary="Get recent data",
    description="Get recent data points from a streaming session",
)
async def get_streaming_recent_data(
    session_id: Annotated[str, Path(description="Session ID")],
    limit: Annotated[
        int, Query(ge=1, le=1000, description="Maximum items to return")
    ] = 100,
) -> StreamingRecentDataResponse:
    """Get recent data points from a streaming session.

    Args:
        session_id: Session ID.
        limit: Maximum points to return.

    Returns:
        Recent data points.

    Raises:
        HTTPException: 404 if session not found.
    """
    detector = get_streaming_detector()

    session = await detector.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    data_points = await detector.get_recent_data(session_id, limit=limit)

    return StreamingRecentDataResponse(
        session_id=session_id,
        data_points=data_points,
        total=len(data_points),
    )


@router.get(
    "/anomaly/streaming/sessions",
    response_model=StreamingSessionListResponse,
    summary="List streaming sessions",
    description="List all active streaming sessions",
)
async def list_streaming_sessions(
    offset: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Maximum items to return")
    ] = 50,
) -> StreamingSessionListResponse:
    """List all streaming sessions.

    Args:
        offset: Pagination offset.
        limit: Maximum items.

    Returns:
        Paginated list of sessions.
    """
    detector = get_streaming_detector()

    sessions = await detector.list_sessions()
    paginated = sessions[offset : offset + limit]

    return StreamingSessionListResponse(
        data=[_session_to_response(s) for s in paginated],
        total=len(sessions),
        offset=offset,
        limit=limit,
    )


@router.get(
    "/anomaly/streaming/algorithms",
    response_model=StreamingAlgorithmListResponse,
    summary="List streaming algorithms",
    description="Get information about available streaming algorithms",
)
async def list_streaming_algorithms() -> StreamingAlgorithmListResponse:
    """Get information about available streaming algorithms.

    Returns:
        List of streaming algorithm information.
    """
    algorithms = get_streaming_algorithm_info_list()
    return StreamingAlgorithmListResponse(
        algorithms=algorithms,
        total=len(algorithms),
    )


@router.websocket("/anomaly/streaming/{session_id}/ws")
async def streaming_websocket(
    websocket: WebSocket,
    session_id: str,
) -> None:
    """WebSocket endpoint for real-time streaming alerts.

    Clients can connect to receive alerts in real-time.
    They can also push data points through the WebSocket.

    Protocol:
    - Send JSON: {"type": "data", "data": {...}} to push data
    - Receive JSON: {"type": "alert", "alert": {...}} on anomaly

    Args:
        websocket: WebSocket connection.
        session_id: Session ID.
    """
    detector = get_streaming_detector()

    # Verify session exists
    session = await detector.get_session(session_id)
    if session is None:
        await websocket.close(code=4004, reason="Session not found")
        return

    await websocket.accept()

    # Register callback for alerts
    async def on_alert(alert):
        """Send alert to WebSocket client."""
        try:
            await websocket.send_json({
                "type": "alert",
                "alert": alert.to_dict(),
            })
        except Exception:
            pass

    detector.register_alert_callback(session_id, on_alert)

    try:
        while True:
            # Receive data from client
            message = await websocket.receive_json()

            if message.get("type") == "data":
                # Push data point
                data = message.get("data", {})
                timestamp_str = message.get("timestamp")
                timestamp = None
                if timestamp_str:
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str)
                    except ValueError:
                        pass

                alert = await detector.push_data_point(
                    session_id=session_id,
                    data=data,
                    timestamp=timestamp,
                )

                # Send acknowledgment
                await websocket.send_json({
                    "type": "ack",
                    "has_alert": alert is not None,
                })

            elif message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass
    finally:
        detector.unregister_alert_callback(session_id, on_alert)


# =============================================================================
# Streaming Helper Functions
# =============================================================================


def _session_to_response(session) -> StreamingSessionResponse:
    """Convert streaming session to response schema."""
    statistics = None
    if session._column_stats:
        statistics = {
            col: StreamingStatisticsSchema(**stats.to_dict())
            for col, stats in session._column_stats.items()
        }

    return StreamingSessionResponse(
        id=session.id,
        source_id=session.source_id,
        algorithm=StreamingAlgorithmSchema(session.algorithm.value),
        window_size=session.window_size,
        threshold=session.threshold,
        columns=session.columns,
        status=StreamingStatusSchema(session.status.value),
        config=session.config,
        statistics=statistics,
        total_points=len(session._buffer),
        total_alerts=len(session._alerts),
        created_at=session.created_at.isoformat(),
        started_at=session.started_at.isoformat() if session.started_at else None,
        stopped_at=session.stopped_at.isoformat() if session.stopped_at else None,
    )


def _alert_to_response(alert) -> StreamingAlertSchema:
    """Convert streaming alert to response schema."""
    return StreamingAlertSchema(
        id=alert.id,
        session_id=alert.session_id,
        timestamp=alert.timestamp.isoformat(),
        data_point=alert.data_point,
        anomaly_score=alert.anomaly_score,
        is_anomaly=alert.is_anomaly,
        algorithm=StreamingAlgorithmSchema(alert.algorithm.value),
        details=alert.details,
    )
