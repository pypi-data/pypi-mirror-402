/**
 * Dynamic configuration form for anomaly detection algorithms.
 *
 * Renders form fields based on algorithm parameter definitions.
 */

import { useIntlayer } from 'react-intlayer'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import type { AlgorithmParameter, AlgorithmInfo, AnomalyDetectionConfig } from '@/api/client'

interface AlgorithmConfigFormProps {
  algorithm: AlgorithmInfo
  config: AnomalyDetectionConfig
  onChange: (config: AnomalyDetectionConfig) => void
  availableColumns: string[]
}

export function AlgorithmConfigForm({
  algorithm,
  config,
  onChange,
  availableColumns,
}: AlgorithmConfigFormProps) {
  const t = useIntlayer('anomaly')
  const parameters = algorithm.parameters

  const handleParamChange = (name: string, value: unknown) => {
    onChange({
      ...config,
      params: { ...config.params, [name]: value },
    })
  }

  const handleColumnsChange = (columns: string[]) => {
    onChange({ ...config, columns })
  }

  return (
    <div className="space-y-6">
      {/* Column Selection */}
      {availableColumns.length > 0 && (
        <div className="space-y-2">
          <Label>{t.selectColumns}</Label>
          <div className="flex flex-wrap gap-2">
            {availableColumns.map((col) => (
              <button
                key={col}
                type="button"
                onClick={() => {
                  const isSelected = config.columns.includes(col)
                  handleColumnsChange(
                    isSelected
                      ? config.columns.filter((c: string) => c !== col)
                      : [...config.columns, col]
                  )
                }}
                className={`rounded-md border px-2 py-1 text-xs transition-colors ${
                  config.columns.includes(col)
                    ? 'border-primary bg-primary/10 text-primary'
                    : 'border-muted-foreground/20 hover:bg-accent'
                }`}
              >
                {col}
              </button>
            ))}
          </div>
          <p className="text-xs text-muted-foreground">{t.allNumericColumns}</p>
        </div>
      )}

      {/* Algorithm Parameters */}
      {parameters.length === 0 ? (
        <p className="text-sm text-muted-foreground">{t.defaultConfig}</p>
      ) : (
        <div className="space-y-4">
          {parameters.map((param) => (
            <ParameterInput
              key={param.name}
              parameter={param}
              value={config.params?.[param.name] ?? param.default}
              onChange={(value) => handleParamChange(param.name, value)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

interface ParameterInputProps {
  parameter: AlgorithmParameter
  value: unknown
  onChange: (value: unknown) => void
}

function ParameterInput({ parameter, value, onChange }: ParameterInputProps) {
  switch (parameter.type) {
    case 'integer':
      return (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor={parameter.name}>{parameter.label}</Label>
            <span className="text-sm text-muted-foreground">{value as number}</span>
          </div>
          {parameter.min_value !== null && parameter.max_value !== null ? (
            <Slider
              id={parameter.name}
              min={parameter.min_value}
              max={parameter.max_value}
              step={1}
              value={[value as number]}
              onValueChange={(values: number[]) => onChange(values[0])}
            />
          ) : (
            <Input
              id={parameter.name}
              type="number"
              value={value as number}
              onChange={(e) => onChange(parseInt(e.target.value))}
            />
          )}
          <p className="text-xs text-muted-foreground">{parameter.description}</p>
        </div>
      )

    case 'float':
      return (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor={parameter.name}>{parameter.label}</Label>
            <span className="text-sm text-muted-foreground">
              {(value as number).toFixed(2)}
            </span>
          </div>
          {parameter.min_value !== null && parameter.max_value !== null ? (
            <Slider
              id={parameter.name}
              min={parameter.min_value}
              max={parameter.max_value}
              step={0.01}
              value={[value as number]}
              onValueChange={(values: number[]) => onChange(values[0])}
            />
          ) : (
            <Input
              id={parameter.name}
              type="number"
              step="0.01"
              value={value as number}
              onChange={(e) => onChange(parseFloat(e.target.value))}
            />
          )}
          <p className="text-xs text-muted-foreground">{parameter.description}</p>
        </div>
      )

    case 'select':
      return (
        <div className="space-y-2">
          <Label htmlFor={parameter.name}>{parameter.label}</Label>
          <Select
            value={value as string}
            onValueChange={onChange}
          >
            <SelectTrigger id={parameter.name}>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {parameter.options?.map((option) => (
                <SelectItem key={option} value={option}>
                  {option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="text-xs text-muted-foreground">{parameter.description}</p>
        </div>
      )

    case 'boolean':
      return (
        <div className="flex items-center justify-between space-y-0">
          <div>
            <Label htmlFor={parameter.name}>{parameter.label}</Label>
            <p className="text-xs text-muted-foreground">{parameter.description}</p>
          </div>
          <input
            id={parameter.name}
            type="checkbox"
            checked={value as boolean}
            onChange={(e) => onChange(e.target.checked)}
            className="h-4 w-4"
          />
        </div>
      )

    default:
      return (
        <div className="space-y-2">
          <Label htmlFor={parameter.name}>{parameter.label}</Label>
          <Input
            id={parameter.name}
            value={value as string}
            onChange={(e) => onChange(e.target.value)}
          />
          <p className="text-xs text-muted-foreground">{parameter.description}</p>
        </div>
      )
  }
}
