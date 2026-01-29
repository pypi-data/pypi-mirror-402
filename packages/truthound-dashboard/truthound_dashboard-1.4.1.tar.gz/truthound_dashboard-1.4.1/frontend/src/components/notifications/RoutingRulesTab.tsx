/**
 * Routing Rules Tab Component
 * Displays and manages notification routing rules with visual rule builder
 */

import { useState, useEffect, useCallback } from 'react'
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { useToast } from '@/hooks/use-toast'
import { str } from '@/lib/intlayer-utils'
import {
  Plus,
  MoreHorizontal,
  Edit,
  Trash2,
  ArrowUpDown,
  Loader2,
  Code,
  Wand2,
  Copy,
  Check,
  AlertCircle,
} from 'lucide-react'
import type { RoutingRule, NotificationChannel } from '@/api/client'
import {
  listRoutingRules,
  createRoutingRule,
  updateRoutingRule,
  deleteRoutingRule,
  listNotificationChannels,
} from '@/api/client'
import {
  RuleBuilder,
  RuleTypeRegistry,
  getRuleSummary,
  jsonToRuleConfig,
  ruleConfigToJson,
  type RuleConfig,
} from './RuleBuilder'
import { RuleTestInline } from './RuleTestPanel'
import { TemplateQuickSelect } from './TemplateLibrary'
import {
  useBulkSelection,
  BulkActionBar,
  SelectionCheckbox,
} from './BulkActionBar'

interface RoutingRulesTabProps {
  className?: string
}

export function RoutingRulesTab({ className }: RoutingRulesTabProps) {
  const content = useIntlayer('notificationsAdvanced')
  const common = useIntlayer('common')
  const { toast } = useToast()

  const [rules, setRules] = useState<RoutingRule[]>([])
  const [channels, setChannels] = useState<NotificationChannel[]>([])
  const [loading, setLoading] = useState(true)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingRule, setEditingRule] = useState<RoutingRule | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [ruleToDelete, setRuleToDelete] = useState<RoutingRule | null>(null)

  // Form state
  const [formName, setFormName] = useState('')
  const [formPriority, setFormPriority] = useState(0)
  const [formStopOnMatch, setFormStopOnMatch] = useState(false)
  const [formIsActive, setFormIsActive] = useState(true)
  const [formRuleConfig, setFormRuleConfig] = useState<RuleConfig>({ type: 'always' })
  const [formRuleConfigJson, setFormRuleConfigJson] = useState('{"type": "always"}')
  const [formActions, setFormActions] = useState<string[]>([])
  const [formSaving, setFormSaving] = useState(false)
  const [editorMode, setEditorMode] = useState<'visual' | 'json'>('visual')
  const [jsonError, setJsonError] = useState<string | null>(null)
  const [copiedJson, setCopiedJson] = useState(false)
  const [showRuleTest, setShowRuleTest] = useState(false)

  // Bulk selection
  const ruleSelection = useBulkSelection<RoutingRule>(rules)

  const loadData = async () => {
    setLoading(true)
    try {
      const [rulesRes, channelsRes] = await Promise.all([
        listRoutingRules(),
        listNotificationChannels(),
      ])
      setRules(rulesRes.items || [])
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

  // Sync visual config to JSON when switching modes
  const syncVisualToJson = useCallback(() => {
    setFormRuleConfigJson(ruleConfigToJson(formRuleConfig))
    setJsonError(null)
  }, [formRuleConfig])

  // Sync JSON to visual config when switching modes
  const syncJsonToVisual = useCallback(() => {
    const parsed = jsonToRuleConfig(formRuleConfigJson)
    if (parsed) {
      setFormRuleConfig(parsed)
      setJsonError(null)
    } else {
      setJsonError('Invalid JSON structure. Expected an object with a "type" field.')
    }
  }, [formRuleConfigJson])

  const handleEditorModeChange = (mode: string) => {
    if (mode === 'json' && editorMode === 'visual') {
      syncVisualToJson()
    } else if (mode === 'visual' && editorMode === 'json') {
      syncJsonToVisual()
    }
    setEditorMode(mode as 'visual' | 'json')
  }

  const handleRuleConfigChange = (config: RuleConfig) => {
    setFormRuleConfig(config)
  }

  const handleJsonChange = (json: string) => {
    setFormRuleConfigJson(json)
    try {
      const parsed = JSON.parse(json)
      if (parsed && typeof parsed.type === 'string') {
        setJsonError(null)
      } else {
        setJsonError('Invalid structure: missing "type" field')
      }
    } catch (e) {
      setJsonError(e instanceof Error ? e.message : 'Invalid JSON')
    }
  }

  const copyJsonToClipboard = async () => {
    const json = editorMode === 'visual' ? ruleConfigToJson(formRuleConfig) : formRuleConfigJson
    await navigator.clipboard.writeText(json)
    setCopiedJson(true)
    setTimeout(() => setCopiedJson(false), 2000)
  }

  const openCreateDialog = () => {
    setEditingRule(null)
    setFormName('')
    setFormPriority(0)
    setFormStopOnMatch(false)
    setFormIsActive(true)
    setFormRuleConfig({ type: 'always' })
    setFormRuleConfigJson('{"type": "always"}')
    setFormActions([])
    setEditorMode('visual')
    setJsonError(null)
    setIsDialogOpen(true)
  }

  const openEditDialog = (rule: RoutingRule) => {
    setEditingRule(rule)
    setFormName(rule.name)
    setFormPriority(rule.priority)
    setFormStopOnMatch(rule.stop_on_match)
    setFormIsActive(rule.is_active)

    // Parse the rule config
    const config = rule.rule_config as RuleConfig
    setFormRuleConfig(config)
    setFormRuleConfigJson(JSON.stringify(config, null, 2))

    setFormActions(rule.actions)
    setEditorMode('visual')
    setJsonError(null)
    setIsDialogOpen(true)
  }

  const handleSave = async () => {
    setFormSaving(true)
    try {
      // Get the final config based on current editor mode
      let ruleConfig: RuleConfig
      if (editorMode === 'json') {
        const parsed = jsonToRuleConfig(formRuleConfigJson)
        if (!parsed) {
          toast({
            title: 'Invalid rule configuration',
            description: 'Please fix the JSON before saving.',
            variant: 'destructive',
          })
          setFormSaving(false)
          return
        }
        ruleConfig = parsed
      } else {
        ruleConfig = formRuleConfig
      }

      // Validate the rule
      if (!RuleTypeRegistry.validate(ruleConfig)) {
        toast({
          title: 'Incomplete rule configuration',
          description: 'Please fill in all required fields.',
          variant: 'destructive',
        })
        setFormSaving(false)
        return
      }

      const data = {
        name: formName,
        priority: formPriority,
        stop_on_match: formStopOnMatch,
        is_active: formIsActive,
        rule_config: ruleConfig,
        actions: formActions,
      }

      if (editingRule) {
        await updateRoutingRule(editingRule.id, data)
        toast({ title: str(content.success.configUpdated) })
      } else {
        await createRoutingRule(data)
        toast({ title: str(content.success.configCreated) })
      }

      setIsDialogOpen(false)
      loadData()
    } catch (e) {
      toast({
        title: editingRule
          ? str(content.errors.updateFailed)
          : str(content.errors.createFailed),
        description: e instanceof Error ? e.message : undefined,
        variant: 'destructive',
      })
    } finally {
      setFormSaving(false)
    }
  }

  const confirmDelete = (rule: RoutingRule) => {
    setRuleToDelete(rule)
    setDeleteDialogOpen(true)
  }

  const handleDelete = async () => {
    if (!ruleToDelete) return

    try {
      await deleteRoutingRule(ruleToDelete.id)
      toast({ title: str(content.success.configDeleted) })
      setDeleteDialogOpen(false)
      setRuleToDelete(null)
      loadData()
    } catch {
      toast({
        title: str(content.errors.deleteFailed),
        variant: 'destructive',
      })
    }
  }

  const toggleActive = async (rule: RoutingRule) => {
    try {
      await updateRoutingRule(rule.id, { is_active: !rule.is_active })
      setRules((prev) =>
        prev.map((r) => (r.id === rule.id ? { ...r, is_active: !r.is_active } : r))
      )
    } catch {
      toast({
        title: str(content.errors.updateFailed),
        variant: 'destructive',
      })
    }
  }

  const getChannelName = (channelId: string) => {
    const channel = channels.find((c) => c.id === channelId)
    return channel?.name || channelId.slice(0, 8)
  }

  const getRuleTypeLabel = (config: Record<string, unknown>): string => {
    const type = config.type as string
    const definition = RuleTypeRegistry.get(type as RuleConfig['type'])
    return definition?.label || type
  }

  const handleCopyRule = (config: RuleConfig) => {
    navigator.clipboard.writeText(ruleConfigToJson(config))
    toast({ title: 'Rule configuration copied to clipboard' })
  }

  // Bulk action handlers
  const handleBulkEnable = async (items: RoutingRule[]) => {
    const toEnable = items.filter((r) => !r.is_active)
    for (const rule of toEnable) {
      await updateRoutingRule(rule.id, { is_active: true })
    }
    toast({ title: `Enabled ${toEnable.length} rules` })
    loadData()
  }

  const handleBulkDisable = async (items: RoutingRule[]) => {
    const toDisable = items.filter((r) => r.is_active)
    for (const rule of toDisable) {
      await updateRoutingRule(rule.id, { is_active: false })
    }
    toast({ title: `Disabled ${toDisable.length} rules` })
    loadData()
  }

  const handleBulkDelete = async (items: RoutingRule[]) => {
    for (const rule of items) {
      await deleteRoutingRule(rule.id)
    }
    toast({ title: `Deleted ${items.length} rules` })
    loadData()
  }

  // Template apply handler
  const handleApplyTemplate = (template: { id: string; config: Record<string, unknown> }) => {
    const config = jsonToRuleConfig(JSON.stringify(template.config))
    if (config) {
      setFormRuleConfig(config)
      setFormRuleConfigJson(JSON.stringify(template.config, null, 2))
      toast({ title: `Applied template: ${template.id}` })
    }
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
          <h3 className="text-lg font-semibold">{content.routing.title}</h3>
          <p className="text-sm text-muted-foreground">{content.routing.subtitle}</p>
        </div>
        <Button onClick={openCreateDialog}>
          <Plus className="h-4 w-4 mr-2" />
          {content.routing.addRule}
        </Button>
      </div>

      {/* Bulk Action Bar */}
      <BulkActionBar
        selectedItems={ruleSelection.selectedItems}
        totalItems={rules.length}
        onClearSelection={ruleSelection.clearSelection}
        onEnable={handleBulkEnable}
        onDisable={handleBulkDisable}
        onDelete={handleBulkDelete}
        itemLabel="rule"
        className="mb-4"
      />

      {rules.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          {content.routing.noRules}
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[40px]">
                <SelectionCheckbox
                  checked={ruleSelection.isAllSelected}
                  indeterminate={ruleSelection.isSomeSelected && !ruleSelection.isAllSelected}
                  onCheckedChange={ruleSelection.toggleAll}
                />
              </TableHead>
              <TableHead>{content.common.name}</TableHead>
              <TableHead className="w-[100px]">
                <div className="flex items-center gap-1">
                  {content.routing.priority}
                  <ArrowUpDown className="h-3 w-3" />
                </div>
              </TableHead>
              <TableHead>Type</TableHead>
              <TableHead className="max-w-[200px]">Summary</TableHead>
              <TableHead>{content.routing.actions}</TableHead>
              <TableHead className="w-[100px]">{content.routing.stopOnMatch}</TableHead>
              <TableHead className="w-[80px]">{content.common.active}</TableHead>
              <TableHead className="w-[60px]" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {rules
              .sort((a, b) => b.priority - a.priority)
              .map((rule) => (
                <TableRow key={rule.id} className={ruleSelection.isSelected(rule.id) ? 'bg-muted/50' : ''}>
                  <TableCell>
                    <SelectionCheckbox
                      checked={ruleSelection.isSelected(rule.id)}
                      onCheckedChange={() => ruleSelection.toggleItem(rule.id)}
                    />
                  </TableCell>
                  <TableCell className="font-medium">{rule.name}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{rule.priority}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant="secondary">{getRuleTypeLabel(rule.rule_config)}</Badge>
                  </TableCell>
                  <TableCell className="max-w-[200px]">
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <span className="text-sm text-muted-foreground truncate block">
                            {getRuleSummary(rule.rule_config as RuleConfig)}
                          </span>
                        </TooltipTrigger>
                        <TooltipContent side="bottom" className="max-w-sm">
                          <pre className="text-xs">
                            {JSON.stringify(rule.rule_config, null, 2)}
                          </pre>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {rule.actions.slice(0, 3).map((channelId) => (
                        <Badge key={channelId} variant="outline" className="text-xs">
                          {getChannelName(channelId)}
                        </Badge>
                      ))}
                      {rule.actions.length > 3 && (
                        <Badge variant="outline" className="text-xs">
                          +{rule.actions.length - 3}
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    {rule.stop_on_match ? (
                      <Badge variant="default">Yes</Badge>
                    ) : (
                      <Badge variant="outline">No</Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <Switch
                      checked={rule.is_active}
                      onCheckedChange={() => toggleActive(rule)}
                    />
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => openEditDialog(rule)}>
                          <Edit className="h-4 w-4 mr-2" />
                          {common.edit}
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={() => confirmDelete(rule)}
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          {common.delete}
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] flex flex-col">
          <DialogHeader>
            <DialogTitle>
              {editingRule ? content.routing.editRule : content.routing.addRule}
            </DialogTitle>
            <DialogDescription>
              Configure when and where notifications should be routed.
            </DialogDescription>
          </DialogHeader>

          <div className="flex-1 overflow-hidden flex flex-col space-y-4 py-4">
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>{content.common.name}</Label>
                <Input
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder="Rule name"
                />
              </div>
              <div className="space-y-2">
                <Label>{content.routing.priority}</Label>
                <Input
                  type="number"
                  value={formPriority}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setFormPriority(parseInt(e.target.value) || 0)
                  }
                />
              </div>
            </div>

            {/* Rule Configuration */}
            <div className="space-y-2 flex-1 min-h-0 flex flex-col">
              <div className="flex items-center justify-between">
                <Label>{content.routing.ruleConfig}</Label>
                <div className="flex items-center gap-2">
                  {/* Template Quick Select */}
                  <TemplateQuickSelect
                    category="routing"
                    onSelect={handleApplyTemplate}
                    triggerClassName="h-7"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={copyJsonToClipboard}
                    className="h-7"
                  >
                    {copiedJson ? (
                      <Check className="h-3 w-3 mr-1 text-green-500" />
                    ) : (
                      <Copy className="h-3 w-3 mr-1" />
                    )}
                    Copy JSON
                  </Button>
                  <Tabs value={editorMode} onValueChange={handleEditorModeChange}>
                    <TabsList className="h-7">
                      <TabsTrigger value="visual" className="text-xs h-6 px-2">
                        <Wand2 className="h-3 w-3 mr-1" />
                        Visual
                      </TabsTrigger>
                      <TabsTrigger value="json" className="text-xs h-6 px-2">
                        <Code className="h-3 w-3 mr-1" />
                        JSON
                      </TabsTrigger>
                    </TabsList>
                  </Tabs>
                </div>
              </div>

              <div className="flex-1 min-h-0 border rounded-md">
                {editorMode === 'visual' ? (
                  <ScrollArea className="h-[300px] p-4">
                    <RuleBuilder
                      value={formRuleConfig}
                      onChange={handleRuleConfigChange}
                      maxDepth={3}
                      onCopyRule={handleCopyRule}
                    />
                  </ScrollArea>
                ) : (
                  <div className="h-[300px] flex flex-col">
                    <Textarea
                      value={formRuleConfigJson}
                      onChange={(e) => handleJsonChange(e.target.value)}
                      className="flex-1 font-mono text-sm resize-none border-0 rounded-none"
                      placeholder='{"type": "always"}'
                    />
                    {jsonError && (
                      <div className="flex items-center gap-2 p-2 bg-destructive/10 text-destructive text-sm border-t">
                        <AlertCircle className="h-4 w-4" />
                        {jsonError}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Rule Test */}
              <RuleTestInline
                ruleConfig={editorMode === 'visual' ? formRuleConfig : JSON.parse(formRuleConfigJson || '{}')}
                expanded={showRuleTest}
                onToggle={() => setShowRuleTest(!showRuleTest)}
              />
            </div>

            {/* Target Channels */}
            <div className="space-y-2">
              <Label>{content.routing.actions}</Label>
              <div className="flex flex-wrap gap-2 p-3 border rounded-md min-h-[60px]">
                {channels.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No notification channels configured. Create channels first.
                  </p>
                ) : (
                  channels.map((channel) => (
                    <Badge
                      key={channel.id}
                      variant={formActions.includes(channel.id) ? 'default' : 'outline'}
                      className="cursor-pointer transition-colors"
                      onClick={() => {
                        setFormActions((prev) =>
                          prev.includes(channel.id)
                            ? prev.filter((id) => id !== channel.id)
                            : [...prev, channel.id]
                        )
                      }}
                    >
                      {channel.name}
                    </Badge>
                  ))
                )}
              </div>
            </div>

            {/* Options */}
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <Switch
                  checked={formStopOnMatch}
                  onCheckedChange={setFormStopOnMatch}
                />
                <Label className="cursor-pointer" onClick={() => setFormStopOnMatch(!formStopOnMatch)}>
                  {content.routing.stopOnMatch}
                </Label>
              </div>
              <div className="flex items-center gap-2">
                <Switch checked={formIsActive} onCheckedChange={setFormIsActive} />
                <Label className="cursor-pointer" onClick={() => setFormIsActive(!formIsActive)}>
                  {content.common.active}
                </Label>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
              {common.cancel}
            </Button>
            <Button
              onClick={handleSave}
              disabled={formSaving || !formName || (editorMode === 'json' && !!jsonError)}
            >
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
          <p>Are you sure you want to delete "{ruleToDelete?.name}"?</p>
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
