/**
 * Jinja2RuleEditor - Specialized editor for Jinja2 templates in routing rules.
 *
 * Features:
 * - Jinja2 syntax highlighting ({{ }}, {% %}, {# #})
 * - Context variables panel with descriptions
 * - Template snippets/autocomplete
 * - Common filters documentation
 * - Live template preview with sample event data
 * - Real-time validation
 *
 * Architecture:
 * - Uses CodeEditor as base component
 * - Side-by-side layout: editor | preview
 * - Integrates with RuleBuilder for jinja2 rule type
 */

import { useState, useCallback, useMemo, useEffect, useRef } from 'react'
import {
  Code2,
  Play,
  Copy,
  Check,
  AlertTriangle,
  ChevronDown,
  Sparkles,
  BookOpen,
  Braces,
  Filter,
  Variable,
  RefreshCw,
  Info,
} from 'lucide-react'
import { useIntlayer } from 'react-intlayer'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'
import { str } from '@/lib/intlayer-utils'
import { CodeEditor, type CodeEditorRef } from '@/components/common/CodeEditor'

// =============================================================================
// Types
// =============================================================================

export interface Jinja2RuleConfig {
  type: 'jinja2'
  template: string
  expected_result?: string
}

export interface Jinja2RuleEditorProps {
  config: Jinja2RuleConfig
  onChange: (config: Jinja2RuleConfig) => void
  onValidate?: (template: string) => Promise<ValidationResult>
  className?: string
}

export interface ValidationResult {
  valid: boolean
  rendered_output?: string
  error?: string
  error_line?: number
}

export interface ContextVariable {
  name: string
  type: string
  description: string
  example: string | number | boolean | string[]
}

export interface TemplateSnippet {
  name: string
  description: string
  template: string
  category: 'control' | 'expression' | 'filter' | 'comment'
}

export interface FilterInfo {
  name: string
  description: string
  example: string
  output: string
}

// =============================================================================
// Constants
// =============================================================================

/**
 * Context variables available in Jinja2 templates.
 * These match the backend RouteContext variables.
 */
const CONTEXT_VARIABLES: ContextVariable[] = [
  {
    name: 'event.severity',
    type: 'string',
    description: 'Issue severity level (critical, high, medium, low, info)',
    example: 'critical',
  },
  {
    name: 'event.issue_count',
    type: 'number',
    description: 'Number of validation issues found',
    example: 5,
  },
  {
    name: 'event.status',
    type: 'string',
    description: 'Validation status (success, warning, failure, error)',
    example: 'failure',
  },
  {
    name: 'event.pass_rate',
    type: 'number',
    description: 'Validation pass rate (0.0 - 1.0)',
    example: 0.85,
  },
  {
    name: 'event.tags',
    type: 'string[]',
    description: 'Tags associated with the event',
    example: ['production', 'critical'],
  },
  {
    name: 'event.metadata',
    type: 'object',
    description: 'Additional metadata dictionary',
    example: '{"environment": "prod"}',
  },
  {
    name: 'event.source_name',
    type: 'string',
    description: 'Name of the data source',
    example: 'users_production.csv',
  },
  {
    name: 'event.validation_name',
    type: 'string',
    description: 'Name of the validation that ran',
    example: 'Daily Data Quality Check',
  },
  {
    name: 'severity',
    type: 'string',
    description: 'Direct access to severity (shorthand)',
    example: 'high',
  },
  {
    name: 'issue_count',
    type: 'number',
    description: 'Direct access to issue count (shorthand)',
    example: 3,
  },
  {
    name: 'pass_rate',
    type: 'number',
    description: 'Direct access to pass rate (shorthand)',
    example: 0.92,
  },
  {
    name: 'tags',
    type: 'string[]',
    description: 'Direct access to tags (shorthand)',
    example: ['staging'],
  },
  {
    name: 'data_asset',
    type: 'string',
    description: 'Data asset name or path',
    example: 'warehouse/orders',
  },
  {
    name: 'status',
    type: 'string',
    description: 'Direct access to status (shorthand)',
    example: 'warning',
  },
  {
    name: 'has_issues',
    type: 'boolean',
    description: 'True if issue_count > 0',
    example: true,
  },
  {
    name: 'is_failure',
    type: 'boolean',
    description: 'True if status is failure or error',
    example: false,
  },
]

/**
 * Template snippets for quick insertion.
 */
const TEMPLATE_SNIPPETS: TemplateSnippet[] = [
  {
    name: 'If-Else',
    description: 'Conditional block',
    template: '{% if condition %}\n  ...\n{% else %}\n  ...\n{% endif %}',
    category: 'control',
  },
  {
    name: 'If-Elif-Else',
    description: 'Multiple conditions',
    template: '{% if condition1 %}\n  ...\n{% elif condition2 %}\n  ...\n{% else %}\n  ...\n{% endif %}',
    category: 'control',
  },
  {
    name: 'For Loop',
    description: 'Iterate over items',
    template: '{% for item in items %}\n  {{ item }}\n{% endfor %}',
    category: 'control',
  },
  {
    name: 'Variable',
    description: 'Output a variable',
    template: '{{ variable_name }}',
    category: 'expression',
  },
  {
    name: 'Filter',
    description: 'Apply a filter',
    template: '{{ variable | filter_name }}',
    category: 'filter',
  },
  {
    name: 'Comment',
    description: 'Add a comment',
    template: '{# This is a comment #}',
    category: 'comment',
  },
  {
    name: 'Severity Check',
    description: 'Check if severity is critical',
    template: "{{ severity == 'critical' }}",
    category: 'expression',
  },
  {
    name: 'High Severity',
    description: 'Check high or critical',
    template: "{{ severity in ['critical', 'high'] }}",
    category: 'expression',
  },
  {
    name: 'Issue Threshold',
    description: 'Check issue count threshold',
    template: '{{ issue_count > 5 }}',
    category: 'expression',
  },
  {
    name: 'Pass Rate Check',
    description: 'Check pass rate below threshold',
    template: '{{ pass_rate < 0.9 }}',
    category: 'expression',
  },
  {
    name: 'Tag Contains',
    description: 'Check if tag exists',
    template: "{{ 'production' in tags }}",
    category: 'expression',
  },
  {
    name: 'Combined Condition',
    description: 'Multiple conditions combined',
    template: "{{ severity == 'critical' and issue_count > 3 }}",
    category: 'expression',
  },
]

/**
 * Available Jinja2 filters with documentation.
 */
const JINJA2_FILTERS: FilterInfo[] = [
  {
    name: 'severity_level',
    description: 'Convert severity string to numeric level (5=critical to 1=info)',
    example: "{{ severity | severity_level }}",
    output: '5',
  },
  {
    name: 'is_critical',
    description: 'Check if severity is critical',
    example: '{{ severity | is_critical }}',
    output: 'True',
  },
  {
    name: 'is_high_or_critical',
    description: 'Check if severity is high or critical',
    example: '{{ severity | is_high_or_critical }}',
    output: 'True',
  },
  {
    name: 'format_percentage',
    description: 'Format number as percentage',
    example: '{{ pass_rate | format_percentage }}',
    output: '95.5%',
  },
  {
    name: 'format_issues',
    description: 'Format issue list for display',
    example: '{{ issues | format_issues(3) }}',
    output: '- [high] validator: message...',
  },
  {
    name: 'truncate_text',
    description: 'Truncate text to max length',
    example: '{{ message | truncate_text(50) }}',
    output: 'This is a long message that gets...',
  },
  {
    name: 'pluralize',
    description: 'Return singular or plural form',
    example: "{{ issue_count | pluralize('issue') }}",
    output: 'issues',
  },
  {
    name: 'upper',
    description: 'Convert to uppercase',
    example: '{{ severity | upper }}',
    output: 'CRITICAL',
  },
  {
    name: 'lower',
    description: 'Convert to lowercase',
    example: '{{ severity | lower }}',
    output: 'critical',
  },
  {
    name: 'title',
    description: 'Convert to title case',
    example: '{{ severity | title }}',
    output: 'Critical',
  },
  {
    name: 'default',
    description: 'Provide default value if undefined',
    example: "{{ missing_var | default('N/A') }}",
    output: 'N/A',
  },
  {
    name: 'length',
    description: 'Get length of string or list',
    example: '{{ tags | length }}',
    output: '3',
  },
  {
    name: 'join',
    description: 'Join list items with separator',
    example: "{{ tags | join(', ') }}",
    output: 'production, critical, daily',
  },
  {
    name: 'first',
    description: 'Get first item of list',
    example: '{{ tags | first }}',
    output: 'production',
  },
  {
    name: 'last',
    description: 'Get last item of list',
    example: '{{ tags | last }}',
    output: 'daily',
  },
  {
    name: 'round',
    description: 'Round number to decimal places',
    example: '{{ pass_rate | round(2) }}',
    output: '0.95',
  },
  {
    name: 'int',
    description: 'Convert to integer',
    example: '{{ pass_rate * 100 | int }}',
    output: '95',
  },
]

/**
 * Default sample event data for preview.
 */
const DEFAULT_SAMPLE_EVENT = {
  severity: 'critical',
  issue_count: 5,
  status: 'failure',
  pass_rate: 0.85,
  tags: ['production', 'critical', 'daily'],
  data_asset: 'users_production.csv',
  source_name: 'users_production.csv',
  validation_name: 'Daily Data Quality Check',
  has_issues: true,
  is_failure: true,
  metadata: {
    environment: 'production',
    owner: 'data-team',
  },
  event: {
    severity: 'critical',
    issue_count: 5,
    status: 'failure',
    pass_rate: 0.85,
    tags: ['production', 'critical', 'daily'],
    source_name: 'users_production.csv',
    validation_name: 'Daily Data Quality Check',
    metadata: {
      environment: 'production',
      owner: 'data-team',
    },
  },
}

// =============================================================================
// Helper Components
// =============================================================================

interface VariablePanelProps {
  onInsert: (variable: string) => void
}

function VariablePanel({ onInsert }: VariablePanelProps) {
  return (
    <ScrollArea className="h-[300px]">
      <div className="space-y-1 pr-4">
        {CONTEXT_VARIABLES.map((variable) => (
          <button
            key={variable.name}
            type="button"
            onClick={() => onInsert(`{{ ${variable.name} }}`)}
            className={cn(
              'w-full text-left px-2 py-1.5 rounded-md text-sm',
              'hover:bg-muted transition-colors',
              'group flex items-start gap-2'
            )}
          >
            <code className="text-xs font-mono text-primary bg-primary/10 px-1 py-0.5 rounded shrink-0">
              {variable.name}
            </code>
            <div className="flex-1 min-w-0">
              <div className="text-xs text-muted-foreground truncate">
                {variable.description}
              </div>
            </div>
            <Badge variant="outline" className="text-[10px] shrink-0">
              {variable.type}
            </Badge>
          </button>
        ))}
      </div>
    </ScrollArea>
  )
}

interface SnippetPanelProps {
  onInsert: (snippet: string) => void
}

function SnippetPanel({ onInsert }: SnippetPanelProps) {
  const categories = [
    { id: 'expression', label: 'Expressions', icon: Braces },
    { id: 'control', label: 'Control Flow', icon: Code2 },
    { id: 'filter', label: 'Filters', icon: Filter },
    { id: 'comment', label: 'Comments', icon: Info },
  ]

  return (
    <ScrollArea className="h-[300px]">
      <Accordion type="multiple" defaultValue={['expression']} className="pr-4">
        {categories.map((category) => {
          const snippets = TEMPLATE_SNIPPETS.filter((s) => s.category === category.id)
          const Icon = category.icon

          return (
            <AccordionItem key={category.id} value={category.id}>
              <AccordionTrigger className="py-2 text-sm">
                <span className="flex items-center gap-2">
                  <Icon className="h-3.5 w-3.5" />
                  {category.label}
                  <Badge variant="secondary" className="text-[10px] ml-auto mr-2">
                    {snippets.length}
                  </Badge>
                </span>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-1">
                  {snippets.map((snippet) => (
                    <button
                      key={snippet.name}
                      type="button"
                      onClick={() => onInsert(snippet.template)}
                      className={cn(
                        'w-full text-left px-2 py-1.5 rounded-md text-sm',
                        'hover:bg-muted transition-colors'
                      )}
                    >
                      <div className="font-medium text-xs">{snippet.name}</div>
                      <div className="text-xs text-muted-foreground">
                        {snippet.description}
                      </div>
                    </button>
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>
          )
        })}
      </Accordion>
    </ScrollArea>
  )
}

interface FiltersPanelProps {
  onInsert: (filter: string) => void
}

function FiltersPanel({ onInsert }: FiltersPanelProps) {
  return (
    <ScrollArea className="h-[300px]">
      <div className="space-y-2 pr-4">
        {JINJA2_FILTERS.map((filter) => (
          <div
            key={filter.name}
            className="p-2 rounded-md border bg-card hover:bg-muted/50 transition-colors"
          >
            <div className="flex items-center justify-between mb-1">
              <button
                type="button"
                onClick={() => onInsert(filter.example)}
                className="font-mono text-sm text-primary hover:underline"
              >
                {filter.name}
              </button>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6"
                      onClick={() => onInsert(filter.example)}
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Insert example</TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
            <p className="text-xs text-muted-foreground mb-1">
              {filter.description}
            </p>
            <div className="flex items-center gap-2 text-xs font-mono">
              <span className="text-muted-foreground">{filter.example}</span>
              <span className="text-muted-foreground">=</span>
              <span className="text-green-600 dark:text-green-400">{filter.output}</span>
            </div>
          </div>
        ))}
      </div>
    </ScrollArea>
  )
}

// =============================================================================
// Main Component
// =============================================================================

export function Jinja2RuleEditor({
  config,
  onChange,
  onValidate,
  className,
}: Jinja2RuleEditorProps) {
  const content = useIntlayer('notificationsAdvanced')

  // Refs
  const editorRef = useRef<CodeEditorRef>(null)

  // Local state
  const [sampleEventJson, setSampleEventJson] = useState(
    JSON.stringify(DEFAULT_SAMPLE_EVENT, null, 2)
  )
  const [previewOutput, setPreviewOutput] = useState<string>('')
  const [previewError, setPreviewError] = useState<string | null>(null)
  const [isValidating, setIsValidating] = useState(false)
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null)
  const [sidebarTab, setSidebarTab] = useState<'variables' | 'snippets' | 'filters'>('variables')

  // Parse sample event
  const sampleEvent = useMemo(() => {
    try {
      return JSON.parse(sampleEventJson)
    } catch {
      return DEFAULT_SAMPLE_EVENT
    }
  }, [sampleEventJson])

  // Update template
  const handleTemplateChange = useCallback(
    (template: string) => {
      onChange({ ...config, template })
    },
    [config, onChange]
  )

  // Insert text at cursor position
  const handleInsert = useCallback(
    (text: string) => {
      if (editorRef.current) {
        editorRef.current.insertAtCursor(text)
      } else {
        // Fallback: append to end
        const newTemplate = config.template ? `${config.template}${text}` : text
        onChange({ ...config, template: newTemplate })
      }
    },
    [config, onChange]
  )

  // Render preview (client-side simulation)
  const renderPreview = useCallback(() => {
    if (!config.template) {
      setPreviewOutput('')
      setPreviewError(null)
      return
    }

    try {
      // Simple client-side rendering simulation
      // In production, this would call the backend validate-jinja2 endpoint
      let output = config.template

      // Replace simple variable patterns
      output = output.replace(/\{\{\s*(\w+(?:\.\w+)*)\s*\}\}/g, (match, varPath) => {
        const parts = varPath.split('.')
        let value: unknown = sampleEvent
        for (const part of parts) {
          if (value && typeof value === 'object' && part in value) {
            value = (value as Record<string, unknown>)[part]
          } else {
            return match // Keep original if not found
          }
        }
        if (typeof value === 'object') {
          return JSON.stringify(value)
        }
        return String(value)
      })

      // Evaluate simple boolean expressions
      if (output.includes('==') || output.includes('!=') || output.includes('<') || output.includes('>')) {
        // This is a very simplified evaluation - real rendering should use backend
        const booleanMatch = output.match(/^\{\{\s*(.+)\s*\}\}$/)
        if (booleanMatch) {
          try {
            // Create a safe context for evaluation
            const context = { ...sampleEvent }
            const expr = booleanMatch[1]
              .replace(/==/g, '===')
              .replace(/!=/g, '!==')
              .replace(/\band\b/gi, '&&')
              .replace(/\bor\b/gi, '||')
              .replace(/\bnot\b/gi, '!')
              .replace(/\bTrue\b/gi, 'true')
              .replace(/\bFalse\b/gi, 'false')

            // Note: This is unsafe for production - use backend validation
            // eslint-disable-next-line no-new-func
            const result = new Function(...Object.keys(context), `return ${expr}`)(...Object.values(context))
            output = String(result)
          } catch {
            // Keep original on eval error
          }
        }
      }

      setPreviewOutput(output)
      setPreviewError(null)
    } catch (e) {
      setPreviewError(e instanceof Error ? e.message : 'Preview error')
      setPreviewOutput('')
    }
  }, [config.template, sampleEvent])

  // Auto-render preview on template or sample data change
  useEffect(() => {
    renderPreview()
  }, [renderPreview])

  // Validate template via API
  const handleValidate = useCallback(async () => {
    if (!onValidate || !config.template) return

    setIsValidating(true)
    try {
      const result = await onValidate(config.template)
      setValidationResult(result)
      if (result.rendered_output) {
        setPreviewOutput(result.rendered_output)
      }
      if (result.error) {
        setPreviewError(result.error)
      }
    } catch (e) {
      setValidationResult({
        valid: false,
        error: e instanceof Error ? e.message : 'Validation failed',
      })
    } finally {
      setIsValidating(false)
    }
  }, [config.template, onValidate])

  // Reset sample data
  const handleResetSampleData = useCallback(() => {
    setSampleEventJson(JSON.stringify(DEFAULT_SAMPLE_EVENT, null, 2))
  }, [])

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          <span className="font-medium">
            {str(content.jinja2Editor?.title) || 'Jinja2 Template Editor'}
          </span>
        </div>
        {onValidate && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleValidate}
            disabled={isValidating || !config.template}
          >
            {isValidating ? (
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Play className="h-4 w-4 mr-2" />
            )}
            {str(content.jinja2Editor?.validate) || 'Validate'}
          </Button>
        )}
      </div>

      {/* Main editor area - two columns */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left column: Editor + Preview */}
        <div className="lg:col-span-2 space-y-4">
          {/* Template Editor */}
          <Card>
            <CardHeader className="py-3 px-4">
              <CardTitle className="text-sm flex items-center gap-2">
                <Code2 className="h-4 w-4" />
                {str(content.jinja2Editor?.templateEditor) || 'Template'}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <CodeEditor
                ref={editorRef}
                value={config.template}
                onChange={handleTemplateChange}
                language="jinja2"
                placeholder={str(content.jinja2Editor?.templatePlaceholder) || "Enter Jinja2 template (e.g., {{ severity == 'critical' }})"}
                minLines={8}
                maxLines={15}
                errorLines={validationResult?.error_line ? [validationResult.error_line] : []}
              />
              {validationResult?.valid === false && validationResult.error && (
                <div className="px-4 py-2 text-sm text-destructive bg-destructive/10 border-t">
                  {validationResult.error}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Preview Panel */}
          <Card>
            <CardHeader className="py-3 px-4">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm flex items-center gap-2">
                  <BookOpen className="h-4 w-4" />
                  {str(content.jinja2Editor?.preview) || 'Preview'}
                </CardTitle>
                {validationResult && (
                  <Badge
                    variant={validationResult.valid ? 'default' : 'destructive'}
                    className="text-xs"
                  >
                    {validationResult.valid ? (
                      <>
                        <Check className="h-3 w-3 mr-1" />
                        {str(content.jinja2Editor?.valid) || 'Valid'}
                      </>
                    ) : (
                      <>
                        <AlertTriangle className="h-3 w-3 mr-1" />
                        {str(content.jinja2Editor?.invalid) || 'Invalid'}
                      </>
                    )}
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent className="py-3 px-4">
              <div className="grid grid-cols-2 gap-4">
                {/* Preview Output */}
                <div>
                  <Label className="text-xs text-muted-foreground mb-2 block">
                    {str(content.jinja2Editor?.output) || 'Output'}
                  </Label>
                  <div
                    className={cn(
                      'p-3 rounded-md border min-h-[60px] font-mono text-sm',
                      previewError
                        ? 'bg-destructive/10 border-destructive text-destructive'
                        : 'bg-muted/50'
                    )}
                  >
                    {previewError ? (
                      <span className="flex items-center gap-2">
                        <AlertTriangle className="h-4 w-4" />
                        {previewError}
                      </span>
                    ) : previewOutput ? (
                      <span
                        className={cn(
                          previewOutput === 'true' || previewOutput === 'True'
                            ? 'text-green-600 dark:text-green-400'
                            : previewOutput === 'false' || previewOutput === 'False'
                            ? 'text-red-600 dark:text-red-400'
                            : ''
                        )}
                      >
                        {previewOutput}
                      </span>
                    ) : (
                      <span className="text-muted-foreground italic">
                        {str(content.jinja2Editor?.noOutput) || 'No output'}
                      </span>
                    )}
                  </div>
                </div>

                {/* Expected Result */}
                <div>
                  <Label className="text-xs text-muted-foreground mb-2 block">
                    {str(content.jinja2Editor?.expectedResult) || 'Expected Result'}
                  </Label>
                  <select
                    value={config.expected_result || 'true'}
                    onChange={(e) =>
                      onChange({ ...config, expected_result: e.target.value })
                    }
                    className={cn(
                      'w-full h-9 rounded-md border border-input bg-background px-3 py-1',
                      'text-sm focus:outline-none focus:ring-2 focus:ring-ring'
                    )}
                  >
                    <option value="true">true (match when True)</option>
                    <option value="false">false (match when False)</option>
                  </select>
                  <p className="text-xs text-muted-foreground mt-1">
                    {str(content.jinja2Editor?.expectedResultHint) ||
                      'The template output is compared against this value'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Sample Event Data */}
          <Collapsible>
            <Card>
              <CollapsibleTrigger asChild>
                <CardHeader className="py-3 px-4 cursor-pointer hover:bg-muted/50 transition-colors">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Braces className="h-4 w-4" />
                      {str(content.jinja2Editor?.sampleData) || 'Sample Event Data'}
                    </CardTitle>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleResetSampleData()
                        }}
                      >
                        <RefreshCw className="h-3 w-3 mr-1" />
                        Reset
                      </Button>
                      <ChevronDown className="h-4 w-4 text-muted-foreground" />
                    </div>
                  </div>
                </CardHeader>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <CardContent className="p-0 border-t">
                  <CodeEditor
                    value={sampleEventJson}
                    onChange={setSampleEventJson}
                    language="json"
                    placeholder="Enter sample event JSON..."
                    minLines={10}
                    maxLines={20}
                    wordWrap
                  />
                </CardContent>
              </CollapsibleContent>
            </Card>
          </Collapsible>
        </div>

        {/* Right column: Sidebar with tabs */}
        <div className="lg:col-span-1">
          <Card className="sticky top-4">
            <Tabs value={sidebarTab} onValueChange={(v) => setSidebarTab(v as typeof sidebarTab)}>
              <CardHeader className="py-2 px-4 border-b">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="variables" className="text-xs">
                    <Variable className="h-3 w-3 mr-1" />
                    {str(content.jinja2Editor?.variables) || 'Variables'}
                  </TabsTrigger>
                  <TabsTrigger value="snippets" className="text-xs">
                    <Code2 className="h-3 w-3 mr-1" />
                    {str(content.jinja2Editor?.snippets) || 'Snippets'}
                  </TabsTrigger>
                  <TabsTrigger value="filters" className="text-xs">
                    <Filter className="h-3 w-3 mr-1" />
                    {str(content.jinja2Editor?.filters) || 'Filters'}
                  </TabsTrigger>
                </TabsList>
              </CardHeader>
              <CardContent className="p-2">
                <TabsContent value="variables" className="mt-0">
                  <VariablePanel onInsert={handleInsert} />
                </TabsContent>
                <TabsContent value="snippets" className="mt-0">
                  <SnippetPanel onInsert={handleInsert} />
                </TabsContent>
                <TabsContent value="filters" className="mt-0">
                  <FiltersPanel onInsert={handleInsert} />
                </TabsContent>
              </CardContent>
            </Tabs>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default Jinja2RuleEditor
