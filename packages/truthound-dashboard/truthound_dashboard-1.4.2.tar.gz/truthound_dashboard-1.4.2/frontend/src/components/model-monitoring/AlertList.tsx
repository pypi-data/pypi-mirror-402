/**
 * Alert list component for model monitoring.
 */

import { useIntlayer } from 'react-intlayer'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Check, CheckCheck, Loader2 } from 'lucide-react'
import { formatDate } from '@/lib/utils'

export interface AlertInstance {
  id: string
  rule_id: string
  model_id: string
  severity: 'critical' | 'warning' | 'info'
  message: string
  metric_value: number | null
  threshold_value: number | null
  acknowledged: boolean
  acknowledged_by: string | null
  acknowledged_at: string | null
  resolved: boolean
  resolved_at: string | null
  created_at: string
}

interface AlertListProps {
  alerts: AlertInstance[]
  isLoading: boolean
  onAcknowledge: (alert: AlertInstance) => void
  onResolve: (alert: AlertInstance) => void
}

export function AlertList({
  alerts,
  isLoading,
  onAcknowledge,
  onResolve,
}: AlertListProps) {
  const t = useIntlayer('modelMonitoring')

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'critical':
        return (
          <Badge className="bg-red-500/10 text-red-500 border-red-500/20">
            {t.severity.critical}
          </Badge>
        )
      case 'warning':
        return (
          <Badge className="bg-orange-500/10 text-orange-500 border-orange-500/20">
            {t.severity.warning}
          </Badge>
        )
      case 'info':
        return (
          <Badge className="bg-blue-500/10 text-blue-500 border-blue-500/20">
            {t.severity.info}
          </Badge>
        )
      default:
        return <Badge variant="outline">{severity}</Badge>
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (alerts.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        {t.alerts.noAlerts}
      </div>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>{t.alerts.severity}</TableHead>
          <TableHead>{t.alerts.message}</TableHead>
          <TableHead>Value</TableHead>
          <TableHead>{t.alerts.triggeredAt}</TableHead>
          <TableHead>{t.alerts.acknowledgedBy}</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {alerts.map((alert) => (
          <TableRow key={alert.id}>
            <TableCell>{getSeverityBadge(alert.severity)}</TableCell>
            <TableCell className="max-w-md truncate">{alert.message}</TableCell>
            <TableCell>
              {alert.metric_value !== null ? (
                <span>
                  {alert.metric_value.toFixed(2)}
                  {alert.threshold_value !== null && (
                    <span className="text-muted-foreground">
                      {' '}
                      / {alert.threshold_value}
                    </span>
                  )}
                </span>
              ) : (
                '-'
              )}
            </TableCell>
            <TableCell className="text-muted-foreground text-sm">
              {formatDate(alert.created_at)}
            </TableCell>
            <TableCell className="text-sm">
              {alert.acknowledged_by ? (
                <span className="text-green-500">{alert.acknowledged_by}</span>
              ) : (
                '-'
              )}
            </TableCell>
            <TableCell className="text-right">
              <div className="flex items-center justify-end gap-2">
                {!alert.acknowledged && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onAcknowledge(alert)}
                  >
                    <Check className="h-4 w-4 mr-1" />
                    {t.alerts.acknowledge}
                  </Button>
                )}
                {!alert.resolved && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onResolve(alert)}
                  >
                    <CheckCheck className="h-4 w-4 mr-1" />
                    {t.alerts.resolve}
                  </Button>
                )}
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
