/**
 * Escalation Tab Component
 * Displays and manages escalation policies and incidents with real-time updates
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
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
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
import { ScrollArea } from '@/components/ui/scroll-area'
import { useToast } from '@/hooks/use-toast'
import { useWebSocket, type WebSocketMessage, type IncidentEventData, type WebSocketStatus } from '@/hooks/useWebSocket'
import { WebSocketStatusIndicator } from './WebSocketStatus'
import { EscalationLevelBuilder } from './EscalationLevelBuilder'
import { str } from '@/lib/intlayer-utils'
import {
  Plus,
  Edit,
  Trash2,
  Loader2,
  AlertTriangle,
  CheckCircle,
  Clock,
  ArrowUp,
  Settings,
} from 'lucide-react'
import { SchedulerControlPanel } from './SchedulerControlPanel'
import { useBulkSelection, BulkActionBar, SelectionCheckbox, type BulkActionItem } from './BulkActionBar'
import type {
  EscalationPolicy,
  EscalationIncident,
  EscalationStats,
  EscalationState,
  EscalationLevel,
} from '@/api/client'

// Adapter type that extends EscalationIncident with BulkActionItem compatibility
type IncidentWithName = EscalationIncident & BulkActionItem
import {
  listEscalationPolicies,
  createEscalationPolicy,
  updateEscalationPolicy,
  deleteEscalationPolicy,
  listEscalationIncidents,
  acknowledgeEscalationIncident,
  resolveEscalationIncident,
  getEscalationStats,
  getEscalationIncident,
} from '@/api/client'

interface EscalationTabProps {
  className?: string
}

const STATE_COLORS: Record<EscalationState, string> = {
  pending: 'bg-yellow-500',
  triggered: 'bg-red-500',
  acknowledged: 'bg-blue-500',
  escalated: 'bg-orange-500',
  resolved: 'bg-green-500',
}

const STATE_ICONS: Record<EscalationState, React.ReactNode> = {
  pending: <Clock className="h-4 w-4" />,
  triggered: <AlertTriangle className="h-4 w-4" />,
  acknowledged: <CheckCircle className="h-4 w-4" />,
  escalated: <ArrowUp className="h-4 w-4" />,
  resolved: <CheckCircle className="h-4 w-4" />,
}

export function EscalationTab({ className }: EscalationTabProps) {
  const rawContent = useIntlayer('notificationsAdvanced')
  const rawCommon = useIntlayer('common')
  const { toast } = useToast()

  // Type-safe content access using any to bypass Intlayer union complexity
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const content = rawContent as any
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const common = rawCommon as any

  const [activeTab, setActiveTab] = useState('policies')
  const [policies, setPolicies] = useState<EscalationPolicy[]>([])
  const [incidents, setIncidents] = useState<EscalationIncident[]>([])
  const [stats, setStats] = useState<EscalationStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingPolicy, setEditingPolicy] = useState<EscalationPolicy | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [policyToDelete, setPolicyToDelete] = useState<EscalationPolicy | null>(null)
  const [schedulerExpanded, setSchedulerExpanded] = useState(false)

  // Map incidents to BulkActionItem compatible format
  const incidentsWithName: IncidentWithName[] = incidents.map((inc) => ({
    ...inc,
    name: inc.incident_ref, // Use incident_ref as the name for BulkActionItem compatibility
  }))

  // Bulk selection for incidents
  const incidentSelection = useBulkSelection(incidentsWithName)

  // Handle WebSocket messages for real-time updates
  const handleWebSocketMessage = useCallback(
    async (message: WebSocketMessage) => {
      const { type } = message
      const data = message.data as unknown as IncidentEventData

      switch (type) {
        case 'incident_created': {
          // Fetch the full incident and add it to the list
          try {
            const newIncident = await getEscalationIncident(data.incident_id)
            setIncidents((prev) => [newIncident, ...prev])
            setStats((prev) =>
              prev
                ? {
                    ...prev,
                    total_incidents: prev.total_incidents + 1,
                    active_count: prev.active_count + 1,
                  }
                : prev
            )
            toast({
              title: 'New Incident',
              description: `Incident ${data.incident_ref} created`,
            })
          } catch {
            // Silently ignore if fetch fails
          }
          break
        }

        case 'incident_state_changed':
        case 'incident_acknowledged':
        case 'incident_escalated': {
          // Update the incident in the list
          setIncidents((prev) =>
            prev.map((inc) =>
              inc.id === data.incident_id
                ? {
                    ...inc,
                    state: (data.to_state as EscalationState) || inc.state,
                    current_level: data.current_level ?? inc.current_level,
                    acknowledged_by: type === 'incident_acknowledged' ? data.actor ?? null : inc.acknowledged_by,
                    acknowledged_at: type === 'incident_acknowledged' ? new Date().toISOString() : inc.acknowledged_at,
                    updated_at: new Date().toISOString(),
                  }
                : inc
            )
          )

          // Show toast for state changes
          const actionLabel =
            type === 'incident_acknowledged'
              ? 'acknowledged'
              : type === 'incident_escalated'
                ? 'escalated'
                : 'updated'
          toast({
            title: `Incident ${actionLabel}`,
            description: `${data.incident_ref}: ${data.from_state} -> ${data.to_state}`,
          })
          break
        }

        case 'incident_resolved': {
          // Update the incident to resolved state
          setIncidents((prev) =>
            prev.map((inc) =>
              inc.id === data.incident_id
                ? {
                    ...inc,
                    state: 'resolved' as EscalationState,
                    resolved_by: data.resolved_by ?? data.actor ?? null,
                    resolved_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                  }
                : inc
            )
          )
          setStats((prev) =>
            prev
              ? {
                  ...prev,
                  active_count: Math.max(0, prev.active_count - 1),
                }
              : prev
          )
          toast({
            title: 'Incident Resolved',
            description: `Incident ${data.incident_ref} resolved`,
            variant: 'default',
          })
          break
        }
      }
    },
    [toast]
  )

  // Form state
  const [formName, setFormName] = useState('')
  const [formDescription, setFormDescription] = useState('')
  const [formAutoResolve, setFormAutoResolve] = useState(true)
  const [formMaxEscalations, setFormMaxEscalations] = useState(3)
  const [formIsActive, setFormIsActive] = useState(true)
  const [formLevels, setFormLevels] = useState<EscalationLevel[]>([])
  const [formSaving, setFormSaving] = useState(false)

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [policiesRes, incidentsRes, statsRes] = await Promise.all([
        listEscalationPolicies(),
        listEscalationIncidents(),
        getEscalationStats(),
      ])
      setPolicies(policiesRes.items || [])
      setIncidents(incidentsRes.items || [])
      setStats(statsRes)
    } catch {
      toast({
        title: str(content.errors.loadFailed),
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }, [toast, content.errors.loadFailed])

  // WebSocket connection for real-time updates
  const handleStatusChange = useCallback((status: WebSocketStatus) => {
    if (status === 'connected') {
      // Refresh data when reconnected
      loadData()
    }
  }, [loadData])

  const { status: wsStatus, reconnectAttempts, connect: wsConnect } = useWebSocket({
    onMessage: handleWebSocketMessage,
    onStatusChange: handleStatusChange,
  })

  useEffect(() => {
    loadData()
  }, [loadData])

  const openCreateDialog = () => {
    setEditingPolicy(null)
    setFormName('')
    setFormDescription('')
    setFormAutoResolve(true)
    setFormMaxEscalations(3)
    setFormIsActive(true)
    // Initialize with one default level
    setFormLevels([
      {
        level: 1,
        delay_minutes: 0,
        targets: [],
      },
    ])
    setIsDialogOpen(true)
  }

  const openEditDialog = (policy: EscalationPolicy) => {
    setEditingPolicy(policy)
    setFormName(policy.name)
    setFormDescription(policy.description)
    setFormAutoResolve(policy.auto_resolve_on_success)
    setFormMaxEscalations(policy.max_escalations)
    setFormIsActive(policy.is_active)
    setFormLevels(policy.levels || [])
    setIsDialogOpen(true)
  }

  const handleSave = async () => {
    // Validate levels have at least one target with identifier
    const hasValidLevels = formLevels.length > 0 && formLevels.every(
      (l) => l.targets.length > 0 && l.targets.every((t) => t.identifier.trim())
    )

    if (!hasValidLevels) {
      toast({
        title: str(content.errors.createFailed),
        description: str(content.escalation.levelBuilder?.validationWarning || 'Each level must have at least one target with a valid identifier'),
        variant: 'destructive',
      })
      return
    }

    setFormSaving(true)
    try {
      const data = {
        name: formName,
        description: formDescription,
        auto_resolve_on_success: formAutoResolve,
        max_escalations: formMaxEscalations,
        is_active: formIsActive,
        levels: formLevels,
      }

      if (editingPolicy) {
        await updateEscalationPolicy(editingPolicy.id, data)
        toast({ title: str(content.success.configUpdated) })
      } else {
        await createEscalationPolicy(data)
        toast({ title: str(content.success.configCreated) })
      }

      setIsDialogOpen(false)
      loadData()
    } catch (e) {
      toast({
        title: editingPolicy
          ? str(content.errors.updateFailed)
          : str(content.errors.createFailed),
        description: e instanceof Error ? e.message : undefined,
        variant: 'destructive',
      })
    } finally {
      setFormSaving(false)
    }
  }

  const confirmDelete = (policy: EscalationPolicy) => {
    setPolicyToDelete(policy)
    setDeleteDialogOpen(true)
  }

  const handleDelete = async () => {
    if (!policyToDelete) return

    try {
      await deleteEscalationPolicy(policyToDelete.id)
      toast({ title: str(content.success.configDeleted) })
      setDeleteDialogOpen(false)
      setPolicyToDelete(null)
      loadData()
    } catch {
      toast({
        title: str(content.errors.deleteFailed),
        variant: 'destructive',
      })
    }
  }

  const toggleActive = async (policy: EscalationPolicy) => {
    try {
      await updateEscalationPolicy(policy.id, { is_active: !policy.is_active })
      setPolicies((prev) =>
        prev.map((p) => (p.id === policy.id ? { ...p, is_active: !p.is_active } : p))
      )
    } catch {
      toast({
        title: str(content.errors.updateFailed),
        variant: 'destructive',
      })
    }
  }

  const handleAcknowledge = async (incident: EscalationIncident) => {
    try {
      await acknowledgeEscalationIncident(incident.id, {
        actor: 'current-user@example.com',
        message: 'Acknowledged via dashboard',
      })
      toast({ title: str(content.success.incidentAcknowledged) })
      loadData()
    } catch {
      toast({
        title: str(content.errors.acknowledgeFailed),
        variant: 'destructive',
      })
    }
  }

  const handleResolve = async (incident: EscalationIncident) => {
    try {
      await resolveEscalationIncident(incident.id, {
        actor: 'current-user@example.com',
        message: 'Resolved via dashboard',
      })
      toast({ title: str(content.success.incidentResolved) })
      loadData()
    } catch {
      toast({
        title: str(content.errors.resolveFailed),
        variant: 'destructive',
      })
    }
  }

  const getPolicyName = (policyId: string) => {
    const policy = policies.find((p) => p.id === policyId)
    return policy?.name || policyId.slice(0, 8)
  }

  const getStateLabel = (state: EscalationState): string => {
    const labels: Record<EscalationState, string> = {
      pending: 'Pending',
      triggered: 'Triggered',
      acknowledged: 'Acknowledged',
      escalated: 'Escalated',
      resolved: 'Resolved',
    }
    return labels[state] || state
  }

  if (loading) {
    return (
      <div className={`flex items-center justify-center py-12 ${className}`}>
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  // Bulk actions for incidents
  const handleBulkAcknowledge = async (items: IncidentWithName[]) => {
    const toAck = items.filter((i) => i.state === 'triggered')
    for (const incident of toAck) {
      await acknowledgeEscalationIncident(incident.id, {
        actor: 'current-user@example.com',
        message: 'Bulk acknowledged via dashboard',
      })
    }
    loadData()
  }

  const handleBulkResolve = async (items: IncidentWithName[]) => {
    const toResolve = items.filter((i) => i.state !== 'resolved')
    for (const incident of toResolve) {
      await resolveEscalationIncident(incident.id, {
        actor: 'current-user@example.com',
        message: 'Bulk resolved via dashboard',
      })
    }
    loadData()
  }

  return (
    <div className={className}>
      {/* Stats Cards and Scheduler Control */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
        {/* Scheduler Control Panel */}
        <div className="md:col-span-1">
          <SchedulerControlPanel compact={!schedulerExpanded} />
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSchedulerExpanded(!schedulerExpanded)}
            className="w-full mt-1 text-xs"
          >
            <Settings className="h-3 w-3 mr-1" />
            {schedulerExpanded ? 'Collapse' : 'Expand'} Scheduler
          </Button>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="md:col-span-4 grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {content.escalation.stats.totalIncidents}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_incidents}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {content.escalation.stats.activeCount}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-500">{stats.active_count}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Policies
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_policies}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {content.escalation.stats.avgResolutionTime}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats.avg_resolution_time_minutes ? `${stats.avg_resolution_time_minutes}m` : '-'}
              </div>
            </CardContent>
          </Card>
          </div>
        )}
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <TabsList>
              <TabsTrigger value="policies">{content.escalation.title}</TabsTrigger>
              <TabsTrigger value="incidents">
                {content.incidents.title}
                {stats && stats.active_count > 0 && (
                  <Badge variant="destructive" className="ml-2">
                    {stats.active_count}
                  </Badge>
                )}
              </TabsTrigger>
            </TabsList>
            {/* WebSocket connection status indicator */}
            <WebSocketStatusIndicator
              status={wsStatus}
              reconnectAttempts={reconnectAttempts}
              onReconnect={wsConnect}
              compact
            />
          </div>
          {activeTab === 'policies' && (
            <Button onClick={openCreateDialog}>
              <Plus className="h-4 w-4 mr-2" />
              {content.escalation.addPolicy}
            </Button>
          )}
        </div>

        <TabsContent value="policies">
          {policies.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <AlertTriangle className="h-12 w-12 mx-auto mb-4 opacity-50" />
              {content.escalation.noPolicies}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{content.common.name}</TableHead>
                  <TableHead>{content.common.description}</TableHead>
                  <TableHead>{content.escalation.levels}</TableHead>
                  <TableHead>{content.escalation.maxEscalations}</TableHead>
                  <TableHead>{content.escalation.autoResolve}</TableHead>
                  <TableHead className="w-[80px]">{content.common.active}</TableHead>
                  <TableHead className="w-[100px]" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {policies.map((policy) => (
                  <TableRow key={policy.id}>
                    <TableCell className="font-medium">{policy.name}</TableCell>
                    <TableCell className="text-muted-foreground max-w-[200px] truncate">
                      {policy.description || '-'}
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{policy.levels.length} levels</Badge>
                    </TableCell>
                    <TableCell>{policy.max_escalations}</TableCell>
                    <TableCell>
                      {policy.auto_resolve_on_success ? (
                        <Badge variant="outline">Yes</Badge>
                      ) : (
                        <Badge variant="secondary">No</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <Switch
                        checked={policy.is_active}
                        onCheckedChange={() => toggleActive(policy)}
                      />
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => openEditDialog(policy)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => confirmDelete(policy)}
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
        </TabsContent>

        <TabsContent value="incidents">
          {incidents.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <CheckCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
              {content.incidents.noIncidents}
            </div>
          ) : (
            <div className="space-y-2">
              {/* Bulk Action Bar for Incidents */}
              <BulkActionBar
                selectedItems={incidentSelection.selectedItems}
                selectedCount={incidentSelection.selectedCount}
                totalCount={incidents.length}
                isAllSelected={incidentSelection.isAllSelected}
                isSomeSelected={incidentSelection.isSomeSelected}
                onToggleAll={incidentSelection.toggleAll}
                onClearSelection={incidentSelection.clearSelection}
                callbacks={{
                  onEnable: handleBulkAcknowledge, // "Enable" = Acknowledge
                  onDisable: handleBulkResolve,   // "Disable" = Resolve
                }}
              />

              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[40px]" />
                    <TableHead>{content.incidents.incidentRef}</TableHead>
                    <TableHead>Policy</TableHead>
                    <TableHead>State</TableHead>
                    <TableHead>{content.incidents.currentLevel}</TableHead>
                    <TableHead>{content.incidents.escalationCount}</TableHead>
                    <TableHead>{content.common.created}</TableHead>
                    <TableHead className="w-[150px]" />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {incidents.map((incident) => (
                    <TableRow key={incident.id} className={incidentSelection.isSelected(incident.id) ? 'bg-primary/5' : ''}>
                      <TableCell className="w-[40px]">
                        <SelectionCheckbox
                          checked={incidentSelection.isSelected(incident.id)}
                          onCheckedChange={() => incidentSelection.toggleItem(incident.id)}
                        />
                      </TableCell>
                      <TableCell className="font-mono text-sm">{incident.incident_ref}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{getPolicyName(incident.policy_id)}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={STATE_COLORS[incident.state]}>
                        <span className="flex items-center gap-1">
                          {STATE_ICONS[incident.state]}
                          {getStateLabel(incident.state)}
                        </span>
                      </Badge>
                    </TableCell>
                    <TableCell>{incident.current_level}</TableCell>
                    <TableCell>{incident.escalation_count}</TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {new Date(incident.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        {incident.state === 'triggered' && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleAcknowledge(incident)}
                          >
                            {content.incidents.actions.acknowledge}
                          </Button>
                        )}
                        {incident.state !== 'resolved' && (
                          <Button
                            variant="default"
                            size="sm"
                            onClick={() => handleResolve(incident)}
                          >
                            {content.incidents.actions.resolve}
                          </Button>
                        )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Create/Edit Policy Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh]">
          <DialogHeader>
            <DialogTitle>
              {editingPolicy ? content.escalation.editPolicy : content.escalation.addPolicy}
            </DialogTitle>
            <DialogDescription>
              {content.escalation.subtitle}
            </DialogDescription>
          </DialogHeader>

          <ScrollArea className="max-h-[calc(90vh-180px)] pr-4">
            <div className="space-y-6 py-4">
              {/* Basic Settings */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>{content.common.name}</Label>
                  <Input
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    placeholder="Policy name"
                  />
                </div>

                <div className="space-y-2">
                  <Label>{content.escalation.maxEscalations}</Label>
                  <Input
                    type="number"
                    value={formMaxEscalations}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormMaxEscalations(parseInt(e.target.value) || 1)}
                    min={1}
                    max={10}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>{content.common.description}</Label>
                <Textarea
                  value={formDescription}
                  onChange={(e) => setFormDescription(e.target.value)}
                  placeholder="Policy description"
                  rows={2}
                />
              </div>

              <div className="flex items-center gap-6">
                <div className="flex items-center gap-2">
                  <Switch checked={formAutoResolve} onCheckedChange={setFormAutoResolve} />
                  <Label className="text-sm">{content.escalation.autoResolve}</Label>
                </div>
                <div className="flex items-center gap-2">
                  <Switch checked={formIsActive} onCheckedChange={setFormIsActive} />
                  <Label className="text-sm">{content.common.active}</Label>
                </div>
              </div>

              {/* Escalation Levels Builder */}
              <div className="border-t pt-4">
                <EscalationLevelBuilder
                  levels={formLevels}
                  onChange={setFormLevels}
                  maxLevels={formMaxEscalations}
                />
              </div>
            </div>
          </ScrollArea>

          <DialogFooter className="border-t pt-4">
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
              {common.cancel}
            </Button>
            <Button
              onClick={handleSave}
              disabled={formSaving || !formName || formLevels.length === 0}
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
          <p>Are you sure you want to delete "{policyToDelete?.name}"?</p>
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
