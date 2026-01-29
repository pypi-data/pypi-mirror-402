/**
 * Sampling configuration component for large-scale drift detection.
 *
 * Allows users to configure sampling parameters for 100M+ row datasets.
 */

import { useIntlayer } from 'react-intlayer'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Clock, Database, Zap, AlertTriangle } from 'lucide-react'

export interface SamplingConfigData {
  enabled: boolean
  method: 'random' | 'stratified' | 'reservoir' | 'systematic'
  sampleSize: number | null
  confidenceLevel: number
  marginOfError: number
  earlyStopThreshold: number
  maxWorkers: number
  strataColumn?: string
}

interface SamplingEstimate {
  recommendedSize: number
  minSize: number
  maxSize: number
  estimatedTimeSeconds: number
  memoryMb: number
  speedupFactor: number
}

interface SamplingConfigProps {
  config: SamplingConfigData
  onChange: (config: SamplingConfigData) => void
  estimate?: SamplingEstimate | null
  populationSize?: number
  columns?: string[]
  isLargeDataset?: boolean
}

const SAMPLING_METHODS = [
  {
    value: 'random',
    label: 'Random Sampling',
    description: 'Simple random sampling without replacement',
  },
  {
    value: 'stratified',
    label: 'Stratified Sampling',
    description: 'Maintains proportions of categories',
  },
  {
    value: 'reservoir',
    label: 'Reservoir Sampling',
    description: 'Single-pass sampling for streaming data',
  },
  {
    value: 'systematic',
    label: 'Systematic Sampling',
    description: 'Evenly spaced sampling with random start',
  },
] as const

const CONFIDENCE_LEVELS = [
  { value: 0.9, label: '90%' },
  { value: 0.95, label: '95%' },
  { value: 0.99, label: '99%' },
]

export function SamplingConfig({
  config,
  onChange,
  estimate,
  populationSize,
  columns = [],
  isLargeDataset = false,
}: SamplingConfigProps) {
  const t = useIntlayer('driftMonitor')

  const updateConfig = (updates: Partial<SamplingConfigData>) => {
    onChange({ ...config, ...updates })
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

  const formatTime = (seconds: number) => {
    if (seconds < 60) {
      return `${seconds.toFixed(1)}s`
    }
    if (seconds < 3600) {
      return `${(seconds / 60).toFixed(1)}m`
    }
    return `${(seconds / 3600).toFixed(1)}h`
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-primary" />
              {t.sampling.title}
            </CardTitle>
            <CardDescription>{t.sampling.description}</CardDescription>
          </div>
          <Switch
            checked={config.enabled}
            onCheckedChange={(enabled) => updateConfig({ enabled })}
          />
        </div>
      </CardHeader>

      {config.enabled && (
        <CardContent className="space-y-6">
          {/* Performance Estimates */}
          {estimate && (
            <div className="grid grid-cols-3 gap-4 rounded-lg bg-muted/50 p-4">
              <div className="text-center">
                <Database className="mx-auto mb-1 h-4 w-4 text-muted-foreground" />
                <div className="text-lg font-semibold">
                  {formatNumber(estimate.recommendedSize)}
                </div>
                <div className="text-xs text-muted-foreground">
                  {t.sampling.sampleSize}
                </div>
              </div>
              <div className="text-center">
                <Clock className="mx-auto mb-1 h-4 w-4 text-muted-foreground" />
                <div className="text-lg font-semibold">
                  {formatTime(estimate.estimatedTimeSeconds)}
                </div>
                <div className="text-xs text-muted-foreground">
                  {t.sampling.estimatedTime}
                </div>
              </div>
              <div className="text-center">
                <Zap className="mx-auto mb-1 h-4 w-4 text-muted-foreground" />
                <div className="text-lg font-semibold">
                  {estimate.speedupFactor.toFixed(0)}x
                </div>
                <div className="text-xs text-muted-foreground">
                  {t.sampling.speedup}
                </div>
              </div>
            </div>
          )}

          {/* Sampling Method */}
          <div className="space-y-2">
            <Label>{t.sampling.method}</Label>
            <Select
              value={config.method}
              onValueChange={(value) =>
                updateConfig({ method: value as SamplingConfigData['method'] })
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SAMPLING_METHODS.map((method) => (
                  <SelectItem key={method.value} value={method.value}>
                    <div>
                      <div>{method.label}</div>
                      <div className="text-xs text-muted-foreground">
                        {method.description}
                      </div>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Strata Column (for stratified sampling) */}
          {config.method === 'stratified' && columns.length > 0 && (
            <div className="space-y-2">
              <Label>{t.sampling.strataColumn}</Label>
              <Select
                value={config.strataColumn || ''}
                onValueChange={(value) => updateConfig({ strataColumn: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select column for stratification" />
                </SelectTrigger>
                <SelectContent>
                  {columns.map((col) => (
                    <SelectItem key={col} value={col}>
                      {col}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Sample Size */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>{t.sampling.sampleSize}</Label>
              <div className="flex items-center gap-2">
                <Switch
                  checked={config.sampleSize === null}
                  onCheckedChange={(auto) =>
                    updateConfig({
                      sampleSize: auto ? null : estimate?.recommendedSize || 10000,
                    })
                  }
                />
                <span className="text-sm text-muted-foreground">Auto</span>
              </div>
            </div>
            {config.sampleSize !== null ? (
              <Input
                type="number"
                value={config.sampleSize}
                onChange={(e) =>
                  updateConfig({ sampleSize: parseInt(e.target.value) || 10000 })
                }
                min={100}
                max={estimate?.maxSize || 10000000}
              />
            ) : (
              <div className="flex items-center gap-2 rounded-md border bg-muted/30 px-3 py-2">
                <span className="text-sm text-muted-foreground">
                  {t.sampling.autoEstimate}:
                </span>
                <Badge variant="secondary">
                  {estimate ? formatNumber(estimate.recommendedSize) : '---'}
                </Badge>
              </div>
            )}
          </div>

          {/* Confidence Level */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>{t.sampling.confidenceLevel}</Label>
              <span className="text-sm font-medium">
                {(config.confidenceLevel * 100).toFixed(0)}%
              </span>
            </div>
            <Select
              value={config.confidenceLevel.toString()}
              onValueChange={(value) =>
                updateConfig({ confidenceLevel: parseFloat(value) })
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CONFIDENCE_LEVELS.map((level) => (
                  <SelectItem key={level.value} value={level.value.toString()}>
                    {level.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Margin of Error */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>{t.sampling.marginOfError}</Label>
              <span className="text-sm font-medium">
                {(config.marginOfError * 100).toFixed(0)}%
              </span>
            </div>
            <Slider
              value={[config.marginOfError]}
              onValueChange={([value]) => updateConfig({ marginOfError: value })}
              min={0.01}
              max={0.1}
              step={0.01}
            />
          </div>

          {/* Advanced Settings */}
          <div className="space-y-4 rounded-lg border p-4">
            <div className="text-sm font-medium">{t.sampling.advancedSettings}</div>

            {/* Early Stop Threshold */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="text-sm">{t.sampling.earlyStopThreshold}</Label>
                <span className="text-sm text-muted-foreground">
                  {(config.earlyStopThreshold * 100).toFixed(0)}%
                </span>
              </div>
              <Slider
                value={[config.earlyStopThreshold]}
                onValueChange={([value]) => updateConfig({ earlyStopThreshold: value })}
                min={0.1}
                max={1.0}
                step={0.1}
              />
              <p className="text-xs text-muted-foreground">
                {t.sampling.earlyStopDescription}
              </p>
            </div>

            {/* Max Workers */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="text-sm">{t.sampling.maxWorkers}</Label>
                <span className="text-sm text-muted-foreground">{config.maxWorkers}</span>
              </div>
              <Slider
                value={[config.maxWorkers]}
                onValueChange={([value]) => updateConfig({ maxWorkers: value })}
                min={1}
                max={16}
                step={1}
              />
            </div>
          </div>

          {/* Large Dataset Notice */}
          {isLargeDataset && populationSize && (
            <div className="flex items-start gap-2 rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-3">
              <AlertTriangle className="mt-0.5 h-4 w-4 text-yellow-500" />
              <div className="text-sm">
                <div className="font-medium text-yellow-600 dark:text-yellow-400">
                  {t.sampling.largeDatasetNotice}
                </div>
                <div className="text-muted-foreground">
                  {t.sampling.largeDatasetDescription.replace(
                    '{rows}',
                    formatNumber(populationSize)
                  )}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  )
}
