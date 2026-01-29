import { useState, useCallback } from 'react'
import { useIntlayer } from 'react-intlayer'
import { useApi, useMutation } from '@/hooks/use-api'
import {
  listPlugins,
  getMarketplaceStats,
  installPlugin,
  uninstallPlugin,
  enablePlugin,
  disablePlugin,
  listCustomValidators,
  listCustomReporters,
  deleteCustomValidator,
  deleteCustomReporter,
  type Plugin,
  type PluginType,
  type PluginStatus,
  type CustomValidator,
  type CustomReporter,
} from '@/api/client'
import { str } from '@/lib/intlayer-utils'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs'
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { toast } from '@/hooks/use-toast'
import {
  Search,
  Download,
  Trash2,
  Power,
  PowerOff,
  Star,
  MoreVertical,
  Package,
  CheckCircle,
  AlertTriangle,
  Shield,
  ShieldCheck,
  ShieldAlert,
  Code,
  FileText,
  Plus,
  RefreshCw,
  Settings,
  Edit,
  Eye,
} from 'lucide-react'
import {
  ValidatorEditorDialog,
  ReporterEditorDialog,
  PluginDetailDialog,
  PluginSettingsTab,
  PluginInstallProgress,
} from '@/components/plugins'

export function Plugins() {
  const t = useIntlayer('plugins')
  const [activeTab, setActiveTab] = useState('marketplace')
  const [searchQuery, setSearchQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState<PluginType | 'all'>('all')
  const [statusFilter, setStatusFilter] = useState<PluginStatus | 'all'>('all')
  const [selectedPlugin, setSelectedPlugin] = useState<Plugin | null>(null)
  const [showInstallDialog, setShowInstallDialog] = useState(false)
  const [showUninstallDialog, setShowUninstallDialog] = useState(false)
  const [showInstallProgress, setShowInstallProgress] = useState(false)

  // New dialog states
  const [showPluginDetail, setShowPluginDetail] = useState(false)
  const [showValidatorEditor, setShowValidatorEditor] = useState(false)
  const [showReporterEditor, setShowReporterEditor] = useState(false)
  const [selectedValidator, setSelectedValidator] = useState<CustomValidator | undefined>(undefined)
  const [selectedReporter, setSelectedReporter] = useState<CustomReporter | undefined>(undefined)

  // API queries
  const { data: plugins, loading: loadingPlugins, refetch: refetchPlugins } = useApi(
    () => listPlugins({
      type: typeFilter !== 'all' ? typeFilter : undefined,
      status: statusFilter !== 'all' ? statusFilter : undefined,
      search: searchQuery || undefined,
      limit: 50,
    }),
    [typeFilter, statusFilter, searchQuery]
  )

  const { data: stats } = useApi(getMarketplaceStats, [])

  const { data: validators, loading: loadingValidators, refetch: refetchValidators } = useApi(
    () => listCustomValidators({ limit: 50 }),
    []
  )

  const { data: reporters, loading: loadingReporters, refetch: refetchReporters } = useApi(
    () => listCustomReporters({ limit: 50 }),
    []
  )

  // Mutations
  const { mutate: doInstall, loading: installing } = useMutation(
    (pluginId: string) => installPlugin(pluginId)
  )

  const { mutate: doUninstall, loading: uninstalling } = useMutation(
    (pluginId: string) => uninstallPlugin(pluginId)
  )

  const { mutate: doEnable } = useMutation(
    (pluginId: string) => enablePlugin(pluginId)
  )

  const { mutate: doDisable } = useMutation(
    (pluginId: string) => disablePlugin(pluginId)
  )

  const { mutate: doDeleteValidator } = useMutation(
    (validatorId: string) => deleteCustomValidator(validatorId)
  )

  const { mutate: doDeleteReporter } = useMutation(
    (reporterId: string) => deleteCustomReporter(reporterId)
  )

  // Handler for opening validator editor
  const handleCreateValidator = useCallback(() => {
    setSelectedValidator(undefined)
    setShowValidatorEditor(true)
  }, [])

  const handleEditValidator = useCallback((validator: CustomValidator) => {
    setSelectedValidator(validator)
    setShowValidatorEditor(true)
  }, [])

  const handleDeleteValidator = useCallback(async (validator: CustomValidator) => {
    if (!confirm(`Are you sure you want to delete "${validator.display_name}"?`)) return
    try {
      await doDeleteValidator(validator.id)
      toast({ title: str(t.messages.validatorDeleted) })
      refetchValidators()
    } catch {
      toast({ title: str(t.messages.validatorDeleteFailed), variant: 'destructive' })
    }
  }, [doDeleteValidator, refetchValidators, t])

  // Handler for opening reporter editor
  const handleCreateReporter = useCallback(() => {
    setSelectedReporter(undefined)
    setShowReporterEditor(true)
  }, [])

  const handleEditReporter = useCallback((reporter: CustomReporter) => {
    setSelectedReporter(reporter)
    setShowReporterEditor(true)
  }, [])

  const handleDeleteReporter = useCallback(async (reporter: CustomReporter) => {
    if (!confirm(`Are you sure you want to delete "${reporter.display_name}"?`)) return
    try {
      await doDeleteReporter(reporter.id)
      toast({ title: str(t.messages.reporterDeleted) })
      refetchReporters()
    } catch {
      toast({ title: str(t.messages.reporterDeleteFailed), variant: 'destructive' })
    }
  }, [doDeleteReporter, refetchReporters, t])

  // Handler for opening plugin detail
  const handleViewPlugin = useCallback((plugin: Plugin) => {
    setSelectedPlugin(plugin)
    setShowPluginDetail(true)
  }, [])

  const handleInstall = async () => {
    if (!selectedPlugin) return
    setShowInstallDialog(false)
    setShowInstallProgress(true)
  }

  const handleInstallComplete = async () => {
    if (!selectedPlugin) return
    try {
      await doInstall(selectedPlugin.id)
      toast({ title: str(t.messages.installSuccess) })
      setShowInstallProgress(false)
      setSelectedPlugin(null)
      refetchPlugins()
    } catch {
      toast({ title: str(t.messages.installFailed), variant: 'destructive' })
    }
  }

  const handleInstallRetry = () => {
    // Reset and retry installation
    setShowInstallProgress(false)
    setTimeout(() => setShowInstallProgress(true), 100)
  }

  const handleUninstall = async () => {
    if (!selectedPlugin) return
    try {
      await doUninstall(selectedPlugin.id)
      toast({ title: str(t.messages.uninstallSuccess) })
      setShowUninstallDialog(false)
      setSelectedPlugin(null)
      refetchPlugins()
    } catch {
      toast({ title: str(t.messages.uninstallFailed), variant: 'destructive' })
    }
  }

  const handleTogglePlugin = async (plugin: Plugin) => {
    try {
      if (plugin.is_enabled) {
        await doDisable(plugin.id)
        toast({ title: str(t.messages.disableSuccess) })
      } else {
        await doEnable(plugin.id)
        toast({ title: str(t.messages.enableSuccess) })
      }
      refetchPlugins()
    } catch {
      toast({ title: 'Operation failed', variant: 'destructive' })
    }
  }

  const getStatusBadge = (status: PluginStatus) => {
    const variants: Record<PluginStatus, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: React.ReactNode }> = {
      available: { variant: 'outline', icon: <Package className="w-3 h-3" /> },
      installed: { variant: 'secondary', icon: <Download className="w-3 h-3" /> },
      enabled: { variant: 'default', icon: <CheckCircle className="w-3 h-3" /> },
      disabled: { variant: 'secondary', icon: <PowerOff className="w-3 h-3" /> },
      update_available: { variant: 'outline', icon: <RefreshCw className="w-3 h-3" /> },
      error: { variant: 'destructive', icon: <AlertTriangle className="w-3 h-3" /> },
    }
    const { variant, icon } = variants[status] || variants.available
    return (
      <Badge variant={variant} className="gap-1">
        {icon}
        {str(t.status[status === 'update_available' ? 'updateAvailable' : status])}
      </Badge>
    )
  }

  const getSecurityBadge = (level: string) => {
    const icons: Record<string, React.ReactNode> = {
      trusted: <ShieldCheck className="w-3 h-3 text-green-500" />,
      verified: <Shield className="w-3 h-3 text-blue-500" />,
      unverified: <ShieldAlert className="w-3 h-3 text-yellow-500" />,
      sandboxed: <Shield className="w-3 h-3 text-gray-500" />,
    }
    return (
      <Badge variant="outline" className="gap-1">
        {icons[level]}
        {str(t.security[level as keyof typeof t.security])}
      </Badge>
    )
  }

  const getTypeBadge = (type: PluginType) => {
    const icons: Record<PluginType, React.ReactNode> = {
      validator: <CheckCircle className="w-3 h-3" />,
      reporter: <FileText className="w-3 h-3" />,
      connector: <Package className="w-3 h-3" />,
      transformer: <Settings className="w-3 h-3" />,
    }
    return (
      <Badge variant="secondary" className="gap-1">
        {icons[type]}
        {str(t.types[type])}
      </Badge>
    )
  }

  const renderPluginCard = (plugin: Plugin) => (
    <Card
      key={plugin.id}
      className="flex flex-col cursor-pointer hover:border-primary/50 transition-colors"
      onClick={() => handleViewPlugin(plugin)}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            {plugin.icon_url ? (
              <img src={plugin.icon_url} alt="" className="w-10 h-10 rounded" />
            ) : (
              <div className="w-10 h-10 rounded bg-muted flex items-center justify-center">
                <Package className="w-5 h-5 text-muted-foreground" />
              </div>
            )}
            <div>
              <CardTitle className="text-base">{plugin.display_name}</CardTitle>
              <CardDescription className="text-xs">
                {str(t.card.by)} {plugin.author?.name || 'Unknown'} · v{plugin.version}
              </CardDescription>
            </div>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreVertical className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleViewPlugin(plugin); }}>
                <Eye className="w-4 h-4 mr-2" />
                {str(t.actions.viewDetails)}
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              {plugin.status === 'available' && (
                <DropdownMenuItem onClick={(e) => { e.stopPropagation(); setSelectedPlugin(plugin); setShowInstallDialog(true); }}>
                  <Download className="w-4 h-4 mr-2" />
                  {str(t.actions.install)}
                </DropdownMenuItem>
              )}
              {(plugin.status === 'installed' || plugin.status === 'enabled' || plugin.status === 'disabled') && (
                <>
                  <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleTogglePlugin(plugin); }}>
                    {plugin.is_enabled ? (
                      <>
                        <PowerOff className="w-4 h-4 mr-2" />
                        {str(t.actions.disable)}
                      </>
                    ) : (
                      <>
                        <Power className="w-4 h-4 mr-2" />
                        {str(t.actions.enable)}
                      </>
                    )}
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    className="text-destructive"
                    onClick={(e) => { e.stopPropagation(); setSelectedPlugin(plugin); setShowUninstallDialog(true); }}
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    {str(t.actions.uninstall)}
                  </DropdownMenuItem>
                </>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>
      <CardContent className="flex-1 pb-2">
        <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
          {plugin.description}
        </p>
        <div className="flex flex-wrap gap-1">
          {getTypeBadge(plugin.type)}
          {getStatusBadge(plugin.status)}
          {getSecurityBadge(plugin.security_level)}
        </div>
      </CardContent>
      <CardFooter className="pt-2 border-t text-xs text-muted-foreground">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1">
            <Download className="w-3 h-3" />
            {plugin.install_count}
          </span>
          {plugin.rating && (
            <span className="flex items-center gap-1">
              <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
              {plugin.rating.toFixed(1)}
            </span>
          )}
          {plugin.validators_count > 0 && (
            <span>{plugin.validators_count} validators</span>
          )}
          {plugin.reporters_count > 0 && (
            <span>{plugin.reporters_count} reporters</span>
          )}
        </div>
      </CardFooter>
    </Card>
  )

  const renderValidatorCard = (validator: CustomValidator) => (
    <Card key={validator.id} className="hover:border-primary/50 transition-colors">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-base flex items-center gap-2">
              <Code className="w-4 h-4" />
              {validator.display_name}
            </CardTitle>
            <CardDescription className="text-xs">
              {validator.category} · {str(t.validator.usageCount)}: {validator.usage_count}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={validator.is_enabled ? 'default' : 'secondary'}>
              {validator.is_enabled ? str(t.status.enabled) : str(t.status.disabled)}
            </Badge>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <MoreVertical className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => handleEditValidator(validator)}>
                  <Edit className="w-4 h-4 mr-2" />
                  {str(t.actions.edit)}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="text-destructive"
                  onClick={() => handleDeleteValidator(validator)}
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  {str(t.actions.delete)}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground line-clamp-2 mb-2">
          {validator.description}
        </p>
        <div className="flex flex-wrap gap-1">
          <Badge variant="outline">{validator.severity}</Badge>
          {validator.is_verified && (
            <Badge variant="secondary" className="gap-1">
              <ShieldCheck className="w-3 h-3" />
              {str(t.validator.verified)}
            </Badge>
          )}
          {validator.tags.slice(0, 3).map(tag => (
            <Badge key={tag} variant="outline">{tag}</Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  )

  const renderReporterCard = (reporter: CustomReporter) => (
    <Card key={reporter.id} className="hover:border-primary/50 transition-colors">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-base flex items-center gap-2">
              <FileText className="w-4 h-4" />
              {reporter.display_name}
            </CardTitle>
            <CardDescription className="text-xs">
              {str(t.reporter.usageCount)}: {reporter.usage_count}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={reporter.is_enabled ? 'default' : 'secondary'}>
              {reporter.is_enabled ? str(t.status.enabled) : str(t.status.disabled)}
            </Badge>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <MoreVertical className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => handleEditReporter(reporter)}>
                  <Edit className="w-4 h-4 mr-2" />
                  {str(t.actions.edit)}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="text-destructive"
                  onClick={() => handleDeleteReporter(reporter)}
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  {str(t.actions.delete)}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground line-clamp-2 mb-2">
          {reporter.description}
        </p>
        <div className="flex flex-wrap gap-1">
          {reporter.output_formats.map(format => (
            <Badge key={format} variant="outline">{format.toUpperCase()}</Badge>
          ))}
          {reporter.is_verified && (
            <Badge variant="secondary" className="gap-1">
              <ShieldCheck className="w-3 h-3" />
              {str(t.reporter.title)}
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  )

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t.title}</h1>
          <p className="text-muted-foreground">{t.description}</p>
        </div>
        <Button onClick={() => refetchPlugins()}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card>
            <CardContent className="pt-4">
              <div className="text-2xl font-bold">{stats.total_plugins}</div>
              <div className="text-xs text-muted-foreground">{str(t.stats.totalPlugins)}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-2xl font-bold">{stats.total_validators}</div>
              <div className="text-xs text-muted-foreground">{str(t.stats.totalValidators)}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-2xl font-bold">{stats.total_reporters}</div>
              <div className="text-xs text-muted-foreground">{str(t.stats.totalReporters)}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-2xl font-bold">{plugins?.data.filter(p => p.status !== 'available').length || 0}</div>
              <div className="text-xs text-muted-foreground">{str(t.stats.installedPlugins)}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-2xl font-bold">{plugins?.data.filter(p => p.is_enabled).length || 0}</div>
              <div className="text-xs text-muted-foreground">{str(t.stats.enabledPlugins)}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="marketplace">{t.tabs.marketplace}</TabsTrigger>
          <TabsTrigger value="installed">{t.tabs.installed}</TabsTrigger>
          <TabsTrigger value="validators">{t.tabs.validators}</TabsTrigger>
          <TabsTrigger value="reporters">{t.tabs.reporters}</TabsTrigger>
          <TabsTrigger value="settings" className="gap-1">
            <Settings className="w-3 h-3" />
            Settings
          </TabsTrigger>
        </TabsList>

        {/* Marketplace Tab */}
        <TabsContent value="marketplace" className="space-y-4">
          {/* Search and Filters */}
          <div className="flex flex-col md:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder={str(t.search.placeholder)}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select value={typeFilter} onValueChange={(v) => setTypeFilter(v as PluginType | 'all')}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder={str(t.search.filterByType)} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="validator">{str(t.types.validator)}</SelectItem>
                <SelectItem value="reporter">{str(t.types.reporter)}</SelectItem>
                <SelectItem value="connector">{str(t.types.connector)}</SelectItem>
                <SelectItem value="transformer">{str(t.types.transformer)}</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as PluginStatus | 'all')}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder={str(t.search.filterByStatus)} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="available">{str(t.status.available)}</SelectItem>
                <SelectItem value="installed">{str(t.status.installed)}</SelectItem>
                <SelectItem value="enabled">{str(t.status.enabled)}</SelectItem>
                <SelectItem value="disabled">{str(t.status.disabled)}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Plugin Grid */}
          {loadingPlugins ? (
            <div className="text-center py-8 text-muted-foreground">Loading...</div>
          ) : plugins?.data.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">{str(t.messages.noPlugins)}</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {plugins?.data.map(renderPluginCard)}
            </div>
          )}
        </TabsContent>

        {/* Installed Tab */}
        <TabsContent value="installed" className="space-y-4">
          {loadingPlugins ? (
            <div className="text-center py-8 text-muted-foreground">Loading...</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {plugins?.data
                .filter(p => p.status !== 'available')
                .map(renderPluginCard)}
            </div>
          )}
          {plugins?.data.filter(p => p.status !== 'available').length === 0 && (
            <div className="text-center py-8 text-muted-foreground">{str(t.messages.noPlugins)}</div>
          )}
        </TabsContent>

        {/* Validators Tab */}
        <TabsContent value="validators" className="space-y-4">
          <div className="flex justify-between">
            <h2 className="text-lg font-semibold">{t.validator.title}</h2>
            <Button onClick={handleCreateValidator}>
              <Plus className="w-4 h-4 mr-2" />
              {str(t.validator.createNew)}
            </Button>
          </div>
          {loadingValidators ? (
            <div className="text-center py-8 text-muted-foreground">Loading...</div>
          ) : validators?.data.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">{str(t.messages.noValidators)}</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {validators?.data.map(renderValidatorCard)}
            </div>
          )}
        </TabsContent>

        {/* Reporters Tab */}
        <TabsContent value="reporters" className="space-y-4">
          <div className="flex justify-between">
            <h2 className="text-lg font-semibold">{t.reporter.title}</h2>
            <Button onClick={handleCreateReporter}>
              <Plus className="w-4 h-4 mr-2" />
              {str(t.reporter.createNew)}
            </Button>
          </div>
          {loadingReporters ? (
            <div className="text-center py-8 text-muted-foreground">Loading...</div>
          ) : reporters?.data.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">{str(t.messages.noReporters)}</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {reporters?.data.map(renderReporterCard)}
            </div>
          )}
        </TabsContent>

        {/* Settings Tab */}
        <TabsContent value="settings" className="space-y-4">
          <PluginSettingsTab />
        </TabsContent>
      </Tabs>

      {/* Install Dialog */}
      <Dialog open={showInstallDialog} onOpenChange={setShowInstallDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{str(t.actions.install)} {selectedPlugin?.display_name}</DialogTitle>
            <DialogDescription>
              {selectedPlugin?.security_level === 'unverified' && (
                <div className="flex items-center gap-2 text-yellow-600 mt-2">
                  <AlertTriangle className="w-4 h-4" />
                  {str(t.securityWarnings.unverifiedPlugin)}
                </div>
              )}
              {selectedPlugin?.permissions && selectedPlugin.permissions.length > 0 && (
                <div className="mt-4">
                  <p className="font-medium">{str(t.securityWarnings.permissionsRequired)}</p>
                  <ul className="list-disc list-inside mt-2">
                    {selectedPlugin.permissions.map(p => (
                      <li key={p}>{str(t.permissions[p as keyof typeof t.permissions] || p)}</li>
                    ))}
                  </ul>
                </div>
              )}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowInstallDialog(false)}>
              {str(t.actions.cancel)}
            </Button>
            <Button onClick={handleInstall} disabled={installing}>
              {installing ? 'Installing...' : str(t.actions.install)}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Uninstall Dialog */}
      <Dialog open={showUninstallDialog} onOpenChange={setShowUninstallDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{str(t.actions.uninstall)} {selectedPlugin?.display_name}</DialogTitle>
            <DialogDescription>
              {str(t.messages.confirmUninstall)}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowUninstallDialog(false)}>
              {str(t.actions.cancel)}
            </Button>
            <Button variant="destructive" onClick={handleUninstall} disabled={uninstalling}>
              {uninstalling ? 'Uninstalling...' : str(t.actions.uninstall)}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Plugin Detail Dialog */}
      <PluginDetailDialog
        open={showPluginDetail}
        onOpenChange={setShowPluginDetail}
        plugin={selectedPlugin}
        onSuccess={() => {
          refetchPlugins()
          setShowPluginDetail(false)
        }}
      />

      {/* Validator Editor Dialog */}
      <ValidatorEditorDialog
        open={showValidatorEditor}
        onOpenChange={setShowValidatorEditor}
        validator={selectedValidator}
        onSuccess={() => {
          refetchValidators()
          setShowValidatorEditor(false)
        }}
      />

      {/* Reporter Editor Dialog */}
      <ReporterEditorDialog
        open={showReporterEditor}
        onOpenChange={setShowReporterEditor}
        reporter={selectedReporter}
        onSuccess={() => {
          refetchReporters()
          setShowReporterEditor(false)
        }}
      />

      {/* Install Progress Dialog */}
      <PluginInstallProgress
        open={showInstallProgress}
        onOpenChange={setShowInstallProgress}
        plugin={selectedPlugin}
        onComplete={handleInstallComplete}
        onRetry={handleInstallRetry}
      />
    </div>
  )
}

export default Plugins
