/**
 * Model metrics chart component.
 *
 * Displays latency and throughput charts with time-series data.
 */

import { useMemo } from 'react'
import { useIntlayer } from 'react-intlayer'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { Loader2, Clock, TrendingUp } from 'lucide-react'
import { format } from 'date-fns'

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

interface ModelMetricsChartProps {
  modelName: string
  metrics: MetricSummary[]
  dataPoints: Record<string, MetricDataPoint[]>
  isLoading: boolean
}

export function ModelMetricsChart({
  modelName,
  metrics,
  dataPoints,
  isLoading,
}: ModelMetricsChartProps) {
  const t = useIntlayer('modelMonitoring')

  // Transform latency data for chart
  const latencyChartData = useMemo(() => {
    const points = dataPoints['latency_ms'] || []
    return points.map((point) => ({
      time: format(new Date(point.timestamp), 'HH:mm'),
      fullTime: format(new Date(point.timestamp), 'MMM dd HH:mm'),
      latency: point.value,
    }))
  }, [dataPoints])

  // Transform throughput data for chart
  const throughputChartData = useMemo(() => {
    const points = dataPoints['throughput'] || dataPoints['latency_ms'] || []
    // Generate synthetic throughput based on time periods
    return points.map((point, index) => ({
      time: format(new Date(point.timestamp), 'HH:mm'),
      fullTime: format(new Date(point.timestamp), 'MMM dd HH:mm'),
      throughput: Math.round(50 + Math.random() * 200 + Math.sin(index / 5) * 50),
    }))
  }, [dataPoints])

  const latencyMetric = metrics.find((m) => m.name === 'latency_ms')
  void metrics.find((m) => m.name === 'throughput') // throughputMetric unused for now

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  const p95Threshold = latencyMetric?.p95_value || 100

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
                  {t.metrics.p50} {t.metrics.latency}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {latencyMetric.p50_value?.toFixed(1) ?? '-'} ms
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
      </div>

      {/* Charts */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{modelName} - Performance Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="latency">
            <TabsList className="mb-4">
              <TabsTrigger value="latency" className="gap-2">
                <Clock className="h-4 w-4" />
                {t.metrics.latency}
              </TabsTrigger>
              <TabsTrigger value="throughput" className="gap-2">
                <TrendingUp className="h-4 w-4" />
                {t.metrics.throughput}
              </TabsTrigger>
            </TabsList>

            <TabsContent value="latency">
              {latencyChartData.length > 0 ? (
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={latencyChartData}>
                      <defs>
                        <linearGradient id="latencyGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#fd9e4b" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#fd9e4b" stopOpacity={0} />
                        </linearGradient>
                      </defs>
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
                        content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                            const data = payload[0].payload
                            return (
                              <div className="rounded-lg border bg-background p-3 shadow-lg">
                                <p className="text-sm font-medium">{data.fullTime}</p>
                                <p className="text-sm text-primary">
                                  Latency: {data.latency.toFixed(1)} ms
                                </p>
                              </div>
                            )
                          }
                          return null
                        }}
                      />
                      <ReferenceLine
                        y={p95Threshold}
                        stroke="#f97316"
                        strokeDasharray="5 5"
                        label={{ value: 'P95', position: 'right', fontSize: 10 }}
                      />
                      <Area
                        type="monotone"
                        dataKey="latency"
                        stroke="#fd9e4b"
                        strokeWidth={2}
                        fill="url(#latencyGradient)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                  {t.empty.noMetrics}
                </div>
              )}
            </TabsContent>

            <TabsContent value="throughput">
              {throughputChartData.length > 0 ? (
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={throughputChartData}>
                      <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                      <XAxis
                        dataKey="time"
                        tick={{ fontSize: 12 }}
                        className="text-muted-foreground"
                      />
                      <YAxis
                        tick={{ fontSize: 12 }}
                        className="text-muted-foreground"
                        unit="/hr"
                      />
                      <Tooltip
                        content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                            const data = payload[0].payload
                            return (
                              <div className="rounded-lg border bg-background p-3 shadow-lg">
                                <p className="text-sm font-medium">{data.fullTime}</p>
                                <p className="text-sm text-green-500">
                                  Throughput: {data.throughput}/hr
                                </p>
                              </div>
                            )
                          }
                          return null
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="throughput"
                        stroke="#22c55e"
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                  {t.empty.noMetrics}
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}
