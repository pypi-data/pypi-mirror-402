/**
 * ValidatorParamInput - Dynamic form input for validator parameters.
 *
 * Renders the appropriate input type based on parameter definition.
 */

import { useState, useCallback } from 'react'
import { X, Plus } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type { ParameterDefinition } from '@/api/client'

interface ValidatorParamInputProps {
  param: ParameterDefinition
  value: unknown
  onChange: (value: unknown) => void
  error?: string
  columns?: string[]
  disabled?: boolean
}

export function ValidatorParamInput({
  param,
  value,
  onChange,
  error,
  columns = [],
  disabled = false,
}: ValidatorParamInputProps) {
  const [inputValue, setInputValue] = useState('')

  // Handle adding items to list types
  const handleAddItem = useCallback(() => {
    if (!inputValue.trim()) return
    const currentList = Array.isArray(value) ? value : []
    if (!currentList.includes(inputValue.trim())) {
      onChange([...currentList, inputValue.trim()])
    }
    setInputValue('')
  }, [inputValue, value, onChange])

  // Handle removing items from list types
  const handleRemoveItem = useCallback(
    (item: string) => {
      const currentList = Array.isArray(value) ? value : []
      onChange(currentList.filter((v) => v !== item))
    },
    [value, onChange]
  )

  // Handle multi-select toggle
  const handleMultiSelectToggle = useCallback(
    (optionValue: string) => {
      const currentList = Array.isArray(value) ? value : []
      if (currentList.includes(optionValue)) {
        onChange(currentList.filter((v) => v !== optionValue))
      } else {
        onChange([...currentList, optionValue])
      }
    },
    [value, onChange]
  )

  const renderInput = () => {
    switch (param.type) {
      case 'string':
        return (
          <Input
            value={(value as string) || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={param.placeholder}
            disabled={disabled}
          />
        )

      case 'integer':
        return (
          <Input
            type="number"
            value={value !== undefined && value !== null ? String(value) : ''}
            onChange={(e) => {
              const val = e.target.value
              if (val === '') {
                onChange(undefined)
              } else {
                onChange(parseInt(val, 10))
              }
            }}
            min={param.min_value}
            max={param.max_value}
            placeholder={param.placeholder}
            disabled={disabled}
          />
        )

      case 'float':
        return (
          <Input
            type="number"
            step="any"
            value={value !== undefined && value !== null ? String(value) : ''}
            onChange={(e) => {
              const val = e.target.value
              if (val === '') {
                onChange(undefined)
              } else {
                onChange(parseFloat(val))
              }
            }}
            min={param.min_value}
            max={param.max_value}
            placeholder={param.placeholder}
            disabled={disabled}
          />
        )

      case 'boolean':
        return (
          <Switch
            checked={Boolean(value)}
            onCheckedChange={onChange}
            disabled={disabled}
          />
        )

      case 'select':
        return (
          <Select
            value={(value as string) || ''}
            onValueChange={onChange}
            disabled={disabled}
          >
            <SelectTrigger>
              <SelectValue placeholder={param.placeholder || 'Select...'} />
            </SelectTrigger>
            <SelectContent>
              {param.options?.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )

      case 'multi_select':
        return (
          <div className="space-y-2">
            <div className="flex flex-wrap gap-1">
              {param.options?.map((option) => {
                const isSelected = Array.isArray(value) && value.includes(option.value)
                return (
                  <Badge
                    key={option.value}
                    variant={isSelected ? 'default' : 'outline'}
                    className="cursor-pointer"
                    onClick={() => !disabled && handleMultiSelectToggle(option.value)}
                  >
                    {option.label}
                  </Badge>
                )
              })}
            </div>
          </div>
        )

      case 'column':
        return (
          <Select
            value={(value as string) || ''}
            onValueChange={onChange}
            disabled={disabled}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select column..." />
            </SelectTrigger>
            <SelectContent>
              {columns.map((col) => (
                <SelectItem key={col} value={col}>
                  {col}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )

      case 'column_list':
      case 'string_list':
        const currentList = Array.isArray(value) ? value : []
        const isColumnList = param.type === 'column_list'
        return (
          <div className="space-y-2">
            <div className="flex flex-wrap gap-1">
              {currentList.map((item) => (
                <Badge key={item} variant="secondary" className="gap-1">
                  {item}
                  <X
                    className="h-3 w-3 cursor-pointer hover:text-destructive"
                    onClick={() => !disabled && handleRemoveItem(item)}
                  />
                </Badge>
              ))}
            </div>
            <div className="flex gap-2">
              {isColumnList && columns.length > 0 ? (
                <Select
                  value=""
                  onValueChange={(val) => {
                    if (val && !currentList.includes(val)) {
                      onChange([...currentList, val])
                    }
                  }}
                  disabled={disabled}
                >
                  <SelectTrigger className="flex-1">
                    <SelectValue placeholder="Add column..." />
                  </SelectTrigger>
                  <SelectContent>
                    {columns
                      .filter((col) => !currentList.includes(col))
                      .map((col) => (
                        <SelectItem key={col} value={col}>
                          {col}
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
              ) : (
                <>
                  <Input
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        handleAddItem()
                      }
                    }}
                    placeholder={param.placeholder || 'Add value...'}
                    disabled={disabled}
                    className="flex-1"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    onClick={handleAddItem}
                    disabled={disabled || !inputValue.trim()}
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </>
              )}
            </div>
          </div>
        )

      case 'regex':
        return (
          <Input
            value={(value as string) || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={param.placeholder || 'Regular expression...'}
            disabled={disabled}
            className="font-mono text-sm"
          />
        )

      case 'expression':
        return (
          <Input
            value={(value as string) || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={param.placeholder || 'Polars expression...'}
            disabled={disabled}
            className="font-mono text-sm"
          />
        )

      case 'schema':
        return (
          <textarea
            value={typeof value === 'string' ? value : JSON.stringify(value, null, 2) || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={param.placeholder || '{\n  "column": "type"\n}'}
            disabled={disabled}
            className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            rows={4}
          />
        )

      default:
        return (
          <Input
            value={(value as string) || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={param.placeholder}
            disabled={disabled}
          />
        )
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Label htmlFor={param.name} className="text-sm font-medium">
          {param.label}
          {param.required && <span className="text-destructive ml-1">*</span>}
        </Label>
      </div>
      {param.description && (
        <p className="text-xs text-muted-foreground">{param.description}</p>
      )}
      {renderInput()}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  )
}
