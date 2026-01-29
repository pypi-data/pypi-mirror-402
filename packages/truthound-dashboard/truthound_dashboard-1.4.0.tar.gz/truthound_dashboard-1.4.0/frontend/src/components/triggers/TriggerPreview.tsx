/**
 * TriggerPreview - Display a summary of trigger configuration.
 */

import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Clock,
  Timer,
  TrendingUp,
  Layers,
  Zap,
  Hand,
  Calendar,
  CheckCircle2,
} from 'lucide-react'
import type { TriggerConfig } from './TriggerBuilder'

interface TriggerPreviewProps {
  config: TriggerConfig
}

export function TriggerPreview({ config }: TriggerPreviewProps) {
  const getTypeIcon = () => {
    switch (config.type) {
      case 'cron':
        return <Clock className="h-4 w-4" />
      case 'interval':
        return <Timer className="h-4 w-4" />
      case 'data_change':
        return <TrendingUp className="h-4 w-4" />
      case 'composite':
        return <Layers className="h-4 w-4" />
      case 'event':
        return <Zap className="h-4 w-4" />
      case 'manual':
        return <Hand className="h-4 w-4" />
      default:
        return <Calendar className="h-4 w-4" />
    }
  }

  const getTypeLabel = () => {
    switch (config.type) {
      case 'cron':
        return 'Cron Schedule'
      case 'interval':
        return 'Time Interval'
      case 'data_change':
        return 'Data Change'
      case 'composite':
        return 'Composite'
      case 'event':
        return 'Event-Driven'
      case 'manual':
        return 'Manual Only'
      default:
        return config.type
    }
  }

  const renderDetails = () => {
    switch (config.type) {
      case 'cron':
        return (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground text-sm">Expression:</span>
              <code className="px-2 py-0.5 bg-muted rounded text-sm font-mono">
                {config.expression || '(not set)'}
              </code>
            </div>
            {config.timezone && config.timezone !== 'UTC' && (
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground text-sm">Timezone:</span>
                <span className="text-sm">{config.timezone}</span>
              </div>
            )}
            {config.expression && (
              <div className="text-xs text-muted-foreground">
                {describeCron(config.expression)}
              </div>
            )}
          </div>
        )

      case 'interval':
        return (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground text-sm">Runs every:</span>
              <span className="text-sm font-medium">
                {formatInterval(config)}
              </span>
            </div>
          </div>
        )

      case 'data_change':
        return (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground text-sm">Threshold:</span>
              <Badge variant="outline">
                {((config.change_threshold || 0.05) * 100).toFixed(0)}% change
              </Badge>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground text-sm">Metrics:</span>
              <div className="flex flex-wrap gap-1">
                {(config.metrics || ['row_count']).map((metric) => (
                  <Badge key={metric} variant="secondary" className="text-xs">
                    {metric.replace('_', ' ')}
                  </Badge>
                ))}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground text-sm">Check interval:</span>
              <span className="text-sm">
                {config.check_interval_minutes || 60} minutes
              </span>
            </div>
          </div>
        )

      case 'composite':
        return (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground text-sm">Logic:</span>
              <Badge variant={config.operator === 'and' ? 'default' : 'secondary'}>
                {config.operator?.toUpperCase() || 'AND'}
              </Badge>
              <span className="text-sm">
                {config.operator === 'and'
                  ? 'All triggers must fire'
                  : 'Any trigger can fire'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground text-sm">Triggers:</span>
              <span className="text-sm">
                {config.triggers?.length || 0} configured
              </span>
            </div>
            {config.triggers && config.triggers.length > 0 && (
              <div className="pl-4 border-l-2 border-muted space-y-1">
                {config.triggers.map((t, i) => (
                  <div key={i} className="text-xs text-muted-foreground">
                    {i + 1}. {t.type}
                    {t.type === 'cron' && t.expression && `: ${t.expression}`}
                    {t.type === 'interval' && `: ${formatInterval(t)}`}
                    {t.type === 'data_change' &&
                      `: ${((t.change_threshold || 0.05) * 100).toFixed(0)}%`}
                  </div>
                ))}
              </div>
            )}
          </div>
        )

      case 'event':
        return (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground text-sm">Listens for:</span>
              <div className="flex flex-wrap gap-1">
                {(config.event_types || []).map((event) => (
                  <Badge key={event} variant="outline" className="text-xs">
                    {event.replace('_', ' ')}
                  </Badge>
                ))}
              </div>
            </div>
            {config.source_filter && config.source_filter.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground text-sm">Source filter:</span>
                <span className="text-sm">
                  {config.source_filter.length} sources
                </span>
              </div>
            )}
          </div>
        )

      case 'manual':
        return (
          <div className="text-sm text-muted-foreground">
            This schedule will only run when manually triggered via the API or UI.
          </div>
        )

      default:
        return null
    }
  }

  const isValid = validateConfig(config)

  return (
    <Card>
      <CardHeader className="py-3 px-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {getTypeIcon()}
            <CardTitle className="text-sm font-medium">{getTypeLabel()}</CardTitle>
          </div>
          {isValid ? (
            <Badge variant="outline" className="text-green-600 border-green-600">
              <CheckCircle2 className="h-3 w-3 mr-1" />
              Valid
            </Badge>
          ) : (
            <Badge variant="outline" className="text-amber-600 border-amber-600">
              Incomplete
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="py-3 px-4 pt-0">{renderDetails()}</CardContent>
    </Card>
  )
}

// Helper functions

function formatInterval(config: TriggerConfig): string {
  const parts: string[] = []
  if ('days' in config && config.days) parts.push(`${config.days} day${config.days > 1 ? 's' : ''}`)
  if ('hours' in config && config.hours) parts.push(`${config.hours} hour${config.hours > 1 ? 's' : ''}`)
  if ('minutes' in config && config.minutes) parts.push(`${config.minutes} minute${config.minutes > 1 ? 's' : ''}`)
  if ('seconds' in config && config.seconds) parts.push(`${config.seconds} second${config.seconds > 1 ? 's' : ''}`)
  return parts.length > 0 ? parts.join(', ') : '(not set)'
}

function describeCron(expression: string): string {
  const parts = expression.split(' ')
  if (parts.length < 5) return ''

  const [minute, hour, dayOfMonth, month, dayOfWeek] = parts

  // Common patterns
  if (expression === '0 0 * * *') return 'Every day at midnight'
  if (expression === '0 */6 * * *') return 'Every 6 hours'
  if (expression === '0 8 * * 1-5') return 'Every weekday at 8:00 AM'
  if (expression === '0 0 1 * *') return 'First day of every month'
  if (expression === '0 0 * * 0') return 'Every Sunday at midnight'
  if (expression === '*/15 * * * *') return 'Every 15 minutes'
  if (expression === '0 */2 * * *') return 'Every 2 hours'

  // Generic description
  if (minute === '0' && hour !== '*' && dayOfMonth === '*' && month === '*') {
    if (dayOfWeek === '*') return `Daily at ${hour}:00`
    if (dayOfWeek === '1-5') return `Weekdays at ${hour}:00`
  }

  return 'Custom schedule'
}

function validateConfig(config: TriggerConfig): boolean {
  switch (config.type) {
    case 'cron':
      return !!(config.expression && config.expression.trim())
    case 'interval':
      return !!(
        ('days' in config && config.days) ||
        ('hours' in config && config.hours) ||
        ('minutes' in config && config.minutes) ||
        ('seconds' in config && config.seconds)
      )
    case 'data_change':
      return (
        'change_threshold' in config &&
        config.change_threshold !== undefined &&
        'metrics' in config &&
        Array.isArray(config.metrics) &&
        config.metrics.length > 0
      )
    case 'composite':
      return (
        'triggers' in config &&
        Array.isArray(config.triggers) &&
        config.triggers.length >= 2
      )
    case 'event':
      return (
        'event_types' in config &&
        Array.isArray(config.event_types) &&
        config.event_types.length > 0
      )
    case 'manual':
      return true
    default:
      return false
  }
}
