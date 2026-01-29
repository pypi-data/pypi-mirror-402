/**
 * RuleSuggestionCard - Displays a single rule suggestion with selection.
 */

import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Lightbulb, Sparkles, AlertTriangle, Info } from 'lucide-react'

export interface SuggestedRule {
  id: string
  validator_name: string
  column_name: string | null
  confidence: number
  reason: string
  parameters: Record<string, unknown>
  priority: number
  category: string
  severity_suggestion?: string
}

interface RuleSuggestionCardProps {
  suggestion: SuggestedRule
  selected: boolean
  onToggle: (id: string) => void
}

export function RuleSuggestionCard({ suggestion, selected, onToggle }: RuleSuggestionCardProps) {
  // Support both 0-1 and 0-100 confidence ranges
  const confidenceValue = suggestion.confidence <= 1 ? suggestion.confidence * 100 : suggestion.confidence
  const confidencePercent = Math.round(confidenceValue)

  const confidenceColor =
    confidenceValue >= 90
      ? 'bg-green-500/10 text-green-500 border-green-500/20'
      : confidenceValue >= 75
        ? 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
        : 'bg-orange-500/10 text-orange-500 border-orange-500/20'

  const categoryColors: Record<string, string> = {
    completeness: 'bg-blue-500/10 text-blue-500',
    uniqueness: 'bg-purple-500/10 text-purple-500',
    distribution: 'bg-green-500/10 text-green-500',
    schema: 'bg-orange-500/10 text-orange-500',
    stats: 'bg-cyan-500/10 text-cyan-500',
    pattern: 'bg-amber-500/10 text-amber-500',
    string: 'bg-cyan-500/10 text-cyan-500',
    datetime: 'bg-amber-500/10 text-amber-500',
  }

  const severityIcon = {
    critical: <AlertTriangle className="h-3 w-3 mr-1" />,
    warning: <Lightbulb className="h-3 w-3 mr-1" />,
    info: <Info className="h-3 w-3 mr-1" />,
  }

  const formatParams = (params: Record<string, unknown>) => {
    const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== null)
    if (entries.length === 0) return null
    return entries
      .map(([k, v]) => {
        if (Array.isArray(v)) {
          return `${k}=[${v.slice(0, 3).join(', ')}${v.length > 3 ? '...' : ''}]`
        }
        return `${k}=${v}`
      })
      .join(', ')
  }

  const paramsString = formatParams(suggestion.parameters)

  return (
    <Card
      className={`cursor-pointer transition-all hover:border-primary/50 ${
        selected ? 'border-primary bg-primary/5' : ''
      }`}
      onClick={() => onToggle(suggestion.id)}
    >
      <CardContent className="py-3 px-4">
        <div className="flex items-start gap-3">
          <Checkbox
            checked={selected}
            onCheckedChange={() => onToggle(suggestion.id)}
            className="mt-1"
            onClick={(e: React.MouseEvent) => e.stopPropagation()}
          />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              {suggestion.column_name && (
                <code className="bg-muted px-2 py-0.5 rounded text-sm font-mono">
                  {suggestion.column_name}
                </code>
              )}
              <span className="font-medium">{suggestion.validator_name}</span>
              <Badge variant="outline" className={categoryColors[suggestion.category] || 'bg-muted'}>
                {suggestion.category}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground mt-1">{suggestion.reason}</p>
            {paramsString && (
              <p className="text-xs font-mono text-muted-foreground mt-1 bg-muted/50 px-2 py-1 rounded">
                {paramsString}
              </p>
            )}
          </div>
          <div className="flex flex-col items-end gap-1">
            <Badge variant="outline" className={confidenceColor}>
              {confidenceValue >= 90 ? (
                <Sparkles className="h-3 w-3 mr-1" />
              ) : suggestion.severity_suggestion ? (
                severityIcon[suggestion.severity_suggestion as keyof typeof severityIcon] || <Lightbulb className="h-3 w-3 mr-1" />
              ) : (
                <Lightbulb className="h-3 w-3 mr-1" />
              )}
              {confidencePercent}%
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
