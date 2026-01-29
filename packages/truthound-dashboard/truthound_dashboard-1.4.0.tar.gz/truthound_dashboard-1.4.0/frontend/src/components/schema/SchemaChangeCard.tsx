/**
 * SchemaChangeCard - Displays a single schema change with details.
 */

import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Plus, Minus, RefreshCw, ArrowRight } from 'lucide-react'

export interface SchemaChange {
  id: string
  change_type: 'column_added' | 'column_removed' | 'type_changed'
  column_name: string
  old_value: string | null
  new_value: string | null
  severity: 'breaking' | 'non_breaking'
  description: string
  created_at: string
}

interface SchemaChangeCardProps {
  change: SchemaChange
  compact?: boolean
}

export function SchemaChangeCard({ change, compact = false }: SchemaChangeCardProps) {
  const icons = {
    column_added: <Plus className="h-4 w-4 text-green-500" />,
    column_removed: <Minus className="h-4 w-4 text-red-500" />,
    type_changed: <RefreshCw className="h-4 w-4 text-yellow-500" />,
  }

  const labels = {
    column_added: 'Added',
    column_removed: 'Removed',
    type_changed: 'Type Changed',
  }

  const severityColors = {
    breaking: 'bg-red-500/10 text-red-500 border-red-500/20',
    non_breaking: 'bg-green-500/10 text-green-500 border-green-500/20',
  }

  if (compact) {
    return (
      <div className="flex items-center gap-2 py-1.5">
        {icons[change.change_type]}
        <span className="font-mono text-sm">{change.column_name}</span>
        <Badge variant="outline" className={severityColors[change.severity]}>
          {change.severity === 'breaking' ? 'Breaking' : 'Safe'}
        </Badge>
        {change.change_type === 'type_changed' && change.old_value && change.new_value && (
          <span className="text-xs text-muted-foreground flex items-center gap-1">
            <code className="bg-muted px-1 rounded">{change.old_value}</code>
            <ArrowRight className="h-3 w-3" />
            <code className="bg-muted px-1 rounded">{change.new_value}</code>
          </span>
        )}
      </div>
    )
  }

  return (
    <Card>
      <CardContent className="py-3 px-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <div className="mt-0.5">{icons[change.change_type]}</div>
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <span className="font-mono font-medium">{change.column_name}</span>
                <Badge variant="outline" className="text-xs">
                  {labels[change.change_type]}
                </Badge>
                <Badge variant="outline" className={severityColors[change.severity]}>
                  {change.severity === 'breaking' ? 'Breaking' : 'Safe'}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground">{change.description}</p>
              {change.change_type === 'type_changed' && change.old_value && change.new_value && (
                <div className="flex items-center gap-2 text-sm mt-1">
                  <code className="bg-muted px-2 py-0.5 rounded text-red-500">{change.old_value}</code>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  <code className="bg-muted px-2 py-0.5 rounded text-green-500">{change.new_value}</code>
                </div>
              )}
              {change.change_type === 'column_added' && change.new_value && (
                <div className="text-sm mt-1">
                  <span className="text-muted-foreground">Type: </span>
                  <code className="bg-muted px-2 py-0.5 rounded">{change.new_value}</code>
                </div>
              )}
              {change.change_type === 'column_removed' && change.old_value && (
                <div className="text-sm mt-1">
                  <span className="text-muted-foreground">Was: </span>
                  <code className="bg-muted px-2 py-0.5 rounded line-through">{change.old_value}</code>
                </div>
              )}
            </div>
          </div>
          <span className="text-xs text-muted-foreground">
            {new Date(change.created_at).toLocaleDateString()}
          </span>
        </div>
      </CardContent>
    </Card>
  )
}
