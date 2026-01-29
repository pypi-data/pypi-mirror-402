/**
 * Anomaly legend component for lineage visualization.
 *
 * Displays color coding explanation and filter options for anomaly status.
 */

import { memo } from 'react'
import {
  AlertTriangle,
  AlertCircle,
  CheckCircle,
  HelpCircle,
  Filter,
  Eye,
  EyeOff,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuCheckboxItem,
  DropdownMenuSeparator,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useIntlayer } from 'react-intlayer'
import type { AnomalyStatusLevel } from './AnomalyOverlayNode'
import type { ImpactSeverityLevel } from './AnomalyImpactPath'

export interface AnomalyLegendProps {
  showLegend?: boolean
  onToggleLegend?: () => void
  selectedStatuses?: AnomalyStatusLevel[]
  onStatusFilterChange?: (statuses: AnomalyStatusLevel[]) => void
  showImpactPaths?: boolean
  onToggleImpactPaths?: () => void
  className?: string
}

const statusConfig: Record<
  AnomalyStatusLevel,
  {
    icon: typeof AlertTriangle
    color: string
    bgColor: string
    label: string
    description: string
  }
> = {
  unknown: {
    icon: HelpCircle,
    color: 'text-muted-foreground',
    bgColor: 'bg-muted/50',
    label: 'Unknown',
    description: 'No anomaly detection run',
  },
  clean: {
    icon: CheckCircle,
    color: 'text-green-500',
    bgColor: 'bg-green-500/10',
    label: 'Clean',
    description: 'No anomalies detected',
  },
  low: {
    icon: AlertCircle,
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-500/10',
    label: 'Low',
    description: '0-5% anomaly rate',
  },
  medium: {
    icon: AlertTriangle,
    color: 'text-orange-500',
    bgColor: 'bg-orange-500/10',
    label: 'Medium',
    description: '5-15% anomaly rate',
  },
  high: {
    icon: AlertTriangle,
    color: 'text-red-500',
    bgColor: 'bg-red-500/10',
    label: 'High',
    description: '15%+ anomaly rate',
  },
}

const impactSeverityConfig: Record<
  ImpactSeverityLevel,
  { color: string; label: string }
> = {
  unknown: { color: '#94a3b8', label: 'Unknown' },
  none: { color: '#94a3b8', label: 'None' },
  low: { color: '#eab308', label: 'Low Impact' },
  medium: { color: '#f97316', label: 'Medium Impact' },
  high: { color: '#ef4444', label: 'High Impact' },
  critical: { color: '#dc2626', label: 'Critical Impact' },
}

export const AnomalyLegend = memo(function AnomalyLegend({
  showLegend = true,
  onToggleLegend,
  selectedStatuses = ['unknown', 'clean', 'low', 'medium', 'high'],
  onStatusFilterChange,
  showImpactPaths = true,
  onToggleImpactPaths,
  className,
}: AnomalyLegendProps) {
  const t = useIntlayer('lineage')

  const handleStatusToggle = (status: AnomalyStatusLevel) => {
    if (!onStatusFilterChange) return

    if (selectedStatuses.includes(status)) {
      onStatusFilterChange(selectedStatuses.filter((s) => s !== status))
    } else {
      onStatusFilterChange([...selectedStatuses, status])
    }
  }

  const allStatuses: AnomalyStatusLevel[] = ['unknown', 'clean', 'low', 'medium', 'high']
  const allSelected = allStatuses.every((s) => selectedStatuses.includes(s))
  const noneSelected = selectedStatuses.length === 0

  const handleSelectAll = () => {
    onStatusFilterChange?.(allStatuses)
  }

  const handleSelectNone = () => {
    onStatusFilterChange?.([])
  }

  if (!showLegend) {
    return (
      <Button
        variant="outline"
        size="sm"
        onClick={onToggleLegend}
        className={className}
      >
        <Eye className="h-4 w-4 mr-2" />
        {t.anomaly?.showLegend ?? 'Show Legend'}
      </Button>
    )
  }

  return (
    <Card className={cn('w-72', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">
            {t.anomaly?.legend ?? 'Anomaly Legend'}
          </CardTitle>
          <div className="flex items-center gap-1">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-7 w-7">
                  <Filter className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel>
                  {t.anomaly?.filterByStatus ?? 'Filter by Status'}
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                {allStatuses.map((status) => {
                  const config = statusConfig[status]
                  const Icon = config.icon
                  return (
                    <DropdownMenuCheckboxItem
                      key={status}
                      checked={selectedStatuses.includes(status)}
                      onCheckedChange={() => handleStatusToggle(status)}
                    >
                      <Icon className={cn('h-4 w-4 mr-2', config.color)} />
                      {config.label}
                    </DropdownMenuCheckboxItem>
                  )
                })}
                <DropdownMenuSeparator />
                <DropdownMenuCheckboxItem
                  checked={allSelected}
                  onCheckedChange={allSelected ? handleSelectNone : handleSelectAll}
                >
                  {allSelected
                    ? t.anomaly?.deselectAll ?? 'Deselect All'
                    : t.anomaly?.selectAll ?? 'Select All'}
                </DropdownMenuCheckboxItem>
              </DropdownMenuContent>
            </DropdownMenu>
            {onToggleLegend && (
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onToggleLegend}>
                <EyeOff className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Anomaly Status Section */}
        <div className="space-y-2">
          <div className="text-xs font-medium text-muted-foreground">
            {t.anomaly?.nodeStatus ?? 'Node Anomaly Status'}
          </div>
          <div className="space-y-1">
            {allStatuses.map((status) => {
              const config = statusConfig[status]
              const Icon = config.icon
              const isActive = selectedStatuses.includes(status)
              return (
                <div
                  key={status}
                  className={cn(
                    'flex items-center gap-2 py-1 px-2 rounded-md transition-opacity cursor-pointer hover:bg-muted/50',
                    !isActive && 'opacity-40'
                  )}
                  onClick={() => handleStatusToggle(status)}
                >
                  <Badge
                    variant="outline"
                    className={cn(
                      'h-5 w-5 rounded-full p-0 flex items-center justify-center',
                      config.bgColor
                    )}
                  >
                    <Icon className={cn('h-3 w-3', config.color)} />
                  </Badge>
                  <div className="flex-1">
                    <div className="text-xs font-medium">{config.label}</div>
                    <div className="text-[10px] text-muted-foreground">
                      {config.description}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Impact Path Section */}
        <div className="space-y-2 pt-2 border-t">
          <div className="flex items-center justify-between">
            <div className="text-xs font-medium text-muted-foreground">
              {t.anomaly?.impactPaths ?? 'Impact Paths'}
            </div>
            {onToggleImpactPaths && (
              <Button
                variant="ghost"
                size="sm"
                className="h-6 text-xs"
                onClick={onToggleImpactPaths}
              >
                {showImpactPaths
                  ? t.anomaly?.hidePaths ?? 'Hide'
                  : t.anomaly?.showPaths ?? 'Show'}
              </Button>
            )}
          </div>
          {showImpactPaths && (
            <div className="space-y-1">
              {(['low', 'medium', 'high', 'critical'] as ImpactSeverityLevel[]).map(
                (severity) => {
                  const config = impactSeverityConfig[severity]
                  return (
                    <div key={severity} className="flex items-center gap-2 py-1">
                      <div className="flex items-center gap-1">
                        <div
                          className="w-8 h-0.5"
                          style={{
                            backgroundColor: config.color,
                            height: severity === 'critical' ? 4 : severity === 'high' ? 3 : 2,
                          }}
                        />
                        {(severity === 'high' || severity === 'critical') && (
                          <div
                            className="w-4 h-0.5 animate-pulse"
                            style={{ backgroundColor: config.color }}
                          />
                        )}
                      </div>
                      <span className="text-xs">{config.label}</span>
                    </div>
                  )
                }
              )}
            </div>
          )}
        </div>

        {/* Stats */}
        {noneSelected && (
          <div className="text-xs text-center text-muted-foreground pt-2 border-t">
            {t.anomaly?.noNodesVisible ?? 'All nodes hidden by filter'}
          </div>
        )}
      </CardContent>
    </Card>
  )
})
