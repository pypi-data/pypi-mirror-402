"""Data lineage service.

This module provides services for managing data lineage graphs,
including node and edge CRUD, impact analysis, and auto-discovery.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any, Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.db import BaseRepository
from truthound_dashboard.db.models import AnomalyDetection, LineageEdge, LineageNode, Source


class LineageNodeRepository(BaseRepository[LineageNode]):
    """Repository for LineageNode model operations."""

    model = LineageNode

    async def get_all_nodes(
        self,
        *,
        offset: int = 0,
        limit: int = 500,
    ) -> Sequence[LineageNode]:
        """Get all lineage nodes.

        Args:
            offset: Number to skip.
            limit: Maximum to return.

        Returns:
            Sequence of lineage nodes.
        """
        return await self.list(offset=offset, limit=limit)

    async def get_by_source_id(self, source_id: str) -> LineageNode | None:
        """Get lineage node by linked source ID.

        Args:
            source_id: Data source ID.

        Returns:
            LineageNode or None.
        """
        result = await self.session.execute(
            select(LineageNode).where(LineageNode.source_id == source_id).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_nodes_by_type(
        self,
        node_type: str,
        *,
        limit: int = 100,
    ) -> Sequence[LineageNode]:
        """Get nodes by type.

        Args:
            node_type: Node type (source, transform, sink).
            limit: Maximum to return.

        Returns:
            Sequence of nodes.
        """
        return await self.list(
            limit=limit,
            filters=[LineageNode.node_type == node_type],
        )


class LineageEdgeRepository(BaseRepository[LineageEdge]):
    """Repository for LineageEdge model operations."""

    model = LineageEdge

    async def get_all_edges(
        self,
        *,
        offset: int = 0,
        limit: int = 1000,
    ) -> Sequence[LineageEdge]:
        """Get all lineage edges.

        Args:
            offset: Number to skip.
            limit: Maximum to return.

        Returns:
            Sequence of lineage edges.
        """
        return await self.list(offset=offset, limit=limit)

    async def get_outgoing_edges(
        self,
        node_id: str,
        *,
        limit: int = 100,
    ) -> Sequence[LineageEdge]:
        """Get outgoing edges from a node.

        Args:
            node_id: Source node ID.
            limit: Maximum to return.

        Returns:
            Sequence of edges.
        """
        return await self.list(
            limit=limit,
            filters=[LineageEdge.source_node_id == node_id],
        )

    async def get_incoming_edges(
        self,
        node_id: str,
        *,
        limit: int = 100,
    ) -> Sequence[LineageEdge]:
        """Get incoming edges to a node.

        Args:
            node_id: Target node ID.
            limit: Maximum to return.

        Returns:
            Sequence of edges.
        """
        return await self.list(
            limit=limit,
            filters=[LineageEdge.target_node_id == node_id],
        )

    async def edge_exists(
        self,
        source_node_id: str,
        target_node_id: str,
        edge_type: str = "derives_from",
    ) -> bool:
        """Check if an edge already exists.

        Args:
            source_node_id: Source node ID.
            target_node_id: Target node ID.
            edge_type: Edge type.

        Returns:
            True if edge exists.
        """
        result = await self.session.execute(
            select(LineageEdge)
            .where(LineageEdge.source_node_id == source_node_id)
            .where(LineageEdge.target_node_id == target_node_id)
            .where(LineageEdge.edge_type == edge_type)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None


class LineageService:
    """Service for managing data lineage graphs.

    Provides functionality for:
    - Node and edge CRUD operations
    - Impact analysis (upstream/downstream)
    - Auto-discovery from source metadata
    - Position management for visualization
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service.

        Args:
            session: Database session.
        """
        self.session = session
        self.node_repo = LineageNodeRepository(session)
        self.edge_repo = LineageEdgeRepository(session)

    # =========================================================================
    # Graph Operations
    # =========================================================================

    async def get_graph(
        self,
        source_id: str | None = None,
    ) -> dict[str, Any]:
        """Get the full lineage graph or filtered by source.

        Args:
            source_id: Optional source ID to filter by.

        Returns:
            Dictionary with nodes and edges.
        """
        if source_id:
            # Get node for source and its connected nodes
            root_node = await self.node_repo.get_by_source_id(source_id)
            if not root_node:
                return {"nodes": [], "edges": [], "total_nodes": 0, "total_edges": 0}

            # Get all connected nodes (simplified - could use BFS for deeper traversal)
            node_ids = {root_node.id}
            nodes = [root_node]

            # Get outgoing edges
            outgoing = await self.edge_repo.get_outgoing_edges(root_node.id)
            for edge in outgoing:
                if edge.target_node_id not in node_ids:
                    target = await self.node_repo.get_by_id(edge.target_node_id)
                    if target:
                        nodes.append(target)
                        node_ids.add(target.id)

            # Get incoming edges
            incoming = await self.edge_repo.get_incoming_edges(root_node.id)
            for edge in incoming:
                if edge.source_node_id not in node_ids:
                    source_node = await self.node_repo.get_by_id(edge.source_node_id)
                    if source_node:
                        nodes.append(source_node)
                        node_ids.add(source_node.id)

            # Get all edges between these nodes
            all_edges = await self.edge_repo.get_all_edges(limit=1000)
            edges = [
                e
                for e in all_edges
                if e.source_node_id in node_ids and e.target_node_id in node_ids
            ]
        else:
            nodes = list(await self.node_repo.get_all_nodes())
            edges = list(await self.edge_repo.get_all_edges())

        return {
            "nodes": [self._node_to_dict(n) for n in nodes],
            "edges": [self._edge_to_dict(e) for e in edges],
            "total_nodes": len(nodes),
            "total_edges": len(edges),
        }

    # =========================================================================
    # Node Operations
    # =========================================================================

    async def create_node(
        self,
        *,
        name: str,
        node_type: str,
        source_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        position_x: float | None = None,
        position_y: float | None = None,
    ) -> LineageNode:
        """Create a new lineage node.

        Args:
            name: Node name.
            node_type: Node type (source, transform, sink).
            source_id: Optional linked data source ID.
            metadata: Optional additional metadata.
            position_x: X coordinate for visualization.
            position_y: Y coordinate for visualization.

        Returns:
            Created node.
        """
        node = await self.node_repo.create(
            name=name,
            node_type=node_type,
            source_id=source_id,
            metadata_json=metadata,
            position_x=position_x,
            position_y=position_y,
        )
        return node

    async def get_node(self, node_id: str) -> LineageNode | None:
        """Get a node by ID.

        Args:
            node_id: Node ID.

        Returns:
            LineageNode or None.
        """
        return await self.node_repo.get_by_id(node_id)

    async def update_node(
        self,
        node_id: str,
        *,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
        position_x: float | None = None,
        position_y: float | None = None,
    ) -> LineageNode | None:
        """Update a lineage node.

        Args:
            node_id: Node ID.
            name: New name.
            metadata: New metadata.
            position_x: New X coordinate.
            position_y: New Y coordinate.

        Returns:
            Updated node or None.
        """
        node = await self.node_repo.get_by_id(node_id)
        if node is None:
            return None

        if name is not None:
            node.name = name
        if metadata is not None:
            node.metadata_json = metadata
        if position_x is not None:
            node.position_x = position_x
        if position_y is not None:
            node.position_y = position_y

        await self.session.flush()
        await self.session.refresh(node)
        return node

    async def delete_node(self, node_id: str) -> bool:
        """Delete a node and its edges.

        Args:
            node_id: Node ID.

        Returns:
            True if deleted.
        """
        return await self.node_repo.delete(node_id)

    # =========================================================================
    # Edge Operations
    # =========================================================================

    async def create_edge(
        self,
        *,
        source_node_id: str,
        target_node_id: str,
        edge_type: str = "derives_from",
        metadata: dict[str, Any] | None = None,
    ) -> LineageEdge:
        """Create a new lineage edge.

        Args:
            source_node_id: Source node ID.
            target_node_id: Target node ID.
            edge_type: Edge type.
            metadata: Optional additional metadata.

        Returns:
            Created edge.

        Raises:
            ValueError: If source or target node not found, or edge already exists.
        """
        # Verify nodes exist
        source_node = await self.node_repo.get_by_id(source_node_id)
        if source_node is None:
            raise ValueError(f"Source node '{source_node_id}' not found")

        target_node = await self.node_repo.get_by_id(target_node_id)
        if target_node is None:
            raise ValueError(f"Target node '{target_node_id}' not found")

        # Check for duplicate
        if await self.edge_repo.edge_exists(source_node_id, target_node_id, edge_type):
            raise ValueError("Edge already exists")

        edge = await self.edge_repo.create(
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            edge_type=edge_type,
            metadata_json=metadata,
        )
        return edge

    async def get_edge(self, edge_id: str) -> LineageEdge | None:
        """Get an edge by ID.

        Args:
            edge_id: Edge ID.

        Returns:
            LineageEdge or None.
        """
        return await self.edge_repo.get_by_id(edge_id)

    async def delete_edge(self, edge_id: str) -> bool:
        """Delete an edge.

        Args:
            edge_id: Edge ID.

        Returns:
            True if deleted.
        """
        return await self.edge_repo.delete(edge_id)

    # =========================================================================
    # Impact Analysis
    # =========================================================================

    async def analyze_impact(
        self,
        node_id: str,
        direction: Literal["upstream", "downstream", "both"] = "both",
        max_depth: int = 10,
    ) -> dict[str, Any]:
        """Analyze upstream/downstream impact from a node.

        Args:
            node_id: Starting node ID.
            direction: Analysis direction.
            max_depth: Maximum traversal depth.

        Returns:
            Impact analysis results.

        Raises:
            ValueError: If node not found.
        """
        root_node = await self.node_repo.get_by_id(node_id)
        if root_node is None:
            raise ValueError(f"Node '{node_id}' not found")

        upstream_nodes: list[dict[str, Any]] = []
        downstream_nodes: list[dict[str, Any]] = []
        affected_sources: set[str] = set()

        if direction in ("upstream", "both"):
            upstream = await self._traverse_upstream(node_id, max_depth)
            upstream_nodes = [self._node_summary(n) for n in upstream]
            for n in upstream:
                if n.source_id:
                    affected_sources.add(n.source_id)

        if direction in ("downstream", "both"):
            downstream = await self._traverse_downstream(node_id, max_depth)
            downstream_nodes = [self._node_summary(n) for n in downstream]
            for n in downstream:
                if n.source_id:
                    affected_sources.add(n.source_id)

        return {
            "root_node_id": node_id,
            "root_node_name": root_node.name,
            "direction": direction,
            "upstream_nodes": upstream_nodes,
            "downstream_nodes": downstream_nodes,
            "affected_sources": list(affected_sources),
            "upstream_count": len(upstream_nodes),
            "downstream_count": len(downstream_nodes),
            "total_affected": len(upstream_nodes) + len(downstream_nodes),
        }

    async def _traverse_upstream(
        self,
        node_id: str,
        max_depth: int,
        visited: set[str] | None = None,
        depth: int = 0,
    ) -> list[LineageNode]:
        """Traverse upstream (parents) from a node."""
        if visited is None:
            visited = set()

        if depth >= max_depth or node_id in visited:
            return []

        visited.add(node_id)
        result: list[LineageNode] = []

        incoming = await self.edge_repo.get_incoming_edges(node_id)
        for edge in incoming:
            parent = await self.node_repo.get_by_id(edge.source_node_id)
            if parent and parent.id not in visited:
                result.append(parent)
                result.extend(
                    await self._traverse_upstream(
                        parent.id, max_depth, visited, depth + 1
                    )
                )

        return result

    async def _traverse_downstream(
        self,
        node_id: str,
        max_depth: int,
        visited: set[str] | None = None,
        depth: int = 0,
    ) -> list[LineageNode]:
        """Traverse downstream (children) from a node."""
        if visited is None:
            visited = set()

        if depth >= max_depth or node_id in visited:
            return []

        visited.add(node_id)
        result: list[LineageNode] = []

        outgoing = await self.edge_repo.get_outgoing_edges(node_id)
        for edge in outgoing:
            child = await self.node_repo.get_by_id(edge.target_node_id)
            if child and child.id not in visited:
                result.append(child)
                result.extend(
                    await self._traverse_downstream(
                        child.id, max_depth, visited, depth + 1
                    )
                )

        return result

    # =========================================================================
    # Auto-Discovery
    # =========================================================================

    async def auto_discover(
        self,
        source_id: str,
        include_fk_relations: bool = True,
        max_depth: int = 3,
    ) -> dict[str, Any]:
        """Auto-discover lineage from a data source.

        This is a placeholder for more sophisticated discovery logic.
        In a real implementation, this would analyze source metadata,
        SQL queries, or foreign key relationships.

        Args:
            source_id: Source ID to discover from.
            include_fk_relations: Include foreign key relationships (for DB sources).
            max_depth: Maximum discovery depth.

        Returns:
            Discovered graph.
        """
        # Check if node already exists for this source
        existing_node = await self.node_repo.get_by_source_id(source_id)
        if existing_node:
            return await self.get_graph(source_id)

        # Get source info
        from truthound_dashboard.db import Source as SourceModel

        result = await self.session.execute(
            select(SourceModel).where(SourceModel.id == source_id)
        )
        source = result.scalar_one_or_none()
        if source is None:
            raise ValueError(f"Source '{source_id}' not found")

        # Create a node for this source
        node = await self.create_node(
            name=source.name,
            node_type="source",
            source_id=source_id,
            metadata={"auto_discovered": True, "source_type": source.type},
            position_x=100,
            position_y=100,
        )

        return {
            "source_id": source_id,
            "discovered_nodes": 1,
            "discovered_edges": 0,
            "graph": await self.get_graph(source_id),
        }

    # =========================================================================
    # Position Management
    # =========================================================================

    async def update_positions(
        self,
        positions: list[dict[str, Any]],
    ) -> int:
        """Batch update node positions.

        Args:
            positions: List of {id, x, y} dictionaries.

        Returns:
            Number of positions updated.
        """
        updated = 0
        for pos in positions:
            node = await self.node_repo.get_by_id(pos["id"])
            if node:
                node.position_x = pos.get("x")
                node.position_y = pos.get("y")
                updated += 1

        await self.session.flush()
        return updated

    # =========================================================================
    # Anomaly Integration
    # =========================================================================

    async def get_nodes_with_anomaly_status(self) -> list[dict[str, Any]]:
        """Get all nodes with their latest anomaly detection status.

        Returns:
            List of nodes with anomaly status overlay data.
        """
        nodes = await self.node_repo.get_all_nodes()
        result = []

        for node in nodes:
            node_dict = self._node_to_dict(node)

            # Initialize anomaly status
            anomaly_status: dict[str, Any] = {
                "status": "unknown",  # unknown, clean, low, medium, high
                "anomaly_rate": None,
                "anomaly_count": None,
                "last_detection_at": None,
                "algorithm": None,
            }

            # If node has a linked source, get its latest anomaly detection
            if node.source_id:
                detection = await self._get_latest_anomaly_for_source(node.source_id)
                if detection:
                    anomaly_status = self._classify_anomaly_status(detection)

            node_dict["anomaly_status"] = anomaly_status
            result.append(node_dict)

        return result

    async def get_graph_with_anomalies(
        self,
        source_id: str | None = None,
    ) -> dict[str, Any]:
        """Get the lineage graph with anomaly status overlay.

        Args:
            source_id: Optional source ID to filter by.

        Returns:
            Graph with anomaly status for each node.
        """
        # Get base graph
        graph = await self.get_graph(source_id=source_id)

        # Enhance nodes with anomaly status
        enhanced_nodes = []
        for node_dict in graph["nodes"]:
            anomaly_status: dict[str, Any] = {
                "status": "unknown",
                "anomaly_rate": None,
                "anomaly_count": None,
                "last_detection_at": None,
                "algorithm": None,
            }

            if node_dict.get("source_id"):
                detection = await self._get_latest_anomaly_for_source(
                    node_dict["source_id"]
                )
                if detection:
                    anomaly_status = self._classify_anomaly_status(detection)

            node_dict["anomaly_status"] = anomaly_status
            enhanced_nodes.append(node_dict)

        return {
            **graph,
            "nodes": enhanced_nodes,
        }

    async def get_impacted_by_anomaly(
        self,
        source_id: str,
        max_depth: int = 10,
    ) -> dict[str, Any]:
        """Get downstream nodes impacted by anomalies in a source.

        This analyzes the anomaly status of a source and identifies all
        downstream nodes that could be affected by data quality issues.

        Args:
            source_id: Source ID to analyze.
            max_depth: Maximum traversal depth.

        Returns:
            Impact analysis including impacted nodes and severity.

        Raises:
            ValueError: If source not found.
        """
        # Find node for this source
        node = await self.node_repo.get_by_source_id(source_id)
        if node is None:
            raise ValueError(f"No lineage node found for source '{source_id}'")

        # Get anomaly status for the source
        detection = await self._get_latest_anomaly_for_source(source_id)
        source_anomaly_status = (
            self._classify_anomaly_status(detection) if detection else None
        )

        # Traverse downstream to find impacted nodes
        downstream = await self._traverse_downstream(node.id, max_depth)

        # Build impact path information
        impacted_nodes = []
        for downstream_node in downstream:
            node_info = self._node_summary(downstream_node)

            # Get anomaly status for downstream node if it has a source
            downstream_anomaly_status = None
            if downstream_node.source_id:
                downstream_detection = await self._get_latest_anomaly_for_source(
                    downstream_node.source_id
                )
                if downstream_detection:
                    downstream_anomaly_status = self._classify_anomaly_status(
                        downstream_detection
                    )

            node_info["anomaly_status"] = downstream_anomaly_status
            node_info["impact_severity"] = self._calculate_impact_severity(
                source_anomaly_status, downstream_anomaly_status
            )
            impacted_nodes.append(node_info)

        # Calculate overall impact severity
        overall_severity = self._calculate_overall_severity(
            source_anomaly_status, impacted_nodes
        )

        return {
            "source_node_id": node.id,
            "source_node_name": node.name,
            "source_id": source_id,
            "source_anomaly_status": source_anomaly_status,
            "impacted_nodes": impacted_nodes,
            "impacted_count": len(impacted_nodes),
            "overall_severity": overall_severity,
            "propagation_path": await self._build_propagation_path(
                node.id, downstream
            ),
        }

    async def _get_latest_anomaly_for_source(
        self,
        source_id: str,
    ) -> AnomalyDetection | None:
        """Get the latest successful anomaly detection for a source."""
        result = await self.session.execute(
            select(AnomalyDetection)
            .where(AnomalyDetection.source_id == source_id)
            .where(AnomalyDetection.status == "completed")
            .order_by(AnomalyDetection.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    def _classify_anomaly_status(
        self,
        detection: AnomalyDetection,
    ) -> dict[str, Any]:
        """Classify anomaly detection into status categories.

        Args:
            detection: Anomaly detection record.

        Returns:
            Anomaly status dictionary.
        """
        anomaly_rate = detection.anomaly_rate or 0.0

        # Classify based on anomaly rate thresholds
        if anomaly_rate >= 0.15:  # 15%+ is high
            status = "high"
        elif anomaly_rate >= 0.05:  # 5-15% is medium
            status = "medium"
        elif anomaly_rate > 0:  # 0-5% is low
            status = "low"
        else:
            status = "clean"

        return {
            "status": status,
            "anomaly_rate": anomaly_rate,
            "anomaly_count": detection.anomaly_count,
            "last_detection_at": (
                detection.completed_at.isoformat() if detection.completed_at else None
            ),
            "algorithm": detection.algorithm,
        }

    def _calculate_impact_severity(
        self,
        source_status: dict[str, Any] | None,
        downstream_status: dict[str, Any] | None,
    ) -> str:
        """Calculate impact severity for a downstream node.

        Args:
            source_status: Anomaly status of source node.
            downstream_status: Anomaly status of downstream node.

        Returns:
            Impact severity level.
        """
        if not source_status:
            return "unknown"

        source_level = source_status.get("status", "unknown")

        # If downstream also has anomalies, amplify the severity
        if downstream_status and downstream_status.get("status") in ("medium", "high"):
            if source_level == "high":
                return "critical"
            elif source_level == "medium":
                return "high"
            else:
                return "medium"

        # Map source anomaly status to impact severity
        severity_map = {
            "high": "high",
            "medium": "medium",
            "low": "low",
            "clean": "none",
            "unknown": "unknown",
        }
        return severity_map.get(source_level, "unknown")

    def _calculate_overall_severity(
        self,
        source_status: dict[str, Any] | None,
        impacted_nodes: list[dict[str, Any]],
    ) -> str:
        """Calculate overall impact severity across all impacted nodes.

        Args:
            source_status: Source anomaly status.
            impacted_nodes: List of impacted nodes with severity.

        Returns:
            Overall severity level.
        """
        if not source_status or source_status.get("status") == "clean":
            return "none"

        if not impacted_nodes:
            return source_status.get("status", "unknown")

        # Count severity levels
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for node in impacted_nodes:
            severity = node.get("impact_severity", "unknown")
            if severity in severity_counts:
                severity_counts[severity] += 1

        # Determine overall based on highest severity and count
        if severity_counts["critical"] > 0:
            return "critical"
        elif severity_counts["high"] >= 3 or (
            severity_counts["high"] > 0 and source_status.get("status") == "high"
        ):
            return "critical"
        elif severity_counts["high"] > 0:
            return "high"
        elif severity_counts["medium"] >= 3:
            return "high"
        elif severity_counts["medium"] > 0:
            return "medium"
        elif severity_counts["low"] > 0:
            return "low"
        else:
            return source_status.get("status", "unknown")

    async def _build_propagation_path(
        self,
        root_node_id: str,
        downstream_nodes: list[LineageNode],
    ) -> list[dict[str, Any]]:
        """Build a list of edges showing the propagation path.

        Args:
            root_node_id: Starting node ID.
            downstream_nodes: List of downstream nodes.

        Returns:
            List of edges in the propagation path.
        """
        if not downstream_nodes:
            return []

        node_ids = {root_node_id} | {n.id for n in downstream_nodes}
        all_edges = await self.edge_repo.get_all_edges(limit=1000)

        path_edges = []
        for edge in all_edges:
            if (
                edge.source_node_id in node_ids
                and edge.target_node_id in node_ids
            ):
                path_edges.append({
                    "id": edge.id,
                    "source_node_id": edge.source_node_id,
                    "target_node_id": edge.target_node_id,
                    "edge_type": edge.edge_type,
                })

        return path_edges

    # =========================================================================
    # Helpers
    # =========================================================================

    def _node_to_dict(self, node: LineageNode) -> dict[str, Any]:
        """Convert node to dictionary."""
        return {
            "id": node.id,
            "name": node.name,
            "node_type": node.node_type,
            "source_id": node.source_id,
            "source_name": node.source.name if node.source else None,
            "metadata": node.metadata_json,
            "position_x": node.position_x,
            "position_y": node.position_y,
            "upstream_count": node.upstream_count,
            "downstream_count": node.downstream_count,
            "created_at": node.created_at.isoformat() if node.created_at else None,
            "updated_at": node.updated_at.isoformat() if node.updated_at else None,
        }

    def _edge_to_dict(self, edge: LineageEdge) -> dict[str, Any]:
        """Convert edge to dictionary."""
        return {
            "id": edge.id,
            "source_node_id": edge.source_node_id,
            "target_node_id": edge.target_node_id,
            "source_node_name": edge.source_node.name if edge.source_node else None,
            "target_node_name": edge.target_node.name if edge.target_node else None,
            "edge_type": edge.edge_type,
            "metadata": edge.metadata_json,
            "created_at": edge.created_at.isoformat() if edge.created_at else None,
        }

    def _node_summary(self, node: LineageNode) -> dict[str, Any]:
        """Get minimal node summary."""
        return {
            "id": node.id,
            "name": node.name,
            "node_type": node.node_type,
            "source_id": node.source_id,
        }
