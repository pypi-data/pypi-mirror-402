/**
 * Remediation Panel Component
 *
 * Displays suggested remediation actions for drift issues,
 * with priority indicators and action buttons.
 */

import { useIntlayer } from 'react-intlayer'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import {
  Search,
  RefreshCw,
  Settings,
  GitCompare,
  Database,
  Filter,
  Wand2,
  CheckCircle,
  ArrowRight,
  ExternalLink,
  AlertCircle,
  Loader2,
  Lightbulb,
} from 'lucide-react'

// Types
export interface RemediationSuggestion {
  action: string
  priority: number
  title: string
  description: string
  affected_columns: string[]
  estimated_impact: string
  requires_manual_review: boolean
  automation_available: boolean
}

interface RemediationPanelProps {
  remediations: RemediationSuggestion[]
  isLoading?: boolean
  onActionClick?: (action: string, remediation: RemediationSuggestion) => void
}

// Helper functions
const getActionIcon = (action: string) => {
  switch (action) {
    case 'investigate_upstream':
      return <Search className="h-4 w-4" />
    case 'update_baseline':
      return <RefreshCw className="h-4 w-4" />
    case 'adjust_threshold':
      return <Settings className="h-4 w-4" />
    case 'review_data_pipeline':
      return <GitCompare className="h-4 w-4" />
    case 'check_data_source':
      return <Database className="h-4 w-4" />
    case 'normalize_values':
      return <Settings className="h-4 w-4" />
    case 'filter_outliers':
      return <Filter className="h-4 w-4" />
    case 'retrain_model':
      return <Wand2 className="h-4 w-4" />
    case 'acknowledge_expected_change':
      return <CheckCircle className="h-4 w-4" />
    default:
      return <Lightbulb className="h-4 w-4" />
  }
}

const getPriorityColor = (priority: number): string => {
  switch (priority) {
    case 1:
      return 'bg-red-500/10 text-red-500 border-red-500/20'
    case 2:
      return 'bg-orange-500/10 text-orange-500 border-orange-500/20'
    case 3:
      return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
    case 4:
      return 'bg-blue-500/10 text-blue-500 border-blue-500/20'
    default:
      return 'bg-gray-500/10 text-gray-500 border-gray-500/20'
  }
}

const getImpactColor = (impact: string): string => {
  switch (impact) {
    case 'high':
      return 'bg-green-500/10 text-green-500 border-green-500/20'
    case 'medium':
      return 'bg-blue-500/10 text-blue-500 border-blue-500/20'
    case 'low':
      return 'bg-gray-500/10 text-gray-500 border-gray-500/20'
    default:
      return 'bg-gray-500/10 text-gray-500 border-gray-500/20'
  }
}

const getPriorityLabel = (priority: number): string => {
  switch (priority) {
    case 1:
      return 'Critical'
    case 2:
      return 'High'
    case 3:
      return 'Medium'
    case 4:
      return 'Low'
    default:
      return 'Info'
  }
}

export function RemediationPanel({
  remediations,
  isLoading = false,
  onActionClick,
}: RemediationPanelProps) {
  const t = useIntlayer('driftMonitor')

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    )
  }

  if (!remediations || remediations.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center gap-2 py-12">
          <CheckCircle className="h-8 w-8 text-green-500" />
          <p className="font-medium">{t.rootCause?.noRemediations ?? 'No actions needed'}</p>
          <p className="text-sm text-muted-foreground">
            {t.rootCause?.noRemediationsDesc ?? 'No remediation suggestions at this time'}
          </p>
        </CardContent>
      </Card>
    )
  }

  // Sort by priority
  const sortedRemediations = [...remediations].sort((a, b) => a.priority - b.priority)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Lightbulb className="h-5 w-5" />
          {t.rootCause?.remediations ?? 'Suggested Actions'}
        </CardTitle>
        <CardDescription>
          {t.rootCause?.remediationsDesc ?? 'Recommended steps to address drift issues'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Accordion type="single" collapsible className="w-full">
          {sortedRemediations.map((remediation, index) => (
            <AccordionItem key={`${remediation.action}-${index}`} value={`item-${index}`}>
              <AccordionTrigger className="hover:no-underline">
                <div className="flex flex-1 items-center gap-3 pr-4">
                  <div
                    className={`rounded-lg p-2 ${
                      remediation.priority <= 2
                        ? 'bg-orange-500/10 text-orange-500'
                        : 'bg-blue-500/10 text-blue-500'
                    }`}
                  >
                    {getActionIcon(remediation.action)}
                  </div>
                  <div className="flex-1 text-left">
                    <div className="font-medium">{remediation.title}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className={getPriorityColor(remediation.priority)}>
                      P{remediation.priority} - {getPriorityLabel(remediation.priority)}
                    </Badge>
                    <Badge variant="outline" className={getImpactColor(remediation.estimated_impact)}>
                      {remediation.estimated_impact} impact
                    </Badge>
                  </div>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4 pl-12 pt-2">
                  {/* Description */}
                  <p className="text-sm text-muted-foreground">{remediation.description}</p>

                  {/* Affected Columns */}
                  {remediation.affected_columns.length > 0 && (
                    <div>
                      <div className="mb-2 text-sm font-medium">
                        {t.rootCause?.affectedColumns ?? 'Affected Columns'}
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {remediation.affected_columns.map((col) => (
                          <Badge key={col} variant="secondary" className="font-mono text-xs">
                            {col}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Metadata */}
                  <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
                    {remediation.requires_manual_review && (
                      <div className="flex items-center gap-1">
                        <AlertCircle className="h-4 w-4 text-yellow-500" />
                        <span>{t.rootCause?.manualReview ?? 'Requires manual review'}</span>
                      </div>
                    )}
                    {remediation.automation_available && (
                      <div className="flex items-center gap-1">
                        <Wand2 className="h-4 w-4 text-green-500" />
                        <span>{t.rootCause?.automationAvailable ?? 'Automation available'}</span>
                      </div>
                    )}
                  </div>

                  {/* Action Buttons */}
                  <div className="flex items-center gap-2 pt-2">
                    {remediation.automation_available && onActionClick && (
                      <Button
                        size="sm"
                        onClick={() => onActionClick('automate', remediation)}
                      >
                        <Wand2 className="mr-2 h-4 w-4" />
                        {t.rootCause?.runAutomation ?? 'Run Automation'}
                      </Button>
                    )}
                    {onActionClick && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onActionClick('investigate', remediation)}
                      >
                        <ExternalLink className="mr-2 h-4 w-4" />
                        {t.rootCause?.investigate ?? 'Investigate'}
                      </Button>
                    )}
                    {onActionClick && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => onActionClick('dismiss', remediation)}
                      >
                        <CheckCircle className="mr-2 h-4 w-4" />
                        {t.rootCause?.dismiss ?? 'Dismiss'}
                      </Button>
                    )}
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>

        {/* Quick Actions Summary */}
        <div className="mt-6 rounded-lg border bg-muted/50 p-4">
          <div className="mb-3 flex items-center gap-2 text-sm font-medium">
            <ArrowRight className="h-4 w-4" />
            {t.rootCause?.quickSummary ?? 'Quick Summary'}
          </div>
          <div className="grid gap-2 text-sm sm:grid-cols-3">
            <div>
              <span className="text-muted-foreground">
                {t.rootCause?.totalSuggestions ?? 'Total suggestions'}:
              </span>{' '}
              <span className="font-medium">{remediations.length}</span>
            </div>
            <div>
              <span className="text-muted-foreground">
                {t.rootCause?.highPriority ?? 'High priority'}:
              </span>{' '}
              <span className="font-medium text-orange-500">
                {remediations.filter((r) => r.priority <= 2).length}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">
                {t.rootCause?.automatable ?? 'Automatable'}:
              </span>{' '}
              <span className="font-medium text-green-500">
                {remediations.filter((r) => r.automation_available).length}
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
