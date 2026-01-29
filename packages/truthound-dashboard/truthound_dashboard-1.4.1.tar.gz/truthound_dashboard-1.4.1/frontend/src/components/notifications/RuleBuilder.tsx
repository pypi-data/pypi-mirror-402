/**
 * RuleBuilder - Visual rule composition for notification routing.
 *
 * Provides a guided interface for building routing rules with:
 * - Rule type selection with descriptions
 * - Type-specific parameter inputs via plugin architecture
 * - Combinator support (all_of, any_of, not) with recursive nesting
 * - Real-time validation
 * - i18n support
 *
 * Architecture:
 * - RuleTypeRegistry: Extensible registry for rule type renderers
 * - BaseRuleRenderer: Abstract renderer interface
 * - RuleBuilder: Main component that orchestrates rendering
 */

import { useState, useCallback, useMemo, createContext, useContext, useRef, KeyboardEvent } from 'react'
import {
  Plus,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  Info,
  ChevronDown,
  ChevronRight,
  Copy,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Slider } from '@/components/ui/slider'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { cn } from '@/lib/utils'
import { Jinja2RuleEditor, type Jinja2RuleConfig } from './Jinja2RuleEditor'
import { ExpressionRuleEditor, type ExpressionConfig } from './ExpressionRuleEditor'

// =============================================================================
// Types & Interfaces
// =============================================================================

export type RuleType =
  | 'severity'
  | 'issue_count'
  | 'pass_rate'
  | 'time_window'
  | 'tag'
  | 'data_asset'
  | 'metadata'
  | 'status'
  | 'error'
  | 'always'
  | 'never'
  | 'all_of'
  | 'any_of'
  | 'not'
  | 'jinja2'
  | 'expression'

export interface RuleConfig {
  type: RuleType
  // Rule-specific parameters stored flat (matches backend structure)
  [key: string]: unknown
  // For combinators
  rules?: RuleConfig[]
}

export type RuleCategory = 'basic' | 'condition' | 'combinator' | 'static' | 'advanced'

export interface ParamSchema {
  type: 'string' | 'number' | 'boolean' | 'select' | 'multi-select' | 'array' | 'weekdays' | 'jinja2-template' | 'expression'
  label: string
  description?: string
  required?: boolean
  default?: unknown
  // For numbers
  min?: number
  max?: number
  step?: number
  // For selects
  options?: Array<{ value: string; label: string }>
  // For strings
  placeholder?: string
  pattern?: string
}

export interface RuleTypeDefinition {
  type: RuleType
  label: string
  description: string
  category: RuleCategory
  params: Record<string, ParamSchema>
  validate?: (config: RuleConfig) => boolean
  defaultConfig?: () => Partial<RuleConfig>
}

// =============================================================================
// Rule Type Registry (Plugin Architecture)
// =============================================================================

class RuleTypeRegistryClass {
  private definitions: Map<RuleType, RuleTypeDefinition> = new Map()

  register(definition: RuleTypeDefinition): void {
    this.definitions.set(definition.type, definition)
  }

  get(type: RuleType): RuleTypeDefinition | undefined {
    return this.definitions.get(type)
  }

  getAll(): RuleTypeDefinition[] {
    return Array.from(this.definitions.values())
  }

  getByCategory(category: RuleCategory): RuleTypeDefinition[] {
    return this.getAll().filter((def) => def.category === category)
  }

  createDefaultConfig(type: RuleType): RuleConfig {
    const definition = this.get(type)
    if (!definition) {
      return { type }
    }

    const config: RuleConfig = { type }

    // Apply default values from params
    for (const [key, schema] of Object.entries(definition.params)) {
      if (schema.default !== undefined) {
        config[key] = schema.default
      } else if (schema.type === 'select' && schema.options?.length) {
        config[key] = schema.options[0].value
      } else if (schema.type === 'multi-select') {
        config[key] = []
      } else if (schema.type === 'weekdays') {
        config[key] = [0, 1, 2, 3, 4] // Monday-Friday default
      } else if (schema.type === 'boolean') {
        config[key] = false
      } else if (schema.type === 'array') {
        config[key] = []
      }
    }

    // Apply custom default config
    if (definition.defaultConfig) {
      Object.assign(config, definition.defaultConfig())
    }

    // Initialize sub-rules for combinators
    if (definition.category === 'combinator') {
      if (type === 'not') {
        config.rules = [{ type: 'always' }]
      } else {
        config.rules = []
      }
    }

    return config
  }

  validate(config: RuleConfig): boolean {
    const definition = this.get(config.type)
    if (!definition) return false

    // Check required params
    for (const [key, schema] of Object.entries(definition.params)) {
      if (schema.required) {
        const value = config[key]
        if (value === undefined || value === null || value === '') {
          return false
        }
      }
    }

    // Run custom validation
    if (definition.validate) {
      return definition.validate(config)
    }

    // Check combinator sub-rules
    if (definition.category === 'combinator') {
      if (config.type === 'not') {
        return config.rules?.length === 1 && this.validate(config.rules[0])
      }
      if (!config.rules || config.rules.length === 0) {
        return false
      }
      return config.rules.every((rule) => this.validate(rule))
    }

    return true
  }
}

export const RuleTypeRegistry = new RuleTypeRegistryClass()

// =============================================================================
// Register All Rule Types
// =============================================================================

// Severity Rule
RuleTypeRegistry.register({
  type: 'severity',
  label: 'Severity',
  description: 'Match notifications by minimum severity level',
  category: 'basic',
  params: {
    min_severity: {
      type: 'select',
      label: 'Minimum Severity',
      description: 'Match events with severity at or above this level',
      required: true,
      default: 'high',
      options: [
        { value: 'info', label: 'Info' },
        { value: 'low', label: 'Low' },
        { value: 'medium', label: 'Medium' },
        { value: 'high', label: 'High' },
        { value: 'critical', label: 'Critical' },
      ],
    },
  },
})

// Issue Count Rule
RuleTypeRegistry.register({
  type: 'issue_count',
  label: 'Issue Count',
  description: 'Match when issue count exceeds threshold',
  category: 'condition',
  params: {
    min_count: {
      type: 'number',
      label: 'Minimum Count',
      description: 'Match events with at least this many issues',
      required: true,
      default: 1,
      min: 0,
    },
  },
})

// Pass Rate Rule
RuleTypeRegistry.register({
  type: 'pass_rate',
  label: 'Pass Rate',
  description: 'Match when pass rate is below threshold',
  category: 'condition',
  params: {
    max_pass_rate: {
      type: 'number',
      label: 'Maximum Pass Rate',
      description: 'Match events with pass rate at or below this value (0.0 - 1.0)',
      required: true,
      default: 0.9,
      min: 0,
      max: 1,
      step: 0.01,
    },
  },
})

// Time Window Rule
RuleTypeRegistry.register({
  type: 'time_window',
  label: 'Time Window',
  description: 'Match during specific hours and days',
  category: 'condition',
  params: {
    start_hour: {
      type: 'number',
      label: 'Start Hour',
      description: 'Start hour (0-23)',
      required: true,
      default: 9,
      min: 0,
      max: 23,
    },
    end_hour: {
      type: 'number',
      label: 'End Hour',
      description: 'End hour (0-23)',
      required: true,
      default: 17,
      min: 0,
      max: 23,
    },
    weekdays: {
      type: 'weekdays',
      label: 'Weekdays',
      description: 'Days of the week (0=Monday, 6=Sunday)',
      required: false,
      default: [0, 1, 2, 3, 4],
    },
    timezone: {
      type: 'string',
      label: 'Timezone',
      description: 'Timezone name (e.g., America/New_York)',
      required: false,
      placeholder: 'UTC',
    },
  },
})

// Tag Rule
RuleTypeRegistry.register({
  type: 'tag',
  label: 'Tag',
  description: 'Match by notification tags',
  category: 'basic',
  params: {
    tags: {
      type: 'array',
      label: 'Tags',
      description: 'Tags to match',
      required: true,
      default: [],
    },
    match_all: {
      type: 'boolean',
      label: 'Match All',
      description: 'Require all tags to match (AND logic)',
      required: false,
      default: false,
    },
  },
})

// Data Asset Rule
RuleTypeRegistry.register({
  type: 'data_asset',
  label: 'Data Asset',
  description: 'Match by data asset name or pattern',
  category: 'basic',
  params: {
    pattern: {
      type: 'string',
      label: 'Asset Pattern',
      description: 'Glob pattern to match data assets (e.g., "*.parquet", "prod/*")',
      required: true,
      default: '*',
      placeholder: '*_production_*',
    },
  },
})

// Metadata Rule
RuleTypeRegistry.register({
  type: 'metadata',
  label: 'Metadata',
  description: 'Match by metadata field value',
  category: 'condition',
  params: {
    key: {
      type: 'string',
      label: 'Field Name',
      description: 'Metadata field name to match',
      required: true,
      placeholder: 'source_type',
    },
    value: {
      type: 'string',
      label: 'Expected Value',
      description: 'Value to match against',
      required: true,
      placeholder: 'database',
    },
    operator: {
      type: 'select',
      label: 'Operator',
      description: 'Comparison operator',
      required: false,
      default: 'eq',
      options: [
        { value: 'eq', label: 'Equals (=)' },
        { value: 'ne', label: 'Not Equals (!=)' },
        { value: 'contains', label: 'Contains' },
        { value: 'regex', label: 'Regex Match' },
        { value: 'gt', label: 'Greater Than (>)' },
        { value: 'lt', label: 'Less Than (<)' },
        { value: 'gte', label: 'Greater or Equal (>=)' },
        { value: 'lte', label: 'Less or Equal (<=)' },
      ],
    },
  },
})

// Status Rule
RuleTypeRegistry.register({
  type: 'status',
  label: 'Status',
  description: 'Match by validation status',
  category: 'basic',
  params: {
    statuses: {
      type: 'multi-select',
      label: 'Statuses',
      description: 'Validation statuses to match',
      required: true,
      default: ['failure', 'error'],
      options: [
        { value: 'success', label: 'Success' },
        { value: 'warning', label: 'Warning' },
        { value: 'failure', label: 'Failure' },
        { value: 'error', label: 'Error' },
      ],
    },
  },
})

// Error Rule
RuleTypeRegistry.register({
  type: 'error',
  label: 'Error Pattern',
  description: 'Match by error message pattern',
  category: 'condition',
  params: {
    error_pattern: {
      type: 'string',
      label: 'Error Pattern',
      description: 'Regex pattern to match error messages',
      required: true,
      default: '.*',
      placeholder: 'connection.*timeout',
    },
  },
})

// Always Rule
RuleTypeRegistry.register({
  type: 'always',
  label: 'Always Match',
  description: 'Always matches (catch-all rule)',
  category: 'static',
  params: {},
})

// Never Rule
RuleTypeRegistry.register({
  type: 'never',
  label: 'Never Match',
  description: 'Never matches (disabled rule)',
  category: 'static',
  params: {},
})

// All Of (AND) Combinator
RuleTypeRegistry.register({
  type: 'all_of',
  label: 'All Of (AND)',
  description: 'Match when ALL sub-rules match',
  category: 'combinator',
  params: {},
  validate: (config) => {
    if (!config.rules || config.rules.length === 0) return false
    return config.rules.every((rule) => RuleTypeRegistry.validate(rule))
  },
})

// Any Of (OR) Combinator
RuleTypeRegistry.register({
  type: 'any_of',
  label: 'Any Of (OR)',
  description: 'Match when ANY sub-rule matches',
  category: 'combinator',
  params: {},
  validate: (config) => {
    if (!config.rules || config.rules.length === 0) return false
    return config.rules.every((rule) => RuleTypeRegistry.validate(rule))
  },
})

// Not Combinator
RuleTypeRegistry.register({
  type: 'not',
  label: 'Not (Negate)',
  description: 'Negate the sub-rule result',
  category: 'combinator',
  params: {},
  validate: (config) => {
    if (!config.rules || config.rules.length !== 1) return false
    return RuleTypeRegistry.validate(config.rules[0])
  },
})

// Jinja2 Template Rule
RuleTypeRegistry.register({
  type: 'jinja2',
  label: 'Jinja2 Template',
  description: 'Use Jinja2 template for flexible, expression-based routing',
  category: 'advanced',
  params: {
    template: {
      type: 'jinja2-template',
      label: 'Template',
      description: 'Jinja2 template expression (e.g., {{ severity == "critical" }})',
      required: true,
      default: '{{ true }}',
      placeholder: '{{ severity == "critical" and issue_count > 5 }}',
    },
    expected_result: {
      type: 'select',
      label: 'Expected Result',
      description: 'Expected output for rule to match',
      required: false,
      default: 'true',
      options: [
        { value: 'true', label: 'true (match when True)' },
        { value: 'false', label: 'false (match when False)' },
      ],
    },
  },
  validate: (config) => {
    const template = config.template as string | undefined
    return !!template && template.trim().length > 0
  },
})

// Expression Rule
RuleTypeRegistry.register({
  type: 'expression',
  label: 'Expression',
  description: 'Python-like expression for complex conditions',
  category: 'advanced',
  params: {
    expression: {
      type: 'expression',
      label: 'Expression',
      description: 'Python-like expression (e.g., severity == "critical" and issue_count > 5)',
      required: true,
      default: '',
      placeholder: 'severity == "critical" and issue_count > 5',
    },
  },
  validate: (config) => {
    const expression = config.expression as string | undefined
    return !!expression && expression.trim().length > 0
  },
})

// =============================================================================
// Context for sharing state
// =============================================================================

interface RuleBuilderContextValue {
  maxDepth: number
  onCopyRule?: (config: RuleConfig) => void
}

const RuleBuilderContext = createContext<RuleBuilderContextValue>({
  maxDepth: 3,
})

// =============================================================================
// Parameter Renderers
// =============================================================================

interface ParamRendererProps<T = unknown> {
  name: string
  schema: ParamSchema
  value: T
  onChange: (value: T) => void
}

function StringParamRenderer({ schema, value, onChange }: ParamRendererProps<string>) {
  return (
    <Input
      placeholder={schema.placeholder}
      value={value || ''}
      onChange={(e) => onChange(e.target.value)}
      className="h-9"
    />
  )
}

function NumberParamRenderer({ schema, value, onChange }: ParamRendererProps<number>) {
  const showSlider = schema.min !== undefined && schema.max !== undefined

  return (
    <div className="space-y-2">
      {showSlider ? (
        <div className="flex items-center gap-4">
          <Slider
            min={schema.min}
            max={schema.max}
            step={schema.step || 1}
            value={[value ?? schema.min ?? 0]}
            onValueChange={([v]) => onChange(v)}
            className="flex-1"
          />
          <Input
            type="number"
            min={schema.min}
            max={schema.max}
            step={schema.step}
            value={value ?? ''}
            onChange={(e) => onChange(e.target.value ? Number(e.target.value) : schema.min ?? 0)}
            className="w-20 h-9"
          />
        </div>
      ) : (
        <Input
          type="number"
          min={schema.min}
          max={schema.max}
          step={schema.step}
          placeholder={schema.placeholder}
          value={value ?? ''}
          onChange={(e) => onChange(e.target.value ? Number(e.target.value) : undefined as unknown as number)}
          className="h-9"
        />
      )}
    </div>
  )
}

function BooleanParamRenderer({ value, onChange }: ParamRendererProps<boolean>) {
  return (
    <div className="flex items-center gap-2">
      <Switch checked={value || false} onCheckedChange={onChange} />
      <span className="text-sm text-muted-foreground">{value ? 'Enabled' : 'Disabled'}</span>
    </div>
  )
}

function SelectParamRenderer({ schema, value, onChange }: ParamRendererProps<string>) {
  return (
    <Select value={value || ''} onValueChange={onChange}>
      <SelectTrigger className="h-9">
        <SelectValue placeholder="Select..." />
      </SelectTrigger>
      <SelectContent>
        {schema.options?.map((opt) => (
          <SelectItem key={opt.value} value={opt.value}>
            {opt.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

function MultiSelectParamRenderer({ schema, value, onChange }: ParamRendererProps<string[]>) {
  const currentValue = value || []

  const toggleOption = (optValue: string) => {
    if (currentValue.includes(optValue)) {
      onChange(currentValue.filter((v) => v !== optValue))
    } else {
      onChange([...currentValue, optValue])
    }
  }

  return (
    <div className="flex flex-wrap gap-2">
      {schema.options?.map((opt) => {
        const isSelected = currentValue.includes(opt.value)
        return (
          <Badge
            key={opt.value}
            variant={isSelected ? 'default' : 'outline'}
            className={cn('cursor-pointer transition-colors', isSelected && 'bg-primary')}
            onClick={() => toggleOption(opt.value)}
          >
            {opt.label}
          </Badge>
        )
      })}
    </div>
  )
}

function ArrayParamRenderer({ schema, value, onChange }: ParamRendererProps<string[]>) {
  const [inputValue, setInputValue] = useState('')
  const currentValue = value || []

  const addItem = () => {
    const trimmed = inputValue.trim()
    if (trimmed && !currentValue.includes(trimmed)) {
      onChange([...currentValue, trimmed])
      setInputValue('')
    }
  }

  const removeItem = (item: string) => {
    onChange(currentValue.filter((v) => v !== item))
  }

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <Input
          placeholder={schema.placeholder || 'Add item...'}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault()
              addItem()
            }
          }}
          className="h-9"
        />
        <Button type="button" variant="outline" size="sm" onClick={addItem} className="h-9">
          <Plus className="h-4 w-4" />
        </Button>
      </div>
      {currentValue.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {currentValue.map((item) => (
            <Badge key={item} variant="secondary" className="gap-1 pr-1">
              {item}
              <button
                type="button"
                onClick={() => removeItem(item)}
                className="ml-1 hover:text-destructive rounded-sm"
              >
                <Trash2 className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  )
}

/**
 * Weekday definitions mapping day number to key.
 * Backend uses Python's weekday() format: 0=Monday, 6=Sunday.
 */
const WEEKDAY_DEFS = [
  { day: 0, key: 'mon', label: 'Mon', fullName: 'Monday' },
  { day: 1, key: 'tue', label: 'Tue', fullName: 'Tuesday' },
  { day: 2, key: 'wed', label: 'Wed', fullName: 'Wednesday' },
  { day: 3, key: 'thu', label: 'Thu', fullName: 'Thursday' },
  { day: 4, key: 'fri', label: 'Fri', fullName: 'Friday' },
  { day: 5, key: 'sat', label: 'Sat', fullName: 'Saturday' },
  { day: 6, key: 'sun', label: 'Sun', fullName: 'Sunday' },
]

/**
 * Enhanced WeekdaysParamRenderer with improved accessibility and visual feedback.
 * Features:
 * - Visual multi-select toggle buttons
 * - Quick selection buttons (weekdays, weekends, all, clear)
 * - Keyboard navigation (arrow keys, space/enter to toggle)
 * - ARIA labels and roles
 * - Selection count feedback
 */
function WeekdaysParamRenderer({ value, onChange }: ParamRendererProps<number[]>) {
  const currentValue = value || []
  const containerRef = useRef<HTMLDivElement>(null)

  const toggleDay = useCallback(
    (day: number) => {
      const newValue = currentValue.includes(day)
        ? currentValue.filter((d) => d !== day)
        : [...currentValue, day].sort((a, b) => a - b)
      onChange(newValue)
    },
    [currentValue, onChange]
  )

  const selectWeekdays = useCallback(() => {
    onChange([0, 1, 2, 3, 4])
  }, [onChange])

  const selectWeekend = useCallback(() => {
    onChange([5, 6])
  }, [onChange])

  const selectAll = useCallback(() => {
    onChange([0, 1, 2, 3, 4, 5, 6])
  }, [onChange])

  const clearAll = useCallback(() => {
    onChange([])
  }, [onChange])

  // Keyboard navigation handler
  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLButtonElement>, currentDay: number) => {
      const buttons = containerRef.current?.querySelectorAll<HTMLButtonElement>(
        '[data-weekday]'
      )
      if (!buttons) return

      const currentIndex = WEEKDAY_DEFS.findIndex((w) => w.day === currentDay)

      switch (e.key) {
        case 'ArrowLeft':
          e.preventDefault()
          if (currentIndex > 0) {
            buttons[currentIndex - 1]?.focus()
          }
          break
        case 'ArrowRight':
          e.preventDefault()
          if (currentIndex < WEEKDAY_DEFS.length - 1) {
            buttons[currentIndex + 1]?.focus()
          }
          break
        case ' ':
        case 'Enter':
          e.preventDefault()
          toggleDay(currentDay)
          break
      }
    },
    [toggleDay]
  )

  // Determine selection state for feedback
  const isAllSelected = currentValue.length === 7
  const isWeekdaysOnly =
    currentValue.length === 5 &&
    [0, 1, 2, 3, 4].every((d) => currentValue.includes(d))
  const isWeekendOnly =
    currentValue.length === 2 &&
    [5, 6].every((d) => currentValue.includes(d))

  return (
    <div className="space-y-3">
      {/* Quick selection buttons */}
      <div className="flex flex-wrap gap-1.5 text-xs">
        <button
          type="button"
          onClick={selectWeekdays}
          className={cn(
            'px-2 py-1 rounded transition-colors',
            isWeekdaysOnly
              ? 'bg-primary/20 text-primary border border-primary/30'
              : 'bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground'
          )}
          aria-label="Select weekdays only"
        >
          Weekdays
        </button>
        <button
          type="button"
          onClick={selectWeekend}
          className={cn(
            'px-2 py-1 rounded transition-colors',
            isWeekendOnly
              ? 'bg-primary/20 text-primary border border-primary/30'
              : 'bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground'
          )}
          aria-label="Select weekends only"
        >
          Weekend
        </button>
        <button
          type="button"
          onClick={selectAll}
          className={cn(
            'px-2 py-1 rounded transition-colors',
            isAllSelected
              ? 'bg-primary/20 text-primary border border-primary/30'
              : 'bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground'
          )}
          aria-label="Select all days"
        >
          All
        </button>
        <button
          type="button"
          onClick={clearAll}
          className="px-2 py-1 rounded bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground transition-colors"
          aria-label="Clear selection"
        >
          Clear
        </button>
      </div>

      {/* Weekday toggle buttons */}
      <div
        ref={containerRef}
        className="flex gap-1.5"
        role="group"
        aria-label="Select days of the week"
      >
        {WEEKDAY_DEFS.map((day, index) => {
          const isSelected = currentValue.includes(day.day)
          return (
            <TooltipProvider key={day.day}>
              <Tooltip delayDuration={400}>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    role="checkbox"
                    aria-checked={isSelected}
                    aria-label={day.fullName}
                    tabIndex={index === 0 ? 0 : -1}
                    data-weekday={day.day}
                    onClick={() => toggleDay(day.day)}
                    onKeyDown={(e) => handleKeyDown(e, day.day)}
                    className={cn(
                      'flex items-center justify-center',
                      'w-10 h-10 text-sm font-medium rounded-lg',
                      'border-2 transition-all duration-150',
                      'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
                      isSelected
                        ? 'bg-primary text-primary-foreground border-primary shadow-sm'
                        : 'bg-background hover:bg-muted border-input hover:border-primary/50'
                    )}
                  >
                    {day.label}
                  </button>
                </TooltipTrigger>
                <TooltipContent side="bottom">
                  <p>{day.fullName}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )
        })}
      </div>

      {/* Selection feedback */}
      <p className="text-xs text-muted-foreground">
        {currentValue.length === 0 && 'No days selected'}
        {currentValue.length === 7 && 'Every day'}
        {currentValue.length > 0 && currentValue.length < 7 && (
          <>
            {currentValue.length} day{currentValue.length !== 1 ? 's' : ''} selected
          </>
        )}
      </p>
    </div>
  )
}

function ParamRenderer({ name, schema, value, onChange }: ParamRendererProps) {
  switch (schema.type) {
    case 'string':
      return <StringParamRenderer name={name} schema={schema} value={value as string} onChange={onChange} />
    case 'number':
      return <NumberParamRenderer name={name} schema={schema} value={value as number} onChange={onChange} />
    case 'boolean':
      return <BooleanParamRenderer name={name} schema={schema} value={value as boolean} onChange={onChange} />
    case 'select':
      return <SelectParamRenderer name={name} schema={schema} value={value as string} onChange={onChange} />
    case 'multi-select':
      return <MultiSelectParamRenderer name={name} schema={schema} value={value as string[]} onChange={onChange} />
    case 'array':
      return <ArrayParamRenderer name={name} schema={schema} value={value as string[]} onChange={onChange} />
    case 'weekdays':
      return <WeekdaysParamRenderer name={name} schema={schema} value={value as number[]} onChange={onChange} />
    case 'expression':
      // Expression type is handled specially in RuleBuilderCard
      // This case is here for completeness if used standalone
      return <StringParamRenderer name={name} schema={schema} value={String(value || '')} onChange={onChange} />
    case 'jinja2-template':
      // Jinja2 template type is handled specially in RuleBuilderCard
      // This case is here for completeness if used standalone
      return <StringParamRenderer name={name} schema={schema} value={String(value || '')} onChange={onChange} />
    default:
      return <StringParamRenderer name={name} schema={schema} value={String(value || '')} onChange={onChange} />
  }
}

// =============================================================================
// Category Styling
// =============================================================================

const CATEGORY_STYLES: Record<RuleCategory, { label: string; color: string; bgColor: string }> = {
  basic: { label: 'Basic', color: 'text-blue-600', bgColor: 'bg-blue-500' },
  condition: { label: 'Condition', color: 'text-purple-600', bgColor: 'bg-purple-500' },
  combinator: { label: 'Combinator', color: 'text-orange-600', bgColor: 'bg-orange-500' },
  static: { label: 'Static', color: 'text-gray-600', bgColor: 'bg-gray-500' },
  advanced: { label: 'Advanced', color: 'text-emerald-600', bgColor: 'bg-emerald-500' },
}

// =============================================================================
// Rule Type Selector Component
// =============================================================================

interface RuleTypeSelectorProps {
  value: RuleType
  onChange: (type: RuleType) => void
  disableCombinators?: boolean
}

function RuleTypeSelector({ value, onChange, disableCombinators }: RuleTypeSelectorProps) {
  const basicRules = RuleTypeRegistry.getByCategory('basic')
  const conditionRules = RuleTypeRegistry.getByCategory('condition')
  const combinatorRules = RuleTypeRegistry.getByCategory('combinator')
  const staticRules = RuleTypeRegistry.getByCategory('static')
  const advancedRules = RuleTypeRegistry.getByCategory('advanced')

  return (
    <Select value={value} onValueChange={(v) => onChange(v as RuleType)}>
      <SelectTrigger className="h-9">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectGroup>
          <SelectLabel className="text-xs text-muted-foreground">Basic Rules</SelectLabel>
          {basicRules.map((def) => (
            <SelectItem key={def.type} value={def.type}>
              <span className="flex items-center gap-2">
                <span
                  className={cn('w-2 h-2 rounded-full', CATEGORY_STYLES[def.category].bgColor)}
                />
                {def.label}
              </span>
            </SelectItem>
          ))}
        </SelectGroup>

        <SelectGroup>
          <SelectLabel className="text-xs text-muted-foreground">Conditions</SelectLabel>
          {conditionRules.map((def) => (
            <SelectItem key={def.type} value={def.type}>
              <span className="flex items-center gap-2">
                <span
                  className={cn('w-2 h-2 rounded-full', CATEGORY_STYLES[def.category].bgColor)}
                />
                {def.label}
              </span>
            </SelectItem>
          ))}
        </SelectGroup>

        <SelectGroup>
          <SelectLabel className="text-xs text-muted-foreground">Advanced</SelectLabel>
          {advancedRules.map((def) => (
            <SelectItem key={def.type} value={def.type}>
              <span className="flex items-center gap-2">
                <span
                  className={cn('w-2 h-2 rounded-full', CATEGORY_STYLES[def.category].bgColor)}
                />
                {def.label}
              </span>
            </SelectItem>
          ))}
        </SelectGroup>

        <SelectGroup>
          <SelectLabel className="text-xs text-muted-foreground">Combinators</SelectLabel>
          {combinatorRules.map((def) => (
            <SelectItem key={def.type} value={def.type} disabled={disableCombinators}>
              <span className="flex items-center gap-2">
                <span
                  className={cn('w-2 h-2 rounded-full', CATEGORY_STYLES[def.category].bgColor)}
                />
                {def.label}
              </span>
            </SelectItem>
          ))}
        </SelectGroup>

        <SelectGroup>
          <SelectLabel className="text-xs text-muted-foreground">Static</SelectLabel>
          {staticRules.map((def) => (
            <SelectItem key={def.type} value={def.type}>
              <span className="flex items-center gap-2">
                <span
                  className={cn('w-2 h-2 rounded-full', CATEGORY_STYLES[def.category].bgColor)}
                />
                {def.label}
              </span>
            </SelectItem>
          ))}
        </SelectGroup>
      </SelectContent>
    </Select>
  )
}

// =============================================================================
// Rule Parameters Editor
// =============================================================================

interface RuleParamsEditorProps {
  definition: RuleTypeDefinition
  config: RuleConfig
  onChange: (config: RuleConfig) => void
}

function RuleParamsEditor({ definition, config, onChange }: RuleParamsEditorProps) {
  const params = Object.entries(definition.params)

  if (params.length === 0) {
    return (
      <p className="text-sm text-muted-foreground italic py-2">
        This rule type has no configurable parameters.
      </p>
    )
  }

  const handleParamChange = (name: string, value: unknown) => {
    onChange({
      ...config,
      [name]: value,
    })
  }

  return (
    <div className="space-y-4">
      {params.map(([name, schema]) => (
        <div key={name} className="space-y-1.5">
          <div className="flex items-center gap-2">
            <Label className="text-sm font-medium">
              {schema.label}
              {schema.required && <span className="text-destructive ml-0.5">*</span>}
            </Label>
            {schema.description && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
                  </TooltipTrigger>
                  <TooltipContent side="right" className="max-w-xs">
                    <p className="text-sm">{schema.description}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
          </div>
          <ParamRenderer
            name={name}
            schema={schema}
            value={config[name]}
            onChange={(v) => handleParamChange(name, v)}
          />
        </div>
      ))}
    </div>
  )
}

// =============================================================================
// Combinator Sub-rules Editor
// =============================================================================

interface CombinatorEditorProps {
  config: RuleConfig
  onChange: (config: RuleConfig) => void
  depth: number
}

function CombinatorEditor({ config, onChange, depth }: CombinatorEditorProps) {
  const isNotRule = config.type === 'not'

  const handleAddSubRule = () => {
    onChange({
      ...config,
      rules: [...(config.rules || []), RuleTypeRegistry.createDefaultConfig('always')],
    })
  }

  const handleRemoveSubRule = (index: number) => {
    const newRules = [...(config.rules || [])]
    newRules.splice(index, 1)
    onChange({
      ...config,
      rules: newRules,
    })
  }

  const handleSubRuleChange = (index: number, newRule: RuleConfig) => {
    const newRules = [...(config.rules || [])]
    newRules[index] = newRule
    onChange({
      ...config,
      rules: newRules,
    })
  }

  return (
    <div className="space-y-3 mt-4">
      <div className="flex items-center justify-between">
        <Label className="text-sm font-medium">
          {isNotRule ? 'Rule to Negate' : 'Sub-rules'}
        </Label>
        {!isNotRule && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleAddSubRule}
            className="h-7 text-xs"
          >
            <Plus className="h-3 w-3 mr-1" />
            Add Rule
          </Button>
        )}
      </div>

      <div className="space-y-2 pl-3 border-l-2 border-muted">
        {(config.rules || []).map((rule, index) => (
          <div key={index} className="relative group">
            <RuleBuilderCard
              config={rule}
              onChange={(newRule) => handleSubRuleChange(index, newRule)}
              depth={depth + 1}
              showRemove={!isNotRule && (config.rules?.length || 0) > 1}
              onRemove={() => handleRemoveSubRule(index)}
            />
          </div>
        ))}

        {!isNotRule && (!config.rules || config.rules.length === 0) && (
          <p className="text-sm text-muted-foreground text-center py-4 bg-muted/50 rounded">
            No sub-rules. Click "Add Rule" to add at least one rule.
          </p>
        )}
      </div>
    </div>
  )
}

// =============================================================================
// Rule Builder Card (Single Rule)
// =============================================================================

interface RuleBuilderCardProps {
  config: RuleConfig
  onChange: (config: RuleConfig) => void
  depth?: number
  showRemove?: boolean
  onRemove?: () => void
}

function RuleBuilderCard({
  config,
  onChange,
  depth = 0,
  showRemove,
  onRemove,
}: RuleBuilderCardProps) {
  const { maxDepth, onCopyRule } = useContext(RuleBuilderContext)
  const [isExpanded, setIsExpanded] = useState(true)

  const definition = RuleTypeRegistry.get(config.type)
  const isCombinator = definition?.category === 'combinator'
  const isValid = RuleTypeRegistry.validate(config)

  const handleTypeChange = useCallback(
    (newType: RuleType) => {
      const newConfig = RuleTypeRegistry.createDefaultConfig(newType)
      onChange(newConfig)
    },
    [onChange]
  )

  const categoryStyle = definition ? CATEGORY_STYLES[definition.category] : CATEGORY_STYLES.basic

  // Determine border color based on depth
  const depthColors = [
    'border-l-primary',
    'border-l-blue-500',
    'border-l-purple-500',
    'border-l-orange-500',
  ]
  const borderColor = depth > 0 ? depthColors[depth % depthColors.length] : ''

  return (
    <Card className={cn('relative transition-shadow', depth > 0 && `border-l-4 ${borderColor}`)}>
      <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
        <CardHeader className="py-3 px-4">
          <div className="flex items-center justify-between gap-2">
            <CollapsibleTrigger asChild>
              <button
                type="button"
                className="flex items-center gap-2 hover:text-primary transition-colors"
              >
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
                <CardTitle className="text-sm font-medium">
                  {depth === 0 ? 'Rule Configuration' : definition?.label || config.type}
                </CardTitle>
              </button>
            </CollapsibleTrigger>

            <div className="flex items-center gap-2">
              {definition && (
                <Badge
                  variant="secondary"
                  className={cn('text-xs text-white', categoryStyle.bgColor)}
                >
                  {categoryStyle.label}
                </Badge>
              )}
              {isValid ? (
                <CheckCircle2 className="h-4 w-4 text-green-500" />
              ) : (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <AlertTriangle className="h-4 w-4 text-amber-500" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Configuration incomplete</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
              {onCopyRule && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6"
                        onClick={() => onCopyRule(config)}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Copy rule configuration</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
              {showRemove && onRemove && (
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 text-destructive hover:text-destructive"
                  onClick={onRemove}
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              )}
            </div>
          </div>
        </CardHeader>

        <CollapsibleContent>
          <CardContent className="py-3 px-4 pt-0 space-y-4">
            {/* Rule Type Selector */}
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <Label className="text-sm font-medium">Rule Type</Label>
                {definition && (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent side="right" className="max-w-xs">
                        <p className="text-sm">{definition.description}</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )}
              </div>
              <RuleTypeSelector
                value={config.type}
                onChange={handleTypeChange}
                disableCombinators={depth >= maxDepth}
              />
            </div>

            {/* Parameters */}
            {/* Special handling for expression rule type */}
            {config.type === 'expression' && (
              <ExpressionRuleEditor
                config={{
                  expression: (config.expression as string) || '',
                  timeout_seconds: config.timeout_seconds as number | undefined,
                }}
                onChange={(exprConfig: ExpressionConfig) => {
                  onChange({
                    ...config,
                    expression: exprConfig.expression,
                    timeout_seconds: exprConfig.timeout_seconds,
                  })
                }}
              />
            )}

            {/* Special handling for jinja2 rule type */}
            {config.type === 'jinja2' && (
              <Jinja2RuleEditor
                config={{
                  type: 'jinja2',
                  template: (config.template as string) || '{{ true }}',
                  expected_result: (config.expected_result as string) || 'true',
                }}
                onChange={(jinja2Config: Jinja2RuleConfig) => {
                  onChange({
                    ...config,
                    template: jinja2Config.template,
                    expected_result: jinja2Config.expected_result,
                  })
                }}
              />
            )}

            {/* Standard parameter editor for non-expression and non-jinja2 rules */}
            {config.type !== 'expression' &&
              config.type !== 'jinja2' &&
              definition &&
              Object.keys(definition.params).length > 0 && (
                <RuleParamsEditor definition={definition} config={config} onChange={onChange} />
              )}

            {/* Static rule messages */}
            {config.type === 'always' && (
              <p className="text-sm text-muted-foreground bg-muted/50 p-3 rounded">
                This rule always matches. Use as a catch-all or fallback rule.
              </p>
            )}
            {config.type === 'never' && (
              <p className="text-sm text-muted-foreground bg-muted/50 p-3 rounded">
                This rule never matches. Use to temporarily disable routing without deleting.
              </p>
            )}

            {/* Combinator sub-rules */}
            {isCombinator && depth < maxDepth && (
              <CombinatorEditor config={config} onChange={onChange} depth={depth} />
            )}

            {isCombinator && depth >= maxDepth && (
              <p className="text-sm text-amber-600 bg-amber-50 dark:bg-amber-950 p-3 rounded">
                Maximum nesting depth reached. Cannot add more combinators.
              </p>
            )}
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  )
}

// =============================================================================
// Main RuleBuilder Component
// =============================================================================

export interface RuleBuilderProps {
  value: RuleConfig
  onChange: (config: RuleConfig) => void
  maxDepth?: number
  onCopyRule?: (config: RuleConfig) => void
  className?: string
}

export function RuleBuilder({
  value,
  onChange,
  maxDepth = 3,
  onCopyRule,
  className,
}: RuleBuilderProps) {
  const contextValue = useMemo(
    () => ({
      maxDepth,
      onCopyRule,
    }),
    [maxDepth, onCopyRule]
  )

  return (
    <RuleBuilderContext.Provider value={contextValue}>
      <div className={className}>
        <RuleBuilderCard config={value} onChange={onChange} />
      </div>
    </RuleBuilderContext.Provider>
  )
}

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Convert a RuleConfig to JSON string for API submission
 */
export function ruleConfigToJson(config: RuleConfig): string {
  return JSON.stringify(config, null, 2)
}

/**
 * Parse a JSON string to RuleConfig
 */
export function jsonToRuleConfig(json: string): RuleConfig | null {
  try {
    const parsed = JSON.parse(json)
    if (parsed && typeof parsed.type === 'string') {
      return parsed as RuleConfig
    }
    return null
  } catch {
    return null
  }
}

/**
 * Format weekdays array to a human-readable string.
 * Uses ranges when consecutive days are selected (e.g., "Mon-Fri" instead of "Mon, Tue, Wed, Thu, Fri").
 *
 * @param weekdays - Array of weekday numbers (0=Monday to 6=Sunday)
 * @returns Formatted string like "Mon-Fri" or "Mon, Wed, Fri"
 */
export function formatWeekdaysForSummary(weekdays: number[]): string {
  if (!weekdays || weekdays.length === 0) return ''
  if (weekdays.length === 7) return 'Every day'

  const sorted = [...weekdays].sort((a, b) => a - b)
  const dayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

  // Check for common patterns
  const isWeekdays =
    sorted.length === 5 && [0, 1, 2, 3, 4].every((d) => sorted.includes(d))
  if (isWeekdays) return 'Mon-Fri'

  const isWeekend =
    sorted.length === 2 && [5, 6].every((d) => sorted.includes(d))
  if (isWeekend) return 'Sat-Sun'

  // Build ranges for consecutive days
  const ranges: Array<{ start: number; end: number }> = []
  let rangeStart = sorted[0]
  let rangeEnd = sorted[0]

  for (let i = 1; i < sorted.length; i++) {
    if (sorted[i] === rangeEnd + 1) {
      rangeEnd = sorted[i]
    } else {
      ranges.push({ start: rangeStart, end: rangeEnd })
      rangeStart = sorted[i]
      rangeEnd = sorted[i]
    }
  }
  ranges.push({ start: rangeStart, end: rangeEnd })

  // Format ranges
  return ranges
    .map((range) => {
      if (range.start === range.end) {
        return dayLabels[range.start]
      } else if (range.end - range.start >= 2) {
        return `${dayLabels[range.start]}-${dayLabels[range.end]}`
      } else {
        return `${dayLabels[range.start]}, ${dayLabels[range.end]}`
      }
    })
    .join(', ')
}

/**
 * Format hour to a localized time string.
 *
 * @param hour - Hour in 24-hour format (0-23)
 * @returns Formatted time string like "09:00" or "9:00 AM"
 */
export function formatHourForSummary(hour: number): string {
  return `${hour.toString().padStart(2, '0')}:00`
}

/**
 * Get a human-readable summary of a rule configuration.
 * Provides concise descriptions of rule parameters suitable for display in lists.
 */
export function getRuleSummary(config: RuleConfig): string {
  const definition = RuleTypeRegistry.get(config.type)
  if (!definition) return config.type

  switch (config.type) {
    case 'severity':
      return `Severity >= ${config.min_severity || 'high'}`
    case 'issue_count':
      return `Issues >= ${config.min_count || 1}`
    case 'pass_rate':
      return `Pass rate <= ${((config.max_pass_rate as number) || 0.9) * 100}%`
    case 'time_window': {
      const startHour = (config.start_hour as number) ?? 9
      const endHour = (config.end_hour as number) ?? 17
      const weekdays = (config.weekdays as number[]) ?? [0, 1, 2, 3, 4]
      const timezone = config.timezone as string | undefined

      const timeRange = `${formatHourForSummary(startHour)}-${formatHourForSummary(endHour)}`
      const weekdayStr = formatWeekdaysForSummary(weekdays)

      let summary = ''
      if (weekdayStr) {
        summary = `${weekdayStr}, ${timeRange}`
      } else {
        summary = timeRange
      }

      if (timezone) {
        summary += ` (${timezone})`
      }

      return summary
    }
    case 'tag':
      return `Tags: ${((config.tags as string[]) || []).join(', ') || 'none'}`
    case 'data_asset':
      return `Asset: ${config.pattern || '*'}`
    case 'metadata':
      return `${config.key} ${config.operator || '='} ${config.value}`
    case 'status':
      return `Status: ${((config.statuses as string[]) || []).join(', ')}`
    case 'error':
      return `Error: ${config.error_pattern || '.*'}`
    case 'always':
      return 'Always match'
    case 'never':
      return 'Never match'
    case 'all_of':
      return `ALL of ${(config.rules || []).length} rules`
    case 'any_of':
      return `ANY of ${(config.rules || []).length} rules`
    case 'not':
      return `NOT ${config.rules?.[0] ? getRuleSummary(config.rules[0]) : '...'}`
    default:
      return definition.label
  }
}

export default RuleBuilder
