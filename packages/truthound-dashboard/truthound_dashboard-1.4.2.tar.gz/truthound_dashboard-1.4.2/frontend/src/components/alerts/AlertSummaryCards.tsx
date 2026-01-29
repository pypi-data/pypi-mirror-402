/**
 * AlertSummaryCards Component
 *
 * Displays summary statistics for alerts including:
 * - Total active alerts
 * - Breakdown by severity
 * - Breakdown by source
 * - 24h trend sparkline
 */

import { useIntlayer } from '@/providers'
import { str } from '@/lib/intlayer-utils'
import {
  AlertTriangle,
  Activity,
  TrendingUp,
  TrendingDown,
  Minus,
  GitCompare,
  Cpu,
  CheckCircle,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Area,
  AreaChart,
  ResponsiveContainer,
} from 'recharts'

interface AlertSummary {
  total_alerts: number
  active_alerts: number
  by_severity: {
    critical: number
    high: number
    medium: number
    low: number
    info: number
  }
  by_source: {
    model: number
    drift: number
    anomaly: number
    validation: number
  }
  by_status: {
    open: number
    acknowledged: number
    resolved: number
    ignored: number
  }
  trend_24h: Array<{
    timestamp: string
    count: number
  }>
  top_sources: Array<{
    name: string
    count: number
  }>
}

interface AlertSummaryCardsProps {
  summary: AlertSummary | null
  loading?: boolean
}

const sourceIcons = {
  model: Cpu,
  drift: GitCompare,
  anomaly: AlertTriangle,
  validation: CheckCircle,
}

const severityColors = {
  critical: 'text-red-500 bg-red-100 dark:bg-red-900/30',
  high: 'text-orange-500 bg-orange-100 dark:bg-orange-900/30',
  medium: 'text-yellow-500 bg-yellow-100 dark:bg-yellow-900/30',
  low: 'text-blue-500 bg-blue-100 dark:bg-blue-900/30',
  info: 'text-gray-500 bg-gray-100 dark:bg-gray-900/30',
}

export function AlertSummaryCards({ summary, loading = false }: AlertSummaryCardsProps) {
  const content = useIntlayer('alerts')

  // Calculate trend
  const trendData = summary?.trend_24h || []
  const recentCounts = trendData.slice(-6).map(d => d.count)
  const oldCounts = trendData.slice(0, 6).map(d => d.count)
  const recentTotal = recentCounts.reduce((a, b) => a + b, 0)
  const oldTotal = oldCounts.reduce((a, b) => a + b, 0)
  const trendDirection = recentTotal > oldTotal ? 'up' : recentTotal < oldTotal ? 'down' : 'flat'

  if (loading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader className="pb-2">
              <div className="h-4 w-24 bg-muted rounded" />
            </CardHeader>
            <CardContent>
              <div className="h-8 w-16 bg-muted rounded mb-2" />
              <div className="h-3 w-32 bg-muted rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (!summary) {
    return null
  }

  return (
    <div className="space-y-4">
      {/* Main stats row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Total Active Alerts */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {str(content.summary.activeAlerts)}
            </CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.active_alerts}</div>
            <div className="flex items-center text-xs text-muted-foreground mt-1">
              {trendDirection === 'up' && (
                <>
                  <TrendingUp className="h-3 w-3 text-red-500 mr-1" />
                  <span className="text-red-500">Increasing</span>
                </>
              )}
              {trendDirection === 'down' && (
                <>
                  <TrendingDown className="h-3 w-3 text-green-500 mr-1" />
                  <span className="text-green-500">Decreasing</span>
                </>
              )}
              {trendDirection === 'flat' && (
                <>
                  <Minus className="h-3 w-3 mr-1" />
                  <span>Stable</span>
                </>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Critical Alerts */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {str(content.summary.criticalAlerts)}
            </CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">
              {summary.by_severity.critical}
            </div>
            <p className="text-xs text-muted-foreground">
              {summary.by_severity.high} high severity
            </p>
          </CardContent>
        </Card>

        {/* Open vs Resolved */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {str(content.status.open)} / {str(content.status.resolved)}
            </CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {summary.by_status.open} / {summary.by_status.resolved}
            </div>
            <p className="text-xs text-muted-foreground">
              {summary.by_status.acknowledged} acknowledged
            </p>
          </CardContent>
        </Card>

        {/* 24h Trend Chart */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {str(content.summary.trend24h)}
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="h-[60px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trendData} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="alertTrend" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <Area
                    type="monotone"
                    dataKey="count"
                    stroke="hsl(var(--primary))"
                    fill="url(#alertTrend)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Secondary stats row */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* By Severity */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              {str(content.filters.severity)} Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(summary.by_severity).map(([severity, count]) => {
                const severityKey = severity as keyof typeof severityColors
                const total = summary.total_alerts || 1
                const percentage = Math.round((count / total) * 100)
                return (
                  <div key={severity} className="flex items-center gap-3">
                    <div className={cn(
                      'w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium',
                      severityColors[severityKey]
                    )}>
                      {count}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm capitalize">{severity}</span>
                        <span className="text-xs text-muted-foreground">{percentage}%</span>
                      </div>
                      <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                        <div
                          className={cn('h-full rounded-full', severityColors[severityKey].split(' ')[0].replace('text-', 'bg-'))}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>

        {/* By Source */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              {str(content.filters.source)} Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(summary.by_source).map(([source, count]) => {
                const sourceKey = source as keyof typeof sourceIcons
                const Icon = sourceIcons[sourceKey]
                const total = summary.total_alerts || 1
                const percentage = Math.round((count / total) * 100)
                return (
                  <div key={source} className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                      <Icon className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm capitalize">{source}</span>
                        <span className="text-xs text-muted-foreground">{count} alerts</span>
                      </div>
                      <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full bg-primary/60"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default AlertSummaryCards
