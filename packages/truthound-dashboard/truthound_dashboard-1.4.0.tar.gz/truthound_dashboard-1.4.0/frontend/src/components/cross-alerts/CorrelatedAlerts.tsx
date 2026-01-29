/**
 * Correlated Alerts Component.
 *
 * Shows anomaly+drift alert pairs with timeline visualization.
 */

import { useCallback, useEffect, useState } from 'react'
import { useIntlayer } from 'react-intlayer'
import { str } from '@/lib/intlayer-utils'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/hooks/use-toast'
import { Loader2, RefreshCw, Link2, AlertTriangle, Activity } from 'lucide-react'
import { CrossAlertCard } from './CrossAlertCard'

const API_BASE = '/api/v1'

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
  created_at?: string
}

interface CorrelatedAlertsProps {
  sourceId: string
  sourceName?: string
  timeWindowHours?: number
  maxItems?: number
  compact?: boolean
  showHeader?: boolean
}

export function CorrelatedAlerts({
  sourceId,
  sourceName,
  timeWindowHours = 24,
  maxItems = 10,
  compact = false,
  showHeader = true,
}: CorrelatedAlertsProps) {
  const t = useIntlayer('crossAlerts')
  const common = useIntlayer('common')
  const { toast } = useToast()

  const [correlations, setCorrelations] = useState<CrossAlertCorrelation[]>([])
  const [isLoading, setIsLoading] = useState(true)

  const loadCorrelations = useCallback(async () => {
    setIsLoading(true)
    try {
      const response = await fetch(
        `${API_BASE}/cross-alerts/correlations/${sourceId}?time_window_hours=${timeWindowHours}&limit=${maxItems}`
      )
      if (!response.ok) throw new Error('Failed to fetch correlations')
      const result = await response.json()
      setCorrelations(result.data || [])
    } catch (error) {
      toast({
        title: str(common.error),
        description: str(t.messages.errorLoadingCorrelations),
        variant: 'destructive',
      })
      setCorrelations([])
    } finally {
      setIsLoading(false)
    }
  }, [sourceId, timeWindowHours, maxItems, toast, common, t])

  useEffect(() => {
    loadCorrelations()
  }, [loadCorrelations])

  // Count by strength
  const strongCount = correlations.filter((c) => c.correlation_strength === 'strong').length
  const moderateCount = correlations.filter((c) => c.correlation_strength === 'moderate').length

  if (isLoading) {
    return (
      <Card>
        {showHeader && (
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Link2 className="h-5 w-5" />
              {t.sections.correlations}
            </CardTitle>
          </CardHeader>
        )}
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    )
  }

  if (correlations.length === 0) {
    return (
      <Card>
        {showHeader && (
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Link2 className="h-5 w-5" />
              {t.sections.correlations}
            </CardTitle>
            <CardDescription>
              {sourceName || sourceId}
            </CardDescription>
          </CardHeader>
        )}
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Link2 className="h-12 w-12 text-muted-foreground/50 mb-4" />
            <p className="font-medium text-muted-foreground">{t.empty.noCorrelations}</p>
            <p className="text-sm text-muted-foreground mt-1">{t.empty.noCorrelationsDesc}</p>
            <Button variant="outline" size="sm" className="mt-4" onClick={loadCorrelations}>
              <RefreshCw className="h-4 w-4 mr-2" />
              {t.actions.refresh}
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      {showHeader && (
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Link2 className="h-5 w-5" />
                {t.sections.correlations}
              </CardTitle>
              <CardDescription className="mt-1">
                {sourceName || sourceId} - Last {timeWindowHours}h
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="gap-1">
                {correlations.length} total
              </Badge>
              {strongCount > 0 && (
                <Badge className="bg-red-500/10 text-red-500 border-red-500/20 gap-1">
                  {strongCount} {t.strength.strong}
                </Badge>
              )}
              {moderateCount > 0 && (
                <Badge className="bg-orange-500/10 text-orange-500 border-orange-500/20 gap-1">
                  {moderateCount} {t.strength.moderate}
                </Badge>
              )}
              <Button variant="ghost" size="icon" onClick={loadCorrelations}>
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
      )}
      <CardContent className={showHeader ? '' : 'pt-6'}>
        <div className="space-y-4">
          {correlations.map((correlation) => (
            <CrossAlertCard
              key={correlation.id}
              correlation={correlation}
              compact={compact}
              showActions={!compact}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Mini version for embedding in other pages.
 */
interface RelatedAlertsProps {
  sourceId: string
  alertType: 'anomaly' | 'drift'
  title?: string
  maxItems?: number
}

export function RelatedAlerts({
  sourceId,
  alertType,
  title,
  maxItems = 5,
}: RelatedAlertsProps) {
  const t = useIntlayer('crossAlerts')

  const [correlations, setCorrelations] = useState<CrossAlertCorrelation[]>([])
  const [isLoading, setIsLoading] = useState(true)

  const loadCorrelations = useCallback(async () => {
    setIsLoading(true)
    try {
      const response = await fetch(
        `${API_BASE}/cross-alerts/correlations/${sourceId}?time_window_hours=48&limit=${maxItems}`
      )
      if (!response.ok) throw new Error('Failed to fetch')
      const result = await response.json()
      setCorrelations(result.data || [])
    } catch {
      setCorrelations([])
    } finally {
      setIsLoading(false)
    }
  }, [sourceId, maxItems])

  useEffect(() => {
    loadCorrelations()
  }, [loadCorrelations])

  // Get the related alerts based on type
  const relatedAlerts = correlations
    .filter((c) => {
      if (alertType === 'anomaly') {
        return c.drift_alert !== null
      } else {
        return c.anomaly_alert !== null
      }
    })
    .slice(0, maxItems)

  const defaultTitle =
    alertType === 'anomaly' ? t.sections.relatedDriftAlerts : t.sections.relatedAnomalyAlerts

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            {alertType === 'anomaly' ? (
              <Activity className="h-4 w-4 text-blue-500" />
            ) : (
              <AlertTriangle className="h-4 w-4 text-orange-500" />
            )}
            {title || defaultTitle}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-4">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    )
  }

  if (relatedAlerts.length === 0) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            {alertType === 'anomaly' ? (
              <Activity className="h-4 w-4 text-blue-500" />
            ) : (
              <AlertTriangle className="h-4 w-4 text-orange-500" />
            )}
            {title || defaultTitle}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-4 text-sm text-muted-foreground">
            <p>{t.empty.noRelatedAlerts}</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            {alertType === 'anomaly' ? (
              <Activity className="h-4 w-4 text-blue-500" />
            ) : (
              <AlertTriangle className="h-4 w-4 text-orange-500" />
            )}
            {title || defaultTitle}
          </CardTitle>
          <Badge variant="outline">{relatedAlerts.length} found</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {relatedAlerts.map((correlation) => {
          const alert = alertType === 'anomaly' ? correlation.drift_alert : correlation.anomaly_alert
          if (!alert) return null

          return (
            <div
              key={correlation.id}
              className="flex items-center justify-between p-2 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
            >
              <div className="flex items-center gap-2">
                <Badge
                  className={
                    correlation.correlation_strength === 'strong'
                      ? 'bg-red-500/10 text-red-500 border-red-500/20'
                      : correlation.correlation_strength === 'moderate'
                        ? 'bg-orange-500/10 text-orange-500 border-orange-500/20'
                        : 'bg-gray-500/10 text-gray-500 border-gray-500/20'
                  }
                >
                  {t.strength[correlation.correlation_strength as keyof typeof t.strength]}
                </Badge>
                <span className="text-sm">
                  {alertType === 'anomaly'
                    ? `${(alert.drift_percentage || 0).toFixed(1)}% drift`
                    : `${alert.anomaly_count || 0} anomalies`}
                </span>
              </div>
              <span className="text-xs text-muted-foreground">
                {new Date(alert.created_at).toLocaleString()}
              </span>
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}
