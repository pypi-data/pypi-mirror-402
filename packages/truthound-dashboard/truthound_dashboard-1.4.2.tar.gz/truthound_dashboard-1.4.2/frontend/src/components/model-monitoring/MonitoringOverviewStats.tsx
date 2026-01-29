/**
 * Overview stats cards for model monitoring dashboard.
 */

import { useIntlayer } from 'react-intlayer'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Cpu,
  Activity,
  AlertTriangle,
  TrendingDown,
  Clock,
  BarChart3,
} from 'lucide-react'

interface MonitoringOverviewStatsProps {
  totalModels: number
  activeModels: number
  degradedModels: number
  predictions24h: number
  activeAlerts: number
  modelsWithDrift: number
  avgLatencyMs: number | null
}

export function MonitoringOverviewStats({
  totalModels,
  activeModels,
  degradedModels,
  predictions24h,
  activeAlerts,
  modelsWithDrift,
  avgLatencyMs,
}: MonitoringOverviewStatsProps) {
  const t = useIntlayer('modelMonitoring')

  return (
    <div className="grid gap-4 md:grid-cols-4 lg:grid-cols-7">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <Cpu className="h-4 w-4" />
            {t.overview.totalModels}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{totalModels}</div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <Activity className="h-4 w-4" />
            {t.overview.activeModels}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-500">{activeModels}</div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <TrendingDown className="h-4 w-4" />
            {t.overview.degradedModels}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className={`text-2xl font-bold ${degradedModels > 0 ? 'text-orange-500' : ''}`}>
            {degradedModels}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            {t.overview.predictions24h}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{predictions24h.toLocaleString()}</div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            {t.overview.activeAlerts}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className={`text-2xl font-bold ${activeAlerts > 0 ? 'text-red-500' : ''}`}>
            {activeAlerts}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <TrendingDown className="h-4 w-4" />
            {t.overview.modelsWithDrift}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className={`text-2xl font-bold ${modelsWithDrift > 0 ? 'text-orange-500' : ''}`}>
            {modelsWithDrift}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <Clock className="h-4 w-4" />
            {t.overview.avgLatency}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {avgLatencyMs !== null ? `${avgLatencyMs.toFixed(1)}ms` : '-'}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
