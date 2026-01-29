/**
 * Schema Evolution Page
 *
 * Tracks schema changes over time, displays version history,
 * and highlights breaking vs non-breaking changes.
 */

import { useEffect, useState, useCallback } from 'react'
import { useIntlayer } from 'react-intlayer'
import {
  GitBranch,
  History,
  AlertTriangle,
  CheckCircle2,
  Clock,
  RefreshCw,
  ChevronRight,
  Plus,
  Minus,
  ArrowRight,
  Database,
  AlertCircle,
} from 'lucide-react'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import { Separator } from '@/components/ui/separator'
import { useToast } from '@/hooks/use-toast'
import { str } from '@/lib/intlayer-utils'
import {
  listSources,
  listSchemaVersions,
  listSchemaChanges,
  getSchemaEvolutionSummary,
  detectSchemaChanges,
  type Source,
  type SchemaVersionSummary,
  type SchemaChangeResponse,
  type SchemaEvolutionSummary,
  type SchemaChangeType,
  type SchemaChangeSeverity,
} from '@/api/client'

// Change type icons and colors
const CHANGE_TYPE_CONFIG: Record<
  SchemaChangeType,
  { icon: typeof Plus; color: string; bgColor: string }
> = {
  column_added: { icon: Plus, color: 'text-green-500', bgColor: 'bg-green-500/10' },
  column_removed: { icon: Minus, color: 'text-red-500', bgColor: 'bg-red-500/10' },
  type_changed: { icon: ArrowRight, color: 'text-amber-500', bgColor: 'bg-amber-500/10' },
  nullable_changed: { icon: ArrowRight, color: 'text-blue-500', bgColor: 'bg-blue-500/10' },
  constraint_changed: { icon: ArrowRight, color: 'text-purple-500', bgColor: 'bg-purple-500/10' },
  column_renamed: { icon: ArrowRight, color: 'text-cyan-500', bgColor: 'bg-cyan-500/10' },
}

// Severity badge config
const SEVERITY_CONFIG: Record<SchemaChangeSeverity, { color: string; label: string }> = {
  breaking: { color: 'bg-red-500/10 text-red-500 border-red-500/20', label: 'Breaking' },
  warning: { color: 'bg-amber-500/10 text-amber-500 border-amber-500/20', label: 'Warning' },
  non_breaking: { color: 'bg-green-500/10 text-green-500 border-green-500/20', label: 'Safe' },
}

// Stats Card
function StatsCard({
  title,
  value,
  icon: Icon,
  variant = 'default',
}: {
  title: string
  value: number | string
  icon: typeof History
  variant?: 'default' | 'success' | 'warning' | 'danger'
}) {
  const variantStyles = {
    default: 'text-primary',
    success: 'text-green-500',
    warning: 'text-amber-500',
    danger: 'text-red-500',
  }

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className={`text-2xl font-bold ${variantStyles[variant]}`}>{value}</p>
          </div>
          <Icon className={`h-8 w-8 ${variantStyles[variant]} opacity-50`} />
        </div>
      </CardContent>
    </Card>
  )
}

// Change Row Component
function ChangeRow({ change }: { change: SchemaChangeResponse }) {
  const t = useIntlayer('schemaEvolution')
  const config = CHANGE_TYPE_CONFIG[change.change_type] || CHANGE_TYPE_CONFIG.type_changed
  const severityConfig = SEVERITY_CONFIG[change.severity] || SEVERITY_CONFIG.non_breaking
  const Icon = config.icon

  // Get localized change type label
  const getChangeTypeLabel = (type: SchemaChangeType) => {
    const labels: Record<SchemaChangeType, string> = {
      column_added: str(t.columnAdded),
      column_removed: str(t.columnRemoved),
      type_changed: str(t.typeChanged),
      nullable_changed: str(t.nullableChanged),
      constraint_changed: str(t.constraintChanged),
      column_renamed: str(t.columnRenamed),
    }
    return labels[type] || type
  }

  return (
    <TableRow>
      <TableCell>
        <div className="flex items-center gap-2">
          <div className={`p-1 rounded ${config.bgColor}`}>
            <Icon className={`h-4 w-4 ${config.color}`} />
          </div>
          <span className="font-medium">{change.column_name}</span>
        </div>
      </TableCell>
      <TableCell>
        <Badge variant="outline" className={config.bgColor}>
          {getChangeTypeLabel(change.change_type)}
        </Badge>
      </TableCell>
      <TableCell className="text-muted-foreground font-mono text-sm">
        {change.old_value || '-'}
      </TableCell>
      <TableCell className="text-muted-foreground font-mono text-sm">
        {change.new_value || '-'}
      </TableCell>
      <TableCell>
        <Badge variant="outline" className={severityConfig.color}>
          {severityConfig.label}
        </Badge>
      </TableCell>
      <TableCell className="text-sm text-muted-foreground max-w-xs truncate">
        {change.details?.reason || change.description || '-'}
      </TableCell>
    </TableRow>
  )
}

// Version Card
function VersionCard({
  version,
  isLatest,
  changes,
}: {
  version: SchemaVersionSummary
  isLatest: boolean
  changes: SchemaChangeResponse[]
}) {
  const t = useIntlayer('schemaEvolution')
  const versionChanges = changes.filter((c) => c.to_version_id === version.id)
  const breakingCount = versionChanges.filter((c) => c.severity === 'breaking').length

  return (
    <AccordionItem value={version.id}>
      <AccordionTrigger className="hover:no-underline">
        <div className="flex items-center justify-between w-full pr-4">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <GitBranch className="h-4 w-4 text-muted-foreground" />
              <span className="font-medium">
                v{version.version_number}
              </span>
              {isLatest && (
                <Badge variant="outline" className="bg-primary/10 text-primary">
                  {str(t.latest)}
                </Badge>
              )}
            </div>
            <Separator orientation="vertical" className="h-4" />
            <span className="text-sm text-muted-foreground">
              {version.column_count} {str(t.columns)}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {versionChanges.length > 0 && (
              <>
                <Badge variant="outline">
                  {versionChanges.length} changes
                </Badge>
                {breakingCount > 0 && (
                  <Badge variant="outline" className="bg-red-500/10 text-red-500">
                    {breakingCount} breaking
                  </Badge>
                )}
              </>
            )}
            <span className="text-xs text-muted-foreground">
              {new Date(version.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>
      </AccordionTrigger>
      <AccordionContent>
        <div className="p-4 space-y-4">
          {versionChanges.length === 0 ? (
            <p className="text-sm text-muted-foreground">{str(t.noChangesDetected)}</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{str(t.columnName)}</TableHead>
                  <TableHead>{str(t.type)}</TableHead>
                  <TableHead>{str(t.oldValue)}</TableHead>
                  <TableHead>{str(t.newValue)}</TableHead>
                  <TableHead>{str(t.compatibility)}</TableHead>
                  <TableHead>{str(t.reason)}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {versionChanges.map((change) => (
                  <ChangeRow key={change.id} change={change} />
                ))}
              </TableBody>
            </Table>
          )}
        </div>
      </AccordionContent>
    </AccordionItem>
  )
}

export default function SchemaEvolution() {
  const t = useIntlayer('schemaEvolution')
  const common = useIntlayer('common')
  const { toast } = useToast()

  // State
  const [sources, setSources] = useState<Source[]>([])
  const [selectedSourceId, setSelectedSourceId] = useState<string | null>(null)
  const [summary, setSummary] = useState<SchemaEvolutionSummary | null>(null)
  const [versions, setVersions] = useState<SchemaVersionSummary[]>([])
  const [changes, setChanges] = useState<SchemaChangeResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [detecting, setDetecting] = useState(false)

  // Fetch sources on mount
  useEffect(() => {
    listSources()
      .then((response) => {
        setSources(response.data || [])
        if (response.data?.length > 0) {
          setSelectedSourceId(response.data[0].id)
        }
      })
      .catch(() => {
        toast({ title: str(t.fetchError), variant: 'destructive' })
      })
      .finally(() => setLoading(false))
  }, [toast, t.fetchError])

  // Fetch evolution data when source changes
  const fetchEvolutionData = useCallback(async () => {
    if (!selectedSourceId) return

    setLoading(true)
    try {
      const [summaryRes, versionsRes, changesRes] = await Promise.all([
        getSchemaEvolutionSummary(selectedSourceId),
        listSchemaVersions(selectedSourceId, { limit: 50 }),
        listSchemaChanges(selectedSourceId, { limit: 100 }),
      ])
      setSummary(summaryRes)
      setVersions(versionsRes.versions || [])
      setChanges(changesRes.changes || [])
    } catch (error) {
      toast({ title: str(t.fetchError), variant: 'destructive' })
    } finally {
      setLoading(false)
    }
  }, [selectedSourceId, toast, t.fetchError])

  useEffect(() => {
    fetchEvolutionData()
  }, [fetchEvolutionData])

  // Detect changes
  const handleDetectChanges = async () => {
    if (!selectedSourceId) return

    setDetecting(true)
    try {
      await detectSchemaChanges(selectedSourceId)
      await fetchEvolutionData()
      toast({ title: 'Changes detected successfully' })
    } catch (error) {
      toast({ title: 'Failed to detect changes', variant: 'destructive' })
    } finally {
      setDetecting(false)
    }
  }

  const selectedSource = sources.find((s) => s.id === selectedSourceId)

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{str(t.title)}</h1>
          <p className="text-muted-foreground">{str(t.description)}</p>
        </div>
        <div className="flex items-center gap-2">
          <Select
            value={selectedSourceId || ''}
            onValueChange={setSelectedSourceId}
            disabled={loading}
          >
            <SelectTrigger className="w-64">
              <SelectValue placeholder={str(t.selectSource)} />
            </SelectTrigger>
            <SelectContent>
              {sources.map((source) => (
                <SelectItem key={source.id} value={source.id}>
                  <div className="flex items-center gap-2">
                    <Database className="h-4 w-4" />
                    {source.name}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            onClick={handleDetectChanges}
            disabled={detecting || !selectedSourceId}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${detecting ? 'animate-spin' : ''}`} />
            {detecting ? str(t.detecting) : str(t.detectChanges)}
          </Button>
        </div>
      </div>

      {sources.length === 0 && !loading ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Database className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">{str(t.noSources)}</p>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatsCard
              title={str(t.currentVersion)}
              value={summary?.current_version || 0}
              icon={GitBranch}
            />
            <StatsCard
              title={str(t.totalVersions)}
              value={summary?.total_versions || 0}
              icon={History}
            />
            <StatsCard
              title={str(t.totalChanges)}
              value={summary?.total_changes || 0}
              icon={ArrowRight}
              variant="warning"
            />
            <StatsCard
              title={str(t.breakingChanges)}
              value={summary?.breaking_changes || 0}
              icon={AlertTriangle}
              variant={summary?.breaking_changes ? 'danger' : 'success'}
            />
          </div>

          {/* Version History */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="h-5 w-5" />
                {str(t.versionHistory)}
              </CardTitle>
              <CardDescription>
                {selectedSource
                  ? `Schema evolution history for ${selectedSource.name}`
                  : str(t.loadingHistory)}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {versions.length === 0 ? (
                <div className="text-center py-8">
                  <GitBranch className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">{str(t.noVersionsFound)}</p>
                </div>
              ) : (
                <Accordion type="single" collapsible className="w-full">
                  {versions.map((version, index) => (
                    <VersionCard
                      key={version.id}
                      version={version}
                      isLatest={index === 0}
                      changes={changes}
                    />
                  ))}
                </Accordion>
              )}
            </CardContent>
          </Card>

          {/* Recent Changes Summary */}
          {changes.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertCircle className="h-5 w-5" />
                  {str(t.summary)}
                </CardTitle>
                <CardDescription>
                  Recent schema changes across all versions
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-4 rounded-lg bg-green-500/10">
                    <p className="text-2xl font-bold text-green-500">
                      {changes.filter((c) => c.change_type === 'column_added').length}
                    </p>
                    <p className="text-sm text-muted-foreground">{str(t.columnAdded)}</p>
                  </div>
                  <div className="text-center p-4 rounded-lg bg-red-500/10">
                    <p className="text-2xl font-bold text-red-500">
                      {changes.filter((c) => c.change_type === 'column_removed').length}
                    </p>
                    <p className="text-sm text-muted-foreground">{str(t.columnRemoved)}</p>
                  </div>
                  <div className="text-center p-4 rounded-lg bg-amber-500/10">
                    <p className="text-2xl font-bold text-amber-500">
                      {changes.filter((c) => c.change_type === 'type_changed').length}
                    </p>
                    <p className="text-sm text-muted-foreground">{str(t.typeChanged)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
