/**
 * CronTriggerForm - Configure cron expression based triggers.
 */

import { useState, useMemo } from 'react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { AlertCircle, CheckCircle2 } from 'lucide-react'

interface CronTriggerFormProps {
  expression: string
  timezone?: string
  onChange: (expression: string, timezone?: string) => void
}

const CRON_PRESETS = [
  { label: 'Every hour', value: '0 * * * *' },
  { label: 'Every 6 hours', value: '0 */6 * * *' },
  { label: 'Daily at midnight', value: '0 0 * * *' },
  { label: 'Daily at 8am', value: '0 8 * * *' },
  { label: 'Weekdays at 8am', value: '0 8 * * 1-5' },
  { label: 'Every Monday', value: '0 0 * * 1' },
  { label: 'First day of month', value: '0 0 1 * *' },
  { label: 'Every 15 minutes', value: '*/15 * * * *' },
  { label: 'Every 30 minutes', value: '*/30 * * * *' },
]

const TIMEZONES = [
  'UTC',
  'America/New_York',
  'America/Los_Angeles',
  'America/Chicago',
  'Europe/London',
  'Europe/Paris',
  'Europe/Berlin',
  'Asia/Tokyo',
  'Asia/Seoul',
  'Asia/Shanghai',
  'Asia/Singapore',
  'Australia/Sydney',
]

export function CronTriggerForm({
  expression,
  timezone,
  onChange,
}: CronTriggerFormProps) {
  const [customMode, setCustomMode] = useState(
    !CRON_PRESETS.some((p) => p.value === expression)
  )

  // Validate cron expression
  const validation = useMemo(() => {
    const parts = expression.trim().split(/\s+/)
    if (parts.length !== 5) {
      return {
        valid: false,
        error: 'Cron expression must have 5 parts (minute hour day month weekday)',
      }
    }

    // Basic validation for each part
    const [minute, hour, day, month, weekday] = parts

    const validateRange = (value: string, min: number, max: number): boolean => {
      if (value === '*') return true
      if (value.includes('/')) {
        const [, step] = value.split('/')
        return !isNaN(parseInt(step))
      }
      if (value.includes('-')) {
        const [start, end] = value.split('-').map(Number)
        return !isNaN(start) && !isNaN(end) && start >= min && end <= max
      }
      if (value.includes(',')) {
        return value.split(',').every((v) => !isNaN(parseInt(v)))
      }
      const num = parseInt(value)
      return !isNaN(num) && num >= min && num <= max
    }

    if (!validateRange(minute, 0, 59)) return { valid: false, error: 'Invalid minute (0-59)' }
    if (!validateRange(hour, 0, 23)) return { valid: false, error: 'Invalid hour (0-23)' }
    if (!validateRange(day, 1, 31)) return { valid: false, error: 'Invalid day (1-31)' }
    if (!validateRange(month, 1, 12)) return { valid: false, error: 'Invalid month (1-12)' }
    if (!validateRange(weekday, 0, 7)) return { valid: false, error: 'Invalid weekday (0-7)' }

    return { valid: true, error: null }
  }, [expression])

  // Human-readable description
  const description = useMemo(() => {
    const preset = CRON_PRESETS.find((p) => p.value === expression)
    if (preset) return preset.label

    // Try to generate a description
    const parts = expression.trim().split(/\s+/)
    if (parts.length !== 5) return 'Invalid expression'

    const [minute, hour, day, month, weekday] = parts

    if (minute === '0' && hour === '0' && day === '*' && month === '*' && weekday === '*') {
      return 'Daily at midnight'
    }
    if (minute === '0' && hour === '*' && day === '*' && month === '*' && weekday === '*') {
      return 'Every hour'
    }
    if (minute.startsWith('*/')) {
      return `Every ${minute.split('/')[1]} minutes`
    }
    if (hour.startsWith('*/')) {
      return `Every ${hour.split('/')[1]} hours`
    }

    return `At ${minute} ${hour} ${day} ${month} ${weekday}`
  }, [expression])

  return (
    <div className="space-y-4">
      {/* Preset selector */}
      <div className="space-y-2">
        <Label>Quick Select</Label>
        <Select
          value={customMode ? 'custom' : expression}
          onValueChange={(v) => {
            if (v === 'custom') {
              setCustomMode(true)
            } else {
              setCustomMode(false)
              onChange(v, timezone)
            }
          }}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select a preset" />
          </SelectTrigger>
          <SelectContent>
            {CRON_PRESETS.map((preset) => (
              <SelectItem key={preset.value} value={preset.value}>
                <div className="flex items-center gap-2">
                  <span>{preset.label}</span>
                  <span className="text-xs text-muted-foreground font-mono">
                    {preset.value}
                  </span>
                </div>
              </SelectItem>
            ))}
            <SelectItem value="custom">Custom expression</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Custom expression input */}
      <div className="space-y-2">
        <Label>Cron Expression</Label>
        <div className="flex items-center gap-2">
          <Input
            value={expression}
            onChange={(e) => {
              setCustomMode(true)
              onChange(e.target.value, timezone)
            }}
            placeholder="* * * * *"
            className="font-mono"
          />
          {validation.valid ? (
            <CheckCircle2 className="h-5 w-5 text-green-500 shrink-0" />
          ) : (
            <AlertCircle className="h-5 w-5 text-red-500 shrink-0" />
          )}
        </div>
        {!validation.valid && (
          <p className="text-sm text-red-500">{validation.error}</p>
        )}
        <p className="text-xs text-muted-foreground">
          Format: minute hour day month weekday (e.g., 0 0 * * * for daily at midnight)
        </p>
      </div>

      {/* Description */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">Schedule:</span>
        <Badge variant="secondary">{description}</Badge>
      </div>

      {/* Timezone selector */}
      <div className="space-y-2">
        <Label>Timezone</Label>
        <Select
          value={timezone || 'UTC'}
          onValueChange={(v) => onChange(expression, v)}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select timezone" />
          </SelectTrigger>
          <SelectContent>
            {TIMEZONES.map((tz) => (
              <SelectItem key={tz} value={tz}>
                {tz}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Help section */}
      <div className="text-xs text-muted-foreground space-y-1 pt-2 border-t">
        <p className="font-medium">Cron Expression Reference:</p>
        <div className="grid grid-cols-5 gap-1 font-mono text-center">
          <span>min</span>
          <span>hr</span>
          <span>day</span>
          <span>mon</span>
          <span>dow</span>
        </div>
        <div className="grid grid-cols-5 gap-1 text-center">
          <span>0-59</span>
          <span>0-23</span>
          <span>1-31</span>
          <span>1-12</span>
          <span>0-7</span>
        </div>
        <p className="pt-1">
          * = any, */n = every n, n-m = range, n,m = list
        </p>
      </div>
    </div>
  )
}
