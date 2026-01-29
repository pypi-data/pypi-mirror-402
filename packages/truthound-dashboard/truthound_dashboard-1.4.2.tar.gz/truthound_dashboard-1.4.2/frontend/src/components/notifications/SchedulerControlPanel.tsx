/**
 * SchedulerControlPanel - Escalation scheduler control UI
 *
 * Provides controls for:
 * - Start/Stop scheduler
 * - Manual trigger
 * - Configuration (check interval)
 * - Status monitoring
 */

import { useState, useEffect, useCallback } from 'react'
import {
  Play,
  Square,
  RefreshCw,
  Settings,
  Clock,
  AlertTriangle,
  CheckCircle,
  Loader2,
  Zap,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { useToast } from '@/hooks/use-toast'
import type { EscalationSchedulerStatus } from '@/api/client'
import {
  getEscalationSchedulerStatus,
  startEscalationScheduler,
  stopEscalationScheduler,
  triggerEscalationCheck,
  updateEscalationSchedulerConfig,
} from '@/api/client'

interface SchedulerControlPanelProps {
  className?: string
  compact?: boolean
  onStatusChange?: (status: EscalationSchedulerStatus) => void
}

export function SchedulerControlPanel({
  className,
  compact = false,
  onStatusChange,
}: SchedulerControlPanelProps) {
  const { toast } = useToast()
  const [status, setStatus] = useState<EscalationSchedulerStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [configDialogOpen, setConfigDialogOpen] = useState(false)
  const [configInterval, setConfigInterval] = useState(60)

  const loadStatus = useCallback(async () => {
    try {
      const result = await getEscalationSchedulerStatus()
      setStatus(result)
      onStatusChange?.(result)
    } catch {
      // Silently fail, status will show as unknown
    } finally {
      setLoading(false)
    }
  }, [onStatusChange])

  useEffect(() => {
    loadStatus()
    // Refresh status every 30 seconds
    const interval = setInterval(loadStatus, 30000)
    return () => clearInterval(interval)
  }, [loadStatus])

  const handleStart = async () => {
    setActionLoading('start')
    try {
      const result = await startEscalationScheduler()
      setStatus(result.status)
      onStatusChange?.(result.status)
      toast({ title: 'Scheduler started', description: result.message })
    } catch (e) {
      toast({
        title: 'Failed to start scheduler',
        description: e instanceof Error ? e.message : undefined,
        variant: 'destructive',
      })
    } finally {
      setActionLoading(null)
    }
  }

  const handleStop = async () => {
    setActionLoading('stop')
    try {
      const result = await stopEscalationScheduler()
      setStatus(result.status)
      onStatusChange?.(result.status)
      toast({ title: 'Scheduler stopped', description: result.message })
    } catch (e) {
      toast({
        title: 'Failed to stop scheduler',
        description: e instanceof Error ? e.message : undefined,
        variant: 'destructive',
      })
    } finally {
      setActionLoading(null)
    }
  }

  const handleTrigger = async () => {
    setActionLoading('trigger')
    try {
      const result = await triggerEscalationCheck()
      toast({
        title: 'Escalation check triggered',
        description: `Checked ${result.incidents_checked} incidents, triggered ${result.escalations_triggered} escalations`,
      })
      loadStatus()
    } catch (e) {
      toast({
        title: 'Failed to trigger check',
        description: e instanceof Error ? e.message : undefined,
        variant: 'destructive',
      })
    } finally {
      setActionLoading(null)
    }
  }

  const handleSaveConfig = async () => {
    setActionLoading('config')
    try {
      const result = await updateEscalationSchedulerConfig({
        check_interval_seconds: configInterval,
      })
      setStatus(result.status)
      onStatusChange?.(result.status)
      toast({ title: 'Configuration updated', description: result.message })
      setConfigDialogOpen(false)
    } catch (e) {
      toast({
        title: 'Failed to update configuration',
        description: e instanceof Error ? e.message : undefined,
        variant: 'destructive',
      })
    } finally {
      setActionLoading(null)
    }
  }

  const openConfigDialog = () => {
    setConfigInterval(status?.check_interval_seconds || 60)
    setConfigDialogOpen(true)
  }

  const formatTime = (isoString: string | null) => {
    if (!isoString) return '-'
    return new Date(isoString).toLocaleTimeString()
  }

  if (loading) {
    return (
      <div className={`flex items-center justify-center py-4 ${className}`}>
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    )
  }

  // Compact mode - just buttons
  if (compact) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Badge
                variant={status?.is_running ? 'default' : 'secondary'}
                className={status?.is_running ? 'bg-green-500' : ''}
              >
                {status?.is_running ? (
                  <CheckCircle className="h-3 w-3 mr-1" />
                ) : (
                  <Square className="h-3 w-3 mr-1" />
                )}
                {status?.is_running ? 'Running' : 'Stopped'}
              </Badge>
            </TooltipTrigger>
            <TooltipContent>
              <p>Scheduler is {status?.is_running ? 'running' : 'stopped'}</p>
              {status?.last_check_at && (
                <p className="text-xs text-muted-foreground">
                  Last check: {formatTime(status.last_check_at)}
                </p>
              )}
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        {status?.is_running ? (
          <Button
            variant="outline"
            size="sm"
            onClick={handleStop}
            disabled={actionLoading !== null}
          >
            {actionLoading === 'stop' ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Square className="h-4 w-4" />
            )}
          </Button>
        ) : (
          <Button
            variant="outline"
            size="sm"
            onClick={handleStart}
            disabled={actionLoading !== null}
          >
            {actionLoading === 'start' ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
            )}
          </Button>
        )}

        <Button
          variant="ghost"
          size="sm"
          onClick={handleTrigger}
          disabled={actionLoading !== null}
        >
          {actionLoading === 'trigger' ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Zap className="h-4 w-4" />
          )}
        </Button>
      </div>
    )
  }

  // Full panel mode
  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Escalation Scheduler
          </span>
          <Badge
            variant={status?.is_running ? 'default' : 'secondary'}
            className={status?.is_running ? 'bg-green-500' : ''}
          >
            {status?.is_running ? 'Running' : 'Stopped'}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Status Info */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-muted-foreground">Check Interval:</span>
            <span className="ml-2 font-medium">{status?.check_interval_seconds}s</span>
          </div>
          <div>
            <span className="text-muted-foreground">Total Checks:</span>
            <span className="ml-2 font-medium">{status?.total_checks || 0}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Last Check:</span>
            <span className="ml-2 font-medium">{formatTime(status?.last_check_at ?? null)}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Next Check:</span>
            <span className="ml-2 font-medium">{formatTime(status?.next_check_at ?? null)}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Escalations:</span>
            <span className="ml-2 font-medium">{status?.total_escalations_triggered || 0}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Errors:</span>
            <span className={`ml-2 font-medium ${(status?.errors_count || 0) > 0 ? 'text-red-500' : ''}`}>
              {status?.errors_count || 0}
            </span>
          </div>
        </div>

        {/* Control Buttons */}
        <div className="flex items-center gap-2">
          {status?.is_running ? (
            <Button
              variant="destructive"
              size="sm"
              onClick={handleStop}
              disabled={actionLoading !== null}
              className="flex-1"
            >
              {actionLoading === 'stop' ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Square className="h-4 w-4 mr-2" />
              )}
              Stop
            </Button>
          ) : (
            <Button
              variant="default"
              size="sm"
              onClick={handleStart}
              disabled={actionLoading !== null}
              className="flex-1"
            >
              {actionLoading === 'start' ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Play className="h-4 w-4 mr-2" />
              )}
              Start
            </Button>
          )}

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleTrigger}
                  disabled={actionLoading !== null}
                >
                  {actionLoading === 'trigger' ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Zap className="h-4 w-4" />
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent>Trigger manual check</TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={openConfigDialog}
                  disabled={actionLoading !== null}
                >
                  <Settings className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Configure scheduler</TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={loadStatus}
                  disabled={actionLoading !== null}
                >
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Refresh status</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>

        {/* Warnings */}
        {(status?.errors_count || 0) > 0 && (
          <div className="flex items-center gap-2 p-2 bg-yellow-500/10 rounded-md text-sm text-yellow-600">
            <AlertTriangle className="h-4 w-4" />
            {status?.errors_count} errors occurred during checks
          </div>
        )}
      </CardContent>

      {/* Config Dialog */}
      <Dialog open={configDialogOpen} onOpenChange={setConfigDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Scheduler Configuration</DialogTitle>
            <DialogDescription>
              Configure the escalation scheduler settings.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Check Interval (seconds)</Label>
              <Input
                type="number"
                value={configInterval}
                onChange={(e) => setConfigInterval(parseInt(e.target.value) || 60)}
                min={10}
                max={3600}
              />
              <p className="text-xs text-muted-foreground">
                How often to check for pending escalations (10-3600 seconds)
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setConfigDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSaveConfig}
              disabled={actionLoading === 'config'}
            >
              {actionLoading === 'config' && (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              )}
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}
