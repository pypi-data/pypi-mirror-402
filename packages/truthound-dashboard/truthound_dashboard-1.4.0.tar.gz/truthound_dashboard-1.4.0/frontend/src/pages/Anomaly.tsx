/**
 * Anomaly Detection Page.
 *
 * Provides ML-based anomaly detection interface for all data sources.
 * Supports multiple algorithms: Isolation Forest, LOF, One-Class SVM, DBSCAN, Statistical, Autoencoder.
 * Includes batch detection across multiple sources.
 */

import { useCallback, useEffect, useState } from 'react'
import { useIntlayer } from 'react-intlayer'
import { str } from '@/lib/intlayer-utils'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/hooks/use-toast'
import {
  Loader2,
  Database,
  Brain,
  AlertTriangle,
  TrendingUp,
  RefreshCw,
  Layers,
  History,
  GitCompare,
  Radio,
} from 'lucide-react'
import { AnomalyDetectionPanel } from '@/components/anomaly/AnomalyDetectionPanel'
import { BatchDetectionDialog } from '@/components/anomaly/BatchDetectionDialog'
import { BatchProgress } from '@/components/anomaly/BatchProgress'
import { BatchResults } from '@/components/anomaly/BatchResults'
import { AlgorithmComparison } from '@/components/anomaly/AlgorithmComparison'
import { StreamingDashboard } from '@/components/anomaly/StreamingDashboard'
import { RelatedAlerts, AutoTriggerConfigPanel } from '@/components/cross-alerts'
import type { Source, AnomalyDetection, BatchDetectionJob } from '@/api/client'
import {
  listSources,
  getLatestAnomalyDetection,
  getSourceSchema,
  listBatchDetections,
  getBatchDetection,
} from '@/api/client'

interface SourceWithLatestAnomaly extends Source {
  latestDetection?: AnomalyDetection | null
}

export default function Anomaly() {
  const t = useIntlayer('anomaly')
  const common = useIntlayer('common')
  const { toast } = useToast()

  // State
  const [sources, setSources] = useState<SourceWithLatestAnomaly[]>([])
  const [selectedSourceId, setSelectedSourceId] = useState<string>('')
  const [columns, setColumns] = useState<string[]>([])
  const [isLoadingSources, setIsLoadingSources] = useState(true)
  const [isLoadingColumns, setIsLoadingColumns] = useState(false)
  const [stats, setStats] = useState({
    totalSources: 0,
    sourcesWithAnomalies: 0,
    totalAnomalies: 0,
    latestRate: 0,
  })

  // Batch detection state
  const [activeTab, setActiveTab] = useState<string>('single')
  const [batchDialogOpen, setBatchDialogOpen] = useState(false)
  const [batchJobs, setBatchJobs] = useState<BatchDetectionJob[]>([])
  const [activeBatchId, setActiveBatchId] = useState<string | null>(null)
  const [selectedBatchJob, setSelectedBatchJob] = useState<BatchDetectionJob | null>(null)
  const [isLoadingBatchJobs, setIsLoadingBatchJobs] = useState(false)

  // Comparison state
  const [comparisonDialogOpen, setComparisonDialogOpen] = useState(false)

  // Load sources with their latest anomaly detection
  const loadSources = useCallback(async () => {
    setIsLoadingSources(true)
    try {
      const response = await listSources({ limit: 100 })
      const sourcesWithAnomalies: SourceWithLatestAnomaly[] = []

      // Fetch latest anomaly detection for each source
      for (const source of response.data) {
        try {
          const latest = await getLatestAnomalyDetection(source.id)
          sourcesWithAnomalies.push({ ...source, latestDetection: latest })
        } catch {
          sourcesWithAnomalies.push({ ...source, latestDetection: null })
        }
      }

      setSources(sourcesWithAnomalies)

      // Calculate stats
      const withAnomalies = sourcesWithAnomalies.filter(
        (s) => s.latestDetection && (s.latestDetection.anomaly_count ?? 0) > 0
      )
      const totalAnomalies = sourcesWithAnomalies.reduce(
        (sum, s) => sum + (s.latestDetection?.anomaly_count ?? 0),
        0
      )
      const avgRate =
        sourcesWithAnomalies.length > 0
          ? sourcesWithAnomalies.reduce(
              (sum, s) => sum + (s.latestDetection?.anomaly_rate ?? 0),
              0
            ) / sourcesWithAnomalies.filter((s) => s.latestDetection).length
          : 0

      setStats({
        totalSources: sourcesWithAnomalies.length,
        sourcesWithAnomalies: withAnomalies.length,
        totalAnomalies,
        latestRate: avgRate,
      })

      // Auto-select first source if available
      if (sourcesWithAnomalies.length > 0 && !selectedSourceId) {
        setSelectedSourceId(sourcesWithAnomalies[0].id)
      }
    } catch (error) {
      toast({
        title: str(common.error),
        description: 'Failed to load data sources',
        variant: 'destructive',
      })
    } finally {
      setIsLoadingSources(false)
    }
  }, [toast, common, selectedSourceId])

  useEffect(() => {
    loadSources()
    loadBatchJobs()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Load batch jobs
  const loadBatchJobs = useCallback(async () => {
    setIsLoadingBatchJobs(true)
    try {
      const response = await listBatchDetections({ limit: 20 })
      setBatchJobs(response.data)

      // Check for running jobs
      const runningJob = response.data.find(
        (j) => j.status === 'running' || j.status === 'pending'
      )
      if (runningJob) {
        setActiveBatchId(runningJob.id)
      }
    } catch (error) {
      // Silently fail - batch jobs are optional
    } finally {
      setIsLoadingBatchJobs(false)
    }
  }, [])

  // Handle batch job creation
  const handleBatchJobCreated = useCallback(
    (jobId: string) => {
      setActiveBatchId(jobId)
      setActiveTab('batch')
      loadBatchJobs()
    },
    [loadBatchJobs]
  )

  // Handle batch job completion
  const handleBatchComplete = useCallback(
    (job: BatchDetectionJob) => {
      setSelectedBatchJob(job)
      setActiveBatchId(null)
      loadBatchJobs()
      loadSources() // Refresh sources to get updated anomaly data
    },
    [loadBatchJobs, loadSources]
  )

  // View batch job results
  const handleViewBatchJob = useCallback(async (jobId: string) => {
    try {
      const job = await getBatchDetection(jobId)
      setSelectedBatchJob(job)
      if (job.status === 'running' || job.status === 'pending') {
        setActiveBatchId(jobId)
      }
    } catch (error) {
      toast({
        title: str(common.error),
        description: 'Failed to load batch job',
        variant: 'destructive',
      })
    }
  }, [toast, common])

  // Load columns when source changes
  useEffect(() => {
    if (!selectedSourceId) {
      setColumns([])
      return
    }

    const loadColumns = async () => {
      setIsLoadingColumns(true)
      try {
        const schema = await getSourceSchema(selectedSourceId)
        // Schema.columns is string[] - use all columns since we can't filter by dtype
        setColumns(schema?.columns ?? [])
      } catch {
        setColumns([])
      } finally {
        setIsLoadingColumns(false)
      }
    }

    loadColumns()
  }, [selectedSourceId])

  const selectedSource = sources.find((s) => s.id === selectedSourceId)

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t.title}</h1>
          <p className="text-muted-foreground">{t.subtitle}</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => setComparisonDialogOpen(true)}
            disabled={!selectedSourceId}
          >
            <GitCompare className="mr-2 h-4 w-4" />
            {t.comparison?.compareAlgorithms ?? 'Compare Algorithms'}
          </Button>
          <Button variant="outline" onClick={() => setBatchDialogOpen(true)}>
            <Layers className="mr-2 h-4 w-4" />
            {t.batch.runBatch}
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              loadSources()
              loadBatchJobs()
            }}
            disabled={isLoadingSources}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${isLoadingSources ? 'animate-spin' : ''}`} />
            {common.refresh}
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>{t.columnsAnalyzed}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Database className="h-5 w-5 text-muted-foreground" />
              <span className="text-2xl font-bold">{stats.totalSources}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>{t.anomaliesFound}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-orange-500" />
              <span className="text-2xl font-bold text-orange-500">{stats.totalAnomalies}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>{t.anomalyRate}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-muted-foreground" />
              <span className="text-2xl font-bold">
                {(stats.latestRate * 100).toFixed(2)}%
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Sources with Anomalies</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-muted-foreground" />
              <span className="text-2xl font-bold">
                {stats.sourcesWithAnomalies} / {stats.totalSources}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="single" className="gap-2">
            <Database className="h-4 w-4" />
            {t.batch.singleSource}
          </TabsTrigger>
          <TabsTrigger value="streaming" className="gap-2">
            <Radio className="h-4 w-4" />
            {t.streaming?.tab ?? 'Streaming'}
          </TabsTrigger>
          <TabsTrigger value="batch" className="gap-2">
            <Layers className="h-4 w-4" />
            {t.batch.batchDetection}
            {batchJobs.some((j) => j.status === 'running' || j.status === 'pending') && (
              <Badge variant="default" className="ml-1 h-5 px-1.5">
                <Loader2 className="h-3 w-3 animate-spin" />
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="history" className="gap-2">
            <History className="h-4 w-4" />
            {t.batch.batchHistory}
          </TabsTrigger>
        </TabsList>

        {/* Single Source Detection */}
        <TabsContent value="single" className="space-y-4">
          {/* Source Selection */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                Select Data Source
              </CardTitle>
              <CardDescription>
                Choose a data source to run anomaly detection
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoadingSources ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : sources.length === 0 ? (
                <div className="flex flex-col items-center justify-center gap-2 py-8">
                  <Database className="h-8 w-8 text-muted-foreground" />
                  <p className="text-muted-foreground">No data sources available</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <Select value={selectedSourceId} onValueChange={setSelectedSourceId}>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select a data source" />
                    </SelectTrigger>
                    <SelectContent>
                      {sources.map((source) => (
                        <SelectItem key={source.id} value={source.id}>
                          <div className="flex items-center gap-2">
                            <span>{source.name}</span>
                            {source.latestDetection && (source.latestDetection.anomaly_count ?? 0) > 0 && (
                              <Badge variant="outline" className="text-orange-500 border-orange-500">
                                {source.latestDetection.anomaly_count} anomalies
                              </Badge>
                            )}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  {selectedSource && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <span>Type: {selectedSource.type}</span>
                      <span>-</span>
                      <span>{columns.length} numeric columns available</span>
                      {selectedSource.latestDetection && (
                        <>
                          <span>-</span>
                          <span>
                            Last detection:{' '}
                            {new Date(selectedSource.latestDetection.created_at).toLocaleDateString()}
                          </span>
                        </>
                      )}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Anomaly Detection Panel */}
          {selectedSourceId && (
            <>
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <Brain className="h-5 w-5" />
                        {t.title}
                      </CardTitle>
                      <CardDescription>{t.subtitle}</CardDescription>
                    </div>
                    <AutoTriggerConfigPanel sourceId={selectedSourceId} />
                  </div>
                </CardHeader>
                <CardContent>
                  {isLoadingColumns ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                    </div>
                  ) : (
                    <AnomalyDetectionPanel sourceId={selectedSourceId} columns={columns} />
                  )}
                </CardContent>
              </Card>

              {/* Related Drift Alerts */}
              <RelatedAlerts
                sourceId={selectedSourceId}
                alertType="anomaly"
                maxItems={5}
              />
            </>
          )}
        </TabsContent>

        {/* Streaming Anomaly Detection */}
        <TabsContent value="streaming" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Radio className="h-5 w-5" />
                {t.streaming?.title ?? 'Real-time Streaming Detection'}
              </CardTitle>
              <CardDescription>
                {t.streaming?.subtitle ?? 'Monitor data streams in real-time and detect anomalies as they occur'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <StreamingDashboard
                sourceId={selectedSourceId || undefined}
                columns={columns}
              />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Batch Detection */}
        <TabsContent value="batch" className="space-y-4">
          {/* Active Batch Job Progress */}
          {activeBatchId && (
            <BatchProgress
              batchId={activeBatchId}
              onComplete={handleBatchComplete}
            />
          )}

          {/* Selected Batch Results */}
          {selectedBatchJob && !activeBatchId && (
            <BatchResults
              job={selectedBatchJob}
              onViewDetails={(sourceId, _detectionId) => {
                setSelectedSourceId(sourceId)
                setActiveTab('single')
              }}
            />
          )}

          {/* Empty state */}
          {!activeBatchId && !selectedBatchJob && (
            <Card>
              <CardContent className="flex flex-col items-center justify-center gap-4 py-12">
                <Layers className="h-12 w-12 text-muted-foreground" />
                <div className="text-center">
                  <h3 className="font-semibold">{t.batch.noBatchJobs}</h3>
                  <p className="text-sm text-muted-foreground">{t.batch.noBatchJobsDesc}</p>
                </div>
                <Button onClick={() => setBatchDialogOpen(true)}>
                  <Layers className="mr-2 h-4 w-4" />
                  {t.batch.runBatch}
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Batch History */}
        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="h-5 w-5" />
                {t.batch.batchHistory}
              </CardTitle>
              <CardDescription>{t.batch.batchHistoryDesc}</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoadingBatchJobs ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : batchJobs.length === 0 ? (
                <div className="flex flex-col items-center justify-center gap-2 py-8">
                  <History className="h-8 w-8 text-muted-foreground" />
                  <p className="text-muted-foreground">{t.batch.noHistory}</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {batchJobs.map((job) => (
                    <div
                      key={job.id}
                      className="flex cursor-pointer items-center justify-between rounded-md border p-3 hover:bg-muted"
                      onClick={() => handleViewBatchJob(job.id)}
                    >
                      <div className="flex items-center gap-3">
                        {job.status === 'running' || job.status === 'pending' ? (
                          <Loader2 className="h-5 w-5 animate-spin text-primary" />
                        ) : job.status === 'completed' ? (
                          <Badge variant="default">
                            {t.batch.status.completed}
                          </Badge>
                        ) : job.status === 'partial' ? (
                          <Badge variant="outline" className="border-orange-500 text-orange-500">
                            {t.batch.status.partial}
                          </Badge>
                        ) : (
                          <Badge variant="destructive">
                            {t.batch.status[job.status as keyof typeof t.batch.status] || job.status}
                          </Badge>
                        )}
                        <div>
                          <p className="font-medium">{job.name || t.batch.untitledJob}</p>
                          <p className="text-sm text-muted-foreground">
                            {job.total_sources} sources - {new Date(job.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-mono text-orange-500">
                          {job.total_anomalies.toLocaleString()} {str(t.anomaliesFound)}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {(job.average_anomaly_rate * 100).toFixed(2)}% avg rate
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Batch Detection Dialog */}
      <BatchDetectionDialog
        open={batchDialogOpen}
        onOpenChange={setBatchDialogOpen}
        onJobCreated={handleBatchJobCreated}
      />

      {/* Algorithm Comparison Dialog */}
      {selectedSourceId && (
        <AlgorithmComparison
          sourceId={selectedSourceId}
          isOpen={comparisonDialogOpen}
          onClose={() => setComparisonDialogOpen(false)}
          columns={columns}
        />
      )}
    </div>
  )
}
