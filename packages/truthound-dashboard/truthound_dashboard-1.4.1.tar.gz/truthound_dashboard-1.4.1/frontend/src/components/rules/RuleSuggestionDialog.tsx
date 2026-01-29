/**
 * RuleSuggestionDialog - Dialog for viewing and applying rule suggestions
 * with advanced options (strictness, presets, export formats).
 */

import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Checkbox } from '@/components/ui/checkbox'
import { ScrollArea } from '@/components/ui/scroll-area'
import { RuleSuggestionCard } from './RuleSuggestionCard'
import { useIntlayer } from 'react-intlayer'
import { str } from '@/lib/intlayer-utils'
import {
  Loader2,
  Sparkles,
  Search,
  CheckSquare,
  Square,
  Filter,
  Settings2,
  ChevronDown,
  Download,
  Copy,
  Check,
  FileCode,
  FileJson,
  FileText,
} from 'lucide-react'
import type {
  SuggestedRule,
  StrictnessLevel,
  RulePreset,
  RuleExportFormat,
  RuleCategory,
  RuleSuggestionRequest,
} from '@/api/client'

interface RuleSuggestionDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  sourceName: string
  sourceId: string
  suggestions: SuggestedRule[]
  isLoading?: boolean
  onApply: (selectedIds: string[]) => Promise<void>
  onGenerate: (options: RuleSuggestionRequest) => Promise<void>
  onExport?: (format: RuleExportFormat, suggestions: SuggestedRule[]) => Promise<string>
}

// Category colors for badges
const CATEGORY_COLORS: Record<string, string> = {
  completeness: 'bg-blue-500/10 text-blue-500',
  uniqueness: 'bg-purple-500/10 text-purple-500',
  distribution: 'bg-green-500/10 text-green-500',
  schema: 'bg-orange-500/10 text-orange-500',
  stats: 'bg-cyan-500/10 text-cyan-500',
  pattern: 'bg-amber-500/10 text-amber-500',
}

// All available categories
const ALL_CATEGORIES: RuleCategory[] = [
  'schema',
  'completeness',
  'uniqueness',
  'distribution',
  'stats',
  'pattern',
]

export function RuleSuggestionDialog({
  open,
  onOpenChange,
  sourceName,
  sourceId,
  suggestions,
  isLoading = false,
  onApply,
  onGenerate,
  onExport,
}: RuleSuggestionDialogProps) {
  const content = useIntlayer('ruleSuggestions')

  // Selection state
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [searchTerm, setSearchTerm] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [isApplying, setIsApplying] = useState(false)

  // Advanced options state
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [strictness, setStrictness] = useState<StrictnessLevel>('medium')
  const [preset, setPreset] = useState<RulePreset | ''>('')
  const [minConfidence, setMinConfidence] = useState(50)
  const [includedCategories, setIncludedCategories] = useState<RuleCategory[]>([...ALL_CATEGORIES])

  // Export state
  const [exportFormat, setExportFormat] = useState<RuleExportFormat>('yaml')
  const [copied, setCopied] = useState(false)
  const [isExporting, setIsExporting] = useState(false)

  // Reset selection when dialog opens with new suggestions
  useEffect(() => {
    if (open && suggestions.length > 0) {
      // Pre-select high confidence suggestions
      const highConfidence = suggestions
        .filter((s) => s.confidence >= 0.85)
        .map((s) => s.id)
      setSelectedIds(new Set(highConfidence))
    }
  }, [open, suggestions])

  const toggleSelection = (id: string) => {
    const newSelected = new Set(selectedIds)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedIds(newSelected)
  }

  const selectAll = () => {
    setSelectedIds(new Set(filteredSuggestions.map((s) => s.id)))
  }

  const deselectAll = () => {
    setSelectedIds(new Set())
  }

  const handleApply = async () => {
    if (selectedIds.size === 0) return
    setIsApplying(true)
    try {
      await onApply(Array.from(selectedIds))
      onOpenChange(false)
    } finally {
      setIsApplying(false)
    }
  }

  const handleGenerate = async () => {
    const options: RuleSuggestionRequest = {
      strictness,
      min_confidence: minConfidence / 100,
      include_categories: includedCategories.length < ALL_CATEGORIES.length ? includedCategories : undefined,
    }
    if (preset) {
      options.preset = preset
    }
    await onGenerate(options)
  }

  const handleExport = async (format: RuleExportFormat) => {
    if (!onExport || selectedIds.size === 0) return
    setIsExporting(true)
    try {
      const selectedSuggestions = suggestions.filter((s) => selectedIds.has(s.id))
      const content = await onExport(format, selectedSuggestions)

      // Download file
      const blob = new Blob([content], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `rules.${format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } finally {
      setIsExporting(false)
    }
  }

  const handleCopyToClipboard = async () => {
    if (!onExport || selectedIds.size === 0) return
    try {
      const selectedSuggestions = suggestions.filter((s) => selectedIds.has(s.id))
      const exportContent = await onExport(exportFormat, selectedSuggestions)
      await navigator.clipboard.writeText(exportContent)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const toggleCategory = (category: RuleCategory) => {
    setIncludedCategories((prev) =>
      prev.includes(category)
        ? prev.filter((c) => c !== category)
        : [...prev, category]
    )
  }

  // Get unique categories from suggestions
  const availableCategories = [...new Set(suggestions.map((s) => s.category))]

  // Filter suggestions
  const filteredSuggestions = suggestions.filter((s) => {
    const matchesSearch =
      searchTerm === '' ||
      s.validator_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.column?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.reason.toLowerCase().includes(searchTerm.toLowerCase())

    const matchesCategory = categoryFilter === 'all' || s.category === categoryFilter

    return matchesSearch && matchesCategory
  })

  const highConfidenceCount = suggestions.filter((s) => s.confidence >= 0.85).length

  // Calculate category breakdown
  const categoryBreakdown: Record<string, number> = {}
  suggestions.forEach((s) => {
    categoryBreakdown[s.category] = (categoryBreakdown[s.category] || 0) + 1
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[85vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            {str(content.title)}
          </DialogTitle>
          <DialogDescription>
            {str(content.description).replace('{source}', sourceName)}
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="suggestions" className="flex-1 flex flex-col min-h-0">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="suggestions">{str(content.suggestions)}</TabsTrigger>
            <TabsTrigger value="settings">{str(content.advancedOptions)}</TabsTrigger>
          </TabsList>

          {/* Suggestions Tab */}
          <TabsContent value="suggestions" className="flex-1 flex flex-col min-h-0 mt-4">
            {isLoading ? (
              <div className="flex-1 flex items-center justify-center py-12">
                <div className="flex flex-col items-center gap-2">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                  <p className="text-sm text-muted-foreground">{str(content.analyzingProfile)}</p>
                </div>
              </div>
            ) : suggestions.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center py-12 gap-4">
                <p className="text-muted-foreground">{str(content.noSuggestionsAvailable)}</p>
                <Button onClick={handleGenerate}>
                  <Sparkles className="h-4 w-4 mr-2" />
                  {str(content.generateRules)}
                </Button>
              </div>
            ) : (
              <>
                {/* Stats and Filters */}
                <div className="flex items-center justify-between gap-4 py-2 border-b">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant="secondary">
                      {suggestions.length} {str(content.suggestions)}
                    </Badge>
                    <Badge variant="outline" className="bg-green-500/10 text-green-500">
                      {highConfidenceCount} {str(content.highConfidence)}
                    </Badge>
                    {/* Category breakdown */}
                    {Object.entries(categoryBreakdown).slice(0, 3).map(([cat, count]) => (
                      <Badge
                        key={cat}
                        variant="outline"
                        className={CATEGORY_COLORS[cat] || 'bg-muted'}
                      >
                        {cat}: {count}
                      </Badge>
                    ))}
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={selectAll}
                      className="h-8 px-2"
                    >
                      <CheckSquare className="h-4 w-4 mr-1" />
                      {str(content.selectAll)}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={deselectAll}
                      className="h-8 px-2"
                    >
                      <Square className="h-4 w-4 mr-1" />
                      {str(content.deselectAll)}
                    </Button>
                  </div>
                </div>

                {/* Search and Filter */}
                <div className="flex items-center gap-2 py-2">
                  <div className="relative flex-1">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder={str(content.searchSuggestions)}
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-8 h-9"
                    />
                  </div>
                  <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                    <SelectTrigger className="w-[160px] h-9">
                      <Filter className="h-4 w-4 mr-2" />
                      <SelectValue placeholder={str(content.allCategories)} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">{str(content.allCategories)}</SelectItem>
                      {availableCategories.map((cat) => (
                        <SelectItem key={cat} value={cat}>
                          {cat}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Suggestions List */}
                <ScrollArea className="flex-1 min-h-[200px] max-h-[350px]">
                  <div className="space-y-2 py-2 pr-4">
                    {filteredSuggestions.length === 0 ? (
                      <p className="text-center text-muted-foreground py-8">
                        {str(content.noSuggestionsMatch)}
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
              </>
            )}
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="flex-1 flex flex-col gap-6 mt-4 overflow-auto">
            {/* Generation Settings */}
            <div className="space-y-4">
              <h4 className="font-medium flex items-center gap-2">
                <Settings2 className="h-4 w-4" />
                {str(content.generationSettings)}
              </h4>

              {/* Strictness */}
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>{str(content.strictness)}</Label>
                  <Select value={strictness} onValueChange={(v) => setStrictness(v as StrictnessLevel)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="loose">
                        <div className="flex flex-col">
                          <span>{str(content.strictnessLoose)}</span>
                          <span className="text-xs text-muted-foreground">{str(content.strictnessLooseDesc)}</span>
                        </div>
                      </SelectItem>
                      <SelectItem value="medium">
                        <div className="flex flex-col">
                          <span>{str(content.strictnessMedium)}</span>
                          <span className="text-xs text-muted-foreground">{str(content.strictnessMediumDesc)}</span>
                        </div>
                      </SelectItem>
                      <SelectItem value="strict">
                        <div className="flex flex-col">
                          <span>{str(content.strictnessStrict)}</span>
                          <span className="text-xs text-muted-foreground">{str(content.strictnessStrictDesc)}</span>
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Preset */}
                <div className="space-y-2">
                  <Label>{str(content.preset)}</Label>
                  <Select value={preset} onValueChange={(v) => setPreset(v as RulePreset)}>
                    <SelectTrigger>
                      <SelectValue placeholder={str(content.presetNone)} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">{str(content.presetNone)}</SelectItem>
                      <SelectItem value="default">{str(content.presetDefault)}</SelectItem>
                      <SelectItem value="strict">{str(content.presetStrict)}</SelectItem>
                      <SelectItem value="loose">{str(content.presetLoose)}</SelectItem>
                      <SelectItem value="minimal">{str(content.presetMinimal)}</SelectItem>
                      <SelectItem value="comprehensive">{str(content.presetComprehensive)}</SelectItem>
                      <SelectItem value="ci_cd">{str(content.presetCiCd)}</SelectItem>
                      <SelectItem value="schema_only">{str(content.presetSchemaOnly)}</SelectItem>
                      <SelectItem value="format_only">{str(content.presetFormatOnly)}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Min Confidence */}
                <div className="space-y-2">
                  <Label>{str(content.minConfidence)}: {minConfidence}%</Label>
                  <Slider
                    value={[minConfidence]}
                    onValueChange={([v]) => setMinConfidence(v)}
                    min={0}
                    max={100}
                    step={5}
                    className="mt-2"
                  />
                </div>
              </div>

              {/* Category Selection */}
              <div className="space-y-2">
                <Label>{str(content.includedCategories)}</Label>
                <div className="flex flex-wrap gap-2">
                  {ALL_CATEGORIES.map((category) => (
                    <div
                      key={category}
                      className="flex items-center space-x-2"
                    >
                      <Checkbox
                        id={`cat-${category}`}
                        checked={includedCategories.includes(category)}
                        onCheckedChange={() => toggleCategory(category)}
                      />
                      <label
                        htmlFor={`cat-${category}`}
                        className="text-sm cursor-pointer"
                      >
                        {category}
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              {/* Generate Button */}
              <Button onClick={handleGenerate} disabled={isLoading} className="w-full">
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    {str(content.analyzingProfile)}
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-2" />
                    {str(content.generateRules)}
                  </>
                )}
              </Button>
            </div>

            {/* Export Options */}
            {suggestions.length > 0 && selectedIds.size > 0 && onExport && (
              <div className="space-y-4 border-t pt-4">
                <h4 className="font-medium flex items-center gap-2">
                  <Download className="h-4 w-4" />
                  {str(content.exportOptions)}
                </h4>

                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <Label>{str(content.exportFormat)}</Label>
                    <Select
                      value={exportFormat}
                      onValueChange={(v) => setExportFormat(v as RuleExportFormat)}
                    >
                      <SelectTrigger className="mt-2">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="yaml">
                          <div className="flex items-center gap-2">
                            <FileText className="h-4 w-4" />
                            YAML
                          </div>
                        </SelectItem>
                        <SelectItem value="json">
                          <div className="flex items-center gap-2">
                            <FileJson className="h-4 w-4" />
                            JSON
                          </div>
                        </SelectItem>
                        <SelectItem value="python">
                          <div className="flex items-center gap-2">
                            <FileCode className="h-4 w-4" />
                            Python
                          </div>
                        </SelectItem>
                        <SelectItem value="toml">
                          <div className="flex items-center gap-2">
                            <FileText className="h-4 w-4" />
                            TOML
                          </div>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex gap-2 mt-6">
                    <Button
                      variant="outline"
                      onClick={() => handleExport(exportFormat)}
                      disabled={isExporting}
                    >
                      {isExporting ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Download className="h-4 w-4 mr-2" />
                      )}
                      {str(content.downloadRules)}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={handleCopyToClipboard}
                    >
                      {copied ? (
                        <>
                          <Check className="h-4 w-4 mr-2" />
                          {str(content.copied)}
                        </>
                      ) : (
                        <>
                          <Copy className="h-4 w-4 mr-2" />
                          {str(content.copyToClipboard)}
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </TabsContent>
        </Tabs>

        <DialogFooter className="border-t pt-4">
          <div className="flex items-center justify-between w-full">
            <p className="text-sm text-muted-foreground">
              {selectedIds.size} / {suggestions.length} {str(content.selected)}
            </p>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleApply}
                disabled={selectedIds.size === 0 || isApplying}
              >
                {isApplying ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    {str(content.applying)}
                  </>
                ) : (
                  <>
                    {str(content.applyRules)} ({selectedIds.size})
                  </>
                )}
              </Button>
            </div>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
