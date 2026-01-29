/**
 * Cross Alert Card Component.
 *
 * Displays a correlated alert pair (anomaly + drift) with visual indicators.
 */

import { useIntlayer } from 'react-intlayer'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  ArrowRight,
  AlertTriangle,
  Activity,
  Clock,
  Columns,
  Target,
  ExternalLink,
} from 'lucide-react'

interface CorrelatedAlert {
  alert_id: string
  alert_type: 'anomaly' | 'drift'
  source_id: string
  source_name?: string | null
  severity: string
  message: string
  created_at: string
  anomaly_rate?: number | null
  anomaly_count?: number | null
  drift_percentage?: number | null
  drifted_columns?: string[] | null
}

interface CrossAlertCorrelation {
  id: string
  source_id: string
  source_name?: string | null
  correlation_strength: 'strong' | 'moderate' | 'weak' | 'none'
  confidence_score: number
  time_delta_seconds: number
  anomaly_alert?: CorrelatedAlert | null
  drift_alert?: CorrelatedAlert | null
  common_columns: string[]
  suggested_action?: string | null
}

interface CrossAlertCardProps {
  correlation: CrossAlertCorrelation
  showActions?: boolean
  compact?: boolean
}

export function CrossAlertCard({
  correlation,
  showActions = true,
  compact = false,
}: CrossAlertCardProps) {
  const t = useIntlayer('crossAlerts')

  const getStrengthColor = (strength: string) => {
    switch (strength) {
      case 'strong':
        return 'bg-red-500/10 text-red-500 border-red-500/20'
      case 'moderate':
        return 'bg-orange-500/10 text-orange-500 border-orange-500/20'
      case 'weak':
        return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
      default:
        return 'bg-gray-500/10 text-gray-500 border-gray-500/20'
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
      default:
        return 'bg-blue-500/10 text-blue-500 border-blue-500/20'
    }
  }

  const formatTimeDelta = (seconds: number) => {
    if (seconds < 60) {
      return `${seconds} ${t.time.seconds}`
    } else if (seconds < 3600) {
      return `${Math.round(seconds / 60)} ${t.time.minutes}`
    } else {
      return `${(seconds / 3600).toFixed(1)} ${t.time.hours}`
    }
  }

  const { anomaly_alert, drift_alert, correlation_strength, confidence_score, common_columns } =
    correlation

  if (compact) {
    return (
      <Card className="border hover:border-primary/50 transition-colors">
        <CardContent className="p-4">
          <div className="flex items-center justify-between gap-4">
            {/* Correlation indicator */}
            <div className="flex items-center gap-3">
              <Badge className={getStrengthColor(correlation_strength)}>
                {t.strength[correlation_strength as keyof typeof t.strength]}
              </Badge>
              <span className="text-sm text-muted-foreground">
                {(confidence_score * 100).toFixed(0)}% {t.labels.confidence}
              </span>
            </div>

            {/* Alert pair */}
            <div className="flex items-center gap-2">
              {anomaly_alert && (
                <Badge variant="outline" className="gap-1">
                  <AlertTriangle className="h-3 w-3" />
                  {anomaly_alert.anomaly_count} anomalies
                </Badge>
              )}
              <ArrowRight className="h-4 w-4 text-muted-foreground" />
              {drift_alert && (
                <Badge variant="outline" className="gap-1">
                  <Activity className="h-3 w-3" />
                  {drift_alert.drift_percentage?.toFixed(1)}% drift
                </Badge>
              )}
            </div>

            {/* Time delta */}
            <div className="flex items-center gap-1 text-sm text-muted-foreground">
              <Clock className="h-3 w-3" />
              {formatTimeDelta(correlation.time_delta_seconds)} {t.time.apart}
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Target className="h-5 w-5 text-primary" />
            {correlation.source_name || correlation.source_id}
          </CardTitle>
          <Badge className={getStrengthColor(correlation_strength)}>
            {t.strength[correlation_strength as keyof typeof t.strength]} {t.labels.correlationStrength}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Alert pair visualization */}
        <div className="grid grid-cols-[1fr,auto,1fr] items-center gap-4">
          {/* Anomaly Alert */}
          {anomaly_alert ? (
            <div className="p-3 rounded-lg bg-orange-500/5 border border-orange-500/20">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="h-4 w-4 text-orange-500" />
                <span className="font-medium">{t.alertType.anomaly}</span>
                <Badge className={getSeverityColor(anomaly_alert.severity)} variant="outline">
                  {anomaly_alert.severity}
                </Badge>
              </div>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">{t.labels.anomalyRate}:</span>
                  <span className="font-medium">
                    {((anomaly_alert.anomaly_rate || 0) * 100).toFixed(2)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">{t.labels.anomalyCount}:</span>
                  <span className="font-medium">{anomaly_alert.anomaly_count}</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-3 rounded-lg bg-muted text-center text-muted-foreground">
              No anomaly alert
            </div>
          )}

          {/* Connection arrow */}
          <div className="flex flex-col items-center gap-1">
            <ArrowRight className="h-6 w-6 text-primary" />
            <span className="text-xs text-muted-foreground">
              {formatTimeDelta(correlation.time_delta_seconds)}
            </span>
          </div>

          {/* Drift Alert */}
          {drift_alert ? (
            <div className="p-3 rounded-lg bg-blue-500/5 border border-blue-500/20">
              <div className="flex items-center gap-2 mb-2">
                <Activity className="h-4 w-4 text-blue-500" />
                <span className="font-medium">{t.alertType.drift}</span>
                <Badge className={getSeverityColor(drift_alert.severity)} variant="outline">
                  {drift_alert.severity}
                </Badge>
              </div>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">{t.labels.driftPercentage}:</span>
                  <span className="font-medium">
                    {(drift_alert.drift_percentage || 0).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">{t.labels.driftedColumns}:</span>
                  <span className="font-medium">
                    {drift_alert.drifted_columns?.length || 0}
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-3 rounded-lg bg-muted text-center text-muted-foreground">
              No drift alert
            </div>
          )}
        </div>

        {/* Common columns */}
        {common_columns.length > 0 && (
          <div className="flex items-start gap-2">
            <Columns className="h-4 w-4 text-muted-foreground mt-0.5" />
            <div>
              <span className="text-sm text-muted-foreground">{t.labels.commonColumns}: </span>
              <div className="flex flex-wrap gap-1 mt-1">
                {common_columns.slice(0, 5).map((col) => (
                  <Badge key={col} variant="secondary" className="text-xs">
                    {col}
                  </Badge>
                ))}
                {common_columns.length > 5 && (
                  <Badge variant="secondary" className="text-xs">
                    +{common_columns.length - 5} more
                  </Badge>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Suggested action */}
        {correlation.suggested_action && (
          <div className="p-3 rounded-lg bg-primary/5 border border-primary/20">
            <span className="text-sm font-medium">{t.labels.suggestedAction}: </span>
            <span className="text-sm text-muted-foreground">
              {correlation.suggested_action}
            </span>
          </div>
        )}

        {/* Confidence score */}
        <div className="flex items-center gap-4 pt-2 border-t">
          <div className="flex-1">
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-muted-foreground">{t.labels.confidence}</span>
              <span className="font-medium">{(confidence_score * 100).toFixed(0)}%</span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all"
                style={{ width: `${confidence_score * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* Actions */}
        {showActions && (
          <div className="flex gap-2 pt-2">
            <Button variant="outline" size="sm" asChild>
              <Link to="/anomaly">
                <AlertTriangle className="h-4 w-4 mr-1" />
                {t.actions.goToAnomaly}
                <ExternalLink className="h-3 w-3 ml-1" />
              </Link>
            </Button>
            <Button variant="outline" size="sm" asChild>
              <Link to="/drift-monitoring">
                <Activity className="h-4 w-4 mr-1" />
                {t.actions.goToDrift}
                <ExternalLink className="h-3 w-3 ml-1" />
              </Link>
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
