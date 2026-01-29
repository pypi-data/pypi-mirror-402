/**
 * EditSourceDialog - Dialog for editing existing data sources
 *
 * Features:
 * - Load existing source configuration
 * - Edit connection settings
 * - Test connection before saving
 * - Mask sensitive fields (passwords, tokens)
 */

import { useState, useEffect, useCallback, useMemo } from 'react'
import {
  Check,
  Loader2,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Shield,
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'
import {
  getSupportedSourceTypes,
  updateSource,
  testSourceConnection,
  type SourceTypeDefinition,
  type Source,
} from '@/api/client'
import { DynamicSourceForm } from './DynamicSourceForm'
import { useToast } from '@/hooks/use-toast'
import { useIntlayer } from '@/providers'
import { str } from '@/lib/intlayer-utils'

interface EditSourceDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  source: Source | null
  onSuccess?: () => void
}

// Fields that should be masked by default
const SENSITIVE_FIELDS = ['password', 'token', 'secret', 'api_key', 'credentials', 'private_key']

// Check if a field is sensitive
function isSensitiveField(fieldName: string): boolean {
  const lowerName = fieldName.toLowerCase()
  return SENSITIVE_FIELDS.some((sf) => lowerName.includes(sf))
}

export function EditSourceDialog({
  open,
  onOpenChange,
  source,
  onSuccess,
}: EditSourceDialogProps) {
  const { toast } = useToast()
  const sources_t = useIntlayer('sources')
  const common = useIntlayer('common')

  // Source types data
  const [sourceTypes, setSourceTypes] = useState<SourceTypeDefinition[]>([])
  const [loadingTypes, setLoadingTypes] = useState(true)

  // Form state
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [config, setConfig] = useState<Record<string, unknown>>({})
  const [errors, setErrors] = useState<Record<string, string>>({})

  // Track which sensitive fields have been modified
  const [modifiedSensitiveFields, setModifiedSensitiveFields] = useState<Set<string>>(new Set())

  // Active tab
  const [activeTab, setActiveTab] = useState<'general' | 'connection'>('general')

  // Test connection state
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{
    success: boolean
    message?: string
    error?: string
  } | null>(null)

  // Saving state
  const [saving, setSaving] = useState(false)

  // Load source types on mount
  useEffect(() => {
    if (open && sourceTypes.length === 0) {
      loadSourceTypes()
    }
  }, [open, sourceTypes.length])

  // Initialize form when source changes
  useEffect(() => {
    if (source && open) {
      setName(source.name)
      setDescription(source.description || '')
      // Deep copy config to avoid mutation
      setConfig(JSON.parse(JSON.stringify(source.config || {})))
      setErrors({})
      setModifiedSensitiveFields(new Set())
      setTestResult(null)
      setActiveTab('general')
    }
  }, [source, open])

  // Reset form when dialog closes
  useEffect(() => {
    if (!open) {
      setTimeout(() => {
        setErrors({})
        setTestResult(null)
        setModifiedSensitiveFields(new Set())
      }, 200)
    }
  }, [open])

  const loadSourceTypes = async () => {
    setLoadingTypes(true)
    try {
      const response = await getSupportedSourceTypes()
      if (response.success) {
        setSourceTypes(response.data.types)
      }
    } catch (error) {
      console.error('Failed to load source types:', error)
      toast({
        title: str(common.error),
        description: str(sources_t.loadTypesError),
        variant: 'destructive',
      })
    } finally {
      setLoadingTypes(false)
    }
  }

  // Get selected source type definition
  const selectedSourceType = useMemo(
    () => sourceTypes.find((t) => t.type === source?.type) || null,
    [sourceTypes, source?.type]
  )

  // Get list of sensitive fields for current source type
  const sensitiveFieldNames = useMemo(() => {
    if (!selectedSourceType) return []
    return selectedSourceType.fields
      .filter((f) => f.type === 'password' || isSensitiveField(f.name))
      .map((f) => f.name)
  }, [selectedSourceType])

  // Handle config change with sensitive field tracking
  const handleConfigChange = useCallback(
    (newConfig: Record<string, unknown>) => {
      // Track which sensitive fields have been modified
      for (const fieldName of sensitiveFieldNames) {
        const oldValue = config[fieldName]
        const newValue = newConfig[fieldName]
        if (oldValue !== newValue && newValue !== undefined && newValue !== '') {
          setModifiedSensitiveFields((prev) => new Set(prev).add(fieldName))
        }
      }
      setConfig(newConfig)
      setTestResult(null) // Reset test when config changes
    },
    [config, sensitiveFieldNames]
  )

  // Validate form
  const validateForm = useCallback((): boolean => {
    const newErrors: Record<string, string> = {}

    if (!name.trim()) {
      newErrors.name = str(sources_t.nameRequired)
    }

    // Validate required fields for the source type
    if (selectedSourceType) {
      for (const field of selectedSourceType.fields) {
        if (field.required) {
          const value = config[field.name]
          // For sensitive fields, only require if it was never set or explicitly cleared
          if (isSensitiveField(field.name) || field.type === 'password') {
            const originalValue = source?.config?.[field.name]
            const wasModified = modifiedSensitiveFields.has(field.name)
            // If not modified and original exists, it's fine
            if (!wasModified && originalValue) continue
            // If modified to empty, that's an error
            if (wasModified && (value === undefined || value === null || value === '')) {
              newErrors[field.name] = `${field.label} ${str(sources_t.fieldRequired)}`
            }
          } else {
            // Regular field validation
            if (value === undefined || value === null || value === '') {
              newErrors[field.name] = `${field.label} ${str(sources_t.fieldRequired)}`
            }
          }
        }
      }
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }, [name, config, selectedSourceType, source, modifiedSensitiveFields, sources_t])

  // Test connection
  const handleTestConnection = useCallback(async () => {
    if (!source) return

    setTesting(true)
    setTestResult(null)

    try {
      const response = await testSourceConnection(source.id)
      setTestResult(response.data)
    } catch (error) {
      setTestResult({
        success: false,
        error: error instanceof Error ? error.message : str(sources_t.testConnection.failed),
      })
    } finally {
      setTesting(false)
    }
  }, [source, sources_t])

  // Save changes
  const handleSave = useCallback(async () => {
    if (!validateForm() || !source) return

    setSaving(true)
    try {
      // Build update payload - only include modified sensitive fields
      const configToSave: Record<string, unknown> = {}

      for (const [key, value] of Object.entries(config)) {
        // For sensitive fields, only include if modified
        if (isSensitiveField(key) || selectedSourceType?.fields.find(f => f.name === key)?.type === 'password') {
          if (modifiedSensitiveFields.has(key)) {
            configToSave[key] = value
          }
          // If not modified, don't include (keep original server value)
        } else {
          configToSave[key] = value
        }
      }

      await updateSource(source.id, {
        name: name.trim(),
        description: description.trim() || undefined,
        config: configToSave,
      })

      toast({
        title: str(common.success),
        description: str(sources_t.edit.updateSuccess),
      })

      onOpenChange(false)
      onSuccess?.()
    } catch (error) {
      toast({
        title: str(common.error),
        description: error instanceof Error ? error.message : str(sources_t.edit.updateFailed),
        variant: 'destructive',
      })
    } finally {
      setSaving(false)
    }
  }, [
    validateForm,
    source,
    name,
    description,
    config,
    modifiedSensitiveFields,
    selectedSourceType,
    toast,
    common,
    sources_t,
    onOpenChange,
    onSuccess,
  ])

  if (!source) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] max-w-2xl overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {str(sources_t.editSource)}
            <Badge variant="outline">{source.type}</Badge>
          </DialogTitle>
          <DialogDescription>
            {str(sources_t.edit.description)}
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'general' | 'connection')} className="flex-1 overflow-hidden flex flex-col">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="general">{str(sources_t.edit.generalTab)}</TabsTrigger>
            <TabsTrigger value="connection">{str(sources_t.edit.connectionTab)}</TabsTrigger>
          </TabsList>

          <div className="flex-1 overflow-y-auto px-1 py-4">
            {/* General Settings Tab */}
            <TabsContent value="general" className="m-0 space-y-4">
              <div className="space-y-4 rounded-lg border bg-muted/30 p-4">
                <div className="space-y-2">
                  <Label htmlFor="edit-source-name" className={cn(errors.name && 'text-destructive')}>
                    {str(sources_t.dialog.sourceName)} <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="edit-source-name"
                    placeholder={str(sources_t.dialog.sourceNamePlaceholder)}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className={cn(errors.name && 'border-destructive')}
                  />
                  {errors.name && <p className="text-xs text-destructive">{errors.name}</p>}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="edit-source-description">{str(sources_t.dialog.sourceDescription)}</Label>
                  <Input
                    id="edit-source-description"
                    placeholder={str(sources_t.dialog.sourceDescriptionPlaceholder)}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                  />
                </div>
              </div>

              {/* Source Info */}
              <div className="space-y-3 rounded-lg border p-4">
                <h4 className="text-sm font-medium text-muted-foreground">{str(sources_t.edit.sourceInfo)}</h4>
                <div className="grid gap-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">ID</span>
                    <code className="text-xs bg-muted px-2 py-1 rounded">{source.id}</code>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">{str(sources_t.sourceType)}</span>
                    <Badge variant="outline">{selectedSourceType?.name || source.type}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">{str(sources_t.edit.createdAt)}</span>
                    <span>{new Date(source.created_at).toLocaleString()}</span>
                  </div>
                  {source.last_validated_at && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">{str(sources_t.lastValidated)}</span>
                      <span>{new Date(source.last_validated_at).toLocaleString()}</span>
                    </div>
                  )}
                </div>
              </div>
            </TabsContent>

            {/* Connection Settings Tab */}
            <TabsContent value="connection" className="m-0 space-y-4">
              {loadingTypes ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : selectedSourceType ? (
                <>
                  {/* Sensitive fields notice */}
                  {sensitiveFieldNames.length > 0 && (
                    <div className="flex items-start gap-3 rounded-lg bg-amber-500/10 p-3 text-amber-700 dark:text-amber-400">
                      <Shield className="mt-0.5 h-5 w-5 flex-shrink-0" />
                      <div className="text-sm">
                        <p className="font-medium">{str(sources_t.edit.sensitiveFieldsNotice)}</p>
                        <p className="mt-1 text-amber-600 dark:text-amber-500">
                          {str(sources_t.edit.sensitiveFieldsHint)}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Dynamic form */}
                  <DynamicSourceForm
                    sourceType={selectedSourceType}
                    values={config}
                    onChange={handleConfigChange}
                    errors={errors}
                  />

                  {/* Connection test section */}
                  <div className="space-y-4 rounded-lg border p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium">{str(sources_t.testConnection.title)}</h4>
                        <p className="text-sm text-muted-foreground">
                          {str(sources_t.edit.testConnectionHint)}
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
                        {testing ? str(sources_t.testConnection.testing) : str(sources_t.testConnection.test)}
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
                            <span>{testResult.message || str(sources_t.testConnection.success)}</span>
                          ) : (
                            <span>{testResult.error || str(sources_t.testConnection.failed)}</span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  {str(sources_t.edit.unsupportedType)}
                </div>
              )}
            </TabsContent>
          </div>
        </Tabs>

        {/* Footer */}
        <DialogFooter className="flex items-center justify-between border-t pt-4">
          <div className="text-xs text-muted-foreground">
            {modifiedSensitiveFields.size > 0 && (
              <span className="text-amber-600">
                {str(sources_t.edit.sensitiveFieldsModified).replace('{count}', String(modifiedSensitiveFields.size))}
              </span>
            )}
          </div>

          <div className="flex gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)} disabled={saving}>
              {str(common.cancel)}
            </Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Check className="mr-2 h-4 w-4" />
              )}
              {saving ? str(sources_t.edit.saving) : str(common.save)}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
