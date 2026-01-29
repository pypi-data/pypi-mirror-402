/**
 * ValidatorEditorDialog - Dialog for creating/editing custom validators
 *
 * Features:
 * - Code editor with Python syntax highlighting
 * - Parameter definition form
 * - Metadata form (name, description, category, etc.)
 * - Test panel for validating code
 * - Template insertion
 */

import { useState, useCallback, useEffect } from 'react'
import { useIntlayer } from 'react-intlayer'
import { str } from '@/lib/intlayer-utils'
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
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import { toast } from '@/hooks/use-toast'
import { CodeEditor } from '@/components/common'
import { ValidatorParamForm } from './ValidatorParamForm'
import { ValidatorTestPanel } from './ValidatorTestPanel'
import {
  Save,
  Loader2,
  FileCode,
  Settings,
  TestTube,
  Wand2,
  X,
} from 'lucide-react'
import {
  getValidatorTemplate,
  createCustomValidator,
  updateCustomValidator,
  testCustomValidator,
} from '@/api/client'
import type {
  CustomValidator,
  ValidatorEditorDialogProps,
  ValidatorFormState,
  ValidatorCategory,
  ValidatorSeverity,
  DEFAULT_VALIDATOR_FORM,
} from './types'

const VALIDATOR_CATEGORIES: ValidatorCategory[] = [
  'schema',
  'completeness',
  'uniqueness',
  'distribution',
  'string',
  'datetime',
  'custom',
]

const SEVERITIES: ValidatorSeverity[] = ['error', 'warning', 'info']

/**
 * Slugify a string for use as a validator name
 */
function slugify(str: string): string {
  return str
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_|_$/g, '')
}

/**
 * Dialog for creating/editing custom validators
 */
export function ValidatorEditorDialog({
  open,
  onOpenChange,
  onSuccess,
  validator,
  columns = [],
}: ValidatorEditorDialogProps) {
  const t = useIntlayer('plugins')
  const isEditing = !!validator

  // Form state
  const [form, setForm] = useState<ValidatorFormState>({
    name: '',
    display_name: '',
    description: '',
    category: 'custom',
    severity: 'warning',
    tags: [],
    parameters: [],
    code: '',
    test_cases: [],
    is_enabled: true,
  })
  const [tagInput, setTagInput] = useState('')
  const [activeTab, setActiveTab] = useState('code')
  const [isSaving, setIsSaving] = useState(false)
  const [isLoadingTemplate, setIsLoadingTemplate] = useState(false)

  // Initialize form with validator data or defaults
  useEffect(() => {
    if (open) {
      if (validator) {
        setForm({
          name: validator.name,
          display_name: validator.display_name,
          description: validator.description,
          category: (validator.category as ValidatorCategory) || 'custom',
          severity: (validator.severity as ValidatorSeverity) || 'warning',
          tags: validator.tags || [],
          parameters: validator.parameters || [],
          code: validator.code || '',
          test_cases: validator.test_cases || [],
          is_enabled: validator.is_enabled,
        })
      } else {
        // Load template for new validators
        handleLoadTemplate()
      }
    }
  }, [open, validator])

  // Load template
  const handleLoadTemplate = useCallback(async () => {
    setIsLoadingTemplate(true)
    try {
      const result = await getValidatorTemplate()
      setForm((prev) => ({
        ...prev,
        code: result.template,
      }))
    } catch {
      // Fallback template
      setForm((prev) => ({
        ...prev,
        code: `def validate(column_name, values, params, schema, row_count):
    """Custom validator function.

    Args:
        column_name: Name of the column being validated.
        values: List of values in the column.
        params: Dictionary of parameter values.
        schema: Column schema information.
        row_count: Total number of rows.

    Returns:
        Dictionary with:
            - passed: bool - Whether validation passed
            - issues: list - List of issue dictionaries
            - message: str - Summary message
            - details: dict - Additional details
    """
    issues = []

    # Your validation logic here

    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "message": f"Validated {len(values)} values",
        "details": {}
    }`,
      }))
    } finally {
      setIsLoadingTemplate(false)
    }
  }, [])

  // Handle form field change
  const handleChange = useCallback(<K extends keyof ValidatorFormState>(
    field: K,
    value: ValidatorFormState[K]
  ) => {
    setForm((prev) => {
      const newForm = { ...prev, [field]: value }
      // Auto-generate name from display_name
      if (field === 'display_name' && !isEditing) {
        newForm.name = slugify(value as string) + '_validator'
      }
      return newForm
    })
  }, [isEditing])

  // Handle tag addition
  const handleAddTag = useCallback(() => {
    const tag = tagInput.trim()
    if (tag && !form.tags.includes(tag)) {
      setForm((prev) => ({ ...prev, tags: [...prev.tags, tag] }))
      setTagInput('')
    }
  }, [tagInput, form.tags])

  // Handle tag removal
  const handleRemoveTag = useCallback((tag: string) => {
    setForm((prev) => ({ ...prev, tags: prev.tags.filter((t) => t !== tag) }))
  }, [])

  // Handle test
  const handleTest = useCallback(
    async (data: {
      test_data: Record<string, unknown>
      param_values: Record<string, unknown>
    }) => {
      const result = await testCustomValidator({
        code: form.code,
        parameters: form.parameters,
        test_data: data.test_data,
        param_values: data.param_values,
      })
      return result
    },
    [form.code, form.parameters]
  )

  // Handle save
  const handleSave = useCallback(async () => {
    // Validation
    if (!form.name.trim()) {
      toast({ title: str(t.editor.validationError), description: str(t.editor.nameRequired), variant: 'destructive' })
      return
    }
    if (!form.display_name.trim()) {
      toast({ title: str(t.editor.validationError), description: str(t.editor.displayNameRequired), variant: 'destructive' })
      return
    }
    if (!form.code.trim()) {
      toast({ title: str(t.editor.validationError), description: str(t.editor.codeRequired), variant: 'destructive' })
      return
    }

    setIsSaving(true)
    try {
      const data = {
        name: form.name,
        display_name: form.display_name,
        description: form.description,
        category: form.category,
        severity: form.severity,
        tags: form.tags,
        parameters: form.parameters,
        code: form.code,
        test_cases: form.test_cases,
        is_enabled: form.is_enabled,
      }

      if (isEditing && validator) {
        await updateCustomValidator(validator.id, data)
        toast({ title: str(t.messages.validatorUpdated) })
      } else {
        await createCustomValidator(data)
        toast({ title: str(t.messages.validatorCreated) })
      }

      onSuccess?.()
      onOpenChange(false)
    } catch (err) {
      toast({
        title: isEditing ? str(t.messages.validatorUpdateFailed) : str(t.messages.validatorCreateFailed),
        description: err instanceof Error ? err.message : 'Unknown error',
        variant: 'destructive',
      })
    } finally {
      setIsSaving(false)
    }
  }, [form, isEditing, validator, onSuccess, onOpenChange, t])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] flex flex-col p-0">
        <DialogHeader className="px-6 pt-6">
          <DialogTitle>
            {isEditing ? str(t.editor.editValidator) : str(t.editor.createValidator)}
          </DialogTitle>
          <DialogDescription>
            {isEditing
              ? str(t.editor.editValidatorDescription)
              : str(t.editor.createValidatorDescription)}
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col overflow-hidden">
          <div className="px-6">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="code" className="gap-2">
                <FileCode className="w-4 h-4" />
                {str(t.editor.codeTab)}
              </TabsTrigger>
              <TabsTrigger value="settings" className="gap-2">
                <Settings className="w-4 h-4" />
                {str(t.editor.settingsTab)}
              </TabsTrigger>
              <TabsTrigger value="test" className="gap-2">
                <TestTube className="w-4 h-4" />
                {str(t.editor.testTab)}
              </TabsTrigger>
            </TabsList>
          </div>

          <ScrollArea className="flex-1 px-6">
            {/* Code Tab */}
            <TabsContent value="code" className="mt-4 space-y-4">
              <div className="flex justify-end">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleLoadTemplate}
                  disabled={isLoadingTemplate}
                >
                  {isLoadingTemplate ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Wand2 className="w-4 h-4 mr-2" />
                  )}
                  {str(t.editor.loadTemplate)}
                </Button>
              </div>

              <div className="space-y-2">
                <Label>{str(t.editor.validatorCode)}</Label>
                <CodeEditor
                  value={form.code}
                  onChange={(v) => handleChange('code', v)}
                  language="python"
                  minLines={15}
                  maxLines={25}
                  placeholder={str(t.editor.codePlaceholder)}
                />
              </div>

              {/* Parameters */}
              <ValidatorParamForm
                parameters={form.parameters}
                onChange={(p) => handleChange('parameters', p)}
                columns={columns}
              />
            </TabsContent>

            {/* Settings Tab */}
            <TabsContent value="settings" className="mt-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                {/* Display Name */}
                <div className="space-y-2">
                  <Label>{str(t.editor.displayName)}</Label>
                  <Input
                    value={form.display_name}
                    onChange={(e) => handleChange('display_name', e.target.value)}
                    placeholder="My Custom Validator"
                  />
                </div>

                {/* Name (auto-generated) */}
                <div className="space-y-2">
                  <Label>{str(t.editor.name)}</Label>
                  <Input
                    value={form.name}
                    onChange={(e) => handleChange('name', e.target.value)}
                    placeholder="my_custom_validator"
                    disabled={isEditing}
                  />
                  <p className="text-xs text-muted-foreground">{str(t.editor.nameHint)}</p>
                </div>
              </div>

              {/* Description */}
              <div className="space-y-2">
                <Label>{str(t.editor.description)}</Label>
                <Textarea
                  value={form.description}
                  onChange={(e) => handleChange('description', e.target.value)}
                  placeholder={str(t.editor.descriptionPlaceholder)}
                  rows={3}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Category */}
                <div className="space-y-2">
                  <Label>{str(t.editor.category)}</Label>
                  <Select
                    value={form.category}
                    onValueChange={(v) => handleChange('category', v as ValidatorCategory)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {VALIDATOR_CATEGORIES.map((cat) => (
                        <SelectItem key={cat} value={cat}>
                          {cat}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Severity */}
                <div className="space-y-2">
                  <Label>{str(t.editor.severity)}</Label>
                  <Select
                    value={form.severity}
                    onValueChange={(v) => handleChange('severity', v as ValidatorSeverity)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {SEVERITIES.map((sev) => (
                        <SelectItem key={sev} value={sev}>
                          {sev}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Tags */}
              <div className="space-y-2">
                <Label>{str(t.editor.tags)}</Label>
                <div className="flex gap-2">
                  <Input
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    placeholder={str(t.editor.tagPlaceholder)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        handleAddTag()
                      }
                    }}
                  />
                  <Button variant="outline" onClick={handleAddTag}>
                    {str(t.editor.addTag)}
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2 mt-2">
                  {form.tags.map((tag) => (
                    <Badge key={tag} variant="secondary" className="gap-1">
                      {tag}
                      <button
                        onClick={() => handleRemoveTag(tag)}
                        className="ml-1 hover:text-destructive"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Enabled */}
              <div className="flex items-center gap-2">
                <Switch
                  id="enabled"
                  checked={form.is_enabled}
                  onCheckedChange={(v) => handleChange('is_enabled', v)}
                />
                <Label htmlFor="enabled">{str(t.editor.enabled)}</Label>
              </div>
            </TabsContent>

            {/* Test Tab */}
            <TabsContent value="test" className="mt-4">
              <ValidatorTestPanel
                code={form.code}
                parameters={form.parameters}
                onTest={handleTest}
              />
            </TabsContent>
          </ScrollArea>
        </Tabs>

        <DialogFooter className="px-6 pb-6">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {str(t.actions.cancel)}
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                {str(t.editor.saving)}
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                {isEditing ? str(t.actions.update) : str(t.actions.create)}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default ValidatorEditorDialog
