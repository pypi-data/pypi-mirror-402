/**
 * API client for truthound-dashboard backend
 */

const API_BASE = '/api/v1'

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean>
}

class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public data?: unknown
  ) {
    super(`API Error: ${status} ${statusText}`)
    this.name = 'ApiError'
  }
}

async function request<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { params, ...init } = options

  // Build URL with query params
  let url = `${API_BASE}${endpoint}`
  if (params) {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value))
      }
    })
    const queryString = searchParams.toString()
    if (queryString) {
      url += `?${queryString}`
    }
  }

  // Set default headers
  const headers = new Headers(init.headers)
  if (!headers.has('Content-Type') && init.body) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(url, {
    ...init,
    headers,
  })

  if (!response.ok) {
    let data
    try {
      data = await response.json()
    } catch {
      // Ignore JSON parse errors
    }
    throw new ApiError(response.status, response.statusText, data)
  }

  // Handle empty responses
  const contentType = response.headers.get('Content-Type')
  if (!contentType || !contentType.includes('application/json')) {
    return {} as T
  }

  return response.json()
}

// Health
export async function getHealth() {
  return request<{
    status: string
    version: string
    timestamp: string
  }>('/health')
}

// ============================================================================
// Source Types and Definitions
// ============================================================================

/**
 * All supported source types.
 */
export type SourceType =
  | 'file'
  | 'postgresql'
  | 'mysql'
  | 'sqlite'
  | 'snowflake'
  | 'bigquery'
  | 'redshift'
  | 'databricks'
  | 'oracle'
  | 'sqlserver'
  | 'spark'

/**
 * Source type categories for UI grouping.
 */
export type SourceCategory = 'file' | 'database' | 'warehouse' | 'bigdata'

/**
 * Field types for dynamic form rendering.
 */
export type FieldType = 'text' | 'password' | 'number' | 'select' | 'boolean' | 'file_path' | 'textarea'

/**
 * Option for select fields.
 */
export interface FieldOption {
  value: string
  label: string
}

/**
 * Definition of a configuration field for dynamic form rendering.
 */
export interface FieldDefinition {
  name: string
  label: string
  type: FieldType
  required: boolean
  placeholder: string
  description: string
  default?: unknown
  options?: FieldOption[]
  min_value?: number
  max_value?: number
  depends_on?: string
  depends_value?: unknown
}

/**
 * Complete definition of a source type for UI rendering.
 */
export interface SourceTypeDefinition {
  type: SourceType
  name: string
  description: string
  icon: string
  category: SourceCategory
  fields: FieldDefinition[]
  required_fields: string[]
  optional_fields: string[]
  docs_url?: string
}

/**
 * Category definition for grouping source types.
 */
export interface SourceCategoryDefinition {
  value: SourceCategory
  label: string
  description: string
}

/**
 * Response containing all source types and categories.
 */
export interface SourceTypesResponse {
  types: SourceTypeDefinition[]
  categories: SourceCategoryDefinition[]
}

// Sources
export interface Source {
  id: string
  name: string
  type: SourceType
  config: Record<string, unknown>
  description?: string
  is_active: boolean
  created_at: string
  updated_at: string
  last_validated_at?: string
  has_schema: boolean
  latest_validation_status?: string
}

export interface SourceListResponse {
  success: boolean
  data: Source[]
  total: number
  offset: number
  limit: number
}

export async function listSources(params?: {
  offset?: number
  limit?: number
  active_only?: boolean
}): Promise<SourceListResponse> {
  return request<SourceListResponse>('/sources', { params })
}

export async function getSource(id: string): Promise<Source> {
  const response = await request<{ success: boolean; data: Source }>(`/sources/${id}`)
  return response.data
}

export async function createSource(data: {
  name: string
  type: string
  config: Record<string, unknown>
  description?: string
}): Promise<Source> {
  const response = await request<{ success: boolean; data: Source }>('/sources', {
    method: 'POST',
    body: JSON.stringify(data),
  })
  return response.data
}

export async function updateSource(
  id: string,
  data: {
    name?: string
    config?: Record<string, unknown>
    description?: string
    is_active?: boolean
  }
): Promise<Source> {
  const response = await request<{ success: boolean; data: Source }>(`/sources/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
  return response.data
}

export async function deleteSource(id: string): Promise<{ message: string }> {
  return request<{ message: string }>(`/sources/${id}`, {
    method: 'DELETE',
  })
}

// Validations
export interface ValidationIssue {
  column: string
  issue_type: string
  count: number
  severity: 'critical' | 'high' | 'medium' | 'low'
  details?: string
  expected?: unknown
  actual?: unknown
}

export interface Validation {
  id: string
  source_id: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'error'
  passed: boolean
  has_critical: boolean
  has_high: boolean
  total_issues: number
  critical_issues: number
  high_issues: number
  medium_issues: number
  low_issues: number
  row_count?: number
  column_count?: number
  issues: ValidationIssue[]
  error_message?: string
  duration_ms?: number
  started_at?: string
  completed_at?: string
  created_at: string
}

export interface ValidationListResponse {
  success: boolean
  data: Validation[]
  total: number
  limit: number
}

/**
 * Configuration for a single validator with its parameters.
 */
export interface ValidatorConfig {
  /** Validator name */
  name: string
  /** Whether to run this validator */
  enabled: boolean
  /** Parameter values */
  params: Record<string, unknown>
  /** Override default severity */
  severity_override?: 'low' | 'medium' | 'high' | 'critical'
}

/**
 * Options for running validation - maps to th.check() parameters.
 *
 * Supports two modes:
 * 1. Simple mode: Use `validators` list with validator names (backward compatible)
 * 2. Advanced mode: Use `validator_configs` for per-validator parameter configuration
 *
 * @see https://github.com/truthound/truthound - th.check() documentation
 */
export interface ValidationRunOptions {
  /** Simple mode: Specific validators to run by name. If not provided, all validators run. */
  validators?: string[]
  /** Advanced mode: Per-validator configuration with parameters. Takes precedence over validators. */
  validator_configs?: ValidatorConfig[]
  /** Custom validators to include in the validation run. */
  custom_validators?: Array<{
    validator_id: string
    column?: string
    params?: Record<string, unknown>
  }>
  /** Path to schema YAML file for schema validation. */
  schema_path?: string
  /** Auto-learn and cache schema for validation. */
  auto_schema?: boolean
  /** Columns to validate. If not provided, all columns are validated. */
  columns?: string[]
  /** Minimum severity level to report ('low' | 'medium' | 'high' | 'critical'). */
  min_severity?: 'low' | 'medium' | 'high' | 'critical'
  /** If true, raises exception on validation failures. */
  strict?: boolean
  /** If true, uses DAG-based parallel execution. */
  parallel?: boolean
  /** Max threads for parallel execution (1-32). Only used when parallel=true. */
  max_workers?: number
  /** Enable query pushdown for SQL sources. Undefined uses auto-detection. */
  pushdown?: boolean
}

export async function runValidation(
  sourceId: string,
  options?: ValidationRunOptions
): Promise<Validation> {
  const response = await request<{ success: boolean; data: Validation }>(`/validations/sources/${sourceId}/validate`, {
    method: 'POST',
    body: JSON.stringify(options || {}),
  })
  return response.data
}

export async function getValidation(id: string): Promise<Validation> {
  const response = await request<{ success: boolean; data: Validation }>(`/validations/${id}`)
  return response.data
}

export async function listSourceValidations(
  sourceId: string,
  params?: { limit?: number }
): Promise<ValidationListResponse> {
  return request<ValidationListResponse>(
    `/validations/sources/${sourceId}/validations`,
    { params }
  )
}

// Schemas
export interface Schema {
  id: string
  source_id: string
  schema_yaml: string
  schema_json?: Record<string, unknown>
  row_count?: number
  column_count?: number
  columns: string[]
  version?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export async function getSourceSchema(sourceId: string): Promise<Schema | null> {
  const response = await request<{ success: boolean; data: Schema | null }>(`/sources/${sourceId}/schema`)
  return response.data
}

export async function learnSchema(
  sourceId: string,
  data?: { infer_constraints?: boolean }
): Promise<Schema> {
  const response = await request<{ success: boolean; data: Schema }>(`/sources/${sourceId}/learn`, {
    method: 'POST',
    body: JSON.stringify(data || {}),
  })
  return response.data
}

export async function updateSchema(
  sourceId: string,
  schemaYaml: string
): Promise<Schema> {
  const response = await request<{ success: boolean; data: Schema }>(`/sources/${sourceId}/schema`, {
    method: 'PUT',
    body: JSON.stringify({ schema_yaml: schemaYaml }),
  })
  return response.data
}

// Profile
export interface ColumnProfile {
  name: string
  dtype: string
  null_pct: string
  unique_pct: string
  min?: unknown
  max?: unknown
  mean?: number
  std?: number
}

// Pattern detection result
export interface DetectedPattern {
  patternType: string
  confidence: number
  matchCount: number
  matchPercentage: number
  sampleMatches?: string[] | null
}

// Histogram bucket
export interface HistogramBucket {
  bucket: string
  count: number
  percentage: number
}

// Enhanced column profile with pattern detection
export interface EnhancedColumnProfile extends ColumnProfile {
  // Inferred semantic type
  inferredType?: string | null
  // Completeness
  nullCount?: number | null
  // Uniqueness
  isUnique?: boolean | null
  // Extended statistics
  median?: number | null
  q1?: number | null
  q3?: number | null
  skewness?: number | null
  kurtosis?: number | null
  // String stats
  minLength?: number | null
  maxLength?: number | null
  avgLength?: number | null
  // Pattern detection
  patterns?: DetectedPattern[] | null
  primaryPattern?: string | null
  // Distribution
  mostCommon?: Array<{ value: string; count: number }> | null
  histogram?: HistogramBucket[] | null
  // Cardinality
  cardinalityEstimate?: number | null
}

// Sampling metadata
export interface SamplingMetadata {
  strategyUsed: string
  sampleSize: number
  totalRows: number
  samplingRatio: number
  seed?: number | null
  confidenceLevel?: number | null
  marginOfError?: number | null
}

export interface ProfileResult {
  source: string
  row_count: number
  column_count: number
  size_bytes: number
  columns: ColumnProfile[]
  // Enhanced fields
  sampling?: SamplingMetadata | null
  detected_patterns_summary?: Record<string, number> | null
  profiled_at?: string | null
  profiling_duration_ms?: number | null
}

// Sampling strategy type
export type SamplingStrategy =
  | 'none'
  | 'head'
  | 'random'
  | 'systematic'
  | 'stratified'
  | 'reservoir'
  | 'adaptive'
  | 'hash'

// Sampling configuration
export interface SamplingConfig {
  strategy: SamplingStrategy
  sample_size?: number | null
  confidence_level?: number
  margin_of_error?: number
  strata_column?: string | null
  seed?: number | null
}

// Pattern detection configuration
export interface PatternDetectionConfig {
  enabled: boolean
  sample_size?: number
  min_confidence?: number
  patterns_to_detect?: string[] | null
}

/**
 * Options for data profiling with enhanced features.
 */
export interface ProfileOptions {
  /**
   * Maximum number of rows to sample for profiling.
   * If undefined, profiles all data. Useful for large datasets.
   * @deprecated Use sampling.sample_size for advanced control
   */
  sample_size?: number
  /**
   * Advanced sampling configuration
   */
  sampling?: SamplingConfig
  /**
   * Pattern detection configuration
   */
  pattern_detection?: PatternDetectionConfig
  /**
   * Include histograms in the profile
   */
  include_histograms?: boolean
  /**
   * Include correlation analysis
   */
  include_correlations?: boolean
  /**
   * Include cardinality estimates
   */
  include_cardinality?: boolean
}

export async function profileSource(
  sourceId: string,
  options?: ProfileOptions
): Promise<ProfileResult> {
  const response = await request<{ success: boolean; data: ProfileResult }>(`/sources/${sourceId}/profile`, {
    method: 'POST',
    body: options ? JSON.stringify(options) : undefined,
  })
  return response.data
}

// Test source connection
export async function testSourceConnection(
  sourceId: string
): Promise<{ success: boolean; data: { success: boolean; message?: string; error?: string } }> {
  return request(`/sources/${sourceId}/test`, { method: 'POST' })
}

// Get supported source types with full field definitions
export async function getSupportedSourceTypes(): Promise<{
  success: boolean
  data: SourceTypesResponse
}> {
  return request('/sources/types/supported')
}

// Test connection configuration before creating a source
export async function testConnectionConfig(
  type: SourceType,
  config: Record<string, unknown>
): Promise<{
  success: boolean
  data: { success: boolean; message?: string; error?: string }
}> {
  return request('/sources/test-connection', {
    method: 'POST',
    body: JSON.stringify({ type, config }),
  })
}

// History
export interface HistorySummary {
  total_runs: number
  passed_runs: number
  failed_runs: number
  success_rate: number
}

export interface TrendDataPoint {
  date: string
  success_rate: number
  run_count: number
  passed_count: number
  failed_count: number
}

export interface FailureFrequencyItem {
  issue: string
  count: number
}

export interface RecentValidation {
  id: string
  status: string
  passed: boolean
  has_critical: boolean
  has_high: boolean
  total_issues: number
  created_at: string
}

export interface HistoryResponse {
  success: boolean
  data: {
    summary: HistorySummary
    trend: TrendDataPoint[]
    failure_frequency: FailureFrequencyItem[]
    recent_validations: RecentValidation[]
  }
}

export async function getValidationHistory(
  sourceId: string,
  params?: {
    period?: '7d' | '30d' | '90d'
    granularity?: 'hourly' | 'daily' | 'weekly'
  }
): Promise<HistoryResponse> {
  return request<HistoryResponse>(`/sources/${sourceId}/history`, { params })
}

// Drift Detection

/**
 * Drift detection methods supported by truthound.
 *
 * Each method has different characteristics and use cases:
 * - auto: Smart selection based on data type (numeric → PSI, categorical → chi2)
 * - ks: Kolmogorov-Smirnov test - best for continuous distributions
 * - psi: Population Stability Index - industry standard, any distribution
 * - chi2: Chi-Square test - best for categorical data
 * - js: Jensen-Shannon divergence - symmetric, bounded (0-1)
 * - kl: Kullback-Leibler divergence - information loss measure
 * - wasserstein: Earth Mover's Distance - metric, meaningful for non-overlapping
 * - cvm: Cramér-von Mises - more sensitive to tail differences than KS
 * - anderson: Anderson-Darling - weighted for tail sensitivity
 */
export type DriftMethod =
  | 'auto'
  | 'ks'
  | 'psi'
  | 'chi2'
  | 'js'
  | 'kl'
  | 'wasserstein'
  | 'cvm'
  | 'anderson'

/**
 * Multiple testing correction methods.
 *
 * When comparing multiple columns, correction adjusts p-values to control
 * false discovery rate:
 * - none: No correction (use with caution)
 * - bonferroni: Conservative, suitable for independent tests
 * - holm: Sequential adjustment, less conservative than Bonferroni
 * - bh: Benjamini-Hochberg (FDR control), default for multiple columns
 */
export type CorrectionMethod = 'none' | 'bonferroni' | 'holm' | 'bh'

/**
 * All drift methods for UI selection.
 */
export const DRIFT_METHODS: { value: DriftMethod; label: string; description: string }[] = [
  { value: 'auto', label: 'Auto', description: 'Smart selection based on data type' },
  { value: 'ks', label: 'Kolmogorov-Smirnov', description: 'Best for continuous distributions' },
  { value: 'psi', label: 'PSI', description: 'Population Stability Index - industry standard' },
  { value: 'chi2', label: 'Chi-Square', description: 'Best for categorical data' },
  { value: 'js', label: 'Jensen-Shannon', description: 'Symmetric divergence, bounded 0-1' },
  { value: 'kl', label: 'Kullback-Leibler', description: 'Information loss measure' },
  { value: 'wasserstein', label: 'Wasserstein', description: 'Earth Mover\'s Distance' },
  { value: 'cvm', label: 'Cramér-von Mises', description: 'More sensitive to tails than KS' },
  { value: 'anderson', label: 'Anderson-Darling', description: 'Tail-weighted sensitivity' },
]

/**
 * Correction methods for UI selection.
 */
export const CORRECTION_METHODS: { value: CorrectionMethod | ''; label: string; description: string }[] = [
  { value: '', label: 'Default (BH)', description: 'Benjamini-Hochberg FDR control for multiple columns' },
  { value: 'none', label: 'None', description: 'No correction (use with caution)' },
  { value: 'bonferroni', label: 'Bonferroni', description: 'Conservative, independent tests' },
  { value: 'holm', label: 'Holm', description: 'Sequential adjustment, less conservative' },
  { value: 'bh', label: 'Benjamini-Hochberg', description: 'FDR control' },
]

/**
 * Default thresholds for each detection method.
 */
export const DEFAULT_THRESHOLDS: Record<DriftMethod, number> = {
  auto: 0.05,
  ks: 0.05,
  psi: 0.1,
  chi2: 0.05,
  js: 0.1,
  kl: 0.1,
  wasserstein: 0.1,
  cvm: 0.05,
  anderson: 0.05,
}

export interface DriftCompareRequest {
  baseline_source_id: string
  current_source_id: string
  columns?: string[]
  /** Detection method (see DriftMethod type for details) */
  method?: DriftMethod
  /** Custom threshold (default varies by method) */
  threshold?: number
  /** Multiple testing correction method */
  correction?: CorrectionMethod
  sample_size?: number
}

export interface ColumnDriftResult {
  column: string
  dtype: string
  drifted: boolean
  level: string
  method: string
  statistic?: number
  p_value?: number
  baseline_stats: Record<string, unknown>
  current_stats: Record<string, unknown>
}

export interface DriftResult {
  comparison_id?: string
  baseline_source: string
  current_source: string
  baseline_rows: number
  current_rows: number
  has_drift: boolean
  has_high_drift: boolean
  total_columns: number
  drifted_columns: string[]
  columns: ColumnDriftResult[]
}

export interface DriftComparison {
  id: string
  baseline_source_id: string
  current_source_id: string
  has_drift: boolean
  has_high_drift: boolean
  total_columns: number
  drifted_columns: number
  drift_percentage: number
  result?: DriftResult
  config?: Record<string, unknown>
  created_at: string
  updated_at?: string
}

export async function compareDrift(
  data: DriftCompareRequest
): Promise<{ success: boolean; data: DriftComparison }> {
  return request('/drift/compare', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function listDriftComparisons(params?: {
  baseline_source_id?: string
  current_source_id?: string
  limit?: number
}): Promise<{ success: boolean; data: DriftComparison[]; total: number }> {
  return request('/drift/comparisons', { params })
}

export async function getDriftComparison(
  id: string
): Promise<{ success: boolean; data: DriftComparison }> {
  return request(`/drift/comparisons/${id}`)
}

// Schedules
export type TriggerType =
  | 'cron'
  | 'interval'
  | 'data_change'
  | 'composite'
  | 'event'
  | 'manual'

export interface Schedule {
  id: string
  name: string
  source_id: string
  cron_expression: string
  trigger_type?: TriggerType
  trigger_config?: Record<string, unknown>
  trigger_count?: number
  last_trigger_result?: Record<string, unknown>
  is_active: boolean
  notify_on_failure: boolean
  last_run_at?: string
  next_run_at?: string
  config?: Record<string, unknown>
  created_at: string
  updated_at?: string
  source_name?: string
}

export interface ScheduleCreateRequest {
  source_id: string
  name: string
  cron_expression?: string
  trigger_type?: TriggerType
  trigger_config?: Record<string, unknown>
  notify_on_failure?: boolean
  config?: Record<string, unknown>
}

export interface ScheduleUpdateRequest {
  name?: string
  cron_expression?: string
  trigger_type?: TriggerType
  trigger_config?: Record<string, unknown>
  notify_on_failure?: boolean
  config?: Record<string, unknown>
}

export async function listSchedules(params?: {
  source_id?: string
  active_only?: boolean
  limit?: number
}): Promise<{ success: boolean; data: Schedule[]; total: number }> {
  return request('/schedules', { params })
}

export async function createSchedule(
  data: ScheduleCreateRequest
): Promise<{ success: boolean; data: Schedule }> {
  return request('/schedules', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function getSchedule(
  id: string
): Promise<{ success: boolean; data: Schedule }> {
  return request(`/schedules/${id}`)
}

export async function updateSchedule(
  id: string,
  data: ScheduleUpdateRequest
): Promise<{ success: boolean; data: Schedule }> {
  return request(`/schedules/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteSchedule(
  id: string
): Promise<{ success: boolean; message: string }> {
  return request(`/schedules/${id}`, { method: 'DELETE' })
}

export async function pauseSchedule(
  id: string
): Promise<{ success: boolean; message: string; schedule: Schedule }> {
  return request(`/schedules/${id}/pause`, { method: 'POST' })
}

export async function resumeSchedule(
  id: string
): Promise<{ success: boolean; message: string; schedule: Schedule }> {
  return request(`/schedules/${id}/resume`, { method: 'POST' })
}

export async function runScheduleNow(
  id: string
): Promise<{ success: boolean; message: string; validation_id: string; passed: boolean }> {
  return request(`/schedules/${id}/run`, { method: 'POST' })
}

// ============================================================================
// PII Scan
// ============================================================================

/**
 * PII types commonly detected by th.scan()
 */
export const PII_TYPES = [
  'email',
  'phone',
  'ssn',
  'credit_card',
  'ip_address',
  'date_of_birth',
  'address',
  'name',
  'passport',
  'driver_license',
  'national_id',
  'bank_account',
  'medical_record',
  'biometric',
] as const

/**
 * Supported privacy regulations for compliance checking.
 */
export type Regulation = 'gdpr' | 'ccpa' | 'lgpd'

export const REGULATIONS: { value: Regulation; label: string; description: string }[] = [
  { value: 'gdpr', label: 'GDPR', description: 'General Data Protection Regulation (EU)' },
  { value: 'ccpa', label: 'CCPA', description: 'California Consumer Privacy Act (US)' },
  { value: 'lgpd', label: 'LGPD', description: 'Lei Geral de Proteção de Dados (Brazil)' },
]

export interface PIIFinding {
  column: string
  pii_type: string
  confidence: number
  sample_count: number
  sample_values?: string[]
}

export interface RegulationViolation {
  regulation: Regulation
  column: string
  pii_type: string
  message: string
  severity: 'low' | 'medium' | 'high' | 'critical'
}

export interface PIIScan {
  id: string
  source_id: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'error'
  total_columns_scanned: number
  columns_with_pii: number
  total_findings: number
  has_violations: boolean
  total_violations: number
  row_count?: number
  column_count?: number
  min_confidence: number
  regulations_checked?: string[] | null
  findings: PIIFinding[]
  violations: RegulationViolation[]
  error_message?: string
  duration_ms?: number
  started_at?: string
  completed_at?: string
  created_at: string
}

export interface PIIScanListResponse {
  data: PIIScan[]
  total: number
  limit: number
}

/**
 * Options for running PII scan - maps to th.scan() parameters.
 */
export interface PIIScanOptions {
  /** Specific columns to scan. If not provided, all columns are scanned. */
  columns?: string[]
  /** Privacy regulations to check compliance (gdpr, ccpa, lgpd). */
  regulations?: Regulation[]
  /** Minimum confidence threshold for PII detection (0.0-1.0). Default: 0.8 */
  min_confidence?: number
}

export async function runPIIScan(
  sourceId: string,
  options?: PIIScanOptions
): Promise<PIIScan> {
  return request<PIIScan>(`/scans/sources/${sourceId}/scan`, {
    method: 'POST',
    body: JSON.stringify(options || {}),
  })
}

export async function getPIIScan(id: string): Promise<PIIScan> {
  return request<PIIScan>(`/scans/${id}`)
}

export async function listSourcePIIScans(
  sourceId: string,
  params?: { limit?: number }
): Promise<PIIScanListResponse> {
  return request<PIIScanListResponse>(
    `/scans/sources/${sourceId}/scans`,
    { params }
  )
}

export async function getLatestPIIScan(sourceId: string): Promise<PIIScan> {
  return request<PIIScan>(`/scans/sources/${sourceId}/scans/latest`)
}

// ============================================================================
// Data Masking (th.mask())
// ============================================================================

/**
 * Masking strategies for th.mask():
 * - redact: Replace values with asterisks
 * - hash: Replace values with SHA256 hash (deterministic)
 * - fake: Replace values with realistic fake data
 */
export type MaskingStrategy = 'redact' | 'hash' | 'fake'

export interface DataMask {
  id: string
  source_id: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'error'
  strategy: MaskingStrategy
  output_path?: string
  columns_masked?: string[]
  auto_detected: boolean
  row_count?: number
  column_count?: number
  duration_ms?: number
  error_message?: string
  started_at?: string
  completed_at?: string
  created_at: string
}

export interface DataMaskListItem {
  id: string
  source_id: string
  source_name?: string
  status: string
  strategy: string
  columns_masked: number
  row_count?: number
  duration_ms?: number
  created_at: string
}

export interface DataMaskListResponse {
  data: DataMaskListItem[]
  total: number
  limit: number
}

export interface MaskOptions {
  /** Columns to mask. If not provided, auto-detects PII columns. */
  columns?: string[]
  /** Masking strategy: redact, hash, or fake. Default: redact */
  strategy?: MaskingStrategy
  /** Output file format: csv, parquet, json. Default: csv */
  output_format?: 'csv' | 'parquet' | 'json'
}

export async function runDataMask(
  sourceId: string,
  options?: MaskOptions
): Promise<DataMask> {
  return request<DataMask>(`/masks/sources/${sourceId}/mask`, {
    method: 'POST',
    body: JSON.stringify(options || {}),
  })
}

export async function getDataMask(id: string): Promise<DataMask> {
  return request<DataMask>(`/masks/${id}`)
}

export async function listSourceDataMasks(
  sourceId: string,
  params?: { limit?: number }
): Promise<DataMaskListResponse> {
  return request<DataMaskListResponse>(
    `/masks/sources/${sourceId}/masks`,
    { params }
  )
}

export async function getLatestDataMask(sourceId: string): Promise<DataMask> {
  return request<DataMask>(`/masks/sources/${sourceId}/masks/latest`)
}

// ============================================================================
// Notifications (Phase 3)
// ============================================================================

export interface NotificationChannel {
  id: string
  name: string
  type: 'slack' | 'email' | 'webhook' | 'discord' | 'telegram' | 'pagerduty' | 'opsgenie' | 'teams' | 'github'
  is_active: boolean
  config_summary: string
  config?: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface NotificationRule {
  id: string
  name: string
  condition: string
  condition_config?: Record<string, unknown>
  channel_ids: string[]
  source_ids?: string[]
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface NotificationLog {
  id: string
  channel_id: string
  rule_id?: string
  event_type: string
  status: 'pending' | 'sent' | 'failed'
  message_preview: string
  error_message?: string
  created_at: string
  sent_at?: string
}

export interface NotificationStats {
  period_hours: number
  total: number
  by_status: Record<string, number>
  by_channel: Record<string, number>
  success_rate: number
}

// Notification Channels
export async function listNotificationChannels(params?: {
  offset?: number
  limit?: number
  active_only?: boolean
  channel_type?: string
}): Promise<{ success: boolean; data: NotificationChannel[]; count: number }> {
  return request('/notifications/channels', { params })
}

export async function getNotificationChannel(
  id: string
): Promise<{ success: boolean; data: NotificationChannel }> {
  return request(`/notifications/channels/${id}`)
}

export async function createNotificationChannel(data: {
  name: string
  type: string
  config: Record<string, unknown>
  is_active?: boolean
}): Promise<{ success: boolean; data: NotificationChannel }> {
  return request('/notifications/channels', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateNotificationChannel(
  id: string,
  data: {
    name?: string
    config?: Record<string, unknown>
    is_active?: boolean
  }
): Promise<{ success: boolean; data: NotificationChannel }> {
  return request(`/notifications/channels/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteNotificationChannel(
  id: string
): Promise<{ success: boolean }> {
  return request(`/notifications/channels/${id}`, { method: 'DELETE' })
}

export async function testNotificationChannel(
  id: string
): Promise<{ success: boolean; message: string; error?: string }> {
  return request(`/notifications/channels/${id}/test`, { method: 'POST' })
}

export async function getNotificationChannelTypes(): Promise<{
  success: boolean
  data: Record<string, Record<string, unknown>>
}> {
  return request('/notifications/channels/types')
}

// Notification Rules
export async function listNotificationRules(params?: {
  offset?: number
  limit?: number
  active_only?: boolean
  condition?: string
}): Promise<{ success: boolean; data: NotificationRule[]; count: number }> {
  return request('/notifications/rules', { params })
}

export async function getNotificationRule(
  id: string
): Promise<{ success: boolean; data: NotificationRule }> {
  return request(`/notifications/rules/${id}`)
}

export async function createNotificationRule(data: {
  name: string
  condition: string
  channel_ids: string[]
  condition_config?: Record<string, unknown>
  source_ids?: string[]
  is_active?: boolean
}): Promise<{ success: boolean; data: NotificationRule }> {
  return request('/notifications/rules', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateNotificationRule(
  id: string,
  data: {
    name?: string
    condition?: string
    channel_ids?: string[]
    condition_config?: Record<string, unknown>
    source_ids?: string[]
    is_active?: boolean
  }
): Promise<{ success: boolean; data: NotificationRule }> {
  return request(`/notifications/rules/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteNotificationRule(
  id: string
): Promise<{ success: boolean }> {
  return request(`/notifications/rules/${id}`, { method: 'DELETE' })
}

export async function getNotificationRuleConditions(): Promise<{
  success: boolean
  data: string[]
}> {
  return request('/notifications/rules/conditions')
}

// Notification Logs
export async function listNotificationLogs(params?: {
  offset?: number
  limit?: number
  channel_id?: string
  status?: string
  hours?: number
}): Promise<{ success: boolean; data: NotificationLog[]; count: number }> {
  return request('/notifications/logs', { params })
}

export async function getNotificationLog(
  id: string
): Promise<{ success: boolean; data: NotificationLog & { message: string; event_data?: unknown } }> {
  return request(`/notifications/logs/${id}`)
}

export async function getNotificationStats(params?: {
  hours?: number
}): Promise<{ success: boolean; data: NotificationStats }> {
  return request('/notifications/logs/stats', { params })
}

// ============================================================================
// Glossary (Phase 5)
// ============================================================================

export interface GlossaryCategory {
  id: string
  name: string
  description?: string
  parent_id?: string
  created_at: string
  updated_at: string
  children?: GlossaryCategory[]
}

export interface GlossaryTermSummary {
  id: string
  name: string
  definition: string
}

export interface GlossaryTerm {
  id: string
  name: string
  definition: string
  category_id?: string
  status: 'draft' | 'approved' | 'deprecated'
  owner_id?: string
  created_at: string
  updated_at: string
  category?: GlossaryCategory
  synonyms: GlossaryTermSummary[]
  related_terms: GlossaryTermSummary[]
}

export interface TermRelationship {
  id: string
  source_term_id: string
  target_term_id: string
  relationship_type: 'synonym' | 'related' | 'parent' | 'child'
  created_at: string
  source_term: GlossaryTermSummary
  target_term: GlossaryTermSummary
}

export interface TermHistory {
  id: string
  term_id: string
  field_name: string
  old_value?: string
  new_value?: string
  changed_by?: string
  changed_at: string
}

export interface TermCreate {
  name: string
  definition: string
  category_id?: string
  status?: 'draft' | 'approved' | 'deprecated'
  owner_id?: string
}

export interface TermUpdate {
  name?: string
  definition?: string
  category_id?: string
  status?: 'draft' | 'approved' | 'deprecated'
  owner_id?: string
}

export interface CategoryCreate {
  name: string
  description?: string
  parent_id?: string
}

export interface CategoryUpdate {
  name?: string
  description?: string
  parent_id?: string
}

export interface RelationshipCreate {
  source_term_id: string
  target_term_id: string
  relationship_type: 'synonym' | 'related' | 'parent' | 'child'
}

// Glossary Terms
export async function getTerms(params?: {
  search?: string
  category_id?: string
  status?: string
  skip?: number
  limit?: number
}): Promise<GlossaryTerm[]> {
  return request<GlossaryTerm[]>('/glossary/terms', { params })
}

export async function getTerm(id: string): Promise<GlossaryTerm> {
  return request<GlossaryTerm>(`/glossary/terms/${id}`)
}

export async function createTerm(data: TermCreate): Promise<GlossaryTerm> {
  return request<GlossaryTerm>('/glossary/terms', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateTerm(id: string, data: TermUpdate): Promise<GlossaryTerm> {
  return request<GlossaryTerm>(`/glossary/terms/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteTerm(id: string): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>(`/glossary/terms/${id}`, { method: 'DELETE' })
}

export async function getTermHistory(id: string): Promise<TermHistory[]> {
  return request<TermHistory[]>(`/glossary/terms/${id}/history`)
}

export async function getTermRelationships(id: string): Promise<TermRelationship[]> {
  return request<TermRelationship[]>(`/glossary/terms/${id}/relationships`)
}

// Glossary Categories
export async function getCategories(): Promise<GlossaryCategory[]> {
  return request<GlossaryCategory[]>('/glossary/categories')
}

export async function createCategory(data: CategoryCreate): Promise<GlossaryCategory> {
  return request<GlossaryCategory>('/glossary/categories', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateCategory(id: string, data: CategoryUpdate): Promise<GlossaryCategory> {
  return request<GlossaryCategory>(`/glossary/categories/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteCategory(id: string): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>(`/glossary/categories/${id}`, { method: 'DELETE' })
}

// Glossary Relationships
export async function createRelationship(data: RelationshipCreate): Promise<TermRelationship> {
  return request<TermRelationship>('/glossary/relationships', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function deleteRelationship(id: string): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>(`/glossary/relationships/${id}`, { method: 'DELETE' })
}

// ============================================================================
// Catalog (Phase 5)
// ============================================================================

export type AssetType = 'table' | 'file' | 'api'
export type SensitivityLevel = 'public' | 'internal' | 'confidential' | 'restricted'

export interface AssetTag {
  id: string
  asset_id: string
  tag_name: string
  tag_value?: string
  created_at: string
}

export interface AssetColumn {
  id: string
  asset_id: string
  name: string
  data_type?: string
  description?: string
  is_nullable: boolean
  is_primary_key: boolean
  term_id?: string
  sensitivity_level?: SensitivityLevel
  created_at: string
  term?: GlossaryTermSummary
}

export interface SourceSummary {
  id: string
  name: string
  type: string
}

export interface CatalogAsset {
  id: string
  name: string
  asset_type: AssetType
  source_id?: string
  description?: string
  owner_id?: string
  quality_score?: number
  created_at: string
  updated_at: string
  source?: SourceSummary
  columns: AssetColumn[]
  tags: AssetTag[]
}

export interface AssetListItem {
  id: string
  name: string
  asset_type: AssetType
  source_id?: string
  source_name?: string
  quality_score?: number
  tag_count: number
  column_count: number
  updated_at: string
}

export interface AssetCreate {
  name: string
  asset_type: AssetType
  source_id?: string
  description?: string
  owner_id?: string
}

export interface AssetUpdate {
  name?: string
  asset_type?: AssetType
  source_id?: string
  description?: string
  owner_id?: string
  quality_score?: number
}

export interface ColumnCreate {
  name: string
  data_type?: string
  description?: string
  is_nullable?: boolean
  is_primary_key?: boolean
  sensitivity_level?: SensitivityLevel
}

export interface ColumnUpdate {
  name?: string
  data_type?: string
  description?: string
  is_nullable?: boolean
  is_primary_key?: boolean
  sensitivity_level?: SensitivityLevel
}

export interface TagCreate {
  tag_name: string
  tag_value?: string
}

// Catalog Assets
export async function getAssets(params?: {
  search?: string
  asset_type?: string
  source_id?: string
  skip?: number
  limit?: number
}): Promise<AssetListItem[]> {
  return request<AssetListItem[]>('/catalog/assets', { params })
}

export async function getAsset(id: string): Promise<CatalogAsset> {
  return request<CatalogAsset>(`/catalog/assets/${id}`)
}

export async function createAsset(data: AssetCreate): Promise<CatalogAsset> {
  return request<CatalogAsset>('/catalog/assets', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateAsset(id: string, data: AssetUpdate): Promise<CatalogAsset> {
  return request<CatalogAsset>(`/catalog/assets/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteAsset(id: string): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>(`/catalog/assets/${id}`, { method: 'DELETE' })
}

// Asset Columns
export async function getAssetColumns(assetId: string): Promise<AssetColumn[]> {
  return request<AssetColumn[]>(`/catalog/assets/${assetId}/columns`)
}

export async function createColumn(assetId: string, data: ColumnCreate): Promise<AssetColumn> {
  return request<AssetColumn>(`/catalog/assets/${assetId}/columns`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateColumn(columnId: string, data: ColumnUpdate): Promise<AssetColumn> {
  return request<AssetColumn>(`/catalog/columns/${columnId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteColumn(columnId: string): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>(`/catalog/columns/${columnId}`, { method: 'DELETE' })
}

export async function mapColumnToTerm(columnId: string, termId: string): Promise<AssetColumn> {
  return request<AssetColumn>(`/catalog/columns/${columnId}/term`, {
    method: 'PUT',
    body: JSON.stringify({ term_id: termId }),
  })
}

export async function unmapColumnFromTerm(columnId: string): Promise<AssetColumn> {
  return request<AssetColumn>(`/catalog/columns/${columnId}/term`, { method: 'DELETE' })
}

// Asset Tags
export async function getAssetTags(assetId: string): Promise<AssetTag[]> {
  return request<AssetTag[]>(`/catalog/assets/${assetId}/tags`)
}

export async function addTag(assetId: string, data: TagCreate): Promise<AssetTag> {
  return request<AssetTag>(`/catalog/assets/${assetId}/tags`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function removeTag(tagId: string): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>(`/catalog/tags/${tagId}`, { method: 'DELETE' })
}

// ============================================================================
// Collaboration (Phase 5)
// ============================================================================

export type ResourceType = 'term' | 'asset' | 'column'
export type ActivityAction = 'created' | 'updated' | 'deleted' | 'commented'

export interface Comment {
  id: string
  resource_type: ResourceType
  resource_id: string
  content: string
  author_id?: string
  parent_id?: string
  created_at: string
  updated_at: string
  replies: Comment[]
}

export interface Activity {
  id: string
  resource_type: string
  resource_id: string
  action: ActivityAction
  actor_id?: string
  description?: string
  metadata?: Record<string, unknown>
  created_at: string
}

export interface CommentCreate {
  resource_type: ResourceType
  resource_id: string
  content: string
  author_id?: string
  parent_id?: string
}

export interface CommentUpdate {
  content: string
}

// Comments
export async function getComments(
  resourceType: ResourceType,
  resourceId: string
): Promise<Comment[]> {
  return request<Comment[]>('/comments', {
    params: { resource_type: resourceType, resource_id: resourceId },
  })
}

export async function createComment(data: CommentCreate): Promise<Comment> {
  return request<Comment>('/comments', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateComment(id: string, data: CommentUpdate): Promise<Comment> {
  return request<Comment>(`/comments/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteComment(id: string): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>(`/comments/${id}`, { method: 'DELETE' })
}

// Activities
export async function getActivities(params?: {
  resource_type?: string
  resource_id?: string
  skip?: number
  limit?: number
}): Promise<Activity[]> {
  return request<Activity[]>('/activities', { params })
}

// ============================================================================
// Validators Registry
// ============================================================================

/**
 * Validator categories.
 */
export type ValidatorCategory =
  | 'schema'
  | 'completeness'
  | 'uniqueness'
  | 'distribution'
  | 'string'
  | 'datetime'
  | 'aggregate'
  | 'cross_table'
  | 'query'
  | 'multi_column'
  | 'table'
  | 'geospatial'
  | 'drift'
  | 'anomaly'

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
  name: string
  label: string
  type: ParameterType
  description?: string
  required?: boolean
  default?: unknown
  options?: SelectOption[]
  min_value?: number
  max_value?: number
  placeholder?: string
  validation_pattern?: string
  depends_on?: string
  depends_value?: unknown
}

/**
 * Complete definition of a validator including its parameters.
 */
export interface ValidatorDefinition {
  name: string
  display_name: string
  category: ValidatorCategory
  description: string
  parameters: ParameterDefinition[]
  tags: string[]
  severity_default: 'low' | 'medium' | 'high' | 'critical'
  requires_extra?: string
}

/**
 * Category info for UI display.
 */
export interface CategoryInfo {
  value: string
  label: string
}

/**
 * Get all available validators.
 */
export async function listValidators(params?: {
  category?: ValidatorCategory
  search?: string
}): Promise<ValidatorDefinition[]> {
  return request<ValidatorDefinition[]>('/validators', { params })
}

/**
 * Get all validator categories.
 */
export async function listValidatorCategories(): Promise<CategoryInfo[]> {
  return request<CategoryInfo[]>('/validators/categories')
}

/**
 * Get a specific validator by name.
 */
export async function getValidator(name: string): Promise<ValidatorDefinition | null> {
  return request<ValidatorDefinition | null>(`/validators/${name}`)
}

// ============================================================================
// Unified Validators (Built-in + Custom)
// ============================================================================

/**
 * Validator source type.
 */
export type ValidatorSource = 'builtin' | 'custom'

/**
 * Unified validator definition (both built-in and custom).
 */
export interface UnifiedValidatorDefinition {
  id: string | null
  name: string
  display_name: string
  category: string
  description: string
  parameters: ParameterDefinition[]
  tags: string[]
  severity_default: 'low' | 'medium' | 'high' | 'critical'
  source: ValidatorSource
  is_enabled: boolean
  requires_extra: string | null
  experimental: boolean
  deprecated: boolean
  usage_count: number
  is_verified: boolean
}

/**
 * Category summary with counts.
 */
export interface ValidatorCategorySummary {
  name: string
  label: string
  builtin_count: number
  custom_count: number
  total: number
}

/**
 * Unified validator list response.
 */
export interface UnifiedValidatorListResponse {
  data: UnifiedValidatorDefinition[]
  total: number
  builtin_count: number
  custom_count: number
  categories: ValidatorCategorySummary[]
}

/**
 * Get all validators (built-in + custom) in a unified list.
 */
export async function listUnifiedValidators(params?: {
  category?: string
  source?: ValidatorSource
  search?: string
  enabled_only?: boolean
  offset?: number
  limit?: number
}): Promise<UnifiedValidatorListResponse> {
  return request<UnifiedValidatorListResponse>('/validators/unified', {
    params: params as Record<string, string | number | boolean>,
  })
}

/**
 * Request to execute a custom validator.
 */
export interface CustomValidatorExecuteRequest {
  source_id: string
  column_name: string
  param_values?: Record<string, unknown>
  sample_size?: number
}

/**
 * Response from custom validator execution.
 */
export interface CustomValidatorExecuteResponse {
  success: boolean
  passed: boolean | null
  execution_time_ms: number
  issues: Array<{
    row?: number
    message: string
    severity?: string
  }>
  message: string
  details: Record<string, unknown>
  error?: string
}

/**
 * Execute a custom validator against a data source.
 */
export async function executeCustomValidator(
  validatorId: string,
  executeRequest: CustomValidatorExecuteRequest
): Promise<CustomValidatorExecuteResponse> {
  return request<CustomValidatorExecuteResponse>(
    `/validators/custom/${validatorId}/execute`,
    {
      method: 'POST',
      body: JSON.stringify(executeRequest),
    }
  )
}

/**
 * Preview custom validator execution with test data.
 */
export async function previewCustomValidatorExecution(
  validatorId: string,
  testData: {
    column_name: string
    values: unknown[]
    params?: Record<string, unknown>
    schema?: Record<string, unknown>
  }
): Promise<CustomValidatorExecuteResponse> {
  return request<CustomValidatorExecuteResponse>(
    `/validators/custom/${validatorId}/execute-preview`,
    {
      method: 'POST',
      body: JSON.stringify(testData),
    }
  )
}

// ============================================================================
// Reports (Phase 4)
// ============================================================================

/**
 * Report format types (6 formats including JUnit for CI/CD integration).
 */
export type ReportFormat = 'html' | 'csv' | 'json' | 'markdown' | 'pdf' | 'junit'

/**
 * Report theme types.
 */
export type ReportTheme = 'light' | 'dark' | 'professional' | 'minimal' | 'high_contrast'

/**
 * Report locale types (15 languages supported).
 * Matches truthound documentation for i18n support.
 */
export type ReportLocale =
  | 'en' // English
  | 'ko' // Korean
  | 'ja' // Japanese
  | 'zh' // Chinese
  | 'de' // German
  | 'fr' // French
  | 'es' // Spanish
  | 'pt' // Portuguese
  | 'it' // Italian
  | 'ru' // Russian
  | 'ar' // Arabic
  | 'th' // Thai
  | 'vi' // Vietnamese
  | 'id' // Indonesian
  | 'tr' // Turkish

/**
 * Locale information for API responses.
 */
export interface LocaleInfo {
  code: ReportLocale
  english_name: string
  native_name: string
  flag: string
  rtl: boolean
}

/**
 * Options for generating a report.
 */
export interface ReportGenerateOptions {
  format?: ReportFormat
  theme?: ReportTheme
  locale?: ReportLocale
  title?: string
  include_samples?: boolean
  include_statistics?: boolean
}

/**
 * Report metadata.
 */
export interface ReportMetadata {
  title: string
  generated_at: string
  source_name?: string
  source_id?: string
  validation_id?: string
  theme: string
  format: string
}

/**
 * Report generation response.
 */
export interface ReportResponse {
  filename: string
  content_type: string
  size_bytes: number
  generation_time_ms: number
  metadata: ReportMetadata
}

/**
 * Available formats response with locales.
 */
export interface AvailableFormatsResponse {
  formats: string[]
  themes: string[]
  locales?: LocaleInfo[]
}

/**
 * Get available report formats, themes, and locales.
 */
export async function getReportFormats(): Promise<AvailableFormatsResponse> {
  return request<AvailableFormatsResponse>('/reports/formats')
}

/**
 * Get available report locales (15 languages).
 */
export async function getReportLocales(): Promise<LocaleInfo[]> {
  return request<LocaleInfo[]>('/reports/locales')
}

/**
 * Generate report metadata (use download for actual content).
 */
export async function generateReportMetadata(
  validationId: string,
  options?: ReportGenerateOptions
): Promise<ReportResponse> {
  return request<ReportResponse>(`/reports/validations/${validationId}/report`, {
    method: 'POST',
    body: JSON.stringify(options || {}),
  })
}

/**
 * Download validation report as file.
 */
export async function downloadValidationReport(
  validationId: string,
  options?: {
    format?: ReportFormat
    theme?: ReportTheme
    locale?: ReportLocale
    include_samples?: boolean
    include_statistics?: boolean
  }
): Promise<Blob> {
  const params = new URLSearchParams()
  if (options?.format) params.append('format', options.format)
  if (options?.theme) params.append('theme', options.theme)
  if (options?.locale) params.append('locale', options.locale)
  if (options?.include_samples !== undefined)
    params.append('include_samples', String(options.include_samples))
  if (options?.include_statistics !== undefined)
    params.append('include_statistics', String(options.include_statistics))

  const url = `${API_BASE}/reports/validations/${validationId}/download?${params}`
  const response = await fetch(url)

  if (!response.ok) {
    throw new ApiError(response.status, response.statusText)
  }

  return response.blob()
}

/**
 * Preview validation report (inline viewing).
 */
export async function previewValidationReport(
  validationId: string,
  format: ReportFormat = 'html',
  theme: ReportTheme = 'professional',
  locale: ReportLocale = 'en'
): Promise<string> {
  const params = new URLSearchParams({ format, theme, locale })
  const url = `${API_BASE}/reports/validations/${validationId}/preview?${params}`
  const response = await fetch(url)

  if (!response.ok) {
    throw new ApiError(response.status, response.statusText)
  }

  return response.text()
}

// ============================================================================
// Maintenance (Phase 4)
// ============================================================================

/**
 * Retention policy type.
 */
export type RetentionPolicyType = 'time' | 'count' | 'size' | 'status' | 'tag' | 'composite'

/**
 * Single retention policy definition.
 */
export interface RetentionPolicy {
  policy_type: RetentionPolicyType
  value: unknown
  target: string
  priority: number
  enabled: boolean
}

/**
 * Retention policy configuration - supports 6 policy types.
 */
export interface RetentionPolicyConfig {
  validation_retention_days: number
  profile_keep_per_source: number
  notification_log_retention_days: number
  run_vacuum: boolean
  enabled: boolean
  // Size-based retention
  max_storage_mb?: number | null
  // Status-based retention
  keep_failed_validations?: boolean
  failed_retention_days?: number
  // Tag-based retention
  protected_tags?: string[]
  delete_tags?: string[]
  // Active policies (read-only, computed)
  active_policies?: RetentionPolicy[]
}

/**
 * Cleanup result for a single task.
 */
export interface CleanupResult {
  task_name: string
  records_deleted: number
  duration_ms: number
  success: boolean
  error?: string
}

/**
 * Maintenance report response.
 */
export interface MaintenanceReport {
  started_at: string
  completed_at?: string
  results: CleanupResult[]
  total_deleted: number
  total_duration_ms: number
  vacuum_performed: boolean
  vacuum_error?: string
  success: boolean
}

/**
 * Maintenance status response.
 */
export interface MaintenanceStatus {
  enabled: boolean
  last_run_at?: string
  next_scheduled_at?: string
  config: RetentionPolicyConfig
  available_tasks: string[]
}

/**
 * Cache statistics.
 */
export interface CacheStats {
  total_entries: number
  expired_entries: number
  valid_entries: number
  max_size: number
  hit_rate?: number
}

/**
 * Get retention policy.
 */
export async function getRetentionPolicy(): Promise<RetentionPolicyConfig> {
  return request<RetentionPolicyConfig>('/maintenance/retention')
}

/**
 * Update retention policy.
 */
export async function updateRetentionPolicy(
  config: Partial<RetentionPolicyConfig>
): Promise<RetentionPolicyConfig> {
  return request<RetentionPolicyConfig>('/maintenance/retention', {
    method: 'PUT',
    body: JSON.stringify(config),
  })
}

/**
 * Get maintenance status.
 */
export async function getMaintenanceStatus(): Promise<MaintenanceStatus> {
  return request<MaintenanceStatus>('/maintenance/status')
}

/**
 * Trigger manual cleanup.
 */
export async function triggerCleanup(options?: {
  tasks?: string[]
  run_vacuum?: boolean
}): Promise<MaintenanceReport> {
  return request<MaintenanceReport>('/maintenance/cleanup', {
    method: 'POST',
    body: JSON.stringify(options || {}),
  })
}

/**
 * Run database vacuum.
 */
export async function runVacuum(): Promise<MaintenanceReport> {
  return request<MaintenanceReport>('/maintenance/vacuum', {
    method: 'POST',
  })
}

/**
 * Get cache statistics.
 */
export async function getCacheStats(): Promise<CacheStats> {
  return request<CacheStats>('/maintenance/cache/stats')
}

/**
 * Clear cache.
 */
export async function clearCache(options?: {
  pattern?: string
  namespace?: string
}): Promise<CacheStats> {
  return request<CacheStats>('/maintenance/cache/clear', {
    method: 'POST',
    body: JSON.stringify(options || {}),
  })
}

// ============================================================================
// Schema Evolution (Phase 6)
// ============================================================================

/**
 * Type of schema change.
 */
export type SchemaChangeType =
  | 'column_added'
  | 'column_removed'
  | 'type_changed'
  | 'nullable_changed'
  | 'constraint_changed'
  | 'column_renamed'

/**
 * Severity of schema change.
 */
export type SchemaChangeSeverity = 'breaking' | 'warning' | 'non_breaking'

/**
 * Summary of a schema version for listings.
 */
export interface SchemaVersionSummary {
  id: string
  version_number: number
  column_count: number
  created_at: string
}

/**
 * Full schema version response.
 */
export interface SchemaVersionResponse {
  id: string
  source_id: string
  schema_id: string
  version_number: number
  column_count: number
  columns: string[]
  schema_hash: string
  column_snapshot: Record<string, unknown>
  created_at: string
  updated_at: string
}

/**
 * Details about a schema change (type compatibility, reason, etc.).
 */
export interface SchemaChangeDetails {
  is_compatible?: boolean
  old_type_normalized?: string
  new_type_normalized?: string
  constraint_type?: string
  nullable?: boolean
  reason?: string
}

/**
 * Schema change record.
 */
export interface SchemaChangeResponse {
  id: string
  source_id: string
  from_version_id: string | null
  to_version_id: string
  change_type: SchemaChangeType
  column_name: string
  old_value: string | null
  new_value: string | null
  severity: SchemaChangeSeverity
  description: string
  details?: SchemaChangeDetails
  created_at: string
}

/**
 * Summary of schema evolution for a source.
 */
export interface SchemaEvolutionSummary {
  source_id: string
  current_version: number
  total_versions: number
  total_changes: number
  breaking_changes: number
  last_change_at: string | null
}

/**
 * Schema evolution detection result.
 */
export interface SchemaEvolutionResponse {
  source_id: string
  source_name: string
  from_version: number | null
  to_version: number
  has_changes: boolean
  total_changes: number
  breaking_changes: number
  changes: SchemaChangeResponse[]
  detected_at: string
}

/**
 * List schema versions for a source.
 */
export async function listSchemaVersions(
  sourceId: string,
  params?: { limit?: number; offset?: number }
): Promise<{ versions: SchemaVersionSummary[]; total: number; source_id: string }> {
  return request(`/sources/${sourceId}/schema/versions`, { params })
}

/**
 * Get a specific schema version.
 */
export async function getSchemaVersion(versionId: string): Promise<SchemaVersionResponse> {
  return request(`/schema/versions/${versionId}`)
}

/**
 * List schema changes for a source.
 */
export async function listSchemaChanges(
  sourceId: string,
  params?: { limit?: number; offset?: number }
): Promise<{ changes: SchemaChangeResponse[]; total: number; source_id: string }> {
  return request(`/sources/${sourceId}/schema/changes`, { params })
}

/**
 * Detect schema changes for a source (compare current schema with latest version).
 */
export async function detectSchemaChanges(
  sourceId: string,
  options?: { force_relearn?: boolean }
): Promise<SchemaEvolutionResponse> {
  return request(`/sources/${sourceId}/schema/detect-changes`, {
    method: 'POST',
    body: JSON.stringify(options || {}),
  })
}

/**
 * Get schema evolution summary for a source.
 */
export async function getSchemaEvolutionSummary(sourceId: string): Promise<SchemaEvolutionSummary> {
  return request(`/sources/${sourceId}/schema/evolution/summary`)
}

// ============================================================================
// Rule Suggestions (Phase 6) - Advanced Options
// ============================================================================

/**
 * Strictness level for rule generation.
 */
export type StrictnessLevel = 'loose' | 'medium' | 'strict'

/**
 * Preset templates for rule generation.
 */
export type RulePreset =
  | 'default'
  | 'strict'
  | 'loose'
  | 'minimal'
  | 'comprehensive'
  | 'ci_cd'
  | 'schema_only'
  | 'format_only'

/**
 * Export format for generated rules.
 */
export type RuleExportFormat = 'yaml' | 'json' | 'python' | 'toml'

/**
 * Categories of validation rules.
 */
export type RuleCategory =
  | 'schema'
  | 'stats'
  | 'pattern'
  | 'completeness'
  | 'uniqueness'
  | 'distribution'
  | 'relationship'
  | 'multi_column'

/**
 * A single suggested validation rule.
 */
export interface SuggestedRule {
  id: string
  column: string
  validator_name: string
  params: Record<string, unknown>
  confidence: number
  reason: string
  severity_suggestion: string
  category: RuleCategory | string
}

/**
 * Cross-column rule type.
 */
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

/**
 * A cross-column rule suggestion.
 */
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

/**
 * Request options for generating rule suggestions.
 */
export interface RuleSuggestionRequest {
  use_latest_profile?: boolean
  profile_id?: string
  min_confidence?: number
  // Advanced options
  strictness?: StrictnessLevel
  preset?: RulePreset
  include_categories?: RuleCategory[]
  exclude_categories?: RuleCategory[]
  include_types?: string[]
  exclude_columns?: string[]
  // Cross-column options
  enable_cross_column?: boolean
  include_cross_column_types?: CrossColumnRuleType[]
  exclude_cross_column_types?: CrossColumnRuleType[]
}

/**
 * Response containing suggested rules.
 */
export interface RuleSuggestionResponse {
  source_id: string
  source_name: string
  profile_id: string
  suggestions: SuggestedRule[]
  total_suggestions: number
  high_confidence_count: number
  generated_at: string
  // Generation settings
  strictness: StrictnessLevel
  preset: RulePreset | null
  categories_included: RuleCategory[]
  by_category: Record<string, number>
  // Cross-column suggestions
  cross_column_suggestions?: CrossColumnRuleSuggestion[]
  cross_column_count?: number
  by_cross_column_type?: Record<string, number>
}

/**
 * Request to apply selected rule suggestions.
 */
export interface ApplyRulesRequest {
  suggestions?: SuggestedRule[]
  rule_ids?: string[]  // Alternative: apply by IDs
  create_new_rule?: boolean
  rule_name?: string
  rule_description?: string
}

/**
 * Response after applying rule suggestions.
 */
export interface ApplyRulesResponse {
  source_id: string
  rule_id: string
  rule_name: string
  applied_count: number
  validators: string[]
  created_at: string
}

/**
 * Request to export rules.
 */
export interface ExportRulesRequest {
  suggestions: SuggestedRule[]
  format: RuleExportFormat
  include_metadata?: boolean
  rule_name?: string
  description?: string
}

/**
 * Response containing exported rules.
 */
export interface ExportRulesResponse {
  content: string
  format: RuleExportFormat
  filename: string
  rule_count: number
  generated_at: string
}

/**
 * Information about a preset.
 */
export interface PresetInfo {
  name: RulePreset
  display_name: string
  description: string
  strictness: StrictnessLevel
  categories: RuleCategory[]
  recommended_for: string
}

/**
 * Response listing available presets and options.
 */
export interface PresetsResponse {
  presets: PresetInfo[]
  strictness_levels: StrictnessLevel[]
  categories: RuleCategory[]
  export_formats: RuleExportFormat[]
}

/**
 * Generate rule suggestions from profile data.
 */
export async function suggestRules(
  sourceId: string,
  options?: RuleSuggestionRequest
): Promise<RuleSuggestionResponse> {
  return request(`/sources/${sourceId}/rules/suggest`, {
    method: 'POST',
    body: JSON.stringify(options || {}),
  })
}

/**
 * Apply selected rule suggestions.
 */
export async function applyRuleSuggestions(
  sourceId: string,
  data: ApplyRulesRequest
): Promise<ApplyRulesResponse> {
  return request(`/sources/${sourceId}/rules/apply-suggestions`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/**
 * Export rules in specified format.
 */
export async function exportRules(
  sourceId: string,
  data: ExportRulesRequest
): Promise<ExportRulesResponse> {
  return request(`/sources/${sourceId}/rules/export`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/**
 * Download exported rules as a file.
 */
export async function downloadExportedRules(
  sourceId: string,
  data: ExportRulesRequest
): Promise<Blob> {
  const response = await fetch(`${API_BASE}/sources/${sourceId}/rules/export/download`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    throw new Error(`Export failed: ${response.statusText}`)
  }
  return response.blob()
}

/**
 * Get available rule generation presets and options.
 */
export async function getRuleSuggestionPresets(): Promise<PresetsResponse> {
  return request('/rule-suggestions/presets')
}

// ============================================================================
// Profile Comparison (Phase 6)
// ============================================================================

/**
 * Trend direction for metrics.
 */
export type TrendDirection = 'up' | 'down' | 'stable'

/**
 * Summary of a profile for listing.
 */
export interface ProfileSummary {
  id: string
  source_id: string
  row_count: number
  column_count: number
  size_bytes: number
  created_at: string
}

/**
 * Column comparison result.
 */
export interface ColumnComparison {
  column: string
  metric: string
  baseline_value: number | string | null
  current_value: number | string | null
  change: number | null
  change_pct: number | null
  is_significant: boolean
  trend: TrendDirection
}

/**
 * Profile comparison summary.
 */
export interface ProfileComparisonSummary {
  total_columns: number
  columns_with_changes: number
  significant_changes: number
  columns_improved: number
  columns_degraded: number
}

/**
 * Profile comparison result.
 */
export interface ProfileComparisonResponse {
  source_id: string
  source_name: string
  baseline_profile_id: string
  current_profile_id: string
  baseline_timestamp: string
  current_timestamp: string
  row_count_change: number
  row_count_change_pct: number
  column_count_change: number
  column_comparisons: ColumnComparison[]
  significant_changes: number
  summary: ProfileComparisonSummary
  compared_at: string
}

/**
 * Profile trend data point.
 */
export interface ProfileTrendPoint {
  timestamp: string
  profile_id: string
  row_count: number
  column_count: number
  avg_null_pct: number
  avg_unique_pct: number
  size_bytes: number
}

/**
 * Column trend data.
 */
export interface ColumnTrend {
  column: string
  metric: string
  values: [string, number][]
  trend_direction: TrendDirection
  change_pct: number
  min_value: number | null
  max_value: number | null
  avg_value: number | null
}

/**
 * Profile trend response.
 */
export interface ProfileTrendResponse {
  source_id: string
  source_name: string
  period: string
  granularity: string
  data_points: ProfileTrendPoint[]
  column_trends: ColumnTrend[]
  total_profiles: number
  row_count_trend: TrendDirection
  summary: Record<string, unknown>
}

/**
 * Latest comparison response.
 */
export interface LatestComparisonResponse {
  source_id: string
  has_previous: boolean
  comparison: ProfileComparisonResponse | null
}

/**
 * List profile history for a source.
 */
export async function listProfiles(
  sourceId: string,
  params?: { limit?: number; offset?: number }
): Promise<{ profiles: ProfileSummary[]; total: number; source_id: string }> {
  return request(`/sources/${sourceId}/profiles`, { params })
}

/**
 * Compare two profiles.
 */
export async function compareProfiles(data: {
  baseline_profile_id: string
  current_profile_id: string
  significance_threshold?: number
}): Promise<ProfileComparisonResponse> {
  return request('/profiles/compare', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/**
 * Get profile trends over time.
 */
export async function getProfileTrend(
  sourceId: string,
  options?: {
    period?: '7d' | '30d' | '90d'
    granularity?: 'hourly' | 'daily' | 'weekly' | 'monthly'
    columns?: string[]
    metrics?: string[]
  }
): Promise<ProfileTrendResponse> {
  const params: Record<string, string | number | boolean> = {}
  if (options?.period) params.period = options.period
  if (options?.granularity) params.granularity = options.granularity
  if (options?.columns?.length) params.columns = options.columns.join(',')
  if (options?.metrics?.length) params.metrics = options.metrics.join(',')
  return request(`/sources/${sourceId}/profiles/trend`, { params })
}

/**
 * Get latest profile comparison (current vs previous).
 */
export async function getLatestProfileComparison(
  sourceId: string
): Promise<LatestComparisonResponse> {
  return request(`/sources/${sourceId}/profiles/latest-comparison`)
}

// ============================================================================
// Versioning (Phase 4)
// ============================================================================

/**
 * Versioning strategy types.
 */
export type VersioningStrategy = 'incremental' | 'semantic' | 'timestamp' | 'gitlike'

/**
 * Version information.
 */
export interface VersionInfo {
  version_id: string
  version_number: string
  validation_id: string
  source_id: string
  strategy: VersioningStrategy
  created_at: string
  parent_version_id: string | null
  metadata: Record<string, unknown>
  content_hash: string | null
}

/**
 * Response for listing versions.
 */
export interface VersionListResponse {
  success: boolean
  data: VersionInfo[]
  total: number
  source_id: string
}

/**
 * Version diff/comparison result.
 */
export interface VersionDiff {
  from_version: VersionInfo
  to_version: VersionInfo
  issues_added: Array<Record<string, unknown>>
  issues_removed: Array<Record<string, unknown>>
  issues_changed: Array<{
    key: string
    from: Record<string, unknown>
    to: Record<string, unknown>
  }>
  summary_changes: Record<string, unknown>
  has_changes: boolean
}

/**
 * Version history response.
 */
export interface VersionHistoryResponse {
  success: boolean
  data: VersionInfo[]
  depth: number
}

/**
 * Create version response.
 */
export interface CreateVersionResponse {
  success: boolean
  data: VersionInfo
  message: string
}

/**
 * List versions for a source.
 */
export async function listVersions(
  sourceId: string,
  params?: { limit?: number }
): Promise<VersionListResponse> {
  return request<VersionListResponse>(`/versions/sources/${sourceId}`, { params })
}

/**
 * Get a specific version.
 */
export async function getVersion(versionId: string): Promise<VersionInfo> {
  return request<VersionInfo>(`/versions/${versionId}`)
}

/**
 * Get the latest version for a source.
 */
export async function getLatestVersion(sourceId: string): Promise<VersionInfo> {
  return request<VersionInfo>(`/versions/sources/${sourceId}/latest`)
}

/**
 * Compare two versions.
 */
export async function compareVersions(
  fromVersionId: string,
  toVersionId: string
): Promise<VersionDiff> {
  return request<VersionDiff>('/versions/compare', {
    method: 'POST',
    body: JSON.stringify({
      from_version_id: fromVersionId,
      to_version_id: toVersionId,
    }),
  })
}

/**
 * Get version history chain.
 */
export async function getVersionHistory(
  versionId: string,
  params?: { depth?: number }
): Promise<VersionHistoryResponse> {
  return request<VersionHistoryResponse>(`/versions/${versionId}/history`, { params })
}

/**
 * Create a new version for a validation.
 */
export async function createVersion(data: {
  validation_id: string
  strategy?: VersioningStrategy
  metadata?: Record<string, unknown>
}): Promise<CreateVersionResponse> {
  return request<CreateVersionResponse>('/versions/', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

// ============================================================================
// Version Rollback
// ============================================================================

/**
 * Rollback availability response.
 */
export interface RollbackAvailabilityResponse {
  success: boolean
  can_rollback: boolean
  current_version_id: string | null
  available_versions: number
  rollback_targets: VersionInfo[]
}

/**
 * Rollback response.
 */
export interface RollbackResponse {
  success: boolean
  source_id: string
  from_version: VersionInfo | null
  to_version: VersionInfo | null
  new_validation_id: string | null
  message: string
  rolled_back_at: string
}

/**
 * Check rollback availability for a source.
 */
export async function checkRollbackAvailability(
  sourceId: string
): Promise<RollbackAvailabilityResponse> {
  return request<RollbackAvailabilityResponse>(
    `/versions/sources/${sourceId}/rollback-availability`
  )
}

/**
 * Rollback to a previous version.
 */
export async function rollbackToVersion(
  sourceId: string,
  targetVersionId: string,
  createNewValidation = true
): Promise<RollbackResponse> {
  return request<RollbackResponse>(`/versions/sources/${sourceId}/rollback`, {
    method: 'POST',
    body: JSON.stringify({
      target_version_id: targetVersionId,
      create_new_validation: createNewValidation,
    }),
  })
}

// ============================================================================
// Chart Settings
// ============================================================================

/**
 * Supported chart libraries.
 */
export type ChartLibrary = 'recharts' | 'chartjs' | 'echarts' | 'plotly' | 'svg'

/**
 * Chart library configuration.
 */
export interface ChartLibraryConfig {
  library: ChartLibrary
  npm_package: string
  version: string
  supported_charts: string[]
  cdn_url: string | null
}

/**
 * Chart settings response.
 */
export interface ChartSettings {
  library: ChartLibrary
  theme: string
  primary_color: string
  animation_enabled: boolean
  default_height: number
  custom_options: Record<string, unknown>
  library_config: ChartLibraryConfig
  available_libraries: {
    library: ChartLibrary
    name: string
    npm_package: string
    supported_charts: string[]
  }[]
}

/**
 * Get chart settings.
 */
export async function getChartSettings(): Promise<ChartSettings> {
  return request<ChartSettings>('/settings/charts')
}

/**
 * Update chart settings.
 */
export async function updateChartSettings(settings: {
  library?: ChartLibrary
  theme?: string
  primary_color?: string
  animation_enabled?: boolean
  default_height?: number
  custom_options?: Record<string, unknown>
}): Promise<ChartSettings> {
  return request<ChartSettings>('/settings/charts', {
    method: 'PUT',
    body: JSON.stringify(settings),
  })
}

// ============================================================================
// Advanced Notifications (Phase 14)
// ============================================================================

// Routing Rules
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

export interface RuleTypeInfo {
  type: string
  name: string
  description: string
  param_schema: Record<string, unknown>
}

export interface RoutingRuleListResponse {
  items: RoutingRule[]
  total: number
  offset: number
  limit: number
}

export async function listRoutingRules(params?: {
  offset?: number
  limit?: number
  active_only?: boolean
}): Promise<RoutingRuleListResponse> {
  return request('/notifications/routing/rules', { params })
}

export async function getRoutingRule(id: string): Promise<RoutingRule> {
  return request(`/notifications/routing/rules/${id}`)
}

export async function createRoutingRule(data: {
  name: string
  rule_config: Record<string, unknown>
  actions: string[]
  priority?: number
  is_active?: boolean
  stop_on_match?: boolean
  metadata?: Record<string, unknown>
}): Promise<RoutingRule> {
  return request('/notifications/routing/rules', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateRoutingRule(
  id: string,
  data: {
    name?: string
    rule_config?: Record<string, unknown>
    actions?: string[]
    priority?: number
    is_active?: boolean
    stop_on_match?: boolean
    metadata?: Record<string, unknown>
  }
): Promise<RoutingRule> {
  return request(`/notifications/routing/rules/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteRoutingRule(id: string): Promise<void> {
  return request(`/notifications/routing/rules/${id}`, { method: 'DELETE' })
}

export async function getRuleTypes(): Promise<{ rule_types: RuleTypeInfo[] }> {
  return request('/notifications/routing/rules/types')
}

// Expression Validation
export interface ExpressionValidateRequest {
  expression: string
  timeout_seconds?: number
}

export interface ExpressionValidateResponse {
  valid: boolean
  error: string | null
  error_line: number | null
  preview_result: boolean | null
  preview_error: string | null
  warnings: string[]
}

/**
 * Validate a Python-like expression for use in routing rules.
 */
export async function validateExpression(
  data: ExpressionValidateRequest
): Promise<ExpressionValidateResponse> {
  return request('/notifications/routing/rules/validate-expression', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/**
 * Request type for Jinja2 template validation.
 */
export interface Jinja2ValidateRequest {
  /** The Jinja2 template string to validate */
  template: string
  /** Optional sample event data for rendering preview */
  sample_data?: Record<string, unknown>
  /** Optional expected result ("true" or "false") */
  expected_result?: string
}

/**
 * Response type for Jinja2 template validation.
 */
export interface Jinja2ValidateResponse {
  /** Whether the template is syntactically valid */
  valid: boolean
  /** Error message if validation failed */
  error: string | null
  /** Line number where error occurred (if applicable) */
  error_line: number | null
  /** The rendered output if sample_data was provided */
  rendered_output: string | null
  /** Whether the rendered output matches expected result */
  matches_expected?: boolean
  /** Error during rendering (template valid but render failed) */
  render_error?: string
}

/**
 * Validate a Jinja2 template for use in routing rules.
 */
export async function validateJinja2Template(
  data: Jinja2ValidateRequest
): Promise<Jinja2ValidateResponse> {
  return request('/notifications/routing/rules/validate-jinja2', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

// Deduplication
export type DeduplicationStrategy = 'sliding' | 'tumbling' | 'session' | 'adaptive'
export type DeduplicationPolicy = 'none' | 'basic' | 'severity' | 'issue_based' | 'strict' | 'custom'

export interface DeduplicationConfig {
  id: string
  name: string
  strategy: DeduplicationStrategy
  policy: DeduplicationPolicy
  window_seconds: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface DeduplicationStats {
  total_received: number
  total_deduplicated: number
  total_passed: number
  dedup_rate: number
  active_fingerprints: number
}

export interface DeduplicationConfigListResponse {
  items: DeduplicationConfig[]
  total: number
  offset: number
  limit: number
}

export async function listDeduplicationConfigs(params?: {
  offset?: number
  limit?: number
  active_only?: boolean
}): Promise<DeduplicationConfigListResponse> {
  return request('/notifications/deduplication/configs', { params })
}

export async function getDeduplicationConfig(id: string): Promise<DeduplicationConfig> {
  return request(`/notifications/deduplication/configs/${id}`)
}

export async function createDeduplicationConfig(data: {
  name: string
  strategy?: DeduplicationStrategy
  policy?: DeduplicationPolicy
  window_seconds?: number
  is_active?: boolean
}): Promise<DeduplicationConfig> {
  return request('/notifications/deduplication/configs', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateDeduplicationConfig(
  id: string,
  data: {
    name?: string
    strategy?: DeduplicationStrategy
    policy?: DeduplicationPolicy
    window_seconds?: number
    is_active?: boolean
  }
): Promise<DeduplicationConfig> {
  return request(`/notifications/deduplication/configs/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteDeduplicationConfig(id: string): Promise<void> {
  return request(`/notifications/deduplication/configs/${id}`, { method: 'DELETE' })
}

export async function getDeduplicationStats(): Promise<DeduplicationStats> {
  return request('/notifications/deduplication/stats')
}

// Throttling
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

export interface ThrottlingStats {
  total_received: number
  total_throttled: number
  total_passed: number
  throttle_rate: number
  current_window_count: number
}

export interface ThrottlingConfigListResponse {
  items: ThrottlingConfig[]
  total: number
  offset: number
  limit: number
}

export async function listThrottlingConfigs(params?: {
  offset?: number
  limit?: number
  active_only?: boolean
  channel_id?: string
}): Promise<ThrottlingConfigListResponse> {
  return request('/notifications/throttling/configs', { params })
}

export async function getThrottlingConfig(id: string): Promise<ThrottlingConfig> {
  return request(`/notifications/throttling/configs/${id}`)
}

export async function createThrottlingConfig(data: {
  name: string
  per_minute?: number | null
  per_hour?: number | null
  per_day?: number | null
  burst_allowance?: number
  channel_id?: string | null
  is_active?: boolean
}): Promise<ThrottlingConfig> {
  return request('/notifications/throttling/configs', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateThrottlingConfig(
  id: string,
  data: {
    name?: string
    per_minute?: number | null
    per_hour?: number | null
    per_day?: number | null
    burst_allowance?: number
    channel_id?: string | null
    is_active?: boolean
  }
): Promise<ThrottlingConfig> {
  return request(`/notifications/throttling/configs/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteThrottlingConfig(id: string): Promise<void> {
  return request(`/notifications/throttling/configs/${id}`, { method: 'DELETE' })
}

export async function getThrottlingStats(): Promise<ThrottlingStats> {
  return request('/notifications/throttling/stats')
}

// Escalation
export type EscalationState = 'pending' | 'triggered' | 'acknowledged' | 'escalated' | 'resolved'
export type EscalationTargetType = 'user' | 'group' | 'oncall' | 'channel'

export interface EscalationTarget {
  type: EscalationTargetType
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
  state: EscalationState
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

export interface EscalationStats {
  total_incidents: number
  by_state: Record<string, number>
  active_count: number
  total_policies: number
  avg_resolution_time_minutes: number | null
}

export interface EscalationPolicyListResponse {
  items: EscalationPolicy[]
  total: number
  offset: number
  limit: number
}

export interface EscalationIncidentListResponse {
  items: EscalationIncident[]
  total: number
  offset: number
  limit: number
}

export async function listEscalationPolicies(params?: {
  offset?: number
  limit?: number
  active_only?: boolean
}): Promise<EscalationPolicyListResponse> {
  return request('/notifications/escalation/policies', { params })
}

export async function getEscalationPolicy(id: string): Promise<EscalationPolicy> {
  return request(`/notifications/escalation/policies/${id}`)
}

export async function createEscalationPolicy(data: {
  name: string
  description?: string
  levels: EscalationLevel[]
  auto_resolve_on_success?: boolean
  max_escalations?: number
  is_active?: boolean
}): Promise<EscalationPolicy> {
  return request('/notifications/escalation/policies', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateEscalationPolicy(
  id: string,
  data: {
    name?: string
    description?: string
    levels?: EscalationLevel[]
    auto_resolve_on_success?: boolean
    max_escalations?: number
    is_active?: boolean
  }
): Promise<EscalationPolicy> {
  return request(`/notifications/escalation/policies/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteEscalationPolicy(id: string): Promise<void> {
  return request(`/notifications/escalation/policies/${id}`, { method: 'DELETE' })
}

export async function listEscalationIncidents(params?: {
  offset?: number
  limit?: number
  state?: EscalationState
  policy_id?: string
}): Promise<EscalationIncidentListResponse> {
  return request('/notifications/escalation/incidents', { params })
}

export async function getEscalationIncident(id: string): Promise<EscalationIncident> {
  return request(`/notifications/escalation/incidents/${id}`)
}

export async function listActiveEscalationIncidents(): Promise<EscalationIncidentListResponse> {
  return request('/notifications/escalation/incidents/active')
}

export async function acknowledgeEscalationIncident(
  id: string,
  data: { actor: string; message?: string }
): Promise<EscalationIncident> {
  return request(`/notifications/escalation/incidents/${id}/acknowledge`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function resolveEscalationIncident(
  id: string,
  data: { actor?: string; message?: string }
): Promise<EscalationIncident> {
  return request(`/notifications/escalation/incidents/${id}/resolve`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function getEscalationStats(): Promise<EscalationStats> {
  return request('/notifications/escalation/stats')
}

// Escalation Scheduler
export interface EscalationSchedulerStatus {
  is_running: boolean
  check_interval_seconds: number
  last_check_at: string | null
  next_check_at: string | null
  total_checks: number
  total_escalations_triggered: number
  errors_count: number
}

export interface EscalationSchedulerConfig {
  check_interval_seconds: number
}

export async function getEscalationSchedulerStatus(): Promise<EscalationSchedulerStatus> {
  return request('/notifications/escalation/scheduler/status')
}

export async function startEscalationScheduler(): Promise<{ message: string; status: EscalationSchedulerStatus }> {
  return request('/notifications/escalation/scheduler/start', { method: 'POST' })
}

export async function stopEscalationScheduler(): Promise<{ message: string; status: EscalationSchedulerStatus }> {
  return request('/notifications/escalation/scheduler/stop', { method: 'POST' })
}

export async function triggerEscalationCheck(): Promise<{
  message: string
  incidents_checked: number
  escalations_triggered: number
}> {
  return request('/notifications/escalation/scheduler/trigger', { method: 'POST' })
}

export async function updateEscalationSchedulerConfig(
  config: EscalationSchedulerConfig
): Promise<{ message: string; status: EscalationSchedulerStatus }> {
  return request('/notifications/escalation/scheduler/config', {
    method: 'PUT',
    body: JSON.stringify(config),
  })
}

// Rule Testing / Dry-Run
export interface RuleTestContext {
  checkpoint_name?: string
  status?: 'success' | 'failure' | 'error'
  severity?: 'critical' | 'high' | 'medium' | 'low' | 'info'
  issue_count?: number
  pass_rate?: number
  tags?: string[]
  data_asset?: string
  metadata?: Record<string, unknown>
  timestamp?: string
}

export interface RuleTestResult {
  matched: boolean
  rule_type: string
  evaluation_time_ms: number
  match_details: Record<string, unknown>
  error?: string
}

export async function testRoutingRule(
  ruleConfig: Record<string, unknown>,
  context: RuleTestContext
): Promise<RuleTestResult> {
  return request('/notifications/routing/rules/test', {
    method: 'POST',
    body: JSON.stringify({ rule_config: ruleConfig, context }),
  })
}

// Combined Advanced Notification Stats
export interface AdvancedNotificationStats {
  routing: Record<string, number>
  deduplication: DeduplicationStats
  throttling: ThrottlingStats
  escalation: EscalationStats
}

export async function getAdvancedNotificationStats(): Promise<AdvancedNotificationStats> {
  return request('/notifications/advanced/stats')
}

// Config Import/Export Types
export type ConfigType = 'routing_rule' | 'deduplication' | 'throttling' | 'escalation'
export type ConflictResolution = 'skip' | 'overwrite' | 'rename'

export interface NotificationConfigBundle {
  version: string
  exported_at: string
  routing_rules: RoutingRule[]
  deduplication_configs: DeduplicationConfig[]
  throttling_configs: ThrottlingConfig[]
  escalation_policies: EscalationPolicy[]
}

export interface ConfigImportItem {
  config_type: ConfigType
  config_id: string
  action: 'create' | 'skip' | 'overwrite'
}

export interface ConfigImportRequest {
  bundle: NotificationConfigBundle
  conflict_resolution: ConflictResolution
  selected_items?: ConfigImportItem[] | null
}

export interface ConfigImportConflict {
  config_type: ConfigType
  config_id: string
  config_name: string
  existing_name: string
  suggested_action: ConflictResolution
}

export interface ConfigImportPreview {
  total_configs: number
  new_configs: number
  conflicts: ConfigImportConflict[]
  routing_rules_count: number
  deduplication_configs_count: number
  throttling_configs_count: number
  escalation_policies_count: number
}

export interface ConfigImportResult {
  success: boolean
  message: string
  created_count: number
  skipped_count: number
  overwritten_count: number
  errors: string[]
  created_ids: Record<string, string[]>
}

export interface ConfigExportOptions {
  include_routing_rules?: boolean
  include_deduplication?: boolean
  include_throttling?: boolean
  include_escalation?: boolean
}

/**
 * Export notification configurations as a JSON bundle.
 */
export async function exportNotificationConfig(
  options?: ConfigExportOptions
): Promise<NotificationConfigBundle> {
  const params: Record<string, string> = {}
  if (options?.include_routing_rules !== undefined) {
    params.include_routing_rules = String(options.include_routing_rules)
  }
  if (options?.include_deduplication !== undefined) {
    params.include_deduplication = String(options.include_deduplication)
  }
  if (options?.include_throttling !== undefined) {
    params.include_throttling = String(options.include_throttling)
  }
  if (options?.include_escalation !== undefined) {
    params.include_escalation = String(options.include_escalation)
  }
  return request('/notifications/config/export', { params })
}

/**
 * Download notification config as a JSON file.
 */
export async function downloadNotificationConfigAsFile(
  options?: ConfigExportOptions
): Promise<Blob> {
  const bundle = await exportNotificationConfig(options)
  const json = JSON.stringify(bundle, null, 2)
  return new Blob([json], { type: 'application/json' })
}

/**
 * Preview import operation to detect conflicts.
 */
export async function previewNotificationConfigImport(
  bundle: NotificationConfigBundle
): Promise<ConfigImportPreview> {
  return request('/notifications/config/import/preview', {
    method: 'POST',
    body: JSON.stringify(bundle),
  })
}

/**
 * Import notification configurations from a bundle.
 */
export async function importNotificationConfig(
  request_data: ConfigImportRequest
): Promise<ConfigImportResult> {
  return request('/notifications/config/import', {
    method: 'POST',
    body: JSON.stringify(request_data),
  })
}

/**
 * Parse an uploaded config file and validate its structure.
 */
export async function parseNotificationConfigFile(file: File): Promise<NotificationConfigBundle> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string
        const bundle = JSON.parse(content) as NotificationConfigBundle

        // Basic validation
        if (!bundle.version || !bundle.exported_at) {
          reject(new Error('Invalid config file: missing version or exported_at'))
          return
        }

        // Ensure arrays exist
        bundle.routing_rules = bundle.routing_rules || []
        bundle.deduplication_configs = bundle.deduplication_configs || []
        bundle.throttling_configs = bundle.throttling_configs || []
        bundle.escalation_policies = bundle.escalation_policies || []

        resolve(bundle)
      } catch (err) {
        reject(new Error(`Failed to parse config file: ${err instanceof Error ? err.message : 'Unknown error'}`))
      }
    }
    reader.onerror = () => reject(new Error('Failed to read file'))
    reader.readAsText(file)
  })
}

// ============================================================================
// Data Lineage (Phase 10)
// ============================================================================

/**
 * Lineage node types.
 */
export type LineageNodeType = 'source' | 'transform' | 'sink'

/**
 * Lineage edge types.
 */
export type LineageEdgeType = 'derives_from' | 'transforms_to' | 'feeds_into'

/**
 * Lineage node.
 */
export interface LineageNode {
  id: string
  name: string
  node_type: LineageNodeType
  source_id: string | null
  metadata: Record<string, unknown> | null
  position_x: number | null
  position_y: number | null
  created_at: string
  updated_at: string
}

/**
 * Lineage edge.
 */
export interface LineageEdge {
  id: string
  source_node_id: string
  target_node_id: string
  edge_type: LineageEdgeType
  metadata: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

/**
 * Full lineage graph response.
 */
export interface LineageGraph {
  nodes: LineageNode[]
  edges: LineageEdge[]
  total_nodes: number
  total_edges: number
}

/**
 * Impact analysis response.
 */
export interface ImpactAnalysisResponse {
  node_id: string
  node_name: string
  upstream: LineageNode[]
  downstream: LineageNode[]
  upstream_count: number
  downstream_count: number
  depth: number
}

/**
 * Auto-discover result.
 */
export interface AutoDiscoverResponse {
  nodes_created: number
  edges_created: number
  nodes: LineageNode[]
  edges: LineageEdge[]
  message: string
}

/**
 * Node position update request item.
 */
export interface NodePositionUpdate {
  node_id: string
  position_x: number
  position_y: number
}

/**
 * Request to create a lineage node.
 */
export interface LineageNodeCreate {
  name: string
  node_type: LineageNodeType
  source_id?: string
  metadata?: Record<string, unknown>
  position_x?: number
  position_y?: number
}

/**
 * Request to update a lineage node.
 */
export interface LineageNodeUpdate {
  name?: string
  node_type?: LineageNodeType
  source_id?: string | null
  metadata?: Record<string, unknown> | null
  position_x?: number | null
  position_y?: number | null
}

/**
 * Request to create a lineage edge.
 */
export interface LineageEdgeCreate {
  source_node_id: string
  target_node_id: string
  edge_type: LineageEdgeType
  metadata?: Record<string, unknown>
}

/**
 * Get the full lineage graph.
 */
export async function getLineageGraph(): Promise<LineageGraph> {
  return request<LineageGraph>('/lineage')
}

/**
 * Get lineage graph for a specific source.
 */
export async function getSourceLineage(
  sourceId: string,
  params?: { depth?: number }
): Promise<LineageGraph> {
  return request<LineageGraph>(`/lineage/sources/${sourceId}`, { params })
}

/**
 * Create a lineage node.
 */
export async function createLineageNode(data: LineageNodeCreate): Promise<LineageNode> {
  return request<LineageNode>('/lineage/nodes', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/**
 * Get a lineage node by ID.
 */
export async function getLineageNode(nodeId: string): Promise<LineageNode> {
  return request<LineageNode>(`/lineage/nodes/${nodeId}`)
}

/**
 * Update a lineage node.
 */
export async function updateLineageNode(
  nodeId: string,
  data: LineageNodeUpdate
): Promise<LineageNode> {
  return request<LineageNode>(`/lineage/nodes/${nodeId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

/**
 * Delete a lineage node.
 */
export async function deleteLineageNode(nodeId: string): Promise<{ message: string }> {
  return request<{ message: string }>(`/lineage/nodes/${nodeId}`, { method: 'DELETE' })
}

/**
 * Create a lineage edge.
 */
export async function createLineageEdge(data: LineageEdgeCreate): Promise<LineageEdge> {
  return request<LineageEdge>('/lineage/edges', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/**
 * Delete a lineage edge.
 */
export async function deleteLineageEdge(edgeId: string): Promise<{ message: string }> {
  return request<{ message: string }>(`/lineage/edges/${edgeId}`, { method: 'DELETE' })
}

/**
 * Run impact analysis for a node.
 */
export async function analyzeLineageImpact(
  nodeId: string,
  params?: { depth?: number }
): Promise<ImpactAnalysisResponse> {
  return request<ImpactAnalysisResponse>(`/lineage/nodes/${nodeId}/impact`, { params })
}

/**
 * Auto-discover lineage from database foreign keys.
 */
export async function autoDiscoverLineage(params?: {
  source_ids?: string[]
  include_fk?: boolean
}): Promise<AutoDiscoverResponse> {
  return request<AutoDiscoverResponse>('/lineage/auto-discover', {
    method: 'POST',
    body: JSON.stringify(params || {}),
  })
}

/**
 * Update positions of multiple nodes.
 */
export async function updateNodePositions(
  updates: NodePositionUpdate[]
): Promise<{ updated: number; message: string }> {
  return request<{ updated: number; message: string }>('/lineage/positions', {
    method: 'POST',
    body: JSON.stringify({ updates }),
  })
}

// ============================================================================
// OpenLineage Export (Phase 10)
// ============================================================================

/**
 * OpenLineage run state.
 */
export type OpenLineageRunState = 'START' | 'RUNNING' | 'COMPLETE' | 'FAIL' | 'ABORT'

/**
 * OpenLineage export format.
 */
export type OpenLineageExportFormat = 'json' | 'ndjson'

/**
 * OpenLineage dataset.
 */
export interface OpenLineageDataset {
  namespace: string
  name: string
  facets: Record<string, unknown>
}

/**
 * OpenLineage job.
 */
export interface OpenLineageJob {
  namespace: string
  name: string
  facets: Record<string, unknown>
}

/**
 * OpenLineage run.
 */
export interface OpenLineageRun {
  run_id: string
  facets: Record<string, unknown>
}

/**
 * OpenLineage event.
 */
export interface OpenLineageEvent {
  event_time: string
  eventType: OpenLineageRunState
  producer: string
  schemaURL: string
  run: OpenLineageRun
  job: OpenLineageJob
  inputs: OpenLineageDataset[]
  outputs: OpenLineageDataset[]
}

/**
 * OpenLineage export request.
 */
export interface OpenLineageExportRequest {
  job_namespace?: string
  job_name?: string
  source_id?: string
  include_schema?: boolean
  include_quality_metrics?: boolean
  format?: OpenLineageExportFormat
}

/**
 * OpenLineage export response.
 */
export interface OpenLineageExportResponse {
  events: OpenLineageEvent[]
  total_events: number
  total_datasets: number
  total_jobs: number
  export_time: string
}

/**
 * OpenLineage webhook configuration.
 */
export interface OpenLineageWebhookConfig {
  url: string
  api_key?: string
  headers?: Record<string, string>
  batch_size?: number
  timeout_seconds?: number
}

/**
 * OpenLineage emit request.
 */
export interface OpenLineageEmitRequest {
  webhook: OpenLineageWebhookConfig
  source_id?: string
  job_namespace?: string
  job_name?: string
}

/**
 * OpenLineage emit response.
 */
export interface OpenLineageEmitResponse {
  success: boolean
  events_sent: number
  failed_events: number
  error_message?: string
}

/**
 * OpenLineage specification info.
 */
export interface OpenLineageSpec {
  spec_version: string
  producer: string
  supported_facets: {
    dataset: string[]
    job: string[]
    run: string[]
  }
  supported_event_types: string[]
  export_formats: string[]
  documentation_url: string
}

/**
 * Export lineage as OpenLineage events.
 */
export async function exportOpenLineage(
  request?: OpenLineageExportRequest
): Promise<OpenLineageExportResponse> {
  return requestFn<OpenLineageExportResponse>('/lineage/openlineage/export', {
    method: 'POST',
    body: JSON.stringify(request || {}),
  })
}

/**
 * Export lineage as granular OpenLineage events (one job per transformation).
 */
export async function exportOpenLineageGranular(
  request?: OpenLineageExportRequest
): Promise<OpenLineageExportResponse> {
  return requestFn<OpenLineageExportResponse>('/lineage/openlineage/export/granular', {
    method: 'POST',
    body: JSON.stringify(request || {}),
  })
}

/**
 * Emit OpenLineage events to an external endpoint.
 */
export async function emitOpenLineage(
  request: OpenLineageEmitRequest
): Promise<OpenLineageEmitResponse> {
  return requestFn<OpenLineageEmitResponse>('/lineage/openlineage/emit', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

/**
 * Get OpenLineage specification info.
 */
export async function getOpenLineageSpec(): Promise<OpenLineageSpec> {
  return requestFn<OpenLineageSpec>('/lineage/openlineage/spec')
}

/**
 * Download OpenLineage events as JSON file.
 */
export function downloadOpenLineageJson(
  events: OpenLineageEvent[],
  filename = 'openlineage-events.json'
): void {
  const blob = new Blob([JSON.stringify(events, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

/**
 * Download OpenLineage events as NDJSON file (newline-delimited JSON).
 */
export function downloadOpenLineageNdjson(
  events: OpenLineageEvent[],
  filename = 'openlineage-events.ndjson'
): void {
  const ndjson = events.map((e) => JSON.stringify(e)).join('\n')
  const blob = new Blob([ndjson], { type: 'application/x-ndjson' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// ============================================================================
// OpenLineage Webhooks
// ============================================================================

/**
 * OpenLineage webhook event type.
 */
export type WebhookEventType = 'job' | 'dataset' | 'all'

/**
 * OpenLineage webhook configuration.
 */
export interface OpenLineageWebhook {
  id: string
  name: string
  url: string
  is_active: boolean
  headers: Record<string, string>
  event_types: WebhookEventType
  batch_size: number
  timeout_seconds: number
  last_sent_at: string | null
  success_count: number
  failure_count: number
  last_error: string | null
  created_at: string
  updated_at: string | null
}

/**
 * Create webhook request.
 */
export interface CreateWebhookRequest {
  name: string
  url: string
  is_active?: boolean
  headers?: Record<string, string>
  api_key?: string
  event_types?: WebhookEventType
  batch_size?: number
  timeout_seconds?: number
}

/**
 * Update webhook request.
 */
export interface UpdateWebhookRequest {
  name?: string
  url?: string
  is_active?: boolean
  headers?: Record<string, string>
  api_key?: string
  event_types?: WebhookEventType
  batch_size?: number
  timeout_seconds?: number
}

/**
 * Webhook list response.
 */
export interface WebhookListResponse {
  data: OpenLineageWebhook[]
  total: number
}

/**
 * Webhook test request.
 */
export interface WebhookTestRequest {
  url: string
  headers?: Record<string, string>
  api_key?: string
  timeout_seconds?: number
}

/**
 * Webhook test result.
 */
export interface WebhookTestResult {
  success: boolean
  status_code: number | null
  response_time_ms: number | null
  error_message: string | null
  response_body: string | null
}

/**
 * List all configured webhooks.
 */
export async function listWebhooks(activeOnly = false): Promise<WebhookListResponse> {
  return request<WebhookListResponse>('/lineage/openlineage/webhooks', {
    params: activeOnly ? { active_only: true } : undefined,
  })
}

/**
 * Get a specific webhook.
 */
export async function getWebhook(webhookId: string): Promise<OpenLineageWebhook> {
  return request<OpenLineageWebhook>(`/lineage/openlineage/webhooks/${webhookId}`)
}

/**
 * Create a new webhook.
 */
export async function createWebhook(data: CreateWebhookRequest): Promise<OpenLineageWebhook> {
  return request<OpenLineageWebhook>('/lineage/openlineage/webhooks', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/**
 * Update an existing webhook.
 */
export async function updateWebhook(
  webhookId: string,
  data: UpdateWebhookRequest
): Promise<OpenLineageWebhook> {
  return request<OpenLineageWebhook>(`/lineage/openlineage/webhooks/${webhookId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

/**
 * Delete a webhook.
 */
export async function deleteWebhook(webhookId: string): Promise<{ message: string }> {
  return request<{ message: string }>(`/lineage/openlineage/webhooks/${webhookId}`, {
    method: 'DELETE',
  })
}

/**
 * Test webhook connectivity.
 */
export async function testWebhook(data: WebhookTestRequest): Promise<WebhookTestResult> {
  return request<WebhookTestResult>('/lineage/openlineage/webhooks/test', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

// Alias for request function to avoid naming conflict
const requestFn = request

// ============================================================================
// Anomaly Detection (Phase 10)
// ============================================================================

/**
 * Anomaly detection algorithms.
 */
export type AnomalyAlgorithm =
  | 'isolation_forest'
  | 'lof'
  | 'one_class_svm'
  | 'dbscan'
  | 'statistical'
  | 'autoencoder'

/**
 * Anomaly detection status.
 */
export type AnomalyStatus = 'pending' | 'running' | 'success' | 'error'

/**
 * Algorithm category for UI grouping.
 */
export type AlgorithmCategory = 'tree' | 'density' | 'svm' | 'clustering' | 'statistical' | 'neural'

/**
 * Anomaly detection algorithms with descriptions.
 */
export const ANOMALY_ALGORITHMS: {
  value: AnomalyAlgorithm
  label: string
  description: string
  category: AlgorithmCategory
}[] = [
  {
    value: 'isolation_forest',
    label: 'Isolation Forest',
    description: 'Tree-based algorithm that isolates anomalies by random partitioning',
    category: 'tree',
  },
  {
    value: 'lof',
    label: 'Local Outlier Factor',
    description: 'Density-based algorithm comparing local density with neighbors',
    category: 'density',
  },
  {
    value: 'one_class_svm',
    label: 'One-Class SVM',
    description: 'SVM trained on normal data to create a decision boundary',
    category: 'svm',
  },
  {
    value: 'dbscan',
    label: 'DBSCAN',
    description: 'Density-based clustering that identifies outliers',
    category: 'clustering',
  },
  {
    value: 'statistical',
    label: 'Statistical',
    description: 'Z-score, IQR, or MAD based detection',
    category: 'statistical',
  },
  {
    value: 'autoencoder',
    label: 'Autoencoder',
    description: 'Neural network with high reconstruction error for anomalies',
    category: 'neural',
  },
]

/**
 * Single anomaly record.
 */
export interface AnomalyRecord {
  row_index: number
  anomaly_score: number
  column_values: Record<string, unknown>
  is_anomaly: boolean
}

/**
 * Column anomaly summary.
 */
export interface ColumnAnomalySummary {
  column: string
  dtype: string
  anomaly_count: number
  anomaly_rate: number
  mean_anomaly_score: number
  min_value: number | null
  max_value: number | null
  top_anomaly_indices: number[]
}

/**
 * Anomaly detection result.
 */
export interface AnomalyDetection {
  id: string
  source_id: string
  status: AnomalyStatus
  algorithm: AnomalyAlgorithm
  config: Record<string, unknown> | null
  total_rows: number | null
  anomaly_count: number | null
  anomaly_rate: number | null
  columns_analyzed: string[] | null
  column_summaries: ColumnAnomalySummary[] | null
  anomalies: AnomalyRecord[] | null
  duration_ms: number | null
  error_message: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
}

/**
 * Anomaly detection list response.
 */
export interface AnomalyDetectionListResponse {
  data: AnomalyDetection[]
  total: number
  offset: number
  limit: number
}

/**
 * Algorithm parameter definition.
 */
export interface AlgorithmParameter {
  name: string
  label: string
  type: 'integer' | 'float' | 'string' | 'select' | 'boolean'
  default: unknown
  min_value: number | null
  max_value: number | null
  options: string[] | null
  description: string
}

/**
 * Algorithm info.
 */
export interface AlgorithmInfo {
  name: AnomalyAlgorithm
  display_name: string
  description: string
  category: AlgorithmCategory
  parameters: AlgorithmParameter[]
  pros: string[]
  cons: string[]
  best_for: string
  requires_scaling: boolean
}

/**
 * Algorithm list response.
 */
export interface AlgorithmListResponse {
  algorithms: AlgorithmInfo[]
  total: number
}

/**
 * Anomaly detection request options.
 */
export interface AnomalyDetectionRequest {
  algorithm?: AnomalyAlgorithm
  columns?: string[]
  config?: Record<string, unknown>
  sample_size?: number
}

/**
 * Anomaly detection config used in the UI.
 */
export interface AnomalyDetectionConfig {
  algorithm: AnomalyAlgorithm
  columns: string[]
  params?: Record<string, unknown>
  sample_size?: number
}

/**
 * Run anomaly detection on a source.
 */
export async function runAnomalyDetection(
  sourceId: string,
  options?: AnomalyDetectionRequest
): Promise<AnomalyDetection> {
  return request<AnomalyDetection>(`/sources/${sourceId}/anomaly/detect`, {
    method: 'POST',
    body: JSON.stringify(options || {}),
  })
}

/**
 * Get an anomaly detection result by ID.
 */
export async function getAnomalyDetection(detectionId: string): Promise<AnomalyDetection> {
  return request<AnomalyDetection>(`/anomaly/${detectionId}`)
}

/**
 * List anomaly detections for a source.
 */
export async function listAnomalyDetections(
  sourceId: string,
  params?: { offset?: number; limit?: number }
): Promise<AnomalyDetectionListResponse> {
  return request<AnomalyDetectionListResponse>(`/sources/${sourceId}/anomaly/detections`, {
    params,
  })
}

/**
 * Get the latest anomaly detection for a source.
 */
export async function getLatestAnomalyDetection(sourceId: string): Promise<AnomalyDetection> {
  return request<AnomalyDetection>(`/sources/${sourceId}/anomaly/latest`)
}

/**
 * Get information about available anomaly detection algorithms.
 */
export async function listAnomalyAlgorithms(): Promise<AlgorithmListResponse> {
  return request<AlgorithmListResponse>('/anomaly/algorithms')
}

// ============================================================================
// Anomaly Explainability (SHAP/LIME)
// ============================================================================

/**
 * Feature contribution to anomaly score.
 */
export interface FeatureContribution {
  feature: string
  value: number
  shap_value: number
  contribution: number
}

/**
 * Explanation for a single anomalous row.
 */
export interface AnomalyExplanationResult {
  row_index: number
  anomaly_score: number
  feature_contributions: FeatureContribution[]
  total_shap: number
  summary: string
}

/**
 * Response containing anomaly explanations.
 */
export interface ExplainabilityResponse {
  detection_id: string
  algorithm: string
  row_indices: number[]
  feature_names: string[]
  explanations: AnomalyExplanationResult[]
  generated_at: string
  error?: string | null
}

/**
 * Request to generate explanations for anomalies.
 */
export interface ExplainabilityRequest {
  row_indices: number[]
  max_features?: number
  sample_background?: number
}

/**
 * Generate SHAP/LIME explanations for specific anomaly rows.
 */
export async function explainAnomaly(
  detectionId: string,
  rowIndices: number[],
  options?: {
    maxFeatures?: number
    sampleBackground?: number
  }
): Promise<ExplainabilityResponse> {
  const response = await request<ExplainabilityResponse>(
    `/anomaly/${detectionId}/explain`,
    {
      method: 'POST',
      body: JSON.stringify({
        row_indices: rowIndices,
        max_features: options?.maxFeatures,
        sample_background: options?.sampleBackground,
      }),
    }
  )
  return response
}

/**
 * Cached explanation from database.
 */
export interface CachedExplanation {
  id: string
  detection_id: string
  row_index: number
  anomaly_score: number
  feature_contributions: FeatureContribution[]
  total_shap: number
  summary: string
  generated_at: string | null
}

/**
 * Response containing list of cached explanations.
 */
export interface CachedExplanationsResponse {
  detection_id: string
  explanations: CachedExplanation[]
  total: number
}

/**
 * Get cached explanations for a detection.
 */
export async function getCachedExplanations(
  detectionId: string,
  rowIndices?: number[]
): Promise<CachedExplanationsResponse> {
  const params: Record<string, string> = {}
  if (rowIndices && rowIndices.length > 0) {
    params.row_indices = rowIndices.join(',')
  }
  return request<CachedExplanationsResponse>(
    `/anomaly/${detectionId}/explanations`,
    { params }
  )
}

// ============================================================================
// Batch Anomaly Detection (Phase 10)
// ============================================================================

/**
 * Batch detection job status.
 */
export type BatchDetectionStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'partial'
  | 'error'
  | 'cancelled'

/**
 * Result for a single source in a batch job.
 */
export interface BatchSourceResult {
  source_id: string
  source_name: string | null
  detection_id: string | null
  status: string
  anomaly_count: number | null
  anomaly_rate: number | null
  total_rows: number | null
  error_message: string | null
}

/**
 * Batch anomaly detection job.
 */
export interface BatchDetectionJob {
  id: string
  name: string | null
  status: BatchDetectionStatus
  algorithm: AnomalyAlgorithm
  config: Record<string, unknown> | null
  total_sources: number
  completed_sources: number
  failed_sources: number
  progress_percent: number
  current_source_id: string | null
  total_anomalies: number
  total_rows_analyzed: number
  average_anomaly_rate: number
  results: BatchSourceResult[] | null
  duration_ms: number | null
  error_message: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
}

/**
 * Batch detection list response.
 */
export interface BatchDetectionListResponse {
  data: BatchDetectionJob[]
  total: number
  offset: number
  limit: number
}

/**
 * Request to create a batch anomaly detection job.
 */
export interface BatchDetectionRequest {
  source_ids: string[]
  name?: string
  algorithm?: AnomalyAlgorithm
  config?: Record<string, unknown>
  sample_size?: number
}

/**
 * Create a batch anomaly detection job.
 */
export async function createBatchDetection(
  batchRequest: BatchDetectionRequest
): Promise<BatchDetectionJob> {
  return request<BatchDetectionJob>('/anomaly/batch', {
    method: 'POST',
    body: JSON.stringify(batchRequest),
  })
}

/**
 * Get batch detection job status.
 */
export async function getBatchDetection(batchId: string): Promise<BatchDetectionJob> {
  return request<BatchDetectionJob>(`/anomaly/batch/${batchId}`)
}

/**
 * Get batch detection results.
 */
export async function getBatchDetectionResults(batchId: string): Promise<BatchSourceResult[]> {
  return request<BatchSourceResult[]>(`/anomaly/batch/${batchId}/results`)
}

/**
 * List batch detection jobs.
 */
export async function listBatchDetections(params?: {
  offset?: number
  limit?: number
}): Promise<BatchDetectionListResponse> {
  return request<BatchDetectionListResponse>('/anomaly/batch', { params })
}

/**
 * Cancel a batch detection job.
 */
export async function cancelBatchDetection(batchId: string): Promise<BatchDetectionJob> {
  return request<BatchDetectionJob>(`/anomaly/batch/${batchId}/cancel`, {
    method: 'POST',
  })
}

/**
 * Delete a batch detection job.
 */
export async function deleteBatchDetection(batchId: string): Promise<void> {
  await request(`/anomaly/batch/${batchId}`, { method: 'DELETE' })
}

// ============================================================================
// Algorithm Comparison
// ============================================================================

/**
 * Level of agreement among algorithms.
 */
export type AgreementLevel = 'all' | 'majority' | 'some' | 'one'

/**
 * Request to compare multiple anomaly detection algorithms.
 */
export interface AlgorithmComparisonRequest {
  algorithms: AnomalyAlgorithm[]
  columns?: string[]
  config?: Record<string, Record<string, unknown>>
  sample_size?: number
}

/**
 * Single algorithm result within a comparison.
 */
export interface AlgorithmComparisonResultItem {
  algorithm: AnomalyAlgorithm
  display_name: string
  status: AnomalyStatus
  anomaly_count: number | null
  anomaly_rate: number | null
  duration_ms: number | null
  error_message: string | null
  anomaly_indices: number[]
}

/**
 * A row with its agreement information across algorithms.
 */
export interface AgreementRecord {
  row_index: number
  detected_by: AnomalyAlgorithm[]
  detection_count: number
  agreement_level: AgreementLevel
  confidence_score: number
  column_values: Record<string, unknown>
}

/**
 * Summary of algorithm agreement.
 */
export interface AgreementSummary {
  total_algorithms: number
  total_unique_anomalies: number
  all_agree_count: number
  majority_agree_count: number
  some_agree_count: number
  one_only_count: number
  agreement_matrix: number[][]
}

/**
 * Algorithm comparison result.
 */
export interface AlgorithmComparisonResult {
  id: string
  source_id: string
  status: AnomalyStatus
  total_rows: number | null
  columns_analyzed: string[] | null
  algorithm_results: AlgorithmComparisonResultItem[]
  agreement_summary: AgreementSummary | null
  agreement_records: AgreementRecord[] | null
  total_duration_ms: number | null
  error_message: string | null
  created_at: string
  completed_at: string | null
}

/**
 * Run multiple algorithms and compare results.
 */
export async function compareAlgorithms(
  sourceId: string,
  comparisonRequest: AlgorithmComparisonRequest
): Promise<AlgorithmComparisonResult> {
  return request<AlgorithmComparisonResult>(`/anomaly/compare?source_id=${sourceId}`, {
    method: 'POST',
    body: JSON.stringify(comparisonRequest),
  })
}

/**
 * Get a comparison result by ID.
 * Note: Comparison results are computed on-the-fly and not persisted.
 */
export async function getAlgorithmComparison(comparisonId: string): Promise<AlgorithmComparisonResult> {
  return request<AlgorithmComparisonResult>(`/anomaly/compare/${comparisonId}`)
}

// =============================================================================
// Streaming Anomaly Detection
// =============================================================================

/**
 * Streaming anomaly detection algorithm.
 */
export type StreamingAlgorithm =
  | 'zscore_rolling'
  | 'ema'
  | 'isolation_forest_incremental'
  | 'half_space_trees'
  | 'rrcf'

/**
 * Streaming session status.
 */
export type StreamingSessionStatus = 'created' | 'running' | 'paused' | 'stopped' | 'error'

/**
 * Rolling statistics for a column.
 */
export interface StreamingStatistics {
  count: number
  mean: number
  std: number
  min: number | null
  max: number | null
  anomaly_count: number
  anomaly_rate: number
}

/**
 * Streaming session configuration for creation.
 */
export interface StreamingSessionCreate {
  source_id?: string
  algorithm?: StreamingAlgorithm
  window_size?: number
  threshold?: number
  columns?: string[]
  config?: Record<string, unknown>
}

/**
 * Streaming session response.
 */
export interface StreamingSession {
  id: string
  source_id: string | null
  algorithm: StreamingAlgorithm
  window_size: number
  threshold: number
  columns: string[]
  status: StreamingSessionStatus
  config: Record<string, unknown> | null
  statistics: Record<string, StreamingStatistics> | null
  total_points: number
  total_alerts: number
  created_at: string
  started_at: string | null
  stopped_at: string | null
}

/**
 * Streaming session list response.
 */
export interface StreamingSessionListResponse {
  success: boolean
  data: StreamingSession[]
  total: number
  offset: number
  limit: number
}

/**
 * Data point to push to streaming session.
 */
export interface StreamingDataPoint {
  data: Record<string, unknown>
  timestamp?: string
}

/**
 * Batch of data points.
 */
export interface StreamingDataBatch {
  data_points: StreamingDataPoint[]
}

/**
 * Streaming anomaly alert.
 */
export interface StreamingAlert {
  id: string
  session_id: string
  timestamp: string
  data_point: Record<string, unknown>
  anomaly_score: number
  is_anomaly: boolean
  algorithm: StreamingAlgorithm
  details: Record<string, unknown>
}

/**
 * Streaming alert list response.
 */
export interface StreamingAlertListResponse {
  success: boolean
  data: StreamingAlert[]
  total: number
  offset: number
  limit: number
}

/**
 * Streaming session status response.
 */
export interface StreamingStatusResponse {
  session_id: string
  status: StreamingSessionStatus
  total_points: number
  total_alerts: number
  buffer_utilization: number
  statistics: Record<string, StreamingStatistics>
  recent_alerts: StreamingAlert[]
}

/**
 * Recent data response.
 */
export interface StreamingRecentDataResponse {
  session_id: string
  data_points: Array<{ timestamp: string; data: Record<string, unknown> }>
  total: number
}

/**
 * Streaming algorithm info.
 */
export interface StreamingAlgorithmInfo {
  name: StreamingAlgorithm
  display_name: string
  description: string
  supports_online_learning: boolean
  parameters: AlgorithmParameter[]
  best_for: string
}

/**
 * Streaming algorithm list response.
 */
export interface StreamingAlgorithmListResponse {
  algorithms: StreamingAlgorithmInfo[]
  total: number
}

/**
 * Start a new streaming anomaly detection session.
 */
export async function startStreamingSession(
  config: StreamingSessionCreate
): Promise<StreamingSession> {
  return request<StreamingSession>('/anomaly/streaming/start', {
    method: 'POST',
    body: JSON.stringify(config),
  })
}

/**
 * Push a data point to a streaming session.
 */
export async function pushStreamingData(
  sessionId: string,
  dataPoint: StreamingDataPoint
): Promise<StreamingAlert | null> {
  return request<StreamingAlert | null>(`/anomaly/streaming/${sessionId}/data`, {
    method: 'POST',
    body: JSON.stringify(dataPoint),
  })
}

/**
 * Push a batch of data points to a streaming session.
 */
export async function pushStreamingBatch(
  sessionId: string,
  batch: StreamingDataBatch
): Promise<StreamingAlert[]> {
  return request<StreamingAlert[]>(`/anomaly/streaming/${sessionId}/batch`, {
    method: 'POST',
    body: JSON.stringify(batch),
  })
}

/**
 * Get streaming session status.
 */
export async function getStreamingStatus(
  sessionId: string
): Promise<StreamingStatusResponse> {
  return request<StreamingStatusResponse>(`/anomaly/streaming/${sessionId}/status`)
}

/**
 * Stop a streaming session.
 */
export async function stopStreamingSession(
  sessionId: string
): Promise<StreamingSession> {
  return request<StreamingSession>(`/anomaly/streaming/${sessionId}/stop`, {
    method: 'POST',
  })
}

/**
 * Delete a streaming session.
 */
export async function deleteStreamingSession(sessionId: string): Promise<void> {
  await request(`/anomaly/streaming/${sessionId}`, { method: 'DELETE' })
}

/**
 * List alerts from a streaming session.
 */
export async function listStreamingAlerts(
  sessionId: string,
  params?: { offset?: number; limit?: number }
): Promise<StreamingAlertListResponse> {
  return request<StreamingAlertListResponse>(
    `/anomaly/streaming/${sessionId}/alerts`,
    { params }
  )
}

/**
 * Get recent data from a streaming session.
 */
export async function getStreamingRecentData(
  sessionId: string,
  limit?: number
): Promise<StreamingRecentDataResponse> {
  return request<StreamingRecentDataResponse>(
    `/anomaly/streaming/${sessionId}/data`,
    { params: limit ? { limit } : undefined }
  )
}

/**
 * List all streaming sessions.
 */
export async function listStreamingSessions(
  params?: { offset?: number; limit?: number }
): Promise<StreamingSessionListResponse> {
  return request<StreamingSessionListResponse>('/anomaly/streaming/sessions', {
    params,
  })
}

/**
 * Get information about available streaming algorithms.
 */
export async function listStreamingAlgorithms(): Promise<StreamingAlgorithmListResponse> {
  return request<StreamingAlgorithmListResponse>('/anomaly/streaming/algorithms')
}

/**
 * Get WebSocket URL for streaming session.
 */
export function getStreamingWebSocketUrl(sessionId: string): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  return `${protocol}//${host}/api/v1/anomaly/streaming/${sessionId}/ws`
}

// ============================================================================
// Trigger Monitoring Types
// ============================================================================

export interface TriggerEvaluation {
  should_trigger: boolean
  reason: string
  evaluated_at: string
}

export interface TriggerCheckStatus {
  schedule_id: string
  schedule_name: string
  trigger_type: string
  last_check_at: string | null
  next_check_at: string | null
  last_triggered_at: string | null
  check_count: number
  trigger_count: number
  is_due_for_check: boolean
  priority: number
  cooldown_remaining_seconds: number
  last_evaluation: TriggerEvaluation | null
}

export interface TriggerMonitoringStats {
  total_schedules: number
  active_data_change_triggers: number
  active_webhook_triggers: number
  active_composite_triggers: number
  total_checks_last_hour: number
  total_triggers_last_hour: number
  average_check_interval_seconds: number
  next_scheduled_check_at: string | null
}

export interface TriggerMonitoringResponse {
  stats: TriggerMonitoringStats
  schedules: TriggerCheckStatus[]
  checker_running: boolean
  checker_interval_seconds: number
  last_checker_run_at: string | null
}

export interface WebhookTriggerRequest {
  source: string
  event_type?: string
  payload?: Record<string, unknown>
  schedule_id?: string
  source_id?: string
  timestamp?: string
}

export interface WebhookTriggerResponse {
  accepted: boolean
  triggered_schedules: string[]
  message: string
  request_id: string
}

// ============================================================================
// Trigger Monitoring API
// ============================================================================

/**
 * Get trigger monitoring status.
 */
export async function getTriggerMonitoring(): Promise<TriggerMonitoringResponse> {
  return request<TriggerMonitoringResponse>('/triggers/monitoring')
}

/**
 * Get trigger status for a specific schedule.
 */
export async function getScheduleTriggerStatus(
  scheduleId: string
): Promise<TriggerCheckStatus> {
  return request<TriggerCheckStatus>(`/triggers/schedules/${scheduleId}/status`)
}

/**
 * Send webhook trigger.
 */
export async function sendWebhookTrigger(
  data: WebhookTriggerRequest,
  signature?: string
): Promise<WebhookTriggerResponse> {
  const headers: Record<string, string> = {}
  if (signature) {
    headers['X-Webhook-Signature'] = signature
  }
  return request<WebhookTriggerResponse>('/triggers/webhook', {
    method: 'POST',
    body: JSON.stringify(data),
    headers,
  })
}

/**
 * Test webhook endpoint connectivity.
 */
export async function testWebhookEndpoint(
  source: string = 'test',
  eventType: string = 'test_event'
): Promise<{ success: boolean; message: string; received: { source: string; event_type: string } }> {
  return request('/triggers/webhook/test', {
    method: 'POST',
    params: { source, event_type: eventType },
  })
}

// ============================================================================
// Plugin System Types
// ============================================================================

export type PluginType = 'validator' | 'reporter' | 'connector' | 'transformer'
export type PluginStatus = 'available' | 'installed' | 'enabled' | 'disabled' | 'update_available' | 'error'
export type PluginSource = 'official' | 'community' | 'local' | 'private'
export type SecurityLevel = 'trusted' | 'verified' | 'unverified' | 'sandboxed'
export type ValidatorParamType = 'string' | 'integer' | 'float' | 'boolean' | 'column' | 'column_list' | 'select' | 'multi_select' | 'regex' | 'json'
export type ReporterOutputFormat = 'pdf' | 'html' | 'json' | 'csv' | 'excel' | 'markdown' | 'custom'

export interface PluginAuthor {
  name: string
  email?: string
  url?: string
}

export interface PluginDependency {
  plugin_id: string
  version_constraint: string
  optional?: boolean
}

export interface Plugin {
  id: string
  name: string
  display_name: string
  description: string
  version: string
  latest_version?: string
  type: PluginType
  source: PluginSource
  status: PluginStatus
  security_level: SecurityLevel
  author?: PluginAuthor
  license?: string
  homepage?: string
  repository?: string
  keywords: string[]
  categories: string[]
  dependencies: PluginDependency[]
  permissions: string[]
  python_version?: string
  dashboard_version?: string
  icon_url?: string
  banner_url?: string
  documentation_url?: string
  changelog?: string
  readme?: string
  is_enabled: boolean
  install_count: number
  rating?: number
  rating_count: number
  validators_count: number
  reporters_count: number
  installed_at?: string
  last_updated?: string
  created_at: string
  updated_at: string
}

export interface PluginListResponse {
  data: Plugin[]
  total: number
  offset: number
  limit: number
}

export interface MarketplaceStats {
  total_plugins: number
  total_validators: number
  total_reporters: number
  total_installs: number
  categories: Array<{
    name: string
    display_name: string
    description: string
    icon?: string
    plugin_count: number
  }>
  featured_plugins: Plugin[]
  popular_plugins: Plugin[]
  recent_plugins: Plugin[]
}

export interface PluginInstallResponse {
  success: boolean
  plugin_id: string
  installed_version?: string
  message?: string
  warnings: string[]
}

export interface PluginUninstallResponse {
  success: boolean
  plugin_id: string
  message?: string
}

export interface ValidatorParamDefinition {
  name: string
  type: ValidatorParamType
  description: string
  required?: boolean
  default?: unknown
  options?: string[]
  min_value?: number
  max_value?: number
  pattern?: string
}

export interface ValidatorTestCase {
  name: string
  input: Record<string, unknown>
  expected_passed: boolean
  [key: string]: unknown  // Allow additional properties
}

export interface CustomValidator {
  id: string
  plugin_id?: string
  name: string
  display_name: string
  description: string
  category: string
  severity: 'error' | 'warning' | 'info'
  tags: string[]
  parameters: ValidatorParamDefinition[]
  code: string
  test_cases: ValidatorTestCase[]
  is_enabled: boolean
  is_verified: boolean
  usage_count: number
  last_used_at?: string
  created_at: string
  updated_at: string
}

export interface CustomValidatorListResponse {
  data: CustomValidator[]
  total: number
  offset: number
  limit: number
}

export interface ValidatorTestRequest {
  code: string
  parameters: ValidatorParamDefinition[]
  test_data: Record<string, unknown>
  param_values?: Record<string, unknown>
}

export interface ValidatorTestResultDetail {
  passed: boolean
  issues: Array<{
    message: string
    severity: string
    row?: number
  }>
  message: string
  details?: Record<string, unknown>
}

export interface ValidatorTestResponse {
  success: boolean
  passed?: boolean
  execution_time_ms: number
  result?: ValidatorTestResultDetail
  error?: string
  warnings: string[]
}

export interface ReporterFieldDefinition {
  name: string
  type: string
  label: string
  description?: string
  required?: boolean
  default?: unknown
  options?: Array<{ label: string; value: string }>
}

export interface CustomReporter {
  id: string
  plugin_id?: string
  name: string
  display_name: string
  description: string
  output_formats: ReporterOutputFormat[]
  config_fields: ReporterFieldDefinition[]
  template?: string
  code?: string
  preview_image_url?: string
  is_enabled: boolean
  is_verified: boolean
  usage_count: number
  created_at: string
  updated_at: string
}

export interface CustomReporterListResponse {
  data: CustomReporter[]
  total: number
  offset: number
  limit: number
}

export interface ReporterGenerateResponse {
  success: boolean
  report_id?: string
  download_url?: string
  preview_html?: string
  error?: string
  generation_time_ms: number
}

// ============================================================================
// Plugin System API Functions
// ============================================================================

/**
 * List plugins with optional filtering.
 */
export async function listPlugins(params?: {
  type?: PluginType
  status?: PluginStatus
  search?: string
  offset?: number
  limit?: number
}): Promise<PluginListResponse> {
  return request<PluginListResponse>('/plugins', { params: params as Record<string, string | number | boolean> })
}

/**
 * Get marketplace statistics.
 */
export async function getMarketplaceStats(): Promise<MarketplaceStats> {
  return request<MarketplaceStats>('/plugins/stats')
}

/**
 * Search plugins in marketplace.
 */
export async function searchPlugins(query: {
  query?: string
  types?: PluginType[]
  sources?: PluginSource[]
  categories?: string[]
  min_rating?: number
  verified_only?: boolean
  sort_by?: 'relevance' | 'rating' | 'installs' | 'updated' | 'name'
  sort_order?: 'asc' | 'desc'
  offset?: number
  limit?: number
}): Promise<PluginListResponse> {
  return request<PluginListResponse>('/plugins/search', {
    method: 'POST',
    body: JSON.stringify(query),
  })
}

/**
 * Get a plugin by ID.
 */
export async function getPlugin(pluginId: string): Promise<Plugin> {
  return request<Plugin>(`/plugins/${pluginId}`)
}

/**
 * Register a new plugin.
 */
export async function registerPlugin(data: Partial<Plugin>): Promise<Plugin> {
  return request<Plugin>('/plugins', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/**
 * Update a plugin.
 */
export async function updatePlugin(pluginId: string, data: Partial<Plugin>): Promise<Plugin> {
  return request<Plugin>(`/plugins/${pluginId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

/**
 * Install a plugin.
 */
export async function installPlugin(pluginId: string, options?: {
  version?: string
  force?: boolean
  enable_after_install?: boolean
}): Promise<PluginInstallResponse> {
  return request<PluginInstallResponse>(`/plugins/${pluginId}/install`, {
    method: 'POST',
    body: JSON.stringify({ plugin_id: pluginId, ...options }),
  })
}

/**
 * Uninstall a plugin.
 */
export async function uninstallPlugin(pluginId: string, removeData?: boolean): Promise<PluginUninstallResponse> {
  return request<PluginUninstallResponse>(`/plugins/${pluginId}/uninstall`, {
    method: 'POST',
    body: JSON.stringify({ plugin_id: pluginId, remove_data: removeData }),
  })
}

/**
 * Enable a plugin.
 */
export async function enablePlugin(pluginId: string): Promise<Plugin> {
  return request<Plugin>(`/plugins/${pluginId}/enable`, { method: 'POST' })
}

/**
 * Disable a plugin.
 */
export async function disablePlugin(pluginId: string): Promise<Plugin> {
  return request<Plugin>(`/plugins/${pluginId}/disable`, { method: 'POST' })
}

/**
 * List custom validators.
 */
export async function listCustomValidators(params?: {
  plugin_id?: string
  category?: string
  enabled_only?: boolean
  search?: string
  offset?: number
  limit?: number
}): Promise<CustomValidatorListResponse> {
  return request<CustomValidatorListResponse>('/validators/custom', { params: params as Record<string, string | number | boolean> })
}

/**
 * Get validator categories.
 */
export async function getValidatorCategories(): Promise<string[]> {
  return request<string[]>('/validators/custom/categories')
}

/**
 * Get validator template.
 */
export async function getValidatorTemplate(): Promise<{ template: string }> {
  return request<{ template: string }>('/validators/custom/template')
}

/**
 * Get a custom validator by ID.
 */
export async function getCustomValidator(validatorId: string): Promise<CustomValidator> {
  return request<CustomValidator>(`/validators/custom/${validatorId}`)
}

/**
 * Create a custom validator.
 */
export async function createCustomValidator(data: Partial<CustomValidator>): Promise<CustomValidator> {
  return request<CustomValidator>('/validators/custom', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/**
 * Update a custom validator.
 */
export async function updateCustomValidator(validatorId: string, data: Partial<CustomValidator>): Promise<CustomValidator> {
  return request<CustomValidator>(`/validators/custom/${validatorId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

/**
 * Delete a custom validator.
 */
export async function deleteCustomValidator(validatorId: string): Promise<void> {
  return request<void>(`/validators/custom/${validatorId}`, { method: 'DELETE' })
}

/**
 * Test a custom validator.
 */
export async function testCustomValidator(data: ValidatorTestRequest): Promise<ValidatorTestResponse> {
  return request<ValidatorTestResponse>('/validators/custom/test', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/**
 * List custom reporters.
 */
export async function listCustomReporters(params?: {
  plugin_id?: string
  is_enabled?: boolean
  enabled_only?: boolean
  search?: string
  offset?: number
  limit?: number
}): Promise<CustomReporterListResponse> {
  // Map is_enabled to enabled_only for API compatibility
  const apiParams: Record<string, string | number | boolean> = {}
  if (params) {
    if (params.plugin_id) apiParams.plugin_id = params.plugin_id
    if (params.is_enabled !== undefined) apiParams.enabled_only = params.is_enabled
    if (params.enabled_only !== undefined) apiParams.enabled_only = params.enabled_only
    if (params.search) apiParams.search = params.search
    if (params.offset !== undefined) apiParams.offset = params.offset
    if (params.limit !== undefined) apiParams.limit = params.limit
  }
  return request<CustomReporterListResponse>('/reporters/custom', { params: apiParams })
}

/**
 * Get reporter templates.
 */
export async function getReporterTemplates(): Promise<{ code_template: string; jinja2_template: string }> {
  return request<{ code_template: string; jinja2_template: string }>('/reporters/custom/templates')
}

/**
 * Get a custom reporter by ID.
 */
export async function getCustomReporter(reporterId: string): Promise<CustomReporter> {
  return request<CustomReporter>(`/reporters/custom/${reporterId}`)
}

/**
 * Create a custom reporter.
 */
export async function createCustomReporter(data: Partial<CustomReporter>): Promise<CustomReporter> {
  return request<CustomReporter>('/reporters/custom', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/**
 * Update a custom reporter.
 */
export async function updateCustomReporter(reporterId: string, data: Partial<CustomReporter>): Promise<CustomReporter> {
  return request<CustomReporter>(`/reporters/custom/${reporterId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

/**
 * Delete a custom reporter.
 */
export async function deleteCustomReporter(reporterId: string): Promise<void> {
  return request<void>(`/reporters/custom/${reporterId}`, { method: 'DELETE' })
}

/**
 * Preview a custom reporter.
 */
export async function previewCustomReporter(data: {
  template?: string
  code?: string
  sample_data?: Record<string, unknown>
  config?: Record<string, unknown>
  format?: string
}): Promise<ReporterGenerateResponse> {
  return request<ReporterGenerateResponse>('/reporters/custom/preview', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/**
 * Generate a report using a custom reporter.
 * Supports two modes:
 * 1. Provide validation_id to auto-fetch validation data
 * 2. Provide data directly for custom report generation
 */
export async function generateCustomReport(reporterId: string, data: {
  output_format: ReporterOutputFormat
  config?: Record<string, unknown>
  validation_id?: string
  data?: Record<string, unknown>
  source_ids?: string[]
}): Promise<ReporterGenerateResponse> {
  return request<ReporterGenerateResponse>(`/reporters/custom/${reporterId}/generate`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/**
 * Download a report generated by a custom reporter.
 * Returns the file as a blob for download.
 */
export async function downloadCustomReport(
  reporterId: string,
  validationId: string,
  options?: {
    output_format?: string
    config?: Record<string, unknown>
  }
): Promise<Blob> {
  const params = new URLSearchParams({
    validation_id: validationId,
    output_format: options?.output_format || 'html',
  })
  if (options?.config) {
    params.append('config', JSON.stringify(options.config))
  }

  const response = await fetch(`${API_BASE}/reporters/custom/${reporterId}/download?${params}`, {
    headers: {
      'Accept': '*/*',
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Download failed' }))
    throw new ApiError(error.detail || 'Download failed', String(response.status))
  }

  return response.blob()
}

// =============================================================================
// Report History API
// =============================================================================

export type ReportStatus = 'pending' | 'generating' | 'completed' | 'failed' | 'expired'

export interface GeneratedReport {
  id: string
  name: string
  description?: string
  format: string
  theme?: string
  locale: string
  config?: Record<string, unknown>
  metadata?: Record<string, unknown>
  validation_id?: string
  source_id?: string
  reporter_id?: string
  status: ReportStatus
  file_path?: string
  file_size?: number
  content_hash?: string
  error_message?: string
  generation_time_ms?: number
  expires_at?: string
  downloaded_count: number
  last_downloaded_at?: string
  created_at: string
  updated_at: string
  // Enriched fields
  source_name?: string
  reporter_name?: string
  download_url?: string
}

export interface GeneratedReportListResponse {
  items: GeneratedReport[]
  total: number
  page: number
  page_size: number
}

export interface ReportStatistics {
  total_reports: number
  total_size_bytes: number
  reports_by_format: Record<string, number>
  reports_by_status: Record<string, number>
  total_downloads: number
  avg_generation_time_ms?: number
  expired_count: number
  reporters_used: number
}

export interface BulkReportGenerateRequest {
  validation_ids: string[]
  format?: string
  theme?: string
  locale?: string
  reporter_id?: string
  config?: Record<string, unknown>
  save_to_history?: boolean
  expires_in_days?: number
}

export interface BulkReportGenerateResponse {
  total: number
  successful: number
  failed: number
  reports: GeneratedReport[]
  errors: Array<{ validation_id: string; error: string }>
}

/**
 * List generated reports with filtering and pagination.
 */
export async function listReportHistory(params?: {
  source_id?: string
  validation_id?: string
  reporter_id?: string
  format?: string
  status?: string
  include_expired?: boolean
  search?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  page?: number
  page_size?: number
}): Promise<GeneratedReportListResponse> {
  const apiParams: Record<string, string | number | boolean> = {}
  if (params) {
    if (params.source_id) apiParams.source_id = params.source_id
    if (params.validation_id) apiParams.validation_id = params.validation_id
    if (params.reporter_id) apiParams.reporter_id = params.reporter_id
    if (params.format) apiParams.format = params.format
    if (params.status) apiParams.status = params.status
    if (params.include_expired !== undefined) apiParams.include_expired = params.include_expired
    if (params.search) apiParams.search = params.search
    if (params.sort_by) apiParams.sort_by = params.sort_by
    if (params.sort_order) apiParams.sort_order = params.sort_order
    if (params.page !== undefined) apiParams.page = params.page
    if (params.page_size !== undefined) apiParams.page_size = params.page_size
  }
  return request<GeneratedReportListResponse>('/reports/history', { params: apiParams })
}

/**
 * Get report statistics.
 */
export async function getReportStatistics(): Promise<ReportStatistics> {
  return request<ReportStatistics>('/reports/history/statistics')
}

/**
 * Get a specific generated report by ID.
 */
export async function getGeneratedReport(reportId: string): Promise<GeneratedReport> {
  return request<GeneratedReport>(`/reports/history/${reportId}`)
}

/**
 * Create a new report record (without generating content).
 */
export async function createReportRecord(data: {
  name: string
  format: string
  validation_id?: string
  source_id?: string
  reporter_id?: string
  description?: string
  theme?: string
  locale?: string
  config?: Record<string, unknown>
  metadata?: Record<string, unknown>
  expires_in_days?: number
}): Promise<GeneratedReport> {
  return request<GeneratedReport>('/reports/history', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/**
 * Update a report record.
 */
export async function updateReportRecord(reportId: string, data: {
  name?: string
  description?: string
  metadata?: Record<string, unknown>
}): Promise<GeneratedReport> {
  return request<GeneratedReport>(`/reports/history/${reportId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

/**
 * Delete a report record.
 */
export async function deleteReportRecord(reportId: string): Promise<void> {
  return request<void>(`/reports/history/${reportId}`, { method: 'DELETE' })
}

/**
 * Download a saved report.
 */
export async function downloadSavedReport(reportId: string): Promise<Blob> {
  const response = await fetch(`${API_BASE}/reports/history/${reportId}/download`, {
    headers: {
      Accept: '*/*',
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Download failed' }))
    throw new ApiError(error.detail || 'Download failed', String(response.status))
  }

  return response.blob()
}

/**
 * Generate content for an existing report record.
 */
export async function generateReportContent(reportId: string): Promise<GeneratedReport> {
  return request<GeneratedReport>(`/reports/history/${reportId}/generate`, {
    method: 'POST',
  })
}

/**
 * Clean up expired reports.
 */
export async function cleanupExpiredReports(): Promise<{ deleted: number }> {
  return request<{ deleted: number }>('/reports/history/cleanup', { method: 'POST' })
}

/**
 * Generate reports in bulk.
 */
export async function generateBulkReports(data: BulkReportGenerateRequest): Promise<BulkReportGenerateResponse> {
  return request<BulkReportGenerateResponse>('/reports/bulk', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

// API client helper for direct requests
export const apiClient = {
  get: <T>(endpoint: string) => request<T>(endpoint),
  post: <T>(endpoint: string, data: unknown) =>
    request<T>(endpoint, { method: 'POST', body: JSON.stringify(data) }),
  put: <T>(endpoint: string, data: unknown) =>
    request<T>(endpoint, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (endpoint: string) => request(endpoint, { method: 'DELETE' }),
}

export { ApiError }
