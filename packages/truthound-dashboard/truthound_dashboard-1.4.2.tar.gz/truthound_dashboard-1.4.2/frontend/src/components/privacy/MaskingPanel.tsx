/**
 * Data masking panel component.
 *
 * Provides interface for configuring and running data masking operations.
 */

import { useCallback, useState } from 'react'
import { useIntlayer } from 'react-intlayer'
import { str } from '@/lib/intlayer-utils'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/hooks/use-toast'
import { Loader2, Play, Lock, Download, CheckCircle } from 'lucide-react'
import { MaskingStrategySelector } from './MaskingStrategySelector'
import type { DataMask, MaskingStrategy, MaskOptions } from '@/api/client'
import { runDataMask, getDataMask } from '@/api/client'

interface MaskingPanelProps {
  sourceId: string
  columns?: string[]
  suggestedColumns?: string[]
  onMaskComplete?: (mask: DataMask) => void
}

export function MaskingPanel({
  sourceId,
  columns = [],
  suggestedColumns = [],
  onMaskComplete,
}: MaskingPanelProps) {
  const t = useIntlayer('privacy')
  void useIntlayer('common')
  const { toast } = useToast()

  // State
  const [isMasking, setIsMasking] = useState(false)
  const [currentMask, setCurrentMask] = useState<DataMask | null>(null)
  const [strategy, setStrategy] = useState<MaskingStrategy>('redact')
  const [selectedColumns, setSelectedColumns] = useState<string[]>(suggestedColumns)

  const handleColumnToggle = (column: string) => {
    setSelectedColumns((prev) =>
      prev.includes(column)
        ? prev.filter((c) => c !== column)
        : [...prev, column]
    )
  }

  const handleSelectSuggested = () => {
    setSelectedColumns(suggestedColumns)
  }

  const handleClearSelection = () => {
    setSelectedColumns([])
  }

  const handleRunMask = useCallback(async () => {
    if (selectedColumns.length === 0) {
      toast({
        title: 'No columns selected',
        description: 'Please select at least one column to mask',
        variant: 'destructive',
      })
      return
    }

    setIsMasking(true)

    const options: MaskOptions = {
      strategy,
      columns: selectedColumns,
    }

    try {
      const mask = await runDataMask(sourceId, options)

      // Poll for completion
      const pollResult = async () => {
        const result = await getDataMask(mask.id)
        if (result.status === 'running' || result.status === 'pending') {
          setTimeout(pollResult, 1000)
        } else {
          setCurrentMask(result)
          setIsMasking(false)
          onMaskComplete?.(result)

          if (result.status === 'success') {
            toast({
              title: str(t.mask.maskComplete),
              description: `Masked ${result.columns_masked?.length ?? 0} columns`,
            })
          } else if (result.status === 'error') {
            toast({
              title: str(t.mask.maskFailed),
              variant: 'destructive',
            })
          }
        }
      }

      pollResult()
    } catch (error) {
      setIsMasking(false)
      toast({
        title: str(t.mask.maskFailed),
        variant: 'destructive',
      })
    }
  }, [sourceId, strategy, selectedColumns, toast, t, onMaskComplete])

  return (
    <div className="space-y-6">
      {/* Strategy Selection */}
      <div>
        <h3 className="mb-3 text-sm font-medium">{t.strategies.title}</h3>
        <MaskingStrategySelector
          selected={strategy}
          onSelect={setStrategy}
          disabled={isMasking}
        />
      </div>

      {/* Column Selection */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base">{t.config.selectColumns}</CardTitle>
              <CardDescription>
                Select columns to apply masking ({selectedColumns.length} selected)
              </CardDescription>
            </div>
            <div className="flex gap-2">
              {suggestedColumns.length > 0 && (
                <Button variant="outline" size="sm" onClick={handleSelectSuggested}>
                  Select PII Columns
                </Button>
              )}
              {selectedColumns.length > 0 && (
                <Button variant="ghost" size="sm" onClick={handleClearSelection}>
                  Clear
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {columns.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {columns.map((column) => {
                const isSelected = selectedColumns.includes(column)
                const isSuggested = suggestedColumns.includes(column)

                return (
                  <Button
                    key={column}
                    variant={isSelected ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handleColumnToggle(column)}
                    disabled={isMasking}
                    className="gap-1"
                  >
                    {column}
                    {isSuggested && !isSelected && (
                      <Badge variant="secondary" className="ml-1 text-[10px]">
                        PII
                      </Badge>
                    )}
                  </Button>
                )
              })}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              No columns available. Run a PII scan first to detect columns with sensitive data.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Run Button */}
      <div className="flex justify-end">
        <Button
          onClick={handleRunMask}
          disabled={isMasking || selectedColumns.length === 0}
          className="gap-2"
        >
          {isMasking ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          {isMasking ? t.mask.masking : t.mask.runMask}
        </Button>
      </div>

      {/* Results */}
      {currentMask && currentMask.status === 'success' && (
        <Card className="border-green-500/20 bg-green-500/5">
          <CardContent className="flex items-center justify-between p-6">
            <div className="flex items-center gap-4">
              <div className="rounded-full bg-green-500/10 p-3">
                <CheckCircle className="h-6 w-6 text-green-500" />
              </div>
              <div>
                <h3 className="font-medium">{t.mask.maskComplete}</h3>
                <div className="mt-1 flex flex-wrap gap-2">
                  <Badge variant="outline">
                    <Lock className="mr-1 h-3 w-3" />
                    {currentMask.columns_masked?.length ?? 0} columns masked
                  </Badge>
                  <Badge variant="secondary">{currentMask.strategy}</Badge>
                </div>
                {currentMask.output_path && (
                  <p className="mt-2 text-sm text-muted-foreground">
                    Output: <code className="text-xs">{currentMask.output_path}</code>
                  </p>
                )}
              </div>
            </div>

            {currentMask.output_path && (
              <Button variant="outline" className="gap-2">
                <Download className="h-4 w-4" />
                {t.mask.downloadMasked}
              </Button>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
