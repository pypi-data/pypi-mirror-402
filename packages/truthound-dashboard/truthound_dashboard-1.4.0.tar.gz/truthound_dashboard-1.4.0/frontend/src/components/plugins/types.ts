/**
 * Plugin System Types
 * Centralized type definitions for plugin components
 */

import type {
  CustomValidator,
  CustomReporter,
  ValidatorParamDefinition,
  ReporterFieldDefinition,
  ReporterOutputFormat,
  ValidatorTestResponse,
} from '@/api/client'

// Re-export API types
export type {
  CustomValidator,
  CustomReporter,
  ValidatorParamDefinition,
  ReporterFieldDefinition,
  ReporterOutputFormat,
}

// Alias for ValidatorTestResponse
export type ValidatorTestResult = ValidatorTestResponse

/**
 * Validator parameter types supported by the editor
 */
export type ValidatorParamType =
  | 'string'
  | 'integer'
  | 'float'
  | 'boolean'
  | 'column'
  | 'column_list'
  | 'select'
  | 'multi_select'
  | 'regex'
  | 'json'

/**
 * Validator severity levels
 */
export type ValidatorSeverity = 'error' | 'warning' | 'info'

/**
 * Validator categories
 */
export type ValidatorCategory =
  | 'schema'
  | 'completeness'
  | 'uniqueness'
  | 'distribution'
  | 'string'
  | 'datetime'
  | 'custom'

/**
 * Test case definition for validators
 */
export interface ValidatorTestCase {
  name: string
  input: Record<string, unknown>
  expected_passed: boolean
  [key: string]: unknown  // Allow additional properties for API compatibility
}

/**
 * Form state for creating/editing validators
 */
export interface ValidatorFormState {
  name: string
  display_name: string
  description: string
  category: ValidatorCategory
  severity: ValidatorSeverity
  tags: string[]
  parameters: ValidatorParamDefinition[]
  code: string
  test_cases: ValidatorTestCase[]
  is_enabled: boolean
}

/**
 * Default values for new validator form
 */
export const DEFAULT_VALIDATOR_FORM: ValidatorFormState = {
  name: '',
  display_name: '',
  description: '',
  category: 'custom',
  severity: 'warning',
  tags: [],
  parameters: [],
  code: '',
  test_cases: [],
  is_enabled: true,
}

/**
 * Form state for creating/editing reporters
 */
export interface ReporterFormState {
  name: string
  display_name: string
  description: string
  output_formats: ReporterOutputFormat[]
  config_fields: ReporterFieldDefinition[]
  template: string
  code: string
  is_enabled: boolean
}

/**
 * Default values for new reporter form
 */
export const DEFAULT_REPORTER_FORM: ReporterFormState = {
  name: '',
  display_name: '',
  description: '',
  output_formats: ['html'],
  config_fields: [],
  template: '',
  code: '',
  is_enabled: true,
}

// ValidatorTestResult is now aliased from API type at top of file

/**
 * Reporter preview result
 */
export interface ReporterPreviewResult {
  success: boolean
  preview_html?: string
  error?: string
  generation_time_ms: number
}

/**
 * Props for editor dialogs
 */
export interface EditorDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess?: () => void
}

/**
 * Props for validator editor dialog
 */
export interface ValidatorEditorDialogProps extends EditorDialogProps {
  validator?: CustomValidator
  columns?: string[]
}

/**
 * Props for reporter editor dialog
 */
export interface ReporterEditorDialogProps extends EditorDialogProps {
  reporter?: CustomReporter
}

/**
 * Column definition for validator column selection
 */
export interface ColumnInfo {
  name: string
  type: string
}
