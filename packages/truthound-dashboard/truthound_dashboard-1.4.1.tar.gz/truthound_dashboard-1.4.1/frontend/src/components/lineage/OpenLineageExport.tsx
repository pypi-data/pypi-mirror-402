/**
 * OpenLineage Export component.
 *
 * Provides UI for exporting lineage data as OpenLineage events,
 * either downloading as JSON/NDJSON or emitting to an external endpoint.
 */

import { useState } from 'react'
import {
  Download,
  Send,
  FileJson,
  FileText,
  ExternalLink,
  Copy,
  Check,
  AlertCircle,
  Info,
  Settings,
  Loader2,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useToast } from '@/hooks/use-toast'
import {
  exportOpenLineage,
  exportOpenLineageGranular,
  emitOpenLineage,
  downloadOpenLineageJson,
  downloadOpenLineageNdjson,
  type OpenLineageExportResponse,
  type OpenLineageExportRequest,
  type OpenLineageEmitRequest,
} from '@/api/client'

interface OpenLineageExportProps {
  sourceId?: string
  disabled?: boolean
}

export function OpenLineageExport({ sourceId, disabled }: OpenLineageExportProps) {
  const { toast } = useToast()
  const [open, setOpen] = useState(false)
  const [activeTab, setActiveTab] = useState<'download' | 'emit'>('download')
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)

  // Export options
  const [jobNamespace, setJobNamespace] = useState('truthound-dashboard')
  const [jobName, setJobName] = useState('lineage_export')
  const [includeSchema, setIncludeSchema] = useState(true)
  const [granular, setGranular] = useState(false)
  const [format, setFormat] = useState<'json' | 'ndjson'>('json')

  // Emit options
  const [webhookUrl, setWebhookUrl] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [batchSize, setBatchSize] = useState(100)

  // Preview state
  const [previewData, setPreviewData] = useState<OpenLineageExportResponse | null>(null)

  const handlePreview = async () => {
    setLoading(true)
    try {
      const request: OpenLineageExportRequest = {
        job_namespace: jobNamespace,
        job_name: jobName,
        source_id: sourceId,
        include_schema: includeSchema,
      }

      const result = granular
        ? await exportOpenLineageGranular(request)
        : await exportOpenLineage(request)

      setPreviewData(result)
      toast({
        title: 'Preview Generated',
        description: `${result.total_events} events ready for export`,
      })
    } catch (error) {
      toast({
        title: 'Preview Failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async () => {
    if (!previewData) {
      await handlePreview()
      return
    }

    try {
      const filename = `openlineage-${jobName}-${new Date().toISOString().slice(0, 10)}`
      if (format === 'json') {
        downloadOpenLineageJson(previewData.events, `${filename}.json`)
      } else {
        downloadOpenLineageNdjson(previewData.events, `${filename}.ndjson`)
      }

      toast({
        title: 'Download Complete',
        description: `Exported ${previewData.total_events} events as ${format.toUpperCase()}`,
      })
    } catch (error) {
      toast({
        title: 'Download Failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      })
    }
  }

  const handleEmit = async () => {
    if (!webhookUrl) {
      toast({
        title: 'Webhook URL Required',
        description: 'Please enter a valid webhook URL',
        variant: 'destructive',
      })
      return
    }

    setLoading(true)
    try {
      const request: OpenLineageEmitRequest = {
        webhook: {
          url: webhookUrl,
          api_key: apiKey || undefined,
          batch_size: batchSize,
          timeout_seconds: 30,
        },
        source_id: sourceId,
        job_namespace: jobNamespace,
        job_name: jobName,
      }

      const result = await emitOpenLineage(request)

      if (result.success) {
        toast({
          title: 'Emission Complete',
          description: `Successfully sent ${result.events_sent} events`,
        })
        setOpen(false)
      } else {
        toast({
          title: 'Emission Failed',
          description: result.error_message || 'Unknown error',
          variant: 'destructive',
        })
      }
    } catch (error) {
      toast({
        title: 'Emission Failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleCopyJson = () => {
    if (!previewData) return
    navigator.clipboard.writeText(JSON.stringify(previewData.events, null, 2))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
    toast({
      title: 'Copied',
      description: 'OpenLineage JSON copied to clipboard',
    })
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" disabled={disabled}>
          <ExternalLink className="mr-2 h-4 w-4" />
          Export OpenLineage
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileJson className="h-5 w-5" />
            Export as OpenLineage
          </DialogTitle>
          <DialogDescription>
            Export your lineage data in OpenLineage format for interoperability with tools like
            Marquez, DataHub, and Atlan.
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'download' | 'emit')}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="download">
              <Download className="mr-2 h-4 w-4" />
              Download
            </TabsTrigger>
            <TabsTrigger value="emit">
              <Send className="mr-2 h-4 w-4" />
              Emit to Endpoint
            </TabsTrigger>
          </TabsList>

          {/* Common Settings */}
          <div className="mt-4 space-y-4 border-b pb-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Settings className="h-4 w-4" />
              Export Settings
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="job-namespace">Job Namespace</Label>
                <Input
                  id="job-namespace"
                  value={jobNamespace}
                  onChange={(e) => setJobNamespace(e.target.value)}
                  placeholder="truthound-dashboard"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="job-name">Job Name</Label>
                <Input
                  id="job-name"
                  value={jobName}
                  onChange={(e) => setJobName(e.target.value)}
                  placeholder="lineage_export"
                />
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <Label>Include Schema</Label>
                <p className="text-xs text-muted-foreground">
                  Include column schema in dataset facets
                </p>
              </div>
              <Switch checked={includeSchema} onCheckedChange={setIncludeSchema} />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <Label>Granular Export</Label>
                <p className="text-xs text-muted-foreground">
                  Create separate events for each transformation
                </p>
              </div>
              <Switch checked={granular} onCheckedChange={setGranular} />
            </div>
          </div>

          {/* Download Tab */}
          <TabsContent value="download" className="space-y-4">
            <div className="space-y-2">
              <Label>Export Format</Label>
              <Select value={format} onValueChange={(v) => setFormat(v as 'json' | 'ndjson')}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="json">
                    <div className="flex items-center gap-2">
                      <FileJson className="h-4 w-4" />
                      JSON (Pretty-printed)
                    </div>
                  </SelectItem>
                  <SelectItem value="ndjson">
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4" />
                      NDJSON (Newline-delimited)
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Preview */}
            {previewData && (
              <div className="rounded-lg border bg-muted/50 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Preview</span>
                  <Button variant="ghost" size="sm" onClick={handleCopyJson}>
                    {copied ? (
                      <Check className="mr-2 h-4 w-4" />
                    ) : (
                      <Copy className="mr-2 h-4 w-4" />
                    )}
                    {copied ? 'Copied' : 'Copy'}
                  </Button>
                </div>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Events:</span>
                    <span className="ml-2 font-mono">{previewData.total_events}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Datasets:</span>
                    <span className="ml-2 font-mono">{previewData.total_datasets}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Jobs:</span>
                    <span className="ml-2 font-mono">{previewData.total_jobs}</span>
                  </div>
                </div>
                <pre className="max-h-48 overflow-auto rounded bg-background p-2 text-xs">
                  {JSON.stringify(previewData.events[0], null, 2)}
                </pre>
              </div>
            )}

            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Info className="h-4 w-4" />
              <span>
                OpenLineage events follow the{' '}
                <a
                  href="https://openlineage.io/spec/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                >
                  OpenLineage spec v1.0.5
                </a>
              </span>
            </div>
          </TabsContent>

          {/* Emit Tab */}
          <TabsContent value="emit" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="webhook-url">
                Webhook URL <span className="text-destructive">*</span>
              </Label>
              <Input
                id="webhook-url"
                value={webhookUrl}
                onChange={(e) => setWebhookUrl(e.target.value)}
                placeholder="https://api.example.com/v1/lineage"
              />
              <p className="text-xs text-muted-foreground">
                Marquez: http://localhost:5000/api/v1/lineage
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="api-key">API Key (Optional)</Label>
              <Input
                id="api-key"
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Bearer token for authentication"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="batch-size">Batch Size</Label>
              <Input
                id="batch-size"
                type="number"
                min={1}
                max={1000}
                value={batchSize}
                onChange={(e) => setBatchSize(parseInt(e.target.value, 10))}
              />
              <p className="text-xs text-muted-foreground">Number of events per HTTP request</p>
            </div>

            <div className="rounded-lg border border-amber-500/20 bg-amber-500/10 p-3">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-4 w-4 text-amber-500 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium text-amber-500">External Endpoint</p>
                  <p className="text-muted-foreground">
                    Events will be sent to an external system. Ensure the endpoint is reachable and
                    accepts OpenLineage events.
                  </p>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          {activeTab === 'download' ? (
            <>
              <Button variant="secondary" onClick={handlePreview} disabled={loading}>
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Preview
              </Button>
              <Button onClick={handleDownload} disabled={loading}>
                <Download className="mr-2 h-4 w-4" />
                Download {format.toUpperCase()}
              </Button>
            </>
          ) : (
            <Button onClick={handleEmit} disabled={loading || !webhookUrl}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              <Send className="mr-2 h-4 w-4" />
              Emit Events
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default OpenLineageExport
