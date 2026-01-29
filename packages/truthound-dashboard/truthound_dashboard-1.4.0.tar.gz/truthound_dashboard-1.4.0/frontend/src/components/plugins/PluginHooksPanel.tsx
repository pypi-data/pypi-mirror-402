/**
 * PluginHooksPanel - Hook registration and management
 *
 * Features:
 * - List registered hooks
 * - Register new hooks
 * - Hook type descriptions
 * - Execution history
 */

import { useState, useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
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
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import { toast } from '@/hooks/use-toast'
import {
  Webhook,
  Plus,
  Trash2,
  Zap,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Info,
  Code,
  Play,
  Pause,
  RefreshCw,
  Search,
} from 'lucide-react'
import type { Plugin } from '@/api/client'

// Types
type HookType =
  | 'before_validation'
  | 'after_validation'
  | 'on_issue_found'
  | 'before_profile'
  | 'after_profile'
  | 'before_compare'
  | 'after_compare'
  | 'on_plugin_load'
  | 'on_plugin_unload'
  | 'on_plugin_error'
  | 'before_notification'
  | 'after_notification'
  | 'on_schedule_run'
  | 'on_data_source_connect'
  | 'on_schema_change'
  | 'custom'

type HookPriority = 'highest' | 'high' | 'normal' | 'low' | 'lowest'

interface HookRegistration {
  id: string
  hook_type: HookType
  plugin_id: string
  function_name: string
  priority: HookPriority
  is_async: boolean
  is_enabled: boolean
  description?: string
}

interface HookTypeInfo {
  type: HookType
  label: string
  description: string
  icon: React.ReactNode
  category: 'validation' | 'profiling' | 'drift' | 'plugin' | 'notification' | 'system'
}

interface PluginHooksPanelProps {
  plugin: Plugin
  onHookChange?: () => void
}

// Hook Type Definitions
const HOOK_TYPES: HookTypeInfo[] = [
  {
    type: 'before_validation',
    label: 'Before Validation',
    description: 'Runs before validation starts. Can modify validation parameters.',
    icon: <Play className="w-4 h-4" />,
    category: 'validation',
  },
  {
    type: 'after_validation',
    label: 'After Validation',
    description: 'Runs after validation completes. Can access and modify results.',
    icon: <CheckCircle className="w-4 h-4" />,
    category: 'validation',
  },
  {
    type: 'on_issue_found',
    label: 'On Issue Found',
    description: 'Triggered when a validation issue is discovered.',
    icon: <AlertTriangle className="w-4 h-4" />,
    category: 'validation',
  },
  {
    type: 'before_profile',
    label: 'Before Profile',
    description: 'Runs before data profiling starts.',
    icon: <Play className="w-4 h-4" />,
    category: 'profiling',
  },
  {
    type: 'after_profile',
    label: 'After Profile',
    description: 'Runs after data profiling completes.',
    icon: <CheckCircle className="w-4 h-4" />,
    category: 'profiling',
  },
  {
    type: 'before_compare',
    label: 'Before Compare',
    description: 'Runs before drift comparison starts.',
    icon: <Play className="w-4 h-4" />,
    category: 'drift',
  },
  {
    type: 'after_compare',
    label: 'After Compare',
    description: 'Runs after drift comparison completes.',
    icon: <CheckCircle className="w-4 h-4" />,
    category: 'drift',
  },
  {
    type: 'on_plugin_load',
    label: 'On Plugin Load',
    description: 'Triggered when a plugin is loaded.',
    icon: <Zap className="w-4 h-4" />,
    category: 'plugin',
  },
  {
    type: 'on_plugin_unload',
    label: 'On Plugin Unload',
    description: 'Triggered when a plugin is unloaded.',
    icon: <Pause className="w-4 h-4" />,
    category: 'plugin',
  },
  {
    type: 'on_plugin_error',
    label: 'On Plugin Error',
    description: 'Triggered when a plugin error occurs.',
    icon: <XCircle className="w-4 h-4" />,
    category: 'plugin',
  },
  {
    type: 'before_notification',
    label: 'Before Notification',
    description: 'Runs before sending a notification. Can modify the message.',
    icon: <Play className="w-4 h-4" />,
    category: 'notification',
  },
  {
    type: 'after_notification',
    label: 'After Notification',
    description: 'Runs after sending a notification.',
    icon: <CheckCircle className="w-4 h-4" />,
    category: 'notification',
  },
  {
    type: 'on_schedule_run',
    label: 'On Schedule Run',
    description: 'Triggered when a scheduled task executes.',
    icon: <Clock className="w-4 h-4" />,
    category: 'system',
  },
  {
    type: 'on_data_source_connect',
    label: 'On Data Source Connect',
    description: 'Triggered when connecting to a data source.',
    icon: <Zap className="w-4 h-4" />,
    category: 'system',
  },
  {
    type: 'on_schema_change',
    label: 'On Schema Change',
    description: 'Triggered when schema changes are detected.',
    icon: <RefreshCw className="w-4 h-4" />,
    category: 'system',
  },
  {
    type: 'custom',
    label: 'Custom',
    description: 'Custom hook type for plugin-specific functionality.',
    icon: <Code className="w-4 h-4" />,
    category: 'system',
  },
]

// Priority Badge
function PriorityBadge({ priority }: { priority: HookPriority }) {
  const config: Record<HookPriority, { className: string; label: string }> = {
    highest: {
      className: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
      label: 'Highest',
    },
    high: {
      className: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
      label: 'High',
    },
    normal: {
      className: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
      label: 'Normal',
    },
    low: {
      className: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400',
      label: 'Low',
    },
    lowest: {
      className: 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-500',
      label: 'Lowest',
    },
  }

  const { className, label } = config[priority]

  return (
    <Badge variant="secondary" className={`text-xs ${className}`}>
      {label}
    </Badge>
  )
}

// Category Badge
function CategoryBadge({ category }: { category: string }) {
  const colors: Record<string, string> = {
    validation: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    profiling: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
    drift: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    plugin: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    notification: 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400',
    system: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400',
  }

  return (
    <Badge variant="secondary" className={`text-xs capitalize ${colors[category] || colors.system}`}>
      {category}
    </Badge>
  )
}

// Hook List Item
function HookListItem({
  hook,
  onToggle,
  onDelete,
}: {
  hook: HookRegistration
  onToggle: () => void
  onDelete: () => void
}) {
  const typeInfo = HOOK_TYPES.find((t) => t.type === hook.hook_type) || HOOK_TYPES[HOOK_TYPES.length - 1]

  return (
    <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${hook.is_enabled ? 'bg-primary/10 text-primary' : 'bg-muted-foreground/10 text-muted-foreground'}`}>
          {typeInfo.icon}
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-medium text-sm">{hook.function_name}</span>
            {hook.is_async && (
              <Badge variant="outline" className="text-xs">
                async
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2 mt-1">
            <Badge variant="outline" className="text-xs">
              {typeInfo.label}
            </Badge>
            <PriorityBadge priority={hook.priority} />
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={onToggle}
        >
          {hook.is_enabled ? (
            <Pause className="w-4 h-4 text-yellow-500" />
          ) : (
            <Play className="w-4 h-4 text-green-500" />
          )}
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-destructive hover:text-destructive"
          onClick={onDelete}
        >
          <Trash2 className="w-4 h-4" />
        </Button>
      </div>
    </div>
  )
}

// Hook Types Reference
function HookTypesReference() {
  const categories = ['validation', 'profiling', 'drift', 'plugin', 'notification', 'system']

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Info className="w-4 h-4" />
          Available Hook Types
        </CardTitle>
        <CardDescription>
          Reference for all available hook types and their purposes
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Accordion type="multiple" className="w-full">
          {categories.map((category) => (
            <AccordionItem key={category} value={category}>
              <AccordionTrigger className="capitalize">
                <div className="flex items-center gap-2">
                  <CategoryBadge category={category} />
                  <span>{category}</span>
                  <span className="text-xs text-muted-foreground">
                    ({HOOK_TYPES.filter((t) => t.category === category).length})
                  </span>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-2">
                  {HOOK_TYPES.filter((t) => t.category === category).map((hookType) => (
                    <div key={hookType.type} className="flex items-start gap-3 p-2 rounded-lg hover:bg-muted/50">
                      <div className="p-1.5 rounded bg-muted">
                        {hookType.icon}
                      </div>
                      <div>
                        <div className="font-medium text-sm">{hookType.label}</div>
                        <p className="text-xs text-muted-foreground">{hookType.description}</p>
                        <code className="text-xs text-muted-foreground font-mono">{hookType.type}</code>
                      </div>
                    </div>
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </CardContent>
    </Card>
  )
}

// Register Hook Dialog
function RegisterHookDialog({
  open,
  onOpenChange,
  pluginId,
  onRegister,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  pluginId: string
  onRegister: (hook: Omit<HookRegistration, 'id'>) => void
}) {
  const [formData, setFormData] = useState({
    hook_type: 'after_validation' as HookType,
    function_name: '',
    priority: 'normal' as HookPriority,
    description: '',
  })

  const handleSubmit = () => {
    if (!formData.function_name) {
      toast({
        title: 'Validation Error',
        description: 'Function name is required.',
        variant: 'destructive',
      })
      return
    }

    onRegister({
      hook_type: formData.hook_type,
      plugin_id: pluginId,
      function_name: formData.function_name,
      priority: formData.priority,
      is_async: false,
      is_enabled: true,
      description: formData.description || undefined,
    })

    setFormData({
      hook_type: 'after_validation',
      function_name: '',
      priority: 'normal',
      description: '',
    })

    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Register Hook</DialogTitle>
          <DialogDescription>
            Register a new hook function for this plugin
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label>Hook Type</Label>
            <Select
              value={formData.hook_type}
              onValueChange={(value: HookType) => setFormData((prev) => ({ ...prev, hook_type: value }))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {HOOK_TYPES.map((hookType) => (
                  <SelectItem key={hookType.type} value={hookType.type}>
                    <div className="flex items-center gap-2">
                      {hookType.icon}
                      <span>{hookType.label}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Function Name</Label>
            <Input
              placeholder="on_validation_complete"
              value={formData.function_name}
              onChange={(e) => setFormData((prev) => ({ ...prev, function_name: e.target.value }))}
              className="font-mono"
            />
            <p className="text-xs text-muted-foreground">
              The function name that will be called when the hook triggers
            </p>
          </div>

          <div className="space-y-2">
            <Label>Priority</Label>
            <Select
              value={formData.priority}
              onValueChange={(value: HookPriority) => setFormData((prev) => ({ ...prev, priority: value }))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="highest">Highest (runs first)</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="normal">Normal (default)</SelectItem>
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="lowest">Lowest (runs last)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Description (optional)</Label>
            <Input
              placeholder="Brief description of what this hook does"
              value={formData.description}
              onChange={(e) => setFormData((prev) => ({ ...prev, description: e.target.value }))}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit}>
            Register Hook
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// Main Component
export function PluginHooksPanel({ plugin, onHookChange }: PluginHooksPanelProps) {
  const [hooks, setHooks] = useState<HookRegistration[]>([])
  const [showRegisterDialog, setShowRegisterDialog] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterType, setFilterType] = useState<string>('all')

  // Filter hooks
  const filteredHooks = useMemo(() => {
    return hooks.filter((hook) => {
      const matchesSearch =
        hook.function_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        hook.hook_type.toLowerCase().includes(searchQuery.toLowerCase())
      const matchesType = filterType === 'all' || hook.hook_type === filterType

      return matchesSearch && matchesType
    })
  }, [hooks, searchQuery, filterType])

  // Stats
  const stats = useMemo(() => ({
    total: hooks.length,
    enabled: hooks.filter((h) => h.is_enabled).length,
    byType: HOOK_TYPES.map((t) => ({
      type: t.type,
      count: hooks.filter((h) => h.hook_type === t.type).length,
    })).filter((s) => s.count > 0),
  }), [hooks])

  // Handlers
  const handleRegister = (hook: Omit<HookRegistration, 'id'>) => {
    const newHook: HookRegistration = {
      ...hook,
      id: `hook-${Date.now()}`,
    }
    setHooks((prev) => [...prev, newHook])

    toast({
      title: 'Hook Registered',
      description: `${hook.function_name} has been registered.`,
    })

    onHookChange?.()
  }

  const handleToggle = (hookId: string) => {
    setHooks((prev) =>
      prev.map((h) =>
        h.id === hookId ? { ...h, is_enabled: !h.is_enabled } : h
      )
    )
    onHookChange?.()
  }

  const handleDelete = (hookId: string) => {
    setHooks((prev) => prev.filter((h) => h.id !== hookId))

    toast({
      title: 'Hook Removed',
      description: 'The hook has been unregistered.',
    })

    onHookChange?.()
  }

  return (
    <div className="space-y-4">
      {/* Header with Stats */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <Webhook className="w-4 h-4" />
              Registered Hooks
            </CardTitle>
            <Button size="sm" onClick={() => setShowRegisterDialog(true)}>
              <Plus className="w-4 h-4 mr-1" />
              Register Hook
            </Button>
          </div>
          <CardDescription>
            Manage hook functions for this plugin
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Stats */}
          <div className="flex items-center gap-4 mb-4">
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Total:</span>
              <Badge variant="secondary">{stats.total}</Badge>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Enabled:</span>
              <Badge variant="secondary" className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                {stats.enabled}
              </Badge>
            </div>
          </div>

          {/* Filters */}
          <div className="flex items-center gap-2 mb-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search hooks..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <Separator className="my-1" />
                {HOOK_TYPES.map((hookType) => (
                  <SelectItem key={hookType.type} value={hookType.type}>
                    {hookType.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Hook List */}
          {filteredHooks.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Webhook className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">
                {hooks.length === 0 ? 'No hooks registered' : 'No hooks match your search'}
              </p>
              {hooks.length === 0 && (
                <Button
                  variant="link"
                  size="sm"
                  onClick={() => setShowRegisterDialog(true)}
                >
                  Register your first hook
                </Button>
              )}
            </div>
          ) : (
            <ScrollArea className="max-h-[300px]">
              <div className="space-y-2">
                {filteredHooks.map((hook) => (
                  <HookListItem
                    key={hook.id}
                    hook={hook}
                    onToggle={() => handleToggle(hook.id)}
                    onDelete={() => handleDelete(hook.id)}
                  />
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>

      {/* Hook Types Reference */}
      <HookTypesReference />

      {/* Register Dialog */}
      <RegisterHookDialog
        open={showRegisterDialog}
        onOpenChange={setShowRegisterDialog}
        pluginId={plugin.id}
        onRegister={handleRegister}
      />
    </div>
  )
}

export default PluginHooksPanel
