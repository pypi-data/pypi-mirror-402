/**
 * List of past anomaly detection runs.
 */

import { useIntlayer } from 'react-intlayer'
import { formatDistanceToNow } from '@/lib/utils'
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
import { Eye, AlertTriangle, CheckCircle2, Clock, XCircle, Loader2 } from 'lucide-react'
import type { AnomalyDetection } from '@/api/client'

interface AnomalyHistoryListProps {
  detections: AnomalyDetection[]
  onViewDetails: (detection: AnomalyDetection) => void
  isLoading?: boolean
}

export function AnomalyHistoryList({
  detections,
  onViewDetails,
  isLoading,
}: AnomalyHistoryListProps) {
  const t = useIntlayer('anomaly')

  const getStatusIcon = (status: AnomalyDetection['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'running':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
      default:
        return <Clock className="h-4 w-4 text-muted-foreground" />
    }
  }

  if (isLoading) {
    return (
      <div className="flex h-32 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (detections.length === 0) {
    return (
      <div className="flex h-32 flex-col items-center justify-center gap-2 rounded-lg border border-dashed">
        <AlertTriangle className="h-8 w-8 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">{t.noHistory}</p>
      </div>
    )
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-10">{t.statusLabel}</TableHead>
            <TableHead>{t.algorithm}</TableHead>
            <TableHead className="w-24">{t.anomalyCount}</TableHead>
            <TableHead className="w-24">{t.anomalyRate}</TableHead>
            <TableHead className="w-24">{t.duration}</TableHead>
            <TableHead className="w-32">{t.runAt}</TableHead>
            <TableHead className="w-16"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {detections.map((detection) => (
            <TableRow key={detection.id}>
              <TableCell>
                <div className="flex items-center gap-2">
                  {getStatusIcon(detection.status)}
                </div>
              </TableCell>
              <TableCell>
                <Badge variant="outline" className="font-mono text-xs">
                  {detection.algorithm}
                </Badge>
              </TableCell>
              <TableCell className="font-mono text-sm">
                {detection.anomaly_count ?? '-'}
              </TableCell>
              <TableCell className="font-mono text-sm">
                {detection.anomaly_rate != null
                  ? `${(detection.anomaly_rate * 100).toFixed(1)}%`
                  : '-'}
              </TableCell>
              <TableCell className="font-mono text-sm">
                {detection.duration_ms != null
                  ? `${(detection.duration_ms / 1000).toFixed(1)}s`
                  : '-'}
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {formatDistanceToNow(detection.created_at)}
              </TableCell>
              <TableCell>
                {detection.status === 'success' && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onViewDetails(detection)}
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
