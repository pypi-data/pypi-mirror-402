/**
 * Panel showing column-level lineage with source-to-target mappings.
 *
 * Displays column transformations grouped by transformation type.
 */

import { useState, useMemo } from 'react'
import { useIntlayer } from 'react-intlayer'
import {
  ChevronDown,
  ChevronRight,
  Search,
  Columns,
  ArrowRight,
  Filter,
} from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { cn } from '@/lib/utils'
import type { ColumnMapping, ColumnTransformationType } from './column-lineage-types'

interface ColumnLineagePanelProps {
  mappings: ColumnMapping[]
  sourceNodeName?: string
  targetNodeName?: string
  onColumnClick?: (mapping: ColumnMapping) => void
  className?: string
}

// Transformation type colors
const transformationColors: Record<ColumnTransformationType, string> = {
  direct: 'bg-blue-500/20 text-blue-700 dark:text-blue-300 border-blue-500/30',
  derived: 'bg-purple-500/20 text-purple-700 dark:text-purple-300 border-purple-500/30',
  aggregated: 'bg-amber-500/20 text-amber-700 dark:text-amber-300 border-amber-500/30',
  filtered: 'bg-green-500/20 text-green-700 dark:text-green-300 border-green-500/30',
  joined: 'bg-pink-500/20 text-pink-700 dark:text-pink-300 border-pink-500/30',
  renamed: 'bg-cyan-500/20 text-cyan-700 dark:text-cyan-300 border-cyan-500/30',
  cast: 'bg-orange-500/20 text-orange-700 dark:text-orange-300 border-orange-500/30',
  computed: 'bg-indigo-500/20 text-indigo-700 dark:text-indigo-300 border-indigo-500/30',
}

export function ColumnLineagePanel({
  mappings,
  sourceNodeName,
  targetNodeName,
  onColumnClick,
  className,
}: ColumnLineagePanelProps) {
  const t = useIntlayer('lineage')

  const [searchQuery, setSearchQuery] = useState('')
  const [filterType, setFilterType] = useState<ColumnTransformationType | 'all'>('all')
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(
    new Set(['direct', 'derived', 'aggregated'])
  )

  // Filter and group mappings
  const { filteredMappings, groupedMappings } = useMemo(() => {
    let filtered = mappings

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(
        (m) =>
          m.sourceColumn.toLowerCase().includes(query) ||
          m.targetColumn.toLowerCase().includes(query)
      )
    }

    // Apply type filter
    if (filterType !== 'all') {
      filtered = filtered.filter((m) => m.transformationType === filterType)
    }

    // Group by transformation type
    const grouped = filtered.reduce(
      (acc, mapping) => {
        const type = mapping.transformationType
        if (!acc[type]) {
          acc[type] = []
        }
        acc[type].push(mapping)
        return acc
      },
      {} as Record<ColumnTransformationType, ColumnMapping[]>
    )

    return { filteredMappings: filtered, groupedMappings: grouped }
  }, [mappings, searchQuery, filterType])

  const toggleGroup = (group: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev)
      if (next.has(group)) {
        next.delete(group)
      } else {
        next.add(group)
      }
      return next
    })
  }

  const transformationTypes = Object.keys(transformationColors) as ColumnTransformationType[]

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Columns className="h-4 w-4" />
          {t.columnLineage.title}
        </CardTitle>
        {(sourceNodeName || targetNodeName) && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            {sourceNodeName && <span>{sourceNodeName}</span>}
            {sourceNodeName && targetNodeName && <ArrowRight className="h-3 w-3" />}
            {targetNodeName && <span>{targetNodeName}</span>}
          </div>
        )}
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Search and filter */}
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder={String(t.columnLineage.searchPlaceholder)}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8"
            />
          </div>
          <Select
            value={filterType}
            onValueChange={(v) => setFilterType(v as ColumnTransformationType | 'all')}
          >
            <SelectTrigger className="w-[140px]">
              <Filter className="mr-2 h-4 w-4" />
              <SelectValue placeholder={t.columnLineage.filterByType} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t.columnLineage.allTypes}</SelectItem>
              {transformationTypes.map((type) => (
                <SelectItem key={type} value={type}>
                  {t.columnLineage.transformationTypes[type]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Stats */}
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <span>
            {filteredMappings.length} {t.columnLineage.mappingsCount}
          </span>
          <span className="text-muted-foreground/50">|</span>
          <span>
            {Object.keys(groupedMappings).length} {t.columnLineage.typesCount}
          </span>
        </div>

        {/* Grouped mappings */}
        <div className="space-y-2">
          {transformationTypes.map((type) => {
            const group = groupedMappings[type]
            if (!group || group.length === 0) return null

            const isExpanded = expandedGroups.has(type)

            return (
              <div key={type} className="rounded-lg border">
                {/* Group header */}
                <button
                  onClick={() => toggleGroup(type)}
                  className="flex w-full items-center justify-between px-3 py-2 hover:bg-muted/50"
                >
                  <div className="flex items-center gap-2">
                    {isExpanded ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                    <Badge variant="outline" className={cn('text-xs', transformationColors[type])}>
                      {t.columnLineage.transformationTypes[type]}
                    </Badge>
                  </div>
                  <span className="text-xs text-muted-foreground">{group.length}</span>
                </button>

                {/* Group content */}
                {isExpanded && (
                  <div className="border-t px-3 py-2 space-y-1">
                    {group.map((mapping, idx) => (
                      <MappingRow
                        key={`${mapping.sourceColumn}-${mapping.targetColumn}-${idx}`}
                        mapping={mapping}
                        onClick={() => onColumnClick?.(mapping)}
                      />
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Empty state */}
        {filteredMappings.length === 0 && (
          <div className="py-8 text-center text-muted-foreground">
            <Columns className="mx-auto h-8 w-8 opacity-50" />
            <p className="mt-2">{t.columnLineage.noMappings}</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

interface MappingRowProps {
  mapping: ColumnMapping
  onClick?: () => void
}

function MappingRow({ mapping, onClick }: MappingRowProps) {
  return (
    <button
      onClick={onClick}
      className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-muted/50 transition-colors"
    >
      <span className="font-mono text-xs text-blue-600 dark:text-blue-400 truncate flex-1 text-left">
        {mapping.sourceColumn}
      </span>
      <ArrowRight className="h-3 w-3 text-muted-foreground flex-shrink-0" />
      <span className="font-mono text-xs text-green-600 dark:text-green-400 truncate flex-1 text-left">
        {mapping.targetColumn}
      </span>
      {mapping.expression && (
        <span className="text-xs text-muted-foreground truncate max-w-[100px]" title={mapping.expression}>
          ({mapping.expression})
        </span>
      )}
    </button>
  )
}
