/**
 * Performance utilities for lineage graph visualization.
 *
 * Provides functions for node clustering, edge simplification,
 * viewport culling, and debouncing for large graph optimization.
 */

import type { Node, Edge, Viewport } from 'reactflow'

// ============================================================================
// Types
// ============================================================================

export interface ClusteredNode {
  id: string
  type: 'cluster'
  position: { x: number; y: number }
  data: {
    nodeIds: string[]
    nodeCount: number
    label: string
    expanded: boolean
    centroid: { x: number; y: number }
  }
}

export interface PerformanceMetrics {
  fps: number
  nodeCount: number
  edgeCount: number
  visibleNodes: number
  clusterCount: number
  memoryUsage: number | null
  renderTime: number
}

export interface ViewportBounds {
  minX: number
  maxX: number
  minY: number
  maxY: number
}

// ============================================================================
// Constants
// ============================================================================

export const PERFORMANCE_THRESHOLDS = {
  /** Node count threshold to enable clustering */
  CLUSTERING_THRESHOLD: 100,
  /** Node count threshold to enable virtualization */
  VIRTUALIZATION_THRESHOLD: 100,
  /** Node count to show warning */
  WARNING_THRESHOLD: 200,
  /** Maximum nodes to render simultaneously */
  MAX_VISIBLE_NODES: 200,
  /** Minimum distance to cluster nodes (in pixels) */
  CLUSTER_DISTANCE: 150,
  /** Viewport padding for culling (in pixels) */
  VIEWPORT_PADDING: 200,
  /** Target FPS for smooth interaction */
  TARGET_FPS: 30,
  /** Debounce delay for layout calculations (ms) */
  LAYOUT_DEBOUNCE_MS: 100,
} as const

// ============================================================================
// Clustering Functions
// ============================================================================

/**
 * Cluster nearby nodes based on spatial proximity.
 *
 * Uses a simple grid-based clustering algorithm that groups
 * nodes within a threshold distance of each other.
 *
 * @param nodes - Array of React Flow nodes
 * @param threshold - Distance threshold for clustering (default: 150px)
 * @returns Object with clustered nodes, original nodes, and cluster map
 */
export function clusterNodes<T>(
  nodes: Node<T>[],
  threshold: number = PERFORMANCE_THRESHOLDS.CLUSTER_DISTANCE
): {
  clusters: ClusteredNode[]
  standaloneNodes: Node<T>[]
  clusterMap: Map<string, string> // nodeId -> clusterId
} {
  if (nodes.length === 0) {
    return { clusters: [], standaloneNodes: [], clusterMap: new Map() }
  }

  const clusterMap = new Map<string, string>()
  const clustered = new Map<string, Node<T>[]>()
  const standalone: Node<T>[] = []

  // Simple grid-based clustering
  const gridSize = threshold
  const grid = new Map<string, Node<T>[]>()

  // Assign nodes to grid cells
  nodes.forEach((node) => {
    const cellX = Math.floor(node.position.x / gridSize)
    const cellY = Math.floor(node.position.y / gridSize)
    const cellKey = `${cellX}:${cellY}`

    if (!grid.has(cellKey)) {
      grid.set(cellKey, [])
    }
    grid.get(cellKey)!.push(node)
  })

  // Process grid cells
  let clusterIndex = 0
  grid.forEach((cellNodes) => {
    if (cellNodes.length >= 3) {
      // Create cluster if 3+ nodes in cell
      const clusterId = `cluster-${clusterIndex++}`
      clustered.set(clusterId, cellNodes)
      cellNodes.forEach((node) => clusterMap.set(node.id, clusterId))
    } else {
      // Keep as standalone
      standalone.push(...cellNodes)
    }
  })

  // Convert clustered groups to ClusteredNode objects
  const clusters: ClusteredNode[] = []
  clustered.forEach((clusterNodes, clusterId) => {
    const centroid = calculateCentroid(clusterNodes)
    clusters.push({
      id: clusterId,
      type: 'cluster',
      position: centroid,
      data: {
        nodeIds: clusterNodes.map((n) => n.id),
        nodeCount: clusterNodes.length,
        label: `${clusterNodes.length} nodes`,
        expanded: false,
        centroid,
      },
    })
  })

  return { clusters, standaloneNodes: standalone, clusterMap }
}

/**
 * Calculate the centroid (average position) of a group of nodes.
 */
function calculateCentroid<T>(nodes: Node<T>[]): { x: number; y: number } {
  if (nodes.length === 0) return { x: 0, y: 0 }

  const sum = nodes.reduce(
    (acc, node) => ({
      x: acc.x + node.position.x,
      y: acc.y + node.position.y,
    }),
    { x: 0, y: 0 }
  )

  return {
    x: sum.x / nodes.length,
    y: sum.y / nodes.length,
  }
}

/**
 * Expand a cluster back into individual nodes.
 *
 * @param cluster - The cluster to expand
 * @param originalNodes - Map of original node IDs to nodes
 * @returns Array of expanded nodes with radial positioning
 */
export function expandCluster<T>(
  cluster: ClusteredNode,
  originalNodes: Map<string, Node<T>>
): Node<T>[] {
  const { nodeIds, centroid } = cluster.data
  const expandedNodes: Node<T>[] = []
  const radius = Math.max(100, nodeIds.length * 20)

  nodeIds.forEach((nodeId, index) => {
    const originalNode = originalNodes.get(nodeId)
    if (originalNode) {
      // Arrange nodes in a circle around the cluster centroid
      const angle = (2 * Math.PI * index) / nodeIds.length
      expandedNodes.push({
        ...originalNode,
        position: {
          x: centroid.x + radius * Math.cos(angle),
          y: centroid.y + radius * Math.sin(angle),
        },
      })
    }
  })

  return expandedNodes
}

// ============================================================================
// Edge Simplification Functions
// ============================================================================

/**
 * Simplify edges by removing redundant connections.
 *
 * This function removes edges that form transitive relationships,
 * keeping only direct connections. For example, if A->B->C exists,
 * and A->C also exists, the A->C edge is removed.
 *
 * @param edges - Array of React Flow edges
 * @param nodes - Array of node IDs for validation
 * @returns Simplified array of edges
 */
export function simplifyEdges<T>(
  edges: Edge<T>[],
  nodeIds: Set<string>
): Edge<T>[] {
  if (edges.length === 0) return edges

  // Build adjacency list
  const adjacency = new Map<string, Set<string>>()
  edges.forEach((edge) => {
    if (!adjacency.has(edge.source)) {
      adjacency.set(edge.source, new Set())
    }
    adjacency.get(edge.source)!.add(edge.target)
  })

  // Find transitive edges to remove
  const transitiveEdges = new Set<string>()

  edges.forEach((edge) => {
    const sourceNeighbors = adjacency.get(edge.source)
    if (!sourceNeighbors) return

    // Check if there's a path through intermediate nodes
    sourceNeighbors.forEach((intermediate) => {
      if (intermediate === edge.target) return

      const intermediateNeighbors = adjacency.get(intermediate)
      if (intermediateNeighbors?.has(edge.target)) {
        // This edge is transitive (can go through intermediate)
        transitiveEdges.add(edge.id)
      }
    })
  })

  // Filter out edges connected to non-existent nodes
  return edges.filter(
    (edge) =>
      !transitiveEdges.has(edge.id) &&
      nodeIds.has(edge.source) &&
      nodeIds.has(edge.target)
  )
}

/**
 * Filter edges to only include those connecting visible nodes.
 */
export function filterVisibleEdges<T>(
  edges: Edge<T>[],
  visibleNodeIds: Set<string>
): Edge<T>[] {
  return edges.filter(
    (edge) => visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target)
  )
}

// ============================================================================
// Viewport Culling Functions
// ============================================================================

/**
 * Get nodes that are visible within the current viewport.
 *
 * Includes padding around the viewport to ensure smooth scrolling
 * without pop-in effects.
 *
 * @param viewport - Current React Flow viewport (x, y, zoom)
 * @param nodes - All nodes in the graph
 * @param containerWidth - Width of the container element
 * @param containerHeight - Height of the container element
 * @param padding - Extra padding around viewport (default: 200px)
 * @returns Array of visible nodes
 */
export function getVisibleNodes<T>(
  viewport: Viewport,
  nodes: Node<T>[],
  containerWidth: number,
  containerHeight: number,
  padding: number = PERFORMANCE_THRESHOLDS.VIEWPORT_PADDING
): Node<T>[] {
  const bounds = getViewportBounds(viewport, containerWidth, containerHeight, padding)

  return nodes.filter((node) => {
    const nodeWidth = 180 // Approximate node width
    const nodeHeight = 60 // Approximate node height

    // Check if node overlaps with viewport bounds
    return (
      node.position.x + nodeWidth >= bounds.minX &&
      node.position.x <= bounds.maxX &&
      node.position.y + nodeHeight >= bounds.minY &&
      node.position.y <= bounds.maxY
    )
  })
}

/**
 * Calculate viewport bounds in graph coordinates.
 */
export function getViewportBounds(
  viewport: Viewport,
  containerWidth: number,
  containerHeight: number,
  padding: number = 0
): ViewportBounds {
  const { x, y, zoom } = viewport

  // Convert screen coordinates to graph coordinates
  const minX = (-x - padding) / zoom
  const maxX = (-x + containerWidth + padding) / zoom
  const minY = (-y - padding) / zoom
  const maxY = (-y + containerHeight + padding) / zoom

  return { minX, maxX, minY, maxY }
}

/**
 * Check if a position is within the viewport bounds.
 */
export function isInViewport(
  position: { x: number; y: number },
  bounds: ViewportBounds
): boolean {
  return (
    position.x >= bounds.minX &&
    position.x <= bounds.maxX &&
    position.y >= bounds.minY &&
    position.y <= bounds.maxY
  )
}

// ============================================================================
// Level of Detail (LOD) Functions
// ============================================================================

/**
 * Determine the appropriate level of detail for a node based on zoom level.
 *
 * Returns 'full', 'simplified', or 'minimal' based on the zoom level.
 */
export function getNodeLOD(zoom: number): 'full' | 'simplified' | 'minimal' {
  if (zoom >= 0.8) return 'full'
  if (zoom >= 0.4) return 'simplified'
  return 'minimal'
}

/**
 * Determine the appropriate level of detail for edges based on zoom level.
 */
export function getEdgeLOD(zoom: number): 'animated' | 'static' | 'hidden' {
  if (zoom >= 0.6) return 'animated'
  if (zoom >= 0.3) return 'static'
  return 'hidden'
}

// ============================================================================
// Debouncing Utilities
// ============================================================================

/**
 * Create a debounced version of a layout calculation function.
 *
 * This prevents layout calculations from firing too frequently
 * during rapid user interactions like zooming or panning.
 *
 * @param fn - The function to debounce
 * @param delay - Delay in milliseconds (default: 100ms)
 * @returns Debounced function
 */
export function debounceLayout<T extends (...args: unknown[]) => unknown>(
  fn: T,
  delay: number = PERFORMANCE_THRESHOLDS.LAYOUT_DEBOUNCE_MS
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null

  return (...args: Parameters<T>) => {
    if (timeoutId) {
      clearTimeout(timeoutId)
    }
    timeoutId = setTimeout(() => {
      fn(...args)
      timeoutId = null
    }, delay)
  }
}

/**
 * Create a throttled version of a function.
 *
 * Ensures the function is called at most once per specified interval.
 *
 * @param fn - The function to throttle
 * @param limit - Minimum interval between calls (ms)
 * @returns Throttled function
 */
export function throttle<T extends (...args: unknown[]) => unknown>(
  fn: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle = false

  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      fn(...args)
      inThrottle = true
      setTimeout(() => {
        inThrottle = false
      }, limit)
    }
  }
}

// ============================================================================
// Performance Measurement
// ============================================================================

/**
 * Create a performance monitor for tracking render metrics.
 */
export function createPerformanceMonitor(): {
  startFrame: () => void
  endFrame: () => void
  getMetrics: () => { fps: number; averageRenderTime: number }
  reset: () => void
} {
  const frameTimes: number[] = []
  const maxSamples = 60
  let lastFrameTime = 0
  let frameStartTime = 0

  return {
    startFrame: () => {
      frameStartTime = performance.now()
    },
    endFrame: () => {
      const now = performance.now()
      const renderTime = now - frameStartTime

      if (lastFrameTime > 0) {
        frameTimes.push(renderTime)
        if (frameTimes.length > maxSamples) {
          frameTimes.shift()
        }
      }
      lastFrameTime = now
    },
    getMetrics: () => {
      if (frameTimes.length === 0) {
        return { fps: 60, averageRenderTime: 0 }
      }

      const avgRenderTime =
        frameTimes.reduce((a, b) => a + b, 0) / frameTimes.length
      // FPS based on render time (assuming 16.67ms target for 60fps)
      const fps = Math.min(60, Math.round(1000 / Math.max(avgRenderTime, 16.67)))

      return { fps, averageRenderTime: avgRenderTime }
    },
    reset: () => {
      frameTimes.length = 0
      lastFrameTime = 0
    },
  }
}

/**
 * Get current memory usage if available.
 */
export function getMemoryUsage(): number | null {
  // Check if performance.memory is available (Chrome only)
  const perf = performance as Performance & {
    memory?: {
      usedJSHeapSize: number
      totalJSHeapSize: number
      jsHeapSizeLimit: number
    }
  }

  if (perf.memory) {
    return perf.memory.usedJSHeapSize
  }
  return null
}

// ============================================================================
// Auto-Optimization
// ============================================================================

/**
 * Determine which optimizations should be enabled based on graph size.
 */
export function getRecommendedOptimizations(nodeCount: number): {
  enableClustering: boolean
  enableVirtualization: boolean
  enableEdgeSimplification: boolean
  enableLOD: boolean
  showWarning: boolean
  warningMessage: string | null
} {
  const enableClustering = nodeCount >= PERFORMANCE_THRESHOLDS.CLUSTERING_THRESHOLD
  const enableVirtualization = nodeCount >= PERFORMANCE_THRESHOLDS.VIRTUALIZATION_THRESHOLD
  const showWarning = nodeCount >= PERFORMANCE_THRESHOLDS.WARNING_THRESHOLD

  let warningMessage: string | null = null
  if (nodeCount >= 500) {
    warningMessage = `Large graph detected (${nodeCount} nodes). Performance optimizations have been automatically enabled.`
  } else if (showWarning) {
    warningMessage = `Graph has ${nodeCount} nodes. Consider enabling performance mode for smoother interaction.`
  }

  return {
    enableClustering,
    enableVirtualization,
    enableEdgeSimplification: nodeCount > 150,
    enableLOD: nodeCount > 100,
    showWarning,
    warningMessage,
  }
}

// ============================================================================
// Graph Statistics
// ============================================================================

/**
 * Calculate statistics about the graph structure.
 */
export function calculateGraphStats<N, E>(
  nodes: Node<N>[],
  edges: Edge<E>[]
): {
  nodeCount: number
  edgeCount: number
  averageDegree: number
  maxDegree: number
  density: number
  connectedComponents: number
} {
  const nodeCount = nodes.length
  const edgeCount = edges.length

  if (nodeCount === 0) {
    return {
      nodeCount: 0,
      edgeCount: 0,
      averageDegree: 0,
      maxDegree: 0,
      density: 0,
      connectedComponents: 0,
    }
  }

  // Calculate degree for each node
  const degrees = new Map<string, number>()
  nodes.forEach((node) => degrees.set(node.id, 0))

  edges.forEach((edge) => {
    degrees.set(edge.source, (degrees.get(edge.source) || 0) + 1)
    degrees.set(edge.target, (degrees.get(edge.target) || 0) + 1)
  })

  const degreeValues = Array.from(degrees.values())
  const averageDegree = degreeValues.reduce((a, b) => a + b, 0) / nodeCount
  const maxDegree = Math.max(...degreeValues)

  // Graph density: actual edges / possible edges
  const possibleEdges = nodeCount * (nodeCount - 1)
  const density = possibleEdges > 0 ? edgeCount / possibleEdges : 0

  // Simple connected components count using DFS
  const connectedComponents = countConnectedComponents(nodes, edges)

  return {
    nodeCount,
    edgeCount,
    averageDegree: Math.round(averageDegree * 100) / 100,
    maxDegree,
    density: Math.round(density * 10000) / 10000,
    connectedComponents,
  }
}

/**
 * Count connected components using DFS.
 */
function countConnectedComponents<N, E>(
  nodes: Node<N>[],
  edges: Edge<E>[]
): number {
  const visited = new Set<string>()
  const adjacency = new Map<string, Set<string>>()

  // Build undirected adjacency list
  nodes.forEach((node) => adjacency.set(node.id, new Set()))
  edges.forEach((edge) => {
    adjacency.get(edge.source)?.add(edge.target)
    adjacency.get(edge.target)?.add(edge.source)
  })

  let components = 0

  const dfs = (nodeId: string) => {
    if (visited.has(nodeId)) return
    visited.add(nodeId)
    adjacency.get(nodeId)?.forEach((neighbor) => dfs(neighbor))
  }

  nodes.forEach((node) => {
    if (!visited.has(node.id)) {
      dfs(node.id)
      components++
    }
  })

  return components
}
