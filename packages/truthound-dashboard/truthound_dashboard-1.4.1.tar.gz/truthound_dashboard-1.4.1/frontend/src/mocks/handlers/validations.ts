/**
 * Validations API handlers
 *
 * Supports all th.check() parameters:
 * - validators, validator_configs, schema_path, auto_schema
 * - columns, min_severity, strict, parallel, max_workers, pushdown
 */

import { http, HttpResponse, delay } from 'msw'
import {
  getStore,
  getById,
  create,
  getValidationsBySourceId,
} from '../data/store'
import { createValidation, createId } from '../factories'

const API_BASE = '/api/v1'

/**
 * Validator configuration for advanced mode.
 */
interface ValidatorConfig {
  name: string
  enabled: boolean
  params: Record<string, unknown>
  severity_override?: 'low' | 'medium' | 'high' | 'critical'
}

/**
 * Validation run request options (mirrors ValidationRunOptions from client.ts)
 * Supports two modes:
 * 1. Simple mode: Use `validators` list (backward compatible)
 * 2. Advanced mode: Use `validator_configs` for per-validator parameters
 */
interface ValidationRunRequest {
  /** Simple mode: Validator names to run */
  validators?: string[]
  /** Advanced mode: Per-validator configuration with parameters */
  validator_configs?: ValidatorConfig[]
  schema_path?: string
  auto_schema?: boolean
  columns?: string[]
  min_severity?: 'low' | 'medium' | 'high' | 'critical'
  strict?: boolean
  parallel?: boolean
  max_workers?: number
  pushdown?: boolean
}

/**
 * Extract enabled validator names from configs.
 */
function getValidatorNamesFromConfigs(configs: ValidatorConfig[]): string[] {
  return configs.filter((c) => c.enabled).map((c) => c.name)
}

export const validationsHandlers = [
  // Run validation for a source
  http.post(`${API_BASE}/validations/sources/:sourceId/validate`, async ({ params, request }) => {
    await delay(800) // Simulate validation time

    const sourceId = params.sourceId as string
    const source = getById(getStore().sources, sourceId)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    // Parse request body for validation options
    let options: ValidationRunRequest = {}
    try {
      const body = await request.json()
      options = body as ValidationRunRequest
    } catch {
      // Empty body is valid - use defaults
    }

    // Determine validators to run based on request mode
    let validatorNames: string[] | undefined = undefined
    if (options.validator_configs && options.validator_configs.length > 0) {
      // Advanced mode: extract enabled validator names from configs
      validatorNames = getValidatorNamesFromConfigs(options.validator_configs)
    } else if (options.validators) {
      // Simple mode: use validator names directly
      validatorNames = options.validators
    }

    // Create new validation with options
    // The mock factory uses these to generate realistic results
    const validation = createValidation({
      id: createId(),
      sourceId,
      // Pass options to factory for more realistic mock behavior
      options: {
        validators: validatorNames,
        validator_configs: options.validator_configs,
        columns: options.columns,
        min_severity: options.min_severity,
        parallel: options.parallel,
      },
    })

    create(getStore().validations, validation)

    // Update source's last_validated_at
    const sources = getStore().sources
    const existingSource = sources.get(sourceId)
    if (existingSource) {
      sources.set(sourceId, {
        ...existingSource,
        last_validated_at: new Date().toISOString(),
        latest_validation_status: validation.passed ? 'success' : 'failed',
      })
    }

    return HttpResponse.json({
      success: true,
      data: validation,
    })
  }),

  // Get validation by ID
  http.get(`${API_BASE}/validations/:id`, async ({ params }) => {
    await delay(150)

    const validation = getById(getStore().validations, params.id as string)

    if (!validation) {
      return HttpResponse.json(
        { detail: 'Validation not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json({
      success: true,
      data: validation,
    })
  }),

  // List validations for a source
  http.get(`${API_BASE}/validations/sources/:sourceId/validations`, async ({ params, request }) => {
    await delay(200)

    const url = new URL(request.url)
    const limit = parseInt(url.searchParams.get('limit') ?? '20')
    const offset = parseInt(url.searchParams.get('offset') ?? '0')

    const sourceId = params.sourceId as string
    const allValidations = getValidationsBySourceId(sourceId)
    const total = allValidations.length
    const validations = allValidations.slice(offset, offset + limit)

    return HttpResponse.json({
      success: true,
      data: validations,
      total,  // Return total count of ALL validations, not just the sliced ones
      offset,
      limit,
    })
  }),
]
