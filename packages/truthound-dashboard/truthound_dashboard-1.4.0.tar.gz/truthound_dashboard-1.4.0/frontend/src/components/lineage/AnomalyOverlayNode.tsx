/**
 * Anomaly overlay node component for React Flow lineage visualization.
 *
 * Extends the base LineageNode with anomaly status indicators and badges.
 */

import { memo } from 'react'
import { Handle, Position, type NodeProps } from 'reactflow'
import { Database, ArrowRightLeft, Archive, ExternalLink, AlertTriangle, CheckCircle, AlertCircle, HelpCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { Badge } from '@/components/ui/badge'
import type { LineageNodeType } from '@/api/client'

export type AnomalyStatusLevel = 'unknown' | 'clean' | 'low' | 'medium' | 'high'

export interface AnomalyStatus {
  status: AnomalyStatusLevel
  anomaly_rate: number | null
  anomaly_count: number | null
  last_detection_at: string | null
  algorithm: string | null
}

export interface AnomalyOverlayNodeData {
  label: string
  nodeType: LineageNodeType
  sourceId: string | null
  hasSource: boolean
  anomalyStatus?: AnomalyStatus
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
    badgeVariant: 'default' | 'secondary' | 'destructive' | 'outline'
    label: string
  }
> = {
  unknown: {
    icon: HelpCircle,
    color: 'text-muted-foreground',
    bgColor: 'bg-muted/50',
    badgeVariant: 'outline',
    label: 'No detection',
  },
  clean: {
    icon: CheckCircle,
    color: 'text-green-500',
    bgColor: 'bg-green-500/10',
    badgeVariant: 'secondary',
    label: 'Clean',
  },
  low: {
    icon: AlertCircle,
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-500/10',
    badgeVariant: 'secondary',
    label: 'Low anomalies',
  },
  medium: {
    icon: AlertTriangle,
    color: 'text-orange-500',
    bgColor: 'bg-orange-500/10',
    badgeVariant: 'default',
    label: 'Medium anomalies',
  },
  high: {
    icon: AlertTriangle,
    color: 'text-red-500',
    bgColor: 'bg-red-500/10',
    badgeVariant: 'destructive',
    label: 'High anomalies',
  },
}

export const AnomalyOverlayNode = memo(function AnomalyOverlayNode({
  data,
  selected,
}: NodeProps<AnomalyOverlayNodeData>) {
  const nodeConfig = nodeTypeConfig[data.nodeType as LineageNodeType] || nodeTypeConfig.source
  const NodeIcon = nodeConfig.icon

  const anomalyStatus = data.anomalyStatus?.status || 'unknown'
  const anomalyConfig = anomalyStatusConfig[anomalyStatus]
  const AnomalyIcon = anomalyConfig.icon

  // Determine border color based on anomaly status
  const getBorderColor = () => {
    if (data.isImpacted) {
      // Impacted nodes get a pulsing animation
      return 'border-orange-500/70 animate-pulse'
    }
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

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div
          className={cn(
            'relative rounded-lg border-2 px-4 py-3 shadow-md transition-all',
            nodeConfig.bgColor,
            getBorderColor(),
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

          <div className="flex items-center gap-3">
            <div className={cn('rounded-md p-2', nodeConfig.bgColor)}>
              <NodeIcon className={cn('h-4 w-4', nodeConfig.color)} />
            </div>

            <div className="flex flex-col">
              <span className="text-sm font-medium text-foreground">
                {data.label}
              </span>
              <span className="text-xs text-muted-foreground capitalize">
                {data.nodeType}
              </span>
            </div>

            {data.hasSource && (
              <ExternalLink className="h-3 w-3 text-muted-foreground" />
            )}
          </div>

          {/* Anomaly status badge */}
          {data.hasSource && (
            <div className="absolute -top-2 -right-2">
              <Badge
                variant={anomalyConfig.badgeVariant}
                className={cn(
                  'h-6 w-6 rounded-full p-0 flex items-center justify-center',
                  anomalyConfig.bgColor
                )}
              >
                <AnomalyIcon className={cn('h-3.5 w-3.5', anomalyConfig.color)} />
              </Badge>
            </div>
          )}

          {/* Impact indicator */}
          {data.isImpacted && (
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
      </TooltipTrigger>
      <TooltipContent side="right" className="max-w-xs">
        <div className="space-y-2">
          <div className="font-medium">{data.label}</div>
          {data.hasSource && data.anomalyStatus && (
            <>
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
            </>
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
})
