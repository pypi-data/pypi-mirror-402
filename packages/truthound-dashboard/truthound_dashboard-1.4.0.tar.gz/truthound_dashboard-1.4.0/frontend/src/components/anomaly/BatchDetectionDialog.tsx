/**
 * Batch Detection Dialog.
 *
 * Dialog for configuring and starting batch anomaly detection across multiple sources.
 */

import { useCallback, useEffect, useState } from 'react'
import { useIntlayer } from 'react-intlayer'
import { str } from '@/lib/intlayer-utils'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useToast } from '@/hooks/use-toast'
import { Loader2, Database, AlertTriangle, CheckCircle2 } from 'lucide-react'
import type {
  Source,
  AlgorithmInfo,
  AnomalyAlgorithm,
  BatchDetectionRequest,
} from '@/api/client'
import { listSources, listAnomalyAlgorithms, createBatchDetection } from '@/api/client'

interface BatchDetectionDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onJobCreated?: (jobId: string) => void
  preSelectedSourceIds?: string[]
}

export function BatchDetectionDialog({
  open,
  onOpenChange,
  onJobCreated,
  preSelectedSourceIds = [],
}: BatchDetectionDialogProps) {
  const t = useIntlayer('anomaly')
  const common = useIntlayer('common')
  const { toast } = useToast()

  // State
  const [sources, setSources] = useState<Source[]>([])
  const [algorithms, setAlgorithms] = useState<AlgorithmInfo[]>([])
  const [isLoadingSources, setIsLoadingSources] = useState(true)
  const [isLoadingAlgorithms, setIsLoadingAlgorithms] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Form state
  const [jobName, setJobName] = useState('')
  const [selectedSourceIds, setSelectedSourceIds] = useState<Set<string>>(
    new Set(preSelectedSourceIds)
  )
  const [selectedAlgorithm, setSelectedAlgorithm] = useState<AnomalyAlgorithm>('isolation_forest')
  const [sampleSize, setSampleSize] = useState<string>('')

  // Load sources
  useEffect(() => {
    if (!open) return

    const loadSources = async () => {
      setIsLoadingSources(true)
      try {
        const response = await listSources({ limit: 100, active_only: true })
        setSources(response.data)
      } catch (error) {
        toast({
          title: str(common.error),
          description: 'Failed to load sources',
          variant: 'destructive',
        })
      } finally {
        setIsLoadingSources(false)
      }
    }
    loadSources()
  }, [open, toast, common])

  // Load algorithms
  useEffect(() => {
    if (!open) return

    const loadAlgorithms = async () => {
      setIsLoadingAlgorithms(true)
      try {
        const response = await listAnomalyAlgorithms()
        setAlgorithms(response.algorithms)
      } catch (error) {
        toast({
          title: str(t.errorLoadingAlgorithms),
          variant: 'destructive',
        })
      } finally {
        setIsLoadingAlgorithms(false)
      }
    }
    loadAlgorithms()
  }, [open, toast, t])

  // Update selected sources when preSelectedSourceIds changes
  useEffect(() => {
    if (preSelectedSourceIds.length > 0) {
      setSelectedSourceIds(new Set(preSelectedSourceIds))
    }
  }, [preSelectedSourceIds])

  // Toggle source selection
  const toggleSource = useCallback((sourceId: string) => {
    setSelectedSourceIds((prev) => {
      const next = new Set(prev)
      if (next.has(sourceId)) {
        next.delete(sourceId)
      } else {
        next.add(sourceId)
      }
      return next
    })
  }, [])

  // Select all sources
  const selectAll = useCallback(() => {
    setSelectedSourceIds(new Set(sources.map((s) => s.id)))
  }, [sources])

  // Clear all selections
  const clearAll = useCallback(() => {
    setSelectedSourceIds(new Set())
  }, [])

  // Submit batch job
  const handleSubmit = useCallback(async () => {
    if (selectedSourceIds.size === 0) {
      toast({
        title: str(common.error),
        description: str(t.batch.noSourcesSelected),
        variant: 'destructive',
      })
      return
    }

    setIsSubmitting(true)
    try {
      const request: BatchDetectionRequest = {
        source_ids: Array.from(selectedSourceIds),
        algorithm: selectedAlgorithm,
      }

      if (jobName.trim()) {
        request.name = jobName.trim()
      }

      if (sampleSize && parseInt(sampleSize) >= 100) {
        request.sample_size = parseInt(sampleSize)
      }

      const job = await createBatchDetection(request)

      toast({
        title: str(t.batch.jobCreated),
        description: `${str(t.batch.processingSources)} ${job.total_sources} sources`,
      })

      onOpenChange(false)
      onJobCreated?.(job.id)

      // Reset form
      setJobName('')
      setSelectedSourceIds(new Set())
      setSampleSize('')
    } catch (error) {
      toast({
        title: str(t.detectionFailed),
        variant: 'destructive',
      })
    } finally {
      setIsSubmitting(false)
    }
  }, [
    selectedSourceIds,
    selectedAlgorithm,
    jobName,
    sampleSize,
    toast,
    common,
    t,
    onOpenChange,
    onJobCreated,
  ])

  const selectedAlgorithmInfo = algorithms.find((a) => a.name === selectedAlgorithm)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            {t.batch.title}
          </DialogTitle>
          <DialogDescription>{t.batch.description}</DialogDescription>
        </DialogHeader>

        {isLoadingSources || isLoadingAlgorithms ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="space-y-4">
            {/* Job Name */}
            <div className="space-y-2">
              <Label htmlFor="job-name">{t.batch.jobName}</Label>
              <Input
                id="job-name"
                value={jobName}
                onChange={(e) => setJobName(e.target.value)}
                placeholder={str(t.batch.jobNamePlaceholder)}
              />
            </div>

            {/* Source Selection */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>{t.batch.selectSources}</Label>
                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={selectAll}
                  >
                    {t.batch.selectAll}
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={clearAll}
                  >
                    {t.batch.clearAll}
                  </Button>
                </div>
              </div>
              <ScrollArea className="h-48 rounded-md border p-2">
                {sources.length === 0 ? (
                  <div className="flex h-full items-center justify-center text-muted-foreground">
                    No sources available
                  </div>
                ) : (
                  <div className="space-y-2">
                    {sources.map((source) => (
                      <div
                        key={source.id}
                        className="flex items-center gap-2 rounded-md p-2 hover:bg-muted"
                      >
                        <Checkbox
                          id={source.id}
                          checked={selectedSourceIds.has(source.id)}
                          onCheckedChange={() => toggleSource(source.id)}
                        />
                        <label
                          htmlFor={source.id}
                          className="flex flex-1 cursor-pointer items-center justify-between"
                        >
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{source.name}</span>
                            <Badge variant="outline" className="text-xs">
                              {source.type}
                            </Badge>
                          </div>
                          {source.latest_validation_status === 'failed' && (
                            <AlertTriangle className="h-4 w-4 text-orange-500" />
                          )}
                          {source.latest_validation_status === 'success' && (
                            <CheckCircle2 className="h-4 w-4 text-green-500" />
                          )}
                        </label>
                      </div>
                    ))}
                  </div>
                )}
              </ScrollArea>
              <p className="text-sm text-muted-foreground">
                {selectedSourceIds.size} {str(t.batch.sourcesSelected)}
              </p>
            </div>

            {/* Algorithm Selection */}
            <div className="space-y-2">
              <Label htmlFor="algorithm">{t.selectAlgorithm}</Label>
              <Select
                value={selectedAlgorithm}
                onValueChange={(value) =>
                  setSelectedAlgorithm(value as AnomalyAlgorithm)
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder={str(t.selectAlgorithm)} />
                </SelectTrigger>
                <SelectContent>
                  {algorithms.map((algo) => (
                    <SelectItem key={algo.name} value={algo.name}>
                      {algo.display_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {selectedAlgorithmInfo && (
                <p className="text-sm text-muted-foreground">
                  {selectedAlgorithmInfo.description}
                </p>
              )}
            </div>

            {/* Sample Size */}
            <div className="space-y-2">
              <Label htmlFor="sample-size">{t.sampleSize}</Label>
              <Input
                id="sample-size"
                type="number"
                value={sampleSize}
                onChange={(e) => setSampleSize(e.target.value)}
                placeholder={str(t.sampleSizeHint)}
                min={100}
              />
              <p className="text-sm text-muted-foreground">{t.sampleSizeHint}</p>
            </div>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {common.cancel}
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={
              isSubmitting ||
              isLoadingSources ||
              isLoadingAlgorithms ||
              selectedSourceIds.size === 0
            }
          >
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {t.running}
              </>
            ) : (
              <>
                {t.batch.runBatch}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
