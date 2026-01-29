/**
 * OpenLineageConfig component - Main configuration panel for OpenLineage webhooks.
 *
 * Displays webhook list with status indicators, add/edit dialogs,
 * and test connection functionality.
 */

import { useState, useEffect, useCallback } from 'react'
import {
  Plus,
  Settings,
  Edit2,
  Trash2,
  ExternalLink,
  Loader2,
  CheckCircle,
  XCircle,
  Webhook,
  Send,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { useToast } from '@/hooks/use-toast'
import { useIntlayer } from '@/providers'
import { str } from '@/lib/intlayer-utils'
import {
  listWebhooks,
  createWebhook,
  updateWebhook,
  deleteWebhook,
  testWebhook,
  type OpenLineageWebhook,
  type CreateWebhookRequest,
  type WebhookTestResult,
} from '@/api/client'

import { WebhookForm } from './WebhookForm'
import { WebhookStatus } from './WebhookStatus'

interface OpenLineageConfigProps {
  trigger?: React.ReactNode
}

export function OpenLineageConfig({ trigger }: OpenLineageConfigProps) {
  const { toast } = useToast()
  const t = useIntlayer('lineage')
  const tCommon = useIntlayer('common')

  const [open, setOpen] = useState(false)
  const [webhooks, setWebhooks] = useState<OpenLineageWebhook[]>([])
  const [loading, setLoading] = useState(false)
  const [formLoading, setFormLoading] = useState(false)

  // Form dialog state
  const [formOpen, setFormOpen] = useState(false)
  const [editingWebhook, setEditingWebhook] = useState<OpenLineageWebhook | null>(null)

  // Delete confirmation state
  const [deleteId, setDeleteId] = useState<string | null>(null)

  // Test state
  const [testingId, setTestingId] = useState<string | null>(null)
  const [testResult, setTestResult] = useState<WebhookTestResult | null>(null)

  const fetchWebhooks = useCallback(async () => {
    setLoading(true)
    try {
      const response = await listWebhooks()
      setWebhooks(response.data)
    } catch (error) {
      toast({
        title: str(t.errorLoadingWebhooks),
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }, [toast, t])

  useEffect(() => {
    if (open) {
      fetchWebhooks()
    }
  }, [open, fetchWebhooks])

  const handleCreate = async (data: CreateWebhookRequest) => {
    setFormLoading(true)
    try {
      await createWebhook(data)
      toast({ title: str(t.webhookCreated) })
      setFormOpen(false)
      fetchWebhooks()
    } catch (error) {
      toast({
        title: str(t.errorCreatingWebhook),
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      })
    } finally {
      setFormLoading(false)
    }
  }

  const handleUpdate = async (data: CreateWebhookRequest) => {
    if (!editingWebhook) return
    setFormLoading(true)
    try {
      await updateWebhook(editingWebhook.id, data)
      toast({ title: str(t.webhookUpdated) })
      setFormOpen(false)
      setEditingWebhook(null)
      fetchWebhooks()
    } catch (error) {
      toast({
        title: str(t.errorUpdatingWebhook),
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      })
    } finally {
      setFormLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!deleteId) return
    try {
      await deleteWebhook(deleteId)
      toast({ title: str(t.webhookDeleted) })
      fetchWebhooks()
    } catch (error) {
      toast({
        title: str(t.errorDeletingWebhook),
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      })
    } finally {
      setDeleteId(null)
    }
  }

  const handleTest = async (webhook: OpenLineageWebhook) => {
    setTestingId(webhook.id)
    setTestResult(null)
    try {
      const result = await testWebhook({
        url: webhook.url,
        headers: webhook.headers,
        timeout_seconds: webhook.timeout_seconds,
      })
      setTestResult(result)
      if (result.success) {
        toast({
          title: str(t.webhookTestSuccess),
          description: `${result.response_time_ms}ms`,
        })
      } else {
        toast({
          title: str(t.webhookTestFailed),
          description: result.error_message || 'Unknown error',
          variant: 'destructive',
        })
      }
    } catch (error) {
      toast({
        title: str(t.errorTestingWebhook),
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      })
    } finally {
      setTestingId(null)
    }
  }

  const openEditForm = (webhook: OpenLineageWebhook) => {
    setEditingWebhook(webhook)
    setFormOpen(true)
  }

  const openCreateForm = () => {
    setEditingWebhook(null)
    setFormOpen(true)
  }

  return (
    <>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          {trigger || (
            <Button variant="outline" size="sm">
              <Settings className="mr-2 h-4 w-4" />
              {str(t.openLineageSettings)}
            </Button>
          )}
        </DialogTrigger>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Webhook className="h-5 w-5" />
              {str(t.webhookConfig)}
            </DialogTitle>
            <DialogDescription>{str(t.webhookConfigDesc)}</DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {/* Add Webhook Button */}
            <div className="flex justify-end">
              <Button onClick={openCreateForm}>
                <Plus className="mr-2 h-4 w-4" />
                {str(t.addWebhook)}
              </Button>
            </div>

            {/* Loading State */}
            {loading && (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            )}

            {/* Empty State */}
            {!loading && webhooks.length === 0 && (
              <Card className="border-dashed">
                <CardContent className="flex flex-col items-center justify-center py-8">
                  <Webhook className="h-12 w-12 text-muted-foreground/50 mb-4" />
                  <h3 className="text-lg font-medium">{str(t.noWebhooks)}</h3>
                  <p className="text-sm text-muted-foreground text-center max-w-sm mt-1">
                    {str(t.noWebhooksDesc)}
                  </p>
                  <Button className="mt-4" onClick={openCreateForm}>
                    <Plus className="mr-2 h-4 w-4" />
                    {str(t.addWebhook)}
                  </Button>
                </CardContent>
              </Card>
            )}

            {/* Webhook List */}
            {!loading && webhooks.length > 0 && (
              <div className="space-y-4">
                {webhooks.map((webhook) => (
                  <Card key={webhook.id}>
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="space-y-1">
                          <CardTitle className="text-base flex items-center gap-2">
                            {webhook.name}
                            <Badge
                              variant="outline"
                              className={
                                webhook.is_active
                                  ? 'border-green-500/50 text-green-600'
                                  : 'border-muted'
                              }
                            >
                              {webhook.is_active ? str(t.activeWebhook) : str(t.inactiveWebhook)}
                            </Badge>
                          </CardTitle>
                          <CardDescription className="flex items-center gap-1">
                            <ExternalLink className="h-3 w-3" />
                            <span className="truncate max-w-[400px]">{webhook.url}</span>
                          </CardDescription>
                        </div>
                        <div className="flex items-center gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleTest(webhook)}
                            disabled={testingId === webhook.id}
                          >
                            {testingId === webhook.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Send className="h-4 w-4" />
                            )}
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => openEditForm(webhook)}
                          >
                            <Edit2 className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setDeleteId(webhook.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <Separator className="mb-4" />
                      <WebhookStatus webhook={webhook} />

                      {/* Test Result */}
                      {testResult && testingId === null && webhooks[0]?.id === webhook.id && (
                        <div
                          className={`mt-4 p-3 rounded-lg ${
                            testResult.success
                              ? 'bg-green-500/10 border border-green-500/20'
                              : 'bg-destructive/10 border border-destructive/20'
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            {testResult.success ? (
                              <CheckCircle className="h-4 w-4 text-green-600" />
                            ) : (
                              <XCircle className="h-4 w-4 text-destructive" />
                            )}
                            <span className="text-sm font-medium">
                              {testResult.success ? str(t.webhookTestSuccess) : str(t.webhookTestFailed)}
                            </span>
                            {testResult.response_time_ms && (
                              <span className="text-xs text-muted-foreground">
                                {testResult.response_time_ms}ms
                              </span>
                            )}
                          </div>
                          {testResult.error_message && (
                            <p className="text-xs text-muted-foreground mt-1">
                              {testResult.error_message}
                            </p>
                          )}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Form Dialog */}
      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent className="max-w-lg max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingWebhook ? str(t.editWebhook) : str(t.addWebhook)}
            </DialogTitle>
          </DialogHeader>
          <WebhookForm
            webhook={editingWebhook}
            onSubmit={editingWebhook ? handleUpdate : handleCreate}
            onCancel={() => {
              setFormOpen(false)
              setEditingWebhook(null)
            }}
            loading={formLoading}
          />
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{str(tCommon.delete)}</AlertDialogTitle>
            <AlertDialogDescription>{str(t.confirmDeleteWebhook)}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{str(tCommon.cancel)}</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete}>{str(tCommon.delete)}</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}

export default OpenLineageConfig
