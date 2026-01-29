/**
 * ExpressionRuleEditor - Specialized editor for Python-like expression rules.
 *
 * Features:
 * - Code editor for Python expressions
 * - Context variables panel with insertion support
 * - Expression validation with syntax checking
 * - Example expressions dropdown
 * - Live preview with sample data
 *
 * This component integrates with the RuleBuilder to provide a rich editing
 * experience for expression-based routing rules.
 */

import { useState, useCallback, useRef, useMemo, useEffect } from 'react'
import {
  Play,
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Loader2,
  Variable,
  Braces,
  Code2,
  Sparkles,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Slider } from '@/components/ui/slider'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { cn } from '@/lib/utils'
import { CodeEditor, type CodeEditorRef } from '@/components/common/CodeEditor'
import { useIntlayer } from 'react-intlayer'
import { str } from '@/lib/intlayer-utils'

// =============================================================================
// Types
// =============================================================================

export interface ExpressionConfig {
  expression: string
  timeout_seconds?: number
}

export interface ContextVariable {
  name: string
  type: string
  description: string
  example: string
}

export interface ExampleExpression {
  name: string
  expression: string
  description: string
}

export interface ValidationResult {
  valid: boolean
  error?: string
  error_line?: number
}

export interface PreviewResult {
  result: boolean
  error?: string
}

export interface ExpressionRuleEditorProps {
  /** Current expression configuration */
  config: ExpressionConfig
  /** Change handler */
  onChange: (config: ExpressionConfig) => void
  /** Optional validation function (called on debounce) */
  onValidate?: (expression: string) => Promise<ValidationResult>
  /** Additional context variables to show */
  additionalVariables?: ContextVariable[]
  /** Class name for the container */
  className?: string
}

// =============================================================================
// Constants
// =============================================================================

/**
 * Default context variables available in expressions.
 * These match the ExpressionContext fields from the backend.
 */
const DEFAULT_CONTEXT_VARIABLES: ContextVariable[] = [
  {
    name: 'severity',
    type: 'string',
    description: 'Highest severity level (critical, high, medium, low, info)',
    example: "'critical'",
  },
  {
    name: 'issue_count',
    type: 'int',
    description: 'Number of validation issues found',
    example: '5',
  },
  {
    name: 'status',
    type: 'string',
    description: 'Validation status (success, warning, failure, error)',
    example: "'failure'",
  },
  {
    name: 'pass_rate',
    type: 'float',
    description: 'Validation pass rate (0.0 to 1.0)',
    example: '0.85',
  },
  {
    name: 'tags',
    type: 'list',
    description: 'List of tags associated with the notification',
    example: "['production', 'critical']",
  },
  {
    name: 'metadata',
    type: 'dict',
    description: 'Custom metadata dictionary',
    example: "{'environment': 'prod'}",
  },
  {
    name: 'timestamp',
    type: 'datetime',
    description: 'When the validation occurred',
    example: 'datetime.now()',
  },
  {
    name: 'checkpoint_name',
    type: 'string',
    description: 'Name of the validation checkpoint',
    example: "'orders_validation'",
  },
  {
    name: 'action_type',
    type: 'string',
    description: 'Type of action (check, learn, profile, compare, scan, mask)',
    example: "'check'",
  },
  {
    name: 'issues',
    type: 'list',
    description: 'List of issue identifiers',
    example: "['null_values', 'duplicates']",
  },
]

/**
 * Built-in functions available in expressions.
 */
const BUILTIN_FUNCTIONS: ContextVariable[] = [
  { name: 'len()', type: 'function', description: 'Get length of a collection', example: 'len(issues)' },
  { name: 'any()', type: 'function', description: 'True if any element is truthy', example: "any(t.startswith('prod') for t in tags)" },
  { name: 'all()', type: 'function', description: 'True if all elements are truthy', example: 'all(x > 0 for x in values)' },
  { name: 'sum()', type: 'function', description: 'Sum of elements', example: 'sum(counts)' },
  { name: 'min()', type: 'function', description: 'Minimum value', example: 'min(values)' },
  { name: 'max()', type: 'function', description: 'Maximum value', example: 'max(values)' },
  { name: 'abs()', type: 'function', description: 'Absolute value', example: 'abs(diff)' },
  { name: 'round()', type: 'function', description: 'Round a number', example: 'round(pass_rate, 2)' },
  { name: 'str()', type: 'function', description: 'Convert to string', example: 'str(issue_count)' },
  { name: 'int()', type: 'function', description: 'Convert to integer', example: 'int(value)' },
  { name: 'float()', type: 'function', description: 'Convert to float', example: 'float(value)' },
  { name: 'bool()', type: 'function', description: 'Convert to boolean', example: 'bool(value)' },
]

/**
 * Example expressions for common use cases.
 */
const EXAMPLE_EXPRESSIONS: ExampleExpression[] = [
  {
    name: 'Critical severity',
    expression: "severity == 'critical'",
    description: 'Match critical severity notifications',
  },
  {
    name: 'High or critical severity',
    expression: "severity in ('high', 'critical')",
    description: 'Match high or critical severity',
  },
  {
    name: 'Low pass rate',
    expression: 'pass_rate < 0.8',
    description: 'Match when pass rate is below 80%',
  },
  {
    name: 'Many issues',
    expression: 'issue_count > 10',
    description: 'Match when more than 10 issues found',
  },
  {
    name: 'Production tag',
    expression: "'production' in tags",
    description: 'Match notifications with production tag',
  },
  {
    name: 'Critical and low pass rate',
    expression: "severity == 'critical' and pass_rate < 0.9",
    description: 'Match critical severity with pass rate below 90%',
  },
  {
    name: 'Environment check',
    expression: "metadata.get('environment') == 'production'",
    description: 'Match production environment from metadata',
  },
  {
    name: 'Complex condition',
    expression: "(severity == 'critical' or len(issues) > 10) and 'production' in tags",
    description: 'Complex condition with multiple checks',
  },
  {
    name: 'Null issues present',
    expression: "any(i.startswith('null') for i in issues)",
    description: 'Match if any null-related issues exist',
  },
  {
    name: 'Failure status',
    expression: "status in ('failure', 'error')",
    description: 'Match failure or error status',
  },
]

/**
 * Sample data for preview evaluation.
 */
const SAMPLE_CONTEXT = {
  severity: 'high',
  issue_count: 5,
  status: 'failure',
  pass_rate: 0.85,
  tags: ['production', 'orders'],
  metadata: { environment: 'production', table: 'orders' },
  timestamp: new Date().toISOString(),
  checkpoint_name: 'orders_validation',
  action_type: 'check',
  issues: ['null_values', 'duplicates'],
}

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Simple expression validator using regex patterns.
 * This provides basic client-side validation before API calls.
 */
function validateExpressionSyntax(expression: string): ValidationResult {
  if (!expression.trim()) {
    return { valid: false, error: 'Expression cannot be empty' }
  }

  // Check for balanced parentheses
  let parenCount = 0
  let bracketCount = 0
  let braceCount = 0
  for (const char of expression) {
    if (char === '(') parenCount++
    else if (char === ')') parenCount--
    else if (char === '[') bracketCount++
    else if (char === ']') bracketCount--
    else if (char === '{') braceCount++
    else if (char === '}') braceCount--

    if (parenCount < 0 || bracketCount < 0 || braceCount < 0) {
      return { valid: false, error: 'Unbalanced brackets or parentheses' }
    }
  }

  if (parenCount !== 0) {
    return { valid: false, error: 'Unbalanced parentheses' }
  }
  if (bracketCount !== 0) {
    return { valid: false, error: 'Unbalanced square brackets' }
  }
  if (braceCount !== 0) {
    return { valid: false, error: 'Unbalanced curly braces' }
  }

  // Check for dangerous patterns (these would be caught by backend too)
  const dangerousPatterns = [
    /__\w+__/,        // Dunder attributes
    /\bimport\b/,     // Import statements
    /\bexec\b/,       // exec function
    /\beval\b/,       // eval function
    /\bcompile\b/,    // compile function
    /\bglobals\b/,    // globals access
    /\blocals\b/,     // locals access
  ]

  for (const pattern of dangerousPatterns) {
    if (pattern.test(expression)) {
      return {
        valid: false,
        error: `Expression contains disallowed pattern: ${pattern.source}`,
      }
    }
  }

  return { valid: true }
}

/**
 * Simple preview evaluator (client-side simulation).
 * Note: This is a simplified evaluation and may not match backend behavior exactly.
 */
function evaluatePreview(expression: string, context: typeof SAMPLE_CONTEXT): PreviewResult {
  try {
    // Create a safe evaluation function using Function constructor
    // This is intentionally limited and won't support all Python syntax
    // It's just for preview purposes

    // Replace Python-specific syntax with JavaScript equivalents
    const jsExpression = expression
      // String membership: 'x' in list -> list.includes('x')
      .replace(/'([^']+)'\s+in\s+(\w+)/g, '$2.includes("$1")')
      .replace(/"([^"]+)"\s+in\s+(\w+)/g, '$2.includes("$1")')
      // Python 'and'/'or'/'not' -> JavaScript
      .replace(/\band\b/g, '&&')
      .replace(/\bor\b/g, '||')
      .replace(/\bnot\b/g, '!')
      // Python True/False/None
      .replace(/\bTrue\b/g, 'true')
      .replace(/\bFalse\b/g, 'false')
      .replace(/\bNone\b/g, 'null')

    // Simple evaluation with limited scope
    const evalFunc = new Function(
      'severity',
      'issue_count',
      'status',
      'pass_rate',
      'tags',
      'metadata',
      'timestamp',
      'checkpoint_name',
      'action_type',
      'issues',
      'len',
      'any',
      'all',
      `return ${jsExpression}`
    )

    const result = evalFunc(
      context.severity,
      context.issue_count,
      context.status,
      context.pass_rate,
      context.tags,
      context.metadata,
      context.timestamp,
      context.checkpoint_name,
      context.action_type,
      context.issues,
      (arr: unknown[]) => arr?.length ?? 0,
      (arr: unknown[]) => arr?.some((x) => x) ?? false,
      (arr: unknown[]) => arr?.every((x) => x) ?? false
    )

    return { result: Boolean(result) }
  } catch (e) {
    return {
      result: false,
      error: e instanceof Error ? e.message : 'Evaluation error',
    }
  }
}

// =============================================================================
// Sub-Components
// =============================================================================

interface VariablePanelProps {
  variables: ContextVariable[]
  builtins: ContextVariable[]
  onInsert: (text: string) => void
}

function VariablePanel({ variables, builtins, onInsert }: VariablePanelProps) {
  const [variablesOpen, setVariablesOpen] = useState(true)
  const [builtinsOpen, setBuiltinsOpen] = useState(false)
  const content = useIntlayer('notificationsAdvanced')

  return (
    <div className="space-y-2">
      {/* Context Variables */}
      <Collapsible open={variablesOpen} onOpenChange={setVariablesOpen}>
        <CollapsibleTrigger className="flex items-center gap-2 w-full text-left text-sm font-medium py-1 hover:text-primary transition-colors">
          {variablesOpen ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
          <Variable className="h-4 w-4" />
          <span>{str(content.expressionEditor?.contextVariables) || 'Context Variables'}</span>
          <Badge variant="secondary" className="ml-auto text-xs">
            {variables.length}
          </Badge>
        </CollapsibleTrigger>
        <CollapsibleContent className="pt-2">
          <div className="space-y-1 pl-6">
            {variables.map((v) => (
              <TooltipProvider key={v.name}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      className={cn(
                        'flex items-center justify-between w-full',
                        'px-2 py-1.5 rounded text-sm text-left',
                        'hover:bg-muted/50 transition-colors',
                        'group'
                      )}
                      onClick={() => onInsert(v.name)}
                    >
                      <span className="font-mono text-primary">{v.name}</span>
                      <Badge variant="outline" className="text-xs opacity-60 group-hover:opacity-100">
                        {v.type}
                      </Badge>
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="right" className="max-w-xs">
                    <p className="text-sm">{v.description}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Example: <code className="font-mono">{v.example}</code>
                    </p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            ))}
          </div>
        </CollapsibleContent>
      </Collapsible>

      {/* Built-in Functions */}
      <Collapsible open={builtinsOpen} onOpenChange={setBuiltinsOpen}>
        <CollapsibleTrigger className="flex items-center gap-2 w-full text-left text-sm font-medium py-1 hover:text-primary transition-colors">
          {builtinsOpen ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
          <Braces className="h-4 w-4" />
          <span>{str(content.expressionEditor?.builtinFunctions) || 'Built-in Functions'}</span>
          <Badge variant="secondary" className="ml-auto text-xs">
            {builtins.length}
          </Badge>
        </CollapsibleTrigger>
        <CollapsibleContent className="pt-2">
          <div className="space-y-1 pl-6">
            {builtins.map((f) => (
              <TooltipProvider key={f.name}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      className={cn(
                        'flex items-center justify-between w-full',
                        'px-2 py-1.5 rounded text-sm text-left',
                        'hover:bg-muted/50 transition-colors'
                      )}
                      onClick={() => onInsert(f.name)}
                    >
                      <span className="font-mono text-blue-500">{f.name}</span>
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="right" className="max-w-xs">
                    <p className="text-sm">{f.description}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Example: <code className="font-mono">{f.example}</code>
                    </p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            ))}
          </div>
        </CollapsibleContent>
      </Collapsible>
    </div>
  )
}

interface ExampleSelectorProps {
  examples: ExampleExpression[]
  onSelect: (expression: string) => void
}

function ExampleSelector({ examples, onSelect }: ExampleSelectorProps) {
  const content = useIntlayer('notificationsAdvanced')

  return (
    <Select onValueChange={onSelect}>
      <SelectTrigger className="h-9">
        <Sparkles className="h-4 w-4 mr-2 text-muted-foreground" />
        <SelectValue placeholder={str(content.expressionEditor?.selectExample) || 'Select example...'} />
      </SelectTrigger>
      <SelectContent>
        {examples.map((ex) => (
          <SelectItem key={ex.name} value={ex.expression}>
            <div className="flex flex-col items-start">
              <span className="font-medium">{ex.name}</span>
              <span className="text-xs text-muted-foreground">{ex.description}</span>
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

interface PreviewPanelProps {
  expression: string
  context: typeof SAMPLE_CONTEXT
  onContextChange: (context: typeof SAMPLE_CONTEXT) => void
}

function PreviewPanel({ expression, context, onContextChange }: PreviewPanelProps) {
  const content = useIntlayer('notificationsAdvanced')
  const preview = useMemo(() => {
    if (!expression.trim()) {
      return { result: false, error: 'Empty expression' }
    }
    return evaluatePreview(expression, context)
  }, [expression, context])

  return (
    <Card className="border-dashed">
      <CardHeader className="py-3 px-4">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Play className="h-4 w-4" />
          {str(content.expressionEditor?.livePreview) || 'Live Preview'}
        </CardTitle>
      </CardHeader>
      <CardContent className="py-3 px-4 pt-0 space-y-4">
        {/* Preview Result */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">
            {str(content.expressionEditor?.result) || 'Result'}:
          </span>
          {preview.error ? (
            <Badge variant="destructive" className="gap-1">
              <AlertCircle className="h-3 w-3" />
              {str(content.expressionEditor?.error) || 'Error'}
            </Badge>
          ) : preview.result ? (
            <Badge className="gap-1 bg-green-500/10 text-green-600 border-green-500/20">
              <CheckCircle2 className="h-3 w-3" />
              {str(content.expressionEditor?.matches) || 'Matches'} (true)
            </Badge>
          ) : (
            <Badge variant="secondary" className="gap-1">
              {str(content.expressionEditor?.noMatch) || 'No Match'} (false)
            </Badge>
          )}
        </div>

        {preview.error && (
          <p className="text-xs text-destructive bg-destructive/10 p-2 rounded">
            {preview.error}
          </p>
        )}

        {/* Editable Sample Data */}
        <div className="space-y-3">
          <p className="text-xs text-muted-foreground font-medium">
            {str(content.expressionEditor?.sampleData) || 'Sample Data'}:
          </p>

          <div className="grid grid-cols-2 gap-3">
            {/* Severity */}
            <div className="space-y-1">
              <Label className="text-xs">severity</Label>
              <Select
                value={context.severity}
                onValueChange={(v) => onContextChange({ ...context, severity: v })}
              >
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="info">info</SelectItem>
                  <SelectItem value="low">low</SelectItem>
                  <SelectItem value="medium">medium</SelectItem>
                  <SelectItem value="high">high</SelectItem>
                  <SelectItem value="critical">critical</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Status */}
            <div className="space-y-1">
              <Label className="text-xs">status</Label>
              <Select
                value={context.status}
                onValueChange={(v) => onContextChange({ ...context, status: v })}
              >
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="success">success</SelectItem>
                  <SelectItem value="warning">warning</SelectItem>
                  <SelectItem value="failure">failure</SelectItem>
                  <SelectItem value="error">error</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Issue Count */}
            <div className="space-y-1">
              <Label className="text-xs">issue_count: {context.issue_count}</Label>
              <Slider
                min={0}
                max={50}
                step={1}
                value={[context.issue_count]}
                onValueChange={([v]) => onContextChange({ ...context, issue_count: v })}
              />
            </div>

            {/* Pass Rate */}
            <div className="space-y-1">
              <Label className="text-xs">pass_rate: {context.pass_rate.toFixed(2)}</Label>
              <Slider
                min={0}
                max={1}
                step={0.01}
                value={[context.pass_rate]}
                onValueChange={([v]) => onContextChange({ ...context, pass_rate: v })}
              />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// =============================================================================
// Main Component
// =============================================================================

export function ExpressionRuleEditor({
  config,
  onChange,
  onValidate,
  additionalVariables = [],
  className,
}: ExpressionRuleEditorProps) {
  const content = useIntlayer('notificationsAdvanced')
  const editorRef = useRef<CodeEditorRef>(null)
  const validationTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  // State
  const [validation, setValidation] = useState<ValidationResult>({ valid: true })
  const [isValidating, setIsValidating] = useState(false)
  const [previewContext, setPreviewContext] = useState(SAMPLE_CONTEXT)
  const [showAdvanced, setShowAdvanced] = useState(false)

  // Combine default and additional variables
  const allVariables = useMemo(
    () => [...DEFAULT_CONTEXT_VARIABLES, ...additionalVariables],
    [additionalVariables]
  )

  // Handle expression change with debounced validation
  const handleExpressionChange = useCallback(
    (expression: string) => {
      onChange({ ...config, expression })

      // Clear previous timeout
      if (validationTimeoutRef.current) {
        clearTimeout(validationTimeoutRef.current)
      }

      // Basic client-side validation immediately
      const basicResult = validateExpressionSyntax(expression)
      if (!basicResult.valid) {
        setValidation(basicResult)
        return
      }

      // Debounced server-side validation
      if (onValidate) {
        setIsValidating(true)
        validationTimeoutRef.current = setTimeout(async () => {
          try {
            const result = await onValidate(expression)
            setValidation(result)
          } catch {
            setValidation({ valid: false, error: 'Validation request failed' })
          } finally {
            setIsValidating(false)
          }
        }, 500)
      } else {
        setValidation(basicResult)
      }
    },
    [config, onChange, onValidate]
  )

  // Handle timeout change
  const handleTimeoutChange = useCallback(
    (timeout: number) => {
      onChange({ ...config, timeout_seconds: timeout })
    },
    [config, onChange]
  )

  // Insert variable at cursor
  const handleInsertVariable = useCallback((text: string) => {
    editorRef.current?.insertAtCursor(text)
  }, [])

  // Handle example selection
  const handleExampleSelect = useCallback(
    (expression: string) => {
      handleExpressionChange(expression)
    },
    [handleExpressionChange]
  )

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (validationTimeoutRef.current) {
        clearTimeout(validationTimeoutRef.current)
      }
    }
  }, [])

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header with Example Selector */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Code2 className="h-5 w-5 text-primary" />
          <span className="font-medium">
            {str(content.expressionEditor?.title) || 'Expression Editor'}
          </span>
        </div>
        <div className="w-64">
          <ExampleSelector examples={EXAMPLE_EXPRESSIONS} onSelect={handleExampleSelect} />
        </div>
      </div>

      {/* Main Editor Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Code Editor (2 columns) */}
        <div className="lg:col-span-2 space-y-2">
          <div className="flex items-center justify-between">
            <Label className="text-sm font-medium">
              {str(content.expressionEditor?.expressionLabel) || 'Expression'}
            </Label>
            <div className="flex items-center gap-2">
              {isValidating && (
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              )}
              {!isValidating && validation.valid && config.expression.trim() && (
                <Badge variant="outline" className="gap-1 text-green-600 border-green-500/30">
                  <CheckCircle2 className="h-3 w-3" />
                  {str(content.expressionEditor?.valid) || 'Valid'}
                </Badge>
              )}
              {!isValidating && !validation.valid && (
                <Badge variant="destructive" className="gap-1">
                  <AlertCircle className="h-3 w-3" />
                  {str(content.expressionEditor?.invalid) || 'Invalid'}
                </Badge>
              )}
            </div>
          </div>

          <CodeEditor
            ref={editorRef}
            value={config.expression}
            onChange={handleExpressionChange}
            language="python"
            placeholder={str(content.expressionEditor?.placeholder) || "Enter a Python-like expression, e.g., severity == 'critical' and pass_rate < 0.9"}
            minLines={6}
            maxLines={15}
            errorLines={validation.error_line ? [validation.error_line] : []}
          />

          {/* Validation Error */}
          {!validation.valid && validation.error && (
            <div className="flex items-start gap-2 p-2 rounded bg-destructive/10 text-destructive text-sm">
              <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <span>{validation.error}</span>
            </div>
          )}

          {/* Helper Text */}
          <p className="text-xs text-muted-foreground">
            {str(content.expressionEditor?.helperText) ||
              'Write a Python-like boolean expression. Click variables on the right to insert them.'}
          </p>
        </div>

        {/* Variables Panel (1 column) */}
        <div className="space-y-4">
          <Card>
            <CardContent className="py-3 px-4">
              <VariablePanel
                variables={allVariables}
                builtins={BUILTIN_FUNCTIONS}
                onInsert={handleInsertVariable}
              />
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Live Preview */}
      <PreviewPanel
        expression={config.expression}
        context={previewContext}
        onContextChange={setPreviewContext}
      />

      {/* Advanced Settings */}
      <Collapsible open={showAdvanced} onOpenChange={setShowAdvanced}>
        <CollapsibleTrigger className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
          {showAdvanced ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
          {str(content.expressionEditor?.advancedSettings) || 'Advanced Settings'}
        </CollapsibleTrigger>
        <CollapsibleContent className="pt-4">
          <Card>
            <CardContent className="py-4 px-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label className="text-sm font-medium">
                      {str(content.expressionEditor?.timeoutLabel) || 'Evaluation Timeout'}
                    </Label>
                    <p className="text-xs text-muted-foreground">
                      {str(content.expressionEditor?.timeoutDescription) ||
                        'Maximum time allowed for expression evaluation (seconds)'}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Slider
                      min={0.1}
                      max={10}
                      step={0.1}
                      value={[config.timeout_seconds ?? 1.0]}
                      onValueChange={([v]) => handleTimeoutChange(v)}
                      className="w-32"
                    />
                    <Input
                      type="number"
                      min={0.1}
                      max={10}
                      step={0.1}
                      value={config.timeout_seconds ?? 1.0}
                      onChange={(e) => handleTimeoutChange(Number(e.target.value))}
                      className="w-20 h-8"
                    />
                    <span className="text-xs text-muted-foreground">s</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </CollapsibleContent>
      </Collapsible>
    </div>
  )
}

export default ExpressionRuleEditor
