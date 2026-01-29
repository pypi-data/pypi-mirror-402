/**
 * Drift score gauge component.
 *
 * Visual gauge display for drift score with color coding and threshold markers.
 */

import { cn } from '@/lib/utils'

interface DriftScoreGaugeProps {
  score: number
  threshold?: number
  criticalThreshold?: number
  className?: string
  size?: 'sm' | 'md' | 'lg'
  showValue?: boolean
  showThresholds?: boolean
}

export function DriftScoreGauge({
  score,
  threshold = 5,
  criticalThreshold = 20,
  className,
  size = 'md',
  showValue = true,
  showThresholds = true,
}: DriftScoreGaugeProps) {
  // Determine color based on score
  const getColor = () => {
    if (score >= criticalThreshold) return 'text-red-500'
    if (score >= threshold) return 'text-orange-500'
    return 'text-green-500'
  }

  const getBgColor = () => {
    if (score >= criticalThreshold) return 'bg-red-500'
    if (score >= threshold) return 'bg-orange-500'
    return 'bg-green-500'
  }

  const getTrackBgColor = () => {
    if (score >= criticalThreshold) return 'bg-red-500/20'
    if (score >= threshold) return 'bg-orange-500/20'
    return 'bg-green-500/20'
  }

  // Size configurations
  const sizeConfig = {
    sm: {
      height: 'h-1.5',
      fontSize: 'text-sm',
      padding: 'py-1',
    },
    md: {
      height: 'h-2',
      fontSize: 'text-base',
      padding: 'py-2',
    },
    lg: {
      height: 'h-3',
      fontSize: 'text-lg',
      padding: 'py-3',
    },
  }

  const config = sizeConfig[size]

  // Normalize score to 0-100 for display (cap at 100)
  const normalizedScore = Math.min(score, 100)

  return (
    <div className={cn('w-full', className)}>
      {/* Score value */}
      {showValue && (
        <div className={cn('flex items-center justify-between mb-1', config.padding)}>
          <span className={cn('font-semibold', config.fontSize, getColor())}>
            {score.toFixed(1)}%
          </span>
          {score >= criticalThreshold && (
            <span className="text-xs text-red-500 font-medium">Critical</span>
          )}
          {score >= threshold && score < criticalThreshold && (
            <span className="text-xs text-orange-500 font-medium">Warning</span>
          )}
          {score < threshold && (
            <span className="text-xs text-green-500 font-medium">Normal</span>
          )}
        </div>
      )}

      {/* Gauge bar */}
      <div className={cn('relative w-full rounded-full', config.height, getTrackBgColor())}>
        {/* Fill */}
        <div
          className={cn('absolute left-0 top-0 h-full rounded-full transition-all duration-300', getBgColor())}
          style={{ width: `${normalizedScore}%` }}
        />

        {/* Threshold markers */}
        {showThresholds && (
          <>
            {/* Warning threshold */}
            <div
              className="absolute top-0 h-full w-0.5 bg-orange-500/50"
              style={{ left: `${Math.min(threshold, 100)}%` }}
            />
            {/* Critical threshold */}
            <div
              className="absolute top-0 h-full w-0.5 bg-red-500/50"
              style={{ left: `${Math.min(criticalThreshold, 100)}%` }}
            />
          </>
        )}
      </div>

      {/* Threshold labels */}
      {showThresholds && size !== 'sm' && (
        <div className="relative mt-1 text-xs text-muted-foreground">
          <span className="absolute" style={{ left: `${Math.min(threshold, 100)}%`, transform: 'translateX(-50%)' }}>
            {threshold}%
          </span>
          <span className="absolute" style={{ left: `${Math.min(criticalThreshold, 100)}%`, transform: 'translateX(-50%)' }}>
            {criticalThreshold}%
          </span>
        </div>
      )}
    </div>
  )
}
