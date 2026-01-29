/**
 * Drift Preview Component.
 *
 * Panel for configuring and running drift comparison preview
 * before creating a monitor.
 */

import { useCallback, useState } from 'react'
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
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Loader2, Eye, AlertTriangle, CheckCircle2 } from 'lucide-react'
import { DriftPreviewResults } from './DriftPreviewResults'
import type { Source } from '@/api/client'

// Preview result type matching backend schema
export interface DriftPreviewData {
  baseline_source_id: string
  current_source_id: string
  baseline_source_name: string | null
  current_source_name: string | null
  has_drift: boolean
  has_high_drift: boolean
  total_columns: number
  drifted_columns: number
  drift_percentage: number
  baseline_rows: number
  current_rows: number
  method: string
  threshold: number
  columns: ColumnPreviewResult[]
  most_affected: string[]
}

export interface ColumnPreviewResult {
  column: string
  dtype: string
  drifted: boolean
  level: string
  method: string
  statistic: number | null
  p_value: number | null
  baseline_stats: Record<string, number>
  current_stats: Record<string, number>
  baseline_distribution: DistributionData | null
  current_distribution: DistributionData | null
}

export interface DistributionData {
  values: number[]
  bins: string[]
  counts: number[]
  percentages: number[]
}

interface DriftPreviewProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  sources: Source[]
  onCreateMonitor?: (data: {
    baseline_source_id: string
    current_source_id: string
    method: string
    threshold: number
  }) => void
}

const METHODS = [
  { label: 'Auto (recommended)', value: 'auto' },
  { label: 'Kolmogorov-Smirnov', value: 'ks' },
  { label: 'Population Stability Index', value: 'psi' },
  { label: 'Chi-Square', value: 'chi2' },
  { label: 'Jensen-Shannon', value: 'js' },
  { label: 'Wasserstein', value: 'wasserstein' },
]

const API_BASE = '/api/v1'

async function previewDrift(data: {
  baseline_source_id: string
  current_source_id: string
  method: string
  threshold: number
  columns?: string[]
}): Promise<DriftPreviewData> {
  const response = await fetch(`${API_BASE}/drift/preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Preview failed' }))
    throw new Error(error.detail || 'Preview failed')
  }
  const result = await response.json()
  return result.data
}

export function DriftPreview({
  open,
  onOpenChange,
  sources,
  onCreateMonitor,
}: DriftPreviewProps) {
  const t = useIntlayer('driftMonitor')
  const common = useIntlayer('common')

  // Form state
  const [baselineSourceId, setBaselineSourceId] = useState('')
  const [currentSourceId, setCurrentSourceId] = useState('')
  const [method, setMethod] = useState('auto')
  const [threshold, setThreshold] = useState(0.05)

  // Preview state
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [previewResult, setPreviewResult] = useState<DriftPreviewData | null>(null)

  const isFormValid =
    baselineSourceId !== '' &&
    currentSourceId !== '' &&
    baselineSourceId !== currentSourceId

  const handleRunPreview = useCallback(async () => {
    if (!isFormValid) return

    setIsLoading(true)
    setError(null)
    setPreviewResult(null)

    try {
      const result = await previewDrift({
        baseline_source_id: baselineSourceId,
        current_source_id: currentSourceId,
        method,
        threshold,
      })
      setPreviewResult(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Preview failed')
    } finally {
      setIsLoading(false)
    }
  }, [baselineSourceId, currentSourceId, method, threshold, isFormValid])

  const handleCreateMonitor = useCallback(() => {
    if (!previewResult || !onCreateMonitor) return

    onCreateMonitor({
      baseline_source_id: baselineSourceId,
      current_source_id: currentSourceId,
      method,
      threshold,
    })

    // Close the preview dialog
    onOpenChange(false)
  }, [previewResult, onCreateMonitor, baselineSourceId, currentSourceId, method, threshold, onOpenChange])

  const handleReset = useCallback(() => {
    setPreviewResult(null)
    setError(null)
  }, [])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Eye className="h-5 w-5" />
            {t.preview?.title ?? 'Preview Drift'}
          </DialogTitle>
          <DialogDescription>
            {t.preview?.description ?? 'Compare two data sources to preview drift results before creating a monitor'}
          </DialogDescription>
        </DialogHeader>

        {/* Configuration Form */}
        {!previewResult && (
          <div className="space-y-4 py-4">
            {/* Baseline Source */}
            <div className="space-y-2">
              <Label>{t.monitor.baselineSource}</Label>
              <Select value={baselineSourceId} onValueChange={setBaselineSourceId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select baseline source" />
                </SelectTrigger>
                <SelectContent>
                  {sources.map((source) => (
                    <SelectItem key={source.id} value={source.id}>
                      {source.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Current Source */}
            <div className="space-y-2">
              <Label>{t.monitor.currentSource}</Label>
              <Select value={currentSourceId} onValueChange={setCurrentSourceId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select current source" />
                </SelectTrigger>
                <SelectContent>
                  {sources.map((source) => (
                    <SelectItem key={source.id} value={source.id}>
                      {source.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {baselineSourceId && currentSourceId && baselineSourceId === currentSourceId && (
                <p className="text-sm text-destructive flex items-center gap-1">
                  <AlertTriangle className="h-4 w-4" />
                  {t.preview?.sameSourceWarning ?? 'Baseline and current source must be different'}
                </p>
              )}
            </div>

            {/* Method */}
            <div className="space-y-2">
              <Label>{t.monitor.method}</Label>
              <Select value={method} onValueChange={setMethod}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {METHODS.map((m) => (
                    <SelectItem key={m.value} value={m.value}>
                      {m.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Threshold */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>{t.monitor.threshold}</Label>
                <span className="text-sm text-muted-foreground">
                  {(threshold * 100).toFixed(0)}%
                </span>
              </div>
              <Slider
                value={[threshold]}
                onValueChange={([value]) => setThreshold(value)}
                min={0.01}
                max={0.5}
                step={0.01}
              />
            </div>

            {/* Error Display */}
            {error && (
              <div className="rounded-lg border border-destructive bg-destructive/10 p-3">
                <p className="text-sm text-destructive flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  {error}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Preview Results */}
        {previewResult && (
          <DriftPreviewResults
            data={previewResult}
            onReset={handleReset}
          />
        )}

        <DialogFooter className="flex-col sm:flex-row gap-2">
          {!previewResult ? (
            <>
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                {common.cancel}
              </Button>
              <Button
                onClick={handleRunPreview}
                disabled={!isFormValid || isLoading}
              >
                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                <Eye className="mr-2 h-4 w-4" />
                {t.preview?.runPreview ?? 'Run Preview'}
              </Button>
            </>
          ) : (
            <>
              <Button variant="outline" onClick={handleReset}>
                {t.preview?.backToConfig ?? 'Back to Configuration'}
              </Button>
              {onCreateMonitor && (
                <Button onClick={handleCreateMonitor}>
                  <CheckCircle2 className="mr-2 h-4 w-4" />
                  {t.monitor.createMonitor}
                </Button>
              )}
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
