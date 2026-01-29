/**
 * Custom edge component for React Flow lineage visualization.
 *
 * Renders animated edges with different styles based on edge type.
 */

import { memo } from 'react'
import { EdgeLabelRenderer, getBezierPath, type EdgeProps } from 'reactflow'
import type { LineageEdgeType } from '@/api/client'

export interface LineageEdgeData {
  edgeType: LineageEdgeType
  label?: string
}

const edgeTypeConfig: Record<LineageEdgeType, { stroke: string; label: string }> = {
  derives_from: { stroke: '#60a5fa', label: 'derives from' }, // blue-400
  transforms_to: { stroke: '#fbbf24', label: 'transforms to' }, // amber-400
  feeds_into: { stroke: '#4ade80', label: 'feeds into' }, // green-400
}

export const LineageEdge = memo(function LineageEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  selected,
}: EdgeProps<LineageEdgeData>) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  })

  const config = data?.edgeType ? edgeTypeConfig[data.edgeType] : edgeTypeConfig.derives_from

  return (
    <>
      <path
        id={id}
        d={edgePath}
        fill="none"
        stroke={selected ? 'hsl(var(--primary))' : config.stroke}
        strokeWidth={selected ? 3 : 2}
        strokeDasharray={data?.edgeType === 'transforms_to' ? '5 5' : undefined}
        markerEnd="url(#arrowhead)"
        style={{ transition: 'stroke 0.2s, stroke-width 0.2s' }}
      />

      {/* Edge label (shown on hover or selection) */}
      {selected && data?.label && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: 'all',
            }}
            className="rounded bg-background/90 px-2 py-1 text-xs text-muted-foreground shadow-sm border"
          >
            {data.label || config.label}
          </div>
        </EdgeLabelRenderer>
      )}

      {/* Custom marker definition */}
      <defs>
        <marker
          id="arrowhead"
          markerWidth="10"
          markerHeight="7"
          refX="9"
          refY="3.5"
          orient="auto"
        >
          <polygon points="0 0, 10 3.5, 0 7" fill="#9ca3af" />
        </marker>
      </defs>
    </>
  )
})
