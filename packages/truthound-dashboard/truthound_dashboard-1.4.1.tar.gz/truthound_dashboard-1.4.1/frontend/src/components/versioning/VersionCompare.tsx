/**
 * VersionCompare component
 *
 * Displays comparison between two validation result versions,
 * showing issues added, removed, and changed.
 */

import { useState, useEffect } from 'react'
import { ArrowRight, Plus, Minus, RefreshCw, Loader2, AlertCircle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  compareVersions,
  type VersionInfo,
  type VersionDiff,
} from '@/api/client'
import { useIntlayer } from '@/providers'
import { str } from '@/lib/intlayer-utils'
import { formatDate } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'

interface VersionCompareProps {
  versions: VersionInfo[]
  sourceId: string
}

export function VersionCompare({ versions }: VersionCompareProps) {
  const versioning = useIntlayer('versioning')
  const common = useIntlayer('common')
  const { toast } = useToast()

  const [fromVersionId, setFromVersionId] = useState<string>('')
  const [toVersionId, setToVersionId] = useState<string>('')
  const [diff, setDiff] = useState<VersionDiff | null>(null)
  const [loading, setLoading] = useState(false)

  // Auto-select latest two versions
  useEffect(() => {
    if (versions.length >= 2 && !fromVersionId && !toVersionId) {
      setFromVersionId(versions[1].version_id)
      setToVersionId(versions[0].version_id)
    }
  }, [versions, fromVersionId, toVersionId])

  async function handleCompare() {
    if (!fromVersionId || !toVersionId) return
    if (fromVersionId === toVersionId) {
      toast({
        title: str(common.error),
        description: 'Please select different versions to compare',
        variant: 'destructive',
      })
      return
    }

    try {
      setLoading(true)
      const result = await compareVersions(fromVersionId, toVersionId)
      setDiff(result)
    } catch (error) {
      console.error('Compare error:', error)
      toast({
        title: str(common.error),
        description: str(versioning.compareError),
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const getVersionLabel = (version: VersionInfo) => {
    return `${version.version_number} (${formatDate(version.created_at)})`
  }

  if (versions.length < 2) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RefreshCw className="h-5 w-5" />
            {versioning.compareVersions}
          </CardTitle>
          <CardDescription>
            At least two versions are required to compare.
          </CardDescription>
        </CardHeader>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Version Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RefreshCw className="h-5 w-5" />
            {versioning.compareVersions}
          </CardTitle>
          <CardDescription>{versioning.selectVersions}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex-1 min-w-[200px]">
              <label className="text-sm font-medium mb-2 block">
                {versioning.fromVersion}
              </label>
              <Select value={fromVersionId} onValueChange={setFromVersionId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select version" />
                </SelectTrigger>
                <SelectContent>
                  {versions.map((v) => (
                    <SelectItem key={v.version_id} value={v.version_id}>
                      {getVersionLabel(v)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <ArrowRight className="h-5 w-5 text-muted-foreground hidden md:block" />

            <div className="flex-1 min-w-[200px]">
              <label className="text-sm font-medium mb-2 block">
                {versioning.toVersion}
              </label>
              <Select value={toVersionId} onValueChange={setToVersionId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select version" />
                </SelectTrigger>
                <SelectContent>
                  {versions.map((v) => (
                    <SelectItem key={v.version_id} value={v.version_id}>
                      {getVersionLabel(v)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Button
              onClick={handleCompare}
              disabled={!fromVersionId || !toVersionId || loading}
              className="mt-6"
            >
              {loading ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="mr-2 h-4 w-4" />
              )}
              {versioning.compare}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Comparison Results */}
      {diff && (
        <div className="space-y-4">
          {/* Summary */}
          <Card>
            <CardHeader>
              <CardTitle>{versioning.changeSummary}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-3">
                <div className="flex items-center gap-3 p-4 rounded-lg bg-green-500/10 border border-green-500/20">
                  <Plus className="h-6 w-6 text-green-600" />
                  <div>
                    <p className="text-2xl font-bold text-green-600">
                      {diff.issues_added.length}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {versioning.addedCount}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-4 rounded-lg bg-red-500/10 border border-red-500/20">
                  <Minus className="h-6 w-6 text-red-600" />
                  <div>
                    <p className="text-2xl font-bold text-red-600">
                      {diff.issues_removed.length}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {versioning.removedCount}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                  <AlertCircle className="h-6 w-6 text-yellow-600" />
                  <div>
                    <p className="text-2xl font-bold text-yellow-600">
                      {diff.issues_changed.length}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {versioning.changedCount}
                    </p>
                  </div>
                </div>
              </div>

              {!diff.has_changes && (
                <div className="mt-4 p-4 rounded-lg bg-muted text-center">
                  <p className="text-muted-foreground">{versioning.noChanges}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Issues Added */}
          {diff.issues_added.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-green-600">
                  <Plus className="h-5 w-5" />
                  {versioning.issuesAdded} ({diff.issues_added.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {diff.issues_added.map((issue, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 rounded-lg border border-green-500/30 bg-green-500/5"
                    >
                      <div className="flex items-center gap-3">
                        <Badge
                          variant={
                            (issue.severity as string) === 'critical'
                              ? 'critical'
                              : (issue.severity as string) === 'high'
                              ? 'high'
                              : (issue.severity as string) === 'medium'
                              ? 'medium'
                              : 'low'
                          }
                        >
                          {issue.severity as string}
                        </Badge>
                        <div>
                          <p className="font-medium">
                            {issue.column as string}: {issue.issue_type as string}
                          </p>
                          {issue.details ? (
                            <p className="text-sm text-muted-foreground">
                              {String(issue.details)}
                            </p>
                          ) : null}
                        </div>
                      </div>
                      <span className="text-sm text-muted-foreground">
                        {(issue.count as number)?.toLocaleString()} occurrences
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Issues Removed */}
          {diff.issues_removed.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-red-600">
                  <Minus className="h-5 w-5" />
                  {versioning.issuesRemoved} ({diff.issues_removed.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {diff.issues_removed.map((issue, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 rounded-lg border border-red-500/30 bg-red-500/5"
                    >
                      <div className="flex items-center gap-3">
                        <Badge
                          variant={
                            (issue.severity as string) === 'critical'
                              ? 'critical'
                              : (issue.severity as string) === 'high'
                              ? 'high'
                              : (issue.severity as string) === 'medium'
                              ? 'medium'
                              : 'low'
                          }
                        >
                          {issue.severity as string}
                        </Badge>
                        <div>
                          <p className="font-medium">
                            {issue.column as string}: {issue.issue_type as string}
                          </p>
                          {issue.details ? (
                            <p className="text-sm text-muted-foreground">
                              {String(issue.details)}
                            </p>
                          ) : null}
                        </div>
                      </div>
                      <span className="text-sm text-muted-foreground">
                        {(issue.count as number)?.toLocaleString()} occurrences
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Issues Changed */}
          {diff.issues_changed.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-yellow-600">
                  <AlertCircle className="h-5 w-5" />
                  {versioning.issuesChanged} ({diff.issues_changed.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {diff.issues_changed.map((change, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-lg border border-yellow-500/30 bg-yellow-500/5"
                    >
                      <p className="font-medium mb-2">{change.key}</p>
                      <div className="grid gap-2 sm:grid-cols-2">
                        <div className="p-2 rounded bg-background">
                          <p className="text-xs text-muted-foreground mb-1">Before</p>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">
                              {(change.from as Record<string, unknown>).severity as string}
                            </Badge>
                            <span className="text-sm">
                              {((change.from as Record<string, unknown>).count as number)?.toLocaleString()} occurrences
                            </span>
                          </div>
                        </div>
                        <div className="p-2 rounded bg-background">
                          <p className="text-xs text-muted-foreground mb-1">After</p>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">
                              {(change.to as Record<string, unknown>).severity as string}
                            </Badge>
                            <span className="text-sm">
                              {((change.to as Record<string, unknown>).count as number)?.toLocaleString()} occurrences
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}

export default VersionCompare
