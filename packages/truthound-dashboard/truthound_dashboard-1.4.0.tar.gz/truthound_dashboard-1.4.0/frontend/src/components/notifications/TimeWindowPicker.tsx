/**
 * TimeWindowPicker - Component for configuring time window rules.
 *
 * Features:
 * - Visual multi-select weekday picker with toggle buttons
 * - Time range selector (24-hour format) with intuitive UI
 * - Timezone selector with common timezone options
 * - Accessibility support (ARIA labels, keyboard navigation)
 * - i18n support via Intlayer
 */

import { useCallback, useMemo, useRef, KeyboardEvent } from 'react'
import { Clock, Globe, Calendar } from 'lucide-react'
import { useIntlayer } from 'react-intlayer'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
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
import { cn } from '@/lib/utils'
import { str } from '@/lib/intlayer-utils'

// =============================================================================
// Types
// =============================================================================

export interface TimeWindowConfig {
  start_hour: number
  end_hour: number
  weekdays: number[]
  timezone?: string
}

export interface TimeWindowPickerProps {
  value: TimeWindowConfig
  onChange: (value: TimeWindowConfig) => void
  className?: string
}

// =============================================================================
// Constants
// =============================================================================

/**
 * Common timezones grouped by region for the timezone selector.
 */
const TIMEZONE_GROUPS = {
  utc: ['UTC'],
  americas: [
    'America/New_York',
    'America/Chicago',
    'America/Denver',
    'America/Los_Angeles',
    'America/Toronto',
    'America/Vancouver',
    'America/Sao_Paulo',
    'America/Mexico_City',
  ],
  europe: [
    'Europe/London',
    'Europe/Paris',
    'Europe/Berlin',
    'Europe/Amsterdam',
    'Europe/Rome',
    'Europe/Madrid',
    'Europe/Moscow',
  ],
  asia: [
    'Asia/Tokyo',
    'Asia/Seoul',
    'Asia/Shanghai',
    'Asia/Hong_Kong',
    'Asia/Singapore',
    'Asia/Mumbai',
    'Asia/Dubai',
  ],
  pacific: [
    'Pacific/Auckland',
    'Pacific/Sydney',
    'Australia/Melbourne',
    'Australia/Sydney',
  ],
}

// =============================================================================
// WeekdayButton Component
// =============================================================================

interface WeekdayButtonProps {
  day: number
  label: string
  fullName: string
  isSelected: boolean
  onToggle: () => void
  tabIndex?: number
  onKeyDown?: (e: KeyboardEvent<HTMLButtonElement>) => void
}

function WeekdayButton({
  day,
  label,
  fullName,
  isSelected,
  onToggle,
  tabIndex = 0,
  onKeyDown,
}: WeekdayButtonProps) {
  return (
    <TooltipProvider>
      <Tooltip delayDuration={300}>
        <TooltipTrigger asChild>
          <button
            type="button"
            role="checkbox"
            aria-checked={isSelected}
            aria-label={fullName}
            tabIndex={tabIndex}
            onClick={onToggle}
            onKeyDown={onKeyDown}
            className={cn(
              'flex items-center justify-center',
              'w-10 h-10 text-sm font-medium rounded-lg',
              'border-2 transition-all duration-150',
              'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
              isSelected
                ? 'bg-primary text-primary-foreground border-primary shadow-sm'
                : 'bg-background hover:bg-muted border-input hover:border-primary/50'
            )}
            data-day={day}
          >
            {label}
          </button>
        </TooltipTrigger>
        <TooltipContent side="bottom">
          <p>{fullName}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

// =============================================================================
// WeekdayPicker Component
// =============================================================================

interface WeekdayPickerProps {
  value: number[]
  onChange: (value: number[]) => void
}

function WeekdayPicker({ value, onChange }: WeekdayPickerProps) {
  const content = useIntlayer('notificationsAdvanced')
  const containerRef = useRef<HTMLDivElement>(null)

  // Weekday definitions (0=Monday to 6=Sunday, matching Python's weekday())
  const weekdays = useMemo(
    () => [
      { day: 0, key: 'mon' as const },
      { day: 1, key: 'tue' as const },
      { day: 2, key: 'wed' as const },
      { day: 3, key: 'thu' as const },
      { day: 4, key: 'fri' as const },
      { day: 5, key: 'sat' as const },
      { day: 6, key: 'sun' as const },
    ],
    []
  )

  const shortNames = content.ruleParams.weekdayNames
  const fullNames = content.ruleParams.weekdayFullNames

  const toggleDay = useCallback(
    (day: number) => {
      const newValue = value.includes(day)
        ? value.filter((d) => d !== day)
        : [...value, day].sort((a, b) => a - b)
      onChange(newValue)
    },
    [value, onChange]
  )

  const selectAll = useCallback(() => {
    onChange([0, 1, 2, 3, 4, 5, 6])
  }, [onChange])

  const selectWeekdays = useCallback(() => {
    onChange([0, 1, 2, 3, 4])
  }, [onChange])

  const selectWeekend = useCallback(() => {
    onChange([5, 6])
  }, [onChange])

  const clearAll = useCallback(() => {
    onChange([])
  }, [onChange])

  // Keyboard navigation for the weekday buttons
  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLButtonElement>, currentDay: number) => {
      const buttons = containerRef.current?.querySelectorAll<HTMLButtonElement>(
        '[data-day]'
      )
      if (!buttons) return

      const currentIndex = weekdays.findIndex((w) => w.day === currentDay)

      switch (e.key) {
        case 'ArrowLeft':
          e.preventDefault()
          if (currentIndex > 0) {
            buttons[currentIndex - 1]?.focus()
          }
          break
        case 'ArrowRight':
          e.preventDefault()
          if (currentIndex < weekdays.length - 1) {
            buttons[currentIndex + 1]?.focus()
          }
          break
        case ' ':
        case 'Enter':
          e.preventDefault()
          toggleDay(currentDay)
          break
        case 'a':
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault()
            selectAll()
          }
          break
      }
    },
    [weekdays, toggleDay, selectAll]
  )

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Calendar className="h-4 w-4 text-muted-foreground" />
        <Label className="text-sm font-medium">
          {str(content.ruleParams.weekdays)}
        </Label>
      </div>

      {/* Quick selection buttons */}
      <div className="flex flex-wrap gap-2 text-xs">
        <button
          type="button"
          onClick={selectWeekdays}
          className="px-2 py-1 rounded bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground transition-colors"
          aria-label={str(content.ruleParams.weekdaysOnly)}
        >
          {str(content.ruleParams.weekdaysOnly)}
        </button>
        <button
          type="button"
          onClick={selectWeekend}
          className="px-2 py-1 rounded bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground transition-colors"
          aria-label={str(content.ruleParams.weekendsOnly)}
        >
          {str(content.ruleParams.weekendsOnly)}
        </button>
        <button
          type="button"
          onClick={selectAll}
          className="px-2 py-1 rounded bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground transition-colors"
          aria-label={str(content.ruleParams.allDays)}
        >
          {str(content.ruleParams.allDays)}
        </button>
        <button
          type="button"
          onClick={clearAll}
          className="px-2 py-1 rounded bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground transition-colors"
          aria-label={str(content.ruleParams.clearDays)}
        >
          {str(content.ruleParams.clearDays)}
        </button>
      </div>

      {/* Weekday buttons */}
      <div
        ref={containerRef}
        className="flex gap-1.5"
        role="group"
        aria-label={str(content.ruleParams.weekdays)}
      >
        {weekdays.map((w, index) => (
          <WeekdayButton
            key={w.day}
            day={w.day}
            label={str(shortNames[w.key])}
            fullName={str(fullNames[w.key])}
            isSelected={value.includes(w.day)}
            onToggle={() => toggleDay(w.day)}
            tabIndex={index === 0 ? 0 : -1}
            onKeyDown={(e) => handleKeyDown(e, w.day)}
          />
        ))}
      </div>

      {/* Selection summary */}
      <p className="text-xs text-muted-foreground">
        {value.length === 0 && str(content.ruleParams.noDaysSelected)}
        {value.length === 7 && str(content.ruleParams.everyDay)}
        {value.length > 0 && value.length < 7 && (
          <>
            {value.length} {str(content.ruleParams.daysSelected)}
          </>
        )}
      </p>
    </div>
  )
}

// =============================================================================
// TimeRangePicker Component
// =============================================================================

interface TimeRangePickerProps {
  startHour: number
  endHour: number
  onStartHourChange: (hour: number) => void
  onEndHourChange: (hour: number) => void
}

function TimeRangePicker({
  startHour,
  endHour,
  onStartHourChange,
  onEndHourChange,
}: TimeRangePickerProps) {
  const content = useIntlayer('notificationsAdvanced')

  const formatHour = (hour: number): string => {
    return `${hour.toString().padStart(2, '0')}:00`
  }

  const parseHour = (value: string): number => {
    const num = parseInt(value.split(':')[0], 10)
    return isNaN(num) ? 0 : Math.max(0, Math.min(23, num))
  }

  const isOvernightRange = startHour > endHour

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Clock className="h-4 w-4 text-muted-foreground" />
        <Label className="text-sm font-medium">
          {str(content.ruleParams.timeRange)}
        </Label>
      </div>

      <div className="flex items-center gap-3">
        {/* Start Hour */}
        <div className="flex-1 space-y-1.5">
          <Label className="text-xs text-muted-foreground">
            {str(content.ruleParams.startHour)}
          </Label>
          <Input
            type="time"
            value={formatHour(startHour)}
            onChange={(e) => onStartHourChange(parseHour(e.target.value))}
            className="h-10"
            step="3600"
            aria-label={str(content.ruleParams.startHour)}
          />
        </div>

        {/* Separator */}
        <div className="flex items-center justify-center pt-6">
          <span className="text-muted-foreground font-medium">
            {str(content.ruleParams.to)}
          </span>
        </div>

        {/* End Hour */}
        <div className="flex-1 space-y-1.5">
          <Label className="text-xs text-muted-foreground">
            {str(content.ruleParams.endHour)}
          </Label>
          <Input
            type="time"
            value={formatHour(endHour)}
            onChange={(e) => onEndHourChange(parseHour(e.target.value))}
            className="h-10"
            step="3600"
            aria-label={str(content.ruleParams.endHour)}
          />
        </div>
      </div>

      {/* Time range info */}
      <div className="text-xs text-muted-foreground">
        {isOvernightRange ? (
          <span className="text-amber-600 dark:text-amber-400">
            {str(content.ruleParams.overnightRange)}: {formatHour(startHour)} - {formatHour(endHour)} ({str(content.ruleParams.nextDay)})
          </span>
        ) : (
          <span>
            {str(content.ruleParams.activeHours)}: {formatHour(startHour)} - {formatHour(endHour)}
          </span>
        )}
      </div>
    </div>
  )
}

// =============================================================================
// TimezonePicker Component
// =============================================================================

interface TimezonePickerProps {
  value: string | undefined
  onChange: (value: string | undefined) => void
}

function TimezonePicker({ value, onChange }: TimezonePickerProps) {
  const content = useIntlayer('notificationsAdvanced')

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Globe className="h-4 w-4 text-muted-foreground" />
        <Label className="text-sm font-medium">
          {str(content.ruleParams.timezone)}
        </Label>
        <span className="text-xs text-muted-foreground">
          ({str(content.ruleParams.optional)})
        </span>
      </div>

      <Select
        value={value || '__browser__'}
        onValueChange={(v) => onChange(v === '__browser__' ? undefined : v)}
      >
        <SelectTrigger className="h-10">
          <SelectValue placeholder={str(content.ruleParams.browserTimezone)} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__browser__">
            {str(content.ruleParams.browserTimezone)}
          </SelectItem>

          <SelectGroup>
            <SelectLabel>{str(content.ruleParams.timezoneGroups.utc)}</SelectLabel>
            {TIMEZONE_GROUPS.utc.map((tz) => (
              <SelectItem key={tz} value={tz}>
                {tz}
              </SelectItem>
            ))}
          </SelectGroup>

          <SelectGroup>
            <SelectLabel>{str(content.ruleParams.timezoneGroups.americas)}</SelectLabel>
            {TIMEZONE_GROUPS.americas.map((tz) => (
              <SelectItem key={tz} value={tz}>
                {tz.split('/')[1]?.replace(/_/g, ' ') || tz}
              </SelectItem>
            ))}
          </SelectGroup>

          <SelectGroup>
            <SelectLabel>{str(content.ruleParams.timezoneGroups.europe)}</SelectLabel>
            {TIMEZONE_GROUPS.europe.map((tz) => (
              <SelectItem key={tz} value={tz}>
                {tz.split('/')[1]?.replace(/_/g, ' ') || tz}
              </SelectItem>
            ))}
          </SelectGroup>

          <SelectGroup>
            <SelectLabel>{str(content.ruleParams.timezoneGroups.asia)}</SelectLabel>
            {TIMEZONE_GROUPS.asia.map((tz) => (
              <SelectItem key={tz} value={tz}>
                {tz.split('/')[1]?.replace(/_/g, ' ') || tz}
              </SelectItem>
            ))}
          </SelectGroup>

          <SelectGroup>
            <SelectLabel>{str(content.ruleParams.timezoneGroups.pacific)}</SelectLabel>
            {TIMEZONE_GROUPS.pacific.map((tz) => (
              <SelectItem key={tz} value={tz}>
                {tz.split('/')[1]?.replace(/_/g, ' ') || tz}
              </SelectItem>
            ))}
          </SelectGroup>
        </SelectContent>
      </Select>

      {value && (
        <p className="text-xs text-muted-foreground">
          {str(content.ruleParams.timezoneNote)}
        </p>
      )}
    </div>
  )
}

// =============================================================================
// Main TimeWindowPicker Component
// =============================================================================

export function TimeWindowPicker({
  value,
  onChange,
  className,
}: TimeWindowPickerProps) {
  const handleWeekdaysChange = useCallback(
    (weekdays: number[]) => {
      onChange({ ...value, weekdays })
    },
    [value, onChange]
  )

  const handleStartHourChange = useCallback(
    (start_hour: number) => {
      onChange({ ...value, start_hour })
    },
    [value, onChange]
  )

  const handleEndHourChange = useCallback(
    (end_hour: number) => {
      onChange({ ...value, end_hour })
    },
    [value, onChange]
  )

  const handleTimezoneChange = useCallback(
    (timezone: string | undefined) => {
      onChange({ ...value, timezone })
    },
    [value, onChange]
  )

  return (
    <div className={cn('space-y-6', className)}>
      {/* Weekday Picker */}
      <WeekdayPicker value={value.weekdays} onChange={handleWeekdaysChange} />

      {/* Time Range Picker */}
      <TimeRangePicker
        startHour={value.start_hour}
        endHour={value.end_hour}
        onStartHourChange={handleStartHourChange}
        onEndHourChange={handleEndHourChange}
      />

      {/* Timezone Picker */}
      <TimezonePicker value={value.timezone} onChange={handleTimezoneChange} />
    </div>
  )
}

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Format weekdays array to human-readable string.
 *
 * @param weekdays - Array of weekday numbers (0=Monday to 6=Sunday)
 * @param shortNames - Object containing short weekday names from i18n
 * @returns Formatted string like "Mon-Fri" or "Mon, Wed, Fri"
 */
export function formatWeekdays(
  weekdays: number[],
  shortNames: Record<string, string>
): string {
  if (weekdays.length === 0) return ''
  if (weekdays.length === 7) return 'Every day'

  const sorted = [...weekdays].sort((a, b) => a - b)
  const dayKeys = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

  // Check for consecutive ranges
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
        return shortNames[dayKeys[range.start]] || dayKeys[range.start]
      } else if (range.end - range.start >= 2) {
        const startName = shortNames[dayKeys[range.start]] || dayKeys[range.start]
        const endName = shortNames[dayKeys[range.end]] || dayKeys[range.end]
        return `${startName}-${endName}`
      } else {
        const startName = shortNames[dayKeys[range.start]] || dayKeys[range.start]
        const endName = shortNames[dayKeys[range.end]] || dayKeys[range.end]
        return `${startName}, ${endName}`
      }
    })
    .join(', ')
}

/**
 * Format time window config to human-readable summary.
 *
 * @param config - Time window configuration
 * @param shortNames - Object containing short weekday names from i18n
 * @returns Formatted string like "Mon-Fri, 09:00-17:00 (UTC)"
 */
export function formatTimeWindowSummary(
  config: TimeWindowConfig,
  shortNames: Record<string, string>
): string {
  const weekdayStr = formatWeekdays(config.weekdays, shortNames)
  const timeStr = `${config.start_hour.toString().padStart(2, '0')}:00-${config.end_hour.toString().padStart(2, '0')}:00`
  const timezoneStr = config.timezone ? ` (${config.timezone})` : ''

  if (weekdayStr) {
    return `${weekdayStr}, ${timeStr}${timezoneStr}`
  }
  return `${timeStr}${timezoneStr}`
}

export default TimeWindowPicker
