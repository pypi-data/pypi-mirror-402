/**
 * CustomReporterSection - Section in download dropdown for custom reporters
 *
 * Features:
 * - Lists available custom reporters
 * - Format selection per reporter
 * - Config value inputs if reporter has config fields
 */

import { useState, useEffect, useCallback } from 'react'
import { useIntlayer } from 'react-intlayer'
import { str } from '@/lib/intlayer-utils'
import {
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
} from '@/components/ui/dropdown-menu'
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
import { Checkbox } from '@/components/ui/checkbox'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import { toast } from '@/hooks/use-toast'
import { Code, Loader2, FileCode } from 'lucide-react'
import {
  listCustomReporters,
  downloadCustomReport,
  type CustomReporter,
} from '@/api/client'

interface CustomReporterSectionProps {
  validationId: string
  disabled?: boolean
}

/**
 * Render config field input based on type
 */
interface ConfigFieldInputProps {
  field: {
    name: string
    type: string
    required?: boolean
    label?: string
    description?: string
    default?: unknown
    options?: Array<{ label: string; value: string }> | string[]
  }
  value: unknown
  onChange: (value: unknown) => void
}

function ConfigFieldInput({ field, value, onChange }: ConfigFieldInputProps) {
  switch (field.type) {
    case 'boolean':
      return (
        <div className="flex items-center gap-2">
          <Checkbox
            id={field.name}
            checked={Boolean(value)}
            onCheckedChange={onChange}
          />
          <Label htmlFor={field.name} className="text-sm cursor-pointer">
            {field.name}
          </Label>
        </div>
      )

    case 'select':
      return (
        <Select
          value={String(value || '')}
          onValueChange={onChange}
        >
          <SelectTrigger className="h-8">
            <SelectValue placeholder="Select..." />
          </SelectTrigger>
          <SelectContent>
            {field.options?.map((opt) => {
              const isObject = typeof opt === 'object' && opt !== null
              const optValue = isObject ? opt.value : opt
              const optLabel = isObject ? opt.label : opt
              return (
                <SelectItem key={optValue} value={optValue}>
                  {optLabel}
                </SelectItem>
              )
            })}
          </SelectContent>
        </Select>
      )

    case 'integer':
    case 'float':
      return (
        <Input
          type="number"
          value={String(value || '')}
          onChange={(e) =>
            onChange(
              field.type === 'integer'
                ? parseInt(e.target.value, 10)
                : parseFloat(e.target.value)
            )
          }
          className="h-8"
        />
      )

    default:
      return (
        <Input
          value={String(value || '')}
          onChange={(e) => onChange(e.target.value)}
          className="h-8"
        />
      )
  }
}

/**
 * Dialog for configuring custom reporter before generation
 */
function CustomReporterConfigDialog({
  open,
  onOpenChange,
  reporter,
  validationId,
  selectedFormat,
  onSuccess,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  reporter: CustomReporter | null
  validationId: string
  selectedFormat: string
  onSuccess: (blob: Blob, filename: string) => void
}) {
  const common = useIntlayer('common')
  const [config, setConfig] = useState<Record<string, unknown>>({})
  const [isGenerating, setIsGenerating] = useState(false)

  // Initialize config with default values
  useEffect(() => {
    if (reporter?.config_fields) {
      const defaults: Record<string, unknown> = {}
      reporter.config_fields.forEach((field) => {
        if (field.default !== undefined) {
          defaults[field.name] = field.default
        }
      })
      setConfig(defaults)
    }
  }, [reporter])

  const handleGenerate = async () => {
    if (!reporter) return

    setIsGenerating(true)
    try {
      const blob = await downloadCustomReport(reporter.id, validationId, {
        output_format: selectedFormat,
        config,
      })

      // Generate filename
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
      const ext = selectedFormat === 'markdown' ? 'md' : selectedFormat
      const filename = `custom_report_${reporter.name}_${timestamp}.${ext}`

      onSuccess(blob, filename)
      onOpenChange(false)
    } catch (err) {
      toast({
        title: str(common.error),
        description:
          err instanceof Error ? err.message : 'Failed to generate report',
        variant: 'destructive',
      })
    } finally {
      setIsGenerating(false)
    }
  }

  if (!reporter) return null

  const hasConfigFields = reporter.config_fields && reporter.config_fields.length > 0

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileCode className="w-5 h-5 text-primary" />
            {reporter.display_name}
          </DialogTitle>
          <DialogDescription>
            {reporter.description || 'Configure and generate custom report'}
          </DialogDescription>
        </DialogHeader>

        {hasConfigFields && (
          <ScrollArea className="max-h-[300px]">
            <div className="space-y-4 py-4">
              {reporter.config_fields.map((field) => (
                <div key={field.name} className="space-y-2">
                  <Label className="text-sm">
                    {field.name}
                    {field.required && (
                      <span className="text-destructive ml-1">*</span>
                    )}
                  </Label>
                  <ConfigFieldInput
                    field={field}
                    value={config[field.name]}
                    onChange={(v) =>
                      setConfig((prev) => ({ ...prev, [field.name]: v }))
                    }
                  />
                  {field.description && (
                    <p className="text-xs text-muted-foreground">
                      {field.description}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </ScrollArea>
        )}

        {!hasConfigFields && (
          <div className="py-4 text-center text-muted-foreground">
            <p>No configuration required.</p>
            <p className="text-sm mt-1">
              Click generate to create the report in {selectedFormat.toUpperCase()} format.
            </p>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {str(common.cancel)}
          </Button>
          <Button onClick={handleGenerate} disabled={isGenerating}>
            {isGenerating ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Generating...
              </>
            ) : (
              'Generate Report'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

/**
 * Custom reporter section for the download dropdown
 */
export function CustomReporterSection({
  validationId,
  disabled = false,
}: CustomReporterSectionProps) {
  const [reporters, setReporters] = useState<CustomReporter[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedReporter, setSelectedReporter] = useState<CustomReporter | null>(null)
  const [selectedFormat, setSelectedFormat] = useState('')
  const [showConfigDialog, setShowConfigDialog] = useState(false)

  // Load custom reporters
  useEffect(() => {
    async function load() {
      try {
        const result = await listCustomReporters({ is_enabled: true })
        setReporters(result.data)
      } catch {
        // Silently fail - custom reporters are optional
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const handleReporterSelect = useCallback(
    (reporter: CustomReporter, format: string) => {
      setSelectedReporter(reporter)
      setSelectedFormat(format)
      setShowConfigDialog(true)
    },
    []
  )

  const handleDownloadSuccess = useCallback(
    (blob: Blob, filename: string) => {
      // Create download link
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)

      toast({
        title: 'Download complete',
        description: `Custom report downloaded: ${filename}`,
      })
    },
    []
  )

  // Don't render if no custom reporters
  if (loading || reporters.length === 0) {
    return null
  }

  return (
    <>
      <DropdownMenuSeparator />
      <DropdownMenuLabel className="flex items-center gap-2">
        <Code className="w-4 h-4" />
        Custom Reporters
      </DropdownMenuLabel>

      {reporters.map((reporter) => (
        <DropdownMenuSub key={reporter.id}>
          <DropdownMenuSubTrigger disabled={disabled}>
            <FileCode className="mr-2 h-4 w-4" />
            {reporter.display_name}
          </DropdownMenuSubTrigger>
          <DropdownMenuSubContent>
            <DropdownMenuLabel>Select Format</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {reporter.output_formats.map((format) => (
              <DropdownMenuItem
                key={format}
                onClick={() => handleReporterSelect(reporter, format)}
              >
                {format.toUpperCase()}
              </DropdownMenuItem>
            ))}
          </DropdownMenuSubContent>
        </DropdownMenuSub>
      ))}

      <CustomReporterConfigDialog
        open={showConfigDialog}
        onOpenChange={setShowConfigDialog}
        reporter={selectedReporter}
        validationId={validationId}
        selectedFormat={selectedFormat}
        onSuccess={handleDownloadSuccess}
      />
    </>
  )
}

export default CustomReporterSection
