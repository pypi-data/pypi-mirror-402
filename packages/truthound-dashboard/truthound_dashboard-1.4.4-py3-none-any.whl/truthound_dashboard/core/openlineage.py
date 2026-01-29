"""OpenLineage emitter service.

This module provides services for converting dashboard lineage to OpenLineage events
and emitting them to external systems.

The OpenLineage emitter follows the Protocol-based design for extensibility:
- IOpenLineageEmitter: Core emission interface
- IEventTransformer: Transform lineage to OpenLineage events
- ITransport: Send events to external systems
"""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Protocol, runtime_checkable
from uuid import uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.core.lineage import LineageService
from truthound_dashboard.db.models import LineageNode, LineageEdge, Source, OpenLineageWebhook
from truthound_dashboard.schemas.openlineage import (
    OpenLineageDataset,
    OpenLineageEvent,
    OpenLineageJob,
    OpenLineageRun,
    RunState,
    SchemaDatasetFacet,
    SchemaField,
    build_dataset_namespace,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Protocols for Extensibility
# =============================================================================


@runtime_checkable
class IEventTransformer(Protocol):
    """Protocol for transforming lineage to OpenLineage events."""

    def transform(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        job_namespace: str,
        job_name: str,
        include_schema: bool = True,
    ) -> list[OpenLineageEvent]:
        """Transform lineage graph to OpenLineage events.

        Args:
            nodes: List of lineage nodes.
            edges: List of lineage edges.
            job_namespace: Namespace for the job.
            job_name: Name of the job.
            include_schema: Whether to include schema facets.

        Returns:
            List of OpenLineage events.
        """
        ...


@runtime_checkable
class ITransport(Protocol):
    """Protocol for transporting OpenLineage events."""

    async def send(
        self,
        events: list[OpenLineageEvent],
        url: str,
        api_key: str | None = None,
        headers: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> tuple[int, int]:
        """Send events to external system.

        Args:
            events: List of events to send.
            url: Target URL.
            api_key: Optional API key.
            headers: Additional headers.
            timeout: Request timeout in seconds.

        Returns:
            Tuple of (sent_count, failed_count).
        """
        ...


# =============================================================================
# Event Transformer Implementation
# =============================================================================


class LineageToOpenLineageTransformer:
    """Transforms dashboard lineage graph to OpenLineage events.

    This transformer creates a complete run event that represents the data flow
    from source nodes through transformations to sink nodes.
    """

    def __init__(self, producer: str = "https://github.com/truthound/truthound-dashboard"):
        """Initialize transformer.

        Args:
            producer: Producer URI for OpenLineage events.
        """
        self.producer = producer

    def transform(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        job_namespace: str,
        job_name: str,
        include_schema: bool = True,
    ) -> list[OpenLineageEvent]:
        """Transform lineage graph to OpenLineage events.

        Creates events representing the complete data flow:
        1. START event with all inputs
        2. COMPLETE event with all outputs

        Args:
            nodes: List of lineage nodes.
            edges: List of lineage edges.
            job_namespace: Namespace for the job.
            job_name: Name of the job.
            include_schema: Whether to include schema facets.

        Returns:
            List of OpenLineage events.
        """
        if not nodes:
            return []

        events: list[OpenLineageEvent] = []
        run_id = str(uuid4())

        # Categorize nodes by type
        source_nodes = [n for n in nodes if n.get("node_type") == "source"]
        transform_nodes = [n for n in nodes if n.get("node_type") == "transform"]
        sink_nodes = [n for n in nodes if n.get("node_type") == "sink"]

        # Build edge map for dependency tracking
        edge_map = self._build_edge_map(edges)

        # Create input datasets from source nodes
        inputs = [
            self._node_to_dataset(node, include_schema)
            for node in source_nodes
        ]

        # Create output datasets from sink and transform nodes
        outputs = [
            self._node_to_dataset(node, include_schema)
            for node in sink_nodes + transform_nodes
        ]

        # Create job with facets
        job = OpenLineageJob(
            namespace=job_namespace,
            name=job_name,
            facets={
                "truthound": {
                    "_producer": self.producer,
                    "_schemaURL": "https://truthound.io/spec/facets/1-0-0/TruthoundJobFacet.json",
                    "total_nodes": len(nodes),
                    "total_edges": len(edges),
                    "source_count": len(source_nodes),
                    "transform_count": len(transform_nodes),
                    "sink_count": len(sink_nodes),
                }
            },
        )

        # Create run
        run = OpenLineageRun(
            run_id=run_id,
            facets={
                "processing_engine": {
                    "_producer": self.producer,
                    "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/ProcessingEngineRunFacet.json",
                    "version": "1.0.0",
                    "name": "truthound-dashboard",
                }
            },
        )

        # Create START event
        start_event = OpenLineageEvent(
            event_time=datetime.utcnow().isoformat() + "Z",
            event_type=RunState.START,
            producer=self.producer,
            run=run,
            job=job,
            inputs=inputs,
            outputs=[],  # No outputs at start
        )
        events.append(start_event)

        # Create COMPLETE event
        complete_event = OpenLineageEvent(
            event_time=datetime.utcnow().isoformat() + "Z",
            event_type=RunState.COMPLETE,
            producer=self.producer,
            run=run,
            job=job,
            inputs=inputs,
            outputs=outputs,
        )
        events.append(complete_event)

        return events

    def transform_per_node(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        job_namespace: str,
        include_schema: bool = True,
    ) -> list[OpenLineageEvent]:
        """Transform each node to a separate OpenLineage run.

        This creates finer-grained events where each transformation
        becomes its own job with explicit input/output relationships.

        Args:
            nodes: List of lineage nodes.
            edges: List of lineage edges.
            job_namespace: Namespace for jobs.
            include_schema: Whether to include schema facets.

        Returns:
            List of OpenLineage events (2 per transform node: START + COMPLETE).
        """
        events: list[OpenLineageEvent] = []

        # Build maps for lookups
        node_map = {n["id"]: n for n in nodes}
        incoming_edges = self._build_incoming_edge_map(edges)
        outgoing_edges = self._build_outgoing_edge_map(edges)

        # Process transform and sink nodes
        for node in nodes:
            if node.get("node_type") == "source":
                continue  # Sources don't have incoming edges

            node_id = node["id"]
            run_id = str(uuid4())

            # Find input datasets (nodes pointing to this node)
            input_node_ids = incoming_edges.get(node_id, [])
            inputs = [
                self._node_to_dataset(node_map[nid], include_schema)
                for nid in input_node_ids
                if nid in node_map
            ]

            # This node is the output
            outputs = [self._node_to_dataset(node, include_schema)]

            job_name = f"process_{node.get('name', node_id)}"
            job = OpenLineageJob(
                namespace=job_namespace,
                name=job_name,
                facets={
                    "truthound": {
                        "_producer": self.producer,
                        "_schemaURL": "https://truthound.io/spec/facets/1-0-0/TruthoundJobFacet.json",
                        "node_id": node_id,
                        "node_type": node.get("node_type"),
                    }
                },
            )

            run = OpenLineageRun(run_id=run_id)

            # START event
            events.append(
                OpenLineageEvent(
                    event_time=datetime.utcnow().isoformat() + "Z",
                    event_type=RunState.START,
                    producer=self.producer,
                    run=run,
                    job=job,
                    inputs=inputs,
                    outputs=[],
                )
            )

            # COMPLETE event
            events.append(
                OpenLineageEvent(
                    event_time=datetime.utcnow().isoformat() + "Z",
                    event_type=RunState.COMPLETE,
                    producer=self.producer,
                    run=run,
                    job=job,
                    inputs=inputs,
                    outputs=outputs,
                )
            )

        return events

    def _node_to_dataset(
        self,
        node: dict[str, Any],
        include_schema: bool,
    ) -> OpenLineageDataset:
        """Convert a lineage node to an OpenLineage dataset.

        Args:
            node: Lineage node dictionary.
            include_schema: Whether to include schema.

        Returns:
            OpenLineageDataset instance.
        """
        metadata = node.get("metadata") or {}
        source_type = metadata.get("source_type", "unknown")

        # Build namespace based on source type
        namespace = build_dataset_namespace(source_type, metadata.get("config"))

        facets: dict[str, Any] = {
            "truthound": {
                "_producer": self.producer,
                "_schemaURL": "https://truthound.io/spec/facets/1-0-0/TruthoundDatasetFacet.json",
                "node_id": node.get("id"),
                "node_type": node.get("node_type"),
                "source_id": node.get("source_id"),
            }
        }

        # Add schema facet if available
        if include_schema and metadata.get("schema_fields"):
            facets["schema"] = {
                "_producer": self.producer,
                "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/SchemaDatasetFacet.json",
                "fields": [
                    {"name": f.get("name"), "type": f.get("type", "string")}
                    for f in metadata["schema_fields"]
                ],
            }

        return OpenLineageDataset(
            namespace=namespace,
            name=node.get("name", "unknown"),
            facets=facets,
        )

    def _build_edge_map(
        self,
        edges: list[dict[str, Any]],
    ) -> dict[str, list[str]]:
        """Build map from source_node_id to target_node_ids."""
        edge_map: dict[str, list[str]] = {}
        for edge in edges:
            source_id = edge.get("source_node_id")
            target_id = edge.get("target_node_id")
            if source_id and target_id:
                if source_id not in edge_map:
                    edge_map[source_id] = []
                edge_map[source_id].append(target_id)
        return edge_map

    def _build_incoming_edge_map(
        self,
        edges: list[dict[str, Any]],
    ) -> dict[str, list[str]]:
        """Build map from target_node_id to source_node_ids."""
        edge_map: dict[str, list[str]] = {}
        for edge in edges:
            source_id = edge.get("source_node_id")
            target_id = edge.get("target_node_id")
            if source_id and target_id:
                if target_id not in edge_map:
                    edge_map[target_id] = []
                edge_map[target_id].append(source_id)
        return edge_map

    def _build_outgoing_edge_map(
        self,
        edges: list[dict[str, Any]],
    ) -> dict[str, list[str]]:
        """Build map from source_node_id to target_node_ids."""
        return self._build_edge_map(edges)


# =============================================================================
# Transport Implementation
# =============================================================================


class HttpTransport:
    """HTTP transport for sending OpenLineage events."""

    def __init__(self, client: httpx.AsyncClient | None = None):
        """Initialize transport.

        Args:
            client: Optional pre-configured httpx client.
        """
        self._client = client
        self._owns_client = client is None

    async def send(
        self,
        events: list[OpenLineageEvent],
        url: str,
        api_key: str | None = None,
        headers: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> tuple[int, int]:
        """Send events via HTTP POST.

        Args:
            events: List of events to send.
            url: Target URL.
            api_key: Optional API key.
            headers: Additional headers.
            timeout: Request timeout in seconds.

        Returns:
            Tuple of (sent_count, failed_count).
        """
        if not events:
            return 0, 0

        client = self._client or httpx.AsyncClient()
        sent_count = 0
        failed_count = 0

        try:
            request_headers = {
                "Content-Type": "application/json",
            }
            if api_key:
                request_headers["Authorization"] = f"Bearer {api_key}"
            if headers:
                request_headers.update(headers)

            for event in events:
                try:
                    response = await client.post(
                        url,
                        json=event.model_dump(by_alias=True),
                        headers=request_headers,
                        timeout=timeout,
                    )
                    if response.status_code in (200, 201, 202):
                        sent_count += 1
                    else:
                        logger.warning(
                            f"Failed to send event: {response.status_code} {response.text}"
                        )
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Error sending event: {e}")
                    failed_count += 1

        finally:
            if self._owns_client and client:
                await client.aclose()

        return sent_count, failed_count


class BatchHttpTransport:
    """Batched HTTP transport for efficient bulk sending."""

    def __init__(
        self,
        batch_size: int = 100,
        client: httpx.AsyncClient | None = None,
    ):
        """Initialize transport.

        Args:
            batch_size: Number of events per batch.
            client: Optional pre-configured httpx client.
        """
        self.batch_size = batch_size
        self._client = client
        self._owns_client = client is None

    async def send(
        self,
        events: list[OpenLineageEvent],
        url: str,
        api_key: str | None = None,
        headers: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> tuple[int, int]:
        """Send events in batches.

        Args:
            events: List of events to send.
            url: Target URL.
            api_key: Optional API key.
            headers: Additional headers.
            timeout: Request timeout in seconds.

        Returns:
            Tuple of (sent_count, failed_count).
        """
        if not events:
            return 0, 0

        client = self._client or httpx.AsyncClient()
        sent_count = 0
        failed_count = 0

        try:
            request_headers = {
                "Content-Type": "application/json",
            }
            if api_key:
                request_headers["Authorization"] = f"Bearer {api_key}"
            if headers:
                request_headers.update(headers)

            # Process in batches
            for i in range(0, len(events), self.batch_size):
                batch = events[i : i + self.batch_size]
                batch_payload = [e.model_dump(by_alias=True) for e in batch]

                try:
                    response = await client.post(
                        url,
                        json=batch_payload,
                        headers=request_headers,
                        timeout=timeout,
                    )
                    if response.status_code in (200, 201, 202):
                        sent_count += len(batch)
                    else:
                        logger.warning(
                            f"Failed to send batch: {response.status_code} {response.text}"
                        )
                        failed_count += len(batch)
                except Exception as e:
                    logger.error(f"Error sending batch: {e}")
                    failed_count += len(batch)

        finally:
            if self._owns_client and client:
                await client.aclose()

        return sent_count, failed_count


# =============================================================================
# OpenLineage Emitter Service
# =============================================================================


class OpenLineageEmitterService:
    """Service for emitting OpenLineage events from dashboard lineage.

    This service provides:
    - Export lineage graph as OpenLineage events (JSON)
    - Emit events to external OpenLineage consumers (Marquez, DataHub, etc.)
    - Support for granular (per-node) or aggregated (full-graph) export
    """

    def __init__(
        self,
        session: AsyncSession,
        transformer: LineageToOpenLineageTransformer | None = None,
        transport: HttpTransport | BatchHttpTransport | None = None,
    ):
        """Initialize service.

        Args:
            session: Database session.
            transformer: Optional custom transformer.
            transport: Optional custom transport.
        """
        self.session = session
        self.lineage_service = LineageService(session)
        self.transformer = transformer or LineageToOpenLineageTransformer()
        self.transport = transport or HttpTransport()

    async def export_as_openlineage(
        self,
        job_namespace: str = "truthound-dashboard",
        job_name: str = "lineage_export",
        source_id: str | None = None,
        include_schema: bool = True,
        granular: bool = False,
    ) -> dict[str, Any]:
        """Export lineage graph as OpenLineage events.

        Args:
            job_namespace: Namespace for the job.
            job_name: Name of the job.
            source_id: Optional source ID to filter.
            include_schema: Include schema in facets.
            granular: If True, create events per node.

        Returns:
            Dictionary with events and metadata.
        """
        # Get lineage graph
        graph = await self.lineage_service.get_graph(source_id=source_id)
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        # Transform to OpenLineage events
        if granular:
            events = self.transformer.transform_per_node(
                nodes=nodes,
                edges=edges,
                job_namespace=job_namespace,
                include_schema=include_schema,
            )
        else:
            events = self.transformer.transform(
                nodes=nodes,
                edges=edges,
                job_namespace=job_namespace,
                job_name=job_name,
                include_schema=include_schema,
            )

        # Count unique datasets
        dataset_names = set()
        for event in events:
            for ds in event.inputs:
                dataset_names.add(f"{ds.namespace}:{ds.name}")
            for ds in event.outputs:
                dataset_names.add(f"{ds.namespace}:{ds.name}")

        # Count unique jobs
        job_names = set()
        for event in events:
            job_names.add(f"{event.job.namespace}:{event.job.name}")

        return {
            "events": [e.model_dump(by_alias=True) for e in events],
            "total_events": len(events),
            "total_datasets": len(dataset_names),
            "total_jobs": len(job_names),
            "export_time": datetime.utcnow().isoformat() + "Z",
        }

    async def emit_to_endpoint(
        self,
        url: str,
        api_key: str | None = None,
        headers: dict[str, str] | None = None,
        job_namespace: str = "truthound-dashboard",
        job_name: str = "lineage_export",
        source_id: str | None = None,
        timeout: int = 30,
    ) -> dict[str, Any]:
        """Emit OpenLineage events to an external endpoint.

        Args:
            url: Target URL (e.g., Marquez API).
            api_key: Optional API key.
            headers: Additional headers.
            job_namespace: Namespace for the job.
            job_name: Name of the job.
            source_id: Optional source ID to filter.
            timeout: Request timeout.

        Returns:
            Result dictionary with success status.
        """
        try:
            # Export events
            export_result = await self.export_as_openlineage(
                job_namespace=job_namespace,
                job_name=job_name,
                source_id=source_id,
                include_schema=True,
            )

            # Convert back to OpenLineageEvent objects
            events = [
                OpenLineageEvent(**e)
                for e in export_result["events"]
            ]

            # Send via transport
            sent_count, failed_count = await self.transport.send(
                events=events,
                url=url,
                api_key=api_key,
                headers=headers,
                timeout=timeout,
            )

            return {
                "success": failed_count == 0,
                "events_sent": sent_count,
                "failed_events": failed_count,
                "error_message": None if failed_count == 0 else f"{failed_count} events failed to send",
            }

        except Exception as e:
            logger.exception("Failed to emit OpenLineage events")
            return {
                "success": False,
                "events_sent": 0,
                "failed_events": 0,
                "error_message": str(e),
            }

    def export_as_ndjson(
        self,
        events: list[dict[str, Any]],
    ) -> str:
        """Export events as newline-delimited JSON.

        Args:
            events: List of event dictionaries.

        Returns:
            NDJSON string.
        """
        return "\n".join(json.dumps(e) for e in events)


# =============================================================================
# Webhook Management Service
# =============================================================================


class OpenLineageWebhookService:
    """Service for managing OpenLineage webhook configurations.

    Provides CRUD operations for webhook configurations and
    testing webhook connectivity.
    """

    def __init__(self, session: AsyncSession):
        """Initialize service.

        Args:
            session: Database session.
        """
        self.session = session

    async def list_webhooks(self, active_only: bool = False) -> list[OpenLineageWebhook]:
        """List all configured webhooks.

        Args:
            active_only: If True, only return active webhooks.

        Returns:
            List of webhook configurations.
        """
        query = select(OpenLineageWebhook).order_by(OpenLineageWebhook.created_at.desc())
        if active_only:
            query = query.where(OpenLineageWebhook.is_active == True)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_webhook(self, webhook_id: str) -> OpenLineageWebhook | None:
        """Get a specific webhook by ID.

        Args:
            webhook_id: Webhook unique identifier.

        Returns:
            Webhook if found, None otherwise.
        """
        result = await self.session.execute(
            select(OpenLineageWebhook).where(OpenLineageWebhook.id == webhook_id)
        )
        return result.scalar_one_or_none()

    async def create_webhook(
        self,
        name: str,
        url: str,
        is_active: bool = True,
        headers: dict[str, str] | None = None,
        api_key: str | None = None,
        event_types: str = "all",
        batch_size: int = 100,
        timeout_seconds: int = 30,
    ) -> OpenLineageWebhook:
        """Create a new webhook configuration.

        Args:
            name: Human-readable name.
            url: Target URL.
            is_active: Whether the webhook is enabled.
            headers: Custom headers.
            api_key: API key for authentication.
            event_types: Types of events to emit.
            batch_size: Events per batch.
            timeout_seconds: Request timeout.

        Returns:
            Created webhook.
        """
        webhook = OpenLineageWebhook(
            name=name,
            url=url,
            is_active=is_active,
            headers_json=headers or {},
            api_key=api_key,
            event_types=event_types,
            batch_size=batch_size,
            timeout_seconds=timeout_seconds,
        )
        self.session.add(webhook)
        await self.session.commit()
        await self.session.refresh(webhook)
        return webhook

    async def update_webhook(
        self,
        webhook_id: str,
        name: str | None = None,
        url: str | None = None,
        is_active: bool | None = None,
        headers: dict[str, str] | None = None,
        api_key: str | None = None,
        event_types: str | None = None,
        batch_size: int | None = None,
        timeout_seconds: int | None = None,
    ) -> OpenLineageWebhook | None:
        """Update an existing webhook.

        Args:
            webhook_id: Webhook to update.
            name: New name (if provided).
            url: New URL (if provided).
            is_active: New active status (if provided).
            headers: New headers (if provided).
            api_key: New API key (if provided).
            event_types: New event types (if provided).
            batch_size: New batch size (if provided).
            timeout_seconds: New timeout (if provided).

        Returns:
            Updated webhook or None if not found.
        """
        webhook = await self.get_webhook(webhook_id)
        if not webhook:
            return None

        if name is not None:
            webhook.name = name
        if url is not None:
            webhook.url = url
        if is_active is not None:
            webhook.is_active = is_active
        if headers is not None:
            webhook.headers_json = headers
        if api_key is not None:
            webhook.api_key = api_key
        if event_types is not None:
            webhook.event_types = event_types
        if batch_size is not None:
            webhook.batch_size = batch_size
        if timeout_seconds is not None:
            webhook.timeout_seconds = timeout_seconds

        await self.session.commit()
        await self.session.refresh(webhook)
        return webhook

    async def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook configuration.

        Args:
            webhook_id: Webhook to delete.

        Returns:
            True if deleted, False if not found.
        """
        webhook = await self.get_webhook(webhook_id)
        if not webhook:
            return False

        await self.session.delete(webhook)
        await self.session.commit()
        return True

    async def test_webhook(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        api_key: str | None = None,
        timeout_seconds: int = 10,
    ) -> dict[str, Any]:
        """Test webhook connectivity.

        Sends a test OpenLineage event to verify the endpoint is reachable
        and accepts events.

        Args:
            url: URL to test.
            headers: Custom headers.
            api_key: API key for authentication.
            timeout_seconds: Request timeout.

        Returns:
            Test result with success status and details.
        """
        # Create a minimal test event
        test_event = {
            "eventTime": datetime.utcnow().isoformat() + "Z",
            "eventType": "START",
            "producer": "https://github.com/truthound/truthound-dashboard",
            "schemaURL": "https://openlineage.io/spec/1-0-5/OpenLineage.json#/definitions/RunEvent",
            "run": {"runId": str(uuid4()), "facets": {}},
            "job": {
                "namespace": "truthound-dashboard",
                "name": "webhook_test",
                "facets": {},
            },
            "inputs": [],
            "outputs": [],
        }

        request_headers = {
            "Content-Type": "application/json",
            "X-OpenLineage-Test": "true",
        }
        if api_key:
            request_headers["Authorization"] = f"Bearer {api_key}"
        if headers:
            request_headers.update(headers)

        start_time = time.time()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=test_event,
                    headers=request_headers,
                    timeout=timeout_seconds,
                )

            elapsed_ms = int((time.time() - start_time) * 1000)

            # Truncate response body
            response_body = response.text[:500] if response.text else None

            if response.status_code in (200, 201, 202, 204):
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "response_time_ms": elapsed_ms,
                    "error_message": None,
                    "response_body": response_body,
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "response_time_ms": elapsed_ms,
                    "error_message": f"HTTP {response.status_code}: {response.reason_phrase}",
                    "response_body": response_body,
                }

        except httpx.TimeoutException:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "status_code": None,
                "response_time_ms": elapsed_ms,
                "error_message": f"Request timed out after {timeout_seconds} seconds",
                "response_body": None,
            }
        except httpx.ConnectError as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "status_code": None,
                "response_time_ms": elapsed_ms,
                "error_message": f"Connection failed: {str(e)}",
                "response_body": None,
            }
        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.exception("Webhook test failed")
            return {
                "success": False,
                "status_code": None,
                "response_time_ms": elapsed_ms,
                "error_message": str(e),
                "response_body": None,
            }

    async def record_emission(
        self,
        webhook_id: str,
        success: bool,
        error: str | None = None,
    ) -> None:
        """Record an emission attempt for a webhook.

        Args:
            webhook_id: Webhook ID.
            success: Whether the emission was successful.
            error: Error message if failed.
        """
        webhook = await self.get_webhook(webhook_id)
        if webhook:
            if success:
                webhook.record_success()
            else:
                webhook.record_failure(error or "Unknown error")
            await self.session.commit()
