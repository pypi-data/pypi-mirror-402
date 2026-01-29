/**
 * ValidatorSelector - Main component for selecting and configuring validators.
 *
 * Features:
 * - Category-based grouping
 * - Search and filter
 * - Per-validator parameter configuration
 * - Preset templates (All, Quick Check, Schema Only, etc.)
 * - Support for both built-in and custom validators
 */

import { useState, useMemo, useCallback, useEffect } from 'react'
import { Search, Filter, ChevronDown, ChevronRight, Zap, Shield, Database, Code, Sparkles } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ValidatorConfigCard } from './ValidatorConfigCard'
import type { ValidatorDefinition, ValidatorConfig, ValidatorCategory, UnifiedValidatorDefinition, ValidatorSource } from '@/api/client'
import {
  createEmptyConfig,
  validateConfig,
} from '@/types/validators'

// =============================================================================
// Types
// =============================================================================

interface ValidatorSelectorProps {
  /** All available validator definitions */
  validators: ValidatorDefinition[]
  /** Current validator configurations */
  configs: ValidatorConfig[]
  /** Callback when configs change */
  onChange: (configs: ValidatorConfig[]) => void
  /** Available columns from data source (for column picker) */
  columns?: string[]
  /** Validation errors by validator name */
  errors?: Record<string, Record<string, string>>
  /** Custom validators (optional) */
  customValidators?: UnifiedValidatorDefinition[]
  /** Callback when custom validator configs change (optional) */
  onCustomValidatorChange?: (configs: CustomValidatorSelectionConfig[]) => void
  /** Current custom validator selections */
  customValidatorConfigs?: CustomValidatorSelectionConfig[]
}

/** Configuration for a custom validator to be run */
export interface CustomValidatorSelectionConfig {
  validator_id: string
  validator_name: string
  column: string
  params: Record<string, unknown>
  enabled: boolean
}

interface CategoryGroup {
  category: ValidatorCategory
  label: string
  validators: ValidatorDefinition[]
  enabledCount: number
}

// =============================================================================
// Presets
// =============================================================================

const PRESETS = [
  {
    id: 'all',
    label: 'All Validators',
    icon: Zap,
    description: 'Run all available validators',
    filter: () => true,
  },
  {
    id: 'quick',
    label: 'Quick Check',
    icon: Zap,
    description: 'Fast validation for common issues',
    filter: (v: ValidatorDefinition) =>
      ['Null', 'Duplicate', 'ColumnExists', 'RowCount'].includes(v.name),
  },
  {
    id: 'schema',
    label: 'Schema Only',
    icon: Database,
    description: 'Structure and type validation',
    filter: (v: ValidatorDefinition) => v.category === 'schema',
  },
  {
    id: 'completeness',
    label: 'Data Quality',
    icon: Shield,
    description: 'Completeness and uniqueness checks',
    filter: (v: ValidatorDefinition) =>
      v.category === 'completeness' || v.category === 'uniqueness',
  },
]

// =============================================================================
// Category Labels
// =============================================================================

const CATEGORY_LABELS: Record<ValidatorCategory | 'custom', string> = {
  schema: 'Schema',
  completeness: 'Completeness',
  uniqueness: 'Uniqueness',
  distribution: 'Distribution',
  string: 'String',
  datetime: 'Datetime',
  aggregate: 'Aggregate',
  cross_table: 'Cross-Table',
  query: 'Query',
  multi_column: 'Multi-Column',
  table: 'Table',
  geospatial: 'Geospatial',
  drift: 'Drift',
  anomaly: 'Anomaly',
  custom: 'Custom Validators',
}

// =============================================================================
// Component
// =============================================================================

export function ValidatorSelector({
  validators,
  configs,
  onChange,
  columns = [],
  errors = {},
  customValidators = [],
  onCustomValidatorChange,
  customValidatorConfigs = [],
}: ValidatorSelectorProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<ValidatorCategory | 'all' | 'custom'>('all')
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set(['schema', 'completeness']))
  const [sourceFilter, setSourceFilter] = useState<ValidatorSource | 'all'>('all')

  // Initialize configs if empty
  useEffect(() => {
    if (configs.length === 0 && validators.length > 0) {
      // Start with all validators enabled by default
      const initialConfigs = validators.map((v) => createEmptyConfig(v))
      onChange(initialConfigs)
    }
  }, [validators, configs.length, onChange])

  // Get config for a validator
  const getConfig = useCallback(
    (name: string): ValidatorConfig => {
      return configs.find((c) => c.name === name) || { name, enabled: false, params: {} }
    },
    [configs]
  )

  // Update a single validator config
  const updateConfig = useCallback(
    (updatedConfig: ValidatorConfig) => {
      const newConfigs = configs.map((c) =>
        c.name === updatedConfig.name ? updatedConfig : c
      )
      // If config doesn't exist, add it
      if (!configs.find((c) => c.name === updatedConfig.name)) {
        newConfigs.push(updatedConfig)
      }
      onChange(newConfigs)
    },
    [configs, onChange]
  )

  // Apply preset
  const applyPreset = useCallback(
    (presetId: string) => {
      const preset = PRESETS.find((p) => p.id === presetId)
      if (!preset) return

      const newConfigs = validators.map((v) => {
        const config = getConfig(v.name)
        return {
          ...config,
          enabled: preset.filter(v),
        }
      })
      onChange(newConfigs)
    },
    [validators, getConfig, onChange]
  )

  // Enable/disable all in category
  const toggleCategory = useCallback(
    (category: ValidatorCategory, enabled: boolean) => {
      const newConfigs = configs.map((c) => {
        const def = validators.find((v) => v.name === c.name)
        if (def?.category === category) {
          return { ...c, enabled }
        }
        return c
      })
      onChange(newConfigs)
    },
    [configs, validators, onChange]
  )

  // Toggle category expansion
  const toggleCategoryExpansion = useCallback((category: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev)
      if (next.has(category)) {
        next.delete(category)
      } else {
        next.add(category)
      }
      return next
    })
  }, [])

  // Group validators by category
  const categoryGroups = useMemo((): CategoryGroup[] => {
    const groups: Record<ValidatorCategory, ValidatorDefinition[]> = {} as Record<
      ValidatorCategory,
      ValidatorDefinition[]
    >

    // Filter by search
    const filtered = validators.filter((v) => {
      if (!searchQuery) return true
      const query = searchQuery.toLowerCase()
      return (
        v.name.toLowerCase().includes(query) ||
        v.display_name.toLowerCase().includes(query) ||
        v.description.toLowerCase().includes(query) ||
        v.tags.some((t) => t.toLowerCase().includes(query))
      )
    })

    // Group by category
    for (const v of filtered) {
      if (!groups[v.category]) {
        groups[v.category] = []
      }
      groups[v.category].push(v)
    }

    // Convert to array and add counts
    return Object.entries(groups)
      .map(([category, vals]) => ({
        category: category as ValidatorCategory,
        label: CATEGORY_LABELS[category as ValidatorCategory] || category,
        validators: vals,
        enabledCount: vals.filter((v) => getConfig(v.name).enabled).length,
      }))
      .filter((g) => selectedCategory === 'all' || g.category === selectedCategory)
      .sort((a, b) => {
        // Sort by category order in CATEGORY_LABELS
        const order = Object.keys(CATEGORY_LABELS)
        return order.indexOf(a.category) - order.indexOf(b.category)
      })
  }, [validators, searchQuery, selectedCategory, getConfig])

  // Summary stats
  const stats = useMemo(() => {
    const builtinEnabled = configs.filter((c) => c.enabled).length
    const customEnabled = customValidatorConfigs.filter((c) => c.enabled).length
    const enabled = builtinEnabled + customEnabled
    const total = validators.length + customValidators.length
    return { enabled, total, builtinEnabled, customEnabled, builtinTotal: validators.length, customTotal: customValidators.length }
  }, [configs, validators, customValidatorConfigs, customValidators])

  // Custom validator helpers
  const getCustomConfig = useCallback(
    (validatorId: string): CustomValidatorSelectionConfig | undefined => {
      return customValidatorConfigs.find((c) => c.validator_id === validatorId)
    },
    [customValidatorConfigs]
  )

  const updateCustomConfig = useCallback(
    (config: CustomValidatorSelectionConfig) => {
      if (!onCustomValidatorChange) return
      const newConfigs = customValidatorConfigs.map((c) =>
        c.validator_id === config.validator_id ? config : c
      )
      if (!customValidatorConfigs.find((c) => c.validator_id === config.validator_id)) {
        newConfigs.push(config)
      }
      onCustomValidatorChange(newConfigs)
    },
    [customValidatorConfigs, onCustomValidatorChange]
  )

  const toggleCustomValidator = useCallback(
    (validator: UnifiedValidatorDefinition, enabled: boolean, column?: string) => {
      if (!onCustomValidatorChange || !validator.id) return
      const existing = getCustomConfig(validator.id)
      if (existing) {
        updateCustomConfig({ ...existing, enabled })
      } else {
        updateCustomConfig({
          validator_id: validator.id,
          validator_name: validator.display_name,
          column: column || columns[0] || '',
          params: {},
          enabled,
        })
      }
    },
    [onCustomValidatorChange, getCustomConfig, updateCustomConfig, columns]
  )

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex flex-wrap gap-3">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search validators..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Category filter */}
        <Select
          value={selectedCategory}
          onValueChange={(v) => setSelectedCategory(v as ValidatorCategory | 'all' | 'custom')}
        >
          <SelectTrigger className="w-[180px]">
            <Filter className="h-4 w-4 mr-2" />
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Source filter (if custom validators available) */}
        {customValidators.length > 0 && (
          <Select
            value={sourceFilter}
            onValueChange={(v) => setSourceFilter(v as ValidatorSource | 'all')}
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Source" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Sources</SelectItem>
              <SelectItem value="builtin">
                <span className="flex items-center gap-2">
                  <Database className="h-3 w-3" />
                  Built-in
                </span>
              </SelectItem>
              <SelectItem value="custom">
                <span className="flex items-center gap-2">
                  <Code className="h-3 w-3" />
                  Custom
                </span>
              </SelectItem>
            </SelectContent>
          </Select>
        )}

        {/* Stats */}
        <Badge variant="outline" className="h-10 px-3 flex items-center gap-2">
          {stats.enabled} / {stats.total} enabled
          {customValidators.length > 0 && (
            <span className="text-muted-foreground text-xs">
              ({stats.builtinEnabled} built-in, {stats.customEnabled} custom)
            </span>
          )}
        </Badge>
      </div>

      {/* Presets */}
      <Tabs defaultValue="custom" className="w-full">
        <TabsList className="w-full justify-start">
          <TabsTrigger value="custom">Custom</TabsTrigger>
          {PRESETS.map((preset) => (
            <TabsTrigger
              key={preset.id}
              value={preset.id}
              onClick={() => applyPreset(preset.id)}
            >
              <preset.icon className="h-4 w-4 mr-1" />
              {preset.label}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="custom" className="mt-4">
          {/* Validator list by category */}
          <div className="space-y-4">
            {categoryGroups.map((group) => (
              <div key={group.category} className="border rounded-lg overflow-hidden">
                {/* Category header */}
                <button
                  onClick={() => toggleCategoryExpansion(group.category)}
                  className="w-full flex items-center justify-between p-3 bg-muted/50 hover:bg-muted/80 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    {expandedCategories.has(group.category) ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                    <span className="font-medium">{group.label}</span>
                    <Badge variant="secondary">
                      {group.enabledCount} / {group.validators.length}
                    </Badge>
                  </div>
                  <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleCategory(group.category, true)}
                    >
                      Enable All
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleCategory(group.category, false)}
                    >
                      Disable All
                    </Button>
                  </div>
                </button>

                {/* Validators in category */}
                {expandedCategories.has(group.category) && (
                  <div className="p-3 space-y-2">
                    {group.validators.map((def) => (
                      <ValidatorConfigCard
                        key={def.name}
                        definition={def}
                        config={getConfig(def.name)}
                        onChange={updateConfig}
                        columns={columns}
                        errors={errors[def.name]}
                      />
                    ))}
                  </div>
                )}
              </div>
            ))}

            {categoryGroups.length === 0 && customValidators.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                No validators match your search criteria.
              </div>
            )}

            {/* Custom Validators Section */}
            {customValidators.length > 0 && (sourceFilter === 'all' || sourceFilter === 'custom') && (selectedCategory === 'all' || selectedCategory === 'custom') && (
              <div className="border rounded-lg overflow-hidden border-primary/30 bg-primary/5">
                <button
                  onClick={() => toggleCategoryExpansion('custom')}
                  className="w-full flex items-center justify-between p-3 bg-primary/10 hover:bg-primary/20 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    {expandedCategories.has('custom') ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                    <Sparkles className="h-4 w-4 text-primary" />
                    <span className="font-medium">Custom Validators</span>
                    <Badge variant="secondary" className="bg-primary/20">
                      {stats.customEnabled} / {stats.customTotal}
                    </Badge>
                  </div>
                </button>

                {expandedCategories.has('custom') && (
                  <div className="p-3 space-y-2">
                    {customValidators
                      .filter((cv) => {
                        if (!searchQuery) return true
                        const query = searchQuery.toLowerCase()
                        return (
                          cv.name.toLowerCase().includes(query) ||
                          cv.display_name.toLowerCase().includes(query) ||
                          cv.description.toLowerCase().includes(query)
                        )
                      })
                      .map((cv) => {
                        const config = cv.id ? getCustomConfig(cv.id) : undefined
                        const isEnabled = config?.enabled || false

                        return (
                          <div
                            key={cv.id}
                            className={`flex items-start gap-3 p-3 rounded-lg border transition-colors ${
                              isEnabled
                                ? 'border-primary/50 bg-primary/5'
                                : 'border-border bg-card hover:bg-muted/50'
                            }`}
                          >
                            {/* Enable/disable checkbox */}
                            <input
                              type="checkbox"
                              checked={isEnabled}
                              onChange={(e) => toggleCustomValidator(cv, e.target.checked)}
                              className="mt-1 h-4 w-4 rounded border-gray-300"
                            />

                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="font-medium">{cv.display_name}</span>
                                <Badge variant="outline" className="text-xs">
                                  <Code className="h-3 w-3 mr-1" />
                                  Custom
                                </Badge>
                                {cv.is_verified && (
                                  <Badge variant="secondary" className="text-xs bg-green-500/20 text-green-700">
                                    Verified
                                  </Badge>
                                )}
                                <Badge variant="secondary" className="text-xs">
                                  {cv.category}
                                </Badge>
                              </div>
                              <p className="text-sm text-muted-foreground mt-1">
                                {cv.description}
                              </p>

                              {/* Column selector for enabled custom validators */}
                              {isEnabled && columns.length > 0 && (
                                <div className="mt-2 flex items-center gap-2">
                                  <span className="text-xs text-muted-foreground">Target column:</span>
                                  <Select
                                    value={config?.column || ''}
                                    onValueChange={(col) => {
                                      if (config && cv.id) {
                                        updateCustomConfig({ ...config, column: col })
                                      }
                                    }}
                                  >
                                    <SelectTrigger className="h-7 w-[180px] text-xs">
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
                                </div>
                              )}

                              {/* Usage count */}
                              {cv.usage_count > 0 && (
                                <span className="text-xs text-muted-foreground mt-1 block">
                                  Used {cv.usage_count} times
                                </span>
                              )}
                            </div>
                          </div>
                        )
                      })}

                    {customValidators.filter((cv) => {
                      if (!searchQuery) return true
                      const query = searchQuery.toLowerCase()
                      return (
                        cv.name.toLowerCase().includes(query) ||
                        cv.display_name.toLowerCase().includes(query) ||
                        cv.description.toLowerCase().includes(query)
                      )
                    }).length === 0 && (
                      <div className="text-center py-4 text-muted-foreground text-sm">
                        No custom validators match your search.
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </TabsContent>

        {/* Preset tabs just show the same content with presets applied */}
        {PRESETS.map((preset) => (
          <TabsContent key={preset.id} value={preset.id} className="mt-4">
            <div className="p-4 bg-muted/30 rounded-lg mb-4">
              <p className="text-sm text-muted-foreground">{preset.description}</p>
            </div>
            <div className="space-y-4">
              {categoryGroups.map((group) => (
                <div key={group.category} className="border rounded-lg overflow-hidden">
                  <button
                    onClick={() => toggleCategoryExpansion(group.category)}
                    className="w-full flex items-center justify-between p-3 bg-muted/50 hover:bg-muted/80 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      {expandedCategories.has(group.category) ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )}
                      <span className="font-medium">{group.label}</span>
                      <Badge variant="secondary">
                        {group.enabledCount} / {group.validators.length}
                      </Badge>
                    </div>
                  </button>

                  {expandedCategories.has(group.category) && (
                    <div className="p-3 space-y-2">
                      {group.validators.map((def) => (
                        <ValidatorConfigCard
                          key={def.name}
                          definition={def}
                          config={getConfig(def.name)}
                          onChange={updateConfig}
                          columns={columns}
                          errors={errors[def.name]}
                        />
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}

export { createEmptyConfig, validateConfig }
