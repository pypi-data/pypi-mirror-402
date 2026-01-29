/**
 * Notifications API handlers
 */

import { http, HttpResponse, delay } from 'msw'
import {
  getStore,
  getAll,
  getById,
  create,
  update,
  remove,
  cleanupOrphanedData,
} from '../data/store'
import {
  createNotificationChannel,
  createNotificationRule,
  createNotificationStats,
  createId,
} from '../factories'

const API_BASE = '/api/v1'

export const notificationsHandlers = [
  // ============================================================================
  // Channels
  // ============================================================================

  // List channels
  http.get(`${API_BASE}/notifications/channels`, async ({ request }) => {
    await delay(200)

    const url = new URL(request.url)
    const offset = parseInt(url.searchParams.get('offset') ?? '0')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')
    const activeOnly = url.searchParams.get('active_only') === 'true'
    const channelType = url.searchParams.get('channel_type')

    let channels = getAll(getStore().notificationChannels)

    if (activeOnly) {
      channels = channels.filter((c) => c.is_active)
    }

    if (channelType) {
      channels = channels.filter((c) => c.type === channelType)
    }

    const total = channels.length
    const paginated = channels.slice(offset, offset + limit)

    return HttpResponse.json({
      success: true,
      data: paginated,
      total,
      offset,
      limit,
    })
  }),

  // Get channel by ID
  http.get(`${API_BASE}/notifications/channels/:id`, async ({ params }) => {
    await delay(150)

    const channel = getById(getStore().notificationChannels, params.id as string)

    if (!channel) {
      return HttpResponse.json(
        { detail: 'Channel not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json({
      success: true,
      data: channel,
    })
  }),

  // Create channel - supports all 9 channel types
  http.post(`${API_BASE}/notifications/channels`, async ({ request }) => {
    await delay(300)

    let body: {
      name: string
      type: string
      config: Record<string, unknown>
      is_active?: boolean
    }

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    // Validate channel type - all 9 types supported
    const validTypes = ['slack', 'email', 'webhook', 'discord', 'telegram', 'pagerduty', 'opsgenie', 'teams', 'github']
    if (!validTypes.includes(body.type)) {
      return HttpResponse.json(
        { detail: `Invalid channel type. Must be one of: ${validTypes.join(', ')}` },
        { status: 400 }
      )
    }

    const channel = createNotificationChannel({
      id: createId(),
      type: body.type as 'slack' | 'email' | 'webhook' | 'discord' | 'telegram' | 'pagerduty' | 'opsgenie' | 'teams' | 'github',
      isActive: body.is_active,
      config: body.config,
    })

    channel.name = body.name
    channel.created_at = new Date().toISOString()
    channel.updated_at = new Date().toISOString()

    create(getStore().notificationChannels, channel)

    return HttpResponse.json({
      success: true,
      data: channel,
    })
  }),

  // Update channel
  http.put(`${API_BASE}/notifications/channels/:id`, async ({ params, request }) => {
    await delay(250)

    let body: Partial<{
      name: string
      config: Record<string, unknown>
      is_active: boolean
    }>

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const updated = update(
      getStore().notificationChannels,
      params.id as string,
      body
    )

    if (!updated) {
      return HttpResponse.json(
        { detail: 'Channel not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json({
      success: true,
      data: updated,
    })
  }),

  // Delete channel
  http.delete(`${API_BASE}/notifications/channels/:id`, async ({ params }) => {
    await delay(200)

    const deleted = remove(getStore().notificationChannels, params.id as string)

    if (!deleted) {
      return HttpResponse.json(
        { detail: 'Channel not found' },
        { status: 404 }
      )
    }

    // Clean up rules and logs referencing this channel
    cleanupOrphanedData()

    return HttpResponse.json({ success: true })
  }),

  // Test channel
  http.post(`${API_BASE}/notifications/channels/:id/test`, async ({ params }) => {
    await delay(600)

    const channel = getById(getStore().notificationChannels, params.id as string)

    if (!channel) {
      return HttpResponse.json(
        { detail: 'Channel not found' },
        { status: 404 }
      )
    }

    // Simulate 85% success rate
    const success = Math.random() > 0.15

    return HttpResponse.json({
      success,
      message: success ? 'Test notification sent successfully' : undefined,
      error: success ? undefined : 'Connection failed: timeout after 10s',
    })
  }),

  // Get channel types - all 9 channel types with full schema information
  http.get(`${API_BASE}/notifications/channels/types`, async () => {
    await delay(100)

    return HttpResponse.json({
      success: true,
      data: {
        // Basic channels
        slack: {
          name: 'Slack',
          category: 'basic',
          description: 'Send notifications to Slack channels via webhooks',
          required_fields: ['webhook_url'],
          optional_fields: ['channel', 'username', 'icon_emoji'],
        },
        email: {
          name: 'Email',
          category: 'basic',
          description: 'Send notifications via SMTP email',
          required_fields: ['smtp_host', 'smtp_port', 'from_email', 'recipients'],
          optional_fields: ['smtp_user', 'smtp_password', 'use_tls'],
        },
        webhook: {
          name: 'Webhook',
          category: 'basic',
          description: 'Send notifications to custom HTTP endpoints',
          required_fields: ['url'],
          optional_fields: ['method', 'headers', 'include_event_data'],
        },
        // Chat channels
        discord: {
          name: 'Discord',
          category: 'chat',
          description: 'Send notifications to Discord channels via webhooks',
          required_fields: ['webhook_url'],
          optional_fields: ['username', 'avatar_url'],
        },
        telegram: {
          name: 'Telegram',
          category: 'chat',
          description: 'Send notifications via Telegram Bot API',
          required_fields: ['bot_token', 'chat_id'],
          optional_fields: ['parse_mode', 'disable_notification'],
        },
        teams: {
          name: 'Microsoft Teams',
          category: 'chat',
          description: 'Send notifications to Microsoft Teams channels',
          required_fields: ['webhook_url'],
          optional_fields: ['theme_color'],
        },
        // Incident management channels
        pagerduty: {
          name: 'PagerDuty',
          category: 'incident',
          description: 'Create incidents in PagerDuty for critical alerts',
          required_fields: ['routing_key'],
          optional_fields: ['severity', 'component', 'group', 'class_type'],
        },
        opsgenie: {
          name: 'OpsGenie',
          category: 'incident',
          description: 'Create alerts in OpsGenie for incident management',
          required_fields: ['api_key'],
          optional_fields: ['priority', 'tags', 'team', 'responders'],
        },
        // DevOps channels
        github: {
          name: 'GitHub',
          category: 'devops',
          description: 'Create issues in GitHub repositories for tracking',
          required_fields: ['token', 'owner', 'repo'],
          optional_fields: ['labels', 'assignees'],
        },
      },
    })
  }),

  // ============================================================================
  // Rules
  // ============================================================================

  // List rules
  http.get(`${API_BASE}/notifications/rules`, async ({ request }) => {
    await delay(200)

    const url = new URL(request.url)
    const offset = parseInt(url.searchParams.get('offset') ?? '0')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')
    const activeOnly = url.searchParams.get('active_only') === 'true'
    const condition = url.searchParams.get('condition')

    let rules = getAll(getStore().notificationRules)

    if (activeOnly) {
      rules = rules.filter((r) => r.is_active)
    }

    if (condition) {
      rules = rules.filter((r) => r.condition === condition)
    }

    const total = rules.length
    const paginated = rules.slice(offset, offset + limit)

    return HttpResponse.json({
      success: true,
      data: paginated,
      total,
      offset,
      limit,
    })
  }),

  // Get rule by ID
  http.get(`${API_BASE}/notifications/rules/:id`, async ({ params }) => {
    await delay(150)

    const rule = getById(getStore().notificationRules, params.id as string)

    if (!rule) {
      return HttpResponse.json(
        { detail: 'Rule not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json({
      success: true,
      data: rule,
    })
  }),

  // Create rule
  http.post(`${API_BASE}/notifications/rules`, async ({ request }) => {
    await delay(300)

    let body: {
      name: string
      condition: string
      channel_ids: string[]
      condition_config?: Record<string, unknown>
      source_ids?: string[]
      is_active?: boolean
    }

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    // Validate that all channel_ids exist
    const channels = getStore().notificationChannels
    const invalidChannelIds = body.channel_ids.filter((id) => !channels.has(id))
    if (invalidChannelIds.length > 0) {
      return HttpResponse.json(
        { detail: `Invalid channel IDs: ${invalidChannelIds.join(', ')}` },
        { status: 400 }
      )
    }

    const rule = createNotificationRule({
      id: createId(),
      condition: body.condition,
      channelIds: body.channel_ids,
      isActive: body.is_active,
    })

    rule.name = body.name
    rule.condition_config = body.condition_config
    rule.source_ids = body.source_ids
    rule.created_at = new Date().toISOString()
    rule.updated_at = new Date().toISOString()

    create(getStore().notificationRules, rule)

    return HttpResponse.json({
      success: true,
      data: rule,
    })
  }),

  // Update rule
  http.put(`${API_BASE}/notifications/rules/:id`, async ({ params, request }) => {
    await delay(250)

    let body: Partial<{
      name: string
      condition: string
      channel_ids: string[]
      condition_config: Record<string, unknown>
      source_ids: string[]
      is_active: boolean
    }>

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const updated = update(
      getStore().notificationRules,
      params.id as string,
      body
    )

    if (!updated) {
      return HttpResponse.json(
        { detail: 'Rule not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json({
      success: true,
      data: updated,
    })
  }),

  // Delete rule
  http.delete(`${API_BASE}/notifications/rules/:id`, async ({ params }) => {
    await delay(200)

    const deleted = remove(getStore().notificationRules, params.id as string)

    if (!deleted) {
      return HttpResponse.json(
        { detail: 'Rule not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json({ success: true })
  }),

  // Get rule conditions - all 9 conditions matching factory/notifications.ts
  http.get(`${API_BASE}/notifications/rules/conditions`, async () => {
    await delay(100)

    return HttpResponse.json({
      success: true,
      data: [
        'on_failure',
        'on_critical',
        'on_high',
        'on_drift',
        'on_success',
        'always',
        'on_warning',
        'on_error',
        'on_threshold',
      ],
    })
  }),

  // ============================================================================
  // Logs
  // ============================================================================

  // List logs
  http.get(`${API_BASE}/notifications/logs`, async ({ request }) => {
    await delay(200)

    const url = new URL(request.url)
    const offset = parseInt(url.searchParams.get('offset') ?? '0')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')
    const channelId = url.searchParams.get('channel_id')
    const status = url.searchParams.get('status')

    let logs = getAll(getStore().notificationLogs)

    if (channelId) {
      logs = logs.filter((l) => l.channel_id === channelId)
    }

    if (status) {
      logs = logs.filter((l) => l.status === status)
    }

    // Sort by created_at desc
    logs.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )

    const total = logs.length
    const paginated = logs.slice(offset, offset + limit)

    return HttpResponse.json({
      success: true,
      data: paginated,
      total,
      offset,
      limit,
    })
  }),

  // Get log by ID
  http.get(`${API_BASE}/notifications/logs/:id`, async ({ params }) => {
    await delay(150)

    const log = getById(getStore().notificationLogs, params.id as string)

    if (!log) {
      return HttpResponse.json(
        { detail: 'Log not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json({
      success: true,
      data: {
        ...log,
        message: log.message_preview,
        event_data: {
          source_id: 'source-123',
          validation_id: 'validation-456',
        },
      },
    })
  }),

  // Get notification stats
  http.get(`${API_BASE}/notifications/logs/stats`, async ({ request }) => {
    await delay(150)

    const url = new URL(request.url)
    const hours = parseInt(url.searchParams.get('hours') ?? '24')

    const stats = createNotificationStats({ hours })

    return HttpResponse.json({
      success: true,
      data: stats,
    })
  }),
]
