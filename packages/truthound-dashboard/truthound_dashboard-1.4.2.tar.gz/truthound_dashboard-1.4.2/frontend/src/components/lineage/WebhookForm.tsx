/**
 * WebhookForm component - Form for creating/editing OpenLineage webhooks.
 *
 * Provides fields for URL, headers, event types, batch size, timeout, etc.
 */

import { useState, useEffect } from 'react'
import { Plus, Trash2, Loader2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useIntlayer } from '@/providers'
import { str } from '@/lib/intlayer-utils'
import type { OpenLineageWebhook, WebhookEventType, CreateWebhookRequest } from '@/api/client'

interface HeaderEntry {
  key: string
  value: string
}

export interface WebhookFormData {
  name: string
  url: string
  is_active: boolean
  headers: Record<string, string>
  api_key: string
  event_types: WebhookEventType
  batch_size: number
  timeout_seconds: number
}

interface WebhookFormProps {
  webhook?: OpenLineageWebhook | null
  onSubmit: (data: CreateWebhookRequest) => Promise<void>
  onCancel: () => void
  loading?: boolean
}

export function WebhookForm({ webhook, onSubmit, onCancel, loading = false }: WebhookFormProps) {
  const t = useIntlayer('lineage')
  const tCommon = useIntlayer('common')

  const [formData, setFormData] = useState<WebhookFormData>({
    name: '',
    url: '',
    is_active: true,
    headers: {},
    api_key: '',
    event_types: 'all',
    batch_size: 100,
    timeout_seconds: 30,
  })

  const [headers, setHeaders] = useState<HeaderEntry[]>([])

  // Initialize form with webhook data when editing
  useEffect(() => {
    if (webhook) {
      setFormData({
        name: webhook.name,
        url: webhook.url,
        is_active: webhook.is_active,
        headers: webhook.headers || {},
        api_key: '', // Don't pre-fill API key for security
        event_types: webhook.event_types as WebhookEventType,
        batch_size: webhook.batch_size,
        timeout_seconds: webhook.timeout_seconds,
      })
      // Convert headers object to array
      setHeaders(
        Object.entries(webhook.headers || {}).map(([key, value]) => ({ key, value }))
      )
    }
  }, [webhook])

  const handleAddHeader = () => {
    setHeaders([...headers, { key: '', value: '' }])
  }

  const handleRemoveHeader = (index: number) => {
    setHeaders(headers.filter((_, i) => i !== index))
  }

  const handleHeaderChange = (index: number, field: 'key' | 'value', value: string) => {
    const newHeaders = [...headers]
    newHeaders[index][field] = value
    setHeaders(newHeaders)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // Convert headers array to object
    const headersObj: Record<string, string> = {}
    headers.forEach(({ key, value }) => {
      if (key.trim()) {
        headersObj[key.trim()] = value
      }
    })

    await onSubmit({
      name: formData.name,
      url: formData.url,
      is_active: formData.is_active,
      headers: headersObj,
      api_key: formData.api_key || undefined,
      event_types: formData.event_types,
      batch_size: formData.batch_size,
      timeout_seconds: formData.timeout_seconds,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Webhook Name */}
      <div className="space-y-2">
        <Label htmlFor="name">{str(t.webhookName)} *</Label>
        <Input
          id="name"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          placeholder="Marquez Production"
          required
        />
      </div>

      {/* Webhook URL */}
      <div className="space-y-2">
        <Label htmlFor="url">{str(t.webhookUrl)} *</Label>
        <Input
          id="url"
          type="url"
          value={formData.url}
          onChange={(e) => setFormData({ ...formData, url: e.target.value })}
          placeholder={str(t.webhookUrlPlaceholder)}
          required
        />
        <p className="text-xs text-muted-foreground">
          Marquez: http://localhost:5000/api/v1/lineage
        </p>
      </div>

      {/* API Key */}
      <div className="space-y-2">
        <Label htmlFor="api_key">{str(t.apiKeyOptional)}</Label>
        <Input
          id="api_key"
          type="password"
          value={formData.api_key}
          onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
          placeholder={str(t.apiKeyPlaceholder)}
        />
      </div>

      {/* Custom Headers */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label>{str(t.customHeaders)}</Label>
          <Button type="button" variant="outline" size="sm" onClick={handleAddHeader}>
            <Plus className="mr-1 h-3 w-3" />
            {str(t.addHeader)}
          </Button>
        </div>
        {headers.length > 0 && (
          <div className="space-y-2">
            {headers.map((header, index) => (
              <div key={index} className="flex items-center gap-2">
                <Input
                  placeholder={str(t.headerKey)}
                  value={header.key}
                  onChange={(e) => handleHeaderChange(index, 'key', e.target.value)}
                  className="flex-1"
                />
                <Input
                  placeholder={str(t.headerValue)}
                  value={header.value}
                  onChange={(e) => handleHeaderChange(index, 'value', e.target.value)}
                  className="flex-1"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => handleRemoveHeader(index)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Event Types */}
      <div className="space-y-2">
        <Label htmlFor="event_types">{str(t.eventTypes)}</Label>
        <Select
          value={formData.event_types}
          onValueChange={(value: WebhookEventType) =>
            setFormData({ ...formData, event_types: value })
          }
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{str(t.allEvents)}</SelectItem>
            <SelectItem value="job">{str(t.jobEventsOnly)}</SelectItem>
            <SelectItem value="dataset">{str(t.datasetEventsOnly)}</SelectItem>
          </SelectContent>
        </Select>
        <p className="text-xs text-muted-foreground">{str(t.eventTypesDesc)}</p>
      </div>

      {/* Batch Size and Timeout */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="batch_size">{str(t.batchSize)}</Label>
          <Input
            id="batch_size"
            type="number"
            min={1}
            max={1000}
            value={formData.batch_size}
            onChange={(e) => setFormData({ ...formData, batch_size: parseInt(e.target.value, 10) })}
          />
          <p className="text-xs text-muted-foreground">{str(t.batchSizeDesc)}</p>
        </div>
        <div className="space-y-2">
          <Label htmlFor="timeout_seconds">{str(t.timeout)}</Label>
          <Input
            id="timeout_seconds"
            type="number"
            min={1}
            max={300}
            value={formData.timeout_seconds}
            onChange={(e) =>
              setFormData({ ...formData, timeout_seconds: parseInt(e.target.value, 10) })
            }
          />
          <p className="text-xs text-muted-foreground">{str(t.timeoutDesc)}</p>
        </div>
      </div>

      {/* Active Toggle */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <Label htmlFor="is_active">{str(t.activeWebhook)}</Label>
          <p className="text-xs text-muted-foreground">
            {formData.is_active ? str(t.activeWebhook) : str(t.inactiveWebhook)}
          </p>
        </div>
        <Switch
          id="is_active"
          checked={formData.is_active}
          onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
        />
      </div>

      {/* Form Actions */}
      <div className="flex justify-end gap-3 pt-4 border-t">
        <Button type="button" variant="outline" onClick={onCancel} disabled={loading}>
          {str(tCommon.cancel)}
        </Button>
        <Button type="submit" disabled={loading || !formData.name || !formData.url}>
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {webhook ? str(tCommon.save) : str(t.addWebhook)}
        </Button>
      </div>
    </form>
  )
}

export default WebhookForm
