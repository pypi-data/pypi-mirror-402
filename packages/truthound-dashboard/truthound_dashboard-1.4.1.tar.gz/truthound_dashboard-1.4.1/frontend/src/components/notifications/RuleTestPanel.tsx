/**
 * RuleTestPanel - Rule testing / dry-run UI
 *
 * Provides ability to test routing rules against sample data:
 * - Predefined sample contexts
 * - Custom context editor
 * - Real-time matching results
 * - Match details visualization
 */

import { useState, useCallback } from 'react'
import {
  Play,
  CheckCircle2,
  XCircle,
  Loader2,
  Wand2,
  AlertCircle,
  Copy,
  Check,
  ChevronDown,
  ChevronRight,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { useToast } from '@/hooks/use-toast'
import type { RuleTestContext, RuleTestResult } from '@/api/client'
import { testRoutingRule } from '@/api/client'

interface RuleTestPanelProps {
  ruleConfig: Record<string, unknown>
  className?: string
  onClose?: () => void
}

// Predefined sample contexts for common scenarios
const SAMPLE_CONTEXTS: Array<{
  id: string
  name: string
  description: string
  context: RuleTestContext
}> = [
  {
    id: 'critical_failure',
    name: 'Critical Failure',
    description: 'Critical severity validation failure with many issues',
    context: {
      checkpoint_name: 'daily_data_check',
      status: 'failure',
      severity: 'critical',
      issue_count: 25,
      pass_rate: 0.6,
      tags: ['production', 'critical-path'],
      data_asset: 'sales_transactions.parquet',
      metadata: { env: 'production', pipeline: 'etl-main' },
    },
  },
  {
    id: 'high_severity',
    name: 'High Severity Issue',
    description: 'High severity with moderate issues',
    context: {
      checkpoint_name: 'hourly_metrics',
      status: 'failure',
      severity: 'high',
      issue_count: 10,
      pass_rate: 0.85,
      tags: ['production'],
      data_asset: 'metrics_hourly.csv',
      metadata: { env: 'production' },
    },
  },
  {
    id: 'medium_staging',
    name: 'Medium (Staging)',
    description: 'Medium severity in staging environment',
    context: {
      checkpoint_name: 'staging_validation',
      status: 'failure',
      severity: 'medium',
      issue_count: 5,
      pass_rate: 0.95,
      tags: ['staging', 'test'],
      data_asset: 'test_data.json',
      metadata: { env: 'staging' },
    },
  },
  {
    id: 'success',
    name: 'Successful Check',
    description: 'All validations passed successfully',
    context: {
      checkpoint_name: 'routine_check',
      status: 'success',
      severity: 'info',
      issue_count: 0,
      pass_rate: 1.0,
      tags: ['production'],
      data_asset: 'clean_data.parquet',
      metadata: { env: 'production' },
    },
  },
  {
    id: 'business_hours',
    name: 'Business Hours',
    description: 'Context with timestamp during business hours',
    context: {
      checkpoint_name: 'business_check',
      status: 'failure',
      severity: 'high',
      issue_count: 15,
      pass_rate: 0.75,
      tags: ['production', 'urgent'],
      timestamp: new Date(new Date().setHours(14, 30, 0, 0)).toISOString(),
    },
  },
  {
    id: 'after_hours',
    name: 'After Hours',
    description: 'Context with timestamp outside business hours',
    context: {
      checkpoint_name: 'nightly_job',
      status: 'failure',
      severity: 'high',
      issue_count: 20,
      pass_rate: 0.7,
      tags: ['production', 'batch'],
      timestamp: new Date(new Date().setHours(23, 30, 0, 0)).toISOString(),
    },
  },
]

export function RuleTestPanel({
  ruleConfig,
  className,
  onClose,
}: RuleTestPanelProps) {
  const { toast } = useToast()
  const [mode, setMode] = useState<'presets' | 'custom'>('presets')
  const [selectedPreset, setSelectedPreset] = useState<string>('')
  const [customContext, setCustomContext] = useState<string>(
    JSON.stringify(SAMPLE_CONTEXTS[0].context, null, 2)
  )
  const [jsonError, setJsonError] = useState<string | null>(null)
  const [testing, setTesting] = useState(false)
  const [result, setResult] = useState<RuleTestResult | null>(null)
  const [copied, setCopied] = useState(false)
  const [detailsOpen, setDetailsOpen] = useState(false)

  const handlePresetSelect = (presetId: string) => {
    setSelectedPreset(presetId)
    const preset = SAMPLE_CONTEXTS.find((p) => p.id === presetId)
    if (preset) {
      setCustomContext(JSON.stringify(preset.context, null, 2))
    }
    setResult(null)
  }

  const handleCustomContextChange = (value: string) => {
    setCustomContext(value)
    try {
      JSON.parse(value)
      setJsonError(null)
    } catch (e) {
      setJsonError(e instanceof Error ? e.message : 'Invalid JSON')
    }
  }

  const runTest = useCallback(async () => {
    let context: RuleTestContext
    try {
      context = JSON.parse(customContext)
    } catch {
      toast({
        title: 'Invalid context',
        description: 'Please fix the JSON before testing.',
        variant: 'destructive',
      })
      return
    }

    setTesting(true)
    setResult(null)
    try {
      const testResult = await testRoutingRule(ruleConfig, context)
      setResult(testResult)
    } catch (e) {
      toast({
        title: 'Test failed',
        description: e instanceof Error ? e.message : 'Unknown error',
        variant: 'destructive',
      })
    } finally {
      setTesting(false)
    }
  }, [customContext, ruleConfig, toast])

  const copyResult = async () => {
    if (!result) return
    await navigator.clipboard.writeText(JSON.stringify(result, null, 2))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Wand2 className="h-4 w-4" />
          Test Rule
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Mode Tabs */}
        <Tabs value={mode} onValueChange={(v) => setMode(v as 'presets' | 'custom')}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="presets">Sample Contexts</TabsTrigger>
            <TabsTrigger value="custom">Custom</TabsTrigger>
          </TabsList>

          <TabsContent value="presets" className="space-y-3 mt-3">
            <div className="space-y-2">
              <Label>Select Sample Context</Label>
              <Select value={selectedPreset} onValueChange={handlePresetSelect}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose a sample..." />
                </SelectTrigger>
                <SelectContent>
                  {SAMPLE_CONTEXTS.map((preset) => (
                    <SelectItem key={preset.id} value={preset.id}>
                      <div className="flex flex-col">
                        <span>{preset.name}</span>
                        <span className="text-xs text-muted-foreground">
                          {preset.description}
                        </span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {selectedPreset && (
              <div className="p-3 bg-muted rounded-md">
                <pre className="text-xs overflow-auto max-h-[200px]">
                  {customContext}
                </pre>
              </div>
            )}
          </TabsContent>

          <TabsContent value="custom" className="space-y-3 mt-3">
            <div className="space-y-2">
              <Label>Custom Test Context (JSON)</Label>
              <Textarea
                value={customContext}
                onChange={(e) => handleCustomContextChange(e.target.value)}
                className="font-mono text-sm min-h-[200px]"
                placeholder='{"checkpoint_name": "test", "severity": "high", ...}'
              />
              {jsonError && (
                <div className="flex items-center gap-2 text-sm text-destructive">
                  <AlertCircle className="h-4 w-4" />
                  {jsonError}
                </div>
              )}
            </div>

            <div className="text-xs text-muted-foreground">
              <p className="font-medium mb-1">Available context fields:</p>
              <ul className="list-disc list-inside space-y-0.5">
                <li><code>checkpoint_name</code> - Name of the checkpoint</li>
                <li><code>status</code> - success, failure, error</li>
                <li><code>severity</code> - critical, high, medium, low, info</li>
                <li><code>issue_count</code> - Number of issues found</li>
                <li><code>pass_rate</code> - Pass rate (0.0 - 1.0)</li>
                <li><code>tags</code> - Array of tags</li>
                <li><code>data_asset</code> - Data asset name/path</li>
                <li><code>metadata</code> - Custom metadata object</li>
                <li><code>timestamp</code> - ISO timestamp</li>
              </ul>
            </div>
          </TabsContent>
        </Tabs>

        {/* Run Test Button */}
        <Button
          onClick={runTest}
          disabled={testing || (mode === 'presets' && !selectedPreset) || !!jsonError}
          className="w-full"
        >
          {testing ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Play className="h-4 w-4 mr-2" />
          )}
          Run Test
        </Button>

        {/* Test Result */}
        {result && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {result.matched ? (
                  <Badge className="bg-green-500">
                    <CheckCircle2 className="h-3 w-3 mr-1" />
                    Matched
                  </Badge>
                ) : (
                  <Badge variant="secondary">
                    <XCircle className="h-3 w-3 mr-1" />
                    Not Matched
                  </Badge>
                )}
                <span className="text-xs text-muted-foreground">
                  {result.evaluation_time_ms.toFixed(2)}ms
                </span>
              </div>
              <Button variant="ghost" size="sm" onClick={copyResult}>
                {copied ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
            </div>

            {result.error && (
              <div className="p-2 bg-destructive/10 text-destructive rounded text-sm">
                {result.error}
              </div>
            )}

            <Collapsible open={detailsOpen} onOpenChange={setDetailsOpen}>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" size="sm" className="w-full justify-between">
                  Match Details
                  {detailsOpen ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <pre className="p-3 bg-muted rounded-md text-xs overflow-auto max-h-[200px]">
                  {JSON.stringify(result.match_details, null, 2)}
                </pre>
              </CollapsibleContent>
            </Collapsible>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// Inline test panel for dialog usage
interface RuleTestInlineProps {
  ruleConfig: Record<string, unknown>
  className?: string
  expanded?: boolean
  onToggle?: () => void
}

export function RuleTestInline({
  ruleConfig,
  className,
  expanded,
  onToggle,
}: RuleTestInlineProps) {
  const { toast } = useToast()
  const [selectedPreset, setSelectedPreset] = useState<string>('')
  const [testing, setTesting] = useState(false)
  const [result, setResult] = useState<RuleTestResult | null>(null)

  const runQuickTest = useCallback(async () => {
    const preset = SAMPLE_CONTEXTS.find((p) => p.id === selectedPreset)
    if (!preset) return

    setTesting(true)
    setResult(null)
    try {
      const testResult = await testRoutingRule(ruleConfig, preset.context)
      setResult(testResult)
    } catch (e) {
      toast({
        title: 'Test failed',
        description: e instanceof Error ? e.message : 'Unknown error',
        variant: 'destructive',
      })
    } finally {
      setTesting(false)
    }
  }, [selectedPreset, ruleConfig, toast])

  return (
    <div className={`space-y-2 ${className}`}>
      <Label className="text-xs">Quick Test</Label>
      <div className="flex items-center gap-2">
        <Select value={selectedPreset} onValueChange={setSelectedPreset}>
          <SelectTrigger className="flex-1 h-8 text-xs">
            <SelectValue placeholder="Select sample..." />
          </SelectTrigger>
          <SelectContent>
            {SAMPLE_CONTEXTS.map((preset) => (
              <SelectItem key={preset.id} value={preset.id} className="text-xs">
                {preset.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button
          size="sm"
          variant="outline"
          onClick={runQuickTest}
          disabled={!selectedPreset || testing}
          className="h-8"
        >
          {testing ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <Play className="h-3 w-3" />
          )}
        </Button>
        {result && (
          <Badge
            variant={result.matched ? 'default' : 'secondary'}
            className={`h-6 ${result.matched ? 'bg-green-500' : ''}`}
          >
            {result.matched ? 'Match' : 'No Match'}
          </Badge>
        )}
      </div>
    </div>
  )
}
