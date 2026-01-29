/**
 * Lazy-loaded node component for performance optimization.
 *
 * Shows a simplified placeholder initially and loads full details
 * on hover or click. Used for distant nodes in the viewport.
 */

import { memo, useState, useCallback } from 'react'
import { Handle, Position, type NodeProps } from 'reactflow'
import { Database, ArrowRightLeft, Archive, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import type { LineageNodeType } from '@/api/client'

// ============================================================================
// Types
// ============================================================================

export interface LazyLineageNodeData {
  label: string
  nodeType: LineageNodeType
  sourceId: string | null
  hasSource: boolean
}

type LoadState = 'idle' | 'loading' | 'loaded'

// ============================================================================
// Node Type Config
// ============================================================================

const nodeTypeConfig: Record<
  LineageNodeType,
  { icon: typeof Database; color: string; bgColor: string }
> = {
  source: {
    icon: Database,
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/10 border-blue-500/30',
  },
  transform: {
    icon: ArrowRightLeft,
    color: 'text-amber-500',
    bgColor: 'bg-amber-500/10 border-amber-500/30',
  },
  sink: {
    icon: Archive,
    color: 'text-green-500',
    bgColor: 'bg-green-500/10 border-green-500/30',
  },
}

// ============================================================================
// Component
// ============================================================================

export const LazyLineageNode = memo(function LazyLineageNode({
  data,
  selected,
}: NodeProps<LazyLineageNodeData>) {
  const [loadState, setLoadState] = useState<LoadState>('idle')
  const [isHovered, setIsHovered] = useState(false)

  const config = nodeTypeConfig[data.nodeType as LineageNodeType] || nodeTypeConfig.source
  const Icon = config.icon

  // Simulate loading additional data on hover
  const handleMouseEnter = useCallback(() => {
    setIsHovered(true)
    if (loadState === 'idle') {
      setLoadState('loading')
      // Simulate async load - in real implementation, this would fetch data
      setTimeout(() => {
        setLoadState('loaded')
      }, 200)
    }
  }, [loadState])

  const handleMouseLeave = useCallback(() => {
    setIsHovered(false)
  }, [])

  // Render simplified version (for distant nodes)
  const renderSimplified = () => (
    <div
      className={cn(
        'relative rounded-md border px-2 py-1.5 shadow-sm transition-all',
        config.bgColor,
        selected && 'ring-2 ring-primary ring-offset-1 ring-offset-background'
      )}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* Input handle */}
      {data.nodeType !== 'source' && (
        <Handle
          type="target"
          position={Position.Left}
          className="!w-2 !h-2 !bg-muted-foreground/50"
        />
      )}

      <div className="flex items-center gap-1.5">
        <Icon className={cn('h-3 w-3', config.color)} />
        <span className="max-w-[100px] truncate text-xs font-medium">
          {data.label}
        </span>
        {loadState === 'loading' && (
          <Loader2 className="h-2 w-2 animate-spin text-muted-foreground" />
        )}
      </div>

      {/* Output handle */}
      {data.nodeType !== 'sink' && (
        <Handle
          type="source"
          position={Position.Right}
          className="!w-2 !h-2 !bg-muted-foreground/50"
        />
      )}
    </div>
  )

  // Render full version (when hovered or selected)
  const renderFull = () => (
    <Tooltip open={isHovered}>
      <TooltipTrigger asChild>
        <div
          className={cn(
            'relative rounded-lg border-2 px-3 py-2 shadow-md transition-all',
            config.bgColor,
            selected && 'ring-2 ring-primary ring-offset-2 ring-offset-background'
          )}
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
        >
          {/* Input handle */}
          {data.nodeType !== 'source' && (
            <Handle
              type="target"
              position={Position.Left}
              className="!w-3 !h-3 !bg-muted-foreground/50"
            />
          )}

          <div className="flex items-center gap-2">
            <div className={cn('rounded-md p-1.5', config.bgColor)}>
              <Icon className={cn('h-4 w-4', config.color)} />
            </div>

            <div className="flex flex-col">
              <span className="text-sm font-medium text-foreground">
                {data.label}
              </span>
              <span className="text-xs capitalize text-muted-foreground">
                {data.nodeType}
              </span>
            </div>
          </div>

          {/* Output handle */}
          {data.nodeType !== 'sink' && (
            <Handle
              type="source"
              position={Position.Right}
              className="!w-3 !h-3 !bg-muted-foreground/50"
            />
          )}
        </div>
      </TooltipTrigger>
      <TooltipContent side="top" className="max-w-xs">
        <div className="space-y-1">
          <p className="font-medium">{data.label}</p>
          <p className="text-xs capitalize text-muted-foreground">
            Type: {data.nodeType}
          </p>
          {data.hasSource && (
            <p className="text-xs text-muted-foreground">
              Linked to data source
            </p>
          )}
        </div>
      </TooltipContent>
    </Tooltip>
  )

  // Show full version when hovered, selected, or data is loaded
  if (isHovered || selected || loadState === 'loaded') {
    return renderFull()
  }

  return renderSimplified()
})

// ============================================================================
// Placeholder Node (for skeleton loading)
// ============================================================================

export function PlaceholderNode() {
  return (
    <div className="rounded-md border bg-muted/30 px-3 py-2">
      <div className="flex items-center gap-2">
        <div className="h-8 w-8 animate-pulse rounded-md bg-muted" />
        <div className="space-y-1">
          <div className="h-3 w-20 animate-pulse rounded bg-muted" />
          <div className="h-2 w-14 animate-pulse rounded bg-muted" />
        </div>
      </div>
    </div>
  )
}
