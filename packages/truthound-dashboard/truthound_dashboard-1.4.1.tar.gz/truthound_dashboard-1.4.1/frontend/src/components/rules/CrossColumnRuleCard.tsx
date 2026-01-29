/**
 * CrossColumnRuleCard Component
 *
 * Displays a cross-column rule suggestion with relationship visualization
 * and detailed evidence information.
 */

import {
  ArrowRight,
  GitBranch,
  Link2,
  Layers,
  Binary,
  Scale,
  Sigma,
  AlertTriangle,
  CheckCircle2,
  Minus,
  Percent,
  X,
  TrendingUp,
  ListOrdered,
} from 'lucide-react'

import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { useState } from 'react'

// Cross-column rule type colors and icons
const RULE_TYPE_CONFIG: Record<
  string,
  { icon: typeof GitBranch; color: string; bgColor: string }
> = {
  composite_key: {
    icon: Layers,
    color: 'text-purple-500',
    bgColor: 'bg-purple-500/10 border-purple-500/20',
  },
  column_comparison: {
    icon: Scale,
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/10 border-blue-500/20',
  },
  column_sum: {
    icon: Sigma,
    color: 'text-green-500',
    bgColor: 'bg-green-500/10 border-green-500/20',
  },
  column_product: {
    icon: X,
    color: 'text-teal-500',
    bgColor: 'bg-teal-500/10 border-teal-500/20',
  },
  column_difference: {
    icon: Minus,
    color: 'text-slate-500',
    bgColor: 'bg-slate-500/10 border-slate-500/20',
  },
  column_ratio: {
    icon: Scale,
    color: 'text-indigo-500',
    bgColor: 'bg-indigo-500/10 border-indigo-500/20',
  },
  column_percentage: {
    icon: Percent,
    color: 'text-violet-500',
    bgColor: 'bg-violet-500/10 border-violet-500/20',
  },
  column_chain_comparison: {
    icon: ListOrdered,
    color: 'text-sky-500',
    bgColor: 'bg-sky-500/10 border-sky-500/20',
  },
  column_dependency: {
    icon: GitBranch,
    color: 'text-orange-500',
    bgColor: 'bg-orange-500/10 border-orange-500/20',
  },
  column_implication: {
    icon: ArrowRight,
    color: 'text-amber-500',
    bgColor: 'bg-amber-500/10 border-amber-500/20',
  },
  column_coexistence: {
    icon: Link2,
    color: 'text-cyan-500',
    bgColor: 'bg-cyan-500/10 border-cyan-500/20',
  },
  column_mutual_exclusivity: {
    icon: Binary,
    color: 'text-red-500',
    bgColor: 'bg-red-500/10 border-red-500/20',
  },
  column_correlation: {
    icon: TrendingUp,
    color: 'text-pink-500',
    bgColor: 'bg-pink-500/10 border-pink-500/20',
  },
  referential_integrity: {
    icon: Link2,
    color: 'text-emerald-500',
    bgColor: 'bg-emerald-500/10 border-emerald-500/20',
  },
}

const DEFAULT_CONFIG = {
  icon: GitBranch,
  color: 'text-gray-500',
  bgColor: 'bg-gray-500/10 border-gray-500/20',
}

interface CrossColumnRuleSuggestion {
  id: string
  rule_type: string
  columns: string[]
  validator_name: string
  params: Record<string, unknown>
  confidence: number
  reason: string
  severity_suggestion: string
  evidence: Record<string, unknown>
  sample_violations: Array<Record<string, unknown>>
}

interface CrossColumnRuleCardProps {
  suggestion: CrossColumnRuleSuggestion
  selected: boolean
  onToggle: (id: string) => void
}

export function CrossColumnRuleCard({
  suggestion,
  selected,
  onToggle,
}: CrossColumnRuleCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const config = RULE_TYPE_CONFIG[suggestion.rule_type] || DEFAULT_CONFIG
  const Icon = config.icon

  // Format confidence as percentage
  const confidencePct = Math.round(suggestion.confidence * 100)

  // Determine confidence color
  const confidenceColor =
    confidencePct >= 85
      ? 'text-green-500'
      : confidencePct >= 70
        ? 'text-amber-500'
        : 'text-red-500'

  const confidenceBgColor =
    confidencePct >= 85
      ? 'bg-green-500/20'
      : confidencePct >= 70
        ? 'bg-amber-500/20'
        : 'bg-red-500/20'

  // Format rule type for display
  const formatRuleType = (type: string) => {
    return type
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
  }

  // Get severity badge variant
  const severityVariant =
    suggestion.severity_suggestion === 'high'
      ? 'destructive'
      : suggestion.severity_suggestion === 'medium'
        ? 'default'
        : 'secondary'

  return (
    <Card
      className={`transition-all cursor-pointer hover:shadow-md ${
        selected ? 'ring-2 ring-primary' : ''
      }`}
      onClick={() => onToggle(suggestion.id)}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          {/* Selection Checkbox */}
          <Checkbox
            checked={selected}
            onCheckedChange={() => onToggle(suggestion.id)}
            onClick={(e) => e.stopPropagation()}
            className="mt-1"
          />

          {/* Rule Type Icon */}
          <div
            className={`p-2 rounded-lg border ${config.bgColor} flex-shrink-0`}
          >
            <Icon className={`h-5 w-5 ${config.color}`} />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            {/* Header */}
            <div className="flex items-center justify-between gap-2 mb-2">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-medium text-sm">
                  {suggestion.validator_name}
                </span>
                <Badge variant="outline" className={config.bgColor}>
                  {formatRuleType(suggestion.rule_type)}
                </Badge>
                <Badge variant={severityVariant} className="capitalize">
                  {suggestion.severity_suggestion}
                </Badge>
              </div>

              {/* Confidence */}
              <Tooltip>
                <TooltipTrigger asChild>
                  <div
                    className={`px-2 py-0.5 rounded-full text-xs font-medium ${confidenceBgColor} ${confidenceColor}`}
                  >
                    {confidencePct}%
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Confidence: {confidencePct}%</p>
                </TooltipContent>
              </Tooltip>
            </div>

            {/* Involved Columns */}
            <div className="flex items-center gap-1 mb-2 flex-wrap">
              {suggestion.columns.map((col, idx) => (
                <span key={col} className="flex items-center">
                  <Badge variant="secondary" className="text-xs">
                    {col}
                  </Badge>
                  {idx < suggestion.columns.length - 1 && (
                    <ArrowRight className="h-3 w-3 mx-1 text-muted-foreground" />
                  )}
                </span>
              ))}
            </div>

            {/* Reason */}
            <p className="text-sm text-muted-foreground">{suggestion.reason}</p>

            {/* Expandable Details */}
            <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
              <CollapsibleTrigger
                className="text-xs text-primary hover:underline mt-2"
                onClick={(e) => e.stopPropagation()}
              >
                {isExpanded ? 'Hide details' : 'Show details'}
              </CollapsibleTrigger>

              <CollapsibleContent className="mt-3 space-y-3">
                {/* Parameters */}
                {Object.keys(suggestion.params).length > 0 && (
                  <div className="bg-muted/50 rounded-md p-2">
                    <p className="text-xs font-medium mb-1">Parameters</p>
                    <div className="grid grid-cols-2 gap-1 text-xs">
                      {Object.entries(suggestion.params).map(([key, value]) => (
                        <div key={key}>
                          <span className="text-muted-foreground">{key}:</span>{' '}
                          <span className="font-mono">
                            {typeof value === 'object'
                              ? JSON.stringify(value)
                              : String(value)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Evidence */}
                {Object.keys(suggestion.evidence).length > 0 && (
                  <div className="bg-muted/50 rounded-md p-2">
                    <p className="text-xs font-medium mb-1">Evidence</p>
                    <div className="grid grid-cols-2 gap-1 text-xs">
                      {Object.entries(suggestion.evidence).map(
                        ([key, value]) => (
                          <div key={key}>
                            <span className="text-muted-foreground">
                              {key.replace(/_/g, ' ')}:
                            </span>{' '}
                            <span className="font-mono">
                              {typeof value === 'number'
                                ? value.toLocaleString()
                                : String(value)}
                            </span>
                          </div>
                        )
                      )}
                    </div>
                  </div>
                )}

                {/* Sample Violations */}
                {suggestion.sample_violations.length > 0 ? (
                  <div className="bg-red-500/5 border border-red-500/20 rounded-md p-2">
                    <div className="flex items-center gap-1 mb-1">
                      <AlertTriangle className="h-3 w-3 text-red-500" />
                      <p className="text-xs font-medium text-red-500">
                        Sample Violations ({suggestion.sample_violations.length}
                        )
                      </p>
                    </div>
                    <div className="text-xs font-mono overflow-x-auto">
                      {suggestion.sample_violations.slice(0, 2).map((v, i) => (
                        <div
                          key={i}
                          className="text-muted-foreground truncate"
                        >
                          {JSON.stringify(v)}
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="bg-green-500/5 border border-green-500/20 rounded-md p-2">
                    <div className="flex items-center gap-1">
                      <CheckCircle2 className="h-3 w-3 text-green-500" />
                      <p className="text-xs text-green-500">
                        No violations found in sample data
                      </p>
                    </div>
                  </div>
                )}
              </CollapsibleContent>
            </Collapsible>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default CrossColumnRuleCard
