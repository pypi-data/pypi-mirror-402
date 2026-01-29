/**
 * Alerts Page
 *
 * Unified alerts dashboard showing:
 * - Summary statistics
 * - Alert list with filters
 * - Correlation panel for selected alert
 */

import { useState, useEffect, useCallback } from 'react'
import { useSafeIntlayer } from '@/hooks/useSafeIntlayer'
import { str } from '@/lib/intlayer-utils'
import { useToast } from '@/hooks/use-toast'
import { RefreshCw, BellRing } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  UnifiedAlertList,
  AlertSummaryCards,
  AlertCorrelation,
} from '@/components/alerts'
import { apiClient } from '@/api/client'

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

interface AlertCorrelationData {
  alert_id: string
  related_alerts: UnifiedAlert[]
  correlation_type: string
  correlation_score: number
  common_factors: string[]
}

export default function Alerts() {
  const content = useSafeIntlayer('alerts')
  const common = useSafeIntlayer('common')
  const { toast } = useToast()

  // State
  const [alerts, setAlerts] = useState<UnifiedAlert[]>([])
  const [summary, setSummary] = useState<AlertSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [summaryLoading, setSummaryLoading] = useState(true)

  // Filters
  const [sourceFilter, setSourceFilter] = useState<AlertSource | null>(null)
  const [severityFilter, setSeverityFilter] = useState<AlertSeverity | null>(null)
  const [statusFilter, setStatusFilter] = useState<AlertStatus | null>(null)

  // Selected alert for details/correlations
  const [selectedAlert, setSelectedAlert] = useState<UnifiedAlert | null>(null)
  const [correlations, setCorrelations] = useState<AlertCorrelationData[]>([])
  const [correlationsLoading, setCorrelationsLoading] = useState(false)
  const [detailsOpen, setDetailsOpen] = useState(false)

  // Action dialogs
  const [acknowledgeDialog, setAcknowledgeDialog] = useState<{
    open: boolean
    alertId: string | null
    bulk: boolean
    alertIds: string[]
  }>({ open: false, alertId: null, bulk: false, alertIds: [] })
  const [resolveDialog, setResolveDialog] = useState<{
    open: boolean
    alertId: string | null
    bulk: boolean
    alertIds: string[]
  }>({ open: false, alertId: null, bulk: false, alertIds: [] })
  const [actorName, setActorName] = useState('')
  const [actionMessage, setActionMessage] = useState('')

  // Fetch alerts
  const fetchAlerts = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (sourceFilter) params.set('source', sourceFilter)
      if (severityFilter) params.set('severity', severityFilter)
      if (statusFilter) params.set('status', statusFilter)
      params.set('limit', '100')

      const response = await apiClient.get(`/alerts?${params.toString()}`) as { data: { data: { items: UnifiedAlert[] } } }
      setAlerts(response.data.data.items)
    } catch (error) {
      toast({
        title: str(common.error),
        description: 'Failed to load alerts',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }, [sourceFilter, severityFilter, statusFilter, toast, common.error])

  // Fetch summary
  const fetchSummary = useCallback(async () => {
    setSummaryLoading(true)
    try {
      const response = await apiClient.get('/alerts/summary') as { data: { data: AlertSummary } }
      setSummary(response.data.data)
    } catch (error) {
      console.error('Failed to load summary:', error)
    } finally {
      setSummaryLoading(false)
    }
  }, [])

  // Fetch correlations for selected alert
  const fetchCorrelations = useCallback(async (alertId: string) => {
    setCorrelationsLoading(true)
    try {
      const response = await apiClient.get(`/alerts/${alertId}/correlations`) as { data: { data: { correlations: AlertCorrelationData[] } } }
      setCorrelations(response.data.data.correlations)
    } catch (error) {
      console.error('Failed to load correlations:', error)
      setCorrelations([])
    } finally {
      setCorrelationsLoading(false)
    }
  }, [])

  // Initial load
  useEffect(() => {
    fetchAlerts()
    fetchSummary()
  }, [fetchAlerts, fetchSummary])

  // Handle view details
  const handleViewDetails = (alert: UnifiedAlert) => {
    setSelectedAlert(alert)
    setDetailsOpen(true)
    fetchCorrelations(alert.id)
  }

  // Handle view correlations from list
  const handleViewCorrelations = (alert: UnifiedAlert) => {
    setSelectedAlert(alert)
    setDetailsOpen(true)
    fetchCorrelations(alert.id)
  }

  // Handle acknowledge
  const handleAcknowledge = (alertId: string) => {
    setAcknowledgeDialog({ open: true, alertId, bulk: false, alertIds: [] })
  }

  const handleBulkAcknowledge = (alertIds: string[]) => {
    setAcknowledgeDialog({ open: true, alertId: null, bulk: true, alertIds })
  }

  const confirmAcknowledge = async () => {
    if (!actorName.trim()) return

    try {
      if (acknowledgeDialog.bulk) {
        await apiClient.post('/alerts/bulk/acknowledge', {
          alert_ids: acknowledgeDialog.alertIds,
          actor: actorName,
          message: actionMessage,
        })
        toast({
          title: str(common.success),
          description: str(content.messages.acknowledgeSuccess),
        })
      } else if (acknowledgeDialog.alertId) {
        await apiClient.post(`/alerts/${acknowledgeDialog.alertId}/acknowledge`, {
          actor: actorName,
          message: actionMessage,
        })
        toast({
          title: str(common.success),
          description: str(content.messages.acknowledgeSuccess),
        })
      }

      setAcknowledgeDialog({ open: false, alertId: null, bulk: false, alertIds: [] })
      setActorName('')
      setActionMessage('')
      fetchAlerts()
      fetchSummary()
    } catch (error) {
      toast({
        title: str(common.error),
        description: str(content.messages.acknowledgeFailed),
        variant: 'destructive',
      })
    }
  }

  // Handle resolve
  const handleResolve = (alertId: string) => {
    setResolveDialog({ open: true, alertId, bulk: false, alertIds: [] })
  }

  const handleBulkResolve = (alertIds: string[]) => {
    setResolveDialog({ open: true, alertId: null, bulk: true, alertIds })
  }

  const confirmResolve = async () => {
    if (!actorName.trim()) return

    try {
      if (resolveDialog.bulk) {
        await apiClient.post('/alerts/bulk/resolve', {
          alert_ids: resolveDialog.alertIds,
          actor: actorName,
          message: actionMessage,
        })
        toast({
          title: str(common.success),
          description: str(content.messages.resolveSuccess),
        })
      } else if (resolveDialog.alertId) {
        await apiClient.post(`/alerts/${resolveDialog.alertId}/resolve`, {
          actor: actorName,
          message: actionMessage,
        })
        toast({
          title: str(common.success),
          description: str(content.messages.resolveSuccess),
        })
      }

      setResolveDialog({ open: false, alertId: null, bulk: false, alertIds: [] })
      setActorName('')
      setActionMessage('')
      fetchAlerts()
      fetchSummary()
    } catch (error) {
      toast({
        title: str(common.error),
        description: str(content.messages.resolveFailed),
        variant: 'destructive',
      })
    }
  }

  // Handle refresh
  const handleRefresh = () => {
    fetchAlerts()
    fetchSummary()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <BellRing className="h-6 w-6 text-primary" />
            {str(content.title)}
          </h1>
          <p className="text-muted-foreground">{str(content.subtitle)}</p>
        </div>
        <Button variant="outline" onClick={handleRefresh}>
          <RefreshCw className="h-4 w-4 mr-2" />
          {str(content.actions.refresh)}
        </Button>
      </div>

      {/* Summary Cards */}
      <AlertSummaryCards summary={summary} loading={summaryLoading} />

      {/* Alert List */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold">All Alerts</h2>
        <UnifiedAlertList
          alerts={alerts}
          loading={loading}
          sourceFilter={sourceFilter}
          severityFilter={severityFilter}
          statusFilter={statusFilter}
          onSourceFilterChange={setSourceFilter}
          onSeverityFilterChange={setSeverityFilter}
          onStatusFilterChange={setStatusFilter}
          onAcknowledge={handleAcknowledge}
          onResolve={handleResolve}
          onBulkAcknowledge={handleBulkAcknowledge}
          onBulkResolve={handleBulkResolve}
          onViewDetails={handleViewDetails}
          onViewCorrelations={handleViewCorrelations}
        />
      </div>

      {/* Alert Details Sheet */}
      <Sheet open={detailsOpen} onOpenChange={setDetailsOpen}>
        <SheetContent className="sm:max-w-lg overflow-y-auto">
          <SheetHeader>
            <SheetTitle>{str(content.details.title)}</SheetTitle>
            <SheetDescription>
              {selectedAlert?.title}
            </SheetDescription>
          </SheetHeader>

          {selectedAlert && (
            <div className="mt-6 space-y-6">
              {/* Alert Info */}
              <div className="space-y-4">
                <div>
                  <Label className="text-muted-foreground">{str(content.details.message)}</Label>
                  <p className="mt-1">{selectedAlert.message}</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-muted-foreground">{str(content.details.source)}</Label>
                    <p className="mt-1">{selectedAlert.source_name}</p>
                  </div>
                  <div>
                    <Label className="text-muted-foreground">{str(content.columns.status)}</Label>
                    <p className="mt-1 capitalize">{selectedAlert.status}</p>
                  </div>
                </div>

                <div>
                  <Label className="text-muted-foreground">{str(content.details.createdAt)}</Label>
                  <p className="mt-1">{new Date(selectedAlert.created_at).toLocaleString()}</p>
                </div>

                {selectedAlert.acknowledged_at && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-muted-foreground">{str(content.details.acknowledgedAt)}</Label>
                      <p className="mt-1">{new Date(selectedAlert.acknowledged_at).toLocaleString()}</p>
                    </div>
                    <div>
                      <Label className="text-muted-foreground">{str(content.details.acknowledgedBy)}</Label>
                      <p className="mt-1">{selectedAlert.acknowledged_by}</p>
                    </div>
                  </div>
                )}

                {selectedAlert.resolved_at && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-muted-foreground">{str(content.details.resolvedAt)}</Label>
                      <p className="mt-1">{new Date(selectedAlert.resolved_at).toLocaleString()}</p>
                    </div>
                    <div>
                      <Label className="text-muted-foreground">{str(content.details.resolvedBy)}</Label>
                      <p className="mt-1">{selectedAlert.resolved_by}</p>
                    </div>
                  </div>
                )}

                {/* Additional details */}
                {Object.keys(selectedAlert.details).length > 0 && (
                  <div>
                    <Label className="text-muted-foreground">{str(content.details.additionalDetails)}</Label>
                    <pre className="mt-1 p-3 bg-muted rounded-lg text-xs overflow-x-auto">
                      {JSON.stringify(selectedAlert.details, null, 2)}
                    </pre>
                  </div>
                )}
              </div>

              {/* Correlations */}
              <AlertCorrelation
                alertId={selectedAlert.id}
                correlations={correlations}
                loading={correlationsLoading}
                onViewAlert={(alert) => {
                  setSelectedAlert(alert)
                  fetchCorrelations(alert.id)
                }}
              />
            </div>
          )}
        </SheetContent>
      </Sheet>

      {/* Acknowledge Dialog */}
      <Dialog
        open={acknowledgeDialog.open}
        onOpenChange={(open) => {
          if (!open) {
            setAcknowledgeDialog({ open: false, alertId: null, bulk: false, alertIds: [] })
            setActorName('')
            setActionMessage('')
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{str(content.acknowledgeDialog.title)}</DialogTitle>
            <DialogDescription>
              {str(content.acknowledgeDialog.description)}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="actor-name">{str(content.acknowledgeDialog.nameLabel)}</Label>
              <Input
                id="actor-name"
                value={actorName}
                onChange={(e) => setActorName(e.target.value)}
                placeholder="Your name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="action-message">{str(content.acknowledgeDialog.messageLabel)}</Label>
              <Textarea
                id="action-message"
                value={actionMessage}
                onChange={(e) => setActionMessage(e.target.value)}
                placeholder="Optional message..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setAcknowledgeDialog({ open: false, alertId: null, bulk: false, alertIds: [] })
                setActorName('')
                setActionMessage('')
              }}
            >
              {str(content.acknowledgeDialog.cancel)}
            </Button>
            <Button onClick={confirmAcknowledge} disabled={!actorName.trim()}>
              {str(content.acknowledgeDialog.confirm)}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Resolve Dialog */}
      <Dialog
        open={resolveDialog.open}
        onOpenChange={(open) => {
          if (!open) {
            setResolveDialog({ open: false, alertId: null, bulk: false, alertIds: [] })
            setActorName('')
            setActionMessage('')
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{str(content.resolveDialog.title)}</DialogTitle>
            <DialogDescription>
              {str(content.resolveDialog.description)}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="resolve-actor-name">{str(content.resolveDialog.nameLabel)}</Label>
              <Input
                id="resolve-actor-name"
                value={actorName}
                onChange={(e) => setActorName(e.target.value)}
                placeholder="Your name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="resolve-message">{str(content.resolveDialog.messageLabel)}</Label>
              <Textarea
                id="resolve-message"
                value={actionMessage}
                onChange={(e) => setActionMessage(e.target.value)}
                placeholder="Resolution details..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setResolveDialog({ open: false, alertId: null, bulk: false, alertIds: [] })
                setActorName('')
                setActionMessage('')
              }}
            >
              {str(content.resolveDialog.cancel)}
            </Button>
            <Button onClick={confirmResolve} disabled={!actorName.trim()}>
              {str(content.resolveDialog.confirm)}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
