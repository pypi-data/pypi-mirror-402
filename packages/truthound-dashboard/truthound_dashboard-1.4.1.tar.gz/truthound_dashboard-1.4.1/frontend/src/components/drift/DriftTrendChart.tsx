/**
 * Drift trend chart component.
 *
 * Displays drift percentage trend over time.
 */

import { useIntlayer } from 'react-intlayer'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { format } from 'date-fns'
import { TrendingUp, Loader2 } from 'lucide-react'

interface TrendDataPoint {
  timestamp: string
  drift_percentage: number
  drifted_columns: number
  total_columns: number
  has_drift: boolean
}

interface DriftTrendData {
  monitor_id: string
  period_start: string
  period_end: string
  data_points: TrendDataPoint[]
  avg_drift_percentage: number
  max_drift_percentage: number
  drift_occurrence_rate: number
}

interface DriftTrendChartProps {
  data: DriftTrendData | null
  isLoading?: boolean
  threshold?: number
}

export function DriftTrendChart({
  data,
  isLoading = false,
  threshold = 5,
}: DriftTrendChartProps) {
  const t = useIntlayer('driftMonitor')

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex h-80 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    )
  }

  if (!data || data.data_points.length === 0) {
    return (
      <Card>
        <CardContent className="flex h-80 flex-col items-center justify-center gap-2">
          <TrendingUp className="h-8 w-8 text-muted-foreground" />
          <p className="text-muted-foreground">No trend data available</p>
        </CardContent>
      </Card>
    )
  }

  const chartData = data.data_points.map((point) => ({
    ...point,
    timestamp: format(new Date(point.timestamp), 'MMM dd'),
    fullDate: format(new Date(point.timestamp), 'MMM dd, yyyy HH:mm'),
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          {t.trend.title}
        </CardTitle>
        <CardDescription>
          {format(new Date(data.period_start), 'MMM dd, yyyy')} -{' '}
          {format(new Date(data.period_end), 'MMM dd, yyyy')}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Summary Stats */}
        <div className="mb-6 grid gap-4 md:grid-cols-3">
          <div className="rounded-lg border p-3">
            <p className="text-sm text-muted-foreground">{t.trend.avgDrift}</p>
            <p className="text-xl font-bold">{data.avg_drift_percentage.toFixed(1)}%</p>
          </div>
          <div className="rounded-lg border p-3">
            <p className="text-sm text-muted-foreground">{t.trend.maxDrift}</p>
            <p className="text-xl font-bold">{data.max_drift_percentage.toFixed(1)}%</p>
          </div>
          <div className="rounded-lg border p-3">
            <p className="text-sm text-muted-foreground">{t.trend.driftOccurrence}</p>
            <p className="text-xl font-bold">{(data.drift_occurrence_rate * 100).toFixed(0)}%</p>
          </div>
        </div>

        {/* Chart */}
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="timestamp"
                tick={{ fontSize: 12 }}
                className="text-muted-foreground"
              />
              <YAxis
                tick={{ fontSize: 12 }}
                className="text-muted-foreground"
                domain={[0, 'auto']}
                unit="%"
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload
                    return (
                      <div className="rounded-lg border bg-background p-3 shadow-lg">
                        <p className="text-sm font-medium">{data.fullDate}</p>
                        <p className="text-sm text-primary">
                          Drift: {data.drift_percentage.toFixed(1)}%
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {data.drifted_columns} / {data.total_columns} columns
                        </p>
                      </div>
                    )
                  }
                  return null
                }}
              />
              <ReferenceLine
                y={threshold}
                stroke="#f97316"
                strokeDasharray="5 5"
                label={{ value: 'Threshold', position: 'right', fontSize: 10 }}
              />
              <Line
                type="monotone"
                dataKey="drift_percentage"
                stroke="#fd9e4b"
                strokeWidth={2}
                dot={(props) => {
                  const { cx, cy, payload } = props
                  return (
                    <circle
                      cx={cx}
                      cy={cy}
                      r={4}
                      fill={payload.has_drift ? '#f97316' : '#22c55e'}
                      stroke="white"
                      strokeWidth={2}
                    />
                  )
                }}
                activeDot={{ r: 6, fill: '#fd9e4b' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
