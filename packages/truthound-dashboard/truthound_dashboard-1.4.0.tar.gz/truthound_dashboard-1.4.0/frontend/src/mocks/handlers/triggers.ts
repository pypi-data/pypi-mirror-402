/**
 * MSW handlers for trigger monitoring and webhook API.
 */

import { http, HttpResponse } from 'msw'

import { getStore } from '../data/store'
import type { Schedule } from '@/api/client'

// Types for trigger monitoring
interface TriggerEvaluation {
  should_trigger: boolean
  reason: string
  evaluated_at: string
}

interface TriggerCheckStatus {
  schedule_id: string
  schedule_name: string
  trigger_type: string
  last_check_at: string | null
  next_check_at: string | null
  last_triggered_at: string | null
  check_count: number
  trigger_count: number
  is_due_for_check: boolean
  priority: number
  cooldown_remaining_seconds: number
  last_evaluation: TriggerEvaluation | null
}

interface TriggerMonitoringStats {
  total_schedules: number
  active_data_change_triggers: number
  active_webhook_triggers: number
  active_composite_triggers: number
  total_checks_last_hour: number
  total_triggers_last_hour: number
  average_check_interval_seconds: number
  next_scheduled_check_at: string | null
}

interface TriggerMonitoringResponse {
  stats: TriggerMonitoringStats
  schedules: TriggerCheckStatus[]
  checker_running: boolean
  checker_interval_seconds: number
  last_checker_run_at: string | null
}

interface WebhookTriggerRequest {
  source: string
  event_type?: string
  payload?: Record<string, unknown>
  schedule_id?: string
  source_id?: string
  timestamp?: string
}

interface WebhookTriggerResponse {
  accepted: boolean
  triggered_schedules: string[]
  message: string
  request_id: string
}

// In-memory tracking for mock data
const triggerCheckTimes: Map<string, Date> = new Map()
const triggerTriggerTimes: Map<string, Date> = new Map()
const triggerCheckCounts: Map<string, number> = new Map()
const triggerTriggerCounts: Map<string, number> = new Map()
let lastCheckerRun: Date | null = null

function generateTriggerStatuses(): TriggerCheckStatus[] {
  const store = getStore()
  const schedules = [...store.schedules.values()].filter(
    (s: Schedule) =>
      s.is_active &&
      ['data_change', 'composite', 'webhook'].includes(String(s.trigger_type) || '')
  )

  const now = new Date()
  return schedules.map((schedule: Schedule) => {
    const scheduleId = schedule.id
    const config = (schedule.trigger_config as Record<string, unknown>) || {}
    const checkIntervalMinutes = (config.check_interval_minutes as number) || 5
    const priority = (config.priority as number) || 5

    const lastCheck = triggerCheckTimes.get(scheduleId)
    const lastTriggered = triggerTriggerTimes.get(scheduleId)

    // Calculate next check time
    let nextCheck: Date | null = null
    if (lastCheck) {
      nextCheck = new Date(lastCheck.getTime() + checkIntervalMinutes * 60 * 1000)
    }

    // Calculate cooldown remaining
    const cooldownMinutes = (config.cooldown_minutes as number) || 15
    let cooldownRemaining = 0
    if (lastTriggered) {
      const cooldownEnd = new Date(
        lastTriggered.getTime() + cooldownMinutes * 60 * 1000
      )
      cooldownRemaining = Math.max(
        0,
        Math.floor((cooldownEnd.getTime() - now.getTime()) / 1000)
      )
    }

    // Check if due for check
    const isDue =
      !lastCheck ||
      now.getTime() >= lastCheck.getTime() + checkIntervalMinutes * 60 * 1000

    // Mock last evaluation
    const lastEvaluation: TriggerEvaluation | null = lastCheck
      ? {
          should_trigger: Math.random() > 0.7,
          reason: cooldownRemaining > 0
            ? 'In cooldown period'
            : 'Data change below threshold',
          evaluated_at: lastCheck.toISOString(),
        }
      : null

    return {
      schedule_id: scheduleId,
      schedule_name: schedule.name,
      trigger_type: schedule.trigger_type || 'data_change',
      last_check_at: lastCheck?.toISOString() || null,
      next_check_at: nextCheck?.toISOString() || null,
      last_triggered_at: lastTriggered?.toISOString() || null,
      check_count: triggerCheckCounts.get(scheduleId) || 0,
      trigger_count: triggerTriggerCounts.get(scheduleId) || 0,
      is_due_for_check: isDue,
      priority,
      cooldown_remaining_seconds: cooldownRemaining,
      last_evaluation: lastEvaluation,
    }
  })
}

export const triggersHandlers = [
  // GET /api/v1/triggers/monitoring - Get trigger monitoring status
  http.get('/api/v1/triggers/monitoring', async () => {
    const schedules = generateTriggerStatuses()

    // Calculate stats
    const activeDataChange = schedules.filter(
      (s) => s.trigger_type === 'data_change'
    ).length
    const activeWebhook = schedules.filter(
      (s) => s.trigger_type === 'webhook'
    ).length
    const activeComposite = schedules.filter(
      (s) => s.trigger_type === 'composite'
    ).length

    const now = new Date()
    const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000)

    // Count activity in last hour
    let checksLastHour = 0
    let triggersLastHour = 0
    triggerCheckTimes.forEach((time) => {
      if (time >= oneHourAgo) checksLastHour++
    })
    triggerTriggerTimes.forEach((time) => {
      if (time >= oneHourAgo) triggersLastHour++
    })

    // Average check interval
    const avgInterval =
      schedules.length > 0
        ? schedules.reduce((acc, _s) => acc + 5 * 60, 0) / schedules.length
        : 300

    // Next scheduled check
    const nextChecks = schedules
      .filter((s) => s.next_check_at)
      .map((s) => s.next_check_at!)
    const nextCheck = nextChecks.length > 0 ? nextChecks.sort()[0] : null

    const response: TriggerMonitoringResponse = {
      stats: {
        total_schedules: schedules.length,
        active_data_change_triggers: activeDataChange,
        active_webhook_triggers: activeWebhook,
        active_composite_triggers: activeComposite,
        total_checks_last_hour: checksLastHour,
        total_triggers_last_hour: triggersLastHour,
        average_check_interval_seconds: avgInterval,
        next_scheduled_check_at: nextCheck,
      },
      schedules: schedules.sort((a, b) => a.priority - b.priority),
      checker_running: true, // Mock: always running
      checker_interval_seconds: 60,
      last_checker_run_at: lastCheckerRun?.toISOString() || null,
    }

    // Simulate checker running
    lastCheckerRun = new Date()

    return HttpResponse.json(response)
  }),

  // GET /api/v1/triggers/schedules/:id/status - Get specific schedule trigger status
  http.get('/api/v1/triggers/schedules/:id/status', async ({ params }) => {
    const scheduleId = params.id as string
    const statuses = generateTriggerStatuses()
    const status = statuses.find((s) => s.schedule_id === scheduleId)

    if (!status) {
      return HttpResponse.json(
        {
          detail: `Schedule ${scheduleId} not found or not using monitored trigger type`,
        },
        { status: 404 }
      )
    }

    return HttpResponse.json(status)
  }),

  // POST /api/v1/triggers/webhook - Receive webhook trigger
  http.post('/api/v1/triggers/webhook', async ({ request }) => {
    const body = (await request.json()) as WebhookTriggerRequest
    const signature = request.headers.get('X-Webhook-Signature')

    const requestId = Math.random().toString(36).substring(2, 10)
    const now = new Date()

    // Find matching webhook schedules
    const store = getStore()
    const webhookSchedules = [...store.schedules.values()].filter(
      (s: Schedule) =>
        s.is_active &&
        String(s.trigger_type) === 'webhook' &&
        (!body.schedule_id || s.id === body.schedule_id) &&
        (!body.source_id || s.source_id === body.source_id)
    )

    const triggeredSchedules: string[] = []

    for (const schedule of webhookSchedules) {
      const config = (schedule.trigger_config as Record<string, unknown>) || {}
      const allowedSources = config.allowed_sources as string[] | undefined

      // Check allowed sources
      if (allowedSources && !allowedSources.includes(body.source)) {
        continue
      }

      // Check cooldown
      const cooldownMinutes = (config.cooldown_minutes as number) || 15
      const lastTriggered = triggerTriggerTimes.get(schedule.id)
      if (lastTriggered) {
        const cooldownEnd = new Date(
          lastTriggered.getTime() + cooldownMinutes * 60 * 1000
        )
        if (now < cooldownEnd) {
          continue
        }
      }

      // Check signature if required
      const requireSignature = config.require_signature as boolean
      if (requireSignature && !signature) {
        continue
      }

      // Trigger matched!
      triggerTriggerTimes.set(schedule.id, now)
      triggerTriggerCounts.set(
        schedule.id,
        (triggerTriggerCounts.get(schedule.id) || 0) + 1
      )
      triggeredSchedules.push(schedule.id)
    }

    const response: WebhookTriggerResponse = {
      accepted: true,
      triggered_schedules: triggeredSchedules,
      message:
        triggeredSchedules.length > 0
          ? `Triggered ${triggeredSchedules.length} schedule(s)`
          : 'No matching schedules triggered',
      request_id: requestId,
    }

    return HttpResponse.json(response)
  }),

  // POST /api/v1/triggers/webhook/test - Test webhook endpoint
  http.post('/api/v1/triggers/webhook/test', async ({ request }) => {
    const url = new URL(request.url)
    const source = url.searchParams.get('source') || 'test'
    const eventType = url.searchParams.get('event_type') || 'test_event'

    return HttpResponse.json({
      success: true,
      message: 'Webhook endpoint is accessible',
      received: {
        source,
        event_type: eventType,
      },
    })
  }),
]
