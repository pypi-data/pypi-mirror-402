/**
 * Lineage page - Data lineage visualization with multiple renderer support.
 *
 * Supports React Flow (default), Cytoscape.js (performance), and Mermaid (export).
 * Includes performance optimizations for large graphs (500+ nodes).
 */

import { useCallback, useEffect, useState } from 'react'
import { useIntlayer } from '@/providers'
import { Loader2, BarChart3, Zap, AlertTriangle, Columns, Table2, Grid3X3 } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'
import { str } from '@/lib/intlayer-utils'
import {
  LineageGraph,
  LineageToolbar,
  LineageNodeDetails,
  ImpactAnalysisPanel,
  OpenLineageExport,
  OpenLineageConfig,
  LineageRendererSelector,
  CytoscapeLineageGraph,
  MermaidLineageGraph,
  LineageExportPanel,
  AnomalyLegend,
  ColumnLineagePanel,
  ColumnMappingTable,
  ColumnImpactAnalysis,
  type LineageRenderer,
  type AnomalyStatusLevel,
  type ColumnMapping,
  type LineageColumn,
  type ColumnImpactResult,
} from '@/components/lineage'
import { TooltipProvider } from '@/components/ui/tooltip'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
// Tabs imported but not currently used in main view - keeping for potential future use
// import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { PERFORMANCE_THRESHOLDS } from '@/lib/lineage-performance'
import type {
  LineageNode,
  LineageGraph as LineageGraphType,
  ImpactAnalysisResponse,
} from '@/api/client'
import {
  getLineageGraph,
  createLineageNode,
  deleteLineageNode,
  autoDiscoverLineage,
  analyzeLineageImpact,
} from '@/api/client'

// Local storage key for renderer preference
const RENDERER_PREFERENCE_KEY = 'lineage-renderer-preference'

export default function Lineage() {
  const t = useIntlayer('lineage')
  const { toast } = useToast()

  // State
  const [lineageData, setLineageData] = useState<LineageGraphType | null>(null)
  const [selectedNode, setSelectedNode] = useState<LineageNode | null>(null)
  const [impactAnalysis, setImpactAnalysis] = useState<ImpactAnalysisResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isDiscovering, setIsDiscovering] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  // Renderer state - load from localStorage
  const [renderer, setRenderer] = useState<LineageRenderer>(() => {
    const saved = localStorage.getItem(RENDERER_PREFERENCE_KEY)
    return (saved as LineageRenderer) || 'reactflow'
  })

  // Performance mode state (undefined = auto, true/false = forced)
  const [forcePerformanceMode, setForcePerformanceMode] = useState<boolean | undefined>(undefined)

  // Anomaly overlay state
  const [showAnomalyOverlay, setShowAnomalyOverlay] = useState(false)
  const [showAnomalyLegend, setShowAnomalyLegend] = useState(true)
  const [showImpactPaths, setShowImpactPaths] = useState(true)
  const [anomalyStatusFilter, setAnomalyStatusFilter] = useState<AnomalyStatusLevel[]>([
    'unknown', 'clean', 'low', 'medium', 'high'
  ])

  // Column lineage state
  const [showColumnLineage, setShowColumnLineage] = useState(false)
  const [columnLineageView, setColumnLineageView] = useState<'graph' | 'table'>('graph')
  const [_selectedColumn, setSelectedColumn] = useState<string | null>(null)
  const [columnMappings, setColumnMappings] = useState<ColumnMapping[]>([])
  const [nodeColumns, setNodeColumns] = useState<Record<string, LineageColumn[]>>({})
  const [columnImpact, setColumnImpact] = useState<ColumnImpactResult | null>(null)
  const [isLoadingColumnData, setIsLoadingColumnData] = useState(false)

  // Check if graph is large enough to warrant performance warning
  const isLargeGraph = (lineageData?.total_nodes ?? 0) >= PERFORMANCE_THRESHOLDS.WARNING_THRESHOLD

  // Save renderer preference to localStorage
  const handleRendererChange = useCallback(
    (newRenderer: LineageRenderer) => {
      setRenderer(newRenderer)
      localStorage.setItem(RENDERER_PREFERENCE_KEY, newRenderer)
      toast({ title: str(t.savedRendererPreference) })
    },
    [toast, t]
  )

  // Handle manual performance mode toggle
  const handleForcePerformanceMode = useCallback((checked: boolean) => {
    setForcePerformanceMode(checked ? true : undefined)
  }, [])

  // Load lineage data
  const loadLineageData = useCallback(async () => {
    setIsLoading(true)
    try {
      const data = await getLineageGraph()
      setLineageData(data)
    } catch (error) {
      toast({
        title: str(t.errorLoadingLineage),
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }, [toast, t])

  useEffect(() => {
    loadLineageData()
  }, [loadLineageData])

  // Handle node selection
  const handleNodeClick = useCallback(
    (node: LineageNode) => {
      setSelectedNode(node)
      setImpactAnalysis(null)
    },
    []
  )

  // Handle add node
  const handleAddNode = useCallback(
    async (name: string, nodeType: LineageNode['node_type']) => {
      try {
        const newNode = await createLineageNode({
          name,
          node_type: nodeType,
        })

        setLineageData((prev) =>
          prev
            ? {
                ...prev,
                nodes: [...prev.nodes, newNode],
                total_nodes: prev.total_nodes + 1,
              }
            : null
        )

        toast({ title: str(t.nodeCreated) })
      } catch (error) {
        toast({
          title: str(t.errorCreatingNode),
          variant: 'destructive',
        })
      }
    },
    [toast, t]
  )

  // Handle delete node
  const handleDeleteNode = useCallback(
    async (nodeId: string) => {
      try {
        await deleteLineageNode(nodeId)

        setLineageData((prev) =>
          prev
            ? {
                ...prev,
                nodes: prev.nodes.filter((n) => n.id !== nodeId),
                edges: prev.edges.filter(
                  (e) => e.source_node_id !== nodeId && e.target_node_id !== nodeId
                ),
                total_nodes: prev.total_nodes - 1,
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
    [toast, t]
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

  // Load column lineage data when enabled
  const loadColumnLineageData = useCallback(async () => {
    if (!lineageData || !showColumnLineage) return

    setIsLoadingColumnData(true)
    try {
      // Load columns for all nodes
      const columnsMap: Record<string, LineageColumn[]> = {}
      const mappings: ColumnMapping[] = []

      // Fetch columns for each node
      for (const node of lineageData.nodes) {
        try {
          const response = await fetch(`/api/v1/lineage/nodes/${node.id}/columns`)
          if (response.ok) {
            const data = await response.json()
            columnsMap[node.id] = data.columns || []
          }
        } catch {
          // Ignore individual node errors
        }
      }

      // Fetch column mappings for each edge
      for (const edge of lineageData.edges) {
        try {
          const response = await fetch(`/api/v1/lineage/edges/${edge.id}/column-mappings`)
          if (response.ok) {
            const data = await response.json()
            mappings.push(...(data.mappings || []))
          }
        } catch {
          // Ignore individual edge errors
        }
      }

      setNodeColumns(columnsMap)
      setColumnMappings(mappings)
    } catch (error) {
      toast({
        title: str(t.columnLineage?.errorLoadingData ?? 'Failed to load column lineage'),
        variant: 'destructive',
      })
    } finally {
      setIsLoadingColumnData(false)
    }
  }, [lineageData, showColumnLineage, toast, t])

  // Load column data when column lineage is enabled
  useEffect(() => {
    if (showColumnLineage) {
      loadColumnLineageData()
    }
  }, [showColumnLineage, loadColumnLineageData])

  // Handle column click for impact analysis
  const handleColumnClick = useCallback(
    async (nodeId: string, columnName: string) => {
      setSelectedColumn(`${nodeId}:${columnName}`)
      try {
        const response = await fetch(
          `/api/v1/lineage/columns/impact?node_id=${nodeId}&column_name=${columnName}`
        )
        if (response.ok) {
          const data = await response.json()
          setColumnImpact(data)
        }
      } catch {
        // Ignore errors
      }
    },
    []
  )

  // Handle column mapping click
  const handleMappingClick = useCallback((mapping: ColumnMapping) => {
    setSelectedColumn(`${mapping.sourceNodeId}:${mapping.sourceColumn}`)
  }, [])

  // Loading state
  if (isLoading) {
    return (
      <div className="flex h-[600px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  // Empty state
  if (lineageData && lineageData.nodes.length === 0) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">{t.title}</h1>
            <p className="text-muted-foreground">{t.subtitle}</p>
          </div>
          <div className="flex items-center gap-2">
            <LineageRendererSelector value={renderer} onChange={handleRendererChange} />
            <OpenLineageConfig />
            <OpenLineageExport />
          </div>
        </div>

        <div className="flex h-[500px] flex-col items-center justify-center gap-4 rounded-lg border-2 border-dashed">
          <p className="text-lg font-medium">{t.noLineageYet}</p>
          <p className="text-muted-foreground">{t.noLineageDesc}</p>
          <LineageToolbar
            onAddNode={handleAddNode}
            onAutoDiscover={handleAutoDiscover}
            onSavePositions={() => {}}
            onRefresh={loadLineageData}
            isDiscovering={isDiscovering}
            isSaving={false}
          />
        </div>
      </div>
    )
  }

  return (
    <TooltipProvider>
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div>
              <h1 className="text-2xl font-bold">{t.title}</h1>
              <p className="text-muted-foreground">{t.subtitle}</p>
            </div>
            {/* Large graph indicator */}
            {isLargeGraph && (
              <Badge variant="secondary" className="text-xs">
                {lineageData?.total_nodes} nodes
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2">
            {/* Column lineage toggle */}
            <Button
              variant={showColumnLineage ? 'default' : 'outline'}
              size="sm"
              onClick={() => setShowColumnLineage(!showColumnLineage)}
              className={showColumnLineage ? 'bg-blue-500 hover:bg-blue-600' : ''}
            >
              <Columns className="mr-2 h-4 w-4" />
              {showColumnLineage
                ? (t.columnLineage?.hideColumnLineage ?? 'Hide Columns')
                : (t.columnLineage?.showColumnLineage ?? 'Show Columns')}
            </Button>

            {/* Column view toggle - only show when column lineage is enabled */}
            {showColumnLineage && (
              <div className="flex items-center rounded-md border">
                <Button
                  variant={columnLineageView === 'graph' ? 'secondary' : 'ghost'}
                  size="sm"
                  className="rounded-r-none"
                  onClick={() => setColumnLineageView('graph')}
                >
                  <Grid3X3 className="h-4 w-4" />
                </Button>
                <Button
                  variant={columnLineageView === 'table' ? 'secondary' : 'ghost'}
                  size="sm"
                  className="rounded-l-none"
                  onClick={() => setColumnLineageView('table')}
                >
                  <Table2 className="h-4 w-4" />
                </Button>
              </div>
            )}

            {/* Anomaly overlay toggle */}
            <Button
              variant={showAnomalyOverlay ? 'default' : 'outline'}
              size="sm"
              onClick={() => setShowAnomalyOverlay(!showAnomalyOverlay)}
              className={showAnomalyOverlay ? 'bg-orange-500 hover:bg-orange-600' : ''}
            >
              <AlertTriangle className="mr-2 h-4 w-4" />
              {showAnomalyOverlay
                ? (t.anomaly?.hideAnomalies ?? 'Hide Anomalies')
                : (t.anomaly?.showAnomalies ?? 'Show Anomalies')}
            </Button>

            {/* Performance info popover */}
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" size="sm">
                  <BarChart3 className="mr-2 h-4 w-4" />
                  {str(t.performanceInfo)}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-80">
                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium">{str(t.performanceOptimizations)}</h4>
                    <p className="text-sm text-muted-foreground">
                      {str(t.performanceOptimizationsDesc)}
                    </p>
                  </div>

                  {/* Thresholds info */}
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>{str(t.clusteringThreshold)}</span>
                      <span className="font-mono">
                        {PERFORMANCE_THRESHOLDS.CLUSTERING_THRESHOLD} nodes
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>{str(t.virtualizationThreshold)}</span>
                      <span className="font-mono">
                        {PERFORMANCE_THRESHOLDS.VIRTUALIZATION_THRESHOLD} nodes
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>{str(t.warningThreshold)}</span>
                      <span className="font-mono">
                        {PERFORMANCE_THRESHOLDS.WARNING_THRESHOLD} nodes
                      </span>
                    </div>
                  </div>

                  {/* Manual override */}
                  <div className="flex items-center justify-between border-t pt-4">
                    <Label htmlFor="force-perf" className="flex items-center gap-2">
                      <Zap className="h-4 w-4" />
                      {str(t.forcePerformanceMode)}
                    </Label>
                    <Switch
                      id="force-perf"
                      checked={forcePerformanceMode ?? false}
                      onCheckedChange={handleForcePerformanceMode}
                    />
                  </div>
                </div>
              </PopoverContent>
            </Popover>

            <LineageRendererSelector value={renderer} onChange={handleRendererChange} />
            <LineageExportPanel
              nodes={lineageData?.nodes ?? []}
              edges={lineageData?.edges ?? []}
            />
            <OpenLineageConfig />
            <OpenLineageExport />
          </div>
        </div>

        {/* Main content area */}
        <div className="relative flex gap-4 h-[600px]">
          {/* Graph/Table area */}
          <div className="flex-1 rounded-lg border overflow-hidden">
            {/* Column lineage table view */}
            {showColumnLineage && columnLineageView === 'table' ? (
              <div className="h-full overflow-auto p-4">
                {isLoadingColumnData ? (
                  <div className="flex h-full items-center justify-center">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  </div>
                ) : (
                  <ColumnMappingTable
                    mappings={columnMappings}
                    nodes={new Map((lineageData?.nodes ?? []).map(n => [n.id, n.name]))}
                    onRowClick={handleMappingClick}
                  />
                )}
              </div>
            ) : (
              <>
                {renderer === 'reactflow' && (
                  <LineageGraph
                    className="h-full"
                    forcePerformanceMode={forcePerformanceMode}
                  />
                )}

                {renderer === 'cytoscape' && lineageData && (
                  <CytoscapeLineageGraph
                    nodes={lineageData.nodes}
                    edges={lineageData.edges}
                    onNodeClick={handleNodeClick}
                    className="h-full"
                  />
                )}

                {renderer === 'mermaid' && lineageData && (
                  <MermaidLineageGraph
                    nodes={lineageData.nodes}
                    edges={lineageData.edges}
                    onNodeClick={handleNodeClick}
                    className="h-full"
                  />
                )}
              </>
            )}
          </div>

          {/* Side panel - show for cytoscape/mermaid OR when column lineage is enabled */}
          {(renderer !== 'reactflow' || showColumnLineage) && (
            <div className="w-80 space-y-4 overflow-y-auto rounded-lg border p-4">
              {/* Node details for non-reactflow renderers */}
              {renderer !== 'reactflow' && (
                <>
                  <LineageNodeDetails
                    node={selectedNode}
                    edges={lineageData?.edges ?? []}
                    allNodes={lineageData?.nodes ?? []}
                    columns={selectedNode ? nodeColumns[selectedNode.id] : undefined}
                    columnMappings={columnMappings}
                    onDelete={handleDeleteNode}
                    onAnalyzeImpact={handleAnalyzeImpact}
                    onColumnClick={(columnName) =>
                      selectedNode && handleColumnClick(selectedNode.id, columnName)
                    }
                    onColumnImpactAnalysis={(columnName) =>
                      selectedNode && handleColumnClick(selectedNode.id, columnName)
                    }
                  />

                  {impactAnalysis && (
                    <ImpactAnalysisPanel
                      analysis={impactAnalysis}
                      isLoading={isAnalyzing}
                    />
                  )}
                </>
              )}

              {/* Column lineage panel */}
              {showColumnLineage && (
                <>
                  <ColumnLineagePanel
                    mappings={columnMappings}
                    onColumnClick={handleMappingClick}
                  />

                  {/* Column impact analysis */}
                  {columnImpact && (
                    <ColumnImpactAnalysis
                      result={columnImpact}
                      onColumnSelect={(nodeId: string, columnName: string) =>
                        handleColumnClick(nodeId, columnName)
                      }
                    />
                  )}
                </>
              )}
            </div>
          )}

          {/* Anomaly legend - floating panel when anomaly overlay is enabled */}
          {showAnomalyOverlay && (
            <div className="absolute bottom-4 left-4 z-10">
              <AnomalyLegend
                showLegend={showAnomalyLegend}
                onToggleLegend={() => setShowAnomalyLegend(!showAnomalyLegend)}
                selectedStatuses={anomalyStatusFilter}
                onStatusFilterChange={setAnomalyStatusFilter}
                showImpactPaths={showImpactPaths}
                onToggleImpactPaths={() => setShowImpactPaths(!showImpactPaths)}
              />
            </div>
          )}
        </div>
      </div>
    </TooltipProvider>
  )
}
