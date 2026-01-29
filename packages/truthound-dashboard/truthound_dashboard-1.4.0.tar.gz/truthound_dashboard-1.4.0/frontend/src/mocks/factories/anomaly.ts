/**
 * Anomaly detection factory - generates anomaly detection results for mock API
 *
 * Supports 6 ML algorithms:
 * - isolation_forest: Tree-based anomaly isolation
 * - lof: Local Outlier Factor
 * - one_class_svm: One-Class SVM
 * - dbscan: DBSCAN clustering
 * - statistical: Z-score/IQR/MAD methods
 * - autoencoder: Neural network-based
 */

import type {
  AnomalyDetection,
  AnomalyRecord,
  ColumnAnomalySummary,
  AnomalyAlgorithm,
  AnomalyStatus,
  AlgorithmInfo,
  AlgorithmParameter,
} from '@/api/client'
import { createId, createTimestamp, randomChoice, randomInt, faker } from './base'

const ALGORITHMS: AnomalyAlgorithm[] = [
  'isolation_forest',
  'lof',
  'one_class_svm',
  'dbscan',
  'statistical',
  'autoencoder',
]

// Status values for anomaly detection - using AnomalyStatus type from client

const COLUMN_NAMES = [
  'amount',
  'quantity',
  'price',
  'revenue',
  'cost',
  'margin',
  'score',
  'rating',
  'count',
  'total',
  'balance',
  'duration',
  'latency',
  'response_time',
  'error_count',
]

const DTYPES = ['int64', 'float64']

export interface AnomalyRecordOptions {
  row_index?: number
  anomaly_score?: number
  is_anomaly?: boolean
}

export interface ColumnAnomalySummaryOptions {
  column?: string
  dtype?: string
  anomaly_count?: number
  anomaly_rate?: number
}

export interface AnomalyDetectionOptions {
  id?: string
  source_id?: string
  status?: AnomalyStatus
  algorithm?: AnomalyAlgorithm
  config?: Record<string, unknown>
  total_rows?: number
  anomaly_rate?: number
  columns_analyzed?: string[]
}

/**
 * Create a single anomaly record
 */
export function createAnomalyRecord(options: AnomalyRecordOptions = {}): AnomalyRecord {
  const isAnomaly = options.is_anomaly ?? faker.datatype.boolean(0.1)

  return {
    row_index: options.row_index ?? randomInt(0, 10000),
    anomaly_score: options.anomaly_score ?? (
      isAnomaly
        ? faker.number.float({ min: 0.7, max: 1.0, fractionDigits: 4 })
        : faker.number.float({ min: 0.0, max: 0.3, fractionDigits: 4 })
    ),
    column_values: {
      amount: faker.number.float({ min: -1000, max: 10000, fractionDigits: 2 }),
      quantity: randomInt(-10, 1000),
      price: faker.number.float({ min: 0, max: 500, fractionDigits: 2 }),
    },
    is_anomaly: isAnomaly,
  }
}

/**
 * Create a column anomaly summary
 */
export function createColumnAnomalySummary(
  options: ColumnAnomalySummaryOptions = {}
): ColumnAnomalySummary {
  const anomalyCount = options.anomaly_count ?? randomInt(0, 100)
  const totalRows = 10000
  const anomalyRate = options.anomaly_rate ?? anomalyCount / totalRows

  return {
    column: options.column ?? randomChoice(COLUMN_NAMES),
    dtype: options.dtype ?? randomChoice(DTYPES),
    anomaly_count: anomalyCount,
    anomaly_rate: anomalyRate,
    mean_anomaly_score: faker.number.float({ min: 0.1, max: 0.9, fractionDigits: 4 }),
    min_value: faker.number.float({ min: -1000, max: 0, fractionDigits: 2 }),
    max_value: faker.number.float({ min: 1000, max: 10000, fractionDigits: 2 }),
    top_anomaly_indices: Array.from({ length: Math.min(5, anomalyCount) }, () => randomInt(0, totalRows)),
  }
}

/**
 * Create an anomaly detection result
 */
export function createAnomalyDetection(options: AnomalyDetectionOptions = {}): AnomalyDetection {
  const status = options.status ?? randomChoice(['success', 'success', 'success', 'error'] as AnomalyStatus[])
  const algorithm = options.algorithm ?? randomChoice(ALGORITHMS)
  const totalRows = options.total_rows ?? randomInt(1000, 100000)
  const anomalyRate = options.anomaly_rate ?? faker.number.float({ min: 0.01, max: 0.15, fractionDigits: 4 })
  const anomalyCount = Math.floor(totalRows * anomalyRate)
  const columnsAnalyzed = options.columns_analyzed ?? faker.helpers.arrayElements(COLUMN_NAMES, randomInt(3, 8))

  const createdAt = createTimestamp(randomInt(0, 30))
  const startedAt = status !== 'pending' ? createdAt : null
  const completedAt = status === 'success' || status === 'error' ? createTimestamp(randomInt(0, 29)) : null

  // Generate column summaries for successful detections
  const columnSummaries = status === 'success'
    ? columnsAnalyzed.map(column => createColumnAnomalySummary({ column }))
    : null

  // Generate anomaly records for successful detections (top 100)
  const anomalies = status === 'success'
    ? Array.from({ length: Math.min(100, anomalyCount) }, (_, i) =>
        createAnomalyRecord({ row_index: i * 10, is_anomaly: true })
      )
    : null

  // Generate algorithm-specific config
  const config = options.config ?? getDefaultConfig(algorithm)

  return {
    id: options.id ?? createId(),
    source_id: options.source_id ?? createId(),
    status,
    algorithm,
    config,
    total_rows: status === 'success' ? totalRows : null,
    anomaly_count: status === 'success' ? anomalyCount : null,
    anomaly_rate: status === 'success' ? anomalyRate : null,
    columns_analyzed: status === 'success' || status === 'running' ? columnsAnalyzed : null,
    column_summaries: columnSummaries,
    anomalies,
    duration_ms: status === 'success' ? randomInt(500, 30000) : null,
    error_message: status === 'error' ? 'Failed to run detection: insufficient numeric columns' : null,
    created_at: createdAt,
    started_at: startedAt,
    completed_at: completedAt,
  }
}

/**
 * Get default config for an algorithm
 */
function getDefaultConfig(algorithm: AnomalyAlgorithm): Record<string, unknown> {
  switch (algorithm) {
    case 'isolation_forest':
      return {
        n_estimators: 100,
        contamination: 0.1,
        max_samples: 'auto',
        random_state: 42,
      }
    case 'lof':
      return {
        n_neighbors: 20,
        contamination: 0.1,
        algorithm: 'auto',
      }
    case 'one_class_svm':
      return {
        kernel: 'rbf',
        nu: 0.1,
        gamma: 'scale',
      }
    case 'dbscan':
      return {
        eps: 0.5,
        min_samples: 5,
        metric: 'euclidean',
      }
    case 'statistical':
      return {
        method: 'zscore',
        threshold: 3.0,
      }
    case 'autoencoder':
      return {
        encoding_dim: 32,
        epochs: 50,
        threshold_percentile: 95,
        batch_size: 32,
      }
  }
}

/**
 * Create algorithm info for the algorithms endpoint
 */
export function createAlgorithmInfo(): AlgorithmInfo[] {
  return [
    {
      name: 'isolation_forest',
      display_name: 'Isolation Forest',
      description: 'Tree-based algorithm that isolates anomalies by random partitioning',
      category: 'tree',
      parameters: [
        createParameter('n_estimators', 'Number of Trees', 'integer', 100, 10, 500, null, 'Number of isolation trees'),
        createParameter('contamination', 'Contamination', 'float', 0.1, 0.01, 0.5, null, 'Expected proportion of anomalies'),
      ],
      pros: ['Fast training and prediction', 'Scales well to large datasets', 'No distribution assumptions'],
      cons: ['May miss clustered anomalies', 'Sensitive to contamination parameter'],
      best_for: 'Large datasets with global anomalies, high-dimensional data',
      requires_scaling: false,
    },
    {
      name: 'lof',
      display_name: 'Local Outlier Factor',
      description: 'Density-based algorithm comparing local density with neighbors',
      category: 'density',
      parameters: [
        createParameter('n_neighbors', 'Number of Neighbors', 'integer', 20, 5, 100, null, 'Number of neighbors for LOF'),
        createParameter('contamination', 'Contamination', 'float', 0.1, 0.01, 0.5, null, 'Expected proportion of anomalies'),
      ],
      pros: ['Detects local anomalies', 'Works well with varying densities', 'Intuitive interpretation'],
      cons: ['Computationally expensive for large datasets', 'Sensitive to n_neighbors'],
      best_for: 'Datasets with varying cluster densities, local outlier detection',
      requires_scaling: true,
    },
    {
      name: 'one_class_svm',
      display_name: 'One-Class SVM',
      description: 'SVM trained on normal data to create a decision boundary',
      category: 'svm',
      parameters: [
        createParameter('kernel', 'Kernel', 'select', 'rbf', null, null, ['rbf', 'linear', 'poly', 'sigmoid'], 'Kernel function'),
        createParameter('nu', 'Nu', 'float', 0.1, 0.01, 0.5, null, 'Upper bound on fraction of anomalies'),
      ],
      pros: ['Effective in high dimensions', 'Flexible via kernel choice', 'Memory efficient'],
      cons: ['Slow for large datasets', 'Sensitive to kernel and parameters'],
      best_for: 'High-dimensional data, when data fits in memory',
      requires_scaling: true,
    },
    {
      name: 'dbscan',
      display_name: 'DBSCAN',
      description: 'Density-based clustering that identifies outliers',
      category: 'clustering',
      parameters: [
        createParameter('eps', 'Epsilon (eps)', 'float', 0.5, 0.01, 10.0, null, 'Maximum distance between samples'),
        createParameter('min_samples', 'Minimum Samples', 'integer', 5, 2, 50, null, 'Minimum samples in neighborhood'),
      ],
      pros: ['No contamination parameter needed', 'Finds arbitrarily shaped clusters', 'Robust to noise'],
      cons: ['Sensitive to eps parameter', 'Struggles with varying densities'],
      best_for: 'Datasets with clear cluster structure, spatial data',
      requires_scaling: true,
    },
    {
      name: 'statistical',
      display_name: 'Statistical',
      description: 'Z-score, IQR, or MAD based detection',
      category: 'statistical',
      parameters: [
        createParameter('method', 'Method', 'select', 'zscore', null, null, ['zscore', 'iqr', 'mad'], 'Statistical method'),
        createParameter('threshold', 'Threshold', 'float', 3.0, 1.0, 5.0, null, 'Number of standard deviations'),
      ],
      pros: ['Simple and interpretable', 'Fast computation', 'Works on univariate data'],
      cons: ['Assumes normal distribution (for z-score)', 'May miss complex anomalies'],
      best_for: 'Univariate data, quick analysis, interpretable results',
      requires_scaling: false,
    },
    {
      name: 'autoencoder',
      display_name: 'Autoencoder',
      description: 'Neural network with high reconstruction error for anomalies',
      category: 'neural',
      parameters: [
        createParameter('encoding_dim', 'Encoding Dimension', 'integer', 32, 8, 256, null, 'Dimension of encoding layer'),
        createParameter('epochs', 'Training Epochs', 'integer', 50, 10, 200, null, 'Number of training epochs'),
        createParameter('threshold_percentile', 'Threshold Percentile', 'float', 95, 90, 99, null, 'Percentile for anomaly threshold'),
      ],
      pros: ['Captures complex patterns', 'Learns data representation', 'Works with high dimensions'],
      cons: ['Requires more data', 'Computationally expensive', 'Black box'],
      best_for: 'Complex patterns, large datasets, multivariate anomalies',
      requires_scaling: true,
    },
  ]
}

function createParameter(
  name: string,
  label: string,
  type: 'integer' | 'float' | 'string' | 'select' | 'boolean',
  defaultValue: unknown,
  minValue: number | null,
  maxValue: number | null,
  options: string[] | null,
  description: string
): AlgorithmParameter {
  return {
    name,
    label,
    type,
    default: defaultValue,
    min_value: minValue,
    max_value: maxValue,
    options,
    description,
  }
}

/**
 * Create multiple anomaly detections
 */
export function createAnomalyDetections(
  count: number,
  sourceId?: string
): AnomalyDetection[] {
  return Array.from({ length: count }, () =>
    createAnomalyDetection({ source_id: sourceId })
  )
}

/**
 * Create diverse anomaly detections for testing all scenarios
 */
export function createDiverseAnomalyDetections(sourceId: string): AnomalyDetection[] {
  const detections: AnomalyDetection[] = []

  // One successful detection for each algorithm
  for (const algorithm of ALGORITHMS) {
    detections.push(createAnomalyDetection({
      source_id: sourceId,
      status: 'success',
      algorithm,
    }))
  }

  // Add some with different statuses
  detections.push(createAnomalyDetection({
    source_id: sourceId,
    status: 'pending',
    algorithm: 'isolation_forest',
  }))

  detections.push(createAnomalyDetection({
    source_id: sourceId,
    status: 'running',
    algorithm: 'lof',
  }))

  detections.push(createAnomalyDetection({
    source_id: sourceId,
    status: 'error',
    algorithm: 'autoencoder',
  }))

  // Add some with high anomaly rate
  detections.push(createAnomalyDetection({
    source_id: sourceId,
    status: 'success',
    algorithm: 'statistical',
    anomaly_rate: 0.25, // 25% anomalies
  }))

  // Add some with low anomaly rate
  detections.push(createAnomalyDetection({
    source_id: sourceId,
    status: 'success',
    algorithm: 'isolation_forest',
    anomaly_rate: 0.02, // 2% anomalies
  }))

  return detections
}

// In-memory store for anomaly detections by source
const anomalyStore: Map<string, AnomalyDetection[]> = new Map()

/**
 * Get anomaly detections for a source
 */
export function getAnomalyDetectionsForSource(sourceId: string): AnomalyDetection[] {
  if (!anomalyStore.has(sourceId)) {
    anomalyStore.set(sourceId, createDiverseAnomalyDetections(sourceId))
  }
  return anomalyStore.get(sourceId)!
}

/**
 * Add a detection to the store
 */
export function addAnomalyDetectionToStore(detection: AnomalyDetection): void {
  const sourceId = detection.source_id
  if (!anomalyStore.has(sourceId)) {
    anomalyStore.set(sourceId, [])
  }
  anomalyStore.get(sourceId)!.unshift(detection) // Add to front (most recent)
}

/**
 * Get a specific detection by ID
 */
export function getAnomalyDetectionById(detectionId: string): AnomalyDetection | undefined {
  for (const detections of anomalyStore.values()) {
    const found = detections.find(d => d.id === detectionId)
    if (found) return found
  }
  return undefined
}

/**
 * Reset the anomaly store
 */
export function resetAnomalyStore(): void {
  anomalyStore.clear()
}
