/**
 * IntervalTriggerForm - Configure interval-based triggers.
 */

import { useMemo } from 'react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Clock } from 'lucide-react'

interface IntervalTriggerFormProps {
  seconds?: number
  minutes?: number
  hours?: number
  days?: number
  onChange: (interval: {
    seconds?: number
    minutes?: number
    hours?: number
    days?: number
  }) => void
}

const INTERVAL_PRESETS = [
  { label: '5 min', seconds: 0, minutes: 5, hours: 0, days: 0 },
  { label: '15 min', seconds: 0, minutes: 15, hours: 0, days: 0 },
  { label: '30 min', seconds: 0, minutes: 30, hours: 0, days: 0 },
  { label: '1 hour', seconds: 0, minutes: 0, hours: 1, days: 0 },
  { label: '6 hours', seconds: 0, minutes: 0, hours: 6, days: 0 },
  { label: '12 hours', seconds: 0, minutes: 0, hours: 12, days: 0 },
  { label: '1 day', seconds: 0, minutes: 0, hours: 0, days: 1 },
  { label: '1 week', seconds: 0, minutes: 0, hours: 0, days: 7 },
]

export function IntervalTriggerForm({
  seconds = 0,
  minutes = 0,
  hours = 0,
  days = 0,
  onChange,
}: IntervalTriggerFormProps) {
  // Calculate total seconds
  const totalSeconds = useMemo(() => {
    return (seconds || 0) + (minutes || 0) * 60 + (hours || 0) * 3600 + (days || 0) * 86400
  }, [seconds, minutes, hours, days])

  // Human-readable description
  const description = useMemo(() => {
    const parts: string[] = []
    if (days) parts.push(`${days} day${days > 1 ? 's' : ''}`)
    if (hours) parts.push(`${hours} hour${hours > 1 ? 's' : ''}`)
    if (minutes) parts.push(`${minutes} minute${minutes > 1 ? 's' : ''}`)
    if (seconds) parts.push(`${seconds} second${seconds > 1 ? 's' : ''}`)

    if (parts.length === 0) return 'Not configured'
    return `Every ${parts.join(', ')}`
  }, [days, hours, minutes, seconds])

  const handleChange = (field: string, value: number) => {
    const newInterval: { seconds?: number; minutes?: number; hours?: number; days?: number } = {
      seconds,
      minutes,
      hours,
      days,
    }
    newInterval[field as keyof typeof newInterval] = value || undefined
    onChange(newInterval)
  }

  const applyPreset = (preset: typeof INTERVAL_PRESETS[0]) => {
    onChange({
      seconds: preset.seconds || undefined,
      minutes: preset.minutes || undefined,
      hours: preset.hours || undefined,
      days: preset.days || undefined,
    })
  }

  const isPresetActive = (preset: typeof INTERVAL_PRESETS[0]) => {
    return (
      (preset.seconds || 0) === (seconds || 0) &&
      (preset.minutes || 0) === (minutes || 0) &&
      (preset.hours || 0) === (hours || 0) &&
      (preset.days || 0) === (days || 0)
    )
  }

  return (
    <div className="space-y-4">
      {/* Quick presets */}
      <div className="space-y-2">
        <Label>Quick Select</Label>
        <div className="flex flex-wrap gap-2">
          {INTERVAL_PRESETS.map((preset) => (
            <Button
              key={preset.label}
              type="button"
              variant={isPresetActive(preset) ? 'default' : 'outline'}
              size="sm"
              onClick={() => applyPreset(preset)}
            >
              {preset.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Custom interval inputs */}
      <div className="grid grid-cols-4 gap-3">
        <div className="space-y-1">
          <Label className="text-xs">Days</Label>
          <Input
            type="number"
            min={0}
            value={days || ''}
            onChange={(e) => handleChange('days', parseInt(e.target.value) || 0)}
            placeholder="0"
          />
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Hours</Label>
          <Input
            type="number"
            min={0}
            max={23}
            value={hours || ''}
            onChange={(e) => handleChange('hours', parseInt(e.target.value) || 0)}
            placeholder="0"
          />
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Minutes</Label>
          <Input
            type="number"
            min={0}
            max={59}
            value={minutes || ''}
            onChange={(e) => handleChange('minutes', parseInt(e.target.value) || 0)}
            placeholder="0"
          />
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Seconds</Label>
          <Input
            type="number"
            min={0}
            max={59}
            value={seconds || ''}
            onChange={(e) => handleChange('seconds', parseInt(e.target.value) || 0)}
            placeholder="0"
          />
        </div>
      </div>

      {/* Description */}
      <div className="flex items-center gap-2">
        <Clock className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm text-muted-foreground">Interval:</span>
        <Badge variant="secondary">{description}</Badge>
      </div>

      {/* Validation */}
      {totalSeconds === 0 && (
        <p className="text-sm text-amber-600">
          Please configure at least one time interval
        </p>
      )}
      {totalSeconds > 0 && totalSeconds < 60 && (
        <p className="text-sm text-amber-600">
          Warning: Very short intervals may cause high system load
        </p>
      )}
    </div>
  )
}
