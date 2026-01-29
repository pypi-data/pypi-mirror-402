/**
 * Report History Mock Factory
 *
 * Generates realistic mock data for report history records.
 */
import { faker, createId, createTimestamp } from './base'

// Helper functions
function generateId(): string {
  return createId()
}

function generateTimestamps(): { created_at: string; updated_at: string } {
  const created = createTimestamp(faker.number.int({ min: 1, max: 30 }))
  const updated = createTimestamp(faker.number.int({ min: 0, max: 1 }))
  return { created_at: created, updated_at: updated }
}

export type ReportStatus = 'pending' | 'generating' | 'completed' | 'failed' | 'expired'
export type ReportFormat = 'html' | 'pdf' | 'csv' | 'json' | 'markdown' | 'junit' | 'excel'

export interface GeneratedReport {
  id: string
  name: string
  description?: string
  format: ReportFormat
  theme?: string
  locale: string
  config?: Record<string, unknown>
  metadata?: Record<string, unknown>
  validation_id?: string
  source_id?: string
  reporter_id?: string
  status: ReportStatus
  file_path?: string
  file_size?: number
  content_hash?: string
  error_message?: string
  generation_time_ms?: number
  expires_at?: string
  downloaded_count: number
  last_downloaded_at?: string
  created_at: string
  updated_at: string
  source_name?: string
  reporter_name?: string
  download_url?: string
}

export interface ReportStatistics {
  total_reports: number
  total_size_bytes: number
  reports_by_format: Record<string, number>
  reports_by_status: Record<string, number>
  total_downloads: number
  avg_generation_time_ms?: number
  expired_count: number
  reporters_used: number
}

const FORMATS: ReportFormat[] = ['html', 'pdf', 'csv', 'json', 'markdown', 'junit', 'excel']
const STATUSES: ReportStatus[] = ['pending', 'generating', 'completed', 'failed', 'expired']
const THEMES = ['light', 'dark', 'professional', 'minimal', 'high_contrast']
const LOCALES = ['en', 'ko', 'ja', 'zh', 'de', 'fr', 'es', 'pt', 'it', 'ru']

const SOURCE_NAMES = [
  'Customer Orders',
  'Product Inventory',
  'User Analytics',
  'Sales Data',
  'Transaction Log',
  'API Events',
  'System Metrics',
  'User Sessions',
]

const REPORTER_NAMES = [
  'Executive Summary Reporter',
  'Detailed Analysis Reporter',
  'Compliance Report Generator',
  'Quick Stats Reporter',
  'Data Quality Scorecard',
]

/**
 * Create a single generated report record.
 */
export function createGeneratedReport(overrides: Partial<GeneratedReport> = {}): GeneratedReport {
  const status = overrides.status || faker.helpers.arrayElement(STATUSES)
  const format = overrides.format || faker.helpers.arrayElement(FORMATS)
  const { created_at, updated_at } = generateTimestamps()

  const hasReporter = faker.datatype.boolean({ probability: 0.3 })
  const isCompleted = status === 'completed'
  const isFailed = status === 'failed'
  const isExpired = status === 'expired'

  // Generate expiration date
  let expires_at: string | undefined
  if (isExpired) {
    expires_at = faker.date.past({ years: 0.1 }).toISOString()
  } else if (faker.datatype.boolean({ probability: 0.7 })) {
    expires_at = faker.date.future({ years: 0.1 }).toISOString()
  }

  // Generate file info for completed reports
  const file_size = isCompleted ? faker.number.int({ min: 1024, max: 10485760 }) : undefined
  const file_path = isCompleted ? `data/reports/${generateId()}.${format}` : undefined
  const content_hash = isCompleted ? faker.string.hexadecimal({ length: 64, casing: 'lower' }).slice(2) : undefined
  const generation_time_ms = isCompleted ? faker.number.float({ min: 100, max: 5000, fractionDigits: 2 }) : undefined

  const report: GeneratedReport = {
    id: generateId(),
    name: `${faker.helpers.arrayElement(['Validation Report', 'Quality Report', 'Analysis Report', 'Summary Report'])} - ${faker.date.recent().toLocaleDateString()}`,
    description: faker.datatype.boolean({ probability: 0.6 }) ? faker.lorem.sentence() : undefined,
    format,
    theme: faker.helpers.arrayElement(THEMES),
    locale: faker.helpers.arrayElement(LOCALES),
    config: faker.datatype.boolean({ probability: 0.3 }) ? { include_samples: true, max_rows: 1000 } : undefined,
    metadata: faker.datatype.boolean({ probability: 0.2 }) ? { version: '1.0', generated_by: 'system' } : undefined,
    validation_id: faker.datatype.boolean({ probability: 0.8 }) ? generateId() : undefined,
    source_id: generateId(),
    reporter_id: hasReporter ? generateId() : undefined,
    status,
    file_path,
    file_size,
    content_hash,
    error_message: isFailed ? faker.lorem.sentence() : undefined,
    generation_time_ms,
    expires_at,
    downloaded_count: isCompleted ? faker.number.int({ min: 0, max: 50 }) : 0,
    last_downloaded_at: isCompleted && faker.datatype.boolean({ probability: 0.5 })
      ? faker.date.recent().toISOString()
      : undefined,
    created_at,
    updated_at,
    source_name: faker.helpers.arrayElement(SOURCE_NAMES),
    reporter_name: hasReporter ? faker.helpers.arrayElement(REPORTER_NAMES) : undefined,
    ...overrides,
  }

  // Add download URL for completed reports
  if (report.status === 'completed') {
    report.download_url = `/api/v1/reports/history/${report.id}/download`
  }

  return report
}

/**
 * Generate multiple report records.
 */
export function generateReports(count: number = 20): GeneratedReport[] {
  return Array.from({ length: count }, () => createGeneratedReport())
}

/**
 * Generate report statistics.
 */
export function generateReportStatistics(reports?: GeneratedReport[]): ReportStatistics {
  const data = reports || generateReports(50)

  const reports_by_format: Record<string, number> = {}
  const reports_by_status: Record<string, number> = {}
  let total_size = 0
  let total_downloads = 0
  const generation_times: number[] = []
  let expired_count = 0
  const reporters = new Set<string>()

  for (const report of data) {
    // By format
    reports_by_format[report.format] = (reports_by_format[report.format] || 0) + 1

    // By status
    reports_by_status[report.status] = (reports_by_status[report.status] || 0) + 1

    // Total size
    if (report.file_size) {
      total_size += report.file_size
    }

    // Downloads
    total_downloads += report.downloaded_count

    // Generation time
    if (report.generation_time_ms) {
      generation_times.push(report.generation_time_ms)
    }

    // Expired
    if (report.status === 'expired') {
      expired_count++
    }

    // Reporters
    if (report.reporter_id) {
      reporters.add(report.reporter_id)
    }
  }

  const avg_generation_time_ms = generation_times.length > 0
    ? generation_times.reduce((a, b) => a + b, 0) / generation_times.length
    : undefined

  return {
    total_reports: data.length,
    total_size_bytes: total_size,
    reports_by_format,
    reports_by_status,
    total_downloads,
    avg_generation_time_ms,
    expired_count,
    reporters_used: reporters.size,
  }
}
