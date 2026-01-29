/**
 * Custom node component for React Flow lineage visualization.
 *
 * Renders different styles based on node type (source, transform, sink).
 * Supports column-level lineage display with expandable column list.
 * Supports anomaly overlay mode for visualizing data quality status.
 */

import { memo, useState } from 'react'
import { Handle, Position, type NodeProps } from 'reactflow'
import { Database, ArrowRightLeft, Archive, ExternalLink, Columns, ChevronDown, ChevronRight, AlertTriangle, CheckCircle, AlertCircle, HelpCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import type { LineageNodeType } from '@/api/client'
import type { LineageColumn } from './column-lineage-types'

export type AnomalyStatusLevel = 'unknown' | 'clean' | 'low' | 'medium' | 'high'

export interface AnomalyStatus {
  status: AnomalyStatusLevel
  anomaly_rate: number | null
  anomaly_count: number | null
  last_detection_at: string | null
  algorithm: string | null
}

export interface LineageNodeData {
  label: string
  nodeType: LineageNodeType
  sourceId: string | null
  hasSource: boolean
  columns?: LineageColumn[]
  columnCount?: number
  showColumnLineage?: boolean
  onColumnSelect?: (columnName: string) => void
  // Anomaly overlay properties
  anomalyStatus?: AnomalyStatus
  showAnomalyOverlay?: boolean
  isImpacted?: boolean
  impactSeverity?: string
}

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

const anomalyStatusConfig: Record<
  AnomalyStatusLevel,
  {
    icon: typeof AlertTriangle
    color: string
    bgColor: string
    label: string
  }
> = {
  unknown: {
    icon: HelpCircle,
    color: 'text-muted-foreground',
    bgColor: 'bg-muted/50',
    label: 'No detection',
  },
  clean: {
    icon: CheckCircle,
    color: 'text-green-500',
    bgColor: 'bg-green-500/10',
    label: 'Clean',
  },
  low: {
    icon: AlertCircle,
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-500/10',
    label: 'Low anomalies',
  },
  medium: {
    icon: AlertTriangle,
    color: 'text-orange-500',
    bgColor: 'bg-orange-500/10',
    label: 'Medium anomalies',
  },
  high: {
    icon: AlertTriangle,
    color: 'text-red-500',
    bgColor: 'bg-red-500/10',
    label: 'High anomalies',
  },
}

export const LineageNode = memo(function LineageNode({
  data,
  selected,
}: NodeProps<LineageNodeData>) {
  const [isExpanded, setIsExpanded] = useState(false)
  const config = nodeTypeConfig[data.nodeType as LineageNodeType] || nodeTypeConfig.source
  const Icon = config.icon

  const columnCount = data.columnCount ?? data.columns?.length ?? 0
  const showColumnBadge = data.showColumnLineage && columnCount > 0
  const showColumnList = isExpanded && data.columns && data.columns.length > 0

  // Anomaly overlay support
  const showAnomalyOverlay = data.showAnomalyOverlay ?? false
  const anomalyStatus = data.anomalyStatus?.status || 'unknown'
  const anomalyConfig = anomalyStatusConfig[anomalyStatus]
  const AnomalyIcon = anomalyConfig.icon

  // Determine border color based on anomaly status
  const getAnomalyBorderColor = () => {
    if (!showAnomalyOverlay) return ''
    if (data.isImpacted) return 'border-orange-500/70'
    switch (anomalyStatus) {
      case 'high':
        return 'border-red-500/70'
      case 'medium':
        return 'border-orange-500/50'
      case 'low':
        return 'border-yellow-500/50'
      case 'clean':
        return 'border-green-500/50'
      default:
        return ''
    }
  }

  const formatPercentage = (rate: number | null) => {
    if (rate === null) return 'N/A'
    return `${(rate * 100).toFixed(1)}%`
  }

  const formatTimestamp = (timestamp: string | null) => {
    if (!timestamp) return 'Never'
    const date = new Date(timestamp)
    return date.toLocaleString()
  }

  const handleToggleExpand = (e: React.MouseEvent) => {
    e.stopPropagation()
    setIsExpanded(!isExpanded)
  }

  const nodeContent = (
    <div
      className={cn(
        'relative rounded-lg border-2 shadow-md transition-all min-w-[180px]',
        config.bgColor,
        getAnomalyBorderColor(),
        data.isImpacted && showAnomalyOverlay && 'animate-pulse',
        selected && 'ring-2 ring-primary ring-offset-2 ring-offset-background'
      )}
    >
      {/* Input handle (not for source nodes) */}
      {data.nodeType !== 'source' && (
        <Handle
          type="target"
          position={Position.Left}
          className="!w-3 !h-3 !bg-muted-foreground/50"
        />
      )}

      {/* Main content */}
      <div className="px-4 py-3">
        <div className="flex items-center gap-3">
          <div className={cn('rounded-md p-2', config.bgColor)}>
            <Icon className={cn('h-4 w-4', config.color)} />
          </div>

          <div className="flex flex-col flex-1 min-w-0">
            <span className="text-sm font-medium text-foreground truncate">
              {data.label}
            </span>
            <span className="text-xs text-muted-foreground capitalize">
              {data.nodeType}
            </span>
          </div>

          <div className="flex items-center gap-1">
            {data.hasSource && (
              <ExternalLink className="h-3 w-3 text-muted-foreground" />
            )}
            {showColumnBadge && (
              <button
                onClick={handleToggleExpand}
                className="flex items-center gap-1 rounded-md px-1.5 py-0.5 hover:bg-muted/50 transition-colors"
              >
                <Columns className="h-3 w-3 text-muted-foreground" />
                <Badge variant="secondary" className="h-4 px-1 text-[10px]">
                  {columnCount}
                </Badge>
                {data.columns && data.columns.length > 0 && (
                  isExpanded ? (
                    <ChevronDown className="h-3 w-3 text-muted-foreground" />
                  ) : (
                    <ChevronRight className="h-3 w-3 text-muted-foreground" />
                  )
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Expandable column list */}
      {showColumnList && (
        <div className="border-t px-2 py-2 max-h-[150px] overflow-y-auto">
          <div className="space-y-0.5">
            {data.columns!.slice(0, 10).map((col) => (
              <button
                key={col.name}
                onClick={(e) => {
                  e.stopPropagation()
                  data.onColumnSelect?.(col.name)
                }}
                className={cn(
                  'flex items-center justify-between w-full px-2 py-1 rounded text-xs hover:bg-muted/50 transition-colors',
                  col.isPrimaryKey && 'bg-amber-500/10'
                )}
              >
                <div className="flex items-center gap-1.5 min-w-0">
                  <span className="font-mono truncate">{col.name}</span>
                  {col.isPrimaryKey && (
                    <Badge variant="outline" className="h-3 px-1 text-[8px] bg-amber-500/20">
                      PK
                    </Badge>
                  )}
                  {col.isForeignKey && (
                    <Badge variant="outline" className="h-3 px-1 text-[8px] bg-blue-500/20">
                      FK
                    </Badge>
                  )}
                </div>
                <span className="text-muted-foreground text-[10px] ml-2 flex-shrink-0">
                  {col.dataType}
                </span>
              </button>
            ))}
            {data.columns!.length > 10 && (
              <p className="text-[10px] text-muted-foreground text-center py-1">
                +{data.columns!.length - 10} more
              </p>
            )}
          </div>
        </div>
      )}

      {/* Anomaly status badge */}
      {showAnomalyOverlay && data.hasSource && (
        <div className="absolute -top-2 -right-2">
          <Badge
            variant="outline"
            className={cn(
              'h-6 w-6 rounded-full p-0 flex items-center justify-center border',
              anomalyConfig.bgColor
            )}
          >
            <AnomalyIcon className={cn('h-3.5 w-3.5', anomalyConfig.color)} />
          </Badge>
        </div>
      )}

      {/* Impact indicator */}
      {showAnomalyOverlay && data.isImpacted && (
        <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2">
          <div className="h-1.5 w-8 bg-orange-500/70 rounded-full animate-pulse" />
        </div>
      )}

      {/* Output handle (not for sink nodes) */}
      {data.nodeType !== 'sink' && (
        <Handle
          type="source"
          position={Position.Right}
          className="!w-3 !h-3 !bg-muted-foreground/50"
        />
      )}
    </div>
  )

  // Wrap with tooltip when anomaly overlay is enabled
  if (showAnomalyOverlay && data.hasSource && data.anomalyStatus) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          {nodeContent}
        </TooltipTrigger>
        <TooltipContent side="right" className="max-w-xs">
          <div className="space-y-2">
            <div className="font-medium">{data.label}</div>
            <div className="flex items-center gap-2">
              <AnomalyIcon className={cn('h-4 w-4', anomalyConfig.color)} />
              <span className={anomalyConfig.color}>{anomalyConfig.label}</span>
            </div>
            {anomalyStatus !== 'unknown' && (
              <div className="text-xs text-muted-foreground space-y-1">
                <div>
                  Rate: {formatPercentage(data.anomalyStatus.anomaly_rate)}
                </div>
                <div>
                  Count: {data.anomalyStatus.anomaly_count ?? 'N/A'}
                </div>
                <div>
                  Algorithm: {data.anomalyStatus.algorithm ?? 'N/A'}
                </div>
                <div>
                  Last scan: {formatTimestamp(data.anomalyStatus.last_detection_at)}
                </div>
              </div>
            )}
            {data.isImpacted && (
              <div className="text-xs text-orange-500 flex items-center gap-1">
                <AlertTriangle className="h-3 w-3" />
                Potentially impacted by upstream anomalies
              </div>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    )
  }

  return nodeContent
})
