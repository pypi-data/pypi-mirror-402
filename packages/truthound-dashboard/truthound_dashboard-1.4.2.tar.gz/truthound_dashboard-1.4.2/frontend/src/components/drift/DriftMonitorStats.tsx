/**
 * Drift monitor statistics cards.
 *
 * Displays overview statistics for drift monitoring.
 */

import { useIntlayer } from 'react-intlayer'
import { Card, CardContent, CardDescription, CardHeader } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Activity, AlertTriangle, CheckCircle, Columns } from 'lucide-react'

interface DriftMonitorStatsProps {
  totalMonitors: number
  activeMonitors: number
  monitorsWithDrift: number
  openAlerts: number
  criticalAlerts: number
  onViewColumnDetails?: () => void
  showColumnDetailsButton?: boolean
}

export function DriftMonitorStats({
  totalMonitors,
  activeMonitors,
  monitorsWithDrift,
  openAlerts,
  criticalAlerts,
  onViewColumnDetails,
  showColumnDetailsButton = false,
}: DriftMonitorStatsProps) {
  const t = useIntlayer('driftMonitor')

  return (
    <div className="grid gap-4 md:grid-cols-4">
      <Card>
        <CardHeader className="pb-2">
          <CardDescription>{t.stats.activeMonitors}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-green-500" />
            <span className="text-2xl font-bold">
              {activeMonitors} / {totalMonitors}
            </span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardDescription>{t.stats.monitorsWithDrift}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {monitorsWithDrift > 0 ? (
                <AlertTriangle className="h-5 w-5 text-orange-500" />
              ) : (
                <CheckCircle className="h-5 w-5 text-green-500" />
              )}
              <span
                className={`text-2xl font-bold ${monitorsWithDrift > 0 ? 'text-orange-500' : 'text-green-500'}`}
              >
                {monitorsWithDrift}
              </span>
            </div>
            {showColumnDetailsButton && monitorsWithDrift > 0 && onViewColumnDetails && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onViewColumnDetails}
                className="text-xs"
              >
                <Columns className="h-3 w-3 mr-1" />
                {t.columnDrilldown?.viewDetails ?? 'View Details'}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardDescription>{t.stats.openAlerts}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <AlertTriangle
              className={`h-5 w-5 ${openAlerts > 0 ? 'text-orange-500' : 'text-muted-foreground'}`}
            />
            <span className={`text-2xl font-bold ${openAlerts > 0 ? 'text-orange-500' : ''}`}>
              {openAlerts}
            </span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardDescription>{t.stats.criticalAlerts}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <AlertTriangle
              className={`h-5 w-5 ${criticalAlerts > 0 ? 'text-red-500' : 'text-muted-foreground'}`}
            />
            <span className={`text-2xl font-bold ${criticalAlerts > 0 ? 'text-red-500' : ''}`}>
              {criticalAlerts}
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
