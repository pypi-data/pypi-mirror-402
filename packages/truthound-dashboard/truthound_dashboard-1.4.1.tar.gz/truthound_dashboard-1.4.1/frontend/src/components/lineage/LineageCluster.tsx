/**
 * Cluster node component for representing multiple grouped nodes.
 *
 * Used for performance optimization when there are many nodes in close proximity.
 * Clicking on a cluster expands it to show individual nodes.
 */

import { memo } from 'react'
import { Handle, Position, type NodeProps } from 'reactflow'
import { Layers, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'

// ============================================================================
// Types
// ============================================================================

export interface LineageClusterData {
  /** IDs of nodes in this cluster */
  nodeIds: string[]
  /** Number of nodes in cluster */
  nodeCount: number
  /** Display label */
  label: string
  /** Whether cluster is expanded */
  expanded: boolean
  /** Center position of cluster */
  centroid: { x: number; y: number }
}

// ============================================================================
// Component
// ============================================================================

export const LineageCluster = memo(function LineageCluster({
  data,
  selected,
}: NodeProps<LineageClusterData>) {
  const { nodeCount, expanded } = data

  // Size based on node count
  const size = Math.min(80, 40 + Math.log2(nodeCount + 1) * 10)

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div
          className={cn(
            'group relative flex cursor-pointer items-center justify-center rounded-full border-2 transition-all hover:scale-105',
            'bg-gradient-to-br from-muted/50 to-muted',
            'border-primary/30 hover:border-primary/60',
            selected && 'ring-2 ring-primary ring-offset-2 ring-offset-background'
          )}
          style={{
            width: size,
            height: size,
          }}
        >
          {/* Input handle */}
          <Handle
            type="target"
            position={Position.Left}
            className="!w-2 !h-2 !bg-muted-foreground/50 !border-none"
          />

          {/* Cluster icon and count */}
          <div className="flex flex-col items-center gap-0.5">
            <Layers className="h-4 w-4 text-primary" />
            <span className="text-xs font-bold text-foreground">{nodeCount}</span>
          </div>

          {/* Expand indicator */}
          <ChevronRight
            className={cn(
              'absolute -right-1 top-1/2 h-3 w-3 -translate-y-1/2 transform text-muted-foreground transition-transform',
              expanded && 'rotate-90'
            )}
          />

          {/* Decorative rings for larger clusters */}
          {nodeCount >= 10 && (
            <>
              <div
                className="absolute inset-0 rounded-full border border-primary/10"
                style={{ transform: 'scale(1.2)' }}
              />
              {nodeCount >= 20 && (
                <div
                  className="absolute inset-0 rounded-full border border-primary/5"
                  style={{ transform: 'scale(1.4)' }}
                />
              )}
            </>
          )}

          {/* Output handle */}
          <Handle
            type="source"
            position={Position.Right}
            className="!w-2 !h-2 !bg-muted-foreground/50 !border-none"
          />
        </div>
      </TooltipTrigger>
      <TooltipContent side="top" className="max-w-xs">
        <div className="space-y-1">
          <p className="font-medium">
            {nodeCount} nodes clustered
          </p>
          <p className="text-xs text-muted-foreground">
            Click to {expanded ? 'collapse' : 'expand'} cluster
          </p>
          {nodeCount > 5 && (
            <div className="flex flex-wrap gap-1 pt-1">
              {data.nodeIds.slice(0, 5).map((id) => (
                <Badge key={id} variant="outline" className="text-xs">
                  {id.length > 10 ? `${id.slice(0, 10)}...` : id}
                </Badge>
              ))}
              {nodeCount > 5 && (
                <Badge variant="secondary" className="text-xs">
                  +{nodeCount - 5} more
                </Badge>
              )}
            </div>
          )}
        </div>
      </TooltipContent>
    </Tooltip>
  )
})

// ============================================================================
// Mini Cluster (for minimap)
// ============================================================================

interface MiniClusterProps {
  nodeCount: number
  x: number
  y: number
  highlighted?: boolean
}

export function MiniCluster({ nodeCount, x, y, highlighted }: MiniClusterProps) {
  const size = Math.min(12, 4 + Math.log2(nodeCount + 1) * 2)

  return (
    <circle
      cx={x}
      cy={y}
      r={size / 2}
      className={cn(
        'transition-all',
        highlighted
          ? 'fill-primary stroke-primary'
          : 'fill-muted-foreground/50 stroke-muted-foreground/30'
      )}
      strokeWidth={1}
    />
  )
}
