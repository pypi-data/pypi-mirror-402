/**
 * ValidatorParamForm - Form for defining validator parameters
 *
 * Allows users to define custom parameters for validators with:
 * - Parameter name, type, description
 * - Required/optional flag
 * - Default values
 * - Options for select types
 * - Min/max values for numeric types
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
import type { ValidatorParamDefinition, ValidatorParamType } from './types'

interface ValidatorParamFormProps {
  parameters: ValidatorParamDefinition[]
  onChange: (parameters: ValidatorParamDefinition[]) => void
  columns?: string[]
  disabled?: boolean
}

const PARAM_TYPES: ValidatorParamType[] = [
  'string',
  'integer',
  'float',
  'boolean',
  'column',
  'column_list',
  'select',
  'multi_select',
  'regex',
  'json',
]

/**
 * Single parameter editor component
 */
function ParamEditor({
  param,
  index,
  onChange,
  onRemove,
  columns = [],
  disabled = false,
}: {
  param: ValidatorParamDefinition
  index: number
  onChange: (param: ValidatorParamDefinition) => void
  onRemove: () => void
  columns?: string[]
  disabled?: boolean
}) {
  const t = useIntlayer('plugins')
  const [isExpanded, setIsExpanded] = useState(true)

  const handleChange = useCallback(
    <K extends keyof ValidatorParamDefinition>(
      field: K,
      value: ValidatorParamDefinition[K]
    ) => {
      onChange({ ...param, [field]: value })
    },
    [param, onChange]
  )

  const needsOptions = param.type === 'select' || param.type === 'multi_select'
  const needsMinMax = param.type === 'integer' || param.type === 'float'

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
              {param.name || `Parameter ${index + 1}`}
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
                <Label className="text-xs">{str(t.editor.paramName)}</Label>
                <Input
                  value={param.name}
                  onChange={(e) => handleChange('name', e.target.value)}
                  placeholder="threshold"
                  disabled={disabled}
                  className="h-8 text-sm"
                />
              </div>

              {/* Type */}
              <div className="space-y-1">
                <Label className="text-xs">{str(t.editor.paramType)}</Label>
                <Select
                  value={param.type}
                  onValueChange={(v) => handleChange('type', v as ValidatorParamType)}
                  disabled={disabled}
                >
                  <SelectTrigger className="h-8 text-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {PARAM_TYPES.map((type) => (
                      <SelectItem key={type} value={type}>
                        {str(t.paramTypes[type as keyof typeof t.paramTypes])}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Description */}
            <div className="space-y-1">
              <Label className="text-xs">{str(t.editor.paramDescription)}</Label>
              <Input
                value={param.description || ''}
                onChange={(e) => handleChange('description', e.target.value)}
                placeholder="Enter parameter description"
                disabled={disabled}
                className="h-8 text-sm"
              />
            </div>

            <div className="flex items-center gap-4">
              {/* Required */}
              <div className="flex items-center gap-2">
                <Switch
                  id={`required-${index}`}
                  checked={param.required}
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
              {param.type === 'boolean' ? (
                <Select
                  value={param.default?.toString() || 'false'}
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
              ) : param.type === 'column' ? (
                <Select
                  value={(param.default as string) || ''}
                  onValueChange={(v) => handleChange('default', v)}
                  disabled={disabled}
                >
                  <SelectTrigger className="h-8 text-sm">
                    <SelectValue placeholder="Select column" />
                  </SelectTrigger>
                  <SelectContent>
                    {columns.map((col) => (
                      <SelectItem key={col} value={col}>
                        {col}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <Input
                  type={param.type === 'integer' || param.type === 'float' ? 'number' : 'text'}
                  value={param.default?.toString() || ''}
                  onChange={(e) => {
                    const value =
                      param.type === 'integer'
                        ? parseInt(e.target.value, 10)
                        : param.type === 'float'
                        ? parseFloat(e.target.value)
                        : e.target.value
                    handleChange('default', value)
                  }}
                  disabled={disabled}
                  className="h-8 text-sm"
                />
              )}
            </div>

            {/* Min/Max for numeric types */}
            {needsMinMax && (
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label className="text-xs">{str(t.editor.minValue)}</Label>
                  <Input
                    type="number"
                    value={param.min_value ?? ''}
                    onChange={(e) =>
                      handleChange('min_value', e.target.value ? Number(e.target.value) : undefined)
                    }
                    disabled={disabled}
                    className="h-8 text-sm"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">{str(t.editor.maxValue)}</Label>
                  <Input
                    type="number"
                    value={param.max_value ?? ''}
                    onChange={(e) =>
                      handleChange('max_value', e.target.value ? Number(e.target.value) : undefined)
                    }
                    disabled={disabled}
                    className="h-8 text-sm"
                  />
                </div>
              </div>
            )}

            {/* Options for select types */}
            {needsOptions && (
              <div className="space-y-1">
                <Label className="text-xs">{str(t.editor.options)}</Label>
                <Input
                  value={param.options?.join(', ') || ''}
                  onChange={(e) =>
                    handleChange(
                      'options',
                      e.target.value.split(',').map((s) => s.trim()).filter(Boolean)
                    )
                  }
                  placeholder="option1, option2, option3"
                  disabled={disabled}
                  className="h-8 text-sm"
                />
                <p className="text-xs text-muted-foreground">{str(t.editor.optionsHint)}</p>
              </div>
            )}
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  )
}

/**
 * Form for managing validator parameters
 */
export function ValidatorParamForm({
  parameters,
  onChange,
  columns = [],
  disabled = false,
}: ValidatorParamFormProps) {
  const t = useIntlayer('plugins')

  const handleAddParam = useCallback(() => {
    const newParam: ValidatorParamDefinition = {
      name: '',
      type: 'string',
      description: '',
      required: false,
    }
    onChange([...parameters, newParam])
  }, [parameters, onChange])

  const handleUpdateParam = useCallback(
    (index: number, param: ValidatorParamDefinition) => {
      const newParams = [...parameters]
      newParams[index] = param
      onChange(newParams)
    },
    [parameters, onChange]
  )

  const handleRemoveParam = useCallback(
    (index: number) => {
      onChange(parameters.filter((_, i) => i !== index))
    },
    [parameters, onChange]
  )

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <Label className="text-sm font-medium">{str(t.editor.parameters)}</Label>
        <Button
          variant="outline"
          size="sm"
          onClick={handleAddParam}
          disabled={disabled}
          className="h-7"
        >
          <Plus className="w-3 h-3 mr-1" />
          {str(t.editor.addParameter)}
        </Button>
      </div>

      {parameters.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-4 border-2 border-dashed rounded-md">
          {str(t.editor.noParameters)}
        </p>
      ) : (
        <div className="space-y-2">
          {parameters.map((param, index) => (
            <ParamEditor
              key={index}
              param={param}
              index={index}
              onChange={(p) => handleUpdateParam(index, p)}
              onRemove={() => handleRemoveParam(index)}
              columns={columns}
              disabled={disabled}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default ValidatorParamForm
