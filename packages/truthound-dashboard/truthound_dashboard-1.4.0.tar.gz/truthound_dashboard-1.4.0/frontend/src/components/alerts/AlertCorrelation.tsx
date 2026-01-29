/**
 * AlertCorrelation Component
 *
 * Displays related alerts for a given alert, grouped by:
 * - Same source (data source, model)
 * - Similar time frame
 * - Similar severity
 */

import { useIntlayer } from '@/providers'
import { str } from '@/lib/intlayer-utils'
import { formatDistanceToNow } from 'date-fns'
import {
  AlertTriangle,
  AlertCircle,
  Info,
  Link2,
  ExternalLink,
  Clock,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'

// Types
type AlertSource = 'model' | 'drift' | 'anomaly' | 'validation'
type AlertSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info'
type AlertStatus = 'open' | 'acknowledged' | 'resolved' | 'ignored'

interface UnifiedAlert {
  id: string
  source: AlertSource
  source_id: string
  source_name: string
  severity: AlertSeverity
  status: AlertStatus
  title: string
  message: string
  details: Record<string, unknown>
  acknowledged_at: string | null
  acknowledged_by: string | null
  resolved_at: string | null
  resolved_by: string | null
  created_at: string
  updated_at: string
}

interface AlertCorrelationData {
  alert_id: string
  related_alerts: UnifiedAlert[]
  correlation_type: string
  correlation_score: number
  common_factors: string[]
}

interface AlertCorrelationProps {
  alertId: string
  correlations: AlertCorrelationData[]
  loading?: boolean
  onViewAlert?: (alert: UnifiedAlert) => void
}

const severityConfig: Record<AlertSeverity, { icon: typeof AlertTriangle; color: string; bgColor: string }> = {
  critical: { icon: AlertTriangle, color: 'text-red-500', bgColor: 'bg-red-100 dark:bg-red-900/30' },
  high: { icon: AlertCircle, color: 'text-orange-500', bgColor: 'bg-orange-100 dark:bg-orange-900/30' },
  medium: { icon: AlertCircle, color: 'text-yellow-500', bgColor: 'bg-yellow-100 dark:bg-yellow-900/30' },
  low: { icon: Info, color: 'text-blue-500', bgColor: 'bg-blue-100 dark:bg-blue-900/30' },
  info: { icon: Info, color: 'text-gray-500', bgColor: 'bg-gray-100 dark:bg-gray-900/30' },
}

const correlationTypeLabels: Record<string, string> = {
  same_source: 'Same Source',
  temporal_severity: 'Similar Time & Severity',
}

export function AlertCorrelation({
  alertId: _alertId, // Reserved for future use (e.g., highlighting the current alert)
  correlations,
  loading = false,
  onViewAlert,
}: AlertCorrelationProps) {
  const content = useIntlayer('alerts')

  const SeverityIcon = ({ severity }: { severity: AlertSeverity }) => {
    const config = severityConfig[severity]
    const Icon = config.icon
    return <Icon className={cn('h-3 w-3', config.color)} />
  }

  if (loading) {
    return (
      <Card className="animate-pulse">
        <CardHeader>
          <div className="h-5 w-32 bg-muted rounded" />
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="h-16 bg-muted rounded" />
            <div className="h-16 bg-muted rounded" />
          </div>
        </CardContent>
      </Card>
    )
  }

  const totalCorrelated = correlations.reduce(
    (sum, c) => sum + c.related_alerts.length,
    0
  )

  if (correlations.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Link2 className="h-4 w-4" />
            {str(content.correlation.title)}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-6 text-muted-foreground">
            <Link2 className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>{str(content.correlation.noCorrelations)}</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-base">
          <div className="flex items-center gap-2">
            <Link2 className="h-4 w-4" />
            {str(content.correlation.title)}
          </div>
          <Badge variant="secondary">{totalCorrelated} related</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {correlations.map((correlation, idx) => (
          <div key={idx} className="space-y-3">
            {/* Correlation header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">
                  {correlationTypeLabels[correlation.correlation_type] || correlation.correlation_type}
                </span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <span className="text-muted-foreground">
                  {str(content.correlation.correlationScore)}:
                </span>
                <div className="w-24">
                  <Progress value={correlation.correlation_score * 100} />
                </div>
                <span className="text-xs font-medium">
                  {Math.round(correlation.correlation_score * 100)}%
                </span>
              </div>
            </div>

            {/* Common factors */}
            <div className="flex flex-wrap gap-1">
              {correlation.common_factors.map((factor, i) => (
                <Badge key={i} variant="outline" className="text-xs">
                  {factor}
                </Badge>
              ))}
            </div>

            {/* Related alerts */}
            <div className="space-y-2">
              {correlation.related_alerts.map((alert) => (
                <div
                  key={alert.id}
                  className="flex items-center justify-between p-2 rounded-lg border bg-muted/50 hover:bg-muted transition-colors"
                >
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <div className={cn(
                      'flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center',
                      severityConfig[alert.severity].bgColor
                    )}>
                      <SeverityIcon severity={alert.severity} />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium truncate">{alert.title}</p>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span>{alert.source_name}</span>
                        <span>-</span>
                        <Clock className="h-3 w-3" />
                        <span>
                          {formatDistanceToNow(new Date(alert.created_at), { addSuffix: true })}
                        </span>
                      </div>
                    </div>
                  </div>
                  {onViewAlert && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onViewAlert(alert)}
                    >
                      <ExternalLink className="h-3 w-3" />
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

export default AlertCorrelation
