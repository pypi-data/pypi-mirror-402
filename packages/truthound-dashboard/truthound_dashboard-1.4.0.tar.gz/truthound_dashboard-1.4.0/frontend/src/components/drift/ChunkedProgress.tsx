/**
 * Chunked progress component for large-scale drift detection.
 *
 * Shows real-time progress during sampled drift comparisons.
 */

import { useEffect, useState } from 'react'
import { useIntlayer } from 'react-intlayer'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Loader2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  Database,
  Layers,
  Zap,
  StopCircle,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface ChunkedProgressData {
  jobId: string
  status: 'running' | 'completed' | 'cancelled' | 'error'
  progress: {
    totalChunks: number
    processedChunks: number
    totalRows: number
    processedRows: number
    percentage: number
  }
  timing: {
    elapsedSeconds: number
    estimatedRemainingSeconds: number
  }
  interimResults: {
    columnsWithDrift: string[]
    earlyStopTriggered: boolean
  }
}

interface ChunkedProgressProps {
  progress: ChunkedProgressData
  onCancel?: () => void
  onComplete?: () => void
  className?: string
}

export function ChunkedProgress({
  progress,
  onCancel,
  onComplete,
  className = '',
}: ChunkedProgressProps) {
  const t = useIntlayer('driftMonitor')
  const [showDetails, setShowDetails] = useState(false)

  const formatTime = (seconds: number) => {
    if (seconds < 60) {
      return `${seconds.toFixed(0)}s`
    }
    if (seconds < 3600) {
      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${mins}m ${secs}s`
    }
    const hours = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    return `${hours}h ${mins}m`
  }

  const formatNumber = (num: number) => {
    if (num >= 1_000_000) {
      return `${(num / 1_000_000).toFixed(1)}M`
    }
    if (num >= 1_000) {
      return `${(num / 1_000).toFixed(1)}K`
    }
    return num.toString()
  }

  const getStatusIcon = () => {
    switch (progress.status) {
      case 'running':
        return <Loader2 className="h-5 w-5 animate-spin text-primary" />
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />
      case 'cancelled':
        return <StopCircle className="h-5 w-5 text-yellow-500" />
      case 'error':
        return <XCircle className="h-5 w-5 text-destructive" />
      default:
        return null
    }
  }

  const getStatusText = () => {
    switch (progress.status) {
      case 'running':
        return t.progress.running
      case 'completed':
        return t.progress.completed
      case 'cancelled':
        return t.progress.cancelled
      case 'error':
        return t.progress.error
      default:
        return progress.status
    }
  }

  const getStatusColor = () => {
    switch (progress.status) {
      case 'running':
        return 'bg-primary'
      case 'completed':
        return 'bg-green-500'
      case 'cancelled':
        return 'bg-yellow-500'
      case 'error':
        return 'bg-destructive'
      default:
        return 'bg-muted'
    }
  }

  // Call onComplete when status changes to completed
  useEffect(() => {
    if (progress.status === 'completed' && onComplete) {
      onComplete()
    }
  }, [progress.status, onComplete])

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            {getStatusIcon()}
            {getStatusText()}
          </CardTitle>
          {progress.status === 'running' && onCancel && (
            <Button variant="outline" size="sm" onClick={onCancel}>
              <StopCircle className="mr-2 h-4 w-4" />
              {t.progress.cancel}
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Main Progress Bar */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">{t.progress.progress}</span>
            <span className="font-medium">{progress.progress.percentage.toFixed(1)}%</span>
          </div>
          <Progress
            value={progress.progress.percentage}
            className={cn('h-3', getStatusColor())}
          />
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-4 gap-4">
          {/* Chunks */}
          <div className="space-y-1 text-center">
            <Layers className="mx-auto h-4 w-4 text-muted-foreground" />
            <div className="text-lg font-semibold">
              {progress.progress.processedChunks}/{progress.progress.totalChunks}
            </div>
            <div className="text-xs text-muted-foreground">{t.progress.chunks}</div>
          </div>

          {/* Rows */}
          <div className="space-y-1 text-center">
            <Database className="mx-auto h-4 w-4 text-muted-foreground" />
            <div className="text-lg font-semibold">
              {formatNumber(progress.progress.processedRows)}
            </div>
            <div className="text-xs text-muted-foreground">{t.progress.rowsProcessed}</div>
          </div>

          {/* Time Elapsed */}
          <div className="space-y-1 text-center">
            <Clock className="mx-auto h-4 w-4 text-muted-foreground" />
            <div className="text-lg font-semibold">
              {formatTime(progress.timing.elapsedSeconds)}
            </div>
            <div className="text-xs text-muted-foreground">{t.progress.elapsed}</div>
          </div>

          {/* ETA */}
          <div className="space-y-1 text-center">
            <Clock className="mx-auto h-4 w-4 text-muted-foreground" />
            <div className="text-lg font-semibold">
              {progress.status === 'running'
                ? formatTime(progress.timing.estimatedRemainingSeconds)
                : '--'}
            </div>
            <div className="text-xs text-muted-foreground">{t.progress.eta}</div>
          </div>
        </div>

        {/* Early Stop Notice */}
        {progress.interimResults.earlyStopTriggered && (
          <div className="flex items-center gap-2 rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-3">
            <Zap className="h-4 w-4 text-yellow-500" />
            <div className="text-sm">
              <span className="font-medium text-yellow-600 dark:text-yellow-400">
                {t.progress.earlyStopTriggered}
              </span>
              <span className="ml-1 text-muted-foreground">
                {t.progress.earlyStopReason}
              </span>
            </div>
          </div>
        )}

        {/* Interim Results - Drifted Columns */}
        {progress.interimResults.columnsWithDrift.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-medium">
                <AlertTriangle className="h-4 w-4 text-destructive" />
                {t.progress.driftedColumnsFound}
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowDetails(!showDetails)}
              >
                {showDetails ? t.progress.hideDetails : t.progress.showDetails}
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              {(showDetails
                ? progress.interimResults.columnsWithDrift
                : progress.interimResults.columnsWithDrift.slice(0, 5)
              ).map((col) => (
                <Badge key={col} variant="destructive" className="text-xs">
                  {col}
                </Badge>
              ))}
              {!showDetails && progress.interimResults.columnsWithDrift.length > 5 && (
                <Badge variant="outline" className="text-xs">
                  +{progress.interimResults.columnsWithDrift.length - 5} more
                </Badge>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

/**
 * Compact inline progress indicator
 */
interface InlineProgressProps {
  percentage: number
  status: 'running' | 'completed' | 'cancelled' | 'error'
  eta?: number
  onCancel?: () => void
}

export function InlineProgress({ percentage, status, eta, onCancel }: InlineProgressProps) {
  void useIntlayer('driftMonitor')

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(0)}s`
    return `${Math.floor(seconds / 60)}m`
  }

  return (
    <div className="flex items-center gap-3">
      {status === 'running' ? (
        <Loader2 className="h-4 w-4 animate-spin text-primary" />
      ) : status === 'completed' ? (
        <CheckCircle2 className="h-4 w-4 text-green-500" />
      ) : status === 'cancelled' ? (
        <StopCircle className="h-4 w-4 text-yellow-500" />
      ) : (
        <XCircle className="h-4 w-4 text-destructive" />
      )}

      <div className="flex-1">
        <Progress value={percentage} className="h-2" />
      </div>

      <span className="min-w-[4rem] text-right text-sm text-muted-foreground">
        {percentage.toFixed(0)}%
      </span>

      {status === 'running' && eta !== undefined && (
        <span className="text-sm text-muted-foreground">
          ETA: {formatTime(eta)}
        </span>
      )}

      {status === 'running' && onCancel && (
        <Button variant="ghost" size="sm" onClick={onCancel} className="h-6 px-2">
          <StopCircle className="h-3 w-3" />
        </Button>
      )}
    </div>
  )
}
