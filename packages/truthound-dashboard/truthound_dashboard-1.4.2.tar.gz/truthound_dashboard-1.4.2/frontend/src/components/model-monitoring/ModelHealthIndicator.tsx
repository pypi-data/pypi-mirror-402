/**
 * Model health score indicator component.
 *
 * Displays a visual health score with color-coded indicator.
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { Heart, HeartPulse, HeartCrack, AlertTriangle } from 'lucide-react'

interface ModelHealthIndicatorProps {
  score: number
  label?: string
  size?: 'sm' | 'md' | 'lg'
  showIcon?: boolean
  className?: string
}

export function ModelHealthIndicator({
  score,
  label = 'Health Score',
  size = 'md',
  showIcon = true,
  className,
}: ModelHealthIndicatorProps) {
  const getHealthColor = (score: number) => {
    if (score >= 80) return { bg: 'bg-green-500', text: 'text-green-500', label: 'Healthy' }
    if (score >= 60) return { bg: 'bg-yellow-500', text: 'text-yellow-500', label: 'Warning' }
    if (score >= 40) return { bg: 'bg-orange-500', text: 'text-orange-500', label: 'Degraded' }
    return { bg: 'bg-red-500', text: 'text-red-500', label: 'Critical' }
  }

  const getHealthIcon = (score: number) => {
    if (score >= 80) return <HeartPulse className={iconSizes[size]} />
    if (score >= 60) return <Heart className={iconSizes[size]} />
    if (score >= 40) return <AlertTriangle className={iconSizes[size]} />
    return <HeartCrack className={iconSizes[size]} />
  }

  const iconSizes = {
    sm: 'h-4 w-4',
    md: 'h-5 w-5',
    lg: 'h-6 w-6',
  }

  const scoreSizes = {
    sm: 'text-lg',
    md: 'text-2xl',
    lg: 'text-3xl',
  }

  const progressSizes = {
    sm: 'h-1.5',
    md: 'h-2',
    lg: 'h-3',
  }

  const { bg, text, label: statusLabel } = getHealthColor(score)

  if (size === 'sm') {
    return (
      <div className={cn('flex items-center gap-2', className)}>
        {showIcon && <span className={text}>{getHealthIcon(score)}</span>}
        <div className="flex items-center gap-1.5">
          <div className={cn('h-1.5 w-12 rounded-full bg-muted overflow-hidden')}>
            <div className={cn('h-full transition-all', bg)} style={{ width: `${score}%` }} />
          </div>
          <span className={cn('text-sm font-medium', text)}>{score.toFixed(0)}%</span>
        </div>
      </div>
    )
  }

  return (
    <Card className={cn(className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          {showIcon && <span className={text}>{getHealthIcon(score)}</span>}
          {label}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-baseline gap-2">
            <span className={cn('font-bold', text, scoreSizes[size])}>{score.toFixed(0)}%</span>
            <span className={cn('text-xs', text)}>{statusLabel}</span>
          </div>
          <div className={cn('rounded-full bg-muted overflow-hidden', progressSizes[size])}>
            <div className={cn('h-full transition-all duration-500', bg)} style={{ width: `${score}%` }} />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Inline health indicator for use in tables.
 */
export function InlineHealthIndicator({ score }: { score: number }) {
  const getHealthColor = (score: number) => {
    if (score >= 80) return 'bg-green-500'
    if (score >= 60) return 'bg-yellow-500'
    if (score >= 40) return 'bg-orange-500'
    return 'bg-red-500'
  }

  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-16 rounded-full bg-muted overflow-hidden">
        <div
          className={cn('h-full transition-all', getHealthColor(score))}
          style={{ width: `${score}%` }}
        />
      </div>
      <span className="text-sm tabular-nums">{score.toFixed(0)}%</span>
    </div>
  )
}

/**
 * Circular health indicator for dashboard cards.
 */
export function CircularHealthIndicator({
  score,
  size = 80,
  strokeWidth = 8,
}: {
  score: number
  size?: number
  strokeWidth?: number
}) {
  const radius = (size - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const offset = circumference - (score / 100) * circumference

  const getHealthColor = (score: number) => {
    if (score >= 80) return '#22c55e' // green-500
    if (score >= 60) return '#eab308' // yellow-500
    if (score >= 40) return '#f97316' // orange-500
    return '#ef4444' // red-500
  }

  const color = getHealthColor(score)

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="none"
          className="text-muted"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-500"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-lg font-bold" style={{ color }}>
          {score.toFixed(0)}%
        </span>
      </div>
    </div>
  )
}
