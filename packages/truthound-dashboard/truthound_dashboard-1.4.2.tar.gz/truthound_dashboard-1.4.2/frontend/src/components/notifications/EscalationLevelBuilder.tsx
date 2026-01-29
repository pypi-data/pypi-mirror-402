/**
 * EscalationLevelBuilder - Configure escalation levels and targets.
 *
 * Provides UI for building multi-level escalation policies with:
 * - Multiple escalation levels with configurable delays
 * - Targets per level (user, group, oncall, channel)
 * - Notification channel selection
 * - Message template support
 * - Visual timeline preview
 */

import { useCallback, useEffect, useState, useMemo } from 'react'
import { useIntlayer } from 'react-intlayer'
import {
  Plus,
  Trash2,
  GripVertical,
  User,
  Users,
  PhoneCall,
  Hash,
  Clock,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  MessageSquare,
  ArrowRight,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
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
import { cn } from '@/lib/utils'
import { str } from '@/lib/intlayer-utils'
import type {
  EscalationLevel,
  EscalationTarget,
  EscalationTargetType,
  NotificationChannel,
} from '@/api/client'
import { listNotificationChannels } from '@/api/client'

// Re-export types for compatibility
export type { EscalationLevel, EscalationTarget, EscalationTargetType }

interface EscalationLevelBuilderProps {
  levels: EscalationLevel[]
  onChange: (levels: EscalationLevel[]) => void
  maxLevels?: number
  maxDelay?: number
  className?: string
}

const TARGET_ICONS: Record<EscalationTargetType, typeof User> = {
  user: User,
  group: Users,
  oncall: PhoneCall,
  channel: Hash,
}

// Quick delay presets in minutes
const DELAY_PRESETS = [
  { value: 0, label: 'Immediate' },
  { value: 5, label: '5m' },
  { value: 15, label: '15m' },
  { value: 30, label: '30m' },
  { value: 60, label: '1h' },
  { value: 120, label: '2h' },
]

// Default labels for fallback
const DEFAULT_LABELS = {
  levels: 'Levels',
  addLevel: 'Add Level',
  targets: 'Targets',
  addTarget: 'Add Target',
  delayMinutes: 'Delay (minutes)',
  description: 'Configure notification targets and delays for each escalation level',
  levelLabel: 'Level',
  noLevels: 'No escalation levels configured. Add at least one level.',
  addFirstLevel: 'Add First Level',
  noTargets: 'No notification targets. Add users, groups, on-call schedules, or channels.',
  immediate: 'Immediate',
  minutes: 'minutes',
  immediateNote: 'This level will trigger immediately when an incident is created',
  selectChannel: 'Channel',
  noChannels: 'No channels configured',
  messageTemplate: 'Custom Message Template',
  messageTemplatePlaceholder: 'Optional: Custom message template for this level. Use {incident_ref}, {level}, {policy_name} as variables.',
  timelinePreview: 'Escalation Timeline Preview',
  totalTime: 'Total escalation time',
  validationWarning: 'Some levels have no targets or empty identifiers',
  placeholders: {
    user: 'user@example.com',
    group: 'Group name or ID',
    oncall: 'On-call schedule ID',
    channel: '#channel-name',
  },
  targetTypes: {
    user: 'User',
    group: 'Group',
    oncall: 'On-Call',
    channel: 'Channel',
  },
}

export function EscalationLevelBuilder({
  levels,
  onChange,
  maxLevels = 5,
  maxDelay = 10080, // 1 week max
  className,
}: EscalationLevelBuilderProps) {
  const content = useIntlayer('notificationsAdvanced')
  const common = useIntlayer('common')

  // Helper to safely extract string from intlayer content or use fallback
  const safeStr = (value: unknown, fallback: string): string => {
    if (value === undefined || value === null) return fallback
    if (typeof value === 'string') return value
    // Try to convert IntlayerNode-like objects
    try {
      const result = str(value as Parameters<typeof str>[0])
      return result || fallback
    } catch {
      return fallback
    }
  }

  // Safely access nested content with fallbacks
  const labels = useMemo(() => {
    // Type-safe access using any to bypass union complexity
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const esc = (content as any)?.escalation
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const lb = esc?.levelBuilder
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const tt = (content as any)?.targetTypes

    return {
      levels: safeStr(esc?.levels, DEFAULT_LABELS.levels),
      addLevel: safeStr(esc?.addLevel, DEFAULT_LABELS.addLevel),
      targets: safeStr(esc?.targets, DEFAULT_LABELS.targets),
      addTarget: safeStr(esc?.addTarget, DEFAULT_LABELS.addTarget),
      delayMinutes: safeStr(esc?.delayMinutes, DEFAULT_LABELS.delayMinutes),
      description: safeStr(lb?.description, DEFAULT_LABELS.description),
      levelLabel: safeStr(lb?.levelLabel, DEFAULT_LABELS.levelLabel),
      noLevels: safeStr(lb?.noLevels, DEFAULT_LABELS.noLevels),
      addFirstLevel: safeStr(lb?.addFirstLevel, DEFAULT_LABELS.addFirstLevel),
      noTargets: safeStr(lb?.noTargets, DEFAULT_LABELS.noTargets),
      immediate: safeStr(lb?.immediate, DEFAULT_LABELS.immediate),
      minutes: safeStr(lb?.minutes, DEFAULT_LABELS.minutes),
      immediateNote: safeStr(lb?.immediateNote, DEFAULT_LABELS.immediateNote),
      selectChannel: safeStr(lb?.selectChannel, DEFAULT_LABELS.selectChannel),
      noChannels: safeStr(lb?.noChannels, DEFAULT_LABELS.noChannels),
      messageTemplate: safeStr(lb?.messageTemplate, DEFAULT_LABELS.messageTemplate),
      messageTemplatePlaceholder: safeStr(lb?.messageTemplatePlaceholder, DEFAULT_LABELS.messageTemplatePlaceholder),
      timelinePreview: safeStr(lb?.timelinePreview, DEFAULT_LABELS.timelinePreview),
      totalTime: safeStr(lb?.totalTime, DEFAULT_LABELS.totalTime),
      validationWarning: safeStr(lb?.validationWarning, DEFAULT_LABELS.validationWarning),
      placeholders: {
        user: safeStr(lb?.placeholders?.user, DEFAULT_LABELS.placeholders.user),
        group: safeStr(lb?.placeholders?.group, DEFAULT_LABELS.placeholders.group),
        oncall: safeStr(lb?.placeholders?.oncall, DEFAULT_LABELS.placeholders.oncall),
        channel: safeStr(lb?.placeholders?.channel, DEFAULT_LABELS.placeholders.channel),
      },
      targetTypes: {
        user: safeStr(tt?.user, DEFAULT_LABELS.targetTypes.user),
        group: safeStr(tt?.group, DEFAULT_LABELS.targetTypes.group),
        oncall: safeStr(tt?.oncall, DEFAULT_LABELS.targetTypes.oncall),
        channel: safeStr(tt?.channel, DEFAULT_LABELS.targetTypes.channel),
      },
    }
  }, [content])

  // Fetch available notification channels
  const [channels, setChannels] = useState<NotificationChannel[]>([])
  const [channelsLoading, setChannelsLoading] = useState(true)
  const [expandedLevels, setExpandedLevels] = useState<Set<number>>(new Set([0]))

  useEffect(() => {
    let mounted = true
    setChannelsLoading(true)
    listNotificationChannels({ active_only: true })
      .then((res) => {
        if (mounted) {
          setChannels(res.data || [])
        }
      })
      .catch(() => {
        // Silently fail, channels will be empty
      })
      .finally(() => {
        if (mounted) setChannelsLoading(false)
      })
    return () => {
      mounted = false
    }
  }, [])

  const toggleLevelExpanded = useCallback((index: number) => {
    setExpandedLevels((prev) => {
      const next = new Set(prev)
      if (next.has(index)) {
        next.delete(index)
      } else {
        next.add(index)
      }
      return next
    })
  }, [])

  const handleAddLevel = useCallback(() => {
    if (levels.length >= maxLevels) return
    const newLevel: EscalationLevel = {
      level: levels.length + 1,
      delay_minutes: levels.length === 0 ? 0 : 15, // First level is immediate
      targets: [],
    }
    onChange([...levels, newLevel])
    // Auto-expand new level
    setExpandedLevels((prev) => new Set([...prev, levels.length]))
  }, [levels, onChange, maxLevels])

  const handleRemoveLevel = useCallback(
    (index: number) => {
      const newLevels = levels
        .filter((_, i) => i !== index)
        .map((l, i) => ({ ...l, level: i + 1 }))
      onChange(newLevels)
      setExpandedLevels((prev) => {
        const next = new Set<number>()
        prev.forEach((i) => {
          if (i < index) next.add(i)
          else if (i > index) next.add(i - 1)
        })
        return next
      })
    },
    [levels, onChange]
  )

  const handleLevelChange = useCallback(
    (index: number, updates: Partial<EscalationLevel>) => {
      const newLevels = [...levels]
      newLevels[index] = { ...newLevels[index], ...updates }
      onChange(newLevels)
    },
    [levels, onChange]
  )

  const handleAddTarget = useCallback(
    (levelIndex: number) => {
      const newLevels = [...levels]
      const newTarget: EscalationTarget = {
        type: 'user',
        identifier: '',
        channel: channels.length > 0 ? channels[0].type : '',
      }
      newLevels[levelIndex].targets.push(newTarget)
      onChange(newLevels)
    },
    [levels, onChange, channels]
  )

  const handleRemoveTarget = useCallback(
    (levelIndex: number, targetIndex: number) => {
      const newLevels = [...levels]
      newLevels[levelIndex].targets = newLevels[levelIndex].targets.filter(
        (_, i) => i !== targetIndex
      )
      onChange(newLevels)
    },
    [levels, onChange]
  )

  const handleTargetChange = useCallback(
    (levelIndex: number, targetIndex: number, updates: Partial<EscalationTarget>) => {
      const newLevels = [...levels]
      newLevels[levelIndex].targets[targetIndex] = {
        ...newLevels[levelIndex].targets[targetIndex],
        ...updates,
      }
      onChange(newLevels)
    },
    [levels, onChange]
  )

  const handleMoveLevel = useCallback(
    (index: number, direction: 'up' | 'down') => {
      if (
        (direction === 'up' && index === 0) ||
        (direction === 'down' && index === levels.length - 1)
      ) {
        return
      }
      const newLevels = [...levels]
      const targetIndex = direction === 'up' ? index - 1 : index + 1
      ;[newLevels[index], newLevels[targetIndex]] = [
        newLevels[targetIndex],
        newLevels[index],
      ]
      // Update level numbers
      newLevels.forEach((l, i) => {
        l.level = i + 1
      })
      onChange(newLevels)
      // Update expanded state
      setExpandedLevels((prev) => {
        const next = new Set<number>()
        prev.forEach((i) => {
          if (i === index) next.add(targetIndex)
          else if (i === targetIndex) next.add(index)
          else next.add(i)
        })
        return next
      })
    },
    [levels, onChange]
  )

  // Calculate total escalation time
  const totalEscalationMinutes = levels.reduce((sum, l) => sum + l.delay_minutes, 0)

  const formatDuration = (minutes: number): string => {
    if (minutes === 0) return labels.immediate
    if (minutes < 60) return `${minutes}m`
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    if (mins === 0) return `${hours}h`
    return `${hours}h ${mins}m`
  }

  const hasValidationErrors = levels.some(
    (l) => l.targets.length === 0 || l.targets.some((t) => !t.identifier.trim())
  )

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <Label className="text-base font-medium">{labels.levels}</Label>
          <p className="text-xs text-muted-foreground">{labels.description}</p>
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleAddLevel}
          disabled={levels.length >= maxLevels}
        >
          <Plus className="h-4 w-4 mr-1" />
          {labels.addLevel}
        </Button>
      </div>

      {/* Validation Warning */}
      {hasValidationErrors && levels.length > 0 && (
        <div className="flex items-center gap-2 p-2 bg-destructive/10 text-destructive rounded-md text-sm">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{labels.validationWarning}</span>
        </div>
      )}

      {/* Empty State */}
      {levels.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="py-8 text-center">
            <p className="text-sm text-muted-foreground mb-3">{labels.noLevels}</p>
            <Button type="button" variant="outline" size="sm" onClick={handleAddLevel}>
              <Plus className="h-4 w-4 mr-1" />
              {labels.addFirstLevel}
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {levels.map((level, levelIndex) => {
            const isExpanded = expandedLevels.has(levelIndex)
            const hasErrors =
              level.targets.length === 0 ||
              level.targets.some((t) => !t.identifier.trim())

            return (
              <Collapsible
                key={levelIndex}
                open={isExpanded}
                onOpenChange={() => toggleLevelExpanded(levelIndex)}
              >
                <Card
                  className={cn(
                    'relative transition-colors',
                    hasErrors && 'border-destructive/50'
                  )}
                >
                  {/* Level Header */}
                  <CollapsibleTrigger asChild>
                    <CardHeader className="py-3 px-4 cursor-pointer hover:bg-muted/50 transition-colors">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <GripVertical className="h-4 w-4 text-muted-foreground" />
                          <CardTitle className="text-sm font-medium">
                            {labels.levelLabel} {level.level}
                          </CardTitle>
                          <Badge
                            variant={level.targets.length > 0 ? 'secondary' : 'destructive'}
                            className="text-xs"
                          >
                            {level.targets.length} {labels.targets.toLowerCase()}
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            <Clock className="h-3 w-3 mr-1" />
                            {formatDuration(level.delay_minutes)}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-1">
                          {/* Move buttons */}
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  type="button"
                                  variant="ghost"
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    handleMoveLevel(levelIndex, 'up')
                                  }}
                                  disabled={levelIndex === 0}
                                  className="h-6 w-6 p-0"
                                >
                                  <ChevronUp className="h-3.5 w-3.5" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>Move up</TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  type="button"
                                  variant="ghost"
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    handleMoveLevel(levelIndex, 'down')
                                  }}
                                  disabled={levelIndex === levels.length - 1}
                                  className="h-6 w-6 p-0"
                                >
                                  <ChevronDown className="h-3.5 w-3.5" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>Move down</TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                          {/* Delete button */}
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  type="button"
                                  variant="ghost"
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    handleRemoveLevel(levelIndex)
                                  }}
                                  className="h-6 w-6 p-0"
                                >
                                  <Trash2 className="h-3.5 w-3.5 text-destructive" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>{str(common.delete)}</TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                          {/* Expand indicator */}
                          {isExpanded ? (
                            <ChevronUp className="h-4 w-4 text-muted-foreground ml-1" />
                          ) : (
                            <ChevronDown className="h-4 w-4 text-muted-foreground ml-1" />
                          )}
                        </div>
                      </div>
                    </CardHeader>
                  </CollapsibleTrigger>

                  <CollapsibleContent>
                    <CardContent className="py-3 px-4 space-y-4 border-t">
                      {/* Delay Configuration */}
                      <div className="space-y-2">
                        <Label className="text-xs font-medium">{labels.delayMinutes}</Label>
                        <div className="flex items-center gap-2 flex-wrap">
                          <Input
                            type="number"
                            min={0}
                            max={maxDelay}
                            value={level.delay_minutes}
                            onChange={(e) =>
                              handleLevelChange(levelIndex, {
                                delay_minutes: Math.min(
                                  Math.max(0, parseInt(e.target.value) || 0),
                                  maxDelay
                                ),
                              })
                            }
                            className="h-8 w-24"
                          />
                          <span className="text-xs text-muted-foreground">{labels.minutes}</span>
                          <div className="flex gap-1 flex-wrap">
                            {DELAY_PRESETS.map((preset) => (
                              <Button
                                key={preset.value}
                                type="button"
                                variant="ghost"
                                size="sm"
                                className={cn(
                                  'h-6 px-2 text-xs',
                                  level.delay_minutes === preset.value && 'bg-primary/10 text-primary'
                                )}
                                onClick={() =>
                                  handleLevelChange(levelIndex, { delay_minutes: preset.value })
                                }
                              >
                                {preset.label}
                              </Button>
                            ))}
                          </div>
                        </div>
                        {levelIndex === 0 && level.delay_minutes === 0 && (
                          <p className="text-xs text-muted-foreground">{labels.immediateNote}</p>
                        )}
                      </div>

                      {/* Targets Section */}
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <Label className="text-xs font-medium">{labels.targets}</Label>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => handleAddTarget(levelIndex)}
                            className="h-6 text-xs"
                          >
                            <Plus className="h-3 w-3 mr-1" />
                            {labels.addTarget}
                          </Button>
                        </div>

                        {level.targets.length === 0 ? (
                          <div className="text-center py-4 bg-muted/30 rounded-md">
                            <p className="text-xs text-muted-foreground mb-2">{labels.noTargets}</p>
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              onClick={() => handleAddTarget(levelIndex)}
                              className="h-7 text-xs"
                            >
                              <Plus className="h-3 w-3 mr-1" />
                              {labels.addTarget}
                            </Button>
                          </div>
                        ) : (
                          <div className="space-y-2">
                            {level.targets.map((target, targetIndex) => {
                              const Icon = TARGET_ICONS[target.type]
                              const hasError = !target.identifier.trim()

                              return (
                                <div
                                  key={targetIndex}
                                  className={cn(
                                    'flex items-center gap-2 p-2 bg-muted/50 rounded-md',
                                    hasError && 'ring-1 ring-destructive/50'
                                  )}
                                >
                                  <Icon className="h-4 w-4 text-muted-foreground shrink-0" />

                                  {/* Target Type */}
                                  <Select
                                    value={target.type}
                                    onValueChange={(v) =>
                                      handleTargetChange(levelIndex, targetIndex, {
                                        type: v as EscalationTargetType,
                                      })
                                    }
                                  >
                                    <SelectTrigger className="h-7 w-28">
                                      <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                      <SelectItem value="user">{labels.targetTypes.user}</SelectItem>
                                      <SelectItem value="group">{labels.targetTypes.group}</SelectItem>
                                      <SelectItem value="oncall">{labels.targetTypes.oncall}</SelectItem>
                                      <SelectItem value="channel">{labels.targetTypes.channel}</SelectItem>
                                    </SelectContent>
                                  </Select>

                                  {/* Identifier */}
                                  <Input
                                    placeholder={
                                      target.type === 'user'
                                        ? labels.placeholders.user
                                        : target.type === 'group'
                                          ? labels.placeholders.group
                                          : target.type === 'oncall'
                                            ? labels.placeholders.oncall
                                            : labels.placeholders.channel
                                    }
                                    value={target.identifier}
                                    onChange={(e) =>
                                      handleTargetChange(levelIndex, targetIndex, {
                                        identifier: e.target.value,
                                      })
                                    }
                                    className={cn('h-7 flex-1', hasError && 'border-destructive')}
                                  />

                                  {/* Notification Channel */}
                                  <Select
                                    value={target.channel}
                                    onValueChange={(v) =>
                                      handleTargetChange(levelIndex, targetIndex, {
                                        channel: v,
                                      })
                                    }
                                    disabled={channelsLoading}
                                  >
                                    <SelectTrigger className="h-7 w-32">
                                      <SelectValue
                                        placeholder={
                                          channelsLoading
                                            ? str(common.loading)
                                            : labels.selectChannel
                                        }
                                      />
                                    </SelectTrigger>
                                    <SelectContent>
                                      {channels.length === 0 ? (
                                        <SelectItem value="" disabled>
                                          {labels.noChannels}
                                        </SelectItem>
                                      ) : (
                                        channels.map((ch) => (
                                          <SelectItem key={ch.id} value={ch.type}>
                                            <div className="flex items-center gap-2">
                                              <Badge variant="outline" className="text-[10px] px-1">
                                                {ch.type}
                                              </Badge>
                                              <span className="truncate">{ch.name}</span>
                                            </div>
                                          </SelectItem>
                                        ))
                                      )}
                                    </SelectContent>
                                  </Select>

                                  {/* Remove Target */}
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleRemoveTarget(levelIndex, targetIndex)}
                                    className="h-6 w-6 p-0 shrink-0"
                                  >
                                    <Trash2 className="h-3 w-3 text-destructive" />
                                  </Button>
                                </div>
                              )
                            })}
                          </div>
                        )}
                      </div>

                      {/* Message Template (Advanced) */}
                      <Collapsible>
                        <CollapsibleTrigger asChild>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="h-6 text-xs text-muted-foreground"
                          >
                            <MessageSquare className="h-3 w-3 mr-1" />
                            {labels.messageTemplate}
                            <ChevronDown className="h-3 w-3 ml-1" />
                          </Button>
                        </CollapsibleTrigger>
                        <CollapsibleContent className="pt-2">
                          <Textarea
                            placeholder={labels.messageTemplatePlaceholder}
                            value={(level as EscalationLevel & { message_template?: string }).message_template || ''}
                            onChange={(e) =>
                              handleLevelChange(levelIndex, {
                                ...level,
                                message_template: e.target.value,
                              } as Partial<EscalationLevel>)
                            }
                            rows={2}
                            className="text-xs"
                          />
                        </CollapsibleContent>
                      </Collapsible>
                    </CardContent>
                  </CollapsibleContent>
                </Card>
              </Collapsible>
            )
          })}
        </div>
      )}

      {/* Escalation Timeline Preview */}
      {levels.length > 0 && (
        <Card className="bg-muted/30">
          <CardHeader className="py-2 px-4">
            <CardTitle className="text-xs font-medium text-muted-foreground">
              {labels.timelinePreview}
            </CardTitle>
          </CardHeader>
          <CardContent className="py-2 px-4">
            <div className="flex items-center gap-1 flex-wrap text-xs">
              {levels.map((l, i) => (
                <span key={i} className="flex items-center gap-1">
                  <Badge
                    variant={l.targets.length > 0 ? 'secondary' : 'destructive'}
                    className="text-[10px] px-1.5 py-0"
                  >
                    L{l.level}
                  </Badge>
                  <span className="text-muted-foreground">
                    ({l.targets.length} {labels.targets.toLowerCase()})
                  </span>
                  {i < levels.length - 1 && (
                    <span className="flex items-center text-primary mx-1">
                      <ArrowRight className="h-3 w-3" />
                      <span className="text-[10px] ml-0.5">{formatDuration(levels[i + 1].delay_minutes)}</span>
                    </span>
                  )}
                </span>
              ))}
            </div>
            <p className="text-[10px] text-muted-foreground mt-2">
              {labels.totalTime}: {formatDuration(totalEscalationMinutes)}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default EscalationLevelBuilder
