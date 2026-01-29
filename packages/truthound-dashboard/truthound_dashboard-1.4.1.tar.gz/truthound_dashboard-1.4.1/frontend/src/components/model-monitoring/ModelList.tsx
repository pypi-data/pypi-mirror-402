/**
 * List of registered models for monitoring.
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
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { MoreHorizontal, Edit, Trash2, BarChart2, Loader2 } from 'lucide-react'
import { formatDate } from '@/lib/utils'

export interface RegisteredModel {
  id: string
  name: string
  version: string
  status: 'active' | 'paused' | 'degraded' | 'error'
  prediction_count: number
  last_prediction_at: string | null
  current_drift_score: number | null
  health_score: number
  created_at: string
}

interface ModelListProps {
  models: RegisteredModel[]
  isLoading: boolean
  onEdit: (model: RegisteredModel) => void
  onDelete: (model: RegisteredModel) => void
  onViewMetrics: (model: RegisteredModel) => void
}

export function ModelList({
  models,
  isLoading,
  onEdit,
  onDelete,
  onViewMetrics,
}: ModelListProps) {
  const t = useIntlayer('modelMonitoring')
  const common = useIntlayer('common')

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return (
          <Badge className="bg-green-500/10 text-green-500 border-green-500/20">
            {t.status.active}
          </Badge>
        )
      case 'paused':
        return (
          <Badge className="bg-gray-500/10 text-gray-500 border-gray-500/20">
            {t.status.paused}
          </Badge>
        )
      case 'degraded':
        return (
          <Badge className="bg-orange-500/10 text-orange-500 border-orange-500/20">
            {t.status.degraded}
          </Badge>
        )
      case 'error':
        return (
          <Badge className="bg-red-500/10 text-red-500 border-red-500/20">
            {t.status.error}
          </Badge>
        )
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  const getHealthColor = (score: number) => {
    if (score >= 80) return 'bg-green-500'
    if (score >= 60) return 'bg-yellow-500'
    if (score >= 40) return 'bg-orange-500'
    return 'bg-red-500'
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (models.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        {t.models.noModels}
      </div>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>{t.models.name}</TableHead>
          <TableHead>{t.models.version}</TableHead>
          <TableHead>{t.models.status}</TableHead>
          <TableHead className="text-right">{t.models.predictions}</TableHead>
          <TableHead>{t.models.lastPrediction}</TableHead>
          <TableHead>{t.models.driftScore}</TableHead>
          <TableHead>{t.models.healthScore}</TableHead>
          <TableHead className="w-[60px]" />
        </TableRow>
      </TableHeader>
      <TableBody>
        {models.map((model) => (
          <TableRow key={model.id}>
            <TableCell className="font-medium">{model.name}</TableCell>
            <TableCell>
              <Badge variant="outline">{model.version}</Badge>
            </TableCell>
            <TableCell>{getStatusBadge(model.status)}</TableCell>
            <TableCell className="text-right">
              {model.prediction_count.toLocaleString()}
            </TableCell>
            <TableCell className="text-muted-foreground text-sm">
              {model.last_prediction_at
                ? formatDate(model.last_prediction_at)
                : '-'}
            </TableCell>
            <TableCell>
              {model.current_drift_score !== null ? (
                <span
                  className={
                    model.current_drift_score > 0.1
                      ? 'text-orange-500'
                      : 'text-green-500'
                  }
                >
                  {(model.current_drift_score * 100).toFixed(1)}%
                </span>
              ) : (
                '-'
              )}
            </TableCell>
            <TableCell>
              <div className="flex items-center gap-2">
                <Progress
                  value={model.health_score}
                  className={`h-2 w-16 ${getHealthColor(model.health_score)}`}
                />
                <span className="text-sm">{model.health_score.toFixed(0)}%</span>
              </div>
            </TableCell>
            <TableCell>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => onViewMetrics(model)}>
                    <BarChart2 className="h-4 w-4 mr-2" />
                    View Metrics
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => onEdit(model)}>
                    <Edit className="h-4 w-4 mr-2" />
                    {common.edit}
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    className="text-destructive"
                    onClick={() => onDelete(model)}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    {common.delete}
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
