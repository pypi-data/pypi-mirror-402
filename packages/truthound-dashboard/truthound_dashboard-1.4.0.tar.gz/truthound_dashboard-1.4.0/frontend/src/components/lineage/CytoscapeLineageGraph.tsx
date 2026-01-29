/**
 * Cytoscape.js based lineage graph renderer.
 *
 * Optimized for large-scale graphs (1000+ nodes) with multiple layout options.
 */

import { useEffect, useRef, useCallback, useState } from 'react'
import cytoscape, { Core } from 'cytoscape'
// @ts-expect-error - cytoscape-dagre has no type declarations
import dagre from 'cytoscape-dagre'
import { useIntlayer } from 'react-intlayer'
import { ZoomIn, ZoomOut, Maximize2, LayoutGrid } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { cn } from '@/lib/utils'
import {
  graphToCytoscape,
  getCytoscapeLayoutConfig,
  type CytoscapeLayout,
} from '@/lib/lineage-utils'
import type { LineageNode, LineageEdge } from '@/api/client'

// Register the dagre layout extension
cytoscape.use(dagre)

interface CytoscapeLineageGraphProps {
  nodes: LineageNode[]
  edges: LineageEdge[]
  onNodeClick?: (node: LineageNode) => void
  className?: string
}

// Color configurations for node types
const nodeColors = {
  source: {
    bg: '#3b82f6',
    border: '#1d4ed8',
    text: '#ffffff',
  },
  transform: {
    bg: '#f59e0b',
    border: '#d97706',
    text: '#ffffff',
  },
  sink: {
    bg: '#22c55e',
    border: '#16a34a',
    text: '#ffffff',
  },
}

// Edge colors by type
const edgeColors = {
  derives_from: '#6b7280',
  transforms_to: '#f59e0b',
  feeds_into: '#22c55e',
}

export function CytoscapeLineageGraph({
  nodes,
  edges,
  onNodeClick,
  className,
}: CytoscapeLineageGraphProps) {
  const t = useIntlayer('lineage')
  const containerRef = useRef<HTMLDivElement>(null)
  const cyRef = useRef<Core | null>(null)
  const [layout, setLayout] = useState<CytoscapeLayout>('dagre')
  const [isInitialized, setIsInitialized] = useState(false)

  // Create node lookup map for click handling
  const nodeMap = useRef<Map<string, LineageNode>>(new Map())

  useEffect(() => {
    nodeMap.current = new Map(nodes.map((n) => [n.id, n]))
  }, [nodes])

  // Initialize Cytoscape instance
  useEffect(() => {
    if (!containerRef.current) return

    const elements = graphToCytoscape(nodes, edges)

    // Create Cytoscape elements array
    const cyElements: cytoscape.ElementDefinition[] = [
      ...elements.nodes.map((n) => ({
        group: 'nodes' as const,
        data: n.data,
        position: n.position,
      })),
      ...elements.edges.map((e) => ({
        group: 'edges' as const,
        data: e.data,
      })),
    ]

    // Create Cytoscape instance
    const cy = cytoscape({
      container: containerRef.current,
      elements: cyElements,
      style: [
        // Node styles
        {
          selector: 'node',
          style: {
            'background-color': (ele) => {
              const nodeType = ele.data('nodeType') as keyof typeof nodeColors
              return nodeColors[nodeType]?.bg || '#6b7280'
            },
            'border-color': (ele) => {
              const nodeType = ele.data('nodeType') as keyof typeof nodeColors
              return nodeColors[nodeType]?.border || '#4b5563'
            },
            'border-width': 2,
            label: 'data(label)',
            color: '#fff',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': 12,
            'font-weight': 500,
            width: 120,
            height: 40,
            shape: (ele) => {
              const nodeType = ele.data('nodeType')
              switch (nodeType) {
                case 'source':
                  return 'barrel'
                case 'transform':
                  return 'hexagon'
                case 'sink':
                  return 'rectangle'
                default:
                  return 'rectangle'
              }
            },
            'text-wrap': 'ellipsis',
            'text-max-width': '100px',
          },
        },
        // Selected node style
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#fd9e4b',
            'overlay-opacity': 0.2,
            'overlay-color': '#fd9e4b',
          },
        },
        // Hovered node style
        {
          selector: 'node:active',
          style: {
            'border-width': 3,
            opacity: 0.9,
          },
        },
        // Edge styles
        {
          selector: 'edge',
          style: {
            width: 2,
            'line-color': (ele) => {
              const edgeType = ele.data('edgeType') as keyof typeof edgeColors
              return edgeColors[edgeType] || '#6b7280'
            },
            'target-arrow-color': (ele) => {
              const edgeType = ele.data('edgeType') as keyof typeof edgeColors
              return edgeColors[edgeType] || '#6b7280'
            },
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'arrow-scale': 1.2,
          },
        },
        // Selected edge style
        {
          selector: 'edge:selected',
          style: {
            width: 3,
            'line-color': '#fd9e4b',
            'target-arrow-color': '#fd9e4b',
          },
        },
      ],
      layout: getCytoscapeLayoutConfig(layout),
      // Performance settings for large graphs
      minZoom: 0.1,
      maxZoom: 4,
      wheelSensitivity: 0.3,
      boxSelectionEnabled: false,
      autounselectify: false,
    })

    // Handle node click
    cy.on('tap', 'node', (evt) => {
      const nodeId = evt.target.id()
      const node = nodeMap.current.get(nodeId)
      if (node && onNodeClick) {
        onNodeClick(node)
      }
    })

    cyRef.current = cy
    setIsInitialized(true)

    return () => {
      cy.destroy()
      cyRef.current = null
      setIsInitialized(false)
    }
  }, [nodes, edges, onNodeClick])

  // Update layout when changed
  useEffect(() => {
    if (!cyRef.current || !isInitialized) return

    const layoutConfig = getCytoscapeLayoutConfig(layout)
    cyRef.current.layout(layoutConfig).run()
  }, [layout, isInitialized])

  // Control functions
  const handleZoomIn = useCallback(() => {
    if (cyRef.current) {
      cyRef.current.zoom(cyRef.current.zoom() * 1.2)
    }
  }, [])

  const handleZoomOut = useCallback(() => {
    if (cyRef.current) {
      cyRef.current.zoom(cyRef.current.zoom() / 1.2)
    }
  }, [])

  const handleFit = useCallback(() => {
    if (cyRef.current) {
      cyRef.current.fit(undefined, 50)
    }
  }, [])

  const handleReLayout = useCallback(() => {
    if (cyRef.current) {
      const layoutConfig = getCytoscapeLayoutConfig(layout)
      cyRef.current.layout(layoutConfig).run()
    }
  }, [layout])

  // Export to PNG
  const exportToPng = useCallback(() => {
    if (!cyRef.current) return null
    return cyRef.current.png({
      output: 'blob',
      scale: 2,
      bg: 'transparent',
      full: true,
    })
  }, [])

  // Expose export function via ref or callback
  useEffect(() => {
    // Store export function for external access if needed
    (window as unknown as { __cytoscapeExportPng?: () => Blob | null }).__cytoscapeExportPng = exportToPng
    return () => {
      delete (window as unknown as { __cytoscapeExportPng?: () => Blob | null }).__cytoscapeExportPng
    }
  }, [exportToPng])

  return (
    <div className={cn('relative flex flex-col', className)}>
      {/* Toolbar */}
      <div className="flex items-center gap-2 p-2 border-b bg-background">
        <Select value={layout} onValueChange={(v) => setLayout(v as CytoscapeLayout)}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder={t.layouts.selectLayout} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="dagre">{t.layouts.dagre}</SelectItem>
            <SelectItem value="breadthfirst">{t.layouts.breadthfirst}</SelectItem>
            <SelectItem value="cose">{t.layouts.cose}</SelectItem>
            <SelectItem value="circle">{t.layouts.circle}</SelectItem>
            <SelectItem value="grid">{t.layouts.grid}</SelectItem>
            <SelectItem value="concentric">{t.layouts.concentric}</SelectItem>
          </SelectContent>
        </Select>

        <div className="flex items-center gap-1 ml-auto">
          <Button variant="ghost" size="icon" onClick={handleZoomIn} title={String(t.zoomIn)}>
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={handleZoomOut} title={String(t.zoomOut)}>
            <ZoomOut className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={handleFit} title={String(t.fitView)}>
            <Maximize2 className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={handleReLayout} title={String(t.autoLayout)}>
            <LayoutGrid className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Graph container */}
      <div
        ref={containerRef}
        className="flex-1 min-h-[500px] bg-background"
        style={{ width: '100%' }}
      />

      {/* Stats overlay */}
      <div className="absolute bottom-4 right-4 flex gap-2 rounded-md bg-background/90 px-3 py-1.5 text-sm shadow">
        <span>{t.totalNodes}: {nodes.length}</span>
        <span className="text-muted-foreground">|</span>
        <span>{t.totalEdges}: {edges.length}</span>
      </div>
    </div>
  )
}
