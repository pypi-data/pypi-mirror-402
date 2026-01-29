/**
 * Custom minimap component for lineage graph navigation.
 *
 * Shows an overview of the entire graph with:
 * - All nodes as small dots
 * - Viewport indicator rectangle
 * - Click-to-navigate functionality
 */

import { memo, useCallback, useMemo, useRef } from 'react'
import { useReactFlow, useViewport, type Node, type Edge } from 'reactflow'
import { cn } from '@/lib/utils'
import type { LineageNodeData } from './LineageNode'
import type { LineageEdgeData } from './LineageEdge'

// ============================================================================
// Types
// ============================================================================

interface LineageMinimapProps {
  /** All nodes in the graph */
  nodes: Node<LineageNodeData>[]
  /** All edges in the graph */
  edges: Edge<LineageEdgeData>[]
  /** Set of currently visible node IDs */
  visibleNodeIds: Set<string>
  /** Minimap width (default: 200) */
  width?: number
  /** Minimap height (default: 150) */
  height?: number
  /** Custom class name */
  className?: string
}

// ============================================================================
// Constants
// ============================================================================

const MINIMAP_PADDING = 20
const NODE_RADIUS = 3
const VISIBLE_NODE_RADIUS = 4

// ============================================================================
// Component
// ============================================================================

export const LineageMinimap = memo(function LineageMinimap({
  nodes,
  edges,
  visibleNodeIds,
  width = 200,
  height = 150,
  className,
}: LineageMinimapProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const { setViewport, fitView } = useReactFlow()
  const viewport = useViewport()

  // Calculate bounds of all nodes
  const bounds = useMemo(() => {
    if (nodes.length === 0) {
      return { minX: 0, maxX: 100, minY: 0, maxY: 100 }
    }

    let minX = Infinity
    let maxX = -Infinity
    let minY = Infinity
    let maxY = -Infinity

    nodes.forEach((node) => {
      minX = Math.min(minX, node.position.x)
      maxX = Math.max(maxX, node.position.x + 180) // Approx node width
      minY = Math.min(minY, node.position.y)
      maxY = Math.max(maxY, node.position.y + 60) // Approx node height
    })

    // Add padding
    return {
      minX: minX - MINIMAP_PADDING,
      maxX: maxX + MINIMAP_PADDING,
      minY: minY - MINIMAP_PADDING,
      maxY: maxY + MINIMAP_PADDING,
    }
  }, [nodes])

  // Calculate scale to fit all nodes in minimap
  const scale = useMemo(() => {
    const graphWidth = bounds.maxX - bounds.minX
    const graphHeight = bounds.maxY - bounds.minY
    const scaleX = (width - 10) / graphWidth
    const scaleY = (height - 10) / graphHeight
    return Math.min(scaleX, scaleY, 1)
  }, [bounds, width, height])

  // Transform graph coordinates to minimap coordinates
  const toMinimapCoords = useCallback(
    (x: number, y: number) => ({
      x: (x - bounds.minX) * scale + 5,
      y: (y - bounds.minY) * scale + 5,
    }),
    [bounds, scale]
  )

  // Calculate viewport rectangle in minimap coordinates
  const viewportRect = useMemo(() => {
    // Assume container size (this should ideally be passed in)
    const containerWidth = 800
    const containerHeight = 600

    const graphMinX = (-viewport.x) / viewport.zoom
    const graphMinY = (-viewport.y) / viewport.zoom
    const graphMaxX = graphMinX + containerWidth / viewport.zoom
    const graphMaxY = graphMinY + containerHeight / viewport.zoom

    const topLeft = toMinimapCoords(graphMinX, graphMinY)
    const bottomRight = toMinimapCoords(graphMaxX, graphMaxY)

    return {
      x: topLeft.x,
      y: topLeft.y,
      width: Math.max(20, bottomRight.x - topLeft.x),
      height: Math.max(15, bottomRight.y - topLeft.y),
    }
  }, [viewport, toMinimapCoords])

  // Handle click to navigate
  const handleClick = useCallback(
    (event: React.MouseEvent<SVGSVGElement>) => {
      const svg = svgRef.current
      if (!svg) return

      const rect = svg.getBoundingClientRect()
      const x = event.clientX - rect.left
      const y = event.clientY - rect.top

      // Convert minimap coordinates to graph coordinates
      const graphX = (x - 5) / scale + bounds.minX
      const graphY = (y - 5) / scale + bounds.minY

      // Center the viewport on clicked position
      const containerWidth = 800
      const containerHeight = 600

      setViewport({
        x: -graphX * viewport.zoom + containerWidth / 2,
        y: -graphY * viewport.zoom + containerHeight / 2,
        zoom: viewport.zoom,
      })
    },
    [scale, bounds, viewport.zoom, setViewport]
  )

  // Handle double-click to fit view
  const handleDoubleClick = useCallback(() => {
    fitView({ padding: 0.2, duration: 500 })
  }, [fitView])

  // Node type colors
  const getNodeColor = (nodeType: string, isVisible: boolean) => {
    if (!isVisible) return 'rgb(156 163 175 / 0.3)' // gray-400/30

    switch (nodeType) {
      case 'source':
        return 'rgb(96 165 250)' // blue-400
      case 'transform':
        return 'rgb(251 191 36)' // amber-400
      case 'sink':
        return 'rgb(74 222 128)' // green-400
      default:
        return 'rgb(156 163 175)' // gray-400
    }
  }

  if (nodes.length === 0) {
    return null
  }

  return (
    <div
      className={cn(
        'absolute bottom-4 left-4 overflow-hidden rounded-md border bg-background/90 shadow-md',
        className
      )}
      style={{ width, height }}
    >
      <svg
        ref={svgRef}
        width={width}
        height={height}
        className="cursor-crosshair"
        onClick={handleClick}
        onDoubleClick={handleDoubleClick}
      >
        {/* Background */}
        <rect width={width} height={height} className="fill-muted/30" />

        {/* Edges */}
        <g className="stroke-muted-foreground/20" strokeWidth={0.5}>
          {edges.slice(0, 500).map((edge) => {
            const sourceNode = nodes.find((n) => n.id === edge.source)
            const targetNode = nodes.find((n) => n.id === edge.target)

            if (!sourceNode || !targetNode) return null

            const source = toMinimapCoords(
              sourceNode.position.x + 90,
              sourceNode.position.y + 30
            )
            const target = toMinimapCoords(
              targetNode.position.x + 90,
              targetNode.position.y + 30
            )

            return (
              <line
                key={edge.id}
                x1={source.x}
                y1={source.y}
                x2={target.x}
                y2={target.y}
              />
            )
          })}
        </g>

        {/* Nodes */}
        <g>
          {nodes.map((node) => {
            const pos = toMinimapCoords(node.position.x + 90, node.position.y + 30)
            const isVisible = visibleNodeIds.has(node.id)
            const color = getNodeColor(node.data.nodeType, isVisible)
            const radius = isVisible ? VISIBLE_NODE_RADIUS : NODE_RADIUS

            return (
              <circle
                key={node.id}
                cx={pos.x}
                cy={pos.y}
                r={radius}
                fill={color}
                className="transition-all duration-150"
              />
            )
          })}
        </g>

        {/* Viewport indicator */}
        <rect
          x={viewportRect.x}
          y={viewportRect.y}
          width={viewportRect.width}
          height={viewportRect.height}
          className="fill-primary/10 stroke-primary"
          strokeWidth={1.5}
          rx={2}
        />
      </svg>

      {/* Stats overlay */}
      <div className="absolute bottom-1 right-1 rounded bg-background/80 px-1 py-0.5 text-[10px] text-muted-foreground">
        {nodes.length} nodes
      </div>
    </div>
  )
})
