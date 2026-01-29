/**
 * PluginDependencyGraph - Dependency visualization component
 *
 * Features:
 * - Visual dependency tree
 * - Cycle detection display
 * - Installation order
 * - Dependency resolution
 */

import { useState, useEffect, useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  Package,
  ChevronRight,
  ChevronDown,
  AlertTriangle,
  CheckCircle,
  XCircle,
  ArrowRight,
  RefreshCw,
  Download,
  AlertCircle,
  GitBranch,
  Layers,
} from 'lucide-react'
import type { Plugin } from '@/api/client'

// Types
interface DependencyInfo {
  plugin_id: string
  version_constraint: string
  dependency_type: 'required' | 'optional' | 'dev' | 'peer' | 'conflict'
  resolved_version?: string
  is_installed: boolean
  is_satisfied: boolean
}

interface DependencyGraphNode {
  plugin_id: string
  version: string
  dependencies: DependencyInfo[]
  dependents: string[]
  depth: number
}

interface DependencyGraph {
  root_plugin_id: string
  nodes: DependencyGraphNode[]
  has_cycles: boolean
  cycle_path?: string[]
  install_order: string[]
  total_dependencies: number
}

interface PluginDependencyGraphProps {
  plugin: Plugin
  onInstallDependency?: (pluginId: string) => void
}

// Dependency Type Badge
function DependencyTypeBadge({ type }: { type: string }) {
  const config: Record<string, { className: string; label: string }> = {
    required: {
      className: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
      label: 'Required',
    },
    optional: {
      className: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400',
      label: 'Optional',
    },
    dev: {
      className: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
      label: 'Dev',
    },
    peer: {
      className: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
      label: 'Peer',
    },
    conflict: {
      className: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
      label: 'Conflict',
    },
  }

  const { className, label } = config[type] || config.required

  return (
    <Badge variant="secondary" className={`text-xs ${className}`}>
      {label}
    </Badge>
  )
}

// Dependency Tree Node
function DependencyTreeNode({
  dependency,
  depth = 0,
  onInstall,
}: {
  dependency: DependencyInfo
  depth?: number
  onInstall?: () => void
}) {
  const [isOpen, setIsOpen] = useState(depth < 2)

  return (
    <div className={`${depth > 0 ? 'ml-4 border-l border-muted pl-4' : ''}`}>
      <div className="flex items-center justify-between py-2">
        <div className="flex items-center gap-2">
          <Package className="w-4 h-4 text-muted-foreground" />
          <span className="font-medium text-sm">{dependency.plugin_id}</span>
          <span className="text-xs text-muted-foreground font-mono">
            {dependency.version_constraint}
          </span>
          <DependencyTypeBadge type={dependency.dependency_type} />
        </div>

        <div className="flex items-center gap-2">
          {dependency.is_installed ? (
            dependency.is_satisfied ? (
              <Badge variant="secondary" className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                <CheckCircle className="w-3 h-3 mr-1" />
                {dependency.resolved_version || 'Installed'}
              </Badge>
            ) : (
              <Badge variant="secondary" className="bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400">
                <AlertTriangle className="w-3 h-3 mr-1" />
                Version mismatch
              </Badge>
            )
          ) : (
            <>
              <Badge variant="secondary" className="bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400">
                <XCircle className="w-3 h-3 mr-1" />
                Not installed
              </Badge>
              {dependency.dependency_type !== 'conflict' && onInstall && (
                <Button variant="ghost" size="sm" onClick={onInstall}>
                  <Download className="w-3 h-3 mr-1" />
                  Install
                </Button>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

// Install Order Visualization
function InstallOrderCard({ order }: { order: string[] }) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <Layers className="w-4 h-4" />
          Installation Order
        </CardTitle>
        <CardDescription>
          Dependencies should be installed in this order
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap items-center gap-2">
          {order.map((pluginId, index) => (
            <div key={pluginId} className="flex items-center">
              <Badge variant="outline" className="font-mono">
                {index + 1}. {pluginId}
              </Badge>
              {index < order.length - 1 && (
                <ArrowRight className="w-4 h-4 mx-1 text-muted-foreground" />
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

// Cycle Detection Alert
function CycleAlert({ cyclePath }: { cyclePath: string[] }) {
  return (
    <Alert variant="destructive">
      <AlertCircle className="w-4 h-4" />
      <AlertDescription>
        <strong>Circular Dependency Detected</strong>
        <p className="mt-2 text-sm">
          The following dependency cycle was found:
        </p>
        <div className="flex flex-wrap items-center gap-2 mt-2">
          {cyclePath.map((pluginId, index) => (
            <div key={`${pluginId}-${index}`} className="flex items-center">
              <Badge variant="destructive" className="font-mono">
                {pluginId}
              </Badge>
              {index < cyclePath.length - 1 && (
                <ArrowRight className="w-4 h-4 mx-1" />
              )}
            </div>
          ))}
          <ArrowRight className="w-4 h-4 mx-1" />
          <Badge variant="destructive" className="font-mono">
            {cyclePath[0]}
          </Badge>
        </div>
      </AlertDescription>
    </Alert>
  )
}

// Main Component
export function PluginDependencyGraph({
  plugin,
  onInstallDependency,
}: PluginDependencyGraphProps) {
  const [graph, setGraph] = useState<DependencyGraph | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [showOptional, setShowOptional] = useState(false)

  // Load dependency graph
  useEffect(() => {
    loadDependencyGraph()
  }, [plugin.id])

  const loadDependencyGraph = async () => {
    setIsLoading(true)
    try {
      // In production, call actual API
      // const response = await getPluginDependencies(plugin.id, { include_optional: showOptional })
      // setGraph(response)

      // Mock response
      const mockDeps = (plugin.dependencies || []) as Array<{
        plugin_id?: string
        version_constraint?: string
        optional?: boolean
      }>
      setGraph({
        root_plugin_id: plugin.id,
        nodes: [
          {
            plugin_id: plugin.id,
            version: plugin.version,
            dependencies: mockDeps.map((d) => ({
              plugin_id: d.plugin_id || 'unknown',
              version_constraint: d.version_constraint || '*',
              dependency_type: d.optional ? 'optional' : 'required',
              is_installed: false,
              is_satisfied: false,
            })),
            dependents: [],
            depth: 0,
          },
        ],
        has_cycles: false,
        install_order: [plugin.id],
        total_dependencies: mockDeps.length,
      })
    } catch (error) {
      console.error('Failed to load dependency graph:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // Filter dependencies based on settings
  const filteredDependencies = useMemo(() => {
    if (!graph || graph.nodes.length === 0) return []
    const rootNode = graph.nodes.find((n) => n.plugin_id === graph.root_plugin_id)
    if (!rootNode) return []

    return showOptional
      ? rootNode.dependencies
      : rootNode.dependencies.filter((d) => d.dependency_type !== 'optional')
  }, [graph, showOptional])

  // Stats
  const stats = useMemo(() => {
    if (!filteredDependencies) return { total: 0, installed: 0, missing: 0 }
    return {
      total: filteredDependencies.length,
      installed: filteredDependencies.filter((d) => d.is_installed).length,
      missing: filteredDependencies.filter((d) => !d.is_installed && d.dependency_type === 'required').length,
    }
  }, [filteredDependencies])

  return (
    <div className="space-y-4">
      {/* Header Actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Total:</span>
            <Badge variant="secondary">{stats.total}</Badge>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Installed:</span>
            <Badge variant="secondary" className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
              {stats.installed}
            </Badge>
          </div>
          {stats.missing > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Missing:</span>
              <Badge variant="destructive">{stats.missing}</Badge>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowOptional(!showOptional)}
          >
            {showOptional ? 'Hide' : 'Show'} Optional
          </Button>
          <Button variant="outline" size="sm" onClick={loadDependencyGraph} disabled={isLoading}>
            <RefreshCw className={`w-4 h-4 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Cycle Detection Alert */}
      {graph?.has_cycles && graph.cycle_path && (
        <CycleAlert cyclePath={graph.cycle_path} />
      )}

      {/* Dependency Tree */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <GitBranch className="w-4 h-4" />
            Dependency Tree
          </CardTitle>
          <CardDescription>
            Plugin dependencies and their installation status
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
          ) : filteredDependencies.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Package className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No dependencies</p>
              <p className="text-xs mt-1">This plugin has no external dependencies</p>
            </div>
          ) : (
            <ScrollArea className="max-h-[400px]">
              <div className="space-y-1">
                {filteredDependencies.map((dep) => (
                  <DependencyTreeNode
                    key={dep.plugin_id}
                    dependency={dep}
                    onInstall={onInstallDependency ? () => onInstallDependency(dep.plugin_id) : undefined}
                  />
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>

      {/* Installation Order */}
      {graph && graph.install_order.length > 1 && (
        <InstallOrderCard order={graph.install_order} />
      )}

      {/* Missing Dependencies Warning */}
      {stats.missing > 0 && (
        <Alert>
          <AlertTriangle className="w-4 h-4" />
          <AlertDescription>
            <strong>{stats.missing} required dependenc{stats.missing === 1 ? 'y is' : 'ies are'} missing.</strong>
            <p className="text-sm mt-1">
              Install the missing dependencies to ensure the plugin works correctly.
            </p>
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
}

export default PluginDependencyGraph
