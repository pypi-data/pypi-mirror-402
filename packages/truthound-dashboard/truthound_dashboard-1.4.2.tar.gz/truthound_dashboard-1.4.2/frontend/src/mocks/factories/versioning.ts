/**
 * Versioning mock data factories
 */

import { faker } from '@faker-js/faker'
import { createId, createTimestamp } from './base'
import type { VersionInfo, VersionDiff, VersioningStrategy } from '@/api/client'

/**
 * Generate a version number based on strategy
 */
function generateVersionNumber(strategy: VersioningStrategy, index: number): string {
  switch (strategy) {
    case 'incremental':
      return `v${index + 1}`
    case 'semantic':
      return `${Math.floor(index / 10) + 1}.${index % 10}.0`
    case 'timestamp':
      return new Date(Date.now() - index * 86400000).toISOString().replace(/[-:.TZ]/g, '').slice(0, 15)
    case 'gitlike':
      return faker.git.commitSha().slice(0, 8)
    default:
      return `v${index + 1}`
  }
}

/**
 * Generate a mock version info
 */
export function createMockVersion(
  sourceId: string,
  validationId: string,
  index: number = 0,
  parentVersionId: string | null = null,
  strategy: VersioningStrategy = 'incremental'
): VersionInfo {
  const versionNumber = generateVersionNumber(strategy, index)
  const versionId = `${sourceId}_${validationId}_${versionNumber}`

  return {
    version_id: versionId,
    version_number: versionNumber,
    validation_id: validationId,
    source_id: sourceId,
    strategy,
    created_at: createTimestamp(index), // Each version is 1 day apart
    parent_version_id: parentVersionId,
    metadata: {
      bump_type: faker.helpers.arrayElement(['patch', 'minor', 'major']),
    },
    content_hash: faker.git.commitSha().slice(0, 16),
  }
}

/**
 * Generate a list of mock versions for a source
 */
export function createMockVersionList(
  sourceId: string,
  count: number = 5,
  strategy: VersioningStrategy = 'incremental'
): VersionInfo[] {
  const versions: VersionInfo[] = []
  let parentVersionId: string | null = null

  // Generate versions from oldest to newest, then reverse
  for (let i = count - 1; i >= 0; i--) {
    const validationId = createId()
    const version = createMockVersion(sourceId, validationId, count - 1 - i, parentVersionId, strategy)
    versions.push(version)
    parentVersionId = version.version_id
  }

  // Reverse so newest is first
  return versions.reverse()
}

/**
 * Generate a mock version diff
 */
export function createMockVersionDiff(
  fromVersion: VersionInfo,
  toVersion: VersionInfo
): VersionDiff {
  const issuesAdded = faker.number.int({ min: 0, max: 5 })
  const issuesRemoved = faker.number.int({ min: 0, max: 3 })
  const issuesChanged = faker.number.int({ min: 0, max: 2 })

  return {
    from_version: fromVersion,
    to_version: toVersion,
    issues_added: Array.from({ length: issuesAdded }, () => ({
      column: faker.database.column(),
      issue_type: faker.helpers.arrayElement(['null_check', 'range_check', 'type_check', 'unique_check']),
      severity: faker.helpers.arrayElement(['critical', 'high', 'medium', 'low']),
      count: faker.number.int({ min: 1, max: 100 }),
      details: faker.lorem.sentence(),
    })),
    issues_removed: Array.from({ length: issuesRemoved }, () => ({
      column: faker.database.column(),
      issue_type: faker.helpers.arrayElement(['null_check', 'range_check', 'type_check', 'unique_check']),
      severity: faker.helpers.arrayElement(['critical', 'high', 'medium', 'low']),
      count: faker.number.int({ min: 1, max: 100 }),
      details: faker.lorem.sentence(),
    })),
    issues_changed: Array.from({ length: issuesChanged }, () => ({
      key: `${faker.database.column()}:${faker.helpers.arrayElement(['null_check', 'range_check'])}`,
      from: {
        severity: 'high',
        count: faker.number.int({ min: 50, max: 100 }),
      },
      to: {
        severity: 'medium',
        count: faker.number.int({ min: 10, max: 49 }),
      },
    })),
    summary_changes: {
      issues_added_count: issuesAdded,
      issues_removed_count: issuesRemoved,
      issues_changed_count: issuesChanged,
    },
    has_changes: issuesAdded > 0 || issuesRemoved > 0 || issuesChanged > 0,
  }
}
