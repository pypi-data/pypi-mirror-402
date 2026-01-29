/**
 * ProfileTrendChart - Displays time-series trend charts using Recharts.
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { TrendingUp, TrendingDown, Minus, BarChart3 } from 'lucide-react'
import type { TrendDirection } from './ProfileComparisonTable'

export interface ProfileTrendPoint {
  timestamp: string
  profile_id: string
  row_count: number
  avg_null_pct: number
  avg_unique_pct: number
  column_count: number
}

export interface ProfileTrendResponse {
  source_id: string
  source_name: string
  period_start: string
  period_end: string
  granularity: 'daily' | 'weekly' | 'monthly'
  data_points: ProfileTrendPoint[]
  trends: {
    row_count: TrendDirection
    null_pct: TrendDirection
    unique_pct: TrendDirection
  }
}

interface ProfileTrendChartProps {
  trend: ProfileTrendResponse
  granularity: 'daily' | 'weekly' | 'monthly'
  onGranularityChange: (granularity: 'daily' | 'weekly' | 'monthly') => void
}

export function ProfileTrendChart({
  trend,
  granularity,
  onGranularityChange,
}: ProfileTrendChartProps) {
  const TrendIcon = ({ direction }: { direction: TrendDirection }) => {
    if (direction === 'up') return <TrendingUp className="h-4 w-4 text-green-500" />
    if (direction === 'down') return <TrendingDown className="h-4 w-4 text-red-500" />
    return <Minus className="h-4 w-4 text-muted-foreground" />
  }

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp)
    if (granularity === 'daily') {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    }
    if (granularity === 'weekly') {
      return `Week ${Math.ceil(date.getDate() / 7)}`
    }
    return date.toLocaleDateString('en-US', { month: 'short' })
  }

  const chartData = trend.data_points.map((point) => ({
    ...point,
    date: formatDate(point.timestamp),
  }))

  const trendBadge = (direction: TrendDirection, label: string) => {
    const colors = {
      up: 'bg-green-500/10 text-green-500',
      down: 'bg-red-500/10 text-red-500',
      stable: 'bg-muted text-muted-foreground',
    }
    return (
      <Badge variant="outline" className={`${colors[direction]} gap-1`}>
        <TrendIcon direction={direction} />
        {label}
      </Badge>
    )
  }

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: Array<{ name: string; value: number; color: string }>; label?: string }) => {
    if (!active || !payload) return null
    return (
      <div className="bg-background border rounded-lg shadow-lg p-3">
        <p className="font-medium mb-2">{label}</p>
        {payload.map((entry, index) => (
          <div key={index} className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: entry.color }} />
            <span className="text-muted-foreground">{entry.name}:</span>
            <span className="font-medium">
              {entry.name.includes('pct') ? `${entry.value.toFixed(1)}%` : entry.value.toLocaleString()}
            </span>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-primary" />
          <span className="font-medium">Profile Trends</span>
        </div>
        <Select value={granularity} onValueChange={onGranularityChange as (value: string) => void}>
          <SelectTrigger className="w-[120px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="daily">Daily</SelectItem>
            <SelectItem value="weekly">Weekly</SelectItem>
            <SelectItem value="monthly">Monthly</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Trend Summary */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Row Count:</span>
          {trendBadge(trend.trends.row_count, trend.trends.row_count)}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Null %:</span>
          {trendBadge(trend.trends.null_pct, trend.trends.null_pct)}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Unique %:</span>
          {trendBadge(trend.trends.unique_pct, trend.trends.unique_pct)}
        </div>
      </div>

      {/* Row Count Chart */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Row Count Over Time</CardTitle>
          <CardDescription>
            {trend.data_points.length} data points from{' '}
            {new Date(trend.period_start).toLocaleDateString()} to{' '}
            {new Date(trend.period_end).toLocaleDateString()}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="date" className="text-xs" tick={{ fill: 'currentColor' }} />
                <YAxis className="text-xs" tick={{ fill: 'currentColor' }} tickFormatter={(v) => v.toLocaleString()} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="row_count"
                  name="Row Count"
                  stroke="hsl(var(--primary))"
                  strokeWidth={2}
                  dot={{ fill: 'hsl(var(--primary))', strokeWidth: 2 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Quality Metrics Chart */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Data Quality Metrics</CardTitle>
          <CardDescription>Average null and unique percentages over time</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="date" className="text-xs" tick={{ fill: 'currentColor' }} />
                <YAxis
                  className="text-xs"
                  tick={{ fill: 'currentColor' }}
                  domain={[0, 100]}
                  tickFormatter={(v) => `${v}%`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="avg_null_pct"
                  name="Avg Null %"
                  stroke="hsl(var(--destructive))"
                  strokeWidth={2}
                  dot={{ fill: 'hsl(var(--destructive))', strokeWidth: 2 }}
                />
                <Line
                  type="monotone"
                  dataKey="avg_unique_pct"
                  name="Avg Unique %"
                  stroke="hsl(142.1, 76.2%, 36.3%)"
                  strokeWidth={2}
                  dot={{ fill: 'hsl(142.1, 76.2%, 36.3%)', strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
