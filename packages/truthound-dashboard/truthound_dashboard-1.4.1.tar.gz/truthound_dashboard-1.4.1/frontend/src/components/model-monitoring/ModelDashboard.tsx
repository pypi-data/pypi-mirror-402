/**
 * Single model dashboard component.
 *
 * Displays detailed metrics, health status, and drift information for a single model.
 */

import { useEffect, useState, useCallback } from 'react'
import { useIntlayer } from 'react-intlayer'
import { str } from '@/lib/intlayer-utils'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useToast } from '@/hooks/use-toast'
import {
  ArrowLeft,
  RefreshCw,
  Activity,
  TrendingUp,
  Clock,
  AlertTriangle,
  CheckCircle,
  Loader2,
} from 'lucide-react'
import { ModelHealthIndicator } from './ModelHealthIndicator'
import { ModelMetricsChart } from './ModelMetricsChart'
import type { RegisteredModel } from './ModelList'

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

interface DashboardData {
  model_id: string
  model_name: string
  time_range_hours: number
  metrics: MetricSummary[]
  data_points: Record<string, MetricDataPoint[]>
  health_breakdown: {
    latency_score: number
    error_rate_score: number
    drift_score: number
    throughput_score: number
  }
  recent_alerts: Array<{
    id: string
    severity: string
    message: string
    created_at: string
  }>
}

interface ModelDashboardProps {
  model: RegisteredModel
  onBack: () => void
}

const API_BASE = '/api/v1'

async function getModelDashboard(modelId: string, hours: number = 24): Promise<DashboardData> {
  const response = await fetch(
    `${API_BASE}/model-monitoring/models/${modelId}/dashboard?hours=${hours}`
  )
  if (!response.ok) throw new Error('Failed to fetch dashboard')
  const result = await response.json()
  return result.data
}

export function ModelDashboard({ model, onBack }: ModelDashboardProps) {
  const t = useIntlayer('modelMonitoring')
  const common = useIntlayer('common')
  const { toast } = useToast()

  const [isLoading, setIsLoading] = useState(true)
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [timeRange, setTimeRange] = useState('24')

  const loadDashboard = useCallback(async () => {
    setIsLoading(true)
    try {
      const data = await getModelDashboard(model.id, parseInt(timeRange))
      setDashboardData(data)
    } catch {
      toast({
        title: str(common.error),
        description: str(t.errors.loadFailed),
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }, [model.id, timeRange, toast, common, t])

  useEffect(() => {
    loadDashboard()
  }, [loadDashboard])

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return (
          <Badge className="bg-green-500/10 text-green-500 border-green-500/20">
            {t.status.active}
          </Badge>
        )
      case 'paused':
        return (
          <Badge className="bg-gray-500/10 text-gray-500 border-gray-500/20">
            {t.status.paused}
          </Badge>
        )
      case 'degraded':
        return (
          <Badge className="bg-orange-500/10 text-orange-500 border-orange-500/20">
            {t.status.degraded}
          </Badge>
        )
      case 'error':
        return (
          <Badge className="bg-red-500/10 text-red-500 border-red-500/20">
            {t.status.error}
          </Badge>
        )
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-bold">{model.name}</h2>
              <Badge variant="outline">{model.version}</Badge>
              {getStatusBadge(model.status)}
            </div>
            <p className="text-sm text-muted-foreground">
              {model.prediction_count.toLocaleString()} predictions total
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1">{t.timeRanges['1h']}</SelectItem>
              <SelectItem value="6">{t.timeRanges['6h']}</SelectItem>
              <SelectItem value="24">{t.timeRanges['24h']}</SelectItem>
              <SelectItem value="168">{t.timeRanges['7d']}</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={loadDashboard} disabled={isLoading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            {common.refresh}
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-24">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : dashboardData ? (
        <>
          {/* Health Overview */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <ModelHealthIndicator
              score={model.health_score}
              label={str(t.models.healthScore)}
              size="lg"
            />

            <Card>
              <CardHeader className="pb-2">
                <CardDescription className="flex items-center gap-2">
                  <Activity className="h-4 w-4" />
                  {t.metrics.latency}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {dashboardData.metrics.find((m) => m.name === 'latency_ms')?.avg_value?.toFixed(
                    1
                  ) ?? '-'}{' '}
                  ms
                </div>
                <p className="text-xs text-muted-foreground">
                  P95:{' '}
                  {dashboardData.metrics
                    .find((m) => m.name === 'latency_ms')
                    ?.p95_value?.toFixed(1) ?? '-'}{' '}
                  ms
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  {t.models.driftScore}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div
                  className={`text-2xl font-bold ${
                    (model.current_drift_score ?? 0) > 0.1 ? 'text-orange-500' : 'text-green-500'
                  }`}
                >
                  {model.current_drift_score !== null
                    ? `${(model.current_drift_score * 100).toFixed(1)}%`
                    : '-'}
                </div>
                <p className="text-xs text-muted-foreground">
                  {(model.current_drift_score ?? 0) > 0.1 ? (
                    <span className="flex items-center gap-1 text-orange-500">
                      <AlertTriangle className="h-3 w-3" />
                      Drift detected
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-green-500">
                      <CheckCircle className="h-3 w-3" />
                      No drift
                    </span>
                  )}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription className="flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  {t.metrics.throughput}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {dashboardData.metrics
                    .find((m) => m.name === 'throughput')
                    ?.last_value?.toFixed(0) ?? '-'}
                  /hr
                </div>
                <p className="text-xs text-muted-foreground">Predictions per hour</p>
              </CardContent>
            </Card>
          </div>

          {/* Health Breakdown */}
          {dashboardData.health_breakdown && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Health Score Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-4">
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Latency</span>
                      <span className="font-medium">
                        {dashboardData.health_breakdown.latency_score.toFixed(0)}%
                      </span>
                    </div>
                    <div className="h-2 rounded-full bg-muted overflow-hidden">
                      <div
                        className="h-full bg-primary transition-all"
                        style={{ width: `${dashboardData.health_breakdown.latency_score}%` }}
                      />
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Error Rate</span>
                      <span className="font-medium">
                        {dashboardData.health_breakdown.error_rate_score.toFixed(0)}%
                      </span>
                    </div>
                    <div className="h-2 rounded-full bg-muted overflow-hidden">
                      <div
                        className="h-full bg-primary transition-all"
                        style={{ width: `${dashboardData.health_breakdown.error_rate_score}%` }}
                      />
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Drift</span>
                      <span className="font-medium">
                        {dashboardData.health_breakdown.drift_score.toFixed(0)}%
                      </span>
                    </div>
                    <div className="h-2 rounded-full bg-muted overflow-hidden">
                      <div
                        className="h-full bg-primary transition-all"
                        style={{ width: `${dashboardData.health_breakdown.drift_score}%` }}
                      />
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Throughput</span>
                      <span className="font-medium">
                        {dashboardData.health_breakdown.throughput_score.toFixed(0)}%
                      </span>
                    </div>
                    <div className="h-2 rounded-full bg-muted overflow-hidden">
                      <div
                        className="h-full bg-primary transition-all"
                        style={{ width: `${dashboardData.health_breakdown.throughput_score}%` }}
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Metrics Chart */}
          <ModelMetricsChart
            modelName={model.name}
            metrics={dashboardData.metrics}
            dataPoints={dashboardData.data_points}
            isLoading={false}
          />

          {/* Recent Alerts */}
          {dashboardData.recent_alerts && dashboardData.recent_alerts.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  Recent Alerts
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {dashboardData.recent_alerts.map((alert) => (
                    <div
                      key={alert.id}
                      className="flex items-start justify-between rounded-lg border p-3"
                    >
                      <div className="flex items-start gap-3">
                        <Badge
                          className={
                            alert.severity === 'critical'
                              ? 'bg-red-500/10 text-red-500 border-red-500/20'
                              : alert.severity === 'warning'
                                ? 'bg-orange-500/10 text-orange-500 border-orange-500/20'
                                : 'bg-blue-500/10 text-blue-500 border-blue-500/20'
                          }
                        >
                          {alert.severity}
                        </Badge>
                        <span className="text-sm">{alert.message}</span>
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {new Date(alert.created_at).toLocaleString()}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      ) : (
        <div className="text-center py-12 text-muted-foreground">{t.empty.noData}</div>
      )}
    </div>
  )
}
