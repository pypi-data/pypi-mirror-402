/**
 * TemplateLibrary - Pre-built templates for notification configurations
 *
 * Provides ready-to-use templates for:
 * - Routing Rules
 * - Deduplication Configs
 * - Throttling Configs
 * - Escalation Policies
 *
 * Templates are extensible via registry pattern
 */

import { useState, useMemo } from 'react'
import {
  BookOpen,
  Route,
  Copy,
  Gauge,
  AlertTriangle,
  Search,
  ChevronRight,
  Check,
  Star,
  Zap,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'

// =============================================================================
// Types
// =============================================================================

export type TemplateCategory = 'routing' | 'deduplication' | 'throttling' | 'escalation'

export interface Template<T = Record<string, unknown>> {
  id: string
  name: string
  description: string
  category: TemplateCategory
  tags: string[]
  config: T
  isPopular?: boolean
  isNew?: boolean
}

// =============================================================================
// Template Registry (Extensible)
// =============================================================================

class TemplateRegistryClass {
  private templates: Map<string, Template> = new Map()

  register(template: Template): void {
    this.templates.set(template.id, template)
  }

  registerMany(templates: Template[]): void {
    templates.forEach((t) => this.register(t))
  }

  get(id: string): Template | undefined {
    return this.templates.get(id)
  }

  getAll(): Template[] {
    return Array.from(this.templates.values())
  }

  getByCategory(category: TemplateCategory): Template[] {
    return this.getAll().filter((t) => t.category === category)
  }

  search(query: string, category?: TemplateCategory): Template[] {
    const q = query.toLowerCase()
    return this.getAll().filter((t) => {
      if (category && t.category !== category) return false
      return (
        t.name.toLowerCase().includes(q) ||
        t.description.toLowerCase().includes(q) ||
        t.tags.some((tag) => tag.toLowerCase().includes(q))
      )
    })
  }
}

export const TemplateRegistry = new TemplateRegistryClass()

// =============================================================================
// Pre-built Templates
// =============================================================================

// Routing Rule Templates
const routingTemplates: Template[] = [
  {
    id: 'routing-critical-production',
    name: 'Critical Production Alerts',
    description: 'Route critical severity issues in production to PagerDuty',
    category: 'routing',
    tags: ['critical', 'production', 'pagerduty'],
    isPopular: true,
    config: {
      type: 'all_of',
      rules: [
        { type: 'severity', min_severity: 'critical' },
        { type: 'tag', tags: ['production'], require_all: false },
      ],
    },
  },
  {
    id: 'routing-high-business-hours',
    name: 'High Severity - Business Hours',
    description: 'Route high severity issues during business hours (9am-5pm, Mon-Fri)',
    category: 'routing',
    tags: ['high', 'business-hours', 'slack'],
    isPopular: true,
    config: {
      type: 'all_of',
      rules: [
        { type: 'severity', min_severity: 'high' },
        { type: 'time_window', start_hour: 9, end_hour: 17, weekdays: [0, 1, 2, 3, 4] },
      ],
    },
  },
  {
    id: 'routing-low-pass-rate',
    name: 'Low Pass Rate Alert',
    description: 'Alert when pass rate drops below 80%',
    category: 'routing',
    tags: ['pass-rate', 'quality', 'threshold'],
    config: {
      type: 'pass_rate',
      max_pass_rate: 0.8,
    },
  },
  {
    id: 'routing-many-issues',
    name: 'High Issue Count',
    description: 'Alert when issue count exceeds threshold',
    category: 'routing',
    tags: ['issues', 'threshold'],
    config: {
      type: 'issue_count',
      min_count: 10,
    },
  },
  {
    id: 'routing-staging-only',
    name: 'Staging Environment Only',
    description: 'Route staging environment notifications to separate channel',
    category: 'routing',
    tags: ['staging', 'environment'],
    config: {
      type: 'all_of',
      rules: [
        { type: 'tag', tags: ['staging'] },
        { type: 'severity', min_severity: 'medium' },
      ],
    },
  },
  {
    id: 'routing-exclude-test',
    name: 'Exclude Test Data',
    description: 'Route all alerts except those tagged as test',
    category: 'routing',
    tags: ['exclude', 'test', 'filter'],
    config: {
      type: 'all_of',
      rules: [
        { type: 'severity', min_severity: 'medium' },
        { type: 'not', rule: { type: 'tag', tags: ['test', 'sandbox'] } },
      ],
    },
  },
  {
    id: 'routing-data-asset-pattern',
    name: 'Parquet File Validation',
    description: 'Route issues from parquet file validations',
    category: 'routing',
    tags: ['parquet', 'data-asset'],
    config: {
      type: 'data_asset',
      pattern: '*.parquet',
    },
  },
  {
    id: 'routing-after-hours-escalation',
    name: 'After Hours Escalation',
    description: 'Escalate critical issues outside business hours',
    category: 'routing',
    tags: ['after-hours', 'critical', 'escalation'],
    isNew: true,
    config: {
      type: 'all_of',
      rules: [
        { type: 'severity', min_severity: 'critical' },
        {
          type: 'not',
          rule: { type: 'time_window', start_hour: 9, end_hour: 17, weekdays: [0, 1, 2, 3, 4] },
        },
      ],
    },
  },
]

// Deduplication Templates
const deduplicationTemplates: Template[] = [
  {
    id: 'dedup-5min-sliding',
    name: '5 Minute Sliding Window',
    description: 'Deduplicate notifications within a 5-minute rolling window',
    category: 'deduplication',
    tags: ['5min', 'sliding', 'realtime'],
    isPopular: true,
    config: {
      strategy: 'sliding',
      policy: 'severity',
      window_seconds: 300,
    },
  },
  {
    id: 'dedup-hourly-tumbling',
    name: 'Hourly Batch',
    description: 'Deduplicate within 1-hour fixed windows',
    category: 'deduplication',
    tags: ['hourly', 'tumbling', 'batch'],
    config: {
      strategy: 'tumbling',
      policy: 'basic',
      window_seconds: 3600,
    },
  },
  {
    id: 'dedup-session-burst',
    name: 'Session-based (Burst Handling)',
    description: 'Handle notification bursts with session windows (5min gap)',
    category: 'deduplication',
    tags: ['session', 'burst', 'gap'],
    isNew: true,
    config: {
      strategy: 'session',
      policy: 'issue_based',
      window_seconds: 300,
    },
  },
  {
    id: 'dedup-strict-15min',
    name: 'Strict 15 Minute',
    description: 'Strict deduplication with all fields for 15 minutes',
    category: 'deduplication',
    tags: ['strict', '15min', 'comprehensive'],
    config: {
      strategy: 'sliding',
      policy: 'strict',
      window_seconds: 900,
    },
  },
  {
    id: 'dedup-adaptive',
    name: 'Adaptive (Dynamic)',
    description: 'Automatically adjust window size based on load',
    category: 'deduplication',
    tags: ['adaptive', 'dynamic', 'auto'],
    config: {
      strategy: 'adaptive',
      policy: 'severity',
      window_seconds: 300,
    },
  },
]

// Throttling Templates
const throttlingTemplates: Template[] = [
  {
    id: 'throttle-slack-default',
    name: 'Slack Default',
    description: 'Standard rate limits for Slack (10/min, 100/hour)',
    category: 'throttling',
    tags: ['slack', 'standard'],
    isPopular: true,
    config: {
      per_minute: 10,
      per_hour: 100,
      per_day: 500,
      burst_allowance: 1.5,
    },
  },
  {
    id: 'throttle-pagerduty',
    name: 'PagerDuty Conservative',
    description: 'Conservative limits for PagerDuty to avoid alert fatigue',
    category: 'throttling',
    tags: ['pagerduty', 'conservative', 'critical'],
    isPopular: true,
    config: {
      per_minute: 5,
      per_hour: 30,
      per_day: 100,
      burst_allowance: 1.2,
    },
  },
  {
    id: 'throttle-email-batch',
    name: 'Email Batch',
    description: 'Email-friendly rate limits (batch-oriented)',
    category: 'throttling',
    tags: ['email', 'batch'],
    config: {
      per_minute: 2,
      per_hour: 20,
      per_day: 100,
      burst_allowance: 1.0,
    },
  },
  {
    id: 'throttle-aggressive',
    name: 'Aggressive Rate Limiting',
    description: 'Very strict limits for high-noise environments',
    category: 'throttling',
    tags: ['strict', 'noise-reduction'],
    config: {
      per_minute: 3,
      per_hour: 20,
      per_day: 50,
      burst_allowance: 1.0,
    },
  },
  {
    id: 'throttle-high-volume',
    name: 'High Volume',
    description: 'Higher limits for high-throughput environments',
    category: 'throttling',
    tags: ['high-volume', 'throughput'],
    isNew: true,
    config: {
      per_minute: 30,
      per_hour: 500,
      per_day: 2000,
      burst_allowance: 2.0,
    },
  },
]

// Escalation Templates
const escalationTemplates: Template[] = [
  {
    id: 'escalation-24x7',
    name: '24x7 On-Call',
    description: 'Standard 24x7 escalation: immediate → 15min → 30min',
    category: 'escalation',
    tags: ['24x7', 'oncall', 'standard'],
    isPopular: true,
    config: {
      levels: [
        { level: 1, delay_minutes: 0, targets: [{ type: 'oncall', identifier: 'primary-oncall', channel: 'slack' }] },
        { level: 2, delay_minutes: 15, targets: [{ type: 'group', identifier: 'team-leads', channel: 'pagerduty' }] },
        { level: 3, delay_minutes: 30, targets: [{ type: 'user', identifier: 'manager', channel: 'phone' }] },
      ],
      auto_resolve_on_success: true,
      max_escalations: 3,
    },
  },
  {
    id: 'escalation-business-hours',
    name: 'Business Hours Only',
    description: 'Escalation during business hours with email fallback',
    category: 'escalation',
    tags: ['business-hours', 'email'],
    config: {
      levels: [
        { level: 1, delay_minutes: 0, targets: [{ type: 'channel', identifier: 'alerts-channel', channel: 'slack' }] },
        { level: 2, delay_minutes: 30, targets: [{ type: 'group', identifier: 'data-team', channel: 'email' }] },
      ],
      auto_resolve_on_success: true,
      max_escalations: 2,
    },
  },
  {
    id: 'escalation-critical-fast',
    name: 'Critical Fast Escalation',
    description: 'Fast escalation for critical issues (5min intervals)',
    category: 'escalation',
    tags: ['critical', 'fast', 'urgent'],
    isNew: true,
    config: {
      levels: [
        { level: 1, delay_minutes: 0, targets: [{ type: 'oncall', identifier: 'primary', channel: 'pagerduty' }] },
        { level: 2, delay_minutes: 5, targets: [{ type: 'oncall', identifier: 'secondary', channel: 'pagerduty' }] },
        { level: 3, delay_minutes: 10, targets: [{ type: 'user', identifier: 'incident-commander', channel: 'phone' }] },
      ],
      auto_resolve_on_success: false,
      max_escalations: 5,
    },
  },
  {
    id: 'escalation-simple',
    name: 'Simple Two-Level',
    description: 'Basic two-level escalation for smaller teams',
    category: 'escalation',
    tags: ['simple', 'small-team'],
    config: {
      levels: [
        { level: 1, delay_minutes: 0, targets: [{ type: 'channel', identifier: 'alerts', channel: 'slack' }] },
        { level: 2, delay_minutes: 60, targets: [{ type: 'user', identifier: 'admin', channel: 'email' }] },
      ],
      auto_resolve_on_success: true,
      max_escalations: 2,
    },
  },
]

// Register all templates
TemplateRegistry.registerMany([
  ...routingTemplates,
  ...deduplicationTemplates,
  ...throttlingTemplates,
  ...escalationTemplates,
])

// =============================================================================
// Component
// =============================================================================

interface TemplateLibraryProps {
  category?: TemplateCategory
  onSelect: (template: Template) => void
  className?: string
}

const CATEGORY_INFO: Record<TemplateCategory, { icon: React.ReactNode; label: string; color: string }> = {
  routing: { icon: <Route className="h-4 w-4" />, label: 'Routing', color: 'text-blue-500' },
  deduplication: { icon: <Copy className="h-4 w-4" />, label: 'Deduplication', color: 'text-green-500' },
  throttling: { icon: <Gauge className="h-4 w-4" />, label: 'Throttling', color: 'text-orange-500' },
  escalation: { icon: <AlertTriangle className="h-4 w-4" />, label: 'Escalation', color: 'text-red-500' },
}

export function TemplateLibrary({ category, onSelect, className }: TemplateLibraryProps) {
  const [search, setSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<TemplateCategory | 'all'>(category || 'all')
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null)
  const [previewOpen, setPreviewOpen] = useState(false)

  const filteredTemplates = useMemo(() => {
    let templates = search
      ? TemplateRegistry.search(search)
      : TemplateRegistry.getAll()

    if (selectedCategory !== 'all') {
      templates = templates.filter((t) => t.category === selectedCategory)
    }

    // Sort: popular first, then new, then alphabetically
    return templates.sort((a, b) => {
      if (a.isPopular && !b.isPopular) return -1
      if (!a.isPopular && b.isPopular) return 1
      if (a.isNew && !b.isNew) return -1
      if (!a.isNew && b.isNew) return 1
      return a.name.localeCompare(b.name)
    })
  }, [search, selectedCategory])

  const handleTemplateClick = (template: Template) => {
    setSelectedTemplate(template)
    setPreviewOpen(true)
  }

  const handleUseTemplate = () => {
    if (selectedTemplate) {
      onSelect(selectedTemplate)
      setPreviewOpen(false)
    }
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <BookOpen className="h-4 w-4" />
          Template Library
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search templates..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8"
          />
        </div>

        {/* Category Filter */}
        {!category && (
          <Tabs value={selectedCategory} onValueChange={(v) => setSelectedCategory(v as TemplateCategory | 'all')}>
            <TabsList className="grid w-full grid-cols-5 h-8">
              <TabsTrigger value="all" className="text-xs h-6">All</TabsTrigger>
              {(Object.keys(CATEGORY_INFO) as TemplateCategory[]).map((cat) => (
                <TabsTrigger key={cat} value={cat} className="text-xs h-6">
                  {CATEGORY_INFO[cat].label}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
        )}

        {/* Template List */}
        <ScrollArea className="h-[300px]">
          <div className="space-y-2 pr-4">
            {filteredTemplates.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                No templates found
              </p>
            ) : (
              filteredTemplates.map((template) => (
                <div
                  key={template.id}
                  className="flex items-center justify-between p-3 rounded-md border hover:bg-muted/50 cursor-pointer transition-colors"
                  onClick={() => handleTemplateClick(template)}
                >
                  <div className="flex items-start gap-3">
                    <div className={CATEGORY_INFO[template.category].color}>
                      {CATEGORY_INFO[template.category].icon}
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">{template.name}</span>
                        {template.isPopular && (
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger>
                                <Star className="h-3 w-3 text-yellow-500 fill-yellow-500" />
                              </TooltipTrigger>
                              <TooltipContent>Popular template</TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        )}
                        {template.isNew && (
                          <Badge variant="secondary" className="text-[10px] h-4 px-1">
                            <Zap className="h-2 w-2 mr-0.5" />
                            New
                          </Badge>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground line-clamp-1">
                        {template.description}
                      </p>
                      <div className="flex gap-1 flex-wrap">
                        {template.tags.slice(0, 3).map((tag) => (
                          <Badge key={tag} variant="outline" className="text-[10px] h-4 px-1">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </CardContent>

      {/* Preview Dialog */}
      <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedTemplate && (
                <span className={CATEGORY_INFO[selectedTemplate.category].color}>
                  {CATEGORY_INFO[selectedTemplate.category].icon}
                </span>
              )}
              {selectedTemplate?.name}
            </DialogTitle>
            <DialogDescription>{selectedTemplate?.description}</DialogDescription>
          </DialogHeader>

          {selectedTemplate && (
            <div className="space-y-4">
              {/* Tags */}
              <div className="flex gap-1 flex-wrap">
                {selectedTemplate.tags.map((tag) => (
                  <Badge key={tag} variant="outline" className="text-xs">
                    {tag}
                  </Badge>
                ))}
              </div>

              {/* Config Preview */}
              <div className="space-y-2">
                <Label className="text-xs">Configuration</Label>
                <pre className="p-3 bg-muted rounded-md text-xs overflow-auto max-h-[200px]">
                  {JSON.stringify(selectedTemplate.config, null, 2)}
                </pre>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setPreviewOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleUseTemplate}>
              <Check className="h-4 w-4 mr-2" />
              Use Template
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}

// Quick template selector for inline use
interface TemplateQuickSelectProps {
  category: TemplateCategory
  onSelect: (template: { id: string; config: Record<string, unknown> }) => void
  className?: string
  triggerClassName?: string  // Optional class for button elements
}

export function TemplateQuickSelect({
  category,
  onSelect,
  className,
  triggerClassName,
}: TemplateQuickSelectProps) {
  const templates = useMemo(() => TemplateRegistry.getByCategory(category), [category])
  const popularTemplates = templates.filter((t) => t.isPopular || t.isNew).slice(0, 4)

  return (
    <div className={`space-y-2 ${className ?? ''}`}>
      <Label className="text-xs">Quick Templates</Label>
      <div className="flex flex-wrap gap-1">
        {popularTemplates.map((template) => (
          <Button
            key={template.id}
            variant="outline"
            size="sm"
            className={triggerClassName ?? "h-7 text-xs"}
            onClick={() => onSelect({ id: template.id, config: template.config })}
          >
            {template.isPopular && <Star className="h-3 w-3 mr-1 text-yellow-500" />}
            {template.name}
          </Button>
        ))}
      </div>
    </div>
  )
}
