/**
 * Batch Progress Component.
 *
 * Shows real-time progress of a batch anomaly detection job.
 */

import { useCallback, useEffect, useState } from 'react'
import { useIntlayer } from 'react-intlayer'
import { str } from '@/lib/intlayer-utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { useToast } from '@/hooks/use-toast'
import {
  Loader2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  StopCircle,
  Database,
  Clock,
} from 'lucide-react'
import type { BatchDetectionJob } from '@/api/client'
import { getBatchDetection, cancelBatchDetection } from '@/api/client'

interface BatchProgressProps {
  batchId: string
  onComplete?: (job: BatchDetectionJob) => void
  className?: string
}

export function BatchProgress({ batchId, onComplete, className }: BatchProgressProps) {
  const t = useIntlayer('anomaly')
  const common = useIntlayer('common')
  const { toast } = useToast()

  const [job, setJob] = useState<BatchDetectionJob | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isCancelling, setIsCancelling] = useState(false)

  // Poll for updates
  useEffect(() => {
    let intervalId: NodeJS.Timeout

    const fetchJob = async () => {
      try {
        const data = await getBatchDetection(batchId)
        setJob(data)
        setIsLoading(false)

        // Stop polling when complete
        if (
          data.status === 'completed' ||
          data.status === 'partial' ||
          data.status === 'error' ||
          data.status === 'cancelled'
        ) {
          if (intervalId) {
            clearInterval(intervalId)
          }
          onComplete?.(data)
        }
      } catch (error) {
        setIsLoading(false)
        if (intervalId) {
          clearInterval(intervalId)
        }
      }
    }

    // Initial fetch
    fetchJob()

    // Poll every 2 seconds while running
    intervalId = setInterval(fetchJob, 2000)

    return () => {
      if (intervalId) {
        clearInterval(intervalId)
      }
    }
  }, [batchId, onComplete])

  // Cancel job
  const handleCancel = useCallback(async () => {
    setIsCancelling(true)
    try {
      const cancelled = await cancelBatchDetection(batchId)
      setJob(cancelled)
      toast({
        title: str(t.batch.jobCancelled),
      })
    } catch (error) {
      toast({
        title: str(common.error),
        variant: 'destructive',
      })
    } finally {
      setIsCancelling(false)
    }
  }, [batchId, toast, t, common])

  if (isLoading || !job) {
    return (
      <Card className={className}>
        <CardContent className="flex h-32 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    )
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
      case 'pending':
        return <Loader2 className="h-5 w-5 animate-spin text-primary" />
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />
      case 'partial':
        return <AlertTriangle className="h-5 w-5 text-orange-500" />
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />
      case 'cancelled':
        return <StopCircle className="h-5 w-5 text-gray-500" />
      default:
        return null
    }
  }

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
      pending: 'secondary',
      running: 'default',
      completed: 'default',
      partial: 'outline',
      error: 'destructive',
      cancelled: 'secondary',
    }
    return (
      <Badge variant={variants[status] || 'default'}>
        {t.batch.status[status as keyof typeof t.batch.status] || status}
      </Badge>
    )
  }

  const currentSource = job.results?.find((r) => r.source_id === job.current_source_id)

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            {getStatusIcon(job.status)}
            {job.name || t.batch.untitledJob}
          </CardTitle>
          {getStatusBadge(job.status)}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">
              {t.batch.progress}: {job.completed_sources + job.failed_sources} / {job.total_sources}
            </span>
            <span className="font-medium">{job.progress_percent.toFixed(0)}%</span>
          </div>
          <Progress value={job.progress_percent} className="h-2" />
        </div>

        {/* Current Source */}
        {job.status === 'running' && currentSource && (
          <div className="flex items-center gap-2 rounded-md bg-muted p-2 text-sm">
            <Database className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">{t.batch.processing}:</span>
            <span className="font-medium">{currentSource.source_name || job.current_source_id}</span>
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">{t.batch.completed}</p>
            <p className="text-xl font-bold text-green-600">{job.completed_sources}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">{t.batch.failed}</p>
            <p className="text-xl font-bold text-red-600">{job.failed_sources}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">{t.anomaliesFound}</p>
            <p className="text-xl font-bold text-orange-500">{job.total_anomalies}</p>
          </div>
        </div>

        {/* Duration */}
        {job.duration_ms != null && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="h-4 w-4" />
            <span>
              {t.duration}: {(job.duration_ms / 1000).toFixed(1)}s
            </span>
          </div>
        )}

        {/* Error Message */}
        {job.error_message && (
          <div className="rounded-md bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-400">
            {job.error_message}
          </div>
        )}

        {/* Per-Source Status (collapsed list) */}
        {job.results && job.results.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium">{t.batch.sourceResults}</p>
            <div className="max-h-32 space-y-1 overflow-y-auto">
              {job.results.map((result) => (
                <div
                  key={result.source_id}
                  className="flex items-center justify-between rounded p-1.5 text-sm hover:bg-muted"
                >
                  <span className="truncate">{result.source_name || result.source_id}</span>
                  <div className="flex items-center gap-2">
                    {result.status === 'success' && (
                      <>
                        <span className="text-orange-500">{result.anomaly_count}</span>
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                      </>
                    )}
                    {result.status === 'error' && (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                    {result.status === 'running' && (
                      <Loader2 className="h-4 w-4 animate-spin text-primary" />
                    )}
                    {result.status === 'pending' && (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Cancel Button */}
        {(job.status === 'running' || job.status === 'pending') && (
          <Button
            variant="outline"
            onClick={handleCancel}
            disabled={isCancelling}
            className="w-full"
          >
            {isCancelling ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {t.batch.cancelling}
              </>
            ) : (
              <>
                <StopCircle className="mr-2 h-4 w-4" />
                {t.batch.cancel}
              </>
            )}
          </Button>
        )}
      </CardContent>
    </Card>
  )
}
