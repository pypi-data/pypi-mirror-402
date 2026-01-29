/**
 * Schema Evolution API handlers
 */

import { http, HttpResponse, delay } from 'msw'
import { getStore, getById } from '../data/store'
import {
  createSchemaEvolutionResponse,
  createSchemaEvolutionSummary,
  createSchemaVersionHistory,
  createSchemaChange,
  createId,
} from '../factories'

const API_BASE = '/api/v1'

// In-memory store for schema versions per source
const schemaVersionsStore = new Map<string, ReturnType<typeof createSchemaVersionHistory>>()
const schemaChangesStore = new Map<string, ReturnType<typeof createSchemaChange>[]>()

function getOrCreateVersionHistory(sourceId: string) {
  if (!schemaVersionsStore.has(sourceId)) {
    const versions = createSchemaVersionHistory(sourceId, 10)
    schemaVersionsStore.set(sourceId, versions)

    // Create changes between versions
    const changes: ReturnType<typeof createSchemaChange>[] = []
    for (let i = 1; i < versions.length; i++) {
      const fromVersion = versions[i]
      const toVersion = versions[i - 1]
      // Create 1-3 changes per version transition
      const changeCount = Math.floor(Math.random() * 3) + 1
      for (let j = 0; j < changeCount; j++) {
        changes.push(createSchemaChange(sourceId, fromVersion.id, toVersion.id, i))
      }
    }
    schemaChangesStore.set(sourceId, changes)
  }
  return schemaVersionsStore.get(sourceId)!
}

export const schemaEvolutionHandlers = [
  // Get schema version history for a source
  http.get(`${API_BASE}/sources/:sourceId/schema/versions`, async ({ params, request }) => {
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

    const versions = getOrCreateVersionHistory(sourceId)
    const paginatedVersions = versions.slice(offset, offset + limit)

    return HttpResponse.json({
      versions: paginatedVersions,
      total: versions.length,
      source_id: sourceId,
    })
  }),

  // Get a specific schema version
  http.get(`${API_BASE}/schema/versions/:versionId`, async ({ params }) => {
    await delay(150)

    const versionId = params.versionId as string

    // Search across all sources for the version
    for (const [sourceId, versions] of schemaVersionsStore.entries()) {
      const version = versions.find((v) => v.id === versionId)
      if (version) {
        return HttpResponse.json({
          ...version,
          source_id: sourceId,
          schema_id: `schema-${sourceId}`,
          schema_hash: `sha256:${createId().replace(/-/g, '')}`,
          columns: ['user_id', 'email', 'name', 'created_at'],
          column_snapshot: {
            user_id: { dtype: 'int64', nullable: false },
            email: { dtype: 'object', nullable: true },
            name: { dtype: 'object', nullable: true },
            created_at: { dtype: 'datetime64[ns]', nullable: false },
          },
          updated_at: version.created_at,
        })
      }
    }

    return HttpResponse.json(
      { detail: 'Version not found' },
      { status: 404 }
    )
  }),

  // Get schema changes for a source
  http.get(`${API_BASE}/sources/:sourceId/schema/changes`, async ({ params, request }) => {
    await delay(200)

    const sourceId = params.sourceId as string
    const source = getById(getStore().sources, sourceId)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    // Ensure versions and changes exist
    getOrCreateVersionHistory(sourceId)

    const url = new URL(request.url)
    const limit = parseInt(url.searchParams.get('limit') ?? '50')
    const offset = parseInt(url.searchParams.get('offset') ?? '0')

    const changes = schemaChangesStore.get(sourceId) ?? []
    const paginatedChanges = changes.slice(offset, offset + limit)

    return HttpResponse.json({
      changes: paginatedChanges,
      total: changes.length,
      source_id: sourceId,
    })
  }),

  // Detect schema changes (manual trigger)
  http.post(`${API_BASE}/sources/:sourceId/schema/detect-changes`, async ({ params }) => {
    await delay(800) // Simulate detection time

    const sourceId = params.sourceId as string
    const source = getById(getStore().sources, sourceId)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    // Generate evolution response
    const response = createSchemaEvolutionResponse(
      sourceId,
      source.name,
      { hasChanges: Math.random() > 0.3 } // 70% chance of having changes
    )

    return HttpResponse.json(response)
  }),

  // Get evolution summary for a source
  http.get(`${API_BASE}/sources/:sourceId/schema/evolution/summary`, async ({ params }) => {
    await delay(150)

    const sourceId = params.sourceId as string
    const source = getById(getStore().sources, sourceId)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    const summary = createSchemaEvolutionSummary(sourceId)

    return HttpResponse.json(summary)
  }),
]
