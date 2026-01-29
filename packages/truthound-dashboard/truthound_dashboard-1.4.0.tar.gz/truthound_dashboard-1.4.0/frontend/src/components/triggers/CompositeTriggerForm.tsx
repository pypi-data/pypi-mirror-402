/**
 * CompositeTriggerForm - Configure composite triggers with AND/OR logic.
 */

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Plus, Trash2, Clock, Timer, TrendingUp, Zap, GripVertical } from 'lucide-react'
import type { TriggerConfig } from './TriggerBuilder'

interface CompositeTriggerFormProps {
  operator: 'and' | 'or'
  triggers: TriggerConfig[]
  onChange: (operator: 'and' | 'or', triggers: TriggerConfig[]) => void
}

const TRIGGER_TYPES_FOR_COMPOSITE = [
  { type: 'cron', label: 'Cron', icon: Clock },
  { type: 'interval', label: 'Interval', icon: Timer },
  { type: 'data_change', label: 'Data Change', icon: TrendingUp },
  { type: 'event', label: 'Event', icon: Zap },
] as const

const DEFAULT_TRIGGER_CONFIGS: Record<string, TriggerConfig> = {
  cron: { type: 'cron', expression: '0 0 * * *' },
  interval: { type: 'interval', hours: 1 },
  data_change: {
    type: 'data_change',
    change_threshold: 0.05,
    metrics: ['row_count'],
    check_interval_minutes: 60,
  },
  event: { type: 'event', event_types: ['schema_changed'] },
}

export function CompositeTriggerForm({
  operator,
  triggers,
  onChange,
}: CompositeTriggerFormProps) {
  const [selectedTypeToAdd, setSelectedTypeToAdd] = useState<string>('cron')

  const addTrigger = () => {
    const newTrigger = DEFAULT_TRIGGER_CONFIGS[selectedTypeToAdd]
    onChange(operator, [...triggers, { ...newTrigger }])
  }

  const removeTrigger = (index: number) => {
    const newTriggers = triggers.filter((_, i) => i !== index)
    onChange(operator, newTriggers)
  }

  const updateTrigger = (index: number, updates: Partial<TriggerConfig>) => {
    const newTriggers = triggers.map((t, i) =>
      i === index ? { ...t, ...updates } : t
    )
    onChange(operator, newTriggers)
  }

  const getTriggerSummary = (trigger: TriggerConfig): string => {
    switch (trigger.type) {
      case 'cron':
        return `Cron: ${trigger.expression || '(not set)'}`
      case 'interval':
        const parts: string[] = []
        if (trigger.days) parts.push(`${trigger.days}d`)
        if (trigger.hours) parts.push(`${trigger.hours}h`)
        if (trigger.minutes) parts.push(`${trigger.minutes}m`)
        if (trigger.seconds) parts.push(`${trigger.seconds}s`)
        return `Every ${parts.join(' ') || '(not set)'}`
      case 'data_change':
        const threshold = (trigger.change_threshold || 0.05) * 100
        return `Data change ≥${threshold.toFixed(0)}%`
      case 'event':
        const events = trigger.event_types || []
        return `Events: ${events.slice(0, 2).join(', ')}${events.length > 2 ? '...' : ''}`
      default:
        return trigger.type
    }
  }

  const getTypeIcon = (type: string) => {
    const typeInfo = TRIGGER_TYPES_FOR_COMPOSITE.find((t) => t.type === type)
    return typeInfo?.icon || Clock
  }

  return (
    <div className="space-y-4">
      {/* Operator selector */}
      <div className="space-y-2">
        <Label>Combination Logic</Label>
        <div className="flex gap-2">
          <Button
            type="button"
            variant={operator === 'and' ? 'default' : 'outline'}
            onClick={() => onChange('and', triggers)}
            className="flex-1"
          >
            <span className="font-bold mr-2">AND</span>
            <span className="text-xs opacity-75">All must match</span>
          </Button>
          <Button
            type="button"
            variant={operator === 'or' ? 'default' : 'outline'}
            onClick={() => onChange('or', triggers)}
            className="flex-1"
          >
            <span className="font-bold mr-2">OR</span>
            <span className="text-xs opacity-75">Any must match</span>
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">
          {operator === 'and'
            ? 'Validation runs when ALL triggers fire simultaneously'
            : 'Validation runs when ANY trigger fires'}
        </p>
      </div>

      {/* Triggers list */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label>Triggers ({triggers.length})</Label>
        </div>

        <div className="space-y-2">
          {triggers.map((trigger, index) => {
            const TypeIcon = getTypeIcon(trigger.type)
            return (
              <Card key={index} className="relative">
                <CardHeader className="py-2 px-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <GripVertical className="h-4 w-4 text-muted-foreground cursor-grab" />
                      <TypeIcon className="h-4 w-4" />
                      <CardTitle className="text-sm">{trigger.type}</CardTitle>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="text-xs">
                        {getTriggerSummary(trigger)}
                      </Badge>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeTrigger(index)}
                        disabled={triggers.length <= 2}
                        className="h-6 w-6 p-0"
                      >
                        <Trash2 className="h-3.5 w-3.5 text-destructive" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="py-2 px-3">
                  <CompositeTriggerItemForm
                    trigger={trigger}
                    onChange={(updates) => updateTrigger(index, updates)}
                  />
                </CardContent>
              </Card>
            )
          })}
        </div>

        {triggers.length < 2 && (
          <p className="text-sm text-amber-600">
            Add at least 2 triggers for composite logic
          </p>
        )}
      </div>

      {/* Add trigger */}
      <div className="flex gap-2 items-end">
        <div className="flex-1 space-y-1">
          <Label className="text-xs">Add Trigger</Label>
          <Select
            value={selectedTypeToAdd}
            onValueChange={setSelectedTypeToAdd}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {TRIGGER_TYPES_FOR_COMPOSITE.map(({ type, label, icon: Icon }) => (
                <SelectItem key={type} value={type}>
                  <div className="flex items-center gap-2">
                    <Icon className="h-4 w-4" />
                    {label}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Button type="button" onClick={addTrigger} size="sm">
          <Plus className="h-4 w-4 mr-1" />
          Add
        </Button>
      </div>

      {/* Summary */}
      <div className="p-3 bg-muted/50 rounded text-sm">
        <strong>Logic:</strong> Trigger when{' '}
        {operator === 'and' ? (
          <>
            <Badge variant="outline" className="mx-1">
              ALL {triggers.length}
            </Badge>{' '}
            conditions are met
          </>
        ) : (
          <>
            <Badge variant="outline" className="mx-1">
              ANY
            </Badge>{' '}
            of {triggers.length} conditions is met
          </>
        )}
      </div>
    </div>
  )
}

// Simplified inline editor for composite trigger items
function CompositeTriggerItemForm({
  trigger,
  onChange,
}: {
  trigger: TriggerConfig
  onChange: (updates: Partial<TriggerConfig>) => void
}) {
  switch (trigger.type) {
    case 'cron':
      return (
        <div className="flex items-center gap-2">
          <Label className="text-xs shrink-0">Expression:</Label>
          <input
            type="text"
            value={trigger.expression || ''}
            onChange={(e) => onChange({ expression: e.target.value })}
            className="flex-1 px-2 py-1 text-sm border rounded font-mono"
            placeholder="0 0 * * *"
          />
        </div>
      )

    case 'interval':
      return (
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            <Label className="text-xs">Days:</Label>
            <input
              type="number"
              min={0}
              value={trigger.days || ''}
              onChange={(e) =>
                onChange({ days: parseInt(e.target.value) || undefined })
              }
              className="w-14 px-2 py-1 text-sm border rounded"
            />
          </div>
          <div className="flex items-center gap-1">
            <Label className="text-xs">Hours:</Label>
            <input
              type="number"
              min={0}
              max={23}
              value={trigger.hours || ''}
              onChange={(e) =>
                onChange({ hours: parseInt(e.target.value) || undefined })
              }
              className="w-14 px-2 py-1 text-sm border rounded"
            />
          </div>
          <div className="flex items-center gap-1">
            <Label className="text-xs">Min:</Label>
            <input
              type="number"
              min={0}
              max={59}
              value={trigger.minutes || ''}
              onChange={(e) =>
                onChange({ minutes: parseInt(e.target.value) || undefined })
              }
              className="w-14 px-2 py-1 text-sm border rounded"
            />
          </div>
        </div>
      )

    case 'data_change':
      return (
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            <Label className="text-xs">Threshold:</Label>
            <input
              type="number"
              min={1}
              max={100}
              value={(trigger.change_threshold || 0.05) * 100}
              onChange={(e) =>
                onChange({
                  change_threshold: (parseInt(e.target.value) || 5) / 100,
                })
              }
              className="w-16 px-2 py-1 text-sm border rounded"
            />
            <span className="text-xs">%</span>
          </div>
        </div>
      )

    case 'event':
      return (
        <div className="flex items-center gap-2 flex-wrap">
          {['schema_changed', 'drift_detected', 'validation_failed'].map(
            (event) => (
              <label key={event} className="flex items-center gap-1 text-xs">
                <input
                  type="checkbox"
                  checked={(trigger.event_types || []).includes(event)}
                  onChange={(e) => {
                    const current = trigger.event_types || []
                    const updated = e.target.checked
                      ? [...current, event]
                      : current.filter((t) => t !== event)
                    onChange({ event_types: updated })
                  }}
                  className="rounded"
                />
                {event.replace('_', ' ')}
              </label>
            )
          )}
        </div>
      )

    default:
      return <span className="text-xs text-muted-foreground">No options</span>
  }
}
