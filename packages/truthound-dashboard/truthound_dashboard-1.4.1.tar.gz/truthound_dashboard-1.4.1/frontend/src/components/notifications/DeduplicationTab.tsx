/**
 * Deduplication Tab Component
 * Displays and manages deduplication configurations
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
import { Plus, Edit, Trash2, Loader2, Filter } from 'lucide-react'
import type {
  DeduplicationConfig,
  DeduplicationStats,
  DeduplicationStrategy,
  DeduplicationPolicy,
} from '@/api/client'
import {
  listDeduplicationConfigs,
  createDeduplicationConfig,
  updateDeduplicationConfig,
  deleteDeduplicationConfig,
  getDeduplicationStats,
} from '@/api/client'
import { DeduplicationStrategyGuide, DeduplicationPolicyGuide } from './StrategyGuide'
import { TemplateQuickSelect } from './TemplateLibrary'
import {
  useBulkSelection,
  BulkActionBar,
  SelectionCheckbox,
} from './BulkActionBar'

interface DeduplicationTabProps {
  className?: string
}

const STRATEGIES: DeduplicationStrategy[] = ['sliding', 'tumbling', 'session', 'adaptive']
const POLICIES: DeduplicationPolicy[] = ['none', 'basic', 'severity', 'issue_based', 'strict', 'custom']

export function DeduplicationTab({ className }: DeduplicationTabProps) {
  const content = useIntlayer('notificationsAdvanced')
  const common = useIntlayer('common')
  const { toast } = useToast()

  const [configs, setConfigs] = useState<DeduplicationConfig[]>([])
  const [stats, setStats] = useState<DeduplicationStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingConfig, setEditingConfig] = useState<DeduplicationConfig | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [configToDelete, setConfigToDelete] = useState<DeduplicationConfig | null>(null)

  // Form state
  const [formName, setFormName] = useState('')
  const [formStrategy, setFormStrategy] = useState<DeduplicationStrategy>('sliding')
  const [formPolicy, setFormPolicy] = useState<DeduplicationPolicy>('basic')
  const [formWindowSeconds, setFormWindowSeconds] = useState(300)
  const [formIsActive, setFormIsActive] = useState(true)
  const [formSaving, setFormSaving] = useState(false)
  const [showStrategyGuide, setShowStrategyGuide] = useState(false)
  const [showPolicyGuide, setShowPolicyGuide] = useState(false)

  // Bulk selection
  const configSelection = useBulkSelection<DeduplicationConfig>(configs)

  const loadData = async () => {
    setLoading(true)
    try {
      const [configsRes, statsRes] = await Promise.all([
        listDeduplicationConfigs(),
        getDeduplicationStats(),
      ])
      setConfigs(configsRes.items || [])
      setStats(statsRes)
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
    setFormStrategy('sliding')
    setFormPolicy('basic')
    setFormWindowSeconds(300)
    setFormIsActive(true)
    setIsDialogOpen(true)
  }

  const openEditDialog = (config: DeduplicationConfig) => {
    setEditingConfig(config)
    setFormName(config.name)
    setFormStrategy(config.strategy)
    setFormPolicy(config.policy)
    setFormWindowSeconds(config.window_seconds)
    setFormIsActive(config.is_active)
    setIsDialogOpen(true)
  }

  const handleSave = async () => {
    setFormSaving(true)
    try {
      const data = {
        name: formName,
        strategy: formStrategy,
        policy: formPolicy,
        window_seconds: formWindowSeconds,
        is_active: formIsActive,
      }

      if (editingConfig) {
        await updateDeduplicationConfig(editingConfig.id, data)
        toast({ title: str(content.success.configUpdated) })
      } else {
        await createDeduplicationConfig(data)
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

  const confirmDelete = (config: DeduplicationConfig) => {
    setConfigToDelete(config)
    setDeleteDialogOpen(true)
  }

  const handleDelete = async () => {
    if (!configToDelete) return

    try {
      await deleteDeduplicationConfig(configToDelete.id)
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

  const toggleActive = async (config: DeduplicationConfig) => {
    try {
      await updateDeduplicationConfig(config.id, { is_active: !config.is_active })
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

  const getStrategyLabel = (strategy: DeduplicationStrategy): string => {
    const labels: Record<DeduplicationStrategy, string> = {
      sliding: 'Sliding Window',
      tumbling: 'Tumbling Window',
      session: 'Session Window',
      adaptive: 'Adaptive Window',
    }
    return labels[strategy] || strategy
  }

  const getPolicyLabel = (policy: DeduplicationPolicy): string => {
    const labels: Record<DeduplicationPolicy, string> = {
      none: 'None',
      basic: 'Basic',
      severity: 'By Severity',
      issue_based: 'Issue Based',
      strict: 'Strict',
      custom: 'Custom',
    }
    return labels[policy] || policy
  }

  // Bulk action handlers
  const handleBulkEnable = async (items: DeduplicationConfig[]) => {
    const toEnable = items.filter((c) => !c.is_active)
    for (const config of toEnable) {
      await updateDeduplicationConfig(config.id, { is_active: true })
    }
    toast({ title: `Enabled ${toEnable.length} configs` })
    loadData()
  }

  const handleBulkDisable = async (items: DeduplicationConfig[]) => {
    const toDisable = items.filter((c) => c.is_active)
    for (const config of toDisable) {
      await updateDeduplicationConfig(config.id, { is_active: false })
    }
    toast({ title: `Disabled ${toDisable.length} configs` })
    loadData()
  }

  const handleBulkDelete = async (items: DeduplicationConfig[]) => {
    for (const config of items) {
      await deleteDeduplicationConfig(config.id)
    }
    toast({ title: `Deleted ${items.length} configs` })
    loadData()
  }

  // Template apply handler
  const handleApplyTemplate = (template: { id: string; config: Record<string, unknown> }) => {
    const config = template.config as {
      strategy?: DeduplicationStrategy
      policy?: DeduplicationPolicy
      window_seconds?: number
    }
    if (config.strategy) setFormStrategy(config.strategy)
    if (config.policy) setFormPolicy(config.policy)
    if (config.window_seconds) setFormWindowSeconds(config.window_seconds)
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
          <h3 className="text-lg font-semibold">{content.deduplication.title}</h3>
          <p className="text-sm text-muted-foreground">{content.deduplication.subtitle}</p>
        </div>
        <Button onClick={openCreateDialog}>
          <Plus className="h-4 w-4 mr-2" />
          {content.deduplication.addConfig}
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
                {content.deduplication.stats.totalReceived}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_received}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {content.deduplication.stats.totalDeduplicated}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_deduplicated}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {content.deduplication.stats.totalPassed}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_passed}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {content.deduplication.stats.dedupRate}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.dedup_rate.toFixed(1)}%</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {content.deduplication.stats.activeFingerprints}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.active_fingerprints}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {configs.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <Filter className="h-12 w-12 mx-auto mb-4 opacity-50" />
          {content.deduplication.noConfigs}
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
              <TableHead>{content.deduplication.strategy}</TableHead>
              <TableHead>{content.deduplication.policy}</TableHead>
              <TableHead>{content.deduplication.windowSeconds}</TableHead>
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
                  <Badge variant="secondary">{getStrategyLabel(config.strategy)}</Badge>
                </TableCell>
                <TableCell>
                  <Badge variant="outline">{getPolicyLabel(config.policy)}</Badge>
                </TableCell>
                <TableCell>{config.window_seconds}s</TableCell>
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
              {editingConfig ? content.deduplication.editConfig : content.deduplication.addConfig}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Template Quick Select */}
            <div className="flex items-center justify-between">
              <Label className="text-base font-medium">Configuration</Label>
              <TemplateQuickSelect
                category="deduplication"
                onSelect={handleApplyTemplate}
              />
            </div>

            <div className="space-y-2">
              <Label>{content.common.name}</Label>
              <Input
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                placeholder="Config name"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>{content.deduplication.strategy}</Label>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="h-6 text-xs"
                    onClick={() => setShowStrategyGuide(!showStrategyGuide)}
                  >
                    {showStrategyGuide ? 'Hide Guide' : 'Show Guide'}
                  </Button>
                </div>
                <Select value={formStrategy} onValueChange={(v) => setFormStrategy(v as DeduplicationStrategy)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {STRATEGIES.map((s) => (
                      <SelectItem key={s} value={s}>
                        {getStrategyLabel(s)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>{content.deduplication.policy}</Label>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="h-6 text-xs"
                    onClick={() => setShowPolicyGuide(!showPolicyGuide)}
                  >
                    {showPolicyGuide ? 'Hide Guide' : 'Show Guide'}
                  </Button>
                </div>
                <Select value={formPolicy} onValueChange={(v) => setFormPolicy(v as DeduplicationPolicy)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {POLICIES.map((p) => (
                      <SelectItem key={p} value={p}>
                        {getPolicyLabel(p)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Strategy Guide */}
            {showStrategyGuide && (
              <DeduplicationStrategyGuide
                selectedStrategy={formStrategy}
                onSelect={(s) => setFormStrategy(s as DeduplicationStrategy)}
              />
            )}

            {/* Policy Guide */}
            {showPolicyGuide && (
              <DeduplicationPolicyGuide
                selectedPolicy={formPolicy}
                onSelect={(p) => setFormPolicy(p as DeduplicationPolicy)}
              />
            )}

            <div className="space-y-2">
              <Label>{content.deduplication.windowSeconds}</Label>
              <Input
                type="number"
                value={formWindowSeconds}
                onChange={(e) => setFormWindowSeconds(parseInt(e.target.value) || 60)}
                min={1}
                max={86400}
              />
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
