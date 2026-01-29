/**
 * PatternResultsDisplay Component
 *
 * Displays detected patterns for a column profile.
 * Shows pattern badges, confidence scores, and match statistics.
 */
import { useIntlayer } from 'react-intlayer'
import {
  Mail,
  Phone,
  Key,
  Link,
  Globe,
  CreditCard,
  Calendar,
  Clock,
  User,
  MapPin,
  DollarSign,
  Percent,
  FileText,
  type LucideIcon,
} from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { str } from '@/lib/intlayer-utils'

// Fallback labels for pattern types
const PATTERN_LABELS: Record<string, string> = {
  email: 'Email',
  phone: 'Phone',
  uuid: 'UUID',
  url: 'URL',
  ip_address: 'IP Address',
  credit_card: 'Credit Card',
  date: 'Date',
  datetime: 'DateTime',
  korean_rrn: 'Korean RRN',
  korean_phone: 'Korean Phone',
  ssn: 'SSN',
  postal_code: 'Postal Code',
  currency: 'Currency',
  percentage: 'Percentage',
}

// Fallback labels for UI text
const FALLBACK_LABELS = {
  matchCount: 'Matches',
  matchPercentage: 'Match %',
  sampleMatches: 'Sample Matches',
  detectedPatterns: 'Detected Patterns',
  inferredType: 'Inferred Type',
  primaryPattern: 'Primary',
  patternConfidence: 'confidence',
  patternsSummary: 'Patterns Detected Summary',
  columnsWithPatterns: 'Columns with Patterns',
}

// Pattern type to icon mapping
const PATTERN_ICONS: Record<string, LucideIcon> = {
  email: Mail,
  phone: Phone,
  uuid: Key,
  url: Link,
  ip_address: Globe,
  credit_card: CreditCard,
  date: Calendar,
  datetime: Clock,
  korean_rrn: User,
  korean_phone: Phone,
  ssn: User,
  postal_code: MapPin,
  currency: DollarSign,
  percentage: Percent,
}

// Pattern type to color mapping
const PATTERN_COLORS: Record<string, string> = {
  email: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
  phone: 'bg-green-500/10 text-green-500 border-green-500/20',
  uuid: 'bg-purple-500/10 text-purple-500 border-purple-500/20',
  url: 'bg-cyan-500/10 text-cyan-500 border-cyan-500/20',
  ip_address: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
  credit_card: 'bg-red-500/10 text-red-500 border-red-500/20',
  date: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
  datetime: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
  korean_rrn: 'bg-pink-500/10 text-pink-500 border-pink-500/20',
  korean_phone: 'bg-green-500/10 text-green-500 border-green-500/20',
  ssn: 'bg-pink-500/10 text-pink-500 border-pink-500/20',
  postal_code: 'bg-teal-500/10 text-teal-500 border-teal-500/20',
  currency: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
  percentage: 'bg-indigo-500/10 text-indigo-500 border-indigo-500/20',
}

export interface DetectedPattern {
  patternType: string
  confidence: number
  matchCount: number
  matchPercentage: number
  sampleMatches?: string[] | null
}

interface PatternBadgeProps {
  pattern: DetectedPattern
  showConfidence?: boolean
}

export function PatternBadge({ pattern, showConfidence = true }: PatternBadgeProps) {
  const t = useIntlayer('profiler')
  const Icon = PATTERN_ICONS[pattern.patternType] || FileText
  const colorClass = PATTERN_COLORS[pattern.patternType] || 'bg-gray-500/10 text-gray-500 border-gray-500/20'

  // Type-safe string extraction helper
  const safeStr = (value: unknown): string => {
    if (value === undefined || value === null) return ''
    if (typeof value === 'string') return value
    return str(value as Parameters<typeof str>[0])
  }

  // Helper to get pattern label with fallback
  const getPatternLabel = (patternType: string): string => {
    try {
      const patterns = (t as Record<string, unknown>).patterns as Record<string, unknown> | undefined
      if (patterns && patternType in patterns) {
        return safeStr(patterns[patternType])
      }
    } catch {
      // Fallback on error
    }
    return PATTERN_LABELS[patternType] || patternType
  }

  // Helper to get UI text with fallback
  const getText = (key: keyof typeof FALLBACK_LABELS): string => {
    try {
      const value = (t as Record<string, unknown>)[key]
      if (value !== undefined && value !== null) {
        return safeStr(value)
      }
    } catch {
      // Fallback on error
    }
    return FALLBACK_LABELS[key]
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge variant="outline" className={`${colorClass} gap-1`}>
            <Icon className="h-3 w-3" />
            {getPatternLabel(pattern.patternType)}
            {showConfidence && (
              <span className="ml-1 opacity-70">
                {(pattern.confidence * 100).toFixed(0)}%
              </span>
            )}
          </Badge>
        </TooltipTrigger>
        <TooltipContent>
          <div className="space-y-1 text-sm">
            <p>
              <strong>{getText('matchCount')}:</strong> {pattern.matchCount.toLocaleString()}
            </p>
            <p>
              <strong>{getText('matchPercentage')}:</strong> {pattern.matchPercentage.toFixed(1)}%
            </p>
            {pattern.sampleMatches && pattern.sampleMatches.length > 0 && (
              <div>
                <strong>{getText('sampleMatches')}:</strong>
                <ul className="mt-1 text-xs text-muted-foreground">
                  {pattern.sampleMatches.slice(0, 3).map((match, i) => (
                    <li key={i} className="truncate max-w-[200px]">
                      {match}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

interface PatternResultsDisplayProps {
  patterns: DetectedPattern[]
  primaryPattern?: string | null
  inferredType?: string | null
  compact?: boolean
}

export function PatternResultsDisplay({
  patterns,
  primaryPattern,
  inferredType,
  compact = false,
}: PatternResultsDisplayProps) {
  const t = useIntlayer('profiler')

  // Type-safe string extraction helper
  const safeStr = (value: unknown): string => {
    if (value === undefined || value === null) return ''
    if (typeof value === 'string') return value
    return str(value as Parameters<typeof str>[0])
  }

  // Helper to get pattern label with fallback
  const getPatternLabel = (patternType: string): string => {
    try {
      const patternsObj = (t as Record<string, unknown>).patterns as Record<string, unknown> | undefined
      if (patternsObj && patternType in patternsObj) {
        return safeStr(patternsObj[patternType])
      }
    } catch {
      // Fallback on error
    }
    return PATTERN_LABELS[patternType] || patternType
  }

  // Helper to get UI text with fallback
  const getText = (key: keyof typeof FALLBACK_LABELS): string => {
    try {
      const value = (t as Record<string, unknown>)[key]
      if (value !== undefined && value !== null) {
        return safeStr(value)
      }
    } catch {
      // Fallback on error
    }
    return FALLBACK_LABELS[key]
  }

  if (!patterns || patterns.length === 0) {
    return null
  }

  // Sort patterns by confidence (descending)
  const sortedPatterns = [...patterns].sort((a, b) => b.confidence - a.confidence)

  if (compact) {
    return (
      <div className="flex flex-wrap gap-1">
        {sortedPatterns.slice(0, 3).map((pattern) => (
          <PatternBadge key={pattern.patternType} pattern={pattern} />
        ))}
        {sortedPatterns.length > 3 && (
          <Badge variant="outline" className="bg-muted">
            +{sortedPatterns.length - 3}
          </Badge>
        )}
      </div>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          {getText('detectedPatterns')}
          {inferredType && (
            <Badge variant="secondary" className="ml-auto">
              {getText('inferredType')}: {inferredType}
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {sortedPatterns.map((pattern) => {
          const Icon = PATTERN_ICONS[pattern.patternType] || FileText
          const isPrimary = pattern.patternType === primaryPattern

          return (
            <div
              key={pattern.patternType}
              className={`p-3 rounded-lg border ${
                isPrimary
                  ? 'border-primary/50 bg-primary/5'
                  : 'border-border bg-muted/30'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Icon className="h-4 w-4" />
                  <span className="font-medium">
                    {getPatternLabel(pattern.patternType)}
                  </span>
                  {isPrimary && (
                    <Badge variant="default" className="text-xs">
                      {getText('primaryPattern')}
                    </Badge>
                  )}
                </div>
                <span className="text-sm font-medium">
                  {(pattern.confidence * 100).toFixed(1)}% {getText('patternConfidence')}
                </span>
              </div>
              <Progress value={pattern.matchPercentage} className="h-2 mb-2" />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>
                  {pattern.matchCount.toLocaleString()} {getText('matchCount')}
                </span>
                <span>{pattern.matchPercentage.toFixed(1)}% {getText('matchPercentage')}</span>
              </div>
              {pattern.sampleMatches && pattern.sampleMatches.length > 0 && (
                <div className="mt-2 pt-2 border-t">
                  <p className="text-xs text-muted-foreground mb-1">
                    {getText('sampleMatches')}:
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {pattern.sampleMatches.slice(0, 3).map((match, i) => (
                      <code
                        key={i}
                        className="text-xs bg-muted px-1.5 py-0.5 rounded truncate max-w-[150px]"
                      >
                        {match}
                      </code>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}

// Summary component for all columns
interface PatternsSummaryProps {
  summary: Record<string, number>
}

export function PatternsSummary({ summary }: PatternsSummaryProps) {
  const t = useIntlayer('profiler')
  const entries = Object.entries(summary).sort((a, b) => b[1] - a[1])

  // Type-safe string extraction helper
  const safeStr = (value: unknown): string => {
    if (value === undefined || value === null) return ''
    if (typeof value === 'string') return value
    return str(value as Parameters<typeof str>[0])
  }

  // Helper to get pattern label with fallback
  const getPatternLabel = (patternType: string): string => {
    try {
      const patternsObj = (t as Record<string, unknown>).patterns as Record<string, unknown> | undefined
      if (patternsObj && patternType in patternsObj) {
        return safeStr(patternsObj[patternType])
      }
    } catch {
      // Fallback on error
    }
    return PATTERN_LABELS[patternType] || patternType
  }

  // Helper to get UI text with fallback
  const getText = (key: keyof typeof FALLBACK_LABELS): string => {
    try {
      const value = (t as Record<string, unknown>)[key]
      if (value !== undefined && value !== null) {
        return safeStr(value)
      }
    } catch {
      // Fallback on error
    }
    return FALLBACK_LABELS[key]
  }

  if (entries.length === 0) {
    return null
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium">
          {getText('patternsSummary')}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2">
          {entries.map(([pattern, count]) => {
            const Icon = PATTERN_ICONS[pattern] || FileText
            const colorClass =
              PATTERN_COLORS[pattern] ||
              'bg-gray-500/10 text-gray-500 border-gray-500/20'

            return (
              <Badge
                key={pattern}
                variant="outline"
                className={`${colorClass} gap-1`}
              >
                <Icon className="h-3 w-3" />
                {getPatternLabel(pattern)}
                <span className="ml-1 font-bold">{count}</span>
              </Badge>
            )
          })}
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          {getText('columnsWithPatterns')}: {entries.reduce((sum, [, count]) => sum + count, 0)}
        </p>
      </CardContent>
    </Card>
  )
}
