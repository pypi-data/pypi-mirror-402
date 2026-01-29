/**
 * SchemaEvolutionTimeline - Displays schema version history as a timeline.
 */

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { SchemaChangeCard, type SchemaChange } from './SchemaChangeCard'
import {
  History,
  GitBranch,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Loader2,
} from 'lucide-react'

export interface SchemaVersionSummary {
  id: string
  version_number: number
  column_count: number
  created_at: string
}

export interface SchemaEvolutionSummary {
  source_id: string
  current_version: number
  total_versions: number
  total_changes: number
  breaking_changes: number
  last_change_at: string | null
}

interface SchemaEvolutionTimelineProps {
  sourceId: string
  summary: SchemaEvolutionSummary | null
  versions: SchemaVersionSummary[]
  changes: SchemaChange[]
  onDetectChanges?: () => Promise<void>
  isLoading?: boolean
  isDetecting?: boolean
}

export function SchemaEvolutionTimeline({
  summary,
  versions,
  changes,
  onDetectChanges,
  isLoading = false,
  isDetecting = false,
}: SchemaEvolutionTimelineProps) {
  const [expandedVersions, setExpandedVersions] = useState<Set<number>>(new Set([versions[0]?.version_number]))

  const toggleVersion = (versionNumber: number) => {
    const newExpanded = new Set(expandedVersions)
    if (newExpanded.has(versionNumber)) {
      newExpanded.delete(versionNumber)
    } else {
      newExpanded.add(versionNumber)
    }
    setExpandedVersions(newExpanded)
  }

  const getChangesForVersion = (versionId: string) => {
    return changes.filter((c) => c.id.includes(versionId) || changes.indexOf(c) < 5)
  }

  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex items-center justify-center gap-2 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span>Loading schema history...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {/* Summary Card */}
      {summary && (
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <GitBranch className="h-5 w-5 text-primary" />
                <CardTitle className="text-lg">Schema Evolution</CardTitle>
              </div>
              {onDetectChanges && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onDetectChanges}
                  disabled={isDetecting}
                >
                  {isDetecting ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Detecting...
                    </>
                  ) : (
                    <>
                      <History className="h-4 w-4 mr-2" />
                      Detect Changes
                    </>
                  )}
                </Button>
              )}
            </div>
            <CardDescription>
              Track schema changes over time
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-muted/50 rounded-lg">
                <div className="text-2xl font-bold">{summary.current_version}</div>
                <div className="text-xs text-muted-foreground">Current Version</div>
              </div>
              <div className="text-center p-3 bg-muted/50 rounded-lg">
                <div className="text-2xl font-bold">{summary.total_versions}</div>
                <div className="text-xs text-muted-foreground">Total Versions</div>
              </div>
              <div className="text-center p-3 bg-muted/50 rounded-lg">
                <div className="text-2xl font-bold">{summary.total_changes}</div>
                <div className="text-xs text-muted-foreground">Total Changes</div>
              </div>
              <div className="text-center p-3 bg-muted/50 rounded-lg">
                <div className="flex items-center justify-center gap-1">
                  {summary.breaking_changes > 0 ? (
                    <AlertTriangle className="h-5 w-5 text-red-500" />
                  ) : (
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  )}
                  <span className="text-2xl font-bold">{summary.breaking_changes}</span>
                </div>
                <div className="text-xs text-muted-foreground">Breaking Changes</div>
              </div>
            </div>
            {summary.last_change_at && (
              <p className="text-sm text-muted-foreground mt-4 text-center">
                Last change: {new Date(summary.last_change_at).toLocaleString()}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Version Timeline */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <History className="h-5 w-5" />
            Version History
          </CardTitle>
        </CardHeader>
        <CardContent>
          {versions.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No schema versions found. Run schema learning to create the first version.
            </div>
          ) : (
            <div className="relative">
              {/* Timeline line */}
              <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-border" />

              <div className="space-y-4">
                {versions.map((version, index) => {
                  const isExpanded = expandedVersions.has(version.version_number)
                  const versionChanges = getChangesForVersion(version.id)
                  const isLatest = index === 0

                  return (
                    <div key={version.id} className="relative pl-10">
                      {/* Timeline dot */}
                      <div
                        className={`absolute left-2.5 w-3 h-3 rounded-full border-2 ${
                          isLatest
                            ? 'bg-primary border-primary'
                            : 'bg-background border-muted-foreground'
                        }`}
                      />

                      <div className="bg-muted/30 rounded-lg p-3">
                        <div
                          className="flex items-center justify-between cursor-pointer"
                          onClick={() => toggleVersion(version.version_number)}
                        >
                          <div className="flex items-center gap-3">
                            <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                              {isExpanded ? (
                                <ChevronDown className="h-4 w-4" />
                              ) : (
                                <ChevronRight className="h-4 w-4" />
                              )}
                            </Button>
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-medium">Version {version.version_number}</span>
                                {isLatest && (
                                  <Badge variant="default" className="text-xs">
                                    Current
                                  </Badge>
                                )}
                              </div>
                              <p className="text-xs text-muted-foreground">
                                {version.column_count} columns
                              </p>
                            </div>
                          </div>
                          <span className="text-xs text-muted-foreground">
                            {new Date(version.created_at).toLocaleDateString()}
                          </span>
                        </div>

                        {isExpanded && versionChanges.length > 0 && (
                          <div className="mt-3 pt-3 border-t space-y-2">
                            <p className="text-xs font-medium text-muted-foreground mb-2">
                              Changes in this version:
                            </p>
                            {versionChanges.map((change) => (
                              <SchemaChangeCard key={change.id} change={change} compact />
                            ))}
                          </div>
                        )}

                        {isExpanded && versionChanges.length === 0 && index === 0 && (
                          <div className="mt-3 pt-3 border-t">
                            <p className="text-sm text-muted-foreground">
                              No changes detected in this version.
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
