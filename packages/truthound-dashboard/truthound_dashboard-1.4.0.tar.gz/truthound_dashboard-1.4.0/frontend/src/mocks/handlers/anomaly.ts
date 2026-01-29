/**
 * Anomaly detection API handlers
 *
 * Handles all anomaly detection endpoints:
 * - Run detection
 * - Get detection results
 * - List detections for a source
 * - Get latest detection
 * - List available algorithms
 * - Batch detection (create, status, results, cancel, delete)
 */

import { http, HttpResponse, delay } from 'msw'
import { getStore, getById } from '../data/store'
import {
  createAnomalyDetection,
  createAlgorithmInfo,
  getAnomalyDetectionsForSource,
  addAnomalyDetectionToStore,
  getAnomalyDetectionById,
  createId,
  randomInt,
  faker,
} from '../factories'
import type {
  AnomalyAlgorithm,
  BatchDetectionJob,
  BatchSourceResult,
  AlgorithmComparisonResult,
  AlgorithmComparisonResultItem,
  AgreementSummary,
  AgreementRecord,
  AgreementLevel,
  StreamingSession,
  StreamingAlgorithm,
  StreamingAlert,
  StreamingStatistics,
  StreamingAlgorithmInfo,
} from '@/api/client'

const API_BASE = '/api/v1'

export const anomalyHandlers = [
  // Run anomaly detection on a source
  http.post(`${API_BASE}/sources/:sourceId/anomaly/detect`, async ({ params, request }) => {
    await delay(2000) // Simulate detection time

    const sourceId = params.sourceId as string

    // Verify source exists
    const source = getById(getStore().sources, sourceId)
    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    let body: {
      algorithm?: AnomalyAlgorithm
      columns?: string[]
      config?: Record<string, unknown>
      sample_size?: number
    } = {}

    try {
      body = await request.json() as typeof body
    } catch {
      // Empty body is OK, will use defaults
    }

    // Create a new detection
    const detection = createAnomalyDetection({
      id: createId(),
      source_id: sourceId,
      status: 'success',
      algorithm: body.algorithm ?? 'isolation_forest',
      config: body.config,
      columns_analyzed: body.columns,
    })

    addAnomalyDetectionToStore(detection)

    return HttpResponse.json(detection, { status: 201 })
  }),

  // Get a specific detection by ID
  http.get(`${API_BASE}/anomaly/:detectionId`, async ({ params }) => {
    await delay(150)

    const detectionId = params.detectionId as string
    const detection = getAnomalyDetectionById(detectionId)

    if (!detection) {
      return HttpResponse.json(
        { detail: 'Detection not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(detection)
  }),

  // List detections for a source
  http.get(`${API_BASE}/sources/:sourceId/anomaly/detections`, async ({ params, request }) => {
    await delay(200)

    const sourceId = params.sourceId as string
    const url = new URL(request.url)
    const offset = parseInt(url.searchParams.get('offset') ?? '0')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')

    // Get detections for this source
    const detections = getAnomalyDetectionsForSource(sourceId)

    // Sort by created_at desc
    detections.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )

    const total = detections.length
    const paginated = detections.slice(offset, offset + limit)

    return HttpResponse.json({
      data: paginated,
      total,
      offset,
      limit,
    })
  }),

  // Get the latest detection for a source
  http.get(`${API_BASE}/sources/:sourceId/anomaly/latest`, async ({ params }) => {
    await delay(150)

    const sourceId = params.sourceId as string
    const detections = getAnomalyDetectionsForSource(sourceId)

    if (detections.length === 0) {
      return HttpResponse.json(
        { detail: 'No detections found for this source' },
        { status: 404 }
      )
    }

    // Sort by created_at desc and return the first one
    detections.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )

    return HttpResponse.json(detections[0])
  }),

  // List available algorithms
  http.get(`${API_BASE}/anomaly/algorithms`, async () => {
    await delay(100)

    const algorithms = createAlgorithmInfo()

    return HttpResponse.json({
      algorithms,
      total: algorithms.length,
    })
  }),

  // ==========================================================================
  // Batch Detection Endpoints
  // ==========================================================================

  // Create batch detection job
  http.post(`${API_BASE}/anomaly/batch`, async ({ request }) => {
    await delay(500)

    let body: {
      source_ids: string[]
      name?: string
      algorithm?: AnomalyAlgorithm
      config?: Record<string, unknown>
      sample_size?: number
    }

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid request body' },
        { status: 400 }
      )
    }

    if (!body.source_ids || body.source_ids.length === 0) {
      return HttpResponse.json(
        { detail: 'No source IDs provided' },
        { status: 400 }
      )
    }

    // Validate source IDs
    const validSourceIds = body.source_ids.filter((id) =>
      getById(getStore().sources, id)
    )

    if (validSourceIds.length === 0) {
      return HttpResponse.json(
        { detail: 'No valid source IDs provided' },
        { status: 400 }
      )
    }

    // Create batch job
    const batchId = createId()
    const createdAt = new Date().toISOString()

    // Generate results for each source (simulate completed batch)
    const results: BatchSourceResult[] = validSourceIds.map((sourceId) => {
      const source = getById(getStore().sources, sourceId)
      const anomalyCount = randomInt(5, 200)
      const totalRows = randomInt(1000, 50000)

      // Create and store detection
      const detection = createAnomalyDetection({
        id: createId(),
        source_id: sourceId,
        status: 'success',
        algorithm: body.algorithm ?? 'isolation_forest',
        config: body.config,
        total_rows: totalRows,
        anomaly_rate: anomalyCount / totalRows,
      })
      addAnomalyDetectionToStore(detection)

      return {
        source_id: sourceId,
        source_name: source?.name ?? null,
        detection_id: detection.id,
        status: 'success',
        anomaly_count: anomalyCount,
        anomaly_rate: anomalyCount / totalRows,
        total_rows: totalRows,
        error_message: null,
      }
    })

    const totalAnomalies = results.reduce((sum, r) => sum + (r.anomaly_count ?? 0), 0)
    const totalRows = results.reduce((sum, r) => sum + (r.total_rows ?? 0), 0)
    const avgRate =
      results.length > 0
        ? results.reduce((sum, r) => sum + (r.anomaly_rate ?? 0), 0) / results.length
        : 0

    const batchJob: BatchDetectionJob = {
      id: batchId,
      name: body.name ?? null,
      status: 'completed',
      algorithm: body.algorithm ?? 'isolation_forest',
      config: body.config ?? null,
      total_sources: validSourceIds.length,
      completed_sources: validSourceIds.length,
      failed_sources: 0,
      progress_percent: 100,
      current_source_id: null,
      total_anomalies: totalAnomalies,
      total_rows_analyzed: totalRows,
      average_anomaly_rate: avgRate,
      results,
      duration_ms: randomInt(2000, 30000),
      error_message: null,
      created_at: createdAt,
      started_at: createdAt,
      completed_at: new Date().toISOString(),
    }

    // Store batch job
    addBatchJobToStore(batchJob)

    return HttpResponse.json(batchJob, { status: 201 })
  }),

  // Get batch job status
  http.get(`${API_BASE}/anomaly/batch/:batchId`, async ({ params }) => {
    await delay(150)

    const batchId = params.batchId as string
    const job = getBatchJobById(batchId)

    if (!job) {
      return HttpResponse.json(
        { detail: 'Batch job not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(job)
  }),

  // Get batch job results
  http.get(`${API_BASE}/anomaly/batch/:batchId/results`, async ({ params }) => {
    await delay(150)

    const batchId = params.batchId as string
    const job = getBatchJobById(batchId)

    if (!job) {
      return HttpResponse.json(
        { detail: 'Batch job not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(job.results ?? [])
  }),

  // List batch jobs
  http.get(`${API_BASE}/anomaly/batch`, async ({ request }) => {
    await delay(200)

    const url = new URL(request.url)
    const offset = parseInt(url.searchParams.get('offset') ?? '0')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')

    const jobs = getBatchJobs()
    const total = jobs.length
    const paginated = jobs.slice(offset, offset + limit)

    return HttpResponse.json({
      data: paginated,
      total,
      offset,
      limit,
    })
  }),

  // Cancel batch job
  http.post(`${API_BASE}/anomaly/batch/:batchId/cancel`, async ({ params }) => {
    await delay(200)

    const batchId = params.batchId as string
    const job = getBatchJobById(batchId)

    if (!job) {
      return HttpResponse.json(
        { detail: 'Batch job not found' },
        { status: 404 }
      )
    }

    // Update job status
    if (job.status === 'running' || job.status === 'pending') {
      job.status = 'cancelled'
      job.completed_at = new Date().toISOString()
    }

    return HttpResponse.json(job)
  }),

  // Delete batch job
  http.delete(`${API_BASE}/anomaly/batch/:batchId`, async ({ params }) => {
    await delay(150)

    const batchId = params.batchId as string
    const deleted = deleteBatchJob(batchId)

    if (!deleted) {
      return HttpResponse.json(
        { detail: 'Batch job not found' },
        { status: 404 }
      )
    }

    return new HttpResponse(null, { status: 204 })
  }),

  // ==========================================================================
  // Algorithm Comparison
  // ==========================================================================

  // Run multiple algorithms and compare results
  http.post(`${API_BASE}/anomaly/compare`, async ({ request }) => {
    await delay(3000) // Simulate running multiple algorithms

    const url = new URL(request.url)
    const sourceId = url.searchParams.get('source_id')

    if (!sourceId) {
      return HttpResponse.json(
        { detail: 'source_id query parameter is required' },
        { status: 400 }
      )
    }

    // Verify source exists
    const source = getById(getStore().sources, sourceId)
    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    let body: {
      algorithms: AnomalyAlgorithm[]
      columns?: string[]
      config?: Record<string, Record<string, unknown>>
      sample_size?: number
    }

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid request body' },
        { status: 400 }
      )
    }

    if (!body.algorithms || body.algorithms.length < 2) {
      return HttpResponse.json(
        { detail: 'At least 2 algorithms are required for comparison' },
        { status: 400 }
      )
    }

    const totalRows = randomInt(1000, 10000)
    const columns = body.columns || ['amount', 'quantity', 'price', 'score']

    // Generate results for each algorithm
    const algorithmResults: AlgorithmComparisonResultItem[] = []
    const allAnomalyIndices: Map<AnomalyAlgorithm, Set<number>> = new Map()

    const algorithmDisplayNames: Record<string, string> = {
      isolation_forest: 'Isolation Forest',
      lof: 'Local Outlier Factor',
      one_class_svm: 'One-Class SVM',
      dbscan: 'DBSCAN',
      statistical: 'Statistical',
      autoencoder: 'Autoencoder',
    }

    for (const algorithm of body.algorithms) {
      // Generate random anomaly indices for this algorithm
      const baseRate = faker.number.float({ min: 0.05, max: 0.15 })
      const anomalyCount = Math.floor(totalRows * baseRate)
      const anomalyIndices = new Set<number>()

      // Generate indices with some overlap between algorithms
      for (let i = 0; i < anomalyCount; i++) {
        // 30% chance to use a common index (for overlap)
        if (i < anomalyCount * 0.3 && allAnomalyIndices.size > 0) {
          // Pick from existing algorithm's indices
          const existingAlgo = Array.from(allAnomalyIndices.keys())[0]
          const existingIndices = Array.from(allAnomalyIndices.get(existingAlgo)!)
          if (existingIndices.length > 0) {
            const idx = existingIndices[randomInt(0, existingIndices.length - 1)]
            anomalyIndices.add(idx)
            continue
          }
        }
        anomalyIndices.add(randomInt(0, totalRows - 1))
      }

      allAnomalyIndices.set(algorithm, anomalyIndices)

      algorithmResults.push({
        algorithm,
        display_name: algorithmDisplayNames[algorithm] || algorithm,
        status: 'success',
        anomaly_count: anomalyIndices.size,
        anomaly_rate: anomalyIndices.size / totalRows,
        duration_ms: randomInt(500, 5000),
        error_message: null,
        anomaly_indices: Array.from(anomalyIndices).slice(0, 1000),
      })
    }

    // Calculate agreement
    const { agreementSummary, agreementRecords } = calculateMockAgreement(
      body.algorithms,
      allAnomalyIndices,
      totalRows
    )

    const comparisonResult: AlgorithmComparisonResult = {
      id: createId(),
      source_id: sourceId,
      status: 'success',
      total_rows: totalRows,
      columns_analyzed: columns,
      algorithm_results: algorithmResults,
      agreement_summary: agreementSummary,
      agreement_records: agreementRecords,
      total_duration_ms: algorithmResults.reduce((sum, r) => sum + (r.duration_ms ?? 0), 0),
      error_message: null,
      created_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
    }

    return HttpResponse.json(comparisonResult, { status: 201 })
  }),

  // Get comparison result by ID (not persisted)
  http.get(`${API_BASE}/anomaly/compare/:comparisonId`, async () => {
    await delay(100)

    return HttpResponse.json(
      {
        detail: 'Comparison results are computed on-the-fly and not persisted. Please run a new comparison using POST /anomaly/compare',
      },
      { status: 404 }
    )
  }),

  // ==========================================================================
  // Anomaly Explainability (SHAP/LIME)
  // ==========================================================================

  // Generate SHAP/LIME explanations for anomaly rows
  http.post(`${API_BASE}/anomaly/:detectionId/explain`, async ({ params, request }) => {
    await delay(1500) // Simulate explanation generation time

    const detectionId = params.detectionId as string

    // Get the detection
    const detection = getAnomalyDetectionById(detectionId)
    if (!detection) {
      return HttpResponse.json(
        { detail: 'Detection not found' },
        { status: 404 }
      )
    }

    let body: {
      row_indices: number[]
      max_features?: number
      sample_background?: number
    } = { row_indices: [] }

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'row_indices is required' },
        { status: 400 }
      )
    }

    if (!body.row_indices || body.row_indices.length === 0) {
      return HttpResponse.json(
        { detail: 'row_indices is required and cannot be empty' },
        { status: 400 }
      )
    }

    const maxFeatures = body.max_features || 10
    const featureNames = detection.columns_analyzed || ['amount', 'quantity', 'price']

    // Generate mock explanations for each requested row
    const explanations = body.row_indices.map((rowIndex) => {
      // Find the anomaly record for this row if it exists
      const anomaly = detection.anomalies?.find((a) => a.row_index === rowIndex)
      const anomalyScore = anomaly?.anomaly_score ?? faker.number.float({ min: 0.5, max: 1.0, fractionDigits: 4 })

      // Generate feature contributions
      const contributions = featureNames.slice(0, maxFeatures).map((feature) => {
        const shapValue = faker.number.float({ min: -1.0, max: 1.0, fractionDigits: 4 })
        return {
          feature,
          value: faker.number.float({ min: -1000, max: 10000, fractionDigits: 2 }),
          shap_value: shapValue,
          contribution: Math.abs(shapValue),
        }
      })

      // Sort by contribution (descending)
      contributions.sort((a, b) => b.contribution - a.contribution)

      // Generate summary
      const topFeatures = contributions.slice(0, 3)
      const summary = generateExplanationSummary(anomalyScore, topFeatures)

      return {
        row_index: rowIndex,
        anomaly_score: anomalyScore,
        feature_contributions: contributions,
        total_shap: contributions.reduce((sum, c) => sum + c.shap_value, 0),
        summary,
      }
    })

    // Store explanations in cache
    for (const exp of explanations) {
      addExplanationToStore(detectionId, exp)
    }

    return HttpResponse.json({
      detection_id: detectionId,
      algorithm: detection.algorithm,
      row_indices: body.row_indices,
      feature_names: featureNames,
      explanations,
      generated_at: new Date().toISOString(),
      error: null,
    })
  }),

  // Get cached explanations for a detection
  http.get(`${API_BASE}/anomaly/:detectionId/explanations`, async ({ params, request }) => {
    await delay(100)

    const detectionId = params.detectionId as string
    const url = new URL(request.url)
    const rowIndicesParam = url.searchParams.get('row_indices')

    // Get cached explanations
    let explanations = getExplanationsForDetection(detectionId)

    // Filter by row indices if provided
    if (rowIndicesParam) {
      const rowIndices = rowIndicesParam.split(',').map(Number)
      explanations = explanations.filter((e) => rowIndices.includes(e.row_index))
    }

    return HttpResponse.json({
      detection_id: detectionId,
      explanations: explanations.map((exp) => ({
        id: createId(),
        detection_id: detectionId,
        row_index: exp.row_index,
        anomaly_score: exp.anomaly_score,
        feature_contributions: exp.feature_contributions,
        total_shap: exp.total_shap,
        summary: exp.summary,
        generated_at: new Date().toISOString(),
      })),
      total: explanations.length,
    })
  }),

  // ==========================================================================
  // Streaming Anomaly Detection
  // ==========================================================================

  // Start streaming session
  http.post(`${API_BASE}/anomaly/streaming/start`, async ({ request }) => {
    await delay(300)

    let body: {
      source_id?: string
      algorithm?: StreamingAlgorithm
      window_size?: number
      threshold?: number
      columns?: string[]
      config?: Record<string, unknown>
    } = {}

    try {
      body = await request.json() as typeof body
    } catch {
      // Empty body is OK, use defaults
    }

    const sessionId = createId()
    const now = new Date().toISOString()

    const session: StreamingSession = {
      id: sessionId,
      source_id: body.source_id ?? null,
      algorithm: body.algorithm ?? 'zscore_rolling',
      window_size: body.window_size ?? 100,
      threshold: body.threshold ?? 3.0,
      columns: body.columns ?? [],
      status: 'running',
      config: body.config ?? null,
      statistics: {},
      total_points: 0,
      total_alerts: 0,
      created_at: now,
      started_at: now,
      stopped_at: null,
    }

    addStreamingSessionToStore(session)

    return HttpResponse.json(session, { status: 201 })
  }),

  // Push data point to streaming session
  http.post(`${API_BASE}/anomaly/streaming/:sessionId/data`, async ({ params, request }) => {
    await delay(50)

    const sessionId = params.sessionId as string
    const session = getStreamingSessionById(sessionId)

    if (!session) {
      return HttpResponse.json(
        { detail: 'Session not found' },
        { status: 404 }
      )
    }

    if (session.status !== 'running') {
      return HttpResponse.json(
        { detail: 'Session is not running' },
        { status: 400 }
      )
    }

    let body: {
      data: Record<string, unknown>
      timestamp?: string
    }

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid request body' },
        { status: 400 }
      )
    }

    // Update session stats
    session.total_points++

    // Simulate anomaly detection (5% chance)
    const isAnomaly = Math.random() < 0.05

    if (isAnomaly) {
      session.total_alerts++

      const alert: StreamingAlert = {
        id: createId(),
        session_id: sessionId,
        timestamp: body.timestamp ?? new Date().toISOString(),
        data_point: body.data,
        anomaly_score: faker.number.float({ min: 0.7, max: 1.0, fractionDigits: 3 }),
        is_anomaly: true,
        algorithm: session.algorithm,
        details: {
          anomaly_columns: session.columns.length > 0
            ? [session.columns[randomInt(0, session.columns.length - 1)]]
            : ['value'],
          threshold: session.threshold,
        },
      }

      addStreamingAlertToStore(sessionId, alert)

      return HttpResponse.json(alert)
    }

    return HttpResponse.json(null)
  }),

  // Push batch of data points
  http.post(`${API_BASE}/anomaly/streaming/:sessionId/batch`, async ({ params, request }) => {
    await delay(100)

    const sessionId = params.sessionId as string
    const session = getStreamingSessionById(sessionId)

    if (!session) {
      return HttpResponse.json(
        { detail: 'Session not found' },
        { status: 404 }
      )
    }

    let body: {
      data_points: Array<{
        data: Record<string, unknown>
        timestamp?: string
      }>
    }

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid request body' },
        { status: 400 }
      )
    }

    const alerts: StreamingAlert[] = []

    for (const dp of body.data_points) {
      session.total_points++

      // 5% chance of anomaly
      if (Math.random() < 0.05) {
        session.total_alerts++

        const alert: StreamingAlert = {
          id: createId(),
          session_id: sessionId,
          timestamp: dp.timestamp ?? new Date().toISOString(),
          data_point: dp.data,
          anomaly_score: faker.number.float({ min: 0.7, max: 1.0, fractionDigits: 3 }),
          is_anomaly: true,
          algorithm: session.algorithm,
          details: {},
        }

        addStreamingAlertToStore(sessionId, alert)
        alerts.push(alert)
      }
    }

    return HttpResponse.json(alerts)
  }),

  // Get streaming session status
  http.get(`${API_BASE}/anomaly/streaming/:sessionId/status`, async ({ params }) => {
    await delay(100)

    const sessionId = params.sessionId as string
    const session = getStreamingSessionById(sessionId)

    if (!session) {
      return HttpResponse.json(
        { detail: 'Session not found' },
        { status: 404 }
      )
    }

    const alerts = getStreamingAlertsForSession(sessionId)

    // Generate mock statistics for columns
    const statistics: Record<string, StreamingStatistics> = {}
    for (const col of session.columns) {
      statistics[col] = {
        count: session.total_points,
        mean: faker.number.float({ min: 50, max: 150, fractionDigits: 2 }),
        std: faker.number.float({ min: 5, max: 30, fractionDigits: 2 }),
        min: faker.number.float({ min: 0, max: 50, fractionDigits: 2 }),
        max: faker.number.float({ min: 150, max: 300, fractionDigits: 2 }),
        anomaly_count: session.total_alerts,
        anomaly_rate: session.total_points > 0
          ? session.total_alerts / session.total_points
          : 0,
      }
    }

    return HttpResponse.json({
      session_id: sessionId,
      status: session.status,
      total_points: session.total_points,
      total_alerts: session.total_alerts,
      buffer_utilization: Math.min(session.total_points / 1000, 1),
      statistics,
      recent_alerts: alerts.slice(-10),
    })
  }),

  // Stop streaming session
  http.post(`${API_BASE}/anomaly/streaming/:sessionId/stop`, async ({ params }) => {
    await delay(200)

    const sessionId = params.sessionId as string
    const session = getStreamingSessionById(sessionId)

    if (!session) {
      return HttpResponse.json(
        { detail: 'Session not found' },
        { status: 404 }
      )
    }

    session.status = 'stopped'
    session.stopped_at = new Date().toISOString()

    return HttpResponse.json(session)
  }),

  // Delete streaming session
  http.delete(`${API_BASE}/anomaly/streaming/:sessionId`, async ({ params }) => {
    await delay(100)

    const sessionId = params.sessionId as string
    const deleted = deleteStreamingSession(sessionId)

    if (!deleted) {
      return HttpResponse.json(
        { detail: 'Session not found' },
        { status: 404 }
      )
    }

    return new HttpResponse(null, { status: 204 })
  }),

  // List streaming alerts
  http.get(`${API_BASE}/anomaly/streaming/:sessionId/alerts`, async ({ params, request }) => {
    await delay(100)

    const sessionId = params.sessionId as string
    const session = getStreamingSessionById(sessionId)

    if (!session) {
      return HttpResponse.json(
        { detail: 'Session not found' },
        { status: 404 }
      )
    }

    const url = new URL(request.url)
    const offset = parseInt(url.searchParams.get('offset') ?? '0')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')

    const alerts = getStreamingAlertsForSession(sessionId)
    const paginated = alerts.slice(offset, offset + limit)

    return HttpResponse.json({
      data: paginated,
      total: alerts.length,
      offset,
      limit,
    })
  }),

  // Get recent data from streaming session
  http.get(`${API_BASE}/anomaly/streaming/:sessionId/data`, async ({ params, request }) => {
    await delay(100)

    const sessionId = params.sessionId as string
    const session = getStreamingSessionById(sessionId)

    if (!session) {
      return HttpResponse.json(
        { detail: 'Session not found' },
        { status: 404 }
      )
    }

    const url = new URL(request.url)
    const limit = parseInt(url.searchParams.get('limit') ?? '100')

    // Generate mock recent data points
    const dataPoints = []
    for (let i = 0; i < Math.min(limit, session.total_points); i++) {
      const timestamp = new Date(Date.now() - i * 1000).toISOString()
      const data: Record<string, unknown> = {}

      for (const col of session.columns) {
        data[col] = faker.number.float({ min: 50, max: 150, fractionDigits: 2 })
      }

      dataPoints.push({ timestamp, data })
    }

    return HttpResponse.json({
      session_id: sessionId,
      data_points: dataPoints,
      total: dataPoints.length,
    })
  }),

  // List all streaming sessions
  http.get(`${API_BASE}/anomaly/streaming/sessions`, async ({ request }) => {
    await delay(100)

    const url = new URL(request.url)
    const offset = parseInt(url.searchParams.get('offset') ?? '0')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')

    const sessions = getStreamingSessions()
    const paginated = sessions.slice(offset, offset + limit)

    return HttpResponse.json({
      data: paginated,
      total: sessions.length,
      offset,
      limit,
    })
  }),

  // List streaming algorithms
  http.get(`${API_BASE}/anomaly/streaming/algorithms`, async () => {
    await delay(100)

    const algorithms: StreamingAlgorithmInfo[] = [
      {
        name: 'zscore_rolling',
        display_name: 'Rolling Z-Score',
        description: 'Detects anomalies based on rolling z-scores computed over a sliding window.',
        supports_online_learning: true,
        parameters: [
          {
            name: 'window_size',
            label: 'Window Size',
            type: 'integer',
            default: 100,
            min_value: 10,
            max_value: 10000,
            options: null,
            description: 'Number of recent points to use for statistics',
          },
          {
            name: 'threshold',
            label: 'Z-Score Threshold',
            type: 'float',
            default: 3.0,
            min_value: 1.0,
            max_value: 5.0,
            options: null,
            description: 'Number of standard deviations for anomaly threshold',
          },
        ],
        best_for: 'Simple time series with stationary patterns',
      },
      {
        name: 'ema',
        display_name: 'Exponential Moving Average',
        description: 'Uses exponentially weighted moving average to track trends and detect deviations.',
        supports_online_learning: true,
        parameters: [
          {
            name: 'alpha',
            label: 'Smoothing Factor',
            type: 'float',
            default: 0.1,
            min_value: 0.01,
            max_value: 0.5,
            options: null,
            description: 'Weight for recent observations',
          },
        ],
        best_for: 'Non-stationary data with changing trends',
      },
      {
        name: 'isolation_forest_incremental',
        display_name: 'Incremental Isolation Forest',
        description: 'Periodically retrains Isolation Forest on recent window data.',
        supports_online_learning: false,
        parameters: [
          {
            name: 'contamination',
            label: 'Contamination',
            type: 'float',
            default: 0.1,
            min_value: 0.01,
            max_value: 0.5,
            options: null,
            description: 'Expected proportion of anomalies',
          },
        ],
        best_for: 'Multi-dimensional streams',
      },
      {
        name: 'half_space_trees',
        display_name: 'Half-Space Trees',
        description: 'Streaming variant of Isolation Forest using half-space partitioning.',
        supports_online_learning: true,
        parameters: [],
        best_for: 'High-dimensional streaming data',
      },
      {
        name: 'rrcf',
        display_name: 'Robust Random Cut Forest',
        description: 'Uses collusive displacement for anomaly scoring.',
        supports_online_learning: true,
        parameters: [],
        best_for: 'Complex streaming data with concept drift',
      },
    ]

    return HttpResponse.json({
      algorithms,
      total: algorithms.length,
    })
  }),
]

// ==========================================================================
// Batch Job Store
// ==========================================================================

const batchJobStore: Map<string, BatchDetectionJob> = new Map()

function addBatchJobToStore(job: BatchDetectionJob): void {
  batchJobStore.set(job.id, job)
}

function getBatchJobById(id: string): BatchDetectionJob | undefined {
  return batchJobStore.get(id)
}

function getBatchJobs(): BatchDetectionJob[] {
  return Array.from(batchJobStore.values()).sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  )
}

function deleteBatchJob(id: string): boolean {
  return batchJobStore.delete(id)
}

// ==========================================================================
// Explanation Store
// ==========================================================================

interface StoredExplanation {
  row_index: number
  anomaly_score: number
  feature_contributions: Array<{
    feature: string
    value: number
    shap_value: number
    contribution: number
  }>
  total_shap: number
  summary: string
}

const explanationStore: Map<string, StoredExplanation[]> = new Map()

function addExplanationToStore(detectionId: string, explanation: StoredExplanation): void {
  if (!explanationStore.has(detectionId)) {
    explanationStore.set(detectionId, [])
  }
  const explanations = explanationStore.get(detectionId)!
  // Replace if exists, otherwise add
  const existingIndex = explanations.findIndex(e => e.row_index === explanation.row_index)
  if (existingIndex >= 0) {
    explanations[existingIndex] = explanation
  } else {
    explanations.push(explanation)
  }
}

function getExplanationsForDetection(detectionId: string): StoredExplanation[] {
  return explanationStore.get(detectionId) || []
}

function generateExplanationSummary(
  anomalyScore: number,
  topFeatures: Array<{ feature: string; value: number; shap_value: number }>
): string {
  // Determine severity
  let severity: string
  if (anomalyScore >= 0.9) {
    severity = 'highly anomalous'
  } else if (anomalyScore >= 0.7) {
    severity = 'moderately anomalous'
  } else if (anomalyScore >= 0.5) {
    severity = 'slightly anomalous'
  } else {
    severity = 'borderline anomalous'
  }

  // Build feature descriptions
  const descriptions = topFeatures.map(f => {
    const direction = f.shap_value > 0 ? 'unusually high' : 'unusually low'
    return `${f.feature} (${f.value.toFixed(2)}) is ${direction}`
  })

  let featuresText: string
  if (descriptions.length === 1) {
    featuresText = descriptions[0]
  } else if (descriptions.length === 2) {
    featuresText = descriptions.join(' and ')
  } else {
    featuresText = descriptions.slice(0, -1).join(', ') + ', and ' + descriptions[descriptions.length - 1]
  }

  return `This row is ${severity} (score: ${anomalyScore.toFixed(3)}). The main contributing factors are: ${featuresText}.`
}

// ==========================================================================
// Algorithm Comparison Helpers
// ==========================================================================

function calculateMockAgreement(
  algorithms: AnomalyAlgorithm[],
  allAnomalyIndices: Map<AnomalyAlgorithm, Set<number>>,
  _totalRows: number
): { agreementSummary: AgreementSummary; agreementRecords: AgreementRecord[] } {
  // Get all unique anomaly indices
  const allIndices = new Set<number>()
  for (const indices of allAnomalyIndices.values()) {
    for (const idx of indices) {
      allIndices.add(idx)
    }
  }

  // Calculate which algorithms detected each row
  const rowDetections: Map<number, AnomalyAlgorithm[]> = new Map()
  for (const [algorithm, indices] of allAnomalyIndices) {
    for (const idx of indices) {
      if (!rowDetections.has(idx)) {
        rowDetections.set(idx, [])
      }
      rowDetections.get(idx)!.push(algorithm)
    }
  }

  const numAlgorithms = algorithms.length
  const majorityThreshold = Math.floor(numAlgorithms / 2) + 1

  // Classify by agreement level
  let allAgreeCount = 0
  let majorityAgreeCount = 0
  let someAgreeCount = 0
  let oneOnlyCount = 0

  const agreementRecords: AgreementRecord[] = []

  for (const [rowIndex, detectedBy] of rowDetections) {
    const detectionCount = detectedBy.length
    const confidenceScore = detectionCount / numAlgorithms

    let agreementLevel: AgreementLevel
    if (detectionCount === numAlgorithms) {
      agreementLevel = 'all'
      allAgreeCount++
    } else if (detectionCount >= majorityThreshold) {
      agreementLevel = 'majority'
      majorityAgreeCount++
    } else if (detectionCount >= 2) {
      agreementLevel = 'some'
      someAgreeCount++
    } else {
      agreementLevel = 'one'
      oneOnlyCount++
    }

    // Only add first 100 records
    if (agreementRecords.length < 100) {
      agreementRecords.push({
        row_index: rowIndex,
        detected_by: detectedBy,
        detection_count: detectionCount,
        agreement_level: agreementLevel,
        confidence_score: confidenceScore,
        column_values: {},
      })
    }
  }

  // Sort by confidence score (descending)
  agreementRecords.sort((a, b) => b.confidence_score - a.confidence_score)

  // Calculate pairwise overlap matrix
  const agreementMatrix: number[][] = []
  for (const algoI of algorithms) {
    const row: number[] = []
    for (const algoJ of algorithms) {
      if (algoI === algoJ) {
        row.push(allAnomalyIndices.get(algoI)?.size ?? 0)
      } else {
        const setI = allAnomalyIndices.get(algoI) ?? new Set()
        const setJ = allAnomalyIndices.get(algoJ) ?? new Set()
        let overlap = 0
        for (const idx of setI) {
          if (setJ.has(idx)) {
            overlap++
          }
        }
        row.push(overlap)
      }
    }
    agreementMatrix.push(row)
  }

  const agreementSummary: AgreementSummary = {
    total_algorithms: numAlgorithms,
    total_unique_anomalies: allIndices.size,
    all_agree_count: allAgreeCount,
    majority_agree_count: majorityAgreeCount,
    some_agree_count: someAgreeCount,
    one_only_count: oneOnlyCount,
    agreement_matrix: agreementMatrix,
  }

  return { agreementSummary, agreementRecords }
}

// ==========================================================================
// Streaming Session Store
// ==========================================================================

const streamingSessionStore: Map<string, StreamingSession> = new Map()
const streamingAlertStore: Map<string, StreamingAlert[]> = new Map()

function addStreamingSessionToStore(session: StreamingSession): void {
  streamingSessionStore.set(session.id, session)
  streamingAlertStore.set(session.id, [])
}

function getStreamingSessionById(id: string): StreamingSession | undefined {
  return streamingSessionStore.get(id)
}

function getStreamingSessions(): StreamingSession[] {
  return Array.from(streamingSessionStore.values()).sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  )
}

function deleteStreamingSession(id: string): boolean {
  streamingAlertStore.delete(id)
  return streamingSessionStore.delete(id)
}

function addStreamingAlertToStore(sessionId: string, alert: StreamingAlert): void {
  if (!streamingAlertStore.has(sessionId)) {
    streamingAlertStore.set(sessionId, [])
  }
  streamingAlertStore.get(sessionId)!.push(alert)
}

function getStreamingAlertsForSession(sessionId: string): StreamingAlert[] {
  return streamingAlertStore.get(sessionId) || []
}
