/**
 * SchemaDiffViewer - Side-by-side schema comparison with diff highlighting.
 *
 * Displays two schema versions side by side, highlighting:
 * - Added columns (green)
 * - Removed columns (red)
 * - Type changes (yellow)
 * - Constraint changes
 */

import { useMemo } from 'react'
import { Plus, Minus, ArrowLeftRight, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'

export interface ColumnDefinition {
  name: string
  type: string
  nullable?: boolean
  constraints?: string[]
  description?: string
}

export interface SchemaVersion {
  version_number: number
  created_at: string
  columns: ColumnDefinition[]
}

export interface SchemaDiff {
  column: string
  change: 'added' | 'removed' | 'type_changed' | 'constraint_changed' | 'unchanged'
  oldType?: string
  newType?: string
  oldNullable?: boolean
  newNullable?: boolean
  oldConstraints?: string[]
  newConstraints?: string[]
  breaking: boolean
}

interface SchemaDiffViewerProps {
  leftSchema: SchemaVersion | null
  rightSchema: SchemaVersion | null
  showUnchanged?: boolean
  compact?: boolean
}

function computeDiff(
  left: SchemaVersion | null,
  right: SchemaVersion | null
): SchemaDiff[] {
  if (!left && !right) return []

  const leftCols = new Map(left?.columns.map((c) => [c.name, c]) ?? [])
  const rightCols = new Map(right?.columns.map((c) => [c.name, c]) ?? [])
  const allNames = new Set([...leftCols.keys(), ...rightCols.keys()])

  const diffs: SchemaDiff[] = []

  for (const name of allNames) {
    const leftCol = leftCols.get(name)
    const rightCol = rightCols.get(name)

    if (!leftCol && rightCol) {
      // Added in right
      diffs.push({
        column: name,
        change: 'added',
        newType: rightCol.type,
        newNullable: rightCol.nullable,
        newConstraints: rightCol.constraints,
        breaking: false,
      })
    } else if (leftCol && !rightCol) {
      // Removed in right
      diffs.push({
        column: name,
        change: 'removed',
        oldType: leftCol.type,
        oldNullable: leftCol.nullable,
        oldConstraints: leftCol.constraints,
        breaking: true,
      })
    } else if (leftCol && rightCol) {
      // Check for changes
      const typeChanged = leftCol.type !== rightCol.type
      const nullableChanged = leftCol.nullable !== rightCol.nullable
      const constraintsChanged =
        JSON.stringify(leftCol.constraints?.sort() ?? []) !==
        JSON.stringify(rightCol.constraints?.sort() ?? [])

      if (typeChanged) {
        diffs.push({
          column: name,
          change: 'type_changed',
          oldType: leftCol.type,
          newType: rightCol.type,
          oldNullable: leftCol.nullable,
          newNullable: rightCol.nullable,
          breaking: true, // Type changes are usually breaking
        })
      } else if (nullableChanged || constraintsChanged) {
        diffs.push({
          column: name,
          change: 'constraint_changed',
          oldType: leftCol.type,
          newType: rightCol.type,
          oldNullable: leftCol.nullable,
          newNullable: rightCol.nullable,
          oldConstraints: leftCol.constraints,
          newConstraints: rightCol.constraints,
          breaking: leftCol.nullable === true && rightCol.nullable === false,
        })
      } else {
        diffs.push({
          column: name,
          change: 'unchanged',
          oldType: leftCol.type,
          newType: rightCol.type,
          breaking: false,
        })
      }
    }
  }

  // Sort: added first, then removed, then changed, then unchanged
  const order = { added: 0, removed: 1, type_changed: 2, constraint_changed: 3, unchanged: 4 }
  diffs.sort((a, b) => order[a.change] - order[b.change] || a.column.localeCompare(b.column))

  return diffs
}

function getChangeIcon(change: SchemaDiff['change']) {
  switch (change) {
    case 'added':
      return <Plus className="h-4 w-4 text-green-600" />
    case 'removed':
      return <Minus className="h-4 w-4 text-red-600" />
    case 'type_changed':
      return <ArrowLeftRight className="h-4 w-4 text-yellow-600" />
    case 'constraint_changed':
      return <AlertTriangle className="h-4 w-4 text-orange-500" />
    default:
      return <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
  }
}

function getChangeBgColor(change: SchemaDiff['change']) {
  switch (change) {
    case 'added':
      return 'bg-green-500/10 border-green-500/30'
    case 'removed':
      return 'bg-red-500/10 border-red-500/30'
    case 'type_changed':
      return 'bg-yellow-500/10 border-yellow-500/30'
    case 'constraint_changed':
      return 'bg-orange-500/10 border-orange-500/30'
    default:
      return 'bg-muted/30 border-muted'
  }
}

export function SchemaDiffViewer({
  leftSchema,
  rightSchema,
  showUnchanged = false,
  compact = false,
}: SchemaDiffViewerProps) {
  const diffs = useMemo(
    () => computeDiff(leftSchema, rightSchema),
    [leftSchema, rightSchema]
  )

  const filteredDiffs = showUnchanged
    ? diffs
    : diffs.filter((d) => d.change !== 'unchanged')

  const stats = useMemo(() => {
    return {
      added: diffs.filter((d) => d.change === 'added').length,
      removed: diffs.filter((d) => d.change === 'removed').length,
      typeChanged: diffs.filter((d) => d.change === 'type_changed').length,
      constraintChanged: diffs.filter((d) => d.change === 'constraint_changed').length,
      unchanged: diffs.filter((d) => d.change === 'unchanged').length,
      breaking: diffs.filter((d) => d.breaking).length,
    }
  }, [diffs])

  if (!leftSchema && !rightSchema) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          Select schema versions to compare
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {/* Summary Stats */}
      <Card>
        <CardHeader className={compact ? 'py-3' : undefined}>
          <CardTitle className="flex items-center justify-between">
            <span>Schema Comparison</span>
            {stats.breaking > 0 && (
              <Badge variant="destructive" className="ml-2">
                <XCircle className="h-3 w-3 mr-1" />
                {stats.breaking} Breaking
              </Badge>
            )}
          </CardTitle>
          {!compact && (
            <CardDescription>
              {leftSchema && rightSchema
                ? `Comparing v${leftSchema.version_number} → v${rightSchema.version_number}`
                : 'Showing schema details'}
            </CardDescription>
          )}
        </CardHeader>
        <CardContent className={compact ? 'py-2' : undefined}>
          <div className="flex flex-wrap gap-3">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500" />
              <span className="text-sm">
                {stats.added} Added
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500" />
              <span className="text-sm">
                {stats.removed} Removed
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-yellow-500" />
              <span className="text-sm">
                {stats.typeChanged} Type Changed
              </span>
            </div>
            {stats.constraintChanged > 0 && (
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-orange-500" />
                <span className="text-sm">
                  {stats.constraintChanged} Constraint Changed
                </span>
              </div>
            )}
            {showUnchanged && (
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-muted" />
                <span className="text-sm">
                  {stats.unchanged} Unchanged
                </span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Side-by-side Diff */}
      <Card>
        <CardContent className="p-0 overflow-hidden">
          {/* Header Row */}
          <div className="grid grid-cols-[1fr_auto_1fr] border-b bg-muted/50">
            <div className="px-4 py-2 font-medium text-sm">
              {leftSchema ? `Version ${leftSchema.version_number}` : 'Previous'}
            </div>
            <div className="px-2 py-2 border-x bg-background" />
            <div className="px-4 py-2 font-medium text-sm">
              {rightSchema ? `Version ${rightSchema.version_number}` : 'Current'}
            </div>
          </div>

          {/* Diff Rows */}
          <div className="divide-y">
            {filteredDiffs.length === 0 ? (
              <div className="py-8 text-center text-muted-foreground">
                {showUnchanged ? 'No columns in schema' : 'No changes detected'}
              </div>
            ) : (
              filteredDiffs.map((diff) => (
                <DiffRow key={diff.column} diff={diff} compact={compact} />
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Breaking Changes Warning */}
      {stats.breaking > 0 && (
        <Card className="border-destructive/50 bg-destructive/5">
          <CardContent className="py-4">
            <div className="flex items-start gap-3">
              <XCircle className="h-5 w-5 text-destructive mt-0.5" />
              <div>
                <p className="font-medium text-destructive">
                  {stats.breaking} Breaking Change{stats.breaking > 1 ? 's' : ''} Detected
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  Breaking changes may cause downstream failures. Column removals and
                  incompatible type changes should be carefully reviewed before deployment.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function DiffRow({ diff, compact }: { diff: SchemaDiff; compact: boolean }) {
  const bgColor = getChangeBgColor(diff.change)

  return (
    <div className={cn('grid grid-cols-[1fr_auto_1fr]', bgColor)}>
      {/* Left Side */}
      <div className={cn('px-4', compact ? 'py-2' : 'py-3')}>
        {diff.change === 'added' ? (
          <span className="text-muted-foreground text-sm italic">—</span>
        ) : (
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <code className="font-mono text-sm font-medium">{diff.column}</code>
              {diff.change === 'removed' && (
                <Badge variant="destructive" className="text-xs">
                  Removed
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="font-mono text-xs">
                {diff.oldType}
              </Badge>
              {diff.oldNullable !== undefined && (
                <span className="text-xs text-muted-foreground">
                  {diff.oldNullable ? 'nullable' : 'not null'}
                </span>
              )}
            </div>
            {!compact && diff.oldConstraints && diff.oldConstraints.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1">
                {diff.oldConstraints.map((c, i) => (
                  <Badge key={i} variant="secondary" className="text-xs">
                    {c}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Center Indicator */}
      <div className="flex items-center px-3 border-x bg-background/50">
        {getChangeIcon(diff.change)}
      </div>

      {/* Right Side */}
      <div className={cn('px-4', compact ? 'py-2' : 'py-3')}>
        {diff.change === 'removed' ? (
          <span className="text-muted-foreground text-sm italic">—</span>
        ) : (
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <code className="font-mono text-sm font-medium">{diff.column}</code>
              {diff.change === 'added' && (
                <Badge className="bg-green-600 text-xs">New</Badge>
              )}
              {diff.change === 'type_changed' && (
                <Badge variant="outline" className="text-yellow-600 border-yellow-600 text-xs">
                  Type Changed
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="font-mono text-xs">
                {diff.newType}
              </Badge>
              {diff.newNullable !== undefined && (
                <span className="text-xs text-muted-foreground">
                  {diff.newNullable ? 'nullable' : 'not null'}
                </span>
              )}
            </div>
            {!compact && diff.newConstraints && diff.newConstraints.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1">
                {diff.newConstraints.map((c, i) => (
                  <Badge key={i} variant="secondary" className="text-xs">
                    {c}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default SchemaDiffViewer
