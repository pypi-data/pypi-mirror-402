/**
 * Maintenance Settings component
 *
 * Provides UI for configuring retention policies and triggering manual cleanup.
 * Displays maintenance status, cache statistics, and allows manual operations.
 */

import { useState, useEffect, useCallback } from 'react'
import {
  Settings,
  Trash2,
  Database,
  Clock,
  Play,
  RefreshCw,
  Loader2,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react'
import { useIntlayer } from '@/providers'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { useToast } from '@/hooks/use-toast'
import { str } from '@/lib/intlayer-utils'
import {
  getRetentionPolicy,
  updateRetentionPolicy,
  getMaintenanceStatus,
  triggerCleanup,
  runVacuum,
  getCacheStats,
  clearCache,
  type RetentionPolicyConfig,
  type MaintenanceStatus,
  type CacheStats,
} from '@/api/client'

export interface MaintenanceSettingsProps {
  className?: string
}

export function MaintenanceSettings({ className }: MaintenanceSettingsProps) {
  const maintenance = useIntlayer('maintenance')
  const common = useIntlayer('common')
  const { toast } = useToast()

  // State
  const [config, setConfig] = useState<RetentionPolicyConfig | null>(null)
  const [status, setStatus] = useState<MaintenanceStatus | null>(null)
  const [cacheStats, setCacheStats] = useState<CacheStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [isCleanupRunning, setIsCleanupRunning] = useState(false)
  const [isVacuumRunning, setIsVacuumRunning] = useState(false)
  const [isClearingCache, setIsClearingCache] = useState(false)

  // Load data
  const loadData = useCallback(async () => {
    setIsLoading(true)
    try {
      const [retentionConfig, maintenanceStatus, cache] = await Promise.all([
        getRetentionPolicy(),
        getMaintenanceStatus(),
        getCacheStats(),
      ])
      setConfig(retentionConfig)
      setStatus(maintenanceStatus)
      setCacheStats(cache)
    } catch (error) {
      console.error('Failed to load maintenance data:', error)
      toast({
        title: str(common.error),
        description: str(maintenance.loadFailed),
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }, [toast, common, maintenance])

  useEffect(() => {
    loadData()
  }, [loadData])

  // Save retention policy
  const handleSave = async () => {
    if (!config) return
    setIsSaving(true)
    try {
      const updated = await updateRetentionPolicy(config)
      setConfig(updated)
      toast({
        title: str(common.success),
        description: str(maintenance.configSaved),
      })
    } catch (error) {
      console.error('Failed to save retention policy:', error)
      toast({
        title: str(common.error),
        description: str(maintenance.saveFailed),
        variant: 'destructive',
      })
    } finally {
      setIsSaving(false)
    }
  }

  // Trigger cleanup
  const handleCleanup = async () => {
    setIsCleanupRunning(true)
    try {
      const report = await triggerCleanup({ run_vacuum: config?.run_vacuum })
      toast({
        title: str(common.success),
        description: `${str(maintenance.cleanupComplete)} ${report.total_deleted} ${str(maintenance.recordsDeleted)}`,
      })
      // Refresh status
      const newStatus = await getMaintenanceStatus()
      setStatus(newStatus)
    } catch (error) {
      console.error('Failed to run cleanup:', error)
      toast({
        title: str(common.error),
        description: str(maintenance.cleanupFailed),
        variant: 'destructive',
      })
    } finally {
      setIsCleanupRunning(false)
    }
  }

  // Run vacuum
  const handleVacuum = async () => {
    setIsVacuumRunning(true)
    try {
      await runVacuum()
      toast({
        title: str(common.success),
        description: str(maintenance.vacuumComplete),
      })
    } catch (error) {
      console.error('Failed to run vacuum:', error)
      toast({
        title: str(common.error),
        description: str(maintenance.vacuumFailed),
        variant: 'destructive',
      })
    } finally {
      setIsVacuumRunning(false)
    }
  }

  // Clear cache
  const handleClearCache = async () => {
    setIsClearingCache(true)
    try {
      const newStats = await clearCache()
      setCacheStats(newStats)
      toast({
        title: str(common.success),
        description: str(maintenance.cacheCleared),
      })
    } catch (error) {
      console.error('Failed to clear cache:', error)
      toast({
        title: str(common.error),
        description: str(maintenance.cacheClearFailed),
        variant: 'destructive',
      })
    } finally {
      setIsClearingCache(false)
    }
  }

  // Update config field
  const updateConfig = <K extends keyof RetentionPolicyConfig>(
    field: K,
    value: RetentionPolicyConfig[K]
  ) => {
    if (!config) return
    setConfig({ ...config, [field]: value })
  }

  if (isLoading) {
    return (
      <div className={`flex items-center justify-center py-12 ${className}`}>
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Maintenance Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            {maintenance.statusTitle}
          </CardTitle>
          <CardDescription>{maintenance.statusDescription}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div className="flex items-center gap-2">
              {status?.enabled ? (
                <CheckCircle2 className="h-4 w-4 text-green-500" />
              ) : (
                <AlertCircle className="h-4 w-4 text-yellow-500" />
              )}
              <span className="text-sm text-muted-foreground">
                {maintenance.autoMaintenance}:{' '}
                <span className="font-medium text-foreground">
                  {status?.enabled ? str(common.enabled) : str(common.disabled)}
                </span>
              </span>
            </div>
            <div className="text-sm text-muted-foreground">
              {maintenance.lastRun}:{' '}
              <span className="font-medium text-foreground">
                {status?.last_run_at
                  ? new Date(status.last_run_at).toLocaleString()
                  : str(common.never)}
              </span>
            </div>
            <div className="text-sm text-muted-foreground">
              {maintenance.nextRun}:{' '}
              <span className="font-medium text-foreground">
                {status?.next_scheduled_at
                  ? new Date(status.next_scheduled_at).toLocaleString()
                  : '-'}
              </span>
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleCleanup}
            disabled={isCleanupRunning}
          >
            {isCleanupRunning ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Play className="mr-2 h-4 w-4" />
            )}
            {maintenance.runCleanup}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleVacuum}
            disabled={isVacuumRunning}
          >
            {isVacuumRunning ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Database className="mr-2 h-4 w-4" />
            )}
            {maintenance.runVacuum}
          </Button>
        </CardFooter>
      </Card>

      {/* Retention Policy */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            {maintenance.retentionTitle}
          </CardTitle>
          <CardDescription>{maintenance.retentionDescription}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="enabled">{maintenance.enableAutoMaintenance}</Label>
              <p className="text-sm text-muted-foreground">
                {maintenance.enableAutoMaintenanceDescription}
              </p>
            </div>
            <Switch
              id="enabled"
              checked={config?.enabled ?? false}
              onCheckedChange={(checked) => updateConfig('enabled', checked)}
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="validation_retention_days">
                {maintenance.validationRetentionDays}
              </Label>
              <Input
                id="validation_retention_days"
                type="number"
                min={1}
                max={365}
                value={config?.validation_retention_days ?? 90}
                onChange={(e) =>
                  updateConfig('validation_retention_days', parseInt(e.target.value) || 90)
                }
              />
              <p className="text-xs text-muted-foreground">
                {maintenance.validationRetentionDaysDescription}
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="profile_keep_per_source">
                {maintenance.profileKeepPerSource}
              </Label>
              <Input
                id="profile_keep_per_source"
                type="number"
                min={1}
                max={100}
                value={config?.profile_keep_per_source ?? 5}
                onChange={(e) =>
                  updateConfig('profile_keep_per_source', parseInt(e.target.value) || 5)
                }
              />
              <p className="text-xs text-muted-foreground">
                {maintenance.profileKeepPerSourceDescription}
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="notification_log_retention_days">
                {maintenance.notificationLogRetentionDays}
              </Label>
              <Input
                id="notification_log_retention_days"
                type="number"
                min={1}
                max={365}
                value={config?.notification_log_retention_days ?? 30}
                onChange={(e) =>
                  updateConfig(
                    'notification_log_retention_days',
                    parseInt(e.target.value) || 30
                  )
                }
              />
              <p className="text-xs text-muted-foreground">
                {maintenance.notificationLogRetentionDaysDescription}
              </p>
            </div>

            <div className="flex items-center justify-between space-y-0 pt-6">
              <div className="space-y-0.5">
                <Label htmlFor="run_vacuum">{maintenance.runVacuumOnCleanup}</Label>
                <p className="text-xs text-muted-foreground">
                  {maintenance.runVacuumOnCleanupDescription}
                </p>
              </div>
              <Switch
                id="run_vacuum"
                checked={config?.run_vacuum ?? false}
                onCheckedChange={(checked) => updateConfig('run_vacuum', checked)}
              />
            </div>
          </div>
        </CardContent>
        <CardFooter>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : null}
            {isSaving ? str(common.saving) : str(common.save)}
          </Button>
        </CardFooter>
      </Card>

      {/* Cache Statistics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            {maintenance.cacheTitle}
          </CardTitle>
          <CardDescription>{maintenance.cacheDescription}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="text-center">
              <p className="text-2xl font-bold">{cacheStats?.total_entries ?? 0}</p>
              <p className="text-sm text-muted-foreground">{maintenance.totalEntries}</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">
                {cacheStats?.valid_entries ?? 0}
              </p>
              <p className="text-sm text-muted-foreground">{maintenance.validEntries}</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-yellow-600">
                {cacheStats?.expired_entries ?? 0}
              </p>
              <p className="text-sm text-muted-foreground">{maintenance.expiredEntries}</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-primary">
                {cacheStats?.hit_rate != null
                  ? `${(cacheStats.hit_rate * 100).toFixed(1)}%`
                  : '-'}
              </p>
              <p className="text-sm text-muted-foreground">{maintenance.hitRate}</p>
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            disabled={isLoading}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            {common.refresh}
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={handleClearCache}
            disabled={isClearingCache}
          >
            {isClearingCache ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Trash2 className="mr-2 h-4 w-4" />
            )}
            {maintenance.clearCache}
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}

export default MaintenanceSettings
