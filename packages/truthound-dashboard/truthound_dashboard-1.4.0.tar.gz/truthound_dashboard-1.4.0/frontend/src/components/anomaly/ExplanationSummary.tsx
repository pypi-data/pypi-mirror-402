/**
 * Explanation Summary Component.
 *
 * Displays a human-readable summary of why a row is anomalous,
 * with key contributing features highlighted.
 */

import { useIntlayer } from 'react-intlayer'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle, TrendingUp, TrendingDown } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { FeatureContribution } from './FeatureContributionChart'

interface ExplanationSummaryProps {
  rowIndex: number
  anomalyScore: number
  summary: string
  topContributions: FeatureContribution[]
  className?: string
}

export function ExplanationSummary({
  rowIndex,
  anomalyScore,
  summary,
  topContributions,
  className,
}: ExplanationSummaryProps) {
  // Reserved for future i18n strings
  void useIntlayer('anomaly')

  // Determine severity based on score
  const severity = getSeverity(anomalyScore)
  const severityColors = {
    critical: 'bg-red-100 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-400 dark:border-red-900',
    high: 'bg-orange-100 text-orange-700 border-orange-200 dark:bg-orange-950 dark:text-orange-400 dark:border-orange-900',
    medium: 'bg-yellow-100 text-yellow-700 border-yellow-200 dark:bg-yellow-950 dark:text-yellow-400 dark:border-yellow-900',
    low: 'bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-950 dark:text-blue-400 dark:border-blue-900',
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header with row info and score */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <AlertTriangle className={cn(
            'h-5 w-5',
            severity === 'critical' ? 'text-red-500' :
            severity === 'high' ? 'text-orange-500' :
            severity === 'medium' ? 'text-yellow-500' :
            'text-blue-500'
          )} />
          <div>
            <p className="font-medium">Row {rowIndex}</p>
            <p className="text-sm text-muted-foreground">
              Anomaly Score: <span className="font-mono">{anomalyScore.toFixed(4)}</span>
            </p>
          </div>
        </div>
        <Badge
          variant="outline"
          className={cn('capitalize', severityColors[severity])}
        >
          {severity}
        </Badge>
      </div>

      {/* Summary text */}
      <div className={cn(
        'rounded-lg border p-4',
        severityColors[severity]
      )}>
        <p className="text-sm leading-relaxed">{summary}</p>
      </div>

      {/* Top contributing features */}
      {topContributions.length > 0 && (
        <div>
          <h4 className="mb-2 text-sm font-medium text-muted-foreground">
            Top Contributing Features
          </h4>
          <div className="space-y-2">
            {topContributions.slice(0, 5).map((contrib, index) => (
              <div
                key={contrib.feature}
                className="flex items-center justify-between rounded border bg-muted/30 px-3 py-2 text-sm"
              >
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs text-muted-foreground">
                    #{index + 1}
                  </span>
                  <span className="font-medium">{contrib.feature}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="font-mono text-muted-foreground">
                    {formatValue(contrib.value)}
                  </span>
                  <div className={cn(
                    'flex items-center gap-1 font-mono text-xs',
                    contrib.shap_value > 0 ? 'text-red-500' : 'text-blue-500'
                  )}>
                    {contrib.shap_value > 0 ? (
                      <TrendingUp className="h-3 w-3" />
                    ) : (
                      <TrendingDown className="h-3 w-3" />
                    )}
                    <span>
                      {contrib.shap_value > 0 ? '+' : ''}
                      {contrib.shap_value.toFixed(3)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function getSeverity(score: number): 'critical' | 'high' | 'medium' | 'low' {
  if (score >= 0.9) return 'critical'
  if (score >= 0.7) return 'high'
  if (score >= 0.5) return 'medium'
  return 'low'
}

function formatValue(value: number): string {
  if (Number.isInteger(value)) {
    return value.toString()
  }
  return value.toFixed(2)
}
