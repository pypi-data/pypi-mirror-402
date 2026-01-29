/**
 * Schema Evolution factory - generates schema version and change data
 */

import { createId, createTimestamp, randomChoice, randomInt, faker } from './base'

// Types matching backend schemas
export interface SchemaVersionSummary {
  id: string
  version_number: number
  column_count: number
  created_at: string
}

export interface SchemaChangeType {
  value: 'column_added' | 'column_removed' | 'type_changed'
}

export interface SchemaChange {
  id: string
  source_id: string
  from_version_id: string | null
  to_version_id: string
  change_type: 'column_added' | 'column_removed' | 'type_changed'
  column_name: string
  old_value: string | null
  new_value: string | null
  severity: 'breaking' | 'non_breaking'
  description: string
  created_at: string
}

export interface SchemaEvolutionResponse {
  source_id: string
  source_name: string
  from_version: number | null
  to_version: number
  has_changes: boolean
  total_changes: number
  breaking_changes: number
  changes: SchemaChange[]
  detected_at: string
}

export interface SchemaEvolutionSummary {
  source_id: string
  current_version: number
  total_versions: number
  total_changes: number
  breaking_changes: number
  last_change_at: string | null
}

const COLUMN_NAMES = [
  'user_id', 'email', 'name', 'created_at', 'updated_at',
  'status', 'amount', 'category', 'description', 'is_active',
  'phone', 'address', 'country', 'zip_code', 'metadata'
]

const DATA_TYPES = [
  'int64', 'float64', 'object', 'datetime64[ns]', 'bool',
  'int32', 'float32', 'string', 'date'
]

export function createSchemaVersionSummary(
  versionNumber: number,
  daysAgo: number = 0
): SchemaVersionSummary {
  return {
    id: createId(),
    version_number: versionNumber,
    column_count: randomInt(5, 20),
    created_at: createTimestamp(daysAgo),
  }
}

export function createSchemaChange(
  sourceId: string,
  fromVersionId: string | null,
  toVersionId: string,
  daysAgo: number = 0
): SchemaChange {
  const changeType = randomChoice<'column_added' | 'column_removed' | 'type_changed'>([
    'column_added', 'column_removed', 'type_changed'
  ])
  const columnName = randomChoice(COLUMN_NAMES)

  let oldValue: string | null = null
  let newValue: string | null = null
  let severity: 'breaking' | 'non_breaking' = 'non_breaking'
  let description: string

  switch (changeType) {
    case 'column_added':
      newValue = randomChoice(DATA_TYPES)
      description = `Column '${columnName}' added with type ${newValue}`
      break
    case 'column_removed':
      oldValue = randomChoice(DATA_TYPES)
      severity = 'breaking'
      description = `Column '${columnName}' removed (was ${oldValue})`
      break
    case 'type_changed':
      oldValue = randomChoice(DATA_TYPES)
      newValue = randomChoice(DATA_TYPES.filter(t => t !== oldValue))
      severity = 'breaking'
      description = `Column '${columnName}' type changed from ${oldValue} to ${newValue}`
      break
  }

  return {
    id: createId(),
    source_id: sourceId,
    from_version_id: fromVersionId,
    to_version_id: toVersionId,
    change_type: changeType,
    column_name: columnName,
    old_value: oldValue,
    new_value: newValue,
    severity,
    description,
    created_at: createTimestamp(daysAgo),
  }
}

export function createSchemaEvolutionResponse(
  sourceId: string,
  sourceName: string,
  options: {
    hasChanges?: boolean
    changeCount?: number
  } = {}
): SchemaEvolutionResponse {
  const hasChanges = options.hasChanges ?? faker.datatype.boolean()
  const changeCount = options.changeCount ?? (hasChanges ? randomInt(1, 5) : 0)

  const toVersionId = createId()
  const fromVersionId = hasChanges ? createId() : null

  const changes: SchemaChange[] = []
  for (let i = 0; i < changeCount; i++) {
    changes.push(createSchemaChange(sourceId, fromVersionId, toVersionId, i))
  }

  const breakingChanges = changes.filter(c => c.severity === 'breaking').length

  return {
    source_id: sourceId,
    source_name: sourceName,
    from_version: hasChanges ? randomInt(1, 10) : null,
    to_version: randomInt(1, 15),
    has_changes: hasChanges,
    total_changes: changeCount,
    breaking_changes: breakingChanges,
    changes,
    detected_at: new Date().toISOString(),
  }
}

export function createSchemaEvolutionSummary(sourceId: string): SchemaEvolutionSummary {
  const totalVersions = randomInt(1, 15)
  const totalChanges = randomInt(0, totalVersions * 3)
  const breakingChanges = randomInt(0, Math.floor(totalChanges / 3))

  return {
    source_id: sourceId,
    current_version: totalVersions,
    total_versions: totalVersions,
    total_changes: totalChanges,
    breaking_changes: breakingChanges,
    last_change_at: totalChanges > 0 ? createTimestamp(randomInt(0, 30)) : null,
  }
}

export function createSchemaVersionHistory(
  _sourceId: string,
  count: number = 10
): SchemaVersionSummary[] {
  const versions: SchemaVersionSummary[] = []

  for (let i = count; i >= 1; i--) {
    versions.push(createSchemaVersionSummary(i, (count - i) * randomInt(1, 7)))
  }

  return versions
}
