/**
 * Notifications management page.
 *
 * Features:
 * - Channel management (all 9 channel types)
 * - Rule configuration
 * - Delivery log viewing
 * - Channel testing
 */

import { useState } from 'react'
import { useSafeIntlayer } from '@/hooks/useSafeIntlayer'
import {
  Bell,
  Plus,
  Trash2,
  Edit2,
  Send,
  CheckCircle,
  XCircle,
  Clock,
  MessageSquare,
  Mail,
  Webhook,
  RefreshCw,
  AlertTriangle,
  Github,
  Loader2,
  Filter,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
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
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { useToast } from '@/hooks/use-toast'
import { useApi, useMutation } from '@/hooks/use-api'
import { useConfirm } from '@/components/ConfirmDialog'
import {
  listNotificationChannels,
  listNotificationRules,
  listNotificationLogs,
  getNotificationStats,
  testNotificationChannel,
  createNotificationChannel,
  updateNotificationChannel,
  deleteNotificationChannel,
  createNotificationRule,
  updateNotificationRule,
  deleteNotificationRule,
  type NotificationChannel,
  type NotificationRule,
} from '@/api/client'
import { formatDate } from '@/lib/utils'
import { str } from '@/lib/intlayer-utils'
import {
  ChannelConfigForm,
  ChannelTypeSelector,
  getChannelSchema,
  type ChannelType,
  type ChannelConfig,
} from '@/components/notifications/ChannelConfigForm'

// ============================================================================
// Helper Functions
// ============================================================================

function getChannelIcon(type: string) {
  switch (type) {
    case 'slack':
      return <MessageSquare className="h-4 w-4" />
    case 'email':
      return <Mail className="h-4 w-4" />
    case 'webhook':
      return <Webhook className="h-4 w-4" />
    case 'discord':
      return <MessageSquare className="h-4 w-4" style={{ color: '#5865F2' }} />
    case 'telegram':
      return <Send className="h-4 w-4" style={{ color: '#0088CC' }} />
    case 'pagerduty':
      return <AlertTriangle className="h-4 w-4" style={{ color: '#06AC38' }} />
    case 'opsgenie':
      return <Bell className="h-4 w-4" style={{ color: '#2684FF' }} />
    case 'teams':
      return <MessageSquare className="h-4 w-4" style={{ color: '#6264A7' }} />
    case 'github':
      return <Github className="h-4 w-4" />
    default:
      return <Bell className="h-4 w-4" />
  }
}

function getStatusBadge(status: string) {
  switch (status) {
    case 'sent':
      return (
        <Badge className="bg-green-500/10 text-green-500 border-green-500/20">
          <CheckCircle className="h-3 w-3 mr-1" />
          Sent
        </Badge>
      )
    case 'failed':
      return (
        <Badge className="bg-red-500/10 text-red-500 border-red-500/20">
          <XCircle className="h-3 w-3 mr-1" />
          Failed
        </Badge>
      )
    default:
      return (
        <Badge className="bg-yellow-500/10 text-yellow-500 border-yellow-500/20">
          <Clock className="h-3 w-3 mr-1" />
          Pending
        </Badge>
      )
  }
}

const CONDITIONS = [
  { value: 'validation_failed', label: 'Validation Failed' },
  { value: 'critical_issues', label: 'Critical Issues Detected' },
  { value: 'high_issues', label: 'High Severity Issues' },
  { value: 'schedule_failed', label: 'Schedule Failed' },
  { value: 'drift_detected', label: 'Drift Detected' },
  { value: 'schema_changed', label: 'Schema Changed' },
] as const

function getConditionLabel(condition: string): string {
  const found = CONDITIONS.find((c) => c.value === condition)
  return found?.label || condition
}

// ============================================================================
// Channel Dialog Component
// ============================================================================

interface ChannelDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  channel?: NotificationChannel | null
  onSave: () => void
}

function ChannelDialog({ open, onOpenChange, channel, onSave }: ChannelDialogProps) {
  const notifications_t = useSafeIntlayer('notifications')
  const common = useSafeIntlayer('common')
  const { toast } = useToast()

  const [step, setStep] = useState<'type' | 'config'>(channel ? 'config' : 'type')
  const [channelType, setChannelType] = useState<ChannelType | null>(
    (channel?.type as ChannelType) || null
  )
  const [channelName, setChannelName] = useState(channel?.name || '')
  const [config, setConfig] = useState<ChannelConfig>(channel?.config || {})
  const [isValid, setIsValid] = useState(false)
  const [saving, setSaving] = useState(false)

  const isEdit = !!channel

  const handleTypeSelect = (type: ChannelType) => {
    setChannelType(type)
    const schema = getChannelSchema(type)
    // Set default values
    const defaults: ChannelConfig = {}
    for (const [key, field] of Object.entries(schema.fields)) {
      if (field.default !== undefined) {
        defaults[key] = field.default
      }
    }
    setConfig(defaults)
    setChannelName(`${schema.name} Channel`)
    setStep('config')
  }

  const handleBack = () => {
    if (!isEdit) {
      setStep('type')
    }
  }

  const handleSave = async () => {
    if (!channelType || !channelName.trim()) return

    setSaving(true)
    try {
      if (isEdit && channel) {
        await updateNotificationChannel(channel.id, {
          name: channelName,
          config,
        })
        toast({ title: str(notifications_t.channelUpdated) || 'Channel updated' })
      } else {
        await createNotificationChannel({
          type: channelType,
          name: channelName,
          config,
          is_active: true,
        })
        toast({ title: str(notifications_t.channelCreated) || 'Channel created' })
      }
      onSave()
      onOpenChange(false)
    } catch (error) {
      toast({
        title: isEdit
          ? str(notifications_t.updateChannelFailed) || 'Failed to update channel'
          : str(notifications_t.createChannelFailed) || 'Failed to create channel',
        variant: 'destructive',
      })
    } finally {
      setSaving(false)
    }
  }

  const handleClose = () => {
    onOpenChange(false)
    // Reset state after animation
    setTimeout(() => {
      setStep(channel ? 'config' : 'type')
      setChannelType((channel?.type as ChannelType) || null)
      setChannelName(channel?.name || '')
      setConfig(channel?.config || {})
    }, 200)
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? str(notifications_t.editChannel) : str(notifications_t.addChannel)}
          </DialogTitle>
          <DialogDescription>
            {step === 'type'
              ? 'Select a notification channel type'
              : `Configure your ${channelType} channel settings`}
          </DialogDescription>
        </DialogHeader>

        {step === 'type' && (
          <ChannelTypeSelector
            value={channelType}
            onChange={handleTypeSelect}
            className="py-4"
          />
        )}

        {step === 'config' && channelType && (
          <div className="space-y-6 py-4">
            {/* Channel Name */}
            <div className="space-y-2">
              <Label htmlFor="channel-name">
                Channel Name
                <Badge variant="outline" className="ml-2 text-xs text-red-500 border-red-500/30">
                  Required
                </Badge>
              </Label>
              <Input
                id="channel-name"
                value={channelName}
                onChange={(e) => setChannelName(e.target.value)}
                placeholder="My Slack Channel"
              />
            </div>

            {/* Channel-specific Config */}
            <ChannelConfigForm
              channelType={channelType}
              config={config}
              onChange={setConfig}
              onValidChange={setIsValid}
            />
          </div>
        )}

        <DialogFooter className="gap-2">
          {step === 'config' && !isEdit && (
            <Button variant="outline" onClick={handleBack}>
              Back
            </Button>
          )}
          <Button variant="outline" onClick={handleClose}>
            {str(common.cancel)}
          </Button>
          {step === 'config' && (
            <Button
              onClick={handleSave}
              disabled={!isValid || !channelName.trim() || saving}
            >
              {saving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {isEdit ? str(common.save) : str(common.create)}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ============================================================================
// Rule Dialog Component
// ============================================================================

interface RuleDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  rule?: NotificationRule | null
  channels: NotificationChannel[]
  onSave: () => void
}

function RuleDialog({ open, onOpenChange, rule, channels, onSave }: RuleDialogProps) {
  const notifications_t = useSafeIntlayer('notifications')
  const common = useSafeIntlayer('common')
  const { toast } = useToast()

  const [ruleName, setRuleName] = useState(rule?.name || '')
  const [condition, setCondition] = useState(rule?.condition || 'validation_failed')
  const [selectedChannels, setSelectedChannels] = useState<string[]>(rule?.channel_ids || [])
  const [saving, setSaving] = useState(false)

  const isEdit = !!rule

  const handleSave = async () => {
    if (!ruleName.trim() || selectedChannels.length === 0) return

    setSaving(true)
    try {
      if (isEdit && rule) {
        await updateNotificationRule(rule.id, {
          name: ruleName,
          condition,
          channel_ids: selectedChannels,
        })
        toast({ title: str(notifications_t.ruleUpdated) || 'Rule updated' })
      } else {
        await createNotificationRule({
          name: ruleName,
          condition,
          channel_ids: selectedChannels,
          is_active: true,
        })
        toast({ title: str(notifications_t.ruleCreated) || 'Rule created' })
      }
      onSave()
      onOpenChange(false)
    } catch (error) {
      toast({
        title: isEdit
          ? str(notifications_t.updateRuleFailed) || 'Failed to update rule'
          : str(notifications_t.createRuleFailed) || 'Failed to create rule',
        variant: 'destructive',
      })
    } finally {
      setSaving(false)
    }
  }

  const handleClose = () => {
    onOpenChange(false)
    setTimeout(() => {
      setRuleName(rule?.name || '')
      setCondition(rule?.condition || 'validation_failed')
      setSelectedChannels(rule?.channel_ids || [])
    }, 200)
  }

  const toggleChannel = (channelId: string) => {
    setSelectedChannels((prev) =>
      prev.includes(channelId)
        ? prev.filter((id) => id !== channelId)
        : [...prev, channelId]
    )
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? str(notifications_t.editRule) : str(notifications_t.addRule)}
          </DialogTitle>
          <DialogDescription>
            Configure when and where notifications should be sent
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Rule Name */}
          <div className="space-y-2">
            <Label htmlFor="rule-name">Rule Name</Label>
            <Input
              id="rule-name"
              value={ruleName}
              onChange={(e) => setRuleName(e.target.value)}
              placeholder="Critical Alerts to Slack"
            />
          </div>

          {/* Condition */}
          <div className="space-y-2">
            <Label>Trigger Condition</Label>
            <Select value={condition} onValueChange={setCondition}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CONDITIONS.map((c) => (
                  <SelectItem key={c.value} value={c.value}>
                    {c.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Channels */}
          <div className="space-y-2">
            <Label>Send To Channels</Label>
            {channels.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No channels configured. Create a channel first.
              </p>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                {channels.map((channel) => (
                  <Button
                    key={channel.id}
                    type="button"
                    variant={selectedChannels.includes(channel.id) ? 'default' : 'outline'}
                    className="justify-start h-auto py-2"
                    onClick={() => toggleChannel(channel.id)}
                  >
                    {getChannelIcon(channel.type)}
                    <span className="ml-2 truncate">{channel.name}</span>
                  </Button>
                ))}
              </div>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            {str(common.cancel)}
          </Button>
          <Button
            onClick={handleSave}
            disabled={!ruleName.trim() || selectedChannels.length === 0 || saving}
          >
            {saving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            {isEdit ? str(common.save) : str(common.create)}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ============================================================================
// Main Component
// ============================================================================

export default function Notifications() {
  const notifications_t = useSafeIntlayer('notifications')
  const common = useSafeIntlayer('common')
  const { toast } = useToast()
  const { confirm, ConfirmDialog } = useConfirm()
  const [activeTab, setActiveTab] = useState('channels')

  // Dialogs
  const [channelDialogOpen, setChannelDialogOpen] = useState(false)
  const [editingChannel, setEditingChannel] = useState<NotificationChannel | null>(null)
  const [ruleDialogOpen, setRuleDialogOpen] = useState(false)
  const [editingRule, setEditingRule] = useState<NotificationRule | null>(null)

  // Fetch data
  const {
    data: channelsData,
    loading: channelsLoading,
    refetch: refetchChannels,
  } = useApi(() => listNotificationChannels(), [])

  const {
    data: rulesData,
    loading: rulesLoading,
    refetch: refetchRules,
  } = useApi(() => listNotificationRules(), [])

  const {
    data: logsData,
    loading: logsLoading,
    refetch: refetchLogs,
  } = useApi(() => listNotificationLogs({ limit: 50 }), [])

  const { data: statsData } = useApi(
    () => getNotificationStats({ hours: 24 }),
    []
  )

  // Mutations
  const testChannelMutation = useMutation(testNotificationChannel)
  const deleteChannelMutation = useMutation(deleteNotificationChannel)
  const deleteRuleMutation = useMutation(deleteNotificationRule)

  const channels = channelsData?.data || []
  const rules = rulesData?.data || []
  const logs = logsData?.data || []
  const stats = statsData?.data

  const handleTestChannel = async (channelId: string) => {
    try {
      const result = await testChannelMutation.mutate(channelId)
      if (result.success) {
        toast({
          title: str(notifications_t.testSuccess),
          variant: 'default',
        })
      } else {
        toast({
          title: str(notifications_t.testFailed),
          description: result.error,
          variant: 'destructive',
        })
      }
    } catch {
      toast({
        title: str(notifications_t.testFailed),
        variant: 'destructive',
      })
    }
  }

  const handleDeleteChannel = async (channelId: string) => {
    const confirmed = await confirm({
      title: str(notifications_t.deleteChannel),
      description: str(notifications_t.deleteChannelConfirm),
      confirmText: str(common.delete),
      variant: 'destructive',
    })
    if (!confirmed) return

    try {
      await deleteChannelMutation.mutate(channelId)
      toast({ title: str(notifications_t.channelDeleted) })
      refetchChannels()
    } catch {
      toast({ title: str(notifications_t.deleteChannelFailed), variant: 'destructive' })
    }
  }

  const handleToggleChannel = async (channel: NotificationChannel) => {
    try {
      await updateNotificationChannel(channel.id, {
        is_active: !channel.is_active,
      })
      refetchChannels()
    } catch {
      toast({ title: 'Failed to update channel', variant: 'destructive' })
    }
  }

  const handleEditChannel = (channel: NotificationChannel) => {
    setEditingChannel(channel)
    setChannelDialogOpen(true)
  }

  const handleAddChannel = () => {
    setEditingChannel(null)
    setChannelDialogOpen(true)
  }

  const handleDeleteRule = async (ruleId: string) => {
    const confirmed = await confirm({
      title: str(notifications_t.deleteRule),
      description: str(notifications_t.deleteRuleConfirm),
      confirmText: str(common.delete),
      variant: 'destructive',
    })
    if (!confirmed) return

    try {
      await deleteRuleMutation.mutate(ruleId)
      toast({ title: str(notifications_t.ruleDeleted) })
      refetchRules()
    } catch {
      toast({ title: str(notifications_t.deleteRuleFailed), variant: 'destructive' })
    }
  }

  const handleToggleRule = async (rule: NotificationRule) => {
    try {
      await updateNotificationRule(rule.id, {
        is_active: !rule.is_active,
      })
      refetchRules()
    } catch {
      toast({ title: 'Failed to update rule', variant: 'destructive' })
    }
  }

  const handleEditRule = (rule: NotificationRule) => {
    setEditingRule(rule)
    setRuleDialogOpen(true)
  }

  const handleAddRule = () => {
    setEditingRule(null)
    setRuleDialogOpen(true)
  }

  // Group channels by type for stats
  const channelsByType = channels.reduce(
    (acc, ch) => {
      acc[ch.type] = (acc[ch.type] || 0) + 1
      return acc
    },
    {} as Record<string, number>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{notifications_t.title}</h1>
          <p className="text-muted-foreground">
            {notifications_t.subtitle}
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total (24h)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Success Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.success_rate || 0}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {notifications_t.sent}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">
              {stats?.by_status?.sent || 0}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {notifications_t.failed}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">
              {stats?.by_status?.failed || 0}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="channels">
            {notifications_t.channels} ({channels.length})
          </TabsTrigger>
          <TabsTrigger value="rules">
            {notifications_t.rules} ({rules.length})
          </TabsTrigger>
          <TabsTrigger value="logs">
            {notifications_t.logs} ({logs.length})
          </TabsTrigger>
        </TabsList>

        {/* Channels Tab */}
        <TabsContent value="channels" className="space-y-4">
          <div className="flex justify-between">
            <Button variant="outline" size="sm" onClick={() => refetchChannels()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              {common.refresh}
            </Button>
            <Button onClick={handleAddChannel}>
              <Plus className="h-4 w-4 mr-2" />
              {notifications_t.addChannel}
            </Button>
          </div>

          {/* Channel Type Summary */}
          {channels.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {Object.entries(channelsByType).map(([type, count]) => (
                <Badge key={type} variant="secondary" className="gap-1">
                  {getChannelIcon(type)}
                  <span className="capitalize">{type}</span>
                  <span className="bg-muted-foreground/20 px-1.5 rounded-full text-xs">
                    {count}
                  </span>
                </Badge>
              ))}
            </div>
          )}

          {channelsLoading ? (
            <div className="text-center py-8 text-muted-foreground">
              <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2" />
              {common.loading}
            </div>
          ) : channels.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Bell className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
                <h3 className="text-lg font-medium mb-2">{notifications_t.noChannels}</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Get started by adding a notification channel
                </p>
                <Button onClick={handleAddChannel}>
                  <Plus className="h-4 w-4 mr-2" />
                  {notifications_t.addChannel}
                </Button>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{common.name}</TableHead>
                    <TableHead>{common.type}</TableHead>
                    <TableHead>Config</TableHead>
                    <TableHead>{common.status}</TableHead>
                    <TableHead className="text-right">{common.actions}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {channels.map((channel) => (
                    <TableRow key={channel.id}>
                      <TableCell className="font-medium">{channel.name}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getChannelIcon(channel.type)}
                          <span className="capitalize">{channel.type}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-muted-foreground text-sm max-w-[200px] truncate">
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className="cursor-help">
                                {channel.config_summary || 'Configured'}
                              </span>
                            </TooltipTrigger>
                            <TooltipContent side="left" className="max-w-xs">
                              <pre className="text-xs">
                                {JSON.stringify(channel.config, null, 2)}
                              </pre>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </TableCell>
                      <TableCell>
                        <Switch
                          checked={channel.is_active}
                          onCheckedChange={() => handleToggleChannel(channel)}
                        />
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleTestChannel(channel.id)}
                                  disabled={testChannelMutation.loading}
                                >
                                  {testChannelMutation.loading ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                  ) : (
                                    <Send className="h-4 w-4" />
                                  )}
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>Send test notification</TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEditChannel(channel)}
                          >
                            <Edit2 className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteChannel(channel.id)}
                          >
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          )}
        </TabsContent>

        {/* Rules Tab */}
        <TabsContent value="rules" className="space-y-4">
          <div className="flex justify-between">
            <Button variant="outline" size="sm" onClick={() => refetchRules()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              {common.refresh}
            </Button>
            <Button onClick={handleAddRule} disabled={channels.length === 0}>
              <Plus className="h-4 w-4 mr-2" />
              {notifications_t.addRule}
            </Button>
          </div>

          {rulesLoading ? (
            <div className="text-center py-8 text-muted-foreground">
              <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2" />
              {common.loading}
            </div>
          ) : rules.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Filter className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
                <h3 className="text-lg font-medium mb-2">{notifications_t.noRules}</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  {channels.length === 0
                    ? 'Create a channel first, then add notification rules'
                    : 'Add rules to trigger notifications on specific events'}
                </p>
                <Button onClick={handleAddRule} disabled={channels.length === 0}>
                  <Plus className="h-4 w-4 mr-2" />
                  {notifications_t.addRule}
                </Button>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{common.name}</TableHead>
                    <TableHead>Condition</TableHead>
                    <TableHead>Channels</TableHead>
                    <TableHead>{common.status}</TableHead>
                    <TableHead className="text-right">{common.actions}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rules.map((rule) => (
                    <TableRow key={rule.id}>
                      <TableCell className="font-medium">{rule.name}</TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {getConditionLabel(rule.condition)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          {rule.channel_ids.slice(0, 3).map((channelId) => {
                            const ch = channels.find((c) => c.id === channelId)
                            if (!ch) return null
                            return (
                              <TooltipProvider key={channelId}>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <div className="p-1 rounded bg-muted">
                                      {getChannelIcon(ch.type)}
                                    </div>
                                  </TooltipTrigger>
                                  <TooltipContent>{ch.name}</TooltipContent>
                                </Tooltip>
                              </TooltipProvider>
                            )
                          })}
                          {rule.channel_ids.length > 3 && (
                            <Badge variant="secondary" className="text-xs">
                              +{rule.channel_ids.length - 3}
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Switch
                          checked={rule.is_active}
                          onCheckedChange={() => handleToggleRule(rule)}
                        />
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEditRule(rule)}
                          >
                            <Edit2 className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteRule(rule.id)}
                          >
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          )}
        </TabsContent>

        {/* Logs Tab */}
        <TabsContent value="logs" className="space-y-4">
          <div className="flex justify-between">
            <Button variant="outline" size="sm" onClick={() => refetchLogs()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              {common.refresh}
            </Button>
          </div>

          {logsLoading ? (
            <div className="text-center py-8 text-muted-foreground">
              <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2" />
              {common.loading}
            </div>
          ) : logs.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Clock className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
                <h3 className="text-lg font-medium mb-2">{notifications_t.noLogs}</h3>
                <p className="text-sm text-muted-foreground">
                  Notification delivery logs will appear here
                </p>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{common.status}</TableHead>
                    <TableHead>Event</TableHead>
                    <TableHead>Channel</TableHead>
                    <TableHead>Message</TableHead>
                    <TableHead>Time</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {logs.map((log) => {
                    const channel = channels.find((c) => c.id === log.channel_id)
                    return (
                      <TableRow key={log.id}>
                        <TableCell>{getStatusBadge(log.status)}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{log.event_type}</Badge>
                        </TableCell>
                        <TableCell>
                          {channel ? (
                            <div className="flex items-center gap-2">
                              {getChannelIcon(channel.type)}
                              <span className="text-sm">{channel.name}</span>
                            </div>
                          ) : (
                            <span className="text-muted-foreground text-sm">Unknown</span>
                          )}
                        </TableCell>
                        <TableCell className="max-w-xs truncate text-muted-foreground">
                          {log.message_preview}
                        </TableCell>
                        <TableCell className="text-muted-foreground text-sm">
                          {formatDate(log.created_at)}
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Dialogs */}
      <ChannelDialog
        open={channelDialogOpen}
        onOpenChange={setChannelDialogOpen}
        channel={editingChannel}
        onSave={refetchChannels}
      />

      <RuleDialog
        open={ruleDialogOpen}
        onOpenChange={setRuleDialogOpen}
        rule={editingRule}
        channels={channels}
        onSave={refetchRules}
      />

      <ConfirmDialog />
    </div>
  )
}
