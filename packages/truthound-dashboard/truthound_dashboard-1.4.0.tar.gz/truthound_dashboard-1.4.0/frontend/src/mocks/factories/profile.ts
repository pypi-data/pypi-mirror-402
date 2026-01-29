/**
 * Profile factory - generates data profiling results
 * Extended for comprehensive test coverage with pattern detection support
 */

import type {
  ProfileResult,
  ColumnProfile,
  DetectedPattern,
  HistogramBucket,
  SamplingMetadata,
} from '@/api/client'
import { randomInt, randomChoice, faker } from './base'

export interface ProfileFactoryOptions {
  sourceName?: string
  columnCount?: number
  rowCount?: number
  sizeBytes?: number
  // Scenario presets
  scenario?: 'normal' | 'large' | 'small' | 'empty' | 'wide' | 'highNulls' | 'lowCardinality'
  // Enhanced options
  includePatterns?: boolean
  includeSamplingMetadata?: boolean
  samplingStrategy?: string
}

// Pattern types that can be detected
const PATTERN_TYPES = [
  'email',
  'phone',
  'uuid',
  'url',
  'ip_address',
  'credit_card',
  'date',
  'datetime',
  'korean_rrn',
  'korean_phone',
  'ssn',
  'postal_code',
  'currency',
  'percentage',
] as const

// Expanded column specs with pattern detection support
const COLUMN_SPECS: Array<{
  name: string
  dtype: string
  hasStats: boolean
  patternType?: (typeof PATTERN_TYPES)[number]
  sampleValues?: () => string[]
}> = [
  // Numeric - integers
  { name: 'id', dtype: 'int64', hasStats: true },
  { name: 'user_id', dtype: 'int64', hasStats: true },
  { name: 'order_id', dtype: 'int64', hasStats: true },
  { name: 'quantity', dtype: 'int64', hasStats: true },
  { name: 'count', dtype: 'int64', hasStats: true },
  // Numeric - floats
  { name: 'amount', dtype: 'float64', hasStats: true },
  { name: 'price', dtype: 'float64', hasStats: true },
  { name: 'total', dtype: 'float64', hasStats: true },
  { name: 'score', dtype: 'float64', hasStats: true },
  { name: 'rating', dtype: 'float64', hasStats: true },
  {
    name: 'percentage',
    dtype: 'float64',
    hasStats: true,
    patternType: 'percentage',
    sampleValues: () => ['45.2%', '78.9%', '12.1%'],
  },
  // String - contact with patterns
  {
    name: 'email',
    dtype: 'object',
    hasStats: false,
    patternType: 'email',
    sampleValues: () => [faker.internet.email(), faker.internet.email(), faker.internet.email()],
  },
  {
    name: 'phone',
    dtype: 'object',
    hasStats: false,
    patternType: 'phone',
    sampleValues: () => [faker.phone.number(), faker.phone.number(), faker.phone.number()],
  },
  { name: 'address', dtype: 'object', hasStats: false },
  // String - identifiers
  { name: 'name', dtype: 'object', hasStats: false },
  { name: 'first_name', dtype: 'object', hasStats: false },
  { name: 'last_name', dtype: 'object', hasStats: false },
  { name: 'company', dtype: 'object', hasStats: false },
  // UUID columns
  {
    name: 'uuid',
    dtype: 'object',
    hasStats: false,
    patternType: 'uuid',
    sampleValues: () => [faker.string.uuid(), faker.string.uuid(), faker.string.uuid()],
  },
  {
    name: 'transaction_id',
    dtype: 'object',
    hasStats: false,
    patternType: 'uuid',
    sampleValues: () => [faker.string.uuid(), faker.string.uuid(), faker.string.uuid()],
  },
  // URL columns
  {
    name: 'website',
    dtype: 'object',
    hasStats: false,
    patternType: 'url',
    sampleValues: () => [faker.internet.url(), faker.internet.url(), faker.internet.url()],
  },
  // IP address columns
  {
    name: 'ip_address',
    dtype: 'object',
    hasStats: false,
    patternType: 'ip_address',
    sampleValues: () => [faker.internet.ip(), faker.internet.ip(), faker.internet.ip()],
  },
  // String - categorical
  { name: 'status', dtype: 'object', hasStats: false },
  { name: 'category', dtype: 'object', hasStats: false },
  { name: 'type', dtype: 'object', hasStats: false },
  { name: 'tier', dtype: 'object', hasStats: false },
  // Datetime with patterns
  {
    name: 'date',
    dtype: 'datetime64[ns]',
    hasStats: false,
    patternType: 'date',
  },
  {
    name: 'created_at',
    dtype: 'datetime64[ns]',
    hasStats: false,
    patternType: 'datetime',
  },
  {
    name: 'updated_at',
    dtype: 'datetime64[ns]',
    hasStats: false,
    patternType: 'datetime',
  },
  { name: 'timestamp', dtype: 'datetime64[ns]', hasStats: false, patternType: 'datetime' },
  // Boolean
  { name: 'is_active', dtype: 'bool', hasStats: false },
  { name: 'is_verified', dtype: 'bool', hasStats: false },
  { name: 'is_deleted', dtype: 'bool', hasStats: false },
  // Complex types
  { name: 'metadata', dtype: 'object', hasStats: false },
  { name: 'tags', dtype: 'object', hasStats: false },
  // Currency
  {
    name: 'currency_amount',
    dtype: 'object',
    hasStats: false,
    patternType: 'currency',
    sampleValues: () => ['$1,234.56', '$987.00', '$45.99'],
  },
  // Postal code
  {
    name: 'postal_code',
    dtype: 'object',
    hasStats: false,
    patternType: 'postal_code',
    sampleValues: () => ['12345', '90210', '10001'],
  },
]

/**
 * Create pattern detection result for a column
 */
function createDetectedPattern(
  patternType: string,
  totalRows: number,
  sampleValues?: () => string[]
): DetectedPattern {
  const matchPercentage = faker.number.float({ min: 85, max: 100, fractionDigits: 1 })
  const matchCount = Math.floor((totalRows * matchPercentage) / 100)

  return {
    patternType,
    confidence: faker.number.float({ min: 0.85, max: 1.0, fractionDigits: 2 }),
    matchCount,
    matchPercentage,
    sampleMatches: sampleValues ? sampleValues() : undefined,
  }
}

/**
 * Create histogram for numeric columns
 */
function createHistogram(min: number, max: number): HistogramBucket[] {
  const buckets: HistogramBucket[] = []
  const bucketCount = 10
  const range = max - min
  const bucketSize = range / bucketCount
  let remaining = 100

  for (let i = 0; i < bucketCount; i++) {
    const bucketStart = min + i * bucketSize
    const bucketEnd = min + (i + 1) * bucketSize
    const percentage =
      i === bucketCount - 1
        ? remaining
        : faker.number.float({ min: 5, max: Math.min(20, remaining), fractionDigits: 1 })
    remaining -= percentage

    buckets.push({
      bucket: `${bucketStart.toFixed(0)}-${bucketEnd.toFixed(0)}`,
      count: Math.floor((percentage / 100) * 10000),
      percentage,
    })
  }

  return buckets
}

interface EnhancedColumnProfileOptions {
  highNulls?: boolean
  lowCardinality?: boolean
  includePatterns?: boolean
  rowCount?: number
}

function createColumnProfile(
  spec: (typeof COLUMN_SPECS)[0],
  options?: EnhancedColumnProfileOptions
): ColumnProfile & {
  inferredType?: string | null
  nullCount?: number | null
  isUnique?: boolean | null
  median?: number | null
  q1?: number | null
  q3?: number | null
  skewness?: number | null
  kurtosis?: number | null
  minLength?: number | null
  maxLength?: number | null
  avgLength?: number | null
  patterns?: DetectedPattern[] | null
  primaryPattern?: string | null
  histogram?: HistogramBucket[] | null
  cardinalityEstimate?: number | null
} {
  const rowCount = options?.rowCount ?? 10000

  // Vary null percentage based on options
  let nullPct: number
  if (options?.highNulls) {
    nullPct = faker.number.float({ min: 30, max: 80, fractionDigits: 1 })
  } else {
    nullPct = faker.number.float({ min: 0, max: 15, fractionDigits: 1 })
  }

  // Vary unique percentage based on options
  let uniquePct: number
  if (options?.lowCardinality) {
    uniquePct = faker.number.float({ min: 1, max: 10, fractionDigits: 1 })
  } else {
    uniquePct = faker.number.float({ min: 20, max: 100, fractionDigits: 1 })
  }

  const nullCount = Math.floor((rowCount * nullPct) / 100)
  const isUnique = uniquePct >= 99

  const profile: ColumnProfile & {
    inferredType?: string | null
    nullCount?: number | null
    isUnique?: boolean | null
    median?: number | null
    q1?: number | null
    q3?: number | null
    skewness?: number | null
    kurtosis?: number | null
    minLength?: number | null
    maxLength?: number | null
    avgLength?: number | null
    patterns?: DetectedPattern[] | null
    primaryPattern?: string | null
    histogram?: HistogramBucket[] | null
    cardinalityEstimate?: number | null
  } = {
    name: spec.name,
    dtype: spec.dtype,
    null_pct: `${nullPct}%`,
    unique_pct: `${uniquePct}%`,
    nullCount,
    isUnique,
  }

  // Add numeric statistics
  if (spec.hasStats) {
    const mean = faker.number.float({ min: 0, max: 10000, fractionDigits: 2 })
    const std = faker.number.float({ min: 0, max: mean * 0.3, fractionDigits: 2 })
    const min = mean - std * 2
    const max = mean + std * 2

    profile.min = min
    profile.max = max
    profile.mean = mean
    profile.std = std
    profile.median = mean + faker.number.float({ min: -std, max: std, fractionDigits: 2 })
    profile.q1 = min + (mean - min) * 0.5
    profile.q3 = mean + (max - mean) * 0.5
    profile.skewness = faker.number.float({ min: -2, max: 2, fractionDigits: 3 })
    profile.kurtosis = faker.number.float({ min: -1, max: 5, fractionDigits: 3 })

    // Add histogram for numeric columns
    profile.histogram = createHistogram(min, max)
  }

  // Add string statistics for object types
  if (spec.dtype === 'object') {
    profile.minLength = randomInt(1, 10)
    profile.maxLength = randomInt(20, 100)
    profile.avgLength = faker.number.float({
      min: profile.minLength,
      max: profile.maxLength,
      fractionDigits: 1,
    })
  }

  // Add cardinality estimate
  const distinctCount = Math.floor((rowCount * uniquePct) / 100)
  profile.cardinalityEstimate = distinctCount

  // Add pattern detection if enabled and spec has a pattern
  if (options?.includePatterns && spec.patternType) {
    const pattern = createDetectedPattern(spec.patternType, rowCount, spec.sampleValues)
    profile.patterns = [pattern]
    profile.primaryPattern = spec.patternType
    profile.inferredType = spec.patternType
  }

  return profile
}

export function createProfileResult(options: ProfileFactoryOptions = {}): ProfileResult {
  // Handle scenario presets
  let columnCount: number
  let rowCount: number
  let sizeBytes: number
  let profileOptions: EnhancedColumnProfileOptions = {
    includePatterns: options.includePatterns ?? true, // Default to include patterns
  }

  switch (options.scenario) {
    case 'empty':
      columnCount = options.columnCount ?? randomInt(3, 8)
      rowCount = 0
      sizeBytes = randomInt(100, 1000)
      break
    case 'small':
      columnCount = options.columnCount ?? randomInt(3, 6)
      rowCount = options.rowCount ?? randomInt(10, 100)
      sizeBytes = options.sizeBytes ?? randomInt(1000, 10000)
      break
    case 'large':
      columnCount = options.columnCount ?? randomInt(15, 25)
      rowCount = options.rowCount ?? randomInt(10000000, 100000000)
      sizeBytes = options.sizeBytes ?? randomInt(1000000000, 10000000000) // 1-10 GB
      break
    case 'wide':
      columnCount = options.columnCount ?? randomInt(50, 100)
      rowCount = options.rowCount ?? randomInt(10000, 100000)
      sizeBytes = options.sizeBytes ?? randomInt(100000000, 500000000)
      break
    case 'highNulls':
      columnCount = options.columnCount ?? randomInt(6, 12)
      rowCount = options.rowCount ?? randomInt(10000, 1000000)
      sizeBytes = options.sizeBytes ?? randomInt(1000000, 100000000)
      profileOptions = { ...profileOptions, highNulls: true }
      break
    case 'lowCardinality':
      columnCount = options.columnCount ?? randomInt(6, 12)
      rowCount = options.rowCount ?? randomInt(10000, 1000000)
      sizeBytes = options.sizeBytes ?? randomInt(1000000, 100000000)
      profileOptions = { ...profileOptions, lowCardinality: true }
      break
    default: // 'normal'
      columnCount = options.columnCount ?? randomInt(6, 12)
      rowCount = options.rowCount ?? randomInt(10000, 1000000)
      sizeBytes = options.sizeBytes ?? randomInt(1000000, 100000000)
  }

  // Set row count in options for pattern detection
  profileOptions.rowCount = rowCount

  // Ensure we don't request more columns than available
  const safeColumnCount = Math.min(columnCount, COLUMN_SPECS.length)
  const selectedSpecs = faker.helpers
    .shuffle([...COLUMN_SPECS])
    .slice(0, safeColumnCount)

  const columns = selectedSpecs.map((spec) => createColumnProfile(spec, profileOptions))

  // Build pattern summary
  const detectedPatternsSummary: Record<string, number> = {}
  columns.forEach((col) => {
    if (col.primaryPattern) {
      detectedPatternsSummary[col.primaryPattern] =
        (detectedPatternsSummary[col.primaryPattern] || 0) + 1
    }
  })

  // Build sampling metadata if requested
  let sampling: SamplingMetadata | undefined
  if (options.includeSamplingMetadata) {
    const strategy = options.samplingStrategy ?? 'adaptive'
    const sampleSize = strategy === 'none' ? rowCount : Math.min(rowCount, randomInt(10000, 50000))
    sampling = {
      strategyUsed: strategy,
      sampleSize,
      totalRows: rowCount,
      samplingRatio: sampleSize / rowCount,
      seed: strategy !== 'none' ? randomInt(1, 99999) : null,
      confidenceLevel: 0.95,
      marginOfError: 0.03,
    }
  }

  return {
    source: options.sourceName ?? faker.system.fileName(),
    row_count: rowCount,
    column_count: safeColumnCount,
    size_bytes: sizeBytes,
    columns,
    // Enhanced fields
    sampling: sampling ?? null,
    detected_patterns_summary:
      Object.keys(detectedPatternsSummary).length > 0 ? detectedPatternsSummary : null,
    profiled_at: new Date().toISOString(),
    profiling_duration_ms: randomInt(500, 5000),
  }
}

/**
 * Create diverse profile results for testing all scenarios
 */
export function createDiverseProfiles(sourceNames: string[]): ProfileResult[] {
  const profiles: ProfileResult[] = []
  const scenarios: ProfileFactoryOptions['scenario'][] = [
    'normal',
    'large',
    'small',
    'empty',
    'wide',
    'highNulls',
    'lowCardinality',
  ]

  // Create one profile for each scenario
  scenarios.forEach((scenario, i) => {
    const sourceName = sourceNames[i % sourceNames.length] ?? `Source ${i + 1}`
    profiles.push(createProfileResult({ scenario, sourceName }))
  })

  // Add a few more random profiles
  for (let i = scenarios.length; i < Math.max(scenarios.length, sourceNames.length); i++) {
    const sourceName = sourceNames[i % sourceNames.length]
    profiles.push(createProfileResult({
      sourceName,
      scenario: randomChoice(scenarios),
    }))
  }

  return profiles
}
