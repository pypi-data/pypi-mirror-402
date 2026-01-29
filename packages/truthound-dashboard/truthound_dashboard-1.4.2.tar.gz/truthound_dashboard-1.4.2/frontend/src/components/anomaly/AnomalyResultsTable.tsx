/**
 * Table displaying anomaly detection results.
 * Includes "Explain" button for SHAP/LIME explanations.
 */

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
import { Lightbulb } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { AnomalyRecord } from '@/api/client'

interface AnomalyResultsTableProps {
  anomalies: AnomalyRecord[]
  maxRows?: number
  onExplain?: (rowIndices: number[]) => void
}

export function AnomalyResultsTable({
  anomalies,
  maxRows = 50,
  onExplain,
}: AnomalyResultsTableProps) {
  const t = useIntlayer('anomaly')

  const displayedAnomalies = anomalies.slice(0, maxRows)

  if (anomalies.length === 0) {
    return (
      <div className="flex h-32 items-center justify-center text-muted-foreground">
        {t.noAnomaliesFound}
      </div>
    )
  }

  // Get all column names from the first anomaly
  const columnNames = Object.keys(anomalies[0]?.column_values || {})

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-24">{t.rowIndex}</TableHead>
            <TableHead className="w-32">{t.anomalyScore}</TableHead>
            {columnNames.map((col) => (
              <TableHead key={col}>{col}</TableHead>
            ))}
            {onExplain && (
              <TableHead className="w-24 text-right">{t.actions}</TableHead>
            )}
          </TableRow>
        </TableHeader>
        <TableBody>
          {displayedAnomalies.map((anomaly) => (
            <TableRow key={anomaly.row_index}>
              <TableCell className="font-mono text-sm">
                {anomaly.row_index}
              </TableCell>
              <TableCell>
                <ScoreBadge score={anomaly.anomaly_score} />
              </TableCell>
              {columnNames.map((col) => (
                <TableCell key={col} className="font-mono text-sm">
                  {formatValue(anomaly.column_values[col])}
                </TableCell>
              ))}
              {onExplain && (
                <TableCell className="text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onExplain([anomaly.row_index])}
                    title={String(t.explainAnomaly)}
                  >
                    <Lightbulb className="h-4 w-4 text-primary" />
                  </Button>
                </TableCell>
              )}
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {anomalies.length > maxRows && (
        <div className="border-t px-4 py-2 text-center text-sm text-muted-foreground">
          Showing {maxRows} of {anomalies.length} anomalies
        </div>
      )}
    </div>
  )
}

function ScoreBadge({ score }: { score: number }) {
  const severity =
    score >= 0.9
      ? 'critical'
      : score >= 0.7
        ? 'high'
        : score >= 0.5
          ? 'medium'
          : 'low'

  const colors = {
    critical: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
    high: 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300',
    medium: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
    low: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
  }

  return (
    <Badge
      variant="outline"
      className={cn('font-mono', colors[severity])}
    >
      {score.toFixed(4)}
    </Badge>
  )
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) {
    return '-'
  }
  if (typeof value === 'number') {
    return Number.isInteger(value) ? value.toString() : value.toFixed(2)
  }
  return String(value)
}
