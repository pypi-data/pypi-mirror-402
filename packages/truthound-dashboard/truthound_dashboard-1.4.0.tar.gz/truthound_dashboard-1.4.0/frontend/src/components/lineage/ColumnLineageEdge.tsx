/**
 * Custom edge component that shows column mappings when selected.
 *
 * Displays transformation information and column flow.
 */

import { memo, useState } from 'react'
import { EdgeLabelRenderer, getBezierPath, type EdgeProps } from 'reactflow'
import { useIntlayer } from 'react-intlayer'
import { ChevronDown, ChevronUp, ArrowRight, Columns } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { LineageEdgeType } from '@/api/client'
import type { ColumnMapping, ColumnTransformationType } from './column-lineage-types'

export interface ColumnLineageEdgeData {
  edgeType: LineageEdgeType
  label?: string
  columnMappings?: ColumnMapping[]
}

// Edge type styles
const edgeTypeConfig: Record<LineageEdgeType, { stroke: string; label: string }> = {
  derives_from: { stroke: '#60a5fa', label: 'derives from' },
  transforms_to: { stroke: '#fbbf24', label: 'transforms to' },
  feeds_into: { stroke: '#4ade80', label: 'feeds into' },
}

// Transformation type colors for the badge
const transformationColors: Record<ColumnTransformationType, string> = {
  direct: 'bg-blue-500/20 text-blue-600 dark:text-blue-400',
  derived: 'bg-purple-500/20 text-purple-600 dark:text-purple-400',
  aggregated: 'bg-amber-500/20 text-amber-600 dark:text-amber-400',
  filtered: 'bg-green-500/20 text-green-600 dark:text-green-400',
  joined: 'bg-pink-500/20 text-pink-600 dark:text-pink-400',
  renamed: 'bg-cyan-500/20 text-cyan-600 dark:text-cyan-400',
  cast: 'bg-orange-500/20 text-orange-600 dark:text-orange-400',
  computed: 'bg-indigo-500/20 text-indigo-600 dark:text-indigo-400',
}

export const ColumnLineageEdge = memo(function ColumnLineageEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  selected,
}: EdgeProps<ColumnLineageEdgeData>) {
  const t = useIntlayer('lineage')
  const [showMappings, setShowMappings] = useState(false)

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  })

  const config = data?.edgeType ? edgeTypeConfig[data.edgeType] : edgeTypeConfig.derives_from
  const mappings = data?.columnMappings ?? []
  const hasMappings = mappings.length > 0

  // Group mappings by transformation type
  const mappingsByType = mappings.reduce(
    (acc, mapping) => {
      const type = mapping.transformationType
      if (!acc[type]) {
        acc[type] = 0
      }
      acc[type]++
      return acc
    },
    {} as Record<ColumnTransformationType, number>
  )

  // Get primary transformation type (most common)
  const primaryType = Object.entries(mappingsByType).sort((a, b) => b[1] - a[1])[0]?.[0] as
    | ColumnTransformationType
    | undefined

  return (
    <>
      {/* Edge path */}
      <path
        id={id}
        d={edgePath}
        fill="none"
        stroke={selected ? 'hsl(var(--primary))' : config.stroke}
        strokeWidth={selected ? 3 : hasMappings ? 2.5 : 2}
        strokeDasharray={data?.edgeType === 'transforms_to' ? '5 5' : undefined}
        markerEnd="url(#arrowhead-column)"
        style={{ transition: 'stroke 0.2s, stroke-width 0.2s' }}
        className={cn(hasMappings && !selected && 'animate-pulse')}
      />

      {/* Column count indicator (always visible if mappings exist) */}
      {hasMappings && !selected && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: 'all',
            }}
            className="flex items-center gap-1 rounded-full bg-background/95 px-2 py-0.5 text-xs shadow-sm border cursor-pointer hover:bg-muted"
            onClick={() => setShowMappings(!showMappings)}
          >
            <Columns className="h-3 w-3 text-muted-foreground" />
            <span className="font-medium">{mappings.length}</span>
            {primaryType && (
              <Badge
                variant="outline"
                className={cn('h-4 px-1 text-[10px]', transformationColors[primaryType])}
              >
                {primaryType}
              </Badge>
            )}
          </div>
        </EdgeLabelRenderer>
      )}

      {/* Expanded mapping details (when selected) */}
      {selected && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: 'all',
            }}
            className="rounded-lg bg-background/95 shadow-lg border min-w-[200px] max-w-[300px]"
          >
            {/* Header */}
            <button
              onClick={() => setShowMappings(!showMappings)}
              className="flex w-full items-center justify-between px-3 py-2 hover:bg-muted/50 rounded-t-lg"
            >
              <div className="flex items-center gap-2">
                <Columns className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">
                  {hasMappings
                    ? `${mappings.length} ${t.columnLineage.columnMappings}`
                    : t.columnLineage.noColumnMappings}
                </span>
              </div>
              {hasMappings && (showMappings ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              ))}
            </button>

            {/* Mapping list */}
            {showMappings && hasMappings && (
              <div className="border-t max-h-[200px] overflow-y-auto">
                {mappings.slice(0, 10).map((mapping, idx) => (
                  <div
                    key={`${mapping.sourceColumn}-${mapping.targetColumn}-${idx}`}
                    className="flex items-center gap-2 px-3 py-1.5 text-xs border-b last:border-b-0 hover:bg-muted/30"
                  >
                    <span className="font-mono text-blue-600 dark:text-blue-400 truncate flex-1">
                      {mapping.sourceColumn}
                    </span>
                    <ArrowRight className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                    <span className="font-mono text-green-600 dark:text-green-400 truncate flex-1">
                      {mapping.targetColumn}
                    </span>
                    <Badge
                      variant="outline"
                      className={cn(
                        'h-4 px-1 text-[9px] flex-shrink-0',
                        transformationColors[mapping.transformationType]
                      )}
                    >
                      {mapping.transformationType.slice(0, 4)}
                    </Badge>
                  </div>
                ))}
                {mappings.length > 10 && (
                  <div className="px-3 py-2 text-xs text-muted-foreground text-center">
                    +{mappings.length - 10} {t.columnLineage.moreMappings}
                  </div>
                )}
              </div>
            )}

            {/* Edge type label */}
            <div className="px-3 py-1.5 text-[10px] text-muted-foreground border-t bg-muted/20 rounded-b-lg">
              {data?.label || config.label}
            </div>
          </div>
        </EdgeLabelRenderer>
      )}

      {/* Custom marker definition */}
      <defs>
        <marker
          id="arrowhead-column"
          markerWidth="10"
          markerHeight="7"
          refX="9"
          refY="3.5"
          orient="auto"
        >
          <polygon points="0 0, 10 3.5, 0 7" fill={selected ? 'hsl(var(--primary))' : '#9ca3af'} />
        </marker>
      </defs>
    </>
  )
})
