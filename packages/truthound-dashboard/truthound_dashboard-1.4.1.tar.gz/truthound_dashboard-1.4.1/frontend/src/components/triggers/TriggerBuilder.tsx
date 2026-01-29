/**
 * TriggerBuilder - Main component for configuring schedule triggers.
 *
 * Provides a unified interface for configuring all trigger types:
 * - Cron: Traditional cron expressions
 * - Interval: Fixed time intervals
 * - DataChange: Profile-based change detection
 * - Composite: Combine multiple triggers
 * - Event: Respond to system events
 * - Webhook: External HTTP triggers
 * - Manual: API-only execution
 */

import { useState, useCallback, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { TriggerTypeSelector } from './TriggerTypeSelector'
import { CronTriggerForm } from './CronTriggerForm'
import { IntervalTriggerForm } from './IntervalTriggerForm'
import { DataChangeTriggerForm } from './DataChangeTriggerForm'
import { CompositeTriggerForm } from './CompositeTriggerForm'
import { TriggerPreview } from './TriggerPreview'
import { Clock, Timer, TrendingUp, Layers, Zap, Hand, Webhook, Copy, Check, Plus, X } from 'lucide-react'

export type TriggerType = 'cron' | 'interval' | 'data_change' | 'composite' | 'event' | 'webhook' | 'manual'

export interface TriggerConfig {
  type: TriggerType
  // Cron specific
  expression?: string
  timezone?: string
  // Interval specific
  seconds?: number
  minutes?: number
  hours?: number
  days?: number
  // Data change specific
  change_threshold?: number
  metrics?: string[]
  check_interval_minutes?: number
  // Composite specific
  operator?: 'and' | 'or'
  triggers?: TriggerConfig[]
  // Event specific
  event_types?: string[]
  source_filter?: string[]
  // Webhook specific
  webhook_secret?: string
  allowed_sources?: string[]
  require_signature?: boolean
  cooldown_minutes?: number
}

interface TriggerBuilderProps {
  value: TriggerConfig
  onChange: (config: TriggerConfig) => void
  /** Legacy cron expression for backward compatibility */
  legacyCronExpression?: string
  /** Show compact mode (less spacing) */
  compact?: boolean
}

const TRIGGER_TYPE_INFO: Record<TriggerType, {
  icon: React.ComponentType<{ className?: string }>
  label: string
  description: string
}> = {
  cron: {
    icon: Clock,
    label: 'Cron Schedule',
    description: 'Schedule using cron expressions (e.g., daily at midnight)',
  },
  interval: {
    icon: Timer,
    label: 'Interval',
    description: 'Run at fixed time intervals (e.g., every 6 hours)',
  },
  data_change: {
    icon: TrendingUp,
    label: 'Data Change',
    description: 'Trigger when data profile changes by a threshold percentage',
  },
  composite: {
    icon: Layers,
    label: 'Composite',
    description: 'Combine multiple triggers with AND/OR logic',
  },
  event: {
    icon: Zap,
    label: 'Event',
    description: 'Trigger in response to system events (e.g., schema changes)',
  },
  webhook: {
    icon: Webhook,
    label: 'Webhook',
    description: 'Trigger from external HTTP requests (e.g., data pipelines)',
  },
  manual: {
    icon: Hand,
    label: 'Manual',
    description: 'Only run when manually triggered via API',
  },
}

export function TriggerBuilder({
  value,
  onChange,
  legacyCronExpression,
  compact = false,
}: TriggerBuilderProps) {
  const [triggerType, setTriggerType] = useState<TriggerType>(value.type || 'cron')

  // Initialize from legacy cron expression if no type is set
  useEffect(() => {
    if (!value.type && legacyCronExpression) {
      onChange({
        type: 'cron',
        expression: legacyCronExpression,
      })
    }
  }, [legacyCronExpression, value.type, onChange])

  const handleTypeChange = useCallback((newType: TriggerType) => {
    setTriggerType(newType)

    // Create default config for new type
    const defaultConfigs: Record<TriggerType, TriggerConfig> = {
      cron: { type: 'cron', expression: '0 0 * * *' },
      interval: { type: 'interval', hours: 1 },
      data_change: {
        type: 'data_change',
        change_threshold: 0.05,
        metrics: ['row_count', 'null_percentage', 'distinct_count'],
        check_interval_minutes: 60,
      },
      composite: {
        type: 'composite',
        operator: 'and',
        triggers: [
          { type: 'cron', expression: '0 0 * * *' },
          { type: 'data_change', change_threshold: 0.05 },
        ],
      },
      event: {
        type: 'event',
        event_types: ['schema_changed'],
      },
      webhook: {
        type: 'webhook',
        allowed_sources: [],
        require_signature: false,
        cooldown_minutes: 15,
      },
      manual: { type: 'manual' },
    }

    onChange(defaultConfigs[newType])
  }, [onChange])

  const handleConfigChange = useCallback((updates: Partial<TriggerConfig>) => {
    onChange({ ...value, ...updates })
  }, [value, onChange])

  const typeInfo = TRIGGER_TYPE_INFO[triggerType]
  const TypeIcon = typeInfo.icon

  return (
    <div className={compact ? 'space-y-3' : 'space-y-4'}>
      {/* Trigger Type Selector */}
      <TriggerTypeSelector
        value={triggerType}
        onChange={handleTypeChange}
        compact={compact}
      />

      {/* Type-specific Configuration */}
      <Card>
        <CardHeader className={compact ? 'pb-2' : undefined}>
          <CardTitle className="text-base flex items-center gap-2">
            <TypeIcon className="h-4 w-4" />
            {typeInfo.label} Configuration
          </CardTitle>
          <CardDescription>{typeInfo.description}</CardDescription>
        </CardHeader>
        <CardContent>
          {triggerType === 'cron' && (
            <CronTriggerForm
              expression={value.expression || '0 0 * * *'}
              timezone={value.timezone}
              onChange={(expression, timezone) =>
                handleConfigChange({ expression, timezone })
              }
            />
          )}

          {triggerType === 'interval' && (
            <IntervalTriggerForm
              seconds={value.seconds}
              minutes={value.minutes}
              hours={value.hours}
              days={value.days}
              onChange={(interval) => handleConfigChange(interval)}
            />
          )}

          {triggerType === 'data_change' && (
            <DataChangeTriggerForm
              changeThreshold={value.change_threshold || 0.05}
              metrics={value.metrics || ['row_count', 'null_percentage', 'distinct_count']}
              checkIntervalMinutes={value.check_interval_minutes || 60}
              onChange={(config) =>
                handleConfigChange({
                  change_threshold: config.changeThreshold,
                  metrics: config.metrics,
                  check_interval_minutes: config.checkIntervalMinutes,
                })
              }
            />
          )}

          {triggerType === 'composite' && (
            <CompositeTriggerForm
              operator={value.operator || 'and'}
              triggers={value.triggers || []}
              onChange={(operator, triggers) =>
                handleConfigChange({ operator, triggers })
              }
            />
          )}

          {triggerType === 'event' && (
            <EventTriggerForm
              eventTypes={value.event_types || []}
              onChange={(event_types) => handleConfigChange({ event_types })}
            />
          )}

          {triggerType === 'webhook' && (
            <WebhookTriggerForm
              allowedSources={value.allowed_sources || []}
              requireSignature={value.require_signature || false}
              cooldownMinutes={value.cooldown_minutes || 15}
              onChange={(config) =>
                handleConfigChange({
                  allowed_sources: config.allowedSources,
                  require_signature: config.requireSignature,
                  cooldown_minutes: config.cooldownMinutes,
                })
              }
            />
          )}

          {triggerType === 'manual' && (
            <div className="text-sm text-muted-foreground py-4 text-center">
              Manual triggers only execute when explicitly invoked via the API or "Run Now" button.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Preview */}
      <TriggerPreview config={value} />
    </div>
  )
}

// Event Trigger Form (inline since it's simple)
function EventTriggerForm({
  eventTypes,
  onChange,
}: {
  eventTypes: string[]
  onChange: (eventTypes: string[]) => void
}) {
  const AVAILABLE_EVENTS = [
    { value: 'validation_completed', label: 'Validation Completed' },
    { value: 'validation_failed', label: 'Validation Failed' },
    { value: 'schema_changed', label: 'Schema Changed' },
    { value: 'drift_detected', label: 'Drift Detected' },
    { value: 'profile_updated', label: 'Profile Updated' },
    { value: 'source_created', label: 'Source Created' },
    { value: 'source_updated', label: 'Source Updated' },
  ]

  const toggleEvent = (event: string) => {
    if (eventTypes.includes(event)) {
      onChange(eventTypes.filter((e) => e !== event))
    } else {
      onChange([...eventTypes, event])
    }
  }

  return (
    <div className="space-y-3">
      <label className="text-sm font-medium">Trigger on Events:</label>
      <div className="grid grid-cols-2 gap-2">
        {AVAILABLE_EVENTS.map((event) => (
          <label
            key={event.value}
            className="flex items-center gap-2 p-2 border rounded cursor-pointer hover:bg-muted/50"
          >
            <input
              type="checkbox"
              checked={eventTypes.includes(event.value)}
              onChange={() => toggleEvent(event.value)}
              className="rounded"
            />
            <span className="text-sm">{event.label}</span>
          </label>
        ))}
      </div>
      {eventTypes.length === 0 && (
        <p className="text-sm text-amber-600">Select at least one event type</p>
      )}
    </div>
  )
}

// Webhook Trigger Form
function WebhookTriggerForm({
  allowedSources,
  requireSignature,
  cooldownMinutes,
  onChange,
}: {
  allowedSources: string[]
  requireSignature: boolean
  cooldownMinutes: number
  onChange: (config: {
    allowedSources: string[]
    requireSignature: boolean
    cooldownMinutes: number
  }) => void
}) {
  const [newSource, setNewSource] = useState('')
  const [copied, setCopied] = useState(false)

  // Generate webhook URL (in real implementation this would come from backend)
  const webhookUrl = `${window.location.origin}/api/v1/triggers/webhook`

  const addSource = () => {
    if (newSource.trim() && !allowedSources.includes(newSource.trim())) {
      onChange({
        allowedSources: [...allowedSources, newSource.trim()],
        requireSignature,
        cooldownMinutes,
      })
      setNewSource('')
    }
  }

  const removeSource = (source: string) => {
    onChange({
      allowedSources: allowedSources.filter((s) => s !== source),
      requireSignature,
      cooldownMinutes,
    })
  }

  const copyUrl = async () => {
    await navigator.clipboard.writeText(webhookUrl)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-4">
      {/* Webhook URL */}
      <div className="space-y-2">
        <Label>Webhook URL</Label>
        <div className="flex gap-2">
          <Input
            value={webhookUrl}
            readOnly
            className="font-mono text-sm"
          />
          <Button type="button" variant="outline" size="icon" onClick={copyUrl}>
            {copied ? (
              <Check className="h-4 w-4 text-green-500" />
            ) : (
              <Copy className="h-4 w-4" />
            )}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">
          POST requests to this URL will trigger the validation
        </p>
      </div>

      {/* Allowed Sources */}
      <div className="space-y-2">
        <Label>Allowed Sources (optional)</Label>
        <p className="text-xs text-muted-foreground">
          Restrict which systems can trigger this webhook. Leave empty to allow all.
        </p>
        <div className="flex gap-2">
          <Input
            value={newSource}
            onChange={(e) => setNewSource(e.target.value)}
            placeholder="e.g., airflow, jenkins, github"
            onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addSource())}
          />
          <Button type="button" variant="outline" size="icon" onClick={addSource}>
            <Plus className="h-4 w-4" />
          </Button>
        </div>
        {allowedSources.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2">
            {allowedSources.map((source) => (
              <Badge key={source} variant="secondary" className="gap-1">
                {source}
                <button
                  type="button"
                  onClick={() => removeSource(source)}
                  className="ml-1 hover:text-destructive"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
          </div>
        )}
      </div>

      {/* Security Options */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={requireSignature}
              onChange={(e) =>
                onChange({
                  allowedSources,
                  requireSignature: e.target.checked,
                  cooldownMinutes,
                })
              }
              className="rounded"
            />
            <span className="text-sm">Require HMAC signature</span>
          </label>
          <p className="text-xs text-muted-foreground">
            Verify X-Webhook-Signature header
          </p>
        </div>
        <div className="space-y-2">
          <Label>Cooldown (minutes)</Label>
          <Input
            type="number"
            min={1}
            max={1440}
            value={cooldownMinutes}
            onChange={(e) =>
              onChange({
                allowedSources,
                requireSignature,
                cooldownMinutes: parseInt(e.target.value) || 15,
              })
            }
          />
        </div>
      </div>

      {/* Request Example */}
      <div className="space-y-2">
        <Label>Example Request</Label>
        <pre className="bg-muted p-3 rounded text-xs font-mono overflow-x-auto">
{`curl -X POST "${webhookUrl}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "source": "airflow",
    "event_type": "dag_completed",
    "payload": {"dag_id": "etl_pipeline"}
  }'`}
        </pre>
      </div>
    </div>
  )
}
