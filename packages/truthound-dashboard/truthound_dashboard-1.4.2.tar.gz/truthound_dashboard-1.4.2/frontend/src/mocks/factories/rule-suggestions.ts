/**
 * Rule Suggestions factory - generates suggested validation rules based on profile data
 *
 * Features:
 *   - Multiple strictness levels (loose, medium, strict)
 *   - Preset templates for different use cases
 *   - Multiple export formats (YAML, JSON, Python, TOML)
 *   - Category-based filtering
 */

import { createId, randomChoice, randomInt, faker } from './base'

// =============================================================================
// Types matching backend schemas
// =============================================================================

export type StrictnessLevel = 'loose' | 'medium' | 'strict'
export type RulePreset =
  | 'default'
  | 'strict'
  | 'loose'
  | 'minimal'
  | 'comprehensive'
  | 'ci_cd'
  | 'schema_only'
  | 'format_only'
export type RuleExportFormat = 'yaml' | 'json' | 'python' | 'toml'
export type RuleCategory =
  | 'schema'
  | 'stats'
  | 'pattern'
  | 'completeness'
  | 'uniqueness'
  | 'distribution'
  | 'relationship'
  | 'multi_column'

export type CrossColumnRuleType =
  | 'composite_key'
  | 'column_sum'
  | 'column_product'
  | 'column_difference'
  | 'column_ratio'
  | 'column_percentage'
  | 'column_comparison'
  | 'column_chain_comparison'
  | 'column_dependency'
  | 'column_implication'
  | 'column_coexistence'
  | 'column_mutual_exclusivity'
  | 'column_correlation'
  | 'referential_integrity'

export interface SuggestedRule {
  id: string
  column: string
  validator_name: string
  params: Record<string, unknown>
  confidence: number
  reason: string
  severity_suggestion: string
  category: RuleCategory | string
  is_cross_column?: boolean
  related_columns?: string[]
  cross_column_type?: CrossColumnRuleType
}

export interface CrossColumnRuleSuggestion {
  id: string
  rule_type: CrossColumnRuleType
  columns: string[]
  validator_name: string
  params: Record<string, unknown>
  confidence: number
  reason: string
  severity_suggestion: string
  evidence: Record<string, unknown>
  sample_violations: Array<Record<string, unknown>>
}

export interface RuleSuggestionResponse {
  source_id: string
  source_name: string
  profile_id: string
  total_suggestions: number
  high_confidence_count: number
  cross_column_count: number
  suggestions: SuggestedRule[]
  cross_column_suggestions: CrossColumnRuleSuggestion[]
  generated_at: string
  strictness: StrictnessLevel
  preset: RulePreset | null
  categories_included: RuleCategory[]
  by_category: Record<string, number>
  by_cross_column_type: Record<string, number>
}

export interface ApplyRulesResponse {
  source_id: string
  rule_id: string
  rule_name: string
  applied_count: number
  validators: string[]
  created_at: string
}

export interface ExportRulesResponse {
  content: string
  format: RuleExportFormat
  filename: string
  rule_count: number
  generated_at: string
}

export interface PresetInfo {
  name: RulePreset
  display_name: string
  description: string
  strictness: StrictnessLevel
  categories: RuleCategory[]
  recommended_for: string
}

export interface PresetsResponse {
  presets: PresetInfo[]
  strictness_levels: StrictnessLevel[]
  categories: RuleCategory[]
  export_formats: RuleExportFormat[]
}

// =============================================================================
// Preset Definitions
// =============================================================================

export type RulePresetExtended = RulePreset | 'cross_column' | 'data_integrity'

export const PRESET_DEFINITIONS: Record<RulePresetExtended, PresetInfo> = {
  default: {
    name: 'default',
    display_name: 'Default',
    description: 'General purpose validation rules',
    strictness: 'medium',
    categories: ['schema', 'completeness', 'uniqueness', 'distribution'],
    recommended_for: 'Most use cases',
  },
  strict: {
    name: 'strict',
    display_name: 'Strict',
    description: 'Production data pipelines, data quality gates',
    strictness: 'strict',
    categories: ['schema', 'completeness', 'uniqueness', 'distribution', 'stats', 'pattern'],
    recommended_for: 'Production environments',
  },
  loose: {
    name: 'loose',
    display_name: 'Loose',
    description: 'Development, testing, exploratory analysis',
    strictness: 'loose',
    categories: ['schema', 'completeness'],
    recommended_for: 'Development and testing',
  },
  minimal: {
    name: 'minimal',
    display_name: 'Minimal',
    description: 'Essential rules only, minimal overhead',
    strictness: 'loose',
    categories: ['schema'],
    recommended_for: 'Quick validation',
  },
  comprehensive: {
    name: 'comprehensive',
    display_name: 'Comprehensive',
    description: 'Full data audit, compliance checks',
    strictness: 'strict',
    categories: ['schema', 'completeness', 'uniqueness', 'distribution', 'stats', 'pattern'],
    recommended_for: 'Data audits and compliance',
  },
  ci_cd: {
    name: 'ci_cd',
    display_name: 'CI/CD',
    description: 'Fast execution, clear failures',
    strictness: 'medium',
    categories: ['schema', 'completeness', 'uniqueness'],
    recommended_for: 'CI/CD pipelines',
  },
  schema_only: {
    name: 'schema_only',
    display_name: 'Schema Only',
    description: 'Schema drift detection, structure validation',
    strictness: 'medium',
    categories: ['schema'],
    recommended_for: 'Schema validation',
  },
  format_only: {
    name: 'format_only',
    display_name: 'Format Only',
    description: 'Data format validation, PII detection',
    strictness: 'medium',
    categories: ['pattern'],
    recommended_for: 'Format validation',
  },
  cross_column: {
    name: 'cross_column' as RulePreset,
    display_name: 'Cross-Column',
    description: 'Focus on cross-column relationships and constraints',
    strictness: 'medium',
    categories: ['relationship', 'multi_column', 'uniqueness'],
    recommended_for: 'Data integrity, referential constraints',
  },
  data_integrity: {
    name: 'data_integrity' as RulePreset,
    display_name: 'Data Integrity',
    description: 'Comprehensive data integrity including cross-column rules',
    strictness: 'strict',
    categories: ['schema', 'completeness', 'uniqueness', 'relationship', 'multi_column'],
    recommended_for: 'Database migrations, data warehouse validation',
  },
}

// Confidence thresholds by strictness
export const STRICTNESS_THRESHOLDS: Record<StrictnessLevel, number> = {
  loose: 0.5,
  medium: 0.7,
  strict: 0.85,
}

// Validator templates for rule generation
const VALIDATOR_TEMPLATES = [
  // Null rules
  {
    validator: 'NotNull',
    category: 'completeness',
    reasonTemplate: 'Column has 0% null values',
    priority: 1,
    confidenceRange: [85, 98],
    requiresColumn: true,
    params: () => ({}),
  },
  {
    validator: 'Null',
    category: 'completeness',
    reasonTemplate: 'Column has less than 1% null values',
    priority: 2,
    confidenceRange: [75, 90],
    requiresColumn: true,
    params: () => ({ mostly: faker.number.float({ min: 0.95, max: 0.99, fractionDigits: 2 }) }),
  },
  // Uniqueness rules
  {
    validator: 'Unique',
    category: 'uniqueness',
    reasonTemplate: 'Column has 100% unique values',
    priority: 1,
    confidenceRange: [90, 99],
    requiresColumn: true,
    params: () => ({}),
  },
  {
    validator: 'DistinctSet',
    category: 'uniqueness',
    reasonTemplate: 'Column has low cardinality with limited distinct values',
    priority: 2,
    confidenceRange: [70, 85],
    requiresColumn: true,
    params: () => ({
      values: faker.helpers.shuffle(['active', 'inactive', 'pending', 'completed', 'cancelled']).slice(0, randomInt(2, 5)),
    }),
  },
  // Range rules
  {
    validator: 'Range',
    category: 'distribution',
    reasonTemplate: 'Column values fall within a defined numeric range',
    priority: 2,
    confidenceRange: [75, 92],
    requiresColumn: true,
    params: () => {
      const min = faker.number.int({ min: 0, max: 100 })
      const max = faker.number.int({ min: min + 10, max: min + 1000 })
      return { min, max }
    },
  },
  {
    validator: 'Positive',
    category: 'distribution',
    reasonTemplate: 'Column contains only positive values',
    priority: 2,
    confidenceRange: [80, 95],
    requiresColumn: true,
    params: () => ({}),
  },
  // Type-specific rules
  {
    validator: 'Email',
    category: 'string',
    reasonTemplate: 'Column name suggests email format',
    priority: 1,
    confidenceRange: [85, 98],
    requiresColumn: true,
    params: () => ({}),
  },
  {
    validator: 'Phone',
    category: 'string',
    reasonTemplate: 'Column name suggests phone number format',
    priority: 2,
    confidenceRange: [70, 88],
    requiresColumn: true,
    params: () => ({}),
  },
  {
    validator: 'URL',
    category: 'string',
    reasonTemplate: 'Column name suggests URL format',
    priority: 2,
    confidenceRange: [75, 90],
    requiresColumn: true,
    params: () => ({}),
  },
  // String length rules
  {
    validator: 'StrLen',
    category: 'string',
    reasonTemplate: 'Column values have consistent string length range',
    priority: 3,
    confidenceRange: [65, 80],
    requiresColumn: true,
    params: () => ({
      min_length: faker.number.int({ min: 1, max: 5 }),
      max_length: faker.number.int({ min: 50, max: 255 }),
    }),
  },
  // Datetime rules
  {
    validator: 'DatetimeRange',
    category: 'datetime',
    reasonTemplate: 'Column contains datetime values within expected range',
    priority: 2,
    confidenceRange: [70, 85],
    requiresColumn: true,
    params: () => ({
      min_date: '2020-01-01',
      max_date: new Date().toISOString().split('T')[0],
    }),
  },
]

// Column names to assign validators to
const COLUMN_NAMES = [
  'user_id',
  'email',
  'name',
  'phone',
  'amount',
  'price',
  'status',
  'category',
  'created_at',
  'updated_at',
  'is_active',
  'description',
  'url',
  'address',
  'quantity',
]

export function createSuggestedRule(options: {
  columnName?: string
  validator?: string
  strictness?: StrictnessLevel
} = {}): SuggestedRule {
  const template = options.validator
    ? VALIDATOR_TEMPLATES.find((t) => t.validator === options.validator) || randomChoice(VALIDATOR_TEMPLATES)
    : randomChoice(VALIDATOR_TEMPLATES)

  const columnName = options.columnName || randomChoice(COLUMN_NAMES)
  const [minConf, maxConf] = template.confidenceRange

  // Adjust confidence based on strictness
  const strictness = options.strictness || 'medium'
  const threshold = STRICTNESS_THRESHOLDS[strictness]
  const adjustedMinConf = Math.max(minConf / 100, threshold)
  const adjustedMaxConf = maxConf / 100

  return {
    id: createId(),
    column: columnName,
    validator_name: template.validator,
    params: template.params(),
    confidence: faker.number.float({ min: adjustedMinConf, max: adjustedMaxConf, fractionDigits: 2 }),
    reason: template.reasonTemplate.replace('{column}', columnName),
    severity_suggestion: template.priority === 1 ? 'critical' : template.priority === 2 ? 'warning' : 'info',
    category: template.category as RuleCategory,
  }
}

export function createRuleSuggestionResponse(
  sourceId: string,
  sourceName: string,
  options: {
    suggestionCount?: number
    crossColumnCount?: number
    profileId?: string
    strictness?: StrictnessLevel
    preset?: RulePreset | null
    includeCategories?: RuleCategory[]
    excludeCategories?: RuleCategory[]
    minConfidence?: number
    enableCrossColumn?: boolean
  } = {}
): RuleSuggestionResponse {
  const suggestionCount = options.suggestionCount ?? randomInt(5, 15)
  const crossColumnCount = options.crossColumnCount ?? randomInt(3, 7)
  const profileId = options.profileId ?? createId()
  const strictness = options.strictness || 'medium'
  const preset = options.preset || null
  const minConfidence = options.minConfidence ?? STRICTNESS_THRESHOLDS[strictness]
  const enableCrossColumn = options.enableCrossColumn ?? true

  // Determine categories from preset or options
  let categories: RuleCategory[]
  if (preset && PRESET_DEFINITIONS[preset as RulePresetExtended]) {
    categories = PRESET_DEFINITIONS[preset as RulePresetExtended].categories
  } else if (options.includeCategories && options.includeCategories.length > 0) {
    categories = options.includeCategories
  } else {
    categories = ['schema', 'completeness', 'uniqueness', 'distribution', 'stats', 'pattern']
  }

  // Apply exclusions
  if (options.excludeCategories && options.excludeCategories.length > 0) {
    categories = categories.filter((c) => !options.excludeCategories!.includes(c))
  }

  // Filter templates by allowed categories
  const filteredTemplates = VALIDATOR_TEMPLATES.filter((t) =>
    categories.includes(t.category as RuleCategory)
  )

  // Generate diverse single-column suggestions
  const usedValidators = new Set<string>()
  const suggestions: SuggestedRule[] = []
  const availableColumns = faker.helpers.shuffle([...COLUMN_NAMES])

  for (let i = 0; i < suggestionCount; i++) {
    const columnName = availableColumns[i % availableColumns.length]

    const availableTemplates = filteredTemplates.filter(
      (t) => !usedValidators.has(`${t.validator}:${columnName}`)
    )

    if (availableTemplates.length > 0) {
      const template = randomChoice(availableTemplates)
      const suggestion = createSuggestedRule({
        columnName,
        validator: template.validator,
        strictness,
      })

      // Only include if above min confidence
      if (suggestion.confidence >= minConfidence) {
        suggestions.push(suggestion)
        usedValidators.add(`${template.validator}:${columnName}`)
      }
    }
  }

  // Sort by confidence descending
  suggestions.sort((a, b) => b.confidence - a.confidence)

  // Generate cross-column suggestions
  const crossColumnSuggestions: CrossColumnRuleSuggestion[] = enableCrossColumn
    ? createCrossColumnSuggestions(crossColumnCount, strictness).filter(
        (s) => s.confidence >= minConfidence
      )
    : []

  // Calculate category breakdown
  const byCategory: Record<string, number> = {}
  for (const s of suggestions) {
    byCategory[s.category] = (byCategory[s.category] || 0) + 1
  }

  // Add cross-column categories
  if (crossColumnSuggestions.length > 0) {
    const relationshipCount = crossColumnSuggestions.filter((s) =>
      ['column_comparison', 'column_dependency', 'column_implication'].includes(s.rule_type)
    ).length
    const multiColumnCount = crossColumnSuggestions.filter((s) =>
      ['composite_key', 'column_sum', 'column_coexistence', 'column_mutual_exclusivity'].includes(
        s.rule_type
      )
    ).length

    if (relationshipCount > 0) byCategory['relationship'] = relationshipCount
    if (multiColumnCount > 0) byCategory['multi_column'] = multiColumnCount
  }

  // Calculate by cross-column type breakdown
  const byCrossColumnType: Record<string, number> = {}
  for (const s of crossColumnSuggestions) {
    byCrossColumnType[s.rule_type] = (byCrossColumnType[s.rule_type] || 0) + 1
  }

  const highConfidenceCount =
    suggestions.filter((s) => s.confidence >= 0.8).length +
    crossColumnSuggestions.filter((s) => s.confidence >= 0.8).length

  // Add cross-column categories to included if present
  if (crossColumnSuggestions.length > 0) {
    if (!categories.includes('relationship')) categories.push('relationship')
    if (!categories.includes('multi_column')) categories.push('multi_column')
  }

  return {
    source_id: sourceId,
    source_name: sourceName,
    profile_id: profileId,
    total_suggestions: suggestions.length + crossColumnSuggestions.length,
    high_confidence_count: highConfidenceCount,
    cross_column_count: crossColumnSuggestions.length,
    suggestions,
    cross_column_suggestions: crossColumnSuggestions,
    generated_at: new Date().toISOString(),
    strictness,
    preset,
    categories_included: categories,
    by_category: byCategory,
    by_cross_column_type: byCrossColumnType,
  }
}

export function createApplyRulesResponse(
  sourceId: string,
  selectedRules: SuggestedRule[],
  ruleName?: string
): ApplyRulesResponse {
  return {
    source_id: sourceId,
    rule_id: createId(),
    rule_name: ruleName || `auto_generated_${Date.now()}`,
    applied_count: selectedRules.length,
    validators: selectedRules.map((r) => r.validator_name),
    created_at: new Date().toISOString(),
  }
}

/**
 * Create export response for rules
 */
export function createExportRulesResponse(
  suggestions: SuggestedRule[],
  format: RuleExportFormat,
  ruleName: string = 'auto_generated_rules',
  description?: string
): ExportRulesResponse {
  let content: string
  let filename: string

  const rules = suggestions.map((s) => ({
    column: s.column,
    validator: s.validator_name,
    params: s.params,
    severity: s.severity_suggestion,
  }))

  switch (format) {
    case 'yaml':
      content = generateYaml(rules, ruleName, description)
      filename = `${ruleName}.yaml`
      break
    case 'json':
      content = JSON.stringify({ name: ruleName, description, rules }, null, 2)
      filename = `${ruleName}.json`
      break
    case 'python':
      content = generatePythonCode(rules, ruleName, description)
      filename = `${ruleName}.py`
      break
    case 'toml':
      content = generateToml(rules, ruleName, description)
      filename = `${ruleName}.toml`
      break
    default:
      content = JSON.stringify(rules, null, 2)
      filename = `${ruleName}.txt`
  }

  return {
    content,
    format,
    filename,
    rule_count: suggestions.length,
    generated_at: new Date().toISOString(),
  }
}

/**
 * Generate YAML content for rules
 */
function generateYaml(
  rules: Array<{ column: string; validator: string; params: Record<string, unknown>; severity: string }>,
  name: string,
  description?: string
): string {
  const lines = [
    `# Auto-generated validation rules`,
    `# Generated at: ${new Date().toISOString()}`,
    ``,
    `name: ${name}`,
  ]
  if (description) {
    lines.push(`description: ${description}`)
  }
  lines.push(``, `rules:`)

  for (const rule of rules) {
    lines.push(`  - column: ${rule.column}`)
    lines.push(`    validator: ${rule.validator}`)
    lines.push(`    severity: ${rule.severity}`)
    if (Object.keys(rule.params).length > 0) {
      lines.push(`    params:`)
      for (const [key, value] of Object.entries(rule.params)) {
        const yamlValue = typeof value === 'string' ? `"${value}"` : JSON.stringify(value)
        lines.push(`      ${key}: ${yamlValue}`)
      }
    }
  }

  return lines.join('\n')
}

/**
 * Generate TOML content for rules
 */
function generateToml(
  rules: Array<{ column: string; validator: string; params: Record<string, unknown>; severity: string }>,
  name: string,
  description?: string
): string {
  const lines = [
    `# Auto-generated validation rules`,
    `# Generated at: ${new Date().toISOString()}`,
    ``,
    `[metadata]`,
    `name = "${name}"`,
  ]
  if (description) {
    lines.push(`description = "${description}"`)
  }
  lines.push(`generated_at = "${new Date().toISOString()}"`)
  lines.push(``)

  rules.forEach((rule, index) => {
    lines.push(`[[rules]]`)
    lines.push(`column = "${rule.column}"`)
    lines.push(`validator = "${rule.validator}"`)
    lines.push(`severity = "${rule.severity}"`)
    if (Object.keys(rule.params).length > 0) {
      lines.push(`[rules.params]`)
      for (const [key, value] of Object.entries(rule.params)) {
        if (typeof value === 'string') {
          lines.push(`${key} = "${value}"`)
        } else if (Array.isArray(value)) {
          lines.push(`${key} = [${value.map((v) => (typeof v === 'string' ? `"${v}"` : v)).join(', ')}]`)
        } else {
          lines.push(`${key} = ${value}`)
        }
      }
    }
    if (index < rules.length - 1) {
      lines.push(``)
    }
  })

  return lines.join('\n')
}

/**
 * Generate Python code for rules
 */
function generatePythonCode(
  rules: Array<{ column: string; validator: string; params: Record<string, unknown>; severity: string }>,
  name: string,
  description?: string
): string {
  const lines = [
    `"""`,
    `Auto-generated validation rules: ${name}`,
    description ? `\n${description}` : '',
    ``,
    `Generated at: ${new Date().toISOString()}`,
    `"""`,
    ``,
    `import truthound as th`,
    ``,
    `# Define validation rules`,
    `rules = [`,
  ]

  for (const rule of rules) {
    const params = Object.entries(rule.params)
      .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
      .join(', ')
    lines.push(`    th.${rule.validator}("${rule.column}"${params ? ', ' + params : ''}),`)
  }

  lines.push(`]`)
  lines.push(``)
  lines.push(`# Run validation`)
  lines.push(`# result = th.check(df, validators=rules)`)

  return lines.join('\n')
}

/**
 * Get available presets
 */
export function getPresetsResponse(): PresetsResponse {
  return {
    presets: Object.values(PRESET_DEFINITIONS),
    strictness_levels: ['loose', 'medium', 'strict'],
    categories: ['schema', 'stats', 'pattern', 'completeness', 'uniqueness', 'distribution', 'relationship', 'multi_column'],
    export_formats: ['yaml', 'json', 'python', 'toml'],
  }
}

// =============================================================================
// Cross-Column Rule Factories
// =============================================================================

const CROSS_COLUMN_TEMPLATES: Array<{
  rule_type: CrossColumnRuleType
  validator: string
  reasonTemplate: string
  columnsGenerator: () => string[]
  paramsGenerator: (columns: string[]) => Record<string, unknown>
  confidenceRange: [number, number]
  severity: string
}> = [
  {
    rule_type: 'composite_key',
    validator: 'MultiColumnUnique',
    reasonTemplate: 'Columns {columns} may form a composite key',
    columnsGenerator: () => [
      randomChoice(['user_id', 'customer_id', 'order_id', 'product_id']),
      randomChoice(['date', 'region', 'category', 'type']),
    ],
    paramsGenerator: (cols) => ({ columns: cols }),
    confidenceRange: [70, 90],
    severity: 'high',
  },
  {
    rule_type: 'column_comparison',
    validator: 'ColumnComparison',
    reasonTemplate: '{col_a} should be > {col_b}',
    columnsGenerator: () => [
      randomChoice(['end_date', 'updated_at', 'ship_date']),
      randomChoice(['start_date', 'created_at', 'order_date']),
    ],
    paramsGenerator: (cols) => ({
      column_a: cols[0],
      column_b: cols[1],
      operator: '>',
    }),
    confidenceRange: [80, 95],
    severity: 'high',
  },
  {
    rule_type: 'column_sum',
    validator: 'ColumnSum',
    reasonTemplate: 'Sum of {columns} should equal {target}',
    columnsGenerator: () => ['subtotal', 'tax', 'shipping'],
    paramsGenerator: (cols) => ({
      columns: cols,
      target_column: 'total',
      tolerance: 0.01,
    }),
    confidenceRange: [75, 90],
    severity: 'high',
  },
  // New: Product rule
  {
    rule_type: 'column_product',
    validator: 'ColumnProduct',
    reasonTemplate: '{col_a} × {col_b} should equal {target}',
    columnsGenerator: () => ['quantity', 'unit_price', 'line_total'],
    paramsGenerator: (cols) => ({
      columns: cols.slice(0, 2),
      target_column: cols[2] || 'total',
      tolerance: 0.01,
    }),
    confidenceRange: [75, 92],
    severity: 'high',
  },
  // New: Difference rule
  {
    rule_type: 'column_difference',
    validator: 'ColumnDifference',
    reasonTemplate: '{col_a} - {col_b} should equal {target}',
    columnsGenerator: () =>
      randomChoice([
        ['revenue', 'cost', 'profit'],
        ['gross_amount', 'deductions', 'net_amount'],
        ['end_balance', 'start_balance', 'change_amount'],
      ]),
    paramsGenerator: (cols) => ({
      minuend_column: cols[0],
      subtrahend_column: cols[1],
      result_column: cols[2],
      tolerance: 0.01,
    }),
    confidenceRange: [75, 90],
    severity: 'high',
  },
  // New: Ratio rule (updated)
  {
    rule_type: 'column_ratio',
    validator: 'ColumnRatio',
    reasonTemplate: 'Ratio of {numerator}/{denominator} should equal {target}',
    columnsGenerator: () =>
      randomChoice([
        ['profit', 'revenue', 'margin'],
        ['discount_amount', 'subtotal', 'discount_rate'],
        ['tax_amount', 'base_amount', 'tax_rate'],
      ]),
    paramsGenerator: (cols) => ({
      numerator_column: cols[0],
      denominator_column: cols[1],
      result_column: cols[2],
      tolerance: 0.01,
    }),
    confidenceRange: [70, 85],
    severity: 'medium',
  },
  // New: Percentage rule
  {
    rule_type: 'column_percentage',
    validator: 'ColumnPercentage',
    reasonTemplate: '{base} × {pct}% should equal {result}',
    columnsGenerator: () =>
      randomChoice([
        ['discount_pct', 'subtotal', 'discount_amount'],
        ['tax_pct', 'base_amount', 'tax_amount'],
        ['commission_pct', 'sales', 'commission'],
      ]),
    paramsGenerator: (cols) => ({
      percentage_column: cols[0],
      base_column: cols[1],
      result_column: cols[2],
      tolerance: 0.01,
    }),
    confidenceRange: [70, 85],
    severity: 'medium',
  },
  // New: Chain comparison rule
  {
    rule_type: 'column_chain_comparison',
    validator: 'ColumnChainComparison',
    reasonTemplate: '{columns} should follow ordering: {operator}',
    columnsGenerator: () =>
      randomChoice([
        ['created_at', 'updated_at', 'deleted_at'],
        ['ordered_at', 'shipped_at', 'delivered_at'],
        ['min_value', 'avg_value', 'max_value'],
        ['floor_price', 'price', 'ceiling_price'],
      ]),
    paramsGenerator: (cols) => ({
      columns: cols,
      operator: '<=',
    }),
    confidenceRange: [75, 90],
    severity: 'medium',
  },
  // New: Correlation rule
  {
    rule_type: 'column_correlation',
    validator: 'ColumnCorrelation',
    reasonTemplate: '{col_a} and {col_b} should be correlated',
    columnsGenerator: () =>
      randomChoice([
        ['price', 'cost'],
        ['views', 'clicks'],
        ['revenue', 'profit'],
        ['age', 'experience_years'],
        ['height', 'weight'],
      ]),
    paramsGenerator: (cols) => ({
      column_a: cols[0],
      column_b: cols[1],
      min_correlation: faker.number.float({ min: 0.3, max: 0.7, fractionDigits: 2 }),
      max_correlation: 1.0,
    }),
    confidenceRange: [65, 80],
    severity: 'medium',
  },
  {
    rule_type: 'column_coexistence',
    validator: 'ColumnCoexistence',
    reasonTemplate: 'Columns {columns} should coexist (all null or all non-null)',
    columnsGenerator: () =>
      randomChoice([
        ['latitude', 'longitude'],
        ['first_name', 'last_name'],
        ['start_date', 'end_date'],
        ['address_line1', 'city', 'postal_code'],
      ]),
    paramsGenerator: (cols) => ({ columns: cols }),
    confidenceRange: [70, 85],
    severity: 'medium',
  },
  {
    rule_type: 'column_dependency',
    validator: 'ColumnDependency',
    reasonTemplate: '{determinant} determines {dependent}',
    columnsGenerator: () =>
      randomChoice([
        ['country', 'currency'],
        ['country_code', 'currency_code'],
        ['product_id', 'product_name'],
      ]),
    paramsGenerator: (cols) => ({
      determinant_column: cols[0],
      dependent_column: cols[1],
    }),
    confidenceRange: [65, 80],
    severity: 'medium',
  },
  {
    rule_type: 'column_implication',
    validator: 'ColumnImplication',
    reasonTemplate: 'If {condition} then {consequent}',
    columnsGenerator: () =>
      randomChoice([
        ['status', 'email'],
        ['is_premium', 'subscription_tier'],
        ['is_active', 'verified_at'],
      ]),
    paramsGenerator: (cols) => ({
      determinant_column: cols[0],
      dependent_column: cols[1],
      condition_value: randomChoice(['active', 'true', 'premium']),
    }),
    confidenceRange: [65, 80],
    severity: 'medium',
  },
  {
    rule_type: 'column_mutual_exclusivity',
    validator: 'ColumnMutualExclusivity',
    reasonTemplate: 'At most one of {columns} should be non-null',
    columnsGenerator: () =>
      randomChoice([
        ['phone_home', 'phone_work', 'phone_mobile'],
        ['card_payment', 'bank_payment', 'crypto_payment'],
      ]),
    paramsGenerator: (cols) => ({ columns: cols }),
    confidenceRange: [60, 75],
    severity: 'low',
  },
  // New: Referential integrity
  {
    rule_type: 'referential_integrity',
    validator: 'ReferentialIntegrity',
    reasonTemplate: '{col_a} should reference existing values in another table',
    columnsGenerator: () =>
      randomChoice([
        ['department_id'],
        ['category_id'],
        ['user_id'],
        ['product_id'],
      ]),
    paramsGenerator: (cols) => ({
      column: cols[0],
      reference_table: `${cols[0].replace('_id', '')}s`,
      reference_column: 'id',
    }),
    confidenceRange: [70, 88],
    severity: 'high',
  },
]

export function createCrossColumnRuleSuggestion(
  options: {
    rule_type?: CrossColumnRuleType
    columns?: string[]
    strictness?: StrictnessLevel
  } = {}
): CrossColumnRuleSuggestion {
  const template = options.rule_type
    ? CROSS_COLUMN_TEMPLATES.find((t) => t.rule_type === options.rule_type) ||
      randomChoice(CROSS_COLUMN_TEMPLATES)
    : randomChoice(CROSS_COLUMN_TEMPLATES)

  const columns = options.columns || template.columnsGenerator()
  const [minConf, maxConf] = template.confidenceRange

  const strictness = options.strictness || 'medium'
  const threshold = STRICTNESS_THRESHOLDS[strictness]
  const adjustedMinConf = Math.max(minConf / 100, threshold)
  const adjustedMaxConf = maxConf / 100

  const reason = template.reasonTemplate
    .replace('{columns}', columns.join(', '))
    .replace('{col_a}', columns[0] || '')
    .replace('{col_b}', columns[1] || '')
    .replace('{target}', 'total')
    .replace('{determinant}', columns[0] || '')
    .replace('{dependent}', columns[1] || '')
    .replace('{condition}', `${columns[0]} = active`)
    .replace('{consequent}', `${columns[1]} is not null`)
    .replace('{numerator}', columns[0] || '')
    .replace('{denominator}', columns[1] || '')

  return {
    id: createId(),
    rule_type: template.rule_type,
    columns,
    validator_name: template.validator,
    params: template.paramsGenerator(columns),
    confidence: faker.number.float({ min: adjustedMinConf, max: adjustedMaxConf, fractionDigits: 2 }),
    reason,
    severity_suggestion: template.severity,
    evidence: {
      pattern: template.rule_type,
      analyzed_rows: faker.number.int({ min: 1000, max: 50000 }),
      match_rate: faker.number.float({ min: 0.9, max: 1.0, fractionDigits: 3 }),
    },
    sample_violations: faker.datatype.boolean({ probability: 0.3 })
      ? [
          {
            row_index: faker.number.int({ min: 1, max: 1000 }),
            values: Object.fromEntries(columns.map((c) => [c, faker.string.alphanumeric(8)])),
          },
        ]
      : [],
  }
}

export function createCrossColumnSuggestions(
  count: number = 5,
  strictness: StrictnessLevel = 'medium'
): CrossColumnRuleSuggestion[] {
  const suggestions: CrossColumnRuleSuggestion[] = []
  const usedTypes = new Set<string>()

  for (let i = 0; i < count; i++) {
    const availableTemplates = CROSS_COLUMN_TEMPLATES.filter(
      (t) => !usedTypes.has(t.rule_type)
    )

    if (availableTemplates.length === 0) break

    const template = randomChoice(availableTemplates)
    const suggestion = createCrossColumnRuleSuggestion({
      rule_type: template.rule_type,
      strictness,
    })

    suggestions.push(suggestion)
    usedTypes.add(template.rule_type)
  }

  // Sort by confidence descending
  suggestions.sort((a, b) => b.confidence - a.confidence)

  return suggestions
}

/**
 * Create mock profile-based rule suggestions for specific column types
 */
export function createContextualSuggestions(
  columns: Array<{ name: string; dtype: string }>,
  strictness: StrictnessLevel = 'medium'
): SuggestedRule[] {
  const suggestions: SuggestedRule[] = []

  for (const col of columns) {
    // Type-based suggestions
    if (col.dtype.includes('int') || col.dtype.includes('float')) {
      suggestions.push(createSuggestedRule({ columnName: col.name, validator: 'Range', strictness }))
      if (col.name.includes('id')) {
        suggestions.push(createSuggestedRule({ columnName: col.name, validator: 'Unique', strictness }))
      }
    }

    if (col.dtype === 'object') {
      if (col.name.toLowerCase().includes('email')) {
        suggestions.push(createSuggestedRule({ columnName: col.name, validator: 'Email', strictness }))
      }
      if (col.name.toLowerCase().includes('phone')) {
        suggestions.push(createSuggestedRule({ columnName: col.name, validator: 'Phone', strictness }))
      }
      if (col.name.toLowerCase().includes('url') || col.name.toLowerCase().includes('website')) {
        suggestions.push(createSuggestedRule({ columnName: col.name, validator: 'URL', strictness }))
      }
      if (col.name.toLowerCase().includes('status') || col.name.toLowerCase().includes('category')) {
        suggestions.push(createSuggestedRule({ columnName: col.name, validator: 'DistinctSet', strictness }))
      }
    }

    if (col.dtype.includes('datetime')) {
      suggestions.push(createSuggestedRule({ columnName: col.name, validator: 'DatetimeRange', strictness }))
    }

    // Add NotNull for most columns
    if (faker.datatype.boolean({ probability: 0.6 })) {
      suggestions.push(createSuggestedRule({ columnName: col.name, validator: 'NotNull', strictness }))
    }
  }

  return suggestions
}
