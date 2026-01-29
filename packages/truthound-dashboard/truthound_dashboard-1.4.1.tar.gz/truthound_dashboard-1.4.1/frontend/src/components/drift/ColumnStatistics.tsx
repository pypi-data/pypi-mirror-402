/**
 * Column statistics comparison table.
 *
 * Displays baseline vs current statistics with change indicators.
 */

import { useIntlayer } from 'react-intlayer'
import { str } from '@/lib/intlayer-utils'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { ArrowUp, ArrowDown, Minus } from 'lucide-react'
import { cn } from '@/lib/utils'

interface StatValue {
  mean?: number
  std?: number
  min?: number
  max?: number
  median?: number
  count?: number
  null_count?: number
  unique_count?: number
  q25?: number
  q75?: number
  [key: string]: unknown
}

interface ColumnStatisticsProps {
  baselineStats: StatValue
  currentStats: StatValue
  className?: string
}

// Format number for display
function formatNumber(value: unknown): string {
  if (value === undefined || value === null) return '-'
  if (typeof value !== 'number') return String(value)
  if (Number.isInteger(value)) return value.toLocaleString()
  return value.toFixed(2)
}

// Calculate percentage change
function getPercentageChange(baseline: number | undefined, current: number | undefined): number | null {
  if (baseline === undefined || current === undefined || baseline === 0) return null
  return ((current - baseline) / Math.abs(baseline)) * 100
}

// Get change indicator
function ChangeIndicator({ baseline, current }: { baseline: number | undefined; current: number | undefined }) {
  const change = getPercentageChange(baseline, current)

  if (change === null) {
    return <Minus className="h-3 w-3 text-muted-foreground" />
  }

  const absChange = Math.abs(change)
  const isIncrease = change > 0
  const isSigChange = absChange > 5 // More than 5% change is significant

  if (absChange < 0.1) {
    return <Minus className="h-3 w-3 text-muted-foreground" />
  }

  return (
    <div className={cn(
      'flex items-center gap-1 text-xs',
      isIncrease
        ? isSigChange ? 'text-orange-500' : 'text-muted-foreground'
        : isSigChange ? 'text-blue-500' : 'text-muted-foreground'
    )}>
      {isIncrease ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
      <span>{absChange.toFixed(1)}%</span>
    </div>
  )
}

export function ColumnStatistics({
  baselineStats,
  currentStats,
  className,
}: ColumnStatisticsProps) {
  const t = useIntlayer('driftMonitor')

  // Define the statistics rows to display
  const statRows: { key: keyof StatValue; label: string }[] = [
    { key: 'mean', label: str(t.columnStats?.mean) || 'Mean' },
    { key: 'std', label: str(t.columnStats?.std) || 'Std Dev' },
    { key: 'median', label: str(t.columnStats?.median) || 'Median' },
    { key: 'min', label: str(t.columnStats?.min) || 'Min' },
    { key: 'max', label: str(t.columnStats?.max) || 'Max' },
    { key: 'q25', label: str(t.columnStats?.q25) || '25th %ile' },
    { key: 'q75', label: str(t.columnStats?.q75) || '75th %ile' },
    { key: 'count', label: str(t.columnStats?.count) || 'Count' },
    { key: 'null_count', label: str(t.columnStats?.nullCount) || 'Null Count' },
    { key: 'unique_count', label: str(t.columnStats?.uniqueCount) || 'Unique Count' },
  ]

  // Filter to only show stats that exist in either baseline or current
  const visibleRows = statRows.filter(
    row => baselineStats[row.key] !== undefined || currentStats[row.key] !== undefined
  )

  return (
    <div className={cn('rounded-lg border', className)}>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[150px]">{t.columnStats?.statistic ?? 'Statistic'}</TableHead>
            <TableHead className="text-right">{t.columnStats?.baseline ?? 'Baseline'}</TableHead>
            <TableHead className="text-right">{t.columnStats?.current ?? 'Current'}</TableHead>
            <TableHead className="text-right w-[100px]">{t.columnStats?.change ?? 'Change'}</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {visibleRows.map(({ key, label }) => {
            const baseline = baselineStats[key] as number | undefined
            const current = currentStats[key] as number | undefined

            return (
              <TableRow key={key}>
                <TableCell className="font-medium">{label}</TableCell>
                <TableCell className="text-right font-mono text-sm">
                  {formatNumber(baseline)}
                </TableCell>
                <TableCell className="text-right font-mono text-sm">
                  {formatNumber(current)}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end">
                    <ChangeIndicator baseline={baseline} current={current} />
                  </div>
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}
