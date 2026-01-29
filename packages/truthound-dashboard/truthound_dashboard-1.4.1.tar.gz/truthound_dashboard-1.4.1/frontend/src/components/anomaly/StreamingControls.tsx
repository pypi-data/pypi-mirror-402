/**
 * Controls for streaming anomaly detection session.
 *
 * Allows configuring and starting/stopping streaming sessions.
 */

import { useState, useCallback } from 'react'
import { useIntlayer } from 'react-intlayer'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Play, Square, Radio, Wifi, WifiOff } from 'lucide-react'
import type {
  StreamingAlgorithm,
  StreamingAlgorithmInfo,
  StreamingSession,
  StreamingSessionCreate,
} from '@/api/client'

interface StreamingControlsProps {
  algorithms: StreamingAlgorithmInfo[]
  session: StreamingSession | null
  isConnected: boolean
  isLoading: boolean
  onStart: (config: StreamingSessionCreate) => Promise<StreamingSession | null>
  onStop: () => Promise<void>
  columns?: string[]
  className?: string
}

export function StreamingControls({
  algorithms,
  session,
  isConnected,
  isLoading,
  onStart,
  onStop,
  columns = [],
  className,
}: StreamingControlsProps) {
  const t = useIntlayer('anomaly')

  // Configuration state
  const [algorithm, setAlgorithm] = useState<StreamingAlgorithm>('zscore_rolling')
  const [windowSize, setWindowSize] = useState(100)
  const [threshold, setThreshold] = useState(3.0)
  const [selectedColumns, setSelectedColumns] = useState<string[]>([])

  const isRunning = session?.status === 'running'

  // Get selected algorithm info
  const selectedAlgorithmInfo = algorithms.find((a) => a.name === algorithm)

  // Handle start
  const handleStart = useCallback(async () => {
    await onStart({
      algorithm,
      window_size: windowSize,
      threshold,
      columns: selectedColumns.length > 0 ? selectedColumns : undefined,
    })
  }, [onStart, algorithm, windowSize, threshold, selectedColumns])

  // Toggle column selection
  const toggleColumn = useCallback((column: string) => {
    setSelectedColumns((prev) =>
      prev.includes(column) ? prev.filter((c) => c !== column) : [...prev, column]
    )
  }, [])

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Radio className="h-5 w-5" />
              {t.streaming?.controls ?? 'Streaming Controls'}
            </CardTitle>
            <CardDescription>
              {t.streaming?.controlsDescription ?? 'Configure and manage real-time anomaly detection'}
            </CardDescription>
          </div>
          {session && (
            <div className="flex items-center gap-2">
              {isConnected ? (
                <Badge variant="default" className="gap-1">
                  <Wifi className="h-3 w-3" />
                  {t.streaming?.connected ?? 'Connected'}
                </Badge>
              ) : (
                <Badge variant="secondary" className="gap-1">
                  <WifiOff className="h-3 w-3" />
                  {t.streaming?.disconnected ?? 'Disconnected'}
                </Badge>
              )}
              <Badge variant={isRunning ? 'default' : 'secondary'}>
                {session.status}
              </Badge>
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Algorithm Selection */}
        <div className="space-y-2">
          <Label>{t.streaming?.algorithm ?? 'Algorithm'}</Label>
          <Select
            value={algorithm}
            onValueChange={(v) => setAlgorithm(v as StreamingAlgorithm)}
            disabled={isRunning}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {algorithms.map((algo) => (
                <SelectItem key={algo.name} value={algo.name}>
                  <div className="flex items-center gap-2">
                    <span>{algo.display_name}</span>
                    {algo.supports_online_learning && (
                      <Badge variant="outline" className="text-xs">
                        {t.streaming?.onlineLearning ?? 'Online'}
                      </Badge>
                    )}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {selectedAlgorithmInfo && (
            <p className="text-xs text-muted-foreground">
              {selectedAlgorithmInfo.description}
            </p>
          )}
        </div>

        {/* Window Size */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label>{t.streaming?.windowSize ?? 'Window Size'}</Label>
            <span className="text-sm text-muted-foreground">{windowSize}</span>
          </div>
          <Slider
            value={[windowSize]}
            onValueChange={([v]) => setWindowSize(v)}
            min={10}
            max={1000}
            step={10}
            disabled={isRunning}
          />
          <p className="text-xs text-muted-foreground">
            {t.streaming?.windowSizeHint ?? 'Number of recent data points to analyze'}
          </p>
        </div>

        {/* Threshold */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label>{t.streaming?.threshold ?? 'Threshold'}</Label>
            <span className="text-sm text-muted-foreground">{threshold.toFixed(1)}</span>
          </div>
          <Slider
            value={[threshold]}
            onValueChange={([v]) => setThreshold(v)}
            min={1}
            max={5}
            step={0.1}
            disabled={isRunning}
          />
          <p className="text-xs text-muted-foreground">
            {t.streaming?.thresholdHint ?? 'Standard deviations for anomaly detection'}
          </p>
        </div>

        {/* Column Selection */}
        {columns.length > 0 && (
          <div className="space-y-2">
            <Label>{t.streaming?.columns ?? 'Columns to Monitor'}</Label>
            <div className="flex flex-wrap gap-2">
              {columns.map((column) => (
                <Badge
                  key={column}
                  variant={selectedColumns.includes(column) ? 'default' : 'outline'}
                  className="cursor-pointer"
                  onClick={() => !isRunning && toggleColumn(column)}
                >
                  {column}
                </Badge>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">
              {selectedColumns.length === 0
                ? (t.streaming?.allColumnsHint ?? 'All numeric columns will be monitored')
                : `${selectedColumns.length} column(s) selected`}
            </p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2">
          {!isRunning ? (
            <Button onClick={handleStart} disabled={isLoading} className="flex-1 gap-2">
              <Play className="h-4 w-4" />
              {t.streaming?.startSession ?? 'Start Streaming'}
            </Button>
          ) : (
            <Button
              onClick={onStop}
              disabled={isLoading}
              variant="destructive"
              className="flex-1 gap-2"
            >
              <Square className="h-4 w-4" />
              {t.streaming?.stopSession ?? 'Stop Streaming'}
            </Button>
          )}
        </div>

        {/* Session Info */}
        {session && (
          <div className="rounded-lg bg-muted/50 p-3 text-sm">
            <div className="grid grid-cols-2 gap-2">
              <div>
                <span className="text-muted-foreground">
                  {t.streaming?.sessionId ?? 'Session ID'}:
                </span>
                <span className="ml-1 font-mono text-xs">{session.id.slice(0, 8)}...</span>
              </div>
              <div>
                <span className="text-muted-foreground">
                  {t.streaming?.totalPoints ?? 'Points'}:
                </span>
                <span className="ml-1">{session.total_points}</span>
              </div>
              <div>
                <span className="text-muted-foreground">
                  {t.streaming?.totalAlerts ?? 'Alerts'}:
                </span>
                <span className="ml-1 text-orange-500">{session.total_alerts}</span>
              </div>
              {session.started_at && (
                <div>
                  <span className="text-muted-foreground">
                    {t.streaming?.startedAt ?? 'Started'}:
                  </span>
                  <span className="ml-1">
                    {new Date(session.started_at).toLocaleTimeString()}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
