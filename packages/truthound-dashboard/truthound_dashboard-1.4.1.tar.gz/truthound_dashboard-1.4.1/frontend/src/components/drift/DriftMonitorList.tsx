/**
 * Drift monitor list component.
 *
 * Displays list of drift monitors with status and actions.
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { formatDistanceToNow } from 'date-fns'
import {
  MoreHorizontal,
  Play,
  Pause,
  PlayCircle,
  Pencil,
  Trash2,
  AlertTriangle,
  CheckCircle,
  Loader2,
  Activity,
  Columns,
} from 'lucide-react'

export interface DriftMonitor {
  id: string
  name: string
  baseline_source_id: string
  current_source_id: string
  baseline_source_name?: string
  current_source_name?: string
  cron_expression: string
  method: string
  threshold: number
  status: 'active' | 'paused' | 'error'
  last_run_at: string | null
  last_drift_detected: boolean | null
  total_runs: number
  drift_detected_count: number
  consecutive_drift_count: number
  created_at: string
}

interface DriftMonitorListProps {
  monitors: DriftMonitor[]
  isLoading?: boolean
  onEdit?: (monitor: DriftMonitor) => void
  onDelete?: (monitor: DriftMonitor) => void
  onRun?: (monitor: DriftMonitor) => void
  onPause?: (monitor: DriftMonitor) => void
  onResume?: (monitor: DriftMonitor) => void
  onViewDetails?: (monitor: DriftMonitor) => void
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'active':
      return 'bg-green-500/10 text-green-500 border-green-500/20'
    case 'paused':
      return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
    case 'error':
      return 'bg-red-500/10 text-red-500 border-red-500/20'
    default:
      return 'bg-gray-500/10 text-gray-500 border-gray-500/20'
  }
}

export function DriftMonitorList({
  monitors,
  isLoading = false,
  onEdit,
  onDelete,
  onRun,
  onPause,
  onResume,
  onViewDetails,
}: DriftMonitorListProps) {
  const t = useIntlayer('driftMonitor')
  const common = useIntlayer('common')

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (monitors.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed py-12">
        <Activity className="h-8 w-8 text-muted-foreground" />
        <p className="text-muted-foreground">{t.empty.noMonitors}</p>
        <p className="text-sm text-muted-foreground">{t.empty.noMonitorsDesc}</p>
      </div>
    )
  }

  return (
    <div className="rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>{t.table.name}</TableHead>
            <TableHead>{t.table.sources}</TableHead>
            <TableHead>{t.table.schedule}</TableHead>
            <TableHead>{t.table.status}</TableHead>
            <TableHead>{t.table.lastRun}</TableHead>
            <TableHead>{t.table.driftStatus}</TableHead>
            <TableHead className="text-right">{t.table.actions}</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {monitors.map((monitor) => (
            <TableRow key={monitor.id}>
              <TableCell className="font-medium">{monitor.name}</TableCell>
              <TableCell>
                <div className="flex flex-col text-sm">
                  <span className="text-muted-foreground">
                    Base: {monitor.baseline_source_name || monitor.baseline_source_id.slice(0, 8)}
                  </span>
                  <span className="text-muted-foreground">
                    Current: {monitor.current_source_name || monitor.current_source_id.slice(0, 8)}
                  </span>
                </div>
              </TableCell>
              <TableCell>
                <code className="text-xs">{monitor.cron_expression}</code>
              </TableCell>
              <TableCell>
                <Badge variant="outline" className={getStatusColor(monitor.status)}>
                  {t.status[monitor.status as keyof typeof t.status]}
                </Badge>
              </TableCell>
              <TableCell>
                {monitor.last_run_at ? (
                  <span className="text-sm text-muted-foreground">
                    {formatDistanceToNow(new Date(monitor.last_run_at), { addSuffix: true })}
                  </span>
                ) : (
                  <span className="text-sm text-muted-foreground">-</span>
                )}
              </TableCell>
              <TableCell>
                {monitor.last_drift_detected === null ? (
                  <span className="text-sm text-muted-foreground">-</span>
                ) : monitor.last_drift_detected ? (
                  <div className="flex items-center gap-1">
                    <AlertTriangle className="h-4 w-4 text-orange-500" />
                    <span className="text-sm text-orange-500">
                      {monitor.consecutive_drift_count}x
                    </span>
                  </div>
                ) : (
                  <div className="flex items-center gap-1">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span className="text-sm text-green-500">OK</span>
                  </div>
                )}
              </TableCell>
              <TableCell className="text-right">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    {onRun && (
                      <DropdownMenuItem onClick={() => onRun(monitor)}>
                        <Play className="mr-2 h-4 w-4" />
                        {t.monitor.runNow}
                      </DropdownMenuItem>
                    )}
                    {monitor.status === 'active' && onPause && (
                      <DropdownMenuItem onClick={() => onPause(monitor)}>
                        <Pause className="mr-2 h-4 w-4" />
                        {t.monitor.pause}
                      </DropdownMenuItem>
                    )}
                    {monitor.status === 'paused' && onResume && (
                      <DropdownMenuItem onClick={() => onResume(monitor)}>
                        <PlayCircle className="mr-2 h-4 w-4" />
                        {t.monitor.resume}
                      </DropdownMenuItem>
                    )}
                    {onViewDetails && monitor.last_run_at && (
                      <DropdownMenuItem onClick={() => onViewDetails(monitor)}>
                        <Columns className="mr-2 h-4 w-4" />
                        {t.columnDrilldown?.viewDetails ?? 'View Details'}
                      </DropdownMenuItem>
                    )}
                    <DropdownMenuSeparator />
                    {onEdit && (
                      <DropdownMenuItem onClick={() => onEdit(monitor)}>
                        <Pencil className="mr-2 h-4 w-4" />
                        {common.edit}
                      </DropdownMenuItem>
                    )}
                    {onDelete && (
                      <DropdownMenuItem
                        onClick={() => onDelete(monitor)}
                        className="text-destructive"
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        {common.delete}
                      </DropdownMenuItem>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
