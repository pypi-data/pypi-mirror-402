/**
 * SourceTypeSelector - Grid-based source type selection
 */

import { useMemo } from 'react'
import {
  Database,
  FileSpreadsheet,
  Cloud,
  Layers,
  Snowflake,
  Zap,
  type LucideIcon,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { SourceTypeDefinition, SourceCategory } from '@/api/client'

interface SourceTypeSelectorProps {
  sourceTypes: SourceTypeDefinition[]
  selectedType: string | null
  onSelect: (type: string) => void
  categoryFilter?: SourceCategory | null
}

// Icon mapping for source types
const SOURCE_ICONS: Record<string, LucideIcon> = {
  file: FileSpreadsheet,
  database: Database,
  cloud: Cloud,
  snowflake: Snowflake,
  layers: Layers,
  zap: Zap,
}

// Category labels and icons
const CATEGORY_CONFIG: Record<
  SourceCategory,
  { label: string; icon: LucideIcon; color: string }
> = {
  file: { label: 'Files', icon: FileSpreadsheet, color: 'text-blue-500' },
  database: { label: 'Databases', icon: Database, color: 'text-green-500' },
  warehouse: { label: 'Data Warehouses', icon: Cloud, color: 'text-purple-500' },
  bigdata: { label: 'Big Data', icon: Layers, color: 'text-orange-500' },
}

export function SourceTypeSelector({
  sourceTypes,
  selectedType,
  onSelect,
  categoryFilter,
}: SourceTypeSelectorProps) {
  // Group source types by category
  const groupedTypes = useMemo(() => {
    const groups: Record<SourceCategory, SourceTypeDefinition[]> = {
      file: [],
      database: [],
      warehouse: [],
      bigdata: [],
    }

    for (const sourceType of sourceTypes) {
      if (groups[sourceType.category]) {
        groups[sourceType.category].push(sourceType)
      }
    }

    return groups
  }, [sourceTypes])

  // Filter by category if specified
  const categoriesToShow = categoryFilter
    ? [categoryFilter]
    : (Object.keys(CATEGORY_CONFIG) as SourceCategory[])

  return (
    <div className="space-y-6">
      {categoriesToShow.map((category) => {
        const types = groupedTypes[category]
        if (types.length === 0) return null

        const config = CATEGORY_CONFIG[category]
        const CategoryIcon = config.icon

        return (
          <div key={category} className="space-y-3">
            <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <CategoryIcon className={cn('h-4 w-4', config.color)} />
              <span>{config.label}</span>
              <span className="text-xs">({types.length})</span>
            </div>

            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
              {types.map((sourceType) => {
                const Icon = SOURCE_ICONS[sourceType.icon] || Database
                const isSelected = selectedType === sourceType.type

                return (
                  <button
                    key={sourceType.type}
                    type="button"
                    onClick={() => onSelect(sourceType.type)}
                    className={cn(
                      'group relative flex flex-col items-center gap-2 rounded-lg border p-4 transition-all',
                      'hover:border-primary/50 hover:bg-accent/50',
                      isSelected
                        ? 'border-primary bg-primary/10 ring-1 ring-primary'
                        : 'border-border bg-card'
                    )}
                  >
                    <div
                      className={cn(
                        'flex h-10 w-10 items-center justify-center rounded-lg',
                        isSelected
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted text-muted-foreground group-hover:bg-primary/20'
                      )}
                    >
                      <Icon className="h-5 w-5" />
                    </div>

                    <div className="text-center">
                      <div className="text-sm font-medium">{sourceType.name}</div>
                      <div className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">
                        {sourceType.description}
                      </div>
                    </div>

                    {/* Selected indicator */}
                    {isSelected && (
                      <div className="absolute right-2 top-2 h-2 w-2 rounded-full bg-primary" />
                    )}
                  </button>
                )
              })}
            </div>
          </div>
        )
      })}
    </div>
  )
}
