/**
 * PluginLifecyclePanel - Plugin lifecycle and hot reload management
 *
 * Features:
 * - State machine visualization
 * - State transition controls
 * - Hot reload configuration
 * - Event history
 */

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { toast } from '@/hooks/use-toast'
import {
  Play,
  Pause,
  StopCircle,
  RefreshCw,
  ArrowUpCircle,
  Activity,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  FileSearch,
  Loader2,
  History,
  Zap,
} from 'lucide-react'
import type { Plugin } from '@/api/client'

// Types
type PluginState =
  | 'discovered'
  | 'loading'
  | 'loaded'
  | 'activating'
  | 'active'
  | 'deactivating'
  | 'unloading'
  | 'unloaded'
  | 'failed'
  | 'reloading'
  | 'upgrading'

type ReloadStrategy = 'immediate' | 'debounced' | 'manual' | 'scheduled'

interface LifecycleEvent {
  from_state: PluginState
  to_state: PluginState
  trigger: string
  timestamp: string
  metadata?: Record<string, unknown>
}

interface LifecycleStatus {
  plugin_id: string
  current_state: PluginState
  can_activate: boolean
  can_deactivate: boolean
  can_reload: boolean
  can_upgrade: boolean
  recent_events: LifecycleEvent[]
}

interface HotReloadStatus {
  plugin_id: string
  enabled: boolean
  watching: boolean
  strategy: ReloadStrategy
  has_pending_reload: boolean
  last_reload_at?: string
  last_reload_duration_ms?: number
}

interface PluginLifecyclePanelProps {
  plugin: Plugin
  onStateChange?: () => void
}

// State Badge Configuration
const STATE_CONFIG: Record<PluginState, { icon: React.ReactNode; className: string; label: string }> = {
  discovered: {
    icon: <FileSearch className="w-3 h-3" />,
    className: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400',
    label: 'Discovered',
  },
  loading: {
    icon: <Loader2 className="w-3 h-3 animate-spin" />,
    className: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    label: 'Loading',
  },
  loaded: {
    icon: <CheckCircle className="w-3 h-3" />,
    className: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    label: 'Loaded',
  },
  activating: {
    icon: <Loader2 className="w-3 h-3 animate-spin" />,
    className: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    label: 'Activating',
  },
  active: {
    icon: <Activity className="w-3 h-3" />,
    className: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    label: 'Active',
  },
  deactivating: {
    icon: <Loader2 className="w-3 h-3 animate-spin" />,
    className: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    label: 'Deactivating',
  },
  unloading: {
    icon: <Loader2 className="w-3 h-3 animate-spin" />,
    className: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400',
    label: 'Unloading',
  },
  unloaded: {
    icon: <StopCircle className="w-3 h-3" />,
    className: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400',
    label: 'Unloaded',
  },
  failed: {
    icon: <XCircle className="w-3 h-3" />,
    className: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    label: 'Failed',
  },
  reloading: {
    icon: <RefreshCw className="w-3 h-3 animate-spin" />,
    className: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
    label: 'Reloading',
  },
  upgrading: {
    icon: <ArrowUpCircle className="w-3 h-3 animate-spin" />,
    className: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
    label: 'Upgrading',
  },
}

// State Badge Component
function StateBadge({ state }: { state: PluginState }) {
  const config = STATE_CONFIG[state] || STATE_CONFIG.discovered
  return (
    <Badge variant="secondary" className={`gap-1 ${config.className}`}>
      {config.icon}
      {config.label}
    </Badge>
  )
}

// Lifecycle Status Card
function LifecycleStatusCard({
  status,
  onActivate,
  onDeactivate,
  onReload,
}: {
  status: LifecycleStatus
  onActivate: () => void
  onDeactivate: () => void
  onReload: () => void
}) {
  const [isTransitioning, setIsTransitioning] = useState(false)

  const handleAction = async (action: () => void) => {
    setIsTransitioning(true)
    try {
      await action()
    } finally {
      setIsTransitioning(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Activity className="w-4 h-4" />
            Lifecycle Status
          </CardTitle>
          <StateBadge state={status.current_state} />
        </div>
        <CardDescription>
          Current state and available transitions
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* State Diagram */}
        <div className="p-4 bg-muted rounded-lg">
          <div className="flex items-center justify-center gap-2 flex-wrap">
            <Badge variant="outline" className={status.current_state === 'discovered' ? 'ring-2 ring-primary' : ''}>
              Discovered
            </Badge>
            <span className="text-muted-foreground">→</span>
            <Badge variant="outline" className={status.current_state === 'loaded' ? 'ring-2 ring-primary' : ''}>
              Loaded
            </Badge>
            <span className="text-muted-foreground">→</span>
            <Badge variant="outline" className={status.current_state === 'active' ? 'ring-2 ring-primary' : ''}>
              Active
            </Badge>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-2">
          {status.can_activate && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleAction(onActivate)}
              disabled={isTransitioning}
            >
              {isTransitioning ? (
                <Loader2 className="w-4 h-4 mr-1 animate-spin" />
              ) : (
                <Play className="w-4 h-4 mr-1" />
              )}
              Activate
            </Button>
          )}
          {status.can_deactivate && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleAction(onDeactivate)}
              disabled={isTransitioning}
            >
              {isTransitioning ? (
                <Loader2 className="w-4 h-4 mr-1 animate-spin" />
              ) : (
                <Pause className="w-4 h-4 mr-1" />
              )}
              Deactivate
            </Button>
          )}
          {status.can_reload && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleAction(onReload)}
              disabled={isTransitioning}
            >
              {isTransitioning ? (
                <Loader2 className="w-4 h-4 mr-1 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4 mr-1" />
              )}
              Reload
            </Button>
          )}
        </div>

        {/* Current State Info */}
        {status.current_state === 'failed' && (
          <Alert variant="destructive">
            <AlertTriangle className="w-4 h-4" />
            <AlertDescription>
              Plugin is in a failed state. Check the event history for error details.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  )
}

// Hot Reload Configuration Card
function HotReloadCard({
  status,
  onChange,
  onTrigger,
}: {
  status: HotReloadStatus
  onChange: (config: Partial<HotReloadStatus>) => void
  onTrigger: () => void
}) {
  const [isReloading, setIsReloading] = useState(false)

  const handleTrigger = async () => {
    setIsReloading(true)
    try {
      await onTrigger()
    } finally {
      setIsReloading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Zap className="w-4 h-4" />
            Hot Reload
          </CardTitle>
          {status.watching && (
            <Badge variant="secondary" className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
              <Activity className="w-3 h-3 mr-1" />
              Watching
            </Badge>
          )}
        </div>
        <CardDescription>
          Configure automatic plugin reloading on file changes
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Enable Toggle */}
        <div className="flex items-center justify-between">
          <div>
            <Label>Enable Hot Reload</Label>
            <p className="text-xs text-muted-foreground">Watch for file changes and reload automatically</p>
          </div>
          <Switch
            checked={status.enabled}
            onCheckedChange={(enabled) => onChange({ enabled })}
          />
        </div>

        <Separator />

        {/* Strategy Selection */}
        <div className="space-y-2">
          <Label>Reload Strategy</Label>
          <Select
            value={status.strategy}
            onValueChange={(strategy: ReloadStrategy) => onChange({ strategy })}
            disabled={!status.enabled}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="immediate">Immediate (reload on every change)</SelectItem>
              <SelectItem value="debounced">Debounced (wait for changes to settle)</SelectItem>
              <SelectItem value="manual">Manual (trigger manually)</SelectItem>
              <SelectItem value="scheduled">Scheduled (reload at intervals)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <Separator />

        {/* Manual Trigger */}
        <div className="flex items-center justify-between">
          <div>
            <span className="text-sm font-medium">Manual Reload</span>
            {status.last_reload_at && (
              <p className="text-xs text-muted-foreground">
                Last: {new Date(status.last_reload_at).toLocaleString()}
                {status.last_reload_duration_ms && ` (${status.last_reload_duration_ms.toFixed(0)}ms)`}
              </p>
            )}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleTrigger}
            disabled={isReloading}
          >
            {isReloading ? (
              <Loader2 className="w-4 h-4 mr-1 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4 mr-1" />
            )}
            Trigger Reload
          </Button>
        </div>

        {/* Pending Reload Indicator */}
        {status.has_pending_reload && (
          <Alert>
            <Clock className="w-4 h-4" />
            <AlertDescription>
              A reload is pending. Changes will be applied shortly.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  )
}

// Event History Card
function EventHistoryCard({ events }: { events: LifecycleEvent[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <History className="w-4 h-4" />
          Event History
        </CardTitle>
        <CardDescription>
          Recent lifecycle transitions and events
        </CardDescription>
      </CardHeader>
      <CardContent>
        {events.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <History className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No events recorded</p>
          </div>
        ) : (
          <ScrollArea className="h-[200px]">
            <div className="space-y-3">
              {events.map((event, index) => (
                <div key={index} className="flex items-start gap-3 p-3 bg-muted rounded-lg">
                  <div className="flex-shrink-0 w-2 h-2 mt-2 rounded-full bg-primary" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <StateBadge state={event.from_state} />
                      <span className="text-muted-foreground">→</span>
                      <StateBadge state={event.to_state} />
                    </div>
                    <div className="mt-1 text-xs text-muted-foreground">
                      <span>{event.trigger}</span>
                      <span className="mx-2">·</span>
                      <span>{new Date(event.timestamp).toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  )
}

// Main Component
export function PluginLifecyclePanel({ plugin, onStateChange }: PluginLifecyclePanelProps) {
  const [lifecycleStatus, setLifecycleStatus] = useState<LifecycleStatus>({
    plugin_id: plugin.id,
    current_state: mapStatusToState(plugin.status),
    can_activate: plugin.status === 'installed' || plugin.status === 'disabled',
    can_deactivate: plugin.status === 'enabled',
    can_reload: plugin.status === 'enabled' || plugin.status === 'installed',
    can_upgrade: plugin.status === 'enabled' || plugin.status === 'installed',
    recent_events: [],
  })

  const [hotReloadStatus, setHotReloadStatus] = useState<HotReloadStatus>({
    plugin_id: plugin.id,
    enabled: false,
    watching: false,
    strategy: 'manual',
    has_pending_reload: false,
  })

  // Helper to map plugin status to lifecycle state
  function mapStatusToState(status: string): PluginState {
    const mapping: Record<string, PluginState> = {
      available: 'discovered',
      installed: 'loaded',
      enabled: 'active',
      disabled: 'loaded',
      error: 'failed',
    }
    return mapping[status] || 'discovered'
  }

  // Update when plugin changes
  useEffect(() => {
    setLifecycleStatus((prev) => ({
      ...prev,
      current_state: mapStatusToState(plugin.status),
      can_activate: plugin.status === 'installed' || plugin.status === 'disabled',
      can_deactivate: plugin.status === 'enabled',
      can_reload: plugin.status === 'enabled' || plugin.status === 'installed',
    }))
  }, [plugin.status])

  // Handlers
  const handleActivate = async () => {
    try {
      // In production, call actual API
      // await transitionPluginState(plugin.id, { target_state: 'active' })

      setLifecycleStatus((prev) => ({
        ...prev,
        current_state: 'active',
        can_activate: false,
        can_deactivate: true,
        recent_events: [
          {
            from_state: prev.current_state,
            to_state: 'active',
            trigger: 'manual_activation',
            timestamp: new Date().toISOString(),
          },
          ...prev.recent_events.slice(0, 9),
        ],
      }))

      toast({
        title: 'Plugin Activated',
        description: `${plugin.display_name} has been activated.`,
      })

      onStateChange?.()
    } catch (error) {
      toast({
        title: 'Activation Failed',
        description: 'Failed to activate the plugin.',
        variant: 'destructive',
      })
    }
  }

  const handleDeactivate = async () => {
    try {
      setLifecycleStatus((prev) => ({
        ...prev,
        current_state: 'loaded',
        can_activate: true,
        can_deactivate: false,
        recent_events: [
          {
            from_state: prev.current_state,
            to_state: 'loaded',
            trigger: 'manual_deactivation',
            timestamp: new Date().toISOString(),
          },
          ...prev.recent_events.slice(0, 9),
        ],
      }))

      toast({
        title: 'Plugin Deactivated',
        description: `${plugin.display_name} has been deactivated.`,
      })

      onStateChange?.()
    } catch (error) {
      toast({
        title: 'Deactivation Failed',
        description: 'Failed to deactivate the plugin.',
        variant: 'destructive',
      })
    }
  }

  const handleReload = async () => {
    try {
      setLifecycleStatus((prev) => ({
        ...prev,
        current_state: 'reloading',
      }))

      // Simulate reload
      await new Promise((resolve) => setTimeout(resolve, 1000))

      setLifecycleStatus((prev) => ({
        ...prev,
        current_state: 'active',
        recent_events: [
          {
            from_state: 'reloading',
            to_state: 'active',
            trigger: 'manual_reload',
            timestamp: new Date().toISOString(),
          },
          ...prev.recent_events.slice(0, 9),
        ],
      }))

      setHotReloadStatus((prev) => ({
        ...prev,
        last_reload_at: new Date().toISOString(),
        last_reload_duration_ms: 1000,
      }))

      toast({
        title: 'Plugin Reloaded',
        description: `${plugin.display_name} has been reloaded.`,
      })

      onStateChange?.()
    } catch (error) {
      toast({
        title: 'Reload Failed',
        description: 'Failed to reload the plugin.',
        variant: 'destructive',
      })
    }
  }

  const handleHotReloadChange = (config: Partial<HotReloadStatus>) => {
    setHotReloadStatus((prev) => ({
      ...prev,
      ...config,
      watching: config.enabled ?? prev.enabled,
    }))
  }

  const handleTriggerHotReload = async () => {
    await handleReload()
  }

  return (
    <div className="space-y-4">
      {/* Lifecycle Status */}
      <LifecycleStatusCard
        status={lifecycleStatus}
        onActivate={handleActivate}
        onDeactivate={handleDeactivate}
        onReload={handleReload}
      />

      {/* Hot Reload Configuration */}
      <HotReloadCard
        status={hotReloadStatus}
        onChange={handleHotReloadChange}
        onTrigger={handleTriggerHotReload}
      />

      {/* Event History */}
      <EventHistoryCard events={lifecycleStatus.recent_events} />
    </div>
  )
}

export default PluginLifecyclePanel
