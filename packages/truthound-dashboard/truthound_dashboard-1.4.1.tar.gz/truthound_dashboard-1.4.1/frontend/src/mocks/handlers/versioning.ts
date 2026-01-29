/**
 * MSW handlers for versioning API
 */

import { http, HttpResponse, delay } from 'msw'
import { createMockVersionList, createMockVersionDiff } from '../factories/versioning'
import type { VersionInfo, VersioningStrategy } from '@/api/client'

const API_BASE = '/api/v1'

// In-memory store for versions
const versionStore: Map<string, VersionInfo[]> = new Map()

// Get or create versions for a source
function getVersionsForSource(sourceId: string): VersionInfo[] {
  if (!versionStore.has(sourceId)) {
    const strategy: VersioningStrategy = 'incremental'
    const versions = createMockVersionList(sourceId, 8, strategy)
    versionStore.set(sourceId, versions)
  }
  return versionStore.get(sourceId) || []
}

export const versioningHandlers = [
  // List versions for a source
  http.get(`${API_BASE}/versions/sources/:sourceId`, async ({ params, request }) => {
    await delay(300)
    const { sourceId } = params as { sourceId: string }
    const url = new URL(request.url)
    const limit = parseInt(url.searchParams.get('limit') || '20', 10)

    const versions = getVersionsForSource(sourceId)
    const limitedVersions = versions.slice(0, limit)

    return HttpResponse.json({
      success: true,
      data: limitedVersions,
      total: versions.length,
      source_id: sourceId,
    })
  }),

  // Get a specific version
  http.get(`${API_BASE}/versions/:versionId`, async ({ params }) => {
    await delay(200)
    const { versionId } = params as { versionId: string }

    // Search all stores for the version
    for (const versions of versionStore.values()) {
      const version = versions.find((v) => v.version_id === versionId)
      if (version) {
        return HttpResponse.json(version)
      }
    }

    return HttpResponse.json(
      { detail: `Version not found: ${versionId}` },
      { status: 404 }
    )
  }),

  // Get latest version for a source
  http.get(`${API_BASE}/versions/sources/:sourceId/latest`, async ({ params }) => {
    await delay(200)
    const { sourceId } = params as { sourceId: string }
    const versions = getVersionsForSource(sourceId)

    if (versions.length === 0) {
      return HttpResponse.json(
        { detail: `No versions found for source: ${sourceId}` },
        { status: 404 }
      )
    }

    return HttpResponse.json(versions[0])
  }),

  // Compare two versions
  http.post(`${API_BASE}/versions/compare`, async ({ request }) => {
    await delay(400)
    const body = await request.json() as {
      from_version_id: string
      to_version_id: string
    }

    let fromVersion: VersionInfo | undefined
    let toVersion: VersionInfo | undefined

    // Find both versions
    for (const versions of versionStore.values()) {
      if (!fromVersion) {
        fromVersion = versions.find((v) => v.version_id === body.from_version_id)
      }
      if (!toVersion) {
        toVersion = versions.find((v) => v.version_id === body.to_version_id)
      }
    }

    if (!fromVersion) {
      return HttpResponse.json(
        { detail: `From version not found: ${body.from_version_id}` },
        { status: 404 }
      )
    }

    if (!toVersion) {
      return HttpResponse.json(
        { detail: `To version not found: ${body.to_version_id}` },
        { status: 404 }
      )
    }

    const diff = createMockVersionDiff(fromVersion, toVersion)
    return HttpResponse.json(diff)
  }),

  // Get version history chain
  http.get(`${API_BASE}/versions/:versionId/history`, async ({ params, request }) => {
    await delay(300)
    const { versionId } = params as { versionId: string }
    const url = new URL(request.url)
    const depth = parseInt(url.searchParams.get('depth') || '10', 10)

    // Find the version and get its history
    let startVersion: VersionInfo | undefined
    let sourceVersions: VersionInfo[] = []

    for (const [, versions] of versionStore.entries()) {
      const version = versions.find((v) => v.version_id === versionId)
      if (version) {
        startVersion = version
        sourceVersions = versions
        break
      }
    }

    if (!startVersion) {
      return HttpResponse.json(
        { detail: `Version not found: ${versionId}` },
        { status: 404 }
      )
    }

    // Build history chain
    const history: VersionInfo[] = []
    let currentVersion: VersionInfo | undefined = startVersion
    let currentDepth = 0

    while (currentVersion && currentDepth < depth) {
      history.push(currentVersion)
      currentDepth++

      if (currentVersion.parent_version_id) {
        currentVersion = sourceVersions.find(
          (v) => v.version_id === currentVersion?.parent_version_id
        )
      } else {
        break
      }
    }

    return HttpResponse.json({
      success: true,
      data: history,
      depth: history.length,
    })
  }),

  // Create a new version
  http.post(`${API_BASE}/versions/`, async ({ request }) => {
    await delay(300)
    const body = await request.json() as {
      validation_id: string
      strategy?: VersioningStrategy
      metadata?: Record<string, unknown>
    }

    // For demo, we'll just return a mock version
    // In reality this would create a real version
    const sourceId = 'src-' + body.validation_id.slice(0, 8)
    const versions = getVersionsForSource(sourceId)
    const newIndex = versions.length

    const newVersion: VersionInfo = {
      version_id: `${sourceId}_${body.validation_id}_v${newIndex + 1}`,
      version_number: `v${newIndex + 1}`,
      validation_id: body.validation_id,
      source_id: sourceId,
      strategy: body.strategy || 'incremental',
      created_at: new Date().toISOString(),
      parent_version_id: versions[0]?.version_id || null,
      metadata: body.metadata || {},
      content_hash: Math.random().toString(36).slice(2, 18),
    }

    // Add to store
    versions.unshift(newVersion)

    return HttpResponse.json({
      success: true,
      data: newVersion,
      message: `Created version ${newVersion.version_number} for validation ${body.validation_id}`,
    })
  }),

  // Check rollback availability
  http.get(`${API_BASE}/versions/sources/:sourceId/rollback-availability`, async ({ params }) => {
    await delay(200)
    const { sourceId } = params as { sourceId: string }
    const versions = getVersionsForSource(sourceId)

    const rollbackTargets = versions.slice(1).map((v) => ({
      ...v,
    }))

    return HttpResponse.json({
      success: true,
      can_rollback: versions.length > 1,
      current_version_id: versions[0]?.version_id || null,
      available_versions: versions.length,
      rollback_targets: rollbackTargets.slice(0, 10),
    })
  }),

  // Rollback to a previous version
  http.post(`${API_BASE}/versions/sources/:sourceId/rollback`, async ({ params, request }) => {
    await delay(500)
    const { sourceId } = params as { sourceId: string }
    const body = await request.json() as {
      target_version_id: string
      create_new_validation?: boolean
    }

    const versions = getVersionsForSource(sourceId)
    const currentVersion = versions[0]
    const targetVersion = versions.find((v) => v.version_id === body.target_version_id)

    if (!targetVersion) {
      return HttpResponse.json(
        { detail: `Target version not found: ${body.target_version_id}` },
        { status: 400 }
      )
    }

    // Create a rollback version if requested
    let newValidationId: string | null = null
    if (body.create_new_validation !== false) {
      newValidationId = `val-rollback-${Date.now()}`

      const rollbackVersion: VersionInfo = {
        version_id: `${sourceId}_${newValidationId}_v${versions.length + 1}`,
        version_number: `v${versions.length + 1}`,
        validation_id: newValidationId,
        source_id: sourceId,
        strategy: targetVersion.strategy,
        created_at: new Date().toISOString(),
        parent_version_id: currentVersion?.version_id || null,
        metadata: {
          rollback_from: currentVersion?.version_id,
          rollback_to: targetVersion.version_id,
          rollback_type: 'explicit',
        },
        content_hash: targetVersion.content_hash,
      }

      versions.unshift(rollbackVersion)
    }

    return HttpResponse.json({
      success: true,
      source_id: sourceId,
      from_version: currentVersion,
      to_version: targetVersion,
      new_validation_id: newValidationId,
      message: `Successfully rolled back to version ${targetVersion.version_number}`,
      rolled_back_at: new Date().toISOString(),
    })
  }),
]
