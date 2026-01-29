/**
 * Column Distribution Chart Component.
 *
 * Displays side-by-side histogram comparison between baseline
 * and current data distributions for a single column.
 */

import { useMemo } from 'react'
import { useIntlayer } from 'react-intlayer'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ArrowRight, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import type { ColumnPreviewResult } from './DriftPreview'

interface ColumnDistributionChartProps {
  column: ColumnPreviewResult
}

function formatStatValue(value: number | null | undefined, decimals = 2): string {
  if (value == null) return '-'
  if (Math.abs(value) >= 1000000) {
    return (value / 1000000).toFixed(1) + 'M'
  }
  if (Math.abs(value) >= 1000) {
    return (value / 1000).toFixed(1) + 'K'
  }
  return value.toFixed(decimals)
}

function getChangeIndicator(baseline: number | undefined, current: number | undefined) {
  if (baseline == null || current == null) return null

  const percentChange = baseline !== 0 ? ((current - baseline) / Math.abs(baseline)) * 100 : 0

  if (Math.abs(percentChange) < 1) {
    return { icon: Minus, color: 'text-muted-foreground', label: 'No change' }
  }
  if (percentChange > 0) {
    return { icon: TrendingUp, color: 'text-green-500', label: `+${percentChange.toFixed(1)}%` }
  }
  return { icon: TrendingDown, color: 'text-red-500', label: `${percentChange.toFixed(1)}%` }
}

export function ColumnDistributionChart({ column }: ColumnDistributionChartProps) {
  const t = useIntlayer('driftMonitor')
  const baseline = column.baseline_stats || {}
  const current = column.current_stats || {}

  // Build chart data from stats
  const chartData = useMemo(() => {
    // If we have distribution data, use it
    if (column.baseline_distribution && column.current_distribution) {
      const bins = column.baseline_distribution.bins
      return bins.map((bin, i) => ({
        name: bin,
        baseline: column.baseline_distribution?.percentages[i] ?? 0,
        current: column.current_distribution?.percentages[i] ?? 0,
      }))
    }

    // Otherwise, create a simple comparison chart from stats
    const stats = ['mean', 'std', 'min', 'max']
    return stats
      .filter((stat) => baseline[stat] != null || current[stat] != null)
      .map((stat) => ({
        name: stat.charAt(0).toUpperCase() + stat.slice(1),
        baseline: baseline[stat] ?? 0,
        current: current[stat] ?? 0,
      }))
  }, [column, baseline, current])

  // Stats comparison
  const statComparisons = [
    { key: 'mean', label: 'Mean' },
    { key: 'std', label: 'Std Dev' },
    { key: 'min', label: 'Min' },
    { key: 'max', label: 'Max' },
    { key: 'count', label: 'Count' },
    { key: 'null_count', label: 'Null Count' },
  ]

  return (
    <div className="space-y-4">
      {/* Statistics Comparison */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {statComparisons.map(({ key, label }) => {
          const baselineVal = baseline[key]
          const currentVal = current[key]
          const change = getChangeIndicator(baselineVal, currentVal)

          return (
            <Card key={key} className="p-3">
              <div className="text-xs font-medium text-muted-foreground mb-1">
                {label}
              </div>
              <div className="flex items-center gap-2">
                <div className="text-sm">
                  <span className="text-muted-foreground">
                    {formatStatValue(baselineVal)}
                  </span>
                  <ArrowRight className="inline h-3 w-3 mx-1 text-muted-foreground" />
                  <span className="font-medium">
                    {formatStatValue(currentVal)}
                  </span>
                </div>
                {change && (
                  <Badge
                    variant="outline"
                    className={`text-xs ${change.color}`}
                  >
                    <change.icon className="h-3 w-3 mr-1" />
                    {change.label}
                  </Badge>
                )}
              </div>
            </Card>
          )
        })}
      </div>

      {/* Distribution Chart */}
      {chartData.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">
              {t.preview?.distributionComparison ?? 'Distribution Comparison'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={chartData}
                  margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis
                    dataKey="name"
                    tick={{ fontSize: 12 }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 12 }}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(value) => formatStatValue(value, 1)}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--popover))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                    }}
                    formatter={(value: number) => [formatStatValue(value), '']}
                  />
                  <Legend />
                  <Bar
                    dataKey="baseline"
                    name={String(t.preview?.baseline ?? 'Baseline')}
                    fill="hsl(var(--muted-foreground))"
                    opacity={0.6}
                    radius={[4, 4, 0, 0]}
                  />
                  <Bar
                    dataKey="current"
                    name={String(t.preview?.current ?? 'Current')}
                    fill="hsl(var(--primary))"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Statistical Test Results */}
      <div className="flex flex-wrap gap-4 text-sm">
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">{t.monitor.method}:</span>
          <Badge variant="outline" className="uppercase">
            {column.method}
          </Badge>
        </div>
        {column.p_value != null && (
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">{t.preview?.pValue ?? 'P-Value'}:</span>
            <Badge
              variant={column.p_value < 0.05 ? 'destructive' : 'outline'}
              className="font-mono"
            >
              {column.p_value.toFixed(4)}
            </Badge>
          </div>
        )}
        {column.statistic != null && (
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">{t.preview?.testStatistic ?? 'Test Statistic'}:</span>
            <Badge variant="outline" className="font-mono">
              {column.statistic.toFixed(4)}
            </Badge>
          </div>
        )}
      </div>
    </div>
  )
}
