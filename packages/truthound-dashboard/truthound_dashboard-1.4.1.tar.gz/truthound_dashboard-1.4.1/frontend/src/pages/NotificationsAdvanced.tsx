/**
 * Advanced Notifications Page.
 *
 * Provides advanced notification management including:
 * - Routing Rules (content-based routing)
 * - Deduplication (noise reduction)
 * - Throttling (rate limiting)
 * - Escalation Policies (multi-level alerts)
 */

import { useState, useCallback, useEffect } from 'react'
import { useSafeIntlayer } from '@/hooks/useSafeIntlayer'
import { str } from '@/lib/intlayer-utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { useToast } from '@/hooks/use-toast'
import {
  Loader2,
  RefreshCw,
  Route,
  Copy,
  Gauge,
  AlertTriangle,
  Bell,
} from 'lucide-react'
import {
  RoutingRulesTab,
  DeduplicationTab,
  ThrottlingTab,
  EscalationTab,
  ConfigImportExport,
  TemplateLibrary,
} from '@/components/notifications'
import {
  getDeduplicationStats,
  getThrottlingStats,
  getEscalationStats,
  listRoutingRules,
} from '@/api/client'

interface Stats {
  routing: { total: number; active: number }
  deduplication: { dedupRate: number; totalDeduplicated: number }
  throttling: { throttleRate: number; totalThrottled: number }
  escalation: { activeIncidents: number; totalPolicies: number }
}

export default function NotificationsAdvanced() {
  const t = useSafeIntlayer('notificationsAdvanced')
  const common = useSafeIntlayer('common')
  const { toast } = useToast()

  const [activeTab, setActiveTab] = useState('routing')
  const [isLoadingStats, setIsLoadingStats] = useState(true)
  const [stats, setStats] = useState<Stats>({
    routing: { total: 0, active: 0 },
    deduplication: { dedupRate: 0, totalDeduplicated: 0 },
    throttling: { throttleRate: 0, totalThrottled: 0 },
    escalation: { activeIncidents: 0, totalPolicies: 0 },
  })

  const loadStats = useCallback(async () => {
    setIsLoadingStats(true)
    try {
      const [routingRes, dedupRes, throttleRes, escalationRes] = await Promise.all([
        listRoutingRules({ limit: 100 }),
        getDeduplicationStats(),
        getThrottlingStats(),
        getEscalationStats(),
      ])

      const routingRules = routingRes.items || []
      setStats({
        routing: {
          total: routingRules.length,
          active: routingRules.filter((r) => r.is_active).length,
        },
        deduplication: {
          dedupRate: dedupRes.dedup_rate,
          totalDeduplicated: dedupRes.total_deduplicated,
        },
        throttling: {
          throttleRate: throttleRes.throttle_rate,
          totalThrottled: throttleRes.total_throttled,
        },
        escalation: {
          activeIncidents: escalationRes.active_count,
          totalPolicies: escalationRes.total_policies,
        },
      })
    } catch {
      toast({
        title: str(common.error),
        description: str(t.errors.loadFailed),
        variant: 'destructive',
      })
    } finally {
      setIsLoadingStats(false)
    }
  }, [toast, common, t])

  useEffect(() => {
    loadStats()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Bell className="h-6 w-6 text-primary" />
            Advanced Notifications
          </h1>
          <p className="text-muted-foreground">
            Configure routing, deduplication, throttling, and escalation policies
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ConfigImportExport onImportComplete={loadStats} />
          <TemplateLibrary onSelect={() => loadStats()} />
          <Button variant="outline" onClick={loadStats} disabled={isLoadingStats}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isLoadingStats ? 'animate-spin' : ''}`} />
            {common.refresh}
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Route className="h-4 w-4" />
              Routing Rules
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoadingStats ? (
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            ) : (
              <>
                <div className="text-2xl font-bold">{stats.routing.total}</div>
                <p className="text-xs text-muted-foreground">
                  {stats.routing.active} active
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Copy className="h-4 w-4" />
              Deduplication
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoadingStats ? (
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            ) : (
              <>
                <div className="text-2xl font-bold text-green-500">
                  {stats.deduplication.dedupRate.toFixed(1)}%
                </div>
                <p className="text-xs text-muted-foreground">
                  {stats.deduplication.totalDeduplicated} deduplicated
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Gauge className="h-4 w-4" />
              Throttling
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoadingStats ? (
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            ) : (
              <>
                <div className="text-2xl font-bold text-orange-500">
                  {stats.throttling.throttleRate.toFixed(1)}%
                </div>
                <p className="text-xs text-muted-foreground">
                  {stats.throttling.totalThrottled} throttled
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              Escalation
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoadingStats ? (
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            ) : (
              <>
                <div className="text-2xl font-bold text-red-500">
                  {stats.escalation.activeIncidents}
                </div>
                <p className="text-xs text-muted-foreground">
                  active incidents ({stats.escalation.totalPolicies} policies)
                </p>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Main Tabs */}
      <Card>
        <CardHeader>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="routing" className="gap-2">
                <Route className="h-4 w-4" />
                {t.tabs.routing}
              </TabsTrigger>
              <TabsTrigger value="deduplication" className="gap-2">
                <Copy className="h-4 w-4" />
                {t.tabs.deduplication}
              </TabsTrigger>
              <TabsTrigger value="throttling" className="gap-2">
                <Gauge className="h-4 w-4" />
                {t.tabs.throttling}
              </TabsTrigger>
              <TabsTrigger value="escalation" className="gap-2">
                <AlertTriangle className="h-4 w-4" />
                {t.tabs.escalation}
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsContent value="routing" className="mt-0">
              <RoutingRulesTab />
            </TabsContent>

            <TabsContent value="deduplication" className="mt-0">
              <DeduplicationTab />
            </TabsContent>

            <TabsContent value="throttling" className="mt-0">
              <ThrottlingTab />
            </TabsContent>

            <TabsContent value="escalation" className="mt-0">
              <EscalationTab />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}
