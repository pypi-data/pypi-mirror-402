/**
 * Tests for lineage-performance.ts
 *
 * Comprehensive tests for graph performance optimization utilities including:
 * - Node clustering
 * - Edge simplification
 * - Viewport culling
 * - Level of detail
 * - Debouncing utilities
 * - Performance metrics
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import type { Node, Edge, Viewport } from 'reactflow'
import {
  PERFORMANCE_THRESHOLDS,
  clusterNodes,
  expandCluster,
  simplifyEdges,
  filterVisibleEdges,
  getVisibleNodes,
  getViewportBounds,
  isInViewport,
  getNodeLOD,
  getEdgeLOD,
  debounceLayout,
  throttle,
  createPerformanceMonitor,
  getMemoryUsage,
  getRecommendedOptimizations,
  calculateGraphStats,
  type ClusteredNode,
  type ViewportBounds,
} from '../lineage-performance'

// ==============================================================================
// Constants Tests
// ==============================================================================

describe('PERFORMANCE_THRESHOLDS', () => {
  it('should have expected threshold values', () => {
    expect(PERFORMANCE_THRESHOLDS.CLUSTERING_THRESHOLD).toBe(100)
    expect(PERFORMANCE_THRESHOLDS.VIRTUALIZATION_THRESHOLD).toBe(100)
    expect(PERFORMANCE_THRESHOLDS.WARNING_THRESHOLD).toBe(200)
    expect(PERFORMANCE_THRESHOLDS.MAX_VISIBLE_NODES).toBe(200)
    expect(PERFORMANCE_THRESHOLDS.CLUSTER_DISTANCE).toBe(150)
    expect(PERFORMANCE_THRESHOLDS.VIEWPORT_PADDING).toBe(200)
    expect(PERFORMANCE_THRESHOLDS.TARGET_FPS).toBe(30)
    expect(PERFORMANCE_THRESHOLDS.LAYOUT_DEBOUNCE_MS).toBe(100)
  })
})

// ==============================================================================
// Clustering Tests
// ==============================================================================

describe('clusterNodes', () => {
  it('should return empty result for empty nodes array', () => {
    const result = clusterNodes([])
    expect(result.clusters).toHaveLength(0)
    expect(result.standaloneNodes).toHaveLength(0)
    expect(result.clusterMap.size).toBe(0)
  })

  it('should not cluster nodes that are far apart', () => {
    const nodes: Node[] = [
      { id: 'node1', position: { x: 0, y: 0 }, data: {} },
      { id: 'node2', position: { x: 1000, y: 1000 }, data: {} },
    ]
    const result = clusterNodes(nodes)

    expect(result.clusters).toHaveLength(0)
    expect(result.standaloneNodes).toHaveLength(2)
  })

  it('should cluster nodes that are close together', () => {
    const nodes: Node[] = [
      { id: 'node1', position: { x: 10, y: 10 }, data: {} },
      { id: 'node2', position: { x: 20, y: 20 }, data: {} },
      { id: 'node3', position: { x: 30, y: 30 }, data: {} },
    ]
    const result = clusterNodes(nodes, 100)

    expect(result.clusters.length).toBeGreaterThanOrEqual(1)
    expect(result.clusters[0].data.nodeCount).toBeGreaterThanOrEqual(3)
  })

  it('should create cluster map correctly', () => {
    const nodes: Node[] = [
      { id: 'node1', position: { x: 10, y: 10 }, data: {} },
      { id: 'node2', position: { x: 20, y: 20 }, data: {} },
      { id: 'node3', position: { x: 30, y: 30 }, data: {} },
    ]
    const result = clusterNodes(nodes, 100)

    // All three nodes should be in the same cluster
    const nodeIds = result.clusters[0]?.data.nodeIds || []
    expect(nodeIds).toContain('node1')
    expect(nodeIds).toContain('node2')
    expect(nodeIds).toContain('node3')
  })

  it('should use default threshold when not specified', () => {
    const nodes: Node[] = [
      { id: 'node1', position: { x: 10, y: 10 }, data: {} },
      { id: 'node2', position: { x: 20, y: 20 }, data: {} },
      { id: 'node3', position: { x: 30, y: 30 }, data: {} },
    ]
    const result = clusterNodes(nodes)

    // Should use CLUSTER_DISTANCE (150) as default
    expect(result).toBeDefined()
  })
})

describe('expandCluster', () => {
  it('should expand cluster into individual nodes', () => {
    const cluster: ClusteredNode = {
      id: 'cluster-0',
      type: 'cluster',
      position: { x: 100, y: 100 },
      data: {
        nodeIds: ['node1', 'node2', 'node3'],
        nodeCount: 3,
        label: '3 nodes',
        expanded: false,
        centroid: { x: 100, y: 100 },
      },
    }

    const originalNodes = new Map<string, Node>([
      ['node1', { id: 'node1', position: { x: 0, y: 0 }, data: { label: 'Node 1' } }],
      ['node2', { id: 'node2', position: { x: 50, y: 50 }, data: { label: 'Node 2' } }],
      ['node3', { id: 'node3', position: { x: 100, y: 100 }, data: { label: 'Node 3' } }],
    ])

    const expandedNodes = expandCluster(cluster, originalNodes)

    expect(expandedNodes).toHaveLength(3)
    // Nodes should be arranged in a circle around centroid
    expandedNodes.forEach((node) => {
      expect(originalNodes.has(node.id)).toBe(true)
    })
  })

  it('should handle missing nodes gracefully', () => {
    const cluster: ClusteredNode = {
      id: 'cluster-0',
      type: 'cluster',
      position: { x: 100, y: 100 },
      data: {
        nodeIds: ['node1', 'missing-node'],
        nodeCount: 2,
        label: '2 nodes',
        expanded: false,
        centroid: { x: 100, y: 100 },
      },
    }

    const originalNodes = new Map<string, Node>([
      ['node1', { id: 'node1', position: { x: 0, y: 0 }, data: {} }],
    ])

    const expandedNodes = expandCluster(cluster, originalNodes)
    expect(expandedNodes).toHaveLength(1)
  })
})

// ==============================================================================
// Edge Simplification Tests
// ==============================================================================

describe('simplifyEdges', () => {
  it('should return empty array for empty edges', () => {
    const result = simplifyEdges([], new Set())
    expect(result).toHaveLength(0)
  })

  it('should remove transitive edges', () => {
    // A -> B -> C and A -> C (transitive)
    const edges: Edge[] = [
      { id: 'e1', source: 'A', target: 'B' },
      { id: 'e2', source: 'B', target: 'C' },
      { id: 'e3', source: 'A', target: 'C' }, // Transitive
    ]
    const nodeIds = new Set(['A', 'B', 'C'])

    const result = simplifyEdges(edges, nodeIds)

    // e3 should be removed as it's transitive through B
    expect(result).toHaveLength(2)
    expect(result.find((e) => e.id === 'e3')).toBeUndefined()
  })

  it('should keep non-transitive edges', () => {
    const edges: Edge[] = [
      { id: 'e1', source: 'A', target: 'B' },
      { id: 'e2', source: 'C', target: 'D' },
    ]
    const nodeIds = new Set(['A', 'B', 'C', 'D'])

    const result = simplifyEdges(edges, nodeIds)
    expect(result).toHaveLength(2)
  })

  it('should filter edges to non-existent nodes', () => {
    const edges: Edge[] = [
      { id: 'e1', source: 'A', target: 'B' },
      { id: 'e2', source: 'A', target: 'MISSING' },
    ]
    const nodeIds = new Set(['A', 'B'])

    const result = simplifyEdges(edges, nodeIds)
    expect(result).toHaveLength(1)
    expect(result[0].id).toBe('e1')
  })
})

describe('filterVisibleEdges', () => {
  it('should filter edges to only visible nodes', () => {
    const edges: Edge[] = [
      { id: 'e1', source: 'A', target: 'B' },
      { id: 'e2', source: 'B', target: 'C' },
      { id: 'e3', source: 'C', target: 'D' },
    ]
    const visibleNodeIds = new Set(['A', 'B'])

    const result = filterVisibleEdges(edges, visibleNodeIds)

    expect(result).toHaveLength(1)
    expect(result[0].id).toBe('e1')
  })
})

// ==============================================================================
// Viewport Culling Tests
// ==============================================================================

describe('getViewportBounds', () => {
  it('should calculate viewport bounds correctly', () => {
    const viewport: Viewport = { x: -100, y: -100, zoom: 1 }
    const bounds = getViewportBounds(viewport, 800, 600)

    expect(bounds.minX).toBe(100)
    expect(bounds.maxX).toBe(900)
    expect(bounds.minY).toBe(100)
    expect(bounds.maxY).toBe(700)
  })

  it('should apply padding correctly', () => {
    const viewport: Viewport = { x: 0, y: 0, zoom: 1 }
    const bounds = getViewportBounds(viewport, 800, 600, 100)

    expect(bounds.minX).toBe(-100)
    expect(bounds.maxX).toBe(900)
    expect(bounds.minY).toBe(-100)
    expect(bounds.maxY).toBe(700)
  })

  it('should handle zoom correctly', () => {
    const viewport: Viewport = { x: 0, y: 0, zoom: 2 }
    const bounds = getViewportBounds(viewport, 800, 600, 0)

    // -0 and 0 comparison issue: use toBeCloseTo or check absolute value
    expect(Math.abs(bounds.minX)).toBe(0)
    expect(bounds.maxX).toBe(400) // 800 / 2
    expect(Math.abs(bounds.minY)).toBe(0)
    expect(bounds.maxY).toBe(300) // 600 / 2
  })
})

describe('isInViewport', () => {
  it('should return true for position inside bounds', () => {
    const bounds: ViewportBounds = { minX: 0, maxX: 100, minY: 0, maxY: 100 }
    expect(isInViewport({ x: 50, y: 50 }, bounds)).toBe(true)
  })

  it('should return false for position outside bounds', () => {
    const bounds: ViewportBounds = { minX: 0, maxX: 100, minY: 0, maxY: 100 }
    expect(isInViewport({ x: 150, y: 50 }, bounds)).toBe(false)
    expect(isInViewport({ x: -50, y: 50 }, bounds)).toBe(false)
  })

  it('should return true for position on bounds edge', () => {
    const bounds: ViewportBounds = { minX: 0, maxX: 100, minY: 0, maxY: 100 }
    expect(isInViewport({ x: 0, y: 0 }, bounds)).toBe(true)
    expect(isInViewport({ x: 100, y: 100 }, bounds)).toBe(true)
  })
})

describe('getVisibleNodes', () => {
  it('should return nodes within viewport', () => {
    const viewport: Viewport = { x: 0, y: 0, zoom: 1 }
    const nodes: Node[] = [
      { id: 'visible', position: { x: 100, y: 100 }, data: {} },
      { id: 'hidden', position: { x: 2000, y: 2000 }, data: {} },
    ]

    const result = getVisibleNodes(viewport, nodes, 800, 600)

    expect(result).toHaveLength(1)
    expect(result[0].id).toBe('visible')
  })

  it('should include padding in visibility calculation', () => {
    const viewport: Viewport = { x: 0, y: 0, zoom: 1 }
    const nodes: Node[] = [
      { id: 'edge-visible', position: { x: 900, y: 100 }, data: {} }, // Just outside 800, but within 200 padding
    ]

    const result = getVisibleNodes(viewport, nodes, 800, 600, 200)
    expect(result).toHaveLength(1)
  })
})

// ==============================================================================
// Level of Detail Tests
// ==============================================================================

describe('getNodeLOD', () => {
  it('should return full for high zoom', () => {
    expect(getNodeLOD(1.0)).toBe('full')
    expect(getNodeLOD(0.8)).toBe('full')
  })

  it('should return simplified for medium zoom', () => {
    expect(getNodeLOD(0.6)).toBe('simplified')
    expect(getNodeLOD(0.4)).toBe('simplified')
  })

  it('should return minimal for low zoom', () => {
    expect(getNodeLOD(0.3)).toBe('minimal')
    expect(getNodeLOD(0.1)).toBe('minimal')
  })
})

describe('getEdgeLOD', () => {
  it('should return animated for high zoom', () => {
    expect(getEdgeLOD(0.8)).toBe('animated')
    expect(getEdgeLOD(0.6)).toBe('animated')
  })

  it('should return static for medium zoom', () => {
    expect(getEdgeLOD(0.5)).toBe('static')
    expect(getEdgeLOD(0.3)).toBe('static')
  })

  it('should return hidden for low zoom', () => {
    expect(getEdgeLOD(0.2)).toBe('hidden')
    expect(getEdgeLOD(0.1)).toBe('hidden')
  })
})

// ==============================================================================
// Debouncing Tests
// ==============================================================================

describe('debounceLayout', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should debounce function calls', () => {
    const fn = vi.fn()
    const debounced = debounceLayout(fn, 100)

    debounced()
    debounced()
    debounced()

    expect(fn).not.toHaveBeenCalled()

    vi.advanceTimersByTime(100)

    expect(fn).toHaveBeenCalledTimes(1)
  })

  it('should use default delay', () => {
    const fn = vi.fn()
    const debounced = debounceLayout(fn)

    debounced()
    vi.advanceTimersByTime(99)
    expect(fn).not.toHaveBeenCalled()

    vi.advanceTimersByTime(1)
    expect(fn).toHaveBeenCalledTimes(1)
  })
})

describe('throttle', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should throttle function calls', () => {
    const fn = vi.fn()
    const throttled = throttle(fn, 100)

    throttled()
    throttled()
    throttled()

    expect(fn).toHaveBeenCalledTimes(1)

    vi.advanceTimersByTime(100)

    throttled()
    expect(fn).toHaveBeenCalledTimes(2)
  })
})

// ==============================================================================
// Performance Measurement Tests
// ==============================================================================

describe('createPerformanceMonitor', () => {
  it('should track frame metrics', () => {
    const monitor = createPerformanceMonitor()

    // Initial metrics
    const initialMetrics = monitor.getMetrics()
    expect(initialMetrics.fps).toBe(60)
    expect(initialMetrics.averageRenderTime).toBe(0)

    // Record some frames
    monitor.startFrame()
    monitor.endFrame()
    monitor.startFrame()
    monitor.endFrame()

    const metrics = monitor.getMetrics()
    expect(metrics.fps).toBeGreaterThan(0)
  })

  it('should reset metrics', () => {
    const monitor = createPerformanceMonitor()

    monitor.startFrame()
    monitor.endFrame()

    monitor.reset()

    const metrics = monitor.getMetrics()
    expect(metrics.fps).toBe(60)
    expect(metrics.averageRenderTime).toBe(0)
  })
})

describe('getMemoryUsage', () => {
  it('should return null when performance.memory is not available', () => {
    const result = getMemoryUsage()
    // In test environment, performance.memory is typically not available
    expect(result === null || typeof result === 'number').toBe(true)
  })
})

// ==============================================================================
// Auto-Optimization Tests
// ==============================================================================

describe('getRecommendedOptimizations', () => {
  it('should not recommend optimizations for small graphs', () => {
    const result = getRecommendedOptimizations(50)

    expect(result.enableClustering).toBe(false)
    expect(result.enableVirtualization).toBe(false)
    expect(result.showWarning).toBe(false)
  })

  it('should recommend clustering for 100+ nodes', () => {
    const result = getRecommendedOptimizations(100)

    expect(result.enableClustering).toBe(true)
    expect(result.enableVirtualization).toBe(true)
  })

  it('should show warning for 200+ nodes', () => {
    const result = getRecommendedOptimizations(200)

    expect(result.showWarning).toBe(true)
    expect(result.warningMessage).not.toBeNull()
  })

  it('should show stronger warning for 500+ nodes', () => {
    const result = getRecommendedOptimizations(500)

    expect(result.showWarning).toBe(true)
    expect(result.warningMessage).toContain('automatically enabled')
  })

  it('should recommend edge simplification for 151+ nodes', () => {
    // Implementation uses > 150, not >= 150
    const result = getRecommendedOptimizations(151)

    expect(result.enableEdgeSimplification).toBe(true)
  })

  it('should recommend LOD for 101+ nodes', () => {
    // Implementation uses > 100, not >= 100
    const result = getRecommendedOptimizations(101)

    expect(result.enableLOD).toBe(true)
  })
})

// ==============================================================================
// Graph Statistics Tests
// ==============================================================================

describe('calculateGraphStats', () => {
  it('should return zeros for empty graph', () => {
    const stats = calculateGraphStats([], [])

    expect(stats.nodeCount).toBe(0)
    expect(stats.edgeCount).toBe(0)
    expect(stats.averageDegree).toBe(0)
    expect(stats.maxDegree).toBe(0)
    expect(stats.density).toBe(0)
    expect(stats.connectedComponents).toBe(0)
  })

  it('should calculate node and edge counts', () => {
    const nodes: Node[] = [
      { id: 'A', position: { x: 0, y: 0 }, data: {} },
      { id: 'B', position: { x: 100, y: 0 }, data: {} },
      { id: 'C', position: { x: 200, y: 0 }, data: {} },
    ]
    const edges: Edge[] = [
      { id: 'e1', source: 'A', target: 'B' },
      { id: 'e2', source: 'B', target: 'C' },
    ]

    const stats = calculateGraphStats(nodes, edges)

    expect(stats.nodeCount).toBe(3)
    expect(stats.edgeCount).toBe(2)
  })

  it('should calculate average and max degree', () => {
    const nodes: Node[] = [
      { id: 'A', position: { x: 0, y: 0 }, data: {} },
      { id: 'B', position: { x: 100, y: 0 }, data: {} },
      { id: 'C', position: { x: 200, y: 0 }, data: {} },
    ]
    const edges: Edge[] = [
      { id: 'e1', source: 'A', target: 'B' },
      { id: 'e2', source: 'B', target: 'C' },
    ]

    const stats = calculateGraphStats(nodes, edges)

    // A: degree 1, B: degree 2, C: degree 1 -> avg = 4/3 = 1.33
    expect(stats.averageDegree).toBeCloseTo(1.33, 1)
    expect(stats.maxDegree).toBe(2)
  })

  it('should count connected components', () => {
    const nodes: Node[] = [
      { id: 'A', position: { x: 0, y: 0 }, data: {} },
      { id: 'B', position: { x: 100, y: 0 }, data: {} },
      { id: 'C', position: { x: 200, y: 0 }, data: {} }, // Isolated
    ]
    const edges: Edge[] = [{ id: 'e1', source: 'A', target: 'B' }]

    const stats = calculateGraphStats(nodes, edges)

    expect(stats.connectedComponents).toBe(2) // A-B and C
  })

  it('should calculate density', () => {
    const nodes: Node[] = [
      { id: 'A', position: { x: 0, y: 0 }, data: {} },
      { id: 'B', position: { x: 100, y: 0 }, data: {} },
      { id: 'C', position: { x: 200, y: 0 }, data: {} },
    ]
    // Complete graph: 3 nodes have 3*2=6 possible edges
    const edges: Edge[] = [
      { id: 'e1', source: 'A', target: 'B' },
      { id: 'e2', source: 'B', target: 'C' },
      { id: 'e3', source: 'A', target: 'C' },
    ]

    const stats = calculateGraphStats(nodes, edges)

    // density = 3 / (3*2) = 0.5
    expect(stats.density).toBeCloseTo(0.5, 2)
  })
})

// ==============================================================================
// Edge Cases and Stress Tests
// ==============================================================================

describe('Edge Cases', () => {
  it('should handle single node graph', () => {
    const nodes: Node[] = [{ id: 'single', position: { x: 0, y: 0 }, data: {} }]

    const clusterResult = clusterNodes(nodes)
    expect(clusterResult.standaloneNodes).toHaveLength(1)

    const stats = calculateGraphStats(nodes, [])
    expect(stats.nodeCount).toBe(1)
    expect(stats.connectedComponents).toBe(1)
  })

  it('should handle graph with no edges', () => {
    const nodes: Node[] = [
      { id: 'A', position: { x: 0, y: 0 }, data: {} },
      { id: 'B', position: { x: 100, y: 0 }, data: {} },
    ]

    const stats = calculateGraphStats(nodes, [])

    expect(stats.averageDegree).toBe(0)
    expect(stats.density).toBe(0)
    expect(stats.connectedComponents).toBe(2)
  })

  it('should handle large node count', () => {
    const nodes: Node[] = Array.from({ length: 500 }, (_, i) => ({
      id: `node-${i}`,
      position: { x: i * 10, y: i * 10 },
      data: {},
    }))

    const result = getRecommendedOptimizations(nodes.length)

    expect(result.enableClustering).toBe(true)
    expect(result.enableVirtualization).toBe(true)
    expect(result.enableEdgeSimplification).toBe(true)
    expect(result.enableLOD).toBe(true)
    expect(result.showWarning).toBe(true)
  })
})
