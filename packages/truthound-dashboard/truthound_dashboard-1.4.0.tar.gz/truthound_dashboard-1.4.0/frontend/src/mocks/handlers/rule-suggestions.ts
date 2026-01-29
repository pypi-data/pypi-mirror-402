/**
 * Rule Suggestions API handlers
 *
 * Supports:
 * - Strictness levels (loose, medium, strict)
 * - Presets (default, strict, loose, minimal, comprehensive, ci_cd, schema_only, format_only)
 * - Category filtering
 * - Multiple export formats (yaml, json, python, toml)
 */

import { http, HttpResponse, delay } from 'msw'
import { getStore, getById, getSchemaBySourceId } from '../data/store'
import {
  createRuleSuggestionResponse,
  createApplyRulesResponse,
  createContextualSuggestions,
  createCrossColumnSuggestions,
  type SuggestedRule,
  type CrossColumnRuleSuggestion,
  type StrictnessLevel,
  type RuleCategory,
} from '../factories'

const API_BASE = '/api/v1'

// Store for generated suggestions (to support apply)
const suggestionsStore = new Map<string, SuggestedRule[]>()
const crossColumnSuggestionsStore = new Map<string, CrossColumnRuleSuggestion[]>()

// Preset definitions
const PRESET_DEFINITIONS = {
  default: {
    name: 'default',
    display_name: 'Default',
    description: 'General purpose validation rules. Balanced coverage and thresholds.',
    strictness: 'medium',
    categories: ['schema', 'completeness', 'uniqueness', 'stats'],
    recommended_for: 'Most data validation scenarios',
  },
  strict: {
    name: 'strict',
    display_name: 'Strict',
    description: 'Tight thresholds for production data. High confidence rules only.',
    strictness: 'strict',
    categories: ['schema', 'completeness', 'uniqueness', 'stats', 'pattern'],
    recommended_for: 'Production data pipelines, data quality gates',
  },
  loose: {
    name: 'loose',
    display_name: 'Loose',
    description: 'Permissive thresholds for development/testing.',
    strictness: 'loose',
    categories: ['schema', 'completeness'],
    recommended_for: 'Development, testing, exploratory analysis',
  },
  minimal: {
    name: 'minimal',
    display_name: 'Minimal',
    description: 'Essential rules only. Focus on critical data integrity.',
    strictness: 'medium',
    categories: ['schema', 'completeness'],
    recommended_for: 'Quick validation, minimal overhead',
  },
  comprehensive: {
    name: 'comprehensive',
    display_name: 'Comprehensive',
    description: 'All available rules. Maximum validation coverage.',
    strictness: 'medium',
    categories: ['schema', 'completeness', 'uniqueness', 'stats', 'pattern', 'distribution'],
    recommended_for: 'Full data audit, compliance checks',
  },
  ci_cd: {
    name: 'ci_cd',
    display_name: 'CI/CD',
    description: 'Optimized for continuous integration. Fast execution, clear failures.',
    strictness: 'strict',
    categories: ['schema', 'completeness', 'uniqueness'],
    recommended_for: 'CI/CD pipelines, automated testing',
  },
  schema_only: {
    name: 'schema_only',
    display_name: 'Schema Only',
    description: 'Structure validation only. No statistical checks.',
    strictness: 'medium',
    categories: ['schema'],
    recommended_for: 'Schema drift detection, structure validation',
  },
  format_only: {
    name: 'format_only',
    display_name: 'Format Only',
    description: 'Format and pattern rules only.',
    strictness: 'medium',
    categories: ['pattern'],
    recommended_for: 'Data format validation, PII detection',
  },
}

// Strictness thresholds
const STRICTNESS_THRESHOLDS = {
  loose: { min_confidence: 0.3 },
  medium: { min_confidence: 0.5 },
  strict: { min_confidence: 0.7 },
}

export const ruleSuggestionsHandlers = [
  // Get available presets
  http.get(`${API_BASE}/rule-suggestions/presets`, async () => {
    await delay(100)

    return HttpResponse.json({
      presets: Object.values(PRESET_DEFINITIONS),
      strictness_levels: ['loose', 'medium', 'strict'],
      categories: ['schema', 'stats', 'pattern', 'completeness', 'uniqueness', 'distribution'],
      export_formats: ['yaml', 'json', 'python', 'toml'],
    })
  }),

  // Generate rule suggestions for a source
  http.post(`${API_BASE}/sources/:sourceId/rules/suggest`, async ({ params, request }) => {
    await delay(1000) // Simulate analysis time

    const sourceId = params.sourceId as string
    const source = getById(getStore().sources, sourceId)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    // Parse request body for options
    interface SuggestRequest {
      profile_id?: string
      min_confidence?: number
      strictness?: 'loose' | 'medium' | 'strict'
      preset?: string
      include_categories?: string[]
      exclude_categories?: string[]
      enable_cross_column?: boolean
      include_cross_column_types?: string[]
      exclude_cross_column_types?: string[]
    }

    let suggestOptions: SuggestRequest = {}
    try {
      const body = await request.json()
      suggestOptions = body as SuggestRequest
    } catch {
      // Empty body is fine, use defaults
    }

    const enableCrossColumn = suggestOptions.enable_cross_column !== false // default true

    // Apply preset if specified
    const preset = suggestOptions.preset
      ? PRESET_DEFINITIONS[suggestOptions.preset as keyof typeof PRESET_DEFINITIONS]
      : null
    const strictness = preset?.strictness || suggestOptions.strictness || 'medium'
    const includeCategories = preset?.categories || suggestOptions.include_categories

    // Determine min_confidence based on strictness
    const thresholds = STRICTNESS_THRESHOLDS[strictness as keyof typeof STRICTNESS_THRESHOLDS]
    const minConfidence = Math.max(
      suggestOptions.min_confidence || 0,
      thresholds?.min_confidence || 0.5
    )

    // Get schema if available for contextual suggestions
    const schema = getSchemaBySourceId(sourceId)
    let suggestions: SuggestedRule[]

    if (schema?.schema_json?.columns) {
      // Generate contextual suggestions based on schema
      const columns = Object.entries(schema.schema_json.columns).map(([name, col]: [string, unknown]) => ({
        name,
        dtype: (col as { dtype?: string }).dtype || 'object',
      }))

      suggestions = createContextualSuggestions(columns)
    } else {
      // Generate generic suggestions
      const genericResponse = createRuleSuggestionResponse(sourceId, source.name, {
        profileId: suggestOptions.profile_id,
      })
      suggestions = genericResponse.suggestions
    }

    // Filter by category if specified
    if (includeCategories && includeCategories.length > 0) {
      suggestions = suggestions.filter((s) =>
        includeCategories.includes(s.category || 'schema')
      )
    }
    if (suggestOptions.exclude_categories && suggestOptions.exclude_categories.length > 0) {
      suggestions = suggestions.filter(
        (s) => !suggestOptions.exclude_categories!.includes(s.category || 'schema')
      )
    }

    // Filter by min_confidence
    suggestions = suggestions.filter((s) => s.confidence >= minConfidence)

    // Count by category
    const byCategory: Record<string, number> = {}
    suggestions.forEach((s) => {
      const cat = s.category || 'schema'
      byCategory[cat] = (byCategory[cat] || 0) + 1
    })

    // Generate cross-column suggestions if enabled
    let crossColumnSuggestions: CrossColumnRuleSuggestion[] = []
    const byCrossColumnType: Record<string, number> = {}

    if (enableCrossColumn) {
      crossColumnSuggestions = createCrossColumnSuggestions(
        5,
        strictness as StrictnessLevel
      ).filter((s) => s.confidence >= minConfidence)

      // Filter by cross-column types if specified
      if (suggestOptions.include_cross_column_types && suggestOptions.include_cross_column_types.length > 0) {
        crossColumnSuggestions = crossColumnSuggestions.filter((s) =>
          suggestOptions.include_cross_column_types!.includes(s.rule_type)
        )
      }
      if (suggestOptions.exclude_cross_column_types && suggestOptions.exclude_cross_column_types.length > 0) {
        crossColumnSuggestions = crossColumnSuggestions.filter(
          (s) => !suggestOptions.exclude_cross_column_types!.includes(s.rule_type)
        )
      }

      // Count by cross-column type
      crossColumnSuggestions.forEach((s) => {
        byCrossColumnType[s.rule_type] = (byCrossColumnType[s.rule_type] || 0) + 1
      })

      // Add relationship/multi_column categories to byCategory
      const relationshipCount = crossColumnSuggestions.filter((s) =>
        ['column_comparison', 'column_dependency', 'column_implication'].includes(s.rule_type)
      ).length
      const multiColumnCount = crossColumnSuggestions.filter((s) =>
        ['composite_key', 'column_sum', 'column_coexistence', 'column_mutual_exclusivity', 'column_ratio'].includes(s.rule_type)
      ).length

      if (relationshipCount > 0) byCategory['relationship'] = relationshipCount
      if (multiColumnCount > 0) byCategory['multi_column'] = multiColumnCount
    }

    const totalSuggestions = suggestions.length + crossColumnSuggestions.length
    const highConfidenceCount =
      suggestions.filter((s) => s.confidence >= 0.8).length +
      crossColumnSuggestions.filter((s) => s.confidence >= 0.8).length

    const categoriesIncluded = [...new Set(suggestions.map((s) => s.category || 'schema'))]
    if (crossColumnSuggestions.length > 0) {
      if (!categoriesIncluded.includes('relationship')) categoriesIncluded.push('relationship')
      if (!categoriesIncluded.includes('multi_column')) categoriesIncluded.push('multi_column')
    }

    const response = {
      source_id: sourceId,
      source_name: source.name,
      profile_id: suggestOptions.profile_id || 'mock-profile-id',
      total_suggestions: totalSuggestions,
      high_confidence_count: highConfidenceCount,
      cross_column_count: crossColumnSuggestions.length,
      suggestions,
      cross_column_suggestions: crossColumnSuggestions,
      generated_at: new Date().toISOString(),
      strictness,
      preset: suggestOptions.preset || null,
      categories_included: categoriesIncluded,
      by_category: byCategory,
      by_cross_column_type: byCrossColumnType,
    }

    // Store for later apply
    suggestionsStore.set(sourceId, suggestions)
    crossColumnSuggestionsStore.set(sourceId, crossColumnSuggestions)

    return HttpResponse.json(response)
  }),

  // Apply selected rule suggestions
  http.post(`${API_BASE}/sources/:sourceId/rules/apply-suggestions`, async ({ params, request }) => {
    await delay(500)

    const sourceId = params.sourceId as string
    const source = getById(getStore().sources, sourceId)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    interface ApplyRequest {
      suggestions?: SuggestedRule[]
      rule_ids?: string[]
      create_new_rule?: boolean
      rule_name?: string
    }

    let applyRequest: ApplyRequest
    try {
      applyRequest = (await request.json()) as ApplyRequest
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid request body' },
        { status: 400 }
      )
    }

    // Get stored suggestions
    const storedSuggestions = suggestionsStore.get(sourceId) ?? []

    // Support both suggestions array and rule_ids
    let selectedRules: SuggestedRule[]
    if (applyRequest.suggestions && applyRequest.suggestions.length > 0) {
      selectedRules = applyRequest.suggestions
    } else if (applyRequest.rule_ids && applyRequest.rule_ids.length > 0) {
      selectedRules = storedSuggestions.filter((s) =>
        applyRequest.rule_ids!.includes(s.id)
      )
    } else {
      return HttpResponse.json(
        { detail: 'suggestions or rule_ids is required' },
        { status: 400 }
      )
    }

    if (selectedRules.length === 0) {
      return HttpResponse.json(
        { detail: 'No valid rules found' },
        { status: 400 }
      )
    }

    const response = createApplyRulesResponse(sourceId, selectedRules)

    return HttpResponse.json(response)
  }),

  // Get previously generated suggestions (without re-analyzing)
  http.get(`${API_BASE}/sources/:sourceId/rules/suggestions`, async ({ params }) => {
    await delay(150)

    const sourceId = params.sourceId as string
    const source = getById(getStore().sources, sourceId)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    const suggestions = suggestionsStore.get(sourceId)

    if (!suggestions) {
      return HttpResponse.json({
        source_id: sourceId,
        source_name: source.name,
        profile_id: null,
        suggestions: [],
        total_suggestions: 0,
        high_confidence_count: 0,
        generated_at: null,
      })
    }

    return HttpResponse.json({
      source_id: sourceId,
      source_name: source.name,
      profile_id: 'mock-profile-id',
      total_suggestions: suggestions.length,
      high_confidence_count: suggestions.filter((s) => s.confidence >= 0.8).length,
      suggestions,
      generated_at: new Date().toISOString(),
    })
  }),

  // Export rules in various formats
  http.post(`${API_BASE}/sources/:sourceId/rules/export`, async ({ params, request }) => {
    await delay(300)

    const sourceId = params.sourceId as string
    const source = getById(getStore().sources, sourceId)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    interface ExportRequest {
      suggestions: SuggestedRule[]
      format?: 'yaml' | 'json' | 'python' | 'toml'
      rule_name?: string
      description?: string
      include_metadata?: boolean
    }

    let exportRequest: ExportRequest
    try {
      exportRequest = (await request.json()) as ExportRequest
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid request body' },
        { status: 400 }
      )
    }

    if (!exportRequest.suggestions || exportRequest.suggestions.length === 0) {
      return HttpResponse.json(
        { detail: 'No suggestions provided to export' },
        { status: 400 }
      )
    }

    const format = exportRequest.format || 'yaml'
    const ruleName = exportRequest.rule_name || 'auto_generated_rules'
    const description = exportRequest.description || `Auto-generated rules (${exportRequest.suggestions.length} validators)`
    const includeMetadata = exportRequest.include_metadata !== false

    // Build rules dict
    const rulesDict: Record<string, Record<string, unknown>> = { columns: {} }
    const validators: string[] = []

    exportRequest.suggestions.forEach((s) => {
      if (!rulesDict.columns[s.column]) {
        rulesDict.columns[s.column] = {}
      }
      const colRules = rulesDict.columns[s.column] as Record<string, unknown>
      colRules[s.validator_name.toLowerCase()] = s.params && Object.keys(s.params).length > 0 ? s.params : true
      validators.push(s.validator_name)
    })

    if (includeMetadata) {
      (rulesDict as Record<string, unknown>)._metadata = {
        name: ruleName,
        description,
        generated_at: new Date().toISOString(),
        rule_count: exportRequest.suggestions.length,
        validators: [...new Set(validators)],
      }
    }

    // Generate content based on format
    let content: string
    let filename: string

    switch (format) {
      case 'json':
        content = JSON.stringify(rulesDict, null, 2)
        filename = `${ruleName}.json`
        break
      case 'python':
        content = generatePythonCode(rulesDict, ruleName, description)
        filename = `${ruleName}.py`
        break
      case 'toml':
        content = generateToml(rulesDict)
        filename = `${ruleName}.toml`
        break
      case 'yaml':
      default:
        content = generateYaml(rulesDict)
        filename = `${ruleName}.yaml`
        break
    }

    return HttpResponse.json({
      content,
      format,
      filename,
      rule_count: exportRequest.suggestions.length,
      generated_at: new Date().toISOString(),
    })
  }),
]

// Helper functions for export formats
function generateYaml(rulesDict: Record<string, unknown>): string {
  const lines: string[] = []

  const metadata = rulesDict._metadata as Record<string, unknown> | undefined
  if (metadata) {
    lines.push('_metadata:')
    Object.entries(metadata).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        lines.push(`  ${key}:`)
        value.forEach((v) => lines.push(`    - ${v}`))
      } else {
        lines.push(`  ${key}: ${JSON.stringify(value)}`)
      }
    })
    lines.push('')
  }

  lines.push('columns:')
  const columns = rulesDict.columns as Record<string, Record<string, unknown>>
  Object.entries(columns).forEach(([colName, validators]) => {
    lines.push(`  ${colName}:`)
    Object.entries(validators).forEach(([valName, valConfig]) => {
      if (typeof valConfig === 'object' && valConfig !== null) {
        lines.push(`    ${valName}:`)
        Object.entries(valConfig as Record<string, unknown>).forEach(([k, v]) => {
          lines.push(`      ${k}: ${JSON.stringify(v)}`)
        })
      } else {
        lines.push(`    ${valName}: ${valConfig}`)
      }
    })
  })

  return lines.join('\n')
}

function generateToml(rulesDict: Record<string, unknown>): string {
  const lines: string[] = []

  const metadata = rulesDict._metadata as Record<string, unknown> | undefined
  if (metadata) {
    lines.push('[_metadata]')
    Object.entries(metadata).forEach(([key, value]) => {
      if (typeof value === 'string') {
        lines.push(`${key} = "${value}"`)
      } else if (Array.isArray(value)) {
        lines.push(`${key} = ${JSON.stringify(value)}`)
      } else {
        lines.push(`${key} = ${value}`)
      }
    })
    lines.push('')
  }

  const columns = rulesDict.columns as Record<string, Record<string, unknown>>
  Object.entries(columns).forEach(([colName, validators]) => {
    lines.push(`[columns."${colName}"]`)
    Object.entries(validators).forEach(([valName, valConfig]) => {
      if (typeof valConfig === 'object' && valConfig !== null) {
        Object.entries(valConfig as Record<string, unknown>).forEach(([k, v]) => {
          lines.push(`${valName}_${k} = ${typeof v === 'string' ? `"${v}"` : v}`)
        })
      } else {
        lines.push(`${valName} = ${valConfig}`)
      }
    })
    lines.push('')
  })

  return lines.join('\n')
}

function generatePythonCode(
  rulesDict: Record<string, unknown>,
  ruleName: string,
  description: string
): string {
  const safeName = ruleName.replace(/-/g, '_').replace(/\s+/g, '_')
  const lines = [
    '"""Auto-generated validation rules.',
    '',
    `Name: ${ruleName}`,
    `Description: ${description}`,
    '"""',
    '',
    'from truthound import th',
    '',
    '',
    `def validate_${safeName}(df):`,
    '    """Run auto-generated validation rules."""',
    '    result = th.check(',
    '        df,',
    '        validators=[',
  ]

  const columns = rulesDict.columns as Record<string, Record<string, unknown>>
  Object.entries(columns).forEach(([colName, validators]) => {
    Object.entries(validators).forEach(([valName, valConfig]) => {
      if (typeof valConfig === 'object' && valConfig !== null) {
        const params = Object.entries(valConfig as Record<string, unknown>)
          .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
          .join(', ')
        lines.push(`            ("${colName}", "${valName}", {${params}}),`)
      } else {
        lines.push(`            ("${colName}", "${valName}"),`)
      }
    })
  })

  lines.push(
    '        ],',
    '    )',
    '    return result',
    '',
    '',
    'if __name__ == "__main__":',
    '    import pandas as pd',
    '    # df = pd.read_csv("your_data.csv")',
    `    # result = validate_${safeName}(df)`,
    '    # print(result)',
    ''
  )

  return lines.join('\n')
}
