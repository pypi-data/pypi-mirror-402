/**
 * Data mask factory - generates realistic data masking operation results
 * Supports th.mask() strategies: redact, hash, fake
 */

import type { DataMask } from '@/api/client'
import {
  createId,
  createTimestamp,
  randomChoice,
  randomInt,
  randomSubset,
  faker,
} from './base'

/**
 * Masking strategies supported by th.mask()
 */
export type MaskingStrategy = 'redact' | 'hash' | 'fake'

/**
 * Mask operation status
 */
export type MaskStatus = 'pending' | 'running' | 'success' | 'failed' | 'error'

export interface DataMaskFactoryOptions {
  id?: string
  sourceId?: string
  status?: MaskStatus
  strategy?: MaskingStrategy
  columnCount?: number
  columnsToMask?: string[]
  autoDetected?: boolean
  rowCount?: number
  durationMs?: number
}

// Common PII column names that would be detected/masked
const PII_COLUMNS = [
  'email',
  'user_email',
  'phone',
  'phone_number',
  'ssn',
  'social_security',
  'credit_card',
  'card_number',
  'ip_address',
  'birth_date',
  'dob',
  'address',
  'street_address',
  'full_name',
  'name',
  'first_name',
  'last_name',
  'passport_number',
  'driver_license',
  'national_id',
  'bank_account',
]

/**
 * Create a single data mask operation
 */
export function createDataMask(
  options: DataMaskFactoryOptions = {}
): DataMask {
  const status = options.status ?? randomChoice(['success', 'success', 'success', 'error'])
  const strategy = options.strategy ?? randomChoice(['redact', 'hash', 'fake'])

  // Determine columns
  const columnCount = options.columnCount ?? randomInt(8, 30)
  const piiColumnCount = Math.min(randomInt(2, 8), columnCount - 3)

  // Columns that were masked (either specified or auto-detected PII)
  const columnsMasked =
    options.columnsToMask ?? randomSubset(PII_COLUMNS, piiColumnCount)

  const autoDetected = options.autoDetected ?? !options.columnsToMask

  // Generate output path
  const sourceId = options.sourceId ?? createId()
  const outputPath = `/data/masked/source_${sourceId.slice(0, 8)}_masked_${strategy}.csv`

  const rowCount = options.rowCount ?? randomInt(1000, 1000000)
  const durationMs = options.durationMs ?? randomInt(500, 30000)

  const startedAt = createTimestamp(randomInt(0, 30))
  const completedAt =
    status !== 'error'
      ? new Date(new Date(startedAt).getTime() + durationMs).toISOString()
      : undefined

  return {
    id: options.id ?? createId(),
    source_id: sourceId,
    status,
    strategy,
    output_path: status === 'success' ? outputPath : undefined,
    columns_masked: columnsMasked,
    auto_detected: autoDetected,
    row_count: status === 'error' ? undefined : rowCount,
    column_count: columnCount,
    duration_ms: durationMs,
    error_message: status === 'error' ? faker.lorem.sentence() : undefined,
    started_at: startedAt,
    completed_at: completedAt,
    created_at: startedAt,
  }
}

/**
 * Create multiple data mask operations
 */
export function createDataMasks(count: number, sourceId?: string): DataMask[] {
  return Array.from({ length: count }, () =>
    createDataMask({ sourceId })
  ).sort(
    (a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  )
}

/**
 * Create diverse mask operations for comprehensive test coverage
 */
export function createDiverseDataMasks(sourceId: string): DataMask[] {
  const masks: DataMask[] = []

  // 1. Redact strategy - successful
  masks.push(
    createDataMask({
      sourceId,
      status: 'success',
      strategy: 'redact',
      columnsToMask: ['email', 'phone', 'ssn'],
    })
  )

  // 2. Hash strategy - successful (useful for joins)
  masks.push(
    createDataMask({
      sourceId,
      status: 'success',
      strategy: 'hash',
      columnsToMask: ['user_id', 'email'],
    })
  )

  // 3. Fake strategy - successful (realistic data replacement)
  masks.push(
    createDataMask({
      sourceId,
      status: 'success',
      strategy: 'fake',
      columnsToMask: ['first_name', 'last_name', 'email', 'phone', 'address'],
    })
  )

  // 4. Auto-detected PII columns
  masks.push(
    createDataMask({
      sourceId,
      status: 'success',
      autoDetected: true,
    })
  )

  // 5. Large dataset masking
  masks.push(
    createDataMask({
      sourceId,
      status: 'success',
      rowCount: 10000000,
      columnCount: 50,
      durationMs: 120000,
    })
  )

  // 6. Error case
  masks.push(
    createDataMask({
      sourceId,
      status: 'error',
    })
  )

  // 7. Additional random masks
  for (let i = 0; i < 4; i++) {
    masks.push(createDataMask({ sourceId }))
  }

  return masks.sort(
    (a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  )
}
