/**
 * Per-column drift card component.
 *
 * Displays drift score badge, mini distribution chart, and test results.
 */

import { useIntlayer } from 'react-intlayer'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  BarChart,
  Bar,
  ResponsiveContainer,
} from 'recharts'
import { AlertTriangle, CheckCircle, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ColumnDriftResult } from '@/api/client'

interface ColumnDriftCardProps {
  result: ColumnDriftResult
  isSelected?: boolean
  onClick?: () => void
  className?: string
}

// Get level color
function getLevelColor(level: string): string {
  switch (level) {
    case 'high':
      return 'bg-red-500/10 text-red-500 border-red-500/20'
    case 'medium':
      return 'bg-orange-500/10 text-orange-500 border-orange-500/20'
    case 'low':
      return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
    default:
      return 'bg-green-500/10 text-green-500 border-green-500/20'
  }
}

// Get dtype badge color
function getDtypeBadgeColor(dtype: string): string {
  if (dtype.includes('int') || dtype.includes('float')) {
    return 'bg-blue-500/10 text-blue-500 border-blue-500/20'
  }
  if (dtype.includes('datetime')) {
    return 'bg-purple-500/10 text-purple-500 border-purple-500/20'
  }
  if (dtype.includes('bool')) {
    return 'bg-pink-500/10 text-pink-500 border-pink-500/20'
  }
  return 'bg-gray-500/10 text-gray-500 border-gray-500/20'
}

// Generate mini chart data
function generateMiniChartData(baselineStats: Record<string, unknown>, currentStats: Record<string, unknown>) {
  const baselineMean = (baselineStats.mean as number) ?? 50
  const baselineStd = (baselineStats.std as number) ?? 10
  const currentMean = (currentStats.mean as number) ?? 50
  const currentStd = (currentStats.std as number) ?? 10

  // Generate 5 bins for mini visualization
  const bins = 5
  const data = []

  for (let i = 0; i < bins; i++) {
    const x = i - 2 // -2 to 2 standard deviations
    const baselineVal = Math.exp(-0.5 * Math.pow(x * baselineStd / (baselineStd || 1), 2))
    const currentVal = Math.exp(-0.5 * Math.pow((x * currentStd - (currentMean - baselineMean) * 0.1) / (currentStd || 1), 2))

    data.push({
      baseline: baselineVal * 100,
      current: currentVal * 100,
    })
  }

  return data
}

export function ColumnDriftCard({
  result,
  isSelected = false,
  onClick,
  className,
}: ColumnDriftCardProps) {
  const t = useIntlayer('driftMonitor')

  const miniChartData = generateMiniChartData(
    result.baseline_stats as Record<string, unknown>,
    result.current_stats as Record<string, unknown>
  )

  return (
    <Card
      className={cn(
        'cursor-pointer transition-all hover:bg-muted/50',
        isSelected && 'ring-2 ring-primary bg-muted/30',
        className
      )}
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className="flex items-center gap-4">
          {/* Drift indicator icon */}
          <div className="flex-shrink-0">
            {result.drifted ? (
              <div className={cn(
                'p-2 rounded-full',
                result.level === 'high' ? 'bg-red-500/10' : 'bg-orange-500/10'
              )}>
                <AlertTriangle className={cn(
                  'h-5 w-5',
                  result.level === 'high' ? 'text-red-500' : 'text-orange-500'
                )} />
              </div>
            ) : (
              <div className="p-2 rounded-full bg-green-500/10">
                <CheckCircle className="h-5 w-5 text-green-500" />
              </div>
            )}
          </div>

          {/* Column info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-medium truncate">{result.column}</span>
              <Badge variant="outline" className={cn('text-xs', getDtypeBadgeColor(result.dtype))}>
                {result.dtype}
              </Badge>
            </div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span>{result.method.toUpperCase()}</span>
              {result.p_value !== undefined && (
                <>
                  <span>|</span>
                  <span>p={result.p_value.toFixed(4)}</span>
                </>
              )}
              {result.statistic !== undefined && (
                <>
                  <span>|</span>
                  <span>stat={result.statistic.toFixed(4)}</span>
                </>
              )}
            </div>
          </div>

          {/* Mini distribution chart */}
          <div className="w-20 h-10 flex-shrink-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={miniChartData} barGap={-8}>
                <Bar dataKey="baseline" fill="#6366f1" fillOpacity={0.5} />
                <Bar dataKey="current" fill="#fd9e4b" fillOpacity={0.7} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Drift level badge */}
          <div className="flex-shrink-0">
            <Badge variant="outline" className={getLevelColor(result.level)}>
              {result.drifted
                ? (t.columnDrilldown?.levels?.[result.level as keyof typeof t.columnDrilldown.levels] ?? result.level)
                : (t.columnDrilldown?.levels?.none ?? 'None')
              }
            </Badge>
          </div>

          {/* Chevron */}
          <ChevronRight className={cn(
            'h-4 w-4 text-muted-foreground transition-transform',
            isSelected && 'rotate-90'
          )} />
        </div>
      </CardContent>
    </Card>
  )
}
