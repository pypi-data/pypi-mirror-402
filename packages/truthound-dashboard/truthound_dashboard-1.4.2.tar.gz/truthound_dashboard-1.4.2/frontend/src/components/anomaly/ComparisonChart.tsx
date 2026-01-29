/**
 * Comparison chart visualization component.
 *
 * Displays bar charts comparing anomaly rates and overlap matrix.
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
  ResponsiveContainer,
  Cell,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import type { AlgorithmComparisonResult } from '@/api/client'

interface ComparisonChartProps {
  result: AlgorithmComparisonResult
}

// Color palette for algorithms
const COLORS = [
  '#fd9e4b', // primary
  '#3b82f6', // blue
  '#10b981', // green
  '#8b5cf6', // purple
  '#ef4444', // red
  '#f59e0b', // amber
]

export function ComparisonChart({ result }: ComparisonChartProps) {
  const t = useIntlayer('anomaly')

  // Prepare data for anomaly rate chart
  const rateChartData = useMemo(() => {
    return result.algorithm_results
      .filter((r) => r.status === 'success')
      .map((r, index) => ({
        name: r.display_name,
        rate: r.anomaly_rate != null ? r.anomaly_rate * 100 : 0,
        count: r.anomaly_count ?? 0,
        fill: COLORS[index % COLORS.length],
      }))
  }, [result.algorithm_results])

  // Prepare data for duration chart
  const durationChartData = useMemo(() => {
    return result.algorithm_results
      .filter((r) => r.status === 'success')
      .map((r, index) => ({
        name: r.display_name,
        duration: r.duration_ms != null ? r.duration_ms / 1000 : 0,
        fill: COLORS[index % COLORS.length],
      }))
  }, [result.algorithm_results])

  // Prepare agreement matrix data
  const matrixData = useMemo(() => {
    if (!result.agreement_summary?.agreement_matrix) return null

    const algorithms = result.algorithm_results
      .filter((r) => r.status === 'success')
      .map((r) => r.display_name)

    const matrix = result.agreement_summary.agreement_matrix

    return { algorithms, matrix }
  }, [result])

  return (
    <div className="space-y-6">
      {/* Anomaly Rate Bar Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            {t.comparison?.rateComparison ?? 'Anomaly Rate Comparison'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={rateChartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
            >
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="name"
                angle={-45}
                textAnchor="end"
                height={80}
                tick={{ fontSize: 12 }}
                className="fill-muted-foreground"
              />
              <YAxis
                tickFormatter={(value) => `${value}%`}
                tick={{ fontSize: 12 }}
                className="fill-muted-foreground"
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (!active || !payload?.[0]) return null
                  const data = payload[0].payload
                  return (
                    <div className="rounded-lg border bg-background p-3 shadow-lg">
                      <p className="font-medium">{data.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {t.comparison?.anomalyRate ?? 'Rate'}: {data.rate.toFixed(2)}%
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {t.comparison?.anomalyCount ?? 'Count'}: {data.count.toLocaleString()}
                      </p>
                    </div>
                  )
                }}
              />
              <Bar dataKey="rate" radius={[4, 4, 0, 0]}>
                {rateChartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Duration Bar Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            {t.comparison?.durationComparison ?? 'Execution Time Comparison'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={durationChartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
            >
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="name"
                angle={-45}
                textAnchor="end"
                height={80}
                tick={{ fontSize: 12 }}
                className="fill-muted-foreground"
              />
              <YAxis
                tickFormatter={(value) => `${value}s`}
                tick={{ fontSize: 12 }}
                className="fill-muted-foreground"
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (!active || !payload?.[0]) return null
                  const data = payload[0].payload
                  return (
                    <div className="rounded-lg border bg-background p-3 shadow-lg">
                      <p className="font-medium">{data.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {t.comparison?.duration ?? 'Duration'}: {data.duration.toFixed(2)}s
                      </p>
                    </div>
                  )
                }}
              />
              <Bar dataKey="duration" radius={[4, 4, 0, 0]}>
                {durationChartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Agreement Matrix (Heatmap-style) */}
      {matrixData && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              {t.comparison?.agreementMatrix ?? 'Agreement Matrix (Overlap)'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr>
                    <th className="p-2 text-left"></th>
                    {matrixData.algorithms.map((algo) => (
                      <th key={algo} className="p-2 text-center font-medium">
                        {algo.split(' ')[0]}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {matrixData.matrix.map((row, i) => (
                    <tr key={i}>
                      <td className="p-2 font-medium">{matrixData.algorithms[i]}</td>
                      {row.map((value, j) => {
                        const maxOverlap = Math.max(...row)
                        const intensity = maxOverlap > 0 ? value / maxOverlap : 0
                        const isDiagonal = i === j

                        return (
                          <td
                            key={j}
                            className={cn(
                              'p-2 text-center',
                              isDiagonal && 'font-bold'
                            )}
                          >
                            <div
                              className={cn(
                                'mx-auto rounded px-2 py-1',
                                isDiagonal
                                  ? 'bg-primary/20 text-primary'
                                  : intensity > 0.7
                                    ? 'bg-green-500/20 text-green-600'
                                    : intensity > 0.3
                                      ? 'bg-yellow-500/20 text-yellow-600'
                                      : 'bg-muted text-muted-foreground'
                              )}
                            >
                              {value}
                            </div>
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-4 text-xs text-muted-foreground">
              {t.comparison?.matrixDescription ??
                'Diagonal shows total anomalies per algorithm. Other cells show overlap (anomalies detected by both algorithms).'}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
