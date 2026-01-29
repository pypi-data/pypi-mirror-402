/**
 * IncidentDetailDialog - View escalation incident details.
 *
 * Displays:
 * - Incident metadata
 * - Current state and escalation level
 * - Escalation policy summary
 * - Next escalation countdown
 * - Visual timeline with animation
 * - Quick actions (acknowledge, resolve)
 */

import { useState, useEffect, useCallback } from 'react'
import { useIntlayer } from 'react-intlayer'
import {
  AlertTriangle,
  Clock,
  CheckCircle2,
  Bell,
  User,
  ArrowUp,
  Shield,
  ChevronDown,
  ChevronUp,
  Timer,
  Layers,
  Play,
} from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Progress } from '@/components/ui/progress'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { cn, formatDate } from '@/lib/utils'
import { str } from '@/lib/intlayer-utils'
import { EscalationTimeline } from './EscalationTimeline'

export type IncidentState =
  | 'pending'
  | 'triggered'
  | 'acknowledged'
  | 'escalated'
  | 'resolved'

export interface IncidentEvent {
  id: string
  event_type: 'created' | 'triggered' | 'escalated' | 'acknowledged' | 'resolved'
  message: string
  user_id?: string
  level?: number
  created_at: string
}

export interface EscalationTarget {
  type: 'user' | 'group' | 'oncall' | 'channel'
  identifier: string
  channel?: string
}

export interface EscalationLevel {
  level: number
  delay_minutes: number
  targets: EscalationTarget[]
}

export interface EscalationPolicy {
  id: string
  name: string
  description?: string
  levels: EscalationLevel[]
  max_escalations: number
  auto_resolve_on_success: boolean
  is_active: boolean
}

export interface EscalationIncident {
  id: string
  policy_id: string
  policy_name?: string
  notification_id: string
  state: IncidentState
  current_level: number
  max_level: number
  escalation_count: number
  acknowledged_by?: string
  acknowledged_at?: string
  resolved_by?: string
  resolved_at?: string
  resolution_note?: string
  next_escalation_at?: string
  events?: IncidentEvent[]
  policy?: EscalationPolicy
  created_at: string
  updated_at: string
}

interface IncidentDetailDialogProps {
  incident: EscalationIncident | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onAcknowledge?: (id: string) => void
  onResolve?: (id: string, note?: string) => void
  isAcknowledging?: boolean
  isResolving?: boolean
}

const STATE_CONFIG: Record<
  IncidentState,
  {
    label: string
    icon: typeof Bell
    color: string
    bgColor: string
  }
> = {
  pending: {
    label: 'Pending',
    icon: Clock,
    color: 'text-yellow-600 dark:text-yellow-400',
    bgColor: 'bg-yellow-100 dark:bg-yellow-900/30',
  },
  triggered: {
    label: 'Triggered',
    icon: Bell,
    color: 'text-orange-600 dark:text-orange-400',
    bgColor: 'bg-orange-100 dark:bg-orange-900/30',
  },
  acknowledged: {
    label: 'Acknowledged',
    icon: CheckCircle2,
    color: 'text-blue-600 dark:text-blue-400',
    bgColor: 'bg-blue-100 dark:bg-blue-900/30',
  },
  escalated: {
    label: 'Escalated',
    icon: ArrowUp,
    color: 'text-red-600 dark:text-red-400',
    bgColor: 'bg-red-100 dark:bg-red-900/30',
  },
  resolved: {
    label: 'Resolved',
    icon: Shield,
    color: 'text-green-600 dark:text-green-400',
    bgColor: 'bg-green-100 dark:bg-green-900/30',
  },
}

/**
 * Countdown timer hook for next escalation
 */
function useCountdown(targetDate: string | undefined | null) {
  const [timeLeft, setTimeLeft] = useState<{
    minutes: number
    seconds: number
    total: number
    isExpired: boolean
  }>({ minutes: 0, seconds: 0, total: 0, isExpired: true })

  useEffect(() => {
    if (!targetDate) {
      setTimeLeft({ minutes: 0, seconds: 0, total: 0, isExpired: true })
      return
    }

    const updateCountdown = () => {
      const now = new Date().getTime()
      const target = new Date(targetDate).getTime()
      const diff = target - now

      if (diff <= 0) {
        setTimeLeft({ minutes: 0, seconds: 0, total: 0, isExpired: true })
        return
      }

      const minutes = Math.floor(diff / 60000)
      const seconds = Math.floor((diff % 60000) / 1000)
      setTimeLeft({ minutes, seconds, total: diff, isExpired: false })
    }

    updateCountdown()
    const interval = setInterval(updateCountdown, 1000)
    return () => clearInterval(interval)
  }, [targetDate])

  return timeLeft
}

/**
 * Policy Summary Component
 */
interface PolicySummaryProps {
  policy?: EscalationPolicy
  currentLevel: number
  maxLevel: number
}

function PolicySummary({ policy, currentLevel, maxLevel }: PolicySummaryProps) {
  const content = useIntlayer('notificationsAdvanced')
  const [isOpen, setIsOpen] = useState(false)

  if (!policy) {
    return null
  }

  const progressPercent = maxLevel > 0 ? (currentLevel / maxLevel) * 100 : 0

  return (
    <Card>
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CardHeader className="py-3">
          <CollapsibleTrigger asChild>
            <Button
              variant="ghost"
              className="w-full justify-between p-0 h-auto hover:bg-transparent"
            >
              <CardTitle className="text-sm flex items-center gap-2">
                <Layers className="h-4 w-4" />
                {content.timeline?.policySummary ?? 'Escalation Policy'}
              </CardTitle>
              {isOpen ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>
          </CollapsibleTrigger>
        </CardHeader>
        <CardContent className="py-2">
          {/* Policy name and progress */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">{policy.name}</span>
              <Badge variant="outline" className="text-xs">
                {policy.levels.length} {content.escalation.levels}
              </Badge>
            </div>

            {/* Level progress bar */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>
                  {content.timeline?.currentLevel ?? 'Current Level'}: {currentLevel}
                </span>
                <span>
                  {content.timeline?.maxLevel ?? 'Max'}: {maxLevel}
                </span>
              </div>
              <Progress value={progressPercent} className="h-2" />
            </div>

            <CollapsibleContent className="space-y-3 pt-2">
              {/* Policy description */}
              {policy.description && (
                <p className="text-sm text-muted-foreground">{policy.description}</p>
              )}

              {/* Levels detail */}
              <div className="space-y-2">
                <p className="text-xs font-medium text-muted-foreground uppercase">
                  {content.timeline?.escalationLevels ?? 'Escalation Levels'}
                </p>
                {policy.levels.map((level) => (
                  <div
                    key={level.level}
                    className={cn(
                      'flex items-center justify-between p-2 rounded-md text-sm',
                      level.level === currentLevel
                        ? 'bg-primary/10 border border-primary/20'
                        : 'bg-muted/50'
                    )}
                  >
                    <div className="flex items-center gap-2">
                      {level.level === currentLevel && (
                        <Play className="h-3 w-3 text-primary" />
                      )}
                      <span className={cn(level.level === currentLevel && 'font-medium')}>
                        Level {level.level}
                      </span>
                      <span className="text-muted-foreground">
                        ({level.delay_minutes}m delay)
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      {level.targets.slice(0, 2).map((target, idx) => (
                        <TooltipProvider key={idx}>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Badge variant="secondary" className="text-xs">
                                {target.type === 'user' && <User className="h-3 w-3 mr-1" />}
                                {target.identifier.split('@')[0]}
                              </Badge>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>{target.identifier}</p>
                              {target.channel && <p className="text-xs">via {target.channel}</p>}
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      ))}
                      {level.targets.length > 2 && (
                        <Badge variant="outline" className="text-xs">
                          +{level.targets.length - 2}
                        </Badge>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Policy settings */}
              <div className="flex gap-4 pt-2 text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <ArrowUp className="h-3 w-3" />
                  {content.escalation.maxEscalations}: {policy.max_escalations}
                </span>
                {policy.auto_resolve_on_success && (
                  <span className="flex items-center gap-1">
                    <Shield className="h-3 w-3" />
                    {content.escalation.autoResolve}
                  </span>
                )}
              </div>
            </CollapsibleContent>
          </div>
        </CardContent>
      </Collapsible>
    </Card>
  )
}

/**
 * Next Escalation Countdown Component
 */
interface NextEscalationCountdownProps {
  nextEscalationAt: string | undefined | null
  currentLevel: number
  maxLevel: number
  state: IncidentState
}

function NextEscalationCountdown({
  nextEscalationAt,
  currentLevel,
  maxLevel,
  state,
}: NextEscalationCountdownProps) {
  const content = useIntlayer('notificationsAdvanced')
  const countdown = useCountdown(nextEscalationAt)

  // Don't show if resolved or no next escalation
  if (state === 'resolved' || !nextEscalationAt || countdown.isExpired) {
    return null
  }

  const isUrgent = countdown.total < 60000 // Less than 1 minute

  return (
    <Card className={cn(isUrgent && 'border-red-300 dark:border-red-700')}>
      <CardContent className="py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div
              className={cn(
                'p-2 rounded-full',
                isUrgent
                  ? 'bg-red-100 dark:bg-red-900/30'
                  : 'bg-orange-100 dark:bg-orange-900/30'
              )}
            >
              <Timer
                className={cn(
                  'h-4 w-4',
                  isUrgent
                    ? 'text-red-600 dark:text-red-400'
                    : 'text-orange-600 dark:text-orange-400',
                  isUrgent && 'animate-pulse'
                )}
              />
            </div>
            <div>
              <p className="text-sm font-medium">
                {content.incidents.nextEscalation}
              </p>
              <p className="text-xs text-muted-foreground">
                {content.timeline?.toLevel ?? 'To Level'} {Math.min(currentLevel + 1, maxLevel)}
              </p>
            </div>
          </div>
          <div className="text-right">
            <div
              className={cn(
                'text-2xl font-mono font-bold tabular-nums',
                isUrgent
                  ? 'text-red-600 dark:text-red-400'
                  : 'text-orange-600 dark:text-orange-400'
              )}
            >
              {countdown.minutes.toString().padStart(2, '0')}:
              {countdown.seconds.toString().padStart(2, '0')}
            </div>
            <p className="text-xs text-muted-foreground">
              {content.timeline?.remaining ?? 'remaining'}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Quick Actions Component
 */
interface QuickActionsProps {
  incident: EscalationIncident
  onAcknowledge?: (id: string) => void
  onResolve?: (id: string, note?: string) => void
  isAcknowledging?: boolean
  isResolving?: boolean
}

function QuickActions({
  incident,
  onAcknowledge,
  onResolve,
  isAcknowledging = false,
  isResolving = false,
}: QuickActionsProps) {
  const content = useIntlayer('notificationsAdvanced')
  const [showResolveNote, setShowResolveNote] = useState(false)
  const [resolveNote, setResolveNote] = useState('')

  const canAcknowledge =
    incident.state === 'triggered' || incident.state === 'escalated'
  const canResolve =
    incident.state === 'triggered' ||
    incident.state === 'escalated' ||
    incident.state === 'acknowledged'

  const handleResolve = useCallback(() => {
    if (onResolve) {
      onResolve(incident.id, resolveNote || undefined)
      setResolveNote('')
      setShowResolveNote(false)
    }
  }, [incident.id, onResolve, resolveNote])

  if (!canAcknowledge && !canResolve) {
    return null
  }

  return (
    <Card>
      <CardHeader className="py-3">
        <CardTitle className="text-sm flex items-center gap-2">
          <Play className="h-4 w-4" />
          {content.timeline?.quickActions ?? 'Quick Actions'}
        </CardTitle>
      </CardHeader>
      <CardContent className="py-2 space-y-3">
        <div className="flex gap-2">
          {canAcknowledge && onAcknowledge && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={() => onAcknowledge(incident.id)}
                    disabled={isAcknowledging}
                  >
                    <CheckCircle2 className="h-4 w-4 mr-2" />
                    {isAcknowledging
                      ? (content.timeline?.acknowledging ?? 'Acknowledging...')
                      : content.incidents.actions.acknowledge}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>{content.timeline?.acknowledgeHint ?? 'Mark this incident as seen and being handled'}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
          {canResolve && onResolve && !showResolveNote && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    className="flex-1"
                    onClick={() => setShowResolveNote(true)}
                    disabled={isResolving}
                  >
                    <Shield className="h-4 w-4 mr-2" />
                    {content.incidents.actions.resolve}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>{content.timeline?.resolveHint ?? 'Mark this incident as resolved'}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>

        {/* Resolution note input */}
        {showResolveNote && (
          <div className="space-y-2">
            <Label htmlFor="resolve-note" className="text-xs">
              {content.timeline?.resolutionNote ?? 'Resolution Note (optional)'}
            </Label>
            <Textarea
              id="resolve-note"
              value={resolveNote}
              onChange={(e) => setResolveNote(e.target.value)}
              placeholder={str(content.timeline?.resolutionPlaceholder ?? 'Describe how the incident was resolved...')}
              rows={2}
              className="text-sm"
            />
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowResolveNote(false)}
              >
                {content.timeline?.cancelResolve ?? 'Cancel'}
              </Button>
              <Button
                size="sm"
                onClick={handleResolve}
                disabled={isResolving}
              >
                <Shield className="h-4 w-4 mr-2" />
                {isResolving
                  ? (content.timeline?.resolving ?? 'Resolving...')
                  : (content.timeline?.confirmResolve ?? 'Confirm Resolve')}
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export function IncidentDetailDialog({
  incident,
  open,
  onOpenChange,
  onAcknowledge,
  onResolve,
  isAcknowledging = false,
  isResolving = false,
}: IncidentDetailDialogProps) {
  const content = useIntlayer('notificationsAdvanced')

  if (!incident) return null

  const stateConfig = STATE_CONFIG[incident.state]
  const StateIcon = stateConfig.icon

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-orange-500" />
            {content.timeline?.incidentDetails ?? 'Incident Details'}
          </DialogTitle>
          <DialogDescription className="flex items-center gap-2">
            <Badge
              className={cn(
                'gap-1',
                stateConfig.bgColor,
                stateConfig.color
              )}
            >
              <StateIcon className="h-3 w-3" />
              {content.states[incident.state]}
            </Badge>
            <span className="text-muted-foreground">
              {incident.policy_name || incident.policy_id}
            </span>
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="flex-1 pr-4">
          <div className="space-y-4 py-4">
            {/* Status Overview */}
            <Card>
              <CardContent className="py-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">
                      {content.timeline?.status ?? 'Status'}
                    </p>
                    <div className="flex items-center gap-2">
                      <Badge
                        className={cn(
                          'gap-1',
                          stateConfig.bgColor,
                          stateConfig.color
                        )}
                      >
                        <StateIcon className="h-3 w-3" />
                        {content.states[incident.state]}
                      </Badge>
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">
                      {content.incidents.currentLevel}
                    </p>
                    <p className="font-medium">
                      {incident.current_level} / {incident.max_level}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">
                      {content.incidents.escalationCount}
                    </p>
                    <p className="font-medium">{incident.escalation_count}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">
                      {content.common.created}
                    </p>
                    <p className="text-sm">{formatDate(incident.created_at)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Next Escalation Countdown */}
            <NextEscalationCountdown
              nextEscalationAt={incident.next_escalation_at}
              currentLevel={incident.current_level}
              maxLevel={incident.max_level}
              state={incident.state}
            />

            {/* Quick Actions */}
            <QuickActions
              incident={incident}
              onAcknowledge={onAcknowledge}
              onResolve={onResolve}
              isAcknowledging={isAcknowledging}
              isResolving={isResolving}
            />

            {/* Policy Summary */}
            <PolicySummary
              policy={incident.policy}
              currentLevel={incident.current_level}
              maxLevel={incident.max_level}
            />

            {/* Acknowledgment/Resolution Info */}
            {(incident.acknowledged_by || incident.resolved_by) && (
              <Card>
                <CardContent className="py-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {incident.acknowledged_by && (
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">
                          {content.incidents.acknowledgedBy}
                        </p>
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">
                            {incident.acknowledged_by}
                          </span>
                        </div>
                        {incident.acknowledged_at && (
                          <p className="text-xs text-muted-foreground mt-1">
                            {formatDate(incident.acknowledged_at)}
                          </p>
                        )}
                      </div>
                    )}
                    {incident.resolved_by && (
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">
                          {content.incidents.resolvedBy}
                        </p>
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">
                            {incident.resolved_by}
                          </span>
                        </div>
                        {incident.resolved_at && (
                          <p className="text-xs text-muted-foreground mt-1">
                            {formatDate(incident.resolved_at)}
                          </p>
                        )}
                        {incident.resolution_note && (
                          <p className="text-sm mt-2 p-2 bg-muted rounded">
                            {incident.resolution_note}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Event Timeline */}
            <Card>
              <CardHeader className="py-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  {content.incidents.timeline}
                </CardTitle>
              </CardHeader>
              <CardContent className="py-2">
                <EscalationTimeline
                  events={incident.events || []}
                  currentState={incident.state}
                  showDuration={true}
                  animated={true}
                  orientation="auto"
                />
              </CardContent>
            </Card>

            {/* Metadata */}
            <Card>
              <Collapsible>
                <CardHeader className="py-3">
                  <CollapsibleTrigger asChild>
                    <Button
                      variant="ghost"
                      className="w-full justify-between p-0 h-auto hover:bg-transparent"
                    >
                      <CardTitle className="text-sm">
                        {content.timeline?.technicalDetails ?? 'Technical Details'}
                      </CardTitle>
                      <ChevronDown className="h-4 w-4" />
                    </Button>
                  </CollapsibleTrigger>
                </CardHeader>
                <CollapsibleContent>
                  <CardContent className="py-2">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-muted-foreground">
                          {content.timeline?.incidentId ?? 'Incident ID'}:
                        </span>
                      </div>
                      <div className="font-mono text-xs">
                        {incident.id.slice(0, 8)}...
                      </div>
                      <div>
                        <span className="text-muted-foreground">
                          {content.timeline?.policyId ?? 'Policy ID'}:
                        </span>
                      </div>
                      <div className="font-mono text-xs">
                        {incident.policy_id.slice(0, 8)}...
                      </div>
                      <div>
                        <span className="text-muted-foreground">
                          {content.timeline?.notificationId ?? 'Notification ID'}:
                        </span>
                      </div>
                      <div className="font-mono text-xs">
                        {incident.notification_id.slice(0, 8)}...
                      </div>
                      <div>
                        <span className="text-muted-foreground">
                          {content.common.updated}:
                        </span>
                      </div>
                      <div>{formatDate(incident.updated_at)}</div>
                    </div>
                  </CardContent>
                </CollapsibleContent>
              </Collapsible>
            </Card>
          </div>
        </ScrollArea>

        <Separator />

        <DialogFooter className="pt-4">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {content.timeline?.close ?? 'Close'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default IncidentDetailDialog
