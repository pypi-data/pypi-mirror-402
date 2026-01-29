/**
 * Register model dialog component.
 *
 * Form for registering new ML models for monitoring.
 */

import { useState, useCallback } from 'react'
import { useIntlayer } from 'react-intlayer'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Slider } from '@/components/ui/slider'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import { Loader2, Cpu, Settings, Bell } from 'lucide-react'

interface RegisterModelFormData {
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
}

interface RegisterModelDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSubmit: (data: RegisterModelFormData) => Promise<void>
  initialData?: Partial<RegisterModelFormData>
  isEditing?: boolean
}

const DEFAULT_FORM_DATA: RegisterModelFormData = {
  name: '',
  version: '1.0.0',
  description: '',
  config: {
    enable_drift_detection: true,
    enable_quality_metrics: true,
    enable_performance_metrics: true,
    sample_rate: 1.0,
    drift_threshold: 0.1,
    drift_window_size: 1000,
  },
  metadata: {},
}

export function RegisterModelDialog({
  open,
  onOpenChange,
  onSubmit,
  initialData,
  isEditing = false,
}: RegisterModelDialogProps) {
  const t = useIntlayer('modelMonitoring')
  const common = useIntlayer('common')

  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formData, setFormData] = useState<RegisterModelFormData>({
    ...DEFAULT_FORM_DATA,
    ...initialData,
    config: { ...DEFAULT_FORM_DATA.config, ...initialData?.config },
  })
  const [metadataKey, setMetadataKey] = useState('')
  const [metadataValue, setMetadataValue] = useState('')

  const handleSubmit = useCallback(async () => {
    setIsSubmitting(true)
    try {
      await onSubmit(formData)
      onOpenChange(false)
      // Reset form after successful submission
      setFormData(DEFAULT_FORM_DATA)
    } finally {
      setIsSubmitting(false)
    }
  }, [formData, onSubmit, onOpenChange])

  const handleAddMetadata = useCallback(() => {
    if (metadataKey.trim() && metadataValue.trim()) {
      setFormData((prev) => ({
        ...prev,
        metadata: { ...prev.metadata, [metadataKey.trim()]: metadataValue.trim() },
      }))
      setMetadataKey('')
      setMetadataValue('')
    }
  }, [metadataKey, metadataValue])

  const handleRemoveMetadata = useCallback((key: string) => {
    setFormData((prev) => {
      const { [key]: _, ...rest } = prev.metadata
      return { ...prev, metadata: rest }
    })
  }, [])

  const updateConfig = useCallback(
    (key: keyof RegisterModelFormData['config'], value: boolean | number) => {
      setFormData((prev) => ({
        ...prev,
        config: { ...prev.config, [key]: value },
      }))
    },
    []
  )

  const isValid = formData.name.trim() !== '' && formData.version.trim() !== ''

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Cpu className="h-5 w-5 text-primary" />
            {isEditing ? t.models.editModel : t.models.registerModel}
          </DialogTitle>
          <DialogDescription>
            Register a new ML model to start monitoring its performance, data quality, and drift.
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="basic" className="mt-4">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="basic" className="gap-2">
              <Cpu className="h-4 w-4" />
              Basic Info
            </TabsTrigger>
            <TabsTrigger value="config" className="gap-2">
              <Settings className="h-4 w-4" />
              Configuration
            </TabsTrigger>
            <TabsTrigger value="alerts" className="gap-2">
              <Bell className="h-4 w-4" />
              Alerts
            </TabsTrigger>
          </TabsList>

          {/* Basic Info Tab */}
          <TabsContent value="basic" className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">{t.models.name} *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData((prev) => ({ ...prev, name: e.target.value }))}
                placeholder="fraud-detection-model"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="version">{t.models.version} *</Label>
              <Input
                id="version"
                value={formData.version}
                onChange={(e) => setFormData((prev) => ({ ...prev, version: e.target.value }))}
                placeholder="1.0.0"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData((prev) => ({ ...prev, description: e.target.value }))}
                placeholder="ML model for detecting fraudulent transactions..."
                rows={3}
              />
            </div>

            {/* Metadata */}
            <div className="space-y-2">
              <Label>Metadata</Label>
              <div className="flex gap-2">
                <Input
                  placeholder="Key"
                  value={metadataKey}
                  onChange={(e) => setMetadataKey(e.target.value)}
                  className="flex-1"
                />
                <Input
                  placeholder="Value"
                  value={metadataValue}
                  onChange={(e) => setMetadataValue(e.target.value)}
                  className="flex-1"
                />
                <Button type="button" variant="outline" onClick={handleAddMetadata}>
                  Add
                </Button>
              </div>
              {Object.keys(formData.metadata).length > 0 && (
                <div className="mt-2 space-y-1">
                  {Object.entries(formData.metadata).map(([key, value]) => (
                    <div
                      key={key}
                      className="flex items-center justify-between rounded-md border px-3 py-1.5 text-sm"
                    >
                      <span>
                        <span className="font-medium">{key}</span>: {value}
                      </span>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemoveMetadata(key)}
                      >
                        Remove
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </TabsContent>

          {/* Configuration Tab */}
          <TabsContent value="config" className="space-y-6 py-4">
            <div className="space-y-4">
              <h4 className="text-sm font-medium">{t.config.title}</h4>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="enable-drift">{t.config.enableDrift}</Label>
                  <p className="text-xs text-muted-foreground">
                    Monitor input/output distribution changes
                  </p>
                </div>
                <Switch
                  id="enable-drift"
                  checked={formData.config.enable_drift_detection}
                  onCheckedChange={(checked) => updateConfig('enable_drift_detection', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="enable-quality">{t.config.enableQuality}</Label>
                  <p className="text-xs text-muted-foreground">
                    Track null rates, type violations, etc.
                  </p>
                </div>
                <Switch
                  id="enable-quality"
                  checked={formData.config.enable_quality_metrics}
                  onCheckedChange={(checked) => updateConfig('enable_quality_metrics', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="enable-perf">{t.config.enablePerformance}</Label>
                  <p className="text-xs text-muted-foreground">
                    Track latency, throughput, error rates
                  </p>
                </div>
                <Switch
                  id="enable-perf"
                  checked={formData.config.enable_performance_metrics}
                  onCheckedChange={(checked) => updateConfig('enable_performance_metrics', checked)}
                />
              </div>
            </div>

            <div className="space-y-4 rounded-lg border p-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>{t.config.sampleRate}</Label>
                  <span className="text-sm text-muted-foreground">
                    {(formData.config.sample_rate * 100).toFixed(0)}%
                  </span>
                </div>
                <Slider
                  value={[formData.config.sample_rate]}
                  onValueChange={([value]) => updateConfig('sample_rate', value)}
                  min={0.01}
                  max={1}
                  step={0.01}
                />
                <p className="text-xs text-muted-foreground">
                  Percentage of predictions to sample for monitoring
                </p>
              </div>

              {formData.config.enable_drift_detection && (
                <>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label>{t.config.driftThreshold}</Label>
                      <span className="text-sm text-muted-foreground">
                        {(formData.config.drift_threshold * 100).toFixed(0)}%
                      </span>
                    </div>
                    <Slider
                      value={[formData.config.drift_threshold]}
                      onValueChange={([value]) => updateConfig('drift_threshold', value)}
                      min={0.01}
                      max={0.5}
                      step={0.01}
                    />
                    <p className="text-xs text-muted-foreground">
                      Threshold for triggering drift alerts
                    </p>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label>{t.config.driftWindowSize}</Label>
                      <span className="text-sm text-muted-foreground">
                        {formData.config.drift_window_size.toLocaleString()} samples
                      </span>
                    </div>
                    <Slider
                      value={[formData.config.drift_window_size]}
                      onValueChange={([value]) => updateConfig('drift_window_size', value)}
                      min={100}
                      max={10000}
                      step={100}
                    />
                    <p className="text-xs text-muted-foreground">
                      Number of samples to use for drift comparison
                    </p>
                  </div>
                </>
              )}
            </div>
          </TabsContent>

          {/* Alerts Tab */}
          <TabsContent value="alerts" className="space-y-4 py-4">
            <div className="rounded-lg border p-4">
              <h4 className="text-sm font-medium mb-4">Default Alert Rules</h4>
              <p className="text-sm text-muted-foreground mb-4">
                The following default alert rules will be created for this model. You can customize
                them after registration.
              </p>
              <div className="space-y-3">
                <div className="flex items-start gap-3 rounded-md border p-3">
                  <div className="h-2 w-2 rounded-full bg-red-500 mt-1.5" />
                  <div>
                    <p className="text-sm font-medium">High Latency Alert</p>
                    <p className="text-xs text-muted-foreground">
                      Triggers when P95 latency exceeds 500ms
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3 rounded-md border p-3">
                  <div className="h-2 w-2 rounded-full bg-orange-500 mt-1.5" />
                  <div>
                    <p className="text-sm font-medium">Drift Detection Alert</p>
                    <p className="text-xs text-muted-foreground">
                      Triggers when drift score exceeds configured threshold
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3 rounded-md border p-3">
                  <div className="h-2 w-2 rounded-full bg-yellow-500 mt-1.5" />
                  <div>
                    <p className="text-sm font-medium">Error Rate Alert</p>
                    <p className="text-xs text-muted-foreground">
                      Triggers when error rate exceeds 5%
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {common.cancel}
          </Button>
          <Button onClick={handleSubmit} disabled={!isValid || isSubmitting}>
            {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isEditing ? common.save : t.models.registerModel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
