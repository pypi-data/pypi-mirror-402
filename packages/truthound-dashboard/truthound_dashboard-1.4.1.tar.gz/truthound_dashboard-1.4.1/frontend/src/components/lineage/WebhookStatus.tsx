/**
 * WebhookStatus component - Status indicator for OpenLineage webhooks.
 *
 * Shows connection status, last sent timestamp, success/failure counts,
 * and last error message.
 */

import { formatDistanceToNow } from 'date-fns'
import { CheckCircle, XCircle, Clock, AlertCircle, Activity } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import { useIntlayer } from '@/providers'
import { str } from '@/lib/intlayer-utils'
import type { OpenLineageWebhook } from '@/api/client'

interface WebhookStatusProps {
  webhook: OpenLineageWebhook
  className?: string
  compact?: boolean
}

export function WebhookStatus({ webhook, className, compact = false }: WebhookStatusProps) {
  const t = useIntlayer('lineage')

  const totalEmissions = webhook.success_count + webhook.failure_count
  const successRate = totalEmissions > 0 ? (webhook.success_count / totalEmissions) * 100 : 100

  const getStatusColor = () => {
    if (!webhook.is_active) return 'bg-muted text-muted-foreground'
    if (webhook.last_error) return 'bg-destructive/10 text-destructive'
    if (webhook.success_count > 0) return 'bg-green-500/10 text-green-600'
    return 'bg-muted text-muted-foreground'
  }

  const getStatusIcon = () => {
    if (!webhook.is_active) return <Clock className="h-4 w-4" />
    if (webhook.last_error) return <XCircle className="h-4 w-4" />
    if (webhook.success_count > 0) return <CheckCircle className="h-4 w-4" />
    return <Activity className="h-4 w-4" />
  }

  if (compact) {
    return (
      <div className={cn('flex items-center gap-2', className)}>
        <Badge
          variant="outline"
          className={cn(
            'flex items-center gap-1',
            webhook.is_active ? 'border-green-500/50 text-green-600' : 'border-muted'
          )}
        >
          {getStatusIcon()}
          {webhook.is_active ? str(t.activeWebhook) : str(t.inactiveWebhook)}
        </Badge>
        {webhook.last_sent_at && (
          <span className="text-xs text-muted-foreground">
            {formatDistanceToNow(new Date(webhook.last_sent_at), { addSuffix: true })}
          </span>
        )}
      </div>
    )
  }

  return (
    <div className={cn('space-y-3', className)}>
      {/* Status Badge */}
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">{str(t.webhookStatus)}</span>
        <Badge variant="outline" className={cn('flex items-center gap-1', getStatusColor())}>
          {getStatusIcon()}
          {webhook.is_active ? str(t.activeWebhook) : str(t.inactiveWebhook)}
        </Badge>
      </div>

      {/* Last Sent */}
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">{str(t.lastSent)}</span>
        <span>
          {webhook.last_sent_at
            ? formatDistanceToNow(new Date(webhook.last_sent_at), { addSuffix: true })
            : str(t.neverSent)}
        </span>
      </div>

      {/* Success/Failure Stats */}
      {totalEmissions > 0 && (
        <>
          <div className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">{str(t.successRate)}</span>
              <span className={successRate >= 90 ? 'text-green-600' : 'text-amber-600'}>
                {successRate.toFixed(1)}%
              </span>
            </div>
            <Progress
              value={successRate}
              className="h-2"
            />
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <span className="text-muted-foreground">{str(t.successCount)}:</span>
              <span className="font-medium">{webhook.success_count}</span>
            </div>
            <div className="flex items-center gap-2">
              <XCircle className="h-4 w-4 text-destructive" />
              <span className="text-muted-foreground">{str(t.failureCount)}:</span>
              <span className="font-medium">{webhook.failure_count}</span>
            </div>
          </div>
        </>
      )}

      {/* Last Error */}
      {webhook.last_error && (
        <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-3">
          <div className="flex items-start gap-2">
            <AlertCircle className="h-4 w-4 text-destructive mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-medium text-destructive">{str(t.lastError)}</p>
              <p className="text-xs text-muted-foreground mt-1 break-all">{webhook.last_error}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default WebhookStatus
