/**
 * Side panel showing details of the selected lineage node.
 */

import { useIntlayer } from 'react-intlayer'
import {
  Database,
  ArrowRightLeft,
  Archive,
  ExternalLink,
  Calendar,
  Trash2,
  Edit2,
  Columns,
  ArrowRight,
  Key,
  Link2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'
import type { LineageNode as LineageNodeType, LineageEdge } from '@/api/client'
import type { LineageColumn, ColumnMapping, ColumnTransformationType } from './column-lineage-types'

interface LineageNodeDetailsProps {
  node: LineageNodeType | null
  edges: LineageEdge[]
  allNodes: LineageNodeType[]
  columns?: LineageColumn[]
  columnMappings?: ColumnMapping[]
  onEdit?: (node: LineageNodeType) => void
  onDelete?: (nodeId: string) => void
  onAnalyzeImpact?: (nodeId: string) => void
  onColumnClick?: (columnName: string) => void
  onColumnImpactAnalysis?: (columnName: string) => void
}

const nodeTypeConfig = {
  source: { icon: Database, color: 'text-blue-500', bgColor: 'bg-blue-500/10' },
  transform: { icon: ArrowRightLeft, color: 'text-amber-500', bgColor: 'bg-amber-500/10' },
  sink: { icon: Archive, color: 'text-green-500', bgColor: 'bg-green-500/10' },
}

// Transformation type colors
const transformationColors: Record<ColumnTransformationType, string> = {
  direct: 'bg-blue-500/20 text-blue-700 dark:text-blue-300',
  derived: 'bg-purple-500/20 text-purple-700 dark:text-purple-300',
  aggregated: 'bg-amber-500/20 text-amber-700 dark:text-amber-300',
  filtered: 'bg-green-500/20 text-green-700 dark:text-green-300',
  joined: 'bg-pink-500/20 text-pink-700 dark:text-pink-300',
  renamed: 'bg-cyan-500/20 text-cyan-700 dark:text-cyan-300',
  cast: 'bg-orange-500/20 text-orange-700 dark:text-orange-300',
  computed: 'bg-indigo-500/20 text-indigo-700 dark:text-indigo-300',
}

export function LineageNodeDetails({
  node,
  edges,
  allNodes,
  columns,
  columnMappings,
  onEdit,
  onDelete,
  onAnalyzeImpact,
  onColumnClick,
  onColumnImpactAnalysis,
}: LineageNodeDetailsProps) {
  const t = useIntlayer('lineage')

  if (!node) {
    return (
      <div className="flex h-full items-center justify-center p-6 text-center text-muted-foreground">
        <p>{t.noNodeSelected}</p>
      </div>
    )
  }

  const config = nodeTypeConfig[node.node_type]
  const Icon = config.icon

  // Find connected nodes
  const upstreamEdges = edges.filter((e) => e.target_node_id === node.id)
  const downstreamEdges = edges.filter((e) => e.source_node_id === node.id)

  const upstreamNodes = upstreamEdges
    .map((e) => allNodes.find((n) => n.id === e.source_node_id))
    .filter(Boolean) as LineageNodeType[]

  const downstreamNodes = downstreamEdges
    .map((e) => allNodes.find((n) => n.id === e.target_node_id))
    .filter(Boolean) as LineageNodeType[]

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  // Filter column mappings for this node
  const incomingMappings = columnMappings?.filter((m) => m.targetNodeId === node.id) ?? []
  const outgoingMappings = columnMappings?.filter((m) => m.sourceNodeId === node.id) ?? []
  const hasColumns = columns && columns.length > 0
  const hasMappings = incomingMappings.length > 0 || outgoingMappings.length > 0

  return (
    <div className="flex flex-col gap-4 p-4">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={cn('rounded-lg p-2', config.bgColor)}>
            <Icon className={cn('h-5 w-5', config.color)} />
          </div>
          <div>
            <h3 className="font-semibold">{node.name}</h3>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="capitalize">
                {t.nodeTypes[node.node_type]}
              </Badge>
              {hasColumns && (
                <Badge variant="secondary" className="text-xs">
                  <Columns className="h-3 w-3 mr-1" />
                  {columns.length}
                </Badge>
              )}
            </div>
          </div>
        </div>

        <div className="flex gap-1">
          {onEdit && (
            <Button variant="ghost" size="icon" onClick={() => onEdit(node)}>
              <Edit2 className="h-4 w-4" />
            </Button>
          )}
          {onDelete && (
            <Button
              variant="ghost"
              size="icon"
              className="text-destructive"
              onClick={() => onDelete(node.id)}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Linked source */}
      {node.source_id && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <ExternalLink className="h-4 w-4" />
          <span>{t.linkedSource}:</span>
          <Badge variant="secondary">{node.source_id.slice(0, 8)}...</Badge>
        </div>
      )}

      {/* Tabbed content */}
      <Tabs defaultValue="details" className="w-full">
        <TabsList className="w-full">
          <TabsTrigger value="details" className="flex-1">{t.columnLineage.detailsTab}</TabsTrigger>
          <TabsTrigger value="columns" className="flex-1" disabled={!hasColumns}>
            {t.columnLineage.columnsTab}
            {hasColumns && (
              <Badge variant="secondary" className="ml-1 h-4 px-1 text-[10px]">
                {columns.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="lineage" className="flex-1" disabled={!hasMappings}>
            {t.columnLineage.lineageTab}
          </TabsTrigger>
        </TabsList>

        {/* Details Tab */}
        <TabsContent value="details" className="space-y-4 mt-4">
          {/* Metadata */}
          {node.metadata && Object.keys(node.metadata).length > 0 && (
            <Card>
              <CardHeader className="py-3">
                <CardTitle className="text-sm">{t.metadata}</CardTitle>
              </CardHeader>
              <CardContent className="py-2">
                <div className="space-y-1 text-sm">
                  {Object.entries(node.metadata).map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="text-muted-foreground">{key}:</span>
                      <span className="font-medium">
                        {Array.isArray(value) ? value.join(', ') : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Connected nodes */}
          <Card>
            <CardHeader className="py-3">
              <CardTitle className="text-sm">{t.connectedNodes}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 py-2">
              {/* Upstream */}
              <div>
                <p className="mb-2 text-xs font-medium text-muted-foreground">
                  {t.upstream} ({upstreamNodes.length})
                </p>
                {upstreamNodes.length === 0 ? (
                  <p className="text-sm text-muted-foreground">None</p>
                ) : (
                  <div className="flex flex-wrap gap-1">
                    {upstreamNodes.map((n) => (
                      <Badge key={n.id} variant="secondary" className="text-xs">
                        {n.name}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>

              {/* Downstream */}
              <div>
                <p className="mb-2 text-xs font-medium text-muted-foreground">
                  {t.downstream} ({downstreamNodes.length})
                </p>
                {downstreamNodes.length === 0 ? (
                  <p className="text-sm text-muted-foreground">None</p>
                ) : (
                  <div className="flex flex-wrap gap-1">
                    {downstreamNodes.map((n) => (
                      <Badge key={n.id} variant="secondary" className="text-xs">
                        {n.name}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Impact analysis button */}
          {onAnalyzeImpact && (
            <Button variant="outline" className="w-full" onClick={() => onAnalyzeImpact(node.id)}>
              {t.analyzeImpact}
            </Button>
          )}
        </TabsContent>

        {/* Columns Tab */}
        <TabsContent value="columns" className="mt-4">
          {hasColumns ? (
            <div className="space-y-2 max-h-[400px] overflow-y-auto">
              {columns.map((col) => (
                <div
                  key={col.name}
                  className={cn(
                    'flex items-center justify-between p-2 rounded-lg border hover:bg-muted/50 cursor-pointer',
                    col.isPrimaryKey && 'border-amber-500/30 bg-amber-500/5'
                  )}
                  onClick={() => onColumnClick?.(col.name)}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="font-mono text-sm truncate">{col.name}</span>
                    {col.isPrimaryKey && (
                      <Key className="h-3 w-3 text-amber-500 flex-shrink-0" />
                    )}
                    {col.isForeignKey && (
                      <Link2 className="h-3 w-3 text-blue-500 flex-shrink-0" />
                    )}
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <Badge variant="secondary" className="text-xs font-mono">
                      {col.dataType}
                    </Badge>
                    {col.nullable && (
                      <Badge variant="outline" className="text-xs text-muted-foreground">
                        NULL
                      </Badge>
                    )}
                    {onColumnImpactAnalysis && (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6"
                        onClick={(e) => {
                          e.stopPropagation()
                          onColumnImpactAnalysis(col.name)
                        }}
                      >
                        <ArrowRightLeft className="h-3 w-3" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center text-muted-foreground">
              <Columns className="mx-auto h-8 w-8 opacity-50" />
              <p className="mt-2">{t.columnLineage.noColumnsAvailable}</p>
            </div>
          )}
        </TabsContent>

        {/* Column Lineage Tab */}
        <TabsContent value="lineage" className="mt-4 space-y-4">
          {/* Incoming mappings (data flowing INTO this node) */}
          {incomingMappings.length > 0 && (
            <Card>
              <CardHeader className="py-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <ArrowRight className="h-4 w-4 rotate-180" />
                  {t.columnLineage.incomingMappings} ({incomingMappings.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="py-2">
                <div className="space-y-1 max-h-[200px] overflow-y-auto">
                  {incomingMappings.map((mapping, idx) => {
                    const sourceNode = allNodes.find((n) => n.id === mapping.sourceNodeId)
                    return (
                      <div
                        key={`${mapping.id}-${idx}`}
                        className="flex items-center gap-2 text-xs p-1.5 rounded hover:bg-muted/50"
                      >
                        <span className="text-muted-foreground truncate max-w-[60px]">
                          {sourceNode?.name ?? mapping.sourceNodeId.slice(0, 6)}
                        </span>
                        <span className="font-mono text-blue-600 dark:text-blue-400">
                          {mapping.sourceColumn}
                        </span>
                        <ArrowRight className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                        <span className="font-mono text-green-600 dark:text-green-400">
                          {mapping.targetColumn}
                        </span>
                        <Badge
                          variant="outline"
                          className={cn('h-4 px-1 text-[9px] ml-auto', transformationColors[mapping.transformationType])}
                        >
                          {mapping.transformationType}
                        </Badge>
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Outgoing mappings (data flowing OUT of this node) */}
          {outgoingMappings.length > 0 && (
            <Card>
              <CardHeader className="py-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <ArrowRight className="h-4 w-4" />
                  {t.columnLineage.outgoingMappings} ({outgoingMappings.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="py-2">
                <div className="space-y-1 max-h-[200px] overflow-y-auto">
                  {outgoingMappings.map((mapping, idx) => {
                    const targetNode = allNodes.find((n) => n.id === mapping.targetNodeId)
                    return (
                      <div
                        key={`${mapping.id}-${idx}`}
                        className="flex items-center gap-2 text-xs p-1.5 rounded hover:bg-muted/50"
                      >
                        <span className="font-mono text-blue-600 dark:text-blue-400">
                          {mapping.sourceColumn}
                        </span>
                        <ArrowRight className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                        <span className="font-mono text-green-600 dark:text-green-400">
                          {mapping.targetColumn}
                        </span>
                        <span className="text-muted-foreground truncate max-w-[60px]">
                          {targetNode?.name ?? mapping.targetNodeId.slice(0, 6)}
                        </span>
                        <Badge
                          variant="outline"
                          className={cn('h-4 px-1 text-[9px] ml-auto', transformationColors[mapping.transformationType])}
                        >
                          {mapping.transformationType}
                        </Badge>
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>
          )}

          {!hasMappings && (
            <div className="py-8 text-center text-muted-foreground">
              <ArrowRightLeft className="mx-auto h-8 w-8 opacity-50" />
              <p className="mt-2">{t.columnLineage.noColumnMappings}</p>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Timestamps */}
      <div className="space-y-1 text-xs text-muted-foreground">
        <div className="flex items-center gap-2">
          <Calendar className="h-3 w-3" />
          <span>{t.createdAt}: {formatDate(node.created_at)}</span>
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="h-3 w-3" />
          <span>{t.updatedAt}: {formatDate(node.updated_at)}</span>
        </div>
      </div>
    </div>
  )
}
