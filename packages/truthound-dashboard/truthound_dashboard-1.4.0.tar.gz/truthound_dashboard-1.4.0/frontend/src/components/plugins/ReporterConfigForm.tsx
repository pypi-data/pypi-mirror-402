/**
 * ReporterConfigForm - Form for defining reporter configuration fields
 *
 * Allows users to define custom configuration fields for reporters with:
 * - Field name, type, label, description
 * - Required/optional flag
 * - Default values
 * - Options for select types
 */

import { useState, useCallback } from 'react'
import { useIntlayer } from 'react-intlayer'
import { str } from '@/lib/intlayer-utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { Plus, Trash2, ChevronDown, ChevronRight, GripVertical } from 'lucide-react'
import type { ReporterFieldDefinition } from './types'

interface ReporterConfigFormProps {
  fields: ReporterFieldDefinition[]
  onChange: (fields: ReporterFieldDefinition[]) => void
  disabled?: boolean
}

type FieldType = 'string' | 'boolean' | 'select' | 'number'

const FIELD_TYPES: FieldType[] = ['string', 'boolean', 'select', 'number']

/**
 * Single field editor component
 */
function FieldEditor({
  field,
  index,
  onChange,
  onRemove,
  disabled = false,
}: {
  field: ReporterFieldDefinition
  index: number
  onChange: (field: ReporterFieldDefinition) => void
  onRemove: () => void
  disabled?: boolean
}) {
  const t = useIntlayer('plugins')
  const [isExpanded, setIsExpanded] = useState(true)

  const handleChange = useCallback(
    <K extends keyof ReporterFieldDefinition>(
      key: K,
      value: ReporterFieldDefinition[K]
    ) => {
      onChange({ ...field, [key]: value })
    },
    [field, onChange]
  )

  const needsOptions = field.type === 'select'

  // Handle options change
  const handleOptionsChange = useCallback(
    (optionsStr: string) => {
      const options = optionsStr
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean)
        .map((s) => {
          const parts = s.split(':')
          return {
            label: parts[0].trim(),
            value: parts.length > 1 ? parts[1].trim() : parts[0].trim(),
          }
        })
      handleChange('options', options)
    },
    [handleChange]
  )

  return (
    <Card className="border-dashed">
      <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
        <CardHeader className="py-2 px-3">
          <div className="flex items-center gap-2">
            <GripVertical className="w-4 h-4 text-muted-foreground cursor-grab" />
            <CollapsibleTrigger asChild>
              <Button variant="ghost" size="sm" className="p-0 h-auto">
                {isExpanded ? (
                  <ChevronDown className="w-4 h-4" />
                ) : (
                  <ChevronRight className="w-4 h-4" />
                )}
              </Button>
            </CollapsibleTrigger>
            <CardTitle className="text-sm flex-1">
              {field.label || field.name || `Field ${index + 1}`}
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={onRemove}
              disabled={disabled}
              className="h-6 w-6 p-0 text-destructive hover:text-destructive"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>

        <CollapsibleContent>
          <CardContent className="pt-0 pb-3 px-3 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              {/* Name */}
              <div className="space-y-1">
                <Label className="text-xs">{str(t.editor.fieldName)}</Label>
                <Input
                  value={field.name}
                  onChange={(e) => handleChange('name', e.target.value)}
                  placeholder="show_details"
                  disabled={disabled}
                  className="h-8 text-sm"
                />
              </div>

              {/* Type */}
              <div className="space-y-1">
                <Label className="text-xs">{str(t.editor.fieldType)}</Label>
                <Select
                  value={field.type}
                  onValueChange={(v) => handleChange('type', v as FieldType)}
                  disabled={disabled}
                >
                  <SelectTrigger className="h-8 text-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {FIELD_TYPES.map((type) => (
                      <SelectItem key={type} value={type}>
                        {type}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Label */}
            <div className="space-y-1">
              <Label className="text-xs">{str(t.editor.fieldLabel)}</Label>
              <Input
                value={field.label || ''}
                onChange={(e) => handleChange('label', e.target.value)}
                placeholder="Show Details"
                disabled={disabled}
                className="h-8 text-sm"
              />
            </div>

            {/* Description */}
            <div className="space-y-1">
              <Label className="text-xs">{str(t.editor.fieldDescription)}</Label>
              <Input
                value={field.description || ''}
                onChange={(e) => handleChange('description', e.target.value)}
                placeholder="Whether to show detailed information"
                disabled={disabled}
                className="h-8 text-sm"
              />
            </div>

            <div className="flex items-center gap-4">
              {/* Required */}
              <div className="flex items-center gap-2">
                <Switch
                  id={`required-${index}`}
                  checked={field.required}
                  onCheckedChange={(v) => handleChange('required', v)}
                  disabled={disabled}
                />
                <Label htmlFor={`required-${index}`} className="text-xs">
                  {str(t.editor.required)}
                </Label>
              </div>
            </div>

            {/* Default Value */}
            <div className="space-y-1">
              <Label className="text-xs">{str(t.editor.defaultValue)}</Label>
              {field.type === 'boolean' ? (
                <Select
                  value={field.default?.toString() || 'false'}
                  onValueChange={(v) => handleChange('default', v === 'true')}
                  disabled={disabled}
                >
                  <SelectTrigger className="h-8 text-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="true">True</SelectItem>
                    <SelectItem value="false">False</SelectItem>
                  </SelectContent>
                </Select>
              ) : field.type === 'number' ? (
                <Input
                  type="number"
                  value={field.default?.toString() || ''}
                  onChange={(e) => handleChange('default', parseFloat(e.target.value))}
                  disabled={disabled}
                  className="h-8 text-sm"
                />
              ) : (
                <Input
                  value={(field.default as string) || ''}
                  onChange={(e) => handleChange('default', e.target.value)}
                  disabled={disabled}
                  className="h-8 text-sm"
                />
              )}
            </div>

            {/* Options for select type */}
            {needsOptions && (
              <div className="space-y-1">
                <Label className="text-xs">{str(t.editor.options)}</Label>
                <Input
                  value={
                    field.options
                      ?.map((o) => (o.label === o.value ? o.value : `${o.label}:${o.value}`))
                      .join(', ') || ''
                  }
                  onChange={(e) => handleOptionsChange(e.target.value)}
                  placeholder="Label:value, Option 2, Label3:value3"
                  disabled={disabled}
                  className="h-8 text-sm"
                />
                <p className="text-xs text-muted-foreground">{str(t.editor.fieldOptionsHint)}</p>
              </div>
            )}
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  )
}

/**
 * Form for managing reporter configuration fields
 */
export function ReporterConfigForm({
  fields,
  onChange,
  disabled = false,
}: ReporterConfigFormProps) {
  const t = useIntlayer('plugins')

  const handleAddField = useCallback(() => {
    const newField: ReporterFieldDefinition = {
      name: '',
      type: 'string',
      label: '',
      description: '',
      required: false,
    }
    onChange([...fields, newField])
  }, [fields, onChange])

  const handleUpdateField = useCallback(
    (index: number, field: ReporterFieldDefinition) => {
      const newFields = [...fields]
      newFields[index] = field
      onChange(newFields)
    },
    [fields, onChange]
  )

  const handleRemoveField = useCallback(
    (index: number) => {
      onChange(fields.filter((_, i) => i !== index))
    },
    [fields, onChange]
  )

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <Label className="text-sm font-medium">{str(t.editor.configFields)}</Label>
        <Button
          variant="outline"
          size="sm"
          onClick={handleAddField}
          disabled={disabled}
          className="h-7"
        >
          <Plus className="w-3 h-3 mr-1" />
          {str(t.editor.addField)}
        </Button>
      </div>

      {fields.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-4 border-2 border-dashed rounded-md">
          {str(t.editor.noConfigFields)}
        </p>
      ) : (
        <div className="space-y-2">
          {fields.map((field, index) => (
            <FieldEditor
              key={index}
              field={field}
              index={index}
              onChange={(f) => handleUpdateField(index, f)}
              onRemove={() => handleRemoveField(index)}
              disabled={disabled}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default ReporterConfigForm
