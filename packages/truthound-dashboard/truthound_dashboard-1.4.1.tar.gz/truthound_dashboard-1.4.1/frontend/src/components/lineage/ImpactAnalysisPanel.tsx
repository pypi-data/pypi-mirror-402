/**
 * Panel showing impact analysis results for a selected node.
 */

import { useIntlayer } from 'react-intlayer'
import { ArrowUp, ArrowDown, AlertTriangle, CheckCircle } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import type { ImpactAnalysisResponse, LineageNode as LineageNodeType } from '@/api/client'

interface ImpactAnalysisPanelProps {
  analysis: ImpactAnalysisResponse | null
  isLoading?: boolean
}

export function ImpactAnalysisPanel({ analysis, isLoading }: ImpactAnalysisPanelProps) {
  const t = useIntlayer('lineage')

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <p className="text-muted-foreground">Analyzing impact...</p>
        </CardContent>
      </Card>
    )
  }

  if (!analysis) {
    return null
  }

  const totalAffected = analysis.upstream_count + analysis.downstream_count
  const hasHighImpact = totalAffected > 5

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              {t.impactAnalysis}
              {hasHighImpact ? (
                <AlertTriangle className="h-4 w-4 text-amber-500" />
              ) : (
                <CheckCircle className="h-4 w-4 text-green-500" />
              )}
            </CardTitle>
            <CardDescription>{t.impactDescription}</CardDescription>
          </div>
          <Badge variant={hasHighImpact ? 'destructive' : 'secondary'}>
            {totalAffected} affected
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Target node */}
        <div className="rounded-lg border p-3">
          <p className="text-sm font-medium">{analysis.node_name}</p>
          <p className="text-xs text-muted-foreground">
            Analysis depth: {analysis.depth} levels
          </p>
        </div>

        {/* Upstream */}
        <div>
          <div className="mb-2 flex items-center gap-2">
            <ArrowUp className="h-4 w-4 text-blue-500" />
            <span className="text-sm font-medium">
              {t.affectedUpstream} ({analysis.upstream_count})
            </span>
          </div>
          {analysis.upstream.length === 0 ? (
            <p className="text-sm text-muted-foreground">No upstream dependencies</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {analysis.upstream.map((node) => (
                <NodeBadge key={node.id} node={node} />
              ))}
            </div>
          )}
        </div>

        {/* Downstream */}
        <div>
          <div className="mb-2 flex items-center gap-2">
            <ArrowDown className="h-4 w-4 text-green-500" />
            <span className="text-sm font-medium">
              {t.affectedDownstream} ({analysis.downstream_count})
            </span>
          </div>
          {analysis.downstream.length === 0 ? (
            <p className="text-sm text-muted-foreground">No downstream dependents</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {analysis.downstream.map((node) => (
                <NodeBadge key={node.id} node={node} />
              ))}
            </div>
          )}
        </div>

        {/* Warning for high impact */}
        {hasHighImpact && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 dark:border-amber-800 dark:bg-amber-950">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-600" />
              <p className="text-sm text-amber-700 dark:text-amber-300">
                Changes to this node may affect {totalAffected} other nodes.
                Review dependencies before making changes.
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function NodeBadge({
  node,
}: {
  node: LineageNodeType
}) {
  const typeColors = {
    source: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
    transform: 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300',
    sink: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
  }

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs',
        typeColors[node.node_type]
      )}
    >
      <span className="font-medium">{node.name}</span>
      <span className="opacity-60 capitalize">({node.node_type})</span>
    </div>
  )
}
