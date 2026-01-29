/**
 * EscalationTimeline - Visual timeline for escalation events.
 *
 * Features:
 * - Responsive design (vertical on mobile, horizontal on desktop)
 * - Color-coded states
 * - Event type icons
 * - Time duration between events
 * - Current state indicator
 * - Animation support for state transitions
 * - Accessibility support
 */

import { useMemo, useEffect, useState, useRef } from 'react'
import { useIntlayer } from 'react-intlayer'
import {
  Bell,
  User,
  Clock,
  Shield,
  ArrowUp,
  AlertTriangle,
  ChevronRight,
  Timer,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import type { IncidentEvent, IncidentState } from './IncidentDetailDialog'

// State configuration for colors and icons
export const STATE_COLORS: Record<
  IncidentState,
  {
    bg: string
    bgDark: string
    text: string
    textDark: string
    border: string
    borderDark: string
    connector: string
    connectorDark: string
  }
> = {
  pending: {
    bg: 'bg-yellow-100',
    bgDark: 'dark:bg-yellow-900/30',
    text: 'text-yellow-700',
    textDark: 'dark:text-yellow-400',
    border: 'border-yellow-300',
    borderDark: 'dark:border-yellow-700',
    connector: 'bg-yellow-300',
    connectorDark: 'dark:bg-yellow-700',
  },
  triggered: {
    bg: 'bg-orange-100',
    bgDark: 'dark:bg-orange-900/30',
    text: 'text-orange-700',
    textDark: 'dark:text-orange-400',
    border: 'border-orange-300',
    borderDark: 'dark:border-orange-700',
    connector: 'bg-orange-300',
    connectorDark: 'dark:bg-orange-700',
  },
  escalated: {
    bg: 'bg-red-100',
    bgDark: 'dark:bg-red-900/30',
    text: 'text-red-700',
    textDark: 'dark:text-red-400',
    border: 'border-red-300',
    borderDark: 'dark:border-red-700',
    connector: 'bg-red-300',
    connectorDark: 'dark:bg-red-700',
  },
  acknowledged: {
    bg: 'bg-blue-100',
    bgDark: 'dark:bg-blue-900/30',
    text: 'text-blue-700',
    textDark: 'dark:text-blue-400',
    border: 'border-blue-300',
    borderDark: 'dark:border-blue-700',
    connector: 'bg-blue-300',
    connectorDark: 'dark:bg-blue-700',
  },
  resolved: {
    bg: 'bg-green-100',
    bgDark: 'dark:bg-green-900/30',
    text: 'text-green-700',
    textDark: 'dark:text-green-400',
    border: 'border-green-300',
    borderDark: 'dark:border-green-700',
    connector: 'bg-green-300',
    connectorDark: 'dark:bg-green-700',
  },
}

// Event type to state mapping
const EVENT_TYPE_TO_STATE: Record<string, IncidentState> = {
  created: 'pending',
  triggered: 'triggered',
  escalated: 'escalated',
  acknowledged: 'acknowledged',
  resolved: 'resolved',
}

// Event icons
const EVENT_ICONS: Record<string, typeof Bell> = {
  created: Clock,
  triggered: Bell,
  escalated: ArrowUp,
  acknowledged: User,
  resolved: Shield,
}

export interface TimelineEvent extends IncidentEvent {
  isLatest?: boolean
}

export interface EscalationTimelineProps {
  events: TimelineEvent[]
  currentState: IncidentState
  className?: string
  orientation?: 'horizontal' | 'vertical' | 'auto'
  showDuration?: boolean
  animated?: boolean
  compact?: boolean
}

/**
 * Format duration between two dates
 */
function formatDuration(start: string, end: string): string {
  const startDate = new Date(start)
  const endDate = new Date(end)
  const diffMs = endDate.getTime() - startDate.getTime()

  if (diffMs < 0) return '-'
  if (diffMs < 1000) return '<1s'

  const seconds = Math.floor(diffMs / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 0) {
    return `${days}d ${hours % 24}h`
  }
  if (hours > 0) {
    return `${hours}h ${minutes % 60}m`
  }
  if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`
  }
  return `${seconds}s`
}

/**
 * Format timestamp to human-readable format
 */
function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp)
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

/**
 * Timeline Event Node Component
 */
interface TimelineNodeProps {
  event: TimelineEvent
  index: number
  isLast: boolean
  isHorizontal: boolean
  showDuration: boolean
  nextEvent?: TimelineEvent
  animated: boolean
  compact: boolean
}

function TimelineNode({
  event,
  index,
  isLast,
  isHorizontal,
  showDuration,
  nextEvent,
  animated,
  compact,
}: TimelineNodeProps) {
  const content = useIntlayer('notificationsAdvanced')
  const [isVisible, setIsVisible] = useState(!animated)
  const nodeRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (animated) {
      const timer = setTimeout(() => setIsVisible(true), index * 150)
      return () => clearTimeout(timer)
    }
  }, [animated, index])

  const state = EVENT_TYPE_TO_STATE[event.event_type] || 'pending'
  const colors = STATE_COLORS[state]
  const EventIcon = EVENT_ICONS[event.event_type] || AlertTriangle

  // Get state label
  const stateLabels: Record<string, React.ReactNode> = {
    created: content.timeline?.created ?? 'Created',
    triggered: content.states.triggered,
    escalated: content.states.escalated,
    acknowledged: content.states.acknowledged,
    resolved: content.states.resolved,
  }

  const duration = nextEvent ? formatDuration(event.created_at, nextEvent.created_at) : null

  if (isHorizontal) {
    return (
      <div
        ref={nodeRef}
        className={cn(
          'flex flex-col items-center transition-all duration-300',
          animated && !isVisible && 'opacity-0 translate-y-4',
          animated && isVisible && 'opacity-100 translate-y-0'
        )}
        role="listitem"
        aria-label={`${stateLabels[event.event_type]}: ${event.message}`}
      >
        {/* Node */}
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <div
                className={cn(
                  'relative flex items-center justify-center rounded-full border-2 transition-all duration-300',
                  colors.bg,
                  colors.bgDark,
                  colors.border,
                  colors.borderDark,
                  compact ? 'w-8 h-8' : 'w-10 h-10',
                  event.isLatest && 'ring-2 ring-primary ring-offset-2 ring-offset-background',
                  animated && 'hover:scale-110'
                )}
              >
                <EventIcon
                  className={cn(
                    colors.text,
                    colors.textDark,
                    compact ? 'h-4 w-4' : 'h-5 w-5'
                  )}
                />
                {event.isLatest && (
                  <span
                    className="absolute -top-1 -right-1 w-3 h-3 bg-primary rounded-full animate-pulse"
                    aria-hidden="true"
                  />
                )}
              </div>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-xs">
              <div className="space-y-1">
                <p className="font-medium">{event.message}</p>
                <p className="text-xs text-muted-foreground">
                  {formatTimestamp(event.created_at)}
                </p>
                {event.user_id && (
                  <p className="text-xs text-muted-foreground">
                    By: {event.user_id}
                  </p>
                )}
                {event.level && (
                  <Badge variant="outline" className="text-xs">
                    Level {event.level}
                  </Badge>
                )}
              </div>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        {/* Label */}
        <div className={cn('mt-2 text-center', compact && 'mt-1')}>
          <Badge
            variant="outline"
            className={cn(
              colors.bg,
              colors.bgDark,
              colors.text,
              colors.textDark,
              'text-xs font-medium'
            )}
          >
            {stateLabels[event.event_type]}
          </Badge>
          {!compact && (
            <p className="text-xs text-muted-foreground mt-1 max-w-[100px] truncate">
              {formatTimestamp(event.created_at)}
            </p>
          )}
        </div>

        {/* Connector with duration */}
        {!isLast && (
          <div className="flex items-center mt-2">
            <div
              className={cn(
                'w-16 h-0.5',
                colors.connector,
                colors.connectorDark,
                'rounded-full'
              )}
              aria-hidden="true"
            />
            {showDuration && duration && (
              <div className="absolute translate-x-6 -translate-y-5">
                <Badge variant="secondary" className="text-xs gap-1">
                  <Timer className="h-3 w-3" />
                  {duration}
                </Badge>
              </div>
            )}
            <ChevronRight
              className={cn('h-4 w-4', colors.text, colors.textDark)}
              aria-hidden="true"
            />
          </div>
        )}
      </div>
    )
  }

  // Vertical layout
  return (
    <div
      ref={nodeRef}
      className={cn(
        'relative flex gap-4 transition-all duration-300',
        animated && !isVisible && 'opacity-0 -translate-x-4',
        animated && isVisible && 'opacity-100 translate-x-0'
      )}
      role="listitem"
      aria-label={`${stateLabels[event.event_type]}: ${event.message}`}
    >
      {/* Timeline line */}
      <div className="flex flex-col items-center">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <div
                className={cn(
                  'relative flex items-center justify-center rounded-full border-2 transition-all duration-300 z-10',
                  colors.bg,
                  colors.bgDark,
                  colors.border,
                  colors.borderDark,
                  compact ? 'w-8 h-8' : 'w-10 h-10',
                  event.isLatest && 'ring-2 ring-primary ring-offset-2 ring-offset-background',
                  animated && 'hover:scale-110'
                )}
              >
                <EventIcon
                  className={cn(
                    colors.text,
                    colors.textDark,
                    compact ? 'h-4 w-4' : 'h-5 w-5'
                  )}
                />
                {event.isLatest && (
                  <span
                    className="absolute -top-1 -right-1 w-3 h-3 bg-primary rounded-full animate-pulse"
                    aria-hidden="true"
                  />
                )}
              </div>
            </TooltipTrigger>
            <TooltipContent side="right" className="max-w-xs">
              <div className="space-y-1">
                {event.user_id && (
                  <p className="text-xs text-muted-foreground">
                    By: {event.user_id}
                  </p>
                )}
                {event.level && (
                  <Badge variant="outline" className="text-xs">
                    Level {event.level}
                  </Badge>
                )}
              </div>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        {/* Vertical connector */}
        {!isLast && (
          <div className="flex flex-col items-center flex-1 min-h-[40px]">
            <div
              className={cn(
                'w-0.5 flex-1',
                colors.connector,
                colors.connectorDark,
                'rounded-full'
              )}
              aria-hidden="true"
            />
          </div>
        )}
      </div>

      {/* Content */}
      <div className={cn('flex-1 pb-6', isLast && 'pb-0')}>
        <div className="flex items-start justify-between gap-2">
          <div>
            <Badge
              variant="outline"
              className={cn(
                colors.bg,
                colors.bgDark,
                colors.text,
                colors.textDark,
                'text-xs font-medium'
              )}
            >
              {stateLabels[event.event_type]}
            </Badge>
            <p className={cn('text-sm mt-1', compact && 'text-xs')}>
              {event.message}
            </p>
            {event.user_id && !compact && (
              <p className="text-xs text-muted-foreground mt-1">
                <User className="h-3 w-3 inline mr-1" />
                {event.user_id}
              </p>
            )}
          </div>
          <div className="text-right shrink-0">
            <p className="text-xs text-muted-foreground">
              {formatTimestamp(event.created_at)}
            </p>
            {showDuration && duration && (
              <Badge variant="secondary" className="text-xs gap-1 mt-1">
                <Timer className="h-3 w-3" />
                {duration}
              </Badge>
            )}
          </div>
        </div>
        {event.level && (
          <Badge variant="outline" className="mt-2 text-xs">
            Level {event.level}
          </Badge>
        )}
      </div>
    </div>
  )
}

/**
 * Main EscalationTimeline Component
 */
export function EscalationTimeline({
  events,
  currentState,
  className,
  orientation = 'auto',
  showDuration = true,
  animated = true,
  compact = false,
}: EscalationTimelineProps) {
  const content = useIntlayer('notificationsAdvanced')
  const containerRef = useRef<HTMLDivElement>(null)
  const [isHorizontal, setIsHorizontal] = useState(false)

  // Determine orientation based on container width
  useEffect(() => {
    if (orientation !== 'auto') {
      setIsHorizontal(orientation === 'horizontal')
      return
    }

    const updateOrientation = () => {
      if (containerRef.current) {
        const width = containerRef.current.offsetWidth
        setIsHorizontal(width >= 640)
      }
    }

    updateOrientation()
    const resizeObserver = new ResizeObserver(updateOrientation)
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current)
    }

    return () => resizeObserver.disconnect()
  }, [orientation])

  // Process events and mark the latest
  const processedEvents = useMemo(() => {
    if (!events || events.length === 0) return []

    // Sort by timestamp
    const sorted = [...events].sort(
      (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    )

    // Mark the latest event
    return sorted.map((event, index) => ({
      ...event,
      isLatest: index === sorted.length - 1,
    }))
  }, [events])

  if (!processedEvents || processedEvents.length === 0) {
    return (
      <div
        className={cn(
          'flex items-center justify-center py-8 text-muted-foreground',
          className
        )}
        role="status"
      >
        <Clock className="h-5 w-5 mr-2 opacity-50" />
        <span>{content.timeline?.noEvents ?? 'No events recorded'}</span>
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className={cn('w-full', className)}
      role="list"
      aria-label={String(content.incidents.timeline)}
    >
      <div
        className={cn(
          isHorizontal
            ? 'flex items-start justify-start gap-2 overflow-x-auto pb-4 px-2'
            : 'space-y-0'
        )}
      >
        {processedEvents.map((event, index) => (
          <TimelineNode
            key={event.id || index}
            event={event}
            index={index}
            isLast={index === processedEvents.length - 1}
            isHorizontal={isHorizontal}
            showDuration={showDuration}
            nextEvent={processedEvents[index + 1]}
            animated={animated}
            compact={compact}
          />
        ))}
      </div>

      {/* Current state summary */}
      <div
        className={cn(
          'mt-4 pt-4 border-t flex items-center justify-between',
          isHorizontal && 'mt-6'
        )}
      >
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">
            {content.timeline?.currentState ?? 'Current State'}:
          </span>
          <Badge
            className={cn(
              STATE_COLORS[currentState].bg,
              STATE_COLORS[currentState].bgDark,
              STATE_COLORS[currentState].text,
              STATE_COLORS[currentState].textDark,
              'gap-1'
            )}
          >
            {(() => {
              const StateIcon = EVENT_ICONS[currentState] || AlertTriangle
              return <StateIcon className="h-3 w-3" />
            })()}
            {content.states[currentState]}
          </Badge>
        </div>
        <p className="text-xs text-muted-foreground">
          {processedEvents.length} {content.timeline?.events ?? 'events'}
        </p>
      </div>
    </div>
  )
}

export default EscalationTimeline
