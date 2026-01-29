/**
 * Factory for generating mock model monitoring data.
 *
 * Provides realistic ML model monitoring data including:
 * - Registered models with status and metrics
 * - Alert rules and handlers
 * - Alert instances
 * - Performance metrics time series
 */

import { faker } from '@faker-js/faker'
import { createId, createTimestamp, randomChoice } from './base'

// ============================================================================
// Types
// ============================================================================

export interface RegisteredModel {
  id: string
  name: string
  version: string
  description: string
  status: 'active' | 'paused' | 'degraded' | 'error'
  config: {
    enable_drift_detection: boolean
    enable_quality_metrics: boolean
    enable_performance_metrics: boolean
    sample_rate: number
    drift_threshold: number
    drift_window_size: number
  }
  metadata: Record<string, string>
  prediction_count: number
  last_prediction_at: string | null
  current_drift_score: number | null
  health_score: number
  created_at: string
  updated_at: string
}

export interface AlertRule {
  id: string
  name: string
  model_id: string
  rule_type: 'threshold' | 'statistical' | 'trend'
  severity: 'critical' | 'warning' | 'info'
  config: {
    metric_name?: string
    threshold?: number
    comparison?: 'gt' | 'lt' | 'gte' | 'lte' | 'eq'
    duration_seconds?: number
    std_deviations?: number
    trend_direction?: 'up' | 'down'
    trend_period_hours?: number
  }
  is_active: boolean
  last_triggered_at: string | null
  trigger_count: number
  created_at: string
  updated_at: string
}

export interface AlertHandler {
  id: string
  name: string
  handler_type: 'slack' | 'webhook' | 'email'
  config: {
    webhook_url?: string
    channel?: string
    username?: string
    url?: string
    method?: string
    headers?: Record<string, string>
    recipients?: string[]
    from_address?: string
    subject_template?: string
  }
  is_active: boolean
  send_count: number
  failure_count: number
  last_sent_at: string | null
  last_error: string | null
  created_at: string
  updated_at: string
}

export interface AlertInstance {
  id: string
  rule_id: string
  model_id: string
  model_name: string
  severity: 'critical' | 'warning' | 'info'
  message: string
  metric_value: number | null
  threshold_value: number | null
  acknowledged: boolean
  acknowledged_by: string | null
  acknowledged_at: string | null
  resolved: boolean
  resolved_at: string | null
  created_at: string
  updated_at: string
}

export interface MetricDataPoint {
  timestamp: string
  value: number
}

export interface MetricSummary {
  name: string
  type: string
  count: number
  min_value: number | null
  max_value: number | null
  avg_value: number | null
  p50_value: number | null
  p95_value: number | null
  p99_value: number | null
  last_value: number | null
}

// ============================================================================
// Model Names
// ============================================================================

const MODEL_NAMES = [
  'fraud-detection',
  'churn-prediction',
  'recommendation-engine',
  'sentiment-analyzer',
  'price-predictor',
  'image-classifier',
  'text-generator',
  'anomaly-detector',
  'risk-scorer',
  'demand-forecaster',
]

// ============================================================================
// Factory Functions
// ============================================================================

export function createTimestamps() {
  const created = createTimestamp(faker.number.int({ min: 1, max: 90 }))
  return {
    created_at: created,
    updated_at: faker.date.between({ from: created, to: new Date() }).toISOString(),
  }
}

export function createRegisteredModel(overrides: Partial<RegisteredModel> = {}): RegisteredModel {
  const timestamps = createTimestamps()
  const status = randomChoice(['active', 'active', 'active', 'paused', 'degraded'] as const)
  const healthScore =
    status === 'active'
      ? faker.number.float({ min: 70, max: 100, fractionDigits: 1 })
      : status === 'degraded'
        ? faker.number.float({ min: 40, max: 69, fractionDigits: 1 })
        : faker.number.float({ min: 50, max: 90, fractionDigits: 1 })

  return {
    id: createId(),
    name: randomChoice(MODEL_NAMES),
    version: `${faker.number.int({ min: 1, max: 3 })}.${faker.number.int({ min: 0, max: 9 })}.${faker.number.int({ min: 0, max: 9 })}`,
    description: faker.lorem.sentence(),
    status,
    config: {
      enable_drift_detection: true,
      enable_quality_metrics: true,
      enable_performance_metrics: true,
      sample_rate: faker.helpers.arrayElement([0.1, 0.25, 0.5, 1.0]),
      drift_threshold: faker.helpers.arrayElement([0.05, 0.1, 0.15]),
      drift_window_size: faker.helpers.arrayElement([500, 1000, 2000, 5000]),
    },
    metadata: {
      team: faker.helpers.arrayElement(['ml-platform', 'data-science', 'analytics']),
      owner: faker.person.fullName(),
    },
    prediction_count: faker.number.int({ min: 1000, max: 5000000 }),
    last_prediction_at: faker.date.recent({ days: 1 }).toISOString(),
    current_drift_score: faker.helpers.maybe(
      () => faker.number.float({ min: 0, max: 0.3, fractionDigits: 3 }),
      { probability: 0.8 }
    ) ?? null,
    health_score: healthScore,
    ...timestamps,
    ...overrides,
  }
}

export function createAlertRule(
  modelId: string,
  overrides: Partial<AlertRule> = {}
): AlertRule {
  const timestamps = createTimestamps()
  const ruleType = randomChoice(['threshold', 'statistical', 'trend'] as const)
  const severity = randomChoice(['critical', 'warning', 'info'] as const)

  let config: AlertRule['config'] = {}
  if (ruleType === 'threshold') {
    config = {
      metric_name: randomChoice(['latency_ms', 'error_rate', 'null_rate', 'drift_score']),
      threshold: faker.number.float({ min: 50, max: 500, fractionDigits: 1 }),
      comparison: randomChoice(['gt', 'lt', 'gte', 'lte'] as const),
      duration_seconds: faker.helpers.arrayElement([60, 300, 600]),
    }
  } else if (ruleType === 'statistical') {
    config = {
      metric_name: randomChoice(['latency_ms', 'throughput']),
      std_deviations: faker.helpers.arrayElement([2, 3, 4]),
    }
  } else {
    config = {
      metric_name: randomChoice(['latency_ms', 'error_rate']),
      trend_direction: randomChoice(['up', 'down'] as const),
      trend_period_hours: faker.helpers.arrayElement([1, 6, 24]),
    }
  }

  const triggerCount = faker.number.int({ min: 0, max: 50 })

  return {
    id: createId(),
    name: `${severity === 'critical' ? 'Critical' : severity === 'warning' ? 'Warning' : 'Info'} ${config.metric_name} Alert`,
    model_id: modelId,
    rule_type: ruleType,
    severity,
    config,
    is_active: faker.datatype.boolean({ probability: 0.8 }),
    last_triggered_at:
      triggerCount > 0 ? faker.date.recent({ days: 7 }).toISOString() : null,
    trigger_count: triggerCount,
    ...timestamps,
    ...overrides,
  }
}

export function createAlertHandler(overrides: Partial<AlertHandler> = {}): AlertHandler {
  const timestamps = createTimestamps()
  const handlerType = randomChoice(['slack', 'webhook', 'email'] as const)

  let config: AlertHandler['config'] = {}
  if (handlerType === 'slack') {
    config = {
      webhook_url: `https://hooks.slack.com/services/${faker.string.alphanumeric(9)}/${faker.string.alphanumeric(11)}/${faker.string.alphanumeric(24)}`,
      channel: `#${randomChoice(['alerts', 'ml-monitoring', 'ops', 'data-quality'])}`,
      username: 'Truthound Bot',
    }
  } else if (handlerType === 'webhook') {
    config = {
      url: `https://${faker.internet.domainName()}/webhook/alerts`,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${faker.string.alphanumeric(32)}`,
      },
    }
  } else {
    config = {
      recipients: [faker.internet.email(), faker.internet.email()],
      from_address: `alerts@${faker.internet.domainName()}`,
      subject_template: '[{{severity}}] Model {{model_name}}: {{alert_name}}',
    }
  }

  const sendCount = faker.number.int({ min: 0, max: 200 })
  const failureCount = faker.number.int({ min: 0, max: Math.floor(sendCount * 0.1) })

  return {
    id: createId(),
    name: `${handlerType.charAt(0).toUpperCase() + handlerType.slice(1)} Handler - ${faker.company.buzzNoun()}`,
    handler_type: handlerType,
    config,
    is_active: faker.datatype.boolean({ probability: 0.85 }),
    send_count: sendCount,
    failure_count: failureCount,
    last_sent_at: sendCount > 0 ? faker.date.recent({ days: 3 }).toISOString() : null,
    last_error: failureCount > 0 && faker.datatype.boolean({ probability: 0.3 })
      ? 'Connection timeout'
      : null,
    ...timestamps,
    ...overrides,
  }
}

export function createAlertInstance(
  ruleId: string,
  modelId: string,
  modelName: string,
  overrides: Partial<AlertInstance> = {}
): AlertInstance {
  const timestamps = createTimestamps()
  const severity = randomChoice(['critical', 'warning', 'info'] as const)
  const acknowledged = faker.datatype.boolean({ probability: 0.6 })
  const resolved = acknowledged && faker.datatype.boolean({ probability: 0.5 })

  return {
    id: createId(),
    rule_id: ruleId,
    model_id: modelId,
    model_name: modelName,
    severity,
    message: faker.helpers.arrayElement([
      `Latency exceeded threshold: ${faker.number.float({ min: 100, max: 500, fractionDigits: 1 })}ms > 100ms`,
      `Drift detected: score ${faker.number.float({ min: 0.1, max: 0.4, fractionDigits: 2 })} > 0.1`,
      `Error rate spike: ${faker.number.float({ min: 5, max: 20, fractionDigits: 1 })}%`,
      `Null rate increased: ${faker.number.float({ min: 2, max: 10, fractionDigits: 1 })}%`,
      `Throughput dropped by ${faker.number.int({ min: 20, max: 50 })}%`,
    ]),
    metric_value: faker.number.float({ min: 50, max: 500, fractionDigits: 2 }),
    threshold_value: faker.number.float({ min: 50, max: 100, fractionDigits: 2 }),
    acknowledged,
    acknowledged_by: acknowledged ? faker.person.firstName() : null,
    acknowledged_at: acknowledged
      ? faker.date.between({ from: timestamps.created_at, to: new Date() }).toISOString()
      : null,
    resolved,
    resolved_at: resolved ? faker.date.recent({ days: 1 }).toISOString() : null,
    ...timestamps,
    ...overrides,
  }
}

export function createMetricDataPoints(
  metricName: string,
  hours: number = 24
): MetricDataPoint[] {
  const points: MetricDataPoint[] = []
  const now = new Date()
  const interval = 30 // 30 minutes
  const numPoints = Math.min((hours * 60) / interval, 100)

  let baseValue: number
  let variance: number

  switch (metricName) {
    case 'latency_ms':
      baseValue = faker.number.float({ min: 30, max: 60 })
      variance = 20
      break
    case 'throughput':
      baseValue = faker.number.float({ min: 100, max: 300 })
      variance = 50
      break
    case 'error_rate':
      baseValue = faker.number.float({ min: 0.5, max: 2 })
      variance = 1
      break
    default:
      baseValue = 50
      variance = 10
  }

  for (let i = numPoints - 1; i >= 0; i--) {
    const timestamp = new Date(now.getTime() - i * interval * 60 * 1000)
    // Add some sinusoidal pattern for realistic data
    const sinComponent = Math.sin((i / numPoints) * Math.PI * 4) * variance * 0.3
    const randomComponent = (Math.random() - 0.5) * variance
    const value = Math.max(0, baseValue + sinComponent + randomComponent)

    points.push({
      timestamp: timestamp.toISOString(),
      value: parseFloat(value.toFixed(2)),
    })
  }

  return points
}

export function createMetricSummary(dataPoints: MetricDataPoint[]): MetricSummary {
  if (dataPoints.length === 0) {
    return {
      name: '',
      type: '',
      count: 0,
      min_value: null,
      max_value: null,
      avg_value: null,
      p50_value: null,
      p95_value: null,
      p99_value: null,
      last_value: null,
    }
  }

  const values = dataPoints.map((p) => p.value)
  const sorted = [...values].sort((a, b) => a - b)
  const n = sorted.length

  return {
    name: '',
    type: '',
    count: n,
    min_value: sorted[0],
    max_value: sorted[n - 1],
    avg_value: values.reduce((a, b) => a + b, 0) / n,
    p50_value: sorted[Math.floor(n * 0.5)],
    p95_value: sorted[Math.floor(n * 0.95)],
    p99_value: sorted[Math.floor(n * 0.99)],
    last_value: values[n - 1],
  }
}

// ============================================================================
// Batch Creation
// ============================================================================

export function createDiverseModels(count: number = 5): RegisteredModel[] {
  const usedNames = new Set<string>()
  const models: RegisteredModel[] = []

  for (let i = 0; i < count; i++) {
    let name: string
    do {
      name = randomChoice(MODEL_NAMES)
    } while (usedNames.has(name) && usedNames.size < MODEL_NAMES.length)
    usedNames.add(name)

    models.push(createRegisteredModel({ name }))
  }

  return models
}

export function createDiverseAlertRules(modelIds: string[]): AlertRule[] {
  const rules: AlertRule[] = []

  modelIds.forEach((modelId) => {
    // Create 2-4 rules per model
    const ruleCount = faker.number.int({ min: 2, max: 4 })
    for (let i = 0; i < ruleCount; i++) {
      rules.push(createAlertRule(modelId))
    }
  })

  return rules
}

export function createDiverseAlertHandlers(count: number = 4): AlertHandler[] {
  const handlers: AlertHandler[] = []
  const types: Array<'slack' | 'webhook' | 'email'> = ['slack', 'webhook', 'email']

  // Ensure at least one of each type
  types.forEach((type) => {
    handlers.push(
      createAlertHandler({
        handler_type: type,
        name: `Primary ${type.charAt(0).toUpperCase() + type.slice(1)} Handler`,
      })
    )
  })

  // Add extra handlers
  for (let i = handlers.length; i < count; i++) {
    handlers.push(createAlertHandler())
  }

  return handlers
}

export function createDiverseAlertInstances(
  rules: AlertRule[],
  models: RegisteredModel[],
  count: number = 10
): AlertInstance[] {
  const alerts: AlertInstance[] = []
  const modelMap = new Map(models.map((m) => [m.id, m]))

  for (let i = 0; i < count; i++) {
    const rule = randomChoice(rules)
    const model = modelMap.get(rule.model_id)
    if (model) {
      alerts.push(createAlertInstance(rule.id, model.id, model.name))
    }
  }

  return alerts
}
