/**
 * Lineage factory - generates lineage graph data for mock API
 *
 * Supports node types: source, transform, sink
 * Supports edge types: derives_from, transforms_to, feeds_into
 */

import type {
  LineageNode,
  LineageEdge,
  LineageGraph,
  LineageNodeType,
  LineageEdgeType,
  ImpactAnalysisResponse,
  AutoDiscoverResponse,
} from '@/api/client'
import { createId, createTimestamp, randomChoice, randomInt, faker } from './base'

// Node type weights for realistic distribution
const NODE_TYPES: LineageNodeType[] = ['source', 'transform', 'sink']
const EDGE_TYPES: LineageEdgeType[] = ['derives_from', 'transforms_to', 'feeds_into']

// Realistic node names by type
const SOURCE_NAMES = [
  'raw_customers',
  'raw_orders',
  'raw_products',
  'raw_transactions',
  'api_events',
  'clickstream_data',
  'user_sessions',
  'log_events',
  'inventory_feed',
  'marketing_data',
  'crm_export',
  'payment_logs',
]

const TRANSFORM_NAMES = [
  'clean_customers',
  'aggregate_orders',
  'join_user_products',
  'dedupe_transactions',
  'normalize_events',
  'filter_active_users',
  'calculate_metrics',
  'enrich_customer_data',
  'pivot_sales',
  'window_analytics',
  'hash_pii',
  'validate_schema',
]

const SINK_NAMES = [
  'dim_customer',
  'fact_orders',
  'mart_revenue',
  'report_daily_sales',
  'dashboard_metrics',
  'ml_training_set',
  'export_analytics',
  'bi_cube',
  'data_lake_archive',
  'compliance_snapshot',
]

export interface LineageNodeOptions {
  id?: string
  name?: string
  node_type?: LineageNodeType
  source_id?: string | null
  metadata?: Record<string, unknown> | null
  position_x?: number
  position_y?: number
}

export interface LineageEdgeOptions {
  id?: string
  source_node_id?: string
  target_node_id?: string
  edge_type?: LineageEdgeType
  metadata?: Record<string, unknown> | null
}

export interface LineageGraphOptions {
  nodeCount?: number
  includeSourceIds?: boolean
  sourceIds?: string[]
}

/**
 * Get a name appropriate for the node type
 */
function getNodeName(nodeType: LineageNodeType): string {
  switch (nodeType) {
    case 'source':
      return randomChoice(SOURCE_NAMES)
    case 'transform':
      return randomChoice(TRANSFORM_NAMES)
    case 'sink':
      return randomChoice(SINK_NAMES)
  }
}

/**
 * Create a lineage node
 */
export function createLineageNode(options: LineageNodeOptions = {}): LineageNode {
  const nodeType = options.node_type ?? randomChoice(NODE_TYPES)
  const timestamp = createTimestamp(randomInt(0, 90))

  return {
    id: options.id ?? createId(),
    name: options.name ?? getNodeName(nodeType),
    node_type: nodeType,
    source_id: options.source_id ?? (nodeType === 'source' && faker.datatype.boolean(0.7) ? createId() : null),
    metadata: options.metadata ?? (faker.datatype.boolean(0.5) ? {
      owner: faker.person.fullName(),
      description: faker.lorem.sentence(),
      tags: faker.helpers.arrayElements(['pii', 'critical', 'aggregated', 'raw', 'validated'], randomInt(1, 3)),
    } : null),
    position_x: options.position_x ?? faker.number.float({ min: 0, max: 800, fractionDigits: 0 }),
    position_y: options.position_y ?? faker.number.float({ min: 0, max: 600, fractionDigits: 0 }),
    created_at: timestamp,
    updated_at: timestamp,
  }
}

/**
 * Create a lineage edge
 */
export function createLineageEdge(options: LineageEdgeOptions = {}): LineageEdge {
  const timestamp = createTimestamp(randomInt(0, 90))

  return {
    id: options.id ?? createId(),
    source_node_id: options.source_node_id ?? createId(),
    target_node_id: options.target_node_id ?? createId(),
    edge_type: options.edge_type ?? randomChoice(EDGE_TYPES),
    metadata: options.metadata ?? (faker.datatype.boolean(0.3) ? {
      transformation: randomChoice(['filter', 'join', 'aggregate', 'map', 'dedupe']),
      schedule: randomChoice(['daily', 'hourly', 'real-time']),
    } : null),
    created_at: timestamp,
    updated_at: timestamp,
  }
}

/**
 * Create a realistic lineage graph with proper DAG structure
 */
export function createLineageGraph(options: LineageGraphOptions = {}): LineageGraph {
  const nodeCount = options.nodeCount ?? randomInt(8, 20)
  const sourceIds = options.sourceIds ?? []

  // Create nodes with proper type distribution (sources -> transforms -> sinks)
  const sourceCount = Math.max(2, Math.floor(nodeCount * 0.3))
  const sinkCount = Math.max(1, Math.floor(nodeCount * 0.2))
  const transformCount = nodeCount - sourceCount - sinkCount

  const nodes: LineageNode[] = []

  // Create source nodes
  for (let i = 0; i < sourceCount; i++) {
    const sourceId = sourceIds[i] ?? (options.includeSourceIds ? createId() : null)
    nodes.push(createLineageNode({
      node_type: 'source',
      source_id: sourceId,
      position_x: 50,
      position_y: 100 + i * 100,
    }))
  }

  // Create transform nodes
  for (let i = 0; i < transformCount; i++) {
    nodes.push(createLineageNode({
      node_type: 'transform',
      position_x: 300 + Math.floor(i / 3) * 200,
      position_y: 100 + (i % 3) * 150,
    }))
  }

  // Create sink nodes
  for (let i = 0; i < sinkCount; i++) {
    nodes.push(createLineageNode({
      node_type: 'sink',
      position_x: 700,
      position_y: 150 + i * 150,
    }))
  }

  // Create edges (DAG structure: sources -> transforms -> sinks)
  const edges: LineageEdge[] = []
  const sourceNodes = nodes.filter(n => n.node_type === 'source')
  const transformNodes = nodes.filter(n => n.node_type === 'transform')
  const sinkNodes = nodes.filter(n => n.node_type === 'sink')

  // Connect sources to transforms
  for (const transform of transformNodes) {
    const inputCount = randomInt(1, Math.min(3, sourceNodes.length))
    const inputs = faker.helpers.arrayElements(sourceNodes, inputCount)
    for (const input of inputs) {
      edges.push(createLineageEdge({
        source_node_id: input.id,
        target_node_id: transform.id,
        edge_type: randomChoice(['derives_from', 'transforms_to']),
      }))
    }
  }

  // Connect transforms to sinks
  for (const sink of sinkNodes) {
    const inputCount = randomInt(1, Math.min(2, transformNodes.length))
    const inputs = faker.helpers.arrayElements(transformNodes, inputCount)
    for (const input of inputs) {
      edges.push(createLineageEdge({
        source_node_id: input.id,
        target_node_id: sink.id,
        edge_type: 'feeds_into',
      }))
    }
  }

  // Add some transform-to-transform edges for complexity
  if (transformNodes.length > 2) {
    const extraEdges = randomInt(1, Math.floor(transformNodes.length / 2))
    for (let i = 0; i < extraEdges; i++) {
      const [from, to] = faker.helpers.arrayElements(transformNodes, 2)
      if (from.id !== to.id) {
        edges.push(createLineageEdge({
          source_node_id: from.id,
          target_node_id: to.id,
          edge_type: 'derives_from',
        }))
      }
    }
  }

  return {
    nodes,
    edges,
    total_nodes: nodes.length,
    total_edges: edges.length,
  }
}

/**
 * Create impact analysis response
 */
export function createImpactAnalysis(nodeId: string, graph?: LineageGraph): ImpactAnalysisResponse {
  const targetGraph = graph ?? createLineageGraph()
  const targetNode = targetGraph.nodes.find(n => n.id === nodeId) ?? targetGraph.nodes[0]

  // Find upstream (nodes that feed into this node)
  const incomingEdges = targetGraph.edges.filter(e => e.target_node_id === targetNode.id)
  const upstream = targetGraph.nodes.filter(n =>
    incomingEdges.some(e => e.source_node_id === n.id)
  )

  // Find downstream (nodes that this node feeds into)
  const outgoingEdges = targetGraph.edges.filter(e => e.source_node_id === targetNode.id)
  const downstream = targetGraph.nodes.filter(n =>
    outgoingEdges.some(e => e.target_node_id === n.id)
  )

  return {
    node_id: targetNode.id,
    node_name: targetNode.name,
    upstream,
    downstream,
    upstream_count: upstream.length,
    downstream_count: downstream.length,
    depth: 3,
  }
}

/**
 * Create auto-discover response
 */
export function createAutoDiscoverResponse(sourceIds?: string[]): AutoDiscoverResponse {
  const graph = createLineageGraph({
    nodeCount: randomInt(5, 12),
    includeSourceIds: true,
    sourceIds,
  })

  return {
    nodes_created: graph.nodes.length,
    edges_created: graph.edges.length,
    nodes: graph.nodes,
    edges: graph.edges,
    message: `Discovered ${graph.nodes.length} nodes and ${graph.edges.length} edges from database relationships`,
  }
}

// In-memory store for lineage data
let lineageStore: LineageGraph | null = null

/**
 * Get or initialize the lineage store
 */
export function getLineageStore(): LineageGraph {
  if (!lineageStore) {
    lineageStore = createLineageGraph({ nodeCount: 12 })
  }
  return lineageStore
}

/**
 * Reset the lineage store
 */
export function resetLineageStore(): void {
  lineageStore = null
}

/**
 * Add a node to the store
 */
export function addNodeToStore(node: LineageNode): void {
  const store = getLineageStore()
  store.nodes.push(node)
  store.total_nodes = store.nodes.length
}

/**
 * Remove a node from the store
 */
export function removeNodeFromStore(nodeId: string): boolean {
  const store = getLineageStore()
  const index = store.nodes.findIndex(n => n.id === nodeId)
  if (index === -1) return false

  store.nodes.splice(index, 1)
  // Also remove related edges
  store.edges = store.edges.filter(
    e => e.source_node_id !== nodeId && e.target_node_id !== nodeId
  )
  store.total_nodes = store.nodes.length
  store.total_edges = store.edges.length
  return true
}

/**
 * Add an edge to the store
 */
export function addEdgeToStore(edge: LineageEdge): void {
  const store = getLineageStore()
  store.edges.push(edge)
  store.total_edges = store.edges.length
}

/**
 * Remove an edge from the store
 */
export function removeEdgeFromStore(edgeId: string): boolean {
  const store = getLineageStore()
  const index = store.edges.findIndex(e => e.id === edgeId)
  if (index === -1) return false

  store.edges.splice(index, 1)
  store.total_edges = store.edges.length
  return true
}
