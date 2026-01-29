/**
 * Advanced Notification factory - generates routing rules, deduplication configs,
 * throttling configs, escalation policies, and escalation incidents
 */

import { createId, createTimestamp, randomChoice, randomInt, faker } from './base'

// ============================================================================
// Types
// ============================================================================

export interface RoutingRule {
  id: string
  name: string
  rule_config: Record<string, unknown>
  actions: string[]
  priority: number
  is_active: boolean
  stop_on_match: boolean
  metadata: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface DeduplicationConfig {
  id: string
  name: string
  strategy: 'sliding' | 'tumbling' | 'session' | 'adaptive'
  policy: 'none' | 'basic' | 'severity' | 'issue_based' | 'strict' | 'custom'
  window_seconds: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ThrottlingConfig {
  id: string
  name: string
  per_minute: number | null
  per_hour: number | null
  per_day: number | null
  burst_allowance: number
  channel_id: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface EscalationTarget {
  type: 'user' | 'group' | 'oncall' | 'channel'
  identifier: string
  channel: string
}

export interface EscalationLevel {
  level: number
  delay_minutes: number
  targets: EscalationTarget[]
}

export interface EscalationPolicy {
  id: string
  name: string
  description: string
  levels: EscalationLevel[]
  auto_resolve_on_success: boolean
  max_escalations: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface EscalationEvent {
  from_state: string | null
  to_state: string
  actor: string | null
  message: string
  timestamp: string
}

export interface EscalationIncident {
  id: string
  policy_id: string
  incident_ref: string
  state: 'pending' | 'triggered' | 'acknowledged' | 'escalated' | 'resolved'
  current_level: number
  escalation_count: number
  context: Record<string, unknown>
  acknowledged_by: string | null
  acknowledged_at: string | null
  resolved_by: string | null
  resolved_at: string | null
  next_escalation_at: string | null
  events: EscalationEvent[]
  created_at: string
  updated_at: string
}

export interface RuleTypeInfo {
  type: string
  name: string
  description: string
  param_schema: Record<string, unknown>
}

// ============================================================================
// Routing Rules
// ============================================================================

const RULE_TYPES = [
  'severity',
  'issue_count',
  'pass_rate',
  'time_window',
  'tag',
  'data_asset',
  'metadata',
  'status',
  'error',
  'always',
  'never',
]

const RULE_CONFIGS: Record<string, () => Record<string, unknown>> = {
  severity: () => ({ min_severity: randomChoice(['low', 'medium', 'high', 'critical']) }),
  issue_count: () => ({ min_count: randomInt(1, 20) }),
  pass_rate: () => ({ max_pass_rate: faker.number.float({ min: 0.5, max: 0.95, fractionDigits: 2 }) }),
  time_window: () => ({
    start_hour: randomInt(0, 12),
    end_hour: randomInt(13, 23),
    weekdays: faker.helpers.arrayElements([0, 1, 2, 3, 4, 5, 6], randomInt(3, 7)),
    timezone: 'UTC',
  }),
  tag: () => ({ tags: faker.helpers.arrayElements(['production', 'staging', 'critical', 'finance', 'pii'], randomInt(1, 3)) }),
  data_asset: () => ({ pattern: `*_${randomChoice(['orders', 'users', 'transactions', 'events'])}` }),
  metadata: () => ({ key: randomChoice(['team', 'department', 'owner']), value: faker.person.firstName().toLowerCase() }),
  status: () => ({ statuses: faker.helpers.arrayElements(['failed', 'error', 'warning'], randomInt(1, 2)) }),
  error: () => ({ error_pattern: `.*${randomChoice(['timeout', 'connection', 'auth'])}.*` }),
  always: () => ({}),
  never: () => ({}),
}

export interface RoutingRuleFactoryOptions {
  id?: string
  name?: string
  ruleType?: string
  channelIds?: string[]
  priority?: number
  isActive?: boolean
}

export function createRoutingRule(options: RoutingRuleFactoryOptions = {}): RoutingRule {
  const ruleType = options.ruleType ?? randomChoice(RULE_TYPES)
  const configGenerator = RULE_CONFIGS[ruleType] ?? (() => ({}))

  return {
    id: options.id ?? createId(),
    name: options.name ?? `${ruleType.replace('_', ' ')} Rule - ${faker.string.alphanumeric(4)}`,
    rule_config: {
      type: ruleType,
      ...configGenerator(),
    },
    actions: options.channelIds ?? [createId()],
    priority: options.priority ?? randomInt(0, 100),
    is_active: options.isActive ?? faker.datatype.boolean(0.85),
    stop_on_match: faker.datatype.boolean(0.2),
    metadata: {},
    created_at: createTimestamp(randomInt(7, 90)),
    updated_at: createTimestamp(randomInt(0, 7)),
  }
}

export function createRoutingRules(count: number, channelIds?: string[]): RoutingRule[] {
  return Array.from({ length: count }, () =>
    createRoutingRule({ channelIds: channelIds ? [faker.helpers.arrayElement(channelIds)] : undefined })
  ).sort((a, b) => b.priority - a.priority)
}

export function getRuleTypes(): RuleTypeInfo[] {
  return [
    { type: 'severity', name: 'Severity', description: 'Match based on issue severity level', param_schema: { min_severity: { type: 'string', required: true } } },
    { type: 'issue_count', name: 'Issue Count', description: 'Match when issue count exceeds threshold', param_schema: { min_count: { type: 'integer', required: true } } },
    { type: 'pass_rate', name: 'Pass Rate', description: 'Match when pass rate falls below threshold', param_schema: { max_pass_rate: { type: 'number', required: true } } },
    { type: 'time_window', name: 'Time Window', description: 'Match during specific time windows', param_schema: { start_hour: { type: 'integer' }, end_hour: { type: 'integer' } } },
    { type: 'tag', name: 'Tag', description: 'Match based on tags', param_schema: { tags: { type: 'array', required: true } } },
    { type: 'data_asset', name: 'Data Asset', description: 'Match based on data asset patterns', param_schema: { pattern: { type: 'string', required: true } } },
    { type: 'metadata', name: 'Metadata', description: 'Match based on metadata key-value pairs', param_schema: { key: { type: 'string' }, value: { type: 'string' } } },
    { type: 'status', name: 'Status', description: 'Match based on validation status', param_schema: { statuses: { type: 'array', required: true } } },
    { type: 'error', name: 'Error', description: 'Match based on error patterns', param_schema: { error_pattern: { type: 'string', required: true } } },
    { type: 'always', name: 'Always', description: 'Always matches (catch-all)', param_schema: {} },
    { type: 'never', name: 'Never', description: 'Never matches (disabled)', param_schema: {} },
    { type: 'all_of', name: 'All Of', description: 'Match when all child rules match (AND)', param_schema: { rules: { type: 'array' } } },
    { type: 'any_of', name: 'Any Of', description: 'Match when any child rule matches (OR)', param_schema: { rules: { type: 'array' } } },
    { type: 'not', name: 'Not', description: 'Match when child rule does not match', param_schema: { rule: { type: 'object' } } },
  ]
}

// ============================================================================
// Deduplication
// ============================================================================

const STRATEGIES = ['sliding', 'tumbling', 'session', 'adaptive'] as const
const POLICIES = ['none', 'basic', 'severity', 'issue_based', 'strict', 'custom'] as const

export interface DeduplicationConfigFactoryOptions {
  id?: string
  name?: string
  strategy?: DeduplicationConfig['strategy']
  policy?: DeduplicationConfig['policy']
  windowSeconds?: number
  isActive?: boolean
}

export function createDeduplicationConfig(options: DeduplicationConfigFactoryOptions = {}): DeduplicationConfig {
  return {
    id: options.id ?? createId(),
    name: options.name ?? `Dedup Config - ${faker.string.alphanumeric(4)}`,
    strategy: options.strategy ?? randomChoice(STRATEGIES),
    policy: options.policy ?? randomChoice(POLICIES),
    window_seconds: options.windowSeconds ?? randomChoice([60, 300, 600, 1800, 3600]),
    is_active: options.isActive ?? faker.datatype.boolean(0.8),
    created_at: createTimestamp(randomInt(14, 120)),
    updated_at: createTimestamp(randomInt(0, 14)),
  }
}

export function createDeduplicationConfigs(count: number): DeduplicationConfig[] {
  return Array.from({ length: count }, () => createDeduplicationConfig())
}

export interface DeduplicationStats {
  total_received: number
  total_deduplicated: number
  total_passed: number
  dedup_rate: number
  active_fingerprints: number
}

export function createDeduplicationStats(): DeduplicationStats {
  const total = randomInt(100, 1000)
  const deduplicated = Math.floor(total * faker.number.float({ min: 0.1, max: 0.4 }))
  const passed = total - deduplicated

  return {
    total_received: total,
    total_deduplicated: deduplicated,
    total_passed: passed,
    dedup_rate: (deduplicated / total) * 100,
    active_fingerprints: randomInt(10, 100),
  }
}

// ============================================================================
// Throttling
// ============================================================================

export interface ThrottlingConfigFactoryOptions {
  id?: string
  name?: string
  perMinute?: number | null
  perHour?: number | null
  perDay?: number | null
  burstAllowance?: number
  channelId?: string | null
  isActive?: boolean
}

export function createThrottlingConfig(options: ThrottlingConfigFactoryOptions = {}): ThrottlingConfig {
  return {
    id: options.id ?? createId(),
    name: options.name ?? `Throttle Config - ${faker.string.alphanumeric(4)}`,
    per_minute: options.perMinute !== undefined ? options.perMinute : (faker.datatype.boolean(0.5) ? randomInt(5, 30) : null),
    per_hour: options.perHour !== undefined ? options.perHour : (faker.datatype.boolean(0.7) ? randomInt(50, 200) : null),
    per_day: options.perDay !== undefined ? options.perDay : (faker.datatype.boolean(0.5) ? randomInt(200, 1000) : null),
    burst_allowance: options.burstAllowance ?? faker.number.float({ min: 1.0, max: 3.0, fractionDigits: 1 }),
    channel_id: options.channelId !== undefined ? options.channelId : (faker.datatype.boolean(0.3) ? createId() : null),
    is_active: options.isActive ?? faker.datatype.boolean(0.85),
    created_at: createTimestamp(randomInt(14, 90)),
    updated_at: createTimestamp(randomInt(0, 14)),
  }
}

export function createThrottlingConfigs(count: number): ThrottlingConfig[] {
  return Array.from({ length: count }, () => createThrottlingConfig())
}

export interface ThrottlingStats {
  total_received: number
  total_throttled: number
  total_passed: number
  throttle_rate: number
  current_window_count: number
}

export function createThrottlingStats(): ThrottlingStats {
  const total = randomInt(100, 500)
  const throttled = Math.floor(total * faker.number.float({ min: 0.01, max: 0.15 }))
  const passed = total - throttled

  return {
    total_received: total,
    total_throttled: throttled,
    total_passed: passed,
    throttle_rate: (throttled / total) * 100,
    current_window_count: randomInt(0, 20),
  }
}

// ============================================================================
// Escalation Policies
// ============================================================================

const TARGET_TYPES = ['user', 'group', 'oncall', 'channel'] as const

export interface EscalationPolicyFactoryOptions {
  id?: string
  name?: string
  levelCount?: number
  channelIds?: string[]
  isActive?: boolean
}

function createEscalationTarget(channelId?: string): EscalationTarget {
  return {
    type: randomChoice(TARGET_TYPES),
    identifier: faker.datatype.boolean(0.6) ? faker.internet.email() : faker.person.firstName().toLowerCase(),
    channel: channelId ?? createId(),
  }
}

function createEscalationLevel(level: number, channelIds?: string[]): EscalationLevel {
  const targetCount = randomInt(1, 3)
  return {
    level,
    delay_minutes: level === 1 ? 0 : randomInt(5, 30) * level,
    targets: Array.from({ length: targetCount }, () =>
      createEscalationTarget(channelIds ? faker.helpers.arrayElement(channelIds) : undefined)
    ),
  }
}

export function createEscalationPolicy(options: EscalationPolicyFactoryOptions = {}): EscalationPolicy {
  const levelCount = options.levelCount ?? randomInt(2, 4)

  return {
    id: options.id ?? createId(),
    name: options.name ?? `Escalation Policy - ${faker.company.buzzNoun()}`,
    description: faker.lorem.sentence(),
    levels: Array.from({ length: levelCount }, (_, i) =>
      createEscalationLevel(i + 1, options.channelIds)
    ),
    auto_resolve_on_success: faker.datatype.boolean(0.8),
    max_escalations: randomInt(3, 5),
    is_active: options.isActive ?? faker.datatype.boolean(0.85),
    created_at: createTimestamp(randomInt(30, 180)),
    updated_at: createTimestamp(randomInt(0, 30)),
  }
}

export function createEscalationPolicies(count: number, channelIds?: string[]): EscalationPolicy[] {
  return Array.from({ length: count }, () => createEscalationPolicy({ channelIds }))
}

// ============================================================================
// Escalation Incidents
// ============================================================================

const INCIDENT_STATES = ['pending', 'triggered', 'acknowledged', 'escalated', 'resolved'] as const

export interface EscalationIncidentFactoryOptions {
  id?: string
  policyId?: string
  state?: EscalationIncident['state']
  incidentRef?: string
}

function createEscalationEvents(state: EscalationIncident['state']): EscalationEvent[] {
  const events: EscalationEvent[] = []
  const baseTime = new Date()
  baseTime.setMinutes(baseTime.getMinutes() - randomInt(30, 240))

  // Initial trigger
  events.push({
    from_state: null,
    to_state: 'triggered',
    actor: null,
    message: 'Escalation triggered',
    timestamp: baseTime.toISOString(),
  })

  if (state === 'triggered') return events

  // Escalation events
  if (state === 'escalated' || (state !== 'acknowledged' && faker.datatype.boolean(0.3))) {
    baseTime.setMinutes(baseTime.getMinutes() + randomInt(10, 30))
    events.push({
      from_state: 'triggered',
      to_state: 'escalated',
      actor: null,
      message: 'Escalated to level 2',
      timestamp: baseTime.toISOString(),
    })
  }

  if (state === 'acknowledged') {
    baseTime.setMinutes(baseTime.getMinutes() + randomInt(5, 20))
    events.push({
      from_state: events[events.length - 1].to_state,
      to_state: 'acknowledged',
      actor: faker.internet.email(),
      message: 'Acknowledged by on-call engineer',
      timestamp: baseTime.toISOString(),
    })
  }

  if (state === 'resolved') {
    baseTime.setMinutes(baseTime.getMinutes() + randomInt(10, 60))
    const previousState = events[events.length - 1].to_state
    events.push({
      from_state: previousState,
      to_state: 'resolved',
      actor: faker.datatype.boolean(0.7) ? faker.internet.email() : null,
      message: faker.datatype.boolean(0.7) ? 'Resolved - issue fixed' : 'Auto-resolved - validation passed',
      timestamp: baseTime.toISOString(),
    })
  }

  return events
}

export function createEscalationIncident(options: EscalationIncidentFactoryOptions = {}): EscalationIncident {
  const state = options.state ?? randomChoice(INCIDENT_STATES)
  const events = createEscalationEvents(state)
  const isResolved = state === 'resolved'
  const isAcknowledged = state === 'acknowledged' || isResolved

  const createdAt = events[0]?.timestamp ?? createTimestamp(randomInt(0, 7))

  return {
    id: options.id ?? createId(),
    policy_id: options.policyId ?? createId(),
    incident_ref: options.incidentRef ?? `validation-${createId().slice(0, 8)}`,
    state,
    current_level: state === 'escalated' ? randomInt(2, 3) : 1,
    escalation_count: state === 'escalated' ? randomInt(1, 3) : 0,
    context: {
      source_name: faker.commerce.productName(),
      validation_id: createId(),
      severity: randomChoice(['critical', 'high', 'medium']),
      issue_count: randomInt(1, 20),
    },
    acknowledged_by: isAcknowledged ? faker.internet.email() : null,
    acknowledged_at: isAcknowledged ? createTimestamp(randomInt(0, 1)) : null,
    resolved_by: isResolved ? (faker.datatype.boolean(0.7) ? faker.internet.email() : null) : null,
    resolved_at: isResolved ? createTimestamp(randomInt(0, 1)) : null,
    next_escalation_at: !isResolved && state !== 'acknowledged' ? createFutureTimestamp(randomInt(5, 30)) : null,
    events,
    created_at: createdAt,
    updated_at: events[events.length - 1]?.timestamp ?? createdAt,
  }
}

// Helper for creating timestamps in the future
function createFutureTimestamp(minutesAhead: number): string {
  const date = new Date()
  date.setMinutes(date.getMinutes() + minutesAhead)
  return date.toISOString()
}

export function createEscalationIncidents(count: number, policyIds?: string[]): EscalationIncident[] {
  return Array.from({ length: count }, () =>
    createEscalationIncident({
      policyId: policyIds ? faker.helpers.arrayElement(policyIds) : undefined,
    })
  ).sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
}

export interface EscalationStats {
  total_incidents: number
  by_state: Record<string, number>
  active_count: number
  total_policies: number
  avg_resolution_time_minutes: number | null
}

export function createEscalationStats(policyCount: number = 3): EscalationStats {
  const total = randomInt(20, 100)
  const resolved = Math.floor(total * faker.number.float({ min: 0.5, max: 0.8 }))
  const acknowledged = Math.floor((total - resolved) * 0.3)
  const escalated = Math.floor((total - resolved - acknowledged) * 0.4)
  const triggered = total - resolved - acknowledged - escalated

  return {
    total_incidents: total,
    by_state: {
      triggered,
      acknowledged,
      escalated,
      resolved,
    },
    active_count: total - resolved,
    total_policies: policyCount,
    avg_resolution_time_minutes: randomInt(15, 120),
  }
}

// ============================================================================
// Diverse Data Creation (for comprehensive test coverage)
// ============================================================================

export function createDiverseRoutingRules(channelIds: string[]): RoutingRule[] {
  if (!channelIds || channelIds.length === 0) return []

  const rules: RoutingRule[] = []

  // One rule for each type
  RULE_TYPES.forEach((ruleType, index) => {
    rules.push(createRoutingRule({
      name: `${ruleType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} Rule`,
      ruleType,
      channelIds: [channelIds[index % channelIds.length]],
      priority: 100 - index * 5,
      isActive: true,
    }))
  })

  // Inactive rules
  rules.push(createRoutingRule({
    name: 'Disabled Critical Rule',
    ruleType: 'severity',
    channelIds: [channelIds[0]],
    isActive: false,
  }))

  // High priority catch-all
  rules.push(createRoutingRule({
    name: 'Default Fallback',
    ruleType: 'always',
    channelIds: channelIds.slice(0, 2),
    priority: 0,
    isActive: true,
  }))

  return rules.sort((a, b) => b.priority - a.priority)
}

export function createDiverseDeduplicationConfigs(): DeduplicationConfig[] {
  const configs: DeduplicationConfig[] = []

  // One config for each strategy
  STRATEGIES.forEach((strategy) => {
    configs.push(createDeduplicationConfig({
      name: `${strategy.charAt(0).toUpperCase() + strategy.slice(1)} Window Config`,
      strategy,
      policy: 'basic',
      isActive: true,
    }))
  })

  // One config for each policy
  POLICIES.forEach((policy) => {
    configs.push(createDeduplicationConfig({
      name: `${policy.charAt(0).toUpperCase() + policy.slice(1)} Policy Config`,
      strategy: 'sliding',
      policy,
      isActive: true,
    }))
  })

  // Inactive config
  configs.push(createDeduplicationConfig({
    name: 'Disabled Dedup Config',
    isActive: false,
  }))

  return configs
}

export function createDiverseThrottlingConfigs(channelIds?: string[]): ThrottlingConfig[] {
  const configs: ThrottlingConfig[] = []

  // Global throttle (no channel)
  configs.push(createThrottlingConfig({
    name: 'Global Rate Limit',
    perMinute: 10,
    perHour: 100,
    perDay: 500,
    burstAllowance: 1.5,
    channelId: null,
    isActive: true,
  }))

  // Per-channel throttles
  if (channelIds && channelIds.length > 0) {
    configs.push(createThrottlingConfig({
      name: 'Slack Rate Limit',
      perMinute: 5,
      perHour: 50,
      channelId: channelIds[0],
      isActive: true,
    }))

    if (channelIds.length > 1) {
      configs.push(createThrottlingConfig({
        name: 'Email Rate Limit',
        perHour: 20,
        perDay: 100,
        channelId: channelIds[1],
        isActive: true,
      }))
    }
  }

  // High burst allowance
  configs.push(createThrottlingConfig({
    name: 'Burst-Friendly Config',
    perMinute: 30,
    burstAllowance: 3.0,
    isActive: true,
  }))

  // Inactive
  configs.push(createThrottlingConfig({
    name: 'Disabled Throttle',
    isActive: false,
  }))

  return configs
}

export function createDiverseEscalationPolicies(channelIds?: string[]): EscalationPolicy[] {
  const policies: EscalationPolicy[] = []

  // Simple 2-level policy
  policies.push(createEscalationPolicy({
    name: 'Basic On-Call Escalation',
    levelCount: 2,
    channelIds,
    isActive: true,
  }))

  // Complex 4-level policy
  policies.push(createEscalationPolicy({
    name: 'Critical Incident Escalation',
    levelCount: 4,
    channelIds,
    isActive: true,
  }))

  // Disabled policy
  policies.push(createEscalationPolicy({
    name: 'Legacy Escalation (Disabled)',
    levelCount: 2,
    channelIds,
    isActive: false,
  }))

  return policies
}

export function createDiverseEscalationIncidents(policyIds: string[]): EscalationIncident[] {
  if (!policyIds || policyIds.length === 0) return []

  const incidents: EscalationIncident[] = []

  // One incident for each state
  INCIDENT_STATES.forEach((state) => {
    incidents.push(createEscalationIncident({
      policyId: faker.helpers.arrayElement(policyIds),
      state,
    }))
  })

  // Multiple active incidents
  for (let i = 0; i < 5; i++) {
    incidents.push(createEscalationIncident({
      policyId: faker.helpers.arrayElement(policyIds),
      state: randomChoice(['triggered', 'escalated', 'acknowledged'] as const),
    }))
  }

  // Multiple resolved incidents
  for (let i = 0; i < 10; i++) {
    incidents.push(createEscalationIncident({
      policyId: faker.helpers.arrayElement(policyIds),
      state: 'resolved',
    }))
  }

  return incidents.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
}
