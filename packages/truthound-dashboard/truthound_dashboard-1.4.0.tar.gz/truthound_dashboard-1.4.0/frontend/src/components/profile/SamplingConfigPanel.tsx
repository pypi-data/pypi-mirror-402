/**
 * SamplingConfigPanel Component
 *
 * Provides UI for configuring sampling strategies for data profiling.
 * Supports 8 sampling strategies with advanced options like confidence level,
 * margin of error, stratification, and reproducibility settings.
 */
import { useIntlayer } from 'react-intlayer'
import { Info } from 'lucide-react'

import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Slider } from '@/components/ui/slider'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { str } from '@/lib/intlayer-utils'

// Sampling strategy types
export type SamplingStrategy =
  | 'none'
  | 'head'
  | 'random'
  | 'systematic'
  | 'stratified'
  | 'reservoir'
  | 'adaptive'
  | 'hash'

export interface SamplingConfig {
  strategy: SamplingStrategy
  sampleSize: number | null
  confidenceLevel: number
  marginOfError: number
  strataColumn: string | null
  seed: number | null
}

interface SamplingConfigPanelProps {
  config: SamplingConfig
  onChange: (config: SamplingConfig) => void
  columns?: string[]
  disabled?: boolean
}

const DEFAULT_CONFIG: SamplingConfig = {
  strategy: 'adaptive',
  sampleSize: null,
  confidenceLevel: 0.95,
  marginOfError: 0.03,
  strataColumn: null,
  seed: null,
}

// Strategy labels and descriptions
const STRATEGY_LABELS: Record<SamplingStrategy, string> = {
  none: 'None (Profile All Data)',
  head: 'Head (First N Rows)',
  random: 'Random Sampling',
  systematic: 'Systematic (Every Nth Row)',
  stratified: 'Stratified (Maintain Distribution)',
  reservoir: 'Reservoir (Streaming)',
  adaptive: 'Adaptive (Auto-Select)',
  hash: 'Hash (Deterministic)',
}

const STRATEGY_DESCRIPTIONS: Record<SamplingStrategy, string> = {
  none: 'Profile all rows. Best for small datasets (<100K rows).',
  head: 'Use first N rows. Fast but may not represent full distribution.',
  random: 'Random selection of rows. Good general-purpose strategy.',
  systematic: 'Select every Nth row. Good for ordered datasets.',
  stratified: 'Maintain category distribution. Best for categorical data.',
  reservoir: 'Single-pass streaming algorithm. Good for very large datasets.',
  adaptive: 'Automatically selects best strategy based on data characteristics.',
  hash: 'Deterministic selection using hash. Reproducible results.',
}

export function SamplingConfigPanel({
  config,
  onChange,
  columns = [],
  disabled = false,
}: SamplingConfigPanelProps) {
  const t = useIntlayer('profiler')

  const strategies: SamplingStrategy[] = [
    'none',
    'head',
    'random',
    'systematic',
    'stratified',
    'reservoir',
    'adaptive',
    'hash',
  ]

  const handleChange = <K extends keyof SamplingConfig>(
    key: K,
    value: SamplingConfig[K]
  ) => {
    onChange({ ...config, [key]: value })
  }

  const showSampleSizeInput = config.strategy !== 'none'
  const showConfidenceSettings =
    config.strategy === 'random' ||
    config.strategy === 'adaptive' ||
    config.strategy === 'stratified'
  const showStrataColumn = config.strategy === 'stratified'
  const showSeedInput =
    config.strategy === 'random' ||
    config.strategy === 'hash' ||
    config.strategy === 'stratified'

  // Type-safe string extraction helper
  const safeStr = (value: unknown): string => {
    if (value === undefined || value === null) return ''
    if (typeof value === 'string') return value
    // Cast to the type str() accepts and let it handle extraction
    return str(value as Parameters<typeof str>[0])
  }

  // Helper to get strategy label
  const getStrategyLabel = (strategy: SamplingStrategy): string => {
    try {
      const strategies = (t as Record<string, unknown>).strategies as Record<string, unknown> | undefined
      if (strategies && strategy in strategies) {
        return safeStr(strategies[strategy])
      }
    } catch {
      // Fallback on error
    }
    return STRATEGY_LABELS[strategy]
  }

  // Helper to get strategy description
  const getStrategyDescription = (strategy: SamplingStrategy): string => {
    try {
      const descriptions = (t as Record<string, unknown>).strategyDescriptions as Record<string, unknown> | undefined
      if (descriptions && strategy in descriptions) {
        return safeStr(descriptions[strategy])
      }
    } catch {
      // Fallback on error
    }
    return STRATEGY_DESCRIPTIONS[strategy]
  }

  // Get tooltip text
  const getTooltipText = (key: string): string => {
    try {
      const tooltips = (t as Record<string, unknown>).tooltips as Record<string, unknown> | undefined
      if (tooltips && key in tooltips) {
        return safeStr(tooltips[key])
      }
    } catch {
      // Fallback on error
    }
    // Fallback texts
    const fallbacks: Record<string, string> = {
      confidenceLevel: 'Higher confidence requires larger samples but gives more reliable results.',
      marginOfError: 'Smaller margin of error requires larger samples for statistical accuracy.',
      strataColumn: 'Select a categorical column to ensure proportional sampling from each category.',
      randomSeed: 'Set a seed for reproducible sampling results across runs.',
    }
    return fallbacks[key] || ''
  }

  // Helper to get label from t with fallback
  const getLabel = (key: string, fallback: string): string => {
    try {
      const value = (t as Record<string, unknown>)[key]
      if (value !== undefined) {
        return safeStr(value)
      }
    } catch {
      // Fallback on error
    }
    return fallback
  }

  return (
    <Card>
      <CardHeader className="pb-4">
        <CardTitle className="text-base">{getLabel('samplingConfig', 'Sampling Configuration')}</CardTitle>
        <CardDescription className="text-sm">
          {getStrategyDescription(config.strategy)}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Strategy Selection */}
        <div className="space-y-2">
          <Label htmlFor="sampling-strategy">{getLabel('samplingStrategy', 'Sampling Strategy')}</Label>
          <Select
            value={config.strategy}
            onValueChange={(value) =>
              handleChange('strategy', value as SamplingStrategy)
            }
            disabled={disabled}
          >
            <SelectTrigger id="sampling-strategy">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {strategies.map((strategy) => (
                <SelectItem key={strategy} value={strategy}>
                  {getStrategyLabel(strategy)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Sample Size Input */}
        {showSampleSizeInput && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Label htmlFor="sample-size">{getLabel('sampleSize', 'Sample Size')}</Label>
              <span className="text-xs text-muted-foreground">
                (auto-estimated if empty)
              </span>
            </div>
            <Input
              id="sample-size"
              type="number"
              min={100}
              placeholder="Auto"
              value={config.sampleSize ?? ''}
              onChange={(e) =>
                handleChange(
                  'sampleSize',
                  e.target.value ? parseInt(e.target.value, 10) : null
                )
              }
              disabled={disabled}
            />
          </div>
        )}

        {/* Confidence Level & Margin of Error */}
        {showConfidenceSettings && (
          <>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Label>{getLabel('confidenceLevel', 'Confidence Level')}</Label>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="max-w-xs">{getTooltipText('confidenceLevel')}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
                <span className="ml-auto text-sm font-medium">
                  {(config.confidenceLevel * 100).toFixed(0)}%
                </span>
              </div>
              <Slider
                value={[config.confidenceLevel * 100]}
                onValueChange={([value]) =>
                  handleChange('confidenceLevel', value / 100)
                }
                min={80}
                max={99}
                step={1}
                disabled={disabled}
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>80%</span>
                <span>99%</span>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Label>{getLabel('marginOfError', 'Margin of Error')}</Label>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="max-w-xs">{getTooltipText('marginOfError')}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
                <span className="ml-auto text-sm font-medium">
                  {(config.marginOfError * 100).toFixed(1)}%
                </span>
              </div>
              <Slider
                value={[config.marginOfError * 100]}
                onValueChange={([value]) =>
                  handleChange('marginOfError', value / 100)
                }
                min={1}
                max={10}
                step={0.5}
                disabled={disabled}
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>1%</span>
                <span>10%</span>
              </div>
            </div>
          </>
        )}

        {/* Strata Column Selection */}
        {showStrataColumn && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Label htmlFor="strata-column">{getLabel('strataColumn', 'Stratification Column')}</Label>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="max-w-xs">{getTooltipText('strataColumn')}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
            <Select
              value={config.strataColumn ?? ''}
              onValueChange={(value) =>
                handleChange('strataColumn', value || null)
              }
              disabled={disabled || columns.length === 0}
            >
              <SelectTrigger id="strata-column">
                <SelectValue placeholder="Select column..." />
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

        {/* Random Seed Input */}
        {showSeedInput && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Label htmlFor="random-seed">{getLabel('randomSeed', 'Random Seed')}</Label>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="max-w-xs">{getTooltipText('randomSeed')}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
            <Input
              id="random-seed"
              type="number"
              placeholder="Random (no seed)"
              value={config.seed ?? ''}
              onChange={(e) =>
                handleChange(
                  'seed',
                  e.target.value ? parseInt(e.target.value, 10) : null
                )
              }
              disabled={disabled}
            />
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export { DEFAULT_CONFIG as DEFAULT_SAMPLING_CONFIG }
