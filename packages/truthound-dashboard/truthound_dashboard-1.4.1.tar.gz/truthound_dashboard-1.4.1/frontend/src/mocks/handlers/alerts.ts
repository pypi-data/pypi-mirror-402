/**
 * Unified Alerts API handlers
 *
 * Handles all unified alerts endpoints:
 * - List all alerts (aggregated)
 * - Get alert summary
 * - Acknowledge/resolve alerts
 * - Alert correlations
 */

import { http, HttpResponse, delay } from 'msw'
import { faker } from '@faker-js/faker'
import { createId } from '../factories/base'

const API_BASE = '/api/v1'

// Types
type AlertSource = 'model' | 'drift' | 'anomaly' | 'validation'
type AlertSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info'
type AlertStatus = 'open' | 'acknowledged' | 'resolved' | 'ignored'

interface UnifiedAlert {
  id: string
  source: AlertSource
  source_id: string
  source_name: string
  severity: AlertSeverity
  status: AlertStatus
  title: string
  message: string
  details: Record<string, unknown>
  acknowledged_at: string | null
  acknowledged_by: string | null
  resolved_at: string | null
  resolved_by: string | null
  related_alert_ids: string[]
  created_at: string
  updated_at: string
}

// Mock data store
const alertsStore: UnifiedAlert[] = []

// Generate sample alerts
function generateSampleAlerts() {
  if (alertsStore.length > 0) return

  const sources: AlertSource[] = ['model', 'drift', 'anomaly', 'validation']
  const severities: AlertSeverity[] = ['critical', 'high', 'medium', 'low', 'info']
  const statuses: AlertStatus[] = ['open', 'open', 'open', 'acknowledged', 'resolved']

  const sourceNames: Record<AlertSource, string[]> = {
    model: ['Recommendation Model', 'Fraud Detection', 'Customer Churn'],
    drift: ['Sales Data Monitor', 'User Events Monitor', 'Product Catalog Monitor'],
    anomaly: ['transactions.csv', 'user_logs.parquet', 'inventory.json'],
    validation: ['orders_table', 'customers_table', 'products_table'],
  }

  const titleTemplates: Record<AlertSource, (name: string) => string> = {
    model: (name) => `Model Alert: ${name} - ${faker.helpers.arrayElement(['latency spike', 'prediction drift', 'accuracy drop'])}`,
    drift: (name) => `Drift Alert: ${faker.number.float({ min: 5, max: 35, fractionDigits: 1 })}% drift detected in ${name}`,
    anomaly: (name) => `High Anomaly Rate: ${faker.number.float({ min: 10, max: 40, fractionDigits: 1 })}% in ${name}`,
    validation: (name) => `Validation Failed: ${faker.number.int({ min: 3, max: 20 })} issues in ${name}`,
  }

  // Generate 20-30 alerts
  const count = faker.number.int({ min: 20, max: 30 })
  for (let i = 0; i < count; i++) {
    const source = faker.helpers.arrayElement(sources)
    const sourceName = faker.helpers.arrayElement(sourceNames[source])
    const severity = faker.helpers.arrayElement(severities)
    const status = faker.helpers.arrayElement(statuses)
    const sourceId = createId()
    const createdAt = faker.date.recent({ days: 7 }).toISOString()

    let acknowledgedAt = null
    let acknowledgedBy = null
    let resolvedAt = null
    let resolvedBy = null

    if (status === 'acknowledged' || status === 'resolved') {
      acknowledgedAt = faker.date.between({ from: createdAt, to: new Date() }).toISOString()
      acknowledgedBy = faker.person.fullName()
    }

    if (status === 'resolved') {
      resolvedAt = faker.date.between({ from: acknowledgedAt || createdAt, to: new Date() }).toISOString()
      resolvedBy = faker.person.fullName()
    }

    alertsStore.push({
      id: `${source}:${sourceId}`,
      source,
      source_id: sourceId,
      source_name: sourceName,
      severity,
      status,
      title: titleTemplates[source](sourceName),
      message: faker.lorem.sentence(),
      details: generateDetails(source),
      acknowledged_at: acknowledgedAt,
      acknowledged_by: acknowledgedBy,
      resolved_at: resolvedAt,
      resolved_by: resolvedBy,
      related_alert_ids: [],
      created_at: createdAt,
      updated_at: createdAt,
    })
  }

  // Sort by created_at descending
  alertsStore.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
}

function generateDetails(source: AlertSource): Record<string, unknown> {
  switch (source) {
    case 'model':
      return {
        rule_id: createId(),
        metric_value: faker.number.float({ min: 0.5, max: 2.0, fractionDigits: 3 }),
        threshold_value: faker.number.float({ min: 0.1, max: 0.5, fractionDigits: 3 }),
      }
    case 'drift':
      return {
        comparison_id: createId(),
        drift_percentage: faker.number.float({ min: 5, max: 50, fractionDigits: 1 }),
        drifted_columns: faker.helpers.arrayElements(
          ['amount', 'quantity', 'price', 'timestamp', 'status'],
          faker.number.int({ min: 1, max: 3 })
        ),
      }
    case 'anomaly':
      return {
        algorithm: faker.helpers.arrayElement(['isolation_forest', 'lof', 'dbscan']),
        anomaly_count: faker.number.int({ min: 50, max: 500 }),
        total_rows: faker.number.int({ min: 1000, max: 10000 }),
        anomaly_rate: faker.number.float({ min: 0.1, max: 0.4, fractionDigits: 2 }),
        columns_analyzed: ['value', 'score', 'count'],
      }
    case 'validation':
      return {
        pass_rate: faker.number.float({ min: 60, max: 95, fractionDigits: 1 }),
        total_issues: faker.number.int({ min: 3, max: 20 }),
        critical_issues: faker.number.int({ min: 0, max: 5 }),
        high_issues: faker.number.int({ min: 1, max: 10 }),
      }
    default:
      return {}
  }
}

// Initialize alerts
generateSampleAlerts()

export const alertsHandlers = [
  // List all alerts
  http.get(`${API_BASE}/alerts`, async ({ request }) => {
    await delay(200)

    const url = new URL(request.url)
    const source = url.searchParams.get('source') as AlertSource | null
    const severity = url.searchParams.get('severity') as AlertSeverity | null
    const status = url.searchParams.get('status') as AlertStatus | null
    const sourceName = url.searchParams.get('source_name')
    const offset = parseInt(url.searchParams.get('offset') ?? '0')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')

    let filtered = [...alertsStore]

    if (source) {
      filtered = filtered.filter(a => a.source === source)
    }
    if (severity) {
      filtered = filtered.filter(a => a.severity === severity)
    }
    if (status) {
      filtered = filtered.filter(a => a.status === status)
    }
    if (sourceName) {
      const search = sourceName.toLowerCase()
      filtered = filtered.filter(a => a.source_name.toLowerCase().includes(search))
    }

    const total = filtered.length
    const paginated = filtered.slice(offset, offset + limit)

    return HttpResponse.json({
      success: true,
      data: {
        items: paginated,
        total,
        offset,
        limit,
      },
    })
  }),

  // Get alert summary
  http.get(`${API_BASE}/alerts/summary`, async () => {
    await delay(150)

    const alerts = alertsStore
    const activeAlerts = alerts.filter(a => a.status !== 'resolved')

    // Count by severity
    const bySeverity = {
      critical: alerts.filter(a => a.severity === 'critical').length,
      high: alerts.filter(a => a.severity === 'high').length,
      medium: alerts.filter(a => a.severity === 'medium').length,
      low: alerts.filter(a => a.severity === 'low').length,
      info: alerts.filter(a => a.severity === 'info').length,
    }

    // Count by source
    const bySource = {
      model: alerts.filter(a => a.source === 'model').length,
      drift: alerts.filter(a => a.source === 'drift').length,
      anomaly: alerts.filter(a => a.source === 'anomaly').length,
      validation: alerts.filter(a => a.source === 'validation').length,
    }

    // Count by status
    const byStatus = {
      open: alerts.filter(a => a.status === 'open').length,
      acknowledged: alerts.filter(a => a.status === 'acknowledged').length,
      resolved: alerts.filter(a => a.status === 'resolved').length,
      ignored: alerts.filter(a => a.status === 'ignored').length,
    }

    // Generate trend data (last 24h, hourly)
    const now = new Date()
    const trend24h = []
    for (let i = 24; i >= 0; i--) {
      const pointTime = new Date(now.getTime() - i * 60 * 60 * 1000)
      const pointStart = new Date(pointTime)
      pointStart.setMinutes(0, 0, 0)
      const pointEnd = new Date(pointStart.getTime() + 60 * 60 * 1000)

      const count = alerts.filter(a => {
        const created = new Date(a.created_at)
        return created >= pointStart && created < pointEnd
      }).length

      trend24h.push({
        timestamp: pointStart.toISOString(),
        count,
      })
    }

    // Top sources
    const sourceCounts: Record<string, number> = {}
    for (const alert of alerts) {
      sourceCounts[alert.source_name] = (sourceCounts[alert.source_name] || 0) + 1
    }
    const topSources = Object.entries(sourceCounts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5)

    return HttpResponse.json({
      success: true,
      data: {
        total_alerts: alerts.length,
        active_alerts: activeAlerts.length,
        by_severity: bySeverity,
        by_source: bySource,
        by_status: byStatus,
        trend_24h: trend24h,
        top_sources: topSources,
      },
    })
  }),

  // Get alert count (for badge)
  http.get(`${API_BASE}/alerts/count`, async ({ request }) => {
    await delay(100)

    const url = new URL(request.url)
    const status = url.searchParams.get('status') as AlertStatus | null

    let count = alertsStore.length
    if (status) {
      count = alertsStore.filter(a => a.status === status).length
    } else {
      // Default: count open alerts
      count = alertsStore.filter(a => a.status === 'open').length
    }

    return HttpResponse.json({
      success: true,
      data: {
        count,
        status_filter: status || 'open',
      },
    })
  }),

  // Get single alert
  http.get(`${API_BASE}/alerts/:alertId`, async ({ params }) => {
    await delay(100)

    const alertId = params.alertId as string
    const alert = alertsStore.find(a => a.id === alertId)

    if (!alert) {
      return HttpResponse.json(
        { detail: 'Alert not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json({
      success: true,
      data: alert,
    })
  }),

  // Acknowledge alert
  http.post(`${API_BASE}/alerts/:alertId/acknowledge`, async ({ params, request }) => {
    await delay(200)

    const alertId = params.alertId as string
    const alert = alertsStore.find(a => a.id === alertId)

    if (!alert) {
      return HttpResponse.json(
        { detail: 'Alert not found' },
        { status: 404 }
      )
    }

    const body = await request.json() as { actor: string; message?: string }

    alert.status = 'acknowledged'
    alert.acknowledged_at = new Date().toISOString()
    alert.acknowledged_by = body.actor
    alert.updated_at = new Date().toISOString()

    return HttpResponse.json({
      success: true,
      data: alert,
    })
  }),

  // Resolve alert
  http.post(`${API_BASE}/alerts/:alertId/resolve`, async ({ params, request }) => {
    await delay(200)

    const alertId = params.alertId as string
    const alert = alertsStore.find(a => a.id === alertId)

    if (!alert) {
      return HttpResponse.json(
        { detail: 'Alert not found' },
        { status: 404 }
      )
    }

    const body = await request.json() as { actor: string; message?: string }

    alert.status = 'resolved'
    alert.resolved_at = new Date().toISOString()
    alert.resolved_by = body.actor
    alert.updated_at = new Date().toISOString()

    return HttpResponse.json({
      success: true,
      data: alert,
    })
  }),

  // Bulk acknowledge
  http.post(`${API_BASE}/alerts/bulk/acknowledge`, async ({ request }) => {
    await delay(300)

    const body = await request.json() as {
      alert_ids: string[]
      actor: string
      message?: string
    }

    let successCount = 0
    const failedIds: string[] = []

    for (const alertId of body.alert_ids) {
      const alert = alertsStore.find(a => a.id === alertId)
      if (alert) {
        alert.status = 'acknowledged'
        alert.acknowledged_at = new Date().toISOString()
        alert.acknowledged_by = body.actor
        alert.updated_at = new Date().toISOString()
        successCount++
      } else {
        failedIds.push(alertId)
      }
    }

    return HttpResponse.json({
      success: true,
      data: {
        success_count: successCount,
        failed_count: failedIds.length,
        failed_ids: failedIds,
      },
    })
  }),

  // Bulk resolve
  http.post(`${API_BASE}/alerts/bulk/resolve`, async ({ request }) => {
    await delay(300)

    const body = await request.json() as {
      alert_ids: string[]
      actor: string
      message?: string
    }

    let successCount = 0
    const failedIds: string[] = []

    for (const alertId of body.alert_ids) {
      const alert = alertsStore.find(a => a.id === alertId)
      if (alert) {
        alert.status = 'resolved'
        alert.resolved_at = new Date().toISOString()
        alert.resolved_by = body.actor
        alert.updated_at = new Date().toISOString()
        successCount++
      } else {
        failedIds.push(alertId)
      }
    }

    return HttpResponse.json({
      success: true,
      data: {
        success_count: successCount,
        failed_count: failedIds.length,
        failed_ids: failedIds,
      },
    })
  }),

  // Get alert correlations
  http.get(`${API_BASE}/alerts/:alertId/correlations`, async ({ params }) => {
    await delay(200)

    const alertId = params.alertId as string
    const alert = alertsStore.find(a => a.id === alertId)

    if (!alert) {
      return HttpResponse.json(
        { detail: 'Alert not found' },
        { status: 404 }
      )
    }

    // Find related alerts (same source_name or within 1 hour)
    const alertTime = new Date(alert.created_at).getTime()
    const oneHour = 60 * 60 * 1000

    const sameSourceAlerts = alertsStore
      .filter(a => a.id !== alertId && a.source_name === alert.source_name)
      .slice(0, 5)

    const temporalAlerts = alertsStore
      .filter(a => {
        if (a.id === alertId) return false
        if (a.source_name === alert.source_name) return false
        const aTime = new Date(a.created_at).getTime()
        return Math.abs(aTime - alertTime) <= oneHour && a.severity === alert.severity
      })
      .slice(0, 5)

    const correlations = []

    if (sameSourceAlerts.length > 0) {
      correlations.push({
        alert_id: alertId,
        related_alerts: sameSourceAlerts,
        correlation_type: 'same_source',
        correlation_score: 0.9,
        common_factors: [`Same source: ${alert.source_name}`],
      })
    }

    if (temporalAlerts.length > 0) {
      correlations.push({
        alert_id: alertId,
        related_alerts: temporalAlerts,
        correlation_type: 'temporal_severity',
        correlation_score: 0.6,
        common_factors: [`Same severity: ${alert.severity}`, 'Within 1h window'],
      })
    }

    return HttpResponse.json({
      success: true,
      data: {
        correlations,
        total_correlated: sameSourceAlerts.length + temporalAlerts.length,
      },
    })
  }),
]
