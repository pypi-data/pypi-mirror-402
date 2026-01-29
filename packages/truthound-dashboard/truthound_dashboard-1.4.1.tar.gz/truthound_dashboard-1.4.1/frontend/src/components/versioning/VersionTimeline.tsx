/**
 * VersionTimeline component
 *
 * Displays a visual timeline of version history with
 * clickable items to view version details.
 */

import { Link } from 'react-router-dom'
import { GitBranch, Tag, Clock, Hash } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { type VersionInfo } from '@/api/client'
import { useIntlayer } from '@/providers'
import { formatDate } from '@/lib/utils'
import { cn } from '@/lib/utils'

interface VersionTimelineProps {
  versions: VersionInfo[]
  selectedVersionId?: string
  onSelectVersion?: (version: VersionInfo) => void
  showValidationLink?: boolean
}

export function VersionTimeline({
  versions,
  selectedVersionId,
  onSelectVersion,
  showValidationLink = false,
}: VersionTimelineProps) {
  const versioning = useIntlayer('versioning')

  const getStrategyIcon = (strategy: string) => {
    switch (strategy) {
      case 'semantic':
        return <Tag className="h-4 w-4" />
      case 'timestamp':
        return <Clock className="h-4 w-4" />
      case 'gitlike':
        return <Hash className="h-4 w-4" />
      default:
        return <GitBranch className="h-4 w-4" />
    }
  }

  const getStrategyLabel = (strategy: string) => {
    switch (strategy) {
      case 'incremental':
        return versioning.strategies.incremental
      case 'semantic':
        return versioning.strategies.semantic
      case 'timestamp':
        return versioning.strategies.timestamp
      case 'gitlike':
        return versioning.strategies.gitlike
      default:
        return strategy
    }
  }

  if (versions.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        {versioning.noVersions}
      </div>
    )
  }

  return (
    <div className="relative">
      {/* Timeline line */}
      <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-border" />

      <div className="space-y-4">
        {versions.map((version, idx) => {
          const isFirst = idx === 0
          const isLast = idx === versions.length - 1
          const isSelected = version.version_id === selectedVersionId

          return (
            <div
              key={version.version_id}
              className={cn(
                'relative pl-10 cursor-pointer group',
                isSelected && 'bg-accent/50 -mx-4 px-4 pl-14 py-2 rounded-lg'
              )}
              onClick={() => onSelectVersion?.(version)}
            >
              {/* Timeline dot */}
              <div
                className={cn(
                  'absolute left-2.5 w-3 h-3 rounded-full border-2 bg-background',
                  isFirst
                    ? 'border-primary bg-primary'
                    : isSelected
                    ? 'border-primary'
                    : 'border-muted-foreground group-hover:border-primary'
                )}
              />

              <div className="flex items-start justify-between gap-4 flex-wrap">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-lg">
                      {version.version_number}
                    </span>
                    {isFirst && (
                      <Badge variant="default" className="text-xs">
                        {versioning.current}
                      </Badge>
                    )}
                    {isLast && !isFirst && (
                      <Badge variant="outline" className="text-xs">
                        {versioning.initial}
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1">
                      {getStrategyIcon(version.strategy)}
                      {getStrategyLabel(version.strategy)}
                    </span>
                    <span>{formatDate(version.created_at)}</span>
                  </div>
                  {version.content_hash && (
                    <code className="text-xs text-muted-foreground">
                      #{version.content_hash.slice(0, 8)}
                    </code>
                  )}
                </div>

                {showValidationLink && (
                  <Link
                    to={`/validations/${version.validation_id}`}
                    className="text-sm text-primary hover:underline"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {versioning.viewDetails} →
                  </Link>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default VersionTimeline
