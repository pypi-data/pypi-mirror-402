/**
 * SchemaVersionCompare - Full-featured schema version comparison component.
 *
 * Combines version selection with the SchemaDiffViewer for a complete
 * schema comparison experience.
 */

import { useState, useEffect, useCallback } from 'react'
import { ArrowRight, GitCompare, Loader2, RefreshCw, Eye, EyeOff } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { SchemaDiffViewer, type SchemaVersion, type ColumnDefinition } from './SchemaDiffViewer'
import { formatDate } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'

interface SchemaVersionInfo {
  id: string
  version_number: number
  column_count: number
  columns: ColumnDefinition[]
  created_at: string
  schema_hash?: string
}

interface SchemaVersionCompareProps {
  sourceId: string
  versions: SchemaVersionInfo[]
  onRefresh?: () => void
  isLoading?: boolean
}

export function SchemaVersionCompare({
  sourceId,
  versions,
  onRefresh,
  isLoading = false,
}: SchemaVersionCompareProps) {
  const { toast } = useToast()
  const [leftVersionId, setLeftVersionId] = useState<string>('')
  const [rightVersionId, setRightVersionId] = useState<string>('')
  const [showUnchanged, setShowUnchanged] = useState(false)
  const [comparing, setComparing] = useState(false)

  // Auto-select latest two versions
  useEffect(() => {
    if (versions.length >= 2 && !leftVersionId && !rightVersionId) {
      // Sort by version number descending
      const sorted = [...versions].sort((a, b) => b.version_number - a.version_number)
      setRightVersionId(sorted[0].id)
      setLeftVersionId(sorted[1].id)
    } else if (versions.length === 1 && !rightVersionId) {
      setRightVersionId(versions[0].id)
    }
  }, [versions, leftVersionId, rightVersionId])

  const leftVersion = versions.find((v) => v.id === leftVersionId)
  const rightVersion = versions.find((v) => v.id === rightVersionId)

  // Convert to SchemaDiffViewer format
  const leftSchema: SchemaVersion | null = leftVersion
    ? {
        version_number: leftVersion.version_number,
        created_at: leftVersion.created_at,
        columns: leftVersion.columns,
      }
    : null

  const rightSchema: SchemaVersion | null = rightVersion
    ? {
        version_number: rightVersion.version_number,
        created_at: rightVersion.created_at,
        columns: rightVersion.columns,
      }
    : null

  const handleSwapVersions = useCallback(() => {
    const temp = leftVersionId
    setLeftVersionId(rightVersionId)
    setRightVersionId(temp)
  }, [leftVersionId, rightVersionId])

  const getVersionLabel = (version: SchemaVersionInfo) => {
    return `v${version.version_number} (${version.column_count} cols) - ${formatDate(version.created_at)}`
  }

  if (versions.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitCompare className="h-5 w-5" />
            Compare Schema Versions
          </CardTitle>
          <CardDescription>
            No schema versions available. Run schema detection first.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {onRefresh && (
            <Button onClick={onRefresh} disabled={isLoading}>
              {isLoading ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="mr-2 h-4 w-4" />
              )}
              Detect Schema
            </Button>
          )}
        </CardContent>
      </Card>
    )
  }

  if (versions.length === 1) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitCompare className="h-5 w-5" />
            Compare Schema Versions
          </CardTitle>
          <CardDescription>
            Only one schema version exists. Run schema detection again to create a comparison point.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-4 bg-muted/50 rounded-lg">
            <p className="font-medium">Current Version: {versions[0].version_number}</p>
            <p className="text-sm text-muted-foreground">
              {versions[0].column_count} columns • {formatDate(versions[0].created_at)}
            </p>
          </div>
          {onRefresh && (
            <Button onClick={onRefresh} disabled={isLoading}>
              {isLoading ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="mr-2 h-4 w-4" />
              )}
              Detect Changes
            </Button>
          )}
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {/* Version Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitCompare className="h-5 w-5" />
            Compare Schema Versions
          </CardTitle>
          <CardDescription>
            Select two versions to compare schema changes
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-end gap-3 flex-wrap">
            <div className="flex-1 min-w-[200px] space-y-2">
              <Label>From Version</Label>
              <Select value={leftVersionId} onValueChange={setLeftVersionId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select previous version" />
                </SelectTrigger>
                <SelectContent>
                  {versions.map((v) => (
                    <SelectItem key={v.id} value={v.id} disabled={v.id === rightVersionId}>
                      {getVersionLabel(v)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Button
              variant="ghost"
              size="icon"
              onClick={handleSwapVersions}
              disabled={!leftVersionId || !rightVersionId}
              className="mb-0.5"
            >
              <ArrowRight className="h-4 w-4" />
            </Button>

            <div className="flex-1 min-w-[200px] space-y-2">
              <Label>To Version</Label>
              <Select value={rightVersionId} onValueChange={setRightVersionId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select current version" />
                </SelectTrigger>
                <SelectContent>
                  {versions.map((v) => (
                    <SelectItem key={v.id} value={v.id} disabled={v.id === leftVersionId}>
                      {getVersionLabel(v)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {onRefresh && (
              <Button
                variant="outline"
                onClick={onRefresh}
                disabled={isLoading}
                className="ml-auto"
              >
                {isLoading ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="mr-2 h-4 w-4" />
                )}
                Refresh
              </Button>
            )}
          </div>

          {/* Options */}
          <div className="flex items-center gap-6 mt-4 pt-4 border-t">
            <div className="flex items-center space-x-2">
              <Switch
                id="show-unchanged"
                checked={showUnchanged}
                onCheckedChange={setShowUnchanged}
              />
              <Label htmlFor="show-unchanged" className="flex items-center gap-2 cursor-pointer">
                {showUnchanged ? (
                  <Eye className="h-4 w-4" />
                ) : (
                  <EyeOff className="h-4 w-4" />
                )}
                Show unchanged columns
              </Label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Diff Viewer */}
      {leftVersionId && rightVersionId && (
        <SchemaDiffViewer
          leftSchema={leftSchema}
          rightSchema={rightSchema}
          showUnchanged={showUnchanged}
        />
      )}
    </div>
  )
}

export default SchemaVersionCompare
