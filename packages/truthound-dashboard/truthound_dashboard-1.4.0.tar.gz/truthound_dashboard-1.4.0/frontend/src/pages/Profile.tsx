import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  getSource,
  profileSource,
  learnSchema,
  listSchemaVersions,
  listSchemaChanges,
  getSchemaEvolutionSummary,
  detectSchemaChanges,
  suggestRules,
  applyRuleSuggestions,
  listProfiles,
  compareProfiles,
  getProfileTrend,
  getLatestProfileComparison,
  type Source,
  type ProfileResult,
  type Schema,
  type SchemaVersionSummary,
  type SchemaChangeResponse,
  type SchemaEvolutionSummary,
  type SuggestedRule,
  type ProfileSummary,
  type ProfileComparisonResponse,
  type ProfileTrendResponse,
} from '@/api/client'
import { formatNumber } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'
import {
  ArrowLeft,
  BarChart3,
  FileCode,
  Database,
  RefreshCw,
  Copy,
  Check,
  AlertCircle,
  Hash,
  Type,
  Percent,
  ArrowUpDown,
  GitBranch,
  Sparkles,
  TrendingUp,
  Loader2,
  Settings2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'

// Import feature components
import { SchemaEvolutionTimeline } from '@/components/schema/SchemaEvolutionTimeline'
import { RuleSuggestionDialog } from '@/components/rules/RuleSuggestionDialog'
import { ProfileComparisonTable } from '@/components/profile/ProfileComparisonTable'
import { ProfileTrendChart } from '@/components/profile/ProfileTrendChart'
import { ProfileVersionSelector } from '@/components/profile/ProfileVersionSelector'
import {
  SamplingConfigPanel,
  PatternDetectionPanel,
  DEFAULT_SAMPLING_CONFIG,
  DEFAULT_PATTERN_CONFIG,
  type SamplingConfig,
  type PatternDetectionConfig,
} from '@/components/profile'

// UISuggestedRule removed - using SuggestedRule from API directly

// Column sorting types
type SortKey = 'name' | 'dtype' | 'null_pct' | 'unique_pct'
type SortDirection = 'asc' | 'desc'

interface SortConfig {
  key: SortKey
  direction: SortDirection
}

// Helper to parse percentage string to number
function parsePercentage(value: string | undefined): number {
  if (!value) return 0
  return parseFloat(value.replace('%', '')) || 0
}

// Helper to format bytes
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

// Get badge variant based on null percentage
function getNullBadgeVariant(nullPct: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  const pct = parsePercentage(nullPct)
  if (pct === 0) return 'outline'
  if (pct < 5) return 'secondary'
  if (pct < 20) return 'default'
  return 'destructive'
}

// Get badge variant based on unique percentage
function getUniqueBadgeVariant(uniquePct: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  const pct = parsePercentage(uniquePct)
  if (pct >= 99) return 'outline' // Likely primary key
  if (pct >= 80) return 'secondary'
  if (pct >= 20) return 'default'
  return 'destructive' // Low cardinality
}

export default function Profile() {
  const { id: sourceId } = useParams<{ id: string }>()
  const { toast } = useToast()

  // ============================================================================
  // Core State
  // ============================================================================
  const [source, setSource] = useState<Source | null>(null)
  const [profile, setProfile] = useState<ProfileResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [profiling, setProfiling] = useState(false)
  const [learningSchema, setLearningSchema] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('profile')

  // Schema dialog
  const [schemaDialogOpen, setSchemaDialogOpen] = useState(false)
  const [learnedSchema, setLearnedSchema] = useState<Schema | null>(null)
  const [copied, setCopied] = useState(false)

  // Sorting
  const [sortConfig, setSortConfig] = useState<SortConfig>({ key: 'name', direction: 'asc' })

  // Filter by data type
  const [typeFilter, setTypeFilter] = useState<string>('all')

  // ============================================================================
  // Schema Evolution State
  // ============================================================================
  const [schemaVersions, setSchemaVersions] = useState<SchemaVersionSummary[]>([])
  const [schemaChanges, setSchemaChanges] = useState<SchemaChangeResponse[]>([])
  const [evolutionSummary, setEvolutionSummary] = useState<SchemaEvolutionSummary | null>(null)
  const [loadingEvolution, setLoadingEvolution] = useState(false)
  const [detectingChanges, setDetectingChanges] = useState(false)

  // ============================================================================
  // Rule Suggestion State
  // ============================================================================
  const [ruleSuggestionDialogOpen, setRuleSuggestionDialogOpen] = useState(false)
  const [suggestions, setSuggestions] = useState<SuggestedRule[]>([])
  const [loadingSuggestions, setLoadingSuggestions] = useState(false)

  // ============================================================================
  // Profile Comparison State
  // ============================================================================
  const [profileHistory, setProfileHistory] = useState<ProfileSummary[]>([])
  const [selectedProfiles, setSelectedProfiles] = useState<string[]>([])
  const [comparison, setComparison] = useState<ProfileComparisonResponse | null>(null)
  const [trendData, setTrendData] = useState<ProfileTrendResponse | null>(null)
  const [loadingComparison, setLoadingComparison] = useState(false)
  const [trendGranularity, setTrendGranularity] = useState<'daily' | 'weekly' | 'monthly'>('daily')

  // ============================================================================
  // Advanced Profiling Configuration State
  // ============================================================================
  const [samplingConfig, setSamplingConfig] = useState<SamplingConfig>(DEFAULT_SAMPLING_CONFIG)
  const [patternConfig, setPatternConfig] = useState<PatternDetectionConfig>(DEFAULT_PATTERN_CONFIG)
  const [showAdvancedConfig, setShowAdvancedConfig] = useState(false)

  // ============================================================================
  // Load Source Data
  // ============================================================================
  useEffect(() => {
    if (!sourceId) return

    async function fetchSource() {
      try {
        setLoading(true)
        const sourceData = await getSource(sourceId!)
        setSource(sourceData)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load source')
      } finally {
        setLoading(false)
      }
    }

    fetchSource()
  }, [sourceId])

  // ============================================================================
  // Load Tab-specific Data
  // ============================================================================
  useEffect(() => {
    if (!sourceId) return

    if (activeTab === 'evolution') {
      loadEvolutionData()
    } else if (activeTab === 'comparison') {
      loadComparisonData()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, sourceId])

  // ============================================================================
  // Schema Evolution Functions
  // ============================================================================
  const loadEvolutionData = useCallback(async () => {
    if (!sourceId) return

    try {
      setLoadingEvolution(true)
      const [versionsRes, changesRes, summaryRes] = await Promise.all([
        listSchemaVersions(sourceId),
        listSchemaChanges(sourceId),
        getSchemaEvolutionSummary(sourceId),
      ])
      setSchemaVersions(versionsRes.versions)
      setSchemaChanges(changesRes.changes)
      setEvolutionSummary(summaryRes)
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Failed to load schema evolution',
        description: err instanceof Error ? err.message : 'Unknown error',
      })
    } finally {
      setLoadingEvolution(false)
    }
  }, [sourceId, toast])

  const handleDetectChanges = useCallback(async () => {
    if (!sourceId) return

    try {
      setDetectingChanges(true)
      const result = await detectSchemaChanges(sourceId)
      if (result.has_changes) {
        toast({
          title: 'Schema Changes Detected',
          description: `Found ${result.total_changes} changes (${result.breaking_changes} breaking)`,
        })
      } else {
        toast({
          title: 'No Changes',
          description: 'Schema is unchanged from the previous version',
        })
      }
      // Reload evolution data
      await loadEvolutionData()
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Detection Failed',
        description: err instanceof Error ? err.message : 'Unknown error',
      })
    } finally {
      setDetectingChanges(false)
    }
  }, [sourceId, toast, loadEvolutionData])

  // ============================================================================
  // Rule Suggestion Functions
  // ============================================================================
  const handleGenerateSuggestions = useCallback(async () => {
    if (!sourceId) return

    try {
      setLoadingSuggestions(true)
      setRuleSuggestionDialogOpen(true)
      const response = await suggestRules(sourceId, { min_confidence: 0.5 })
      // Use API response directly (SuggestedRule[])
      setSuggestions(response.suggestions)
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Failed to generate suggestions',
        description: err instanceof Error ? err.message : 'Unknown error',
      })
      setRuleSuggestionDialogOpen(false)
    } finally {
      setLoadingSuggestions(false)
    }
  }, [sourceId, toast])

  const handleApplyRules = useCallback(
    async (selectedIds: string[]) => {
      if (!sourceId || selectedIds.length === 0) return

      try {
        // Filter suggestions by selected IDs - already in API format
        const selectedSuggestions = suggestions.filter((s) => selectedIds.includes(s.id))

        const result = await applyRuleSuggestions(sourceId, {
          suggestions: selectedSuggestions,
          create_new_rule: true,
          rule_name: `Auto-generated rules for ${source?.name || sourceId}`,
        })
        toast({
          title: 'Rules Applied',
          description: `Applied ${result.applied_count} validation rules`,
        })
      } catch (err) {
        toast({
          variant: 'destructive',
          title: 'Failed to apply rules',
          description: err instanceof Error ? err.message : 'Unknown error',
        })
      }
    },
    [sourceId, source, suggestions, toast]
  )

  // ============================================================================
  // Profile Comparison Functions
  // ============================================================================
  const loadComparisonData = useCallback(async () => {
    if (!sourceId) return

    try {
      setLoadingComparison(true)
      const [historyRes, latestRes, trendRes] = await Promise.all([
        listProfiles(sourceId, { limit: 20 }),
        getLatestProfileComparison(sourceId).catch(() => ({ has_previous: false, comparison: null, source_id: sourceId })),
        getProfileTrend(sourceId, { period: '30d', granularity: trendGranularity }),
      ])
      setProfileHistory(historyRes.profiles)
      if (latestRes.comparison) {
        setComparison(latestRes.comparison)
      }
      setTrendData(trendRes)
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Failed to load comparison data',
        description: err instanceof Error ? err.message : 'Unknown error',
      })
    } finally {
      setLoadingComparison(false)
    }
  }, [sourceId, trendGranularity, toast])

  const handleCompareProfiles = useCallback(async () => {
    if (selectedProfiles.length !== 2) {
      toast({
        variant: 'destructive',
        title: 'Select Two Profiles',
        description: 'Please select exactly two profiles to compare',
      })
      return
    }

    try {
      setLoadingComparison(true)
      const result = await compareProfiles({
        baseline_profile_id: selectedProfiles[0],
        current_profile_id: selectedProfiles[1],
      })
      setComparison(result)
      toast({
        title: 'Comparison Complete',
        description: `Found ${result.significant_changes} significant changes`,
      })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Comparison Failed',
        description: err instanceof Error ? err.message : 'Unknown error',
      })
    } finally {
      setLoadingComparison(false)
    }
  }, [selectedProfiles, toast])

  // ============================================================================
  // Profile Functions
  // ============================================================================
  const handleProfile = useCallback(async () => {
    if (!sourceId) return

    try {
      setProfiling(true)
      const result = await profileSource(sourceId)
      setProfile(result)
      toast({
        title: 'Profile Complete',
        description: `Analyzed ${result.row_count.toLocaleString()} rows across ${result.column_count} columns`,
      })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Profiling Failed',
        description: err instanceof Error ? err.message : 'Unknown error',
      })
    } finally {
      setProfiling(false)
    }
  }, [sourceId, toast])

  // Learn schema
  const handleLearnSchema = useCallback(async () => {
    if (!sourceId) return

    try {
      setLearningSchema(true)
      const result = await learnSchema(sourceId, { infer_constraints: true })
      setLearnedSchema(result)
      setSchemaDialogOpen(true)
      toast({
        title: 'Schema Generated',
        description: `Generated schema with ${result.column_count} columns`,
      })
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Schema Generation Failed',
        description: err instanceof Error ? err.message : 'Unknown error',
      })
    } finally {
      setLearningSchema(false)
    }
  }, [sourceId, toast])

  // Copy schema to clipboard
  const handleCopySchema = useCallback(async () => {
    if (!learnedSchema?.schema_yaml) return

    try {
      await navigator.clipboard.writeText(learnedSchema.schema_yaml)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
      toast({
        title: 'Copied',
        description: 'Schema YAML copied to clipboard',
      })
    } catch {
      toast({
        variant: 'destructive',
        title: 'Copy Failed',
        description: 'Failed to copy to clipboard',
      })
    }
  }, [learnedSchema, toast])

  // Sort columns
  const handleSort = useCallback((key: SortKey) => {
    setSortConfig((prev) => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
    }))
  }, [])

  // Get unique data types for filter
  const dataTypes = profile?.columns
    ? [...new Set(profile.columns.map((c) => c.dtype))].sort()
    : []

  // Filter and sort columns
  const sortedColumns = profile?.columns
    ? [...profile.columns]
        .filter((col) => typeFilter === 'all' || col.dtype === typeFilter)
        .sort((a, b) => {
          const { key, direction } = sortConfig
          let cmp = 0

          switch (key) {
            case 'name':
              cmp = a.name.localeCompare(b.name)
              break
            case 'dtype':
              cmp = a.dtype.localeCompare(b.dtype)
              break
            case 'null_pct':
              cmp = parsePercentage(a.null_pct) - parsePercentage(b.null_pct)
              break
            case 'unique_pct':
              cmp = parsePercentage(a.unique_pct) - parsePercentage(b.unique_pct)
              break
          }

          return direction === 'asc' ? cmp : -cmp
        })
    : []

  // ============================================================================
  // Loading/Error States
  // ============================================================================
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-destructive/10 border border-destructive rounded-lg p-4 flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-destructive" />
          <p className="text-destructive">{error}</p>
        </div>
      </div>
    )
  }

  if (!source) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <Database className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h2 className="text-lg font-medium mb-2">Source not found</h2>
          <Button asChild>
            <Link to="/sources">Back to Sources</Link>
          </Button>
        </div>
      </div>
    )
  }

  // ============================================================================
  // Render
  // ============================================================================
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to={`/sources/${sourceId}`}>
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold">{source.name} - Data Insights</h1>
            <p className="text-muted-foreground">
              Profiling, schema evolution, and rule suggestions
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleGenerateSuggestions}
            disabled={!profile || loadingSuggestions}
          >
            <Sparkles className="h-4 w-4 mr-2" />
            Suggest Rules
          </Button>
          <Button
            variant="outline"
            onClick={handleLearnSchema}
            disabled={learningSchema || profiling}
          >
            <FileCode className="h-4 w-4 mr-2" />
            {learningSchema ? 'Generating...' : 'Generate Schema'}
          </Button>
          <Button onClick={handleProfile} disabled={profiling || learningSchema}>
            {profiling ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Profiling...
              </>
            ) : (
              <>
                <BarChart3 className="h-4 w-4 mr-2" />
                Run Profile
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3 lg:w-[400px]">
          <TabsTrigger value="profile" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Profile
          </TabsTrigger>
          <TabsTrigger value="evolution" className="flex items-center gap-2">
            <GitBranch className="h-4 w-4" />
            Schema Evolution
          </TabsTrigger>
          <TabsTrigger value="comparison" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Comparison
          </TabsTrigger>
        </TabsList>

        {/* ================================================================== */}
        {/* Profile Tab */}
        {/* ================================================================== */}
        <TabsContent value="profile" className="space-y-6">
          {/* Advanced Profiling Settings - Collapsible */}
          <Collapsible open={showAdvancedConfig} onOpenChange={setShowAdvancedConfig}>
            <Card>
              <CollapsibleTrigger asChild>
                <CardHeader className="cursor-pointer hover:bg-muted/50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Settings2 className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <CardTitle className="text-base">Advanced Profiling Settings</CardTitle>
                        <CardDescription className="text-sm">
                          Configure sampling strategies and pattern detection options
                        </CardDescription>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm">
                      {showAdvancedConfig ? (
                        <ChevronUp className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </CardHeader>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <CardContent className="pt-0">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    <SamplingConfigPanel
                      config={samplingConfig}
                      onChange={setSamplingConfig}
                      columns={profile?.columns.map((c) => c.name) || []}
                      disabled={profiling}
                    />
                    <PatternDetectionPanel
                      config={patternConfig}
                      onChange={setPatternConfig}
                      disabled={profiling}
                    />
                  </div>
                </CardContent>
              </CollapsibleContent>
            </Card>
          </Collapsible>

          {/* Profile not run yet */}
          {!profile && (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16">
                <BarChart3 className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium mb-2">No Profile Data</h3>
                <p className="text-muted-foreground text-center mb-4 max-w-md">
                  Run a profile to analyze your data structure, column types, null percentages, and
                  unique value distributions.
                </p>
                <Button onClick={handleProfile} disabled={profiling}>
                  {profiling ? 'Profiling...' : 'Run Profile'}
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Profile Results */}
          {profile && (
            <>
              {/* Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                      <Hash className="h-4 w-4" />
                      Rows
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{formatNumber(profile.row_count)}</div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                      <Type className="h-4 w-4" />
                      Columns
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{profile.column_count}</div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                      <Database className="h-4 w-4" />
                      Size
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{formatBytes(profile.size_bytes)}</div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                      <Percent className="h-4 w-4" />
                      Avg Null %
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {profile.columns.length > 0
                        ? (
                            profile.columns.reduce((sum, col) => sum + parsePercentage(col.null_pct), 0) /
                            profile.columns.length
                          ).toFixed(1)
                        : 0}
                      %
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Column Statistics Table */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Column Statistics</CardTitle>
                      <CardDescription>Detailed statistics for each column</CardDescription>
                    </div>

                    {/* Type Filter */}
                    <Select value={typeFilter} onValueChange={setTypeFilter}>
                      <SelectTrigger className="w-40">
                        <SelectValue placeholder="Filter by type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Types</SelectItem>
                        {dataTypes.map((type) => (
                          <SelectItem key={type} value={type}>
                            {type}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="rounded-md border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-8 -ml-3 font-semibold"
                              onClick={() => handleSort('name')}
                            >
                              Column
                              <ArrowUpDown className="ml-2 h-3 w-3" />
                            </Button>
                          </TableHead>
                          <TableHead>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-8 -ml-3 font-semibold"
                              onClick={() => handleSort('dtype')}
                            >
                              Type
                              <ArrowUpDown className="ml-2 h-3 w-3" />
                            </Button>
                          </TableHead>
                          <TableHead>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-8 -ml-3 font-semibold"
                              onClick={() => handleSort('null_pct')}
                            >
                              Nulls
                              <ArrowUpDown className="ml-2 h-3 w-3" />
                            </Button>
                          </TableHead>
                          <TableHead>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-8 -ml-3 font-semibold"
                              onClick={() => handleSort('unique_pct')}
                            >
                              Unique
                              <ArrowUpDown className="ml-2 h-3 w-3" />
                            </Button>
                          </TableHead>
                          <TableHead>Min</TableHead>
                          <TableHead>Max</TableHead>
                          <TableHead>Mean</TableHead>
                          <TableHead>Std</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {sortedColumns.length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                              No columns match the filter
                            </TableCell>
                          </TableRow>
                        ) : (
                          sortedColumns.map((col) => (
                            <TableRow key={col.name}>
                              <TableCell className="font-mono text-sm font-medium">
                                {col.name}
                              </TableCell>
                              <TableCell>
                                <Badge variant="outline">{col.dtype}</Badge>
                              </TableCell>
                              <TableCell>
                                <Badge variant={getNullBadgeVariant(col.null_pct)}>
                                  {col.null_pct}
                                </Badge>
                              </TableCell>
                              <TableCell>
                                <Badge variant={getUniqueBadgeVariant(col.unique_pct)}>
                                  {col.unique_pct}
                                </Badge>
                              </TableCell>
                              <TableCell className="font-mono text-sm">
                                {col.min !== undefined && col.min !== null
                                  ? String(col.min).length > 20
                                    ? `${String(col.min).slice(0, 20)}...`
                                    : String(col.min)
                                  : '-'}
                              </TableCell>
                              <TableCell className="font-mono text-sm">
                                {col.max !== undefined && col.max !== null
                                  ? String(col.max).length > 20
                                    ? `${String(col.max).slice(0, 20)}...`
                                    : String(col.max)
                                  : '-'}
                              </TableCell>
                              <TableCell className="font-mono text-sm">
                                {col.mean !== undefined && col.mean !== null
                                  ? typeof col.mean === 'number'
                                    ? col.mean.toFixed(2)
                                    : col.mean
                                  : '-'}
                              </TableCell>
                              <TableCell className="font-mono text-sm">
                                {col.std !== undefined && col.std !== null
                                  ? typeof col.std === 'number'
                                    ? col.std.toFixed(2)
                                    : col.std
                                  : '-'}
                              </TableCell>
                            </TableRow>
                          ))
                        )}
                      </TableBody>
                    </Table>
                  </div>

                  {/* Results summary */}
                  <div className="mt-4 text-sm text-muted-foreground">
                    Showing {sortedColumns.length} of {profile.columns.length} columns
                    {typeFilter !== 'all' && ` (filtered by ${typeFilter})`}
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* ================================================================== */}
        {/* Schema Evolution Tab */}
        {/* ================================================================== */}
        <TabsContent value="evolution" className="space-y-6">
          <SchemaEvolutionTimeline
            sourceId={sourceId || ''}
            summary={evolutionSummary}
            versions={schemaVersions}
            changes={schemaChanges.map((c) => ({
              ...c,
              severity: c.severity as 'breaking' | 'non_breaking',
              change_type: c.change_type as 'column_added' | 'column_removed' | 'type_changed',
            }))}
            onDetectChanges={handleDetectChanges}
            isLoading={loadingEvolution}
            isDetecting={detectingChanges}
          />
        </TabsContent>

        {/* ================================================================== */}
        {/* Profile Comparison Tab */}
        {/* ================================================================== */}
        <TabsContent value="comparison" className="space-y-6">
          {loadingComparison && !comparison && (
            <Card>
              <CardContent className="py-8">
                <div className="flex items-center justify-center gap-2 text-muted-foreground">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span>Loading comparison data...</span>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Profile Trend Chart */}
          {trendData && trendData.data_points.length > 0 && (
            <ProfileTrendChart
              trend={{
                ...trendData,
                granularity: (trendData.granularity || 'daily') as 'daily' | 'weekly' | 'monthly',
                period_start: trendData.data_points[0]?.timestamp || '',
                period_end: trendData.data_points[trendData.data_points.length - 1]?.timestamp || '',
                trends: {
                  row_count: trendData.row_count_trend,
                  null_pct: 'stable' as const,
                  unique_pct: 'stable' as const,
                },
              }}
              granularity={trendGranularity}
              onGranularityChange={setTrendGranularity}
            />
          )}

          {/* Profile Selection */}
          {profileHistory.length > 0 && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Profile History</CardTitle>
                    <CardDescription>
                      Select two profiles to compare. {profileHistory.length} profiles available.
                    </CardDescription>
                  </div>
                  <Button
                    onClick={handleCompareProfiles}
                    disabled={selectedProfiles.length !== 2 || loadingComparison}
                  >
                    {loadingComparison ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Comparing...
                      </>
                    ) : (
                      'Compare Selected'
                    )}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <ProfileVersionSelector
                  profiles={profileHistory.map(p => ({
                    ...p,
                    avg_null_pct: 0,
                    avg_unique_pct: 0,
                  }))}
                  selectedIds={selectedProfiles}
                  onSelectionChange={setSelectedProfiles}
                  maxSelection={2}
                  tableOnly
                />
              </CardContent>
            </Card>
          )}

          {/* Comparison Results */}
          {comparison && <ProfileComparisonTable comparison={comparison} />}

          {/* Empty State */}
          {!loadingComparison && profileHistory.length === 0 && (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16">
                <TrendingUp className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium mb-2">No Profile History</h3>
                <p className="text-muted-foreground text-center mb-4 max-w-md">
                  Run profiling multiple times to build a history for comparison.
                </p>
                <Button onClick={handleProfile} disabled={profiling}>
                  {profiling ? 'Profiling...' : 'Run Profile'}
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* ================================================================== */}
      {/* Dialogs */}
      {/* ================================================================== */}

      {/* Schema Dialog */}
      <Dialog open={schemaDialogOpen} onOpenChange={setSchemaDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>Generated Schema</DialogTitle>
            <DialogDescription>
              Auto-generated schema from {source.name}. You can copy this YAML to use with
              truthound validation.
            </DialogDescription>
          </DialogHeader>

          {learnedSchema && (
            <div className="space-y-4">
              {/* Schema stats */}
              <div className="flex gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Columns:</span>{' '}
                  <span className="font-medium">{learnedSchema.column_count}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Rows analyzed:</span>{' '}
                  <span className="font-medium">
                    {formatNumber(learnedSchema.row_count)}
                  </span>
                </div>
              </div>

              {/* Schema YAML */}
              <div className="relative">
                <pre className="bg-muted p-4 rounded-lg text-sm overflow-auto max-h-[400px] font-mono">
                  {learnedSchema.schema_yaml}
                </pre>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setSchemaDialogOpen(false)}>
              Close
            </Button>
            <Button onClick={handleCopySchema}>
              {copied ? (
                <>
                  <Check className="h-4 w-4 mr-2" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4 mr-2" />
                  Copy YAML
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Rule Suggestion Dialog */}
      <RuleSuggestionDialog
        open={ruleSuggestionDialogOpen}
        onOpenChange={setRuleSuggestionDialogOpen}
        sourceName={source.name}
        sourceId={sourceId!}
        suggestions={suggestions}
        isLoading={loadingSuggestions}
        onApply={handleApplyRules}
        onGenerate={async () => { await handleGenerateSuggestions() }}
      />
    </div>
  )
}
