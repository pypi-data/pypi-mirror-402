/**
 * ReporterEditorDialog - Dialog for creating/editing custom reporters
 *
 * Features:
 * - Dual editor: Jinja2 template or Python code
 * - Configuration field definition
 * - Output format selection
 * - Live preview panel
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
import { Checkbox } from '@/components/ui/checkbox'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { toast } from '@/hooks/use-toast'
import { CodeEditor } from '@/components/common'
import { ReporterConfigForm } from './ReporterConfigForm'
import { ReporterPreviewPanel } from './ReporterPreviewPanel'
import {
  Save,
  Loader2,
  FileCode,
  FileText,
  Settings,
  Eye,
  Wand2,
} from 'lucide-react'
import {
  getReporterTemplates,
  createCustomReporter,
  updateCustomReporter,
  previewCustomReporter,
} from '@/api/client'
import type {
  CustomReporter,
  ReporterEditorDialogProps,
  ReporterFormState,
  ReporterFieldDefinition,
  ReporterOutputFormat,
  ReporterPreviewResult,
} from './types'

const OUTPUT_FORMATS: ReporterOutputFormat[] = ['html', 'pdf', 'json', 'csv', 'excel', 'markdown']

/**
 * Slugify a string for use as a reporter name
 */
function slugify(str: string): string {
  return str
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_|_$/g, '')
}

/**
 * Dialog for creating/editing custom reporters
 */
export function ReporterEditorDialog({
  open,
  onOpenChange,
  onSuccess,
  reporter,
}: ReporterEditorDialogProps) {
  const t = useIntlayer('plugins')
  const isEditing = !!reporter

  // Form state
  const [form, setForm] = useState<ReporterFormState>({
    name: '',
    display_name: '',
    description: '',
    output_formats: ['html'],
    config_fields: [],
    template: '',
    code: '',
    is_enabled: true,
  })
  const [editorMode, setEditorMode] = useState<'template' | 'code'>('template')
  const [activeTab, setActiveTab] = useState('editor')
  const [isSaving, setIsSaving] = useState(false)
  const [isLoadingTemplate, setIsLoadingTemplate] = useState(false)

  // Initialize form with reporter data or defaults
  useEffect(() => {
    if (open) {
      if (reporter) {
        setForm({
          name: reporter.name,
          display_name: reporter.display_name,
          description: reporter.description,
          output_formats: reporter.output_formats || ['html'],
          config_fields: reporter.config_fields || [],
          template: reporter.template || '',
          code: reporter.code || '',
          is_enabled: reporter.is_enabled,
        })
        // Set editor mode based on what's populated
        setEditorMode(reporter.template ? 'template' : 'code')
      } else {
        // Load template for new reporters
        handleLoadTemplate()
      }
    }
  }, [open, reporter])

  // Load templates
  const handleLoadTemplate = useCallback(async () => {
    setIsLoadingTemplate(true)
    try {
      const result = await getReporterTemplates()
      setForm((prev) => ({
        ...prev,
        template: editorMode === 'template' ? result.jinja2_template : prev.template,
        code: editorMode === 'code' ? result.code_template : prev.code,
      }))
    } catch {
      // Fallback templates
      setForm((prev) => ({
        ...prev,
        template: editorMode === 'template' ? `<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #fd9e4b; }
        .card { background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .stat { font-size: 24px; font-weight: bold; }
    </style>
</head>
<body>
    <h1>{{ title }}</h1>
    <div class="card">
        <p>Generated: {{ metadata.generated_at }}</p>
        <p class="stat">Total Rows: {{ total_rows }}</p>
    </div>
</body>
</html>` : prev.template,
        code: editorMode === 'code' ? `def generate_report(data, config, format, metadata):
    """Generate custom report.

    Args:
        data: Report data dictionary.
        config: User configuration values.
        format: Output format (html, pdf, json, etc.).
        metadata: Report metadata.

    Returns:
        Dictionary with:
            - content: Generated content string
            - content_type: MIME type
            - filename: Suggested filename
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{data.get('title', 'Report')}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #fd9e4b; }}
        </style>
    </head>
    <body>
        <h1>{data.get('title', 'Report')}</h1>
        <p>Generated: {metadata.get('generated_at', 'Unknown')}</p>
    </body>
    </html>
    """
    return {
        "content": html,
        "content_type": "text/html",
        "filename": "report.html"
    }` : prev.code,
      }))
    } finally {
      setIsLoadingTemplate(false)
    }
  }, [editorMode])

  // Handle form field change
  const handleChange = useCallback(<K extends keyof ReporterFormState>(
    field: K,
    value: ReporterFormState[K]
  ) => {
    setForm((prev) => {
      const newForm = { ...prev, [field]: value }
      // Auto-generate name from display_name
      if (field === 'display_name' && !isEditing) {
        newForm.name = slugify(value as string) + '_reporter'
      }
      return newForm
    })
  }, [isEditing])

  // Handle output format toggle
  const handleFormatToggle = useCallback((format: ReporterOutputFormat) => {
    setForm((prev) => {
      const formats = prev.output_formats.includes(format)
        ? prev.output_formats.filter((f) => f !== format)
        : [...prev.output_formats, format]
      return { ...prev, output_formats: formats.length > 0 ? formats : ['html'] }
    })
  }, [])

  // Handle preview
  const handlePreview = useCallback(
    async (data: {
      template?: string
      code?: string
      sample_data: Record<string, unknown>
      config: Record<string, unknown>
      format: string
    }): Promise<ReporterPreviewResult> => {
      const result = await previewCustomReporter({
        template: data.template,
        code: data.code,
        sample_data: data.sample_data,
        config: data.config,
        format: data.format,
      })
      return result
    },
    []
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
    if (!form.template.trim() && !form.code.trim()) {
      toast({ title: str(t.editor.validationError), description: str(t.editor.templateOrCodeRequired), variant: 'destructive' })
      return
    }

    setIsSaving(true)
    try {
      const data = {
        name: form.name,
        display_name: form.display_name,
        description: form.description,
        output_formats: form.output_formats,
        config_fields: form.config_fields,
        template: editorMode === 'template' ? form.template : undefined,
        code: editorMode === 'code' ? form.code : undefined,
        is_enabled: form.is_enabled,
      }

      if (isEditing && reporter) {
        await updateCustomReporter(reporter.id, data)
        toast({ title: str(t.messages.reporterUpdated) })
      } else {
        await createCustomReporter(data)
        toast({ title: str(t.messages.reporterCreated) })
      }

      onSuccess?.()
      onOpenChange(false)
    } catch (err) {
      toast({
        title: isEditing ? str(t.messages.reporterUpdateFailed) : str(t.messages.reporterCreateFailed),
        description: err instanceof Error ? err.message : 'Unknown error',
        variant: 'destructive',
      })
    } finally {
      setIsSaving(false)
    }
  }, [form, editorMode, isEditing, reporter, onSuccess, onOpenChange, t])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] flex flex-col p-0">
        <DialogHeader className="px-6 pt-6">
          <DialogTitle>
            {isEditing ? str(t.editor.editReporter) : str(t.editor.createReporter)}
          </DialogTitle>
          <DialogDescription>
            {isEditing
              ? str(t.editor.editReporterDescription)
              : str(t.editor.createReporterDescription)}
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col overflow-hidden">
          <div className="px-6">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="editor" className="gap-2">
                <FileCode className="w-4 h-4" />
                {str(t.editor.editorTab)}
              </TabsTrigger>
              <TabsTrigger value="settings" className="gap-2">
                <Settings className="w-4 h-4" />
                {str(t.editor.settingsTab)}
              </TabsTrigger>
              <TabsTrigger value="preview" className="gap-2">
                <Eye className="w-4 h-4" />
                {str(t.editor.previewTab)}
              </TabsTrigger>
            </TabsList>
          </div>

          <ScrollArea className="flex-1 px-6">
            {/* Editor Tab */}
            <TabsContent value="editor" className="mt-4 space-y-4">
              {/* Editor Mode Selection */}
              <div className="flex items-center justify-between">
                <Tabs value={editorMode} onValueChange={(v) => setEditorMode(v as 'template' | 'code')}>
                  <TabsList>
                    <TabsTrigger value="template" className="gap-2">
                      <FileText className="w-4 h-4" />
                      Jinja2 Template
                    </TabsTrigger>
                    <TabsTrigger value="code" className="gap-2">
                      <FileCode className="w-4 h-4" />
                      Python Code
                    </TabsTrigger>
                  </TabsList>
                </Tabs>
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

              {/* Template/Code Editor */}
              <div className="space-y-2">
                <Label>
                  {editorMode === 'template'
                    ? str(t.editor.jinja2Template)
                    : str(t.editor.pythonCode)}
                </Label>
                <CodeEditor
                  value={editorMode === 'template' ? form.template : form.code}
                  onChange={(v) =>
                    handleChange(editorMode === 'template' ? 'template' : 'code', v)
                  }
                  language={editorMode === 'template' ? 'jinja2' : 'python'}
                  minLines={15}
                  maxLines={25}
                  placeholder={
                    editorMode === 'template'
                      ? str(t.editor.templatePlaceholder)
                      : str(t.editor.codePlaceholder)
                  }
                />
                <p className="text-xs text-muted-foreground">
                  {editorMode === 'template'
                    ? str(t.editor.templateHint)
                    : str(t.editor.codeHint)}
                </p>
              </div>

              {/* Configuration Fields */}
              <ReporterConfigForm
                fields={form.config_fields}
                onChange={(f) => handleChange('config_fields', f)}
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
                    placeholder="My Custom Reporter"
                  />
                </div>

                {/* Name (auto-generated) */}
                <div className="space-y-2">
                  <Label>{str(t.editor.name)}</Label>
                  <Input
                    value={form.name}
                    onChange={(e) => handleChange('name', e.target.value)}
                    placeholder="my_custom_reporter"
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

              {/* Output Formats */}
              <div className="space-y-2">
                <Label>{str(t.editor.outputFormats)}</Label>
                <div className="flex flex-wrap gap-3">
                  {OUTPUT_FORMATS.map((format) => (
                    <div key={format} className="flex items-center gap-2">
                      <Checkbox
                        id={`format-${format}`}
                        checked={form.output_formats.includes(format)}
                        onCheckedChange={() => handleFormatToggle(format)}
                      />
                      <Label htmlFor={`format-${format}`} className="text-sm cursor-pointer">
                        {format.toUpperCase()}
                      </Label>
                    </div>
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

            {/* Preview Tab */}
            <TabsContent value="preview" className="mt-4">
              <ReporterPreviewPanel
                template={editorMode === 'template' ? form.template : undefined}
                code={editorMode === 'code' ? form.code : undefined}
                configFields={form.config_fields}
                outputFormats={form.output_formats}
                onPreview={handlePreview}
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

export default ReporterEditorDialog
