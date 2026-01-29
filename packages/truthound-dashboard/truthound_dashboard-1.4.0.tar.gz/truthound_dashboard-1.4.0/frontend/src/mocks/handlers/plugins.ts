/**
 * MSW handlers for Plugin System API
 */

import { http, HttpResponse, delay } from 'msw'
import {
  createPlugin,
  createCustomValidator,
  createCustomReporter,
  generatePlugins,
  generateCustomValidators,
  generateCustomReporters,
  createPluginLifecycleInfo,
  createHotReloadConfig,
  createHotReloadStatus,
  createDependencyGraph,
  createTrustedSigner,
  createSecurityPolicy,
  createSecurityAnalysisResult,
  createHookRegistration,
  createPluginDocumentation,
  generateTrustedSigners,
  generateHookRegistrations,
  type PluginLifecycleInfo,
  type HotReloadConfig,
  type HotReloadStatus,
  type TrustedSigner,
  type SecurityPolicy,
  type HookRegistration,
  type PluginState,
  type HookType,
} from '../factories/plugins'
import type { Plugin, CustomValidator, CustomReporter } from '@/api/client'

const API_BASE = '/api/v1'

// In-memory store
const plugins: Plugin[] = generatePlugins(15)
const validators: CustomValidator[] = generateCustomValidators(8)
const reporters: CustomReporter[] = generateCustomReporters(5)

// Advanced plugin features stores
const lifecycleStore = new Map<string, PluginLifecycleInfo>()
const hotReloadConfigStore = new Map<string, HotReloadConfig>()
const hotReloadStatusStore = new Map<string, HotReloadStatus>()
const trustedSigners: TrustedSigner[] = generateTrustedSigners(5)
let securityPolicy: SecurityPolicy = createSecurityPolicy()
const hookStore = new Map<string, HookRegistration[]>()

// Initialize stores for existing plugins
plugins.forEach(p => {
  lifecycleStore.set(p.id, createPluginLifecycleInfo(p.id))
  hotReloadConfigStore.set(p.id, createHotReloadConfig())
  hotReloadStatusStore.set(p.id, createHotReloadStatus(p.id))
  hookStore.set(p.id, generateHookRegistrations(p.id, 3))
})

export const pluginHandlers = [
  // ============================================================================
  // Plugin Marketplace
  // ============================================================================

  // List plugins
  http.get(`${API_BASE}/plugins`, async ({ request }) => {
    await delay(200)
    const url = new URL(request.url)
    const type = url.searchParams.get('type')
    const status = url.searchParams.get('status')
    const search = url.searchParams.get('search')
    const offset = parseInt(url.searchParams.get('offset') || '0')
    const limit = parseInt(url.searchParams.get('limit') || '20')

    let filtered = [...plugins]

    if (type) {
      filtered = filtered.filter(p => p.type === type)
    }
    if (status) {
      filtered = filtered.filter(p => p.status === status)
    }
    if (search) {
      const searchLower = search.toLowerCase()
      filtered = filtered.filter(p =>
        p.name.toLowerCase().includes(searchLower) ||
        p.display_name.toLowerCase().includes(searchLower) ||
        p.description.toLowerCase().includes(searchLower)
      )
    }

    const total = filtered.length
    const data = filtered.slice(offset, offset + limit)

    return HttpResponse.json({
      data,
      total,
      offset,
      limit,
    })
  }),

  // Get marketplace stats
  http.get(`${API_BASE}/plugins/stats`, async () => {
    await delay(100)
    return HttpResponse.json({
      total_plugins: plugins.length,
      total_validators: validators.length,
      total_reporters: reporters.length,
      total_installs: plugins.reduce((sum, p) => sum + p.install_count, 0),
      categories: [
        { name: 'data-quality', display_name: 'Data Quality', description: 'Data quality plugins', plugin_count: 5 },
        { name: 'validation', display_name: 'Validation', description: 'Validation plugins', plugin_count: 8 },
        { name: 'reporting', display_name: 'Reporting', description: 'Reporting plugins', plugin_count: 4 },
      ],
      featured_plugins: plugins.slice(0, 3),
      popular_plugins: [...plugins].sort((a, b) => b.install_count - a.install_count).slice(0, 5),
      recent_plugins: [...plugins].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).slice(0, 5),
    })
  }),

  // Search plugins
  http.post(`${API_BASE}/plugins/search`, async ({ request }) => {
    await delay(200)
    const body = await request.json() as {
      query?: string
      types?: string[]
      sources?: string[]
      min_rating?: number
      offset?: number
      limit?: number
    }

    let filtered = [...plugins]

    if (body.query) {
      const searchLower = body.query.toLowerCase()
      filtered = filtered.filter(p =>
        p.name.toLowerCase().includes(searchLower) ||
        p.display_name.toLowerCase().includes(searchLower) ||
        p.description.toLowerCase().includes(searchLower)
      )
    }
    if (body.types?.length) {
      filtered = filtered.filter(p => body.types!.includes(p.type))
    }
    if (body.sources?.length) {
      filtered = filtered.filter(p => body.sources!.includes(p.source))
    }
    if (body.min_rating) {
      filtered = filtered.filter(p => p.rating && p.rating >= body.min_rating!)
    }

    const offset = body.offset || 0
    const limit = body.limit || 20
    const total = filtered.length
    const data = filtered.slice(offset, offset + limit)

    return HttpResponse.json({ data, total, offset, limit })
  }),

  // Get plugin by ID
  http.get(`${API_BASE}/plugins/:pluginId`, async ({ params }) => {
    await delay(100)
    const plugin = plugins.find(p => p.id === params.pluginId)
    if (!plugin) {
      return HttpResponse.json({ detail: 'Plugin not found' }, { status: 404 })
    }
    return HttpResponse.json(plugin)
  }),

  // Register plugin
  http.post(`${API_BASE}/plugins`, async ({ request }) => {
    await delay(300)
    const body = await request.json() as Partial<Plugin>
    const newPlugin = createPlugin(body)
    plugins.push(newPlugin)
    return HttpResponse.json(newPlugin, { status: 201 })
  }),

  // Update plugin
  http.patch(`${API_BASE}/plugins/:pluginId`, async ({ params, request }) => {
    await delay(200)
    const index = plugins.findIndex(p => p.id === params.pluginId)
    if (index === -1) {
      return HttpResponse.json({ detail: 'Plugin not found' }, { status: 404 })
    }
    const body = await request.json() as Partial<Plugin>
    plugins[index] = { ...plugins[index], ...body, updated_at: new Date().toISOString() }
    return HttpResponse.json(plugins[index])
  }),

  // Install plugin
  http.post(`${API_BASE}/plugins/:pluginId/install`, async ({ params }) => {
    await delay(500)
    const index = plugins.findIndex(p => p.id === params.pluginId)
    if (index === -1) {
      return HttpResponse.json({ success: false, plugin_id: params.pluginId as string, message: 'Plugin not found' })
    }
    plugins[index].status = 'enabled'
    plugins[index].is_enabled = true
    plugins[index].install_count += 1
    plugins[index].installed_at = new Date().toISOString()

    return HttpResponse.json({
      success: true,
      plugin_id: params.pluginId,
      installed_version: plugins[index].version,
      message: `Plugin ${plugins[index].name} installed successfully`,
      warnings: [],
    })
  }),

  // Uninstall plugin
  http.post(`${API_BASE}/plugins/:pluginId/uninstall`, async ({ params }) => {
    await delay(300)
    const index = plugins.findIndex(p => p.id === params.pluginId)
    if (index === -1) {
      return HttpResponse.json({ success: false, plugin_id: params.pluginId as string, message: 'Plugin not found' })
    }
    plugins[index].status = 'available'
    plugins[index].is_enabled = false
    plugins[index].installed_at = undefined

    return HttpResponse.json({
      success: true,
      plugin_id: params.pluginId,
      message: 'Plugin uninstalled successfully',
    })
  }),

  // Enable plugin
  http.post(`${API_BASE}/plugins/:pluginId/enable`, async ({ params }) => {
    await delay(200)
    const index = plugins.findIndex(p => p.id === params.pluginId)
    if (index === -1) {
      return HttpResponse.json({ detail: 'Plugin not found' }, { status: 404 })
    }
    plugins[index].status = 'enabled'
    plugins[index].is_enabled = true
    return HttpResponse.json(plugins[index])
  }),

  // Disable plugin
  http.post(`${API_BASE}/plugins/:pluginId/disable`, async ({ params }) => {
    await delay(200)
    const index = plugins.findIndex(p => p.id === params.pluginId)
    if (index === -1) {
      return HttpResponse.json({ detail: 'Plugin not found' }, { status: 404 })
    }
    plugins[index].status = 'disabled'
    plugins[index].is_enabled = false
    return HttpResponse.json(plugins[index])
  }),

  // ============================================================================
  // Custom Validators
  // ============================================================================

  // List custom validators
  http.get(`${API_BASE}/validators/custom`, async ({ request }) => {
    await delay(200)
    const url = new URL(request.url)
    const pluginId = url.searchParams.get('plugin_id')
    const category = url.searchParams.get('category')
    const enabledOnly = url.searchParams.get('enabled_only') === 'true'
    const search = url.searchParams.get('search')
    const offset = parseInt(url.searchParams.get('offset') || '0')
    const limit = parseInt(url.searchParams.get('limit') || '20')

    let filtered = [...validators]

    if (pluginId) {
      filtered = filtered.filter(v => v.plugin_id === pluginId)
    }
    if (category) {
      filtered = filtered.filter(v => v.category === category)
    }
    if (enabledOnly) {
      filtered = filtered.filter(v => v.is_enabled)
    }
    if (search) {
      const searchLower = search.toLowerCase()
      filtered = filtered.filter(v =>
        v.name.toLowerCase().includes(searchLower) ||
        v.display_name.toLowerCase().includes(searchLower) ||
        v.description.toLowerCase().includes(searchLower)
      )
    }

    const total = filtered.length
    const data = filtered.slice(offset, offset + limit)

    return HttpResponse.json({ data, total, offset, limit })
  }),

  // Get validator categories
  http.get(`${API_BASE}/validators/custom/categories`, async () => {
    await delay(100)
    const categories = [...new Set(validators.map(v => v.category))]
    return HttpResponse.json(categories)
  }),

  // Get validator template
  http.get(`${API_BASE}/validators/custom/template`, async () => {
    await delay(100)
    return HttpResponse.json({
      template: `def validate(column_name, values, params, schema, row_count):
    """Custom validator function.

    Args:
        column_name: Name of the column being validated.
        values: List of values in the column.
        params: Dictionary of parameter values.
        schema: Column schema information.
        row_count: Total number of rows.

    Returns:
        Dictionary with:
            - passed: bool - Whether validation passed
            - issues: list - List of issue dictionaries
            - message: str - Summary message
            - details: dict - Additional details
    """
    issues = []

    # Example: Check for null values
    null_count = sum(1 for v in values if v is None)
    if null_count > 0:
        issues.append({
            "row": None,
            "message": f"Found {null_count} null values",
            "severity": "warning"
        })

    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "message": f"Validation completed with {len(issues)} issues",
        "details": {"null_count": null_count}
    }`,
    })
  }),

  // Get custom validator by ID
  http.get(`${API_BASE}/validators/custom/:validatorId`, async ({ params }) => {
    await delay(100)
    const validator = validators.find(v => v.id === params.validatorId)
    if (!validator) {
      return HttpResponse.json({ detail: 'Validator not found' }, { status: 404 })
    }
    return HttpResponse.json(validator)
  }),

  // Create custom validator
  http.post(`${API_BASE}/validators/custom`, async ({ request }) => {
    await delay(300)
    const body = await request.json() as Partial<CustomValidator>
    const newValidator = createCustomValidator(body)
    validators.push(newValidator)
    return HttpResponse.json(newValidator, { status: 201 })
  }),

  // Update custom validator
  http.patch(`${API_BASE}/validators/custom/:validatorId`, async ({ params, request }) => {
    await delay(200)
    const index = validators.findIndex(v => v.id === params.validatorId)
    if (index === -1) {
      return HttpResponse.json({ detail: 'Validator not found' }, { status: 404 })
    }
    const body = await request.json() as Partial<CustomValidator>
    validators[index] = { ...validators[index], ...body, updated_at: new Date().toISOString() }
    return HttpResponse.json(validators[index])
  }),

  // Delete custom validator
  http.delete(`${API_BASE}/validators/custom/:validatorId`, async ({ params }) => {
    await delay(200)
    const index = validators.findIndex(v => v.id === params.validatorId)
    if (index === -1) {
      return HttpResponse.json({ detail: 'Validator not found' }, { status: 404 })
    }
    validators.splice(index, 1)
    return new HttpResponse(null, { status: 204 })
  }),

  // Test custom validator
  http.post(`${API_BASE}/validators/custom/test`, async ({ request }) => {
    await delay(500)
    const body = await request.json() as {
      code: string
      parameters: unknown[]
      test_data: Record<string, unknown>
      param_values?: Record<string, unknown>
    }

    // Simulate test execution
    const passed = Math.random() > 0.3

    return HttpResponse.json({
      success: true,
      passed,
      execution_time_ms: Math.random() * 100,
      result: {
        passed,
        issues: passed ? [] : [{ message: 'Test validation issue', severity: 'warning' }],
        message: passed ? 'Validation passed' : 'Validation failed',
        details: { values_tested: (body.test_data.values as unknown[])?.length || 0 },
      },
      warnings: [],
    })
  }),

  // ============================================================================
  // Custom Reporters
  // ============================================================================

  // List custom reporters
  http.get(`${API_BASE}/reporters/custom`, async ({ request }) => {
    await delay(200)
    const url = new URL(request.url)
    const pluginId = url.searchParams.get('plugin_id')
    const enabledOnly = url.searchParams.get('enabled_only') === 'true'
    const search = url.searchParams.get('search')
    const offset = parseInt(url.searchParams.get('offset') || '0')
    const limit = parseInt(url.searchParams.get('limit') || '20')

    let filtered = [...reporters]

    if (pluginId) {
      filtered = filtered.filter(r => r.plugin_id === pluginId)
    }
    if (enabledOnly) {
      filtered = filtered.filter(r => r.is_enabled)
    }
    if (search) {
      const searchLower = search.toLowerCase()
      filtered = filtered.filter(r =>
        r.name.toLowerCase().includes(searchLower) ||
        r.display_name.toLowerCase().includes(searchLower) ||
        r.description.toLowerCase().includes(searchLower)
      )
    }

    const total = filtered.length
    const data = filtered.slice(offset, offset + limit)

    return HttpResponse.json({ data, total, offset, limit })
  }),

  // Get reporter templates
  http.get(`${API_BASE}/reporters/custom/templates`, async () => {
    await delay(100)
    return HttpResponse.json({
      code_template: `def generate_report(data, config, format, metadata):
    """Custom report generator function."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <body>
        <h1>Validation Report</h1>
        <p>Generated: {metadata.get('generated_at', 'Unknown')}</p>
    </body>
    </html>
    """
    return {
        "content": html,
        "content_type": "text/html",
        "filename": "report.html"
    }`,
      jinja2_template: `<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
</head>
<body>
    <h1>{{ title }}</h1>
    <p>Generated: {{ metadata.generated_at }}</p>
</body>
</html>`,
    })
  }),

  // Get custom reporter by ID
  http.get(`${API_BASE}/reporters/custom/:reporterId`, async ({ params }) => {
    await delay(100)
    const reporter = reporters.find(r => r.id === params.reporterId)
    if (!reporter) {
      return HttpResponse.json({ detail: 'Reporter not found' }, { status: 404 })
    }
    return HttpResponse.json(reporter)
  }),

  // Create custom reporter
  http.post(`${API_BASE}/reporters/custom`, async ({ request }) => {
    await delay(300)
    const body = await request.json() as Partial<CustomReporter>
    const newReporter = createCustomReporter(body)
    reporters.push(newReporter)
    return HttpResponse.json(newReporter, { status: 201 })
  }),

  // Update custom reporter
  http.patch(`${API_BASE}/reporters/custom/:reporterId`, async ({ params, request }) => {
    await delay(200)
    const index = reporters.findIndex(r => r.id === params.reporterId)
    if (index === -1) {
      return HttpResponse.json({ detail: 'Reporter not found' }, { status: 404 })
    }
    const body = await request.json() as Partial<CustomReporter>
    reporters[index] = { ...reporters[index], ...body, updated_at: new Date().toISOString() }
    return HttpResponse.json(reporters[index])
  }),

  // Delete custom reporter
  http.delete(`${API_BASE}/reporters/custom/:reporterId`, async ({ params }) => {
    await delay(200)
    const index = reporters.findIndex(r => r.id === params.reporterId)
    if (index === -1) {
      return HttpResponse.json({ detail: 'Reporter not found' }, { status: 404 })
    }
    reporters.splice(index, 1)
    return new HttpResponse(null, { status: 204 })
  }),

  // Preview custom reporter
  http.post(`${API_BASE}/reporters/custom/preview`, async () => {
    await delay(500)
    return HttpResponse.json({
      success: true,
      preview_html: `<!DOCTYPE html>
<html>
<head>
    <title>Preview Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #fd9e4b; }
        .card { background: #f5f5f5; padding: 15px; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>Preview Report</h1>
    <div class="card">
        <p>This is a preview of your custom report.</p>
        <p>Generated at: ${new Date().toISOString()}</p>
    </div>
</body>
</html>`,
      generation_time_ms: Math.random() * 200,
    })
  }),

  // Generate report (POST)
  http.post(`${API_BASE}/reporters/custom/:reporterId/generate`, async ({ params, request }) => {
    await delay(800)
    const reporter = reporters.find(r => r.id === params.reporterId)
    if (!reporter) {
      return HttpResponse.json({ success: false, error: 'Reporter not found' }, { status: 404 })
    }

    const body = await request.json() as {
      validation_id?: string
      output_format: string
      config?: Record<string, unknown>
      data?: Record<string, unknown>
    }

    const timestamp = new Date().toISOString()
    const format = body.output_format || 'html'
    const validationId = body.validation_id || 'mock-validation-id'

    const generatedContent = generateReportContent(reporter, format, validationId, timestamp)

    return HttpResponse.json({
      success: true,
      preview_html: generatedContent.content,
      generation_time_ms: Math.random() * 500,
    })
  }),

  // Download report (GET)
  http.get(`${API_BASE}/reporters/custom/:reporterId/download`, async ({ params, request }) => {
    await delay(500)
    const reporter = reporters.find(r => r.id === params.reporterId)
    if (!reporter) {
      return HttpResponse.json({ detail: 'Reporter not found' }, { status: 404 })
    }

    const url = new URL(request.url)
    const validationId = url.searchParams.get('validation_id') || 'mock-validation-id'
    const format = url.searchParams.get('output_format') || 'html'
    const timestamp = new Date().toISOString()

    const generatedContent = generateReportContent(reporter, format, validationId, timestamp)

    return new HttpResponse(generatedContent.content, {
      status: 200,
      headers: {
        'Content-Type': generatedContent.contentType,
        'Content-Disposition': `attachment; filename="${generatedContent.filename}"`,
        'Content-Length': String(generatedContent.content.length),
      },
    })
  }),

  // Check for plugin updates
  http.get(`${API_BASE}/plugins/:pluginId/check-update`, async ({ params }) => {
    await delay(300)
    const plugin = plugins.find(p => p.id === params.pluginId)
    if (!plugin) {
      return HttpResponse.json({ detail: 'Plugin not found' }, { status: 404 })
    }

    // Simulate update availability for some plugins
    const hasUpdate = Math.random() > 0.6
    const currentVersion = plugin.version
    const latestVersion = hasUpdate
      ? currentVersion.replace(/(\d+)\.(\d+)\.(\d+)/, (_, major, minor, patch) =>
          `${major}.${parseInt(minor) + 1}.${patch}`
        )
      : currentVersion

    return HttpResponse.json({
      has_update: hasUpdate,
      current_version: currentVersion,
      latest_version: latestVersion,
      changelog: hasUpdate
        ? `## v${latestVersion}\n\n- Bug fixes and improvements\n- Performance enhancements\n- New features`
        : null,
      release_date: hasUpdate ? new Date().toISOString() : null,
    })
  }),

  // Update plugin
  http.post(`${API_BASE}/plugins/:pluginId/update`, async ({ params }) => {
    await delay(800)
    const index = plugins.findIndex(p => p.id === params.pluginId)
    if (index === -1) {
      return HttpResponse.json({ detail: 'Plugin not found' }, { status: 404 })
    }

    // Simulate version bump
    const currentVersion = plugins[index].version
    const newVersion = currentVersion.replace(/(\d+)\.(\d+)\.(\d+)/, (_, major, minor, patch) =>
      `${major}.${parseInt(minor) + 1}.${patch}`
    )

    plugins[index] = {
      ...plugins[index],
      version: newVersion,
      updated_at: new Date().toISOString(),
    }

    return HttpResponse.json({
      success: true,
      plugin_id: params.pluginId,
      old_version: currentVersion,
      new_version: newVersion,
      message: `Plugin updated from ${currentVersion} to ${newVersion}`,
    })
  }),

  // ============================================================================
  // Plugin Lifecycle
  // ============================================================================

  // Get plugin lifecycle status
  http.get(`${API_BASE}/plugins/:pluginId/lifecycle`, async ({ params }) => {
    await delay(100)
    const plugin = plugins.find(p => p.id === params.pluginId)
    if (!plugin) {
      return HttpResponse.json({ detail: 'Plugin not found' }, { status: 404 })
    }

    let lifecycle = lifecycleStore.get(plugin.id)
    if (!lifecycle) {
      lifecycle = createPluginLifecycleInfo(plugin.id)
      lifecycleStore.set(plugin.id, lifecycle)
    }

    return HttpResponse.json(lifecycle)
  }),

  // Transition plugin state
  http.post(`${API_BASE}/plugins/:pluginId/transition`, async ({ params, request }) => {
    await delay(300)
    const plugin = plugins.find(p => p.id === params.pluginId)
    if (!plugin) {
      return HttpResponse.json({ detail: 'Plugin not found' }, { status: 404 })
    }

    const body = await request.json() as { target_state: PluginState; force?: boolean }
    let lifecycle = lifecycleStore.get(plugin.id)
    if (!lifecycle) {
      lifecycle = createPluginLifecycleInfo(plugin.id)
    }

    const previousState = lifecycle.current_state
    const allowedTransitions = lifecycle.allowed_transitions

    if (!body.force && !allowedTransitions.includes(body.target_state)) {
      return HttpResponse.json({
        success: false,
        error: `Invalid transition from ${previousState} to ${body.target_state}`,
        allowed_transitions: allowedTransitions,
      }, { status: 400 })
    }

    // Update lifecycle
    lifecycle = {
      ...lifecycle,
      current_state: body.target_state,
      previous_state: previousState,
      state_changed_at: new Date().toISOString(),
      allowed_transitions: getValidTransitionsForState(body.target_state),
      state_history: [
        ...lifecycle.state_history,
        {
          from_state: previousState,
          to_state: body.target_state,
          timestamp: new Date().toISOString(),
          reason: body.force ? 'Forced transition' : undefined,
        },
      ],
    }
    lifecycleStore.set(plugin.id, lifecycle)

    return HttpResponse.json({
      success: true,
      previous_state: previousState,
      current_state: body.target_state,
      lifecycle,
    })
  }),

  // ============================================================================
  // Hot Reload
  // ============================================================================

  // Get hot reload status
  http.get(`${API_BASE}/plugins/:pluginId/hot-reload`, async ({ params }) => {
    await delay(100)
    const plugin = plugins.find(p => p.id === params.pluginId)
    if (!plugin) {
      return HttpResponse.json({ detail: 'Plugin not found' }, { status: 404 })
    }

    let status = hotReloadStatusStore.get(plugin.id)
    if (!status) {
      status = createHotReloadStatus(plugin.id)
      hotReloadStatusStore.set(plugin.id, status)
    }

    let config = hotReloadConfigStore.get(plugin.id)
    if (!config) {
      config = createHotReloadConfig()
      hotReloadConfigStore.set(plugin.id, config)
    }

    return HttpResponse.json({ status, config })
  }),

  // Configure hot reload
  http.post(`${API_BASE}/plugins/:pluginId/hot-reload/configure`, async ({ params, request }) => {
    await delay(200)
    const plugin = plugins.find(p => p.id === params.pluginId)
    if (!plugin) {
      return HttpResponse.json({ detail: 'Plugin not found' }, { status: 404 })
    }

    const body = await request.json() as Partial<HotReloadConfig>
    let config = hotReloadConfigStore.get(plugin.id) || createHotReloadConfig()
    config = { ...config, ...body }
    hotReloadConfigStore.set(plugin.id, config)

    // Update status based on config
    let status = hotReloadStatusStore.get(plugin.id) || createHotReloadStatus(plugin.id)
    status = { ...status, is_watching: config.enabled }
    hotReloadStatusStore.set(plugin.id, status)

    return HttpResponse.json({ success: true, config, status })
  }),

  // Trigger hot reload
  http.post(`${API_BASE}/plugins/:pluginId/hot-reload/trigger`, async ({ params }) => {
    await delay(500)
    const plugin = plugins.find(p => p.id === params.pluginId)
    if (!plugin) {
      return HttpResponse.json({ detail: 'Plugin not found' }, { status: 404 })
    }

    let status = hotReloadStatusStore.get(plugin.id) || createHotReloadStatus(plugin.id)
    const success = Math.random() > 0.1

    status = {
      ...status,
      last_reload_at: new Date().toISOString(),
      reload_count: status.reload_count + 1,
      last_error: success ? undefined : 'Reload failed: module import error',
      pending_changes: false,
    }
    hotReloadStatusStore.set(plugin.id, status)

    return HttpResponse.json({
      success,
      reload_time_ms: Math.random() * 500,
      status,
      message: success ? 'Plugin reloaded successfully' : 'Reload failed',
    })
  }),

  // ============================================================================
  // Dependencies
  // ============================================================================

  // Get plugin dependencies
  http.get(`${API_BASE}/plugins/:pluginId/dependencies`, async ({ params, request }) => {
    await delay(200)
    const plugin = plugins.find(p => p.id === params.pluginId)
    if (!plugin) {
      return HttpResponse.json({ detail: 'Plugin not found' }, { status: 404 })
    }

    const url = new URL(request.url)
    const includeOptional = url.searchParams.get('include_optional') === 'true'

    const graph = createDependencyGraph(plugin.id, plugin.version)

    if (!includeOptional && graph.nodes[0]) {
      graph.nodes[0].dependencies = graph.nodes[0].dependencies.filter(
        d => d.dependency_type !== 'optional'
      )
    }

    return HttpResponse.json(graph)
  }),

  // Resolve dependencies
  http.post(`${API_BASE}/plugins/dependencies/resolve`, async ({ request }) => {
    await delay(400)
    const body = await request.json() as { plugin_ids: string[] }

    const resolutionResults = body.plugin_ids.map(pluginId => {
      const plugin = plugins.find(p => p.id === pluginId)
      if (!plugin) {
        return { plugin_id: pluginId, success: false, error: 'Plugin not found' }
      }
      return {
        plugin_id: pluginId,
        success: true,
        install_order: [pluginId],
        conflicts: [],
      }
    })

    const allSuccess = resolutionResults.every(r => r.success)

    return HttpResponse.json({
      success: allSuccess,
      results: resolutionResults,
      total_plugins: body.plugin_ids.length,
      resolved_count: resolutionResults.filter(r => r.success).length,
    })
  }),

  // ============================================================================
  // Security - Trust Store
  // ============================================================================

  // Get trust store
  http.get(`${API_BASE}/plugins/security/trust-store`, async () => {
    await delay(100)
    return HttpResponse.json({
      signers: trustedSigners,
      total: trustedSigners.length,
      last_updated: new Date().toISOString(),
    })
  }),

  // Add trusted signer
  http.post(`${API_BASE}/plugins/security/trust-store`, async ({ request }) => {
    await delay(200)
    const body = await request.json() as Partial<TrustedSigner>
    const newSigner = createTrustedSigner(body)
    trustedSigners.push(newSigner)
    return HttpResponse.json(newSigner, { status: 201 })
  }),

  // Remove trusted signer
  http.delete(`${API_BASE}/plugins/security/trust-store/:signerId`, async ({ params }) => {
    await delay(200)
    const index = trustedSigners.findIndex(s => s.id === params.signerId)
    if (index === -1) {
      return HttpResponse.json({ detail: 'Signer not found' }, { status: 404 })
    }
    trustedSigners.splice(index, 1)
    return new HttpResponse(null, { status: 204 })
  }),

  // ============================================================================
  // Security - Policy
  // ============================================================================

  // Get security policy
  http.get(`${API_BASE}/plugins/security/policy`, async () => {
    await delay(100)
    return HttpResponse.json(securityPolicy)
  }),

  // Update security policy
  http.put(`${API_BASE}/plugins/security/policy`, async ({ request }) => {
    await delay(200)
    const body = await request.json() as Partial<SecurityPolicy>
    securityPolicy = { ...securityPolicy, ...body }
    return HttpResponse.json(securityPolicy)
  }),

  // Analyze plugin security
  http.post(`${API_BASE}/plugins/:pluginId/security/analyze`, async ({ params }) => {
    await delay(600)
    const plugin = plugins.find(p => p.id === params.pluginId)
    if (!plugin) {
      return HttpResponse.json({ detail: 'Plugin not found' }, { status: 404 })
    }

    const result = createSecurityAnalysisResult(plugin.id)
    return HttpResponse.json(result)
  }),

  // Verify plugin signature
  http.post(`${API_BASE}/plugins/security/verify-signature`, async ({ request }) => {
    await delay(300)
    const body = await request.json() as { plugin_id: string; signature: string }
    const plugin = plugins.find(p => p.id === body.plugin_id)
    if (!plugin) {
      return HttpResponse.json({ detail: 'Plugin not found' }, { status: 404 })
    }

    const isValid = Math.random() > 0.2
    const signer = isValid ? trustedSigners[0] : undefined

    return HttpResponse.json({
      valid: isValid,
      signer: signer ? { id: signer.id, name: signer.name, trust_level: signer.trust_level } : null,
      verified_at: new Date().toISOString(),
      algorithm: signer?.algorithm || 'unknown',
      message: isValid ? 'Signature verified successfully' : 'Invalid or untrusted signature',
    })
  }),

  // ============================================================================
  // Hooks
  // ============================================================================

  // List all hooks
  http.get(`${API_BASE}/plugins/hooks`, async ({ request }) => {
    await delay(100)
    const url = new URL(request.url)
    const pluginId = url.searchParams.get('plugin_id')
    const hookType = url.searchParams.get('hook_type') as HookType | null
    const enabledOnly = url.searchParams.get('enabled_only') === 'true'

    let allHooks: HookRegistration[] = []

    if (pluginId) {
      allHooks = hookStore.get(pluginId) || []
    } else {
      hookStore.forEach(hooks => allHooks.push(...hooks))
    }

    if (hookType) {
      allHooks = allHooks.filter(h => h.hook_type === hookType)
    }
    if (enabledOnly) {
      allHooks = allHooks.filter(h => h.enabled)
    }

    return HttpResponse.json({
      hooks: allHooks,
      total: allHooks.length,
    })
  }),

  // Get hook types
  http.get(`${API_BASE}/plugins/hooks/types`, async () => {
    await delay(50)
    return HttpResponse.json({
      types: [
        { type: 'pre_validation', category: 'validation', description: 'Before validation runs' },
        { type: 'post_validation', category: 'validation', description: 'After validation completes' },
        { type: 'pre_profile', category: 'profiling', description: 'Before profiling runs' },
        { type: 'post_profile', category: 'profiling', description: 'After profiling completes' },
        { type: 'pre_scan', category: 'scanning', description: 'Before PII scan runs' },
        { type: 'post_scan', category: 'scanning', description: 'After PII scan completes' },
        { type: 'pre_mask', category: 'masking', description: 'Before data masking' },
        { type: 'post_mask', category: 'masking', description: 'After data masking' },
        { type: 'pre_compare', category: 'comparison', description: 'Before drift comparison' },
        { type: 'post_compare', category: 'comparison', description: 'After drift comparison' },
        { type: 'on_error', category: 'events', description: 'On any error' },
        { type: 'on_success', category: 'events', description: 'On successful operation' },
        { type: 'on_failure', category: 'events', description: 'On failed validation' },
        { type: 'on_plugin_load', category: 'lifecycle', description: 'When plugin loads' },
        { type: 'on_plugin_unload', category: 'lifecycle', description: 'When plugin unloads' },
        { type: 'on_config_change', category: 'lifecycle', description: 'When configuration changes' },
      ],
    })
  }),

  // Register hook
  http.post(`${API_BASE}/plugins/hooks`, async ({ request }) => {
    await delay(200)
    const body = await request.json() as {
      plugin_id: string
      hook_type: HookType
      callback_name: string
      priority?: string
    }

    const plugin = plugins.find(p => p.id === body.plugin_id)
    if (!plugin) {
      return HttpResponse.json({ detail: 'Plugin not found' }, { status: 404 })
    }

    const newHook = createHookRegistration(body.plugin_id, {
      hook_type: body.hook_type,
      callback_name: body.callback_name,
      priority: (body.priority as HookRegistration['priority']) || 'normal',
    })

    const pluginHooks = hookStore.get(body.plugin_id) || []
    pluginHooks.push(newHook)
    hookStore.set(body.plugin_id, pluginHooks)

    return HttpResponse.json(newHook, { status: 201 })
  }),

  // Delete hook
  http.delete(`${API_BASE}/plugins/hooks/:hookId`, async ({ params }) => {
    await delay(150)
    let found = false

    hookStore.forEach((hooks, pluginId) => {
      const index = hooks.findIndex(h => h.id === params.hookId)
      if (index !== -1) {
        hooks.splice(index, 1)
        hookStore.set(pluginId, hooks)
        found = true
      }
    })

    if (!found) {
      return HttpResponse.json({ detail: 'Hook not found' }, { status: 404 })
    }

    return new HttpResponse(null, { status: 204 })
  }),

  // ============================================================================
  // Documentation
  // ============================================================================

  // Get plugin documentation
  http.get(`${API_BASE}/plugins/:pluginId/documentation`, async ({ params }) => {
    await delay(200)
    const plugin = plugins.find(p => p.id === params.pluginId)
    if (!plugin) {
      return HttpResponse.json({ detail: 'Plugin not found' }, { status: 404 })
    }

    const docs = createPluginDocumentation(plugin.id, plugin.version)
    return HttpResponse.json(docs)
  }),

  // Render documentation
  http.post(`${API_BASE}/plugins/:pluginId/documentation/render`, async ({ params, request }) => {
    await delay(300)
    const plugin = plugins.find(p => p.id === params.pluginId)
    if (!plugin) {
      return HttpResponse.json({ detail: 'Plugin not found' }, { status: 404 })
    }

    const body = await request.json() as { format?: 'markdown' | 'html' | 'json' }
    const format = body.format || 'markdown'
    const docs = createPluginDocumentation(plugin.id, plugin.version)

    let content: string
    let contentType: string

    switch (format) {
      case 'html':
        content = `<!DOCTYPE html>
<html>
<head><title>${plugin.display_name} Documentation</title></head>
<body>
<h1>${plugin.display_name}</h1>
<p>Version: ${plugin.version}</p>
<h2>Classes</h2>
${docs.classes.map(c => `<h3>${c.name}</h3><p>${c.docstring || ''}</p>`).join('')}
<h2>Functions</h2>
${docs.functions.map(f => `<h3>${f.name}</h3><p>${f.docstring || ''}</p>`).join('')}
</body>
</html>`
        contentType = 'text/html'
        break

      case 'json':
        content = JSON.stringify(docs, null, 2)
        contentType = 'application/json'
        break

      default:
        content = `# ${plugin.display_name}

**Version:** ${plugin.version}

## Classes

${docs.classes.map(c => `### ${c.name}\n\n${c.docstring || ''}`).join('\n\n')}

## Functions

${docs.functions.map(f => `### ${f.name}\n\n${f.docstring || ''}`).join('\n\n')}

## Examples

${docs.examples.map(e => `### ${e.title}\n\n\`\`\`python\n${e.code}\n\`\`\`\n\n${e.description || ''}`).join('\n\n')}
`
        contentType = 'text/markdown'
    }

    return HttpResponse.json({
      content,
      content_type: contentType,
      format,
      rendered_at: new Date().toISOString(),
    })
  }),
]

// Helper function
function getValidTransitionsForState(state: PluginState): PluginState[] {
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

// Helper function to generate report content
function generateReportContent(
  reporter: CustomReporter,
  format: string,
  validationId: string,
  timestamp: string
): { content: string; contentType: string; filename: string } {
  const ts = Date.now()

  switch (format) {
    case 'json':
      return {
        content: JSON.stringify({
          reporter: reporter.display_name,
          validation_id: validationId,
          generated_at: timestamp,
          data: {
            status: 'success',
            total_issues: 3,
            passed: true,
            row_count: 10000,
            column_count: 15,
          },
          issues: [
            { column: 'email', issue_type: 'null_values', severity: 'medium', count: 5 },
            { column: 'age', issue_type: 'out_of_range', severity: 'high', count: 2 },
            { column: 'status', issue_type: 'invalid_category', severity: 'medium', count: 1 },
          ],
        }, null, 2),
        contentType: 'application/json',
        filename: `custom_report_${reporter.name}_${ts}.json`,
      }

    case 'csv':
      return {
        content: `# Custom Report: ${reporter.display_name}
# Generated: ${timestamp}
# Validation ID: ${validationId}

Metric,Value
Total Issues,3
Status,Passed
Row Count,10000
Column Count,15
Reporter,${reporter.display_name}

# Issues
Column,Issue Type,Severity,Count
email,null_values,medium,5
age,out_of_range,high,2
status,invalid_category,medium,1
`,
        contentType: 'text/csv',
        filename: `custom_report_${reporter.name}_${ts}.csv`,
      }

    case 'markdown':
      return {
        content: `# Custom Report: ${reporter.display_name}

**Generated:** ${timestamp}
**Validation ID:** \`${validationId}\`

## Summary

| Metric | Value |
|--------|-------|
| Total Issues | 3 |
| Status | Passed |
| Row Count | 10,000 |
| Column Count | 15 |

## Issues

| Column | Issue Type | Severity | Count |
|--------|------------|----------|-------|
| \`email\` | null_values | medium | 5 |
| \`age\` | out_of_range | high | 2 |
| \`status\` | invalid_category | medium | 1 |

---

*Generated by ${reporter.display_name}*
`,
        contentType: 'text/markdown',
        filename: `custom_report_${reporter.name}_${ts}.md`,
      }

    default:
      return {
        content: `<!DOCTYPE html>
<html>
<head>
    <title>Custom Report - ${reporter.display_name}</title>
    <style>
        body { font-family: -apple-system, system-ui, sans-serif; padding: 2rem; max-width: 900px; margin: 0 auto; }
        h1 { color: #fd9e4b; border-bottom: 2px solid #fd9e4b; padding-bottom: 0.5rem; }
        .card { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 1.5rem; margin: 1rem 0; }
        .meta { color: #6b7280; font-size: 0.875rem; }
        table { border-collapse: collapse; width: 100%; margin-top: 1rem; }
        th, td { border: 1px solid #e5e7eb; padding: 0.75rem; text-align: left; }
        th { background: #fd9e4b; color: white; }
        tr:nth-child(even) { background: #f9fafb; }
        .badge { display: inline-block; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 500; }
        .badge-success { background: #dcfce7; color: #166534; }
        .badge-warning { background: #fef9c3; color: #854d0e; }
        .badge-error { background: #fee2e2; color: #991b1b; }
    </style>
</head>
<body>
    <h1>Custom Report: ${reporter.display_name}</h1>
    <p class="meta">Generated at: ${timestamp}</p>
    <p class="meta">Validation ID: ${validationId}</p>

    <div class="card">
        <h2>Summary</h2>
        <p><span class="badge badge-success">PASSED</span></p>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Total Issues</td><td>3</td></tr>
            <tr><td>Row Count</td><td>10,000</td></tr>
            <tr><td>Column Count</td><td>15</td></tr>
            <tr><td>Reporter</td><td>${reporter.display_name}</td></tr>
        </table>
    </div>

    <div class="card">
        <h2>Issues</h2>
        <table>
            <tr><th>Column</th><th>Issue Type</th><th>Severity</th><th>Count</th></tr>
            <tr><td>email</td><td>null_values</td><td><span class="badge badge-warning">medium</span></td><td>5</td></tr>
            <tr><td>age</td><td>out_of_range</td><td><span class="badge badge-error">high</span></td><td>2</td></tr>
            <tr><td>status</td><td>invalid_category</td><td><span class="badge badge-warning">medium</span></td><td>1</td></tr>
        </table>
    </div>

    <footer class="meta" style="margin-top: 2rem; border-top: 1px solid #e5e7eb; padding-top: 1rem;">
        Generated by Truthound Dashboard - ${reporter.display_name}
    </footer>
</body>
</html>`,
        contentType: 'text/html',
        filename: `custom_report_${reporter.name}_${ts}.html`,
      }
  }
}
