/**
 * Lineage API handlers
 *
 * Handles all lineage-related endpoints including:
 * - Graph retrieval
 * - Node CRUD
 * - Edge CRUD
 * - Impact analysis
 * - Auto-discovery
 * - Position updates
 */

import { http, HttpResponse, delay } from 'msw'
import {
  getLineageStore,
  createLineageNode,
  createLineageEdge,
  addNodeToStore,
  removeNodeFromStore,
  addEdgeToStore,
  removeEdgeFromStore,
  createImpactAnalysis,
  createAutoDiscoverResponse,
  createId,
  createTimestamp,
} from '../factories'
import type {
  LineageNodeCreate,
  LineageNodeUpdate,
  LineageEdgeCreate,
  LineageNodeType,
  LineageEdgeType,
} from '@/api/client'

const API_BASE = '/api/v1'

export const lineageHandlers = [
  // Get full lineage graph
  http.get(`${API_BASE}/lineage`, async () => {
    await delay(300)

    const graph = getLineageStore()

    return HttpResponse.json(graph)
  }),

  // Get lineage for a specific source
  http.get(`${API_BASE}/lineage/sources/:sourceId`, async ({ params }) => {
    await delay(250)

    const sourceId = params.sourceId as string
    // Note: depth parameter is accepted but not implemented in mock (returns all connected nodes)

    const graph = getLineageStore()

    // Find nodes related to this source
    const sourceNode = graph.nodes.find(n => n.source_id === sourceId)

    if (!sourceNode) {
      // Return empty graph if no lineage for this source
      return HttpResponse.json({
        nodes: [],
        edges: [],
        total_nodes: 0,
        total_edges: 0,
      })
    }

    // Get connected nodes within depth (simplified - just return all for now)
    const relatedNodeIds = new Set<string>([sourceNode.id])

    // Find directly connected nodes
    for (const edge of graph.edges) {
      if (edge.source_node_id === sourceNode.id) {
        relatedNodeIds.add(edge.target_node_id)
      }
      if (edge.target_node_id === sourceNode.id) {
        relatedNodeIds.add(edge.source_node_id)
      }
    }

    const nodes = graph.nodes.filter(n => relatedNodeIds.has(n.id))
    const edges = graph.edges.filter(
      e => relatedNodeIds.has(e.source_node_id) && relatedNodeIds.has(e.target_node_id)
    )

    return HttpResponse.json({
      nodes,
      edges,
      total_nodes: nodes.length,
      total_edges: edges.length,
    })
  }),

  // Create a lineage node
  http.post(`${API_BASE}/lineage/nodes`, async ({ request }) => {
    await delay(200)

    let body: LineageNodeCreate
    try {
      body = await request.json() as LineageNodeCreate
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    if (!body.name || !body.node_type) {
      return HttpResponse.json(
        { detail: 'name and node_type are required' },
        { status: 400 }
      )
    }

    const node = createLineageNode({
      id: createId(),
      name: body.name,
      node_type: body.node_type as LineageNodeType,
      source_id: body.source_id,
      metadata: body.metadata,
      position_x: body.position_x,
      position_y: body.position_y,
    })

    addNodeToStore(node)

    return HttpResponse.json(node, { status: 201 })
  }),

  // Get a lineage node by ID
  http.get(`${API_BASE}/lineage/nodes/:nodeId`, async ({ params }) => {
    await delay(100)

    const nodeId = params.nodeId as string
    const graph = getLineageStore()
    const node = graph.nodes.find(n => n.id === nodeId)

    if (!node) {
      return HttpResponse.json(
        { detail: 'Node not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(node)
  }),

  // Update a lineage node
  http.put(`${API_BASE}/lineage/nodes/:nodeId`, async ({ params, request }) => {
    await delay(150)

    const nodeId = params.nodeId as string
    const graph = getLineageStore()
    const nodeIndex = graph.nodes.findIndex(n => n.id === nodeId)

    if (nodeIndex === -1) {
      return HttpResponse.json(
        { detail: 'Node not found' },
        { status: 404 }
      )
    }

    let body: LineageNodeUpdate
    try {
      body = await request.json() as LineageNodeUpdate
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    // Update node
    const node = graph.nodes[nodeIndex]
    if (body.name !== undefined) node.name = body.name
    if (body.node_type !== undefined) node.node_type = body.node_type as LineageNodeType
    if (body.source_id !== undefined) node.source_id = body.source_id
    if (body.metadata !== undefined) node.metadata = body.metadata
    if (body.position_x !== undefined) node.position_x = body.position_x
    if (body.position_y !== undefined) node.position_y = body.position_y
    node.updated_at = createTimestamp(0)

    return HttpResponse.json(node)
  }),

  // Delete a lineage node
  http.delete(`${API_BASE}/lineage/nodes/:nodeId`, async ({ params }) => {
    await delay(150)

    const nodeId = params.nodeId as string
    const removed = removeNodeFromStore(nodeId)

    if (!removed) {
      return HttpResponse.json(
        { detail: 'Node not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json({ message: 'Node deleted successfully' })
  }),

  // Create a lineage edge
  http.post(`${API_BASE}/lineage/edges`, async ({ request }) => {
    await delay(200)

    let body: LineageEdgeCreate
    try {
      body = await request.json() as LineageEdgeCreate
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    if (!body.source_node_id || !body.target_node_id || !body.edge_type) {
      return HttpResponse.json(
        { detail: 'source_node_id, target_node_id, and edge_type are required' },
        { status: 400 }
      )
    }

    // Verify nodes exist
    const graph = getLineageStore()
    const sourceExists = graph.nodes.some(n => n.id === body.source_node_id)
    const targetExists = graph.nodes.some(n => n.id === body.target_node_id)

    if (!sourceExists || !targetExists) {
      return HttpResponse.json(
        { detail: 'Source or target node not found' },
        { status: 400 }
      )
    }

    const edge = createLineageEdge({
      id: createId(),
      source_node_id: body.source_node_id,
      target_node_id: body.target_node_id,
      edge_type: body.edge_type as LineageEdgeType,
      metadata: body.metadata,
    })

    addEdgeToStore(edge)

    return HttpResponse.json(edge, { status: 201 })
  }),

  // Delete a lineage edge
  http.delete(`${API_BASE}/lineage/edges/:edgeId`, async ({ params }) => {
    await delay(150)

    const edgeId = params.edgeId as string
    const removed = removeEdgeFromStore(edgeId)

    if (!removed) {
      return HttpResponse.json(
        { detail: 'Edge not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json({ message: 'Edge deleted successfully' })
  }),

  // Get impact analysis for a node
  http.get(`${API_BASE}/lineage/nodes/:nodeId/impact`, async ({ params }) => {
    await delay(400)

    const nodeId = params.nodeId as string
    // Note: depth parameter is accepted but not implemented in mock

    const graph = getLineageStore()
    const node = graph.nodes.find(n => n.id === nodeId)

    if (!node) {
      return HttpResponse.json(
        { detail: 'Node not found' },
        { status: 404 }
      )
    }

    const impact = createImpactAnalysis(nodeId, graph)

    return HttpResponse.json(impact)
  }),

  // Auto-discover lineage from database
  http.post(`${API_BASE}/lineage/auto-discover`, async ({ request }) => {
    await delay(2000) // Simulate discovery time

    let body: { source_ids?: string[]; include_fk?: boolean } = {}
    try {
      body = await request.json() as typeof body
    } catch {
      // Empty body is OK
    }

    const result = createAutoDiscoverResponse(body.source_ids)

    // Add discovered nodes and edges to store
    const store = getLineageStore()
    for (const node of result.nodes) {
      if (!store.nodes.some(n => n.id === node.id)) {
        addNodeToStore(node)
      }
    }
    for (const edge of result.edges) {
      if (!store.edges.some(e => e.id === edge.id)) {
        addEdgeToStore(edge)
      }
    }

    return HttpResponse.json(result)
  }),

  // Update node positions (batch)
  http.post(`${API_BASE}/lineage/positions`, async ({ request }) => {
    await delay(200)

    let body: { updates: Array<{ node_id: string; position_x: number; position_y: number }> }
    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    if (!body.updates || !Array.isArray(body.updates)) {
      return HttpResponse.json(
        { detail: 'updates array is required' },
        { status: 400 }
      )
    }

    const graph = getLineageStore()
    let updated = 0

    for (const update of body.updates) {
      const node = graph.nodes.find(n => n.id === update.node_id)
      if (node) {
        node.position_x = update.position_x
        node.position_y = update.position_y
        node.updated_at = createTimestamp(0)
        updated++
      }
    }

    return HttpResponse.json({
      updated,
      message: `Updated positions for ${updated} nodes`,
    })
  }),

  // ============================================================================
  // Anomaly Integration Endpoints
  // ============================================================================

  // Get lineage graph with anomaly overlay
  http.get(`${API_BASE}/lineage/graph/with-anomalies`, async ({ request }) => {
    await delay(400)

    const url = new URL(request.url)
    const sourceId = url.searchParams.get('source_id')

    const graph = getLineageStore()

    // Add anomaly status to each node
    const nodesWithAnomalies = graph.nodes.map(node => {
      // Generate mock anomaly status based on node characteristics
      let anomalyStatus = {
        status: 'unknown' as 'unknown' | 'clean' | 'low' | 'medium' | 'high',
        anomaly_rate: null as number | null,
        anomaly_count: null as number | null,
        last_detection_at: null as string | null,
        algorithm: null as string | null,
      }

      // Only add anomaly status for nodes with sources
      if (node.source_id) {
        // Generate semi-random but consistent anomaly status based on node name hash
        const hash = node.name.split('').reduce((a, b) => {
          a = ((a << 5) - a) + b.charCodeAt(0)
          return a & a
        }, 0)
        const statusIndex = Math.abs(hash) % 10

        if (statusIndex < 3) {
          anomalyStatus = {
            status: 'clean',
            anomaly_rate: 0,
            anomaly_count: 0,
            last_detection_at: createTimestamp(-24 * 60),
            algorithm: 'isolation_forest',
          }
        } else if (statusIndex < 5) {
          anomalyStatus = {
            status: 'low',
            anomaly_rate: 0.02 + (Math.abs(hash) % 30) / 1000,
            anomaly_count: Math.abs(hash) % 50 + 1,
            last_detection_at: createTimestamp(-12 * 60),
            algorithm: 'local_outlier_factor',
          }
        } else if (statusIndex < 7) {
          anomalyStatus = {
            status: 'medium',
            anomaly_rate: 0.07 + (Math.abs(hash) % 50) / 1000,
            anomaly_count: Math.abs(hash) % 200 + 50,
            last_detection_at: createTimestamp(-6 * 60),
            algorithm: 'isolation_forest',
          }
        } else if (statusIndex < 9) {
          anomalyStatus = {
            status: 'high',
            anomaly_rate: 0.18 + (Math.abs(hash) % 100) / 1000,
            anomaly_count: Math.abs(hash) % 500 + 200,
            last_detection_at: createTimestamp(-2 * 60),
            algorithm: 'one_class_svm',
          }
        }
        // statusIndex >= 9: remains 'unknown'
      }

      return {
        ...node,
        anomaly_status: anomalyStatus,
      }
    })

    // Filter by source_id if provided
    let filteredNodes = nodesWithAnomalies
    let filteredEdges = graph.edges

    if (sourceId) {
      const sourceNode = nodesWithAnomalies.find(n => n.source_id === sourceId)
      if (sourceNode) {
        const relatedIds = new Set<string>([sourceNode.id])
        for (const edge of graph.edges) {
          if (edge.source_node_id === sourceNode.id) relatedIds.add(edge.target_node_id)
          if (edge.target_node_id === sourceNode.id) relatedIds.add(edge.source_node_id)
        }
        filteredNodes = nodesWithAnomalies.filter(n => relatedIds.has(n.id))
        filteredEdges = graph.edges.filter(
          e => relatedIds.has(e.source_node_id) && relatedIds.has(e.target_node_id)
        )
      }
    }

    return HttpResponse.json({
      nodes: filteredNodes,
      edges: filteredEdges,
      total_nodes: filteredNodes.length,
      total_edges: filteredEdges.length,
    })
  }),

  // Get anomaly impact analysis for a node
  http.get(`${API_BASE}/lineage/nodes/:nodeId/anomaly-impact`, async ({ params, request }) => {
    await delay(500)

    const nodeId = params.nodeId as string
    const url = new URL(request.url)
    const maxDepth = parseInt(url.searchParams.get('max_depth') || '10', 10)

    const graph = getLineageStore()
    const node = graph.nodes.find(n => n.id === nodeId)

    if (!node) {
      return HttpResponse.json({ detail: 'Node not found' }, { status: 404 })
    }

    if (!node.source_id) {
      return HttpResponse.json(
        { detail: 'Node is not linked to a data source. Anomaly impact analysis requires a linked source.' },
        { status: 400 }
      )
    }

    // Generate source anomaly status
    const hash = node.name.split('').reduce((a, b) => {
      a = ((a << 5) - a) + b.charCodeAt(0)
      return a & a
    }, 0)
    const statusIndex = Math.abs(hash) % 10

    let sourceAnomalyStatus = null
    if (statusIndex >= 5) {
      sourceAnomalyStatus = {
        status: statusIndex < 7 ? 'medium' : 'high',
        anomaly_rate: statusIndex < 7 ? 0.08 + (Math.abs(hash) % 50) / 1000 : 0.20 + (Math.abs(hash) % 100) / 1000,
        anomaly_count: statusIndex < 7 ? Math.abs(hash) % 200 + 50 : Math.abs(hash) % 500 + 200,
        last_detection_at: createTimestamp(-4 * 60),
        algorithm: 'isolation_forest',
      }
    }

    // Find downstream nodes
    const downstreamIds = new Set<string>()
    const visited = new Set<string>([nodeId])
    const queue = [nodeId]
    let depth = 0

    while (queue.length > 0 && depth < maxDepth) {
      const currentSize = queue.length
      for (let i = 0; i < currentSize; i++) {
        const currentId = queue.shift()!
        for (const edge of graph.edges) {
          if (edge.source_node_id === currentId && !visited.has(edge.target_node_id)) {
            visited.add(edge.target_node_id)
            downstreamIds.add(edge.target_node_id)
            queue.push(edge.target_node_id)
          }
        }
      }
      depth++
    }

    // Build impacted nodes list with severity
    const impactedNodes = Array.from(downstreamIds).map(id => {
      const downstreamNode = graph.nodes.find(n => n.id === id)!
      const nodeHash = downstreamNode.name.split('').reduce((a, b) => {
        a = ((a << 5) - a) + b.charCodeAt(0)
        return a & a
      }, 0)

      // Calculate impact severity based on source anomaly and distance
      let impactSeverity = 'unknown'
      if (sourceAnomalyStatus) {
        if (sourceAnomalyStatus.status === 'high') {
          impactSeverity = Math.abs(nodeHash) % 3 === 0 ? 'critical' : 'high'
        } else if (sourceAnomalyStatus.status === 'medium') {
          impactSeverity = Math.abs(nodeHash) % 2 === 0 ? 'high' : 'medium'
        } else {
          impactSeverity = 'low'
        }
      }

      return {
        id,
        name: downstreamNode.name,
        node_type: downstreamNode.node_type,
        source_id: downstreamNode.source_id,
        anomaly_status: downstreamNode.source_id ? {
          status: Math.abs(nodeHash) % 4 === 0 ? 'medium' : 'clean',
          anomaly_rate: Math.abs(nodeHash) % 4 === 0 ? 0.06 : 0,
          anomaly_count: Math.abs(nodeHash) % 4 === 0 ? 30 : 0,
          last_detection_at: createTimestamp(-8 * 60),
          algorithm: 'local_outlier_factor',
        } : null,
        impact_severity: impactSeverity,
      }
    })

    // Build propagation path
    const propagationPath = graph.edges
      .filter(e =>
        (e.source_node_id === nodeId || downstreamIds.has(e.source_node_id)) &&
        downstreamIds.has(e.target_node_id)
      )
      .map(e => ({
        id: e.id,
        source_node_id: e.source_node_id,
        target_node_id: e.target_node_id,
        edge_type: e.edge_type,
      }))

    // Calculate overall severity
    let overallSeverity = 'unknown'
    if (sourceAnomalyStatus) {
      const criticalCount = impactedNodes.filter(n => n.impact_severity === 'critical').length
      const highCount = impactedNodes.filter(n => n.impact_severity === 'high').length
      const mediumCount = impactedNodes.filter(n => n.impact_severity === 'medium').length

      if (criticalCount > 0 || (highCount >= 3 && sourceAnomalyStatus.status === 'high')) {
        overallSeverity = 'critical'
      } else if (highCount > 0) {
        overallSeverity = 'high'
      } else if (mediumCount >= 3 || (mediumCount > 0 && sourceAnomalyStatus.status === 'medium')) {
        overallSeverity = 'medium'
      } else if (impactedNodes.length > 0) {
        overallSeverity = 'low'
      } else {
        overallSeverity = sourceAnomalyStatus.status
      }
    } else {
      overallSeverity = 'none'
    }

    return HttpResponse.json({
      source_node_id: nodeId,
      source_node_name: node.name,
      source_id: node.source_id,
      source_anomaly_status: sourceAnomalyStatus,
      impacted_nodes: impactedNodes,
      impacted_count: impactedNodes.length,
      overall_severity: overallSeverity,
      propagation_path: propagationPath,
    })
  }),

  // ============================================================================
  // OpenLineage Export Endpoints
  // ============================================================================

  // Export lineage as OpenLineage events
  http.post(`${API_BASE}/lineage/openlineage/export`, async ({ request }) => {
    await delay(500)

    let body: {
      job_namespace?: string
      job_name?: string
      source_id?: string
      include_schema?: boolean
    } = {}
    try {
      body = await request.json() as typeof body
    } catch {
      // Empty body is OK
    }

    const graph = getLineageStore()
    const jobNamespace = body.job_namespace || 'truthound-dashboard'
    const jobName = body.job_name || 'lineage_export'
    const runId = createId()
    const eventTime = new Date().toISOString()

    // Filter nodes by source_id if provided
    let nodes = graph.nodes
    if (body.source_id) {
      const sourceNode = nodes.find(n => n.source_id === body.source_id)
      if (sourceNode) {
        const relatedIds = new Set<string>([sourceNode.id])
        for (const edge of graph.edges) {
          if (edge.source_node_id === sourceNode.id) relatedIds.add(edge.target_node_id)
          if (edge.target_node_id === sourceNode.id) relatedIds.add(edge.source_node_id)
        }
        nodes = nodes.filter(n => relatedIds.has(n.id))
      }
    }

    // Build datasets from nodes
    const inputs = nodes
      .filter(n => n.node_type === 'source')
      .map(n => ({
        namespace: `${n.metadata?.source_type || 'unknown'}://truthound`,
        name: n.name,
        facets: {
          truthound: {
            _producer: 'truthound-dashboard',
            node_id: n.id,
            node_type: n.node_type,
            source_id: n.source_id,
          },
          ...(body.include_schema !== false && n.metadata?.schema_fields
            ? {
                schema: {
                  _producer: 'truthound-dashboard',
                  fields: n.metadata.schema_fields,
                },
              }
            : {}),
        },
      }))

    const outputs = nodes
      .filter(n => n.node_type === 'transform' || n.node_type === 'sink')
      .map(n => ({
        namespace: `${n.metadata?.source_type || 'transform'}://truthound`,
        name: n.name,
        facets: {
          truthound: {
            _producer: 'truthound-dashboard',
            node_id: n.id,
            node_type: n.node_type,
          },
        },
      }))

    // Create START and COMPLETE events
    const events = [
      {
        event_time: eventTime,
        eventType: 'START',
        producer: 'https://github.com/truthound/truthound-dashboard',
        schemaURL: 'https://openlineage.io/spec/1-0-5/OpenLineage.json#/definitions/RunEvent',
        run: { run_id: runId, facets: {} },
        job: {
          namespace: jobNamespace,
          name: jobName,
          facets: {
            truthound: {
              _producer: 'truthound-dashboard',
              total_nodes: nodes.length,
              total_edges: graph.edges.length,
            },
          },
        },
        inputs,
        outputs: [],
      },
      {
        event_time: new Date(Date.now() + 1000).toISOString(),
        eventType: 'COMPLETE',
        producer: 'https://github.com/truthound/truthound-dashboard',
        schemaURL: 'https://openlineage.io/spec/1-0-5/OpenLineage.json#/definitions/RunEvent',
        run: { run_id: runId, facets: {} },
        job: {
          namespace: jobNamespace,
          name: jobName,
          facets: {},
        },
        inputs,
        outputs,
      },
    ]

    // Count unique datasets
    const datasetNames = new Set([
      ...inputs.map(d => `${d.namespace}:${d.name}`),
      ...outputs.map(d => `${d.namespace}:${d.name}`),
    ])

    return HttpResponse.json({
      events,
      total_events: events.length,
      total_datasets: datasetNames.size,
      total_jobs: 1,
      export_time: eventTime,
    })
  }),

  // Export lineage as granular OpenLineage events
  http.post(`${API_BASE}/lineage/openlineage/export/granular`, async ({ request }) => {
    await delay(600)

    let body: {
      job_namespace?: string
      source_id?: string
      include_schema?: boolean
    } = {}
    try {
      body = await request.json() as typeof body
    } catch {
      // Empty body is OK
    }

    const graph = getLineageStore()
    const jobNamespace = body.job_namespace || 'truthound-dashboard'
    const events: unknown[] = []

    // Build edge map for dependencies
    const incomingEdges: Record<string, string[]> = {}
    for (const edge of graph.edges) {
      if (!incomingEdges[edge.target_node_id]) {
        incomingEdges[edge.target_node_id] = []
      }
      incomingEdges[edge.target_node_id].push(edge.source_node_id)
    }

    // Create events for each non-source node
    const nodeMap: Record<string, typeof graph.nodes[0]> = {}
    for (const node of graph.nodes) {
      nodeMap[node.id] = node
    }

    for (const node of graph.nodes) {
      if (node.node_type === 'source') continue

      const runId = createId()
      const eventTime = new Date().toISOString()

      // Get input nodes
      const inputNodeIds = incomingEdges[node.id] || []
      const inputs = inputNodeIds
        .filter(id => nodeMap[id])
        .map(id => {
          const n = nodeMap[id]
          return {
            namespace: `${n.metadata?.source_type || 'unknown'}://truthound`,
            name: n.name,
            facets: { truthound: { node_id: n.id } },
          }
        })

      const output = {
        namespace: `${node.metadata?.source_type || 'transform'}://truthound`,
        name: node.name,
        facets: { truthound: { node_id: node.id, node_type: node.node_type } },
      }

      events.push({
        event_time: eventTime,
        eventType: 'START',
        producer: 'https://github.com/truthound/truthound-dashboard',
        schemaURL: 'https://openlineage.io/spec/1-0-5/OpenLineage.json#/definitions/RunEvent',
        run: { run_id: runId, facets: {} },
        job: {
          namespace: jobNamespace,
          name: `process_${node.name}`,
          facets: { truthound: { node_id: node.id } },
        },
        inputs,
        outputs: [],
      })

      events.push({
        event_time: new Date(Date.now() + 100).toISOString(),
        eventType: 'COMPLETE',
        producer: 'https://github.com/truthound/truthound-dashboard',
        schemaURL: 'https://openlineage.io/spec/1-0-5/OpenLineage.json#/definitions/RunEvent',
        run: { run_id: runId, facets: {} },
        job: {
          namespace: jobNamespace,
          name: `process_${node.name}`,
          facets: {},
        },
        inputs,
        outputs: [output],
      })
    }

    // Count unique datasets and jobs
    const datasetNames = new Set<string>()
    const jobNames = new Set<string>()
    for (const event of events as { inputs: { namespace: string; name: string }[]; outputs: { namespace: string; name: string }[]; job: { name: string } }[]) {
      for (const d of event.inputs) datasetNames.add(`${d.namespace}:${d.name}`)
      for (const d of event.outputs) datasetNames.add(`${d.namespace}:${d.name}`)
      jobNames.add(event.job.name)
    }

    return HttpResponse.json({
      events,
      total_events: events.length,
      total_datasets: datasetNames.size,
      total_jobs: jobNames.size,
      export_time: new Date().toISOString(),
    })
  }),

  // Emit OpenLineage events to external endpoint
  http.post(`${API_BASE}/lineage/openlineage/emit`, async ({ request }) => {
    await delay(1000)

    let body: {
      webhook: {
        url: string
        api_key?: string
        batch_size?: number
      }
      source_id?: string
      job_namespace?: string
      job_name?: string
    }
    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    if (!body.webhook?.url) {
      return HttpResponse.json(
        { detail: 'webhook.url is required' },
        { status: 400 }
      )
    }

    // Mock successful emission
    void getLineageStore()
    const eventCount = 2 // START + COMPLETE

    // Simulate potential partial failure
    const failureRate = 0
    const failedEvents = Math.floor(eventCount * failureRate)
    const sentEvents = eventCount - failedEvents

    return HttpResponse.json({
      success: failedEvents === 0,
      events_sent: sentEvents,
      failed_events: failedEvents,
      error_message: failedEvents > 0 ? `${failedEvents} events failed to send` : null,
    })
  }),

  // Get OpenLineage specification info
  http.get(`${API_BASE}/lineage/openlineage/spec`, async () => {
    await delay(100)

    return HttpResponse.json({
      spec_version: '1.0.5',
      producer: 'https://github.com/truthound/truthound-dashboard',
      supported_facets: {
        dataset: [
          'schema',
          'dataQualityMetrics',
          'dataQualityAssertions',
          'documentation',
          'ownership',
          'columnLineage',
          'lifecycleStateChange',
        ],
        job: ['sourceCode', 'sql', 'documentation'],
        run: ['errorMessage', 'parent', 'nominalTime', 'processingEngine'],
      },
      supported_event_types: ['START', 'RUNNING', 'COMPLETE', 'FAIL', 'ABORT'],
      export_formats: ['json', 'ndjson'],
      documentation_url: 'https://openlineage.io/docs/',
    })
  }),

  // ============================================================================
  // OpenLineage Webhook Endpoints
  // ============================================================================

  // In-memory webhook store
  ...(() => {
    interface Webhook {
      id: string
      name: string
      url: string
      is_active: boolean
      headers: Record<string, string>
      event_types: 'job' | 'dataset' | 'all'
      batch_size: number
      timeout_seconds: number
      last_sent_at: string | null
      success_count: number
      failure_count: number
      last_error: string | null
      created_at: string
      updated_at: string | null
    }

    const webhooksStore: Webhook[] = []

    return [
      // List webhooks
      http.get(`${API_BASE}/lineage/openlineage/webhooks`, async ({ request }) => {
        await delay(200)

        const url = new URL(request.url)
        const activeOnly = url.searchParams.get('active_only') === 'true'

        const webhooks = activeOnly
          ? webhooksStore.filter(w => w.is_active)
          : webhooksStore

        return HttpResponse.json({
          data: webhooks,
          total: webhooks.length,
        })
      }),

      // Get webhook by ID
      http.get(`${API_BASE}/lineage/openlineage/webhooks/:webhookId`, async ({ params }) => {
        await delay(100)

        const webhook = webhooksStore.find(w => w.id === params.webhookId)
        if (!webhook) {
          return HttpResponse.json({ detail: 'Webhook not found' }, { status: 404 })
        }

        return HttpResponse.json(webhook)
      }),

      // Create webhook
      http.post(`${API_BASE}/lineage/openlineage/webhooks`, async ({ request }) => {
        await delay(300)

        let body: {
          name: string
          url: string
          is_active?: boolean
          headers?: Record<string, string>
          api_key?: string
          event_types?: 'job' | 'dataset' | 'all'
          batch_size?: number
          timeout_seconds?: number
        }
        try {
          body = await request.json() as typeof body
        } catch {
          return HttpResponse.json({ detail: 'Invalid JSON' }, { status: 400 })
        }

        if (!body.name || !body.url) {
          return HttpResponse.json({ detail: 'name and url are required' }, { status: 400 })
        }

        const webhook: Webhook = {
          id: createId(),
          name: body.name,
          url: body.url,
          is_active: body.is_active ?? true,
          headers: body.headers ?? {},
          event_types: body.event_types ?? 'all',
          batch_size: body.batch_size ?? 100,
          timeout_seconds: body.timeout_seconds ?? 30,
          last_sent_at: null,
          success_count: 0,
          failure_count: 0,
          last_error: null,
          created_at: createTimestamp(0),
          updated_at: null,
        }

        webhooksStore.push(webhook)

        return HttpResponse.json(webhook, { status: 201 })
      }),

      // Update webhook
      http.put(`${API_BASE}/lineage/openlineage/webhooks/:webhookId`, async ({ params, request }) => {
        await delay(200)

        const webhookIndex = webhooksStore.findIndex(w => w.id === params.webhookId)
        if (webhookIndex === -1) {
          return HttpResponse.json({ detail: 'Webhook not found' }, { status: 404 })
        }

        let body: {
          name?: string
          url?: string
          is_active?: boolean
          headers?: Record<string, string>
          api_key?: string
          event_types?: 'job' | 'dataset' | 'all'
          batch_size?: number
          timeout_seconds?: number
        }
        try {
          body = await request.json() as typeof body
        } catch {
          return HttpResponse.json({ detail: 'Invalid JSON' }, { status: 400 })
        }

        const webhook = webhooksStore[webhookIndex]
        if (body.name !== undefined) webhook.name = body.name
        if (body.url !== undefined) webhook.url = body.url
        if (body.is_active !== undefined) webhook.is_active = body.is_active
        if (body.headers !== undefined) webhook.headers = body.headers
        if (body.event_types !== undefined) webhook.event_types = body.event_types
        if (body.batch_size !== undefined) webhook.batch_size = body.batch_size
        if (body.timeout_seconds !== undefined) webhook.timeout_seconds = body.timeout_seconds
        webhook.updated_at = createTimestamp(0)

        return HttpResponse.json(webhook)
      }),

      // Delete webhook
      http.delete(`${API_BASE}/lineage/openlineage/webhooks/:webhookId`, async ({ params }) => {
        await delay(200)

        const webhookIndex = webhooksStore.findIndex(w => w.id === params.webhookId)
        if (webhookIndex === -1) {
          return HttpResponse.json({ detail: 'Webhook not found' }, { status: 404 })
        }

        webhooksStore.splice(webhookIndex, 1)

        return HttpResponse.json({ message: 'Webhook deleted successfully' })
      }),

      // Test webhook connection
      http.post(`${API_BASE}/lineage/openlineage/webhooks/test`, async ({ request }) => {
        await delay(800) // Simulate network latency

        let body: {
          url: string
          headers?: Record<string, string>
          api_key?: string
          timeout_seconds?: number
        }
        try {
          body = await request.json() as typeof body
        } catch {
          return HttpResponse.json({ detail: 'Invalid JSON' }, { status: 400 })
        }

        if (!body.url) {
          return HttpResponse.json({ detail: 'url is required' }, { status: 400 })
        }

        // Simulate test result based on URL
        const isLocalhost = body.url.includes('localhost') || body.url.includes('127.0.0.1')
        const isMarquez = body.url.includes('marquez') || body.url.includes('5000')
        const isDataHub = body.url.includes('datahub') || body.url.includes('8080')

        // Mock successful connection for known endpoints
        if (isLocalhost && (isMarquez || isDataHub)) {
          return HttpResponse.json({
            success: true,
            status_code: 202,
            response_time_ms: Math.floor(Math.random() * 200) + 50,
            error_message: null,
            response_body: '{"status": "accepted"}',
          })
        }

        // For https URLs, simulate success
        if (body.url.startsWith('https://')) {
          return HttpResponse.json({
            success: true,
            status_code: 200,
            response_time_ms: Math.floor(Math.random() * 500) + 100,
            error_message: null,
            response_body: null,
          })
        }

        // For other URLs, simulate connection refused
        return HttpResponse.json({
          success: false,
          status_code: null,
          response_time_ms: Math.floor(Math.random() * 100) + 50,
          error_message: 'Connection refused: Unable to connect to the specified URL',
          response_body: null,
        })
      }),
    ]
  })(),

  // ============================================================================
  // Column-Level Lineage Endpoints
  // ============================================================================

  // Get column lineage for a node
  http.get(`${API_BASE}/lineage/nodes/:nodeId/columns`, async ({ params }) => {
    await delay(200)

    const nodeId = params.nodeId as string
    const graph = getLineageStore()
    const node = graph.nodes.find(n => n.id === nodeId)

    if (!node) {
      return HttpResponse.json({ detail: 'Node not found' }, { status: 404 })
    }

    // Generate mock columns based on node type
    const dataTypes = ['string', 'integer', 'timestamp', 'decimal', 'boolean', 'json']
    const columnNames = node.node_type === 'source'
      ? ['id', 'created_at', 'updated_at', 'name', 'value', 'status', 'metadata']
      : node.node_type === 'transform'
        ? ['source_id', 'processed_at', 'result', 'error_count', 'total_value']
        : ['report_id', 'generated_at', 'summary', 'metrics']

    const columns = columnNames.map((name, idx) => ({
      name,
      dataType: dataTypes[idx % dataTypes.length],
      nullable: idx > 2,
      isPrimaryKey: idx === 0,
      isForeignKey: name.endsWith('_id') && idx > 0,
      description: `Column ${name} in ${node.name}`,
      tags: idx % 3 === 0 ? ['pii'] : idx % 3 === 1 ? ['critical'] : [],
    }))

    return HttpResponse.json({
      nodeId,
      nodeName: node.name,
      columns,
      incomingMappings: [],
      outgoingMappings: [],
    })
  }),

  // Get column mappings for an edge
  http.get(`${API_BASE}/lineage/edges/:edgeId/column-mappings`, async ({ params }) => {
    await delay(200)

    const edgeId = params.edgeId as string
    const graph = getLineageStore()
    const edge = graph.edges.find(e => e.id === edgeId)

    if (!edge) {
      return HttpResponse.json({ detail: 'Edge not found' }, { status: 404 })
    }

    void ['direct', 'derived', 'aggregated', 'renamed', 'cast', 'computed']
    const sourceNode = graph.nodes.find(n => n.id === edge.source_node_id)
    const targetNode = graph.nodes.find(n => n.id === edge.target_node_id)

    // Generate mock column mappings
    const mappings = [
      {
        id: `${edgeId}-mapping-1`,
        sourceColumn: 'id',
        targetColumn: sourceNode?.node_type === 'source' ? 'source_id' : 'id',
        sourceNodeId: edge.source_node_id,
        targetNodeId: edge.target_node_id,
        transformationType: 'renamed' as const,
        confidence: 1.0,
      },
      {
        id: `${edgeId}-mapping-2`,
        sourceColumn: 'value',
        targetColumn: 'total_value',
        sourceNodeId: edge.source_node_id,
        targetNodeId: edge.target_node_id,
        transformationType: 'aggregated' as const,
        expression: 'SUM(value)',
        confidence: 0.95,
      },
      {
        id: `${edgeId}-mapping-3`,
        sourceColumn: 'created_at',
        targetColumn: 'processed_at',
        sourceNodeId: edge.source_node_id,
        targetNodeId: edge.target_node_id,
        transformationType: 'direct' as const,
        confidence: 1.0,
      },
    ]

    return HttpResponse.json({
      edgeId,
      sourceNodeId: edge.source_node_id,
      sourceNodeName: sourceNode?.name ?? edge.source_node_id,
      targetNodeId: edge.target_node_id,
      targetNodeName: targetNode?.name ?? edge.target_node_id,
      mappings,
    })
  }),

  // Get column impact analysis
  http.get(`${API_BASE}/lineage/columns/impact`, async ({ request }) => {
    await delay(500)

    const url = new URL(request.url)
    const nodeId = url.searchParams.get('node_id')
    const columnName = url.searchParams.get('column')

    if (!nodeId || !columnName) {
      return HttpResponse.json(
        { detail: 'node_id and column are required' },
        { status: 400 }
      )
    }

    const graph = getLineageStore()
    const sourceNode = graph.nodes.find(n => n.id === nodeId)

    if (!sourceNode) {
      return HttpResponse.json({ detail: 'Node not found' }, { status: 404 })
    }

    // Find downstream nodes
    const downstreamNodeIds = new Set<string>()
    const visited = new Set<string>()
    const queue = [nodeId]

    while (queue.length > 0) {
      const currentId = queue.shift()!
      if (visited.has(currentId)) continue
      visited.add(currentId)

      for (const edge of graph.edges) {
        if (edge.source_node_id === currentId) {
          downstreamNodeIds.add(edge.target_node_id)
          queue.push(edge.target_node_id)
        }
      }
    }

    const transformTypes = ['direct', 'derived', 'aggregated', 'renamed', 'cast', 'computed'] as const
    const affectedColumns = Array.from(downstreamNodeIds).flatMap((nId, idx) => {
      const n = graph.nodes.find(node => node.id === nId)
      if (!n) return []
      return [
        {
          nodeId: nId,
          nodeName: n.name,
          columnName: idx % 2 === 0 ? 'derived_' + columnName : columnName + '_processed',
          transformationType: transformTypes[idx % transformTypes.length],
          depth: Math.floor(idx / 2) + 1,
        },
      ]
    })

    const impactPath = affectedColumns.slice(0, 5).map((col, idx) => ({
      fromNodeId: idx === 0 ? nodeId : affectedColumns[idx - 1]?.nodeId ?? nodeId,
      fromNodeName: idx === 0 ? sourceNode.name : graph.nodes.find(n => n.id === affectedColumns[idx - 1]?.nodeId)?.name ?? '',
      fromColumn: idx === 0 ? columnName : affectedColumns[idx - 1]?.columnName ?? columnName,
      toNodeId: col.nodeId,
      toNodeName: col.nodeName,
      toColumn: col.columnName,
      transformationType: col.transformationType,
    }))

    return HttpResponse.json({
      sourceColumn: columnName,
      sourceNodeId: nodeId,
      sourceNodeName: sourceNode.name,
      affectedColumns,
      totalAffected: affectedColumns.length,
      affectedTables: downstreamNodeIds.size,
      impactPath,
    })
  }),
]
