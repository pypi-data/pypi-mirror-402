/**
 * Metrics chart component for model monitoring.
 */

import { useMemo } from 'react'
import { useIntlayer } from 'react-intlayer'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { Loader2 } from 'lucide-react'

interface MetricDataPoint {
  timestamp: string
  value: number
}

interface MetricSummary {
  name: string
  type: string
  count: number
  min_value: number | null
  max_value: number | null
  avg_value: number | null
  p50_value: number | null
  p95_value: number | null
  p99_value: number | null
  last_value: number | null
}

interface MetricsChartProps {
  modelName: string
  metrics: MetricSummary[]
  dataPoints: Record<string, MetricDataPoint[]>
  isLoading: boolean
}

export function MetricsChart({
  modelName,
  metrics,
  dataPoints,
  isLoading,
}: MetricsChartProps) {
  const t = useIntlayer('modelMonitoring')

  // Transform data for chart
  const chartData = useMemo(() => {
    const latencyPoints = dataPoints['latency_ms'] || []
    return latencyPoints.map((point) => ({
      time: new Date(point.timestamp).toLocaleTimeString(),
      latency: point.value,
    }))
  }, [dataPoints])

  const latencyMetric = metrics.find((m) => m.name === 'latency_ms')
  const throughputMetric = metrics.find((m) => m.name === 'throughput')

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        {latencyMetric && (
          <>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {t.metrics.avg} {t.metrics.latency}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {latencyMetric.avg_value?.toFixed(1) ?? '-'} ms
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {t.metrics.p95} {t.metrics.latency}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {latencyMetric.p95_value?.toFixed(1) ?? '-'} ms
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {t.metrics.p99} {t.metrics.latency}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {latencyMetric.p99_value?.toFixed(1) ?? '-'} ms
                </div>
              </CardContent>
            </Card>
          </>
        )}
        {throughputMetric && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {t.metrics.throughput}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {throughputMetric.last_value?.toFixed(1) ?? '-'}/hr
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Latency Chart */}
      {chartData.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>
              {t.metrics.latency} - {modelName}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis
                    dataKey="time"
                    tick={{ fontSize: 12 }}
                    className="text-muted-foreground"
                  />
                  <YAxis
                    tick={{ fontSize: 12 }}
                    className="text-muted-foreground"
                    unit=" ms"
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '6px',
                    }}
                    labelStyle={{ color: 'hsl(var(--foreground))' }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="latency"
                    stroke="hsl(var(--primary))"
                    strokeWidth={2}
                    dot={false}
                    name="Latency (ms)"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            {t.empty.noMetrics}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
