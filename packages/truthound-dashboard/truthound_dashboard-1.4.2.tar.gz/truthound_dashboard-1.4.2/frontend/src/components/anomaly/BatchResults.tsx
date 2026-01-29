/**
 * Batch Results Component.
 *
 * Displays results from a completed batch anomaly detection job.
 * Shows a sortable summary table with per-source results.
 */

import { useMemo, useState } from 'react'
import { useIntlayer } from 'react-intlayer'
import { str } from '@/lib/intlayer-utils'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
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
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ExternalLink,
  BarChart3,
  Database,
  Clock,
} from 'lucide-react'
import type { BatchDetectionJob, BatchSourceResult } from '@/api/client'

interface BatchResultsProps {
  job: BatchDetectionJob
  onViewDetails?: (sourceId: string, detectionId: string) => void
  className?: string
}

type SortField = 'source_name' | 'anomaly_count' | 'anomaly_rate' | 'total_rows' | 'status'
type SortOrder = 'asc' | 'desc'

export function BatchResults({ job, onViewDetails, className }: BatchResultsProps) {
  const t = useIntlayer('anomaly')

  const [sortField, setSortField] = useState<SortField>('anomaly_rate')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')

  // Sort results
  const sortedResults = useMemo(() => {
    if (!job.results) return []

    return [...job.results].sort((a, b) => {
      let comparison = 0

      switch (sortField) {
        case 'source_name':
          comparison = (a.source_name || '').localeCompare(b.source_name || '')
          break
        case 'anomaly_count':
          comparison = (a.anomaly_count ?? 0) - (b.anomaly_count ?? 0)
          break
        case 'anomaly_rate':
          comparison = (a.anomaly_rate ?? 0) - (b.anomaly_rate ?? 0)
          break
        case 'total_rows':
          comparison = (a.total_rows ?? 0) - (b.total_rows ?? 0)
          break
        case 'status':
          comparison = a.status.localeCompare(b.status)
          break
      }

      return sortOrder === 'asc' ? comparison : -comparison
    })
  }, [job.results, sortField, sortOrder])

  // Toggle sort
  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortField(field)
      setSortOrder('desc')
    }
  }

  // Get sort icon
  const getSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <ArrowUpDown className="ml-1 h-3 w-3" />
    }
    return sortOrder === 'asc' ? (
      <ArrowUp className="ml-1 h-3 w-3" />
    ) : (
      <ArrowDown className="ml-1 h-3 w-3" />
    )
  }

  // Get status icon and color
  const getStatusDisplay = (result: BatchSourceResult) => {
    switch (result.status) {
      case 'success':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />
      case 'error':
        return (
          <div className="flex items-center gap-1">
            <XCircle className="h-4 w-4 text-red-500" />
            {result.error_message && (
              <span className="max-w-[200px] truncate text-xs text-red-500">
                {result.error_message}
              </span>
            )}
          </div>
        )
      default:
        return <span className="text-muted-foreground">-</span>
    }
  }

  // Get anomaly rate badge color
  const getAnomalyRateBadge = (rate: number | null) => {
    if (rate === null) return null

    const percent = rate * 100
    let variant: 'default' | 'secondary' | 'destructive' | 'outline' = 'secondary'

    if (percent >= 15) {
      variant = 'destructive'
    } else if (percent >= 10) {
      variant = 'default'
    } else if (percent >= 5) {
      variant = 'outline'
    }

    return (
      <Badge variant={variant} className="font-mono">
        {percent.toFixed(2)}%
      </Badge>
    )
  }

  const statusBadgeVariant = (status: string): 'default' | 'secondary' | 'destructive' | 'outline' => {
    switch (status) {
      case 'completed':
        return 'default'
      case 'partial':
        return 'outline'
      case 'error':
        return 'destructive'
      default:
        return 'secondary'
    }
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              {job.name || t.batch.untitledJob}
            </CardTitle>
            <CardDescription className="mt-1 flex items-center gap-4">
              <span className="flex items-center gap-1">
                <Database className="h-3 w-3" />
                {job.total_sources} {str(t.batch.sourcesTotal)}
              </span>
              {job.duration_ms != null && (
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {(job.duration_ms / 1000).toFixed(1)}s
                </span>
              )}
            </CardDescription>
          </div>
          <Badge variant={statusBadgeVariant(job.status)}>
            {t.batch.status[job.status as keyof typeof t.batch.status] || job.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Summary Stats */}
        <div className="grid grid-cols-4 gap-4">
          <div className="rounded-lg border p-3">
            <p className="text-sm text-muted-foreground">{t.batch.completed}</p>
            <p className="text-2xl font-bold text-green-600">{job.completed_sources}</p>
          </div>
          <div className="rounded-lg border p-3">
            <p className="text-sm text-muted-foreground">{t.batch.failed}</p>
            <p className="text-2xl font-bold text-red-600">{job.failed_sources}</p>
          </div>
          <div className="rounded-lg border p-3">
            <p className="text-sm text-muted-foreground">{t.anomaliesFound}</p>
            <p className="text-2xl font-bold text-orange-500">
              {job.total_anomalies.toLocaleString()}
            </p>
          </div>
          <div className="rounded-lg border p-3">
            <p className="text-sm text-muted-foreground">{t.batch.avgAnomalyRate}</p>
            <p className="text-2xl font-bold">
              {(job.average_anomaly_rate * 100).toFixed(2)}%
            </p>
          </div>
        </div>

        {/* Results Table */}
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="-ml-3 h-8"
                    onClick={() => toggleSort('source_name')}
                  >
                    {t.batch.sourceName}
                    {getSortIcon('source_name')}
                  </Button>
                </TableHead>
                <TableHead className="text-center">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8"
                    onClick={() => toggleSort('status')}
                  >
                    {t.statusLabel}
                    {getSortIcon('status')}
                  </Button>
                </TableHead>
                <TableHead className="text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8"
                    onClick={() => toggleSort('total_rows')}
                  >
                    {t.totalRows}
                    {getSortIcon('total_rows')}
                  </Button>
                </TableHead>
                <TableHead className="text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8"
                    onClick={() => toggleSort('anomaly_count')}
                  >
                    {t.anomalyCount}
                    {getSortIcon('anomaly_count')}
                  </Button>
                </TableHead>
                <TableHead className="text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8"
                    onClick={() => toggleSort('anomaly_rate')}
                  >
                    {t.anomalyRate}
                    {getSortIcon('anomaly_rate')}
                  </Button>
                </TableHead>
                <TableHead className="text-right">{t.viewDetails}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedResults.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                    {t.noResults}
                  </TableCell>
                </TableRow>
              ) : (
                sortedResults.map((result) => (
                  <TableRow key={result.source_id}>
                    <TableCell className="font-medium">
                      {result.source_name || result.source_id}
                    </TableCell>
                    <TableCell className="text-center">
                      {getStatusDisplay(result)}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {result.total_rows?.toLocaleString() ?? '-'}
                    </TableCell>
                    <TableCell className="text-right">
                      {result.anomaly_count != null ? (
                        <span className="font-mono text-orange-500">
                          {result.anomaly_count.toLocaleString()}
                        </span>
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      {getAnomalyRateBadge(result.anomaly_rate)}
                    </TableCell>
                    <TableCell className="text-right">
                      {result.detection_id && result.status === 'success' && onViewDetails ? (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onViewDetails(result.source_id, result.detection_id!)}
                        >
                          <ExternalLink className="h-4 w-4" />
                        </Button>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* High anomaly rate warning */}
        {sortedResults.some((r) => r.anomaly_rate && r.anomaly_rate > 0.15) && (
          <div className="flex items-start gap-2 rounded-md bg-orange-50 p-3 text-sm dark:bg-orange-900/20">
            <AlertTriangle className="mt-0.5 h-4 w-4 text-orange-500" />
            <div>
              <p className="font-medium text-orange-700 dark:text-orange-400">
                {t.batch.highAnomalyRateWarning}
              </p>
              <p className="text-orange-600 dark:text-orange-500">
                {t.batch.highAnomalyRateDescription}
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
