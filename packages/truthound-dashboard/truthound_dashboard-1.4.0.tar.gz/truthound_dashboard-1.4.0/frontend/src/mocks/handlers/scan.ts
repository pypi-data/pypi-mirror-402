/**
 * PII scan API handlers
 *
 * Supports all th.scan() parameters:
 * - columns: specific columns to scan
 * - regulations: privacy regulations to check (gdpr, ccpa, lgpd)
 * - min_confidence: confidence threshold for PII detection
 */

import { http, HttpResponse, delay } from 'msw'
import { getStore, getById, create, getAll } from '../data/store'
import { createPIIScan, createId } from '../factories'

const API_BASE = '/api/v1'

/**
 * PII scan request options (mirrors PIIScanRequest from API)
 */
interface PIIScanRequest {
  columns?: string[]
  regulations?: ('gdpr' | 'ccpa' | 'lgpd')[]
  min_confidence?: number
}

export const scanHandlers = [
  // Run PII scan for a source
  http.post(`${API_BASE}/scans/sources/:sourceId/scan`, async ({ params, request }) => {
    await delay(1000) // Simulate scan time

    const sourceId = params.sourceId as string
    const source = getById(getStore().sources, sourceId)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    // Parse request body for scan options
    let options: PIIScanRequest = {}
    try {
      const body = await request.json()
      options = body as PIIScanRequest
    } catch {
      // Empty body is valid - use defaults
    }

    // Create new PII scan with options
    const scan = createPIIScan({
      id: createId(),
      sourceId,
      options: {
        columns: options.columns,
        regulations: options.regulations,
        min_confidence: options.min_confidence,
      },
    })

    create(getStore().piiScans, scan)

    return HttpResponse.json(scan)
  }),

  // Get PII scan by ID
  http.get(`${API_BASE}/scans/:id`, async ({ params }) => {
    await delay(150)

    const scan = getById(getStore().piiScans, params.id as string)

    if (!scan) {
      return HttpResponse.json(
        { detail: 'PII scan not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(scan)
  }),

  // List PII scans for a source
  http.get(`${API_BASE}/scans/sources/:sourceId/scans`, async ({ params, request }) => {
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

    const allScans = getPIIScansBySourceId(sourceId)
    const scans = allScans.slice(0, limit)

    return HttpResponse.json({
      data: scans,
      total: allScans.length,
      limit,
    })
  }),

  // Get latest PII scan for a source
  http.get(`${API_BASE}/scans/sources/:sourceId/scans/latest`, async ({ params }) => {
    await delay(150)

    const sourceId = params.sourceId as string
    const source = getById(getStore().sources, sourceId)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    const scans = getPIIScansBySourceId(sourceId)

    if (scans.length === 0) {
      return HttpResponse.json(
        { detail: 'No PII scans found for source' },
        { status: 404 }
      )
    }

    return HttpResponse.json(scans[0])
  }),
]

// Helper function to get PII scans by source ID
function getPIIScansBySourceId(sourceId: string) {
  return getAll(getStore().piiScans)
    .filter((s) => s.source_id === sourceId)
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
}
