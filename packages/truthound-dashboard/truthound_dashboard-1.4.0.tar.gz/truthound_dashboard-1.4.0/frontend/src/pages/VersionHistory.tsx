/**
 * VersionHistory page
 *
 * Shows version history for a data source's validation results,
 * allowing users to view, compare, and track changes over time.
 */

import { useEffect, useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  ArrowLeft,
  GitBranch,
  History,
  RefreshCw,
  Loader2,
  Database,
  Tag,
  Info,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  getSource,
  listVersions,
  type Source,
  type VersionInfo,
} from '@/api/client'
import { useIntlayer } from '@/providers'
import { str } from '@/lib/intlayer-utils'
import { formatDate } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'
import { VersionCompare, VersionTimeline } from '@/components/versioning'

export default function VersionHistory() {
  const { id: sourceId } = useParams<{ id: string }>()
  const versioning = useIntlayer('versioning')
  const common = useIntlayer('common')
  const { toast } = useToast()

  const [source, setSource] = useState<Source | null>(null)
  const [versions, setVersions] = useState<VersionInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedVersion, setSelectedVersion] = useState<VersionInfo | null>(null)
  const [detailDialogOpen, setDetailDialogOpen] = useState(false)

  const loadData = useCallback(async () => {
    if (!sourceId) return
    try {
      setLoading(true)
      const [sourceData, versionsData] = await Promise.all([
        getSource(sourceId),
        listVersions(sourceId, { limit: 50 }),
      ])
      setSource(sourceData)
      setVersions(versionsData.data)
    } catch (error) {
      console.error('Load error:', error)
      toast({
        title: str(common.error),
        description: str(versioning.loadError),
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }, [sourceId, toast, common, versioning])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleSelectVersion = (version: VersionInfo) => {
    setSelectedVersion(version)
    setDetailDialogOpen(true)
  }

  const getStrategyLabel = (strategy: string) => {
    switch (strategy) {
      case 'incremental':
        return versioning.strategies.incremental
      case 'semantic':
        return versioning.strategies.semantic
      case 'timestamp':
        return versioning.strategies.timestamp
      case 'gitlike':
        return versioning.strategies.gitlike
      default:
        return strategy
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (!source) {
    return (
      <div className="flex flex-col items-center justify-center h-64">
        <Database className="h-12 w-12 text-muted-foreground mb-4" />
        <p className="text-muted-foreground">Source not found</p>
        <Button asChild className="mt-4">
          <Link to="/sources">Back to Sources</Link>
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link
        to={`/sources/${sourceId}`}
        className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        {versioning.backToSource}
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div className="flex items-center gap-4">
          <div className="h-14 w-14 rounded-lg bg-primary/10 flex items-center justify-center">
            <History className="h-7 w-7 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">{versioning.title}</h1>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="outline">{source.name}</Badge>
              <span className="text-muted-foreground">
                {versions.length} {versioning.version}
                {versions.length !== 1 ? 's' : ''}
              </span>
            </div>
          </div>
        </div>

        <Button variant="outline" onClick={loadData}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <GitBranch className="h-8 w-8 text-primary" />
              <div>
                <p className="text-2xl font-bold">{versions.length}</p>
                <p className="text-sm text-muted-foreground">Total Versions</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Tag className="h-8 w-8 text-green-600" />
              <div>
                <p className="text-2xl font-bold font-mono">
                  {versions[0]?.version_number || '-'}
                </p>
                <p className="text-sm text-muted-foreground">{versioning.latestVersion}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <History className="h-8 w-8 text-blue-600" />
              <div>
                <p className="text-lg font-medium">
                  {versions[0] ? formatDate(versions[0].created_at) : '-'}
                </p>
                <p className="text-sm text-muted-foreground">Last Updated</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="timeline" className="space-y-4">
        <TabsList>
          <TabsTrigger value="timeline" className="flex items-center gap-2">
            <History className="h-4 w-4" />
            {versioning.timeline}
          </TabsTrigger>
          <TabsTrigger value="compare" className="flex items-center gap-2">
            <RefreshCw className="h-4 w-4" />
            {versioning.compareVersions}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="timeline" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <GitBranch className="h-5 w-5" />
                {versioning.historyChain}
              </CardTitle>
              <CardDescription>{versioning.subtitle}</CardDescription>
            </CardHeader>
            <CardContent>
              <VersionTimeline
                versions={versions}
                onSelectVersion={handleSelectVersion}
                showValidationLink
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="compare">
          <VersionCompare versions={versions} sourceId={sourceId || ''} />
        </TabsContent>
      </Tabs>

      {/* Version Detail Dialog */}
      <Dialog open={detailDialogOpen} onOpenChange={setDetailDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Info className="h-5 w-5" />
              {versioning.version} {selectedVersion?.version_number}
            </DialogTitle>
            <DialogDescription>
              Version details and metadata
            </DialogDescription>
          </DialogHeader>
          {selectedVersion && (
            <div className="space-y-4">
              <div className="grid gap-3">
                <div className="flex justify-between items-center p-3 rounded-lg bg-muted/50">
                  <span className="text-sm text-muted-foreground">
                    {versioning.versionNumber}
                  </span>
                  <code className="font-mono font-bold">
                    {selectedVersion.version_number}
                  </code>
                </div>
                <div className="flex justify-between items-center p-3 rounded-lg bg-muted/50">
                  <span className="text-sm text-muted-foreground">
                    {versioning.strategy}
                  </span>
                  <Badge variant="outline">
                    {getStrategyLabel(selectedVersion.strategy)}
                  </Badge>
                </div>
                <div className="flex justify-between items-center p-3 rounded-lg bg-muted/50">
                  <span className="text-sm text-muted-foreground">
                    {versioning.createdAt}
                  </span>
                  <span>{formatDate(selectedVersion.created_at)}</span>
                </div>
                <div className="flex justify-between items-center p-3 rounded-lg bg-muted/50">
                  <span className="text-sm text-muted-foreground">
                    {versioning.validationId}
                  </span>
                  <Link
                    to={`/validations/${selectedVersion.validation_id}`}
                    className="text-primary hover:underline text-sm font-mono"
                  >
                    {selectedVersion.validation_id.slice(0, 8)}...
                  </Link>
                </div>
                <div className="flex justify-between items-center p-3 rounded-lg bg-muted/50">
                  <span className="text-sm text-muted-foreground">
                    {versioning.parentVersion}
                  </span>
                  <span className="text-sm">
                    {selectedVersion.parent_version_id ? (
                      <code className="font-mono">
                        {selectedVersion.parent_version_id.slice(0, 16)}...
                      </code>
                    ) : (
                      <span className="text-muted-foreground">
                        {versioning.noParent}
                      </span>
                    )}
                  </span>
                </div>
                {selectedVersion.content_hash && (
                  <div className="flex justify-between items-center p-3 rounded-lg bg-muted/50">
                    <span className="text-sm text-muted-foreground">
                      {versioning.contentHash}
                    </span>
                    <code className="font-mono text-sm">
                      {selectedVersion.content_hash}
                    </code>
                  </div>
                )}
              </div>

              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setDetailDialogOpen(false)}>
                  Close
                </Button>
                <Button asChild>
                  <Link to={`/validations/${selectedVersion.validation_id}`}>
                    {versioning.viewDetails}
                  </Link>
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
