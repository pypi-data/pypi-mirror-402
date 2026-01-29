/**
 * PII scan factory - generates realistic PII scan results
 * Supports th.scan() parameters: columns, regulations, min_confidence
 */

import type { PIIScan, PIIFinding, RegulationViolation } from '@/api/client'
import {
  createId,
  createTimestamp,
  randomChoice,
  randomInt,
  faker,
} from './base'

/**
 * Options for th.scan() call - mirrors PIIScanRequest from API
 */
export interface PIIScanOptions {
  columns?: string[]
  regulations?: ('gdpr' | 'ccpa' | 'lgpd')[]
  min_confidence?: number
}

export interface PIIScanFactoryOptions {
  id?: string
  sourceId?: string
  status?: PIIScan['status']
  findingCount?: number
  hasViolations?: boolean
  violationCount?: number
  durationMs?: number
  rowCount?: number
  columnCount?: number
  minConfidence?: number
  regulationsChecked?: string[]
  /**
   * th.scan() options that influence mock behavior:
   * - columns: limits findings to these columns only
   * - regulations: determines violation generation
   * - min_confidence: filters findings below this threshold
   */
  options?: PIIScanOptions
}

// PII types commonly detected
const PII_TYPES = [
  'email',
  'phone',
  'ssn',
  'credit_card',
  'ip_address',
  'date_of_birth',
  'address',
  'name',
  'passport',
  'driver_license',
  'national_id',
  'bank_account',
]

// Columns that typically contain PII
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
  'ip',
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
  'account_number',
]

// Regulation descriptions for violations
const REGULATION_MESSAGES: Record<string, string[]> = {
  gdpr: [
    'Personal data must be processed lawfully, fairly, and transparently',
    'Data must be collected for specified, explicit, and legitimate purposes',
    'Data must be adequate, relevant, and limited to what is necessary',
    'Data must be accurate and kept up to date',
    'Data must be kept in a form which permits identification for no longer than necessary',
    'Data must be processed securely',
  ],
  ccpa: [
    'Consumer has the right to know what personal information is collected',
    'Consumer has the right to delete personal information',
    'Consumer has the right to opt-out of sale of personal information',
    'Consumer has the right to non-discrimination for exercising their rights',
    'Business must provide notice at collection',
  ],
  lgpd: [
    'Processing must have a legal basis',
    'Data subject must be informed about data processing',
    'Data must be processed for legitimate purposes',
    'Data must be adequate and relevant for processing purposes',
    'Data security measures must be implemented',
  ],
}

const SEVERITIES: ('low' | 'medium' | 'high' | 'critical')[] = [
  'critical',
  'high',
  'medium',
  'low',
]

function createPIIFinding(options?: {
  column?: string
  piiType?: string
  minConfidence?: number
}): PIIFinding {
  const column = options?.column ?? randomChoice(PII_COLUMNS)
  const piiType = options?.piiType ?? randomChoice(PII_TYPES)
  const minConf = options?.minConfidence ?? 0.8
  // Generate confidence above threshold
  const confidence = Number(
    (minConf + Math.random() * (1 - minConf)).toFixed(2)
  )

  // Generate sample values based on PII type
  const sampleValues = generateSampleValues(piiType, randomInt(1, 5))

  return {
    column,
    pii_type: piiType,
    confidence,
    sample_count: randomInt(10, 10000),
    sample_values: sampleValues,
  }
}

function generateSampleValues(piiType: string, count: number): string[] {
  const generators: Record<string, () => string> = {
    email: () => faker.internet.email(),
    phone: () => faker.phone.number(),
    ssn: () => `***-**-${randomInt(1000, 9999)}`,
    credit_card: () => `****-****-****-${randomInt(1000, 9999)}`,
    ip_address: () => faker.internet.ip(),
    date_of_birth: () => faker.date.birthdate().toISOString().split('T')[0],
    address: () => faker.location.streetAddress(),
    name: () => faker.person.fullName(),
    passport: () => `***${faker.string.alphanumeric(5)}***`,
    driver_license: () => `***${faker.string.alphanumeric(6)}***`,
    national_id: () => `***${randomInt(1000000, 9999999)}***`,
    bank_account: () => `****${randomInt(1000, 9999)}`,
  }

  const generator = generators[piiType] || (() => faker.string.alphanumeric(10))
  return Array.from({ length: count }, generator)
}

function createRegulationViolation(options?: {
  regulation?: 'gdpr' | 'ccpa' | 'lgpd'
  column?: string
  piiType?: string
}): RegulationViolation {
  const regulation = options?.regulation ?? randomChoice(['gdpr', 'ccpa', 'lgpd'] as const)
  const column = options?.column ?? randomChoice(PII_COLUMNS)
  const piiType = options?.piiType ?? randomChoice(PII_TYPES)
  const messages = REGULATION_MESSAGES[regulation] || REGULATION_MESSAGES.gdpr
  const message = randomChoice(messages)

  return {
    regulation,
    column,
    pii_type: piiType,
    message,
    severity: randomChoice(SEVERITIES),
  }
}

function createFindings(
  count: number,
  options?: {
    columns?: string[]
    minConfidence?: number
  }
): PIIFinding[] {
  const findings: PIIFinding[] = []
  const availableColumns = options?.columns?.length
    ? options.columns
    : PII_COLUMNS

  for (let i = 0; i < count; i++) {
    findings.push(
      createPIIFinding({
        column: randomChoice(availableColumns),
        minConfidence: options?.minConfidence,
      })
    )
  }

  return findings
}

function createViolations(
  count: number,
  options?: {
    regulations?: ('gdpr' | 'ccpa' | 'lgpd')[]
    findings?: PIIFinding[]
  }
): RegulationViolation[] {
  const violations: RegulationViolation[] = []
  const regulations = options?.regulations?.length
    ? options.regulations
    : (['gdpr', 'ccpa', 'lgpd'] as const)

  for (let i = 0; i < count; i++) {
    const finding = options?.findings?.[i % (options?.findings?.length || 1)]
    violations.push(
      createRegulationViolation({
        regulation: randomChoice([...regulations]),
        column: finding?.column,
        piiType: finding?.pii_type,
      })
    )
  }

  return violations
}

export function createPIIScan(
  factoryOptions: PIIScanFactoryOptions = {}
): PIIScan {
  const { options: scanOptions, ...baseOptions } = factoryOptions
  const status = baseOptions.status ?? randomChoice(['success', 'failed', 'error'])

  // Determine finding count
  let findingCount: number
  if (baseOptions.findingCount !== undefined) {
    findingCount = baseOptions.findingCount
  } else {
    findingCount = status === 'error' ? 0 : randomInt(0, 15)
  }

  // Create findings
  const findings = createFindings(findingCount, {
    columns: scanOptions?.columns,
    minConfidence: scanOptions?.min_confidence ?? baseOptions.minConfidence ?? 0.8,
  })

  // Determine if has violations
  const hasViolations =
    baseOptions.hasViolations ??
    (scanOptions?.regulations && scanOptions.regulations.length > 0 && findingCount > 0)

  // Create violations if regulations were checked
  let violations: RegulationViolation[] = []
  if (hasViolations) {
    const violationCount =
      baseOptions.violationCount ?? Math.min(findingCount, randomInt(1, 5))
    violations = createViolations(violationCount, {
      regulations: scanOptions?.regulations,
      findings,
    })
  }

  // Calculate unique columns with PII
  const columnsWithPii = new Set(findings.map((f) => f.column)).size
  const totalColumnsScanned =
    baseOptions.columnCount ?? randomInt(columnsWithPii + 2, 50)

  const durationMs = baseOptions.durationMs ?? randomInt(500, 30000)
  const startedAt = createTimestamp(randomInt(0, 30))
  const completedAt =
    status !== 'error'
      ? new Date(new Date(startedAt).getTime() + durationMs).toISOString()
      : undefined

  return {
    id: baseOptions.id ?? createId(),
    source_id: baseOptions.sourceId ?? createId(),
    status,
    total_columns_scanned: totalColumnsScanned,
    columns_with_pii: columnsWithPii,
    total_findings: findings.length,
    has_violations: violations.length > 0,
    total_violations: violations.length,
    row_count: baseOptions.rowCount ?? randomInt(100, 1000000),
    column_count: totalColumnsScanned,
    min_confidence: scanOptions?.min_confidence ?? baseOptions.minConfidence ?? 0.8,
    regulations_checked:
      scanOptions?.regulations ?? baseOptions.regulationsChecked ?? null,
    findings,
    violations,
    error_message: status === 'error' ? faker.lorem.sentence() : undefined,
    duration_ms: durationMs,
    started_at: startedAt,
    completed_at: completedAt,
    created_at: startedAt,
  }
}

export function createPIIScans(count: number, sourceId?: string): PIIScan[] {
  return Array.from({ length: count }, () => createPIIScan({ sourceId })).sort(
    (a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  )
}

/**
 * Create diverse PII scans for comprehensive test coverage
 */
export function createDiversePIIScans(sourceId: string): PIIScan[] {
  const scans: PIIScan[] = []

  // 1. Clean scan - no PII found
  scans.push(
    createPIIScan({
      sourceId,
      status: 'success',
      findingCount: 0,
      hasViolations: false,
    })
  )

  // 2. PII found but no violations (no regulations checked)
  scans.push(
    createPIIScan({
      sourceId,
      status: 'success',
      findingCount: 5,
      hasViolations: false,
    })
  )

  // 3. GDPR violations
  scans.push(
    createPIIScan({
      sourceId,
      status: 'failed',
      findingCount: 8,
      hasViolations: true,
      options: {
        regulations: ['gdpr'],
      },
    })
  )

  // 4. Multiple regulation violations
  scans.push(
    createPIIScan({
      sourceId,
      status: 'failed',
      findingCount: 12,
      hasViolations: true,
      violationCount: 6,
      options: {
        regulations: ['gdpr', 'ccpa', 'lgpd'],
      },
    })
  )

  // 5. High confidence threshold scan
  scans.push(
    createPIIScan({
      sourceId,
      status: 'success',
      findingCount: 3,
      options: {
        min_confidence: 0.95,
      },
    })
  )

  // 6. Specific columns scan
  scans.push(
    createPIIScan({
      sourceId,
      status: 'success',
      findingCount: 4,
      options: {
        columns: ['email', 'phone', 'ssn'],
      },
    })
  )

  // 7. Error scan
  scans.push(
    createPIIScan({
      sourceId,
      status: 'error',
      findingCount: 0,
    })
  )

  // 8. Large dataset scan
  scans.push(
    createPIIScan({
      sourceId,
      rowCount: 10000000,
      columnCount: 150,
      durationMs: 120000,
    })
  )

  // 9. Additional random scans
  for (let i = 0; i < 5; i++) {
    scans.push(createPIIScan({ sourceId }))
  }

  return scans.sort(
    (a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  )
}
