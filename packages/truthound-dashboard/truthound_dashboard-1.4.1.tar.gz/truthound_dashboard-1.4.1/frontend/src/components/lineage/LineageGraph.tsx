/**
 * Main lineage graph component using React Flow.
 *
 * Renders an interactive DAG visualization of data lineage.
 * Automatically enables performance optimizations for large graphs (100+ nodes).
 */

import { useCallback, useEffect, useMemo, useState } from 'react'
import ReactFlow, {
  Background,
  MiniMap,
  Panel,
  useNodesState,
  useEdgesState,
  addEdge,
  type Connection,
  type Node,
  type Edge,
  type NodeTypes,
  type EdgeTypes,
  ReactFlowProvider,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { useIntlayer } from 'react-intlayer'
import { AlertTriangle, Zap } from 'lucide-react'
import { TooltipProvider } from '@/components/ui/tooltip'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/hooks/use-toast'
import { str } from '@/lib/intlayer-utils'
import { useLineagePerformance } from '@/hooks/useLineagePerformance'
import { LineageNode, type LineageNodeData } from './LineageNode'
import { LazyLineageNode } from './LazyLineageNode'
import { LineageCluster } from './LineageCluster'
import { LineageEdge, type LineageEdgeData } from './LineageEdge'
import { LineageMinimap } from './LineageMinimap'
import { LineageControls } from './LineageControls'
import { LineageToolbar } from './LineageToolbar'
import { LineageNodeDetails } from './LineageNodeDetails'
import { ImpactAnalysisPanel } from './ImpactAnalysisPanel'
import type {
  LineageNode as LineageNodeType,
  LineageGraph as LineageGraphType,
  ImpactAnalysisResponse,
} from '@/api/client'
import {
  getLineageGraph,
  createLineageNode,
  deleteLineageNode,
  autoDiscoverLineage,
  updateNodePositions,
  analyzeLineageImpact,
} from '@/api/client'

// Custom node types (standard mode)
const nodeTypes: NodeTypes = {
  lineageNode: LineageNode,
}

// Custom node types (performance mode - uses lazy loading)
const performanceNodeTypes: NodeTypes = {
  lineageNode: LazyLineageNode,
  cluster: LineageCluster,
}

// Custom edge types
const edgeTypes: EdgeTypes = {
  lineageEdge: LineageEdge,
}

interface LineageGraphProps {
  sourceId?: string
  className?: string
  /** Force performance mode on/off */
  forcePerformanceMode?: boolean
}

function LineageGraphInner({ sourceId: _sourceId, className, forcePerformanceMode }: LineageGraphProps) {
  const t = useIntlayer('lineage')
  const { toast } = useToast()

  // State
  const [lineageData, setLineageData] = useState<LineageGraphType | null>(null)
  const [nodes, setNodes, onNodesChange] = useNodesState<LineageNodeData>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<LineageEdgeData>([])
  const [selectedNode, setSelectedNode] = useState<LineageNodeType | null>(null)
  const [impactAnalysis, setImpactAnalysis] = useState<ImpactAnalysisResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isDiscovering, setIsDiscovering] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  // Performance monitoring
  const {
    metrics,
    isPerformanceMode,
    setPerformanceMode,
    recommendations,
  } = useLineagePerformance(nodes.length)

  // Apply forced performance mode if specified
  useEffect(() => {
    if (forcePerformanceMode !== undefined) {
      setPerformanceMode(forcePerformanceMode)
    }
  }, [forcePerformanceMode, setPerformanceMode])

  // Select node types based on performance mode
  const activeNodeTypes = useMemo(
    () => (isPerformanceMode ? performanceNodeTypes : nodeTypes),
    [isPerformanceMode]
  )

  // Load lineage data
  const loadLineageData = useCallback(async () => {
    setIsLoading(true)
    try {
      const data = await getLineageGraph()
      setLineageData(data)

      // Convert to React Flow nodes
      const flowNodes: Node<LineageNodeData>[] = data.nodes.map((node) => ({
        id: node.id,
        type: 'lineageNode',
        position: {
          x: node.position_x ?? Math.random() * 600,
          y: node.position_y ?? Math.random() * 400,
        },
        data: {
          label: node.name,
          nodeType: node.node_type,
          sourceId: node.source_id,
          hasSource: !!node.source_id,
        },
      }))

      // Convert to React Flow edges
      const flowEdges: Edge<LineageEdgeData>[] = data.edges.map((edge) => ({
        id: edge.id,
        source: edge.source_node_id,
        target: edge.target_node_id,
        type: 'lineageEdge',
        data: {
          edgeType: edge.edge_type,
        },
      }))

      setNodes(flowNodes)
      setEdges(flowEdges)
    } catch (error) {
      toast({
        title: str(t.errorLoadingLineage),
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }, [setNodes, setEdges, toast, t])

  useEffect(() => {
    loadLineageData()
  }, [loadLineageData])

  // Handle node selection
  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      const nodeData = lineageData?.nodes.find((n) => n.id === node.id)
      setSelectedNode(nodeData ?? null)
      setImpactAnalysis(null)
    },
    [lineageData]
  )

  // Handle add node
  const handleAddNode = useCallback(
    async (name: string, nodeType: LineageNodeType['node_type']) => {
      try {
        const newNode = await createLineageNode({
          name,
          node_type: nodeType,
        })

        // Add to React Flow
        const flowNode: Node<LineageNodeData> = {
          id: newNode.id,
          type: 'lineageNode',
          position: { x: 300, y: 200 },
          data: {
            label: newNode.name,
            nodeType: newNode.node_type,
            sourceId: newNode.source_id,
            hasSource: !!newNode.source_id,
          },
        }

        setNodes((nds: Node<LineageNodeData>[]) => [...nds, flowNode])
        setLineageData((prev) =>
          prev ? { ...prev, nodes: [...prev.nodes, newNode] } : null
        )

        toast({ title: str(t.nodeCreated) })
      } catch (error) {
        toast({
          title: str(t.errorCreatingNode),
          variant: 'destructive',
        })
      }
    },
    [setNodes, toast, t]
  )

  // Handle delete node
  const handleDeleteNode = useCallback(
    async (nodeId: string) => {
      try {
        await deleteLineageNode(nodeId)

        setNodes((nds: Node<LineageNodeData>[]) => nds.filter((n: Node<LineageNodeData>) => n.id !== nodeId))
        setEdges((eds: Edge<LineageEdgeData>[]) =>
          eds.filter((e: Edge<LineageEdgeData>) => e.source !== nodeId && e.target !== nodeId)
        )
        setLineageData((prev) =>
          prev
            ? {
                ...prev,
                nodes: prev.nodes.filter((n) => n.id !== nodeId),
                edges: prev.edges.filter(
                  (e) => e.source_node_id !== nodeId && e.target_node_id !== nodeId
                ),
              }
            : null
        )
        setSelectedNode(null)

        toast({ title: str(t.nodeDeleted) })
      } catch (error) {
        toast({
          title: str(t.errorDeletingNode),
          variant: 'destructive',
        })
      }
    },
    [setNodes, setEdges, toast, t]
  )

  // Handle auto-discover
  const handleAutoDiscover = useCallback(async () => {
    setIsDiscovering(true)
    try {
      const result = await autoDiscoverLineage()
      toast({
        title: str(t.discoveryComplete),
        description: `${result.nodes_created} ${str(t.nodesDiscovered)}, ${result.edges_created} ${str(t.edgesDiscovered)}`,
      })
      loadLineageData()
    } catch (error) {
      toast({
        title: str(t.discoveryFailed),
        variant: 'destructive',
      })
    } finally {
      setIsDiscovering(false)
    }
  }, [loadLineageData, toast, t])

  // Handle save positions
  const handleSavePositions = useCallback(async () => {
    setIsSaving(true)
    try {
      const updates = nodes.map((node: Node<LineageNodeData>) => ({
        node_id: node.id,
        position_x: node.position.x,
        position_y: node.position.y,
      }))
      await updateNodePositions(updates)
      toast({ title: str(t.positionsSaved) })
    } catch (error) {
      toast({
        title: str(t.errorSavingPositions),
        variant: 'destructive',
      })
    } finally {
      setIsSaving(false)
    }
  }, [nodes, toast, t])

  // Handle impact analysis
  const handleAnalyzeImpact = useCallback(
    async (nodeId: string) => {
      setIsAnalyzing(true)
      try {
        const analysis = await analyzeLineageImpact(nodeId)
        setImpactAnalysis(analysis)
      } catch (error) {
        toast({
          title: 'Failed to analyze impact',
          variant: 'destructive',
        })
      } finally {
        setIsAnalyzing(false)
      }
    },
    [toast]
  )

  // Handle new connection
  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds: Edge<LineageEdgeData>[]) =>
        addEdge(
          {
            ...params,
            type: 'lineageEdge',
            data: { edgeType: 'derives_from' },
          },
          eds
        )
      )
    },
    [setEdges]
  )

  // Empty state
  if (!isLoading && lineageData && lineageData.nodes.length === 0) {
    return (
      <div className="flex h-[500px] flex-col items-center justify-center gap-4 rounded-lg border-2 border-dashed">
        <p className="text-lg font-medium">{t.noLineageYet}</p>
        <p className="text-muted-foreground">{t.noLineageDesc}</p>
        <LineageToolbar
          onAddNode={handleAddNode}
          onAutoDiscover={handleAutoDiscover}
          onSavePositions={handleSavePositions}
          onRefresh={loadLineageData}
          isDiscovering={isDiscovering}
          isSaving={isSaving}
        />
      </div>
    )
  }

  // Handle performance mode toggle
  const handlePerformanceModeToggle = useCallback(
    (checked: boolean) => {
      setPerformanceMode(checked)
    },
    [setPerformanceMode]
  )

  return (
    <TooltipProvider>
      <div className={`flex h-[600px] gap-4 ${className ?? ''}`}>
        {/* Performance warning for large graphs */}
        {recommendations.showWarning && !isPerformanceMode && (
          <Alert className="absolute top-2 left-2 z-10 max-w-md">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              {recommendations.warningMessage}
            </AlertDescription>
          </Alert>
        )}

        {/* Main graph area */}
        <div className="relative flex-1 rounded-lg border">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            nodeTypes={activeNodeTypes}
            edgeTypes={edgeTypes}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            defaultEdgeOptions={{ type: 'lineageEdge' }}
            minZoom={0.1}
            maxZoom={2}
          >
            <Background />

            {/* Use custom minimap in performance mode, standard otherwise */}
            {isPerformanceMode ? (
              <LineageMinimap
                nodes={nodes}
                edges={edges}
                visibleNodeIds={new Set(nodes.map((n) => n.id))}
              />
            ) : (
              <MiniMap
                nodeStrokeWidth={3}
                zoomable
                pannable
                className="!bg-background"
              />
            )}

            <LineageControls />

            <Panel position="top-left">
              <LineageToolbar
                onAddNode={handleAddNode}
                onAutoDiscover={handleAutoDiscover}
                onSavePositions={handleSavePositions}
                onRefresh={loadLineageData}
                isDiscovering={isDiscovering}
                isSaving={isSaving}
              />
            </Panel>

            <Panel position="top-right">
              <div className="flex flex-col gap-2 rounded-md bg-background/90 px-3 py-2 text-sm shadow-sm">
                {/* Node/Edge counts */}
                <div className="flex items-center gap-2">
                  <span>{str(t.totalNodes)}: {lineageData?.total_nodes ?? 0}</span>
                  <span className="text-muted-foreground">|</span>
                  <span>{str(t.totalEdges)}: {lineageData?.total_edges ?? 0}</span>
                </div>

                {/* Performance mode toggle */}
                {(recommendations.enableVirtualization || isPerformanceMode) && (
                  <div className="flex items-center gap-2 border-t pt-2">
                    <Switch
                      id="perf-mode"
                      checked={isPerformanceMode}
                      onCheckedChange={handlePerformanceModeToggle}
                    />
                    <Label
                      htmlFor="perf-mode"
                      className="flex cursor-pointer items-center gap-1 text-xs"
                    >
                      <Zap className="h-3 w-3" />
                      {str(t.performanceMode)}
                    </Label>
                    {isPerformanceMode && (
                      <Badge variant="secondary" className="text-xs">
                        FPS: {metrics.fps}
                      </Badge>
                    )}
                  </div>
                )}
              </div>
            </Panel>
          </ReactFlow>
        </div>

        {/* Side panel */}
        <div className="w-80 space-y-4 overflow-y-auto rounded-lg border">
          <LineageNodeDetails
            node={selectedNode}
            edges={lineageData?.edges ?? []}
            allNodes={lineageData?.nodes ?? []}
            onDelete={handleDeleteNode}
            onAnalyzeImpact={handleAnalyzeImpact}
          />

          {impactAnalysis && (
            <div className="px-4">
              <ImpactAnalysisPanel
                analysis={impactAnalysis}
                isLoading={isAnalyzing}
              />
            </div>
          )}
        </div>
      </div>
    </TooltipProvider>
  )
}

// Export with ReactFlowProvider wrapper
export function LineageGraph(props: LineageGraphProps) {
  return (
    <ReactFlowProvider>
      <LineageGraphInner {...props} />
    </ReactFlowProvider>
  )
}
