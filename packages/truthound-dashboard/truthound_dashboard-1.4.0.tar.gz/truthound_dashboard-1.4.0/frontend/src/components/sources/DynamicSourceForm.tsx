/**
 * DynamicSourceForm - Renders form fields based on source type definition
 */

import { useCallback, useMemo } from 'react'
import { Eye, EyeOff, HelpCircle } from 'lucide-react'
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
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'
import type { FieldDefinition, SourceTypeDefinition } from '@/api/client'
import { useState } from 'react'

interface DynamicSourceFormProps {
  sourceType: SourceTypeDefinition
  values: Record<string, unknown>
  onChange: (values: Record<string, unknown>) => void
  errors?: Record<string, string>
}

export function DynamicSourceForm({
  sourceType,
  values,
  onChange,
  errors = {},
}: DynamicSourceFormProps) {
  const [showPasswords, setShowPasswords] = useState<Record<string, boolean>>({})

  // Check if a field should be visible based on depends_on condition
  const isFieldVisible = useCallback(
    (field: FieldDefinition): boolean => {
      if (!field.depends_on) return true
      const dependsValue = values[field.depends_on]
      return dependsValue === field.depends_value
    },
    [values]
  )

  // Get visible fields
  const visibleFields = useMemo(
    () => sourceType.fields.filter(isFieldVisible),
    [sourceType.fields, isFieldVisible]
  )

  // Handle field value change
  const handleFieldChange = useCallback(
    (fieldName: string, value: unknown) => {
      onChange({ ...values, [fieldName]: value })
    },
    [values, onChange]
  )

  // Toggle password visibility
  const togglePasswordVisibility = (fieldName: string) => {
    setShowPasswords((prev) => ({ ...prev, [fieldName]: !prev[fieldName] }))
  }

  // Render a single field based on its type
  const renderField = (field: FieldDefinition) => {
    const value = values[field.name]
    const error = errors[field.name]
    const fieldId = `field-${field.name}`

    const labelElement = (
      <div className="flex items-center gap-2">
        <Label htmlFor={fieldId} className={cn(error && 'text-destructive')}>
          {field.label}
          {field.required && <span className="ml-1 text-destructive">*</span>}
        </Label>
        {field.description && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-3.5 w-3.5 text-muted-foreground" />
              </TooltipTrigger>
              <TooltipContent side="right" className="max-w-xs">
                <p className="text-sm">{field.description}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>
    )

    switch (field.type) {
      case 'text':
      case 'file_path':
        return (
          <div key={field.name} className="space-y-2">
            {labelElement}
            <Input
              id={fieldId}
              type="text"
              placeholder={field.placeholder}
              value={(value as string) ?? field.default ?? ''}
              onChange={(e) => handleFieldChange(field.name, e.target.value)}
              className={cn(error && 'border-destructive')}
            />
            {error && <p className="text-xs text-destructive">{error}</p>}
          </div>
        )

      case 'password':
        return (
          <div key={field.name} className="space-y-2">
            {labelElement}
            <div className="relative">
              <Input
                id={fieldId}
                type={showPasswords[field.name] ? 'text' : 'password'}
                placeholder={field.placeholder || '********'}
                value={(value as string) ?? ''}
                onChange={(e) => handleFieldChange(field.name, e.target.value)}
                className={cn('pr-10', error && 'border-destructive')}
              />
              <button
                type="button"
                onClick={() => togglePasswordVisibility(field.name)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showPasswords[field.name] ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
            {error && <p className="text-xs text-destructive">{error}</p>}
          </div>
        )

      case 'number':
        return (
          <div key={field.name} className="space-y-2">
            {labelElement}
            <Input
              id={fieldId}
              type="number"
              placeholder={field.placeholder}
              value={(value as number) ?? field.default ?? ''}
              onChange={(e) =>
                handleFieldChange(field.name, e.target.value ? Number(e.target.value) : undefined)
              }
              min={field.min_value}
              max={field.max_value}
              className={cn(error && 'border-destructive')}
            />
            {error && <p className="text-xs text-destructive">{error}</p>}
          </div>
        )

      case 'select':
        return (
          <div key={field.name} className="space-y-2">
            {labelElement}
            <Select
              value={(value as string) ?? (field.default as string) ?? ''}
              onValueChange={(v) => handleFieldChange(field.name, v)}
            >
              <SelectTrigger className={cn(error && 'border-destructive')}>
                <SelectValue placeholder={field.placeholder || 'Select...'} />
              </SelectTrigger>
              <SelectContent>
                {field.options?.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {error && <p className="text-xs text-destructive">{error}</p>}
          </div>
        )

      case 'boolean':
        return (
          <div key={field.name} className="flex items-center justify-between py-2">
            <div className="space-y-0.5">
              {labelElement}
              {field.description && (
                <p className="text-xs text-muted-foreground">{field.description}</p>
              )}
            </div>
            <Switch
              id={fieldId}
              checked={(value as boolean) ?? (field.default as boolean) ?? false}
              onCheckedChange={(checked) => handleFieldChange(field.name, checked)}
            />
          </div>
        )

      case 'textarea':
        return (
          <div key={field.name} className="space-y-2">
            {labelElement}
            <textarea
              id={fieldId}
              placeholder={field.placeholder}
              value={(value as string) ?? field.default ?? ''}
              onChange={(e) => handleFieldChange(field.name, e.target.value)}
              className={cn(
                'flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                error && 'border-destructive'
              )}
            />
            {error && <p className="text-xs text-destructive">{error}</p>}
          </div>
        )

      default:
        return null
    }
  }

  // Group fields by type (required first, then optional)
  const requiredFields = visibleFields.filter((f) => f.required)
  const optionalFields = visibleFields.filter((f) => !f.required)

  return (
    <div className="space-y-6">
      {/* Required fields */}
      {requiredFields.length > 0 && (
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-muted-foreground">Required</h4>
          <div className="grid gap-4 sm:grid-cols-2">
            {requiredFields.map(renderField)}
          </div>
        </div>
      )}

      {/* Optional fields */}
      {optionalFields.length > 0 && (
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-muted-foreground">Optional</h4>
          <div className="grid gap-4 sm:grid-cols-2">
            {optionalFields.map(renderField)}
          </div>
        </div>
      )}
    </div>
  )
}
