/**
 * Main anomaly detection panel.
 *
 * Combines algorithm selection, configuration, execution, and results display.
 */

import { useCallback, useEffect, useState } from 'react'
import { useIntlayer } from 'react-intlayer'
import { str } from '@/lib/intlayer-utils'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { useToast } from '@/hooks/use-toast'
import { Loader2, Play, History, BarChart3, Table2 } from 'lucide-react'
import { AlgorithmSelector } from './AlgorithmSelector'
import { AlgorithmConfigForm } from './AlgorithmConfigForm'
import { AnomalyResultsTable } from './AnomalyResultsTable'
import { AnomalyScoreChart } from './AnomalyScoreChart'
import { ColumnAnomalySummary } from './ColumnAnomalySummary'
import { AnomalyHistoryList } from './AnomalyHistoryList'
import { AnomalyExplanation, type ExplainabilityResult } from './AnomalyExplanation'
import type {
  AlgorithmInfo,
  AnomalyDetection,
  AnomalyDetectionConfig,
} from '@/api/client'
import {
  listAnomalyAlgorithms,
  runAnomalyDetection,
  getAnomalyDetection,
  listAnomalyDetections,
  explainAnomaly,
} from '@/api/client'

interface AnomalyDetectionPanelProps {
  sourceId: string
  columns?: string[]
  className?: string
}

export function AnomalyDetectionPanel({
  sourceId,
  columns = [],
  className,
}: AnomalyDetectionPanelProps) {
  const t = useIntlayer('anomaly')
  const { toast } = useToast()

  // State
  const [algorithms, setAlgorithms] = useState<AlgorithmInfo[]>([])
  const [selectedAlgorithm, setSelectedAlgorithm] = useState<AlgorithmInfo | null>(null)
  const [config, setConfig] = useState<AnomalyDetectionConfig>({
    algorithm: 'isolation_forest',
    columns: [],
  })
  const [isLoadingAlgorithms, setIsLoadingAlgorithms] = useState(true)
  const [isRunning, setIsRunning] = useState(false)
  const [currentDetection, setCurrentDetection] = useState<AnomalyDetection | null>(null)
  const [history, setHistory] = useState<AnomalyDetection[]>([])
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  const [activeTab, setActiveTab] = useState<string>('configure')
  const [explanationOpen, setExplanationOpen] = useState(false)
  const [explanationRowIndices, setExplanationRowIndices] = useState<number[]>([])

  // Load algorithms
  useEffect(() => {
    const loadAlgorithms = async () => {
      setIsLoadingAlgorithms(true)
      try {
        const response = await listAnomalyAlgorithms()
        setAlgorithms(response.algorithms)
        // Default to isolation_forest
        const defaultAlgo = response.algorithms.find((a: AlgorithmInfo) => a.name === 'isolation_forest')
        if (defaultAlgo) {
          setSelectedAlgorithm(defaultAlgo)
          setConfig((prev: AnomalyDetectionConfig) => ({ ...prev, algorithm: defaultAlgo.name }))
        }
      } catch (error) {
        toast({
          title: str(t.errorLoadingAlgorithms),
          variant: 'destructive',
        })
      } finally {
        setIsLoadingAlgorithms(false)
      }
    }
    loadAlgorithms()
  }, [toast, t])

  // Load history
  const loadHistory = useCallback(async () => {
    setIsLoadingHistory(true)
    try {
      const response = await listAnomalyDetections(sourceId)
      setHistory(response.data)
    } catch (error) {
      toast({
        title: str(t.errorLoadingHistory),
        variant: 'destructive',
      })
    } finally {
      setIsLoadingHistory(false)
    }
  }, [sourceId, toast, t])

  useEffect(() => {
    loadHistory()
  }, [loadHistory])

  // Handle algorithm selection
  const handleAlgorithmSelect = useCallback((algorithm: AlgorithmInfo) => {
    setSelectedAlgorithm(algorithm)
    setConfig((prev) => ({
      ...prev,
      algorithm: algorithm.name,
      params: {},
    }))
  }, [])

  // Handle config change
  const handleConfigChange = useCallback((newConfig: AnomalyDetectionConfig) => {
    setConfig(newConfig)
  }, [])

  // Run detection
  const handleRunDetection = useCallback(async () => {
    setIsRunning(true)
    try {
      const detection = await runAnomalyDetection(sourceId, config)

      // Poll for completion
      const pollResult = async () => {
        const result = await getAnomalyDetection(detection.id)
        if (result.status === 'running' || result.status === 'pending') {
          setTimeout(pollResult, 1000)
        } else {
          setCurrentDetection(result)
          setIsRunning(false)
          setActiveTab('results')
          loadHistory()

          if (result.status === 'success') {
            toast({ title: str(t.detectionComplete) })
          } else if (result.status === 'error') {
            toast({
              title: str(t.detectionFailed),
              description: result.error_message,
              variant: 'destructive',
            })
          }
        }
      }

      pollResult()
    } catch (error) {
      setIsRunning(false)
      toast({
        title: str(t.detectionFailed),
        variant: 'destructive',
      })
    }
  }, [sourceId, config, toast, t, loadHistory])

  // Handle view details from history
  const handleViewDetails = useCallback((detection: AnomalyDetection) => {
    setCurrentDetection(detection)
    setActiveTab('results')
  }, [])

  // Handle explain anomaly
  const handleExplain = useCallback((rowIndices: number[]) => {
    setExplanationRowIndices(rowIndices)
    setExplanationOpen(true)
  }, [])

  // Generate explanation via API
  const generateExplanation = useCallback(
    async (detectionId: string, rowIndices: number[]): Promise<ExplainabilityResult> => {
      const result = await explainAnomaly(detectionId, rowIndices)
      return result
    },
    []
  )

  if (isLoadingAlgorithms) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className={className}>
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="mb-4 flex items-center justify-between">
          <TabsList>
            <TabsTrigger value="configure" className="gap-2">
              <BarChart3 className="h-4 w-4" />
              {t.configure}
            </TabsTrigger>
            <TabsTrigger value="results" className="gap-2" disabled={!currentDetection}>
              <Table2 className="h-4 w-4" />
              {t.results}
            </TabsTrigger>
            <TabsTrigger value="history" className="gap-2">
              <History className="h-4 w-4" />
              {t.history}
            </TabsTrigger>
          </TabsList>

          {activeTab === 'configure' && (
            <Button
              onClick={handleRunDetection}
              disabled={isRunning || !selectedAlgorithm}
              className="gap-2"
            >
              {isRunning ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Play className="h-4 w-4" />
              )}
              {isRunning ? t.running : t.runDetection}
            </Button>
          )}
        </div>

        <TabsContent value="configure" className="space-y-6">
          {/* Algorithm Selection */}
          <div>
            <h3 className="mb-3 text-sm font-medium">{t.selectAlgorithm}</h3>
            <AlgorithmSelector
              algorithms={algorithms}
              selectedAlgorithm={selectedAlgorithm}
              onSelect={handleAlgorithmSelect}
            />
          </div>

          {/* Algorithm Configuration */}
          {selectedAlgorithm && (
            <div>
              <h3 className="mb-3 text-sm font-medium">{t.configureParams}</h3>
              <AlgorithmConfigForm
                algorithm={selectedAlgorithm}
                config={config}
                onChange={handleConfigChange}
                availableColumns={columns}
              />
            </div>
          )}
        </TabsContent>

        <TabsContent value="results" className="space-y-6">
          {currentDetection ? (
            <>
              {/* Summary Stats */}
              <div className="grid gap-4 md:grid-cols-4">
                <div className="rounded-lg border p-4">
                  <p className="text-sm text-muted-foreground">{t.totalRows}</p>
                  <p className="text-2xl font-bold">
                    {currentDetection.total_rows?.toLocaleString() ?? '-'}
                  </p>
                </div>
                <div className="rounded-lg border p-4">
                  <p className="text-sm text-muted-foreground">{t.anomalyCount}</p>
                  <p className="text-2xl font-bold text-orange-500">
                    {currentDetection.anomaly_count?.toLocaleString() ?? '-'}
                  </p>
                </div>
                <div className="rounded-lg border p-4">
                  <p className="text-sm text-muted-foreground">{t.anomalyRate}</p>
                  <p className="text-2xl font-bold">
                    {currentDetection.anomaly_rate != null
                      ? `${(currentDetection.anomaly_rate * 100).toFixed(2)}%`
                      : '-'}
                  </p>
                </div>
                <div className="rounded-lg border p-4">
                  <p className="text-sm text-muted-foreground">{t.duration}</p>
                  <p className="text-2xl font-bold">
                    {currentDetection.duration_ms != null
                      ? `${(currentDetection.duration_ms / 1000).toFixed(1)}s`
                      : '-'}
                  </p>
                </div>
              </div>

              {/* Score Distribution Chart */}
              {currentDetection.anomalies && currentDetection.anomalies.length > 0 && (
                <div>
                  <h3 className="mb-3 text-sm font-medium">{t.scoreDistribution}</h3>
                  <AnomalyScoreChart anomalies={currentDetection.anomalies} />
                </div>
              )}

              {/* Column Summary */}
              {currentDetection.column_summaries && currentDetection.column_summaries.length > 0 && (
                <div>
                  <h3 className="mb-3 text-sm font-medium">{t.columnSummary}</h3>
                  <ColumnAnomalySummary summaries={currentDetection.column_summaries} />
                </div>
              )}

              {/* Anomaly Records Table */}
              {currentDetection.anomalies && currentDetection.anomalies.length > 0 && (
                <div>
                  <h3 className="mb-3 text-sm font-medium">{t.anomalyRecords}</h3>
                  <AnomalyResultsTable
                    anomalies={currentDetection.anomalies}
                    onExplain={handleExplain}
                  />
                </div>
              )}
            </>
          ) : (
            <div className="flex h-64 flex-col items-center justify-center gap-2 rounded-lg border border-dashed">
              <Table2 className="h-8 w-8 text-muted-foreground" />
              <p className="text-muted-foreground">{t.noResults}</p>
              <p className="text-sm text-muted-foreground">{t.runDetectionFirst}</p>
            </div>
          )}
        </TabsContent>

        <TabsContent value="history">
          <AnomalyHistoryList
            detections={history}
            onViewDetails={handleViewDetails}
            isLoading={isLoadingHistory}
          />
        </TabsContent>
      </Tabs>

      {/* Anomaly Explanation Dialog */}
      {currentDetection && (
        <AnomalyExplanation
          detectionId={currentDetection.id}
          rowIndices={explanationRowIndices}
          onExplain={generateExplanation}
          onClose={() => setExplanationOpen(false)}
          isOpen={explanationOpen}
        />
      )}
    </div>
  )
}
