/**
 * AddSourceDialog - Multi-step dialog for creating data sources
 *
 * Steps:
 * 1. Select source type
 * 2. Configure connection
 * 3. Test connection (optional)
 */

import { useState, useEffect, useCallback, useMemo } from 'react'
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Loader2,
  RefreshCw,
  ExternalLink,
  AlertCircle,
  CheckCircle,
} from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'
import {
  getSupportedSourceTypes,
  createSource,
  testConnectionConfig,
  type SourceTypeDefinition,
  type SourceCategoryDefinition,
  type SourceType,
  type SourceCategory,
} from '@/api/client'
import { SourceTypeSelector } from './SourceTypeSelector'
import { DynamicSourceForm } from './DynamicSourceForm'
import { useToast } from '@/hooks/use-toast'

interface AddSourceDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess?: () => void
}

type Step = 'type' | 'config' | 'test'

interface FormState {
  name: string
  description: string
  type: SourceType | null
  config: Record<string, unknown>
}

const initialFormState: FormState = {
  name: '',
  description: '',
  type: null,
  config: {},
}

export function AddSourceDialog({ open, onOpenChange, onSuccess }: AddSourceDialogProps) {
  const { toast } = useToast()

  // Source types data
  const [sourceTypes, setSourceTypes] = useState<SourceTypeDefinition[]>([])
  const [categories, setCategories] = useState<SourceCategoryDefinition[]>([])
  const [loadingTypes, setLoadingTypes] = useState(true)

  // Form state
  const [step, setStep] = useState<Step>('type')
  const [form, setForm] = useState<FormState>(initialFormState)
  const [errors, setErrors] = useState<Record<string, string>>({})

  // Test connection state
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{
    success: boolean
    message?: string
    error?: string
  } | null>(null)

  // Creating state
  const [creating, setCreating] = useState(false)

  // Category filter for type selection
  const [categoryFilter, setCategoryFilter] = useState<SourceCategory | null>(null)

  // Load source types on mount
  useEffect(() => {
    if (open && sourceTypes.length === 0) {
      loadSourceTypes()
    }
  }, [open, sourceTypes.length])

  // Reset form when dialog opens/closes
  useEffect(() => {
    if (!open) {
      // Reset after dialog closes with animation
      setTimeout(() => {
        setStep('type')
        setForm(initialFormState)
        setErrors({})
        setTestResult(null)
        setCategoryFilter(null)
      }, 200)
    }
  }, [open])

  const loadSourceTypes = async () => {
    setLoadingTypes(true)
    try {
      const response = await getSupportedSourceTypes()
      if (response.success) {
        setSourceTypes(response.data.types)
        setCategories(response.data.categories)
      }
    } catch (error) {
      console.error('Failed to load source types:', error)
      toast({
        title: 'Error',
        description: 'Failed to load source types',
        variant: 'destructive',
      })
    } finally {
      setLoadingTypes(false)
    }
  }

  // Get selected source type definition
  const selectedSourceType = useMemo(
    () => sourceTypes.find((t) => t.type === form.type) || null,
    [sourceTypes, form.type]
  )

  // Handle type selection
  const handleTypeSelect = useCallback((type: string) => {
    setForm((prev) => ({
      ...prev,
      type: type as SourceType,
      config: {}, // Reset config when type changes
    }))
    setErrors({})
    setTestResult(null)
  }, [])

  // Handle config change
  const handleConfigChange = useCallback((config: Record<string, unknown>) => {
    setForm((prev) => ({ ...prev, config }))
    setTestResult(null) // Reset test when config changes
  }, [])

  // Validate current step
  const validateStep = useCallback((): boolean => {
    const newErrors: Record<string, string> = {}

    if (step === 'type') {
      if (!form.type) {
        toast({
          title: 'Validation Error',
          description: 'Please select a source type',
          variant: 'destructive',
        })
        return false
      }
    }

    if (step === 'config') {
      // Validate name
      if (!form.name.trim()) {
        newErrors.name = 'Name is required'
      }

      // Validate required fields for the source type
      if (selectedSourceType) {
        for (const field of selectedSourceType.fields) {
          if (field.required) {
            const value = form.config[field.name]
            if (value === undefined || value === null || value === '') {
              newErrors[field.name] = `${field.label} is required`
            }
          }
        }
      }
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }, [step, form, selectedSourceType, toast])

  // Navigate to next step
  const handleNext = useCallback(() => {
    if (!validateStep()) return

    if (step === 'type') {
      setStep('config')
    } else if (step === 'config') {
      setStep('test')
    }
  }, [step, validateStep])

  // Navigate to previous step
  const handleBack = useCallback(() => {
    if (step === 'config') {
      setStep('type')
    } else if (step === 'test') {
      setStep('config')
    }
  }, [step])

  // Test connection
  const handleTestConnection = useCallback(async () => {
    if (!form.type) return

    setTesting(true)
    setTestResult(null)

    try {
      const response = await testConnectionConfig(form.type, form.config)
      setTestResult(response.data)
    } catch (error) {
      setTestResult({
        success: false,
        error: error instanceof Error ? error.message : 'Connection test failed',
      })
    } finally {
      setTesting(false)
    }
  }, [form.type, form.config])

  // Create source
  const handleCreate = useCallback(async () => {
    if (!validateStep() || !form.type) return

    setCreating(true)
    try {
      await createSource({
        name: form.name.trim(),
        type: form.type,
        config: form.config,
        description: form.description.trim() || undefined,
      })

      toast({
        title: 'Source Created',
        description: `Successfully created "${form.name}"`,
      })

      onOpenChange(false)
      onSuccess?.()
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to create source',
        variant: 'destructive',
      })
    } finally {
      setCreating(false)
    }
  }, [form, validateStep, toast, onOpenChange, onSuccess])

  // Step indicator
  const steps: { key: Step; label: string }[] = [
    { key: 'type', label: 'Select Type' },
    { key: 'config', label: 'Configure' },
    { key: 'test', label: 'Test & Create' },
  ]

  const currentStepIndex = steps.findIndex((s) => s.key === step)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] max-w-3xl overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>Add Data Source</DialogTitle>
          <DialogDescription>
            Connect to a new data source for validation and monitoring.
          </DialogDescription>
        </DialogHeader>

        {/* Step indicator */}
        <div className="flex items-center justify-center gap-2 py-4">
          {steps.map((s, index) => (
            <div key={s.key} className="flex items-center">
              <div
                className={cn(
                  'flex h-8 w-8 items-center justify-center rounded-full border-2 text-sm font-medium transition-colors',
                  index < currentStepIndex
                    ? 'border-primary bg-primary text-primary-foreground'
                    : index === currentStepIndex
                      ? 'border-primary text-primary'
                      : 'border-muted text-muted-foreground'
                )}
              >
                {index < currentStepIndex ? (
                  <Check className="h-4 w-4" />
                ) : (
                  index + 1
                )}
              </div>
              <span
                className={cn(
                  'ml-2 text-sm',
                  index === currentStepIndex ? 'font-medium' : 'text-muted-foreground'
                )}
              >
                {s.label}
              </span>
              {index < steps.length - 1 && (
                <div
                  className={cn(
                    'mx-4 h-0.5 w-8',
                    index < currentStepIndex ? 'bg-primary' : 'bg-muted'
                  )}
                />
              )}
            </div>
          ))}
        </div>

        {/* Content area with scroll */}
        <div className="flex-1 overflow-y-auto px-1">
          {/* Step 1: Type Selection */}
          {step === 'type' && (
            <div className="space-y-4">
              {/* Category tabs */}
              <Tabs
                value={categoryFilter || 'all'}
                onValueChange={(v) => setCategoryFilter(v === 'all' ? null : (v as SourceCategory))}
              >
                <TabsList className="grid w-full grid-cols-5">
                  <TabsTrigger value="all">All</TabsTrigger>
                  {categories.map((cat) => (
                    <TabsTrigger key={cat.value} value={cat.value}>
                      {cat.label}
                    </TabsTrigger>
                  ))}
                </TabsList>
              </Tabs>

              {loadingTypes ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : (
                <SourceTypeSelector
                  sourceTypes={sourceTypes}
                  selectedType={form.type}
                  onSelect={handleTypeSelect}
                  categoryFilter={categoryFilter}
                />
              )}
            </div>
          )}

          {/* Step 2: Configuration */}
          {step === 'config' && selectedSourceType && (
            <div className="space-y-6">
              {/* Source name and description */}
              <div className="space-y-4 rounded-lg border bg-muted/30 p-4">
                <div className="flex items-center gap-2">
                  <Badge variant="outline">{selectedSourceType.name}</Badge>
                  {selectedSourceType.docs_url && (
                    <a
                      href={selectedSourceType.docs_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
                    >
                      <ExternalLink className="h-3 w-3" />
                      Docs
                    </a>
                  )}
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="source-name" className={cn(errors.name && 'text-destructive')}>
                      Source Name <span className="text-destructive">*</span>
                    </Label>
                    <Input
                      id="source-name"
                      placeholder="e.g., Production Database"
                      value={form.name}
                      onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
                      className={cn(errors.name && 'border-destructive')}
                    />
                    {errors.name && <p className="text-xs text-destructive">{errors.name}</p>}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="source-description">Description</Label>
                    <Input
                      id="source-description"
                      placeholder="Optional description"
                      value={form.description}
                      onChange={(e) => setForm((prev) => ({ ...prev, description: e.target.value }))}
                    />
                  </div>
                </div>
              </div>

              {/* Dynamic connection form */}
              <DynamicSourceForm
                sourceType={selectedSourceType}
                values={form.config}
                onChange={handleConfigChange}
                errors={errors}
              />
            </div>
          )}

          {/* Step 3: Test & Create */}
          {step === 'test' && selectedSourceType && (
            <div className="space-y-6">
              {/* Summary */}
              <div className="space-y-3 rounded-lg border bg-muted/30 p-4">
                <h4 className="font-medium">Connection Summary</h4>
                <div className="grid gap-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Name</span>
                    <span className="font-medium">{form.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Type</span>
                    <Badge variant="outline">{selectedSourceType.name}</Badge>
                  </div>
                  {form.description && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Description</span>
                      <span className="max-w-[200px] truncate">{form.description}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Test connection */}
              <div className="space-y-4 rounded-lg border p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">Test Connection</h4>
                    <p className="text-sm text-muted-foreground">
                      Verify the connection before creating the source.
                    </p>
                  </div>
                  <Button
                    variant="outline"
                    onClick={handleTestConnection}
                    disabled={testing}
                  >
                    {testing ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <RefreshCw className="mr-2 h-4 w-4" />
                    )}
                    {testing ? 'Testing...' : 'Test Connection'}
                  </Button>
                </div>

                {/* Test result */}
                {testResult && (
                  <div
                    className={cn(
                      'flex items-start gap-3 rounded-lg p-3',
                      testResult.success
                        ? 'bg-green-500/10 text-green-700 dark:text-green-400'
                        : 'bg-destructive/10 text-destructive'
                    )}
                  >
                    {testResult.success ? (
                      <CheckCircle className="mt-0.5 h-5 w-5 flex-shrink-0" />
                    ) : (
                      <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0" />
                    )}
                    <div className="text-sm">
                      {testResult.success ? (
                        <span>{testResult.message || 'Connection successful!'}</span>
                      ) : (
                        <span>{testResult.error || 'Connection failed'}</span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer navigation */}
        <DialogFooter className="flex items-center justify-between border-t pt-4">
          <div>
            {step !== 'type' && (
              <Button variant="ghost" onClick={handleBack} disabled={creating}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back
              </Button>
            )}
          </div>

          <div className="flex gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)} disabled={creating}>
              Cancel
            </Button>

            {step === 'test' ? (
              <Button onClick={handleCreate} disabled={creating}>
                {creating ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Check className="mr-2 h-4 w-4" />
                )}
                {creating ? 'Creating...' : 'Create Source'}
              </Button>
            ) : (
              <Button onClick={handleNext} disabled={!form.type && step === 'type'}>
                Next
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
