/**
 * Summary of anomalies by column.
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
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import type { ColumnAnomalySummary as ColumnAnomalySummaryType } from '@/api/client'

interface ColumnAnomalySummaryProps {
  summaries: ColumnAnomalySummaryType[]
}

export function ColumnAnomalySummary({ summaries }: ColumnAnomalySummaryProps) {
  const t = useIntlayer('anomaly')

  if (summaries.length === 0) {
    return null
  }

  // Sort by anomaly count descending
  const sortedSummaries = [...summaries].sort(
    (a, b) => b.anomaly_count - a.anomaly_count
  )

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>{t.columnName}</TableHead>
            <TableHead className="w-24">Type</TableHead>
            <TableHead className="w-32">{t.columnAnomalies}</TableHead>
            <TableHead className="w-40">Rate</TableHead>
            <TableHead className="w-24">{t.meanScore}</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sortedSummaries.map((summary) => (
            <TableRow key={summary.column}>
              <TableCell className="font-medium">{summary.column}</TableCell>
              <TableCell>
                <Badge variant="outline" className="font-mono text-xs">
                  {summary.dtype}
                </Badge>
              </TableCell>
              <TableCell className="font-mono text-sm">
                {summary.anomaly_count}
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <Progress
                    value={summary.anomaly_rate * 100}
                    className="h-2 w-16"
                  />
                  <span className="text-sm text-muted-foreground">
                    {(summary.anomaly_rate * 100).toFixed(1)}%
                  </span>
                </div>
              </TableCell>
              <TableCell className="font-mono text-sm">
                {summary.mean_anomaly_score.toFixed(3)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
