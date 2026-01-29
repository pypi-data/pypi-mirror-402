"""Lineage-related Pydantic schemas.

This module defines schemas for data lineage API operations.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .base import BaseSchema, IDMixin, ListResponseWrapper, TimestampMixin

# Lineage node types
LineageNodeType = Literal["source", "transform", "sink"]

# Lineage edge types
LineageEdgeType = Literal["derives_from", "transforms_to", "joins_with", "filters_from"]

# Impact analysis direction
ImpactDirection = Literal["upstream", "downstream", "both"]


# =============================================================================
# Node Schemas
# =============================================================================


class LineageNodeBase(BaseSchema):
    """Base lineage node schema with common fields."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable node name",
        examples=["Customer Data", "Sales Transform"],
    )
    node_type: LineageNodeType = Field(
        ...,
        description="Node type: source, transform, or sink",
        examples=["source", "transform"],
    )
    source_id: str | None = Field(
        default=None,
        description="Reference to data source (if type is source)",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional metadata for the node",
    )
    position_x: float | None = Field(
        default=None,
        description="X coordinate for graph visualization",
    )
    position_y: float | None = Field(
        default=None,
        description="Y coordinate for graph visualization",
    )


class LineageNodeCreate(LineageNodeBase):
    """Schema for creating a new lineage node."""

    pass


class LineageNodeUpdate(BaseSchema):
    """Schema for updating an existing lineage node."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="New node name",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="New metadata",
    )
    position_x: float | None = Field(
        default=None,
        description="New X coordinate",
    )
    position_y: float | None = Field(
        default=None,
        description="New Y coordinate",
    )


class LineageNodeResponse(LineageNodeBase, IDMixin, TimestampMixin):
    """Schema for lineage node responses."""

    # Additional computed fields
    source_name: str | None = Field(
        default=None,
        description="Name of linked data source",
    )
    upstream_count: int = Field(
        default=0,
        description="Number of upstream nodes",
    )
    downstream_count: int = Field(
        default=0,
        description="Number of downstream nodes",
    )


class LineageNodeSummary(BaseSchema):
    """Minimal node summary for lists and references."""

    id: str
    name: str
    node_type: LineageNodeType
    source_id: str | None = None


class LineageNodeListResponse(ListResponseWrapper[LineageNodeResponse]):
    """Paginated lineage node list response."""

    pass


# =============================================================================
# Edge Schemas
# =============================================================================


class LineageEdgeBase(BaseSchema):
    """Base lineage edge schema with common fields."""

    source_node_id: str = Field(
        ...,
        description="ID of the source node (origin of data flow)",
    )
    target_node_id: str = Field(
        ...,
        description="ID of the target node (destination of data flow)",
    )
    edge_type: LineageEdgeType = Field(
        default="derives_from",
        description="Type of relationship between nodes",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional metadata for the edge (e.g., transformation details)",
    )


class LineageEdgeCreate(LineageEdgeBase):
    """Schema for creating a new lineage edge."""

    pass


class LineageEdgeResponse(LineageEdgeBase, IDMixin):
    """Schema for lineage edge responses."""

    created_at: str = Field(..., description="Edge creation timestamp")

    # Optional enrichment
    source_node_name: str | None = Field(
        default=None,
        description="Name of source node",
    )
    target_node_name: str | None = Field(
        default=None,
        description="Name of target node",
    )


class LineageEdgeListResponse(ListResponseWrapper[LineageEdgeResponse]):
    """Paginated lineage edge list response."""

    pass


# =============================================================================
# Graph Schemas
# =============================================================================


class LineageGraphResponse(BaseSchema):
    """Complete lineage graph with nodes and edges."""

    nodes: list[LineageNodeResponse] = Field(
        default_factory=list,
        description="All nodes in the graph",
    )
    edges: list[LineageEdgeResponse] = Field(
        default_factory=list,
        description="All edges in the graph",
    )
    total_nodes: int = Field(
        default=0,
        description="Total number of nodes",
    )
    total_edges: int = Field(
        default=0,
        description="Total number of edges",
    )


# =============================================================================
# Impact Analysis Schemas
# =============================================================================


class ImpactAnalysisRequest(BaseSchema):
    """Request for impact analysis."""

    direction: ImpactDirection = Field(
        default="both",
        description="Direction of impact analysis",
    )
    max_depth: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum depth to traverse",
    )


class ImpactAnalysisResponse(BaseSchema):
    """Response for upstream/downstream impact analysis."""

    root_node_id: str = Field(..., description="Starting node ID")
    root_node_name: str = Field(..., description="Starting node name")
    direction: ImpactDirection = Field(..., description="Analysis direction")

    upstream_nodes: list[LineageNodeSummary] = Field(
        default_factory=list,
        description="Upstream (source) nodes",
    )
    downstream_nodes: list[LineageNodeSummary] = Field(
        default_factory=list,
        description="Downstream (dependent) nodes",
    )
    affected_sources: list[str] = Field(
        default_factory=list,
        description="IDs of affected data sources",
    )

    upstream_count: int = Field(default=0, description="Number of upstream nodes")
    downstream_count: int = Field(default=0, description="Number of downstream nodes")
    total_affected: int = Field(default=0, description="Total affected nodes")


# =============================================================================
# Auto-Discovery Schemas
# =============================================================================


class AutoDiscoverRequest(BaseSchema):
    """Request to auto-discover lineage from a source."""

    source_id: str = Field(..., description="Source ID to discover from")
    include_fk_relations: bool = Field(
        default=True,
        description="Include foreign key relationships (for DB sources)",
    )
    max_depth: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum depth for discovery",
    )


class AutoDiscoverResponse(BaseSchema):
    """Response from auto-discovery."""

    source_id: str = Field(..., description="Source ID that was analyzed")
    discovered_nodes: int = Field(default=0, description="Number of nodes discovered")
    discovered_edges: int = Field(default=0, description="Number of edges discovered")
    graph: LineageGraphResponse = Field(
        ...,
        description="Discovered lineage graph",
    )


# =============================================================================
# Position Update Schemas
# =============================================================================


class NodePosition(BaseSchema):
    """Position update for a single node."""

    id: str = Field(..., description="Node ID")
    x: float = Field(..., description="New X coordinate")
    y: float = Field(..., description="New Y coordinate")


class PositionUpdateRequest(BaseSchema):
    """Batch position update request."""

    positions: list[NodePosition] = Field(
        ...,
        min_length=1,
        description="List of node positions to update",
    )


class PositionUpdateResponse(BaseSchema):
    """Response from position update."""

    updated_count: int = Field(..., description="Number of positions updated")


# =============================================================================
# Anomaly Integration Schemas
# =============================================================================

# Anomaly status levels
AnomalyStatusLevel = Literal["unknown", "clean", "low", "medium", "high"]

# Impact severity levels
ImpactSeverityLevel = Literal["unknown", "none", "low", "medium", "high", "critical"]


class AnomalyStatus(BaseSchema):
    """Anomaly status for a lineage node."""

    status: AnomalyStatusLevel = Field(
        default="unknown",
        description="Anomaly status level",
    )
    anomaly_rate: float | None = Field(
        default=None,
        description="Rate of anomalies detected (0.0-1.0)",
    )
    anomaly_count: int | None = Field(
        default=None,
        description="Number of anomalies detected",
    )
    last_detection_at: str | None = Field(
        default=None,
        description="Timestamp of last anomaly detection",
    )
    algorithm: str | None = Field(
        default=None,
        description="Algorithm used for detection",
    )


class LineageNodeWithAnomaly(LineageNodeResponse):
    """Lineage node with anomaly status overlay."""

    anomaly_status: AnomalyStatus = Field(
        default_factory=AnomalyStatus,
        description="Anomaly detection status for this node",
    )


class LineageGraphWithAnomaliesResponse(BaseSchema):
    """Lineage graph with anomaly status overlay for all nodes."""

    nodes: list[LineageNodeWithAnomaly] = Field(
        default_factory=list,
        description="Nodes with anomaly status",
    )
    edges: list[LineageEdgeResponse] = Field(
        default_factory=list,
        description="All edges in the graph",
    )
    total_nodes: int = Field(
        default=0,
        description="Total number of nodes",
    )
    total_edges: int = Field(
        default=0,
        description="Total number of edges",
    )


class ImpactedNode(BaseSchema):
    """A node impacted by upstream anomalies."""

    id: str = Field(..., description="Node ID")
    name: str = Field(..., description="Node name")
    node_type: LineageNodeType = Field(..., description="Node type")
    source_id: str | None = Field(default=None, description="Linked source ID")
    anomaly_status: AnomalyStatus | None = Field(
        default=None,
        description="Own anomaly status if available",
    )
    impact_severity: ImpactSeverityLevel = Field(
        default="unknown",
        description="Severity of impact from upstream anomalies",
    )


class PropagationEdge(BaseSchema):
    """An edge in the anomaly propagation path."""

    id: str = Field(..., description="Edge ID")
    source_node_id: str = Field(..., description="Source node ID")
    target_node_id: str = Field(..., description="Target node ID")
    edge_type: LineageEdgeType = Field(..., description="Edge type")


class AnomalyImpactResponse(BaseSchema):
    """Response for anomaly impact analysis."""

    source_node_id: str = Field(..., description="Starting node ID")
    source_node_name: str = Field(..., description="Starting node name")
    source_id: str = Field(..., description="Linked data source ID")
    source_anomaly_status: AnomalyStatus | None = Field(
        default=None,
        description="Anomaly status of the source",
    )
    impacted_nodes: list[ImpactedNode] = Field(
        default_factory=list,
        description="Downstream nodes impacted by anomalies",
    )
    impacted_count: int = Field(
        default=0,
        description="Number of impacted nodes",
    )
    overall_severity: ImpactSeverityLevel = Field(
        default="unknown",
        description="Overall severity of the impact",
    )
    propagation_path: list[PropagationEdge] = Field(
        default_factory=list,
        description="Edges showing anomaly propagation path",
    )
