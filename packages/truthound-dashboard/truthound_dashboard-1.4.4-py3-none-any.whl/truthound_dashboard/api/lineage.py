"""Lineage API endpoints.

This module provides API endpoints for data lineage visualization and management.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Path, Query, Body

from truthound_dashboard.schemas.lineage import (
    AnomalyImpactResponse,
    AnomalyStatus,
    AutoDiscoverRequest,
    AutoDiscoverResponse,
    ImpactAnalysisRequest,
    ImpactAnalysisResponse,
    ImpactDirection,
    ImpactedNode,
    LineageEdgeCreate,
    LineageEdgeListResponse,
    LineageEdgeResponse,
    LineageGraphResponse,
    LineageGraphWithAnomaliesResponse,
    LineageNodeCreate,
    LineageNodeListResponse,
    LineageNodeResponse,
    LineageNodeUpdate,
    LineageNodeWithAnomaly,
    PositionUpdateRequest,
    PositionUpdateResponse,
    PropagationEdge,
)
from truthound_dashboard.schemas.openlineage import (
    OpenLineageExportRequest,
    OpenLineageExportResponse,
    OpenLineageEmitRequest,
    OpenLineageEmitResponse,
    OpenLineageExportFormat,
    OpenLineageEvent,
    WebhookCreate,
    WebhookUpdate,
    WebhookResponse,
    WebhookListResponse,
    WebhookTestRequest,
    WebhookTestResult,
)
from truthound_dashboard.schemas import MessageResponse

from .deps import LineageServiceDep, OpenLineageEmitterServiceDep, OpenLineageWebhookServiceDep

router = APIRouter()


# =============================================================================
# Graph Endpoints
# =============================================================================


@router.get(
    "",
    response_model=LineageGraphResponse,
    summary="Get lineage graph",
    description="Get the complete lineage graph or filtered by source",
)
async def get_lineage_graph(
    service: LineageServiceDep,
    source_id: Annotated[
        str | None, Query(description="Filter by source ID")
    ] = None,
) -> LineageGraphResponse:
    """Get the lineage graph.

    Args:
        service: Injected lineage service.
        source_id: Optional source ID to filter by.

    Returns:
        Complete lineage graph.
    """
    graph = await service.get_graph(source_id=source_id)
    return LineageGraphResponse(**graph)


@router.get(
    "/sources/{source_id}",
    response_model=LineageGraphResponse,
    summary="Get source lineage",
    description="Get lineage graph for a specific data source",
)
async def get_source_lineage(
    service: LineageServiceDep,
    source_id: Annotated[str, Path(description="Source ID")],
) -> LineageGraphResponse:
    """Get lineage for a specific source.

    Args:
        service: Injected lineage service.
        source_id: Source ID to get lineage for.

    Returns:
        Lineage graph for the source.
    """
    graph = await service.get_graph(source_id=source_id)
    return LineageGraphResponse(**graph)


# =============================================================================
# Node Endpoints
# =============================================================================


@router.get(
    "/nodes",
    response_model=LineageNodeListResponse,
    summary="List nodes",
    description="Get a paginated list of lineage nodes",
)
async def list_nodes(
    service: LineageServiceDep,
    offset: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
    limit: Annotated[
        int, Query(ge=1, le=500, description="Maximum items to return")
    ] = 100,
) -> LineageNodeListResponse:
    """List all lineage nodes.

    Args:
        service: Injected lineage service.
        offset: Number of items to skip.
        limit: Maximum items to return.

    Returns:
        Paginated list of nodes.
    """
    graph = await service.get_graph()
    nodes = graph["nodes"][offset : offset + limit]
    return LineageNodeListResponse(
        data=[LineageNodeResponse(**n) for n in nodes],
        total=graph["total_nodes"],
        offset=offset,
        limit=limit,
    )


@router.post(
    "/nodes",
    response_model=LineageNodeResponse,
    status_code=201,
    summary="Create node",
    description="Create a new lineage node",
)
async def create_node(
    service: LineageServiceDep,
    node: LineageNodeCreate,
) -> LineageNodeResponse:
    """Create a new lineage node.

    Args:
        service: Injected lineage service.
        node: Node creation data.

    Returns:
        Created node.
    """
    created = await service.create_node(
        name=node.name,
        node_type=node.node_type,
        source_id=node.source_id,
        metadata=node.metadata,
        position_x=node.position_x,
        position_y=node.position_y,
    )
    return LineageNodeResponse(
        id=created.id,
        name=created.name,
        node_type=created.node_type,
        source_id=created.source_id,
        source_name=created.source.name if created.source else None,
        metadata=created.metadata_json,
        position_x=created.position_x,
        position_y=created.position_y,
        upstream_count=created.upstream_count,
        downstream_count=created.downstream_count,
        created_at=created.created_at.isoformat() if created.created_at else "",
        updated_at=created.updated_at.isoformat() if created.updated_at else None,
    )


@router.get(
    "/nodes/{node_id}",
    response_model=LineageNodeResponse,
    summary="Get node",
    description="Get a specific lineage node by ID",
)
async def get_node(
    service: LineageServiceDep,
    node_id: Annotated[str, Path(description="Node ID")],
) -> LineageNodeResponse:
    """Get a specific lineage node.

    Args:
        service: Injected lineage service.
        node_id: Node unique identifier.

    Returns:
        Node details.

    Raises:
        HTTPException: 404 if node not found.
    """
    node = await service.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return LineageNodeResponse(
        id=node.id,
        name=node.name,
        node_type=node.node_type,
        source_id=node.source_id,
        source_name=node.source.name if node.source else None,
        metadata=node.metadata_json,
        position_x=node.position_x,
        position_y=node.position_y,
        upstream_count=node.upstream_count,
        downstream_count=node.downstream_count,
        created_at=node.created_at.isoformat() if node.created_at else "",
        updated_at=node.updated_at.isoformat() if node.updated_at else None,
    )


@router.put(
    "/nodes/{node_id}",
    response_model=LineageNodeResponse,
    summary="Update node",
    description="Update an existing lineage node",
)
async def update_node(
    service: LineageServiceDep,
    node_id: Annotated[str, Path(description="Node ID")],
    update: LineageNodeUpdate,
) -> LineageNodeResponse:
    """Update an existing lineage node.

    Args:
        service: Injected lineage service.
        node_id: Node unique identifier.
        update: Update data.

    Returns:
        Updated node.

    Raises:
        HTTPException: 404 if node not found.
    """
    updated = await service.update_node(
        node_id,
        name=update.name,
        metadata=update.metadata,
        position_x=update.position_x,
        position_y=update.position_y,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return LineageNodeResponse(
        id=updated.id,
        name=updated.name,
        node_type=updated.node_type,
        source_id=updated.source_id,
        source_name=updated.source.name if updated.source else None,
        metadata=updated.metadata_json,
        position_x=updated.position_x,
        position_y=updated.position_y,
        upstream_count=updated.upstream_count,
        downstream_count=updated.downstream_count,
        created_at=updated.created_at.isoformat() if updated.created_at else "",
        updated_at=updated.updated_at.isoformat() if updated.updated_at else None,
    )


@router.delete(
    "/nodes/{node_id}",
    response_model=MessageResponse,
    summary="Delete node",
    description="Delete a lineage node and its edges",
)
async def delete_node(
    service: LineageServiceDep,
    node_id: Annotated[str, Path(description="Node ID")],
) -> MessageResponse:
    """Delete a lineage node.

    Args:
        service: Injected lineage service.
        node_id: Node unique identifier.

    Returns:
        Success message.

    Raises:
        HTTPException: 404 if node not found.
    """
    deleted = await service.delete_node(node_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Node not found")
    return MessageResponse(message="Node deleted successfully")


# =============================================================================
# Edge Endpoints
# =============================================================================


@router.get(
    "/edges",
    response_model=LineageEdgeListResponse,
    summary="List edges",
    description="Get a paginated list of lineage edges",
)
async def list_edges(
    service: LineageServiceDep,
    offset: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
    limit: Annotated[
        int, Query(ge=1, le=1000, description="Maximum items to return")
    ] = 100,
) -> LineageEdgeListResponse:
    """List all lineage edges.

    Args:
        service: Injected lineage service.
        offset: Number of items to skip.
        limit: Maximum items to return.

    Returns:
        Paginated list of edges.
    """
    graph = await service.get_graph()
    edges = graph["edges"][offset : offset + limit]
    return LineageEdgeListResponse(
        data=[LineageEdgeResponse(**e) for e in edges],
        total=graph["total_edges"],
        offset=offset,
        limit=limit,
    )


@router.post(
    "/edges",
    response_model=LineageEdgeResponse,
    status_code=201,
    summary="Create edge",
    description="Create a new lineage edge between nodes",
)
async def create_edge(
    service: LineageServiceDep,
    edge: LineageEdgeCreate,
) -> LineageEdgeResponse:
    """Create a new lineage edge.

    Args:
        service: Injected lineage service.
        edge: Edge creation data.

    Returns:
        Created edge.

    Raises:
        HTTPException: 400 if nodes not found or edge already exists.
    """
    try:
        created = await service.create_edge(
            source_node_id=edge.source_node_id,
            target_node_id=edge.target_node_id,
            edge_type=edge.edge_type,
            metadata=edge.metadata,
        )
        return LineageEdgeResponse(
            id=created.id,
            source_node_id=created.source_node_id,
            target_node_id=created.target_node_id,
            source_node_name=created.source_node.name if created.source_node else None,
            target_node_name=created.target_node.name if created.target_node else None,
            edge_type=created.edge_type,
            metadata=created.metadata_json,
            created_at=created.created_at.isoformat() if created.created_at else "",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/edges/{edge_id}",
    response_model=MessageResponse,
    summary="Delete edge",
    description="Delete a lineage edge",
)
async def delete_edge(
    service: LineageServiceDep,
    edge_id: Annotated[str, Path(description="Edge ID")],
) -> MessageResponse:
    """Delete a lineage edge.

    Args:
        service: Injected lineage service.
        edge_id: Edge unique identifier.

    Returns:
        Success message.

    Raises:
        HTTPException: 404 if edge not found.
    """
    deleted = await service.delete_edge(edge_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Edge not found")
    return MessageResponse(message="Edge deleted successfully")


# =============================================================================
# Impact Analysis Endpoints
# =============================================================================


@router.get(
    "/nodes/{node_id}/impact",
    response_model=ImpactAnalysisResponse,
    summary="Analyze impact",
    description="Analyze upstream/downstream impact from a node",
)
async def analyze_impact(
    service: LineageServiceDep,
    node_id: Annotated[str, Path(description="Node ID")],
    direction: Annotated[
        ImpactDirection, Query(description="Analysis direction")
    ] = "both",
    max_depth: Annotated[
        int, Query(ge=1, le=50, description="Maximum traversal depth")
    ] = 10,
) -> ImpactAnalysisResponse:
    """Analyze impact from a node.

    Args:
        service: Injected lineage service.
        node_id: Starting node ID.
        direction: Direction of analysis (upstream, downstream, both).
        max_depth: Maximum traversal depth.

    Returns:
        Impact analysis results.

    Raises:
        HTTPException: 404 if node not found.
    """
    try:
        result = await service.analyze_impact(
            node_id=node_id,
            direction=direction,
            max_depth=max_depth,
        )
        return ImpactAnalysisResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# Anomaly Integration Endpoints
# =============================================================================


@router.get(
    "/graph/with-anomalies",
    response_model=LineageGraphWithAnomaliesResponse,
    summary="Get lineage graph with anomaly overlay",
    description="""
Get the lineage graph with anomaly detection status for each node.

Nodes linked to data sources will include their latest anomaly detection
status, allowing visualization of data quality issues across the lineage.

Anomaly status levels:
- **unknown**: No anomaly detection run
- **clean**: No anomalies detected
- **low**: 0-5% anomaly rate
- **medium**: 5-15% anomaly rate
- **high**: 15%+ anomaly rate
""",
    tags=["anomaly-integration"],
)
async def get_lineage_with_anomalies(
    service: LineageServiceDep,
    source_id: Annotated[
        str | None, Query(description="Optional source ID to filter by")
    ] = None,
) -> LineageGraphWithAnomaliesResponse:
    """Get lineage graph with anomaly status overlay.

    Args:
        service: Injected lineage service.
        source_id: Optional source ID to filter by.

    Returns:
        Graph with anomaly status for each node.
    """
    result = await service.get_graph_with_anomalies(source_id=source_id)

    # Convert nodes to response model
    nodes = [
        LineageNodeWithAnomaly(
            **{k: v for k, v in n.items() if k != "anomaly_status"},
            anomaly_status=AnomalyStatus(**n.get("anomaly_status", {})),
        )
        for n in result["nodes"]
    ]

    return LineageGraphWithAnomaliesResponse(
        nodes=nodes,
        edges=[LineageEdgeResponse(**e) for e in result["edges"]],
        total_nodes=result["total_nodes"],
        total_edges=result["total_edges"],
    )


@router.get(
    "/nodes/{node_id}/anomaly-impact",
    response_model=AnomalyImpactResponse,
    summary="Get anomaly impact analysis",
    description="""
Analyze the downstream impact of anomalies detected in a source.

This endpoint identifies all downstream nodes that could be affected by
data quality issues in the specified source, including:
- Impact severity for each downstream node
- Overall severity assessment
- Propagation path showing how anomalies flow through the lineage
""",
    tags=["anomaly-integration"],
)
async def get_anomaly_impact(
    service: LineageServiceDep,
    node_id: Annotated[str, Path(description="Node ID to analyze")],
    max_depth: Annotated[
        int, Query(ge=1, le=50, description="Maximum traversal depth")
    ] = 10,
) -> AnomalyImpactResponse:
    """Get downstream impact of anomalies from a node.

    Args:
        service: Injected lineage service.
        node_id: Starting node ID (must be linked to a source).
        max_depth: Maximum traversal depth.

    Returns:
        Impact analysis results.

    Raises:
        HTTPException: 404 if node not found or not linked to a source.
    """
    # First get the node to find its source_id
    node = await service.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")

    if not node.source_id:
        raise HTTPException(
            status_code=400,
            detail="Node is not linked to a data source. "
            "Anomaly impact analysis requires a linked source.",
        )

    try:
        result = await service.get_impacted_by_anomaly(
            source_id=node.source_id,
            max_depth=max_depth,
        )

        # Convert to response model
        return AnomalyImpactResponse(
            source_node_id=result["source_node_id"],
            source_node_name=result["source_node_name"],
            source_id=result["source_id"],
            source_anomaly_status=(
                AnomalyStatus(**result["source_anomaly_status"])
                if result.get("source_anomaly_status")
                else None
            ),
            impacted_nodes=[
                ImpactedNode(
                    id=n["id"],
                    name=n["name"],
                    node_type=n["node_type"],
                    source_id=n.get("source_id"),
                    anomaly_status=(
                        AnomalyStatus(**n["anomaly_status"])
                        if n.get("anomaly_status")
                        else None
                    ),
                    impact_severity=n.get("impact_severity", "unknown"),
                )
                for n in result.get("impacted_nodes", [])
            ],
            impacted_count=result.get("impacted_count", 0),
            overall_severity=result.get("overall_severity", "unknown"),
            propagation_path=[
                PropagationEdge(**e)
                for e in result.get("propagation_path", [])
            ],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# Auto-Discovery Endpoints
# =============================================================================


@router.post(
    "/auto-discover",
    response_model=AutoDiscoverResponse,
    summary="Auto-discover lineage",
    description="Auto-discover lineage from a data source",
)
async def auto_discover(
    service: LineageServiceDep,
    request: AutoDiscoverRequest,
) -> AutoDiscoverResponse:
    """Auto-discover lineage from a source.

    Args:
        service: Injected lineage service.
        request: Auto-discovery request.

    Returns:
        Discovery results.

    Raises:
        HTTPException: 404 if source not found.
    """
    try:
        result = await service.auto_discover(
            source_id=request.source_id,
            include_fk_relations=request.include_fk_relations,
            max_depth=request.max_depth,
        )
        return AutoDiscoverResponse(
            source_id=result["source_id"],
            discovered_nodes=result["discovered_nodes"],
            discovered_edges=result["discovered_edges"],
            graph=LineageGraphResponse(**result["graph"]),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# Position Update Endpoints
# =============================================================================


@router.post(
    "/positions",
    response_model=PositionUpdateResponse,
    summary="Update positions",
    description="Batch update node positions for visualization",
)
async def update_positions(
    service: LineageServiceDep,
    request: PositionUpdateRequest,
) -> PositionUpdateResponse:
    """Batch update node positions.

    Args:
        service: Injected lineage service.
        request: Position update request.

    Returns:
        Number of positions updated.
    """
    positions = [
        {"id": p.id, "x": p.x, "y": p.y}
        for p in request.positions
    ]
    updated_count = await service.update_positions(positions)
    return PositionUpdateResponse(updated_count=updated_count)


# =============================================================================
# OpenLineage Export Endpoints
# =============================================================================


@router.post(
    "/openlineage/export",
    response_model=OpenLineageExportResponse,
    summary="Export as OpenLineage",
    description="""
Export lineage graph as OpenLineage events.

OpenLineage is an open standard for lineage metadata interoperability.
This endpoint converts the dashboard's lineage graph into OpenLineage
events that can be consumed by tools like:
- Marquez
- DataHub
- Atlan
- OpenMetadata
- Apache Atlas

The export includes:
- Job information (namespace, name)
- Input datasets (source nodes)
- Output datasets (transform/sink nodes)
- Dataset facets (schema, quality metrics)
""",
    tags=["openlineage"],
)
async def export_openlineage(
    service: OpenLineageEmitterServiceDep,
    request: OpenLineageExportRequest,
) -> OpenLineageExportResponse:
    """Export lineage as OpenLineage events.

    Args:
        service: Injected OpenLineage emitter service.
        request: Export request with options.

    Returns:
        OpenLineage events and metadata.
    """
    result = await service.export_as_openlineage(
        job_namespace=request.job_namespace,
        job_name=request.job_name,
        source_id=request.source_id,
        include_schema=request.include_schema,
        granular=False,
    )

    return OpenLineageExportResponse(
        events=[OpenLineageEvent(**e) for e in result["events"]],
        total_events=result["total_events"],
        total_datasets=result["total_datasets"],
        total_jobs=result["total_jobs"],
        export_time=result["export_time"],
    )


@router.post(
    "/openlineage/export/granular",
    response_model=OpenLineageExportResponse,
    summary="Export as OpenLineage (granular)",
    description="""
Export lineage graph as granular OpenLineage events.

Unlike the standard export which creates a single job for the entire
lineage graph, this endpoint creates a separate job for each transformation
in the lineage, providing finer-grained lineage tracking.

This is useful when you want to track the lineage of each individual
transformation step rather than the entire pipeline.
""",
    tags=["openlineage"],
)
async def export_openlineage_granular(
    service: OpenLineageEmitterServiceDep,
    request: OpenLineageExportRequest,
) -> OpenLineageExportResponse:
    """Export lineage as granular OpenLineage events (one job per transform).

    Args:
        service: Injected OpenLineage emitter service.
        request: Export request with options.

    Returns:
        OpenLineage events and metadata.
    """
    result = await service.export_as_openlineage(
        job_namespace=request.job_namespace,
        job_name=request.job_name,
        source_id=request.source_id,
        include_schema=request.include_schema,
        granular=True,
    )

    return OpenLineageExportResponse(
        events=[OpenLineageEvent(**e) for e in result["events"]],
        total_events=result["total_events"],
        total_datasets=result["total_datasets"],
        total_jobs=result["total_jobs"],
        export_time=result["export_time"],
    )


@router.post(
    "/openlineage/emit",
    response_model=OpenLineageEmitResponse,
    summary="Emit to OpenLineage endpoint",
    description="""
Emit OpenLineage events to an external endpoint.

This endpoint sends the lineage data directly to an OpenLineage-compatible
API endpoint such as:
- Marquez: `http://localhost:5000/api/v1/lineage`
- DataHub: `http://localhost:8080/openlineage`
- Custom webhook endpoints

Authentication can be provided via API key (Bearer token) or custom headers.
""",
    tags=["openlineage"],
)
async def emit_openlineage(
    service: OpenLineageEmitterServiceDep,
    request: OpenLineageEmitRequest,
) -> OpenLineageEmitResponse:
    """Emit OpenLineage events to an external endpoint.

    Args:
        service: Injected OpenLineage emitter service.
        request: Emit request with webhook configuration.

    Returns:
        Emission result with success status.
    """
    result = await service.emit_to_endpoint(
        url=request.webhook.url,
        api_key=request.webhook.api_key,
        headers=request.webhook.headers,
        job_namespace=request.job_namespace,
        job_name=request.job_name,
        source_id=request.source_id,
        timeout=request.webhook.timeout_seconds,
    )

    return OpenLineageEmitResponse(
        success=result["success"],
        events_sent=result["events_sent"],
        failed_events=result["failed_events"],
        error_message=result.get("error_message"),
    )


@router.get(
    "/openlineage/spec",
    summary="Get OpenLineage specification info",
    description="Get information about the supported OpenLineage specification version and features.",
    tags=["openlineage"],
)
async def get_openlineage_spec() -> dict[str, Any]:
    """Get OpenLineage specification information.

    Returns:
        Specification details including version and supported features.
    """
    return {
        "spec_version": "1.0.5",
        "producer": "https://github.com/truthound/truthound-dashboard",
        "supported_facets": {
            "dataset": [
                "schema",
                "dataQualityMetrics",
                "dataQualityAssertions",
                "documentation",
                "ownership",
                "columnLineage",
                "lifecycleStateChange",
            ],
            "job": [
                "sourceCode",
                "sql",
                "documentation",
            ],
            "run": [
                "errorMessage",
                "parent",
                "nominalTime",
                "processingEngine",
            ],
        },
        "supported_event_types": ["START", "RUNNING", "COMPLETE", "FAIL", "ABORT"],
        "export_formats": ["json", "ndjson"],
        "documentation_url": "https://openlineage.io/docs/",
    }


# =============================================================================
# OpenLineage Webhook Endpoints
# =============================================================================


@router.get(
    "/openlineage/webhooks",
    response_model=WebhookListResponse,
    summary="List webhooks",
    description="Get all configured OpenLineage webhooks.",
    tags=["openlineage"],
)
async def list_webhooks(
    service: OpenLineageWebhookServiceDep,
    active_only: Annotated[
        bool, Query(description="Only return active webhooks")
    ] = False,
) -> WebhookListResponse:
    """List all configured webhooks.

    Args:
        service: Injected webhook service.
        active_only: If True, only return active webhooks.

    Returns:
        List of webhooks.
    """
    webhooks = await service.list_webhooks(active_only=active_only)
    return WebhookListResponse(
        data=[
            WebhookResponse(
                id=w.id,
                name=w.name,
                url=w.url,
                is_active=w.is_active,
                headers=w.headers,
                event_types=w.event_types,
                batch_size=w.batch_size,
                timeout_seconds=w.timeout_seconds,
                last_sent_at=w.last_sent_at.isoformat() if w.last_sent_at else None,
                success_count=w.success_count,
                failure_count=w.failure_count,
                last_error=w.last_error,
                created_at=w.created_at.isoformat() if w.created_at else "",
                updated_at=w.updated_at.isoformat() if w.updated_at else None,
            )
            for w in webhooks
        ],
        total=len(webhooks),
    )


@router.post(
    "/openlineage/webhooks",
    response_model=WebhookResponse,
    status_code=201,
    summary="Create webhook",
    description="Create a new OpenLineage webhook configuration.",
    tags=["openlineage"],
)
async def create_webhook(
    service: OpenLineageWebhookServiceDep,
    webhook: WebhookCreate,
) -> WebhookResponse:
    """Create a new webhook configuration.

    Args:
        service: Injected webhook service.
        webhook: Webhook creation data.

    Returns:
        Created webhook.
    """
    created = await service.create_webhook(
        name=webhook.name,
        url=webhook.url,
        is_active=webhook.is_active,
        headers=webhook.headers,
        api_key=webhook.api_key,
        event_types=webhook.event_types.value,
        batch_size=webhook.batch_size,
        timeout_seconds=webhook.timeout_seconds,
    )
    return WebhookResponse(
        id=created.id,
        name=created.name,
        url=created.url,
        is_active=created.is_active,
        headers=created.headers,
        event_types=created.event_types,
        batch_size=created.batch_size,
        timeout_seconds=created.timeout_seconds,
        last_sent_at=created.last_sent_at.isoformat() if created.last_sent_at else None,
        success_count=created.success_count,
        failure_count=created.failure_count,
        last_error=created.last_error,
        created_at=created.created_at.isoformat() if created.created_at else "",
        updated_at=created.updated_at.isoformat() if created.updated_at else None,
    )


@router.get(
    "/openlineage/webhooks/{webhook_id}",
    response_model=WebhookResponse,
    summary="Get webhook",
    description="Get a specific webhook by ID.",
    tags=["openlineage"],
)
async def get_webhook(
    service: OpenLineageWebhookServiceDep,
    webhook_id: Annotated[str, Path(description="Webhook ID")],
) -> WebhookResponse:
    """Get a specific webhook.

    Args:
        service: Injected webhook service.
        webhook_id: Webhook unique identifier.

    Returns:
        Webhook details.

    Raises:
        HTTPException: 404 if webhook not found.
    """
    webhook = await service.get_webhook(webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return WebhookResponse(
        id=webhook.id,
        name=webhook.name,
        url=webhook.url,
        is_active=webhook.is_active,
        headers=webhook.headers,
        event_types=webhook.event_types,
        batch_size=webhook.batch_size,
        timeout_seconds=webhook.timeout_seconds,
        last_sent_at=webhook.last_sent_at.isoformat() if webhook.last_sent_at else None,
        success_count=webhook.success_count,
        failure_count=webhook.failure_count,
        last_error=webhook.last_error,
        created_at=webhook.created_at.isoformat() if webhook.created_at else "",
        updated_at=webhook.updated_at.isoformat() if webhook.updated_at else None,
    )


@router.put(
    "/openlineage/webhooks/{webhook_id}",
    response_model=WebhookResponse,
    summary="Update webhook",
    description="Update an existing webhook configuration.",
    tags=["openlineage"],
)
async def update_webhook(
    service: OpenLineageWebhookServiceDep,
    webhook_id: Annotated[str, Path(description="Webhook ID")],
    update: WebhookUpdate,
) -> WebhookResponse:
    """Update an existing webhook.

    Args:
        service: Injected webhook service.
        webhook_id: Webhook unique identifier.
        update: Update data.

    Returns:
        Updated webhook.

    Raises:
        HTTPException: 404 if webhook not found.
    """
    updated = await service.update_webhook(
        webhook_id,
        name=update.name,
        url=update.url,
        is_active=update.is_active,
        headers=update.headers,
        api_key=update.api_key,
        event_types=update.event_types.value if update.event_types else None,
        batch_size=update.batch_size,
        timeout_seconds=update.timeout_seconds,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return WebhookResponse(
        id=updated.id,
        name=updated.name,
        url=updated.url,
        is_active=updated.is_active,
        headers=updated.headers,
        event_types=updated.event_types,
        batch_size=updated.batch_size,
        timeout_seconds=updated.timeout_seconds,
        last_sent_at=updated.last_sent_at.isoformat() if updated.last_sent_at else None,
        success_count=updated.success_count,
        failure_count=updated.failure_count,
        last_error=updated.last_error,
        created_at=updated.created_at.isoformat() if updated.created_at else "",
        updated_at=updated.updated_at.isoformat() if updated.updated_at else None,
    )


@router.delete(
    "/openlineage/webhooks/{webhook_id}",
    response_model=MessageResponse,
    summary="Delete webhook",
    description="Delete a webhook configuration.",
    tags=["openlineage"],
)
async def delete_webhook(
    service: OpenLineageWebhookServiceDep,
    webhook_id: Annotated[str, Path(description="Webhook ID")],
) -> MessageResponse:
    """Delete a webhook configuration.

    Args:
        service: Injected webhook service.
        webhook_id: Webhook unique identifier.

    Returns:
        Success message.

    Raises:
        HTTPException: 404 if webhook not found.
    """
    deleted = await service.delete_webhook(webhook_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return MessageResponse(message="Webhook deleted successfully")


@router.post(
    "/openlineage/webhooks/test",
    response_model=WebhookTestResult,
    summary="Test webhook",
    description="""
Test a webhook endpoint connectivity.

Sends a test OpenLineage event to verify the endpoint is reachable
and accepts events. The test event is marked with a special header
to identify it as a test.
""",
    tags=["openlineage"],
)
async def test_webhook(
    service: OpenLineageWebhookServiceDep,
    request: WebhookTestRequest,
) -> WebhookTestResult:
    """Test webhook connectivity.

    Args:
        service: Injected webhook service.
        request: Test request with URL and configuration.

    Returns:
        Test result with success status and details.
    """
    result = await service.test_webhook(
        url=request.url,
        headers=request.headers,
        api_key=request.api_key,
        timeout_seconds=request.timeout_seconds,
    )
    return WebhookTestResult(
        success=result["success"],
        status_code=result.get("status_code"),
        response_time_ms=result.get("response_time_ms"),
        error_message=result.get("error_message"),
        response_body=result.get("response_body"),
    )
