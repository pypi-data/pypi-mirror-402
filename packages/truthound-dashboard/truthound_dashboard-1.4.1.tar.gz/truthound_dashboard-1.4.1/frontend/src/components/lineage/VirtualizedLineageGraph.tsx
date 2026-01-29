/**
 * Virtualized lineage graph component for large graph performance.
 *
 * Renders only visible nodes within the viewport and implements
 * level-of-detail (LOD) rendering for optimal performance with 500+ nodes.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import ReactFlow, {
  Background,
  Panel,
  useReactFlow,
  useViewport,
  type Node,
  type Edge,
  type NodeTypes,
  type EdgeTypes,
  type OnNodesChange,
  type OnEdgesChange,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { useIntlayer } from 'react-intlayer'
import { AlertTriangle, Zap } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { str } from '@/lib/intlayer-utils'
import {
  getVisibleNodes,
  filterVisibleEdges,
  clusterNodes,
  expandCluster,
  getNodeLOD,
  getRecommendedOptimizations,
  PERFORMANCE_THRESHOLDS,
  type ClusteredNode,
} from '@/lib/lineage-performance'
import { LineageNode, type LineageNodeData } from './LineageNode'
import { LazyLineageNode } from './LazyLineageNode'
import { LineageCluster } from './LineageCluster'
import { LineageEdge, type LineageEdgeData } from './LineageEdge'
import { LineageMinimap } from './LineageMinimap'
import { LineageControls } from './LineageControls'
import { useLineagePerformance } from '@/hooks/useLineagePerformance'

// ============================================================================
// Types
// ============================================================================

interface VirtualizedLineageGraphProps {
  /** All nodes in the graph */
  nodes: Node<LineageNodeData>[]
  /** All edges in the graph */
  edges: Edge<LineageEdgeData>[]
  /** Callback when nodes change */
  onNodesChange: OnNodesChange
  /** Callback when edges change */
  onEdgesChange: OnEdgesChange
  /** Callback when a node is clicked */
  onNodeClick?: (event: React.MouseEvent, node: Node) => void
  /** Enable performance mode by default */
  defaultPerformanceMode?: boolean
  /** Custom class name */
  className?: string
}

// ============================================================================
// Node Type Registry
// ============================================================================

const createNodeTypes = (lod: 'full' | 'simplified' | 'minimal'): NodeTypes => ({
  lineageNode: lod === 'full' ? LineageNode : LazyLineageNode,
  cluster: LineageCluster,
})

const edgeTypes: EdgeTypes = {
  lineageEdge: LineageEdge,
}

// ============================================================================
// Component
// ============================================================================

export function VirtualizedLineageGraph({
  nodes: allNodes,
  edges: allEdges,
  onNodesChange,
  onEdgesChange,
  onNodeClick,
  defaultPerformanceMode,
  className,
}: VirtualizedLineageGraphProps) {
  const t = useIntlayer('lineage')
  const containerRef = useRef<HTMLDivElement>(null)
  useReactFlow() // Keep for potential future use
  const viewport = useViewport()

  // Performance tracking
  const { metrics, isPerformanceMode, setPerformanceMode, recordFrame } =
    useLineagePerformance(allNodes.length)

  // Get recommended optimizations based on node count
  const recommendations = useMemo(
    () => getRecommendedOptimizations(allNodes.length),
    [allNodes.length]
  )

  // Auto-enable performance mode for large graphs
  useEffect(() => {
    if (defaultPerformanceMode !== undefined) {
      setPerformanceMode(defaultPerformanceMode)
    } else if (allNodes.length >= PERFORMANCE_THRESHOLDS.VIRTUALIZATION_THRESHOLD) {
      setPerformanceMode(true)
    }
  }, [allNodes.length, defaultPerformanceMode, setPerformanceMode])

  // Container dimensions
  const [containerSize, setContainerSize] = useState({ width: 800, height: 600 })

  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        setContainerSize({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        })
      }
    }

    updateSize()
    window.addEventListener('resize', updateSize)
    return () => window.removeEventListener('resize', updateSize)
  }, [])

  // Clustering state
  const [clusteredData, setClusteredData] = useState<{
    clusters: ClusteredNode[]
    standaloneNodes: Node<LineageNodeData>[]
    clusterMap: Map<string, string>
  } | null>(null)

  const [expandedClusters, setExpandedClusters] = useState<Set<string>>(new Set())

  // Original nodes map for cluster expansion
  const originalNodesMap = useMemo(() => {
    const map = new Map<string, Node<LineageNodeData>>()
    allNodes.forEach((node) => map.set(node.id, node))
    return map
  }, [allNodes])

  // Cluster nodes when performance mode is enabled
  useEffect(() => {
    if (isPerformanceMode && recommendations.enableClustering) {
      const result = clusterNodes(allNodes, PERFORMANCE_THRESHOLDS.CLUSTER_DISTANCE)
      setClusteredData(result)
    } else {
      setClusteredData(null)
    }
  }, [allNodes, isPerformanceMode, recommendations.enableClustering])

  // Calculate visible nodes based on viewport
  const visibleData = useMemo(() => {
    recordFrame()

    if (!isPerformanceMode) {
      return { nodes: allNodes, edges: allEdges }
    }

    let nodesToRender: Node<LineageNodeData | ClusteredNode['data']>[] = []

    if (clusteredData) {
      // Add standalone nodes
      nodesToRender = [...clusteredData.standaloneNodes]

      // Add clusters or expanded nodes
      clusteredData.clusters.forEach((cluster) => {
        if (expandedClusters.has(cluster.id)) {
          // Add expanded nodes
          const expanded = expandCluster(cluster, originalNodesMap)
          nodesToRender.push(...expanded)
        } else {
          // Add cluster node
          nodesToRender.push({
            id: cluster.id,
            type: 'cluster',
            position: cluster.position,
            data: cluster.data,
          } as Node<ClusteredNode['data']>)
        }
      })
    } else {
      nodesToRender = allNodes
    }

    // Apply viewport culling
    const visible = getVisibleNodes(
      viewport,
      nodesToRender,
      containerSize.width,
      containerSize.height
    )

    // Limit max visible nodes
    const limitedNodes = visible.slice(0, PERFORMANCE_THRESHOLDS.MAX_VISIBLE_NODES)

    // Filter edges to visible nodes
    const visibleNodeIds = new Set(limitedNodes.map((n) => n.id))

    // Add cluster member IDs to visible set for edge filtering
    if (clusteredData) {
      clusteredData.clusters.forEach((cluster) => {
        if (visibleNodeIds.has(cluster.id)) {
          cluster.data.nodeIds.forEach((id) => visibleNodeIds.add(id))
        }
      })
    }

    const visibleEdges = filterVisibleEdges(allEdges, visibleNodeIds)

    return { nodes: limitedNodes, edges: visibleEdges }
  }, [
    isPerformanceMode,
    clusteredData,
    expandedClusters,
    originalNodesMap,
    allNodes,
    allEdges,
    viewport,
    containerSize,
    recordFrame,
  ])

  // Get LOD-based node types
  const lod = getNodeLOD(viewport.zoom)
  const nodeTypes = useMemo(() => createNodeTypes(lod), [lod])

  // Handle cluster click
  const handleNodeClick = useCallback(
    (event: React.MouseEvent, node: Node) => {
      if (node.type === 'cluster') {
        setExpandedClusters((prev) => {
          const next = new Set(prev)
          if (next.has(node.id)) {
            next.delete(node.id)
          } else {
            next.add(node.id)
          }
          return next
        })
      } else {
        onNodeClick?.(event, node)
      }
    },
    [onNodeClick]
  )

  // Toggle performance mode
  const handlePerformanceModeToggle = useCallback(
    (checked: boolean) => {
      setPerformanceMode(checked)
      if (!checked) {
        setExpandedClusters(new Set())
      }
    },
    [setPerformanceMode]
  )

  return (
    <div ref={containerRef} className={`relative h-full w-full ${className ?? ''}`}>
      {/* Performance warning */}
      {recommendations.showWarning && !isPerformanceMode && (
        <Alert className="absolute top-2 left-2 right-2 z-10 max-w-md">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{recommendations.warningMessage}</AlertDescription>
        </Alert>
      )}

      <ReactFlow
        nodes={visibleData.nodes}
        edges={visibleData.edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        defaultEdgeOptions={{ type: 'lineageEdge' }}
        minZoom={0.1}
        maxZoom={2}
      >
        <Background />
        <LineageControls />

        {/* Performance mode minimap */}
        {isPerformanceMode && (
          <LineageMinimap
            nodes={allNodes}
            edges={allEdges}
            visibleNodeIds={new Set(visibleData.nodes.map((n) => n.id))}
          />
        )}

        {/* Performance stats panel */}
        <Panel position="top-right">
          <div className="flex flex-col gap-2 rounded-md bg-background/90 px-3 py-2 text-sm shadow-sm">
            {/* Node count */}
            <div className="flex items-center gap-2">
              <span>
                {str(t.totalNodes)}: {allNodes.length}
              </span>
              {isPerformanceMode && (
                <Badge variant="secondary" className="text-xs">
                  {visibleData.nodes.length} visible
                </Badge>
              )}
            </div>

            <span className="text-muted-foreground">|</span>

            <span>
              {str(t.totalEdges)}: {allEdges.length}
            </span>

            {/* Performance mode toggle */}
            <div className="flex items-center gap-2 border-t pt-2">
              <Switch
                id="performance-mode"
                checked={isPerformanceMode}
                onCheckedChange={handlePerformanceModeToggle}
              />
              <Label
                htmlFor="performance-mode"
                className="flex cursor-pointer items-center gap-1 text-xs"
              >
                <Zap className="h-3 w-3" />
                {str(t.performanceMode)}
              </Label>
            </div>

            {/* FPS indicator */}
            {isPerformanceMode && (
              <div className="text-xs text-muted-foreground">
                FPS: {metrics.fps} | Clusters: {clusteredData?.clusters.length ?? 0}
              </div>
            )}
          </div>
        </Panel>
      </ReactFlow>
    </div>
  )
}
