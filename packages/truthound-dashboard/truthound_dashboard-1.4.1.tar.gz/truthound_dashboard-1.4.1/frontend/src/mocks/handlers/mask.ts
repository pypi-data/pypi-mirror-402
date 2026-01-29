/**
 * Data masking API handlers
 *
 * Supports th.mask() strategies:
 * - redact: Replace values with asterisks
 * - hash: Replace values with SHA256 hash
 * - fake: Replace values with realistic fake data
 */

import { http, HttpResponse, delay } from 'msw'
import { getStore, getById, create, getAll } from '../data/store'
import { createDataMask, createId } from '../factories'

const API_BASE = '/api/v1'

/**
 * Mask request options (mirrors MaskRequest from API)
 */
interface MaskRequest {
  columns?: string[]
  strategy?: 'redact' | 'hash' | 'fake'
  output_format?: 'csv' | 'parquet' | 'json'
}

export const maskHandlers = [
  // Run data masking for a source
  http.post(`${API_BASE}/masks/sources/:sourceId/mask`, async ({ params, request }) => {
    await delay(1500) // Simulate masking time

    const sourceId = params.sourceId as string
    const source = getById(getStore().sources, sourceId)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    // Parse request body for mask options
    let options: MaskRequest = {}
    try {
      const body = await request.json()
      options = body as MaskRequest
    } catch {
      // Empty body is valid - use defaults
    }

    // Create new data mask operation
    const mask = createDataMask({
      id: createId(),
      sourceId,
      strategy: options.strategy ?? 'redact',
      columnsToMask: options.columns,
      autoDetected: !options.columns,
      status: 'success',
    })

    create(getStore().dataMasks, mask)

    return HttpResponse.json(mask, { status: 201 })
  }),

  // Get data mask by ID
  http.get(`${API_BASE}/masks/:id`, async ({ params }) => {
    await delay(150)

    const mask = getById(getStore().dataMasks, params.id as string)

    if (!mask) {
      return HttpResponse.json(
        { detail: 'Mask operation not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(mask)
  }),

  // List data masks for a source
  http.get(`${API_BASE}/masks/sources/:sourceId/masks`, async ({ params, request }) => {
    await delay(200)

    const url = new URL(request.url)
    const limit = parseInt(url.searchParams.get('limit') ?? '20')

    const sourceId = params.sourceId as string
    const source = getById(getStore().sources, sourceId)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    const allMasks = getDataMasksBySourceId(sourceId)
    const masks = allMasks.slice(0, limit)

    return HttpResponse.json({
      data: masks.map((m) => ({
        id: m.id,
        source_id: m.source_id,
        source_name: source.name,
        status: m.status,
        strategy: m.strategy,
        columns_masked: m.columns_masked?.length ?? 0,
        row_count: m.row_count,
        duration_ms: m.duration_ms,
        created_at: m.created_at,
      })),
      total: allMasks.length,
      limit,
    })
  }),

  // Get latest data mask for a source
  http.get(`${API_BASE}/masks/sources/:sourceId/masks/latest`, async ({ params }) => {
    await delay(150)

    const sourceId = params.sourceId as string
    const source = getById(getStore().sources, sourceId)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    const masks = getDataMasksBySourceId(sourceId)

    if (masks.length === 0) {
      return HttpResponse.json(
        { detail: 'No mask operations found for source' },
        { status: 404 }
      )
    }

    return HttpResponse.json(masks[0])
  }),
]

// Helper function to get data masks by source ID
function getDataMasksBySourceId(sourceId: string) {
  return getAll(getStore().dataMasks)
    .filter((m) => m.source_id === sourceId)
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
}
