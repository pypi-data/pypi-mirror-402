/**
 * Trigger Monitoring Page
 *
 * Displays real-time status of data change, composite, and webhook triggers.
 * Provides visibility into trigger evaluations, cooldowns, and execution history.
 */

import { useEffect, useState, useCallback } from 'react'
import { useSafeIntlayer } from '@/hooks/useSafeIntlayer'
import {
  Activity,
  Clock,
  Webhook,
  Layers,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Timer,
  Zap,
  Copy,
  ExternalLink,
} from 'lucide-react'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useToast } from '@/hooks/use-toast'
import { str } from '@/lib/intlayer-utils'
import {
  getTriggerMonitoring,
  type TriggerMonitoringResponse,
  type TriggerCheckStatus,
} from '@/api/client'

// Trigger type badge colors
const TRIGGER_TYPE_COLORS: Record<string, string> = {
  cron: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
  interval: 'bg-green-500/10 text-green-500 border-green-500/20',
  data_change: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
  composite: 'bg-purple-500/10 text-purple-500 border-purple-500/20',
  webhook: 'bg-pink-500/10 text-pink-500 border-pink-500/20',
  event: 'bg-cyan-500/10 text-cyan-500 border-cyan-500/20',
  manual: 'bg-gray-500/10 text-gray-500 border-gray-500/20',
}

// Format cooldown remaining
function formatCooldown(seconds: number): string {
  if (seconds <= 0) return '-'
  const min = Math.floor(seconds / 60)
  const sec = seconds % 60
  if (min > 0) return `${min}m ${sec}s`
  return `${sec}s`
}

// Stats Card Component
function StatsCard({
  title,
  value,
  icon: Icon,
  variant = 'default',
}: {
  title: string
  value: number | string
  icon: React.ComponentType<{ className?: string }>
  variant?: 'default' | 'success' | 'warning' | 'danger'
}) {
  const variantStyles = {
    default: 'text-primary',
    success: 'text-green-500',
    warning: 'text-amber-500',
    danger: 'text-red-500',
  }

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className={`text-2xl font-bold ${variantStyles[variant]}`}>{value}</p>
          </div>
          <Icon className={`h-8 w-8 ${variantStyles[variant]} opacity-50`} />
        </div>
      </CardContent>
    </Card>
  )
}

// Trigger Status Row Component
function TriggerStatusRow({ schedule }: { schedule: TriggerCheckStatus }) {
  const t = useSafeIntlayer('triggers')
  const isInCooldown = schedule.cooldown_remaining_seconds > 0
  const statusBadge = schedule.is_due_for_check ? (
    <Badge variant="outline" className="bg-amber-500/10 text-amber-500">
      {str(t.dueForCheck)}
    </Badge>
  ) : isInCooldown ? (
    <Badge variant="outline" className="bg-blue-500/10 text-blue-500">
      {str(t.inCooldown)}
    </Badge>
  ) : (
    <Badge variant="outline" className="bg-green-500/10 text-green-500">
      {str(t.ready)}
    </Badge>
  )

  return (
    <TableRow>
      <TableCell className="font-medium">{schedule.schedule_name}</TableCell>
      <TableCell>
        <Badge
          variant="outline"
          className={TRIGGER_TYPE_COLORS[schedule.trigger_type] || TRIGGER_TYPE_COLORS.manual}
        >
          {schedule.trigger_type}
        </Badge>
      </TableCell>
      <TableCell>{statusBadge}</TableCell>
      <TableCell className="text-muted-foreground text-sm">
        {schedule.last_check_at
          ? (() => {
              const date = new Date(schedule.last_check_at)
              const now = new Date()
              const diffMs = now.getTime() - date.getTime()
              const diffSec = Math.floor(diffMs / 1000)
              const diffMin = Math.floor(diffSec / 60)
              const diffHr = Math.floor(diffMin / 60)
              if (diffSec < 60) return `${diffSec}s ${str(t.ago)}`
              if (diffMin < 60) return `${diffMin}m ${str(t.ago)}`
              if (diffHr < 24) return `${diffHr}h ${str(t.ago)}`
              return date.toLocaleString()
            })()
          : str(t.never)}
      </TableCell>
      <TableCell className="text-muted-foreground text-sm">
        {schedule.last_triggered_at
          ? (() => {
              const date = new Date(schedule.last_triggered_at)
              const now = new Date()
              const diffMs = now.getTime() - date.getTime()
              const diffSec = Math.floor(diffMs / 1000)
              const diffMin = Math.floor(diffSec / 60)
              const diffHr = Math.floor(diffMin / 60)
              if (diffSec < 60) return `${diffSec}s ${str(t.ago)}`
              if (diffMin < 60) return `${diffMin}m ${str(t.ago)}`
              if (diffHr < 24) return `${diffHr}h ${str(t.ago)}`
              return date.toLocaleString()
            })()
          : str(t.never)}
      </TableCell>
      <TableCell className="text-center">{schedule.check_count}</TableCell>
      <TableCell className="text-center">{schedule.trigger_count}</TableCell>
      <TableCell className="text-center">
        <Badge variant="outline">{schedule.priority}</Badge>
      </TableCell>
      <TableCell className="text-muted-foreground">
        {isInCooldown ? (
          <span className="text-amber-500">{formatCooldown(schedule.cooldown_remaining_seconds)}</span>
        ) : (
          '-'
        )}
      </TableCell>
      <TableCell>
        {schedule.last_evaluation?.should_trigger ? (
          <CheckCircle2 className="h-4 w-4 text-green-500" />
        ) : (
          <AlertCircle className="h-4 w-4 text-muted-foreground" />
        )}
      </TableCell>
    </TableRow>
  )
}

export default function TriggerMonitoring() {
  const t = useSafeIntlayer('triggers')
  const common = useSafeIntlayer('common')
  const { toast } = useToast()

  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<TriggerMonitoringResponse | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  // Format relative time
  const formatRelativeTime = useCallback((dateString: string | null): string => {
    if (!dateString) return str(t.never)

    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffSec = Math.floor(diffMs / 1000)
    const diffMin = Math.floor(diffSec / 60)
    const diffHr = Math.floor(diffMin / 60)

    if (diffSec < 60) return `${diffSec}s ${str(t.ago)}`
    if (diffMin < 60) return `${diffMin}m ${str(t.ago)}`
    if (diffHr < 24) return `${diffHr}h ${str(t.ago)}`
    return date.toLocaleString()
  }, [common])

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const response = await getTriggerMonitoring()
      setData(response)
    } catch (error) {
      toast({
        title: str(t.refreshFailed),
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }, [toast, t.refreshFailed])

  useEffect(() => {
    fetchData()
  }, [fetchData, refreshKey])

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setRefreshKey((k) => k + 1)
    }, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleRefresh = () => {
    setRefreshKey((k) => k + 1)
    toast({ title: str(t.refreshed) })
  }

  const stats = data?.stats
  const schedules = data?.schedules || []

  // Filter schedules by type
  const dataChangeSchedules = schedules.filter((s) => s.trigger_type === 'data_change')
  const webhookSchedules = schedules.filter((s) => s.trigger_type === 'webhook')
  const compositeSchedules = schedules.filter((s) => s.trigger_type === 'composite')

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{str(t.title)}</h1>
          <p className="text-muted-foreground">{str(t.subtitle)}</p>
        </div>
        <Button onClick={handleRefresh} disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          {str(t.refresh)}
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <StatsCard
          title={str(t.totalSchedules)}
          value={stats?.total_schedules || 0}
          icon={Activity}
        />
        <StatsCard
          title={str(t.dataChangeTriggers)}
          value={stats?.active_data_change_triggers || 0}
          icon={Zap}
          variant="warning"
        />
        <StatsCard
          title={str(t.webhookTriggers)}
          value={stats?.active_webhook_triggers || 0}
          icon={Webhook}
          variant="success"
        />
        <StatsCard
          title={str(t.compositeTriggers)}
          value={stats?.active_composite_triggers || 0}
          icon={Layers}
        />
        <StatsCard
          title={str(t.checksLastHour)}
          value={stats?.total_checks_last_hour || 0}
          icon={Clock}
        />
        <StatsCard
          title={str(t.triggersLastHour)}
          value={stats?.total_triggers_last_hour || 0}
          icon={CheckCircle2}
          variant="success"
        />
      </div>

      {/* Checker Status */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <Timer className="h-5 w-5" />
            {str(t.checkerStatus)}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">{str(t.status)}</p>
              <Badge
                variant="outline"
                className={
                  data?.checker_running
                    ? 'bg-green-500/10 text-green-500'
                    : 'bg-red-500/10 text-red-500'
                }
              >
                {data?.checker_running ? str(t.checkerRunning) : str(t.checkerStopped)}
              </Badge>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">{str(t.checkerInterval)}</p>
              <p className="font-medium">{data?.checker_interval_seconds || 0}s</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">{str(t.lastCheckerRun)}</p>
              <p className="font-medium">
                {data?.last_checker_run_at ? formatRelativeTime(data.last_checker_run_at) : str(t.never)}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">{str(t.nextScheduledCheck)}</p>
              <p className="font-medium">
                {stats?.next_scheduled_check_at
                  ? new Date(stats.next_scheduled_check_at).toLocaleString()
                  : str(t.never)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Trigger Tables by Type */}
      <Tabs defaultValue="all" className="space-y-4">
        <TabsList>
          <TabsTrigger value="all">{str(t.overview)}</TabsTrigger>
          <TabsTrigger value="data_change">
            {str(t.dataChange)} ({dataChangeSchedules.length})
          </TabsTrigger>
          <TabsTrigger value="webhook">
            {str(t.webhook)} ({webhookSchedules.length})
          </TabsTrigger>
          <TabsTrigger value="composite">
            {str(t.compositeType)} ({compositeSchedules.length})
          </TabsTrigger>
        </TabsList>

        {/* All Triggers Tab */}
        <TabsContent value="all">
          <Card>
            <CardHeader>
              <CardTitle>{str(t.schedules)}</CardTitle>
              <CardDescription>
                {schedules.length > 0
                  ? `${schedules.length} active trigger schedules`
                  : str(t.noTriggersDesc)}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {schedules.length === 0 ? (
                <div className="text-center py-8">
                  <Activity className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">{str(t.noTriggers)}</p>
                  <p className="text-sm text-muted-foreground">{str(t.noTriggersDesc)}</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{str(t.scheduleName)}</TableHead>
                      <TableHead>{str(t.triggerType)}</TableHead>
                      <TableHead>{str(t.status)}</TableHead>
                      <TableHead>{str(t.lastCheck)}</TableHead>
                      <TableHead>{str(t.lastTriggered)}</TableHead>
                      <TableHead className="text-center">{str(t.checkCount)}</TableHead>
                      <TableHead className="text-center">{str(t.triggerCount)}</TableHead>
                      <TableHead className="text-center">{str(t.priority)}</TableHead>
                      <TableHead>{str(t.cooldownRemaining)}</TableHead>
                      <TableHead>{str(t.shouldTrigger)}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {schedules.map((schedule) => (
                      <TriggerStatusRow key={schedule.schedule_id} schedule={schedule} />
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Data Change Tab */}
        <TabsContent value="data_change">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-amber-500" />
                {str(t.dataChangeTriggers)}
              </CardTitle>
              <CardDescription>
                Triggers that fire when data changes exceed configured thresholds
              </CardDescription>
            </CardHeader>
            <CardContent>
              {dataChangeSchedules.length === 0 ? (
                <div className="text-center py-8">
                  <Zap className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">{str(t.noTriggers)}</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{str(t.scheduleName)}</TableHead>
                      <TableHead>{str(t.status)}</TableHead>
                      <TableHead>{str(t.lastCheck)}</TableHead>
                      <TableHead>{str(t.lastTriggered)}</TableHead>
                      <TableHead className="text-center">{str(t.triggerCount)}</TableHead>
                      <TableHead>{str(t.cooldownRemaining)}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {dataChangeSchedules.map((schedule) => (
                      <TableRow key={schedule.schedule_id}>
                        <TableCell className="font-medium">{schedule.schedule_name}</TableCell>
                        <TableCell>
                          {schedule.is_due_for_check ? (
                            <Badge
                              variant="outline"
                              className="bg-amber-500/10 text-amber-500"
                            >
                              {str(t.dueForCheck)}
                            </Badge>
                          ) : schedule.cooldown_remaining_seconds > 0 ? (
                            <Badge variant="outline" className="bg-blue-500/10 text-blue-500">
                              {str(t.inCooldown)}
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="bg-green-500/10 text-green-500">
                              {str(t.ready)}
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell>{formatRelativeTime(schedule.last_check_at)}</TableCell>
                        <TableCell>{formatRelativeTime(schedule.last_triggered_at)}</TableCell>
                        <TableCell className="text-center">{schedule.trigger_count}</TableCell>
                        <TableCell>
                          {schedule.cooldown_remaining_seconds > 0 ? (
                            <span className="text-amber-500">{formatCooldown(schedule.cooldown_remaining_seconds)}</span>
                          ) : (
                            '-'
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Webhook Tab */}
        <TabsContent value="webhook">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Webhook className="h-5 w-5 text-pink-500" />
                {str(t.webhookTriggers)}
              </CardTitle>
              <CardDescription>
                External triggers from data pipelines (Airflow, Dagster, Prefect, etc.)
              </CardDescription>
            </CardHeader>
            <CardContent>
              {webhookSchedules.length === 0 ? (
                <div className="text-center py-8">
                  <Webhook className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">{str(t.noWebhooks)}</p>
                  <p className="text-sm text-muted-foreground">{str(t.noWebhooksDesc)}</p>
                </div>
              ) : (
                <>
                  {/* Webhook endpoint info */}
                  <div className="mb-4 p-4 rounded-lg bg-muted/50">
                    <p className="text-sm font-medium mb-2">{str(t.webhookEndpoint)}</p>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 px-3 py-2 rounded bg-background font-mono text-sm">
                        POST /api/v1/triggers/webhook
                      </code>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          navigator.clipboard.writeText(
                            `${window.location.origin}/api/v1/triggers/webhook`
                          )
                          toast({ title: str(t.urlCopied) })
                        }}
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>{str(t.scheduleName)}</TableHead>
                        <TableHead>{str(t.lastTriggered)}</TableHead>
                        <TableHead className="text-center">{str(t.triggerCount)}</TableHead>
                        <TableHead>{str(t.requireSignature)}</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {webhookSchedules.map((schedule) => (
                        <TableRow key={schedule.schedule_id}>
                          <TableCell className="font-medium">
                            {schedule.schedule_name}
                          </TableCell>
                          <TableCell>
                            {formatRelativeTime(schedule.last_triggered_at)}
                          </TableCell>
                          <TableCell className="text-center">
                            {schedule.trigger_count}
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">Optional</Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Composite Tab */}
        <TabsContent value="composite">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Layers className="h-5 w-5 text-purple-500" />
                {str(t.compositeTriggers)}
              </CardTitle>
              <CardDescription>
                Triggers that combine multiple conditions with AND/OR logic
              </CardDescription>
            </CardHeader>
            <CardContent>
              {compositeSchedules.length === 0 ? (
                <div className="text-center py-8">
                  <Layers className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">{str(t.noTriggers)}</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{str(t.scheduleName)}</TableHead>
                      <TableHead>{str(t.operator)}</TableHead>
                      <TableHead>{str(t.status)}</TableHead>
                      <TableHead>{str(t.lastTriggered)}</TableHead>
                      <TableHead className="text-center">{str(t.triggerCount)}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {compositeSchedules.map((schedule) => (
                      <TableRow key={schedule.schedule_id}>
                        <TableCell className="font-medium">
                          {schedule.schedule_name}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">AND</Badge>
                        </TableCell>
                        <TableCell>
                          {schedule.is_due_for_check ? (
                            <Badge
                              variant="outline"
                              className="bg-amber-500/10 text-amber-500"
                            >
                              {str(t.dueForCheck)}
                            </Badge>
                          ) : (
                            <Badge
                              variant="outline"
                              className="bg-green-500/10 text-green-500"
                            >
                              {str(t.ready)}
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          {formatRelativeTime(schedule.last_triggered_at)}
                        </TableCell>
                        <TableCell className="text-center">{schedule.trigger_count}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
