/**
 * Drift Preview Results Component.
 *
 * Displays the results of a drift preview comparison,
 * including summary cards, column-level results, and distribution charts.
 */

import { useState } from 'react'
import { useIntlayer } from 'react-intlayer'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
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
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  BarChart3,
  Database,
  Columns3,
  TrendingUp,
} from 'lucide-react'
import { ColumnDistributionChart } from './ColumnDistributionChart'
import type { DriftPreviewData } from './DriftPreview'

interface DriftPreviewResultsProps {
  data: DriftPreviewData
  onReset?: () => void
}

function getLevelBadgeVariant(level: string): 'destructive' | 'secondary' | 'outline' | 'default' {
  switch (level) {
    case 'high':
      return 'destructive'
    case 'medium':
      return 'default'
    case 'low':
      return 'secondary'
    default:
      return 'outline'
  }
}

function formatNumber(value: number | null | undefined, decimals = 2): string {
  if (value == null) return '-'
  return value.toFixed(decimals)
}

export function DriftPreviewResults({ data, onReset: _onReset }: DriftPreviewResultsProps) {
  const t = useIntlayer('driftMonitor')
  const [expandedColumn, setExpandedColumn] = useState<string | null>(null)

  // Sort columns: drifted first, then by level severity
  const sortedColumns = [...data.columns].sort((a, b) => {
    // Drifted columns first
    if (a.drifted !== b.drifted) return a.drifted ? -1 : 1

    // Then by level
    const levelOrder = { high: 0, medium: 1, low: 2, none: 3 }
    const aLevel = levelOrder[a.level as keyof typeof levelOrder] ?? 3
    const bLevel = levelOrder[b.level as keyof typeof levelOrder] ?? 3
    return aLevel - bLevel
  })

  return (
    <div className="space-y-6 py-4">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Drift Status Card */}
        <Card className={data.has_drift ? 'border-destructive' : 'border-green-500'}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {t.preview?.driftStatus ?? 'Drift Status'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              {data.has_drift ? (
                <>
                  <AlertTriangle className="h-5 w-5 text-destructive" />
                  <span className="text-lg font-bold text-destructive">
                    {t.preview?.driftDetected ?? 'Drift Detected'}
                  </span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                  <span className="text-lg font-bold text-green-500">
                    {t.preview?.noDrift ?? 'No Drift'}
                  </span>
                </>
              )}
            </div>
            {data.has_high_drift && (
              <Badge variant="destructive" className="mt-2">
                {t.severity.high}
              </Badge>
            )}
          </CardContent>
        </Card>

        {/* Drift Percentage Card */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-1">
              <TrendingUp className="h-4 w-4" />
              {t.preview?.driftPercentage ?? 'Drift Percentage'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {data.drift_percentage.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              {data.drifted_columns} / {data.total_columns} {t.preview?.columnsAffected ?? 'columns affected'}
            </p>
          </CardContent>
        </Card>

        {/* Row Count Comparison */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-1">
              <Database className="h-4 w-4" />
              {t.preview?.rowComparison ?? 'Row Count'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">{t.preview?.baseline ?? 'Baseline'}:</span>
                <span className="font-medium">{data.baseline_rows.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">{t.preview?.current ?? 'Current'}:</span>
                <span className="font-medium">{data.current_rows.toLocaleString()}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Detection Config */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-1">
              <BarChart3 className="h-4 w-4" />
              {t.preview?.configuration ?? 'Configuration'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">{t.monitor.method}:</span>
                <span className="font-medium uppercase">{data.method}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">{t.monitor.threshold}:</span>
                <span className="font-medium">{(data.threshold * 100).toFixed(0)}%</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Source Names */}
      <div className="flex gap-4 text-sm">
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">{t.monitor.baselineSource}:</span>
          <Badge variant="outline">{data.baseline_source_name || data.baseline_source_id}</Badge>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">{t.monitor.currentSource}:</span>
          <Badge variant="outline">{data.current_source_name || data.current_source_id}</Badge>
        </div>
      </div>

      {/* Most Affected Columns */}
      {data.most_affected.length > 0 && (
        <Card className="border-orange-500/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-orange-500" />
              {t.preview?.mostAffected ?? 'Most Affected Columns'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {data.most_affected.map((col) => (
                <Badge key={col} variant="destructive">
                  {col}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Column Results Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Columns3 className="h-4 w-4" />
            {t.preview?.columnResults ?? 'Column Results'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-8"></TableHead>
                <TableHead>{t.preview?.column ?? 'Column'}</TableHead>
                <TableHead>{t.preview?.type ?? 'Type'}</TableHead>
                <TableHead>{t.preview?.status ?? 'Status'}</TableHead>
                <TableHead>{t.preview?.level ?? 'Level'}</TableHead>
                <TableHead className="text-right">{t.preview?.pValue ?? 'P-Value'}</TableHead>
                <TableHead className="text-right">{t.preview?.statistic ?? 'Statistic'}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedColumns.map((col) => (
                <Collapsible
                  key={col.column}
                  open={expandedColumn === col.column}
                  onOpenChange={(open) =>
                    setExpandedColumn(open ? col.column : null)
                  }
                  asChild
                >
                  <>
                    <CollapsibleTrigger asChild>
                      <TableRow
                        className="cursor-pointer hover:bg-muted/50"
                        data-drifted={col.drifted}
                      >
                        <TableCell>
                          {expandedColumn === col.column ? (
                            <ChevronDown className="h-4 w-4" />
                          ) : (
                            <ChevronRight className="h-4 w-4" />
                          )}
                        </TableCell>
                        <TableCell className="font-medium">{col.column}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className="text-xs">
                            {col.dtype}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {col.drifted ? (
                            <AlertTriangle className="h-4 w-4 text-destructive" />
                          ) : (
                            <CheckCircle2 className="h-4 w-4 text-green-500" />
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge variant={getLevelBadgeVariant(col.level)}>
                            {col.level}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right font-mono text-xs">
                          {formatNumber(col.p_value, 4)}
                        </TableCell>
                        <TableCell className="text-right font-mono text-xs">
                          {formatNumber(col.statistic, 4)}
                        </TableCell>
                      </TableRow>
                    </CollapsibleTrigger>
                    <CollapsibleContent asChild>
                      <TableRow>
                        <TableCell colSpan={7} className="bg-muted/30 p-4">
                          <ColumnDistributionChart
                            column={col}
                          />
                        </TableCell>
                      </TableRow>
                    </CollapsibleContent>
                  </>
                </Collapsible>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
