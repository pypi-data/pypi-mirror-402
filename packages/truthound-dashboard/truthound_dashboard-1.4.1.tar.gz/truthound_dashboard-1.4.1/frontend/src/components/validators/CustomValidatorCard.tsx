/**
 * CustomValidatorCard - Card component for custom validators in the selector
 *
 * Features:
 * - Toggle enable/disable
 * - Parameter value inputs
 * - Edit/View actions
 */

import { useState, useCallback } from 'react'
import { useIntlayer } from 'react-intlayer'
import { str } from '@/lib/intlayer-utils'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  ChevronDown,
  ChevronRight,
  Code,
  Edit,
  ShieldCheck,
} from 'lucide-react'
import type { CustomValidator, ValidatorParamDefinition } from '@/api/client'

/**
 * Configuration for a custom validator
 */
export interface CustomValidatorConfig {
  id: string
  enabled: boolean
  params: Record<string, unknown>
}

interface CustomValidatorCardProps {
  validator: CustomValidator
  config: CustomValidatorConfig
  onChange: (config: CustomValidatorConfig) => void
  onEdit?: (validator: CustomValidator) => void
  columns?: string[]
}

/**
 * Render parameter input based on type
 */
function ParamInput({
  param,
  value,
  onChange,
  columns = [],
  disabled = false,
}: {
  param: ValidatorParamDefinition
  value: unknown
  onChange: (value: unknown) => void
  columns?: string[]
  disabled?: boolean
}) {
  switch (param.type) {
    case 'boolean':
      return (
        <Select
          value={value?.toString() || 'false'}
          onValueChange={(v) => onChange(v === 'true')}
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
      )
    case 'column':
      return (
        <Select
          value={(value as string) || ''}
          onValueChange={onChange}
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
      )
    case 'select':
      return (
        <Select
          value={(value as string) || ''}
          onValueChange={onChange}
          disabled={disabled}
        >
          <SelectTrigger className="h-8 text-sm">
            <SelectValue placeholder="Select..." />
          </SelectTrigger>
          <SelectContent>
            {param.options?.map((opt) => (
              <SelectItem key={opt} value={opt}>
                {opt}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )
    case 'integer':
    case 'float':
      return (
        <Input
          type="number"
          value={value?.toString() || ''}
          onChange={(e) =>
            onChange(
              param.type === 'integer'
                ? parseInt(e.target.value, 10)
                : parseFloat(e.target.value)
            )
          }
          disabled={disabled}
          className="h-8 text-sm"
          min={param.min_value}
          max={param.max_value}
        />
      )
    default:
      return (
        <Input
          value={(value as string) || ''}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          className="h-8 text-sm"
        />
      )
  }
}

/**
 * Card for a custom validator in the selector
 */
export function CustomValidatorCard({
  validator,
  config,
  onChange,
  onEdit,
  columns = [],
}: CustomValidatorCardProps) {
  const t = useIntlayer('plugins')
  const [isExpanded, setIsExpanded] = useState(false)

  const hasParams = validator.parameters && validator.parameters.length > 0

  // Handle toggle
  const handleToggle = useCallback(
    (enabled: boolean) => {
      onChange({ ...config, enabled })
    },
    [config, onChange]
  )

  // Handle param change
  const handleParamChange = useCallback(
    (paramName: string, value: unknown) => {
      onChange({
        ...config,
        params: { ...config.params, [paramName]: value },
      })
    },
    [config, onChange]
  )

  return (
    <Card className={config.enabled ? 'border-primary/50' : 'opacity-70'}>
      <CardHeader className="py-2 px-3">
        <div className="flex items-center gap-3">
          {/* Enable toggle */}
          <Switch
            checked={config.enabled}
            onCheckedChange={handleToggle}
          />

          {/* Expand toggle */}
          {hasParams && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1 hover:bg-muted rounded"
            >
              {isExpanded ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
            </button>
          )}

          {/* Validator info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <Code className="w-4 h-4 text-primary shrink-0" />
              <span className="font-medium text-sm truncate">
                {validator.display_name}
              </span>
              {validator.is_verified && (
                <ShieldCheck className="w-4 h-4 text-green-500" />
              )}
            </div>
            <p className="text-xs text-muted-foreground truncate mt-0.5">
              {validator.description}
            </p>
          </div>

          {/* Badges */}
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {validator.category}
            </Badge>
            <Badge
              variant={
                validator.severity === 'error'
                  ? 'destructive'
                  : validator.severity === 'warning'
                  ? 'default'
                  : 'secondary'
              }
              className="text-xs"
            >
              {validator.severity}
            </Badge>
          </div>

          {/* Edit button */}
          {onEdit && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onEdit(validator)}
              className="h-7 w-7 p-0"
            >
              <Edit className="w-4 h-4" />
            </Button>
          )}
        </div>
      </CardHeader>

      {/* Parameters */}
      {hasParams && isExpanded && (
        <Collapsible open={isExpanded}>
          <CollapsibleContent>
            <CardContent className="pt-0 pb-3 px-3 border-t mt-2">
              <div className="grid grid-cols-2 gap-3 mt-3">
                {validator.parameters.map((param) => (
                  <div key={param.name} className="space-y-1">
                    <Label className="text-xs">
                      {param.name}
                      {param.required && (
                        <span className="text-destructive ml-1">*</span>
                      )}
                    </Label>
                    <ParamInput
                      param={param}
                      value={config.params[param.name] ?? param.default}
                      onChange={(v) => handleParamChange(param.name, v)}
                      columns={columns}
                      disabled={!config.enabled}
                    />
                    {param.description && (
                      <p className="text-xs text-muted-foreground">
                        {param.description}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </CollapsibleContent>
        </Collapsible>
      )}
    </Card>
  )
}

export default CustomValidatorCard
