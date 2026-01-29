/**
 * Feature Contribution Chart Component.
 *
 * Displays SHAP values as a horizontal bar chart (force plot style)
 * showing how each feature contributes to the anomaly score.
 */

import { useMemo } from 'react'
import { useIntlayer } from 'react-intlayer'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from 'recharts'
import { cn } from '@/lib/utils'

export interface FeatureContribution {
  feature: string
  value: number
  shap_value: number
  contribution: number
}

interface FeatureContributionChartProps {
  contributions: FeatureContribution[]
  maxFeatures?: number
  height?: number
  className?: string
}

export function FeatureContributionChart({
  contributions,
  maxFeatures = 10,
  height = 300,
  className,
}: FeatureContributionChartProps) {
  // Reserved for future i18n strings
  void useIntlayer('anomaly')

  // Prepare data for chart - show top N features
  const chartData = useMemo(() => {
    return contributions
      .slice(0, maxFeatures)
      .map((c) => ({
        feature: c.feature,
        value: c.value,
        shap: c.shap_value,
        contribution: c.contribution,
        // For bar display, use positive/negative shap value
        display: c.shap_value,
      }))
      .reverse() // Reverse so highest contribution is at top
  }, [contributions, maxFeatures])

  // Calculate domain for symmetric display
  const maxValue = useMemo(() => {
    const max = Math.max(...chartData.map((d) => Math.abs(d.shap)))
    return Math.ceil(max * 10) / 10 + 0.1
  }, [chartData])

  if (chartData.length === 0) {
    return (
      <div className={cn('flex h-32 items-center justify-center text-muted-foreground', className)}>
        No feature contributions available
      </div>
    )
  }

  return (
    <div className={cn('w-full', className)}>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 20, right: 30, left: 100, bottom: 5 }}
        >
          <XAxis
            type="number"
            domain={[-maxValue, maxValue]}
            tickFormatter={(v) => v.toFixed(2)}
            tick={{ fontSize: 11 }}
          />
          <YAxis
            type="category"
            dataKey="feature"
            tick={{ fontSize: 11 }}
            width={90}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload || !payload.length) return null
              const data = payload[0].payload
              return (
                <div className="rounded-lg border bg-background p-3 shadow-lg">
                  <p className="font-medium">{data.feature}</p>
                  <div className="mt-1 space-y-1 text-sm">
                    <p>
                      <span className="text-muted-foreground">Value:</span>{' '}
                      <span className="font-mono">{data.value.toFixed(2)}</span>
                    </p>
                    <p>
                      <span className="text-muted-foreground">SHAP:</span>{' '}
                      <span
                        className={cn(
                          'font-mono',
                          data.shap > 0 ? 'text-red-500' : 'text-blue-500'
                        )}
                      >
                        {data.shap > 0 ? '+' : ''}
                        {data.shap.toFixed(4)}
                      </span>
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {data.shap > 0
                        ? 'Pushes toward anomaly'
                        : 'Pushes toward normal'}
                    </p>
                  </div>
                </div>
              )
            }}
          />
          <ReferenceLine x={0} stroke="#888" strokeWidth={1} />
          <Bar dataKey="display" radius={[0, 4, 4, 0]}>
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.shap > 0 ? '#ef4444' : '#3b82f6'}
                opacity={0.8}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="mt-2 flex items-center justify-center gap-6 text-xs text-muted-foreground">
        <div className="flex items-center gap-1.5">
          <div className="h-3 w-3 rounded bg-red-500 opacity-80" />
          <span>Increases anomaly score</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="h-3 w-3 rounded bg-blue-500 opacity-80" />
          <span>Decreases anomaly score</span>
        </div>
      </div>
    </div>
  )
}
