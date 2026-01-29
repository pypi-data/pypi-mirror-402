/**
 * Drift Monitoring Page.
 *
 * Provides automatic drift detection monitoring with alerts and trends.
 */

import { useCallback, useEffect, useState } from 'react'
import { useIntlayer } from 'react-intlayer'
import { str } from '@/lib/intlayer-utils'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { useToast } from '@/hooks/use-toast'
import { Loader2, Plus, RefreshCw, Activity, Bell, TrendingUp, Columns, Eye, Search } from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  DriftMonitorList,
  DriftMonitorForm,
  DriftAlertList,
  DriftTrendChart,
  DriftMonitorStats,
  ColumnDrilldown,
  DriftPreview,
  RootCauseAnalysis,
  RemediationPanel,
} from '@/components/drift'
import type { RootCauseAnalysisData, RemediationSuggestion } from '@/components/drift'
import { RelatedAlerts, AutoTriggerConfigPanel } from '@/components/cross-alerts'
import type { DriftMonitor } from '@/components/drift/DriftMonitorList'
import type { DriftAlert } from '@/components/drift/DriftAlertList'
import type { Source, DriftResult } from '@/api/client'
import { listSources } from '@/api/client'

// API functions for drift monitoring
const API_BASE = '/api/v1'

async function listDriftMonitors(): Promise<{ data: DriftMonitor[]; total: number }> {
  const response = await fetch(`${API_BASE}/drift/monitors`)
  if (!response.ok) throw new Error('Failed to fetch monitors')
  const result = await response.json()
  return result
}

async function getDriftMonitorsSummary(): Promise<{
  total_monitors: number
  active_monitors: number
  paused_monitors: number
  monitors_with_drift: number
  total_open_alerts: number
  critical_alerts: number
  high_alerts: number
}> {
  const response = await fetch(`${API_BASE}/drift/monitors/summary`)
  if (!response.ok) throw new Error('Failed to fetch summary')
  const result = await response.json()
  return result.data
}

async function createDriftMonitor(data: object): Promise<DriftMonitor> {
  const response = await fetch(`${API_BASE}/drift/monitors`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) throw new Error('Failed to create monitor')
  const result = await response.json()
  return result.data
}

async function updateDriftMonitor(id: string, data: object): Promise<DriftMonitor> {
  const response = await fetch(`${API_BASE}/drift/monitors/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) throw new Error('Failed to update monitor')
  const result = await response.json()
  return result.data
}

async function deleteDriftMonitor(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/drift/monitors/${id}`, { method: 'DELETE' })
  if (!response.ok) throw new Error('Failed to delete monitor')
}

async function runDriftMonitor(id: string): Promise<{ has_drift: boolean; drift_percentage: number }> {
  const response = await fetch(`${API_BASE}/drift/monitors/${id}/run`, { method: 'POST' })
  if (!response.ok) throw new Error('Failed to run monitor')
  const result = await response.json()
  return result.data
}

async function getDriftMonitorTrend(id: string, days: number = 30): Promise<object> {
  const response = await fetch(`${API_BASE}/drift/monitors/${id}/trend?days=${days}`)
  if (!response.ok) throw new Error('Failed to fetch trend')
  const result = await response.json()
  return result.data
}

async function getDriftMonitorLatestRun(id: string): Promise<DriftResult | null> {
  const response = await fetch(`${API_BASE}/drift/monitors/${id}/latest-run`)
  if (!response.ok) return null
  const result = await response.json()
  return result.data
}

async function listDriftAlerts(params?: {
  status?: string
  severity?: string
}): Promise<{ data: DriftAlert[]; total: number }> {
  const searchParams = new URLSearchParams()
  if (params?.status) searchParams.append('status', params.status)
  if (params?.severity) searchParams.append('severity', params.severity)
  const response = await fetch(`${API_BASE}/drift/alerts?${searchParams}`)
  if (!response.ok) throw new Error('Failed to fetch alerts')
  const result = await response.json()
  return result
}

async function updateDriftAlert(id: string, data: { status?: string; notes?: string }): Promise<DriftAlert> {
  const response = await fetch(`${API_BASE}/drift/alerts/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) throw new Error('Failed to update alert')
  const result = await response.json()
  return result.data
}

async function getDriftRootCauseAnalysis(
  monitorId: string,
  runId: string
): Promise<RootCauseAnalysisData | null> {
  const response = await fetch(`${API_BASE}/drift/monitors/${monitorId}/runs/${runId}/root-cause`)
  if (!response.ok) return null
  const result = await response.json()
  return result.data
}

export default function DriftMonitoring() {
  const t = useIntlayer('driftMonitor')
  const common = useIntlayer('common')
  const { toast } = useToast()

  // State
  const [activeTab, setActiveTab] = useState('monitors')
  const [isLoading, setIsLoading] = useState(true)
  const [monitors, setMonitors] = useState<DriftMonitor[]>([])
  const [alerts, setAlerts] = useState<DriftAlert[]>([])
  const [sources, setSources] = useState<Source[]>([])
  const [summary, setSummary] = useState({
    total_monitors: 0,
    active_monitors: 0,
    paused_monitors: 0,
    monitors_with_drift: 0,
    total_open_alerts: 0,
    critical_alerts: 0,
    high_alerts: 0,
  })
  const [selectedMonitorId, setSelectedMonitorId] = useState<string>('')
  const [trendData, setTrendData] = useState<object | null>(null)
  const [isLoadingTrend, setIsLoadingTrend] = useState(false)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingMonitor, setEditingMonitor] = useState<DriftMonitor | null>(null)

  // Column drilldown state
  const [showColumnDrilldown, setShowColumnDrilldown] = useState(false)
  const [selectedMonitorForDrilldown, setSelectedMonitorForDrilldown] = useState<DriftMonitor | null>(null)
  const [latestRunResult, setLatestRunResult] = useState<DriftResult | null>(null)
  const [isLoadingLatestRun, setIsLoadingLatestRun] = useState(false)

  // Preview state
  const [showPreview, setShowPreview] = useState(false)

  // Root cause analysis state
  const [rootCauseData, setRootCauseData] = useState<RootCauseAnalysisData | null>(null)
  const [isLoadingRootCause, setIsLoadingRootCause] = useState(false)
  const [showRootCause, setShowRootCause] = useState(false)

  // Load data
  const loadData = useCallback(async () => {
    setIsLoading(true)
    try {
      const [monitorsResult, alertsResult, summaryResult, sourcesResult] = await Promise.all([
        listDriftMonitors(),
        listDriftAlerts({ status: 'open' }),
        getDriftMonitorsSummary(),
        listSources({ limit: 100 }),
      ])

      setMonitors(monitorsResult.data)
      setAlerts(alertsResult.data)
      setSummary(summaryResult)
      setSources(sourcesResult.data)

      // Select first monitor for trend
      if (monitorsResult.data.length > 0 && !selectedMonitorId) {
        setSelectedMonitorId(monitorsResult.data[0].id)
      }
    } catch (error) {
      toast({
        title: str(common.error),
        description: 'Failed to load data',
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }, [toast, common, selectedMonitorId])

  useEffect(() => {
    loadData()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Load trend when monitor changes
  useEffect(() => {
    if (!selectedMonitorId) return

    const loadTrend = async () => {
      setIsLoadingTrend(true)
      try {
        const data = await getDriftMonitorTrend(selectedMonitorId)
        setTrendData(data)
      } catch {
        setTrendData(null)
      } finally {
        setIsLoadingTrend(false)
      }
    }

    loadTrend()
  }, [selectedMonitorId])

  // Handlers
  const handleCreateMonitor = useCallback(
    async (data: object) => {
      try {
        await createDriftMonitor(data)
        toast({ title: str(t.messages.monitorCreated) })
        loadData()
      } catch (error) {
        toast({
          title: str(common.error),
          description: 'Failed to create monitor',
          variant: 'destructive',
        })
        throw error
      }
    },
    [toast, t, common, loadData]
  )

  const handleEditMonitor = useCallback((monitor: DriftMonitor) => {
    setEditingMonitor(monitor)
  }, [])

  const handleUpdateMonitor = useCallback(
    async (data: object) => {
      if (!editingMonitor) return
      try {
        await updateDriftMonitor(editingMonitor.id, data)
        toast({ title: str(t.messages.monitorUpdated) })
        setEditingMonitor(null)
        loadData()
      } catch (error) {
        toast({
          title: str(common.error),
          description: 'Failed to update monitor',
          variant: 'destructive',
        })
        throw error
      }
    },
    [editingMonitor, toast, t, common, loadData]
  )

  const handleDeleteMonitor = useCallback(
    async (monitor: DriftMonitor) => {
      if (!confirm(str(t.confirm.deleteMonitor))) return
      try {
        await deleteDriftMonitor(monitor.id)
        toast({ title: str(t.messages.monitorDeleted) })
        loadData()
      } catch (error) {
        toast({
          title: str(common.error),
          description: 'Failed to delete monitor',
          variant: 'destructive',
        })
      }
    },
    [toast, t, common, loadData]
  )

  const handleRunMonitor = useCallback(
    async (monitor: DriftMonitor) => {
      try {
        toast({ title: str(t.messages.monitorRunStarted) })
        const result = await runDriftMonitor(monitor.id)
        if (result.has_drift) {
          toast({
            title: str(t.messages.driftDetected),
            description: `${result.drift_percentage.toFixed(1)}% drift detected`,
            variant: 'destructive',
          })
        } else {
          toast({ title: str(t.messages.noDriftDetected) })
        }
        loadData()
      } catch (error) {
        toast({
          title: str(common.error),
          description: 'Failed to run monitor',
          variant: 'destructive',
        })
      }
    },
    [toast, t, common, loadData]
  )

  const handlePauseMonitor = useCallback(
    async (monitor: DriftMonitor) => {
      try {
        await updateDriftMonitor(monitor.id, { status: 'paused' })
        toast({ title: str(t.messages.monitorUpdated) })
        loadData()
      } catch (error) {
        toast({
          title: str(common.error),
          variant: 'destructive',
        })
      }
    },
    [toast, t, common, loadData]
  )

  const handleResumeMonitor = useCallback(
    async (monitor: DriftMonitor) => {
      try {
        await updateDriftMonitor(monitor.id, { status: 'active' })
        toast({ title: str(t.messages.monitorUpdated) })
        loadData()
      } catch (error) {
        toast({
          title: str(common.error),
          variant: 'destructive',
        })
      }
    },
    [toast, t, common, loadData]
  )

  const handleAcknowledgeAlert = useCallback(
    async (alert: DriftAlert) => {
      try {
        await updateDriftAlert(alert.id, { status: 'acknowledged' })
        toast({ title: str(t.messages.alertAcknowledged) })
        loadData()
      } catch (error) {
        toast({
          title: str(common.error),
          variant: 'destructive',
        })
      }
    },
    [toast, t, common, loadData]
  )

  const handleResolveAlert = useCallback(
    async (alert: DriftAlert) => {
      try {
        await updateDriftAlert(alert.id, { status: 'resolved' })
        toast({ title: str(t.messages.alertResolved) })
        loadData()
      } catch (error) {
        toast({
          title: str(common.error),
          variant: 'destructive',
        })
      }
    },
    [toast, t, common, loadData]
  )

  const handleIgnoreAlert = useCallback(
    async (alert: DriftAlert) => {
      try {
        await updateDriftAlert(alert.id, { status: 'ignored' })
        loadData()
      } catch (error) {
        toast({
          title: str(common.error),
          variant: 'destructive',
        })
      }
    },
    [toast, common, loadData]
  )

  // Handler for viewing column details from a monitor
  const handleViewColumnDetails = useCallback(
    async (monitor: DriftMonitor) => {
      setSelectedMonitorForDrilldown(monitor)
      setShowColumnDrilldown(true)
      setIsLoadingLatestRun(true)
      try {
        const result = await getDriftMonitorLatestRun(monitor.id)
        setLatestRunResult(result)
      } catch {
        setLatestRunResult(null)
      } finally {
        setIsLoadingLatestRun(false)
      }
    },
    []
  )

  // Handler for opening column drilldown from stats card
  const handleOpenColumnDrilldown = useCallback(() => {
    // Find a monitor with drift detected
    const monitorWithDrift = monitors.find(m => m.last_drift_detected)
    if (monitorWithDrift) {
      handleViewColumnDetails(monitorWithDrift)
    }
  }, [monitors, handleViewColumnDetails])

  // Handler for loading root cause analysis
  const handleLoadRootCause = useCallback(
    async (monitor: DriftMonitor, runId: string) => {
      setIsLoadingRootCause(true)
      setShowRootCause(true)
      try {
        const data = await getDriftRootCauseAnalysis(monitor.id, runId)
        setRootCauseData(data)
      } catch {
        setRootCauseData(null)
        toast({
          title: str(common.error),
          description: 'Failed to load root cause analysis',
          variant: 'destructive',
        })
      } finally {
        setIsLoadingRootCause(false)
      }
    },
    [toast, common]
  )

  // Handler for remediation actions
  const handleRemediationAction = useCallback(
    (suggestion: RemediationSuggestion, action: 'automate' | 'investigate' | 'dismiss') => {
      // In a real app, this would trigger the appropriate action
      toast({
        title: action === 'automate' ? 'Automation Started' : action === 'investigate' ? 'Investigation Started' : 'Suggestion Dismissed',
        description: suggestion.title,
      })
    },
    [toast]
  )

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t.title}</h1>
          <p className="text-muted-foreground">{t.subtitle}</p>
        </div>
        <div className="flex gap-2">
          <AutoTriggerConfigPanel />
          <Button variant="outline" onClick={loadData} disabled={isLoading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            {common.refresh}
          </Button>
          <Button variant="outline" onClick={() => setShowPreview(true)}>
            <Eye className="mr-2 h-4 w-4" />
            {t.preview?.previewDrift ?? 'Preview Drift'}
          </Button>
          <Button onClick={() => setShowCreateForm(true)}>
            <Plus className="mr-2 h-4 w-4" />
            {t.monitor.createMonitor}
          </Button>
        </div>
      </div>

      {/* Stats */}
      <DriftMonitorStats
        totalMonitors={summary.total_monitors}
        activeMonitors={summary.active_monitors}
        monitorsWithDrift={summary.monitors_with_drift}
        openAlerts={summary.total_open_alerts}
        criticalAlerts={summary.critical_alerts}
        showColumnDetailsButton
        onViewColumnDetails={handleOpenColumnDrilldown}
      />

      {/* Main Tabs */}
      <Card>
        <CardHeader>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
              <TabsTrigger value="monitors" className="gap-2">
                <Activity className="h-4 w-4" />
                {t.tabs.monitors}
              </TabsTrigger>
              <TabsTrigger value="alerts" className="gap-2">
                <Bell className="h-4 w-4" />
                {t.tabs.alerts}
                {summary.total_open_alerts > 0 && (
                  <span className="ml-1 rounded-full bg-red-500 px-2 py-0.5 text-xs text-white">
                    {summary.total_open_alerts}
                  </span>
                )}
              </TabsTrigger>
              <TabsTrigger value="trends" className="gap-2">
                <TrendingUp className="h-4 w-4" />
                {t.tabs.trends}
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsContent value="monitors" className="mt-0">
              <DriftMonitorList
                monitors={monitors}
                isLoading={isLoading}
                onEdit={handleEditMonitor}
                onDelete={handleDeleteMonitor}
                onRun={handleRunMonitor}
                onPause={handlePauseMonitor}
                onResume={handleResumeMonitor}
                onViewDetails={handleViewColumnDetails}
              />
            </TabsContent>

            <TabsContent value="alerts" className="mt-0 space-y-4">
              <DriftAlertList
                alerts={alerts}
                isLoading={isLoading}
                onAcknowledge={handleAcknowledgeAlert}
                onResolve={handleResolveAlert}
                onIgnore={handleIgnoreAlert}
              />

              {/* Related Anomaly Alerts for selected monitor */}
              {selectedMonitorId && (
                <RelatedAlerts
                  sourceId={monitors.find(m => m.id === selectedMonitorId)?.current_source_id || ''}
                  alertType="drift"
                  maxItems={5}
                />
              )}
            </TabsContent>

            <TabsContent value="trends" className="mt-0 space-y-4">
              {monitors.length > 0 && (
                <div className="flex items-center gap-4">
                  <span className="text-sm font-medium">Select Monitor:</span>
                  <Select value={selectedMonitorId} onValueChange={setSelectedMonitorId}>
                    <SelectTrigger className="w-64">
                      <SelectValue placeholder="Select a monitor" />
                    </SelectTrigger>
                    <SelectContent>
                      {monitors.map((monitor) => (
                        <SelectItem key={monitor.id} value={monitor.id}>
                          {monitor.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
              <DriftTrendChart data={trendData as any} isLoading={isLoadingTrend} />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Create Form Dialog */}
      <DriftMonitorForm
        open={showCreateForm}
        onOpenChange={setShowCreateForm}
        onSubmit={handleCreateMonitor}
        sources={sources}
      />

      {/* Edit Form Dialog */}
      {editingMonitor && (
        <DriftMonitorForm
          open={!!editingMonitor}
          onOpenChange={(open) => !open && setEditingMonitor(null)}
          onSubmit={handleUpdateMonitor}
          sources={sources}
          initialData={editingMonitor}
          isEditing
        />
      )}

      {/* Preview Dialog */}
      <DriftPreview
        open={showPreview}
        onOpenChange={setShowPreview}
        sources={sources}
        onCreateMonitor={() => {
          setShowPreview(false)
          // Pre-fill form with preview data
          setShowCreateForm(true)
        }}
      />

      {/* Column Drilldown Sheet */}
      <Sheet open={showColumnDrilldown} onOpenChange={setShowColumnDrilldown}>
        <SheetContent side="right" className="w-full sm:max-w-4xl overflow-y-auto">
          <SheetHeader>
            <SheetTitle className="flex items-center gap-2">
              <Columns className="h-5 w-5" />
              {selectedMonitorForDrilldown?.name ?? t.columnDrilldown?.title ?? 'Column Details'}
            </SheetTitle>
          </SheetHeader>
          <div className="mt-6">
            {isLoadingLatestRun ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : latestRunResult ? (
              <div className="space-y-6">
                {/* Action buttons */}
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={() => {
                      if (selectedMonitorForDrilldown && latestRunResult.comparison_id) {
                        handleLoadRootCause(selectedMonitorForDrilldown, latestRunResult.comparison_id)
                      }
                    }}
                    disabled={!latestRunResult.comparison_id}
                  >
                    <Search className="mr-2 h-4 w-4" />
                    {t.rootCause?.analyzeRootCause ?? 'Analyze Root Cause'}
                  </Button>
                </div>

                <ColumnDrilldown
                  result={latestRunResult}
                  threshold={selectedMonitorForDrilldown?.threshold ?? 5}
                  onClose={() => setShowColumnDrilldown(false)}
                />
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                <Columns className="h-12 w-12 mb-4 opacity-50" />
                <p>{t.empty?.noRunData ?? 'No run data available'}</p>
                <p className="text-sm">{t.empty?.runMonitorFirst ?? 'Run the monitor to see column details'}</p>
              </div>
            )}
          </div>
        </SheetContent>
      </Sheet>

      {/* Root Cause Analysis Sheet */}
      <Sheet open={showRootCause} onOpenChange={setShowRootCause}>
        <SheetContent side="right" className="w-full sm:max-w-5xl p-0">
          <SheetHeader className="px-6 pt-6">
            <SheetTitle className="flex items-center gap-2">
              <Search className="h-5 w-5" />
              {t.rootCause?.title ?? 'Root Cause Analysis'}
            </SheetTitle>
          </SheetHeader>
          <ScrollArea className="h-[calc(100vh-5rem)]">
            <div className="p-6 space-y-6">
              {isLoadingRootCause ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : rootCauseData ? (
                <>
                  <RootCauseAnalysis data={rootCauseData} />
                  {rootCauseData.remediations && rootCauseData.remediations.length > 0 && (
                    <RemediationPanel
                      remediations={rootCauseData.remediations}
                      onActionClick={(action, remediation) => handleRemediationAction(remediation, action as 'automate' | 'investigate' | 'dismiss')}
                    />
                  )}
                </>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                  <Search className="h-12 w-12 mb-4 opacity-50" />
                  <p>{t.rootCause?.noData ?? 'No root cause data available'}</p>
                </div>
              )}
            </div>
          </ScrollArea>
        </SheetContent>
      </Sheet>
    </div>
  )
}
