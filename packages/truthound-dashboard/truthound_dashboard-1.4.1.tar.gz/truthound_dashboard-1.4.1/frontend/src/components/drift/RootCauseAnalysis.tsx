/**
 * Root Cause Analysis Component
 *
 * Displays detailed root cause analysis for a drift run,
 * including per-column breakdown, causes, and severity indicators.
 */

import { useIntlayer } from 'react-intlayer'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  BarChart3,
  Database,
  Clock,
  Info,
  Loader2,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react'

// Types
export interface StatisticalShift {
  baseline_value: number
  current_value: number
  absolute_change: number
  percent_change: number
}

export interface ColumnRootCause {
  column: string
  dtype: string
  drift_level: string
  causes: string[]
  primary_cause: string | null
  confidence: number
  mean_shift: StatisticalShift | null
  std_shift: StatisticalShift | null
  min_shift: StatisticalShift | null
  max_shift: StatisticalShift | null
  new_categories: Array<{ category: string; current_count: number; current_percentage: number }>
  missing_categories: Array<{
    category: string
    baseline_count: number
    baseline_percentage: number
  }>
  null_rate_baseline: number | null
  null_rate_current: number | null
}

export interface DataVolumeChange {
  baseline_rows: number
  current_rows: number
  absolute_change: number
  percent_change: number
  significance: string
}

export interface RemediationSuggestion {
  action: string
  priority: number
  title: string
  description: string
  affected_columns: string[]
  estimated_impact: string
  requires_manual_review: boolean
  automation_available: boolean
}

export interface RootCauseAnalysisData {
  run_id: string
  monitor_id: string | null
  analyzed_at: string
  total_columns: number
  drifted_columns: number
  drift_percentage: number
  data_volume_change: DataVolumeChange | null
  column_analyses: ColumnRootCause[]
  primary_causes: string[]
  cause_distribution: Record<string, number>
  remediations?: RemediationSuggestion[]
  overall_confidence: number
  analysis_duration_ms: number
}

interface RootCauseAnalysisProps {
  data: RootCauseAnalysisData | null
  isLoading?: boolean
  error?: string | null
}

// Helper functions
const getCauseIcon = (cause: string) => {
  switch (cause) {
    case 'mean_shift':
      return <TrendingUp className="h-4 w-4" />
    case 'variance_change':
      return <BarChart3 className="h-4 w-4" />
    case 'outlier_introduction':
      return <AlertTriangle className="h-4 w-4" />
    case 'data_volume_change':
      return <Database className="h-4 w-4" />
    case 'temporal_pattern':
      return <Clock className="h-4 w-4" />
    default:
      return <Info className="h-4 w-4" />
  }
}

const getCauseColor = (cause: string): string => {
  switch (cause) {
    case 'mean_shift':
      return 'bg-orange-500/10 text-orange-500 border-orange-500/20'
    case 'variance_change':
      return 'bg-purple-500/10 text-purple-500 border-purple-500/20'
    case 'outlier_introduction':
      return 'bg-red-500/10 text-red-500 border-red-500/20'
    case 'data_volume_change':
      return 'bg-blue-500/10 text-blue-500 border-blue-500/20'
    case 'temporal_pattern':
      return 'bg-cyan-500/10 text-cyan-500 border-cyan-500/20'
    case 'distribution_shape_change':
      return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
    case 'null_rate_change':
      return 'bg-gray-500/10 text-gray-500 border-gray-500/20'
    default:
      return 'bg-slate-500/10 text-slate-500 border-slate-500/20'
  }
}

const getDriftLevelColor = (level: string): string => {
  switch (level) {
    case 'high':
      return 'bg-red-500/10 text-red-500 border-red-500/20'
    case 'medium':
      return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
    case 'low':
      return 'bg-blue-500/10 text-blue-500 border-blue-500/20'
    default:
      return 'bg-green-500/10 text-green-500 border-green-500/20'
  }
}

const formatNumber = (value: number | null | undefined, decimals = 2): string => {
  if (value === null || value === undefined) return '-'
  return value.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

const formatPercent = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return '-'
  const sign = value >= 0 ? '+' : ''
  return `${sign}${formatNumber(value)}%`
}

export function RootCauseAnalysis({ data, isLoading = false, error = null }: RootCauseAnalysisProps) {
  const t = useIntlayer('driftMonitor')

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error) {
    return (
      <Card className="border-red-500/20">
        <CardContent className="flex items-center gap-3 p-6">
          <AlertCircle className="h-5 w-5 text-red-500" />
          <span className="text-red-500">{error}</span>
        </CardContent>
      </Card>
    )
  }

  if (!data) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center gap-2 py-12">
          <Info className="h-8 w-8 text-muted-foreground" />
          <p className="text-muted-foreground">{t.rootCause?.noAnalysis ?? 'No analysis available'}</p>
        </CardContent>
      </Card>
    )
  }

  const driftedColumns = data.column_analyses.filter((c) => c.causes.length > 0)
  const sortedCauses = Object.entries(data.cause_distribution).sort(([, a], [, b]) => b - a)

  return (
    <div className="space-y-6">
      {/* Summary Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            {t.rootCause?.title ?? 'Root Cause Analysis'}
          </CardTitle>
          <CardDescription>
            {t.rootCause?.subtitle ?? 'Detailed analysis of why drift is occurring'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {/* Total Columns */}
            <div className="rounded-lg border p-4">
              <div className="text-sm text-muted-foreground">
                {t.rootCause?.totalColumns ?? 'Total Columns'}
              </div>
              <div className="text-2xl font-bold">{data.total_columns}</div>
            </div>

            {/* Drifted Columns */}
            <div className="rounded-lg border p-4">
              <div className="text-sm text-muted-foreground">
                {t.rootCause?.driftedColumns ?? 'Drifted Columns'}
              </div>
              <div className="text-2xl font-bold text-orange-500">{data.drifted_columns}</div>
              <div className="text-sm text-muted-foreground">
                ({formatNumber(data.drift_percentage)}%)
              </div>
            </div>

            {/* Confidence */}
            <div className="rounded-lg border p-4">
              <div className="text-sm text-muted-foreground">
                {t.rootCause?.confidence ?? 'Confidence'}
              </div>
              <div className="mt-1 flex items-center gap-2">
                <Progress value={data.overall_confidence * 100} className="h-2 flex-1" />
                <span className="text-sm font-medium">
                  {formatNumber(data.overall_confidence * 100, 0)}%
                </span>
              </div>
            </div>

            {/* Analysis Time */}
            <div className="rounded-lg border p-4">
              <div className="text-sm text-muted-foreground">
                {t.rootCause?.analysisTime ?? 'Analysis Time'}
              </div>
              <div className="text-2xl font-bold">{data.analysis_duration_ms}ms</div>
            </div>
          </div>

          {/* Data Volume Change */}
          {data.data_volume_change && (
            <div className="mt-4 rounded-lg border p-4">
              <div className="mb-2 flex items-center gap-2 text-sm font-medium">
                <Database className="h-4 w-4" />
                {t.rootCause?.volumeChange ?? 'Data Volume Change'}
                <Badge
                  variant="outline"
                  className={
                    data.data_volume_change.significance === 'critical'
                      ? 'bg-red-500/10 text-red-500'
                      : data.data_volume_change.significance === 'significant'
                        ? 'bg-orange-500/10 text-orange-500'
                        : data.data_volume_change.significance === 'notable'
                          ? 'bg-yellow-500/10 text-yellow-500'
                          : 'bg-green-500/10 text-green-500'
                  }
                >
                  {data.data_volume_change.significance}
                </Badge>
              </div>
              <div className="grid gap-4 sm:grid-cols-3">
                <div>
                  <div className="text-xs text-muted-foreground">Baseline</div>
                  <div className="font-medium">
                    {data.data_volume_change.baseline_rows.toLocaleString()} rows
                  </div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">Current</div>
                  <div className="font-medium">
                    {data.data_volume_change.current_rows.toLocaleString()} rows
                  </div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">Change</div>
                  <div className="flex items-center gap-1 font-medium">
                    {data.data_volume_change.percent_change >= 0 ? (
                      <TrendingUp className="h-4 w-4 text-green-500" />
                    ) : (
                      <TrendingDown className="h-4 w-4 text-red-500" />
                    )}
                    {formatPercent(data.data_volume_change.percent_change)}
                  </div>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Cause Distribution */}
      {sortedCauses.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              {t.rootCause?.causeDistribution ?? 'Cause Distribution'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {sortedCauses.map(([cause, count]) => (
                <Badge key={cause} variant="outline" className={`gap-1 ${getCauseColor(cause)}`}>
                  {getCauseIcon(cause)}
                  <span className="capitalize">{cause.replace(/_/g, ' ')}</span>
                  <span className="ml-1 rounded-full bg-background px-1.5 text-xs">{count}</span>
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Per-Column Analysis */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            {t.rootCause?.columnAnalysis ?? 'Column Analysis'}
          </CardTitle>
          <CardDescription>
            {t.rootCause?.columnAnalysisDesc ?? 'Detailed breakdown by column'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Accordion type="multiple" className="w-full">
            {driftedColumns.map((col) => (
              <AccordionItem key={col.column} value={col.column}>
                <AccordionTrigger className="hover:no-underline">
                  <div className="flex flex-1 items-center justify-between gap-4 pr-4">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm">{col.column}</span>
                      <Badge variant="outline" className="text-xs">
                        {col.dtype}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className={getDriftLevelColor(col.drift_level)}>
                        {col.drift_level}
                      </Badge>
                      {col.primary_cause && (
                        <Badge variant="outline" className={getCauseColor(col.primary_cause)}>
                          {col.primary_cause.replace(/_/g, ' ')}
                        </Badge>
                      )}
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger>
                            <div className="flex items-center gap-1 text-xs text-muted-foreground">
                              <CheckCircle2 className="h-3 w-3" />
                              {formatNumber(col.confidence * 100, 0)}%
                            </div>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>Confidence in analysis</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>
                  </div>
                </AccordionTrigger>
                <AccordionContent>
                  <div className="space-y-4 pt-2">
                    {/* Causes */}
                    {col.causes.length > 0 && (
                      <div>
                        <div className="mb-2 text-sm font-medium">
                          {t.rootCause?.detectedCauses ?? 'Detected Causes'}
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {col.causes.map((cause) => (
                            <Badge key={cause} variant="outline" className={getCauseColor(cause)}>
                              {getCauseIcon(cause)}
                              <span className="ml-1 capitalize">{cause.replace(/_/g, ' ')}</span>
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Statistical Shifts Table */}
                    {(col.mean_shift || col.std_shift || col.min_shift || col.max_shift) && (
                      <div>
                        <div className="mb-2 text-sm font-medium">
                          {t.rootCause?.statisticalShifts ?? 'Statistical Shifts'}
                        </div>
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Metric</TableHead>
                              <TableHead className="text-right">Baseline</TableHead>
                              <TableHead className="text-right">Current</TableHead>
                              <TableHead className="text-right">Change</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {col.mean_shift && (
                              <TableRow>
                                <TableCell className="font-medium">Mean</TableCell>
                                <TableCell className="text-right">
                                  {formatNumber(col.mean_shift.baseline_value)}
                                </TableCell>
                                <TableCell className="text-right">
                                  {formatNumber(col.mean_shift.current_value)}
                                </TableCell>
                                <TableCell
                                  className={`text-right ${col.mean_shift.percent_change > 10 ? 'text-orange-500' : ''}`}
                                >
                                  {formatPercent(col.mean_shift.percent_change)}
                                </TableCell>
                              </TableRow>
                            )}
                            {col.std_shift && (
                              <TableRow>
                                <TableCell className="font-medium">Std Dev</TableCell>
                                <TableCell className="text-right">
                                  {formatNumber(col.std_shift.baseline_value)}
                                </TableCell>
                                <TableCell className="text-right">
                                  {formatNumber(col.std_shift.current_value)}
                                </TableCell>
                                <TableCell
                                  className={`text-right ${col.std_shift.percent_change > 20 ? 'text-purple-500' : ''}`}
                                >
                                  {formatPercent(col.std_shift.percent_change)}
                                </TableCell>
                              </TableRow>
                            )}
                            {col.min_shift && (
                              <TableRow>
                                <TableCell className="font-medium">Min</TableCell>
                                <TableCell className="text-right">
                                  {formatNumber(col.min_shift.baseline_value)}
                                </TableCell>
                                <TableCell className="text-right">
                                  {formatNumber(col.min_shift.current_value)}
                                </TableCell>
                                <TableCell className="text-right">
                                  {formatPercent(col.min_shift.percent_change)}
                                </TableCell>
                              </TableRow>
                            )}
                            {col.max_shift && (
                              <TableRow>
                                <TableCell className="font-medium">Max</TableCell>
                                <TableCell className="text-right">
                                  {formatNumber(col.max_shift.baseline_value)}
                                </TableCell>
                                <TableCell className="text-right">
                                  {formatNumber(col.max_shift.current_value)}
                                </TableCell>
                                <TableCell
                                  className={`text-right ${col.max_shift.percent_change > 50 ? 'text-red-500' : ''}`}
                                >
                                  {formatPercent(col.max_shift.percent_change)}
                                </TableCell>
                              </TableRow>
                            )}
                          </TableBody>
                        </Table>
                      </div>
                    )}

                    {/* Null Rate */}
                    {(col.null_rate_baseline !== null || col.null_rate_current !== null) && (
                      <div className="flex items-center gap-4 text-sm">
                        <span className="text-muted-foreground">Null Rate:</span>
                        <span>
                          Baseline: {formatNumber((col.null_rate_baseline ?? 0) * 100)}%
                        </span>
                        <span>Current: {formatNumber((col.null_rate_current ?? 0) * 100)}%</span>
                      </div>
                    )}
                  </div>
                </AccordionContent>
              </AccordionItem>
            ))}

            {driftedColumns.length === 0 && (
              <div className="flex items-center justify-center py-8 text-muted-foreground">
                <CheckCircle2 className="mr-2 h-5 w-5 text-green-500" />
                {t.rootCause?.noDrift ?? 'No drift detected in any columns'}
              </div>
            )}
          </Accordion>
        </CardContent>
      </Card>
    </div>
  )
}
