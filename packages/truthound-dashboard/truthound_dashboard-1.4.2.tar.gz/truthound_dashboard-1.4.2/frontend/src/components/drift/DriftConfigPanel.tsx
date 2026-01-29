/**
 * Drift Configuration Panel component.
 *
 * A comprehensive panel for configuring drift detection parameters:
 * - Detection method selection (9 methods)
 * - Threshold configuration with method-specific defaults
 * - Multiple testing correction methods
 * - Column selection for targeted comparison
 */

import { useCallback, useMemo, useState } from 'react'
import { useIntlayer } from 'react-intlayer'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
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
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  type DriftMethod,
  type CorrectionMethod,
  CORRECTION_METHODS,
  DEFAULT_THRESHOLDS,
} from '@/api/client'
import { DriftMethodSelector, type DriftMethodSelectorVariant } from './DriftMethodSelector'
import { ChevronDown, Info, RotateCcw, Settings2, Columns3 } from 'lucide-react'

/**
 * Helper to safely extract string from Intlayer node.
 */
function getIntlayerString(node: unknown): string {
  if (typeof node === 'string') return node
  if (node && typeof node === 'object' && 'value' in node) {
    const val = (node as { value: unknown }).value
    return typeof val === 'string' ? val : String(val)
  }
  return String(node ?? '')
}

export interface DriftConfig {
  /** Detection method */
  method: DriftMethod
  /** Custom threshold (null = use default) */
  threshold: number | null
  /** Multiple testing correction method */
  correction: CorrectionMethod | null
  /** Specific columns to compare (null = all columns) */
  columns: string[] | null
}

export interface DriftConfigPanelProps {
  /** Current configuration */
  config: DriftConfig
  /** Callback when configuration changes */
  onChange: (config: DriftConfig) => void
  /** Available columns for selection */
  availableColumns?: string[]
  /** Method selector variant */
  methodVariant?: DriftMethodSelectorVariant
  /** Whether to show advanced options collapsed by default */
  collapsedByDefault?: boolean
  /** Whether to show the column selector */
  showColumnSelector?: boolean
  /** Custom class name */
  className?: string
  /** Disabled state */
  disabled?: boolean
}

/**
 * Threshold configuration section.
 */
function ThresholdConfig({
  value,
  method,
  onChange,
  disabled,
}: {
  value: number | null
  method: DriftMethod
  onChange: (threshold: number | null) => void
  disabled?: boolean
}) {
  const t = useIntlayer('drift')
  const defaultThreshold = DEFAULT_THRESHOLDS[method]
  const displayValue = value ?? defaultThreshold
  const [useCustom, setUseCustom] = useState(value !== null)

  const handleToggleCustom = useCallback((checked: boolean) => {
    setUseCustom(checked)
    if (!checked) {
      onChange(null) // Use default
    } else {
      onChange(defaultThreshold)
    }
  }, [onChange, defaultThreshold])

  const handleSliderChange = useCallback((values: number[]) => {
    onChange(values[0])
  }, [onChange])

  const config = t.config as Record<string, unknown>

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Label className="text-sm font-medium">{getIntlayerString(config.threshold)}</Label>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <Info className="h-4 w-4 text-muted-foreground" />
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p>{getIntlayerString(config.thresholdDescription)}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">
            {getIntlayerString(config.defaultThreshold)}: {defaultThreshold}
          </span>
          <Switch
            checked={useCustom}
            onCheckedChange={handleToggleCustom}
            disabled={disabled}
          />
        </div>
      </div>

      {useCustom ? (
        <div className="space-y-2">
          <div className="flex items-center gap-4">
            <Slider
              value={[displayValue]}
              onValueChange={handleSliderChange}
              min={0.001}
              max={0.5}
              step={0.001}
              disabled={disabled}
              className="flex-1"
            />
            <Input
              type="number"
              value={displayValue}
              onChange={(e) => onChange(parseFloat(e.target.value) || defaultThreshold)}
              min={0.001}
              max={0.5}
              step={0.001}
              disabled={disabled}
              className="w-20"
            />
          </div>
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Strict (0.001)</span>
            <span>Lenient (0.5)</span>
          </div>
        </div>
      ) : (
        <div className="text-sm text-muted-foreground p-2 bg-muted/50 rounded-md">
          Using default threshold: <span className="font-mono">{defaultThreshold}</span>
        </div>
      )}
    </div>
  )
}

/**
 * Correction method configuration section.
 */
function CorrectionConfig({
  value,
  onChange,
  disabled,
}: {
  value: CorrectionMethod | null
  onChange: (correction: CorrectionMethod | null) => void
  disabled?: boolean
}) {
  const t = useIntlayer('drift')

  const getCorrectionLabel = (method: string): string => {
    if (!method) return 'Default (BH)'
    const labels = t.correctionMethods as Record<string, unknown>
    return getIntlayerString(labels[method])
  }

  const getCorrectionDescription = (method: string): string => {
    const descriptions = t.correctionDescriptions as Record<string, unknown>
    if (!method) return getIntlayerString(descriptions.bh)
    return getIntlayerString(descriptions[method])
  }

  const config = t.config as Record<string, unknown>

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Label className="text-sm font-medium">{getIntlayerString(config.correctionMethod)}</Label>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger>
              <Info className="h-4 w-4 text-muted-foreground" />
            </TooltipTrigger>
            <TooltipContent className="max-w-xs">
              <p>{getIntlayerString(config.correctionDescription)}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      <Select
        value={value ?? ''}
        onValueChange={(v) => onChange(v === '' ? null : v as CorrectionMethod)}
        disabled={disabled}
      >
        <SelectTrigger>
          <SelectValue placeholder="Default (BH)" />
        </SelectTrigger>
        <SelectContent>
          {CORRECTION_METHODS.map((method) => (
            <SelectItem key={method.value} value={method.value}>
              <div className="flex flex-col">
                <span>{getCorrectionLabel(method.value)}</span>
                <span className="text-xs text-muted-foreground">
                  {getCorrectionDescription(method.value)}
                </span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}

/**
 * Column selection configuration section.
 */
function ColumnSelector({
  selected,
  available,
  onChange,
  disabled,
}: {
  selected: string[] | null
  available: string[]
  onChange: (columns: string[] | null) => void
  disabled?: boolean
}) {
  const t = useIntlayer('drift')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectAll, setSelectAll] = useState(selected === null)

  const filteredColumns = useMemo(() => {
    if (!searchQuery) return available
    const query = searchQuery.toLowerCase()
    return available.filter((col) => col.toLowerCase().includes(query))
  }, [available, searchQuery])

  const handleSelectAll = useCallback((checked: boolean) => {
    setSelectAll(checked)
    onChange(checked ? null : [])
  }, [onChange])

  const handleColumnToggle = useCallback((column: string, checked: boolean) => {
    if (selectAll) {
      // When unchecking from "all", switch to explicit selection
      setSelectAll(false)
      const newSelection = available.filter((c) => c !== column)
      onChange(newSelection)
    } else {
      const currentSelection = selected ?? []
      const newSelection = checked
        ? [...currentSelection, column]
        : currentSelection.filter((c) => c !== column)
      onChange(newSelection.length === available.length ? null : newSelection)
    }
  }, [selectAll, selected, available, onChange])

  const isColumnSelected = useCallback((column: string) => {
    if (selectAll) return true
    return selected?.includes(column) ?? false
  }, [selectAll, selected])

  const selectedCount = selectAll ? available.length : (selected?.length ?? 0)
  const config = t.config as Record<string, unknown>

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Columns3 className="h-4 w-4 text-muted-foreground" />
          <Label className="text-sm font-medium">{getIntlayerString(config.columns)}</Label>
        </div>
        <Badge variant="secondary">
          {selectedCount} / {available.length}
        </Badge>
      </div>

      <div className="flex items-center gap-2">
        <Checkbox
          id="select-all"
          checked={selectAll}
          onCheckedChange={handleSelectAll}
          disabled={disabled}
        />
        <Label htmlFor="select-all" className="text-sm cursor-pointer">
          {getIntlayerString(config.allColumns)}
        </Label>
      </div>

      {!selectAll && (
        <>
          <Input
            placeholder={getIntlayerString(config.selectColumns)}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            disabled={disabled}
            className="h-8"
          />

          <ScrollArea className="h-40 rounded-md border p-2">
            <div className="space-y-1">
              {filteredColumns.map((column) => (
                <div key={column} className="flex items-center gap-2">
                  <Checkbox
                    id={`col-${column}`}
                    checked={isColumnSelected(column)}
                    onCheckedChange={(checked) => handleColumnToggle(column, !!checked)}
                    disabled={disabled}
                  />
                  <Label
                    htmlFor={`col-${column}`}
                    className="text-sm font-mono cursor-pointer truncate"
                    title={column}
                  >
                    {column}
                  </Label>
                </div>
              ))}
              {filteredColumns.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-4">
                  No columns match your search
                </p>
              )}
            </div>
          </ScrollArea>
        </>
      )}
    </div>
  )
}

/**
 * Main DriftConfigPanel component.
 *
 * Provides a comprehensive configuration interface for drift detection:
 * - Method selection with all 9 truthound methods
 * - Threshold configuration with smart defaults
 * - Multiple testing correction
 * - Column selection for targeted comparison
 */
export function DriftConfigPanel({
  config,
  onChange,
  availableColumns = [],
  methodVariant = 'compact',
  collapsedByDefault = true,
  showColumnSelector = true,
  className,
  disabled = false,
}: DriftConfigPanelProps) {
  const t = useIntlayer('drift')
  const [advancedOpen, setAdvancedOpen] = useState(!collapsedByDefault)

  const handleMethodChange = useCallback((method: DriftMethod) => {
    onChange({
      ...config,
      method,
      // Reset threshold to null (use default) when method changes
      threshold: null,
    })
  }, [config, onChange])

  const handleThresholdChange = useCallback((threshold: number | null) => {
    onChange({ ...config, threshold })
  }, [config, onChange])

  const handleCorrectionChange = useCallback((correction: CorrectionMethod | null) => {
    onChange({ ...config, correction })
  }, [config, onChange])

  const handleColumnsChange = useCallback((columns: string[] | null) => {
    onChange({ ...config, columns })
  }, [config, onChange])

  const handleReset = useCallback(() => {
    onChange({
      method: 'auto',
      threshold: null,
      correction: null,
      columns: null,
    })
  }, [onChange])

  const hasCustomConfig = config.method !== 'auto' ||
    config.threshold !== null ||
    config.correction !== null ||
    config.columns !== null

  const tConfig = t.config as Record<string, unknown>

  return (
    <div className={cn('space-y-4', className)}>
      {/* Method Selection */}
      <div className="space-y-2">
        <Label className="text-sm font-medium">{getIntlayerString(t.detectionMethod)}</Label>
        <DriftMethodSelector
          value={config.method}
          onChange={handleMethodChange}
          variant={methodVariant}
          showThresholdHints
          disabled={disabled}
        />
      </div>

      {/* Advanced Options */}
      <Collapsible open={advancedOpen} onOpenChange={setAdvancedOpen}>
        <CollapsibleTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-between"
            disabled={disabled}
          >
            <span className="flex items-center gap-2">
              <Settings2 className="h-4 w-4" />
              {getIntlayerString(tConfig.advancedOptions)}
            </span>
            <ChevronDown className={cn(
              'h-4 w-4 transition-transform',
              advancedOpen && 'rotate-180'
            )} />
          </Button>
        </CollapsibleTrigger>

        <CollapsibleContent className="space-y-4 pt-4">
          {/* Threshold Configuration */}
          <ThresholdConfig
            value={config.threshold}
            method={config.method}
            onChange={handleThresholdChange}
            disabled={disabled}
          />

          {/* Correction Method */}
          <CorrectionConfig
            value={config.correction}
            onChange={handleCorrectionChange}
            disabled={disabled}
          />

          {/* Column Selection */}
          {showColumnSelector && availableColumns.length > 0 && (
            <ColumnSelector
              selected={config.columns}
              available={availableColumns}
              onChange={handleColumnsChange}
              disabled={disabled}
            />
          )}

          {/* Reset Button */}
          {hasCustomConfig && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleReset}
              disabled={disabled}
              className="w-full"
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Reset to Defaults
            </Button>
          )}
        </CollapsibleContent>
      </Collapsible>
    </div>
  )
}

export default DriftConfigPanel
