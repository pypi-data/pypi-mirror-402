/**
 * PII Scan panel component.
 *
 * Provides interface for configuring and running PII scans.
 */

import { useCallback, useState } from 'react'
import { useIntlayer } from 'react-intlayer'
import { str } from '@/lib/intlayer-utils'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { Checkbox } from '@/components/ui/checkbox'
import { useToast } from '@/hooks/use-toast'
import { Loader2, Play, Eye, AlertTriangle, Shield } from 'lucide-react'
import { PIIFindingsTable } from './PIIFindingsTable'
import type { PIIScan, PIIScanOptions, Regulation } from '@/api/client'
import { runPIIScan, getPIIScan } from '@/api/client'

interface PIIScanPanelProps {
  sourceId: string
  columns?: string[]
  onScanComplete?: (scan: PIIScan) => void
}

const REGULATIONS: Regulation[] = ['gdpr', 'ccpa', 'lgpd']

export function PIIScanPanel({ sourceId, columns = [], onScanComplete }: PIIScanPanelProps) {
  const t = useIntlayer('privacy')
  void useIntlayer('common')
  const { toast } = useToast()

  // State
  const [isScanning, setIsScanning] = useState(false)
  const [currentScan, setCurrentScan] = useState<PIIScan | null>(null)
  const [minConfidence, setMinConfidence] = useState(0.8)
  const [selectedRegulations, setSelectedRegulations] = useState<Regulation[]>(['gdpr'])
  const [selectedColumns, setSelectedColumns] = useState<string[]>([])

  const handleRegulationToggle = (regulation: Regulation) => {
    setSelectedRegulations((prev) =>
      prev.includes(regulation)
        ? prev.filter((r) => r !== regulation)
        : [...prev, regulation]
    )
  }

  const handleColumnToggle = (column: string) => {
    setSelectedColumns((prev) =>
      prev.includes(column)
        ? prev.filter((c) => c !== column)
        : [...prev, column]
    )
  }

  const handleRunScan = useCallback(async () => {
    setIsScanning(true)

    const options: PIIScanOptions = {
      min_confidence: minConfidence,
      regulations: selectedRegulations,
    }

    if (selectedColumns.length > 0) {
      options.columns = selectedColumns
    }

    try {
      const scan = await runPIIScan(sourceId, options)

      // Poll for completion
      const pollResult = async () => {
        const result = await getPIIScan(scan.id)
        if (result.status === 'running' || result.status === 'pending') {
          setTimeout(pollResult, 1000)
        } else {
          setCurrentScan(result)
          setIsScanning(false)
          onScanComplete?.(result)

          if (result.status === 'success') {
            toast({
              title: str(t.scan.scanComplete),
              description: `Found ${result.columns_with_pii} columns with PII`,
            })
          } else if (result.status === 'error') {
            toast({
              title: str(t.scan.scanFailed),
              variant: 'destructive',
            })
          }
        }
      }

      pollResult()
    } catch (error) {
      setIsScanning(false)
      toast({
        title: str(t.scan.scanFailed),
        variant: 'destructive',
      })
    }
  }, [sourceId, minConfidence, selectedRegulations, selectedColumns, toast, t, onScanComplete])

  return (
    <div className="space-y-6">
      {/* Configuration */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Confidence Threshold */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t.config.minConfidence}</CardTitle>
            <CardDescription>{t.config.minConfidenceDesc}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Slider
                value={[minConfidence]}
                onValueChange={([value]) => setMinConfidence(value)}
                min={0.5}
                max={1}
                step={0.05}
                disabled={isScanning}
              />
              <div className="flex justify-between text-sm text-muted-foreground">
                <span>50%</span>
                <span className="font-medium text-foreground">{(minConfidence * 100).toFixed(0)}%</span>
                <span>100%</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Regulations */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t.config.selectRegulations}</CardTitle>
            <CardDescription>Select applicable privacy regulations</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              {REGULATIONS.map((reg) => (
                <div key={reg} className="flex items-center space-x-2">
                  <Checkbox
                    id={reg}
                    checked={selectedRegulations.includes(reg)}
                    onCheckedChange={() => handleRegulationToggle(reg)}
                    disabled={isScanning}
                  />
                  <Label htmlFor={reg} className="text-sm font-normal uppercase">
                    {reg}
                  </Label>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Column Selection */}
      {columns.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t.config.selectColumns}</CardTitle>
            <CardDescription>
              Leave empty to scan all columns, or select specific columns
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {columns.slice(0, 20).map((column) => (
                <Button
                  key={column}
                  variant={selectedColumns.includes(column) ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleColumnToggle(column)}
                  disabled={isScanning}
                >
                  {column}
                </Button>
              ))}
              {columns.length > 20 && (
                <span className="self-center text-sm text-muted-foreground">
                  +{columns.length - 20} more
                </span>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Run Button */}
      <div className="flex justify-end">
        <Button onClick={handleRunScan} disabled={isScanning} className="gap-2">
          {isScanning ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          {isScanning ? t.scan.scanning : t.scan.runScan}
        </Button>
      </div>

      {/* Results */}
      {currentScan && (
        <div className="space-y-6">
          {/* Summary Stats */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>{t.scan.columnsScanned}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <Eye className="h-5 w-5 text-muted-foreground" />
                  <span className="text-2xl font-bold">{currentScan.total_columns_scanned}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription>{t.scan.columnsWithPII}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <AlertTriangle
                    className={`h-5 w-5 ${
                      currentScan.columns_with_pii > 0 ? 'text-orange-500' : 'text-green-500'
                    }`}
                  />
                  <span
                    className={`text-2xl font-bold ${
                      currentScan.columns_with_pii > 0 ? 'text-orange-500' : 'text-green-500'
                    }`}
                  >
                    {currentScan.columns_with_pii}
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription>{t.scan.totalFindings}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <Shield className="h-5 w-5 text-muted-foreground" />
                  <span className="text-2xl font-bold">{currentScan.findings?.length ?? 0}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription>{t.scan.avgConfidence}</CardDescription>
              </CardHeader>
              <CardContent>
                <span className="text-2xl font-bold">
                  {currentScan.findings && currentScan.findings.length > 0
                    ? (
                        (currentScan.findings.reduce((sum, f) => sum + f.confidence, 0) /
                          currentScan.findings.length) *
                        100
                      ).toFixed(0)
                    : 0}
                  %
                </span>
              </CardContent>
            </Card>
          </div>

          {/* Findings Table */}
          <div>
            <h3 className="mb-3 text-sm font-medium">{t.scan.totalFindings}</h3>
            <PIIFindingsTable findings={currentScan.findings ?? []} />
          </div>
        </div>
      )}
    </div>
  )
}
