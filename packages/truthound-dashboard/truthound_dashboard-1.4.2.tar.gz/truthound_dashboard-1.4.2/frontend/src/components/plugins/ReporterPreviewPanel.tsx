/**
 * ReporterPreviewPanel - Preview panel for custom reporters
 *
 * Features:
 * - Live preview of generated report
 * - Sample data input
 * - Configuration field values
 * - Format selection
 * - Execution time display
 */

import { useState, useCallback } from 'react'
import { useIntlayer } from 'react-intlayer'
import { str } from '@/lib/intlayer-utils'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import { CodeEditor } from '@/components/common'
import {
  Eye,
  CheckCircle,
  AlertTriangle,
  Clock,
  Loader2,
} from 'lucide-react'
import type { ReporterFieldDefinition, ReporterOutputFormat, ReporterPreviewResult } from './types'

interface ReporterPreviewPanelProps {
  template?: string
  code?: string
  configFields: ReporterFieldDefinition[]
  outputFormats: ReporterOutputFormat[]
  onPreview: (data: {
    template?: string
    code?: string
    sample_data: Record<string, unknown>
    config: Record<string, unknown>
    format: string
  }) => Promise<ReporterPreviewResult>
  disabled?: boolean
}

const DEFAULT_SAMPLE_DATA = `{
  "title": "Validation Report",
  "source_name": "example_source",
  "validation_date": "2024-01-15T10:30:00Z",
  "total_rows": 10000,
  "passed": 9850,
  "failed": 150,
  "issues": [
    {"column": "email", "message": "Invalid format", "count": 50},
    {"column": "age", "message": "Out of range", "count": 100}
  ],
  "metadata": {
    "generated_at": "2024-01-15T10:35:00Z",
    "version": "1.0.0"
  }
}`

/**
 * Panel for previewing custom reporters
 */
export function ReporterPreviewPanel({
  template,
  code,
  configFields,
  outputFormats,
  onPreview,
  disabled = false,
}: ReporterPreviewPanelProps) {
  const t = useIntlayer('plugins')
  const [sampleData, setSampleData] = useState(DEFAULT_SAMPLE_DATA)
  const [configValues, setConfigValues] = useState<Record<string, unknown>>({})
  const [selectedFormat, setSelectedFormat] = useState<string>(outputFormats[0] || 'html')
  const [result, setResult] = useState<ReporterPreviewResult | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Initialize config values from defaults
  const initConfigValues = useCallback(() => {
    const values: Record<string, unknown> = {}
    configFields.forEach((field) => {
      if (field.default !== undefined) {
        values[field.name] = field.default
      }
    })
    setConfigValues((prev) => ({ ...values, ...prev }))
  }, [configFields])

  // Handle preview
  const handlePreview = useCallback(async () => {
    if (!template && !code) {
      setError(str(t.editor.previewNoTemplate))
      return
    }

    setIsRunning(true)
    setError(null)
    setResult(null)

    try {
      // Parse sample data JSON
      let parsedData: Record<string, unknown>
      try {
        parsedData = JSON.parse(sampleData)
      } catch {
        setError(str(t.editor.previewInvalidJson))
        setIsRunning(false)
        return
      }

      // Run preview
      const previewResult = await onPreview({
        template,
        code,
        sample_data: parsedData,
        config: configValues,
        format: selectedFormat,
      })
      setResult(previewResult)
    } catch (err) {
      setError(err instanceof Error ? err.message : str(t.editor.previewError))
    } finally {
      setIsRunning(false)
    }
  }, [template, code, sampleData, configValues, selectedFormat, onPreview, t])

  // Handle config value change
  const handleConfigChange = useCallback((name: string, value: unknown) => {
    setConfigValues((prev) => ({ ...prev, [name]: value }))
  }, [])

  // Render config field input
  const renderConfigInput = (field: ReporterFieldDefinition) => {
    const value = configValues[field.name]

    switch (field.type) {
      case 'boolean':
        return (
          <select
            value={value?.toString() || 'false'}
            onChange={(e) => handleConfigChange(field.name, e.target.value === 'true')}
            className="h-8 text-sm border rounded px-2 bg-background w-full"
            disabled={disabled || isRunning}
          >
            <option value="true">True</option>
            <option value="false">False</option>
          </select>
        )
      case 'select':
        return (
          <select
            value={(value as string) || ''}
            onChange={(e) => handleConfigChange(field.name, e.target.value)}
            className="h-8 text-sm border rounded px-2 bg-background w-full"
            disabled={disabled || isRunning}
          >
            <option value="">Select...</option>
            {field.options?.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        )
      case 'number':
        return (
          <Input
            type="number"
            value={value?.toString() || ''}
            onChange={(e) => handleConfigChange(field.name, parseFloat(e.target.value))}
            disabled={disabled || isRunning}
            className="h-8 text-sm"
          />
        )
      default:
        return (
          <Input
            value={(value as string) || ''}
            onChange={(e) => handleConfigChange(field.name, e.target.value)}
            disabled={disabled || isRunning}
            className="h-8 text-sm"
          />
        )
    }
  }

  return (
    <div className="space-y-4">
      {/* Configuration Fields */}
      {configFields.length > 0 && (
        <Card>
          <CardHeader className="py-2 px-3">
            <CardTitle className="text-sm">{str(t.editor.reporterConfig)}</CardTitle>
          </CardHeader>
          <CardContent className="py-2 px-3">
            <div className="grid grid-cols-2 gap-3">
              {configFields.map((field) => (
                <div key={field.name} className="space-y-1">
                  <Label className="text-xs">
                    {field.label || field.name}
                    {field.required && <span className="text-destructive ml-1">*</span>}
                  </Label>
                  {renderConfigInput(field)}
                  {field.description && (
                    <p className="text-xs text-muted-foreground">{field.description}</p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Sample Data */}
      <div className="space-y-2">
        <Label className="text-sm font-medium">{str(t.editor.sampleData)}</Label>
        <CodeEditor
          value={sampleData}
          onChange={setSampleData}
          language="json"
          minLines={6}
          maxLines={10}
          readOnly={disabled || isRunning}
          placeholder={str(t.editor.sampleDataPlaceholder)}
        />
        <p className="text-xs text-muted-foreground">{str(t.editor.sampleDataHint)}</p>
      </div>

      {/* Format Selection and Run Button */}
      <div className="flex gap-2">
        <Select
          value={selectedFormat}
          onValueChange={setSelectedFormat}
          disabled={disabled || isRunning}
        >
          <SelectTrigger className="w-32">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {outputFormats.map((fmt) => (
              <SelectItem key={fmt} value={fmt}>
                {fmt.toUpperCase()}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button
          onClick={handlePreview}
          disabled={disabled || isRunning || (!template && !code)}
          className="flex-1"
        >
          {isRunning ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              {str(t.editor.generating)}
            </>
          ) : (
            <>
              <Eye className="w-4 h-4 mr-2" />
              {str(t.editor.preview)}
            </>
          )}
        </Button>
      </div>

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="w-4 h-4" />
          <AlertTitle>{str(t.editor.error)}</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Preview Result */}
      {result && (
        <Card>
          <CardHeader className="py-2 px-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm flex items-center gap-2">
                {result.success ? (
                  <CheckCircle className="w-4 h-4 text-green-500" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-yellow-500" />
                )}
                {str(t.editor.previewResult)}
              </CardTitle>
              <Badge variant="outline" className="gap-1">
                <Clock className="w-3 h-3" />
                {result.generation_time_ms.toFixed(2)}ms
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="py-2 px-3">
            {result.success && result.preview_html ? (
              <div className="border rounded-md overflow-hidden bg-white">
                <ScrollArea className="h-64">
                  <iframe
                    srcDoc={result.preview_html}
                    className="w-full h-64 border-0"
                    title="Report Preview"
                    sandbox="allow-same-origin"
                  />
                </ScrollArea>
              </div>
            ) : result.error ? (
              <Alert variant="destructive">
                <AlertTriangle className="w-4 h-4" />
                <AlertDescription>{result.error}</AlertDescription>
              </Alert>
            ) : null}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default ReporterPreviewPanel
