/**
 * Real-time streaming chart for anomaly detection.
 *
 * Displays live time series data with anomaly markers.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useIntlayer } from 'react-intlayer'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceDot,
  Brush,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { ZoomIn, ZoomOut, RotateCcw, Pause, Play } from 'lucide-react'
import type { StreamingAlert, StreamingStatistics } from '@/api/client'

interface DataPoint {
  timestamp: string
  data: Record<string, unknown>
}

interface StreamingChartProps {
  /** Recent data points */
  dataPoints: DataPoint[]
  /** Alerts to mark on the chart */
  alerts: StreamingAlert[]
  /** Statistics for each column */
  statistics: Record<string, StreamingStatistics> | null
  /** Columns available for display */
  columns: string[]
  /** Maximum points to display */
  maxPoints?: number
  className?: string
}

export function StreamingChart({
  dataPoints,
  alerts,
  statistics,
  columns,
  maxPoints = 100,
  className,
}: StreamingChartProps) {
  const t = useIntlayer('anomaly')

  // State
  const [selectedColumn, setSelectedColumn] = useState<string>(columns[0] || '')
  const [isPaused, setIsPaused] = useState(false)
  const [zoomDomain, setZoomDomain] = useState<[number, number] | null>(null)

  // Refs
  const chartRef = useRef<HTMLDivElement>(null)
  const pausedDataRef = useRef<DataPoint[]>([])

  // Update selected column when columns change
  useEffect(() => {
    if (columns.length > 0 && !columns.includes(selectedColumn)) {
      setSelectedColumn(columns[0])
    }
  }, [columns, selectedColumn])

  // Prepare chart data
  const chartData = useMemo(() => {
    const data = isPaused ? pausedDataRef.current : dataPoints

    return data.slice(-maxPoints).map((point, index) => {
      const value = point.data[selectedColumn]
      const timestamp = new Date(point.timestamp)
      const isAnomaly = alerts.some(
        (alert) =>
          alert.timestamp === point.timestamp &&
          alert.data_point[selectedColumn] === value
      )

      return {
        index,
        time: timestamp.toLocaleTimeString(),
        timestamp: point.timestamp,
        value: typeof value === 'number' ? value : null,
        isAnomaly,
      }
    })
  }, [dataPoints, alerts, selectedColumn, maxPoints, isPaused])

  // Get anomaly points for reference dots
  const anomalyPoints = useMemo(() => {
    return chartData.filter((d) => d.isAnomaly)
  }, [chartData])

  // Store data when paused
  useEffect(() => {
    if (!isPaused) {
      pausedDataRef.current = [...dataPoints]
    }
  }, [isPaused, dataPoints])

  // Handle zoom
  const handleZoomIn = useCallback(() => {
    if (chartData.length === 0) return
    const midPoint = Math.floor(chartData.length / 2)
    const range = Math.floor(chartData.length / 4)
    setZoomDomain([Math.max(0, midPoint - range), Math.min(chartData.length - 1, midPoint + range)])
  }, [chartData.length])

  const handleZoomOut = useCallback(() => {
    setZoomDomain(null)
  }, [])

  const handleReset = useCallback(() => {
    setZoomDomain(null)
    setIsPaused(false)
    pausedDataRef.current = []
  }, [])

  // Get column statistics
  const columnStats = statistics?.[selectedColumn]

  if (columns.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="flex h-64 items-center justify-center">
          <p className="text-muted-foreground">
            {t.streaming?.noColumns ?? 'No columns to display'}
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm">
            {t.streaming?.liveChart ?? 'Live Data Stream'}
          </CardTitle>
          <div className="flex items-center gap-2">
            {/* Column selector */}
            <Select value={selectedColumn} onValueChange={setSelectedColumn}>
              <SelectTrigger className="h-8 w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {columns.map((col) => (
                  <SelectItem key={col} value={col}>
                    {col}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Control buttons */}
            <div className="flex gap-1">
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => setIsPaused(!isPaused)}
                title={isPaused ? 'Resume' : 'Pause'}
              >
                {isPaused ? (
                  <Play className="h-4 w-4" />
                ) : (
                  <Pause className="h-4 w-4" />
                )}
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={handleZoomIn}
                title="Zoom In"
              >
                <ZoomIn className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={handleZoomOut}
                title="Zoom Out"
              >
                <ZoomOut className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={handleReset}
                title="Reset"
              >
                <RotateCcw className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Stats bar */}
        {columnStats && (
          <div className="mt-2 flex flex-wrap gap-2">
            <Badge variant="outline" className="text-xs">
              Mean: {columnStats.mean.toFixed(2)}
            </Badge>
            <Badge variant="outline" className="text-xs">
              Std: {columnStats.std.toFixed(2)}
            </Badge>
            <Badge variant="outline" className="text-xs">
              Count: {columnStats.count}
            </Badge>
            {columnStats.anomaly_count > 0 && (
              <Badge variant="destructive" className="text-xs">
                Anomalies: {columnStats.anomaly_count} (
                {(columnStats.anomaly_rate * 100).toFixed(1)}%)
              </Badge>
            )}
          </div>
        )}

        {isPaused && (
          <Badge variant="secondary" className="mt-2">
            {t.streaming?.paused ?? 'Paused'} - {pausedDataRef.current.length} points
          </Badge>
        )}
      </CardHeader>

      <CardContent>
        <div ref={chartRef} className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={chartData}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="time"
                tick={{ fontSize: 10 }}
                className="fill-muted-foreground"
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fontSize: 10 }}
                className="fill-muted-foreground"
                domain={['auto', 'auto']}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--background))',
                  borderColor: 'hsl(var(--border))',
                  borderRadius: '0.5rem',
                }}
                labelStyle={{ color: 'hsl(var(--foreground))' }}
                formatter={(value: number) => [value?.toFixed(4), selectedColumn]}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="hsl(var(--primary))"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />

              {/* Anomaly markers */}
              {anomalyPoints.map((point) => (
                <ReferenceDot
                  key={`anomaly-${point.index}`}
                  x={point.time}
                  y={point.value ?? 0}
                  r={6}
                  fill="#ef4444"
                  stroke="#fff"
                  strokeWidth={2}
                />
              ))}

              {/* Brush for zoom */}
              {chartData.length > 20 && (
                <Brush
                  dataKey="time"
                  height={20}
                  stroke="hsl(var(--primary))"
                  startIndex={zoomDomain?.[0]}
                  endIndex={zoomDomain?.[1]}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
