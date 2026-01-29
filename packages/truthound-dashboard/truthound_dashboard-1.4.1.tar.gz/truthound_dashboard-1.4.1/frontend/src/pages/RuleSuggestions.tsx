/**
 * Rule Suggestions Page
 *
 * Unified view for profile-based validation rule suggestions with:
 * - Source selection and profile analysis
 * - Strictness levels and presets
 * - Category-based filtering
 * - Multiple export formats (YAML, JSON, Python, TOML)
 * - Batch rule application
 */

import { useEffect, useState, useCallback } from 'react'
import { useSafeIntlayer } from '@/hooks/useSafeIntlayer'
import {
  Sparkles,
  Database,
  Settings2,
  Filter,
  Search,
  CheckSquare,
  Square,
  Download,
  Copy,
  Check,
  Loader2,
  FileText,
  FileJson,
  FileCode,
  AlertCircle,
  TrendingUp,
  Zap,
  BarChart3,
  RefreshCw,
} from 'lucide-react'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import { useToast } from '@/hooks/use-toast'
import { str } from '@/lib/intlayer-utils'
import { RuleSuggestionCard } from '@/components/rules/RuleSuggestionCard'
import { CrossColumnRuleCard } from '@/components/rules/CrossColumnRuleCard'
import {
  listSources,
  suggestRules,
  applyRuleSuggestions,
  exportRules,
  type Source,
  type SuggestedRule,
  type CrossColumnRuleSuggestion,
  type StrictnessLevel,
  type RulePreset,
  type RuleExportFormat,
  type RuleCategory,
  type RuleSuggestionRequest,
} from '@/api/client'

// Category colors for badges
const CATEGORY_COLORS: Record<string, string> = {
  completeness: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
  uniqueness: 'bg-purple-500/10 text-purple-500 border-purple-500/20',
  distribution: 'bg-green-500/10 text-green-500 border-green-500/20',
  schema: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
  stats: 'bg-cyan-500/10 text-cyan-500 border-cyan-500/20',
  pattern: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
  string: 'bg-cyan-500/10 text-cyan-500 border-cyan-500/20',
  datetime: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
  relationship: 'bg-indigo-500/10 text-indigo-500 border-indigo-500/20',
  multi_column: 'bg-pink-500/10 text-pink-500 border-pink-500/20',
}

// All available categories
const ALL_CATEGORIES: RuleCategory[] = [
  'schema',
  'completeness',
  'uniqueness',
  'distribution',
  'stats',
  'pattern',
  'relationship',
  'multi_column',
]

// Preset information with descriptions
const PRESET_INFO: Record<string, { icon: typeof Zap; description: string }> = {
  default: { icon: BarChart3, description: 'General purpose validation' },
  strict: { icon: AlertCircle, description: 'Production data pipelines' },
  loose: { icon: Settings2, description: 'Development/testing' },
  minimal: { icon: Zap, description: 'Essential rules only' },
  comprehensive: { icon: TrendingUp, description: 'Full data audit' },
  ci_cd: { icon: RefreshCw, description: 'CI/CD pipelines' },
  schema_only: { icon: Database, description: 'Schema validation' },
  format_only: { icon: FileText, description: 'Format validation' },
  cross_column: { icon: TrendingUp, description: 'Cross-column relationships' },
  data_integrity: { icon: AlertCircle, description: 'Data integrity rules' },
}

// Stats Card component
function StatsCard({
  title,
  value,
  icon: Icon,
  variant = 'default',
  description,
}: {
  title: string
  value: number | string
  icon: typeof Sparkles
  variant?: 'default' | 'success' | 'warning' | 'danger'
  description?: string
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
            {description && (
              <p className="text-xs text-muted-foreground mt-1">{description}</p>
            )}
          </div>
          <Icon className={`h-8 w-8 ${variantStyles[variant]} opacity-50`} />
        </div>
      </CardContent>
    </Card>
  )
}

// Category breakdown chart component
function CategoryBreakdown({
  byCategory,
  t,
}: {
  byCategory: Record<string, number>
  t: ReturnType<typeof useSafeIntlayer<'ruleSuggestions'>>
}) {
  const total = Object.values(byCategory).reduce((a, b) => a + b, 0)
  if (total === 0) return null

  return (
    <div className="space-y-3">
      {Object.entries(byCategory)
        .sort(([, a], [, b]) => b - a)
        .map(([category, count]) => (
          <div key={category} className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="capitalize">{category}</span>
              <span className="text-muted-foreground">
                {count} ({Math.round((count / total) * 100)}%)
              </span>
            </div>
            <Progress
              value={(count / total) * 100}
              className="h-2"
            />
          </div>
        ))}
    </div>
  )
}

export default function RuleSuggestions() {
  const t = useSafeIntlayer('ruleSuggestions')
  const common = useSafeIntlayer('common')
  const { toast } = useToast()

  // Data state
  const [sources, setSources] = useState<Source[]>([])
  const [selectedSourceId, setSelectedSourceId] = useState<string | null>(null)
  const [suggestions, setSuggestions] = useState<SuggestedRule[]>([])
  const [crossColumnSuggestions, setCrossColumnSuggestions] = useState<CrossColumnRuleSuggestion[]>([])
  const [byCategory, setByCategory] = useState<Record<string, number>>({})
  const [byCrossColumnType, setByCrossColumnType] = useState<Record<string, number>>({})

  // UI state
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [applying, setApplying] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [copied, setCopied] = useState(false)

  // Selection state
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [selectedCrossColumnIds, setSelectedCrossColumnIds] = useState<Set<string>>(new Set())
  const [searchTerm, setSearchTerm] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [activeTab, setActiveTab] = useState<string>('generate')
  const [ruleViewTab, setRuleViewTab] = useState<string>('single')

  // Generation options
  const [strictness, setStrictness] = useState<StrictnessLevel>('medium')
  const [preset, setPreset] = useState<RulePreset | ''>('')
  const [minConfidence, setMinConfidence] = useState(50)
  const [includedCategories, setIncludedCategories] = useState<RuleCategory[]>([...ALL_CATEGORIES])
  const [enableCrossColumn, setEnableCrossColumn] = useState(true)

  // Export state
  const [exportFormat, setExportFormat] = useState<RuleExportFormat>('yaml')

  // Fetch sources on mount
  useEffect(() => {
    listSources()
      .then((response) => {
        setSources(response.data || [])
        if (response.data?.length > 0) {
          setSelectedSourceId(response.data[0].id)
        }
      })
      .catch(() => {
        toast({ title: 'Failed to fetch sources', variant: 'destructive' })
      })
      .finally(() => setLoading(false))
  }, [toast])

  // Generate suggestions
  const handleGenerate = useCallback(async () => {
    if (!selectedSourceId) return

    setGenerating(true)
    try {
      const options: RuleSuggestionRequest = {
        strictness,
        min_confidence: minConfidence / 100,
        include_categories: includedCategories.length < ALL_CATEGORIES.length ? includedCategories : undefined,
        enable_cross_column: enableCrossColumn,
      }
      if (preset) {
        options.preset = preset
      }

      const response = await suggestRules(selectedSourceId, options)
      setSuggestions(response.suggestions || [])
      setCrossColumnSuggestions(response.cross_column_suggestions || [])
      setByCategory(response.by_category || {})
      setByCrossColumnType(response.by_cross_column_type || {})

      // Auto-select high confidence single-column suggestions
      const highConfidence = (response.suggestions || [])
        .filter((s: SuggestedRule) => s.confidence >= 0.85)
        .map((s: SuggestedRule) => s.id)
      setSelectedIds(new Set(highConfidence))

      // Auto-select high confidence cross-column suggestions
      const highConfidenceCrossColumn = (response.cross_column_suggestions || [])
        .filter((s: CrossColumnRuleSuggestion) => s.confidence >= 0.85)
        .map((s: CrossColumnRuleSuggestion) => s.id)
      setSelectedCrossColumnIds(new Set(highConfidenceCrossColumn))

      const totalCount = (response.suggestions?.length || 0) + (response.cross_column_suggestions?.length || 0)
      toast({ title: `Generated ${totalCount} suggestions (${response.cross_column_suggestions?.length || 0} cross-column)` })
    } catch (error) {
      toast({ title: 'Failed to generate suggestions', variant: 'destructive' })
    } finally {
      setGenerating(false)
    }
  }, [selectedSourceId, strictness, preset, minConfidence, includedCategories, enableCrossColumn, toast])

  // Apply selected suggestions
  const handleApply = useCallback(async () => {
    if (!selectedSourceId || selectedIds.size === 0) return

    setApplying(true)
    try {
      await applyRuleSuggestions(selectedSourceId, { rule_ids: Array.from(selectedIds) })
      toast({
        title: str(t.rulesApplied),
        description: `${selectedIds.size} ${str(t.appliedCount)}`,
      })
    } catch (error) {
      toast({ title: 'Failed to apply rules', variant: 'destructive' })
    } finally {
      setApplying(false)
    }
  }, [selectedSourceId, selectedIds, toast, t])

  // Export suggestions
  const handleExport = useCallback(async (format: RuleExportFormat) => {
    if (!selectedSourceId || selectedIds.size === 0) return

    setExporting(true)
    try {
      const selectedSuggestions = suggestions.filter((s) => selectedIds.has(s.id))
      const response = await exportRules(selectedSourceId, {
        suggestions: selectedSuggestions,
        format,
      })

      // Download file
      const blob = new Blob([response.content], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = response.filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      toast({ title: str(t.exportSuccess) })
    } catch (error) {
      toast({ title: 'Failed to export rules', variant: 'destructive' })
    } finally {
      setExporting(false)
    }
  }, [selectedSourceId, selectedIds, suggestions, toast, t])

  // Copy to clipboard
  const handleCopy = useCallback(async () => {
    if (!selectedSourceId || selectedIds.size === 0) return

    try {
      const selectedSuggestions = suggestions.filter((s) => selectedIds.has(s.id))
      const response = await exportRules(selectedSourceId, {
        suggestions: selectedSuggestions,
        format: exportFormat,
      })
      await navigator.clipboard.writeText(response.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      toast({ title: 'Failed to copy', variant: 'destructive' })
    }
  }, [selectedSourceId, selectedIds, suggestions, exportFormat, toast])

  // Toggle selection for single-column rules
  const toggleSelection = (id: string) => {
    const newSelected = new Set(selectedIds)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedIds(newSelected)
  }

  // Toggle selection for cross-column rules
  const toggleCrossColumnSelection = (id: string) => {
    const newSelected = new Set(selectedCrossColumnIds)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedCrossColumnIds(newSelected)
  }

  const selectAll = () => {
    if (ruleViewTab === 'single') {
      setSelectedIds(new Set(filteredSuggestions.map((s) => s.id)))
    } else {
      setSelectedCrossColumnIds(new Set(filteredCrossColumnSuggestions.map((s) => s.id)))
    }
  }

  const deselectAll = () => {
    if (ruleViewTab === 'single') {
      setSelectedIds(new Set())
    } else {
      setSelectedCrossColumnIds(new Set())
    }
  }

  const toggleCategory = (category: RuleCategory) => {
    setIncludedCategories((prev) =>
      prev.includes(category)
        ? prev.filter((c) => c !== category)
        : [...prev, category]
    )
  }

  // Filter single-column suggestions
  const filteredSuggestions = suggestions.filter((s) => {
    const matchesSearch =
      searchTerm === '' ||
      s.validator_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.column?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.reason.toLowerCase().includes(searchTerm.toLowerCase())

    const matchesCategory = categoryFilter === 'all' || s.category === categoryFilter

    return matchesSearch && matchesCategory
  })

  // Filter cross-column suggestions
  const filteredCrossColumnSuggestions = crossColumnSuggestions.filter((s) => {
    const matchesSearch =
      searchTerm === '' ||
      s.validator_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.columns.some((c) => c.toLowerCase().includes(searchTerm.toLowerCase())) ||
      s.reason.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.rule_type.toLowerCase().includes(searchTerm.toLowerCase())

    return matchesSearch
  })

  // Get unique categories from suggestions
  const availableCategories = [...new Set(suggestions.map((s) => s.category))]
  const availableCrossColumnTypes = [...new Set(crossColumnSuggestions.map((s) => s.rule_type))]

  const highConfidenceCount =
    suggestions.filter((s) => s.confidence >= 0.85).length +
    crossColumnSuggestions.filter((s) => s.confidence >= 0.85).length
  const selectedSource = sources.find((s) => s.id === selectedSourceId)
  const totalSelectedCount = selectedIds.size + selectedCrossColumnIds.size

  return (
    <TooltipProvider>
      <div className="container mx-auto py-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-primary" />
              {str(t.title)}
            </h1>
            <p className="text-muted-foreground">{str(t.description)}</p>
          </div>
          <div className="flex items-center gap-2">
            <Select
              value={selectedSourceId || ''}
              onValueChange={setSelectedSourceId}
              disabled={loading}
            >
              <SelectTrigger className="w-64">
                <SelectValue placeholder="Select a source..." />
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
          </div>
        </div>

        {sources.length === 0 && !loading ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Database className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">{str(t.noSuggestionsAvailable)}</p>
            </CardContent>
          </Card>
        ) : (
          <Tabs defaultValue="generate" className="space-y-4">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="generate">{str(t.generationSettings)}</TabsTrigger>
              <TabsTrigger value="suggestions">{str(t.suggestions)}</TabsTrigger>
              <TabsTrigger value="export">{str(t.exportOptions)}</TabsTrigger>
            </TabsList>

            {/* Generation Settings Tab */}
            <TabsContent value="generate" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Strictness & Preset Card */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Settings2 className="h-5 w-5" />
                      {str(t.strictness)}
                    </CardTitle>
                    <CardDescription>
                      Configure rule generation strictness and presets
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Strictness */}
                    <div className="space-y-2">
                      <Label>{str(t.strictness)}</Label>
                      <Select value={strictness} onValueChange={(v) => setStrictness(v as StrictnessLevel)}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="loose">
                            <div className="flex flex-col items-start">
                              <span>{str(t.strictnessLoose)}</span>
                              <span className="text-xs text-muted-foreground">{str(t.strictnessLooseDesc)}</span>
                            </div>
                          </SelectItem>
                          <SelectItem value="medium">
                            <div className="flex flex-col items-start">
                              <span>{str(t.strictnessMedium)}</span>
                              <span className="text-xs text-muted-foreground">{str(t.strictnessMediumDesc)}</span>
                            </div>
                          </SelectItem>
                          <SelectItem value="strict">
                            <div className="flex flex-col items-start">
                              <span>{str(t.strictnessStrict)}</span>
                              <span className="text-xs text-muted-foreground">{str(t.strictnessStrictDesc)}</span>
                            </div>
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Preset */}
                    <div className="space-y-2">
                      <Label>{str(t.preset)}</Label>
                      <Select value={preset} onValueChange={(v) => setPreset(v as RulePreset)}>
                        <SelectTrigger>
                          <SelectValue placeholder={str(t.presetNone)} />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="">{str(t.presetNone)}</SelectItem>
                          {Object.entries(PRESET_INFO).map(([key, { icon: Icon, description }]) => (
                            <SelectItem key={key} value={key}>
                              <div className="flex items-center gap-2">
                                <Icon className="h-4 w-4" />
                                <span className="capitalize">{key.replace(/_/g, ' ')}</span>
                                <span className="text-xs text-muted-foreground">- {description}</span>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Min Confidence */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label>{str(t.minConfidence)}</Label>
                        <span className="text-sm font-medium">{minConfidence}%</span>
                      </div>
                      <Slider
                        value={[minConfidence]}
                        onValueChange={([v]) => setMinConfidence(v)}
                        min={0}
                        max={100}
                        step={5}
                      />
                      <p className="text-xs text-muted-foreground">{str(t.minConfidenceDesc)}</p>
                    </div>
                  </CardContent>
                </Card>

                {/* Category Selection Card */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Filter className="h-5 w-5" />
                      {str(t.includedCategories)}
                    </CardTitle>
                    <CardDescription>
                      Select which rule categories to include
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-3">
                      {ALL_CATEGORIES.map((category) => (
                        <div
                          key={category}
                          className={`flex items-center space-x-2 p-2 rounded-md border cursor-pointer transition-colors ${
                            includedCategories.includes(category)
                              ? CATEGORY_COLORS[category] || 'bg-primary/10'
                              : 'bg-muted/50'
                          }`}
                          onClick={() => toggleCategory(category)}
                        >
                          <Checkbox
                            id={`cat-${category}`}
                            checked={includedCategories.includes(category)}
                            onCheckedChange={() => toggleCategory(category)}
                          />
                          <label
                            htmlFor={`cat-${category}`}
                            className="text-sm cursor-pointer capitalize"
                          >
                            {category}
                          </label>
                        </div>
                      ))}
                    </div>

                    <Separator />

                    {/* Cross-Column Toggle */}
                    <div
                      className={`flex items-center justify-between p-3 rounded-md border cursor-pointer transition-colors ${
                        enableCrossColumn
                          ? 'bg-primary/10 border-primary/30'
                          : 'bg-muted/50'
                      }`}
                      onClick={() => setEnableCrossColumn(!enableCrossColumn)}
                    >
                      <div className="flex items-center gap-2">
                        <Checkbox
                          checked={enableCrossColumn}
                          onCheckedChange={() => setEnableCrossColumn(!enableCrossColumn)}
                        />
                        <div>
                          <p className="text-sm font-medium">{str(t.enableCrossColumn)}</p>
                          <p className="text-xs text-muted-foreground">
                            {str(t.enableCrossColumnDesc)}
                          </p>
                        </div>
                      </div>
                    </div>

                    <Separator />

                    {/* Generate Button */}
                    <Button
                      onClick={handleGenerate}
                      disabled={generating || !selectedSourceId}
                      className="w-full"
                      size="lg"
                    >
                      {generating ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          {str(t.analyzingProfile)}
                        </>
                      ) : (
                        <>
                          <Sparkles className="h-4 w-4 mr-2" />
                          {str(t.generateRules)}
                        </>
                      )}
                    </Button>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Suggestions Tab */}
            <TabsContent value="suggestions" className="space-y-4">
              {/* Stats */}
              {(suggestions.length > 0 || crossColumnSuggestions.length > 0) && (
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <StatsCard
                    title={str(t.singleColumnRules)}
                    value={suggestions.length}
                    icon={Sparkles}
                  />
                  <StatsCard
                    title={str(t.crossColumnRules)}
                    value={crossColumnSuggestions.length}
                    icon={TrendingUp}
                    variant="success"
                  />
                  <StatsCard
                    title={str(t.highConfidence)}
                    value={highConfidenceCount}
                    icon={TrendingUp}
                    variant="success"
                  />
                  <StatsCard
                    title={str(t.selected)}
                    value={totalSelectedCount}
                    icon={CheckSquare}
                    variant="warning"
                  />
                  <StatsCard
                    title={str(t.byCategory)}
                    value={Object.keys(byCategory).length}
                    icon={BarChart3}
                  />
                </div>
              )}

              <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
                {/* Suggestions List */}
                <Card className="lg:col-span-3">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="flex items-center gap-2">
                        <Sparkles className="h-5 w-5" />
                        {str(t.suggestions)}
                      </CardTitle>
                      <div className="flex items-center gap-2">
                        <Button variant="ghost" size="sm" onClick={selectAll}>
                          <CheckSquare className="h-4 w-4 mr-1" />
                          {str(t.selectAll)}
                        </Button>
                        <Button variant="ghost" size="sm" onClick={deselectAll}>
                          <Square className="h-4 w-4 mr-1" />
                          {str(t.deselectAll)}
                        </Button>
                      </div>
                    </div>
                    <CardDescription>
                      {selectedSource
                        ? `Rule suggestions for ${selectedSource.name}`
                        : 'Select a source and generate suggestions'}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {suggestions.length === 0 && crossColumnSuggestions.length === 0 ? (
                      <div className="text-center py-12">
                        <Sparkles className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                        <p className="text-muted-foreground">{str(t.noSuggestionsAvailable)}</p>
                        <Button onClick={handleGenerate} className="mt-4" disabled={generating}>
                          <Sparkles className="h-4 w-4 mr-2" />
                          {str(t.generateRules)}
                        </Button>
                      </div>
                    ) : (
                      <>
                        {/* Search and Filter */}
                        <div className="flex items-center gap-2 mb-4">
                          <div className="relative flex-1">
                            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                            <Input
                              placeholder={str(t.searchSuggestions)}
                              value={searchTerm}
                              onChange={(e) => setSearchTerm(e.target.value)}
                              className="pl-8"
                            />
                          </div>
                          {ruleViewTab === 'single' && (
                            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                              <SelectTrigger className="w-[160px]">
                                <Filter className="h-4 w-4 mr-2" />
                                <SelectValue placeholder={str(t.allCategories)} />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="all">{str(t.allCategories)}</SelectItem>
                                {availableCategories.map((cat) => (
                                  <SelectItem key={cat} value={cat}>
                                    <span className="capitalize">{cat}</span>
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          )}
                        </div>

                        {/* Single/Cross-Column Tabs */}
                        <Tabs value={ruleViewTab} onValueChange={setRuleViewTab} className="mb-4">
                          <TabsList className="grid w-full grid-cols-2">
                            <TabsTrigger value="single" className="flex items-center gap-2">
                              <Sparkles className="h-4 w-4" />
                              {str(t.singleColumnRules)} ({suggestions.length})
                            </TabsTrigger>
                            <TabsTrigger value="cross" className="flex items-center gap-2">
                              <TrendingUp className="h-4 w-4" />
                              {str(t.crossColumnRules)} ({crossColumnSuggestions.length})
                            </TabsTrigger>
                          </TabsList>

                          {/* Single-Column Rules Tab */}
                          <TabsContent value="single" className="mt-4">
                            <ScrollArea className="h-[450px]">
                              <div className="space-y-2 pr-4">
                                {filteredSuggestions.length === 0 ? (
                                  <p className="text-center text-muted-foreground py-8">
                                    {str(t.noSuggestionsMatch)}
                                  </p>
                                ) : (
                                  filteredSuggestions.map((suggestion) => (
                                    <RuleSuggestionCard
                                      key={suggestion.id}
                                      suggestion={{
                                        ...suggestion,
                                        column_name: suggestion.column,
                                        parameters: suggestion.params,
                                        priority: suggestion.severity_suggestion === 'critical' ? 1 : 2,
                                      }}
                                      selected={selectedIds.has(suggestion.id)}
                                      onToggle={toggleSelection}
                                    />
                                  ))
                                )}
                              </div>
                            </ScrollArea>
                          </TabsContent>

                          {/* Cross-Column Rules Tab */}
                          <TabsContent value="cross" className="mt-4">
                            {crossColumnSuggestions.length === 0 ? (
                              <div className="text-center py-8">
                                <TrendingUp className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                                <p className="text-muted-foreground">
                                  {str(t.crossColumnDescription)}
                                </p>
                                <p className="text-sm text-muted-foreground mt-2">
                                  Enable cross-column rules in Generation Settings and regenerate.
                                </p>
                              </div>
                            ) : (
                              <ScrollArea className="h-[450px]">
                                <div className="space-y-2 pr-4">
                                  {filteredCrossColumnSuggestions.length === 0 ? (
                                    <p className="text-center text-muted-foreground py-8">
                                      {str(t.noSuggestionsMatch)}
                                    </p>
                                  ) : (
                                    filteredCrossColumnSuggestions.map((suggestion) => (
                                      <CrossColumnRuleCard
                                        key={suggestion.id}
                                        suggestion={suggestion}
                                        selected={selectedCrossColumnIds.has(suggestion.id)}
                                        onToggle={toggleCrossColumnSelection}
                                      />
                                    ))
                                  )}
                                </div>
                              </ScrollArea>
                            )}
                          </TabsContent>
                        </Tabs>
                      </>
                    )}
                  </CardContent>
                </Card>

                {/* Category Breakdown Sidebar */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <BarChart3 className="h-5 w-5" />
                      {ruleViewTab === 'single' ? str(t.byCategory) : str(t.byCrossColumnType)}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {ruleViewTab === 'single' ? (
                      Object.keys(byCategory).length > 0 ? (
                        <CategoryBreakdown byCategory={byCategory} t={t} />
                      ) : (
                        <p className="text-sm text-muted-foreground text-center py-4">
                          Generate suggestions to see breakdown
                        </p>
                      )
                    ) : Object.keys(byCrossColumnType).length > 0 ? (
                      <CategoryBreakdown byCategory={byCrossColumnType} t={t} />
                    ) : (
                      <p className="text-sm text-muted-foreground text-center py-4">
                        Enable cross-column rules to see breakdown
                      </p>
                    )}
                  </CardContent>
                </Card>
              </div>

              {/* Apply Button */}
              {(suggestions.length > 0 || crossColumnSuggestions.length > 0) && (
                <div className="flex justify-end">
                  <Button
                    onClick={handleApply}
                    disabled={applying || totalSelectedCount === 0}
                    size="lg"
                  >
                    {applying ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        {str(t.applying)}
                      </>
                    ) : (
                      <>
                        <CheckSquare className="h-4 w-4 mr-2" />
                        {str(t.applyRules)} ({totalSelectedCount})
                      </>
                    )}
                  </Button>
                </div>
              )}
            </TabsContent>

            {/* Export Tab */}
            <TabsContent value="export" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Download className="h-5 w-5" />
                    {str(t.exportOptions)}
                  </CardTitle>
                  <CardDescription>
                    Export selected rules in various formats
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {totalSelectedCount === 0 ? (
                    <div className="text-center py-8">
                      <AlertCircle className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                      <p className="text-muted-foreground">
                        Select suggestions first to export
                      </p>
                    </div>
                  ) : (
                    <>
                      {/* Format Selection */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {[
                          { format: 'yaml' as const, icon: FileText, label: 'YAML' },
                          { format: 'json' as const, icon: FileJson, label: 'JSON' },
                          { format: 'python' as const, icon: FileCode, label: 'Python' },
                          { format: 'toml' as const, icon: FileText, label: 'TOML' },
                        ].map(({ format, icon: Icon, label }) => (
                          <Card
                            key={format}
                            className={`cursor-pointer transition-all hover:border-primary/50 ${
                              exportFormat === format ? 'border-primary bg-primary/5' : ''
                            }`}
                            onClick={() => setExportFormat(format)}
                          >
                            <CardContent className="p-4 text-center">
                              <Icon className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                              <p className="font-medium">{label}</p>
                            </CardContent>
                          </Card>
                        ))}
                      </div>

                      {/* Export Actions */}
                      <div className="flex items-center justify-between border-t pt-4">
                        <p className="text-sm text-muted-foreground">
                          {totalSelectedCount} {str(t.selected)} rules ready to export
                          ({selectedIds.size} single + {selectedCrossColumnIds.size} cross-column)
                        </p>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            onClick={handleCopy}
                          >
                            {copied ? (
                              <>
                                <Check className="h-4 w-4 mr-2" />
                                {str(t.copied)}
                              </>
                            ) : (
                              <>
                                <Copy className="h-4 w-4 mr-2" />
                                {str(t.copyToClipboard)}
                              </>
                            )}
                          </Button>
                          <Button
                            onClick={() => handleExport(exportFormat)}
                            disabled={exporting}
                          >
                            {exporting ? (
                              <>
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                {str(t.exporting)}
                              </>
                            ) : (
                              <>
                                <Download className="h-4 w-4 mr-2" />
                                {str(t.downloadRules)} ({exportFormat.toUpperCase()})
                              </>
                            )}
                          </Button>
                        </div>
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        )}
      </div>
    </TooltipProvider>
  )
}
