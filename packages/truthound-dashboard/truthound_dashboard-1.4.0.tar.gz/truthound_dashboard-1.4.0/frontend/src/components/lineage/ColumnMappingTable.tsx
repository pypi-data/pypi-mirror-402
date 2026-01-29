/**
 * Table view of column mappings with sorting and filtering.
 *
 * Displays source column, transformation, and target column in a sortable table.
 */

import { useState, useMemo } from 'react'
import { useIntlayer } from 'react-intlayer'
import {
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Search,
  Filter,
  ExternalLink,
} from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { cn } from '@/lib/utils'
import type { ColumnMapping, ColumnTransformationType } from './column-lineage-types'

interface ColumnMappingTableProps {
  mappings: ColumnMapping[]
  nodes?: Map<string, string> // nodeId -> nodeName mapping
  onRowClick?: (mapping: ColumnMapping) => void
  onHighlightInGraph?: (mapping: ColumnMapping) => void
  className?: string
}

type SortField = 'source' | 'target' | 'type' | 'confidence'
type SortDirection = 'asc' | 'desc'

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

export function ColumnMappingTable({
  mappings,
  nodes,
  onRowClick,
  onHighlightInGraph,
  className,
}: ColumnMappingTableProps) {
  const t = useIntlayer('lineage')

  const [searchQuery, setSearchQuery] = useState('')
  const [filterType, setFilterType] = useState<ColumnTransformationType | 'all'>('all')
  const [sortField, setSortField] = useState<SortField>('source')
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')

  // Get node name from ID
  const getNodeName = (nodeId: string) => nodes?.get(nodeId) || nodeId.slice(0, 8)

  // Filter and sort mappings
  const processedMappings = useMemo(() => {
    let result = [...mappings]

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      result = result.filter(
        (m) =>
          m.sourceColumn.toLowerCase().includes(query) ||
          m.targetColumn.toLowerCase().includes(query) ||
          m.expression?.toLowerCase().includes(query)
      )
    }

    // Apply type filter
    if (filterType !== 'all') {
      result = result.filter((m) => m.transformationType === filterType)
    }

    // Sort
    result.sort((a, b) => {
      let comparison = 0
      switch (sortField) {
        case 'source':
          comparison = a.sourceColumn.localeCompare(b.sourceColumn)
          break
        case 'target':
          comparison = a.targetColumn.localeCompare(b.targetColumn)
          break
        case 'type':
          comparison = a.transformationType.localeCompare(b.transformationType)
          break
        case 'confidence':
          comparison = (a.confidence ?? 1) - (b.confidence ?? 1)
          break
      }
      return sortDirection === 'asc' ? comparison : -comparison
    })

    return result
  }, [mappings, searchQuery, filterType, sortField, sortDirection])

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return <ArrowUpDown className="ml-1 h-3 w-3 opacity-50" />
    }
    return sortDirection === 'asc' ? (
      <ArrowUp className="ml-1 h-3 w-3" />
    ) : (
      <ArrowDown className="ml-1 h-3 w-3" />
    )
  }

  const transformationTypes = Object.keys(transformationColors) as ColumnTransformationType[]

  return (
    <div className={cn('space-y-4', className)}>
      {/* Filters */}
      <div className="flex gap-2 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder={String(t.columnLineage.searchColumns)}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-8"
          />
        </div>
        <Select
          value={filterType}
          onValueChange={(v) => setFilterType(v as ColumnTransformationType | 'all')}
        >
          <SelectTrigger className="w-[160px]">
            <Filter className="mr-2 h-4 w-4" />
            <SelectValue placeholder={t.columnLineage.filterByType} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t.columnLineage.allTypes}</SelectItem>
            {transformationTypes.map((type) => (
              <SelectItem key={type} value={type}>
                {t.columnLineage.transformationTypes[type]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Results count */}
      <div className="text-sm text-muted-foreground">
        {processedMappings.length} {t.columnLineage.ofTotal} {mappings.length} {t.columnLineage.mappings}
      </div>

      {/* Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>
                <button
                  onClick={() => handleSort('source')}
                  className="flex items-center hover:text-foreground"
                >
                  {t.columnLineage.sourceColumn}
                  <SortIcon field="source" />
                </button>
              </TableHead>
              <TableHead>
                <button
                  onClick={() => handleSort('type')}
                  className="flex items-center hover:text-foreground"
                >
                  {t.columnLineage.transformation}
                  <SortIcon field="type" />
                </button>
              </TableHead>
              <TableHead>
                <button
                  onClick={() => handleSort('target')}
                  className="flex items-center hover:text-foreground"
                >
                  {t.columnLineage.targetColumn}
                  <SortIcon field="target" />
                </button>
              </TableHead>
              <TableHead>
                <button
                  onClick={() => handleSort('confidence')}
                  className="flex items-center hover:text-foreground"
                >
                  {t.columnLineage.confidence}
                  <SortIcon field="confidence" />
                </button>
              </TableHead>
              <TableHead className="w-[80px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {processedMappings.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                  {t.columnLineage.noResults}
                </TableCell>
              </TableRow>
            ) : (
              processedMappings.map((mapping, idx) => (
                <TableRow
                  key={`${mapping.id}-${idx}`}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => onRowClick?.(mapping)}
                >
                  <TableCell>
                    <div className="flex flex-col">
                      <span className="font-mono text-sm text-blue-600 dark:text-blue-400">
                        {mapping.sourceColumn}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {getNodeName(mapping.sourceNodeId)}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-col gap-1">
                      <Badge
                        variant="outline"
                        className={cn('w-fit text-xs', transformationColors[mapping.transformationType])}
                      >
                        {t.columnLineage.transformationTypes[mapping.transformationType]}
                      </Badge>
                      {mapping.expression && (
                        <span
                          className="text-xs text-muted-foreground font-mono truncate max-w-[150px]"
                          title={mapping.expression}
                        >
                          {mapping.expression}
                        </span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-col">
                      <span className="font-mono text-sm text-green-600 dark:text-green-400">
                        {mapping.targetColumn}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {getNodeName(mapping.targetNodeId)}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    {mapping.confidence !== undefined ? (
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                          <div
                            className={cn(
                              'h-full rounded-full',
                              mapping.confidence >= 0.8
                                ? 'bg-green-500'
                                : mapping.confidence >= 0.5
                                  ? 'bg-amber-500'
                                  : 'bg-red-500'
                            )}
                            style={{ width: `${mapping.confidence * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {Math.round(mapping.confidence * 100)}%
                        </span>
                      </div>
                    ) : (
                      <span className="text-xs text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={(e) => {
                        e.stopPropagation()
                        onHighlightInGraph?.(mapping)
                      }}
                    >
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
