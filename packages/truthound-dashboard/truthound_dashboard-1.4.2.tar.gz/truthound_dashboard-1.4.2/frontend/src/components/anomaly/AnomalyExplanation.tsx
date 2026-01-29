/**
 * Anomaly Explanation Component.
 *
 * Main component for displaying SHAP/LIME explanations for anomalies.
 * Combines force plot visualization, feature contributions table,
 * and human-readable summary.
 */

import { useCallback, useState } from 'react'
import { useIntlayer } from 'react-intlayer'
import { str } from '@/lib/intlayer-utils'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/hooks/use-toast'
import {
  Loader2,
  Lightbulb,
  BarChart3,
  Table2,
  FileText,
  RefreshCw,
  AlertTriangle,
} from 'lucide-react'
import { FeatureContributionChart, type FeatureContribution } from './FeatureContributionChart'
import { ExplanationSummary } from './ExplanationSummary'
import { cn } from '@/lib/utils'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

export interface AnomalyExplanationData {
  row_index: number
  anomaly_score: number
  feature_contributions: FeatureContribution[]
  total_shap: number
  summary: string
}

export interface ExplainabilityResult {
  detection_id: string
  algorithm: string
  row_indices: number[]
  feature_names: string[]
  explanations: AnomalyExplanationData[]
  generated_at: string
  error?: string | null
}

interface AnomalyExplanationProps {
  detectionId: string
  rowIndices: number[]
  onExplain: (detectionId: string, rowIndices: number[]) => Promise<ExplainabilityResult>
  onClose: () => void
  isOpen: boolean
  className?: string
}

export function AnomalyExplanation({
  detectionId,
  rowIndices,
  onExplain,
  onClose,
  isOpen,
  className: _className, // Reserved for future use
}: AnomalyExplanationProps) {
  const t = useIntlayer('anomaly')
  const { toast } = useToast()

  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<ExplainabilityResult | null>(null)
  const [selectedRowIndex, setSelectedRowIndex] = useState<number>(
    rowIndices[0] ?? 0
  )
  const [activeTab, setActiveTab] = useState<string>('summary')

  // Load explanations
  const loadExplanations = useCallback(async () => {
    setIsLoading(true)
    try {
      const data = await onExplain(detectionId, rowIndices)
      setResult(data)

      if (data.error) {
        toast({
          title: str(t.explainError),
          description: data.error,
          variant: 'destructive',
        })
      }
    } catch (error) {
      toast({
        title: str(t.explainError),
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }, [detectionId, rowIndices, onExplain, toast, t])

  // Load on open if no result
  const handleOpenChange = useCallback((open: boolean) => {
    if (open && !result && !isLoading) {
      loadExplanations()
    }
    if (!open) {
      onClose()
    }
  }, [result, isLoading, loadExplanations, onClose])

  // Get current explanation
  const currentExplanation = result?.explanations.find(
    (e) => e.row_index === selectedRowIndex
  )

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-primary" />
            {t.explainTitle}
          </DialogTitle>
          <DialogDescription>
            {t.explainDescription}
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-auto">
          {isLoading ? (
            <div className="flex h-64 flex-col items-center justify-center gap-4">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <p className="text-muted-foreground">{t.generatingExplanations}</p>
            </div>
          ) : result?.error && !result.explanations.length ? (
            <div className="flex h-64 flex-col items-center justify-center gap-4">
              <AlertTriangle className="h-8 w-8 text-destructive" />
              <p className="text-muted-foreground">{result.error}</p>
              <Button variant="outline" onClick={loadExplanations}>
                <RefreshCw className="mr-2 h-4 w-4" />
                {t.retry}
              </Button>
            </div>
          ) : result && result.explanations.length > 0 ? (
            <div className="space-y-4">
              {/* Row selector if multiple rows */}
              {rowIndices.length > 1 && (
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm text-muted-foreground">
                    {t.selectRow}:
                  </span>
                  {result.explanations.map((exp) => (
                    <Button
                      key={exp.row_index}
                      variant={selectedRowIndex === exp.row_index ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setSelectedRowIndex(exp.row_index)}
                    >
                      Row {exp.row_index}
                      <Badge
                        variant="secondary"
                        className={cn(
                          'ml-2',
                          exp.anomaly_score >= 0.9 ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300' :
                          exp.anomaly_score >= 0.7 ? 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300' :
                          ''
                        )}
                      >
                        {(exp.anomaly_score * 100).toFixed(0)}%
                      </Badge>
                    </Button>
                  ))}
                </div>
              )}

              {/* Tabs for different views */}
              {currentExplanation && (
                <Tabs value={activeTab} onValueChange={setActiveTab}>
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="summary" className="gap-2">
                      <FileText className="h-4 w-4" />
                      {t.summaryTab}
                    </TabsTrigger>
                    <TabsTrigger value="chart" className="gap-2">
                      <BarChart3 className="h-4 w-4" />
                      {t.chartTab}
                    </TabsTrigger>
                    <TabsTrigger value="table" className="gap-2">
                      <Table2 className="h-4 w-4" />
                      {t.tableTab}
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent value="summary" className="mt-4">
                    <ExplanationSummary
                      rowIndex={currentExplanation.row_index}
                      anomalyScore={currentExplanation.anomaly_score}
                      summary={currentExplanation.summary}
                      topContributions={currentExplanation.feature_contributions}
                    />
                  </TabsContent>

                  <TabsContent value="chart" className="mt-4">
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <h4 className="text-sm font-medium">
                          {t.featureContributions}
                        </h4>
                        <Badge variant="outline">
                          {result.algorithm}
                        </Badge>
                      </div>
                      <FeatureContributionChart
                        contributions={currentExplanation.feature_contributions}
                        maxFeatures={10}
                        height={350}
                      />
                    </div>
                  </TabsContent>

                  <TabsContent value="table" className="mt-4">
                    <FeatureContributionTable
                      contributions={currentExplanation.feature_contributions}
                    />
                  </TabsContent>
                </Tabs>
              )}

              {/* Meta info */}
              <div className="flex items-center justify-between text-xs text-muted-foreground border-t pt-4">
                <span>
                  Algorithm: <span className="font-medium">{result.algorithm}</span>
                </span>
                <span>
                  Generated: {new Date(result.generated_at).toLocaleString()}
                </span>
              </div>
            </div>
          ) : (
            <div className="flex h-64 flex-col items-center justify-center gap-4">
              <Lightbulb className="h-8 w-8 text-muted-foreground" />
              <p className="text-muted-foreground">{t.noExplanationsYet}</p>
              <Button onClick={loadExplanations}>
                <RefreshCw className="mr-2 h-4 w-4" />
                {t.generateExplanations}
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

/**
 * Feature contribution table component
 */
function FeatureContributionTable({
  contributions,
}: {
  contributions: FeatureContribution[]
}) {
  const t = useIntlayer('anomaly')

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12">#</TableHead>
            <TableHead>{t.featureName}</TableHead>
            <TableHead className="text-right">{t.featureValue}</TableHead>
            <TableHead className="text-right">{t.shapValue}</TableHead>
            <TableHead className="text-right">{t.contribution}</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {contributions.map((contrib, index) => (
            <TableRow key={contrib.feature}>
              <TableCell className="font-mono text-muted-foreground">
                {index + 1}
              </TableCell>
              <TableCell className="font-medium">{contrib.feature}</TableCell>
              <TableCell className="text-right font-mono">
                {formatValue(contrib.value)}
              </TableCell>
              <TableCell className={cn(
                'text-right font-mono',
                contrib.shap_value > 0 ? 'text-red-500' : 'text-blue-500'
              )}>
                {contrib.shap_value > 0 ? '+' : ''}{contrib.shap_value.toFixed(4)}
              </TableCell>
              <TableCell className="text-right font-mono">
                {contrib.contribution.toFixed(4)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

function formatValue(value: number): string {
  if (Number.isInteger(value)) {
    return value.toString()
  }
  return value.toFixed(2)
}
