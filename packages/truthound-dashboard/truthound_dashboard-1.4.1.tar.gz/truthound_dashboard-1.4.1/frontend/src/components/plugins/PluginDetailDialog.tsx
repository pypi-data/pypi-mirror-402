/**
 * PluginDetailDialog - Dialog for showing plugin details
 *
 * Features:
 * - Plugin metadata display
 * - README rendering (markdown)
 * - Changelog display
 * - Dependencies list
 * - Permissions display
 * - Install/Uninstall actions
 */

import { useState, useCallback } from 'react'
import { useIntlayer } from 'react-intlayer'
import { str } from '@/lib/intlayer-utils'
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { toast } from '@/hooks/use-toast'
import {
  Package,
  Download,
  Trash2,
  Power,
  PowerOff,
  Star,
  ExternalLink,
  Github,
  FileText,
  History,
  AlertTriangle,
  Shield,
  ShieldCheck,
  ShieldAlert,
  CheckCircle,
  Loader2,
  Info,
  Code,
  FileCode,
} from 'lucide-react'
import {
  installPlugin,
  uninstallPlugin,
  enablePlugin,
  disablePlugin,
  type Plugin,
} from '@/api/client'

interface PluginDetailDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  plugin: Plugin | null
  onSuccess?: () => void
}

/**
 * Security badge component
 */
function SecurityBadge({ level }: { level: string }) {
  const t = useIntlayer('plugins')

  const config: Record<string, { icon: React.ReactNode; className: string }> = {
    trusted: {
      icon: <ShieldCheck className="w-3 h-3" />,
      className: 'text-green-500 border-green-500',
    },
    verified: {
      icon: <Shield className="w-3 h-3" />,
      className: 'text-blue-500 border-blue-500',
    },
    unverified: {
      icon: <ShieldAlert className="w-3 h-3" />,
      className: 'text-yellow-500 border-yellow-500',
    },
    sandboxed: {
      icon: <Shield className="w-3 h-3" />,
      className: 'text-gray-500 border-gray-500',
    },
  }

  const { icon, className } = config[level] || config.unverified

  return (
    <Badge variant="outline" className={`gap-1 ${className}`}>
      {icon}
      {str(t.security[level as keyof typeof t.security])}
    </Badge>
  )
}

/**
 * Status badge component
 */
function StatusBadge({ status }: { status: string }) {
  const t = useIntlayer('plugins')

  const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
    available: 'outline',
    installed: 'secondary',
    enabled: 'default',
    disabled: 'secondary',
    update_available: 'outline',
    error: 'destructive',
  }

  return (
    <Badge variant={variants[status] || 'outline'}>
      {str(t.status[status === 'update_available' ? 'updateAvailable' : status as keyof typeof t.status])}
    </Badge>
  )
}

/**
 * Dialog for showing plugin details
 */
export function PluginDetailDialog({
  open,
  onOpenChange,
  plugin,
  onSuccess,
}: PluginDetailDialogProps) {
  const t = useIntlayer('plugins')
  const [activeTab, setActiveTab] = useState('overview')
  const [isLoading, setIsLoading] = useState(false)

  // Handle install
  const handleInstall = useCallback(async () => {
    if (!plugin) return
    setIsLoading(true)
    try {
      await installPlugin(plugin.id)
      toast({ title: str(t.messages.installSuccess) })
      onSuccess?.()
    } catch {
      toast({ title: str(t.messages.installFailed), variant: 'destructive' })
    } finally {
      setIsLoading(false)
    }
  }, [plugin, t, onSuccess])

  // Handle uninstall
  const handleUninstall = useCallback(async () => {
    if (!plugin) return
    setIsLoading(true)
    try {
      await uninstallPlugin(plugin.id)
      toast({ title: str(t.messages.uninstallSuccess) })
      onSuccess?.()
    } catch {
      toast({ title: str(t.messages.uninstallFailed), variant: 'destructive' })
    } finally {
      setIsLoading(false)
    }
  }, [plugin, t, onSuccess])

  // Handle enable/disable
  const handleToggle = useCallback(async () => {
    if (!plugin) return
    setIsLoading(true)
    try {
      if (plugin.is_enabled) {
        await disablePlugin(plugin.id)
        toast({ title: str(t.messages.disableSuccess) })
      } else {
        await enablePlugin(plugin.id)
        toast({ title: str(t.messages.enableSuccess) })
      }
      onSuccess?.()
    } catch {
      toast({ title: 'Operation failed', variant: 'destructive' })
    } finally {
      setIsLoading(false)
    }
  }, [plugin, t, onSuccess])

  if (!plugin) return null

  const isInstalled = plugin.status !== 'available'

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[85vh] flex flex-col p-0">
        <DialogHeader className="px-6 pt-6">
          <div className="flex items-start gap-4">
            {/* Icon */}
            {plugin.icon_url ? (
              <img
                src={plugin.icon_url}
                alt=""
                className="w-16 h-16 rounded-lg object-cover"
              />
            ) : (
              <div className="w-16 h-16 rounded-lg bg-muted flex items-center justify-center">
                <Package className="w-8 h-8 text-muted-foreground" />
              </div>
            )}

            {/* Title and Meta */}
            <div className="flex-1">
              <DialogTitle className="text-xl">{plugin.display_name}</DialogTitle>
              <DialogDescription className="mt-1">
                {str(t.card.by)} {plugin.author?.name || 'Unknown'} · v{plugin.version}
              </DialogDescription>
              <div className="flex flex-wrap gap-2 mt-2">
                <StatusBadge status={plugin.status} />
                <SecurityBadge level={plugin.security_level} />
                <Badge variant="outline" className="gap-1">
                  <Download className="w-3 h-3" />
                  {plugin.install_count}
                </Badge>
                {plugin.rating && (
                  <Badge variant="outline" className="gap-1">
                    <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                    {plugin.rating.toFixed(1)}
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </DialogHeader>

        <Tabs
          value={activeTab}
          onValueChange={setActiveTab}
          className="flex-1 flex flex-col overflow-hidden"
        >
          <div className="px-6">
            <TabsList className="w-full justify-start">
              <TabsTrigger value="overview" className="gap-1">
                <Info className="w-4 h-4" />
                {str(t.detail.overview)}
              </TabsTrigger>
              <TabsTrigger value="readme" className="gap-1">
                <FileText className="w-4 h-4" />
                README
              </TabsTrigger>
              <TabsTrigger value="changelog" className="gap-1">
                <History className="w-4 h-4" />
                {str(t.detail.changelog)}
              </TabsTrigger>
            </TabsList>
          </div>

          <ScrollArea className="flex-1 px-6 pb-4">
            {/* Overview Tab */}
            <TabsContent value="overview" className="mt-4 space-y-6">
              {/* Description */}
              <div>
                <h4 className="text-sm font-medium mb-2">{str(t.detail.description)}</h4>
                <p className="text-sm text-muted-foreground">{plugin.description}</p>
              </div>

              {/* Security Warning */}
              {plugin.security_level === 'unverified' && (
                <div className="flex items-start gap-2 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-md border border-yellow-200 dark:border-yellow-900">
                  <AlertTriangle className="w-5 h-5 text-yellow-600 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                      {str(t.securityWarnings.unverifiedPlugin)}
                    </p>
                    <p className="text-xs text-yellow-700 dark:text-yellow-300 mt-1">
                      {str(t.securityWarnings.unverifiedDescription)}
                    </p>
                  </div>
                </div>
              )}

              {/* Permissions */}
              {plugin.permissions && plugin.permissions.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium mb-2">{str(t.detail.permissions)}</h4>
                  <div className="flex flex-wrap gap-2">
                    {plugin.permissions.map((perm) => (
                      <Badge key={perm} variant="outline">
                        {str(t.permissions[perm as keyof typeof t.permissions] || perm)}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Dependencies */}
              {plugin.dependencies && plugin.dependencies.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium mb-2">{str(t.detail.dependencies)}</h4>
                  <div className="space-y-1">
                    {plugin.dependencies.map((dep, idx) => (
                      <div key={idx} className="text-sm flex items-center gap-2">
                        <Package className="w-4 h-4 text-muted-foreground" />
                        <span>{dep.plugin_id}</span>
                        <span className="text-muted-foreground">{dep.version_constraint}</span>
                        {dep.optional && (
                          <Badge variant="outline" className="text-xs">
                            Optional
                          </Badge>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Plugin Contents */}
              <div>
                <h4 className="text-sm font-medium mb-2">{str(t.detail.contents)}</h4>
                <div className="grid grid-cols-2 gap-3">
                  {plugin.validators_count > 0 && (
                    <div className="flex items-center gap-2 p-2 border rounded-md">
                      <CheckCircle className="w-5 h-5 text-primary" />
                      <div>
                        <p className="text-sm font-medium">{plugin.validators_count} Validators</p>
                        <p className="text-xs text-muted-foreground">{str(t.detail.validatorsIncluded)}</p>
                      </div>
                    </div>
                  )}
                  {plugin.reporters_count > 0 && (
                    <div className="flex items-center gap-2 p-2 border rounded-md">
                      <FileCode className="w-5 h-5 text-primary" />
                      <div>
                        <p className="text-sm font-medium">{plugin.reporters_count} Reporters</p>
                        <p className="text-xs text-muted-foreground">{str(t.detail.reportersIncluded)}</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <Separator />

              {/* Metadata */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">{str(t.detail.type)}</p>
                  <p className="font-medium">{str(t.types[plugin.type as keyof typeof t.types])}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">{str(t.detail.source)}</p>
                  <p className="font-medium">{str(t.sources[plugin.source as keyof typeof t.sources])}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">{str(t.detail.license)}</p>
                  <p className="font-medium">{plugin.license || 'Unknown'}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">{str(t.detail.version)}</p>
                  <p className="font-medium">v{plugin.version}</p>
                </div>
              </div>

              {/* Links */}
              <div className="flex flex-wrap gap-2">
                {plugin.homepage && (
                  <Button variant="outline" size="sm" asChild>
                    <a href={plugin.homepage} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="w-4 h-4 mr-1" />
                      {str(t.detail.homepage)}
                    </a>
                  </Button>
                )}
                {plugin.repository && (
                  <Button variant="outline" size="sm" asChild>
                    <a href={plugin.repository} target="_blank" rel="noopener noreferrer">
                      <Github className="w-4 h-4 mr-1" />
                      Repository
                    </a>
                  </Button>
                )}
                {plugin.documentation_url && (
                  <Button variant="outline" size="sm" asChild>
                    <a href={plugin.documentation_url} target="_blank" rel="noopener noreferrer">
                      <FileText className="w-4 h-4 mr-1" />
                      {str(t.detail.documentation)}
                    </a>
                  </Button>
                )}
              </div>
            </TabsContent>

            {/* README Tab */}
            <TabsContent value="readme" className="mt-4">
              {plugin.readme ? (
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  {/* Simple markdown rendering - in production use a proper markdown renderer */}
                  <pre className="whitespace-pre-wrap font-sans text-sm">
                    {plugin.readme}
                  </pre>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground text-center py-8">
                  {str(t.detail.noReadme)}
                </p>
              )}
            </TabsContent>

            {/* Changelog Tab */}
            <TabsContent value="changelog" className="mt-4">
              {plugin.changelog ? (
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <pre className="whitespace-pre-wrap font-sans text-sm">
                    {plugin.changelog}
                  </pre>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground text-center py-8">
                  {str(t.detail.noChangelog)}
                </p>
              )}
            </TabsContent>
          </ScrollArea>
        </Tabs>

        <DialogFooter className="px-6 pb-6 border-t pt-4">
          <div className="flex gap-2 w-full">
            {!isInstalled ? (
              <Button onClick={handleInstall} disabled={isLoading} className="flex-1">
                {isLoading ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Download className="w-4 h-4 mr-2" />
                )}
                {str(t.actions.install)}
              </Button>
            ) : (
              <>
                <Button
                  variant="outline"
                  onClick={handleToggle}
                  disabled={isLoading}
                  className="flex-1"
                >
                  {isLoading ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : plugin.is_enabled ? (
                    <PowerOff className="w-4 h-4 mr-2" />
                  ) : (
                    <Power className="w-4 h-4 mr-2" />
                  )}
                  {plugin.is_enabled ? str(t.actions.disable) : str(t.actions.enable)}
                </Button>
                <Button
                  variant="destructive"
                  onClick={handleUninstall}
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Trash2 className="w-4 h-4 mr-2" />
                  )}
                  {str(t.actions.uninstall)}
                </Button>
              </>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default PluginDetailDialog
