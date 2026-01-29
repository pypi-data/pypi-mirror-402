/**
 * Auto-Trigger Configuration Component.
 *
 * Allows configuration of automatic cross-alert triggering.
 */

import { useCallback, useEffect, useState } from 'react'
import { useIntlayer } from 'react-intlayer'
import { str } from '@/lib/intlayer-utils'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import { useToast } from '@/hooks/use-toast'
import { Loader2, Settings, Zap, AlertTriangle, Activity, Clock } from 'lucide-react'

const API_BASE = '/api/v1'

interface AutoTriggerThresholds {
  anomaly_rate_threshold: number
  anomaly_count_threshold: number
  drift_percentage_threshold: number
  drift_columns_threshold: number
}

interface AutoTriggerConfigData {
  enabled: boolean
  trigger_drift_on_anomaly: boolean
  trigger_anomaly_on_drift: boolean
  thresholds: AutoTriggerThresholds
  notify_on_correlation: boolean
  notification_channel_ids: string[] | null
  cooldown_seconds: number
}

interface AutoTriggerConfigProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  sourceId?: string | null
}

export function AutoTriggerConfig({ open, onOpenChange, sourceId }: AutoTriggerConfigProps) {
  const t = useIntlayer('crossAlerts')
  const common = useIntlayer('common')
  const { toast } = useToast()

  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [config, setConfig] = useState<AutoTriggerConfigData>({
    enabled: true,
    trigger_drift_on_anomaly: true,
    trigger_anomaly_on_drift: true,
    thresholds: {
      anomaly_rate_threshold: 0.1,
      anomaly_count_threshold: 10,
      drift_percentage_threshold: 10.0,
      drift_columns_threshold: 2,
    },
    notify_on_correlation: true,
    notification_channel_ids: null,
    cooldown_seconds: 300,
  })

  const loadConfig = useCallback(async () => {
    setIsLoading(true)
    try {
      const url = sourceId
        ? `${API_BASE}/cross-alerts/config?source_id=${sourceId}`
        : `${API_BASE}/cross-alerts/config`
      const response = await fetch(url)
      if (!response.ok) throw new Error('Failed to fetch config')
      const result = await response.json()
      setConfig({
        enabled: result.data.enabled ?? true,
        trigger_drift_on_anomaly: result.data.trigger_drift_on_anomaly ?? true,
        trigger_anomaly_on_drift: result.data.trigger_anomaly_on_drift ?? true,
        thresholds: result.data.thresholds ?? {
          anomaly_rate_threshold: 0.1,
          anomaly_count_threshold: 10,
          drift_percentage_threshold: 10.0,
          drift_columns_threshold: 2,
        },
        notify_on_correlation: result.data.notify_on_correlation ?? true,
        notification_channel_ids: result.data.notification_channel_ids ?? null,
        cooldown_seconds: result.data.cooldown_seconds ?? 300,
      })
    } catch {
      // Use defaults
    } finally {
      setIsLoading(false)
    }
  }, [sourceId])

  useEffect(() => {
    if (open) {
      loadConfig()
    }
  }, [open, loadConfig])

  const handleSave = async () => {
    setIsSaving(true)
    try {
      const response = await fetch(`${API_BASE}/cross-alerts/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_id: sourceId,
          ...config,
        }),
      })
      if (!response.ok) throw new Error('Failed to save config')

      toast({ title: str(t.messages.configSaved) })
      onOpenChange(false)
    } catch {
      toast({
        title: str(common.error),
        description: 'Failed to save configuration',
        variant: 'destructive',
      })
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            {t.sections.autoTriggerConfig}
          </DialogTitle>
          <DialogDescription>
            {sourceId
              ? `Configure auto-triggers for this source`
              : `Configure global auto-trigger settings`}
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="space-y-6">
            {/* Main toggle */}
            <div className="flex items-center justify-between rounded-lg border p-4">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <Zap className="h-4 w-4 text-primary" />
                  <Label className="font-medium">{t.config.enabled}</Label>
                </div>
                <p className="text-sm text-muted-foreground">
                  Enable automatic cross-feature triggering
                </p>
              </div>
              <Switch
                checked={config.enabled}
                onCheckedChange={(checked) => setConfig({ ...config, enabled: checked })}
              />
            </div>

            {/* Trigger directions */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Trigger Directions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-orange-500" />
                    <Label>{t.config.triggerDriftOnAnomaly}</Label>
                  </div>
                  <Switch
                    checked={config.trigger_drift_on_anomaly}
                    onCheckedChange={(checked) =>
                      setConfig({ ...config, trigger_drift_on_anomaly: checked })
                    }
                    disabled={!config.enabled}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Activity className="h-4 w-4 text-blue-500" />
                    <Label>{t.config.triggerAnomalyOnDrift}</Label>
                  </div>
                  <Switch
                    checked={config.trigger_anomaly_on_drift}
                    onCheckedChange={(checked) =>
                      setConfig({ ...config, trigger_anomaly_on_drift: checked })
                    }
                    disabled={!config.enabled}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Thresholds */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">{t.config.thresholds.title}</CardTitle>
                <CardDescription>
                  Set minimum thresholds for triggering cross-checks
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Anomaly rate threshold */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label>{t.config.thresholds.anomalyRateThreshold}</Label>
                    <span className="text-sm font-medium">
                      {(config.thresholds.anomaly_rate_threshold * 100).toFixed(0)}%
                    </span>
                  </div>
                  <Slider
                    value={[config.thresholds.anomaly_rate_threshold * 100]}
                    onValueChange={([value]) =>
                      setConfig({
                        ...config,
                        thresholds: {
                          ...config.thresholds,
                          anomaly_rate_threshold: value / 100,
                        },
                      })
                    }
                    min={1}
                    max={50}
                    step={1}
                    disabled={!config.enabled}
                  />
                </div>

                {/* Anomaly count threshold */}
                <div className="space-y-2">
                  <Label>{t.config.thresholds.anomalyCountThreshold}</Label>
                  <Input
                    type="number"
                    min={1}
                    value={config.thresholds.anomaly_count_threshold}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        thresholds: {
                          ...config.thresholds,
                          anomaly_count_threshold: parseInt(e.target.value) || 1,
                        },
                      })
                    }
                    disabled={!config.enabled}
                  />
                </div>

                {/* Drift percentage threshold */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label>{t.config.thresholds.driftPercentageThreshold}</Label>
                    <span className="text-sm font-medium">
                      {config.thresholds.drift_percentage_threshold.toFixed(0)}%
                    </span>
                  </div>
                  <Slider
                    value={[config.thresholds.drift_percentage_threshold]}
                    onValueChange={([value]) =>
                      setConfig({
                        ...config,
                        thresholds: {
                          ...config.thresholds,
                          drift_percentage_threshold: value,
                        },
                      })
                    }
                    min={5}
                    max={50}
                    step={1}
                    disabled={!config.enabled}
                  />
                </div>

                {/* Drift columns threshold */}
                <div className="space-y-2">
                  <Label>{t.config.thresholds.driftColumnsThreshold}</Label>
                  <Input
                    type="number"
                    min={1}
                    value={config.thresholds.drift_columns_threshold}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        thresholds: {
                          ...config.thresholds,
                          drift_columns_threshold: parseInt(e.target.value) || 1,
                        },
                      })
                    }
                    disabled={!config.enabled}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Other settings */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Additional Settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label>{t.config.notifyOnCorrelation}</Label>
                  <Switch
                    checked={config.notify_on_correlation}
                    onCheckedChange={(checked) =>
                      setConfig({ ...config, notify_on_correlation: checked })
                    }
                    disabled={!config.enabled}
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <Label>{t.config.cooldownSeconds}</Label>
                  </div>
                  <Input
                    type="number"
                    min={0}
                    value={config.cooldown_seconds}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        cooldown_seconds: parseInt(e.target.value) || 0,
                      })
                    }
                    disabled={!config.enabled}
                  />
                  <p className="text-xs text-muted-foreground">
                    Minimum time between auto-triggered checks (to prevent alert storms)
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {common.cancel}
          </Button>
          <Button onClick={handleSave} disabled={isLoading || isSaving}>
            {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {t.actions.saveConfig}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

/**
 * Inline config panel for embedding in pages.
 */
interface AutoTriggerConfigPanelProps {
  sourceId?: string | null
}

export function AutoTriggerConfigPanel({ sourceId }: AutoTriggerConfigPanelProps) {
  const t = useIntlayer('crossAlerts')
  const [showConfig, setShowConfig] = useState(false)

  return (
    <>
      <Button variant="outline" size="sm" onClick={() => setShowConfig(true)}>
        <Settings className="h-4 w-4 mr-2" />
        {t.actions.configure}
      </Button>
      <AutoTriggerConfig open={showConfig} onOpenChange={setShowConfig} sourceId={sourceId} />
    </>
  )
}
