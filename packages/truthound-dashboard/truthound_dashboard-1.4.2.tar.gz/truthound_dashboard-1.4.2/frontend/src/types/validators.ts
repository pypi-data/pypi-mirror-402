/**
 * Validator configuration types for truthound-dashboard.
 *
 * This module provides TypeScript types matching the backend validator registry,
 * enabling type-safe configuration of individual validators with their parameters.
 */

// =============================================================================
// Enums and Constants
// =============================================================================

/**
 * Validator categories matching truthound's classification.
 */
export type ValidatorCategory =
  // Core validators (no extra dependencies)
  | 'schema'
  | 'completeness'
  | 'uniqueness'
  | 'distribution'
  // Format validators
  | 'string'
  | 'datetime'
  // Statistical validators
  | 'aggregate'
  | 'drift'
  | 'anomaly'
  // Relational validators
  | 'cross_table'
  | 'multi_column'
  | 'query'
  // Domain validators
  | 'table'
  | 'geospatial'
  | 'privacy'
  | 'business'
  // Advanced validators
  | 'time_series'
  | 'referential'
  | 'streaming'

/**
 * Category display information for UI.
 */
export interface CategoryInfo {
  value: ValidatorCategory
  label: string
  description: string
  icon?: string
  color?: string
  requires_extra?: string
  validator_count?: number
}

export const VALIDATOR_CATEGORIES: CategoryInfo[] = [
  // Core validators (no extra dependencies)
  {
    value: 'schema',
    label: 'Schema',
    description: 'Validate structure, columns, and data types',
    icon: 'layout',
    color: '#3b82f6',
  },
  {
    value: 'completeness',
    label: 'Completeness',
    description: 'Check for null values and missing data',
    icon: 'check-circle',
    color: '#22c55e',
  },
  {
    value: 'uniqueness',
    label: 'Uniqueness',
    description: 'Detect duplicates and validate keys',
    icon: 'fingerprint',
    color: '#8b5cf6',
  },
  {
    value: 'distribution',
    label: 'Distribution',
    description: 'Validate value ranges and distributions',
    icon: 'bar-chart',
    color: '#f59e0b',
  },
  // Format validators
  {
    value: 'string',
    label: 'String',
    description: 'Pattern matching and format validation',
    icon: 'type',
    color: '#06b6d4',
  },
  {
    value: 'datetime',
    label: 'Datetime',
    description: 'Date/time format and range validation',
    icon: 'calendar',
    color: '#ec4899',
  },
  // Statistical validators
  {
    value: 'aggregate',
    label: 'Aggregate',
    description: 'Statistical aggregate checks (mean, sum, etc.)',
    icon: 'calculator',
    color: '#6366f1',
  },
  {
    value: 'drift',
    label: 'Drift',
    description: 'Distribution change detection between datasets',
    icon: 'trending-up',
    color: '#ef4444',
    requires_extra: 'drift',
  },
  {
    value: 'anomaly',
    label: 'Anomaly',
    description: 'ML-based outlier and anomaly detection',
    icon: 'alert-triangle',
    color: '#f97316',
    requires_extra: 'anomaly',
  },
  // Relational validators
  {
    value: 'cross_table',
    label: 'Cross-Table',
    description: 'Multi-table relationships and foreign keys',
    icon: 'link',
    color: '#14b8a6',
  },
  {
    value: 'multi_column',
    label: 'Multi-Column',
    description: 'Column relationships and calculations',
    icon: 'columns',
    color: '#84cc16',
  },
  {
    value: 'query',
    label: 'Query',
    description: 'Expression-based custom validation',
    icon: 'code',
    color: '#a855f7',
  },
  // Domain validators
  {
    value: 'table',
    label: 'Table',
    description: 'Table metadata and structure validation',
    icon: 'table',
    color: '#0ea5e9',
  },
  {
    value: 'geospatial',
    label: 'Geospatial',
    description: 'Geographic coordinate validation',
    icon: 'map-pin',
    color: '#10b981',
  },
  {
    value: 'privacy',
    label: 'Privacy',
    description: 'PII detection and compliance (GDPR, CCPA)',
    icon: 'shield',
    color: '#dc2626',
  },
]

/**
 * Parameter types for validator configuration.
 */
export type ParameterType =
  | 'string'
  | 'string_list'
  | 'integer'
  | 'float'
  | 'boolean'
  | 'select'
  | 'multi_select'
  | 'column'
  | 'column_list'
  | 'schema'
  | 'expression'
  | 'regex'
  | 'date'
  | 'datetime'
  | 'source_ref'

/**
 * Issue severity levels.
 */
export type IssueSeverity = 'low' | 'medium' | 'high' | 'critical'

// =============================================================================
// Parameter Definition
// =============================================================================

/**
 * Option for select/multi_select parameters.
 */
export interface SelectOption {
  value: string
  label: string
}

/**
 * Definition of a validator parameter.
 */
export interface ParameterDefinition {
  /** Parameter name (matches truthound API) */
  name: string
  /** Display label for UI */
  label: string
  /** Parameter type */
  type: ParameterType
  /** Help text for the parameter */
  description?: string
  /** Whether parameter is required */
  required?: boolean
  /** Default value if not specified */
  default?: unknown
  /** Options for select/multi_select types */
  options?: SelectOption[]
  /** Minimum for numeric types */
  min_value?: number
  /** Maximum for numeric types */
  max_value?: number
  /** Placeholder text */
  placeholder?: string
  /** Regex pattern for validation */
  validation_pattern?: string
  /** Parameter name this depends on (for conditional display) */
  depends_on?: string
  /** Value the dependency must have for this param to show */
  depends_value?: unknown
  /** Parameter group for UI organization */
  group?: string
}

// =============================================================================
// Validator Definition
// =============================================================================

/**
 * Complete definition of a validator including its parameters.
 */
export interface ValidatorDefinition {
  /** Validator class name (e.g., 'ColumnExists') */
  name: string
  /** Human-readable name */
  display_name: string
  /** Validator category */
  category: ValidatorCategory
  /** What this validator checks */
  description: string
  /** Configurable parameters */
  parameters: ParameterDefinition[]
  /** Searchable tags */
  tags: string[]
  /** Default issue severity */
  severity_default: IssueSeverity
  /** Extra dependency required (e.g., 'drift', 'anomaly') */
  requires_extra?: string
  /** Whether this validator is experimental */
  experimental?: boolean
  /** Whether this validator is deprecated */
  deprecated?: boolean
  /** Message explaining deprecation and alternatives */
  deprecation_message?: string
}

// =============================================================================
// Validator Configuration
// =============================================================================

/**
 * Configuration for running a specific validator with parameters.
 */
export interface ValidatorConfig {
  /** Validator name */
  name: string
  /** Whether to run this validator */
  enabled: boolean
  /** Parameter values */
  params: Record<string, unknown>
  /** Override default severity */
  severity_override?: IssueSeverity
}

/**
 * Extended validation run options with validator configs.
 */
export interface ValidationRunOptionsExtended {
  /** Simple mode: Validator names to run */
  validators?: string[]
  /** Advanced mode: Per-validator configuration */
  validator_configs?: ValidatorConfig[]
  /** Path to schema YAML file */
  schema_path?: string
  /** Auto-learn schema */
  auto_schema?: boolean
  /** Columns to validate */
  columns?: string[]
  /** Minimum severity to report */
  min_severity?: IssueSeverity
  /** Raise exception on failure */
  strict?: boolean
  /** Use parallel execution */
  parallel?: boolean
  /** Max worker threads */
  max_workers?: number
  /** Query pushdown for SQL */
  pushdown?: boolean
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Create an empty validator config for a given definition.
 */
export function createEmptyConfig(definition: ValidatorDefinition): ValidatorConfig {
  const params: Record<string, unknown> = {}

  for (const param of definition.parameters) {
    if (param.default !== undefined) {
      params[param.name] = param.default
    } else if (param.type === 'boolean') {
      params[param.name] = false
    } else if (
      param.type === 'string_list' ||
      param.type === 'column_list' ||
      param.type === 'multi_select'
    ) {
      params[param.name] = []
    }
  }

  return {
    name: definition.name,
    enabled: true,
    params,
  }
}

/**
 * Validate a parameter value against its definition.
 */
export function validateParamValue(
  value: unknown,
  definition: ParameterDefinition
): { valid: boolean; error?: string } {
  // Check required
  if (definition.required && (value === undefined || value === null || value === '')) {
    return { valid: false, error: `${definition.label} is required` }
  }

  // Skip further validation if empty and not required
  if (value === undefined || value === null || value === '') {
    return { valid: true }
  }

  // Type-specific validation
  switch (definition.type) {
    case 'integer':
      if (!Number.isInteger(value)) {
        return { valid: false, error: `${definition.label} must be an integer` }
      }
      if (definition.min_value !== undefined && (value as number) < definition.min_value) {
        return { valid: false, error: `${definition.label} must be at least ${definition.min_value}` }
      }
      if (definition.max_value !== undefined && (value as number) > definition.max_value) {
        return { valid: false, error: `${definition.label} must be at most ${definition.max_value}` }
      }
      break

    case 'float':
      if (typeof value !== 'number') {
        return { valid: false, error: `${definition.label} must be a number` }
      }
      if (definition.min_value !== undefined && value < definition.min_value) {
        return { valid: false, error: `${definition.label} must be at least ${definition.min_value}` }
      }
      if (definition.max_value !== undefined && value > definition.max_value) {
        return { valid: false, error: `${definition.label} must be at most ${definition.max_value}` }
      }
      break

    case 'regex':
      try {
        new RegExp(value as string)
      } catch {
        return { valid: false, error: `${definition.label} is not a valid regular expression` }
      }
      break

    case 'schema':
      try {
        if (typeof value === 'string') {
          JSON.parse(value)
        }
      } catch {
        return { valid: false, error: `${definition.label} must be valid JSON` }
      }
      break
  }

  // Pattern validation
  if (definition.validation_pattern && typeof value === 'string') {
    const pattern = new RegExp(definition.validation_pattern)
    if (!pattern.test(value)) {
      return { valid: false, error: `${definition.label} format is invalid` }
    }
  }

  return { valid: true }
}

/**
 * Validate all parameters in a validator config.
 */
export function validateConfig(
  config: ValidatorConfig,
  definition: ValidatorDefinition
): { valid: boolean; errors: Record<string, string> } {
  const errors: Record<string, string> = {}

  for (const paramDef of definition.parameters) {
    // Check dependency
    if (paramDef.depends_on) {
      const depValue = config.params[paramDef.depends_on]
      if (depValue !== paramDef.depends_value) {
        continue // Skip validation if dependency not met
      }
    }

    const result = validateParamValue(config.params[paramDef.name], paramDef)
    if (!result.valid && result.error) {
      errors[paramDef.name] = result.error
    }
  }

  return {
    valid: Object.keys(errors).length === 0,
    errors,
  }
}

/**
 * Convert validator configs to simple name list (for backward compatibility).
 */
export function configsToNameList(configs: ValidatorConfig[]): string[] {
  return configs.filter((c) => c.enabled).map((c) => c.name)
}

/**
 * Check if any configs have non-default parameters.
 */
export function hasCustomParams(
  configs: ValidatorConfig[],
  definitions: ValidatorDefinition[]
): boolean {
  for (const config of configs) {
    if (!config.enabled) continue

    const def = definitions.find((d) => d.name === config.name)
    if (!def) continue

    for (const param of def.parameters) {
      const value = config.params[param.name]
      if (value !== undefined && value !== null && value !== param.default) {
        // Check if it's a non-empty array
        if (Array.isArray(value) && value.length > 0) {
          return true
        }
        // Check if it's a non-empty string
        if (typeof value === 'string' && value !== '') {
          return true
        }
        // Check numbers and booleans
        if (typeof value === 'number' || typeof value === 'boolean') {
          return true
        }
      }
    }
  }
  return false
}

/**
 * Get category info by value.
 */
export function getCategoryInfo(category: ValidatorCategory): CategoryInfo | undefined {
  return VALIDATOR_CATEGORIES.find((c) => c.value === category)
}

/**
 * Check if a validator requires extra dependencies.
 */
export function requiresExtraDependency(validator: ValidatorDefinition): boolean {
  return !!validator.requires_extra
}

/**
 * Group validators by category.
 */
export function groupValidatorsByCategory(
  validators: ValidatorDefinition[]
): Map<ValidatorCategory, ValidatorDefinition[]> {
  const grouped = new Map<ValidatorCategory, ValidatorDefinition[]>()

  for (const validator of validators) {
    const existing = grouped.get(validator.category) || []
    existing.push(validator)
    grouped.set(validator.category, existing)
  }

  return grouped
}
