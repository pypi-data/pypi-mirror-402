/**
 * Advanced Notifications API handlers
 * Handles routing rules, deduplication, throttling, and escalation endpoints
 */

import { http, HttpResponse, delay } from 'msw'
import {
  getStore,
  getAll,
  getById,
  create,
  update,
  remove,
} from '../data/store'
import {
  createRoutingRule,
  createDeduplicationConfig,
  createThrottlingConfig,
  createEscalationPolicy,
  createDeduplicationStats,
  createThrottlingStats,
  createEscalationStats,
  getRuleTypes,
  createId,
  type RoutingRule,
  type DeduplicationConfig,
  type ThrottlingConfig,
  type EscalationPolicy,
} from '../factories'

const API_BASE = '/api/v1'

export const notificationsAdvancedHandlers = [
  // ============================================================================
  // Routing Rules
  // ============================================================================

  // Get rule types
  http.get(`${API_BASE}/notifications/routing/rules/types`, async () => {
    await delay(100)

    return HttpResponse.json({
      rule_types: getRuleTypes(),
    })
  }),

  // List routing rules
  http.get(`${API_BASE}/notifications/routing/rules`, async ({ request }) => {
    await delay(200)

    const url = new URL(request.url)
    const offset = parseInt(url.searchParams.get('offset') ?? '0')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')
    const activeOnly = url.searchParams.get('active_only') === 'true'

    let rules = getAll(getStore().routingRules)

    if (activeOnly) {
      rules = rules.filter((r) => r.is_active)
    }

    // Sort by priority descending
    rules.sort((a, b) => b.priority - a.priority)

    const total = rules.length
    const paginated = rules.slice(offset, offset + limit)

    return HttpResponse.json({
      items: paginated,
      total,
      offset,
      limit,
    })
  }),

  // Get routing rule by ID
  http.get(`${API_BASE}/notifications/routing/rules/:id`, async ({ params }) => {
    await delay(150)

    const rule = getById(getStore().routingRules, params.id as string)

    if (!rule) {
      return HttpResponse.json(
        { detail: 'Routing rule not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(rule)
  }),

  // Create routing rule
  http.post(`${API_BASE}/notifications/routing/rules`, async ({ request }) => {
    await delay(300)

    let body: Partial<RoutingRule>

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const rule = createRoutingRule({
      id: createId(),
      name: body.name,
      channelIds: body.actions,
      priority: body.priority,
      isActive: body.is_active,
    })

    if (body.rule_config) {
      rule.rule_config = body.rule_config
    }
    if (body.stop_on_match !== undefined) {
      rule.stop_on_match = body.stop_on_match
    }
    if (body.metadata) {
      rule.metadata = body.metadata
    }

    rule.created_at = new Date().toISOString()
    rule.updated_at = new Date().toISOString()

    create(getStore().routingRules, rule)

    return HttpResponse.json(rule)
  }),

  // Update routing rule
  http.put(`${API_BASE}/notifications/routing/rules/:id`, async ({ params, request }) => {
    await delay(250)

    let body: Partial<RoutingRule>

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const updated = update(
      getStore().routingRules,
      params.id as string,
      { ...body, updated_at: new Date().toISOString() }
    )

    if (!updated) {
      return HttpResponse.json(
        { detail: 'Routing rule not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(updated)
  }),

  // Delete routing rule
  http.delete(`${API_BASE}/notifications/routing/rules/:id`, async ({ params }) => {
    await delay(200)

    const deleted = remove(getStore().routingRules, params.id as string)

    if (!deleted) {
      return HttpResponse.json(
        { detail: 'Routing rule not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json({ success: true, message: 'Routing rule deleted' })
  }),

  // Validate routing rule configuration
  http.post(`${API_BASE}/notifications/routing/rules/validate`, async ({ request }) => {
    await delay(200)

    interface NestedRuleConfig {
      type: string
      params?: Record<string, unknown>
      rules?: NestedRuleConfig[]
      rule?: NestedRuleConfig
    }

    let body: NestedRuleConfig

    try {
      body = await request.json() as NestedRuleConfig
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const url = new URL(request.url)
    const maxDepth = parseInt(url.searchParams.get('max_depth') ?? '10')
    const maxRulesPerCombinator = parseInt(url.searchParams.get('max_rules_per_combinator') ?? '50')
    const checkCircularRefs = url.searchParams.get('check_circular_refs') !== 'false'

    // Simple mock validation
    const errors: string[] = []
    const warnings: string[] = []
    const circularPaths: string[] = []
    let ruleCount = 0
    let maxDepthFound = 0

    const COMBINATOR_TYPES = ['all_of', 'any_of', 'not']
    const VALID_RULE_TYPES = [
      'severity', 'issue_count', 'pass_rate', 'time_window', 'tag',
      'data_asset', 'metadata', 'status', 'error', 'always', 'never',
      'expression', ...COMBINATOR_TYPES
    ]

    function validateRecursive(config: NestedRuleConfig, depth: number, path: string): void {
      ruleCount++
      maxDepthFound = Math.max(maxDepthFound, depth)

      if (depth > maxDepth) {
        errors.push(`Maximum nesting depth (${maxDepth}) exceeded at depth ${depth}`)
        return
      }

      if (!config.type) {
        errors.push(`Rule missing required field 'type' at ${path || 'root'}`)
        return
      }

      if (!VALID_RULE_TYPES.includes(config.type)) {
        errors.push(`Unknown rule type '${config.type}' at ${path || 'root'}`)
        return
      }

      if (config.type === 'not') {
        if (!config.rule) {
          errors.push(`'not' combinator requires a 'rule' field at ${path || 'root'}`)
        } else {
          validateRecursive(config.rule, depth + 1, path ? `${path}.rule` : 'rule')
        }
      } else if (config.type === 'all_of' || config.type === 'any_of') {
        if (!config.rules || config.rules.length === 0) {
          errors.push(`'${config.type}' combinator requires a non-empty 'rules' array at ${path || 'root'}`)
        } else {
          if (config.rules.length > maxRulesPerCombinator) {
            errors.push(`Combinator has ${config.rules.length} rules, exceeds maximum of ${maxRulesPerCombinator}`)
          }
          if (config.rules.length === 1) {
            warnings.push(`'${config.type}' combinator with only 1 rule is redundant at ${path || 'root'}`)
          }
          config.rules.forEach((nestedRule, idx) => {
            const nestedPath = path ? `${path}.rules[${idx}]` : `rules[${idx}]`
            validateRecursive(nestedRule, depth + 1, nestedPath)
          })
        }
      }
    }

    validateRecursive(body, 0, '')

    return HttpResponse.json({
      valid: errors.length === 0,
      errors,
      warnings,
      rule_count: ruleCount,
      max_depth: maxDepthFound,
      circular_paths: circularPaths,
    })
  }),

  // Validate expression
  http.post(`${API_BASE}/notifications/routing/rules/validate-expression`, async ({ request }) => {
    await delay(300)

    interface ExpressionValidateRequest {
      expression: string
      timeout_seconds?: number
    }

    let body: ExpressionValidateRequest

    try {
      body = await request.json() as ExpressionValidateRequest
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const { expression } = body
    // timeout_seconds is accepted but not used in mock - it's used by the real backend

    // Empty expression check
    if (!expression || !expression.trim()) {
      return HttpResponse.json({
        valid: false,
        error: 'Expression cannot be empty',
        error_line: null,
        preview_result: null,
        preview_error: null,
        warnings: [],
      })
    }

    // Check for balanced parentheses
    let parenCount = 0
    let bracketCount = 0
    let braceCount = 0
    for (const char of expression) {
      if (char === '(') parenCount++
      else if (char === ')') parenCount--
      else if (char === '[') bracketCount++
      else if (char === ']') bracketCount--
      else if (char === '{') braceCount++
      else if (char === '}') braceCount--
    }

    if (parenCount !== 0) {
      return HttpResponse.json({
        valid: false,
        error: 'Unbalanced parentheses',
        error_line: null,
        preview_result: null,
        preview_error: null,
        warnings: [],
      })
    }

    if (bracketCount !== 0) {
      return HttpResponse.json({
        valid: false,
        error: 'Unbalanced square brackets',
        error_line: null,
        preview_result: null,
        preview_error: null,
        warnings: [],
      })
    }

    if (braceCount !== 0) {
      return HttpResponse.json({
        valid: false,
        error: 'Unbalanced curly braces',
        error_line: null,
        preview_result: null,
        preview_error: null,
        warnings: [],
      })
    }

    // Check for dangerous patterns
    const dangerousPatterns = [
      /__\w+__/,        // Dunder attributes
      /\bimport\b/,     // Import statements
      /\bexec\b/,       // exec function
      /\beval\b/,       // eval function
      /\bcompile\b/,    // compile function
      /\bglobals\b/,    // globals access
      /\blocals\b/,     // locals access
    ]

    for (const pattern of dangerousPatterns) {
      if (pattern.test(expression)) {
        return HttpResponse.json({
          valid: false,
          error: `Expression contains disallowed pattern: ${pattern.source}`,
          error_line: null,
          preview_result: null,
          preview_error: null,
          warnings: [],
        })
      }
    }

    // Simple expression evaluation simulation with mock data
    const sampleContext = {
      severity: 'high',
      issue_count: 5,
      status: 'failure',
      pass_rate: 0.85,
      tags: ['production', 'orders'],
      metadata: { environment: 'production', table: 'orders' },
      checkpoint_name: 'sample_validation',
      action_type: 'check',
      issues: ['null_values', 'duplicates'],
    }

    // Simulate preview result based on simple patterns
    let previewResult: boolean | null = null
    let previewError: string | null = null

    try {
      // Simple pattern matching for common expressions
      if (expression.includes("severity == 'critical'")) {
        previewResult = sampleContext.severity === 'critical'
      } else if (expression.includes("severity == 'high'")) {
        previewResult = sampleContext.severity === 'high'
      } else if (expression.includes("pass_rate <")) {
        const match = expression.match(/pass_rate\s*<\s*(\d+\.?\d*)/)
        if (match) {
          previewResult = sampleContext.pass_rate < parseFloat(match[1])
        }
      } else if (expression.includes("issue_count >")) {
        const match = expression.match(/issue_count\s*>\s*(\d+)/)
        if (match) {
          previewResult = sampleContext.issue_count > parseInt(match[1])
        }
      } else if (expression.includes("'production' in tags")) {
        previewResult = sampleContext.tags.includes('production')
      } else if (expression.includes("status == 'failure'")) {
        previewResult = sampleContext.status === 'failure'
      } else {
        // Default: assume valid expression evaluates to true for demo
        previewResult = true
      }
    } catch (e) {
      previewError = e instanceof Error ? e.message : 'Evaluation error'
    }

    // Generate warnings
    const warnings: string[] = []
    if (expression.includes('metadata[') && !expression.includes('.get(')) {
      warnings.push(
        "Consider using metadata.get('key') instead of metadata['key'] to handle missing keys gracefully"
      )
    }
    if (expression.length > 500) {
      warnings.push('Expression is quite long. Consider breaking it into multiple rules.')
    }

    return HttpResponse.json({
      valid: true,
      error: null,
      error_line: null,
      preview_result: previewResult,
      preview_error: previewError,
      warnings,
    })
  }),

  // Validate Jinja2 template
  http.post(`${API_BASE}/notifications/routing/rules/validate-jinja2`, async ({ request }) => {
    await delay(150)

    const body = (await request.json()) as {
      template?: string
      sample_data?: Record<string, unknown>
      expected_result?: string
    }

    const { template, sample_data, expected_result } = body

    // Validate empty template
    if (!template || template.trim() === '') {
      return HttpResponse.json({
        valid: false,
        error: 'Template cannot be empty',
        error_line: null,
        rendered_output: null,
      })
    }

    // Check for basic Jinja2 syntax errors
    const openBraces = (template.match(/\{\{/g) || []).length
    const closeBraces = (template.match(/\}\}/g) || []).length
    if (openBraces !== closeBraces) {
      return HttpResponse.json({
        valid: false,
        error: 'Unbalanced template braces: {{ and }} must be paired',
        error_line: 1,
        rendered_output: null,
      })
    }

    const openBlocks = (template.match(/\{%/g) || []).length
    const closeBlocks = (template.match(/%\}/g) || []).length
    if (openBlocks !== closeBlocks) {
      return HttpResponse.json({
        valid: false,
        error: 'Unbalanced block tags: {% and %} must be paired',
        error_line: 1,
        rendered_output: null,
      })
    }

    // Simulate rendering with sample data
    let renderedOutput: string | null = null
    let matchesExpected = false

    if (sample_data) {
      try {
        // Simple variable replacement simulation
        renderedOutput = template.replace(/\{\{\s*(\w+(?:\.\w+)*)\s*\}\}/g, (match, varPath) => {
          const parts = varPath.split('.')
          let value: unknown = sample_data
          for (const part of parts) {
            if (value && typeof value === 'object' && part in value) {
              value = (value as Record<string, unknown>)[part]
            } else {
              return match
            }
          }
          if (typeof value === 'object') {
            return JSON.stringify(value)
          }
          return String(value)
        })

        // Simple boolean expression evaluation
        if (
          renderedOutput.includes('==') ||
          renderedOutput.includes('!=') ||
          renderedOutput.includes('<') ||
          renderedOutput.includes('>')
        ) {
          const boolMatch = renderedOutput.match(/^\{\{\s*(.+)\s*\}\}$/)
          if (boolMatch) {
            try {
              const expr = boolMatch[1]
                .replace(/==/g, '===')
                .replace(/!=/g, '!==')
                .replace(/\band\b/gi, '&&')
                .replace(/\bor\b/gi, '||')
                .replace(/\bnot\b/gi, '!')
                .replace(/\bTrue\b/gi, 'true')
                .replace(/\bFalse\b/gi, 'false')

              // eslint-disable-next-line no-new-func
              const evalResult = new Function(...Object.keys(sample_data), `return ${expr}`)(
                ...Object.values(sample_data)
              )
              renderedOutput = String(evalResult)
            } catch {
              // Keep original on eval error
            }
          }
        }

        // Check if output matches expected result
        if (expected_result) {
          const renderedLower = renderedOutput.toLowerCase().trim()
          const expectedLower = expected_result.toLowerCase().trim()
          matchesExpected = renderedLower === expectedLower
        }
      } catch (e) {
        return HttpResponse.json({
          valid: true,
          error: null,
          error_line: null,
          rendered_output: null,
          render_error: e instanceof Error ? e.message : 'Rendering failed',
        })
      }
    }

    return HttpResponse.json({
      valid: true,
      error: null,
      error_line: null,
      rendered_output: renderedOutput,
      matches_expected: matchesExpected,
    })
  }),

  // ============================================================================
  // Deduplication
  // ============================================================================

  // List deduplication configs
  http.get(`${API_BASE}/notifications/deduplication/configs`, async ({ request }) => {
    await delay(200)

    const url = new URL(request.url)
    const offset = parseInt(url.searchParams.get('offset') ?? '0')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')
    const activeOnly = url.searchParams.get('active_only') === 'true'

    let configs = getAll(getStore().deduplicationConfigs)

    if (activeOnly) {
      configs = configs.filter((c) => c.is_active)
    }

    const total = configs.length
    const paginated = configs.slice(offset, offset + limit)

    return HttpResponse.json({
      items: paginated,
      total,
      offset,
      limit,
    })
  }),

  // Get deduplication config by ID
  http.get(`${API_BASE}/notifications/deduplication/configs/:id`, async ({ params }) => {
    await delay(150)

    const config = getById(getStore().deduplicationConfigs, params.id as string)

    if (!config) {
      return HttpResponse.json(
        { detail: 'Deduplication config not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(config)
  }),

  // Create deduplication config
  http.post(`${API_BASE}/notifications/deduplication/configs`, async ({ request }) => {
    await delay(300)

    let body: Partial<DeduplicationConfig>

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const config = createDeduplicationConfig({
      id: createId(),
      name: body.name,
      strategy: body.strategy,
      policy: body.policy,
      windowSeconds: body.window_seconds,
      isActive: body.is_active,
    })

    config.created_at = new Date().toISOString()
    config.updated_at = new Date().toISOString()

    create(getStore().deduplicationConfigs, config)

    return HttpResponse.json(config)
  }),

  // Update deduplication config
  http.put(`${API_BASE}/notifications/deduplication/configs/:id`, async ({ params, request }) => {
    await delay(250)

    let body: Partial<DeduplicationConfig>

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const updated = update(
      getStore().deduplicationConfigs,
      params.id as string,
      { ...body, updated_at: new Date().toISOString() }
    )

    if (!updated) {
      return HttpResponse.json(
        { detail: 'Deduplication config not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(updated)
  }),

  // Delete deduplication config
  http.delete(`${API_BASE}/notifications/deduplication/configs/:id`, async ({ params }) => {
    await delay(200)

    const deleted = remove(getStore().deduplicationConfigs, params.id as string)

    if (!deleted) {
      return HttpResponse.json(
        { detail: 'Deduplication config not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json({ success: true, message: 'Deduplication config deleted' })
  }),

  // Get deduplication stats
  http.get(`${API_BASE}/notifications/deduplication/stats`, async () => {
    await delay(150)

    return HttpResponse.json(createDeduplicationStats())
  }),

  // ============================================================================
  // Throttling
  // ============================================================================

  // List throttling configs
  http.get(`${API_BASE}/notifications/throttling/configs`, async ({ request }) => {
    await delay(200)

    const url = new URL(request.url)
    const offset = parseInt(url.searchParams.get('offset') ?? '0')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')
    const activeOnly = url.searchParams.get('active_only') === 'true'
    const channelId = url.searchParams.get('channel_id')

    let configs = getAll(getStore().throttlingConfigs)

    if (activeOnly) {
      configs = configs.filter((c) => c.is_active)
    }

    if (channelId) {
      configs = configs.filter((c) => c.channel_id === channelId)
    }

    const total = configs.length
    const paginated = configs.slice(offset, offset + limit)

    return HttpResponse.json({
      items: paginated,
      total,
      offset,
      limit,
    })
  }),

  // Get throttling config by ID
  http.get(`${API_BASE}/notifications/throttling/configs/:id`, async ({ params }) => {
    await delay(150)

    const config = getById(getStore().throttlingConfigs, params.id as string)

    if (!config) {
      return HttpResponse.json(
        { detail: 'Throttling config not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(config)
  }),

  // Create throttling config
  http.post(`${API_BASE}/notifications/throttling/configs`, async ({ request }) => {
    await delay(300)

    let body: Partial<ThrottlingConfig>

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const config = createThrottlingConfig({
      id: createId(),
      name: body.name,
      perMinute: body.per_minute,
      perHour: body.per_hour,
      perDay: body.per_day,
      burstAllowance: body.burst_allowance,
      channelId: body.channel_id,
      isActive: body.is_active,
    })

    config.created_at = new Date().toISOString()
    config.updated_at = new Date().toISOString()

    create(getStore().throttlingConfigs, config)

    return HttpResponse.json(config)
  }),

  // Update throttling config
  http.put(`${API_BASE}/notifications/throttling/configs/:id`, async ({ params, request }) => {
    await delay(250)

    let body: Partial<ThrottlingConfig>

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const updated = update(
      getStore().throttlingConfigs,
      params.id as string,
      { ...body, updated_at: new Date().toISOString() }
    )

    if (!updated) {
      return HttpResponse.json(
        { detail: 'Throttling config not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(updated)
  }),

  // Delete throttling config
  http.delete(`${API_BASE}/notifications/throttling/configs/:id`, async ({ params }) => {
    await delay(200)

    const deleted = remove(getStore().throttlingConfigs, params.id as string)

    if (!deleted) {
      return HttpResponse.json(
        { detail: 'Throttling config not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json({ success: true, message: 'Throttling config deleted' })
  }),

  // Get throttling stats
  http.get(`${API_BASE}/notifications/throttling/stats`, async () => {
    await delay(150)

    return HttpResponse.json(createThrottlingStats())
  }),

  // ============================================================================
  // Escalation Policies
  // ============================================================================

  // List escalation policies
  http.get(`${API_BASE}/notifications/escalation/policies`, async ({ request }) => {
    await delay(200)

    const url = new URL(request.url)
    const offset = parseInt(url.searchParams.get('offset') ?? '0')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')
    const activeOnly = url.searchParams.get('active_only') === 'true'

    let policies = getAll(getStore().escalationPolicies)

    if (activeOnly) {
      policies = policies.filter((p) => p.is_active)
    }

    const total = policies.length
    const paginated = policies.slice(offset, offset + limit)

    return HttpResponse.json({
      items: paginated,
      total,
      offset,
      limit,
    })
  }),

  // Get escalation policy by ID
  http.get(`${API_BASE}/notifications/escalation/policies/:id`, async ({ params }) => {
    await delay(150)

    const policy = getById(getStore().escalationPolicies, params.id as string)

    if (!policy) {
      return HttpResponse.json(
        { detail: 'Escalation policy not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(policy)
  }),

  // Create escalation policy
  http.post(`${API_BASE}/notifications/escalation/policies`, async ({ request }) => {
    await delay(300)

    let body: Partial<EscalationPolicy>

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const policy = createEscalationPolicy({
      id: createId(),
      name: body.name,
      levelCount: body.levels?.length,
      isActive: body.is_active,
    })

    if (body.description) policy.description = body.description
    if (body.levels) policy.levels = body.levels
    if (body.auto_resolve_on_success !== undefined) policy.auto_resolve_on_success = body.auto_resolve_on_success
    if (body.max_escalations) policy.max_escalations = body.max_escalations

    policy.created_at = new Date().toISOString()
    policy.updated_at = new Date().toISOString()

    create(getStore().escalationPolicies, policy)

    return HttpResponse.json(policy)
  }),

  // Update escalation policy
  http.put(`${API_BASE}/notifications/escalation/policies/:id`, async ({ params, request }) => {
    await delay(250)

    let body: Partial<EscalationPolicy>

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const updated = update(
      getStore().escalationPolicies,
      params.id as string,
      { ...body, updated_at: new Date().toISOString() }
    )

    if (!updated) {
      return HttpResponse.json(
        { detail: 'Escalation policy not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(updated)
  }),

  // Delete escalation policy
  http.delete(`${API_BASE}/notifications/escalation/policies/:id`, async ({ params }) => {
    await delay(200)

    const deleted = remove(getStore().escalationPolicies, params.id as string)

    if (!deleted) {
      return HttpResponse.json(
        { detail: 'Escalation policy not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json({ success: true, message: 'Escalation policy deleted' })
  }),

  // ============================================================================
  // Escalation Incidents
  // ============================================================================

  // List escalation incidents
  http.get(`${API_BASE}/notifications/escalation/incidents`, async ({ request }) => {
    await delay(200)

    const url = new URL(request.url)
    const offset = parseInt(url.searchParams.get('offset') ?? '0')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')
    const policyId = url.searchParams.get('policy_id')
    const state = url.searchParams.get('state')

    let incidents = getAll(getStore().escalationIncidents)

    if (policyId) {
      incidents = incidents.filter((i) => i.policy_id === policyId)
    }

    if (state) {
      incidents = incidents.filter((i) => i.state === state)
    }

    // Sort by created_at descending
    incidents.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

    const total = incidents.length
    const paginated = incidents.slice(offset, offset + limit)

    return HttpResponse.json({
      items: paginated,
      total,
      offset,
      limit,
    })
  }),

  // List active incidents
  http.get(`${API_BASE}/notifications/escalation/incidents/active`, async ({ request }) => {
    await delay(200)

    const url = new URL(request.url)
    const offset = parseInt(url.searchParams.get('offset') ?? '0')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')

    const incidents = getAll(getStore().escalationIncidents)
      .filter((i) => i.state !== 'resolved')

    // Sort by created_at descending
    incidents.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

    const total = incidents.length
    const paginated = incidents.slice(offset, offset + limit)

    return HttpResponse.json({
      items: paginated,
      total,
      offset,
      limit,
    })
  }),

  // Get escalation incident by ID
  http.get(`${API_BASE}/notifications/escalation/incidents/:id`, async ({ params }) => {
    await delay(150)

    const incident = getById(getStore().escalationIncidents, params.id as string)

    if (!incident) {
      return HttpResponse.json(
        { detail: 'Escalation incident not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(incident)
  }),

  // Acknowledge incident
  http.post(`${API_BASE}/notifications/escalation/incidents/:id/acknowledge`, async ({ params, request }) => {
    await delay(300)

    let body: { actor: string; message?: string }

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const incident = getById(getStore().escalationIncidents, params.id as string)

    if (!incident) {
      return HttpResponse.json(
        { detail: 'Escalation incident not found' },
        { status: 404 }
      )
    }

    if (incident.state === 'resolved') {
      return HttpResponse.json(
        { detail: 'Cannot acknowledge resolved incident' },
        { status: 400 }
      )
    }

    if (incident.state === 'acknowledged') {
      return HttpResponse.json(
        { detail: 'Incident already acknowledged' },
        { status: 400 }
      )
    }

    const oldState = incident.state
    const now = new Date().toISOString()

    incident.state = 'acknowledged'
    incident.acknowledged_by = body.actor
    incident.acknowledged_at = now
    incident.updated_at = now
    incident.events.push({
      from_state: oldState,
      to_state: 'acknowledged',
      actor: body.actor,
      message: body.message ?? `Acknowledged by ${body.actor}`,
      timestamp: now,
    })

    update(getStore().escalationIncidents, incident.id, incident)

    return HttpResponse.json(incident)
  }),

  // Resolve incident
  http.post(`${API_BASE}/notifications/escalation/incidents/:id/resolve`, async ({ params, request }) => {
    await delay(300)

    let body: { actor?: string; message?: string }

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const incident = getById(getStore().escalationIncidents, params.id as string)

    if (!incident) {
      return HttpResponse.json(
        { detail: 'Escalation incident not found' },
        { status: 404 }
      )
    }

    if (incident.state === 'resolved') {
      return HttpResponse.json(
        { detail: 'Incident already resolved' },
        { status: 400 }
      )
    }

    const oldState = incident.state
    const now = new Date().toISOString()
    const actor = body.actor ?? 'system'

    incident.state = 'resolved'
    incident.resolved_by = body.actor ?? null
    incident.resolved_at = now
    incident.next_escalation_at = null
    incident.updated_at = now
    incident.events.push({
      from_state: oldState,
      to_state: 'resolved',
      actor: body.actor ?? null,
      message: body.message ?? `Resolved by ${actor}`,
      timestamp: now,
    })

    update(getStore().escalationIncidents, incident.id, incident)

    return HttpResponse.json(incident)
  }),

  // Get escalation stats
  http.get(`${API_BASE}/notifications/escalation/stats`, async () => {
    await delay(150)

    const policies = getAll(getStore().escalationPolicies)

    return HttpResponse.json(createEscalationStats(policies.length))
  }),

  // ============================================================================
  // Config Import/Export
  // ============================================================================

  // Export notification config
  http.get(`${API_BASE}/notifications/config/export`, async ({ request }) => {
    await delay(300)

    const url = new URL(request.url)
    const includeRoutingRules = url.searchParams.get('include_routing_rules') !== 'false'
    const includeDeduplication = url.searchParams.get('include_deduplication') !== 'false'
    const includeThrottling = url.searchParams.get('include_throttling') !== 'false'
    const includeEscalation = url.searchParams.get('include_escalation') !== 'false'

    const bundle: {
      version: string
      exported_at: string
      routing_rules: RoutingRule[]
      deduplication_configs: DeduplicationConfig[]
      throttling_configs: ThrottlingConfig[]
      escalation_policies: EscalationPolicy[]
    } = {
      version: '1.0',
      exported_at: new Date().toISOString(),
      routing_rules: [],
      deduplication_configs: [],
      throttling_configs: [],
      escalation_policies: [],
    }

    if (includeRoutingRules) {
      bundle.routing_rules = getAll(getStore().routingRules)
    }

    if (includeDeduplication) {
      bundle.deduplication_configs = getAll(getStore().deduplicationConfigs)
    }

    if (includeThrottling) {
      bundle.throttling_configs = getAll(getStore().throttlingConfigs)
    }

    if (includeEscalation) {
      bundle.escalation_policies = getAll(getStore().escalationPolicies)
    }

    return HttpResponse.json(bundle)
  }),

  // Preview import
  http.post(`${API_BASE}/notifications/config/import/preview`, async ({ request }) => {
    await delay(400)

    interface ImportBundle {
      routing_rules?: RoutingRule[]
      deduplication_configs?: DeduplicationConfig[]
      throttling_configs?: ThrottlingConfig[]
      escalation_policies?: EscalationPolicy[]
    }

    let bundle: ImportBundle

    try {
      bundle = await request.json() as ImportBundle
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const conflicts: Array<{
      config_type: string
      config_id: string
      config_name: string
      existing_name: string
      suggested_action: string
    }> = []

    // Check routing rules for conflicts
    for (const rule of bundle.routing_rules || []) {
      const existing = getById(getStore().routingRules, rule.id)
      if (existing) {
        conflicts.push({
          config_type: 'routing_rule',
          config_id: rule.id,
          config_name: rule.name,
          existing_name: existing.name,
          suggested_action: 'skip',
        })
      }
    }

    // Check deduplication configs for conflicts
    for (const config of bundle.deduplication_configs || []) {
      const existing = getById(getStore().deduplicationConfigs, config.id)
      if (existing) {
        conflicts.push({
          config_type: 'deduplication',
          config_id: config.id,
          config_name: config.name,
          existing_name: existing.name,
          suggested_action: 'skip',
        })
      }
    }

    // Check throttling configs for conflicts
    for (const config of bundle.throttling_configs || []) {
      const existing = getById(getStore().throttlingConfigs, config.id)
      if (existing) {
        conflicts.push({
          config_type: 'throttling',
          config_id: config.id,
          config_name: config.name,
          existing_name: existing.name,
          suggested_action: 'skip',
        })
      }
    }

    // Check escalation policies for conflicts
    for (const policy of bundle.escalation_policies || []) {
      const existing = getById(getStore().escalationPolicies, policy.id)
      if (existing) {
        conflicts.push({
          config_type: 'escalation',
          config_id: policy.id,
          config_name: policy.name,
          existing_name: existing.name,
          suggested_action: 'skip',
        })
      }
    }

    const totalConfigs =
      (bundle.routing_rules?.length || 0) +
      (bundle.deduplication_configs?.length || 0) +
      (bundle.throttling_configs?.length || 0) +
      (bundle.escalation_policies?.length || 0)

    return HttpResponse.json({
      total_configs: totalConfigs,
      new_configs: totalConfigs - conflicts.length,
      conflicts,
      routing_rules_count: bundle.routing_rules?.length || 0,
      deduplication_configs_count: bundle.deduplication_configs?.length || 0,
      throttling_configs_count: bundle.throttling_configs?.length || 0,
      escalation_policies_count: bundle.escalation_policies?.length || 0,
    })
  }),

  // Import notification config
  http.post(`${API_BASE}/notifications/config/import`, async ({ request }) => {
    await delay(500)

    interface ImportRequest {
      bundle: {
        routing_rules?: RoutingRule[]
        deduplication_configs?: DeduplicationConfig[]
        throttling_configs?: ThrottlingConfig[]
        escalation_policies?: EscalationPolicy[]
      }
      conflict_resolution: 'skip' | 'overwrite' | 'rename'
    }

    let body: ImportRequest

    try {
      body = await request.json() as ImportRequest
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const { bundle, conflict_resolution } = body
    let createdCount = 0
    let skippedCount = 0
    let overwrittenCount = 0
    const errors: string[] = []
    const createdIds: Record<string, string[]> = {
      routing_rules: [],
      deduplication_configs: [],
      throttling_configs: [],
      escalation_policies: [],
    }

    // Import routing rules
    for (const rule of bundle.routing_rules || []) {
      const existing = getById(getStore().routingRules, rule.id)
      if (existing) {
        if (conflict_resolution === 'skip') {
          skippedCount++
        } else if (conflict_resolution === 'overwrite') {
          update(getStore().routingRules, rule.id, {
            ...rule,
            updated_at: new Date().toISOString(),
          })
          overwrittenCount++
          createdIds.routing_rules.push(rule.id)
        } else {
          // rename
          const newId = createId()
          const newRule = {
            ...rule,
            id: newId,
            name: `${rule.name} (imported)`,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }
          create(getStore().routingRules, newRule)
          createdCount++
          createdIds.routing_rules.push(newId)
        }
      } else {
        const newRule = {
          ...rule,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }
        create(getStore().routingRules, newRule)
        createdCount++
        createdIds.routing_rules.push(rule.id)
      }
    }

    // Import deduplication configs
    for (const config of bundle.deduplication_configs || []) {
      const existing = getById(getStore().deduplicationConfigs, config.id)
      if (existing) {
        if (conflict_resolution === 'skip') {
          skippedCount++
        } else if (conflict_resolution === 'overwrite') {
          update(getStore().deduplicationConfigs, config.id, {
            ...config,
            updated_at: new Date().toISOString(),
          })
          overwrittenCount++
          createdIds.deduplication_configs.push(config.id)
        } else {
          const newId = createId()
          const newConfig = {
            ...config,
            id: newId,
            name: `${config.name} (imported)`,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }
          create(getStore().deduplicationConfigs, newConfig)
          createdCount++
          createdIds.deduplication_configs.push(newId)
        }
      } else {
        const newConfig = {
          ...config,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }
        create(getStore().deduplicationConfigs, newConfig)
        createdCount++
        createdIds.deduplication_configs.push(config.id)
      }
    }

    // Import throttling configs
    for (const config of bundle.throttling_configs || []) {
      const existing = getById(getStore().throttlingConfigs, config.id)
      if (existing) {
        if (conflict_resolution === 'skip') {
          skippedCount++
        } else if (conflict_resolution === 'overwrite') {
          update(getStore().throttlingConfigs, config.id, {
            ...config,
            updated_at: new Date().toISOString(),
          })
          overwrittenCount++
          createdIds.throttling_configs.push(config.id)
        } else {
          const newId = createId()
          const newConfig = {
            ...config,
            id: newId,
            name: `${config.name} (imported)`,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }
          create(getStore().throttlingConfigs, newConfig)
          createdCount++
          createdIds.throttling_configs.push(newId)
        }
      } else {
        const newConfig = {
          ...config,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }
        create(getStore().throttlingConfigs, newConfig)
        createdCount++
        createdIds.throttling_configs.push(config.id)
      }
    }

    // Import escalation policies
    for (const policy of bundle.escalation_policies || []) {
      const existing = getById(getStore().escalationPolicies, policy.id)
      if (existing) {
        if (conflict_resolution === 'skip') {
          skippedCount++
        } else if (conflict_resolution === 'overwrite') {
          update(getStore().escalationPolicies, policy.id, {
            ...policy,
            updated_at: new Date().toISOString(),
          })
          overwrittenCount++
          createdIds.escalation_policies.push(policy.id)
        } else {
          const newId = createId()
          const newPolicy = {
            ...policy,
            id: newId,
            name: `${policy.name} (imported)`,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }
          create(getStore().escalationPolicies, newPolicy)
          createdCount++
          createdIds.escalation_policies.push(newId)
        }
      } else {
        const newPolicy = {
          ...policy,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }
        create(getStore().escalationPolicies, newPolicy)
        createdCount++
        createdIds.escalation_policies.push(policy.id)
      }
    }

    return HttpResponse.json({
      success: errors.length === 0,
      message: `Import completed: ${createdCount} created, ${skippedCount} skipped, ${overwrittenCount} overwritten`,
      created_count: createdCount,
      skipped_count: skippedCount,
      overwritten_count: overwrittenCount,
      errors,
      created_ids: createdIds,
    })
  }),
]
