/**
 * Plugin factory for generating mock plugin data
 */

import { faker } from '@faker-js/faker'
import { createId, createTimestamp, createRecentTimestamp } from './base'

// Wrapper for compatibility
function generateId(): string {
  return createId()
}

function generateTimestamps() {
  return {
    created_at: createTimestamp(faker.number.int({ min: 1, max: 365 })),
    updated_at: createRecentTimestamp(),
  }
}
import type {
  Plugin,
  PluginType,
  PluginStatus,
  PluginSource,
  SecurityLevel,
  CustomValidator,
  CustomReporter,
  ValidatorParamDefinition,
  ReporterFieldDefinition,
  ReporterOutputFormat,
} from '@/api/client'

const PLUGIN_TYPES: PluginType[] = ['validator', 'reporter', 'connector', 'transformer']
const PLUGIN_STATUSES: PluginStatus[] = ['available', 'installed', 'enabled', 'disabled']
const PLUGIN_SOURCES: PluginSource[] = ['official', 'community', 'local']
const SECURITY_LEVELS: SecurityLevel[] = ['trusted', 'verified', 'unverified', 'sandboxed']
const VALIDATOR_CATEGORIES = ['schema', 'completeness', 'uniqueness', 'distribution', 'string', 'datetime', 'custom']
const OUTPUT_FORMATS: ReporterOutputFormat[] = ['pdf', 'html', 'json', 'csv', 'excel', 'markdown']

export function createPlugin(overrides: Partial<Plugin> = {}): Plugin {
  const timestamps = generateTimestamps()
  const type = faker.helpers.arrayElement(PLUGIN_TYPES)
  const source = faker.helpers.arrayElement(PLUGIN_SOURCES)
  const status = faker.helpers.arrayElement(PLUGIN_STATUSES)
  const securityLevel = source === 'official' ? 'trusted' : faker.helpers.arrayElement(SECURITY_LEVELS)

  return {
    id: generateId(),
    name: faker.helpers.slugify(faker.commerce.productName()).toLowerCase(),
    display_name: faker.commerce.productName(),
    description: faker.lorem.paragraph(),
    version: faker.system.semver(),
    latest_version: faker.datatype.boolean() ? faker.system.semver() : undefined,
    type,
    source,
    status,
    security_level: securityLevel,
    author: {
      name: faker.person.fullName(),
      email: faker.internet.email(),
      url: faker.internet.url(),
    },
    license: faker.helpers.arrayElement(['MIT', 'Apache-2.0', 'BSD-3-Clause', 'GPL-3.0']),
    homepage: faker.internet.url(),
    repository: `https://github.com/${faker.internet.username()}/${faker.helpers.slugify(faker.commerce.productName())}`,
    keywords: faker.helpers.multiple(() => faker.word.noun(), { count: { min: 2, max: 5 } }),
    categories: faker.helpers.arrayElements(['data-quality', 'validation', 'reporting', 'integration', 'analytics'], { min: 1, max: 3 }),
    dependencies: faker.datatype.boolean() ? [{
      plugin_id: generateId(),
      version_constraint: `>=${faker.system.semver()}`,
      optional: faker.datatype.boolean(),
    }] : [],
    permissions: faker.helpers.arrayElements(['read_data', 'write_data', 'network_access'], { min: 0, max: 2 }),
    python_version: '>=3.9',
    dashboard_version: '>=1.0.0',
    icon_url: faker.datatype.boolean() ? faker.image.url() : undefined,
    banner_url: faker.datatype.boolean() ? faker.image.url() : undefined,
    documentation_url: faker.datatype.boolean() ? faker.internet.url() : undefined,
    changelog: faker.datatype.boolean() ? `## ${faker.system.semver()}\n- ${faker.git.commitMessage()}` : undefined,
    readme: faker.datatype.boolean() ? faker.lorem.paragraphs(3) : undefined,
    is_enabled: status === 'enabled',
    install_count: faker.number.int({ min: 0, max: 10000 }),
    rating: faker.datatype.boolean() ? faker.number.float({ min: 1, max: 5, fractionDigits: 1 }) : undefined,
    rating_count: faker.number.int({ min: 0, max: 500 }),
    validators_count: type === 'validator' ? faker.number.int({ min: 1, max: 10 }) : 0,
    reporters_count: type === 'reporter' ? faker.number.int({ min: 1, max: 5 }) : 0,
    installed_at: status !== 'available' ? timestamps.created_at : undefined,
    last_updated: timestamps.updated_at,
    ...timestamps,
    ...overrides,
  }
}

export function createValidatorParamDefinition(overrides: Partial<ValidatorParamDefinition> = {}): ValidatorParamDefinition {
  const type = faker.helpers.arrayElement(['string', 'integer', 'float', 'boolean', 'column', 'select'] as const)
  return {
    name: faker.helpers.slugify(faker.word.noun()).toLowerCase(),
    type,
    description: faker.lorem.sentence(),
    required: faker.datatype.boolean(),
    default: type === 'integer' ? faker.number.int({ min: 0, max: 100 }) :
             type === 'float' ? faker.number.float({ min: 0, max: 1, fractionDigits: 2 }) :
             type === 'boolean' ? faker.datatype.boolean() :
             type === 'select' ? faker.helpers.arrayElement(['option1', 'option2', 'option3']) :
             faker.word.noun(),
    options: type === 'select' ? ['option1', 'option2', 'option3'] : undefined,
    min_value: type === 'integer' || type === 'float' ? 0 : undefined,
    max_value: type === 'integer' || type === 'float' ? 100 : undefined,
    ...overrides,
  }
}

export function createCustomValidator(overrides: Partial<CustomValidator> = {}): CustomValidator {
  const timestamps = generateTimestamps()
  return {
    id: generateId(),
    plugin_id: faker.datatype.boolean() ? generateId() : undefined,
    name: faker.helpers.slugify(faker.commerce.productName()).toLowerCase() + '_validator',
    display_name: faker.commerce.productName() + ' Validator',
    description: faker.lorem.paragraph(),
    category: faker.helpers.arrayElement(VALIDATOR_CATEGORIES),
    severity: faker.helpers.arrayElement(['error', 'warning', 'info']),
    tags: faker.helpers.multiple(() => faker.word.noun(), { count: { min: 1, max: 4 } }),
    parameters: faker.helpers.multiple(() => createValidatorParamDefinition(), { count: { min: 0, max: 3 } }),
    code: `def validate(column_name, values, params, schema, row_count):
    """Custom validator implementation."""
    issues = []
    threshold = params.get('threshold', 0.1)

    # Example validation logic
    null_count = sum(1 for v in values if v is None)
    null_ratio = null_count / len(values) if values else 0

    if null_ratio > threshold:
        issues.append({
            "message": f"Null ratio {null_ratio:.2%} exceeds threshold {threshold:.2%}",
            "severity": "warning"
        })

    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "message": f"Validated {len(values)} values",
        "details": {"null_ratio": null_ratio}
    }`,
    test_cases: [{
      name: 'Test with valid data',
      input: { values: [1, 2, 3, 4, 5] },
      expected_passed: true,
    }],
    is_enabled: faker.datatype.boolean(0.8),
    is_verified: faker.datatype.boolean(0.3),
    usage_count: faker.number.int({ min: 0, max: 500 }),
    last_used_at: faker.datatype.boolean() ? faker.date.recent().toISOString() : undefined,
    ...timestamps,
    ...overrides,
  }
}

export function createReporterFieldDefinition(overrides: Partial<ReporterFieldDefinition> = {}): ReporterFieldDefinition {
  return {
    name: faker.helpers.slugify(faker.word.noun()).toLowerCase(),
    type: faker.helpers.arrayElement(['string', 'boolean', 'select', 'number']),
    label: faker.word.words(2),
    description: faker.lorem.sentence(),
    required: faker.datatype.boolean(),
    default: faker.word.noun(),
    options: faker.datatype.boolean() ? [
      { label: 'Option 1', value: 'option1' },
      { label: 'Option 2', value: 'option2' },
    ] : undefined,
    ...overrides,
  }
}

export function createCustomReporter(overrides: Partial<CustomReporter> = {}): CustomReporter {
  const timestamps = generateTimestamps()
  const hasTemplate = faker.datatype.boolean()

  return {
    id: generateId(),
    plugin_id: faker.datatype.boolean() ? generateId() : undefined,
    name: faker.helpers.slugify(faker.commerce.productName()).toLowerCase() + '_reporter',
    display_name: faker.commerce.productName() + ' Reporter',
    description: faker.lorem.paragraph(),
    output_formats: faker.helpers.arrayElements(OUTPUT_FORMATS, { min: 1, max: 3 }),
    config_fields: faker.helpers.multiple(() => createReporterFieldDefinition(), { count: { min: 0, max: 4 } }),
    template: hasTemplate ? `<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #fd9e4b; }
        .card { background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>{{ title }}</h1>
    <div class="card">
        <p>Generated: {{ metadata.generated_at }}</p>
        <p>Status: {{ status }}</p>
    </div>
</body>
</html>` : undefined,
    code: !hasTemplate ? `def generate_report(data, config, format, metadata):
    """Generate custom report."""
    html = f"""
    <html>
    <body>
        <h1>Validation Report</h1>
        <p>Generated: {metadata.get('generated_at', 'Unknown')}</p>
        <p>Total Issues: {len(data.get('issues', []))}</p>
    </body>
    </html>
    """
    return {
        "content": html,
        "content_type": "text/html",
        "filename": "report.html"
    }` : undefined,
    preview_image_url: faker.datatype.boolean() ? faker.image.url() : undefined,
    is_enabled: faker.datatype.boolean(0.8),
    is_verified: faker.datatype.boolean(0.3),
    usage_count: faker.number.int({ min: 0, max: 200 }),
    ...timestamps,
    ...overrides,
  }
}

// Generate initial mock data
export function generatePlugins(count: number = 15): Plugin[] {
  return faker.helpers.multiple(() => createPlugin(), { count })
}

export function generateCustomValidators(count: number = 8): CustomValidator[] {
  return faker.helpers.multiple(() => createCustomValidator(), { count })
}

export function generateCustomReporters(count: number = 5): CustomReporter[] {
  return faker.helpers.multiple(() => createCustomReporter(), { count })
}

// ============================================================================
// Advanced Plugin Features - Types
// ============================================================================

export type PluginState =
  | 'unloaded'
  | 'loading'
  | 'loaded'
  | 'initializing'
  | 'initialized'
  | 'starting'
  | 'running'
  | 'stopping'
  | 'stopped'
  | 'error'
  | 'disabled'

export type DependencyType = 'required' | 'optional' | 'dev' | 'peer' | 'conflict'

export type HookType =
  | 'pre_validation'
  | 'post_validation'
  | 'pre_profile'
  | 'post_profile'
  | 'pre_scan'
  | 'post_scan'
  | 'pre_mask'
  | 'post_mask'
  | 'pre_compare'
  | 'post_compare'
  | 'on_error'
  | 'on_success'
  | 'on_failure'
  | 'on_plugin_load'
  | 'on_plugin_unload'
  | 'on_config_change'

export type HookPriority = 'lowest' | 'low' | 'normal' | 'high' | 'highest'

export type SignatureAlgorithm = 'hmac_sha256' | 'rsa_sha256' | 'ed25519'

export type IsolationLevel = 'none' | 'process' | 'container'

export interface PluginLifecycleInfo {
  plugin_id: string
  current_state: PluginState
  previous_state?: PluginState
  state_changed_at: string
  error_message?: string
  error_traceback?: string
  allowed_transitions: PluginState[]
  state_history: Array<{
    from_state: PluginState
    to_state: PluginState
    timestamp: string
    reason?: string
  }>
}

export interface HotReloadConfig {
  enabled: boolean
  watch_paths: string[]
  debounce_ms: number
  reload_strategy: 'graceful' | 'immediate' | 'scheduled'
  max_reload_attempts: number
  backup_on_reload: boolean
}

export interface HotReloadStatus {
  plugin_id: string
  is_watching: boolean
  last_reload_at?: string
  reload_count: number
  last_error?: string
  watched_files: string[]
  pending_changes: boolean
}

export interface DependencyInfo {
  plugin_id: string
  version_constraint: string
  dependency_type: DependencyType
  resolved_version?: string
  is_installed: boolean
  is_satisfied: boolean
}

export interface DependencyGraphNode {
  plugin_id: string
  version: string
  dependencies: DependencyInfo[]
  dependents: string[]
  depth: number
}

export interface DependencyGraph {
  root_plugin_id: string
  nodes: DependencyGraphNode[]
  has_cycles: boolean
  cycle_path?: string[]
  install_order: string[]
  total_dependencies: number
}

export interface TrustedSigner {
  id: string
  name: string
  public_key: string
  algorithm: SignatureAlgorithm
  fingerprint: string
  trusted_since: string
  expires_at?: string
  trust_level: 'full' | 'partial' | 'revoked'
  plugins_signed: number
}

export interface SecurityPolicy {
  isolation_level: IsolationLevel
  allowed_imports: string[]
  blocked_imports: string[]
  network_access: boolean
  file_system_access: 'none' | 'read_only' | 'restricted' | 'full'
  max_memory_mb: number
  max_cpu_percent: number
  timeout_seconds: number
  require_signature: boolean
  min_trust_level: 'trusted' | 'verified' | 'unverified'
}

export interface SecurityAnalysisResult {
  plugin_id: string
  analyzed_at: string
  security_score: number
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  issues: Array<{
    severity: 'info' | 'warning' | 'error' | 'critical'
    category: string
    message: string
    location?: string
    recommendation?: string
  }>
  permissions_required: string[]
  dangerous_patterns: string[]
  external_dependencies: string[]
}

export interface HookRegistration {
  id: string
  plugin_id: string
  hook_type: HookType
  callback_name: string
  priority: HookPriority
  enabled: boolean
  created_at: string
  last_triggered_at?: string
  trigger_count: number
  average_execution_ms: number
  last_error?: string
}

export interface PluginDocumentation {
  plugin_id: string
  version: string
  extracted_at: string
  module_doc?: {
    name: string
    docstring?: string
    summary?: string
  }
  classes: Array<{
    name: string
    docstring?: string
    methods: Array<{
      name: string
      docstring?: string
      parameters: Array<{
        name: string
        type?: string
        default?: string
        description?: string
      }>
      returns?: { type?: string; description?: string }
    }>
  }>
  functions: Array<{
    name: string
    docstring?: string
    parameters: Array<{
      name: string
      type?: string
      default?: string
      description?: string
    }>
    returns?: { type?: string; description?: string }
  }>
  examples: Array<{
    title: string
    code: string
    description?: string
  }>
}

// ============================================================================
// Advanced Plugin Features - Factories
// ============================================================================

const PLUGIN_STATES: PluginState[] = [
  'unloaded', 'loading', 'loaded', 'initializing', 'initialized',
  'starting', 'running', 'stopping', 'stopped', 'error', 'disabled'
]

const HOOK_TYPES: HookType[] = [
  'pre_validation', 'post_validation', 'pre_profile', 'post_profile',
  'pre_scan', 'post_scan', 'pre_mask', 'post_mask', 'pre_compare', 'post_compare',
  'on_error', 'on_success', 'on_failure', 'on_plugin_load', 'on_plugin_unload', 'on_config_change'
]

const HOOK_PRIORITIES: HookPriority[] = ['lowest', 'low', 'normal', 'high', 'highest']

const SIGNATURE_ALGORITHMS: SignatureAlgorithm[] = ['hmac_sha256', 'rsa_sha256', 'ed25519']

export function createPluginLifecycleInfo(pluginId: string, overrides: Partial<PluginLifecycleInfo> = {}): PluginLifecycleInfo {
  const currentState = faker.helpers.arrayElement(['running', 'stopped', 'initialized'] as PluginState[])
  const stateHistory = faker.helpers.multiple(() => ({
    from_state: faker.helpers.arrayElement(PLUGIN_STATES),
    to_state: faker.helpers.arrayElement(PLUGIN_STATES),
    timestamp: faker.date.recent().toISOString(),
    reason: faker.datatype.boolean() ? faker.lorem.sentence() : undefined,
  }), { count: { min: 1, max: 5 } })

  return {
    plugin_id: pluginId,
    current_state: currentState,
    previous_state: stateHistory.length > 0 ? stateHistory[stateHistory.length - 1].from_state : undefined,
    state_changed_at: faker.date.recent().toISOString(),
    error_message: currentState === 'error' ? faker.lorem.sentence() : undefined,
    allowed_transitions: getValidTransitions(currentState),
    state_history: stateHistory,
    ...overrides,
  }
}

function getValidTransitions(state: PluginState): PluginState[] {
  const transitions: Record<PluginState, PluginState[]> = {
    unloaded: ['loading'],
    loading: ['loaded', 'error'],
    loaded: ['initializing', 'unloaded'],
    initializing: ['initialized', 'error'],
    initialized: ['starting', 'unloaded'],
    starting: ['running', 'error'],
    running: ['stopping', 'error'],
    stopping: ['stopped', 'error'],
    stopped: ['starting', 'unloaded'],
    error: ['unloaded'],
    disabled: ['unloaded'],
  }
  return transitions[state] || []
}

export function createHotReloadConfig(overrides: Partial<HotReloadConfig> = {}): HotReloadConfig {
  return {
    enabled: faker.datatype.boolean(0.7),
    watch_paths: faker.helpers.multiple(() => faker.system.filePath(), { count: { min: 1, max: 3 } }),
    debounce_ms: faker.helpers.arrayElement([100, 200, 500, 1000]),
    reload_strategy: faker.helpers.arrayElement(['graceful', 'immediate', 'scheduled']),
    max_reload_attempts: faker.number.int({ min: 1, max: 5 }),
    backup_on_reload: faker.datatype.boolean(0.8),
    ...overrides,
  }
}

export function createHotReloadStatus(pluginId: string, overrides: Partial<HotReloadStatus> = {}): HotReloadStatus {
  return {
    plugin_id: pluginId,
    is_watching: faker.datatype.boolean(0.6),
    last_reload_at: faker.datatype.boolean() ? faker.date.recent().toISOString() : undefined,
    reload_count: faker.number.int({ min: 0, max: 20 }),
    last_error: faker.datatype.boolean(0.1) ? faker.lorem.sentence() : undefined,
    watched_files: faker.helpers.multiple(() => faker.system.filePath(), { count: { min: 1, max: 5 } }),
    pending_changes: faker.datatype.boolean(0.2),
    ...overrides,
  }
}

export function createDependencyInfo(overrides: Partial<DependencyInfo> = {}): DependencyInfo {
  const isInstalled = faker.datatype.boolean(0.7)
  return {
    plugin_id: faker.helpers.slugify(faker.commerce.productName()).toLowerCase(),
    version_constraint: faker.helpers.arrayElement(['^1.0.0', '>=2.0.0', '~1.2.3', '>=1.0.0,<2.0.0']),
    dependency_type: faker.helpers.arrayElement(['required', 'optional', 'dev', 'peer'] as DependencyType[]),
    resolved_version: isInstalled ? faker.system.semver() : undefined,
    is_installed: isInstalled,
    is_satisfied: isInstalled && faker.datatype.boolean(0.9),
    ...overrides,
  }
}

export function createDependencyGraph(pluginId: string, pluginVersion: string, overrides: Partial<DependencyGraph> = {}): DependencyGraph {
  const dependencies = faker.helpers.multiple(() => createDependencyInfo(), { count: { min: 0, max: 5 } })
  const hasCycles = faker.datatype.boolean(0.1)

  return {
    root_plugin_id: pluginId,
    nodes: [{
      plugin_id: pluginId,
      version: pluginVersion,
      dependencies,
      dependents: [],
      depth: 0,
    }],
    has_cycles: hasCycles,
    cycle_path: hasCycles ? [pluginId, dependencies[0]?.plugin_id || 'dep-a', pluginId] : undefined,
    install_order: [pluginId, ...dependencies.map(d => d.plugin_id)],
    total_dependencies: dependencies.length,
    ...overrides,
  }
}

export function createTrustedSigner(overrides: Partial<TrustedSigner> = {}): TrustedSigner {
  const algorithm = faker.helpers.arrayElement(SIGNATURE_ALGORITHMS)
  return {
    id: generateId(),
    name: faker.company.name(),
    public_key: faker.string.alphanumeric(64),
    algorithm,
    fingerprint: faker.string.hexadecimal({ length: 40 }).substring(2),
    trusted_since: faker.date.past().toISOString(),
    expires_at: faker.datatype.boolean(0.3) ? faker.date.future().toISOString() : undefined,
    trust_level: faker.helpers.arrayElement(['full', 'partial'] as const),
    plugins_signed: faker.number.int({ min: 1, max: 50 }),
    ...overrides,
  }
}

export function createSecurityPolicy(overrides: Partial<SecurityPolicy> = {}): SecurityPolicy {
  return {
    isolation_level: faker.helpers.arrayElement(['none', 'process', 'container'] as IsolationLevel[]),
    allowed_imports: ['numpy', 'pandas', 'requests', 'json', 'datetime'],
    blocked_imports: ['os.system', 'subprocess', 'eval', 'exec'],
    network_access: faker.datatype.boolean(0.5),
    file_system_access: faker.helpers.arrayElement(['none', 'read_only', 'restricted', 'full']),
    max_memory_mb: faker.helpers.arrayElement([128, 256, 512, 1024]),
    max_cpu_percent: faker.helpers.arrayElement([25, 50, 75, 100]),
    timeout_seconds: faker.helpers.arrayElement([30, 60, 120, 300]),
    require_signature: faker.datatype.boolean(0.6),
    min_trust_level: faker.helpers.arrayElement(['trusted', 'verified', 'unverified']),
    ...overrides,
  }
}

export function createSecurityAnalysisResult(pluginId: string, overrides: Partial<SecurityAnalysisResult> = {}): SecurityAnalysisResult {
  const score = faker.number.int({ min: 40, max: 100 })
  const riskLevel = score >= 90 ? 'low' : score >= 70 ? 'medium' : score >= 50 ? 'high' : 'critical'

  const issues = faker.helpers.multiple(() => ({
    severity: faker.helpers.arrayElement(['info', 'warning', 'error', 'critical'] as const),
    category: faker.helpers.arrayElement(['code_quality', 'security', 'dependencies', 'permissions']),
    message: faker.lorem.sentence(),
    location: faker.datatype.boolean() ? `line ${faker.number.int({ min: 1, max: 200 })}` : undefined,
    recommendation: faker.datatype.boolean() ? faker.lorem.sentence() : undefined,
  }), { count: { min: 0, max: 5 } })

  return {
    plugin_id: pluginId,
    analyzed_at: faker.date.recent().toISOString(),
    security_score: score,
    risk_level: riskLevel,
    issues,
    permissions_required: faker.helpers.arrayElements(['read_data', 'write_data', 'network_access', 'file_system'], { min: 0, max: 3 }),
    dangerous_patterns: faker.datatype.boolean(0.2) ? ['eval()', 'exec()'] : [],
    external_dependencies: faker.helpers.multiple(() => faker.helpers.slugify(faker.word.noun()), { count: { min: 0, max: 5 } }),
    ...overrides,
  }
}

export function createHookRegistration(pluginId: string, overrides: Partial<HookRegistration> = {}): HookRegistration {
  const timestamps = generateTimestamps()
  return {
    id: generateId(),
    plugin_id: pluginId,
    hook_type: faker.helpers.arrayElement(HOOK_TYPES),
    callback_name: `on_${faker.word.verb()}_${faker.word.noun()}`,
    priority: faker.helpers.arrayElement(HOOK_PRIORITIES),
    enabled: faker.datatype.boolean(0.9),
    created_at: timestamps.created_at,
    last_triggered_at: faker.datatype.boolean() ? faker.date.recent().toISOString() : undefined,
    trigger_count: faker.number.int({ min: 0, max: 1000 }),
    average_execution_ms: faker.number.float({ min: 0.1, max: 100, fractionDigits: 2 }),
    last_error: faker.datatype.boolean(0.05) ? faker.lorem.sentence() : undefined,
    ...overrides,
  }
}

export function createPluginDocumentation(pluginId: string, version: string, overrides: Partial<PluginDocumentation> = {}): PluginDocumentation {
  const createParameter = () => ({
    name: faker.helpers.slugify(faker.word.noun()).toLowerCase(),
    type: faker.helpers.arrayElement(['str', 'int', 'float', 'bool', 'list', 'dict', 'Any']),
    default: faker.datatype.boolean() ? faker.word.noun() : undefined,
    description: faker.lorem.sentence(),
  })

  const createMethod = () => ({
    name: faker.helpers.slugify(faker.word.verb()).toLowerCase(),
    docstring: faker.lorem.paragraph(),
    parameters: faker.helpers.multiple(createParameter, { count: { min: 0, max: 4 } }),
    returns: faker.datatype.boolean() ? {
      type: faker.helpers.arrayElement(['str', 'int', 'bool', 'dict', 'list', 'None']),
      description: faker.lorem.sentence(),
    } : undefined,
  })

  return {
    plugin_id: pluginId,
    version,
    extracted_at: faker.date.recent().toISOString(),
    module_doc: {
      name: faker.helpers.slugify(faker.commerce.productName()).toLowerCase(),
      docstring: faker.lorem.paragraphs(2),
      summary: faker.lorem.sentence(),
    },
    classes: faker.helpers.multiple(() => ({
      name: faker.word.noun().charAt(0).toUpperCase() + faker.word.noun().slice(1) + 'Validator',
      docstring: faker.lorem.paragraph(),
      methods: faker.helpers.multiple(createMethod, { count: { min: 1, max: 5 } }),
    }), { count: { min: 1, max: 3 } }),
    functions: faker.helpers.multiple(() => ({
      name: faker.helpers.slugify(faker.word.verb()).toLowerCase(),
      docstring: faker.lorem.paragraph(),
      parameters: faker.helpers.multiple(createParameter, { count: { min: 0, max: 4 } }),
      returns: faker.datatype.boolean() ? {
        type: faker.helpers.arrayElement(['str', 'int', 'bool', 'dict']),
        description: faker.lorem.sentence(),
      } : undefined,
    }), { count: { min: 1, max: 5 } }),
    examples: faker.helpers.multiple(() => ({
      title: faker.lorem.words(3),
      code: `from ${faker.word.noun()} import ${faker.word.noun()}\n\nresult = ${faker.word.verb()}()\nprint(result)`,
      description: faker.lorem.sentence(),
    }), { count: { min: 1, max: 3 } }),
    ...overrides,
  }
}

// Generate collections
export function generateTrustedSigners(count: number = 5): TrustedSigner[] {
  return faker.helpers.multiple(() => createTrustedSigner(), { count })
}

export function generateHookRegistrations(pluginId: string, count: number = 5): HookRegistration[] {
  return faker.helpers.multiple(() => createHookRegistration(pluginId), { count })
}
