/**
 * DataChangeTriggerForm - Configure data change detection triggers.
 *
 * Triggers when profile metrics change by a threshold percentage.
 */

import { useMemo } from 'react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { Badge } from '@/components/ui/badge'
import { TrendingUp, Info } from 'lucide-react'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'

interface DataChangeTriggerFormProps {
  changeThreshold: number
  metrics: string[]
  checkIntervalMinutes: number
  onChange: (config: {
    changeThreshold: number
    metrics: string[]
    checkIntervalMinutes: number
  }) => void
}

const AVAILABLE_METRICS = [
  {
    id: 'row_count',
    label: 'Row Count',
    description: 'Total number of rows in the dataset',
  },
  {
    id: 'column_count',
    label: 'Column Count',
    description: 'Total number of columns',
  },
  {
    id: 'null_percentage',
    label: 'Null Percentage',
    description: 'Percentage of null values across columns',
  },
  {
    id: 'distinct_count',
    label: 'Distinct Count',
    description: 'Number of distinct values per column',
  },
  {
    id: 'mean',
    label: 'Mean Values',
    description: 'Average values for numeric columns',
  },
  {
    id: 'std',
    label: 'Standard Deviation',
    description: 'Standard deviation for numeric columns',
  },
  {
    id: 'min',
    label: 'Minimum Values',
    description: 'Minimum values for columns',
  },
  {
    id: 'max',
    label: 'Maximum Values',
    description: 'Maximum values for columns',
  },
  {
    id: 'schema_hash',
    label: 'Schema Hash',
    description: 'Hash of column names and types',
  },
]

const CHECK_INTERVAL_PRESETS = [
  { label: '5 min', value: 5 },
  { label: '15 min', value: 15 },
  { label: '30 min', value: 30 },
  { label: '1 hour', value: 60 },
  { label: '6 hours', value: 360 },
  { label: '12 hours', value: 720 },
  { label: '1 day', value: 1440 },
]

export function DataChangeTriggerForm({
  changeThreshold,
  metrics,
  checkIntervalMinutes,
  onChange,
}: DataChangeTriggerFormProps) {
  const thresholdPercent = Math.round(changeThreshold * 100)

  const toggleMetric = (metricId: string) => {
    const newMetrics = metrics.includes(metricId)
      ? metrics.filter((m) => m !== metricId)
      : [...metrics, metricId]
    onChange({ changeThreshold, metrics: newMetrics, checkIntervalMinutes })
  }

  const handleThresholdChange = (value: number[]) => {
    onChange({
      changeThreshold: value[0] / 100,
      metrics,
      checkIntervalMinutes,
    })
  }

  const handleIntervalChange = (value: number) => {
    onChange({ changeThreshold, metrics, checkIntervalMinutes: value })
  }

  // Format check interval for display
  const intervalDisplay = useMemo(() => {
    if (checkIntervalMinutes >= 1440) {
      const days = Math.floor(checkIntervalMinutes / 1440)
      return `${days} day${days > 1 ? 's' : ''}`
    }
    if (checkIntervalMinutes >= 60) {
      const hours = Math.floor(checkIntervalMinutes / 60)
      return `${hours} hour${hours > 1 ? 's' : ''}`
    }
    return `${checkIntervalMinutes} min`
  }, [checkIntervalMinutes])

  return (
    <div className="space-y-5">
      {/* Threshold slider */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label className="flex items-center gap-1">
            Change Threshold
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <Info className="h-3.5 w-3.5 text-muted-foreground" />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Trigger when any monitored metric changes by at least this percentage</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </Label>
          <Badge variant="secondary" className="font-mono">
            {thresholdPercent}%
          </Badge>
        </div>
        <Slider
          value={[thresholdPercent]}
          onValueChange={handleThresholdChange}
          min={1}
          max={50}
          step={1}
          className="w-full"
        />
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>1% (sensitive)</span>
          <span>50% (coarse)</span>
        </div>
      </div>

      {/* Metrics selection */}
      <div className="space-y-2">
        <Label>Metrics to Monitor</Label>
        <div className="grid grid-cols-3 gap-2">
          {AVAILABLE_METRICS.map((metric) => (
            <TooltipProvider key={metric.id}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <label
                    className={`flex items-center gap-2 p-2 border rounded cursor-pointer transition-colors ${
                      metrics.includes(metric.id)
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:bg-muted/50'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={metrics.includes(metric.id)}
                      onChange={() => toggleMetric(metric.id)}
                      className="rounded"
                    />
                    <span className="text-sm truncate">{metric.label}</span>
                  </label>
                </TooltipTrigger>
                <TooltipContent>
                  <p>{metric.description}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          ))}
        </div>
        {metrics.length === 0 && (
          <p className="text-sm text-amber-600">Select at least one metric to monitor</p>
        )}
      </div>

      {/* Check interval */}
      <div className="space-y-2">
        <Label>Check Interval</Label>
        <div className="flex flex-wrap gap-2">
          {CHECK_INTERVAL_PRESETS.map((preset) => (
            <button
              key={preset.value}
              type="button"
              onClick={() => handleIntervalChange(preset.value)}
              className={`px-3 py-1.5 text-sm rounded border transition-colors ${
                checkIntervalMinutes === preset.value
                  ? 'border-primary bg-primary/5 text-primary'
                  : 'border-border hover:bg-muted/50'
              }`}
            >
              {preset.label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2 pt-1">
          <Label className="text-sm text-muted-foreground shrink-0">Custom:</Label>
          <Input
            type="number"
            min={1}
            value={checkIntervalMinutes}
            onChange={(e) => handleIntervalChange(parseInt(e.target.value) || 60)}
            className="w-24"
          />
          <span className="text-sm text-muted-foreground">minutes</span>
        </div>
      </div>

      {/* Summary */}
      <div className="flex items-center gap-2 p-3 bg-muted/50 rounded">
        <TrendingUp className="h-4 w-4 text-primary shrink-0" />
        <span className="text-sm">
          Check every <strong>{intervalDisplay}</strong>. Trigger when any of{' '}
          <strong>{metrics.length}</strong> metric(s) change by{' '}
          <strong>≥{thresholdPercent}%</strong>.
        </span>
      </div>
    </div>
  )
}
