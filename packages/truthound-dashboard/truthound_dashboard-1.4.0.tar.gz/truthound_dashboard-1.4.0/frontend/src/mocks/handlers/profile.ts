/**
 * Profile API handlers
 * Supports enhanced profiling with sampling strategies and pattern detection
 */

import { http, HttpResponse, delay } from 'msw'
import { getStore, getById } from '../data/store'
import {
  createProfileResult,
  createProfileHistory,
  createProfileComparisonResponse,
  createProfileTrendResponse,
  createId,
  type ProfileSummary,
} from '../factories'

const API_BASE = '/api/v1'

/**
 * Sampling configuration
 */
interface SamplingConfig {
  strategy?: string
  sample_size?: number | null
  confidence_level?: number
  margin_of_error?: number
  strata_column?: string | null
  seed?: number | null
}

/**
 * Pattern detection configuration
 */
interface PatternDetectionConfig {
  enabled?: boolean
  sample_size?: number
  min_confidence?: number
  patterns_to_detect?: string[] | null
}

/**
 * Enhanced request body for profile endpoint
 */
interface ProfileRequest {
  // Legacy field
  sample_size?: number
  // New fields
  sampling?: SamplingConfig
  pattern_detection?: PatternDetectionConfig
  include_histograms?: boolean
  include_correlations?: boolean
  include_cardinality?: boolean
}

// In-memory store for profile history per source
const profileHistoryStore = new Map<string, ProfileSummary[]>()

function getOrCreateProfileHistory(sourceId: string): ProfileSummary[] {
  if (!profileHistoryStore.has(sourceId)) {
    const history = createProfileHistory(sourceId, 15)
    profileHistoryStore.set(sourceId, history)
  }
  return profileHistoryStore.get(sourceId)!
}

export const profileHandlers = [
  // Profile a source with enhanced options
  http.post(`${API_BASE}/sources/:sourceId/profile`, async ({ params, request }) => {
    await delay(1200) // Simulate profiling time

    const sourceId = params.sourceId as string
    const source = getById(getStore().sources, sourceId)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    // Parse request body if present
    let profileRequest: ProfileRequest | undefined
    try {
      const body = await request.text()
      if (body) {
        profileRequest = JSON.parse(body) as ProfileRequest
      }
    } catch {
      // Empty body or invalid JSON, continue without options
    }

    // Determine sample size from either legacy or new format
    let sampleSize: number | undefined
    let samplingStrategy: string | undefined

    if (profileRequest?.sampling) {
      sampleSize = profileRequest.sampling.sample_size ?? undefined
      samplingStrategy = profileRequest.sampling.strategy
    } else if (profileRequest?.sample_size) {
      sampleSize = profileRequest.sample_size
    }

    // Determine if pattern detection is enabled
    const includePatterns = profileRequest?.pattern_detection?.enabled !== false

    // Create profile result with enhanced options
    const profile = createProfileResult({
      sourceName: source.name,
      rowCount: sampleSize ? Math.min(sampleSize, 1000000) : undefined,
      includePatterns,
      includeSamplingMetadata: Boolean(profileRequest?.sampling),
      samplingStrategy,
    })

    return HttpResponse.json(profile)
  }),

  // Get profile history for a source
  http.get(`${API_BASE}/sources/:sourceId/profiles`, async ({ params, request }) => {
    await delay(200)

    const sourceId = params.sourceId as string
    const source = getById(getStore().sources, sourceId)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    const url = new URL(request.url)
    const limit = parseInt(url.searchParams.get('limit') ?? '20')
    const offset = parseInt(url.searchParams.get('offset') ?? '0')

    const history = getOrCreateProfileHistory(sourceId)
    const paginatedHistory = history.slice(offset, offset + limit)

    return HttpResponse.json({
      profiles: paginatedHistory,
      total: history.length,
      source_id: sourceId,
    })
  }),

  // Compare two profiles
  http.post(`${API_BASE}/profiles/compare`, async ({ request }) => {
    await delay(500)

    interface CompareRequest {
      baseline_profile_id: string
      current_profile_id: string
    }

    let compareRequest: CompareRequest
    try {
      compareRequest = (await request.json()) as CompareRequest
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid request body' },
        { status: 400 }
      )
    }

    if (!compareRequest.baseline_profile_id || !compareRequest.current_profile_id) {
      return HttpResponse.json(
        { detail: 'baseline_profile_id and current_profile_id are required' },
        { status: 400 }
      )
    }

    // Find the source for these profiles
    let sourceId = ''
    let sourceName = 'Unknown Source'

    for (const [sId, profiles] of profileHistoryStore.entries()) {
      if (profiles.some((p) => p.id === compareRequest.baseline_profile_id || p.id === compareRequest.current_profile_id)) {
        sourceId = sId
        const source = getById(getStore().sources, sId)
        if (source) {
          sourceName = source.name
        }
        break
      }
    }

    const response = createProfileComparisonResponse(
      sourceId || createId(),
      sourceName,
      {
        baselineProfileId: compareRequest.baseline_profile_id,
        currentProfileId: compareRequest.current_profile_id,
      }
    )

    return HttpResponse.json(response)
  }),

  // Get profile trend for a source
  http.get(`${API_BASE}/sources/:sourceId/profiles/trend`, async ({ params, request }) => {
    await delay(300)

    const sourceId = params.sourceId as string
    const source = getById(getStore().sources, sourceId)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    const url = new URL(request.url)
    const granularity = (url.searchParams.get('granularity') ?? 'daily') as 'daily' | 'weekly' | 'monthly'

    const response = createProfileTrendResponse(sourceId, source.name, { granularity })

    return HttpResponse.json(response)
  }),

  // Get latest comparison (compare latest with previous)
  http.get(`${API_BASE}/sources/:sourceId/profiles/latest-comparison`, async ({ params }) => {
    await delay(300)

    const sourceId = params.sourceId as string
    const source = getById(getStore().sources, sourceId)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    const history = getOrCreateProfileHistory(sourceId)

    if (history.length < 2) {
      return HttpResponse.json({
        source_id: sourceId,
        has_previous: false,
        comparison: null,
      })
    }

    const response = createProfileComparisonResponse(sourceId, source.name, {
      baselineProfileId: history[1].id,
      currentProfileId: history[0].id,
    })

    return HttpResponse.json({
      source_id: sourceId,
      has_previous: true,
      comparison: response,
    })
  }),
]
