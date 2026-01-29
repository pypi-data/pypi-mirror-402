/**
 * Column drilldown component.
 *
 * Main component for column-level drift analysis with expandable details.
 */

import { useState, useMemo } from 'react'
import { useIntlayer } from 'react-intlayer'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
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
  Search,
  Filter,
  AlertTriangle,
  CheckCircle,
  Columns,
  BarChart3,
  Table as TableIcon,
  X,
  ArrowUpDown,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { ColumnDriftCard } from './ColumnDriftCard'
import { ColumnStatistics } from './ColumnStatistics'
import { ColumnDistributionComparison } from './ColumnDistributionComparison'
import { DriftScoreGauge } from './DriftScoreGauge'
import type { ColumnDriftResult, DriftResult } from '@/api/client'

interface ColumnDrilldownProps {
  result: DriftResult
  threshold?: number
  className?: string
  onClose?: () => void
}

type SortOption = 'name' | 'drift' | 'pvalue' | 'level'
type FilterOption = 'all' | 'drifted' | 'not-drifted' | 'high' | 'medium' | 'low'

export function ColumnDrilldown({
  result,
  threshold = 5,
  className,
  onClose,
}: ColumnDrilldownProps) {
  const t = useIntlayer('driftMonitor')
  const [searchQuery, setSearchQuery] = useState('')
  const [filterOption, setFilterOption] = useState<FilterOption>('all')
  const [sortOption, setSortOption] = useState<SortOption>('drift')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc')
  const [selectedColumn, setSelectedColumn] = useState<ColumnDriftResult | null>(null)
  const [activeTab, setActiveTab] = useState<'distribution' | 'statistics'>('distribution')

  // Filter and sort columns
  const filteredAndSortedColumns = useMemo(() => {
    let columns = [...result.columns]

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      columns = columns.filter(
        col =>
          col.column.toLowerCase().includes(query) ||
          col.dtype.toLowerCase().includes(query) ||
          col.method.toLowerCase().includes(query)
      )
    }

    // Apply drift filter
    switch (filterOption) {
      case 'drifted':
        columns = columns.filter(col => col.drifted)
        break
      case 'not-drifted':
        columns = columns.filter(col => !col.drifted)
        break
      case 'high':
        columns = columns.filter(col => col.level === 'high')
        break
      case 'medium':
        columns = columns.filter(col => col.level === 'medium')
        break
      case 'low':
        columns = columns.filter(col => col.level === 'low')
        break
    }

    // Apply sorting
    columns.sort((a, b) => {
      let comparison = 0
      switch (sortOption) {
        case 'name':
          comparison = a.column.localeCompare(b.column)
          break
        case 'drift':
          comparison = (a.drifted ? 1 : 0) - (b.drifted ? 1 : 0)
          break
        case 'pvalue':
          comparison = (a.p_value ?? 1) - (b.p_value ?? 1)
          break
        case 'level':
          const levelOrder = { high: 3, medium: 2, low: 1, none: 0 }
          comparison = (levelOrder[a.level as keyof typeof levelOrder] ?? 0) -
                       (levelOrder[b.level as keyof typeof levelOrder] ?? 0)
          break
      }
      return sortDirection === 'asc' ? comparison : -comparison
    })

    return columns
  }, [result.columns, searchQuery, filterOption, sortOption, sortDirection])

  // Summary stats
  const driftedCount = result.columns.filter(c => c.drifted).length
  const highCount = result.columns.filter(c => c.level === 'high').length
  const mediumCount = result.columns.filter(c => c.level === 'medium').length
  const driftPercentage = (driftedCount / result.total_columns) * 100

  const toggleSort = () => {
    setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc')
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header with summary */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Columns className="h-5 w-5" />
              {t.columnDrilldown?.title ?? 'Column Drift Analysis'}
            </CardTitle>
            {onClose && (
              <Button variant="ghost" size="icon" onClick={onClose}>
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {/* Overall drift gauge */}
          <div className="mb-4">
            <DriftScoreGauge
              score={driftPercentage}
              threshold={threshold}
              criticalThreshold={threshold * 4}
              size="md"
            />
          </div>

          {/* Summary badges */}
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline" className="bg-background">
              <Columns className="h-3 w-3 mr-1" />
              {result.total_columns} {t.columnDrilldown?.totalColumns ?? 'columns'}
            </Badge>
            <Badge
              variant="outline"
              className={cn(
                driftedCount > 0
                  ? 'bg-orange-500/10 text-orange-500 border-orange-500/20'
                  : 'bg-green-500/10 text-green-500 border-green-500/20'
              )}
            >
              {driftedCount > 0 ? (
                <AlertTriangle className="h-3 w-3 mr-1" />
              ) : (
                <CheckCircle className="h-3 w-3 mr-1" />
              )}
              {driftedCount} {t.columnDrilldown?.drifted ?? 'drifted'}
            </Badge>
            {highCount > 0 && (
              <Badge variant="outline" className="bg-red-500/10 text-red-500 border-red-500/20">
                {highCount} {t.columnDrilldown?.levels?.high ?? 'high'}
              </Badge>
            )}
            {mediumCount > 0 && (
              <Badge variant="outline" className="bg-orange-500/10 text-orange-500 border-orange-500/20">
                {mediumCount} {t.columnDrilldown?.levels?.medium ?? 'medium'}
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Filters and search */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder={String(t.columnDrilldown?.searchPlaceholder ?? 'Search columns...')}
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        <Select value={filterOption} onValueChange={v => setFilterOption(v as FilterOption)}>
          <SelectTrigger className="w-[150px]">
            <Filter className="h-4 w-4 mr-2" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t.columnDrilldown?.filter?.all ?? 'All Columns'}</SelectItem>
            <SelectItem value="drifted">{t.columnDrilldown?.filter?.drifted ?? 'Drifted Only'}</SelectItem>
            <SelectItem value="not-drifted">{t.columnDrilldown?.filter?.notDrifted ?? 'Not Drifted'}</SelectItem>
            <SelectItem value="high">{t.columnDrilldown?.filter?.high ?? 'High Level'}</SelectItem>
            <SelectItem value="medium">{t.columnDrilldown?.filter?.medium ?? 'Medium Level'}</SelectItem>
            <SelectItem value="low">{t.columnDrilldown?.filter?.low ?? 'Low Level'}</SelectItem>
          </SelectContent>
        </Select>

        <Select value={sortOption} onValueChange={v => setSortOption(v as SortOption)}>
          <SelectTrigger className="w-[140px]">
            <ArrowUpDown className="h-4 w-4 mr-2" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="drift">{t.columnDrilldown?.sort?.drift ?? 'By Drift'}</SelectItem>
            <SelectItem value="level">{t.columnDrilldown?.sort?.level ?? 'By Level'}</SelectItem>
            <SelectItem value="pvalue">{t.columnDrilldown?.sort?.pvalue ?? 'By P-Value'}</SelectItem>
            <SelectItem value="name">{t.columnDrilldown?.sort?.name ?? 'By Name'}</SelectItem>
          </SelectContent>
        </Select>

        <Button variant="outline" size="icon" onClick={toggleSort}>
          <ArrowUpDown className={cn(
            'h-4 w-4 transition-transform',
            sortDirection === 'desc' && 'rotate-180'
          )} />
        </Button>
      </div>

      {/* Column list and details */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Column list */}
        <div className="space-y-2 max-h-[600px] overflow-y-auto pr-2">
          {filteredAndSortedColumns.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                {t.columnDrilldown?.noResults ?? 'No columns match the filter criteria'}
              </CardContent>
            </Card>
          ) : (
            filteredAndSortedColumns.map(col => (
              <ColumnDriftCard
                key={col.column}
                result={col}
                isSelected={selectedColumn?.column === col.column}
                onClick={() => setSelectedColumn(
                  selectedColumn?.column === col.column ? null : col
                )}
              />
            ))
          )}
        </div>

        {/* Column details */}
        <div className="space-y-4">
          {selectedColumn ? (
            <>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center justify-between">
                    <span>{selectedColumn.column}</span>
                    <Badge variant="outline" className="text-xs">
                      {selectedColumn.dtype}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Tabs value={activeTab} onValueChange={v => setActiveTab(v as 'distribution' | 'statistics')}>
                    <TabsList className="grid w-full grid-cols-2">
                      <TabsTrigger value="distribution" className="gap-2">
                        <BarChart3 className="h-4 w-4" />
                        {t.columnDrilldown?.tabs?.distribution ?? 'Distribution'}
                      </TabsTrigger>
                      <TabsTrigger value="statistics" className="gap-2">
                        <TableIcon className="h-4 w-4" />
                        {t.columnDrilldown?.tabs?.statistics ?? 'Statistics'}
                      </TabsTrigger>
                    </TabsList>

                    <TabsContent value="distribution" className="mt-4">
                      <ColumnDistributionComparison
                        baselineStats={selectedColumn.baseline_stats as Record<string, unknown>}
                        currentStats={selectedColumn.current_stats as Record<string, unknown>}
                      />
                    </TabsContent>

                    <TabsContent value="statistics" className="mt-4">
                      <ColumnStatistics
                        baselineStats={selectedColumn.baseline_stats as Record<string, unknown>}
                        currentStats={selectedColumn.current_stats as Record<string, unknown>}
                      />
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>

              {/* Test results summary */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">
                    {t.columnDrilldown?.testResults ?? 'Statistical Test Results'}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs text-muted-foreground">
                        {t.columnDrilldown?.testMethod ?? 'Test Method'}
                      </p>
                      <p className="font-medium">{selectedColumn.method.toUpperCase()}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">
                        {t.columnDrilldown?.driftLevel ?? 'Drift Level'}
                      </p>
                      <Badge
                        variant="outline"
                        className={cn(
                          selectedColumn.level === 'high'
                            ? 'bg-red-500/10 text-red-500'
                            : selectedColumn.level === 'medium'
                            ? 'bg-orange-500/10 text-orange-500'
                            : selectedColumn.level === 'low'
                            ? 'bg-yellow-500/10 text-yellow-500'
                            : 'bg-green-500/10 text-green-500'
                        )}
                      >
                        {selectedColumn.level}
                      </Badge>
                    </div>
                    {selectedColumn.statistic !== undefined && (
                      <div>
                        <p className="text-xs text-muted-foreground">
                          {t.columnDrilldown?.statistic ?? 'Test Statistic'}
                        </p>
                        <p className="font-mono">{selectedColumn.statistic.toFixed(6)}</p>
                      </div>
                    )}
                    {selectedColumn.p_value !== undefined && (
                      <div>
                        <p className="text-xs text-muted-foreground">
                          {t.columnDrilldown?.pValue ?? 'P-Value'}
                        </p>
                        <p className={cn(
                          'font-mono',
                          selectedColumn.p_value < 0.05 && 'text-orange-500',
                          selectedColumn.p_value < 0.01 && 'text-red-500'
                        )}>
                          {selectedColumn.p_value.toFixed(6)}
                        </p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card className="h-full min-h-[400px]">
              <CardContent className="flex h-full items-center justify-center text-muted-foreground">
                <div className="text-center">
                  <Columns className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>{t.columnDrilldown?.selectColumn ?? 'Select a column to view details'}</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
