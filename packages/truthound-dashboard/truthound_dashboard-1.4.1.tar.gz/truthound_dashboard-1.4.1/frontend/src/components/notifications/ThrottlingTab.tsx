/**
 * Throttling Tab Component
 * Displays and manages throttling configurations
 */

import { useState, useEffect } from 'react'
import { useIntlayer } from 'react-intlayer'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useToast } from '@/hooks/use-toast'
import { str } from '@/lib/intlayer-utils'
import { Plus, Edit, Trash2, Loader2, Gauge } from 'lucide-react'
import type { ThrottlingConfig, ThrottlingStats, NotificationChannel } from '@/api/client'
import {
  listThrottlingConfigs,
  createThrottlingConfig,
  updateThrottlingConfig,
  deleteThrottlingConfig,
  getThrottlingStats,
  listNotificationChannels,
} from '@/api/client'
import { ThrottlingAlgorithmGuide, BurstAllowanceVisual } from './StrategyGuide'
import { TemplateQuickSelect } from './TemplateLibrary'
import {
  useBulkSelection,
  BulkActionBar,
  SelectionCheckbox,
} from './BulkActionBar'

interface ThrottlingTabProps {
  className?: string
}

export function ThrottlingTab({ className }: ThrottlingTabProps) {
  const content = useIntlayer('notificationsAdvanced')
  const common = useIntlayer('common')
  const { toast } = useToast()

  const [configs, setConfigs] = useState<ThrottlingConfig[]>([])
  const [channels, setChannels] = useState<NotificationChannel[]>([])
  const [stats, setStats] = useState<ThrottlingStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingConfig, setEditingConfig] = useState<ThrottlingConfig | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [configToDelete, setConfigToDelete] = useState<ThrottlingConfig | null>(null)

  // Form state
  const [formName, setFormName] = useState('')
  const [formPerMinute, setFormPerMinute] = useState<number | null>(null)
  const [formPerHour, setFormPerHour] = useState<number | null>(100)
  const [formPerDay, setFormPerDay] = useState<number | null>(null)
  const [formBurstAllowance, setFormBurstAllowance] = useState(1.5)
  const [formChannelId, setFormChannelId] = useState<string | null>(null)
  const [formIsActive, setFormIsActive] = useState(true)
  const [formSaving, setFormSaving] = useState(false)
  const [showAlgorithmGuide, setShowAlgorithmGuide] = useState(false)

  // Bulk selection
  const configSelection = useBulkSelection<ThrottlingConfig>(configs)

  const loadData = async () => {
    setLoading(true)
    try {
      const [configsRes, statsRes, channelsRes] = await Promise.all([
        listThrottlingConfigs(),
        getThrottlingStats(),
        listNotificationChannels(),
      ])
      setConfigs(configsRes.items || [])
      setStats(statsRes)
      setChannels(channelsRes.data || [])
    } catch {
      toast({
        title: str(content.errors.loadFailed),
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const openCreateDialog = () => {
    setEditingConfig(null)
    setFormName('')
    setFormPerMinute(null)
    setFormPerHour(100)
    setFormPerDay(null)
    setFormBurstAllowance(1.5)
    setFormChannelId(null)
    setFormIsActive(true)
    setIsDialogOpen(true)
  }

  const openEditDialog = (config: ThrottlingConfig) => {
    setEditingConfig(config)
    setFormName(config.name)
    setFormPerMinute(config.per_minute)
    setFormPerHour(config.per_hour)
    setFormPerDay(config.per_day)
    setFormBurstAllowance(config.burst_allowance)
    setFormChannelId(config.channel_id)
    setFormIsActive(config.is_active)
    setIsDialogOpen(true)
  }

  const handleSave = async () => {
    setFormSaving(true)
    try {
      const data = {
        name: formName,
        per_minute: formPerMinute,
        per_hour: formPerHour,
        per_day: formPerDay,
        burst_allowance: formBurstAllowance,
        channel_id: formChannelId,
        is_active: formIsActive,
      }

      if (editingConfig) {
        await updateThrottlingConfig(editingConfig.id, data)
        toast({ title: str(content.success.configUpdated) })
      } else {
        await createThrottlingConfig(data)
        toast({ title: str(content.success.configCreated) })
      }

      setIsDialogOpen(false)
      loadData()
    } catch (e) {
      toast({
        title: editingConfig
          ? str(content.errors.updateFailed)
          : str(content.errors.createFailed),
        description: e instanceof Error ? e.message : undefined,
        variant: 'destructive',
      })
    } finally {
      setFormSaving(false)
    }
  }

  const confirmDelete = (config: ThrottlingConfig) => {
    setConfigToDelete(config)
    setDeleteDialogOpen(true)
  }

  const handleDelete = async () => {
    if (!configToDelete) return

    try {
      await deleteThrottlingConfig(configToDelete.id)
      toast({ title: str(content.success.configDeleted) })
      setDeleteDialogOpen(false)
      setConfigToDelete(null)
      loadData()
    } catch {
      toast({
        title: str(content.errors.deleteFailed),
        variant: 'destructive',
      })
    }
  }

  const toggleActive = async (config: ThrottlingConfig) => {
    try {
      await updateThrottlingConfig(config.id, { is_active: !config.is_active })
      setConfigs((prev) =>
        prev.map((c) => (c.id === config.id ? { ...c, is_active: !c.is_active } : c))
      )
    } catch {
      toast({
        title: str(content.errors.updateFailed),
        variant: 'destructive',
      })
    }
  }

  const getChannelName = (channelId: string | null) => {
    if (!channelId) return content.throttling.global
    const channel = channels.find((c) => c.id === channelId)
    return channel?.name || channelId.slice(0, 8)
  }

  const formatLimit = (limit: number | null, suffix: string) => {
    if (limit === null) return '-'
    return `${limit}/${suffix}`
  }

  // Bulk action handlers
  const handleBulkEnable = async (items: ThrottlingConfig[]) => {
    const toEnable = items.filter((c) => !c.is_active)
    for (const config of toEnable) {
      await updateThrottlingConfig(config.id, { is_active: true })
    }
    toast({ title: `Enabled ${toEnable.length} configs` })
    loadData()
  }

  const handleBulkDisable = async (items: ThrottlingConfig[]) => {
    const toDisable = items.filter((c) => c.is_active)
    for (const config of toDisable) {
      await updateThrottlingConfig(config.id, { is_active: false })
    }
    toast({ title: `Disabled ${toDisable.length} configs` })
    loadData()
  }

  const handleBulkDelete = async (items: ThrottlingConfig[]) => {
    for (const config of items) {
      await deleteThrottlingConfig(config.id)
    }
    toast({ title: `Deleted ${items.length} configs` })
    loadData()
  }

  // Template apply handler
  const handleApplyTemplate = (template: { id: string; config: Record<string, unknown> }) => {
    const config = template.config as {
      per_minute?: number | null
      per_hour?: number | null
      per_day?: number | null
      burst_allowance?: number
    }
    if (config.per_minute !== undefined) setFormPerMinute(config.per_minute)
    if (config.per_hour !== undefined) setFormPerHour(config.per_hour)
    if (config.per_day !== undefined) setFormPerDay(config.per_day)
    if (config.burst_allowance !== undefined) setFormBurstAllowance(config.burst_allowance)
    toast({ title: `Applied template: ${template.id}` })
  }

  if (loading) {
    return (
      <div className={`flex items-center justify-center py-12 ${className}`}>
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className={className}>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold">{content.throttling.title}</h3>
          <p className="text-sm text-muted-foreground">{content.throttling.subtitle}</p>
        </div>
        <Button onClick={openCreateDialog}>
          <Plus className="h-4 w-4 mr-2" />
          {content.throttling.addConfig}
        </Button>
      </div>

      {/* Bulk Action Bar */}
      <BulkActionBar
        selectedItems={configSelection.selectedItems}
        totalItems={configs.length}
        onClearSelection={configSelection.clearSelection}
        onEnable={handleBulkEnable}
        onDisable={handleBulkDisable}
        onDelete={handleBulkDelete}
        itemLabel="config"
        className="mb-4"
      />

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {content.throttling.stats.totalReceived}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_received}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {content.throttling.stats.totalThrottled}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-500">{stats.total_throttled}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {content.throttling.stats.totalPassed}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-500">{stats.total_passed}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {content.throttling.stats.throttleRate}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.throttle_rate.toFixed(1)}%</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {content.throttling.stats.currentWindowCount}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.current_window_count}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {configs.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <Gauge className="h-12 w-12 mx-auto mb-4 opacity-50" />
          {content.throttling.noConfigs}
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[40px]">
                <SelectionCheckbox
                  checked={configSelection.isAllSelected}
                  indeterminate={configSelection.isSomeSelected && !configSelection.isAllSelected}
                  onCheckedChange={configSelection.toggleAll}
                />
              </TableHead>
              <TableHead>{content.common.name}</TableHead>
              <TableHead>Channel</TableHead>
              <TableHead>{content.throttling.perMinute}</TableHead>
              <TableHead>{content.throttling.perHour}</TableHead>
              <TableHead>{content.throttling.perDay}</TableHead>
              <TableHead>{content.throttling.burstAllowance}</TableHead>
              <TableHead className="w-[80px]">{content.common.active}</TableHead>
              <TableHead className="w-[100px]" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {configs.map((config) => (
              <TableRow key={config.id} className={configSelection.isSelected(config.id) ? 'bg-muted/50' : ''}>
                <TableCell>
                  <SelectionCheckbox
                    checked={configSelection.isSelected(config.id)}
                    onCheckedChange={() => configSelection.toggleItem(config.id)}
                  />
                </TableCell>
                <TableCell className="font-medium">{config.name}</TableCell>
                <TableCell>
                  <Badge variant={config.channel_id ? 'outline' : 'secondary'}>
                    {getChannelName(config.channel_id)}
                  </Badge>
                </TableCell>
                <TableCell>{formatLimit(config.per_minute, 'min')}</TableCell>
                <TableCell>{formatLimit(config.per_hour, 'hr')}</TableCell>
                <TableCell>{formatLimit(config.per_day, 'day')}</TableCell>
                <TableCell>{config.burst_allowance}x</TableCell>
                <TableCell>
                  <Switch
                    checked={config.is_active}
                    onCheckedChange={() => toggleActive(config)}
                  />
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => openEditDialog(config)}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => confirmDelete(config)}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {editingConfig ? content.throttling.editConfig : content.throttling.addConfig}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Template Quick Select */}
            <div className="flex items-center justify-between">
              <Label className="text-base font-medium">Configuration</Label>
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-7 text-xs"
                  onClick={() => setShowAlgorithmGuide(!showAlgorithmGuide)}
                >
                  {showAlgorithmGuide ? 'Hide Algorithm Guide' : 'Show Algorithm Guide'}
                </Button>
                <TemplateQuickSelect
                  category="throttling"
                  onSelect={handleApplyTemplate}
                />
              </div>
            </div>

            {/* Algorithm Guide */}
            {showAlgorithmGuide && (
              <ThrottlingAlgorithmGuide />
            )}

            <div className="space-y-2">
              <Label>{content.common.name}</Label>
              <Input
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                placeholder="Config name"
              />
            </div>

            <div className="space-y-2">
              <Label>Channel (leave empty for global)</Label>
              <Select
                value={formChannelId || '__global__'}
                onValueChange={(v) => setFormChannelId(v === '__global__' ? null : v)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__global__">{content.throttling.global}</SelectItem>
                  {channels.map((ch) => (
                    <SelectItem key={ch.id} value={ch.id}>
                      {ch.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>{content.throttling.perMinute}</Label>
                <Input
                  type="number"
                  value={formPerMinute ?? ''}
                  onChange={(e) =>
                    setFormPerMinute(e.target.value ? parseInt(e.target.value) : null)
                  }
                  placeholder="No limit"
                  min={1}
                />
              </div>
              <div className="space-y-2">
                <Label>{content.throttling.perHour}</Label>
                <Input
                  type="number"
                  value={formPerHour ?? ''}
                  onChange={(e) =>
                    setFormPerHour(e.target.value ? parseInt(e.target.value) : null)
                  }
                  placeholder="No limit"
                  min={1}
                />
              </div>
              <div className="space-y-2">
                <Label>{content.throttling.perDay}</Label>
                <Input
                  type="number"
                  value={formPerDay ?? ''}
                  onChange={(e) =>
                    setFormPerDay(e.target.value ? parseInt(e.target.value) : null)
                  }
                  placeholder="No limit"
                  min={1}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>{content.throttling.burstAllowance}</Label>
              <div className="grid grid-cols-2 gap-4">
                <Input
                  type="number"
                  value={formBurstAllowance}
                  onChange={(e) => setFormBurstAllowance(parseFloat(e.target.value) || 1.0)}
                  step={0.1}
                  min={1.0}
                  max={10.0}
                />
                <BurstAllowanceVisual
                  burstAllowance={formBurstAllowance}
                  baseLimit={formPerHour || 100}
                />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Switch checked={formIsActive} onCheckedChange={setFormIsActive} />
              <Label>{content.common.active}</Label>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
              {common.cancel}
            </Button>
            <Button onClick={handleSave} disabled={formSaving || !formName}>
              {formSaving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {common.save}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{common.delete}</DialogTitle>
          </DialogHeader>
          <p>Are you sure you want to delete "{configToDelete?.name}"?</p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              {common.cancel}
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              {common.delete}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
