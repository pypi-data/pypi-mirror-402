/**
 * Model Monitoring API mock handlers.
 *
 * Provides complete CRUD operations for ML model monitoring including:
 * - Registered models management
 * - Model metrics and dashboards
 * - Alert rules and handlers
 * - Alert instances
 */

import { http, HttpResponse, delay } from 'msw'
import { faker } from '@faker-js/faker'
import { getStore } from '../data/store'
import {
  createRegisteredModel,
  createAlertRule,
  createAlertHandler,
  createMetricDataPoints,
  createMetricSummary,
  createDiverseModels,
  createDiverseAlertRules,
  createDiverseAlertHandlers,
  createDiverseAlertInstances,
  type RegisteredModel,
  type AlertRule,
  type AlertHandler,
  type AlertInstance,
} from '../factories'

const API_BASE = '/api/v1'

// ============================================================================
// Store Extension
// ============================================================================

interface ModelMonitoringStore {
  mlModels: RegisteredModel[]
  mlAlertRules: AlertRule[]
  mlAlertHandlers: AlertHandler[]
  mlAlerts: AlertInstance[]
  mlPredictions: Array<{ model_id: string; timestamp: string; data: unknown }>
}

function getModelMonitoringStore(): ModelMonitoringStore {
  const store = getStore() as unknown as { modelMonitoring?: ModelMonitoringStore }

  if (!store.modelMonitoring) {
    // Initialize with sample data
    const models = createDiverseModels(5)
    const rules = createDiverseAlertRules(models.map((m) => m.id))
    const handlers = createDiverseAlertHandlers(4)
    const alerts = createDiverseAlertInstances(rules, models, 8)

    store.modelMonitoring = {
      mlModels: models,
      mlAlertRules: rules,
      mlAlertHandlers: handlers,
      mlAlerts: alerts,
      mlPredictions: [],
    }
  }

  return store.modelMonitoring
}

// ============================================================================
// Overview Endpoint
// ============================================================================

export const modelMonitoringHandlers = [
  // Get overview statistics
  http.get(`${API_BASE}/model-monitoring/overview`, async () => {
    await delay(200)
    const store = getModelMonitoringStore()

    const activeModels = store.mlModels.filter((m) => m.status === 'active').length
    const degradedModels = store.mlModels.filter((m) => m.status === 'degraded').length
    const activeAlerts = store.mlAlerts.filter((a) => !a.resolved).length
    const modelsWithDrift = store.mlModels.filter((m) => (m.current_drift_score ?? 0) > 0.1).length

    // Calculate average latency from a random range
    const avgLatency = faker.number.float({ min: 30, max: 80, fractionDigits: 1 })

    return HttpResponse.json({
      data: {
        total_models: store.mlModels.length,
        active_models: activeModels,
        degraded_models: degradedModels,
        total_predictions_24h: faker.number.int({ min: 10000, max: 500000 }),
        active_alerts: activeAlerts,
        models_with_drift: modelsWithDrift,
        avg_latency_ms: avgLatency,
      },
    })
  }),

  // ============================================================================
  // Models CRUD
  // ============================================================================

  // List models
  http.get(`${API_BASE}/model-monitoring/models`, async ({ request }) => {
    await delay(200)
    const store = getModelMonitoringStore()

    const url = new URL(request.url)
    const offset = parseInt(url.searchParams.get('offset') ?? '0')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')
    const status = url.searchParams.get('status')

    let models = [...store.mlModels]

    if (status) {
      models = models.filter((m) => m.status === status)
    }

    // Sort by created_at descending
    models.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )

    const total = models.length
    const paginated = models.slice(offset, offset + limit)

    return HttpResponse.json({
      data: {
        items: paginated,
        total,
        offset,
        limit,
      },
    })
  }),

  // Get model by ID
  http.get(`${API_BASE}/model-monitoring/models/:id`, async ({ params }) => {
    await delay(150)
    const store = getModelMonitoringStore()

    const model = store.mlModels.find((m) => m.id === params.id)

    if (!model) {
      return HttpResponse.json({ detail: 'Model not found' }, { status: 404 })
    }

    return HttpResponse.json({ data: model })
  }),

  // Create model
  http.post(`${API_BASE}/model-monitoring/models`, async ({ request }) => {
    await delay(300)
    const store = getModelMonitoringStore()

    const body = (await request.json()) as Partial<RegisteredModel>
    const model = createRegisteredModel({
      name: body.name,
      version: body.version,
      description: body.description,
      config: body.config,
      metadata: body.metadata,
      prediction_count: 0,
      last_prediction_at: null,
      current_drift_score: null,
      health_score: 100,
      status: 'active',
    })

    store.mlModels.push(model)

    // Create default alert rules for the model
    const defaultRules: AlertRule[] = [
      createAlertRule(model.id, {
        name: 'High Latency Alert',
        rule_type: 'threshold',
        severity: 'warning',
        config: {
          metric_name: 'latency_ms',
          threshold: 100,
          comparison: 'gt',
          duration_seconds: 300,
        },
      }),
      createAlertRule(model.id, {
        name: 'Drift Detection Alert',
        rule_type: 'threshold',
        severity: 'warning',
        config: {
          metric_name: 'drift_score',
          threshold: model.config?.drift_threshold || 0.1,
          comparison: 'gt',
        },
      }),
    ]
    store.mlAlertRules.push(...defaultRules)

    return HttpResponse.json({ data: model })
  }),

  // Update model
  http.put(`${API_BASE}/model-monitoring/models/:id`, async ({ params, request }) => {
    await delay(200)
    const store = getModelMonitoringStore()

    const body = (await request.json()) as Partial<RegisteredModel>
    const index = store.mlModels.findIndex((m) => m.id === params.id)

    if (index === -1) {
      return HttpResponse.json({ detail: 'Model not found' }, { status: 404 })
    }

    const updatedModel = {
      ...store.mlModels[index],
      ...body,
      updated_at: new Date().toISOString(),
    }
    store.mlModels[index] = updatedModel

    return HttpResponse.json({ data: updatedModel })
  }),

  // Delete model
  http.delete(`${API_BASE}/model-monitoring/models/:id`, async ({ params }) => {
    await delay(200)
    const store = getModelMonitoringStore()

    const index = store.mlModels.findIndex((m) => m.id === params.id)

    if (index === -1) {
      return HttpResponse.json({ detail: 'Model not found' }, { status: 404 })
    }

    const modelId = store.mlModels[index].id
    store.mlModels.splice(index, 1)

    // Clean up related data
    store.mlAlertRules = store.mlAlertRules.filter((r) => r.model_id !== modelId)
    store.mlAlerts = store.mlAlerts.filter((a) => a.model_id !== modelId)

    return HttpResponse.json({ success: true, message: 'Model deleted' })
  }),

  // ============================================================================
  // Model Metrics
  // ============================================================================

  // Get model metrics
  http.get(`${API_BASE}/model-monitoring/models/:id/metrics`, async ({ params, request }) => {
    await delay(250)
    const store = getModelMonitoringStore()

    const url = new URL(request.url)
    const hours = parseInt(url.searchParams.get('hours') ?? '24')

    const model = store.mlModels.find((m) => m.id === params.id)

    if (!model) {
      return HttpResponse.json({ detail: 'Model not found' }, { status: 404 })
    }

    // Generate metrics data
    const latencyPoints = createMetricDataPoints('latency_ms', hours)
    const throughputPoints = createMetricDataPoints('throughput', hours)

    const latencySummary = createMetricSummary(latencyPoints)
    latencySummary.name = 'latency_ms'
    latencySummary.type = 'latency'

    const throughputSummary = createMetricSummary(throughputPoints)
    throughputSummary.name = 'throughput'
    throughputSummary.type = 'throughput'

    return HttpResponse.json({
      data: {
        model_id: params.id,
        model_name: model.name,
        time_range_hours: hours,
        metrics: [latencySummary, throughputSummary],
        data_points: {
          latency_ms: latencyPoints,
          throughput: throughputPoints,
        },
      },
    })
  }),

  // Get model dashboard data
  http.get(`${API_BASE}/model-monitoring/models/:id/dashboard`, async ({ params, request }) => {
    await delay(300)
    const store = getModelMonitoringStore()

    const url = new URL(request.url)
    const hours = parseInt(url.searchParams.get('hours') ?? '24')

    const model = store.mlModels.find((m) => m.id === params.id)

    if (!model) {
      return HttpResponse.json({ detail: 'Model not found' }, { status: 404 })
    }

    // Generate metrics data
    const latencyPoints = createMetricDataPoints('latency_ms', hours)
    const throughputPoints = createMetricDataPoints('throughput', hours)

    const latencySummary = createMetricSummary(latencyPoints)
    latencySummary.name = 'latency_ms'
    latencySummary.type = 'latency'

    const throughputSummary = createMetricSummary(throughputPoints)
    throughputSummary.name = 'throughput'
    throughputSummary.type = 'throughput'

    // Get recent alerts for this model
    const recentAlerts = store.mlAlerts
      .filter((a) => a.model_id === params.id)
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, 5)

    return HttpResponse.json({
      data: {
        model_id: params.id,
        model_name: model.name,
        time_range_hours: hours,
        metrics: [latencySummary, throughputSummary],
        data_points: {
          latency_ms: latencyPoints,
          throughput: throughputPoints,
        },
        health_breakdown: {
          latency_score: faker.number.float({ min: 70, max: 100, fractionDigits: 1 }),
          error_rate_score: faker.number.float({ min: 80, max: 100, fractionDigits: 1 }),
          drift_score: faker.number.float({ min: 60, max: 100, fractionDigits: 1 }),
          throughput_score: faker.number.float({ min: 75, max: 100, fractionDigits: 1 }),
        },
        recent_alerts: recentAlerts.map((a) => ({
          id: a.id,
          severity: a.severity,
          message: a.message,
          created_at: a.created_at,
        })),
      },
    })
  }),

  // Log prediction (for monitoring)
  http.post(`${API_BASE}/model-monitoring/models/:id/predictions`, async ({ params, request }) => {
    await delay(50)
    const store = getModelMonitoringStore()

    const model = store.mlModels.find((m) => m.id === params.id)

    if (!model) {
      return HttpResponse.json({ detail: 'Model not found' }, { status: 404 })
    }

    const body = await request.json()

    // Update model stats
    model.prediction_count += 1
    model.last_prediction_at = new Date().toISOString()
    model.updated_at = new Date().toISOString()

    // Store prediction (limited to last 1000)
    store.mlPredictions.push({
      model_id: model.id,
      timestamp: new Date().toISOString(),
      data: body,
    })
    if (store.mlPredictions.length > 1000) {
      store.mlPredictions = store.mlPredictions.slice(-1000)
    }

    return HttpResponse.json({ success: true })
  }),

  // ============================================================================
  // Alert Rules CRUD
  // ============================================================================

  // List alert rules
  http.get(`${API_BASE}/model-monitoring/rules`, async ({ request }) => {
    await delay(200)
    const store = getModelMonitoringStore()

    const url = new URL(request.url)
    const offset = parseInt(url.searchParams.get('offset') ?? '0')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')
    const modelId = url.searchParams.get('model_id')

    let rules = [...store.mlAlertRules]

    if (modelId) {
      rules = rules.filter((r) => r.model_id === modelId)
    }

    const total = rules.length
    const paginated = rules.slice(offset, offset + limit)

    return HttpResponse.json({
      data: {
        items: paginated,
        total,
        offset,
        limit,
      },
    })
  }),

  // Get alert rule by ID
  http.get(`${API_BASE}/model-monitoring/rules/:id`, async ({ params }) => {
    await delay(150)
    const store = getModelMonitoringStore()

    const rule = store.mlAlertRules.find((r) => r.id === params.id)

    if (!rule) {
      return HttpResponse.json({ detail: 'Rule not found' }, { status: 404 })
    }

    return HttpResponse.json({ data: rule })
  }),

  // Create alert rule
  http.post(`${API_BASE}/model-monitoring/rules`, async ({ request }) => {
    await delay(300)
    const store = getModelMonitoringStore()

    const body = (await request.json()) as Partial<AlertRule>

    if (!body.model_id) {
      return HttpResponse.json({ detail: 'model_id is required' }, { status: 400 })
    }

    const rule = createAlertRule(body.model_id, {
      name: body.name,
      rule_type: body.rule_type,
      severity: body.severity,
      config: body.config,
      is_active: body.is_active !== false,
    })

    store.mlAlertRules.push(rule)

    return HttpResponse.json({ data: rule })
  }),

  // Update alert rule
  http.put(`${API_BASE}/model-monitoring/rules/:id`, async ({ params, request }) => {
    await delay(200)
    const store = getModelMonitoringStore()

    const body = (await request.json()) as Partial<AlertRule>
    const index = store.mlAlertRules.findIndex((r) => r.id === params.id)

    if (index === -1) {
      return HttpResponse.json({ detail: 'Rule not found' }, { status: 404 })
    }

    const updatedRule = {
      ...store.mlAlertRules[index],
      ...body,
      updated_at: new Date().toISOString(),
    }
    store.mlAlertRules[index] = updatedRule

    return HttpResponse.json({ data: updatedRule })
  }),

  // Delete alert rule
  http.delete(`${API_BASE}/model-monitoring/rules/:id`, async ({ params }) => {
    await delay(200)
    const store = getModelMonitoringStore()

    const index = store.mlAlertRules.findIndex((r) => r.id === params.id)

    if (index === -1) {
      return HttpResponse.json({ detail: 'Rule not found' }, { status: 404 })
    }

    store.mlAlertRules.splice(index, 1)

    return HttpResponse.json({ success: true, message: 'Rule deleted' })
  }),

  // ============================================================================
  // Alert Handlers CRUD
  // ============================================================================

  // List alert handlers
  http.get(`${API_BASE}/model-monitoring/handlers`, async ({ request }) => {
    await delay(200)
    const store = getModelMonitoringStore()

    const url = new URL(request.url)
    const offset = parseInt(url.searchParams.get('offset') ?? '0')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')
    const handlerType = url.searchParams.get('handler_type')

    let handlers = [...store.mlAlertHandlers]

    if (handlerType) {
      handlers = handlers.filter((h) => h.handler_type === handlerType)
    }

    const total = handlers.length
    const paginated = handlers.slice(offset, offset + limit)

    return HttpResponse.json({
      data: {
        items: paginated,
        total,
        offset,
        limit,
      },
    })
  }),

  // Get alert handler by ID
  http.get(`${API_BASE}/model-monitoring/handlers/:id`, async ({ params }) => {
    await delay(150)
    const store = getModelMonitoringStore()

    const handler = store.mlAlertHandlers.find((h) => h.id === params.id)

    if (!handler) {
      return HttpResponse.json({ detail: 'Handler not found' }, { status: 404 })
    }

    return HttpResponse.json({ data: handler })
  }),

  // Create alert handler
  http.post(`${API_BASE}/model-monitoring/handlers`, async ({ request }) => {
    await delay(300)
    const store = getModelMonitoringStore()

    const body = (await request.json()) as Partial<AlertHandler>

    const handler = createAlertHandler({
      name: body.name,
      handler_type: body.handler_type,
      config: body.config,
      is_active: body.is_active !== false,
    })

    store.mlAlertHandlers.push(handler)

    return HttpResponse.json({ data: handler })
  }),

  // Update alert handler
  http.put(`${API_BASE}/model-monitoring/handlers/:id`, async ({ params, request }) => {
    await delay(200)
    const store = getModelMonitoringStore()

    const body = (await request.json()) as Partial<AlertHandler>
    const index = store.mlAlertHandlers.findIndex((h) => h.id === params.id)

    if (index === -1) {
      return HttpResponse.json({ detail: 'Handler not found' }, { status: 404 })
    }

    const updatedHandler = {
      ...store.mlAlertHandlers[index],
      ...body,
      updated_at: new Date().toISOString(),
    }
    store.mlAlertHandlers[index] = updatedHandler

    return HttpResponse.json({ data: updatedHandler })
  }),

  // Delete alert handler
  http.delete(`${API_BASE}/model-monitoring/handlers/:id`, async ({ params }) => {
    await delay(200)
    const store = getModelMonitoringStore()

    const index = store.mlAlertHandlers.findIndex((h) => h.id === params.id)

    if (index === -1) {
      return HttpResponse.json({ detail: 'Handler not found' }, { status: 404 })
    }

    store.mlAlertHandlers.splice(index, 1)

    return HttpResponse.json({ success: true, message: 'Handler deleted' })
  }),

  // Test alert handler
  http.post(`${API_BASE}/model-monitoring/handlers/:id/test`, async ({ params }) => {
    await delay(500)
    const store = getModelMonitoringStore()

    const handler = store.mlAlertHandlers.find((h) => h.id === params.id)

    if (!handler) {
      return HttpResponse.json({ detail: 'Handler not found' }, { status: 404 })
    }

    // Simulate test send with 90% success rate
    const success = Math.random() > 0.1

    if (success) {
      handler.send_count += 1
      handler.last_sent_at = new Date().toISOString()
      handler.last_error = null
    } else {
      handler.failure_count += 1
      handler.last_error = 'Test failed: Connection refused'
    }

    handler.updated_at = new Date().toISOString()

    return HttpResponse.json({
      data: {
        success,
        message: success ? 'Test message sent successfully' : 'Test failed',
        handler,
      },
    })
  }),

  // ============================================================================
  // Alerts CRUD
  // ============================================================================

  // List alerts
  http.get(`${API_BASE}/model-monitoring/alerts`, async ({ request }) => {
    await delay(200)
    const store = getModelMonitoringStore()

    const url = new URL(request.url)
    const activeOnly = url.searchParams.get('active_only') === 'true'
    const offset = parseInt(url.searchParams.get('offset') ?? '0')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')
    const modelId = url.searchParams.get('model_id')
    const severity = url.searchParams.get('severity')

    let alerts = [...store.mlAlerts]

    if (activeOnly) {
      alerts = alerts.filter((a) => !a.resolved)
    }

    if (modelId) {
      alerts = alerts.filter((a) => a.model_id === modelId)
    }

    if (severity) {
      alerts = alerts.filter((a) => a.severity === severity)
    }

    // Sort by created_at descending
    alerts.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )

    const total = alerts.length
    const paginated = alerts.slice(offset, offset + limit)

    return HttpResponse.json({
      data: {
        items: paginated,
        total,
        offset,
        limit,
      },
    })
  }),

  // Get alert by ID
  http.get(`${API_BASE}/model-monitoring/alerts/:id`, async ({ params }) => {
    await delay(150)
    const store = getModelMonitoringStore()

    const alert = store.mlAlerts.find((a) => a.id === params.id)

    if (!alert) {
      return HttpResponse.json({ detail: 'Alert not found' }, { status: 404 })
    }

    return HttpResponse.json({ data: alert })
  }),

  // Acknowledge alert
  http.post(`${API_BASE}/model-monitoring/alerts/:id/acknowledge`, async ({ params, request }) => {
    await delay(200)
    const store = getModelMonitoringStore()

    const body = (await request.json()) as { actor: string }
    const alert = store.mlAlerts.find((a) => a.id === params.id)

    if (!alert) {
      return HttpResponse.json({ detail: 'Alert not found' }, { status: 404 })
    }

    alert.acknowledged = true
    alert.acknowledged_by = body.actor || 'user'
    alert.acknowledged_at = new Date().toISOString()
    alert.updated_at = new Date().toISOString()

    return HttpResponse.json({ data: alert })
  }),

  // Resolve alert
  http.post(`${API_BASE}/model-monitoring/alerts/:id/resolve`, async ({ params }) => {
    await delay(200)
    const store = getModelMonitoringStore()

    const alert = store.mlAlerts.find((a) => a.id === params.id)

    if (!alert) {
      return HttpResponse.json({ detail: 'Alert not found' }, { status: 404 })
    }

    alert.resolved = true
    alert.resolved_at = new Date().toISOString()
    alert.updated_at = new Date().toISOString()

    return HttpResponse.json({ data: alert })
  }),
]
