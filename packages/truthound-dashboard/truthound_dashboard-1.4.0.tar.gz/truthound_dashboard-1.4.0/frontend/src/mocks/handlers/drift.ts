/**
 * Drift detection API handlers
 *
 * Supports all 8 drift detection methods from truthound:
 * - ks, psi, chi2, js, kl, wasserstein, cvm, anderson
 *
 * Also supports multiple testing correction methods:
 * - none, bonferroni, holm, bh
 */

import { http, HttpResponse, delay } from 'msw'
import { getStore, getAll, getById, create } from '../data/store'
import { createDriftComparison, createId, createTimestamp, faker, randomInt, randomChoice } from '../factories'
import type { DriftMethod, CorrectionMethod } from '@/api/client'

// In-memory store for drift monitors
interface DriftMonitor {
  id: string
  name: string
  baseline_source_id: string
  current_source_id: string
  baseline_source_name?: string
  current_source_name?: string
  cron_expression: string
  method: string
  threshold: number
  status: 'active' | 'paused' | 'error'
  last_run_at: string | null
  last_drift_detected: boolean | null
  total_runs: number
  drift_detected_count: number
  consecutive_drift_count: number
  created_at: string
  updated_at?: string
  // Store the latest run result
  last_run_result?: object
}

interface DriftAlert {
  id: string
  monitor_id: string
  monitor_name: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  status: 'open' | 'acknowledged' | 'resolved' | 'ignored'
  message: string
  drift_percentage: number
  drifted_columns: string[]
  created_at: string
  updated_at?: string
}

// Initialize monitors and alerts store
const monitorsStore = new Map<string, DriftMonitor>()
const alertsStore = new Map<string, DriftAlert>()

const API_BASE = '/api/v1'

export const driftHandlers = [
  // Compare drift between two sources
  http.post(`${API_BASE}/drift/compare`, async ({ request }) => {
    await delay(1500) // Simulate comparison time

    let body: {
      baseline_source_id: string
      current_source_id: string
      columns?: string[]
      method?: DriftMethod
      threshold?: number
      correction?: CorrectionMethod
      sample_size?: number
    }

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const baselineSource = getById(getStore().sources, body.baseline_source_id)
    const currentSource = getById(getStore().sources, body.current_source_id)

    if (!baselineSource) {
      return HttpResponse.json(
        { detail: 'Baseline source not found' },
        { status: 404 }
      )
    }

    if (!currentSource) {
      return HttpResponse.json(
        { detail: 'Current source not found' },
        { status: 404 }
      )
    }

    // Create comparison with all provided options
    const comparison = createDriftComparison({
      id: createId(),
      baselineSourceId: body.baseline_source_id,
      currentSourceId: body.current_source_id,
      method: body.method,
      threshold: body.threshold,
      correction: body.correction,
    })

    create(getStore().driftComparisons, comparison)

    return HttpResponse.json({
      success: true,
      data: comparison,
    })
  }),

  // List drift comparisons
  http.get(`${API_BASE}/drift/comparisons`, async ({ request }) => {
    await delay(200)

    const url = new URL(request.url)
    const baselineSourceId = url.searchParams.get('baseline_source_id')
    const currentSourceId = url.searchParams.get('current_source_id')
    const limit = parseInt(url.searchParams.get('limit') ?? '20')
    const offset = parseInt(url.searchParams.get('offset') ?? '0')

    let comparisons = getAll(getStore().driftComparisons)

    if (baselineSourceId) {
      comparisons = comparisons.filter(
        (c) => c.baseline_source_id === baselineSourceId
      )
    }

    if (currentSourceId) {
      comparisons = comparisons.filter(
        (c) => c.current_source_id === currentSourceId
      )
    }

    // Sort by created_at desc
    comparisons.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )

    const total = comparisons.length
    const paginated = comparisons.slice(offset, offset + limit)

    return HttpResponse.json({
      success: true,
      data: paginated,
      total,
      offset,
      limit,
    })
  }),

  // Get drift comparison by ID
  http.get(`${API_BASE}/drift/comparisons/:id`, async ({ params }) => {
    await delay(150)

    const comparison = getById(getStore().driftComparisons, params.id as string)

    if (!comparison) {
      return HttpResponse.json(
        { detail: 'Drift comparison not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json({
      success: true,
      data: comparison,
    })
  }),

  // Preview drift comparison without saving
  http.post(`${API_BASE}/drift/preview`, async ({ request }) => {
    await delay(1200) // Simulate comparison time

    let body: {
      baseline_source_id: string
      current_source_id: string
      columns?: string[]
      method?: string
      threshold?: number
    }

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const baselineSource = getById(getStore().sources, body.baseline_source_id)
    const currentSource = getById(getStore().sources, body.current_source_id)

    if (!baselineSource) {
      return HttpResponse.json(
        { detail: 'Baseline source not found' },
        { status: 404 }
      )
    }

    if (!currentSource) {
      return HttpResponse.json(
        { detail: 'Current source not found' },
        { status: 404 }
      )
    }

    // Create preview result (not saved)
    const method = body.method || 'auto'
    const threshold = body.threshold || 0.05

    // Generate realistic preview data
    const numColumns = Math.floor(Math.random() * 8) + 5
    const columns = []
    const columnNames = ['age', 'income', 'balance', 'score', 'amount', 'count', 'rate', 'price', 'quantity', 'duration']
    const dtypes = ['int64', 'float64', 'int64', 'float64', 'float64', 'int64', 'float64', 'float64', 'int64', 'float64']
    const levels = ['high', 'medium', 'low', 'none']

    const driftedColumnNames: string[] = []

    for (let i = 0; i < numColumns; i++) {
      const drifted = Math.random() > 0.6
      const level = drifted ? levels[Math.floor(Math.random() * 3)] : 'none'
      const pValue = drifted ? Math.random() * 0.05 : Math.random() * 0.5 + 0.5
      const statistic = Math.random() * 0.5

      const baselineMean = Math.random() * 100 + 50
      const currentMean = baselineMean * (drifted ? (Math.random() * 0.4 + 0.8) : (Math.random() * 0.1 + 0.95))
      const baselineStd = Math.random() * 20 + 10
      const currentStd = baselineStd * (drifted ? (Math.random() * 0.3 + 0.85) : (Math.random() * 0.1 + 0.95))

      const col = {
        column: columnNames[i % columnNames.length],
        dtype: dtypes[i % dtypes.length],
        drifted,
        level,
        method,
        statistic,
        p_value: pValue,
        baseline_stats: {
          mean: baselineMean,
          std: baselineStd,
          min: baselineMean - baselineStd * 2,
          max: baselineMean + baselineStd * 2,
          count: 10000,
          null_count: Math.floor(Math.random() * 100),
        },
        current_stats: {
          mean: currentMean,
          std: currentStd,
          min: currentMean - currentStd * 2,
          max: currentMean + currentStd * 2,
          count: 10200,
          null_count: Math.floor(Math.random() * 100),
        },
        baseline_distribution: null,
        current_distribution: null,
      }

      columns.push(col)

      if (drifted) {
        driftedColumnNames.push(col.column)
      }
    }

    const driftedCount = columns.filter(c => c.drifted).length
    const hasDrift = driftedCount > 0
    const hasHighDrift = columns.some(c => c.level === 'high')
    const driftPercentage = (driftedCount / numColumns) * 100

    const previewData = {
      baseline_source_id: body.baseline_source_id,
      current_source_id: body.current_source_id,
      baseline_source_name: baselineSource.name,
      current_source_name: currentSource.name,
      has_drift: hasDrift,
      has_high_drift: hasHighDrift,
      total_columns: numColumns,
      drifted_columns: driftedCount,
      drift_percentage: Math.round(driftPercentage * 100) / 100,
      baseline_rows: 10000,
      current_rows: 10200,
      method,
      threshold,
      columns,
      most_affected: driftedColumnNames.slice(0, 5),
    }

    return HttpResponse.json({
      success: true,
      data: previewData,
    })
  }),

  // ==========================================
  // Drift Monitor Handlers
  // ==========================================

  // List drift monitors
  http.get(`${API_BASE}/drift/monitors`, async () => {
    await delay(200)

    // Initialize some monitors if empty
    if (monitorsStore.size === 0) {
      const sources = getAll(getStore().sources)
      if (sources.length >= 2) {
        const monitorConfigs = [
          { name: 'Production Data Monitor', status: 'active' as const, hasDrift: true },
          { name: 'Customer Data Monitor', status: 'active' as const, hasDrift: false },
          { name: 'Transaction Monitor', status: 'paused' as const, hasDrift: true },
          { name: 'Weekly Sales Check', status: 'active' as const, hasDrift: false },
        ]

        monitorConfigs.forEach((config, i) => {
          const baselineSource = sources[i % sources.length]
          const currentSource = sources[(i + 1) % sources.length]
          const monitor: DriftMonitor = {
            id: createId(),
            name: config.name,
            baseline_source_id: baselineSource.id,
            current_source_id: currentSource.id,
            baseline_source_name: baselineSource.name,
            current_source_name: currentSource.name,
            cron_expression: i % 2 === 0 ? '0 0 * * *' : '0 */6 * * *',
            method: randomChoice(['auto', 'ks', 'psi', 'chi2']),
            threshold: randomChoice([0.05, 0.1, 0.15]),
            status: config.status,
            last_run_at: config.status === 'active' ? createTimestamp(randomInt(0, 7)) : null,
            last_drift_detected: config.hasDrift,
            total_runs: randomInt(5, 50),
            drift_detected_count: config.hasDrift ? randomInt(1, 10) : 0,
            consecutive_drift_count: config.hasDrift ? randomInt(1, 3) : 0,
            created_at: createTimestamp(randomInt(30, 90)),
            updated_at: createTimestamp(randomInt(0, 7)),
          }
          monitorsStore.set(monitor.id, monitor)
        })
      }
    }

    const monitors = Array.from(monitorsStore.values())

    return HttpResponse.json({
      data: monitors,
      total: monitors.length,
    })
  }),

  // Get monitors summary
  http.get(`${API_BASE}/drift/monitors/summary`, async () => {
    await delay(100)

    const monitors = Array.from(monitorsStore.values())
    const alerts = Array.from(alertsStore.values())

    const summary = {
      total_monitors: monitors.length,
      active_monitors: monitors.filter(m => m.status === 'active').length,
      paused_monitors: monitors.filter(m => m.status === 'paused').length,
      monitors_with_drift: monitors.filter(m => m.last_drift_detected).length,
      total_open_alerts: alerts.filter(a => a.status === 'open').length,
      critical_alerts: alerts.filter(a => a.severity === 'critical' && a.status === 'open').length,
      high_alerts: alerts.filter(a => a.severity === 'high' && a.status === 'open').length,
    }

    return HttpResponse.json({
      success: true,
      data: summary,
    })
  }),

  // Create drift monitor
  http.post(`${API_BASE}/drift/monitors`, async ({ request }) => {
    await delay(300)

    const body = await request.json() as Partial<DriftMonitor>
    const sources = getAll(getStore().sources)
    const baselineSource = sources.find(s => s.id === body.baseline_source_id)
    const currentSource = sources.find(s => s.id === body.current_source_id)

    const monitor: DriftMonitor = {
      id: createId(),
      name: body.name || 'New Monitor',
      baseline_source_id: body.baseline_source_id || '',
      current_source_id: body.current_source_id || '',
      baseline_source_name: baselineSource?.name,
      current_source_name: currentSource?.name,
      cron_expression: body.cron_expression || '0 0 * * *',
      method: body.method || 'auto',
      threshold: body.threshold || 0.05,
      status: 'active',
      last_run_at: null,
      last_drift_detected: null,
      total_runs: 0,
      drift_detected_count: 0,
      consecutive_drift_count: 0,
      created_at: new Date().toISOString(),
    }

    monitorsStore.set(monitor.id, monitor)

    return HttpResponse.json({
      success: true,
      data: monitor,
    })
  }),

  // Update drift monitor
  http.put(`${API_BASE}/drift/monitors/:id`, async ({ params, request }) => {
    await delay(200)

    const monitor = monitorsStore.get(params.id as string)
    if (!monitor) {
      return HttpResponse.json({ detail: 'Monitor not found' }, { status: 404 })
    }

    const body = await request.json() as Partial<DriftMonitor>
    const updatedMonitor = {
      ...monitor,
      ...body,
      updated_at: new Date().toISOString(),
    }

    monitorsStore.set(monitor.id, updatedMonitor)

    return HttpResponse.json({
      success: true,
      data: updatedMonitor,
    })
  }),

  // Delete drift monitor
  http.delete(`${API_BASE}/drift/monitors/:id`, async ({ params }) => {
    await delay(200)

    const monitor = monitorsStore.get(params.id as string)
    if (!monitor) {
      return HttpResponse.json({ detail: 'Monitor not found' }, { status: 404 })
    }

    monitorsStore.delete(params.id as string)

    return HttpResponse.json({
      success: true,
    })
  }),

  // Run drift monitor
  http.post(`${API_BASE}/drift/monitors/:id/run`, async ({ params }) => {
    await delay(1500) // Simulate drift detection time

    const monitor = monitorsStore.get(params.id as string)
    if (!monitor) {
      return HttpResponse.json({ detail: 'Monitor not found' }, { status: 404 })
    }

    // Generate drift result
    const hasDrift = faker.datatype.boolean(0.4)
    const driftPercentage = hasDrift ? faker.number.float({ min: 5, max: 60, fractionDigits: 1 }) : faker.number.float({ min: 0, max: 4, fractionDigits: 1 })

    // Generate detailed column results
    const numColumns = randomInt(8, 20)
    const driftedCount = hasDrift ? randomInt(1, Math.ceil(numColumns * 0.5)) : 0
    const columns = generateColumnResults(numColumns, driftedCount)

    const runResult = {
      baseline_source: monitor.baseline_source_id,
      current_source: monitor.current_source_id,
      baseline_rows: randomInt(10000, 100000),
      current_rows: randomInt(10000, 100000),
      has_drift: hasDrift,
      has_high_drift: columns.some(c => c.level === 'high'),
      total_columns: numColumns,
      drifted_columns: columns.filter(c => c.drifted).map(c => c.column),
      columns,
    }

    // Update monitor
    const updatedMonitor = {
      ...monitor,
      last_run_at: new Date().toISOString(),
      last_drift_detected: hasDrift,
      total_runs: monitor.total_runs + 1,
      drift_detected_count: monitor.drift_detected_count + (hasDrift ? 1 : 0),
      consecutive_drift_count: hasDrift ? monitor.consecutive_drift_count + 1 : 0,
      last_run_result: runResult,
      updated_at: new Date().toISOString(),
    }
    monitorsStore.set(monitor.id, updatedMonitor)

    // Create alert if drift detected
    if (hasDrift && driftPercentage > 20) {
      const alert: DriftAlert = {
        id: createId(),
        monitor_id: monitor.id,
        monitor_name: monitor.name,
        severity: driftPercentage > 40 ? 'critical' : driftPercentage > 30 ? 'high' : 'medium',
        status: 'open',
        message: `${driftPercentage.toFixed(1)}% drift detected in ${driftedCount} columns`,
        drift_percentage: driftPercentage,
        drifted_columns: runResult.drifted_columns,
        created_at: new Date().toISOString(),
      }
      alertsStore.set(alert.id, alert)
    }

    return HttpResponse.json({
      success: true,
      data: {
        has_drift: hasDrift,
        drift_percentage: driftPercentage,
      },
    })
  }),

  // Get latest run result for a monitor
  http.get(`${API_BASE}/drift/monitors/:id/latest-run`, async ({ params }) => {
    await delay(200)

    const monitor = monitorsStore.get(params.id as string)
    if (!monitor) {
      return HttpResponse.json({ detail: 'Monitor not found' }, { status: 404 })
    }

    // If no run result, generate one
    if (!monitor.last_run_result) {
      const numColumns = randomInt(8, 20)
      const hasDrift = monitor.last_drift_detected ?? false
      const driftedCount = hasDrift ? randomInt(1, Math.ceil(numColumns * 0.5)) : randomInt(0, 2)
      const columns = generateColumnResults(numColumns, driftedCount)

      // Generate a comparison_id for root cause analysis
      const comparisonId = createId()

      const runResult = {
        comparison_id: comparisonId,
        baseline_source: monitor.baseline_source_id,
        current_source: monitor.current_source_id,
        baseline_rows: randomInt(10000, 100000),
        current_rows: randomInt(10000, 100000),
        has_drift: hasDrift,
        has_high_drift: columns.some(c => c.level === 'high'),
        total_columns: numColumns,
        drifted_columns: columns.filter(c => c.drifted).map(c => c.column),
        columns,
      }

      // Also store it in the driftComparisons store for root cause analysis
      const comparison = {
        id: comparisonId,
        baseline_source_id: monitor.baseline_source_id,
        current_source_id: monitor.current_source_id,
        has_drift: hasDrift,
        has_high_drift: runResult.has_high_drift,
        total_columns: numColumns,
        drifted_columns: driftedCount,
        drift_percentage: driftedCount > 0 ? (driftedCount / numColumns) * 100 : 0,
        result: runResult,
        created_at: new Date().toISOString(),
      }
      create(getStore().driftComparisons, comparison)

      monitor.last_run_result = runResult
      monitorsStore.set(monitor.id, monitor)
    }

    return HttpResponse.json({
      success: true,
      data: monitor.last_run_result,
    })
  }),

  // Get monitor trend data
  http.get(`${API_BASE}/drift/monitors/:id/trend`, async ({ params, request }) => {
    await delay(200)

    const url = new URL(request.url)
    const days = parseInt(url.searchParams.get('days') ?? '30')

    const monitor = monitorsStore.get(params.id as string)
    if (!monitor) {
      return HttpResponse.json({ detail: 'Monitor not found' }, { status: 404 })
    }

    // Generate trend data points
    const dataPoints = []
    const now = new Date()
    let cumulativeDrift = 0
    let maxDrift = 0
    let driftCount = 0

    for (let i = days; i >= 0; i--) {
      const date = new Date(now)
      date.setDate(date.getDate() - i)

      const hasDrift = faker.datatype.boolean(0.3)
      const driftPercentage = hasDrift
        ? faker.number.float({ min: 5, max: 40, fractionDigits: 1 })
        : faker.number.float({ min: 0, max: 4, fractionDigits: 1 })

      dataPoints.push({
        timestamp: date.toISOString(),
        drift_percentage: driftPercentage,
        drifted_columns: hasDrift ? randomInt(1, 8) : 0,
        total_columns: 15,
        has_drift: hasDrift,
      })

      cumulativeDrift += driftPercentage
      maxDrift = Math.max(maxDrift, driftPercentage)
      if (hasDrift) driftCount++
    }

    return HttpResponse.json({
      success: true,
      data: {
        monitor_id: monitor.id,
        period_start: dataPoints[0]?.timestamp,
        period_end: dataPoints[dataPoints.length - 1]?.timestamp,
        data_points: dataPoints,
        avg_drift_percentage: cumulativeDrift / dataPoints.length,
        max_drift_percentage: maxDrift,
        drift_occurrence_rate: driftCount / dataPoints.length,
      },
    })
  }),

  // ==========================================
  // Drift Alert Handlers
  // ==========================================

  // List drift alerts
  http.get(`${API_BASE}/drift/alerts`, async ({ request }) => {
    await delay(200)

    const url = new URL(request.url)
    const status = url.searchParams.get('status')
    const severity = url.searchParams.get('severity')

    // Initialize some alerts if empty
    if (alertsStore.size === 0) {
      const monitors = Array.from(monitorsStore.values())
      monitors.forEach((monitor, i) => {
        if (monitor.last_drift_detected && i < 3) {
          const alert: DriftAlert = {
            id: createId(),
            monitor_id: monitor.id,
            monitor_name: monitor.name,
            severity: randomChoice(['critical', 'high', 'medium', 'low']),
            status: 'open',
            message: `Drift detected: ${randomInt(10, 40)}% change in data distribution`,
            drift_percentage: faker.number.float({ min: 10, max: 40, fractionDigits: 1 }),
            drifted_columns: ['revenue', 'user_count', 'transaction_amount'].slice(0, randomInt(1, 3)),
            created_at: createTimestamp(randomInt(0, 7)),
          }
          alertsStore.set(alert.id, alert)
        }
      })
    }

    let alerts = Array.from(alertsStore.values())

    if (status) {
      alerts = alerts.filter(a => a.status === status)
    }
    if (severity) {
      alerts = alerts.filter(a => a.severity === severity)
    }

    // Sort by created_at desc
    alerts.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

    return HttpResponse.json({
      data: alerts,
      total: alerts.length,
    })
  }),

  // Update drift alert
  http.put(`${API_BASE}/drift/alerts/:id`, async ({ params, request }) => {
    await delay(200)

    const alert = alertsStore.get(params.id as string)
    if (!alert) {
      return HttpResponse.json({ detail: 'Alert not found' }, { status: 404 })
    }

    const body = await request.json() as Partial<DriftAlert>
    const updatedAlert = {
      ...alert,
      ...body,
      updated_at: new Date().toISOString(),
    }

    alertsStore.set(alert.id, updatedAlert)

    return HttpResponse.json({
      success: true,
      data: updatedAlert,
    })
  }),

  // ==========================================
  // Root Cause Analysis Handlers
  // ==========================================

  // Get root cause analysis for a drift comparison
  http.get(`${API_BASE}/drift/comparisons/:runId/root-cause`, async ({ params }) => {
    await delay(800) // Simulate analysis time

    const runId = params.runId as string
    const comparison = getById(getStore().driftComparisons, runId)

    if (!comparison) {
      return HttpResponse.json(
        { detail: 'Drift comparison not found' },
        { status: 404 }
      )
    }

    // Generate root cause analysis based on the comparison
    const analysis = generateRootCauseAnalysis(runId, comparison)

    return HttpResponse.json({
      success: true,
      data: analysis,
    })
  }),

  // Get root cause analysis for a monitor run
  http.get(`${API_BASE}/drift/monitors/:monitorId/runs/:runId/root-cause`, async ({ params }) => {
    await delay(800) // Simulate analysis time

    const runId = params.runId as string
    const monitorId = params.monitorId as string
    const comparison = getById(getStore().driftComparisons, runId)

    if (!comparison) {
      return HttpResponse.json(
        { detail: 'Drift run not found' },
        { status: 404 }
      )
    }

    // Generate root cause analysis based on the comparison
    const analysis = generateRootCauseAnalysis(runId, comparison, monitorId)

    return HttpResponse.json({
      success: true,
      data: analysis,
    })
  }),

  // ==========================================
  // Large-Scale Dataset Optimization Handlers
  // ==========================================

  // Estimate sample size for comparison
  http.get(`${API_BASE}/drift/estimate-sample-size`, async ({ request }) => {
    await delay(300)

    const url = new URL(request.url)
    const baselineSourceId = url.searchParams.get('baseline_source_id')
    const currentSourceId = url.searchParams.get('current_source_id')
    const confidenceLevel = parseFloat(url.searchParams.get('confidence_level') ?? '0.95')
    const marginOfError = parseFloat(url.searchParams.get('margin_of_error') ?? '0.03')

    if (!baselineSourceId || !currentSourceId) {
      return HttpResponse.json(
        { detail: 'baseline_source_id and current_source_id are required' },
        { status: 400 }
      )
    }

    const baselineSource = getById(getStore().sources, baselineSourceId)
    const currentSource = getById(getStore().sources, currentSourceId)

    if (!baselineSource || !currentSource) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    // Simulate large dataset sizes
    const baselineRows = randomInt(50_000_000, 200_000_000)
    const currentRows = randomInt(50_000_000, 200_000_000)
    const populationSize = Math.max(baselineRows, currentRows)
    const isLargeDataset = populationSize >= 10_000_000

    // Calculate recommended sample size (Cochran's formula simplified)
    const z = confidenceLevel === 0.99 ? 2.576 : confidenceLevel === 0.95 ? 1.96 : 1.645
    const p = 0.1 // expected drift rate
    const n0 = (z ** 2 * p * (1 - p)) / (marginOfError ** 2)
    const recommendedSize = Math.ceil(n0 / (1 + (n0 - 1) / populationSize))
    const minSize = Math.max(100, Math.floor(recommendedSize * 0.3))
    const maxSize = Math.min(populationSize, recommendedSize * 3)

    // Estimate processing time and memory
    const numColumns = 15
    const estimatedTimeSeconds = (recommendedSize * numColumns) / 10000
    const memoryMb = (recommendedSize * 100 * numColumns) / (1024 * 1024)

    // Speedup options
    const speedupOptions = {
      minimal: {
        sample_size: Math.floor(recommendedSize * 0.5),
        speedup_factor: Math.round(populationSize / (recommendedSize * 0.5)),
        estimated_time_seconds: Math.round(estimatedTimeSeconds * 0.5 * 100) / 100,
      },
      recommended: {
        sample_size: recommendedSize,
        speedup_factor: Math.round(populationSize / recommendedSize),
        estimated_time_seconds: Math.round(estimatedTimeSeconds * 100) / 100,
      },
      thorough: {
        sample_size: Math.floor(recommendedSize * 2),
        speedup_factor: Math.round(populationSize / (recommendedSize * 2)),
        estimated_time_seconds: Math.round(estimatedTimeSeconds * 2 * 100) / 100,
      },
    }

    return HttpResponse.json({
      success: true,
      data: {
        baseline_source_id: baselineSourceId,
        current_source_id: currentSourceId,
        dataset_info: {
          baseline_rows: baselineRows,
          current_rows: currentRows,
          population_size: populationSize,
          is_large_dataset: isLargeDataset,
          large_dataset_threshold: 10_000_000,
        },
        sampling_recommendation: {
          sampling_recommended: isLargeDataset,
          reason: isLargeDataset
            ? `Dataset has ${populationSize.toLocaleString()} rows, exceeding the 10,000,000 row threshold`
            : `Dataset has ${populationSize.toLocaleString()} rows, within manageable size`,
        },
        sample_size_estimate: {
          recommended_size: recommendedSize,
          min_size: minSize,
          max_size: maxSize,
          confidence_level: confidenceLevel,
          margin_of_error: marginOfError,
          estimated_time_seconds: Math.round(estimatedTimeSeconds * 100) / 100,
          memory_mb: Math.round(memoryMb * 100) / 100,
        },
        performance_estimates: {
          estimated_time_seconds: Math.round(estimatedTimeSeconds * 100) / 100,
          estimated_memory_mb: Math.round(memoryMb * 100) / 100,
          speedup_options: speedupOptions,
        },
        available_methods: [
          {
            method: 'random',
            description: 'Simple random sampling without replacement',
            best_for: 'General-purpose sampling when no stratification needed',
          },
          {
            method: 'stratified',
            description: 'Sampling that maintains proportions of categories',
            best_for: 'Ensuring representation of all categories',
          },
          {
            method: 'reservoir',
            description: 'Single-pass sampling for streaming data',
            best_for: 'Very large datasets or streaming sources',
          },
          {
            method: 'systematic',
            description: 'Evenly spaced sampling with random start',
            best_for: 'Ordered data where even distribution matters',
          },
        ],
      },
    })
  }),

  // Run sampled comparison
  http.post(`${API_BASE}/drift/monitors/:id/run-sampled`, async ({ params, request }) => {
    const url = new URL(request.url)
    const sampleSize = url.searchParams.get('sample_size')
      ? parseInt(url.searchParams.get('sample_size')!)
      : null
    const samplingMethod = url.searchParams.get('sampling_method') ?? 'random'
    const confidenceLevel = parseFloat(url.searchParams.get('confidence_level') ?? '0.95')
    const earlyStopThreshold = parseFloat(url.searchParams.get('early_stop_threshold') ?? '0.5')
    const maxWorkers = parseInt(url.searchParams.get('max_workers') ?? '4')

    const monitor = monitorsStore.get(params.id as string)
    if (!monitor) {
      return HttpResponse.json({ detail: 'Monitor not found' }, { status: 404 })
    }

    // Simulate large dataset processing with chunked progress
    const jobId = createId()
    const populationBaseline = randomInt(50_000_000, 200_000_000)
    const populationCurrent = randomInt(50_000_000, 200_000_000)
    const actualSampleSize = sampleSize ?? Math.min(100000, Math.ceil(Math.max(populationBaseline, populationCurrent) * 0.001))
    const numColumns = 15
    const chunkSize = 10000
    const totalChunks = Math.ceil(actualSampleSize / chunkSize)

    // Simulate processing delay (proportional to sample size but much faster than full scan)
    const processingTime = Math.min(3000, actualSampleSize / 50)
    await delay(processingTime)

    // Generate results
    const hasDrift = faker.datatype.boolean(0.4)
    const driftedColumnCount = hasDrift ? randomInt(2, 8) : randomInt(0, 1)
    const driftedColumns = generateColumnResults(numColumns, driftedColumnCount)
      .filter(c => c.drifted)
      .map(c => c.column)

    const earlyStopped = hasDrift && driftedColumnCount > numColumns * earlyStopThreshold
    const processedChunks = earlyStopped ? Math.floor(totalChunks * 0.6) : totalChunks
    void Math.min(actualSampleSize, processedChunks * chunkSize) // processedRows for future use

    // Generate chunk details
    const chunkDetails = []
    for (let i = 0; i < processedChunks; i++) {
      const rowsInChunk = Math.min(chunkSize, actualSampleSize - i * chunkSize)
      chunkDetails.push({
        chunk_index: i,
        rows_processed: rowsInChunk,
        drifted_columns: i < 3 ? driftedColumns.slice(0, Math.min(i + 1, driftedColumns.length)) : driftedColumns,
        processing_time_seconds: faker.number.float({ min: 0.5, max: 2, fractionDigits: 2 }),
      })
    }

    const totalTime = chunkDetails.reduce((sum, c) => sum + c.processing_time_seconds, 0)
    const estimatedTime = (actualSampleSize * numColumns) / 10000
    const speedupFactor = Math.max(populationBaseline, populationCurrent) / actualSampleSize

    // Update monitor
    monitor.last_run_at = new Date().toISOString()
    monitor.total_runs += 1
    monitor.last_drift_detected = hasDrift
    if (hasDrift) {
      monitor.drift_detected_count += 1
      monitor.consecutive_drift_count += 1
    } else {
      monitor.consecutive_drift_count = 0
    }
    monitorsStore.set(monitor.id, monitor)

    return HttpResponse.json({
      success: true,
      data: {
        job_id: jobId,
        monitor_id: monitor.id,
        status: 'completed',
        sampling: {
          method: samplingMethod,
          sample_size: actualSampleSize,
          confidence_level: confidenceLevel,
          population_baseline: populationBaseline,
          population_current: populationCurrent,
        },
        processing: {
          num_chunks: processedChunks,
          total_chunks_planned: totalChunks,
          early_stopped: earlyStopped,
          parallel_workers: maxWorkers,
        },
        results: {
          has_drift: hasDrift,
          total_columns: numColumns,
          drifted_columns: driftedColumnCount,
          drifted_column_names: driftedColumns,
          drift_percentage: Math.round((driftedColumnCount / numColumns) * 10000) / 100,
        },
        performance: {
          total_time_seconds: Math.round(totalTime * 100) / 100,
          estimated_time_seconds: Math.round(estimatedTime * 100) / 100,
          estimated_memory_mb: Math.round((actualSampleSize * 100 * numColumns) / (1024 * 1024) * 100) / 100,
          speedup_factor: Math.round(speedupFactor * 10) / 10,
        },
        chunk_details: chunkDetails,
      },
    })
  }),

  // Get job progress (for active jobs)
  http.get(`${API_BASE}/drift/jobs/:jobId/progress`, async ({ params }) => {
    await delay(100)

    // Simulate an in-progress job
    const jobId = params.jobId as string

    // Return a mock progress response
    const totalChunks = 10
    const processedChunks = randomInt(3, 8)
    const totalRows = 100000
    const processedRows = processedChunks * 10000

    return HttpResponse.json({
      success: true,
      data: {
        job_id: jobId,
        status: processedChunks === totalChunks ? 'completed' : 'running',
        progress: {
          total_chunks: totalChunks,
          processed_chunks: processedChunks,
          total_rows: totalRows,
          processed_rows: processedRows,
          percentage: Math.round((processedRows / totalRows) * 100 * 10) / 10,
        },
        timing: {
          elapsed_seconds: processedChunks * 1.5,
          estimated_remaining_seconds: (totalChunks - processedChunks) * 1.5,
        },
        interim_results: {
          columns_with_drift: ['revenue', 'user_count', 'conversion_rate'].slice(0, randomInt(0, 3)),
          early_stop_triggered: false,
        },
      },
    })
  }),

  // Cancel job
  http.post(`${API_BASE}/drift/jobs/:jobId/cancel`, async () => {
    await delay(100)

    return HttpResponse.json({
      success: true,
      message: 'Job cancelled',
    })
  }),
]

// Helper function to generate root cause analysis
function generateRootCauseAnalysis(
  runId: string,
  comparison: ReturnType<typeof getById<ReturnType<typeof getStore>['driftComparisons'] extends Map<string, infer T> ? T : never>>,
  monitorId?: string
) {
  if (!comparison) return null

  const columns = comparison.result?.columns ?? []
  const columnAnalyses = columns.map((col: {
    column: string
    dtype?: string
    level?: string
    drifted?: boolean
    baseline_stats?: Record<string, unknown>
    current_stats?: Record<string, unknown>
  }) => {
    const causes: string[] = []
    let primaryCause: string | null = null
    let confidence = 0.5

    const baselineStats = col.baseline_stats ?? {}
    const currentStats = col.current_stats ?? {}
    const baselineMean = baselineStats.mean as number | undefined
    const currentMean = currentStats.mean as number | undefined

    // Analyze mean shift
    let meanShift = null
    if (baselineMean !== undefined && currentMean !== undefined && baselineMean !== 0) {
      const pctChange = Math.abs(currentMean - baselineMean) / Math.abs(baselineMean) * 100
      meanShift = {
        baseline_value: baselineMean,
        current_value: currentMean,
        absolute_change: currentMean - baselineMean,
        percent_change: pctChange,
      }
      if (pctChange > 10) {
        causes.push('mean_shift')
        if (pctChange > 20) {
          primaryCause = 'mean_shift'
          confidence = Math.min(0.9, pctChange / 100 + 0.5)
        }
      }
    }

    // Analyze variance change
    let stdShift = null
    const baselineStd = baselineStats.std as number | undefined
    const currentStd = currentStats.std as number | undefined
    if (baselineStd !== undefined && currentStd !== undefined && baselineStd !== 0) {
      const pctChange = Math.abs(currentStd - baselineStd) / Math.abs(baselineStd) * 100
      stdShift = {
        baseline_value: baselineStd,
        current_value: currentStd,
        absolute_change: currentStd - baselineStd,
        percent_change: pctChange,
      }
      if (pctChange > 20) {
        causes.push('variance_change')
        if (pctChange > 40 && !primaryCause) {
          primaryCause = 'variance_change'
          confidence = Math.max(confidence, Math.min(0.85, pctChange / 100 + 0.4))
        }
      }
    }

    // Analyze min/max for outliers
    let minShift = null
    let maxShift = null
    const baselineMin = baselineStats.min as number | undefined
    const currentMin = currentStats.min as number | undefined
    const baselineMax = baselineStats.max as number | undefined
    const currentMax = currentStats.max as number | undefined
    if (baselineMin !== undefined && currentMin !== undefined) {
      const pctChange = baselineMin !== 0
        ? Math.abs(currentMin - baselineMin) / Math.abs(baselineMin) * 100
        : Math.abs(currentMin - baselineMin) * 100
      minShift = {
        baseline_value: baselineMin,
        current_value: currentMin,
        absolute_change: currentMin - baselineMin,
        percent_change: pctChange,
      }
    }
    if (baselineMax !== undefined && currentMax !== undefined) {
      const pctChange = baselineMax !== 0
        ? Math.abs(currentMax - baselineMax) / Math.abs(baselineMax) * 100
        : Math.abs(currentMax - baselineMax) * 100
      maxShift = {
        baseline_value: baselineMax,
        current_value: currentMax,
        absolute_change: currentMax - baselineMax,
        percent_change: pctChange,
      }
      if (pctChange > 50 || (minShift && minShift.percent_change > 50)) {
        causes.push('outlier_introduction')
        if (!primaryCause) {
          primaryCause = 'outlier_introduction'
          confidence = Math.max(confidence, 0.75)
        }
      }
    }

    // If drifted but no clear cause
    if (col.drifted && causes.length === 0) {
      causes.push('distribution_shape_change')
      if (!primaryCause) {
        primaryCause = 'distribution_shape_change'
        confidence = 0.6
      }
    }

    return {
      column: col.column,
      dtype: col.dtype ?? 'unknown',
      drift_level: col.level ?? 'none',
      causes,
      primary_cause: primaryCause,
      confidence,
      mean_shift: meanShift,
      std_shift: stdShift,
      min_shift: minShift,
      max_shift: maxShift,
      new_categories: [],
      missing_categories: [],
      category_distribution_changes: [],
      outlier_info: null,
      temporal_patterns: [],
      null_rate_baseline: (baselineStats.null_count as number | undefined) && (baselineStats.count as number | undefined)
        ? (baselineStats.null_count as number) / (baselineStats.count as number)
        : null,
      null_rate_current: (currentStats.null_count as number | undefined) && (currentStats.count as number | undefined)
        ? (currentStats.null_count as number) / (currentStats.count as number)
        : null,
    }
  })

  // Aggregate causes
  const causeDistribution: Record<string, number> = {}
  const primaryCauses: string[] = []
  columnAnalyses.forEach((col: { causes: string[]; primary_cause: string | null }) => {
    col.causes.forEach((cause: string) => {
      causeDistribution[cause] = (causeDistribution[cause] ?? 0) + 1
    })
    if (col.primary_cause && !primaryCauses.includes(col.primary_cause)) {
      primaryCauses.push(col.primary_cause)
    }
  })

  // Generate remediations
  const remediations = generateRemediations(columnAnalyses, causeDistribution)

  // Calculate overall confidence
  const confidences = columnAnalyses.map((c: { confidence: number }) => c.confidence).filter(Boolean)
  const overallConfidence = confidences.length > 0
    ? confidences.reduce((a: number, b: number) => a + b, 0) / confidences.length
    : 0.7

  return {
    run_id: runId,
    monitor_id: monitorId ?? null,
    analyzed_at: new Date().toISOString(),
    total_columns: comparison.total_columns ?? columnAnalyses.length,
    drifted_columns: comparison.drifted_columns ?? 0,
    drift_percentage: comparison.drift_percentage ?? 0,
    data_volume_change: comparison.result?.baseline_rows && comparison.result?.current_rows
      ? {
          baseline_rows: comparison.result.baseline_rows,
          current_rows: comparison.result.current_rows,
          absolute_change: comparison.result.current_rows - comparison.result.baseline_rows,
          percent_change: comparison.result.baseline_rows > 0
            ? ((comparison.result.current_rows - comparison.result.baseline_rows) / comparison.result.baseline_rows) * 100
            : 0,
          significance: getVolumeSignificance(
            comparison.result.baseline_rows,
            comparison.result.current_rows
          ),
        }
      : null,
    column_analyses: columnAnalyses,
    primary_causes: primaryCauses,
    cause_distribution: causeDistribution,
    remediations,
    overall_confidence: overallConfidence,
    analysis_duration_ms: Math.floor(Math.random() * 500) + 200,
  }
}

function getVolumeSignificance(baseline: number, current: number): string {
  const pctChange = Math.abs((current - baseline) / baseline) * 100
  if (pctChange < 5) return 'normal'
  if (pctChange < 15) return 'notable'
  if (pctChange < 30) return 'significant'
  return 'critical'
}

function generateRemediations(
  columnAnalyses: Array<{ column: string; causes: string[]; primary_cause: string | null }>,
  causeDistribution: Record<string, number>
) {
  const remediations: Array<{
    action: string
    priority: number
    title: string
    description: string
    affected_columns: string[]
    estimated_impact: string
    requires_manual_review: boolean
    automation_available: boolean
  }> = []

  let priority = 1

  // Mean shift remediations
  if (causeDistribution['mean_shift']) {
    const affected = columnAnalyses
      .filter((c) => c.causes.includes('mean_shift'))
      .map((c) => c.column)
    remediations.push({
      action: 'investigate_upstream',
      priority: priority++,
      title: 'Investigate Upstream Data Changes',
      description: `Significant mean shifts detected in ${affected.length} column(s). Check upstream data sources for changes in data collection, processing logic, or business rule modifications.`,
      affected_columns: affected,
      estimated_impact: 'high',
      requires_manual_review: true,
      automation_available: false,
    })
  }

  // Variance change remediations
  if (causeDistribution['variance_change']) {
    const affected = columnAnalyses
      .filter((c) => c.causes.includes('variance_change'))
      .map((c) => c.column)
    remediations.push({
      action: 'review_data_pipeline',
      priority: priority++,
      title: 'Review Data Pipeline for Variance Issues',
      description: `Variance changes detected in ${affected.length} column(s). This could indicate issues with data normalization, changes in data sources, or outlier introduction.`,
      affected_columns: affected,
      estimated_impact: 'medium',
      requires_manual_review: true,
      automation_available: false,
    })
  }

  // Outlier remediations
  if (causeDistribution['outlier_introduction']) {
    const affected = columnAnalyses
      .filter((c) => c.causes.includes('outlier_introduction'))
      .map((c) => c.column)
    remediations.push({
      action: 'filter_outliers',
      priority: priority++,
      title: 'Review and Filter Outliers',
      description: `New outliers detected in ${affected.length} column(s). Consider implementing outlier detection and filtering, or investigate if outliers represent valid data changes.`,
      affected_columns: affected,
      estimated_impact: 'medium',
      requires_manual_review: true,
      automation_available: true,
    })
  }

  // Update baseline suggestion
  if (Object.keys(causeDistribution).length > 0) {
    const totalDrifted = columnAnalyses.filter((c) => c.causes.length > 0).length
    remediations.push({
      action: 'update_baseline',
      priority: Math.min(priority + 1, 5),
      title: 'Consider Updating Baseline',
      description: `If the drift in ${totalDrifted} column(s) represents expected business changes, consider updating the baseline dataset to reflect the new data distribution.`,
      affected_columns: columnAnalyses.filter((c) => c.causes.length > 0).map((c) => c.column),
      estimated_impact: 'medium',
      requires_manual_review: true,
      automation_available: true,
    })
  }

  return remediations
}

// Helper function to generate column drift results
function generateColumnResults(totalColumns: number, driftedCount: number) {
  const columnNames = [
    'revenue', 'user_count', 'transaction_amount', 'session_duration',
    'conversion_rate', 'bounce_rate', 'avg_order_value', 'customer_ltv',
    'churn_rate', 'engagement_score', 'page_views', 'click_rate',
    'retention_rate', 'nps_score', 'response_time', 'error_rate',
    'stock_level', 'turnover_rate', 'gross_margin', 'operating_income'
  ]

  const dtypes = ['float64', 'int64', 'float64', 'float64', 'float64', 'float64']
  const methods = ['ks', 'psi', 'chi2', 'js', 'wasserstein']
  const columns = []

  for (let i = 0; i < totalColumns; i++) {
    const isDrifted = i < driftedCount
    const level = isDrifted
      ? (i === 0 ? 'high' : i < driftedCount / 2 ? 'medium' : 'low')
      : 'none'

    const baselineMean = faker.number.float({ min: 10, max: 1000, fractionDigits: 2 })
    const baselineStd = faker.number.float({ min: 1, max: baselineMean * 0.3, fractionDigits: 2 })

    const driftMultiplier = level === 'high' ? 0.5 : level === 'medium' ? 0.25 : level === 'low' ? 0.1 : 0
    const currentMean = baselineMean * (1 + (faker.datatype.boolean() ? driftMultiplier : -driftMultiplier))
    const currentStd = baselineStd * (1 + faker.number.float({ min: -0.2, max: 0.3 }))

    const pValue = isDrifted
      ? faker.number.float({ min: 0.0001, max: 0.04, fractionDigits: 4 })
      : faker.number.float({ min: 0.06, max: 0.99, fractionDigits: 4 })

    columns.push({
      column: columnNames[i % columnNames.length],
      dtype: dtypes[i % dtypes.length],
      drifted: isDrifted,
      level,
      method: randomChoice(methods),
      statistic: faker.number.float({ min: 0, max: 1, fractionDigits: 4 }),
      p_value: pValue,
      baseline_stats: {
        mean: baselineMean,
        std: baselineStd,
        median: baselineMean * (1 + faker.number.float({ min: -0.1, max: 0.1 })),
        min: baselineMean - baselineStd * 2,
        max: baselineMean + baselineStd * 2,
        q25: baselineMean - baselineStd * 0.67,
        q75: baselineMean + baselineStd * 0.67,
        count: randomInt(10000, 1000000),
        null_count: randomInt(0, 100),
        unique_count: randomInt(100, 10000),
      },
      current_stats: {
        mean: currentMean,
        std: currentStd,
        median: currentMean * (1 + faker.number.float({ min: -0.1, max: 0.1 })),
        min: currentMean - currentStd * 2,
        max: currentMean + currentStd * 2,
        q25: currentMean - currentStd * 0.67,
        q75: currentMean + currentStd * 0.67,
        count: randomInt(10000, 1000000),
        null_count: randomInt(0, 100),
        unique_count: randomInt(100, 10000),
      },
    })
  }

  return columns
}
