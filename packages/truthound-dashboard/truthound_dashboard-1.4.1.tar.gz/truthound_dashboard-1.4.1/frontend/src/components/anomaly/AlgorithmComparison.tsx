/**
 * Algorithm comparison main component.
 *
 * Allows users to select multiple algorithms to compare side-by-side.
 */

import { useCallback, useEffect, useState } from 'react'
import { useIntlayer } from 'react-intlayer'
import { str } from '@/lib/intlayer-utils'
import { Button } from '@/components/ui/button'
import { useToast } from '@/hooks/use-toast'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Loader2,
  Play,
  BarChart3,
  Table2,
  Users,
  Check,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { ComparisonResultsTable } from './ComparisonResultsTable'
import { ComparisonChart } from './ComparisonChart'
import { AlgorithmAgreement } from './AlgorithmAgreement'
import type {
  AlgorithmInfo,
  AlgorithmComparisonResult,
  AnomalyAlgorithm,
} from '@/api/client'
import { listAnomalyAlgorithms, compareAlgorithms } from '@/api/client'

interface AlgorithmComparisonProps {
  sourceId: string
  isOpen: boolean
  onClose: () => void
  columns?: string[]
}

export function AlgorithmComparison({
  sourceId,
  isOpen,
  onClose,
  columns = [],
}: AlgorithmComparisonProps) {
  const t = useIntlayer('anomaly')
  const { toast } = useToast()

  // State
  const [algorithms, setAlgorithms] = useState<AlgorithmInfo[]>([])
  const [selectedAlgorithms, setSelectedAlgorithms] = useState<Set<AnomalyAlgorithm>>(new Set())
  const [isLoadingAlgorithms, setIsLoadingAlgorithms] = useState(true)
  const [isRunning, setIsRunning] = useState(false)
  const [result, setResult] = useState<AlgorithmComparisonResult | null>(null)
  const [activeTab, setActiveTab] = useState<string>('select')

  // Load algorithms
  useEffect(() => {
    const loadAlgorithms = async () => {
      setIsLoadingAlgorithms(true)
      try {
        const response = await listAnomalyAlgorithms()
        setAlgorithms(response.algorithms)
        // Pre-select some algorithms
        setSelectedAlgorithms(new Set(['isolation_forest', 'lof', 'statistical'] as AnomalyAlgorithm[]))
      } catch (error) {
        toast({
          title: str(t.comparison?.errorLoadingAlgorithms ?? t.errorLoadingAlgorithms),
          variant: 'destructive',
        })
      } finally {
        setIsLoadingAlgorithms(false)
      }
    }
    if (isOpen) {
      loadAlgorithms()
    }
  }, [isOpen, toast, t])

  // Toggle algorithm selection
  const toggleAlgorithm = useCallback((algo: AnomalyAlgorithm) => {
    setSelectedAlgorithms((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(algo)) {
        newSet.delete(algo)
      } else {
        if (newSet.size < 6) {
          newSet.add(algo)
        }
      }
      return newSet
    })
  }, [])

  // Run comparison
  const handleRunComparison = useCallback(async () => {
    if (selectedAlgorithms.size < 2) {
      toast({
        title: str(t.comparison?.minAlgorithmsRequired ?? 'Select at least 2 algorithms'),
        variant: 'destructive',
      })
      return
    }

    setIsRunning(true)
    try {
      const comparisonResult = await compareAlgorithms(sourceId, {
        algorithms: Array.from(selectedAlgorithms),
        columns: columns.length > 0 ? columns : undefined,
      })
      setResult(comparisonResult)
      setActiveTab('results')
      toast({ title: str(t.comparison?.comparisonComplete ?? 'Comparison complete') })
    } catch (error) {
      toast({
        title: str(t.comparison?.comparisonFailed ?? 'Comparison failed'),
        variant: 'destructive',
      })
    } finally {
      setIsRunning(false)
    }
  }, [sourceId, selectedAlgorithms, columns, toast, t])

  // Reset on close
  const handleClose = useCallback(() => {
    setResult(null)
    setActiveTab('select')
    onClose()
  }, [onClose])

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            {t.comparison?.title ?? 'Compare Algorithms'}
          </DialogTitle>
          <DialogDescription>
            {t.comparison?.description ?? 'Select multiple algorithms to compare their anomaly detection results side-by-side.'}
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-hidden">
          {isLoadingAlgorithms ? (
            <div className="flex h-64 items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="select" className="gap-2">
                  <Check className="h-4 w-4" />
                  {t.comparison?.selectTab ?? 'Select'}
                </TabsTrigger>
                <TabsTrigger value="results" className="gap-2" disabled={!result}>
                  <Table2 className="h-4 w-4" />
                  {t.comparison?.resultsTab ?? 'Results'}
                </TabsTrigger>
                <TabsTrigger value="chart" className="gap-2" disabled={!result}>
                  <BarChart3 className="h-4 w-4" />
                  {t.comparison?.chartTab ?? 'Chart'}
                </TabsTrigger>
                <TabsTrigger value="agreement" className="gap-2" disabled={!result}>
                  <Users className="h-4 w-4" />
                  {t.comparison?.agreementTab ?? 'Agreement'}
                </TabsTrigger>
              </TabsList>

              <div className="flex-1 overflow-auto mt-4">
                <TabsContent value="select" className="m-0 h-full">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <p className="text-sm text-muted-foreground">
                        {t.comparison?.selectInstructions ?? 'Select 2-6 algorithms to compare'}
                      </p>
                      <Badge variant="outline">
                        {selectedAlgorithms.size}/6 {t.comparison?.selected ?? 'selected'}
                      </Badge>
                    </div>

                    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                      {algorithms.map((algo) => {
                        const isSelected = selectedAlgorithms.has(algo.name)
                        return (
                          <Card
                            key={algo.name}
                            className={`cursor-pointer transition-all hover:border-primary/50 ${
                              isSelected ? 'border-primary ring-2 ring-primary/20' : ''
                            }`}
                            onClick={() => toggleAlgorithm(algo.name)}
                          >
                            <CardHeader className="py-3">
                              <div className="flex items-center gap-3">
                                <Checkbox
                                  checked={isSelected}
                                  onCheckedChange={() => toggleAlgorithm(algo.name)}
                                />
                                <div>
                                  <CardTitle className="text-sm">{algo.display_name}</CardTitle>
                                  <p className="text-xs text-muted-foreground mt-1">
                                    {algo.best_for}
                                  </p>
                                </div>
                              </div>
                            </CardHeader>
                          </Card>
                        )
                      })}
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="results" className="m-0 h-full">
                  {result && <ComparisonResultsTable result={result} />}
                </TabsContent>

                <TabsContent value="chart" className="m-0 h-full">
                  {result && <ComparisonChart result={result} />}
                </TabsContent>

                <TabsContent value="agreement" className="m-0 h-full">
                  {result && <AlgorithmAgreement result={result} />}
                </TabsContent>
              </div>
            </Tabs>
          )}
        </div>

        <DialogFooter className="mt-4">
          <Button variant="outline" onClick={handleClose}>
            {t.comparison?.close ?? 'Close'}
          </Button>
          {activeTab === 'select' && (
            <Button
              onClick={handleRunComparison}
              disabled={isRunning || selectedAlgorithms.size < 2}
              className="gap-2"
            >
              {isRunning ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Play className="h-4 w-4" />
              )}
              {isRunning
                ? (t.comparison?.running ?? 'Running...')
                : (t.comparison?.runComparison ?? 'Run Comparison')}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
