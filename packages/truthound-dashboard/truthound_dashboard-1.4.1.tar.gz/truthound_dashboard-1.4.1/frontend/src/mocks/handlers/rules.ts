/**
 * Validation Rules API handlers
 *
 * Handles source-specific validation rules CRUD operations
 */

import { http, HttpResponse, delay } from 'msw'
import { createId } from '../factories'

const API_BASE = '/api/v1'

// In-memory store for validation rules
interface ValidationRule {
  id: string
  source_id: string
  name: string
  description: string | null
  rules_yaml: string
  rules_json: Record<string, unknown> | null
  is_active: boolean
  version: string | null
  column_count: number
  created_at: string
  updated_at: string
}

const rulesStore = new Map<string, ValidationRule>()

// Default rules YAML template
const DEFAULT_RULES_YAML = `# Validation Rules
columns:
  # Example: id must be not null and unique
  # id:
  #   not_null: true
  #   unique: true
`

// Helper to count columns in YAML
function countColumnsInYaml(yaml: string): number {
  const columnsMatch = yaml.match(/columns:\s*\n([\s\S]*?)(?=\n\w|$)/i)
  if (!columnsMatch) return 0

  const columnLines = columnsMatch[1].match(/^\s{2}\w+:/gm)
  return columnLines ? columnLines.length : 0
}

// Initialize with sample rules for each source
function initializeRulesForSource(sourceId: string): ValidationRule {
  const now = new Date().toISOString()
  const rule: ValidationRule = {
    id: createId(),
    source_id: sourceId,
    name: 'Default Rules',
    description: 'Auto-generated validation rules',
    rules_yaml: DEFAULT_RULES_YAML,
    rules_json: null,
    is_active: true,
    version: '1.0.0',
    column_count: 0,
    created_at: now,
    updated_at: now,
  }
  rulesStore.set(rule.id, rule)
  return rule
}

// Get rules for a source
function getRulesForSource(sourceId: string): ValidationRule[] {
  return Array.from(rulesStore.values()).filter((r) => r.source_id === sourceId)
}

// Get active rule for a source
function getActiveRuleForSource(sourceId: string): ValidationRule | null {
  const rules = getRulesForSource(sourceId)
  return rules.find((r) => r.is_active) || null
}

export const rulesHandlers = [
  // List rules for a source
  http.get(`${API_BASE}/sources/:sourceId/rules`, async ({ params }) => {
    await delay(200)

    const sourceId = params.sourceId as string
    let rules = getRulesForSource(sourceId)

    // If no rules exist, create a default one
    if (rules.length === 0) {
      const defaultRule = initializeRulesForSource(sourceId)
      rules = [defaultRule]
    }

    return HttpResponse.json({
      success: true,
      data: rules.map((r) => ({
        id: r.id,
        source_id: r.source_id,
        name: r.name,
        description: r.description,
        is_active: r.is_active,
        version: r.version,
        column_count: r.column_count,
        created_at: r.created_at,
        updated_at: r.updated_at,
      })),
    })
  }),

  // Get active rule for a source
  http.get(`${API_BASE}/sources/:sourceId/rules/active`, async ({ params }) => {
    await delay(150)

    const sourceId = params.sourceId as string
    let activeRule = getActiveRuleForSource(sourceId)

    // If no rules exist, create a default one
    if (!activeRule) {
      activeRule = initializeRulesForSource(sourceId)
    }

    return HttpResponse.json(activeRule)
  }),

  // Create a new rule
  http.post(`${API_BASE}/sources/:sourceId/rules`, async ({ params, request }) => {
    await delay(300)

    const sourceId = params.sourceId as string
    const url = new URL(request.url)
    const activate = url.searchParams.get('activate') === 'true'

    let body: {
      name: string
      description: string | null
      rules_yaml: string
    }

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const now = new Date().toISOString()

    // If activating, deactivate all other rules for this source
    if (activate) {
      getRulesForSource(sourceId).forEach((rule) => {
        rulesStore.set(rule.id, { ...rule, is_active: false })
      })
    }

    const newRule: ValidationRule = {
      id: createId(),
      source_id: sourceId,
      name: body.name,
      description: body.description,
      rules_yaml: body.rules_yaml,
      rules_json: null,
      is_active: activate,
      version: '1.0.0',
      column_count: countColumnsInYaml(body.rules_yaml),
      created_at: now,
      updated_at: now,
    }

    rulesStore.set(newRule.id, newRule)

    return HttpResponse.json(newRule, { status: 201 })
  }),

  // Update a rule
  http.put(`${API_BASE}/rules/:ruleId`, async ({ params, request }) => {
    await delay(250)

    const ruleId = params.ruleId as string
    const existingRule = rulesStore.get(ruleId)

    if (!existingRule) {
      return HttpResponse.json(
        { detail: 'Rule not found' },
        { status: 404 }
      )
    }

    let body: Partial<{
      name: string
      description: string | null
      rules_yaml: string
    }>

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const updatedRule: ValidationRule = {
      ...existingRule,
      ...body,
      column_count: body.rules_yaml
        ? countColumnsInYaml(body.rules_yaml)
        : existingRule.column_count,
      updated_at: new Date().toISOString(),
    }

    rulesStore.set(ruleId, updatedRule)

    return HttpResponse.json(updatedRule)
  }),

  // Delete a rule
  http.delete(`${API_BASE}/rules/:ruleId`, async ({ params }) => {
    await delay(200)

    const ruleId = params.ruleId as string
    const rule = rulesStore.get(ruleId)

    if (!rule) {
      return HttpResponse.json(
        { detail: 'Rule not found' },
        { status: 404 }
      )
    }

    rulesStore.delete(ruleId)

    return HttpResponse.json({ success: true, message: 'Rule deleted successfully' })
  }),

  // Activate a rule
  http.post(`${API_BASE}/rules/:ruleId/activate`, async ({ params }) => {
    await delay(200)

    const ruleId = params.ruleId as string
    const rule = rulesStore.get(ruleId)

    if (!rule) {
      return HttpResponse.json(
        { detail: 'Rule not found' },
        { status: 404 }
      )
    }

    // Deactivate all other rules for this source
    getRulesForSource(rule.source_id).forEach((r) => {
      rulesStore.set(r.id, { ...r, is_active: false })
    })

    // Activate this rule
    const activatedRule = { ...rule, is_active: true, updated_at: new Date().toISOString() }
    rulesStore.set(ruleId, activatedRule)

    return HttpResponse.json(activatedRule)
  }),
]

// Helper to reset the rules store (for tests)
export function resetRulesStore() {
  rulesStore.clear()
}
