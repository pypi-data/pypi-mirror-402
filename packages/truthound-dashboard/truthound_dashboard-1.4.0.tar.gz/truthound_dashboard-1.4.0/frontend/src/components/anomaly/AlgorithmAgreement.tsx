/**
 * Algorithm agreement view component.
 *
 * Shows rows detected by all/some/one algorithm with confidence scores.
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
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
// Tabs imported but currently unused - keeping for potential future use
// import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Users,
  Shield,
  ShieldCheck,
  ShieldAlert,
  ShieldQuestion,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { AlgorithmComparisonResult, AgreementLevel } from '@/api/client'

interface AlgorithmAgreementProps {
  result: AlgorithmComparisonResult
}

const agreementLevelConfig: Record<
  AgreementLevel,
  {
    label: string
    icon: typeof Users
    color: string
    bgColor: string
    description: string
  }
> = {
  all: {
    label: 'All Agree',
    icon: ShieldCheck,
    color: 'text-green-500',
    bgColor: 'bg-green-500/10',
    description: 'Detected by all algorithms - highest confidence',
  },
  majority: {
    label: 'Majority',
    icon: Shield,
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/10',
    description: 'Detected by more than half of algorithms',
  },
  some: {
    label: 'Some',
    icon: ShieldAlert,
    color: 'text-amber-500',
    bgColor: 'bg-amber-500/10',
    description: 'Detected by at least 2 algorithms',
  },
  one: {
    label: 'One Only',
    icon: ShieldQuestion,
    color: 'text-red-500',
    bgColor: 'bg-red-500/10',
    description: 'Detected by only 1 algorithm - needs review',
  },
}

export function AlgorithmAgreement({ result }: AlgorithmAgreementProps) {
  const t = useIntlayer('anomaly')
  const [activeFilter, setActiveFilter] = useState<'all' | AgreementLevel>('all')

  const summary = result.agreement_summary
  const records = result.agreement_records || []

  // Filter records by agreement level
  const filteredRecords = useMemo(() => {
    if (activeFilter === 'all') return records
    return records.filter((r) => r.agreement_level === activeFilter)
  }, [records, activeFilter])

  // Get display names map
  const algorithmDisplayNames = useMemo(() => {
    const map: Record<string, string> = {}
    result.algorithm_results.forEach((r) => {
      map[r.algorithm] = r.display_name
    })
    return map
  }, [result.algorithm_results])

  if (!summary) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-2 rounded-lg border border-dashed">
        <Users className="h-8 w-8 text-muted-foreground" />
        <p className="text-muted-foreground">
          {t.comparison?.noAgreementData ?? 'No agreement data available'}
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {(['all', 'majority', 'some', 'one'] as const).map((level) => {
          const config = agreementLevelConfig[level]
          const Icon = config.icon
          const count =
            level === 'all'
              ? summary.all_agree_count
              : level === 'majority'
                ? summary.majority_agree_count
                : level === 'some'
                  ? summary.some_agree_count
                  : summary.one_only_count

          return (
            <Card
              key={level}
              className={cn(
                'cursor-pointer transition-all hover:border-primary/50',
                activeFilter === level && 'border-primary ring-2 ring-primary/20'
              )}
              onClick={() => setActiveFilter(level)}
            >
              <CardContent className="pt-4">
                <div className="flex items-center justify-between">
                  <div className={cn('rounded-lg p-2', config.bgColor)}>
                    <Icon className={cn('h-5 w-5', config.color)} />
                  </div>
                  <p className="text-2xl font-bold">{count}</p>
                </div>
                <p className="mt-2 text-sm font-medium">
                  {t.comparison?.agreementLevels?.[level] ?? config.label}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">{config.description}</p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Overall Stats */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">
            {t.comparison?.agreementOverview ?? 'Agreement Overview'}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              {t.comparison?.totalUniqueAnomalies ?? 'Total Unique Anomalies'}
            </span>
            <span className="font-medium">
              {summary.total_unique_anomalies.toLocaleString()}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              {t.comparison?.algorithmsCompared ?? 'Algorithms Compared'}
            </span>
            <span className="font-medium">{summary.total_algorithms}</span>
          </div>

          {/* Agreement distribution bar */}
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              {t.comparison?.agreementDistribution ?? 'Agreement Distribution'}
            </p>
            <div className="flex h-4 overflow-hidden rounded-full">
              {summary.all_agree_count > 0 && (
                <div
                  className="bg-green-500"
                  style={{
                    width: `${(summary.all_agree_count / summary.total_unique_anomalies) * 100}%`,
                  }}
                  title={`All: ${summary.all_agree_count}`}
                />
              )}
              {summary.majority_agree_count > 0 && (
                <div
                  className="bg-blue-500"
                  style={{
                    width: `${(summary.majority_agree_count / summary.total_unique_anomalies) * 100}%`,
                  }}
                  title={`Majority: ${summary.majority_agree_count}`}
                />
              )}
              {summary.some_agree_count > 0 && (
                <div
                  className="bg-amber-500"
                  style={{
                    width: `${(summary.some_agree_count / summary.total_unique_anomalies) * 100}%`,
                  }}
                  title={`Some: ${summary.some_agree_count}`}
                />
              )}
              {summary.one_only_count > 0 && (
                <div
                  className="bg-red-500"
                  style={{
                    width: `${(summary.one_only_count / summary.total_unique_anomalies) * 100}%`,
                  }}
                  title={`One: ${summary.one_only_count}`}
                />
              )}
            </div>
            <div className="flex flex-wrap gap-4 text-xs">
              <div className="flex items-center gap-1">
                <div className="h-2 w-2 rounded-full bg-green-500" />
                <span>All ({summary.all_agree_count})</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="h-2 w-2 rounded-full bg-blue-500" />
                <span>Majority ({summary.majority_agree_count})</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="h-2 w-2 rounded-full bg-amber-500" />
                <span>Some ({summary.some_agree_count})</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="h-2 w-2 rounded-full bg-red-500" />
                <span>One ({summary.one_only_count})</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Agreement Records Table */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">
              {t.comparison?.anomalyRecords ?? 'Anomaly Records'}
            </CardTitle>
            <Badge variant="outline">
              {filteredRecords.length} {t.comparison?.records ?? 'records'}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-20">
                    {t.comparison?.rowIndex ?? 'Row'}
                  </TableHead>
                  <TableHead>
                    {t.comparison?.detectedBy ?? 'Detected By'}
                  </TableHead>
                  <TableHead className="w-32">
                    {t.comparison?.agreementLevel ?? 'Agreement'}
                  </TableHead>
                  <TableHead className="w-32">
                    {t.comparison?.confidence ?? 'Confidence'}
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredRecords.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="h-24 text-center">
                      <p className="text-muted-foreground">
                        {t.comparison?.noRecordsFound ?? 'No records found'}
                      </p>
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredRecords.slice(0, 50).map((record) => {
                    const levelConfig = agreementLevelConfig[record.agreement_level]
                    const LevelIcon = levelConfig.icon

                    return (
                      <TableRow key={record.row_index}>
                        <TableCell className="font-mono">
                          {record.row_index}
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {record.detected_by.map((algo) => (
                              <Badge key={algo} variant="secondary" className="text-xs">
                                {algorithmDisplayNames[algo] || algo}
                              </Badge>
                            ))}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant="outline"
                            className={cn('gap-1', levelConfig.color)}
                          >
                            <LevelIcon className="h-3 w-3" />
                            {levelConfig.label}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Progress
                              value={record.confidence_score * 100}
                              className="h-2 w-16"
                            />
                            <span className="text-sm font-medium">
                              {(record.confidence_score * 100).toFixed(0)}%
                            </span>
                          </div>
                        </TableCell>
                      </TableRow>
                    )
                  })
                )}
              </TableBody>
            </Table>
          </div>
          {filteredRecords.length > 50 && (
            <p className="mt-2 text-center text-sm text-muted-foreground">
              {t.comparison?.showingFirst50 ?? 'Showing first 50 records'}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
