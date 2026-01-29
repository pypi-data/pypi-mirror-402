/**
 * Privacy & Compliance Page.
 *
 * Provides interface for PII detection (th.scan) and data masking (th.mask).
 * Supports GDPR, CCPA, LGPD, HIPAA compliance workflows.
 */

import { useCallback, useEffect, useState } from 'react'
import { useSafeIntlayer } from '@/hooks/useSafeIntlayer'
import { str } from '@/lib/intlayer-utils'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/hooks/use-toast'
import {
  Loader2,
  Database,
  Shield,
  Eye,
  Lock,
  RefreshCw,
  AlertTriangle,
} from 'lucide-react'
import {
  PIIScanPanel,
  MaskingPanel,
  ScanHistoryList,
  PrivacyStats,
} from '@/components/privacy'
import type { Source, PIIScan, DataMaskListItem } from '@/api/client'
import {
  listSources,
  listSourcePIIScans,
  listSourceDataMasks,
  getLatestPIIScan,
  getSourceSchema,
} from '@/api/client'

interface SourceWithPrivacyInfo extends Source {
  latestScan?: PIIScan | null
  piiColumns?: string[]
}

export default function Privacy() {
  const t = useSafeIntlayer('privacy')
  const common = useSafeIntlayer('common')
  const { toast } = useToast()

  // State
  const [sources, setSources] = useState<SourceWithPrivacyInfo[]>([])
  const [selectedSourceId, setSelectedSourceId] = useState<string>('')
  const [columns, setColumns] = useState<string[]>([])
  const [isLoadingSources, setIsLoadingSources] = useState(true)
  const [isLoadingColumns, setIsLoadingColumns] = useState(false)
  const [scanHistory, setScanHistory] = useState<PIIScan[]>([])
  const [maskHistory, setMaskHistory] = useState<DataMaskListItem[]>([])
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  const [activeTab, setActiveTab] = useState('scan')
  const [stats, setStats] = useState({
    totalScans: 0,
    totalFindings: 0,
    columnsProtected: 0,
    complianceScore: 100,
  })

  // Load sources with their latest PII scan info
  const loadSources = useCallback(async () => {
    setIsLoadingSources(true)
    try {
      const response = await listSources({ limit: 100 })
      const sourcesWithInfo: SourceWithPrivacyInfo[] = []

      for (const source of response.data) {
        try {
          const latestScan = await getLatestPIIScan(source.id)
          const piiColumns = latestScan?.findings?.map((f) => f.column) ?? []
          sourcesWithInfo.push({ ...source, latestScan, piiColumns })
        } catch {
          sourcesWithInfo.push({ ...source, latestScan: null, piiColumns: [] })
        }
      }

      setSources(sourcesWithInfo)

      // Calculate stats
      const totalFindings = sourcesWithInfo.reduce(
        (sum, s) => sum + (s.latestScan?.findings?.length ?? 0),
        0
      )
      const sourcesWithPII = sourcesWithInfo.filter(
        (s) => s.latestScan && s.latestScan.columns_with_pii > 0
      )
      const complianceScore =
        sourcesWithInfo.length > 0
          ? Math.round(
              ((sourcesWithInfo.length - sourcesWithPII.length) / sourcesWithInfo.length) * 100
            )
          : 100

      setStats((prev) => ({
        ...prev,
        totalFindings,
        complianceScore,
      }))

      // Auto-select first source
      if (sourcesWithInfo.length > 0 && !selectedSourceId) {
        setSelectedSourceId(sourcesWithInfo[0].id)
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
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

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
        // Schema.columns is string[] - column names directly
        setColumns(schema?.columns ?? [])
      } catch {
        setColumns([])
      } finally {
        setIsLoadingColumns(false)
      }
    }

    loadColumns()
  }, [selectedSourceId])

  // Load history when source changes
  const loadHistory = useCallback(async () => {
    if (!selectedSourceId) return

    setIsLoadingHistory(true)
    try {
      const [scansResponse, masksResponse] = await Promise.all([
        listSourcePIIScans(selectedSourceId, { limit: 10 }),
        listSourceDataMasks(selectedSourceId, { limit: 10 }),
      ])

      setScanHistory(scansResponse.data)
      setMaskHistory(masksResponse.data)

      // Update stats
      setStats((prev) => ({
        ...prev,
        totalScans: scansResponse.data.length,
        columnsProtected: masksResponse.data.reduce((sum, m) => sum + m.columns_masked, 0),
      }))
    } catch {
      // Silently fail for history
    } finally {
      setIsLoadingHistory(false)
    }
  }, [selectedSourceId])

  useEffect(() => {
    loadHistory()
  }, [loadHistory])

  const selectedSource = sources.find((s) => s.id === selectedSourceId)
  const piiColumns = selectedSource?.piiColumns ?? []

  const handleScanComplete = () => {
    loadHistory()
    loadSources()
  }

  const handleMaskComplete = () => {
    loadHistory()
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t.title}</h1>
          <p className="text-muted-foreground">{t.subtitle}</p>
        </div>
        <Button variant="outline" onClick={loadSources} disabled={isLoadingSources}>
          <RefreshCw className={`mr-2 h-4 w-4 ${isLoadingSources ? 'animate-spin' : ''}`} />
          {common.refresh}
        </Button>
      </div>

      {/* Stats Overview */}
      <PrivacyStats
        totalScans={stats.totalScans}
        totalFindings={stats.totalFindings}
        columnsProtected={stats.columnsProtected}
        complianceScore={stats.complianceScore}
      />

      {/* Source Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            {t.config.selectSource}
          </CardTitle>
          <CardDescription>Choose a data source to scan or mask</CardDescription>
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
                        {source.latestScan && source.latestScan.columns_with_pii > 0 ? (
                          <Badge variant="outline" className="text-orange-500 border-orange-500/20">
                            <AlertTriangle className="mr-1 h-3 w-3" />
                            {source.latestScan.columns_with_pii} PII columns
                          </Badge>
                        ) : source.latestScan ? (
                          <Badge variant="outline" className="text-green-500 border-green-500/20">
                            <Shield className="mr-1 h-3 w-3" />
                            No PII
                          </Badge>
                        ) : null}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {selectedSource && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <span>Type: {selectedSource.type}</span>
                  <span>•</span>
                  <span>{columns.length} columns</span>
                  {piiColumns.length > 0 && (
                    <>
                      <span>•</span>
                      <span className="text-orange-500">{piiColumns.length} with PII</span>
                    </>
                  )}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Main Content Tabs */}
      {selectedSourceId && (
        <Card>
          <CardHeader>
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList>
                <TabsTrigger value="scan" className="gap-2">
                  <Eye className="h-4 w-4" />
                  {t.tabs.scan}
                </TabsTrigger>
                <TabsTrigger value="mask" className="gap-2">
                  <Lock className="h-4 w-4" />
                  {t.tabs.mask}
                </TabsTrigger>
                <TabsTrigger value="history" className="gap-2">
                  {t.tabs.history}
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </CardHeader>
          <CardContent>
            {isLoadingColumns ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsContent value="scan" className="mt-0">
                  <PIIScanPanel
                    sourceId={selectedSourceId}
                    columns={columns}
                    onScanComplete={handleScanComplete}
                  />
                </TabsContent>

                <TabsContent value="mask" className="mt-0">
                  <MaskingPanel
                    sourceId={selectedSourceId}
                    columns={columns}
                    suggestedColumns={piiColumns}
                    onMaskComplete={handleMaskComplete}
                  />
                </TabsContent>

                <TabsContent value="history" className="mt-0">
                  <ScanHistoryList
                    scans={scanHistory}
                    masks={maskHistory}
                    isLoading={isLoadingHistory}
                  />
                </TabsContent>
              </Tabs>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
