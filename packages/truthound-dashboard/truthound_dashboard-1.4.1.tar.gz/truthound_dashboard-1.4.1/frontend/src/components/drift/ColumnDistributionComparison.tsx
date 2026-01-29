/**
 * Column distribution comparison component.
 *
 * Side-by-side histograms comparing baseline vs current distributions.
 */

import { useState, useMemo } from 'react'
import { useIntlayer } from 'react-intlayer'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  AreaChart,
  Area,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Layers } from 'lucide-react'
import { cn } from '@/lib/utils'

interface DistributionData {
  bin: string
  baseline: number
  current: number
}

interface StatValue {
  mean?: number
  std?: number
  min?: number
  max?: number
  count?: number
  [key: string]: unknown
}

interface ColumnDistributionComparisonProps {
  baselineStats: StatValue
  currentStats: StatValue
  className?: string
}

// Generate histogram data from stats
function generateHistogramData(
  baselineStats: StatValue,
  currentStats: StatValue
): DistributionData[] {
  const baselineMean = baselineStats.mean ?? 0
  const baselineStd = baselineStats.std ?? 1
  const currentMean = currentStats.mean ?? 0
  const currentStd = currentStats.std ?? 1

  // Determine range for histogram
  const minVal = Math.min(
    baselineStats.min ?? baselineMean - 3 * baselineStd,
    currentStats.min ?? currentMean - 3 * currentStd
  )
  const maxVal = Math.max(
    baselineStats.max ?? baselineMean + 3 * baselineStd,
    currentStats.max ?? currentMean + 3 * currentStd
  )

  const bins = 10
  const binWidth = (maxVal - minVal) / bins
  const data: DistributionData[] = []

  for (let i = 0; i < bins; i++) {
    const binStart = minVal + i * binWidth
    const binEnd = binStart + binWidth
    const binCenter = (binStart + binEnd) / 2

    // Generate approximate frequencies using normal distribution
    const baselineFreq = generateNormalFrequency(binCenter, baselineMean, baselineStd, baselineStats.count ?? 1000)
    const currentFreq = generateNormalFrequency(binCenter, currentMean, currentStd, currentStats.count ?? 1000)

    data.push({
      bin: formatBinLabel(binStart, binEnd),
      baseline: Math.round(baselineFreq),
      current: Math.round(currentFreq),
    })
  }

  return data
}

// Generate normal distribution frequency
function generateNormalFrequency(x: number, mean: number, std: number, total: number): number {
  if (std === 0) return x === mean ? total : 0
  const z = (x - mean) / std
  const normalPdf = (1 / (std * Math.sqrt(2 * Math.PI))) * Math.exp(-0.5 * z * z)
  return normalPdf * total * (std * 0.6) // Scale factor for bin width
}

// Format bin label
function formatBinLabel(start: number, end: number): string {
  if (Math.abs(start) >= 1000 || Math.abs(end) >= 1000) {
    return `${(start / 1000).toFixed(1)}k-${(end / 1000).toFixed(1)}k`
  }
  if (Math.abs(start) >= 1 || Math.abs(end) >= 1) {
    return `${start.toFixed(0)}-${end.toFixed(0)}`
  }
  return `${start.toFixed(2)}-${end.toFixed(2)}`
}

export function ColumnDistributionComparison({
  baselineStats,
  currentStats,
  className,
}: ColumnDistributionComparisonProps) {
  const t = useIntlayer('driftMonitor')
  const [overlayMode, setOverlayMode] = useState(false)
  const [showKDE, setShowKDE] = useState(false)

  const histogramData = useMemo(
    () => generateHistogramData(baselineStats, currentStats),
    [baselineStats, currentStats]
  )

  const CustomTooltip = ({ active, payload, label }: {
    active?: boolean
    payload?: { name: string; value: number; color: string }[]
    label?: string
  }) => {
    if (active && payload && payload.length) {
      return (
        <div className="rounded-lg border bg-background p-3 shadow-lg">
          <p className="text-sm font-medium mb-2">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value.toLocaleString()}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  return (
    <Card className={cn('', className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-medium">
            {t.columnDrilldown?.distribution ?? 'Distribution Comparison'}
          </CardTitle>
          <div className="flex items-center gap-4">
            <div className="flex items-center space-x-2">
              <Switch
                id="overlay-mode"
                checked={overlayMode}
                onCheckedChange={setOverlayMode}
              />
              <Label htmlFor="overlay-mode" className="text-xs cursor-pointer">
                <Layers className="h-3 w-3 inline mr-1" />
                {t.columnDrilldown?.overlay ?? 'Overlay'}
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <Switch
                id="kde-mode"
                checked={showKDE}
                onCheckedChange={setShowKDE}
              />
              <Label htmlFor="kde-mode" className="text-xs cursor-pointer">
                {t.columnDrilldown?.smooth ?? 'Smooth'}
              </Label>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            {showKDE ? (
              <AreaChart data={histogramData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis
                  dataKey="bin"
                  tick={{ fontSize: 10 }}
                  className="text-muted-foreground"
                  angle={-45}
                  textAnchor="end"
                  height={60}
                />
                <YAxis
                  tick={{ fontSize: 10 }}
                  className="text-muted-foreground"
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="baseline"
                  name={String(t.columnDrilldown?.baseline ?? 'Baseline')}
                  stroke="#6366f1"
                  fill="#6366f1"
                  fillOpacity={overlayMode ? 0.3 : 0.6}
                />
                <Area
                  type="monotone"
                  dataKey="current"
                  name={String(t.columnDrilldown?.current ?? 'Current')}
                  stroke="#fd9e4b"
                  fill="#fd9e4b"
                  fillOpacity={overlayMode ? 0.3 : 0.6}
                />
              </AreaChart>
            ) : (
              <BarChart data={histogramData} barCategoryGap={overlayMode ? '0%' : '10%'}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis
                  dataKey="bin"
                  tick={{ fontSize: 10 }}
                  className="text-muted-foreground"
                  angle={-45}
                  textAnchor="end"
                  height={60}
                />
                <YAxis
                  tick={{ fontSize: 10 }}
                  className="text-muted-foreground"
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Bar
                  dataKey="baseline"
                  name={String(t.columnDrilldown?.baseline ?? 'Baseline')}
                  fill="#6366f1"
                  fillOpacity={overlayMode ? 0.6 : 1}
                />
                <Bar
                  dataKey="current"
                  name={String(t.columnDrilldown?.current ?? 'Current')}
                  fill="#fd9e4b"
                  fillOpacity={overlayMode ? 0.6 : 1}
                />
              </BarChart>
            )}
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
