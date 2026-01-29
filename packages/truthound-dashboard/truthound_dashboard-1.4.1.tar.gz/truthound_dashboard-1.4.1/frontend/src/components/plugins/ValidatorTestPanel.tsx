/**
 * ValidatorTestPanel - Test panel for custom validators
 *
 * Features:
 * - Test data input (JSON format)
 * - Parameter value inputs
 * - Run test button
 * - Results display with pass/fail status
 * - Error and warning display
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
import { ScrollArea } from '@/components/ui/scroll-area'
import { CodeEditor } from '@/components/common'
import {
  Play,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  Loader2,
  Info,
} from 'lucide-react'
import type { ValidatorParamDefinition, ValidatorTestResult } from './types'

interface ValidatorTestPanelProps {
  code: string
  parameters: ValidatorParamDefinition[]
  onTest: (data: {
    test_data: Record<string, unknown>
    param_values: Record<string, unknown>
  }) => Promise<ValidatorTestResult>
  disabled?: boolean
}

const DEFAULT_TEST_DATA = `{
  "column_name": "example_column",
  "values": [1, 2, null, 4, 5, null],
  "schema": {
    "type": "integer",
    "nullable": true
  },
  "row_count": 6
}`

/**
 * Panel for testing custom validators
 */
export function ValidatorTestPanel({
  code,
  parameters,
  onTest,
  disabled = false,
}: ValidatorTestPanelProps) {
  const t = useIntlayer('plugins')
  const [testData, setTestData] = useState(DEFAULT_TEST_DATA)
  const [paramValues, setParamValues] = useState<Record<string, unknown>>({})
  const [result, setResult] = useState<ValidatorTestResult | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Initialize param values from defaults
  const initParamValues = useCallback(() => {
    const values: Record<string, unknown> = {}
    parameters.forEach((param) => {
      if (param.default !== undefined) {
        values[param.name] = param.default
      }
    })
    setParamValues((prev) => ({ ...values, ...prev }))
  }, [parameters])

  // Handle test execution
  const handleRunTest = useCallback(async () => {
    if (!code.trim()) {
      setError(str(t.editor.testNoCode))
      return
    }

    setIsRunning(true)
    setError(null)
    setResult(null)

    try {
      // Parse test data JSON
      let parsedData: Record<string, unknown>
      try {
        parsedData = JSON.parse(testData)
      } catch {
        setError(str(t.editor.testInvalidJson))
        setIsRunning(false)
        return
      }

      // Run the test
      const testResult = await onTest({
        test_data: parsedData,
        param_values: paramValues,
      })
      setResult(testResult)
    } catch (err) {
      setError(err instanceof Error ? err.message : str(t.editor.testError))
    } finally {
      setIsRunning(false)
    }
  }, [code, testData, paramValues, onTest, t])

  // Handle param value change
  const handleParamChange = useCallback((name: string, value: unknown) => {
    setParamValues((prev) => ({ ...prev, [name]: value }))
  }, [])

  // Render parameter input
  const renderParamInput = (param: ValidatorParamDefinition) => {
    const value = paramValues[param.name]

    switch (param.type) {
      case 'boolean':
        return (
          <select
            value={value?.toString() || 'false'}
            onChange={(e) => handleParamChange(param.name, e.target.value === 'true')}
            className="h-8 text-sm border rounded px-2 bg-background"
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
            onChange={(e) => handleParamChange(param.name, e.target.value)}
            className="h-8 text-sm border rounded px-2 bg-background"
            disabled={disabled || isRunning}
          >
            <option value="">Select...</option>
            {param.options?.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        )
      case 'integer':
      case 'float':
        return (
          <Input
            type="number"
            value={value?.toString() || ''}
            onChange={(e) =>
              handleParamChange(
                param.name,
                param.type === 'integer'
                  ? parseInt(e.target.value, 10)
                  : parseFloat(e.target.value)
              )
            }
            disabled={disabled || isRunning}
            className="h-8 text-sm"
            min={param.min_value}
            max={param.max_value}
          />
        )
      default:
        return (
          <Input
            value={(value as string) || ''}
            onChange={(e) => handleParamChange(param.name, e.target.value)}
            disabled={disabled || isRunning}
            className="h-8 text-sm"
          />
        )
    }
  }

  return (
    <div className="space-y-4">
      {/* Parameter Values */}
      {parameters.length > 0 && (
        <Card>
          <CardHeader className="py-2 px-3">
            <CardTitle className="text-sm">{str(t.editor.testParams)}</CardTitle>
          </CardHeader>
          <CardContent className="py-2 px-3">
            <div className="grid grid-cols-2 gap-3">
              {parameters.map((param) => (
                <div key={param.name} className="space-y-1">
                  <Label className="text-xs">
                    {param.name}
                    {param.required && <span className="text-destructive ml-1">*</span>}
                  </Label>
                  {renderParamInput(param)}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Test Data */}
      <div className="space-y-2">
        <Label className="text-sm font-medium">{str(t.editor.testData)}</Label>
        <CodeEditor
          value={testData}
          onChange={setTestData}
          language="json"
          minLines={6}
          maxLines={10}
          readOnly={disabled || isRunning}
          placeholder={str(t.editor.testDataPlaceholder)}
        />
        <p className="text-xs text-muted-foreground">{str(t.editor.testDataHint)}</p>
      </div>

      {/* Run Button */}
      <Button
        onClick={handleRunTest}
        disabled={disabled || isRunning || !code.trim()}
        className="w-full"
      >
        {isRunning ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            {str(t.editor.running)}
          </>
        ) : (
          <>
            <Play className="w-4 h-4 mr-2" />
            {str(t.editor.runTest)}
          </>
        )}
      </Button>

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="w-4 h-4" />
          <AlertTitle>{str(t.editor.error)}</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Results Display */}
      {result && (
        <Card>
          <CardHeader className="py-2 px-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm flex items-center gap-2">
                {result.success ? (
                  result.passed ? (
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  ) : (
                    <XCircle className="w-4 h-4 text-destructive" />
                  )
                ) : (
                  <AlertTriangle className="w-4 h-4 text-yellow-500" />
                )}
                {str(t.editor.testResults)}
              </CardTitle>
              <div className="flex items-center gap-2">
                <Badge variant={result.passed ? 'default' : 'destructive'}>
                  {result.passed ? str(t.editor.passed) : str(t.editor.failed)}
                </Badge>
                <Badge variant="outline" className="gap-1">
                  <Clock className="w-3 h-3" />
                  {result.execution_time_ms.toFixed(2)}ms
                </Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent className="py-2 px-3">
            <ScrollArea className="max-h-48">
              <div className="space-y-3">
                {/* Message */}
                {result.result?.message && (
                  <div className="text-sm">{result.result.message}</div>
                )}

                {/* Issues */}
                {result.result?.issues && result.result.issues.length > 0 && (
                  <div className="space-y-1">
                    <Label className="text-xs text-muted-foreground">Issues:</Label>
                    {result.result.issues.map((issue, idx) => (
                      <div
                        key={idx}
                        className="flex items-start gap-2 text-sm p-2 bg-muted/50 rounded"
                      >
                        {issue.severity === 'error' ? (
                          <XCircle className="w-4 h-4 text-destructive shrink-0 mt-0.5" />
                        ) : issue.severity === 'warning' ? (
                          <AlertTriangle className="w-4 h-4 text-yellow-500 shrink-0 mt-0.5" />
                        ) : (
                          <Info className="w-4 h-4 text-blue-500 shrink-0 mt-0.5" />
                        )}
                        <span>{issue.message}</span>
                        {issue.row !== undefined && (
                          <Badge variant="outline" className="ml-auto">
                            Row {issue.row}
                          </Badge>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Details */}
                {result.result?.details && Object.keys(result.result.details).length > 0 && (
                  <div className="space-y-1">
                    <Label className="text-xs text-muted-foreground">Details:</Label>
                    <pre className="text-xs bg-muted/50 p-2 rounded overflow-auto">
                      {JSON.stringify(result.result.details, null, 2)}
                    </pre>
                  </div>
                )}

                {/* Warnings */}
                {result.warnings && result.warnings.length > 0 && (
                  <div className="space-y-1">
                    <Label className="text-xs text-muted-foreground">Warnings:</Label>
                    {result.warnings.map((warning, idx) => (
                      <div
                        key={idx}
                        className="flex items-center gap-2 text-sm text-yellow-600"
                      >
                        <AlertTriangle className="w-4 h-4" />
                        {warning}
                      </div>
                    ))}
                  </div>
                )}

                {/* Error */}
                {result.error && (
                  <Alert variant="destructive">
                    <AlertTriangle className="w-4 h-4" />
                    <AlertDescription>{result.error}</AlertDescription>
                  </Alert>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default ValidatorTestPanel
