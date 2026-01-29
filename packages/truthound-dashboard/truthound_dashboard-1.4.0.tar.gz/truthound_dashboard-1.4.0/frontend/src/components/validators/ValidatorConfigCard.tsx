/**
 * ValidatorConfigCard - Configuration card for a single validator.
 *
 * Displays validator info and parameter inputs in a collapsible card.
 */

import { useState } from 'react'
import { ChevronDown, ChevronRight, Settings2 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ValidatorParamInput } from './ValidatorParamInput'
import type { ValidatorDefinition, ValidatorConfig } from '@/api/client'

interface ValidatorConfigCardProps {
  definition: ValidatorDefinition
  config: ValidatorConfig
  onChange: (config: ValidatorConfig) => void
  columns?: string[]
  errors?: Record<string, string>
}

export function ValidatorConfigCard({
  definition,
  config,
  onChange,
  columns = [],
  errors = {},
}: ValidatorConfigCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const hasParams = definition.parameters.length > 0
  const hasErrors = Object.keys(errors).length > 0
  const hasConfiguredParams = Object.keys(config.params).some(
    (key) => config.params[key] !== undefined && config.params[key] !== null && config.params[key] !== ''
  )

  const handleToggleEnabled = (enabled: boolean) => {
    onChange({ ...config, enabled })
  }

  const handleParamChange = (paramName: string, value: unknown) => {
    onChange({
      ...config,
      params: { ...config.params, [paramName]: value },
    })
  }

  const severityColors = {
    low: 'bg-blue-500/10 text-blue-500',
    medium: 'bg-yellow-500/10 text-yellow-500',
    high: 'bg-orange-500/10 text-orange-500',
    critical: 'bg-red-500/10 text-red-500',
  }

  return (
    <Card className={`transition-all ${!config.enabled ? 'opacity-60' : ''}`}>
      <CardHeader className="py-3 px-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Switch
              checked={config.enabled}
              onCheckedChange={handleToggleEnabled}
              aria-label={`Enable ${definition.display_name}`}
            />
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <span className="font-medium text-sm">{definition.display_name}</span>
                <Badge
                  variant="outline"
                  className={severityColors[definition.severity_default]}
                >
                  {definition.severity_default}
                </Badge>
                {hasConfiguredParams && (
                  <Badge variant="secondary" className="gap-1">
                    <Settings2 className="h-3 w-3" />
                    Configured
                  </Badge>
                )}
                {hasErrors && (
                  <Badge variant="destructive">
                    {Object.keys(errors).length} error(s)
                  </Badge>
                )}
              </div>
              <CardDescription className="text-xs mt-0.5">
                {definition.description}
              </CardDescription>
            </div>
          </div>
          {hasParams && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="h-8 w-8 p-0"
            >
              {isExpanded ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </Button>
          )}
        </div>
      </CardHeader>
      {hasParams && isExpanded && (
        <CardContent className="pt-0 pb-4 px-4">
          <div className="grid gap-4 pl-9">
            {definition.parameters.map((param) => {
              // Check if this param should be shown based on dependency
              if (param.depends_on) {
                const depValue = config.params[param.depends_on]
                if (depValue !== param.depends_value) {
                  return null
                }
              }

              return (
                <ValidatorParamInput
                  key={param.name}
                  param={param}
                  value={config.params[param.name]}
                  onChange={(value) => handleParamChange(param.name, value)}
                  error={errors[param.name]}
                  columns={columns}
                  disabled={!config.enabled}
                />
              )
            })}
          </div>
        </CardContent>
      )}
    </Card>
  )
}
