/**
 * Column impact analysis component.
 *
 * Shows all downstream columns affected by changes to a selected column.
 */

import { useState, useMemo } from 'react'
import { useIntlayer } from 'react-intlayer'
import {
  AlertTriangle,
  CheckCircle,
  ChevronRight,
  Database,
  Columns,
  ArrowDownRight,
  Search,
  Table2,
  Layers,
} from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import type {
  ColumnImpactResult,
  AffectedColumn,
  ColumnImpactPath,
  ColumnTransformationType,
} from './column-lineage-types'

interface ColumnImpactAnalysisProps {
  result: ColumnImpactResult | null
  isLoading?: boolean
  onColumnSelect?: (nodeId: string, columnName: string) => void
  onHighlightPath?: (path: ColumnImpactPath[]) => void
  className?: string
}

// Transformation type colors
const transformationColors: Record<ColumnTransformationType, string> = {
  direct: 'bg-blue-500/20 text-blue-700 dark:text-blue-300 border-blue-500/30',
  derived: 'bg-purple-500/20 text-purple-700 dark:text-purple-300 border-purple-500/30',
  aggregated: 'bg-amber-500/20 text-amber-700 dark:text-amber-300 border-amber-500/30',
  filtered: 'bg-green-500/20 text-green-700 dark:text-green-300 border-green-500/30',
  joined: 'bg-pink-500/20 text-pink-700 dark:text-pink-300 border-pink-500/30',
  renamed: 'bg-cyan-500/20 text-cyan-700 dark:text-cyan-300 border-cyan-500/30',
  cast: 'bg-orange-500/20 text-orange-700 dark:text-orange-300 border-orange-500/30',
  computed: 'bg-indigo-500/20 text-indigo-700 dark:text-indigo-300 border-indigo-500/30',
}

export function ColumnImpactAnalysis({
  result,
  isLoading,
  onColumnSelect,
  onHighlightPath,
  className,
}: ColumnImpactAnalysisProps) {
  const t = useIntlayer('lineage')
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())

  // Group affected columns by node - use void to suppress unused warning
  void useMemo(() => {
    if (!result) return new Map<string, AffectedColumn[]>()

    const groups = new Map<string, AffectedColumn[]>()
    for (const col of result.affectedColumns) {
      const key = col.nodeId
      if (!groups.has(key)) {
        groups.set(key, [])
      }
      groups.get(key)!.push(col)
    }
    return groups
  }, [result])

  // Filter affected columns
  const filteredColumns = useMemo(() => {
    if (!result || !searchQuery) return result?.affectedColumns ?? []
    const query = searchQuery.toLowerCase()
    return result.affectedColumns.filter(
      (col) =>
        col.columnName.toLowerCase().includes(query) ||
        col.nodeName.toLowerCase().includes(query)
    )
  }, [result, searchQuery])

  // Group filtered columns by node
  const filteredGroupedByNode = useMemo(() => {
    const groups = new Map<string, AffectedColumn[]>()
    for (const col of filteredColumns) {
      const key = col.nodeId
      if (!groups.has(key)) {
        groups.set(key, [])
      }
      groups.get(key)!.push(col)
    }
    return groups
  }, [filteredColumns])

  const toggleNode = (nodeId: string) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev)
      if (next.has(nodeId)) {
        next.delete(nodeId)
      } else {
        next.add(nodeId)
      }
      return next
    })
  }

  if (isLoading) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center py-12">
          <div className="flex flex-col items-center gap-3">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
            <p className="text-muted-foreground">{t.columnLineage.analyzing}</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!result) {
    return (
      <Card className={className}>
        <CardContent className="flex flex-col items-center justify-center py-12 text-muted-foreground">
          <Columns className="h-12 w-12 opacity-50" />
          <p className="mt-4 text-center">{t.columnLineage.selectColumnToAnalyze}</p>
        </CardContent>
      </Card>
    )
  }

  const hasHighImpact = result.totalAffected > 10 || result.affectedTables > 3
  const hasCriticalImpact = result.totalAffected > 20 || result.affectedTables > 5

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-base">
              {t.columnLineage.impactAnalysis}
              {hasCriticalImpact ? (
                <AlertTriangle className="h-4 w-4 text-red-500" />
              ) : hasHighImpact ? (
                <AlertTriangle className="h-4 w-4 text-amber-500" />
              ) : (
                <CheckCircle className="h-4 w-4 text-green-500" />
              )}
            </CardTitle>
            <CardDescription>{t.columnLineage.impactDescription}</CardDescription>
          </div>
          <Badge
            variant={hasCriticalImpact ? 'destructive' : hasHighImpact ? 'default' : 'secondary'}
          >
            {result.totalAffected} {t.columnLineage.affected}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Source column info */}
        <div className="rounded-lg border p-3 bg-muted/30">
          <div className="flex items-center gap-2 mb-2">
            <Database className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">{result.sourceNodeName}</span>
          </div>
          <div className="flex items-center gap-2">
            <Columns className="h-4 w-4 text-blue-500" />
            <span className="font-mono font-medium text-blue-600 dark:text-blue-400">
              {result.sourceColumn}
            </span>
          </div>
        </div>

        {/* Impact stats */}
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-lg border p-3 text-center">
            <div className="flex items-center justify-center gap-2">
              <Columns className="h-4 w-4 text-muted-foreground" />
              <span className="text-2xl font-bold">{result.totalAffected}</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">{t.columnLineage.affectedColumns}</p>
          </div>
          <div className="rounded-lg border p-3 text-center">
            <div className="flex items-center justify-center gap-2">
              <Table2 className="h-4 w-4 text-muted-foreground" />
              <span className="text-2xl font-bold">{result.affectedTables}</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">{t.columnLineage.affectedTables}</p>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder={String(t.columnLineage.searchAffected)}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-8"
          />
        </div>

        {/* Affected columns grouped by node */}
        <div className="space-y-2 max-h-[400px] overflow-y-auto">
          {Array.from(filteredGroupedByNode.entries()).map(([nodeId, columns]) => {
            const isExpanded = expandedNodes.has(nodeId)
            const nodeName = columns[0]?.nodeName ?? nodeId

            return (
              <div key={nodeId} className="rounded-lg border overflow-hidden">
                <button
                  onClick={() => toggleNode(nodeId)}
                  className="flex w-full items-center justify-between p-3 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <ChevronRight
                      className={cn('h-4 w-4 transition-transform', isExpanded && 'rotate-90')}
                    />
                    <Database className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">{nodeName}</span>
                  </div>
                  <Badge variant="secondary" className="text-xs">
                    {columns.length} {t.columnLineage.columns}
                  </Badge>
                </button>

                {isExpanded && (
                  <div className="border-t divide-y">
                    {columns.map((col, idx) => (
                      <div
                        key={`${col.nodeId}-${col.columnName}-${idx}`}
                        className="flex items-center justify-between px-3 py-2 hover:bg-muted/30 cursor-pointer"
                        onClick={() => onColumnSelect?.(col.nodeId, col.columnName)}
                      >
                        <div className="flex items-center gap-2">
                          <ArrowDownRight className="h-3 w-3 text-muted-foreground" />
                          <span className="font-mono text-sm">{col.columnName}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge
                            variant="outline"
                            className={cn('text-xs', transformationColors[col.transformationType])}
                          >
                            {t.columnLineage.transformationTypes[col.transformationType]}
                          </Badge>
                          <Badge variant="secondary" className="text-xs">
                            {t.columnLineage.depth}: {col.depth}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Impact path visualization */}
        {result.impactPath.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Layers className="h-4 w-4" />
              {t.columnLineage.impactPath}
            </div>
            <div className="space-y-1">
              {result.impactPath.slice(0, 5).map((path, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 text-xs p-2 rounded-lg border bg-muted/20 cursor-pointer hover:bg-muted/40"
                  onClick={() => onHighlightPath?.([path])}
                >
                  <span className="text-muted-foreground">{path.fromNodeName}</span>
                  <span className="font-mono text-blue-600 dark:text-blue-400">
                    {path.fromColumn}
                  </span>
                  <ChevronRight className="h-3 w-3" />
                  <span className="text-muted-foreground">{path.toNodeName}</span>
                  <span className="font-mono text-green-600 dark:text-green-400">
                    {path.toColumn}
                  </span>
                </div>
              ))}
              {result.impactPath.length > 5 && (
                <p className="text-xs text-muted-foreground text-center py-2">
                  +{result.impactPath.length - 5} {t.columnLineage.morePaths}
                </p>
              )}
            </div>
          </div>
        )}

        {/* High impact warning */}
        {hasCriticalImpact && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-3 dark:border-red-800 dark:bg-red-950">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-red-600" />
              <p className="text-sm text-red-700 dark:text-red-300">
                {t.columnLineage.criticalImpactWarning}
              </p>
            </div>
          </div>
        )}
        {hasHighImpact && !hasCriticalImpact && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 dark:border-amber-800 dark:bg-amber-950">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-600" />
              <p className="text-sm text-amber-700 dark:text-amber-300">
                {t.columnLineage.highImpactWarning}
              </p>
            </div>
          </div>
        )}

        {/* Empty state */}
        {filteredColumns.length === 0 && searchQuery && (
          <div className="py-8 text-center text-muted-foreground">
            <p>{t.columnLineage.noMatchingColumns}</p>
          </div>
        )}
        {result.totalAffected === 0 && (
          <div className="py-8 text-center text-muted-foreground">
            <CheckCircle className="mx-auto h-8 w-8 text-green-500 opacity-50" />
            <p className="mt-2">{t.columnLineage.noDownstreamImpact}</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
