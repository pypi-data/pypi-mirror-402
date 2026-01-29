/**
 * Model Monitoring Page.
 *
 * Provides ML model monitoring dashboard with:
 * - Model registration and management
 * - Performance and data quality metrics
 * - Drift detection
 * - Alert rules and handlers
 */

import { useState, useCallback, useEffect } from 'react'
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
import { useToast } from '@/hooks/use-toast'
import {
  Loader2,
  RefreshCw,
  Plus,
  Cpu,
  BarChart3,
  AlertTriangle,
  Bell,
  Webhook,
} from 'lucide-react'
import {
  MonitoringOverviewStats,
  ModelList,
  MetricsChart,
  AlertList,
  AlertRuleList,
  AlertHandlerList,
  ModelDashboard,
  RegisterModelDialog,
  type RegisteredModel,
  type AlertInstance,
  type AlertRule,
  type AlertHandler,
} from '@/components/model-monitoring'

// API functions
const API_BASE = '/api/v1'

interface MonitoringOverview {
  total_models: number
  active_models: number
  degraded_models: number
  total_predictions_24h: number
  active_alerts: number
  models_with_drift: number
  avg_latency_ms: number | null
}

interface MetricsResponse {
  model_id: string
  model_name: string
  time_range_hours: number
  metrics: Array<{
    name: string
    type: string
    count: number
    min_value: number | null
    max_value: number | null
    avg_value: number | null
    p50_value: number | null
    p95_value: number | null
    p99_value: number | null
    last_value: number | null
  }>
  data_points: Record<string, Array<{ timestamp: string; value: number }>>
}

async function getMonitoringOverview(): Promise<MonitoringOverview> {
  const response = await fetch(`${API_BASE}/model-monitoring/overview`)
  if (!response.ok) throw new Error('Failed to fetch overview')
  const result = await response.json()
  return result.data
}

async function listModels(): Promise<{ items: RegisteredModel[]; total: number }> {
  const response = await fetch(`${API_BASE}/model-monitoring/models`)
  if (!response.ok) throw new Error('Failed to fetch models')
  const result = await response.json()
  return result.data
}

async function createModel(data: Partial<RegisteredModel>): Promise<RegisteredModel> {
  const response = await fetch(`${API_BASE}/model-monitoring/models`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) throw new Error('Failed to create model')
  const result = await response.json()
  return result.data
}

async function getModelMetrics(modelId: string, hours: number = 24): Promise<MetricsResponse> {
  const response = await fetch(
    `${API_BASE}/model-monitoring/models/${modelId}/metrics?hours=${hours}`
  )
  if (!response.ok) throw new Error('Failed to fetch metrics')
  const result = await response.json()
  return result.data
}

async function deleteModel(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/model-monitoring/models/${id}`, { method: 'DELETE' })
  if (!response.ok) throw new Error('Failed to delete model')
}

async function listAlerts(params?: {
  active_only?: boolean
}): Promise<{ items: AlertInstance[]; total: number }> {
  const searchParams = new URLSearchParams()
  if (params?.active_only) searchParams.append('active_only', 'true')
  const response = await fetch(`${API_BASE}/model-monitoring/alerts?${searchParams}`)
  if (!response.ok) throw new Error('Failed to fetch alerts')
  const result = await response.json()
  return result.data
}

async function acknowledgeAlert(id: string, actor: string): Promise<void> {
  const response = await fetch(`${API_BASE}/model-monitoring/alerts/${id}/acknowledge`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ actor }),
  })
  if (!response.ok) throw new Error('Failed to acknowledge alert')
}

async function resolveAlert(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/model-monitoring/alerts/${id}/resolve`, {
    method: 'POST',
  })
  if (!response.ok) throw new Error('Failed to resolve alert')
}

async function listAlertRules(): Promise<{ items: AlertRule[]; total: number }> {
  const response = await fetch(`${API_BASE}/model-monitoring/rules`)
  if (!response.ok) throw new Error('Failed to fetch rules')
  const result = await response.json()
  return result.data
}

async function deleteAlertRule(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/model-monitoring/rules/${id}`, { method: 'DELETE' })
  if (!response.ok) throw new Error('Failed to delete rule')
}

async function updateAlertRule(id: string, data: { is_active: boolean }): Promise<void> {
  const response = await fetch(`${API_BASE}/model-monitoring/rules/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) throw new Error('Failed to update rule')
}

async function listAlertHandlers(): Promise<{ items: AlertHandler[]; total: number }> {
  const response = await fetch(`${API_BASE}/model-monitoring/handlers`)
  if (!response.ok) throw new Error('Failed to fetch handlers')
  const result = await response.json()
  return result.data
}

async function deleteAlertHandler(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/model-monitoring/handlers/${id}`, { method: 'DELETE' })
  if (!response.ok) throw new Error('Failed to delete handler')
}

async function updateAlertHandler(id: string, data: { is_active: boolean }): Promise<void> {
  const response = await fetch(`${API_BASE}/model-monitoring/handlers/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) throw new Error('Failed to update handler')
}

async function testAlertHandler(id: string): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE}/model-monitoring/handlers/${id}/test`, {
    method: 'POST',
  })
  if (!response.ok) throw new Error('Failed to test handler')
  const result = await response.json()
  return result.data
}

export default function ModelMonitoring() {
  const t = useIntlayer('modelMonitoring')
  const common = useIntlayer('common')
  const { toast } = useToast()

  // State
  const [activeTab, setActiveTab] = useState('overview')
  const [isLoading, setIsLoading] = useState(true)
  const [overview, setOverview] = useState<MonitoringOverview>({
    total_models: 0,
    active_models: 0,
    degraded_models: 0,
    total_predictions_24h: 0,
    active_alerts: 0,
    models_with_drift: 0,
    avg_latency_ms: null,
  })
  const [models, setModels] = useState<RegisteredModel[]>([])
  const [alerts, setAlerts] = useState<AlertInstance[]>([])
  const [rules, setRules] = useState<AlertRule[]>([])
  const [handlers, setHandlers] = useState<AlertHandler[]>([])

  // Metrics state
  const [selectedModelId, setSelectedModelId] = useState<string>('')
  const [metricsData, setMetricsData] = useState<MetricsResponse | null>(null)
  const [isLoadingMetrics, setIsLoadingMetrics] = useState(false)
  const [timeRange, setTimeRange] = useState('24')

  // Detail view state
  const [selectedModel, setSelectedModel] = useState<RegisteredModel | null>(null)

  // Dialog state
  const [showRegisterDialog, setShowRegisterDialog] = useState(false)

  // Load data
  const loadData = useCallback(async () => {
    setIsLoading(true)
    try {
      const [overviewRes, modelsRes, alertsRes, rulesRes, handlersRes] = await Promise.all([
        getMonitoringOverview(),
        listModels(),
        listAlerts({ active_only: true }),
        listAlertRules(),
        listAlertHandlers(),
      ])

      setOverview(overviewRes)
      setModels(modelsRes.items)
      setAlerts(alertsRes.items)
      setRules(rulesRes.items)
      setHandlers(handlersRes.items)

      // Auto-select first model
      if (modelsRes.items.length > 0 && !selectedModelId) {
        setSelectedModelId(modelsRes.items[0].id)
      }
    } catch {
      toast({
        title: str(common.error),
        description: str(t.errors.loadFailed),
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }, [toast, common, t, selectedModelId])

  useEffect(() => {
    loadData()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Load metrics when model changes
  useEffect(() => {
    if (!selectedModelId) {
      setMetricsData(null)
      return
    }

    const loadMetrics = async () => {
      setIsLoadingMetrics(true)
      try {
        const data = await getModelMetrics(selectedModelId, parseInt(timeRange))
        setMetricsData(data)
      } catch {
        setMetricsData(null)
      } finally {
        setIsLoadingMetrics(false)
      }
    }

    loadMetrics()
  }, [selectedModelId, timeRange])

  // Handlers
  const handleRegisterModel = useCallback(
    async (data: {
      name: string
      version: string
      description: string
      config: {
        enable_drift_detection: boolean
        enable_quality_metrics: boolean
        enable_performance_metrics: boolean
        sample_rate: number
        drift_threshold: number
        drift_window_size: number
      }
      metadata: Record<string, string>
    }) => {
      try {
        await createModel(data)
        toast({ title: str(t.messages.modelRegistered) })
        loadData()
      } catch {
        toast({
          title: str(common.error),
          description: str(t.errors.createFailed),
          variant: 'destructive',
        })
        throw new Error('Failed to register model')
      }
    },
    [toast, t, common, loadData]
  )

  const handleDeleteModel = useCallback(
    async (model: RegisteredModel) => {
      if (!confirm(str(t.confirm.deleteModel))) return
      try {
        await deleteModel(model.id)
        toast({ title: str(t.messages.modelDeleted) })
        loadData()
      } catch {
        toast({
          title: str(common.error),
          description: str(t.errors.deleteFailed),
          variant: 'destructive',
        })
      }
    },
    [toast, t, common, loadData]
  )

  const handleViewMetrics = useCallback((model: RegisteredModel) => {
    setSelectedModelId(model.id)
    setActiveTab('metrics')
  }, [])

  const handleViewDashboard = useCallback((model: RegisteredModel) => {
    setSelectedModel(model)
  }, [])

  const handleAcknowledgeAlert = useCallback(
    async (alert: AlertInstance) => {
      try {
        await acknowledgeAlert(alert.id, 'user')
        toast({ title: str(t.messages.alertAcknowledged) })
        loadData()
      } catch {
        toast({
          title: str(common.error),
          variant: 'destructive',
        })
      }
    },
    [toast, t, common, loadData]
  )

  const handleResolveAlert = useCallback(
    async (alert: AlertInstance) => {
      try {
        await resolveAlert(alert.id)
        toast({ title: str(t.messages.alertResolved) })
        loadData()
      } catch {
        toast({
          title: str(common.error),
          variant: 'destructive',
        })
      }
    },
    [toast, t, common, loadData]
  )

  const handleToggleRule = useCallback(
    async (rule: AlertRule) => {
      try {
        await updateAlertRule(rule.id, { is_active: !rule.is_active })
        toast({ title: str(t.messages.ruleUpdated) })
        loadData()
      } catch {
        toast({
          title: str(common.error),
          variant: 'destructive',
        })
      }
    },
    [toast, t, common, loadData]
  )

  const handleDeleteRule = useCallback(
    async (rule: AlertRule) => {
      if (!confirm(str(t.confirm.deleteRule))) return
      try {
        await deleteAlertRule(rule.id)
        toast({ title: str(t.messages.ruleDeleted) })
        loadData()
      } catch {
        toast({
          title: str(common.error),
          description: str(t.errors.deleteFailed),
          variant: 'destructive',
        })
      }
    },
    [toast, t, common, loadData]
  )

  const handleToggleHandler = useCallback(
    async (handler: AlertHandler) => {
      try {
        await updateAlertHandler(handler.id, { is_active: !handler.is_active })
        toast({ title: str(t.messages.handlerUpdated) })
        loadData()
      } catch {
        toast({
          title: str(common.error),
          variant: 'destructive',
        })
      }
    },
    [toast, t, common, loadData]
  )

  const handleDeleteHandler = useCallback(
    async (handler: AlertHandler) => {
      if (!confirm(str(t.confirm.deleteHandler))) return
      try {
        await deleteAlertHandler(handler.id)
        toast({ title: str(t.messages.handlerDeleted) })
        loadData()
      } catch {
        toast({
          title: str(common.error),
          description: str(t.errors.deleteFailed),
          variant: 'destructive',
        })
      }
    },
    [toast, t, common, loadData]
  )

  const handleTestHandler = useCallback(
    async (handler: AlertHandler) => {
      try {
        const result = await testAlertHandler(handler.id)
        if (result.success) {
          toast({ title: 'Test message sent successfully' })
        } else {
          toast({
            title: 'Test failed',
            description: result.message,
            variant: 'destructive',
          })
        }
        loadData()
      } catch {
        toast({
          title: str(common.error),
          variant: 'destructive',
        })
      }
    },
    [toast, common, loadData]
  )

  // If viewing a specific model dashboard
  if (selectedModel) {
    return (
      <div className="p-6">
        <ModelDashboard model={selectedModel} onBack={() => setSelectedModel(null)} />
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Cpu className="h-6 w-6 text-primary" />
            {t.title}
          </h1>
          <p className="text-muted-foreground">{t.subtitle}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={loadData} disabled={isLoading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            {common.refresh}
          </Button>
          <Button onClick={() => setShowRegisterDialog(true)}>
            <Plus className="mr-2 h-4 w-4" />
            {t.models.registerModel}
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      <MonitoringOverviewStats
        totalModels={overview.total_models}
        activeModels={overview.active_models}
        degradedModels={overview.degraded_models}
        predictions24h={overview.total_predictions_24h}
        activeAlerts={overview.active_alerts}
        modelsWithDrift={overview.models_with_drift}
        avgLatencyMs={overview.avg_latency_ms}
      />

      {/* Main Tabs */}
      <Card>
        <CardHeader>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
              <TabsTrigger value="overview" className="gap-2">
                <Cpu className="h-4 w-4" />
                {t.tabs.models}
              </TabsTrigger>
              <TabsTrigger value="metrics" className="gap-2">
                <BarChart3 className="h-4 w-4" />
                {t.tabs.metrics}
              </TabsTrigger>
              <TabsTrigger value="alerts" className="gap-2">
                <AlertTriangle className="h-4 w-4" />
                {t.tabs.alerts}
                {overview.active_alerts > 0 && (
                  <span className="ml-1 rounded-full bg-red-500 px-2 py-0.5 text-xs text-white">
                    {overview.active_alerts}
                  </span>
                )}
              </TabsTrigger>
              <TabsTrigger value="rules" className="gap-2">
                <Bell className="h-4 w-4" />
                {t.tabs.rules}
              </TabsTrigger>
              <TabsTrigger value="handlers" className="gap-2">
                <Webhook className="h-4 w-4" />
                {t.tabs.handlers}
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            {/* Models Tab */}
            <TabsContent value="overview" className="mt-0">
              <ModelList
                models={models}
                isLoading={isLoading}
                onEdit={handleViewDashboard}
                onDelete={handleDeleteModel}
                onViewMetrics={handleViewMetrics}
              />
            </TabsContent>

            {/* Metrics Tab */}
            <TabsContent value="metrics" className="mt-0 space-y-4">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{t.metrics.selectModel}:</span>
                  <Select value={selectedModelId} onValueChange={setSelectedModelId}>
                    <SelectTrigger className="w-64">
                      <SelectValue placeholder="Select a model" />
                    </SelectTrigger>
                    <SelectContent>
                      {models.map((model) => (
                        <SelectItem key={model.id} value={model.id}>
                          {model.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{t.metrics.timeRange}:</span>
                  <Select value={timeRange} onValueChange={setTimeRange}>
                    <SelectTrigger className="w-40">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">{t.timeRanges['1h']}</SelectItem>
                      <SelectItem value="6">{t.timeRanges['6h']}</SelectItem>
                      <SelectItem value="24">{t.timeRanges['24h']}</SelectItem>
                      <SelectItem value="168">{t.timeRanges['7d']}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              {metricsData ? (
                <MetricsChart
                  modelName={metricsData.model_name}
                  metrics={metricsData.metrics}
                  dataPoints={metricsData.data_points}
                  isLoading={isLoadingMetrics}
                />
              ) : (
                <div className="text-center py-12 text-muted-foreground">
                  {isLoadingMetrics ? (
                    <Loader2 className="h-8 w-8 animate-spin mx-auto" />
                  ) : (
                    t.empty.noData
                  )}
                </div>
              )}
            </TabsContent>

            {/* Alerts Tab */}
            <TabsContent value="alerts" className="mt-0">
              <AlertList
                alerts={alerts}
                isLoading={isLoading}
                onAcknowledge={handleAcknowledgeAlert}
                onResolve={handleResolveAlert}
              />
            </TabsContent>

            {/* Rules Tab */}
            <TabsContent value="rules" className="mt-0">
              <div className="flex justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold">{t.rules.title}</h3>
                </div>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  {t.rules.addRule}
                </Button>
              </div>
              <AlertRuleList
                rules={rules}
                isLoading={isLoading}
                onEdit={() => {}}
                onDelete={handleDeleteRule}
                onToggle={handleToggleRule}
              />
            </TabsContent>

            {/* Handlers Tab */}
            <TabsContent value="handlers" className="mt-0">
              <div className="flex justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold">{t.handlers.title}</h3>
                </div>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  {t.handlers.addHandler}
                </Button>
              </div>
              <AlertHandlerList
                handlers={handlers}
                isLoading={isLoading}
                onEdit={() => {}}
                onDelete={handleDeleteHandler}
                onToggle={handleToggleHandler}
                onTest={handleTestHandler}
              />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Register Model Dialog */}
      <RegisterModelDialog
        open={showRegisterDialog}
        onOpenChange={setShowRegisterDialog}
        onSubmit={handleRegisterModel}
      />
    </div>
  )
}
