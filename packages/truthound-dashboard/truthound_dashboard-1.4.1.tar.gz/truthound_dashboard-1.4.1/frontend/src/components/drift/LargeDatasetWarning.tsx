/**
 * Large dataset warning component.
 *
 * Shows when a dataset is large and recommends sampling for better performance.
 */

import { useIntlayer } from 'react-intlayer'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle, Zap, Database, ChevronRight } from 'lucide-react'

interface DatasetInfo {
  baselineRows: number
  currentRows: number
  populationSize: number
  isLargeDataset: boolean
  largeDatasetThreshold: number
}

interface PerformanceEstimate {
  fullScanTimeSeconds: number
  sampledTimeSeconds: number
  speedupFactor: number
  recommendedSampleSize: number
  memoryMb: number
}

interface LargeDatasetWarningProps {
  datasetInfo: DatasetInfo
  performanceEstimate?: PerformanceEstimate | null
  onEnableSampling?: () => void
  className?: string
}

export function LargeDatasetWarning({
  datasetInfo,
  performanceEstimate,
  onEnableSampling,
  className = '',
}: LargeDatasetWarningProps) {
  const t = useIntlayer('driftMonitor')

  const formatNumber = (num: number) => {
    if (num >= 1_000_000_000) {
      return `${(num / 1_000_000_000).toFixed(1)}B`
    }
    if (num >= 1_000_000) {
      return `${(num / 1_000_000).toFixed(1)}M`
    }
    if (num >= 1_000) {
      return `${(num / 1_000).toFixed(1)}K`
    }
    return num.toString()
  }

  const formatTime = (seconds: number) => {
    if (seconds < 60) {
      return `${seconds.toFixed(0)}s`
    }
    if (seconds < 3600) {
      return `${(seconds / 60).toFixed(0)}m`
    }
    return `${(seconds / 3600).toFixed(1)}h`
  }

  if (!datasetInfo.isLargeDataset) {
    return null
  }

  return (
    <Alert variant="destructive" className={`border-yellow-500/50 bg-yellow-500/10 ${className}`}>
      <AlertTriangle className="h-5 w-5 text-yellow-500" />
      <AlertTitle className="flex items-center gap-2 text-yellow-600 dark:text-yellow-400">
        {t.largeDataset.title}
        <Badge variant="outline" className="border-yellow-500/50 text-yellow-600">
          {formatNumber(datasetInfo.populationSize)} {t.largeDataset.rows}
        </Badge>
      </AlertTitle>
      <AlertDescription className="mt-3 space-y-4">
        <p className="text-muted-foreground">{t.largeDataset.description}</p>

        {/* Performance Comparison */}
        {performanceEstimate && (
          <div className="grid grid-cols-2 gap-4 rounded-lg border border-yellow-500/20 bg-background/50 p-4">
            {/* Full Scan */}
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <Database className="h-4 w-4" />
                {t.largeDataset.fullScan}
              </div>
              <div className="flex items-center gap-3">
                <div>
                  <div className="text-lg font-semibold text-destructive">
                    {formatTime(performanceEstimate.fullScanTimeSeconds)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {t.largeDataset.estimatedTime}
                  </div>
                </div>
              </div>
            </div>

            {/* With Sampling */}
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <Zap className="h-4 w-4 text-primary" />
                {t.largeDataset.withSampling}
              </div>
              <div className="flex items-center gap-3">
                <div>
                  <div className="text-lg font-semibold text-primary">
                    {formatTime(performanceEstimate.sampledTimeSeconds)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {performanceEstimate.speedupFactor.toFixed(0)}x {t.largeDataset.faster}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Recommendations */}
        <div className="space-y-2">
          <div className="text-sm font-medium">{t.largeDataset.recommendations}</div>
          <ul className="space-y-1 text-sm text-muted-foreground">
            <li className="flex items-start gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
              {t.largeDataset.recommendation1}
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
              {t.largeDataset.recommendation2}
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
              {t.largeDataset.recommendation3}
            </li>
          </ul>
        </div>

        {/* Enable Sampling Button */}
        {onEnableSampling && (
          <Button onClick={onEnableSampling} className="w-full">
            <Zap className="mr-2 h-4 w-4" />
            {t.largeDataset.enableSampling}
            <ChevronRight className="ml-2 h-4 w-4" />
          </Button>
        )}
      </AlertDescription>
    </Alert>
  )
}

/**
 * Inline version for more compact display
 */
interface InlineLargeDatasetWarningProps {
  rowCount: number
  threshold?: number
  onEnableSampling?: () => void
}

export function InlineLargeDatasetWarning({
  rowCount,
  threshold = 10_000_000,
  onEnableSampling,
}: InlineLargeDatasetWarningProps) {
  const t = useIntlayer('driftMonitor')

  if (rowCount < threshold) {
    return null
  }

  const formatNumber = (num: number) => {
    if (num >= 1_000_000) {
      return `${(num / 1_000_000).toFixed(1)}M`
    }
    if (num >= 1_000) {
      return `${(num / 1_000).toFixed(1)}K`
    }
    return num.toString()
  }

  return (
    <div className="flex items-center gap-2 rounded-md border border-yellow-500/30 bg-yellow-500/10 px-3 py-2 text-sm">
      <AlertTriangle className="h-4 w-4 text-yellow-500" />
      <span className="text-yellow-600 dark:text-yellow-400">
        {t.largeDataset.inlineWarning.replace('{rows}', formatNumber(rowCount))}
      </span>
      {onEnableSampling && (
        <Button
          variant="link"
          size="sm"
          onClick={onEnableSampling}
          className="h-auto p-0 text-primary"
        >
          {t.largeDataset.enableSamplingShort}
        </Button>
      )}
    </div>
  )
}
