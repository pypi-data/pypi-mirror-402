/**
 * Report History Mock Handlers
 *
 * MSW handlers for report history API endpoints.
 */
import { http, HttpResponse, delay } from 'msw'
import {
  createGeneratedReport,
  generateReports,
  generateReportStatistics,
  type GeneratedReport,
  type ReportStatistics,
} from '../factories/reports'

const API_BASE = '/api/v1'

// In-memory store for generated reports
let reportsStore: GeneratedReport[] = generateReports(30)

/**
 * Get filtered reports based on query parameters.
 */
function filterReports(params: URLSearchParams): { items: GeneratedReport[]; total: number } {
  let filtered = [...reportsStore]

  // Apply filters
  const sourceId = params.get('source_id')
  if (sourceId) {
    filtered = filtered.filter((r) => r.source_id === sourceId)
  }

  const validationId = params.get('validation_id')
  if (validationId) {
    filtered = filtered.filter((r) => r.validation_id === validationId)
  }

  const reporterId = params.get('reporter_id')
  if (reporterId) {
    filtered = filtered.filter((r) => r.reporter_id === reporterId)
  }

  const format = params.get('format')
  if (format) {
    filtered = filtered.filter((r) => r.format === format)
  }

  const status = params.get('status')
  if (status) {
    filtered = filtered.filter((r) => r.status === status)
  }

  const includeExpired = params.get('include_expired') === 'true'
  if (!includeExpired) {
    filtered = filtered.filter((r) => r.status !== 'expired')
  }

  const search = params.get('search')
  if (search) {
    const lowerSearch = search.toLowerCase()
    filtered = filtered.filter((r) => r.name.toLowerCase().includes(lowerSearch))
  }

  // Sorting
  const sortBy = params.get('sort_by') || 'created_at'
  const sortOrder = params.get('sort_order') || 'desc'
  filtered.sort((a, b) => {
    const aVal = (a as unknown as Record<string, unknown>)[sortBy]
    const bVal = (b as unknown as Record<string, unknown>)[sortBy]
    if (aVal === bVal) return 0
    if (sortOrder === 'desc') {
      return aVal && bVal && aVal > bVal ? -1 : 1
    }
    return aVal && bVal && aVal < bVal ? -1 : 1
  })

  // Pagination
  const page = parseInt(params.get('page') || '1', 10)
  const pageSize = parseInt(params.get('page_size') || '20', 10)
  const start = (page - 1) * pageSize
  const items = filtered.slice(start, start + pageSize)

  return {
    items,
    total: filtered.length,
  }
}

export const reportHistoryHandlers = [
  // List reports
  http.get(`${API_BASE}/reports/history`, async ({ request }) => {
    await delay(300)
    const url = new URL(request.url)
    const { items, total } = filterReports(url.searchParams)
    const page = parseInt(url.searchParams.get('page') || '1', 10)
    const pageSize = parseInt(url.searchParams.get('page_size') || '20', 10)

    return HttpResponse.json({
      items,
      total,
      page,
      page_size: pageSize,
    })
  }),

  // Get statistics
  http.get(`${API_BASE}/reports/history/statistics`, async () => {
    await delay(200)
    const stats = generateReportStatistics(reportsStore)
    return HttpResponse.json(stats)
  }),

  // Get single report
  http.get(`${API_BASE}/reports/history/:reportId`, async ({ params }) => {
    await delay(150)
    const { reportId } = params
    const report = reportsStore.find((r) => r.id === reportId)

    if (!report) {
      return HttpResponse.json({ detail: 'Report not found' }, { status: 404 })
    }

    return HttpResponse.json(report)
  }),

  // Create report record
  http.post(`${API_BASE}/reports/history`, async ({ request }) => {
    await delay(300)
    const data = (await request.json()) as Partial<GeneratedReport>
    const newReport = createGeneratedReport({
      ...data,
      status: 'pending',
    })
    reportsStore.unshift(newReport)
    return HttpResponse.json(newReport, { status: 201 })
  }),

  // Update report record
  http.patch(`${API_BASE}/reports/history/:reportId`, async ({ params, request }) => {
    await delay(200)
    const { reportId } = params
    const index = reportsStore.findIndex((r) => r.id === reportId)

    if (index === -1) {
      return HttpResponse.json({ detail: 'Report not found' }, { status: 404 })
    }

    const updates = (await request.json()) as Partial<GeneratedReport>
    reportsStore[index] = {
      ...reportsStore[index],
      ...updates,
      updated_at: new Date().toISOString(),
    }

    return HttpResponse.json(reportsStore[index])
  }),

  // Delete report record
  http.delete(`${API_BASE}/reports/history/:reportId`, async ({ params }) => {
    await delay(200)
    const { reportId } = params
    const index = reportsStore.findIndex((r) => r.id === reportId)

    if (index === -1) {
      return HttpResponse.json({ detail: 'Report not found' }, { status: 404 })
    }

    reportsStore.splice(index, 1)
    return new HttpResponse(null, { status: 204 })
  }),

  // Download report
  http.get(`${API_BASE}/reports/history/:reportId/download`, async ({ params }) => {
    await delay(500)
    const { reportId } = params
    const report = reportsStore.find((r) => r.id === reportId)

    if (!report) {
      return HttpResponse.json({ detail: 'Report not found' }, { status: 404 })
    }

    if (report.status !== 'completed') {
      return HttpResponse.json({ detail: `Report is not ready (status: ${report.status})` }, { status: 400 })
    }

    // Increment download count
    report.downloaded_count += 1
    report.last_downloaded_at = new Date().toISOString()

    // Return mock content based on format
    const contentMap: Record<string, { content: string; type: string }> = {
      html: { content: '<html><body><h1>Mock Report</h1></body></html>', type: 'text/html' },
      pdf: { content: 'Mock PDF content', type: 'application/pdf' },
      csv: { content: 'col1,col2,col3\nval1,val2,val3', type: 'text/csv' },
      json: { content: JSON.stringify({ report: 'Mock data' }), type: 'application/json' },
      markdown: { content: '# Mock Report\n\nContent here', type: 'text/markdown' },
      junit: { content: '<?xml version="1.0"?><testsuite></testsuite>', type: 'application/xml' },
      excel: { content: 'Mock Excel content', type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' },
    }

    const { content, type } = contentMap[report.format] || contentMap.html

    return new HttpResponse(content, {
      headers: {
        'Content-Type': type,
        'Content-Disposition': `attachment; filename="${report.name}.${report.format}"`,
      },
    })
  }),

  // Generate report content
  http.post(`${API_BASE}/reports/history/:reportId/generate`, async ({ params }) => {
    await delay(1000) // Simulate generation time
    const { reportId } = params
    const index = reportsStore.findIndex((r) => r.id === reportId)

    if (index === -1) {
      return HttpResponse.json({ detail: 'Report not found' }, { status: 404 })
    }

    const report = reportsStore[index]

    if (report.status === 'completed') {
      return HttpResponse.json({ detail: 'Report already generated' }, { status: 400 })
    }

    // Update report to completed
    reportsStore[index] = {
      ...report,
      status: 'completed',
      file_path: `data/reports/${report.id}.${report.format}`,
      file_size: Math.floor(Math.random() * 1000000) + 1024,
      content_hash: Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join(''),
      generation_time_ms: Math.random() * 2000 + 100,
      download_url: `/api/v1/reports/history/${report.id}/download`,
      updated_at: new Date().toISOString(),
    }

    return HttpResponse.json(reportsStore[index])
  }),

  // Cleanup expired reports
  http.post(`${API_BASE}/reports/history/cleanup`, async () => {
    await delay(500)
    const before = reportsStore.length
    reportsStore = reportsStore.filter((r) => r.status !== 'expired')
    const deleted = before - reportsStore.length

    return HttpResponse.json({ deleted })
  }),

  // Bulk generate reports
  http.post(`${API_BASE}/reports/bulk`, async ({ request }) => {
    await delay(1500)
    const data = (await request.json()) as {
      validation_ids: string[]
      format?: string
      theme?: string
      locale?: string
      reporter_id?: string
      config?: Record<string, unknown>
      save_to_history?: boolean
      expires_in_days?: number
    }

    const reports: GeneratedReport[] = []
    const errors: Array<{ validation_id: string; error: string }> = []

    for (const validationId of data.validation_ids) {
      // Simulate occasional failures
      if (Math.random() < 0.1) {
        errors.push({
          validation_id: validationId,
          error: 'Validation not found or inaccessible',
        })
        continue
      }

      const report = createGeneratedReport({
        validation_id: validationId,
        format: (data.format as GeneratedReport['format']) || 'html',
        theme: data.theme || 'professional',
        locale: data.locale || 'en',
        reporter_id: data.reporter_id,
        config: data.config,
        status: 'completed',
        file_size: Math.floor(Math.random() * 1000000) + 1024,
        generation_time_ms: Math.random() * 2000 + 100,
      })

      if (data.save_to_history !== false) {
        reportsStore.unshift(report)
      }
      reports.push(report)
    }

    return HttpResponse.json({
      total: data.validation_ids.length,
      successful: reports.length,
      failed: errors.length,
      reports,
      errors,
    })
  }),
]
