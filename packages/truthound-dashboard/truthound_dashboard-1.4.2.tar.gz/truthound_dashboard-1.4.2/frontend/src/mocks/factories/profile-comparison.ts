/**
 * Profile Comparison factory - generates profile comparison and trend data
 */

import { createId, createTimestamp, randomChoice, randomInt, faker } from './base'

// Types matching backend schemas
export type TrendDirection = 'up' | 'down' | 'stable'

export interface ColumnComparison {
  column: string
  metric: string
  baseline_value: number | string | null
  current_value: number | string | null
  change: number | null
  change_pct: number | null
  is_significant: boolean
  trend: TrendDirection
}

export interface ProfileComparisonResponse {
  baseline_profile_id: string
  current_profile_id: string
  source_id: string
  source_name: string
  baseline_timestamp: string
  current_timestamp: string
  row_count_change: number
  row_count_change_pct: number
  column_count_change: number
  column_comparisons: ColumnComparison[]
  significant_changes: number
  summary: {
    total_columns: number
    columns_with_changes: number
    significant_changes: number
    columns_improved: number
    columns_degraded: number
  }
  compared_at: string
}

export interface ProfileTrendPoint {
  timestamp: string
  profile_id: string
  row_count: number
  avg_null_pct: number
  avg_unique_pct: number
  column_count: number
}

export interface ProfileTrendResponse {
  source_id: string
  source_name: string
  period_start: string
  period_end: string
  granularity: 'daily' | 'weekly' | 'monthly'
  data_points: ProfileTrendPoint[]
  trends: {
    row_count: TrendDirection
    null_pct: TrendDirection
    unique_pct: TrendDirection
  }
}

export interface ProfileSummary {
  id: string
  source_id: string
  row_count: number
  column_count: number
  size_bytes: number
  avg_null_pct: number
  avg_unique_pct: number
  created_at: string
}

const METRICS = [
  'null_pct',
  'unique_pct',
  'min',
  'max',
  'mean',
  'std',
  'distinct_count',
]

const COLUMN_NAMES = [
  'user_id',
  'email',
  'name',
  'phone',
  'amount',
  'price',
  'status',
  'category',
  'created_at',
  'is_active',
]

function determineTrend(change: number | null): TrendDirection {
  if (change === null) return 'stable'
  if (Math.abs(change) < 1) return 'stable'
  return change > 0 ? 'up' : 'down'
}

function createColumnComparison(columnName: string): ColumnComparison {
  const metric = randomChoice(METRICS)
  const isNumeric = ['min', 'max', 'mean', 'std', 'distinct_count'].includes(metric)

  let baselineValue: number | string | null
  let currentValue: number | string | null
  let change: number | null = null
  let changePct: number | null = null

  if (isNumeric) {
    baselineValue = faker.number.float({ min: 0, max: 1000, fractionDigits: 2 })
    // Generate current value with some variation from baseline
    const variation = faker.number.float({ min: -20, max: 20, fractionDigits: 2 })
    currentValue = Math.max(0, baselineValue + variation)
    change = currentValue - baselineValue
    changePct = baselineValue !== 0 ? (change / baselineValue) * 100 : 0
  } else {
    // For percentage metrics
    baselineValue = faker.number.float({ min: 0, max: 100, fractionDigits: 1 })
    const variation = faker.number.float({ min: -10, max: 10, fractionDigits: 1 })
    currentValue = Math.max(0, Math.min(100, (baselineValue as number) + variation))
    change = (currentValue as number) - (baselineValue as number)
    changePct = baselineValue !== 0 ? (change / (baselineValue as number)) * 100 : 0
  }

  const isSignificant = Math.abs(changePct || 0) > 5

  return {
    column: columnName,
    metric,
    baseline_value: baselineValue,
    current_value: currentValue,
    change: Number(change?.toFixed(2)) || null,
    change_pct: Number(changePct?.toFixed(2)) || null,
    is_significant: isSignificant,
    trend: determineTrend(change),
  }
}

export function createProfileComparisonResponse(
  sourceId: string,
  sourceName: string,
  options: {
    baselineProfileId?: string
    currentProfileId?: string
    columnCount?: number
  } = {}
): ProfileComparisonResponse {
  const columnCount = options.columnCount ?? randomInt(6, 12)
  const columns = faker.helpers.shuffle([...COLUMN_NAMES]).slice(0, columnCount)

  // Generate multiple comparisons per column (different metrics)
  const columnComparisons: ColumnComparison[] = []
  for (const col of columns) {
    // Add 1-3 metric comparisons per column
    const metricCount = randomInt(1, 3)
    const usedMetrics = new Set<string>()

    for (let i = 0; i < metricCount; i++) {
      const comparison = createColumnComparison(col)
      if (!usedMetrics.has(comparison.metric)) {
        columnComparisons.push(comparison)
        usedMetrics.add(comparison.metric)
      }
    }
  }

  const significantChanges = columnComparisons.filter((c) => c.is_significant).length
  const columnsImproved = columnComparisons.filter(
    (c) => c.metric === 'null_pct' && c.trend === 'down'
  ).length + columnComparisons.filter(
    (c) => c.metric === 'unique_pct' && c.trend === 'up'
  ).length
  const columnsDegraded = columnComparisons.filter(
    (c) => c.metric === 'null_pct' && c.trend === 'up'
  ).length + columnComparisons.filter(
    (c) => c.metric === 'unique_pct' && c.trend === 'down'
  ).length

  const baselineRowCount = randomInt(10000, 1000000)
  const rowCountChange = randomInt(-10000, 50000)
  // Note: currentRowCount can be computed as: baselineRowCount + rowCountChange

  return {
    baseline_profile_id: options.baselineProfileId ?? createId(),
    current_profile_id: options.currentProfileId ?? createId(),
    source_id: sourceId,
    source_name: sourceName,
    baseline_timestamp: createTimestamp(randomInt(7, 30)),
    current_timestamp: createTimestamp(0),
    row_count_change: rowCountChange,
    row_count_change_pct: Number(((rowCountChange / baselineRowCount) * 100).toFixed(2)),
    column_count_change: 0,
    column_comparisons: columnComparisons,
    significant_changes: significantChanges,
    summary: {
      total_columns: columns.length,
      columns_with_changes: columnComparisons.filter((c) => c.change !== 0).length,
      significant_changes: significantChanges,
      columns_improved: columnsImproved,
      columns_degraded: columnsDegraded,
    },
    compared_at: new Date().toISOString(),
  }
}

export function createProfileTrendPoint(
  daysAgo: number,
  baseValues?: {
    rowCount: number
    avgNullPct: number
    avgUniquePct: number
    columnCount: number
  }
): ProfileTrendPoint {
  // Create trend with some natural variation
  const base = baseValues ?? {
    rowCount: randomInt(50000, 500000),
    avgNullPct: faker.number.float({ min: 2, max: 15, fractionDigits: 1 }),
    avgUniquePct: faker.number.float({ min: 40, max: 80, fractionDigits: 1 }),
    columnCount: randomInt(8, 15),
  }

  // Add some variation based on time
  const rowVariation = Math.floor(base.rowCount * 0.02 * (30 - daysAgo) / 30)
  const nullVariation = faker.number.float({ min: -2, max: 2, fractionDigits: 1 })
  const uniqueVariation = faker.number.float({ min: -3, max: 3, fractionDigits: 1 })

  return {
    timestamp: createTimestamp(daysAgo),
    profile_id: createId(),
    row_count: base.rowCount + rowVariation,
    avg_null_pct: Math.max(0, Math.min(100, base.avgNullPct + nullVariation)),
    avg_unique_pct: Math.max(0, Math.min(100, base.avgUniquePct + uniqueVariation)),
    column_count: base.columnCount,
  }
}

export function createProfileTrendResponse(
  sourceId: string,
  sourceName: string,
  options: {
    granularity?: 'daily' | 'weekly' | 'monthly'
    pointCount?: number
  } = {}
): ProfileTrendResponse {
  const granularity = options.granularity ?? 'daily'
  const pointCount = options.pointCount ?? (granularity === 'daily' ? 30 : granularity === 'weekly' ? 12 : 6)

  // Create base values for consistent trends
  const baseValues = {
    rowCount: randomInt(50000, 500000),
    avgNullPct: faker.number.float({ min: 2, max: 15, fractionDigits: 1 }),
    avgUniquePct: faker.number.float({ min: 40, max: 80, fractionDigits: 1 }),
    columnCount: randomInt(8, 15),
  }

  const dataPoints: ProfileTrendPoint[] = []
  const dayMultiplier = granularity === 'daily' ? 1 : granularity === 'weekly' ? 7 : 30

  for (let i = pointCount - 1; i >= 0; i--) {
    dataPoints.push(createProfileTrendPoint(i * dayMultiplier, baseValues))
  }

  // Calculate overall trends
  const firstPoint = dataPoints[0]
  const lastPoint = dataPoints[dataPoints.length - 1]

  const rowCountTrend: TrendDirection =
    lastPoint.row_count > firstPoint.row_count * 1.05 ? 'up' :
    lastPoint.row_count < firstPoint.row_count * 0.95 ? 'down' : 'stable'

  const nullPctTrend: TrendDirection =
    lastPoint.avg_null_pct > firstPoint.avg_null_pct + 2 ? 'up' :
    lastPoint.avg_null_pct < firstPoint.avg_null_pct - 2 ? 'down' : 'stable'

  const uniquePctTrend: TrendDirection =
    lastPoint.avg_unique_pct > firstPoint.avg_unique_pct + 2 ? 'up' :
    lastPoint.avg_unique_pct < firstPoint.avg_unique_pct - 2 ? 'down' : 'stable'

  return {
    source_id: sourceId,
    source_name: sourceName,
    period_start: dataPoints[0].timestamp,
    period_end: dataPoints[dataPoints.length - 1].timestamp,
    granularity,
    data_points: dataPoints,
    trends: {
      row_count: rowCountTrend,
      null_pct: nullPctTrend,
      unique_pct: uniquePctTrend,
    },
  }
}

export function createProfileSummary(
  sourceId: string,
  daysAgo: number = 0
): ProfileSummary {
  return {
    id: createId(),
    source_id: sourceId,
    row_count: randomInt(10000, 1000000),
    column_count: randomInt(6, 20),
    size_bytes: randomInt(1000000, 100000000),
    avg_null_pct: faker.number.float({ min: 0, max: 20, fractionDigits: 1 }),
    avg_unique_pct: faker.number.float({ min: 30, max: 100, fractionDigits: 1 }),
    created_at: createTimestamp(daysAgo),
  }
}

export function createProfileHistory(
  sourceId: string,
  count: number = 10
): ProfileSummary[] {
  const profiles: ProfileSummary[] = []

  for (let i = 0; i < count; i++) {
    profiles.push(createProfileSummary(sourceId, i * randomInt(1, 7)))
  }

  return profiles
}
