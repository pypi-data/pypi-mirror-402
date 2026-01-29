/**
 * Real-time streaming anomaly detection dashboard.
 *
 * Provides a complete interface for streaming anomaly detection including:
 * - Session controls (start/stop, algorithm config)
 * - Live data visualization
 * - Real-time alerts
 * - Rolling statistics
 */

import { useEffect, useCallback, useState } from 'react'
import { useIntlayer } from 'react-intlayer'
import { str } from '@/lib/intlayer-utils'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useToast } from '@/hooks/use-toast'
import { useStreamingAnomaly } from '@/hooks/useStreamingAnomaly'
import { StreamingControls } from './StreamingControls'
import { StreamingChart } from './StreamingChart'
import {
  AlertTriangle,
  Activity,
  TrendingUp,
  Trash2,
  Database,
  Clock,
} from 'lucide-react'
import type { StreamingAlert } from '@/api/client'

interface StreamingDashboardProps {
  sourceId?: string
  columns?: string[]
  className?: string
}

export function StreamingDashboard({
  sourceId,
  columns = [],
  className,
}: StreamingDashboardProps) {
  const t = useIntlayer('anomaly')
  const { toast } = useToast()

  // Streaming hook
  const {
    session,
    status,
    alerts,
    algorithms,
    isLoading,
    isConnected,
    error,
    startSession,
    stopSession,
    clearAlerts,
    loadAlgorithms,
  } = useStreamingAnomaly({
    autoReconnect: true,
    pollInterval: 2000,
  })

  // Simulated data for demo
  const [simulatedData, setSimulatedData] = useState<
    Array<{ timestamp: string; data: Record<string, unknown> }>
  >([])
  const [isSimulating, setIsSimulating] = useState(false)

  // Load algorithms on mount
  useEffect(() => {
    loadAlgorithms()
  }, [loadAlgorithms])

  // Show error toast
  useEffect(() => {
    if (error) {
      toast({
        title: str(t.streaming?.error ?? 'Error'),
        description: error,
        variant: 'destructive',
      })
    }
  }, [error, toast, t])

  // Handle start session with source ID
  const handleStartSession = useCallback(
    async (config: Parameters<typeof startSession>[0]) => {
      const result = await startSession({
        ...config,
        source_id: sourceId,
      })

      if (result) {
        toast({
          title: str(t.streaming?.sessionStarted ?? 'Session Started'),
          description: `Session ${result.id.slice(0, 8)}... is now running`,
        })
        setSimulatedData([])
      }

      return result
    },
    [startSession, sourceId, toast, t]
  )

  // Handle stop session
  const handleStopSession = useCallback(async () => {
    await stopSession()
    setIsSimulating(false)
    toast({
      title: str(t.streaming?.sessionStopped ?? 'Session Stopped'),
    })
  }, [stopSession, toast, t])

  // Simulate data for demo mode
  const startSimulation = useCallback(() => {
    if (!session || session.status !== 'running') return

    setIsSimulating(true)

    const interval = setInterval(() => {
      // Generate random data point
      const timestamp = new Date().toISOString()
      const data: Record<string, unknown> = {}

      const cols = session.columns.length > 0 ? session.columns : columns
      for (const col of cols) {
        // Normal value with occasional anomaly
        const isAnomaly = Math.random() < 0.05
        const baseValue = 100
        const noise = (Math.random() - 0.5) * 10
        const anomalySpike = isAnomaly ? (Math.random() > 0.5 ? 50 : -50) : 0
        data[col] = baseValue + noise + anomalySpike
      }

      setSimulatedData((prev) => [...prev.slice(-99), { timestamp, data }])
    }, 500)

    return () => {
      clearInterval(interval)
      setIsSimulating(false)
    }
  }, [session, columns])

  // Get active columns
  const activeColumns =
    session?.columns && session.columns.length > 0 ? session.columns : columns

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Top Row: Controls and Stats */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Controls */}
        <StreamingControls
          algorithms={algorithms}
          session={session}
          isConnected={isConnected}
          isLoading={isLoading}
          onStart={handleStartSession}
          onStop={handleStopSession}
          columns={columns}
          className="lg:col-span-2"
        />

        {/* Quick Stats */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Activity className="h-4 w-4" />
              {t.streaming?.statistics ?? 'Statistics'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">
                  {t.streaming?.dataPoints ?? 'Data Points'}
                </p>
                <p className="text-2xl font-bold">
                  {status?.total_points ?? 0}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">
                  {t.streaming?.anomalies ?? 'Anomalies'}
                </p>
                <p className="text-2xl font-bold text-orange-500">
                  {status?.total_alerts ?? 0}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">
                  {t.streaming?.bufferUtilization ?? 'Buffer'}
                </p>
                <p className="text-lg font-semibold">
                  {((status?.buffer_utilization ?? 0) * 100).toFixed(0)}%
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">
                  {t.streaming?.anomalyRate ?? 'Anomaly Rate'}
                </p>
                <p className="text-lg font-semibold">
                  {status?.total_points
                    ? ((status.total_alerts / status.total_points) * 100).toFixed(1)
                    : 0}
                  %
                </p>
              </div>
            </div>

            {/* Demo mode button */}
            {session?.status === 'running' && !isSimulating && (
              <Button
                variant="outline"
                size="sm"
                className="mt-4 w-full gap-2"
                onClick={startSimulation}
              >
                <Database className="h-4 w-4" />
                {t.streaming?.startDemo ?? 'Start Demo Data'}
              </Button>
            )}
            {isSimulating && (
              <Badge variant="secondary" className="mt-4 w-full justify-center">
                <Activity className="mr-1 h-3 w-3 animate-pulse" />
                {t.streaming?.simulatingData ?? 'Simulating data...'}
              </Badge>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Chart */}
      {session && (
        <StreamingChart
          dataPoints={simulatedData}
          alerts={alerts}
          statistics={status?.statistics ?? null}
          columns={activeColumns}
          maxPoints={100}
        />
      )}

      {/* Alerts Section */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-sm">
              <AlertTriangle className="h-4 w-4 text-orange-500" />
              {t.streaming?.recentAlerts ?? 'Recent Alerts'}
              {alerts.length > 0 && (
                <Badge variant="destructive" className="ml-2">
                  {alerts.length}
                </Badge>
              )}
            </CardTitle>
            {alerts.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearAlerts}
                className="gap-1 text-xs"
              >
                <Trash2 className="h-3 w-3" />
                {t.streaming?.clearAlerts ?? 'Clear'}
              </Button>
            )}
          </div>
          <CardDescription>
            {t.streaming?.alertsDescription ?? 'Real-time anomaly alerts from the streaming session'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {alerts.length === 0 ? (
            <div className="flex h-32 flex-col items-center justify-center text-muted-foreground">
              <TrendingUp className="mb-2 h-8 w-8" />
              <p>{t.streaming?.noAlerts ?? 'No anomalies detected yet'}</p>
              <p className="text-xs">
                {t.streaming?.noAlertsHint ?? 'Alerts will appear here when anomalies are detected'}
              </p>
            </div>
          ) : (
            <ScrollArea className="h-64">
              <div className="space-y-2">
                {alerts.map((alert) => (
                  <AlertCard key={alert.id} alert={alert} />
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// Alert card component
function AlertCard({ alert }: { alert: StreamingAlert }) {
  const t = useIntlayer('anomaly')

  return (
    <div className="flex items-start gap-3 rounded-lg border bg-destructive/5 p-3">
      <AlertTriangle className="mt-0.5 h-4 w-4 text-destructive" />
      <div className="flex-1 space-y-1">
        <div className="flex items-center justify-between">
          <Badge variant="destructive" className="text-xs">
            Score: {alert.anomaly_score.toFixed(3)}
          </Badge>
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            {new Date(alert.timestamp).toLocaleTimeString()}
          </span>
        </div>
        <div className="text-xs">
          <span className="text-muted-foreground">
            {t.streaming?.algorithm ?? 'Algorithm'}:
          </span>{' '}
          <span className="font-medium">{alert.algorithm}</span>
        </div>
        <div className="mt-1 flex flex-wrap gap-1">
          {Object.entries(alert.data_point).map(([key, value]) => (
            <Badge key={key} variant="outline" className="text-xs">
              {key}: {typeof value === 'number' ? value.toFixed(2) : String(value ?? '')}
            </Badge>
          ))}
        </div>
        {Array.isArray(alert.details?.anomaly_columns) && alert.details.anomaly_columns.length > 0 && (
          <div className="text-xs text-muted-foreground">
            Anomalous columns: {(alert.details.anomaly_columns as string[]).join(', ')}
          </div>
        )}
      </div>
    </div>
  )
}
