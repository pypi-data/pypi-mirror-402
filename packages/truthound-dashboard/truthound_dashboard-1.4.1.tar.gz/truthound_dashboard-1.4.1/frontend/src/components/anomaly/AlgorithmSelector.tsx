/**
 * Algorithm selector component for anomaly detection.
 *
 * Displays algorithm cards with descriptions and categories.
 */

import { useIntlayer } from 'react-intlayer'
import { Cpu, Network, Activity, GitBranch, BarChart3, Brain, Check } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { AlgorithmCategory, AlgorithmInfo } from '@/api/client'

interface AlgorithmSelectorProps {
  algorithms: AlgorithmInfo[]
  selectedAlgorithm: AlgorithmInfo | null
  onSelect: (algorithm: AlgorithmInfo) => void
}

const categoryConfig: Record<
  AlgorithmCategory,
  { icon: typeof Cpu; color: string }
> = {
  tree: { icon: GitBranch, color: 'text-green-500' },
  density: { icon: Activity, color: 'text-blue-500' },
  svm: { icon: Network, color: 'text-purple-500' },
  clustering: { icon: Cpu, color: 'text-amber-500' },
  statistical: { icon: BarChart3, color: 'text-cyan-500' },
  neural: { icon: Brain, color: 'text-pink-500' },
}

export function AlgorithmSelector({
  algorithms,
  selectedAlgorithm,
  onSelect,
}: AlgorithmSelectorProps) {
  const t = useIntlayer('anomaly')

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {algorithms.map((algo) => {
        const config = categoryConfig[algo.category]
        const Icon = config.icon
        const isSelected = selectedAlgorithm?.name === algo.name

        return (
          <Card
            key={algo.name}
            className={cn(
              'cursor-pointer transition-all hover:border-primary/50',
              isSelected && 'border-primary ring-2 ring-primary/20'
            )}
            onClick={() => onSelect(algo)}
          >
            <CardHeader className="pb-2">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <div className={cn('rounded-md p-1.5', `${config.color}/10`)}>
                    <Icon className={cn('h-4 w-4', config.color)} />
                  </div>
                  <CardTitle className="text-base">{algo.display_name}</CardTitle>
                </div>
                {isSelected && (
                  <div className="rounded-full bg-primary p-0.5">
                    <Check className="h-3 w-3 text-primary-foreground" />
                  </div>
                )}
              </div>
              <CardDescription className="text-xs">
                {algo.description}
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-3">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs">
                  {t.categories[algo.category]}
                </Badge>
                {algo.requires_scaling && (
                  <Badge variant="secondary" className="text-xs">
                    {t.requiresScaling}
                  </Badge>
                )}
              </div>

              <div className="text-xs text-muted-foreground">
                <span className="font-medium">{t.bestFor}:</span> {algo.best_for}
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
