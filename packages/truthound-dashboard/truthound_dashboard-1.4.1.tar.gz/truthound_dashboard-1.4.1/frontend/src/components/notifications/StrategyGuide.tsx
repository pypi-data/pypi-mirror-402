/**
 * StrategyGuide - Visual guides for strategy/algorithm selection
 *
 * Provides visual explanations for:
 * - Deduplication strategies (Sliding, Tumbling, Session, Adaptive)
 * - Deduplication policies
 * - Throttling algorithms (TokenBucket, FixedWindow, SlidingWindow)
 *
 * Helps users understand when to use each option
 */

import { useState } from 'react'
import {
  Info,
  ArrowRight,
  Clock,
  Layers,
  Zap,
  TrendingUp,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
} from 'lucide-react'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

// =============================================================================
// Deduplication Strategy Guide
// =============================================================================

export interface StrategyInfo {
  id: string
  name: string
  description: string
  useCase: string
  pros: string[]
  cons: string[]
  diagram: React.ReactNode
}

const DEDUP_STRATEGIES: Record<string, StrategyInfo> = {
  sliding: {
    id: 'sliding',
    name: 'Sliding Window',
    description: 'Rolling time window that continuously moves forward',
    useCase: 'Best for real-time deduplication where you need continuous protection',
    pros: ['Continuous coverage', 'No boundary issues', 'Smooth operation'],
    cons: ['Higher memory usage', 'More complex to implement'],
    diagram: (
      <div className="space-y-2">
        <div className="text-xs text-muted-foreground">Timeline →</div>
        <div className="flex items-center gap-1">
          <div className="h-6 w-20 bg-muted rounded flex items-center justify-center text-xs">Past</div>
          <div className="h-6 w-24 bg-primary/20 border-2 border-primary rounded flex items-center justify-center text-xs font-medium">
            Window (5m)
          </div>
          <ArrowRight className="h-4 w-4" />
          <div className="h-6 w-24 bg-primary/10 border border-dashed border-primary rounded flex items-center justify-center text-xs">
            Moves →
          </div>
        </div>
        <p className="text-xs text-muted-foreground">Window slides continuously with time</p>
      </div>
    ),
  },
  tumbling: {
    id: 'tumbling',
    name: 'Tumbling Window',
    description: 'Fixed, non-overlapping time windows',
    useCase: 'Best for batch processing or hourly/daily summaries',
    pros: ['Simple to understand', 'Predictable behavior', 'Lower memory'],
    cons: ['Boundary issues (duplicates across windows)', 'Not smooth'],
    diagram: (
      <div className="space-y-2">
        <div className="text-xs text-muted-foreground">Timeline →</div>
        <div className="flex items-center gap-0.5">
          <div className="h-6 w-16 bg-primary/20 border border-primary rounded flex items-center justify-center text-xs">
            1h
          </div>
          <div className="h-6 w-16 bg-primary/30 border border-primary rounded flex items-center justify-center text-xs font-medium">
            1h
          </div>
          <div className="h-6 w-16 bg-primary/20 border border-primary rounded flex items-center justify-center text-xs">
            1h
          </div>
          <div className="h-6 w-16 bg-muted border border-dashed rounded flex items-center justify-center text-xs">
            ...
          </div>
        </div>
        <p className="text-xs text-muted-foreground">Windows don't overlap, reset at boundaries</p>
      </div>
    ),
  },
  session: {
    id: 'session',
    name: 'Session Window',
    description: 'Dynamic windows based on activity gaps',
    useCase: 'Best for bursty traffic or event-driven systems',
    pros: ['Handles bursts well', 'Adapts to activity', 'Natural grouping'],
    cons: ['Less predictable', 'Can grow unbounded'],
    diagram: (
      <div className="space-y-2">
        <div className="text-xs text-muted-foreground">Events over time →</div>
        <div className="flex items-center gap-1">
          <div className="h-6 px-2 bg-primary/30 border border-primary rounded flex items-center gap-1 text-xs">
            <span>••••</span>
          </div>
          <div className="h-6 w-8 flex items-center justify-center text-xs text-muted-foreground">
            gap
          </div>
          <div className="h-6 px-2 bg-primary/30 border border-primary rounded flex items-center gap-1 text-xs">
            <span>••</span>
          </div>
          <div className="h-6 w-8 flex items-center justify-center text-xs text-muted-foreground">
            gap
          </div>
          <div className="h-6 px-2 bg-primary/30 border border-primary rounded flex items-center gap-1 text-xs">
            <span>•••••••</span>
          </div>
        </div>
        <p className="text-xs text-muted-foreground">New session after inactivity gap</p>
      </div>
    ),
  },
  adaptive: {
    id: 'adaptive',
    name: 'Adaptive Window',
    description: 'Automatically adjusts window size based on load',
    useCase: 'Best for variable workloads with unpredictable patterns',
    pros: ['Self-tuning', 'Handles varying load', 'Optimal resource use'],
    cons: ['Complex behavior', 'Harder to debug'],
    diagram: (
      <div className="space-y-2">
        <div className="text-xs text-muted-foreground">Load over time →</div>
        <div className="flex items-end gap-1 h-12">
          <div className="h-4 w-8 bg-primary/30 rounded-t" />
          <div className="h-8 w-8 bg-primary/50 rounded-t" />
          <div className="h-10 w-8 bg-primary/70 rounded-t" />
          <div className="h-6 w-8 bg-primary/40 rounded-t" />
          <div className="h-3 w-8 bg-primary/20 rounded-t" />
        </div>
        <p className="text-xs text-muted-foreground">Window size adapts: small→large→small</p>
      </div>
    ),
  },
}

interface DeduplicationStrategyGuideProps {
  value?: string
  selectedStrategy?: string
  onSelect?: (strategy: string) => void
  className?: string
}

export function DeduplicationStrategyGuide({ value, selectedStrategy, onSelect, className }: DeduplicationStrategyGuideProps) {
  // Support both `value` and `selectedStrategy` props for flexibility
  const effectiveValue = value ?? selectedStrategy
  const strategy = effectiveValue ? DEDUP_STRATEGIES[effectiveValue] : null

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="sm" className={cn('h-6 px-2', className)}>
          <HelpCircle className="h-3 w-3 mr-1" />
          <span className="text-xs">Strategy Guide</span>
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-96" align="start">
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Info className="h-4 w-4 text-primary" />
            <span className="font-medium">Deduplication Strategies</span>
          </div>

          {strategy ? (
            <div className="space-y-3">
              <div>
                <h4 className="font-medium text-sm">{strategy.name}</h4>
                <p className="text-xs text-muted-foreground">{strategy.description}</p>
              </div>

              <div className="p-3 bg-muted rounded-md">{strategy.diagram}</div>

              <div>
                <span className="text-xs font-medium">Best for:</span>
                <p className="text-xs text-muted-foreground">{strategy.useCase}</p>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-xs font-medium text-green-600">Pros</span>
                  <ul className="text-xs text-muted-foreground">
                    {strategy.pros.map((pro, i) => (
                      <li key={i} className="flex items-start gap-1">
                        <CheckCircle2 className="h-3 w-3 text-green-500 mt-0.5 flex-shrink-0" />
                        {pro}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <span className="text-xs font-medium text-orange-600">Cons</span>
                  <ul className="text-xs text-muted-foreground">
                    {strategy.cons.map((con, i) => (
                      <li key={i} className="flex items-start gap-1">
                        <AlertCircle className="h-3 w-3 text-orange-500 mt-0.5 flex-shrink-0" />
                        {con}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              {Object.values(DEDUP_STRATEGIES).map((s) => (
                <div key={s.id} className="p-2 border rounded hover:bg-muted/50">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-xs">{s.name}</Badge>
                    <span className="text-xs text-muted-foreground">{s.description}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </PopoverContent>
    </Popover>
  )
}

// =============================================================================
// Deduplication Policy Guide
// =============================================================================

const DEDUP_POLICIES: Record<string, { name: string; fields: string[]; description: string }> = {
  none: { name: 'None', fields: [], description: 'No deduplication' },
  basic: { name: 'Basic', fields: ['checkpoint_name', 'action_type'], description: 'Simple dedup by checkpoint and action' },
  severity: { name: 'Severity', fields: ['checkpoint_name', 'action_type', 'severity'], description: 'Include severity in fingerprint' },
  issue_based: { name: 'Issue Based', fields: ['checkpoint_name', 'action_type', 'issue_hash'], description: 'Dedup by specific issue' },
  strict: { name: 'Strict', fields: ['checkpoint_name', 'action_type', 'severity', 'issue_hash', 'timestamp_bucket'], description: 'All fields including time bucket' },
  custom: { name: 'Custom', fields: ['user-defined'], description: 'Define your own fingerprint fields' },
}

interface DeduplicationPolicyGuideProps {
  value?: string
  selectedPolicy?: string
  onSelect?: (policy: string) => void
  className?: string
}

export function DeduplicationPolicyGuide({ value, selectedPolicy, onSelect, className }: DeduplicationPolicyGuideProps) {
  const effectiveValue = value ?? selectedPolicy
  const policy = effectiveValue ? DEDUP_POLICIES[effectiveValue] : null

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="ghost" size="sm" className={cn('h-6 px-2', className)}>
            <Info className="h-3 w-3" />
          </Button>
        </TooltipTrigger>
        <TooltipContent side="right" className="max-w-xs">
          {policy ? (
            <div className="space-y-2">
              <p className="font-medium">{policy.name} Policy</p>
              <p className="text-xs">{policy.description}</p>
              {policy.fields.length > 0 && (
                <div>
                  <span className="text-xs font-medium">Fingerprint includes:</span>
                  <ul className="text-xs">
                    {policy.fields.map((f) => (
                      <li key={f} className="text-muted-foreground">• {f}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-1">
              <p className="font-medium text-sm">Deduplication Policies</p>
              {Object.entries(DEDUP_POLICIES).map(([key, p]) => (
                <div key={key} className="text-xs">
                  <span className="font-medium">{p.name}:</span>{' '}
                  <span className="text-muted-foreground">{p.description}</span>
                </div>
              ))}
            </div>
          )}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

// =============================================================================
// Throttling Algorithm Guide
// =============================================================================

const THROTTLE_ALGORITHMS: Record<string, StrategyInfo> = {
  token_bucket: {
    id: 'token_bucket',
    name: 'Token Bucket',
    description: 'Tokens refill at constant rate, consumed per request',
    useCase: 'Best for smooth rate limiting with burst allowance',
    pros: ['Allows controlled bursts', 'Smooth average rate', 'Industry standard'],
    cons: ['Slightly more memory', 'Needs token tracking'],
    diagram: (
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <div className="h-12 w-16 border-2 border-primary rounded-b-lg relative overflow-hidden">
            <div className="absolute bottom-0 left-0 right-0 h-8 bg-primary/30" />
            <div className="absolute inset-0 flex items-end justify-center pb-1">
              <span className="text-xs font-medium">8/10</span>
            </div>
          </div>
          <div className="text-xs space-y-1">
            <div className="flex items-center gap-1">
              <TrendingUp className="h-3 w-3 text-green-500" />
              <span>+1 token/sec</span>
            </div>
            <div className="flex items-center gap-1">
              <ArrowRight className="h-3 w-3 text-orange-500" />
              <span>-1 per request</span>
            </div>
          </div>
        </div>
        <p className="text-xs text-muted-foreground">Bucket refills, request consumes token</p>
      </div>
    ),
  },
  fixed_window: {
    id: 'fixed_window',
    name: 'Fixed Window',
    description: 'Simple counter that resets at fixed intervals',
    useCase: 'Best for simple rate limiting with clear boundaries',
    pros: ['Simple implementation', 'Low memory', 'Easy to understand'],
    cons: ['Boundary burst problem', 'Can allow 2x rate at boundaries'],
    diagram: (
      <div className="space-y-2">
        <div className="flex items-center gap-1">
          <div className="h-8 w-20 border rounded flex items-center justify-center">
            <span className="text-xs">7/10</span>
          </div>
          <div className="text-xs text-muted-foreground">|</div>
          <div className="h-8 w-20 border border-primary rounded flex items-center justify-center bg-primary/10">
            <span className="text-xs font-medium">3/10</span>
          </div>
          <div className="text-xs text-muted-foreground">|</div>
          <div className="h-8 w-20 border border-dashed rounded flex items-center justify-center">
            <span className="text-xs">0/10</span>
          </div>
        </div>
        <p className="text-xs text-muted-foreground">Counter resets at window boundary</p>
      </div>
    ),
  },
  sliding_window: {
    id: 'sliding_window',
    name: 'Sliding Window',
    description: 'Weighted average of current and previous windows',
    useCase: 'Best for accurate rate limiting without boundary issues',
    pros: ['No boundary bursts', 'Accurate limiting', 'Smooth behavior'],
    cons: ['More complex', 'Slightly higher compute'],
    diagram: (
      <div className="space-y-2">
        <div className="flex items-center gap-0">
          <div className="h-8 w-16 bg-muted/50 rounded-l flex items-center justify-center">
            <span className="text-xs">prev: 7</span>
          </div>
          <div className="h-8 w-16 bg-primary/20 flex items-center justify-center">
            <span className="text-xs">curr: 3</span>
          </div>
          <div className="h-8 w-4 flex items-center justify-center">
            <span className="text-xs">=</span>
          </div>
          <div className="h-8 w-12 bg-primary/30 rounded-r flex items-center justify-center">
            <span className="text-xs font-medium">~5</span>
          </div>
        </div>
        <p className="text-xs text-muted-foreground">Weighted: (7 × 0.3) + (3 × 0.7) = 4.2</p>
      </div>
    ),
  },
}

export function ThrottlingAlgorithmGuide({ className }: { className?: string }) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="sm" className={cn('h-6 px-2', className)}>
          <HelpCircle className="h-3 w-3 mr-1" />
          <span className="text-xs">Algorithm Guide</span>
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-96" align="start">
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Gauge className="h-4 w-4 text-primary" />
            <span className="font-medium">Throttling Algorithms</span>
          </div>

          <div className="space-y-4">
            {Object.values(THROTTLE_ALGORITHMS).map((algo) => (
              <div key={algo.id} className="space-y-2 p-3 border rounded-md">
                <h4 className="font-medium text-sm">{algo.name}</h4>
                <p className="text-xs text-muted-foreground">{algo.description}</p>
                <div className="py-2">{algo.diagram}</div>
                <div className="text-xs">
                  <span className="font-medium">Best for:</span>{' '}
                  <span className="text-muted-foreground">{algo.useCase}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </PopoverContent>
    </Popover>
  )
}

// =============================================================================
// Burst Allowance Visualization
// =============================================================================

interface BurstAllowanceVisualProps {
  limit?: number
  baseLimit?: number  // Alias for limit
  burstAllowance: number
  className?: string
}

export function BurstAllowanceVisual({
  limit: limitProp,
  baseLimit,
  burstAllowance,
  className,
}: BurstAllowanceVisualProps) {
  // Support both `limit` and `baseLimit` props
  const limit = limitProp ?? baseLimit ?? 100
  const maxBurst = Math.floor(limit * burstAllowance)

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className={cn('flex items-center gap-2', className)}>
            <div className="flex items-end gap-0.5">
              <div
                className="bg-primary/30 rounded-t"
                style={{ width: 20, height: 24 }}
              />
              <div
                className="bg-primary/60 rounded-t border-t-2 border-primary"
                style={{ width: 20, height: 24 * burstAllowance }}
              />
            </div>
            <div className="text-xs">
              <div>{limit}/min</div>
              <div className="text-muted-foreground">burst: {maxBurst}</div>
            </div>
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <div className="text-xs space-y-1">
            <p>Base limit: {limit}/minute</p>
            <p>Burst allowance: {burstAllowance}x ({(burstAllowance * 100).toFixed(0)}%)</p>
            <p className="font-medium">Maximum burst: {maxBurst} requests</p>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

// Export a single import point
import { Gauge } from 'lucide-react'
