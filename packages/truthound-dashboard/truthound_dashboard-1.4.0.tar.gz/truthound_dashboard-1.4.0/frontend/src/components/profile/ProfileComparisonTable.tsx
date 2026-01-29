/**
 * ProfileComparisonTable - Displays comparison between two profiles.
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { TrendingUp, TrendingDown, Minus, AlertTriangle, CheckCircle2 } from 'lucide-react'

export type TrendDirection = 'up' | 'down' | 'stable'

export interface ColumnComparison {
  column: string
  metric: string
  baseline_value: number | string | null
  current_value: number | string | null
  change: number | null
  change_pct: number | null
  is_significant: boolean
  trend: TrendDirection
}

export interface ProfileComparisonSummary {
  total_columns: number
  columns_with_changes: number
  significant_changes: number
  columns_improved: number
  columns_degraded: number
}

export interface ProfileComparisonResponse {
  baseline_profile_id: string
  current_profile_id: string
  source_id: string
  source_name: string
  baseline_timestamp: string
  current_timestamp: string
  row_count_change: number
  row_count_change_pct: number
  column_comparisons: ColumnComparison[]
  summary: ProfileComparisonSummary
  compared_at: string
}

interface ProfileComparisonTableProps {
  comparison: ProfileComparisonResponse
  showOnlySignificant?: boolean
}

export function ProfileComparisonTable({
  comparison,
  showOnlySignificant = false,
}: ProfileComparisonTableProps) {
  const TrendIcon = ({ trend, isSignificant }: { trend: TrendDirection; isSignificant: boolean }) => {
    if (trend === 'up') {
      return <TrendingUp className={`h-4 w-4 ${isSignificant ? 'text-red-500' : 'text-muted-foreground'}`} />
    }
    if (trend === 'down') {
      return <TrendingDown className={`h-4 w-4 ${isSignificant ? 'text-green-500' : 'text-muted-foreground'}`} />
    }
    return <Minus className="h-4 w-4 text-muted-foreground" />
  }

  const formatValue = (value: number | string | null) => {
    if (value === null) return '-'
    if (typeof value === 'number') {
      return value.toFixed(2)
    }
    return value
  }

  const formatChange = (change: number | null, changePct: number | null) => {
    if (change === null) return '-'
    const sign = change > 0 ? '+' : ''
    const pctStr = changePct !== null ? ` (${changePct > 0 ? '+' : ''}${changePct.toFixed(1)}%)` : ''
    return `${sign}${change.toFixed(2)}${pctStr}`
  }

  const displayedComparisons = showOnlySignificant
    ? comparison.column_comparisons.filter((c) => c.is_significant)
    : comparison.column_comparisons

  // Group by column
  const groupedByColumn = displayedComparisons.reduce(
    (acc, comp) => {
      if (!acc[comp.column]) {
        acc[comp.column] = []
      }
      acc[comp.column].push(comp)
      return acc
    },
    {} as Record<string, ColumnComparison[]>
  )

  return (
    <div className="space-y-4">
      {/* Summary Card */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Comparison Summary</CardTitle>
          <CardDescription>
            Comparing profiles from{' '}
            <span className="font-medium">{new Date(comparison.baseline_timestamp).toLocaleDateString()}</span>
            {' → '}
            <span className="font-medium">{new Date(comparison.current_timestamp).toLocaleDateString()}</span>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="text-center p-3 bg-muted/50 rounded-lg">
              <div className="text-2xl font-bold">{comparison.summary.total_columns}</div>
              <div className="text-xs text-muted-foreground">Total Columns</div>
            </div>
            <div className="text-center p-3 bg-muted/50 rounded-lg">
              <div className="text-2xl font-bold">{comparison.summary.columns_with_changes}</div>
              <div className="text-xs text-muted-foreground">With Changes</div>
            </div>
            <div className="text-center p-3 bg-muted/50 rounded-lg">
              <div className="flex items-center justify-center gap-1">
                {comparison.summary.significant_changes > 0 && (
                  <AlertTriangle className="h-4 w-4 text-yellow-500" />
                )}
                <span className="text-2xl font-bold">{comparison.summary.significant_changes}</span>
              </div>
              <div className="text-xs text-muted-foreground">Significant</div>
            </div>
            <div className="text-center p-3 bg-green-500/10 rounded-lg">
              <div className="flex items-center justify-center gap-1">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                <span className="text-2xl font-bold text-green-600">{comparison.summary.columns_improved}</span>
              </div>
              <div className="text-xs text-muted-foreground">Improved</div>
            </div>
            <div className="text-center p-3 bg-red-500/10 rounded-lg">
              <div className="flex items-center justify-center gap-1">
                <AlertTriangle className="h-4 w-4 text-red-500" />
                <span className="text-2xl font-bold text-red-600">{comparison.summary.columns_degraded}</span>
              </div>
              <div className="text-xs text-muted-foreground">Degraded</div>
            </div>
          </div>

          {/* Row count change */}
          <div className="mt-4 p-3 bg-muted/30 rounded-lg flex items-center justify-between">
            <span className="text-sm">Row Count Change</span>
            <div className="flex items-center gap-2">
              <TrendIcon
                trend={comparison.row_count_change > 0 ? 'up' : comparison.row_count_change < 0 ? 'down' : 'stable'}
                isSignificant={Math.abs(comparison.row_count_change_pct) > 5}
              />
              <span className={`font-medium ${comparison.row_count_change > 0 ? 'text-green-600' : comparison.row_count_change < 0 ? 'text-red-600' : ''}`}>
                {formatChange(comparison.row_count_change, comparison.row_count_change_pct)}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Comparison Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Column Details</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Column</TableHead>
                <TableHead>Metric</TableHead>
                <TableHead className="text-right">Baseline</TableHead>
                <TableHead className="text-right">Current</TableHead>
                <TableHead className="text-right">Change</TableHead>
                <TableHead className="text-center">Trend</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {Object.entries(groupedByColumn).map(([column, comparisons]) =>
                comparisons.map((comp, idx) => (
                  <TableRow key={`${column}-${comp.metric}`}>
                    {idx === 0 ? (
                      <TableCell rowSpan={comparisons.length} className="font-mono font-medium align-top">
                        {column}
                      </TableCell>
                    ) : null}
                    <TableCell>
                      <Badge variant="outline" className="text-xs">
                        {comp.metric}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right font-mono text-sm">
                      {formatValue(comp.baseline_value)}
                    </TableCell>
                    <TableCell className="text-right font-mono text-sm">
                      {formatValue(comp.current_value)}
                    </TableCell>
                    <TableCell className={`text-right font-mono text-sm ${comp.is_significant ? 'font-medium' : ''}`}>
                      {formatChange(comp.change, comp.change_pct)}
                    </TableCell>
                    <TableCell className="text-center">
                      <div className="flex items-center justify-center gap-1">
                        <TrendIcon trend={comp.trend} isSignificant={comp.is_significant} />
                        {comp.is_significant && (
                          <Badge variant="outline" className="bg-yellow-500/10 text-yellow-600 text-xs">
                            !
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
