/**
 * Schedule factory - generates scheduled job mock data
 * Extended for comprehensive test coverage
 */

import type { Schedule } from '@/api/client'
import { createId, createTimestamp, randomChoice, randomInt, faker } from './base'

export type TriggerType =
  | 'cron'
  | 'interval'
  | 'data_change'
  | 'composite'
  | 'event'
  | 'manual'

export interface ScheduleFactoryOptions {
  id?: string
  sourceId?: string
  sourceName?: string
  name?: string
  isActive?: boolean
  hasRun?: boolean
  cronExpression?: string
  triggerType?: TriggerType
  triggerConfig?: Record<string, unknown>
  notifyOnFailure?: boolean
  validators?: string[]
  autoSchema?: boolean
}

// Comprehensive cron expressions for various scheduling patterns
const CRON_EXPRESSIONS = [
  // Minute-level
  { expr: '*/5 * * * *', desc: 'Every 5 minutes' },
  { expr: '*/15 * * * *', desc: 'Every 15 minutes' },
  { expr: '*/30 * * * *', desc: 'Every 30 minutes' },
  // Hourly
  { expr: '0 * * * *', desc: 'Every hour' },
  { expr: '0 */2 * * *', desc: 'Every 2 hours' },
  { expr: '0 */4 * * *', desc: 'Every 4 hours' },
  { expr: '0 */6 * * *', desc: 'Every 6 hours' },
  { expr: '0 */12 * * *', desc: 'Every 12 hours' },
  // Daily
  { expr: '0 0 * * *', desc: 'Daily at midnight' },
  { expr: '0 6 * * *', desc: 'Daily at 6 AM' },
  { expr: '0 9 * * *', desc: 'Daily at 9 AM' },
  { expr: '0 12 * * *', desc: 'Daily at noon' },
  { expr: '0 18 * * *', desc: 'Daily at 6 PM' },
  { expr: '0 23 * * *', desc: 'Daily at 11 PM' },
  // Business hours
  { expr: '0 9-17 * * 1-5', desc: 'Business hours (hourly)' },
  { expr: '0 9,12,15,18 * * 1-5', desc: 'Business checkpoints' },
  { expr: '0 9,18 * * 1-5', desc: 'Start and end of business day' },
  // Weekly
  { expr: '0 0 * * 0', desc: 'Weekly on Sunday' },
  { expr: '0 0 * * 1', desc: 'Weekly on Monday' },
  { expr: '0 6 * * 1', desc: 'Monday morning at 6 AM' },
  { expr: '0 0 * * 5', desc: 'Weekly on Friday' },
  // Monthly
  { expr: '0 0 1 * *', desc: 'Monthly on 1st' },
  { expr: '0 0 15 * *', desc: 'Monthly on 15th' },
  { expr: '0 0 L * *', desc: 'Last day of month' },
  // Quarterly
  { expr: '0 0 1 1,4,7,10 *', desc: 'Quarterly (Q1-Q4 start)' },
  // Complex patterns
  { expr: '0 8-20/2 * * 1-5', desc: 'Every 2 hours during work day' },
  { expr: '30 4 1,15 * *', desc: '1st and 15th at 4:30 AM' },
]

// Comprehensive schedule names
const SCHEDULE_NAMES = [
  // Quality checks
  'Daily Quality Check',
  'Hourly Validation',
  'Real-time Data Monitor',
  'Continuous Integrity Check',
  // Audits
  'Weekly Data Audit',
  'Monthly Compliance Scan',
  'Quarterly Data Review',
  // Operations
  'Nightly ETL Validation',
  'Post-Load Quality Gate',
  'Pre-Report Verification',
  // Business specific
  'Business Hours Check',
  'End-of-Day Validation',
  'Market Close Verification',
  'Settlement Reconciliation',
  // Technical
  'Schema Drift Detection',
  'Data Freshness Check',
  'Anomaly Detection Run',
  'Pipeline Health Check',
  // Special
  'Critical Systems Monitor',
  'Customer Data Validation',
  'Financial Data Audit',
  'Inventory Sync Check',
]

// Validator combinations for different use cases
const VALIDATOR_PRESETS = [
  ['schema'],
  ['null_check'],
  ['type_check'],
  ['schema', 'null_check'],
  ['schema', 'type_check'],
  ['null_check', 'type_check'],
  ['schema', 'null_check', 'type_check'],
  ['schema', 'null_check', 'type_check', 'range_check'],
  ['schema', 'null_check', 'type_check', 'uniqueness_check'],
  ['schema', 'null_check', 'type_check', 'format_check'],
  ['schema', 'null_check', 'type_check', 'range_check', 'uniqueness_check', 'format_check'],
]

function calculateNextRun(isActive: boolean, cronExpr: string): string | undefined {
  if (!isActive) return undefined

  const next = new Date()
  // Simulate different next run times based on cron pattern
  // Parse cron expression: minute hour day month weekday
  const parts = cronExpr.split(' ')
  const minutePart = parts[0] || ''
  const hourPart = parts[1] || ''

  if (minutePart.startsWith('*/')) {
    // Every N minutes (e.g., */5, */15, */30)
    const interval = parseInt(minutePart.slice(2)) || 5
    next.setMinutes(next.getMinutes() + randomInt(1, interval))
  } else if (hourPart.startsWith('*/')) {
    // Every N hours (e.g., 0 */2 * * *)
    const interval = parseInt(hourPart.slice(2)) || 2
    next.setHours(next.getHours() + randomInt(1, interval))
  } else if (hourPart === '*' && minutePart === '0') {
    // Hourly (0 * * * *)
    next.setHours(next.getHours() + randomInt(1, 2))
  } else if (hourPart.includes('-')) {
    // Range pattern like 9-17 (business hours)
    next.setHours(next.getHours() + randomInt(1, 8))
  } else if (hourPart.includes(',')) {
    // Specific hours like 9,12,15,18
    next.setHours(next.getHours() + randomInt(2, 6))
  } else {
    // Daily or less frequent - default to 1-48 hours
    next.setHours(next.getHours() + randomInt(1, 48))
  }
  return next.toISOString()
}

function calculateLastRun(hasRun: boolean): string | undefined {
  if (!hasRun) return undefined

  const last = new Date()
  last.setHours(last.getHours() - randomInt(1, 168)) // Up to 1 week ago
  return last.toISOString()
}

// Default trigger configs for different types
const DEFAULT_TRIGGER_CONFIGS: Record<TriggerType, () => Record<string, unknown>> = {
  cron: () => ({ type: 'cron', expression: randomChoice(CRON_EXPRESSIONS).expr }),
  interval: () => ({
    type: 'interval',
    hours: randomChoice([1, 2, 4, 6, 12]),
    minutes: randomChoice([0, 15, 30, 45]),
  }),
  data_change: () => ({
    type: 'data_change',
    change_threshold: randomChoice([0.01, 0.05, 0.1, 0.2]),
    metrics: randomChoice([['row_count'], ['row_count', 'null_percentage'], ['row_count', 'null_percentage', 'distinct_count']]),
    check_interval_minutes: randomChoice([15, 30, 60, 120]),
  }),
  composite: () => ({
    type: 'composite',
    operator: randomChoice(['and', 'or'] as const),
    triggers: [
      { type: 'cron', expression: '0 0 * * *' },
      { type: 'data_change', change_threshold: 0.05, metrics: ['row_count'] },
    ],
  }),
  event: () => ({
    type: 'event',
    event_types: randomChoice([
      ['schema_changed'],
      ['drift_detected'],
      ['validation_failed'],
      ['schema_changed', 'drift_detected'],
    ]),
  }),
  manual: () => ({ type: 'manual' }),
}

export function createSchedule(options: ScheduleFactoryOptions = {}): Schedule {
  const cron = options.cronExpression
    ? CRON_EXPRESSIONS.find((c) => c.expr === options.cronExpression) ?? { expr: options.cronExpression, desc: 'Custom' }
    : randomChoice(CRON_EXPRESSIONS)
  const isActive = options.isActive ?? faker.datatype.boolean(0.8)
  const hasRun = options.hasRun ?? faker.datatype.boolean(0.7)
  const validators = options.validators ?? randomChoice(VALIDATOR_PRESETS)
  const triggerType = options.triggerType ?? 'cron'
  const triggerConfig = options.triggerConfig ?? DEFAULT_TRIGGER_CONFIGS[triggerType]()

  // For cron type, use the cron expression from the config if not specified
  const cronExpression = triggerType === 'cron'
    ? (triggerConfig.expression as string || cron.expr)
    : cron.expr

  return {
    id: options.id ?? createId(),
    name: options.name ?? randomChoice(SCHEDULE_NAMES) + ` (${faker.string.alphanumeric(3)})`,
    source_id: options.sourceId ?? createId(),
    cron_expression: cronExpression,
    trigger_type: triggerType,
    trigger_config: triggerConfig,
    trigger_count: hasRun ? randomInt(1, 100) : 0,
    is_active: isActive,
    notify_on_failure: options.notifyOnFailure ?? faker.datatype.boolean(0.7),
    last_run_at: calculateLastRun(hasRun),
    next_run_at: calculateNextRun(isActive, cronExpression),
    config: {
      validators,
      auto_schema: options.autoSchema ?? faker.datatype.boolean(0.6),
    },
    created_at: createTimestamp(randomInt(14, 180)),
    updated_at: createTimestamp(randomInt(0, 14)),
    source_name: options.sourceName ?? faker.commerce.productName() + ' Data',
  }
}

export function createSchedules(count: number): Schedule[] {
  return Array.from({ length: count }, () => createSchedule())
}

/**
 * Create schedules with guaranteed coverage of all test scenarios
 */
export function createDiverseSchedules(sources: Array<{ id: string; name: string }>): Schedule[] {
  // Guard against empty sources
  if (!sources || sources.length === 0) {
    return []
  }

  const schedules: Schedule[] = []
  let sourceIndex = 0

  const getNextSource = () => {
    const source = sources[sourceIndex % sources.length]
    sourceIndex++
    return source
  }

  // 1. Active schedule that has run recently
  const s1 = getNextSource()
  schedules.push(createSchedule({
    sourceId: s1.id,
    sourceName: s1.name,
    name: 'Active Daily Check',
    isActive: true,
    hasRun: true,
    cronExpression: '0 6 * * *',
  }))

  // 2. Active schedule that has never run
  const s2 = getNextSource()
  schedules.push(createSchedule({
    sourceId: s2.id,
    sourceName: s2.name,
    name: 'New Schedule (Never Run)',
    isActive: true,
    hasRun: false,
    cronExpression: '0 0 1 * *',
  }))

  // 3. Paused schedule (was active, now inactive)
  const s3 = getNextSource()
  schedules.push(createSchedule({
    sourceId: s3.id,
    sourceName: s3.name,
    name: 'Paused Weekly Audit',
    isActive: false,
    hasRun: true,
    cronExpression: '0 0 * * 1',
  }))

  // 4. Inactive schedule that never ran
  const s4 = getNextSource()
  schedules.push(createSchedule({
    sourceId: s4.id,
    sourceName: s4.name,
    name: 'Draft Schedule (Inactive)',
    isActive: false,
    hasRun: false,
  }))

  // 5. High frequency schedule (every 5 minutes)
  const s5 = getNextSource()
  schedules.push(createSchedule({
    sourceId: s5.id,
    sourceName: s5.name,
    name: 'Real-time Monitor',
    isActive: true,
    hasRun: true,
    cronExpression: '*/5 * * * *',
  }))

  // 6. Low frequency schedule (monthly)
  const s6 = getNextSource()
  schedules.push(createSchedule({
    sourceId: s6.id,
    sourceName: s6.name,
    name: 'Monthly Compliance Check',
    isActive: true,
    hasRun: true,
    cronExpression: '0 0 1 * *',
  }))

  // 7. Business hours only schedule
  const s7 = getNextSource()
  schedules.push(createSchedule({
    sourceId: s7.id,
    sourceName: s7.name,
    name: 'Business Hours Validation',
    isActive: true,
    hasRun: true,
    cronExpression: '0 9-17 * * 1-5',
  }))

  // 8. With all notifications enabled
  const s8 = getNextSource()
  schedules.push(createSchedule({
    sourceId: s8.id,
    sourceName: s8.name,
    name: 'Critical Alert Schedule',
    isActive: true,
    hasRun: true,
    notifyOnFailure: true,
  }))

  // 9. Notifications disabled
  const s9 = getNextSource()
  schedules.push(createSchedule({
    sourceId: s9.id,
    sourceName: s9.name,
    name: 'Silent Validation',
    isActive: true,
    hasRun: true,
    notifyOnFailure: false,
  }))

  // 10. Minimal validators
  const s10 = getNextSource()
  schedules.push(createSchedule({
    sourceId: s10.id,
    sourceName: s10.name,
    name: 'Simple Schema Check',
    isActive: true,
    hasRun: true,
    validators: ['schema'],
    autoSchema: false,
  }))

  // 11. Full validators
  const s11 = getNextSource()
  schedules.push(createSchedule({
    sourceId: s11.id,
    sourceName: s11.name,
    name: 'Comprehensive Validation',
    isActive: true,
    hasRun: true,
    validators: ['schema', 'null_check', 'type_check', 'range_check', 'uniqueness_check', 'format_check'],
    autoSchema: true,
  }))

  // 12. Auto-schema enabled
  const s12 = getNextSource()
  schedules.push(createSchedule({
    sourceId: s12.id,
    sourceName: s12.name,
    name: 'Auto-learning Schedule',
    isActive: true,
    hasRun: true,
    autoSchema: true,
  }))

  // 13. Weekend schedule
  const s13 = getNextSource()
  schedules.push(createSchedule({
    sourceId: s13.id,
    sourceName: s13.name,
    name: 'Weekend Batch Process',
    isActive: true,
    hasRun: true,
    cronExpression: '0 0 * * 0',
  }))

  // 14. Interval trigger - every 6 hours
  const s14 = getNextSource()
  schedules.push(createSchedule({
    sourceId: s14.id,
    sourceName: s14.name,
    name: 'Hourly Data Refresh Check',
    isActive: true,
    hasRun: true,
    triggerType: 'interval',
    triggerConfig: { type: 'interval', hours: 6 },
  }))

  // 15. Data change trigger
  const s15 = getNextSource()
  schedules.push(createSchedule({
    sourceId: s15.id,
    sourceName: s15.name,
    name: 'Data Change Detection',
    isActive: true,
    hasRun: true,
    triggerType: 'data_change',
    triggerConfig: {
      type: 'data_change',
      change_threshold: 0.05,
      metrics: ['row_count', 'null_percentage'],
      check_interval_minutes: 30,
    },
  }))

  // 16. Composite trigger (AND logic)
  const s16 = getNextSource()
  schedules.push(createSchedule({
    sourceId: s16.id,
    sourceName: s16.name,
    name: 'Composite Validation (AND)',
    isActive: true,
    hasRun: true,
    triggerType: 'composite',
    triggerConfig: {
      type: 'composite',
      operator: 'and',
      triggers: [
        { type: 'cron', expression: '0 8 * * 1-5' },
        { type: 'data_change', change_threshold: 0.1, metrics: ['row_count'] },
      ],
    },
  }))

  // 17. Composite trigger (OR logic)
  const s17 = getNextSource()
  schedules.push(createSchedule({
    sourceId: s17.id,
    sourceName: s17.name,
    name: 'Composite Validation (OR)',
    isActive: true,
    hasRun: false,
    triggerType: 'composite',
    triggerConfig: {
      type: 'composite',
      operator: 'or',
      triggers: [
        { type: 'interval', hours: 12 },
        { type: 'event', event_types: ['schema_changed'] },
      ],
    },
  }))

  // 18. Event trigger
  const s18 = getNextSource()
  schedules.push(createSchedule({
    sourceId: s18.id,
    sourceName: s18.name,
    name: 'Schema Change Watcher',
    isActive: true,
    hasRun: true,
    triggerType: 'event',
    triggerConfig: {
      type: 'event',
      event_types: ['schema_changed', 'drift_detected'],
    },
  }))

  // 19. Manual trigger only
  const s19 = getNextSource()
  schedules.push(createSchedule({
    sourceId: s19.id,
    sourceName: s19.name,
    name: 'On-Demand Validation',
    isActive: true,
    hasRun: false,
    triggerType: 'manual',
    triggerConfig: { type: 'manual' },
  }))

  // 20. Add a few more random schedules
  for (let i = 0; i < 3; i++) {
    const s = getNextSource()
    schedules.push(createSchedule({
      sourceId: s.id,
      sourceName: s.name,
    }))
  }

  return schedules
}
