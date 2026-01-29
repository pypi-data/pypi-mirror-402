/**
 * Comparison results table component.
 *
 * Displays algorithm comparison results in a sortable table.
 */

import { useMemo, useState } from 'react'
import { useIntlayer } from 'react-intlayer'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  ArrowUp,
  ArrowDown,
  Trophy,
  AlertTriangle,
  Clock,
  CheckCircle2,
  XCircle,
} from 'lucide-react'
import type { AlgorithmComparisonResult } from '@/api/client'

interface ComparisonResultsTableProps {
  result: AlgorithmComparisonResult
}

type SortKey = 'algorithm' | 'anomaly_count' | 'anomaly_rate' | 'duration_ms'
type SortDirection = 'asc' | 'desc'

export function ComparisonResultsTable({ result }: ComparisonResultsTableProps) {
  const t = useIntlayer('anomaly')
  const [sortKey, setSortKey] = useState<SortKey>('anomaly_rate')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')

  // Sort algorithm results
  const sortedResults = useMemo(() => {
    const items = [...result.algorithm_results]

    items.sort((a, b) => {
      let valA: number | string = 0
      let valB: number | string = 0

      switch (sortKey) {
        case 'algorithm':
          valA = a.display_name
          valB = b.display_name
          break
        case 'anomaly_count':
          valA = a.anomaly_count ?? 0
          valB = b.anomaly_count ?? 0
          break
        case 'anomaly_rate':
          valA = a.anomaly_rate ?? 0
          valB = b.anomaly_rate ?? 0
          break
        case 'duration_ms':
          valA = a.duration_ms ?? 0
          valB = b.duration_ms ?? 0
          break
      }

      if (typeof valA === 'string' && typeof valB === 'string') {
        return sortDirection === 'asc'
          ? valA.localeCompare(valB)
          : valB.localeCompare(valA)
      }

      return sortDirection === 'asc'
        ? (valA as number) - (valB as number)
        : (valB as number) - (valA as number)
    })

    return items
  }, [result.algorithm_results, sortKey, sortDirection])

  // Find best and worst for highlighting
  const stats = useMemo(() => {
    const successResults = result.algorithm_results.filter((r) => r.status === 'success')
    if (successResults.length === 0) return null

    const rates = successResults.map((r) => r.anomaly_rate ?? 0)
    const durations = successResults.map((r) => r.duration_ms ?? 0)

    return {
      maxRate: Math.max(...rates),
      minRate: Math.min(...rates),
      fastestDuration: Math.min(...durations),
      slowestDuration: Math.max(...durations),
    }
  }, [result.algorithm_results])

  // Toggle sort
  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDirection('desc')
    }
  }

  // Render sort indicator
  const SortIndicator = ({ columnKey }: { columnKey: SortKey }) => {
    if (sortKey !== columnKey) return null
    return sortDirection === 'asc' ? (
      <ArrowUp className="ml-1 h-3 w-3" />
    ) : (
      <ArrowDown className="ml-1 h-3 w-3" />
    )
  }

  return (
    <div className="space-y-4">
      {/* Summary stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-lg border p-4">
          <p className="text-sm text-muted-foreground">
            {t.comparison?.totalRows ?? 'Total Rows'}
          </p>
          <p className="text-2xl font-bold">
            {result.total_rows?.toLocaleString() ?? '-'}
          </p>
        </div>
        <div className="rounded-lg border p-4">
          <p className="text-sm text-muted-foreground">
            {t.comparison?.algorithmsCompared ?? 'Algorithms'}
          </p>
          <p className="text-2xl font-bold">{result.algorithm_results.length}</p>
        </div>
        <div className="rounded-lg border p-4">
          <p className="text-sm text-muted-foreground">
            {t.comparison?.columnsAnalyzed ?? 'Columns'}
          </p>
          <p className="text-2xl font-bold">
            {result.columns_analyzed?.length ?? '-'}
          </p>
        </div>
        <div className="rounded-lg border p-4">
          <p className="text-sm text-muted-foreground">
            {t.comparison?.totalDuration ?? 'Total Duration'}
          </p>
          <p className="text-2xl font-bold">
            {result.total_duration_ms != null
              ? `${(result.total_duration_ms / 1000).toFixed(1)}s`
              : '-'}
          </p>
        </div>
      </div>

      {/* Results table */}
      <div className="rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-auto p-0 hover:bg-transparent"
                  onClick={() => handleSort('algorithm')}
                >
                  {t.comparison?.algorithm ?? 'Algorithm'}
                  <SortIndicator columnKey="algorithm" />
                </Button>
              </TableHead>
              <TableHead>{t.comparison?.status ?? 'Status'}</TableHead>
              <TableHead className="text-right">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-auto p-0 hover:bg-transparent"
                  onClick={() => handleSort('anomaly_count')}
                >
                  {t.comparison?.anomalyCount ?? 'Anomaly Count'}
                  <SortIndicator columnKey="anomaly_count" />
                </Button>
              </TableHead>
              <TableHead className="text-right">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-auto p-0 hover:bg-transparent"
                  onClick={() => handleSort('anomaly_rate')}
                >
                  {t.comparison?.anomalyRate ?? 'Anomaly Rate'}
                  <SortIndicator columnKey="anomaly_rate" />
                </Button>
              </TableHead>
              <TableHead className="text-right">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-auto p-0 hover:bg-transparent"
                  onClick={() => handleSort('duration_ms')}
                >
                  {t.comparison?.duration ?? 'Duration'}
                  <SortIndicator columnKey="duration_ms" />
                </Button>
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedResults.map((item) => {
              const isBestRate = stats && item.anomaly_rate === stats.maxRate
              const isWorstRate = stats && item.anomaly_rate === stats.minRate
              const isFastest = stats && item.duration_ms === stats.fastestDuration
              const isSlowest = stats && item.duration_ms === stats.slowestDuration

              return (
                <TableRow key={item.algorithm}>
                  <TableCell className="font-medium">
                    {item.display_name}
                  </TableCell>
                  <TableCell>
                    {item.status === 'success' ? (
                      <Badge
                        variant="outline"
                        className="border-green-500 text-green-500"
                      >
                        <CheckCircle2 className="mr-1 h-3 w-3" />
                        {t.comparison?.success ?? 'Success'}
                      </Badge>
                    ) : (
                      <Badge
                        variant="outline"
                        className="border-red-500 text-red-500"
                      >
                        <XCircle className="mr-1 h-3 w-3" />
                        {t.comparison?.failed ?? 'Failed'}
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    {item.anomaly_count?.toLocaleString() ?? '-'}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      {item.anomaly_rate != null
                        ? `${(item.anomaly_rate * 100).toFixed(2)}%`
                        : '-'}
                      {isBestRate && item.status === 'success' && (
                        <Trophy className="h-4 w-4 text-amber-500" aria-label="Highest rate" />
                      )}
                      {isWorstRate && item.status === 'success' && !isBestRate && (
                        <AlertTriangle className="h-4 w-4 text-blue-500" aria-label="Lowest rate" />
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      {item.duration_ms != null
                        ? `${(item.duration_ms / 1000).toFixed(2)}s`
                        : '-'}
                      {isFastest && item.status === 'success' && (
                        <Clock className="h-4 w-4 text-green-500" aria-label="Fastest" />
                      )}
                      {isSlowest && item.status === 'success' && !isFastest && (
                        <Clock className="h-4 w-4 text-red-500" aria-label="Slowest" />
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
