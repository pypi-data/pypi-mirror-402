/**
 * Alert handler list component for model monitoring.
 *
 * Displays and manages alert handlers (Slack, Webhook, Email).
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
import {
  MoreHorizontal,
  Edit,
  Trash2,
  Loader2,
  Slack,
  Webhook,
  Mail,
  TestTube,
  CheckCircle,
  XCircle,
} from 'lucide-react'
import { formatDate } from '@/lib/utils'

export interface AlertHandler {
  id: string
  name: string
  handler_type: 'slack' | 'webhook' | 'email'
  config: {
    webhook_url?: string
    channel?: string
    username?: string
    url?: string
    method?: string
    headers?: Record<string, string>
    recipients?: string[]
    from_address?: string
    subject_template?: string
  }
  is_active: boolean
  send_count: number
  failure_count: number
  last_sent_at: string | null
  last_error: string | null
  created_at: string
  updated_at: string
}

interface AlertHandlerListProps {
  handlers: AlertHandler[]
  isLoading: boolean
  onEdit: (handler: AlertHandler) => void
  onDelete: (handler: AlertHandler) => void
  onToggle: (handler: AlertHandler) => void
  onTest: (handler: AlertHandler) => void
}

export function AlertHandlerList({
  handlers,
  isLoading,
  onEdit,
  onDelete,
  onToggle,
  onTest,
}: AlertHandlerListProps) {
  const t = useIntlayer('modelMonitoring')
  const common = useIntlayer('common')

  // Helper function to get handler icon - currently used in getHandlerTypeBadge
  void ((type: string) => {
    switch (type) {
      case 'slack':
        return <Slack className="h-4 w-4" />
      case 'webhook':
        return <Webhook className="h-4 w-4" />
      case 'email':
        return <Mail className="h-4 w-4" />
      default:
        return null
    }
  })

  const getHandlerTypeBadge = (type: string) => {
    switch (type) {
      case 'slack':
        return (
          <Badge className="bg-purple-500/10 text-purple-500 border-purple-500/20 gap-1">
            <Slack className="h-3 w-3" />
            {t.handlerTypes.slack}
          </Badge>
        )
      case 'webhook':
        return (
          <Badge className="bg-blue-500/10 text-blue-500 border-blue-500/20 gap-1">
            <Webhook className="h-3 w-3" />
            {t.handlerTypes.webhook}
          </Badge>
        )
      case 'email':
        return (
          <Badge className="bg-green-500/10 text-green-500 border-green-500/20 gap-1">
            <Mail className="h-3 w-3" />
            {t.handlerTypes.email}
          </Badge>
        )
      default:
        return <Badge variant="outline">{type}</Badge>
    }
  }

  const getConfigSummary = (handler: AlertHandler) => {
    switch (handler.handler_type) {
      case 'slack':
        return handler.config.channel || '-'
      case 'webhook':
        return handler.config.url
          ? new URL(handler.config.url).hostname
          : handler.config.webhook_url
            ? new URL(handler.config.webhook_url).hostname
            : '-'
      case 'email':
        return handler.config.recipients?.join(', ') || '-'
      default:
        return '-'
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (handlers.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">{t.handlers.noHandlers}</div>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>{common.name}</TableHead>
          <TableHead>{t.handlers.handlerType}</TableHead>
          <TableHead>Target</TableHead>
          <TableHead className="text-right">{t.handlers.sendCount}</TableHead>
          <TableHead className="text-right">{t.handlers.failureCount}</TableHead>
          <TableHead>{t.handlers.lastSent}</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Active</TableHead>
          <TableHead className="w-[60px]" />
        </TableRow>
      </TableHeader>
      <TableBody>
        {handlers.map((handler) => (
          <TableRow key={handler.id}>
            <TableCell className="font-medium">{handler.name}</TableCell>
            <TableCell>{getHandlerTypeBadge(handler.handler_type)}</TableCell>
            <TableCell className="text-sm text-muted-foreground max-w-[200px] truncate">
              {getConfigSummary(handler)}
            </TableCell>
            <TableCell className="text-right">{handler.send_count}</TableCell>
            <TableCell className="text-right">
              {handler.failure_count > 0 ? (
                <span className="text-red-500">{handler.failure_count}</span>
              ) : (
                <span className="text-muted-foreground">0</span>
              )}
            </TableCell>
            <TableCell className="text-muted-foreground text-sm">
              {handler.last_sent_at ? formatDate(handler.last_sent_at) : '-'}
            </TableCell>
            <TableCell>
              {handler.last_error ? (
                <div className="flex items-center gap-1 text-red-500">
                  <XCircle className="h-4 w-4" />
                  <span className="text-xs truncate max-w-[100px]" title={handler.last_error}>
                    Error
                  </span>
                </div>
              ) : handler.send_count > 0 ? (
                <div className="flex items-center gap-1 text-green-500">
                  <CheckCircle className="h-4 w-4" />
                  <span className="text-xs">OK</span>
                </div>
              ) : (
                <span className="text-xs text-muted-foreground">-</span>
              )}
            </TableCell>
            <TableCell>
              <Switch checked={handler.is_active} onCheckedChange={() => onToggle(handler)} />
            </TableCell>
            <TableCell>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => onTest(handler)}>
                    <TestTube className="h-4 w-4 mr-2" />
                    Test Handler
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => onEdit(handler)}>
                    <Edit className="h-4 w-4 mr-2" />
                    {common.edit}
                  </DropdownMenuItem>
                  <DropdownMenuItem className="text-destructive" onClick={() => onDelete(handler)}>
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
