/**
 * TriggerTypeSelector - Select trigger type with visual cards.
 */

import { Clock, Timer, TrendingUp, Layers, Zap, Hand, Webhook } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { TriggerType } from './TriggerBuilder'

interface TriggerTypeSelectorProps {
  value: TriggerType
  onChange: (type: TriggerType) => void
  compact?: boolean
}

const TRIGGER_TYPES: {
  type: TriggerType
  icon: React.ComponentType<{ className?: string }>
  label: string
  shortDesc: string
}[] = [
  {
    type: 'cron',
    icon: Clock,
    label: 'Cron',
    shortDesc: 'Cron expression',
  },
  {
    type: 'interval',
    icon: Timer,
    label: 'Interval',
    shortDesc: 'Fixed intervals',
  },
  {
    type: 'data_change',
    icon: TrendingUp,
    label: 'Data Change',
    shortDesc: 'Profile changes',
  },
  {
    type: 'composite',
    icon: Layers,
    label: 'Composite',
    shortDesc: 'Multiple triggers',
  },
  {
    type: 'event',
    icon: Zap,
    label: 'Event',
    shortDesc: 'System events',
  },
  {
    type: 'webhook',
    icon: Webhook,
    label: 'Webhook',
    shortDesc: 'External triggers',
  },
  {
    type: 'manual',
    icon: Hand,
    label: 'Manual',
    shortDesc: 'API only',
  },
]

export function TriggerTypeSelector({
  value,
  onChange,
  compact = false,
}: TriggerTypeSelectorProps) {
  return (
    <div className={cn('grid gap-2', compact ? 'grid-cols-7' : 'grid-cols-4')}>
      {TRIGGER_TYPES.map(({ type, icon: Icon, label, shortDesc }) => (
        <button
          key={type}
          type="button"
          onClick={() => onChange(type)}
          className={cn(
            'flex flex-col items-center gap-1 p-3 rounded-lg border-2 transition-all',
            'hover:border-primary/50 hover:bg-muted/50',
            value === type
              ? 'border-primary bg-primary/5'
              : 'border-border bg-background'
          )}
        >
          <Icon
            className={cn(
              'h-5 w-5',
              value === type ? 'text-primary' : 'text-muted-foreground'
            )}
          />
          <span
            className={cn(
              'text-sm font-medium',
              value === type ? 'text-primary' : 'text-foreground'
            )}
          >
            {label}
          </span>
          {!compact && (
            <span className="text-xs text-muted-foreground">{shortDesc}</span>
          )}
        </button>
      ))}
    </div>
  )
}
