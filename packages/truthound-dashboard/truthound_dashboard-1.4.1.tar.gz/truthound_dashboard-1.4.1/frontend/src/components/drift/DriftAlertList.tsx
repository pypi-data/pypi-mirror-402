/**
 * Drift alert list component.
 *
 * Displays list of drift alerts with severity and actions.
 */

import { useIntlayer } from 'react-intlayer'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { formatDistanceToNow } from 'date-fns'
import {
  AlertTriangle,
  AlertCircle,
  Info,
  MoreHorizontal,
  Check,
  CheckCircle,
  Eye,
  XCircle,
  Loader2,
  Bell,
} from 'lucide-react'

export interface DriftAlert {
  id: string
  monitor_id: string
  comparison_id: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  drift_percentage: number
  drifted_columns: string[]
  message: string
  status: 'open' | 'acknowledged' | 'resolved' | 'ignored'
  acknowledged_at: string | null
  resolved_at: string | null
  notes: string | null
  created_at: string
}

interface DriftAlertListProps {
  alerts: DriftAlert[]
  isLoading?: boolean
  onAcknowledge?: (alert: DriftAlert) => void
  onResolve?: (alert: DriftAlert) => void
  onIgnore?: (alert: DriftAlert) => void
  onViewDetails?: (alert: DriftAlert) => void
}

const getSeverityIcon = (severity: string) => {
  switch (severity) {
    case 'critical':
      return <AlertCircle className="h-5 w-5 text-red-500" />
    case 'high':
      return <AlertTriangle className="h-5 w-5 text-orange-500" />
    case 'medium':
      return <AlertTriangle className="h-5 w-5 text-yellow-500" />
    case 'low':
      return <Info className="h-5 w-5 text-blue-500" />
    default:
      return <Info className="h-5 w-5 text-gray-500" />
  }
}

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'critical':
      return 'bg-red-500/10 text-red-500 border-red-500/20'
    case 'high':
      return 'bg-orange-500/10 text-orange-500 border-orange-500/20'
    case 'medium':
      return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
    case 'low':
      return 'bg-blue-500/10 text-blue-500 border-blue-500/20'
    default:
      return 'bg-gray-500/10 text-gray-500 border-gray-500/20'
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'open':
      return 'bg-red-500/10 text-red-500 border-red-500/20'
    case 'acknowledged':
      return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
    case 'resolved':
      return 'bg-green-500/10 text-green-500 border-green-500/20'
    case 'ignored':
      return 'bg-gray-500/10 text-gray-500 border-gray-500/20'
    default:
      return 'bg-gray-500/10 text-gray-500 border-gray-500/20'
  }
}

export function DriftAlertList({
  alerts,
  isLoading = false,
  onAcknowledge,
  onResolve,
  onIgnore,
  onViewDetails,
}: DriftAlertListProps) {
  const t = useIntlayer('driftMonitor')

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (alerts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed py-12">
        <Bell className="h-8 w-8 text-muted-foreground" />
        <p className="text-muted-foreground">{t.empty.noAlerts}</p>
        <p className="text-sm text-muted-foreground">{t.empty.noAlertsDesc}</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {alerts.map((alert) => (
        <Card
          key={alert.id}
          className={`transition-colors ${alert.status === 'open' ? 'border-l-4 border-l-red-500' : ''}`}
        >
          <CardContent className="flex items-center justify-between p-4">
            <div className="flex items-center gap-4">
              <div
                className={`rounded-lg p-2 ${
                  alert.severity === 'critical'
                    ? 'bg-red-500/10'
                    : alert.severity === 'high'
                      ? 'bg-orange-500/10'
                      : 'bg-yellow-500/10'
                }`}
              >
                {getSeverityIcon(alert.severity)}
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className={getSeverityColor(alert.severity)}>
                    {t.severity[alert.severity as keyof typeof t.severity]}
                  </Badge>
                  <Badge variant="outline" className={getStatusColor(alert.status)}>
                    {t.alertStatus[alert.status as keyof typeof t.alertStatus]}
                  </Badge>
                  <span className="text-sm font-medium">
                    {alert.drift_percentage.toFixed(1)}% drift
                  </span>
                </div>
                <p className="text-sm">{alert.message}</p>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span>
                    {formatDistanceToNow(new Date(alert.created_at), { addSuffix: true })}
                  </span>
                  {alert.drifted_columns.length > 0 && (
                    <>
                      <span>•</span>
                      <span>{alert.drifted_columns.length} columns affected</span>
                    </>
                  )}
                </div>
              </div>
            </div>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {onViewDetails && (
                  <DropdownMenuItem onClick={() => onViewDetails(alert)}>
                    <Eye className="mr-2 h-4 w-4" />
                    {t.alertActions.viewDetails}
                  </DropdownMenuItem>
                )}
                {alert.status === 'open' && onAcknowledge && (
                  <DropdownMenuItem onClick={() => onAcknowledge(alert)}>
                    <Check className="mr-2 h-4 w-4" />
                    {t.alertActions.acknowledge}
                  </DropdownMenuItem>
                )}
                {(alert.status === 'open' || alert.status === 'acknowledged') && onResolve && (
                  <DropdownMenuItem onClick={() => onResolve(alert)}>
                    <CheckCircle className="mr-2 h-4 w-4" />
                    {t.alertActions.resolve}
                  </DropdownMenuItem>
                )}
                {alert.status === 'open' && onIgnore && (
                  <DropdownMenuItem onClick={() => onIgnore(alert)}>
                    <XCircle className="mr-2 h-4 w-4" />
                    {t.alertActions.ignore}
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
