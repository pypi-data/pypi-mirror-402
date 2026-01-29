/**
 * Alert rule list component for model monitoring.
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
import { Switch } from '@/components/ui/switch'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { MoreHorizontal, Edit, Trash2, Loader2 } from 'lucide-react'
import { formatDate } from '@/lib/utils'

export interface AlertRule {
  id: string
  name: string
  model_id: string
  rule_type: 'threshold' | 'statistical' | 'trend'
  severity: 'critical' | 'warning' | 'info'
  config: Record<string, unknown>
  is_active: boolean
  last_triggered_at: string | null
  trigger_count: number
  created_at: string
}

interface AlertRuleListProps {
  rules: AlertRule[]
  isLoading: boolean
  onEdit: (rule: AlertRule) => void
  onDelete: (rule: AlertRule) => void
  onToggle: (rule: AlertRule) => void
}

export function AlertRuleList({
  rules,
  isLoading,
  onEdit,
  onDelete,
  onToggle,
}: AlertRuleListProps) {
  const t = useIntlayer('modelMonitoring')
  const common = useIntlayer('common')

  const getRuleTypeBadge = (type: string) => {
    switch (type) {
      case 'threshold':
        return <Badge variant="outline">{t.ruleTypes.threshold}</Badge>
      case 'statistical':
        return <Badge variant="outline">{t.ruleTypes.statistical}</Badge>
      case 'trend':
        return <Badge variant="outline">{t.ruleTypes.trend}</Badge>
      default:
        return <Badge variant="outline">{type}</Badge>
    }
  }

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'critical':
        return (
          <Badge className="bg-red-500/10 text-red-500 border-red-500/20">
            {t.severity.critical}
          </Badge>
        )
      case 'warning':
        return (
          <Badge className="bg-orange-500/10 text-orange-500 border-orange-500/20">
            {t.severity.warning}
          </Badge>
        )
      case 'info':
        return (
          <Badge className="bg-blue-500/10 text-blue-500 border-blue-500/20">
            {t.severity.info}
          </Badge>
        )
      default:
        return <Badge variant="outline">{severity}</Badge>
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (rules.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        {t.rules.noRules}
      </div>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>{common.name}</TableHead>
          <TableHead>{t.rules.ruleType}</TableHead>
          <TableHead>{t.alerts.severity}</TableHead>
          <TableHead className="text-right">{t.rules.triggerCount}</TableHead>
          <TableHead>{t.rules.lastTriggered}</TableHead>
          <TableHead>Active</TableHead>
          <TableHead className="w-[60px]" />
        </TableRow>
      </TableHeader>
      <TableBody>
        {rules.map((rule) => (
          <TableRow key={rule.id}>
            <TableCell className="font-medium">{rule.name}</TableCell>
            <TableCell>{getRuleTypeBadge(rule.rule_type)}</TableCell>
            <TableCell>{getSeverityBadge(rule.severity)}</TableCell>
            <TableCell className="text-right">{rule.trigger_count}</TableCell>
            <TableCell className="text-muted-foreground text-sm">
              {rule.last_triggered_at
                ? formatDate(rule.last_triggered_at)
                : '-'}
            </TableCell>
            <TableCell>
              <Switch
                checked={rule.is_active}
                onCheckedChange={() => onToggle(rule)}
              />
            </TableCell>
            <TableCell>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => onEdit(rule)}>
                    <Edit className="h-4 w-4 mr-2" />
                    {common.edit}
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    className="text-destructive"
                    onClick={() => onDelete(rule)}
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
