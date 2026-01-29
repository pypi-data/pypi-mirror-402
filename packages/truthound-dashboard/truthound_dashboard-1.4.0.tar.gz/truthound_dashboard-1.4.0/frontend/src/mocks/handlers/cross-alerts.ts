/**
 * Cross-alerts API mock handlers.
 *
 * Handles all cross-alert correlation endpoints:
 * - Get correlations
 * - Find correlations for source
 * - Get/update auto-trigger config
 * - List trigger events
 * - Manual triggers
 * - Get summary
 */

import { http, HttpResponse, delay } from 'msw'
import { createId, createTimestamp, randomInt, randomChoice } from '../factories/base'

const API_BASE = '/api/v1'

// In-memory storage for mock data
let globalConfig = {
  enabled: true,
  trigger_drift_on_anomaly: true,
  trigger_anomaly_on_drift: true,
  thresholds: {
    anomaly_rate_threshold: 0.1,
    anomaly_count_threshold: 10,
    drift_percentage_threshold: 10.0,
    drift_columns_threshold: 2,
  },
  notify_on_correlation: true,
  notification_channel_ids: null as string[] | null,
  cooldown_seconds: 300,
  last_anomaly_trigger_at: null as string | null,
  last_drift_trigger_at: null as string | null,
}

const sourceConfigs: Record<string, typeof globalConfig> = {}
const correlations: any[] = []
const triggerEvents: any[] = []

// Generate mock correlated alerts
function generateMockCorrelations(sourceId: string, count: number = 5): any[] {
  const strengths = ['strong', 'moderate', 'weak'] as const
  const severities = ['critical', 'high', 'medium', 'low'] as const
  const columns = ['amount', 'quantity', 'price', 'revenue', 'count', 'total', 'score', 'rate']

  const results = []
  for (let i = 0; i < count; i++) {
    const strength = randomChoice(strengths)
    const timeDelta = randomInt(60, 7200) // 1 min to 2 hours

    const anomalyCreatedAt = new Date(Date.now() - randomInt(0, 86400000)) // within 24h
    const driftCreatedAt = new Date(anomalyCreatedAt.getTime() + timeDelta * 1000)

    const commonCols = columns.slice(0, randomInt(1, 4))
    const driftedCols = [...commonCols, ...columns.slice(4, 4 + randomInt(0, 2))]

    results.push({
      id: createId(),
      source_id: sourceId,
      source_name: `Source ${sourceId.slice(0, 8)}`,
      correlation_strength: strength,
      confidence_score: strength === 'strong' ? 0.85 + Math.random() * 0.15 :
                        strength === 'moderate' ? 0.6 + Math.random() * 0.25 :
                        0.3 + Math.random() * 0.3,
      time_delta_seconds: timeDelta,
      anomaly_alert: {
        alert_id: createId(),
        alert_type: 'anomaly',
        source_id: sourceId,
        source_name: `Source ${sourceId.slice(0, 8)}`,
        severity: randomChoice(severities),
        message: `Detected ${randomInt(5, 100)} anomalies (${(Math.random() * 20).toFixed(1)}% rate)`,
        created_at: anomalyCreatedAt.toISOString(),
        anomaly_rate: Math.random() * 0.2,
        anomaly_count: randomInt(5, 100),
        drift_percentage: null,
        drifted_columns: null,
      },
      drift_alert: {
        alert_id: createId(),
        alert_type: 'drift',
        source_id: sourceId,
        source_name: `Source ${sourceId.slice(0, 8)}`,
        severity: randomChoice(severities),
        message: `Drift detected: ${(Math.random() * 40 + 10).toFixed(1)}% of columns drifted`,
        created_at: driftCreatedAt.toISOString(),
        anomaly_rate: null,
        anomaly_count: null,
        drift_percentage: Math.random() * 40 + 10,
        drifted_columns: driftedCols,
      },
      common_columns: commonCols,
      suggested_action: strength === 'strong'
        ? `Investigate upstream changes affecting columns: ${commonCols.slice(0, 2).join(', ')}`
        : strength === 'moderate'
        ? 'Review data quality and consider updating baseline'
        : 'Monitor for recurring patterns',
      notes: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
  }

  return results.sort((a, b) => b.confidence_score - a.confidence_score)
}

// Generate mock trigger events
function generateMockTriggerEvents(sourceId: string, count: number = 5): any[] {
  const triggerTypes = ['anomaly_to_drift', 'drift_to_anomaly'] as const
  const statuses = ['completed', 'skipped', 'failed'] as const

  const results = []
  for (let i = 0; i < count; i++) {
    const triggerType = randomChoice(triggerTypes)
    const status = randomChoice(statuses)

    results.push({
      id: createId(),
      source_id: sourceId,
      trigger_type: triggerType,
      trigger_alert_id: createId(),
      trigger_alert_type: triggerType === 'anomaly_to_drift' ? 'anomaly' : 'drift',
      result_id: status === 'completed' ? createId() : null,
      correlation_found: status === 'completed' && Math.random() > 0.5,
      correlation_id: status === 'completed' && Math.random() > 0.5 ? createId() : null,
      status,
      error_message: status === 'failed' ? 'Connection timeout' : null,
      skipped_reason: status === 'skipped' ? 'Cooldown active (180s remaining)' : null,
      created_at: createTimestamp(-randomInt(0, 86400)),
      updated_at: createTimestamp(-randomInt(0, 86400)),
    })
  }

  return results.sort((a, b) =>
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  )
}

export const crossAlertsHandlers = [
  // Get correlations (paginated list)
  http.get(`${API_BASE}/cross-alerts/correlations`, async ({ request }) => {
    await delay(150)

    const url = new URL(request.url)
    const sourceId = url.searchParams.get('source_id')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')
    const offset = parseInt(url.searchParams.get('offset') ?? '0')

    let filtered = correlations
    if (sourceId) {
      filtered = correlations.filter(c => c.source_id === sourceId)
    }

    const total = filtered.length
    const paginated = filtered.slice(offset, offset + limit)

    return HttpResponse.json({
      success: true,
      data: paginated,
      total,
      offset,
      limit,
    })
  }),

  // Find correlations for a specific source
  http.get(`${API_BASE}/cross-alerts/correlations/:sourceId`, async ({ params, request }) => {
    await delay(300)

    const sourceId = params.sourceId as string
    const url = new URL(request.url)
    // timeWindowHours is parsed for future filtering support
    const _timeWindowHours = parseInt(url.searchParams.get('time_window_hours') ?? '24')
    void _timeWindowHours // silence unused warning
    const limit = parseInt(url.searchParams.get('limit') ?? '50')

    // Generate mock correlations for this source
    const mockCorrelations = generateMockCorrelations(sourceId, Math.min(limit, randomInt(2, 8)))

    return HttpResponse.json({
      success: true,
      data: mockCorrelations,
      total: mockCorrelations.length,
    })
  }),

  // Get auto-trigger config
  http.get(`${API_BASE}/cross-alerts/config`, async ({ request }) => {
    await delay(100)

    const url = new URL(request.url)
    const sourceId = url.searchParams.get('source_id')

    if (sourceId && sourceConfigs[sourceId]) {
      return HttpResponse.json({
        success: true,
        data: { ...globalConfig, ...sourceConfigs[sourceId] },
      })
    }

    return HttpResponse.json({
      success: true,
      data: globalConfig,
    })
  }),

  // Create/update auto-trigger config
  http.post(`${API_BASE}/cross-alerts/config`, async ({ request }) => {
    await delay(150)

    const body = await request.json() as any
    const { source_id, ...configData } = body

    if (source_id) {
      sourceConfigs[source_id] = { ...sourceConfigs[source_id], ...configData }
      return HttpResponse.json({
        success: true,
        data: { ...globalConfig, ...sourceConfigs[source_id] },
      }, { status: 201 })
    }

    globalConfig = { ...globalConfig, ...configData }
    return HttpResponse.json({
      success: true,
      data: globalConfig,
    }, { status: 201 })
  }),

  // Update auto-trigger config
  http.put(`${API_BASE}/cross-alerts/config`, async ({ request }) => {
    await delay(150)

    const url = new URL(request.url)
    const sourceId = url.searchParams.get('source_id')
    const body = await request.json() as any

    if (sourceId) {
      sourceConfigs[sourceId] = { ...sourceConfigs[sourceId], ...body }
      return HttpResponse.json({
        success: true,
        data: { ...globalConfig, ...sourceConfigs[sourceId] },
      })
    }

    globalConfig = { ...globalConfig, ...body }
    return HttpResponse.json({
      success: true,
      data: globalConfig,
    })
  }),

  // List auto-trigger events
  http.get(`${API_BASE}/cross-alerts/events`, async ({ request }) => {
    await delay(150)

    const url = new URL(request.url)
    const sourceId = url.searchParams.get('source_id')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')
    const offset = parseInt(url.searchParams.get('offset') ?? '0')

    // Generate mock events if empty
    if (triggerEvents.length === 0) {
      triggerEvents.push(...generateMockTriggerEvents('default-source', 10))
    }

    let filtered = triggerEvents
    if (sourceId) {
      filtered = triggerEvents.filter(e => e.source_id === sourceId)
    }

    const total = filtered.length
    const paginated = filtered.slice(offset, offset + limit)

    return HttpResponse.json({
      success: true,
      data: paginated,
      total,
      offset,
      limit,
    })
  }),

  // Manual trigger: drift on anomaly
  http.post(`${API_BASE}/cross-alerts/trigger/drift-on-anomaly/:detectionId`, async ({ params }) => {
    await delay(500)

    const detectionId = params.detectionId as string

    const event = {
      id: createId(),
      source_id: createId(),
      trigger_type: 'anomaly_to_drift',
      trigger_alert_id: detectionId,
      trigger_alert_type: 'anomaly',
      result_id: createId(),
      correlation_found: Math.random() > 0.5,
      correlation_id: Math.random() > 0.5 ? createId() : null,
      status: 'completed',
      error_message: null,
      skipped_reason: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }

    triggerEvents.unshift(event)

    return HttpResponse.json({
      success: true,
      data: event,
    })
  }),

  // Manual trigger: anomaly on drift
  http.post(`${API_BASE}/cross-alerts/trigger/anomaly-on-drift/:monitorId`, async ({ params }) => {
    await delay(500)

    const monitorId = params.monitorId as string

    const event = {
      id: createId(),
      source_id: createId(),
      trigger_type: 'drift_to_anomaly',
      trigger_alert_id: monitorId,
      trigger_alert_type: 'drift',
      result_id: createId(),
      correlation_found: Math.random() > 0.5,
      correlation_id: Math.random() > 0.5 ? createId() : null,
      status: 'completed',
      error_message: null,
      skipped_reason: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }

    triggerEvents.unshift(event)

    return HttpResponse.json({
      success: true,
      data: event,
    })
  }),

  // Get summary
  http.get(`${API_BASE}/cross-alerts/summary`, async () => {
    await delay(100)

    const strongCount = correlations.filter(c => c.correlation_strength === 'strong').length
    const moderateCount = correlations.filter(c => c.correlation_strength === 'moderate').length
    const weakCount = correlations.filter(c => c.correlation_strength === 'weak').length

    const now = Date.now()
    const last24h = now - 86400000

    const recentCorrelations = correlations.filter(
      c => new Date(c.created_at).getTime() > last24h
    ).length
    const recentTriggers = triggerEvents.filter(
      e => new Date(e.created_at).getTime() > last24h
    ).length

    const anomalyToDrift = triggerEvents.filter(
      e => e.trigger_type === 'anomaly_to_drift'
    ).length
    const driftToAnomaly = triggerEvents.filter(
      e => e.trigger_type === 'drift_to_anomaly'
    ).length

    return HttpResponse.json({
      success: true,
      data: {
        total_correlations: correlations.length,
        strong_correlations: strongCount,
        moderate_correlations: moderateCount,
        weak_correlations: weakCount,
        recent_correlations_24h: recentCorrelations,
        recent_auto_triggers_24h: recentTriggers,
        top_affected_sources: [],
        auto_trigger_enabled: globalConfig.enabled,
        anomaly_to_drift_triggers: anomalyToDrift,
        drift_to_anomaly_triggers: driftToAnomaly,
      },
    })
  }),
]
