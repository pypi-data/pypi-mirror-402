/**
 * Profile Comparison Page
 *
 * Compare profile snapshots over time, visualize trends,
 * and track data quality changes.
 */

import { useEffect, useState, useCallback } from 'react'
import { useIntlayer } from 'react-intlayer'
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Minus,
  Calendar,
  RefreshCw,
  Database,
  ArrowUpDown,
  Activity,
} from 'lucide-react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useToast } from '@/hooks/use-toast'
import { str } from '@/lib/intlayer-utils'
import {
  listSources,
  listProfiles,
  compareProfiles,
  getProfileTrend,
  getLatestProfileComparison,
  type Source,
  type ProfileSummary,
  type ProfileComparisonResponse,
  type ProfileTrendResponse,
  type ColumnComparison,
  type TrendDirection,
} from '@/api/client'

// Trend icon component
function TrendIcon({ direction }: { direction: TrendDirection }) {
  if (direction === 'up') {
    return <TrendingUp className="h-4 w-4 text-green-500" />
  }
  if (direction === 'down') {
    return <TrendingDown className="h-4 w-4 text-red-500" />
  }
  return <Minus className="h-4 w-4 text-muted-foreground" />
}

// Format bytes to human readable
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
}

// Format percentage change
function formatChange(value: number | null, isPct: boolean = false): string {
  if (value === null) return '-'
  const sign = value > 0 ? '+' : ''
  const formatted = isPct ? `${sign}${value.toFixed(1)}%` : `${sign}${value.toLocaleString()}`
  return formatted
}

// Stats Card
function StatsCard({
  title,
  value,
  change,
  icon: Icon,
  variant = 'default',
}: {
  title: string
  value: number | string
  change?: number | null
  icon: typeof Activity
  variant?: 'default' | 'success' | 'warning' | 'danger'
}) {
  const variantStyles = {
    default: 'text-primary',
    success: 'text-green-500',
    warning: 'text-amber-500',
    danger: 'text-red-500',
  }

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className={`text-2xl font-bold ${variantStyles[variant]}`}>{value}</p>
            {change !== undefined && change !== null && (
              <p className={`text-sm ${change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                {formatChange(change, true)}
              </p>
            )}
          </div>
          <Icon className={`h-8 w-8 ${variantStyles[variant]} opacity-50`} />
        </div>
      </CardContent>
    </Card>
  )
}

// Column Comparison Row
function ComparisonRow({ comparison }: { comparison: ColumnComparison }) {
  const t = useIntlayer('profileComparison')
  const changeColor =
    comparison.change === null
      ? 'text-muted-foreground'
      : comparison.change > 0
      ? 'text-green-500'
      : comparison.change < 0
      ? 'text-red-500'
      : 'text-muted-foreground'

  return (
    <TableRow className={comparison.is_significant ? 'bg-amber-500/5' : ''}>
      <TableCell className="font-medium">{comparison.column}</TableCell>
      <TableCell>
        <Badge variant="outline">{comparison.metric}</Badge>
      </TableCell>
      <TableCell className="text-muted-foreground text-right">
        {typeof comparison.baseline_value === 'number'
          ? comparison.baseline_value.toFixed(2)
          : comparison.baseline_value || '-'}
      </TableCell>
      <TableCell className="text-right font-medium">
        {typeof comparison.current_value === 'number'
          ? comparison.current_value.toFixed(2)
          : comparison.current_value || '-'}
      </TableCell>
      <TableCell className={`text-right ${changeColor}`}>
        {formatChange(comparison.change_pct, true)}
      </TableCell>
      <TableCell className="text-center">
        <TrendIcon direction={comparison.trend} />
      </TableCell>
      <TableCell className="text-center">
        {comparison.is_significant && (
          <Badge variant="outline" className="bg-amber-500/10 text-amber-500">
            {str(t.significantChanges)}
          </Badge>
        )}
      </TableCell>
    </TableRow>
  )
}

export default function ProfileComparison() {
  const t = useIntlayer('profileComparison')
  const { toast } = useToast()

  // State
  const [sources, setSources] = useState<Source[]>([])
  const [selectedSourceId, setSelectedSourceId] = useState<string | null>(null)
  const [profiles, setProfiles] = useState<ProfileSummary[]>([])
  const [baselineId, setBaselineId] = useState<string | null>(null)
  const [currentId, setCurrentId] = useState<string | null>(null)
  const [comparison, setComparison] = useState<ProfileComparisonResponse | null>(null)
  const [trendData, setTrendData] = useState<ProfileTrendResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [comparing, setComparing] = useState(false)
  const [period, setPeriod] = useState<'7d' | '30d' | '90d'>('30d')

  // Fetch sources
  useEffect(() => {
    listSources()
      .then((response) => {
        setSources(response.data || [])
        if (response.data?.length > 0) {
          setSelectedSourceId(response.data[0].id)
        }
      })
      .finally(() => setLoading(false))
  }, [])

  // Fetch profiles and trends when source changes
  const fetchData = useCallback(async () => {
    if (!selectedSourceId) return

    setLoading(true)
    try {
      const [profilesRes, trendRes, latestRes] = await Promise.all([
        listProfiles(selectedSourceId, { limit: 50 }),
        getProfileTrend(selectedSourceId, { period }),
        getLatestProfileComparison(selectedSourceId),
      ])

      setProfiles(profilesRes.profiles || [])
      setTrendData(trendRes)

      // Set default selection to latest two profiles
      if (profilesRes.profiles?.length >= 2) {
        setCurrentId(profilesRes.profiles[0].id)
        setBaselineId(profilesRes.profiles[1].id)
      }

      // Use latest comparison if available
      if (latestRes.has_previous && latestRes.comparison) {
        setComparison(latestRes.comparison)
      }
    } catch (error) {
      toast({ title: 'Failed to fetch profile data', variant: 'destructive' })
    } finally {
      setLoading(false)
    }
  }, [selectedSourceId, period, toast])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  // Compare profiles
  const handleCompare = async () => {
    if (!baselineId || !currentId) return

    setComparing(true)
    try {
      const result = await compareProfiles({
        baseline_profile_id: baselineId,
        current_profile_id: currentId,
      })
      setComparison(result)
    } catch (error) {
      toast({ title: 'Failed to compare profiles', variant: 'destructive' })
    } finally {
      setComparing(false)
    }
  }

  // Chart data
  const chartData = trendData?.data_points.map((dp) => ({
    date: new Date(dp.timestamp).toLocaleDateString(),
    rowCount: dp.row_count,
    avgNullPct: dp.avg_null_pct,
    avgUniquePct: dp.avg_unique_pct,
  })) || []

  const selectedSource = sources.find((s) => s.id === selectedSourceId)

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{str(t.comparisonSummary)}</h1>
          <p className="text-muted-foreground">{str(t.profileTrends)}</p>
        </div>
        <div className="flex items-center gap-2">
          <Select
            value={selectedSourceId || ''}
            onValueChange={setSelectedSourceId}
            disabled={loading}
          >
            <SelectTrigger className="w-64">
              <SelectValue placeholder="Select source..." />
            </SelectTrigger>
            <SelectContent>
              {sources.map((source) => (
                <SelectItem key={source.id} value={source.id}>
                  <div className="flex items-center gap-2">
                    <Database className="h-4 w-4" />
                    {source.name}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button onClick={fetchData} disabled={loading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {profiles.length < 2 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <BarChart3 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">{str(t.notEnoughProfiles)}</p>
            <p className="text-sm text-muted-foreground">{str(t.runProfilingFirst)}</p>
          </CardContent>
        </Card>
      ) : (
        <Tabs defaultValue="compare" className="space-y-4">
          <TabsList>
            <TabsTrigger value="compare">{str(t.comparisonSummary)}</TabsTrigger>
            <TabsTrigger value="trends">{str(t.profileTrends)}</TabsTrigger>
            <TabsTrigger value="history">{str(t.profileHistory)}</TabsTrigger>
          </TabsList>

          {/* Compare Tab */}
          <TabsContent value="compare" className="space-y-4">
            {/* Profile Selectors */}
            <Card>
              <CardHeader>
                <CardTitle>{str(t.selectProfiles)}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <label className="text-sm font-medium mb-2 block">{str(t.baselineLabel)}</label>
                    <Select value={baselineId || ''} onValueChange={setBaselineId}>
                      <SelectTrigger>
                        <SelectValue placeholder={str(t.baseline)} />
                      </SelectTrigger>
                      <SelectContent>
                        {profiles.map((p) => (
                          <SelectItem key={p.id} value={p.id} disabled={p.id === currentId}>
                            {new Date(p.created_at).toLocaleString()} ({p.row_count.toLocaleString()} rows)
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <ArrowUpDown className="h-5 w-5 text-muted-foreground" />
                  <div className="flex-1">
                    <label className="text-sm font-medium mb-2 block">{str(t.currentLabel)}</label>
                    <Select value={currentId || ''} onValueChange={setCurrentId}>
                      <SelectTrigger>
                        <SelectValue placeholder={str(t.current)} />
                      </SelectTrigger>
                      <SelectContent>
                        {profiles.map((p, idx) => (
                          <SelectItem key={p.id} value={p.id} disabled={p.id === baselineId}>
                            {new Date(p.created_at).toLocaleString()} ({p.row_count.toLocaleString()} rows)
                            {idx === 0 && (
                              <Badge variant="outline" className="ml-2">
                                {str(t.latest)}
                              </Badge>
                            )}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <Button
                    onClick={handleCompare}
                    disabled={!baselineId || !currentId || comparing}
                    className="mt-6"
                  >
                    {comparing ? str(t.comparing) : str(t.compareSelected)}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Comparison Results */}
            {comparison && (
              <>
                {/* Stats */}
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <StatsCard
                    title={str(t.rowCountChange)}
                    value={comparison.row_count_change.toLocaleString()}
                    change={comparison.row_count_change_pct}
                    icon={Activity}
                    variant={comparison.row_count_change >= 0 ? 'success' : 'warning'}
                  />
                  <StatsCard
                    title={str(t.totalColumns)}
                    value={comparison.summary?.total_columns || 0}
                    icon={BarChart3}
                  />
                  <StatsCard
                    title={str(t.withChanges)}
                    value={comparison.summary?.columns_with_changes || 0}
                    icon={ArrowUpDown}
                    variant="warning"
                  />
                  <StatsCard
                    title={str(t.improved)}
                    value={comparison.summary?.columns_improved || 0}
                    icon={TrendingUp}
                    variant="success"
                  />
                  <StatsCard
                    title={str(t.degraded)}
                    value={comparison.summary?.columns_degraded || 0}
                    icon={TrendingDown}
                    variant="danger"
                  />
                </div>

                {/* Column Comparisons */}
                <Card>
                  <CardHeader>
                    <CardTitle>{str(t.columnDetails)}</CardTitle>
                    <CardDescription>
                      {str(t.comparingProfiles)} {new Date(comparison.baseline_timestamp).toLocaleString()}{' '}
                      {str(t.to)} {new Date(comparison.current_timestamp).toLocaleString()}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {comparison.column_comparisons.length === 0 ? (
                      <p className="text-center text-muted-foreground py-8">
                        No significant changes detected
                      </p>
                    ) : (
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>{str(t.column)}</TableHead>
                            <TableHead>{str(t.metric)}</TableHead>
                            <TableHead className="text-right">{str(t.baseline)}</TableHead>
                            <TableHead className="text-right">{str(t.current)}</TableHead>
                            <TableHead className="text-right">{str(t.change)}</TableHead>
                            <TableHead className="text-center">{str(t.trend)}</TableHead>
                            <TableHead className="text-center">Status</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {comparison.column_comparisons.map((comp, idx) => (
                            <ComparisonRow key={`${comp.column}-${comp.metric}-${idx}`} comparison={comp} />
                          ))}
                        </TableBody>
                      </Table>
                    )}
                  </CardContent>
                </Card>
              </>
            )}
          </TabsContent>

          {/* Trends Tab */}
          <TabsContent value="trends" className="space-y-4">
            {/* Period Selector */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Period:</span>
              <Select value={period} onValueChange={(v) => setPeriod(v as typeof period)}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="7d">7 days</SelectItem>
                  <SelectItem value="30d">30 days</SelectItem>
                  <SelectItem value="90d">90 days</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Row Count Chart */}
            <Card>
              <CardHeader>
                <CardTitle>{str(t.rowCountOverTime)}</CardTitle>
                <CardDescription>
                  {trendData?.total_profiles || 0} {str(t.dataPoints)}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                      <XAxis dataKey="date" className="text-xs" />
                      <YAxis className="text-xs" />
                      <Tooltip />
                      <Area
                        type="monotone"
                        dataKey="rowCount"
                        name={str(t.rowCount)}
                        stroke="hsl(var(--primary))"
                        fill="hsl(var(--primary))"
                        fillOpacity={0.2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Quality Metrics Chart */}
            <Card>
              <CardHeader>
                <CardTitle>{str(t.dataQualityMetrics)}</CardTitle>
                <CardDescription>{str(t.avgNullAndUnique)}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                      <XAxis dataKey="date" className="text-xs" />
                      <YAxis className="text-xs" domain={[0, 100]} />
                      <Tooltip />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="avgNullPct"
                        name={str(t.avgNullPct)}
                        stroke="#ef4444"
                        strokeWidth={2}
                      />
                      <Line
                        type="monotone"
                        dataKey="avgUniquePct"
                        name={str(t.avgUniquePct)}
                        stroke="#22c55e"
                        strokeWidth={2}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* History Tab */}
          <TabsContent value="history">
            <Card>
              <CardHeader>
                <CardTitle>{str(t.profileHistory)}</CardTitle>
                <CardDescription>
                  {profiles.length} {str(t.profilesAvailable)}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{str(t.date)}</TableHead>
                      <TableHead className="text-right">{str(t.rows)}</TableHead>
                      <TableHead className="text-right">{str(t.columns)}</TableHead>
                      <TableHead className="text-right">{str(t.size)}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {profiles.map((profile, idx) => (
                      <TableRow key={profile.id}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Calendar className="h-4 w-4 text-muted-foreground" />
                            {new Date(profile.created_at).toLocaleString()}
                            {idx === 0 && (
                              <Badge variant="outline" className="bg-primary/10 text-primary">
                                {str(t.latest)}
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          {profile.row_count.toLocaleString()}
                        </TableCell>
                        <TableCell className="text-right">{profile.column_count}</TableCell>
                        <TableCell className="text-right text-muted-foreground">
                          {formatBytes(profile.size_bytes)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  )
}
