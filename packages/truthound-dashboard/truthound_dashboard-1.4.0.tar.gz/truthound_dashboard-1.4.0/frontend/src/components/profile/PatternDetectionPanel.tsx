/**
 * PatternDetectionPanel Component
 *
 * Provides UI for configuring pattern detection during data profiling.
 * Supports detection of common data patterns like email, phone, UUID, etc.
 */
import * as React from 'react'
import { useIntlayer } from 'react-intlayer'
import { Check, ChevronsUpDown } from 'lucide-react'

import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { str } from '@/lib/intlayer-utils'

// Pattern types
export type PatternType =
  | 'email'
  | 'phone'
  | 'uuid'
  | 'url'
  | 'ip_address'
  | 'credit_card'
  | 'date'
  | 'datetime'
  | 'korean_rrn'
  | 'korean_phone'
  | 'ssn'
  | 'postal_code'
  | 'currency'
  | 'percentage'

export const ALL_PATTERN_TYPES: PatternType[] = [
  'email',
  'phone',
  'uuid',
  'url',
  'ip_address',
  'credit_card',
  'date',
  'datetime',
  'korean_rrn',
  'korean_phone',
  'ssn',
  'postal_code',
  'currency',
  'percentage',
]

// Pattern labels for when intlayer isn't available
const PATTERN_LABELS: Record<PatternType, string> = {
  email: 'Email',
  phone: 'Phone',
  uuid: 'UUID',
  url: 'URL',
  ip_address: 'IP Address',
  credit_card: 'Credit Card',
  date: 'Date',
  datetime: 'DateTime',
  korean_rrn: 'Korean RRN',
  korean_phone: 'Korean Phone',
  ssn: 'SSN',
  postal_code: 'Postal Code',
  currency: 'Currency',
  percentage: 'Percentage',
}

export interface PatternDetectionConfig {
  enabled: boolean
  sampleSize: number
  minConfidence: number
  patternsToDetect: PatternType[] | null
}

interface PatternDetectionPanelProps {
  config: PatternDetectionConfig
  onChange: (config: PatternDetectionConfig) => void
  disabled?: boolean
}

const DEFAULT_CONFIG: PatternDetectionConfig = {
  enabled: true,
  sampleSize: 1000,
  minConfidence: 0.8,
  patternsToDetect: null, // null means all patterns
}

export function PatternDetectionPanel({
  config,
  onChange,
  disabled = false,
}: PatternDetectionPanelProps) {
  const t = useIntlayer('profiler')
  const [open, setOpen] = React.useState(false)

  const handleChange = <K extends keyof PatternDetectionConfig>(
    key: K,
    value: PatternDetectionConfig[K]
  ) => {
    onChange({ ...config, [key]: value })
  }

  const togglePattern = (pattern: PatternType) => {
    const currentPatterns = config.patternsToDetect ?? [...ALL_PATTERN_TYPES]
    const isSelected = currentPatterns.includes(pattern)

    if (isSelected) {
      const newPatterns = currentPatterns.filter((p) => p !== pattern)
      handleChange(
        'patternsToDetect',
        newPatterns.length === 0 ? null : newPatterns
      )
    } else {
      handleChange('patternsToDetect', [...currentPatterns, pattern])
    }
  }

  const selectAllPatterns = () => {
    handleChange('patternsToDetect', null)
  }

  const selectedPatterns = config.patternsToDetect ?? ALL_PATTERN_TYPES
  const isAllSelected = config.patternsToDetect === null

  // Type-safe string extraction helper
  const safeStr = (value: unknown): string => {
    if (value === undefined || value === null) return ''
    if (typeof value === 'string') return value
    return str(value as Parameters<typeof str>[0])
  }

  // Helper to get pattern label
  const getPatternLabel = (pattern: PatternType): string => {
    try {
      const patterns = (t as Record<string, unknown>).patterns as Record<string, unknown> | undefined
      if (patterns && pattern in patterns) {
        return safeStr(patterns[pattern])
      }
    } catch {
      // Fallback on error
    }
    return PATTERN_LABELS[pattern]
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
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base">{getLabel('patternDetection', 'Pattern Detection')}</CardTitle>
            <CardDescription className="text-sm mt-1">
              Detect common data patterns like email, phone, UUID
            </CardDescription>
          </div>
          <Switch
            checked={config.enabled}
            onCheckedChange={(checked) => handleChange('enabled', checked)}
            disabled={disabled}
          />
        </div>
      </CardHeader>
      {config.enabled && (
        <CardContent className="space-y-4">
          {/* Pattern Sample Size */}
          <div className="space-y-2">
            <Label htmlFor="pattern-sample-size">{getLabel('patternSampleSize', 'Pattern Sample Size')}</Label>
            <Input
              id="pattern-sample-size"
              type="number"
              min={100}
              max={100000}
              value={config.sampleSize}
              onChange={(e) =>
                handleChange('sampleSize', parseInt(e.target.value, 10) || 1000)
              }
              disabled={disabled}
            />
            <p className="text-xs text-muted-foreground">
              Number of values to sample for pattern detection (100-100,000)
            </p>
          </div>

          {/* Minimum Confidence */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>{getLabel('minPatternConfidence', 'Minimum Confidence')}</Label>
              <span className="text-sm font-medium">
                {(config.minConfidence * 100).toFixed(0)}%
              </span>
            </div>
            <Slider
              value={[config.minConfidence * 100]}
              onValueChange={([value]) =>
                handleChange('minConfidence', value / 100)
              }
              min={50}
              max={100}
              step={5}
              disabled={disabled}
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>50%</span>
              <span>100%</span>
            </div>
          </div>

          {/* Patterns to Detect */}
          <div className="space-y-2">
            <Label>{getLabel('patternsToDetect', 'Patterns to Detect')}</Label>
            <Popover open={open} onOpenChange={setOpen}>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  role="combobox"
                  aria-expanded={open}
                  className="w-full justify-between"
                  disabled={disabled}
                >
                  {isAllSelected
                    ? 'All Patterns'
                    : `${selectedPatterns.length} patterns selected`}
                  <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-64 p-0" align="start">
                <ScrollArea className="h-[300px]">
                  <div className="p-2 space-y-1">
                    {/* Select All Option */}
                    <div
                      className="flex items-center space-x-2 p-2 rounded hover:bg-muted cursor-pointer"
                      onClick={selectAllPatterns}
                    >
                      <Check
                        className={`h-4 w-4 ${isAllSelected ? 'opacity-100' : 'opacity-0'}`}
                      />
                      <span className="font-medium">All Patterns</span>
                    </div>
                    <div className="border-t my-2" />
                    {/* Individual Patterns */}
                    {ALL_PATTERN_TYPES.map((pattern) => (
                      <div
                        key={pattern}
                        className="flex items-center space-x-2 p-2 rounded hover:bg-muted cursor-pointer"
                        onClick={() => togglePattern(pattern)}
                      >
                        <Checkbox
                          checked={selectedPatterns.includes(pattern)}
                          onCheckedChange={() => togglePattern(pattern)}
                        />
                        <span>{getPatternLabel(pattern)}</span>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </PopoverContent>
            </Popover>
          </div>

          {/* Selected Patterns Display */}
          {!isAllSelected && selectedPatterns.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {selectedPatterns.map((pattern) => (
                <Badge key={pattern} variant="secondary" className="text-xs">
                  {getPatternLabel(pattern)}
                </Badge>
              ))}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  )
}

export { DEFAULT_CONFIG as DEFAULT_PATTERN_CONFIG }
