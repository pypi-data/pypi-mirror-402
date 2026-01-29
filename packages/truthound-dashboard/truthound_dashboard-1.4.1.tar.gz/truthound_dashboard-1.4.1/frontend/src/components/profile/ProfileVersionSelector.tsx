/**
 * ProfileVersionSelector - Select profiles for comparison from history.
 */

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { GitCompare, History, Loader2 } from 'lucide-react'

export interface ProfileSummary {
  id: string
  source_id: string
  row_count: number
  column_count: number
  size_bytes: number
  avg_null_pct: number
  avg_unique_pct: number
  created_at: string
}

interface ProfileVersionSelectorProps {
  profiles: ProfileSummary[]
  isLoading?: boolean
  onCompare?: (baselineId: string, currentId: string) => void
  isComparing?: boolean
  // Alternative controlled mode
  selectedIds?: string[]
  onSelectionChange?: (ids: string[]) => void
  maxSelection?: number
  // If true, renders only the table without the Card wrapper
  tableOnly?: boolean
}

export function ProfileVersionSelector({
  profiles,
  isLoading = false,
  onCompare,
  isComparing = false,
  selectedIds: controlledSelectedIds,
  onSelectionChange,
  maxSelection = 2,
  tableOnly = false,
}: ProfileVersionSelectorProps) {
  const [internalSelectedIds, setInternalSelectedIds] = useState<string[]>([])

  // Support both controlled and uncontrolled modes
  const selectedIds = controlledSelectedIds ?? internalSelectedIds
  const setSelectedIds = onSelectionChange ?? setInternalSelectedIds

  const toggleSelection = (id: string) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter((i) => i !== id))
    } else if (selectedIds.length >= maxSelection) {
      // Replace oldest selection
      setSelectedIds([...selectedIds.slice(1), id])
    } else {
      setSelectedIds([...selectedIds, id])
    }
  }

  const handleCompare = () => {
    if (selectedIds.length === 2 && onCompare) {
      // Sort by date to determine baseline (older) and current (newer)
      const sorted = selectedIds
        .map((id) => profiles.find((p) => p.id === id)!)
        .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
      onCompare(sorted[0].id, sorted[1].id)
    }
  }

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
  }

  const selectionInfo = () => {
    if (selectedIds.length === 0) return 'Select 2 profiles to compare'
    if (selectedIds.length === 1) return 'Select 1 more profile'
    return 'Ready to compare'
  }

  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex items-center justify-center gap-2 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span>Loading profile history...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (profiles.length === 0) {
    const emptyContent = (
      <div className="text-center text-muted-foreground py-8">
        <History className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p>No profile history available.</p>
        <p className="text-sm">Run profiling to create the first snapshot.</p>
      </div>
    )

    if (tableOnly) {
      return emptyContent
    }

    return (
      <Card>
        <CardContent className="py-8">
          {emptyContent}
        </CardContent>
      </Card>
    )
  }

  const tableContent = (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-12"></TableHead>
          <TableHead>Date</TableHead>
          <TableHead className="text-right">Rows</TableHead>
          <TableHead className="text-right">Columns</TableHead>
          <TableHead className="text-right">Size</TableHead>
          <TableHead className="text-right">Null %</TableHead>
          <TableHead className="text-right">Unique %</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {profiles.map((profile, index) => {
          const isSelected = selectedIds.includes(profile.id)
          const selectionOrder = selectedIds.indexOf(profile.id) + 1

          return (
            <TableRow
              key={profile.id}
              className={`cursor-pointer transition-colors ${isSelected ? 'bg-primary/5' : 'hover:bg-muted/50'}`}
              onClick={() => toggleSelection(profile.id)}
            >
              <TableCell>
                <div className="flex items-center gap-2">
                  <Checkbox
                    checked={isSelected}
                    onCheckedChange={() => toggleSelection(profile.id)}
                    onClick={(e: React.MouseEvent) => e.stopPropagation()}
                  />
                  {isSelected && (
                    <Badge variant="outline" className="text-xs">
                      {selectionOrder === 1 ? 'Baseline' : 'Current'}
                    </Badge>
                  )}
                </div>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <span className="font-medium">
                    {new Date(profile.created_at).toLocaleDateString()}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {new Date(profile.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                  {index === 0 && (
                    <Badge variant="secondary" className="text-xs">
                      Latest
                    </Badge>
                  )}
                </div>
              </TableCell>
              <TableCell className="text-right font-mono">
                {profile.row_count.toLocaleString()}
              </TableCell>
              <TableCell className="text-right font-mono">
                {profile.column_count}
              </TableCell>
              <TableCell className="text-right font-mono text-muted-foreground">
                {formatBytes(profile.size_bytes)}
              </TableCell>
              <TableCell className="text-right">
                <span className={profile.avg_null_pct > 10 ? 'text-yellow-600' : ''}>
                  {profile.avg_null_pct.toFixed(1)}%
                </span>
              </TableCell>
              <TableCell className="text-right">
                <span className={profile.avg_unique_pct < 50 ? 'text-yellow-600' : ''}>
                  {profile.avg_unique_pct.toFixed(1)}%
                </span>
              </TableCell>
            </TableRow>
          )
        })}
      </TableBody>
    </Table>
  )

  // Return just the table for controlled mode
  if (tableOnly) {
    return tableContent
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg flex items-center gap-2">
              <History className="h-5 w-5" />
              Profile History
            </CardTitle>
            <CardDescription>
              {profiles.length} profiles available. {selectionInfo()}
            </CardDescription>
          </div>
          {onCompare && (
            <Button
              onClick={handleCompare}
              disabled={selectedIds.length !== 2 || isComparing}
            >
              {isComparing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Comparing...
                </>
              ) : (
                <>
                  <GitCompare className="h-4 w-4 mr-2" />
                  Compare Selected
                </>
              )}
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {tableContent}
      </CardContent>
    </Card>
  )
}
