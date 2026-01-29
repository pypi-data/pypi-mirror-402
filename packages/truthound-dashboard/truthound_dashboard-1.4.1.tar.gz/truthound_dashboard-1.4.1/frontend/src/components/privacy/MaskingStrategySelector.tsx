/**
 * Masking strategy selector component.
 *
 * Provides visual selection of masking strategies (redact, hash, fake).
 */

import { useIntlayer } from 'react-intlayer'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { EyeOff, Hash, Sparkles, Check } from 'lucide-react'
import type { MaskingStrategy } from '@/api/client'

interface MaskingStrategySelectorProps {
  selected: MaskingStrategy
  onSelect: (strategy: MaskingStrategy) => void
  disabled?: boolean
}

interface StrategyOption {
  value: MaskingStrategy
  icon: typeof EyeOff
  color: string
  bgColor: string
}

const strategies: StrategyOption[] = [
  {
    value: 'redact',
    icon: EyeOff,
    color: 'text-red-500',
    bgColor: 'bg-red-500/10',
  },
  {
    value: 'hash',
    icon: Hash,
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/10',
  },
  {
    value: 'fake',
    icon: Sparkles,
    color: 'text-purple-500',
    bgColor: 'bg-purple-500/10',
  },
]

export function MaskingStrategySelector({
  selected,
  onSelect,
  disabled = false,
}: MaskingStrategySelectorProps) {
  const t = useIntlayer('privacy')

  const getStrategyLabel = (value: MaskingStrategy) => {
    switch (value) {
      case 'redact':
        return t.strategies.redact
      case 'hash':
        return t.strategies.hash
      case 'fake':
        return t.strategies.fake
    }
  }

  const getStrategyDesc = (value: MaskingStrategy) => {
    switch (value) {
      case 'redact':
        return t.strategies.redactDesc
      case 'hash':
        return t.strategies.hashDesc
      case 'fake':
        return t.strategies.fakeDesc
    }
  }

  return (
    <div className="grid gap-4 md:grid-cols-3">
      {strategies.map((strategy) => {
        const Icon = strategy.icon
        const isSelected = selected === strategy.value

        return (
          <Card
            key={strategy.value}
            className={cn(
              'cursor-pointer transition-all hover:border-primary/50',
              isSelected && 'border-primary ring-2 ring-primary/20',
              disabled && 'cursor-not-allowed opacity-50'
            )}
            onClick={() => !disabled && onSelect(strategy.value)}
          >
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div className={cn('rounded-lg p-2', strategy.bgColor)}>
                  <Icon className={cn('h-5 w-5', strategy.color)} />
                </div>
                {isSelected && (
                  <div className="rounded-full bg-primary p-1">
                    <Check className="h-3 w-3 text-primary-foreground" />
                  </div>
                )}
              </div>
              <CardTitle className="text-base">{getStrategyLabel(strategy.value)}</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-xs">
                {getStrategyDesc(strategy.value)}
              </CardDescription>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
