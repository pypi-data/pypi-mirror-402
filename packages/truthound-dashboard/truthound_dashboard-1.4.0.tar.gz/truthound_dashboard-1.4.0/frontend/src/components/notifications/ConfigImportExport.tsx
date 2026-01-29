/**
 * Config Import/Export Component
 *
 * A reusable component for importing and exporting notification configurations.
 * Supports JSON format with conflict resolution options.
 */

import { useState, useRef, useCallback } from 'react'
import { useIntlayer } from 'react-intlayer'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Progress } from '@/components/ui/progress'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Separator } from '@/components/ui/separator'
import { useToast } from '@/hooks/use-toast'
import { str } from '@/lib/intlayer-utils'
import {
  Download,
  Upload,
  FileJson,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Loader2,
  FileWarning,
  Settings2,
  Route,
  Filter,
  Timer,
  Bell,
} from 'lucide-react'
import type {
  NotificationConfigBundle,
  ConfigImportPreview,
  ConfigImportResult,
  ConfigImportConflict,
  ConflictResolution,
  ConfigExportOptions,
} from '@/api/client'
import {
  downloadNotificationConfigAsFile,
  parseNotificationConfigFile,
  previewNotificationConfigImport,
  importNotificationConfig,
} from '@/api/client'

export interface ConfigImportExportProps {
  className?: string
  onImportComplete?: () => void
}

type ImportStep = 'select' | 'preview' | 'importing' | 'complete'

export function ConfigImportExport({ className, onImportComplete }: ConfigImportExportProps) {
  const content = useIntlayer('notificationsAdvanced')
  const common = useIntlayer('common')
  const { toast } = useToast()

  // Export state
  const [isExporting, setIsExporting] = useState(false)
  const [exportOptions, setExportOptions] = useState<ConfigExportOptions>({
    include_routing_rules: true,
    include_deduplication: true,
    include_throttling: true,
    include_escalation: true,
  })

  // Import state
  const [isImportDialogOpen, setIsImportDialogOpen] = useState(false)
  const [importStep, setImportStep] = useState<ImportStep>('select')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [parsedBundle, setParsedBundle] = useState<NotificationConfigBundle | null>(null)
  const [importPreview, setImportPreview] = useState<ConfigImportPreview | null>(null)
  const [conflictResolution, setConflictResolution] = useState<ConflictResolution>('skip')
  const [importResult, setImportResult] = useState<ConfigImportResult | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [parseError, setParseError] = useState<string | null>(null)
  const [importProgress, setImportProgress] = useState(0)

  const fileInputRef = useRef<HTMLInputElement>(null)

  // Export handlers
  const handleExport = async () => {
    setIsExporting(true)
    try {
      const blob = await downloadNotificationConfigAsFile(exportOptions)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `truthound-notification-config-${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      toast({
        title: str(content.configExport?.exportSuccess),
        description: str(content.configExport?.exportSuccessDesc),
      })
    } catch (error) {
      toast({
        title: str(content.configExport?.exportError),
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      })
    } finally {
      setIsExporting(false)
    }
  }

  // Import handlers
  const openImportDialog = () => {
    setIsImportDialogOpen(true)
    setImportStep('select')
    setSelectedFile(null)
    setParsedBundle(null)
    setImportPreview(null)
    setImportResult(null)
    setParseError(null)
    setImportProgress(0)
  }

  const handleFileSelect = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setSelectedFile(file)
    setParseError(null)
    setIsProcessing(true)

    try {
      const bundle = await parseNotificationConfigFile(file)
      setParsedBundle(bundle)

      // Get preview from server
      const preview = await previewNotificationConfigImport(bundle)
      setImportPreview(preview)
      setImportStep('preview')
    } catch (error) {
      setParseError(error instanceof Error ? error.message : 'Failed to parse file')
      setParsedBundle(null)
      setImportPreview(null)
    } finally {
      setIsProcessing(false)
    }
  }, [])

  const handleImport = async () => {
    if (!parsedBundle) return

    setImportStep('importing')
    setIsProcessing(true)
    setImportProgress(10)

    try {
      // Simulate progress for better UX
      const progressInterval = setInterval(() => {
        setImportProgress((prev) => Math.min(prev + 10, 90))
      }, 200)

      const result = await importNotificationConfig({
        bundle: parsedBundle,
        conflict_resolution: conflictResolution,
      })

      clearInterval(progressInterval)
      setImportProgress(100)
      setImportResult(result)
      setImportStep('complete')

      if (result.success) {
        toast({
          title: str(content.configImport?.importSuccess),
          description: result.message,
        })
        onImportComplete?.()
      } else {
        toast({
          title: str(content.configImport?.importPartial),
          description: result.message,
          variant: 'destructive',
        })
      }
    } catch (error) {
      setImportResult({
        success: false,
        message: error instanceof Error ? error.message : 'Import failed',
        created_count: 0,
        skipped_count: 0,
        overwritten_count: 0,
        errors: [error instanceof Error ? error.message : 'Unknown error'],
        created_ids: {},
      })
      setImportStep('complete')
    } finally {
      setIsProcessing(false)
    }
  }

  const closeImportDialog = () => {
    setIsImportDialogOpen(false)
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const getConfigTypeIcon = (type: string) => {
    switch (type) {
      case 'routing_rule':
        return <Route className="h-4 w-4" />
      case 'deduplication':
        return <Filter className="h-4 w-4" />
      case 'throttling':
        return <Timer className="h-4 w-4" />
      case 'escalation':
        return <Bell className="h-4 w-4" />
      default:
        return <Settings2 className="h-4 w-4" />
    }
  }

  const getConfigTypeName = (type: string) => {
    switch (type) {
      case 'routing_rule':
        return str(content.tabs?.routingRules)
      case 'deduplication':
        return str(content.tabs?.deduplication)
      case 'throttling':
        return str(content.tabs?.throttling)
      case 'escalation':
        return str(content.tabs?.escalation)
      default:
        return type
    }
  }

  const renderSelectStep = () => (
    <div className="space-y-6">
      <div className="flex flex-col items-center justify-center gap-4 rounded-lg border-2 border-dashed p-8">
        <FileJson className="h-12 w-12 text-muted-foreground" />
        <div className="text-center">
          <p className="font-medium">{content.configImport?.selectFile}</p>
          <p className="text-sm text-muted-foreground">
            {content.configImport?.supportedFormats}
          </p>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".json"
          onChange={handleFileSelect}
          className="hidden"
          id="config-file-input"
        />
        <Button
          onClick={() => fileInputRef.current?.click()}
          disabled={isProcessing}
        >
          {isProcessing ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              {content.configImport?.parsing}
            </>
          ) : (
            <>
              <Upload className="mr-2 h-4 w-4" />
              {content.configImport?.browseFiles}
            </>
          )}
        </Button>
      </div>

      {parseError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{parseError}</AlertDescription>
        </Alert>
      )}

      {selectedFile && !parseError && (
        <div className="flex items-center gap-2 rounded-md bg-muted p-3">
          <FileJson className="h-5 w-5" />
          <span className="flex-1 truncate">{selectedFile.name}</span>
          <span className="text-sm text-muted-foreground">
            {(selectedFile.size / 1024).toFixed(1)} KB
          </span>
        </div>
      )}
    </div>
  )

  const renderPreviewStep = () => (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Route className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                {content.tabs?.routingRules}
              </span>
            </div>
            <p className="mt-1 text-2xl font-bold">
              {importPreview?.routing_rules_count ?? 0}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                {content.tabs?.deduplication}
              </span>
            </div>
            <p className="mt-1 text-2xl font-bold">
              {importPreview?.deduplication_configs_count ?? 0}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Timer className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                {content.tabs?.throttling}
              </span>
            </div>
            <p className="mt-1 text-2xl font-bold">
              {importPreview?.throttling_configs_count ?? 0}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Bell className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                {content.tabs?.escalation}
              </span>
            </div>
            <p className="mt-1 text-2xl font-bold">
              {importPreview?.escalation_policies_count ?? 0}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* New vs Conflicts Summary */}
      <div className="flex items-center gap-4">
        <Badge variant="outline" className="gap-1">
          <CheckCircle2 className="h-3 w-3 text-green-500" />
          {importPreview?.new_configs ?? 0} {content.configImport?.newConfigs}
        </Badge>
        {(importPreview?.conflicts?.length ?? 0) > 0 && (
          <Badge variant="outline" className="gap-1">
            <FileWarning className="h-3 w-3 text-yellow-500" />
            {importPreview?.conflicts?.length ?? 0} {content.configImport?.conflicts}
          </Badge>
        )}
      </div>

      {/* Conflicts Section */}
      {importPreview?.conflicts && importPreview.conflicts.length > 0 && (
        <Accordion type="single" collapsible defaultValue="conflicts">
          <AccordionItem value="conflicts">
            <AccordionTrigger>
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-yellow-500" />
                {content.configImport?.conflictsDetected} ({importPreview.conflicts.length})
              </div>
            </AccordionTrigger>
            <AccordionContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{content.configImport?.configType}</TableHead>
                    <TableHead>{content.configImport?.importingName}</TableHead>
                    <TableHead>{content.configImport?.existingName}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {importPreview.conflicts.map((conflict: ConfigImportConflict, index: number) => (
                    <TableRow key={`${conflict.config_type}-${conflict.config_id}-${index}`}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getConfigTypeIcon(conflict.config_type)}
                          {getConfigTypeName(conflict.config_type)}
                        </div>
                      </TableCell>
                      <TableCell className="font-medium">{conflict.config_name}</TableCell>
                      <TableCell className="text-muted-foreground">
                        {conflict.existing_name}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      )}

      {/* Conflict Resolution */}
      <div className="space-y-2">
        <label className="text-sm font-medium">
          {content.configImport?.conflictResolution}
        </label>
        <Select
          value={conflictResolution}
          onValueChange={(value: ConflictResolution) => setConflictResolution(value)}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="skip">
              {content.configImport?.resolutionSkip}
            </SelectItem>
            <SelectItem value="overwrite">
              {content.configImport?.resolutionOverwrite}
            </SelectItem>
            <SelectItem value="rename">
              {content.configImport?.resolutionRename}
            </SelectItem>
          </SelectContent>
        </Select>
        <p className="text-xs text-muted-foreground">
          {conflictResolution === 'skip' && content.configImport?.skipDescription}
          {conflictResolution === 'overwrite' && content.configImport?.overwriteDescription}
          {conflictResolution === 'rename' && content.configImport?.renameDescription}
        </p>
      </div>
    </div>
  )

  const renderImportingStep = () => (
    <div className="flex flex-col items-center justify-center gap-4 py-8">
      <Loader2 className="h-12 w-12 animate-spin text-primary" />
      <div className="text-center">
        <p className="font-medium">{content.configImport?.importing}</p>
        <p className="text-sm text-muted-foreground">
          {content.configImport?.pleaseWait}
        </p>
      </div>
      <Progress value={importProgress} className="w-full max-w-xs" />
    </div>
  )

  const renderCompleteStep = () => (
    <div className="space-y-6">
      {/* Result Summary */}
      <div className="flex flex-col items-center gap-4 py-4">
        {importResult?.success ? (
          <CheckCircle2 className="h-12 w-12 text-green-500" />
        ) : (
          <XCircle className="h-12 w-12 text-destructive" />
        )}
        <div className="text-center">
          <p className="font-medium">
            {importResult?.success
              ? content.configImport?.importComplete
              : content.configImport?.importFailed}
          </p>
          <p className="text-sm text-muted-foreground">{importResult?.message}</p>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold text-green-500">
              {importResult?.created_count ?? 0}
            </p>
            <p className="text-sm text-muted-foreground">
              {content.configImport?.created}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold text-yellow-500">
              {importResult?.skipped_count ?? 0}
            </p>
            <p className="text-sm text-muted-foreground">
              {content.configImport?.skipped}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold text-blue-500">
              {importResult?.overwritten_count ?? 0}
            </p>
            <p className="text-sm text-muted-foreground">
              {content.configImport?.overwritten}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Errors */}
      {importResult?.errors && importResult.errors.length > 0 && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <ul className="list-disc pl-4">
              {importResult.errors.map((error, index) => (
                <li key={index}>{error}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}
    </div>
  )

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings2 className="h-5 w-5" />
          {content.configExport?.title}
        </CardTitle>
        <CardDescription>{content.configExport?.description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Export Section */}
        <div className="space-y-4">
          <h4 className="font-medium">{content.configExport?.exportTitle}</h4>

          {/* Export Options */}
          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="export-routing"
                checked={exportOptions.include_routing_rules}
                onCheckedChange={(checked) =>
                  setExportOptions((prev) => ({
                    ...prev,
                    include_routing_rules: !!checked,
                  }))
                }
              />
              <label htmlFor="export-routing" className="text-sm">
                {content.tabs?.routingRules}
              </label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="export-dedup"
                checked={exportOptions.include_deduplication}
                onCheckedChange={(checked) =>
                  setExportOptions((prev) => ({
                    ...prev,
                    include_deduplication: !!checked,
                  }))
                }
              />
              <label htmlFor="export-dedup" className="text-sm">
                {content.tabs?.deduplication}
              </label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="export-throttle"
                checked={exportOptions.include_throttling}
                onCheckedChange={(checked) =>
                  setExportOptions((prev) => ({
                    ...prev,
                    include_throttling: !!checked,
                  }))
                }
              />
              <label htmlFor="export-throttle" className="text-sm">
                {content.tabs?.throttling}
              </label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="export-escalation"
                checked={exportOptions.include_escalation}
                onCheckedChange={(checked) =>
                  setExportOptions((prev) => ({
                    ...prev,
                    include_escalation: !!checked,
                  }))
                }
              />
              <label htmlFor="export-escalation" className="text-sm">
                {content.tabs?.escalation}
              </label>
            </div>
          </div>

          <Button onClick={handleExport} disabled={isExporting}>
            {isExporting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {content.configExport?.exporting}
              </>
            ) : (
              <>
                <Download className="mr-2 h-4 w-4" />
                {content.configExport?.exportButton}
              </>
            )}
          </Button>
        </div>

        <Separator />

        {/* Import Section */}
        <div className="space-y-4">
          <h4 className="font-medium">{content.configImport?.importTitle}</h4>
          <p className="text-sm text-muted-foreground">
            {content.configImport?.importDescription}
          </p>
          <Button variant="outline" onClick={openImportDialog}>
            <Upload className="mr-2 h-4 w-4" />
            {content.configImport?.importButton}
          </Button>
        </div>
      </CardContent>

      {/* Import Dialog */}
      <Dialog open={isImportDialogOpen} onOpenChange={setIsImportDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{content.configImport?.dialogTitle}</DialogTitle>
            <DialogDescription>
              {importStep === 'select' && content.configImport?.dialogDescriptionSelect}
              {importStep === 'preview' && content.configImport?.dialogDescriptionPreview}
              {importStep === 'importing' && content.configImport?.dialogDescriptionImporting}
              {importStep === 'complete' && content.configImport?.dialogDescriptionComplete}
            </DialogDescription>
          </DialogHeader>

          {/* Step Content */}
          {importStep === 'select' && renderSelectStep()}
          {importStep === 'preview' && renderPreviewStep()}
          {importStep === 'importing' && renderImportingStep()}
          {importStep === 'complete' && renderCompleteStep()}

          <DialogFooter>
            {importStep === 'select' && (
              <Button variant="outline" onClick={closeImportDialog}>
                {common.cancel}
              </Button>
            )}
            {importStep === 'preview' && (
              <>
                <Button
                  variant="outline"
                  onClick={() => {
                    setImportStep('select')
                    setSelectedFile(null)
                    setParsedBundle(null)
                    setImportPreview(null)
                    if (fileInputRef.current) {
                      fileInputRef.current.value = ''
                    }
                  }}
                >
                  {content.configImport?.backToSelect}
                </Button>
                <Button onClick={handleImport} disabled={isProcessing}>
                  {content.configImport?.startImport}
                </Button>
              </>
            )}
            {importStep === 'complete' && (
              <Button onClick={closeImportDialog}>{common.close}</Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}

export default ConfigImportExport
