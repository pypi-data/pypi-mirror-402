/**
 * Anomaly impact path visualization component.
 *
 * Shows the propagation path of anomalies through the lineage graph
 * with animated edges and severity indicators.
 */

import { memo, useMemo } from 'react'
import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  type EdgeProps,
} from 'reactflow'
import { AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'

export type ImpactSeverityLevel = 'unknown' | 'none' | 'low' | 'medium' | 'high' | 'critical'

export interface AnomalyImpactPathData {
  edgeType?: string
  isImpactPath?: boolean
  impactSeverity?: ImpactSeverityLevel
  animated?: boolean
}

const severityConfig: Record<
  ImpactSeverityLevel,
  { color: string; strokeWidth: number; dashArray?: string }
> = {
  unknown: {
    color: '#94a3b8', // slate-400
    strokeWidth: 2,
    dashArray: '4 4',
  },
  none: {
    color: '#94a3b8', // slate-400
    strokeWidth: 2,
  },
  low: {
    color: '#eab308', // yellow-500
    strokeWidth: 2,
  },
  medium: {
    color: '#f97316', // orange-500
    strokeWidth: 3,
  },
  high: {
    color: '#ef4444', // red-500
    strokeWidth: 3,
  },
  critical: {
    color: '#dc2626', // red-600
    strokeWidth: 4,
  },
}

export const AnomalyImpactPath = memo(function AnomalyImpactPath({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  style = {},
  markerEnd,
}: EdgeProps<AnomalyImpactPathData>) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  })

  const isImpactPath = data?.isImpactPath ?? false
  const severity = data?.impactSeverity || 'unknown'
  const animated = data?.animated ?? isImpactPath
  const config = severityConfig[severity]

  // Generate unique gradient ID for animated paths
  const gradientId = useMemo(() => `impact-gradient-${id}`, [id])

  // Animation styles for the path
  const animationStyles = useMemo(() => {
    if (!animated || !isImpactPath) return {}

    return {
      animation: 'dash 1.5s linear infinite',
      strokeDasharray: '10 5',
    }
  }, [animated, isImpactPath])

  return (
    <>
      {/* Animated gradient definition */}
      {isImpactPath && animated && (
        <defs>
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={config.color} stopOpacity={0.3}>
              <animate
                attributeName="stop-opacity"
                values="0.3;0.8;0.3"
                dur="1.5s"
                repeatCount="indefinite"
              />
            </stop>
            <stop offset="50%" stopColor={config.color} stopOpacity={0.8}>
              <animate
                attributeName="stop-opacity"
                values="0.8;1;0.8"
                dur="1.5s"
                repeatCount="indefinite"
              />
            </stop>
            <stop offset="100%" stopColor={config.color} stopOpacity={0.3}>
              <animate
                attributeName="stop-opacity"
                values="0.3;0.8;0.3"
                dur="1.5s"
                repeatCount="indefinite"
              />
            </stop>
          </linearGradient>
        </defs>
      )}

      {/* Glow effect for high severity paths */}
      {isImpactPath && (severity === 'high' || severity === 'critical') && (
        <BaseEdge
          id={`${id}-glow`}
          path={edgePath}
          style={{
            stroke: config.color,
            strokeWidth: config.strokeWidth + 4,
            strokeOpacity: 0.2,
            filter: 'blur(4px)',
          }}
        />
      )}

      {/* Main edge path */}
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          ...style,
          stroke: isImpactPath ? (animated ? `url(#${gradientId})` : config.color) : '#94a3b8',
          strokeWidth: isImpactPath ? config.strokeWidth : 2,
          strokeDasharray: config.dashArray,
          ...animationStyles,
        }}
      />

      {/* Impact severity label */}
      {isImpactPath && severity !== 'none' && severity !== 'unknown' && (
        <EdgeLabelRenderer>
          <div
            className="pointer-events-all nodrag nopan"
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            }}
          >
            <Badge
              variant={severity === 'critical' || severity === 'high' ? 'destructive' : 'secondary'}
              className={cn(
                'flex items-center gap-1 text-xs shadow-sm',
                severity === 'medium' && 'bg-orange-500/20 text-orange-600 border-orange-500/30',
                severity === 'low' && 'bg-yellow-500/20 text-yellow-600 border-yellow-500/30'
              )}
            >
              <AlertTriangle className="h-3 w-3" />
              {severity}
            </Badge>
          </div>
        </EdgeLabelRenderer>
      )}

      {/* CSS Animation keyframes */}
      <style>
        {`
          @keyframes dash {
            to {
              stroke-dashoffset: -30;
            }
          }
        `}
      </style>
    </>
  )
})

/**
 * Edge component for regular lineage edges (non-impact paths).
 * Can be enhanced to show impact when in impact analysis mode.
 */
export const LineageEdgeWithImpact = memo(function LineageEdgeWithImpact({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  style = {},
  markerEnd,
}: EdgeProps<AnomalyImpactPathData>) {
  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  })

  const isImpactPath = data?.isImpactPath ?? false

  if (isImpactPath) {
    // Re-render as AnomalyImpactPath with required edge props
    const impactProps: EdgeProps<AnomalyImpactPathData> = {
      id,
      source: '',
      target: '',
      sourceX,
      sourceY,
      targetX,
      targetY,
      sourcePosition,
      targetPosition,
      data,
      style,
      markerEnd,
    }
    return <AnomalyImpactPath {...impactProps} />
  }

  return (
    <BaseEdge
      id={id}
      path={edgePath}
      markerEnd={markerEnd}
      style={{
        ...style,
        stroke: '#94a3b8',
        strokeWidth: 2,
      }}
    />
  )
})
