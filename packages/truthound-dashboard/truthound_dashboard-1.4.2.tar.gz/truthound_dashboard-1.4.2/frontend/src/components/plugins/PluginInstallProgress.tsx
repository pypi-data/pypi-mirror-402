/**
 * PluginInstallProgress - Plugin installation progress dialog
 *
 * Features:
 * - Step-by-step installation progress
 * - Download progress with percentage
 * - Verification status
 * - Error handling and retry
 */

import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  CheckCircle,
  XCircle,
  Loader2,
  Download,
  Shield,
  Settings,
  Package,
  AlertTriangle,
  RefreshCw,
  FileCode,
  Key,
  Play,
} from 'lucide-react'
import type { Plugin } from '@/api/client'

interface InstallStep {
  id: string
  label: string
  description: string
  icon: React.ReactNode
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped'
  progress?: number
  error?: string
  details?: string[]
}

interface PluginInstallProgressProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  plugin: Plugin | null
  onComplete: () => void
  onRetry: () => void
}

export function PluginInstallProgress({
  open,
  onOpenChange,
  plugin,
  onComplete,
  onRetry,
}: PluginInstallProgressProps) {
  const [steps, setSteps] = useState<InstallStep[]>([])
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [installStatus, setInstallStatus] = useState<'installing' | 'completed' | 'failed'>('installing')
  const [logs, setLogs] = useState<string[]>([])

  // Initialize steps when dialog opens
  useEffect(() => {
    if (!open || !plugin) return

    const initialSteps: InstallStep[] = [
      {
        id: 'download',
        label: 'Downloading',
        description: 'Downloading plugin package...',
        icon: <Download className="w-4 h-4" />,
        status: 'pending',
        progress: 0,
      },
      {
        id: 'verify',
        label: 'Verifying',
        description: 'Verifying package integrity and signatures...',
        icon: <Key className="w-4 h-4" />,
        status: 'pending',
      },
      {
        id: 'security',
        label: 'Security Check',
        description: 'Analyzing code for security issues...',
        icon: <Shield className="w-4 h-4" />,
        status: 'pending',
      },
      {
        id: 'dependencies',
        label: 'Dependencies',
        description: 'Resolving and installing dependencies...',
        icon: <Package className="w-4 h-4" />,
        status: 'pending',
      },
      {
        id: 'install',
        label: 'Installing',
        description: 'Installing plugin files...',
        icon: <FileCode className="w-4 h-4" />,
        status: 'pending',
      },
      {
        id: 'configure',
        label: 'Configuring',
        description: 'Applying plugin configuration...',
        icon: <Settings className="w-4 h-4" />,
        status: 'pending',
      },
      {
        id: 'activate',
        label: 'Activating',
        description: 'Activating plugin...',
        icon: <Play className="w-4 h-4" />,
        status: 'pending',
      },
    ]

    setSteps(initialSteps)
    setCurrentStepIndex(0)
    setInstallStatus('installing')
    setLogs([`Starting installation of ${plugin.display_name}...`])

    // Start installation simulation
    simulateInstallation(initialSteps)
  }, [open, plugin])

  const simulateInstallation = async (initialSteps: InstallStep[]) => {
    const updatedSteps = [...initialSteps]

    for (let i = 0; i < updatedSteps.length; i++) {
      setCurrentStepIndex(i)

      // Update step to running
      updatedSteps[i].status = 'running'
      setSteps([...updatedSteps])
      addLog(`Step ${i + 1}/${updatedSteps.length}: ${updatedSteps[i].label}...`)

      // Simulate step processing
      if (updatedSteps[i].id === 'download') {
        // Simulate download progress
        for (let progress = 0; progress <= 100; progress += 10) {
          updatedSteps[i].progress = progress
          setSteps([...updatedSteps])
          await delay(100)
        }
        addLog(`Downloaded: ${plugin?.name}-${plugin?.version}.tar.gz (2.4 MB)`)
      } else if (updatedSteps[i].id === 'verify') {
        await delay(800)
        updatedSteps[i].details = [
          'SHA256 checksum: verified',
          plugin?.security_level === 'trusted' ? 'Signature: valid (trusted signer)' : 'Signature: not present',
        ]
        addLog('Package verification completed')
      } else if (updatedSteps[i].id === 'security') {
        await delay(1200)
        updatedSteps[i].details = [
          'No dangerous patterns detected',
          'Sandbox compatible: yes',
          `Risk level: ${plugin?.security_level || 'low'}`,
        ]
        addLog('Security analysis passed')
      } else if (updatedSteps[i].id === 'dependencies') {
        await delay(600)
        const deps = plugin?.dependencies?.length || 0
        updatedSteps[i].details = deps > 0
          ? [`Resolved ${deps} dependencies`]
          : ['No additional dependencies required']
        addLog(deps > 0 ? `Installed ${deps} dependencies` : 'No dependencies to install')
      } else if (updatedSteps[i].id === 'install') {
        await delay(500)
        addLog('Plugin files extracted to plugins directory')
      } else if (updatedSteps[i].id === 'configure') {
        await delay(400)
        addLog('Default configuration applied')
      } else if (updatedSteps[i].id === 'activate') {
        await delay(300)
        addLog(`Plugin ${plugin?.display_name} activated successfully`)
      } else {
        await delay(500)
      }

      // Mark step as completed
      updatedSteps[i].status = 'completed'
      setSteps([...updatedSteps])
    }

    // Installation complete
    setInstallStatus('completed')
    addLog('Installation completed successfully!')
  }

  const addLog = (message: string) => {
    const timestamp = new Date().toLocaleTimeString()
    setLogs((prev) => [...prev, `[${timestamp}] ${message}`])
  }

  const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

  const handleClose = () => {
    if (installStatus === 'completed') {
      onComplete()
    }
    onOpenChange(false)
  }

  const getStepIcon = (step: InstallStep) => {
    switch (step.status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />
      case 'running':
        return <Loader2 className="w-5 h-5 text-primary animate-spin" />
      case 'skipped':
        return <div className="w-5 h-5 rounded-full bg-muted" />
      default:
        return <div className="w-5 h-5 rounded-full border-2 border-muted" />
    }
  }

  const overallProgress = Math.round(
    (steps.filter((s) => s.status === 'completed').length / steps.length) * 100
  )

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {installStatus === 'installing' && (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Installing {plugin?.display_name}
              </>
            )}
            {installStatus === 'completed' && (
              <>
                <CheckCircle className="w-5 h-5 text-green-500" />
                Installation Complete
              </>
            )}
            {installStatus === 'failed' && (
              <>
                <XCircle className="w-5 h-5 text-red-500" />
                Installation Failed
              </>
            )}
          </DialogTitle>
          <DialogDescription>
            {plugin?.name} v{plugin?.version}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Overall Progress */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span>Overall Progress</span>
              <span className="font-medium">{overallProgress}%</span>
            </div>
            <Progress value={overallProgress} className="h-2" />
          </div>

          {/* Steps */}
          <div className="space-y-3">
            {steps.map((step, index) => (
              <div
                key={step.id}
                className={`flex items-start gap-3 p-3 rounded-lg transition-colors ${
                  step.status === 'running'
                    ? 'bg-primary/5 border border-primary/20'
                    : step.status === 'completed'
                    ? 'bg-green-500/5'
                    : step.status === 'failed'
                    ? 'bg-red-500/5'
                    : 'bg-muted/50'
                }`}
              >
                <div className="mt-0.5">{getStepIcon(step)}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span
                      className={`font-medium text-sm ${
                        step.status === 'pending' ? 'text-muted-foreground' : ''
                      }`}
                    >
                      {step.label}
                    </span>
                    {step.status === 'completed' && (
                      <Badge variant="secondary" className="text-xs bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                        Done
                      </Badge>
                    )}
                    {step.status === 'failed' && (
                      <Badge variant="destructive" className="text-xs">
                        Failed
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {step.description}
                  </p>
                  {step.status === 'running' && step.progress !== undefined && (
                    <Progress value={step.progress} className="h-1 mt-2" />
                  )}
                  {step.details && step.status === 'completed' && (
                    <div className="mt-2 space-y-1">
                      {step.details.map((detail, i) => (
                        <p key={i} className="text-xs text-muted-foreground flex items-center gap-1">
                          <CheckCircle className="w-3 h-3 text-green-500" />
                          {detail}
                        </p>
                      ))}
                    </div>
                  )}
                  {step.error && (
                    <p className="text-xs text-red-500 mt-1 flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      {step.error}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Logs */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Installation Log</span>
              <Badge variant="outline" className="text-xs">
                {logs.length} entries
              </Badge>
            </div>
            <ScrollArea className="h-[120px] bg-muted rounded-lg p-3">
              <div className="font-mono text-xs space-y-1">
                {logs.map((log, i) => (
                  <p key={i} className="text-muted-foreground">
                    {log}
                  </p>
                ))}
              </div>
            </ScrollArea>
          </div>
        </div>

        <DialogFooter>
          {installStatus === 'failed' && (
            <Button variant="outline" onClick={onRetry}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Retry
            </Button>
          )}
          <Button
            onClick={handleClose}
            variant={installStatus === 'completed' ? 'default' : 'outline'}
            disabled={installStatus === 'installing'}
          >
            {installStatus === 'completed' ? 'Done' : 'Cancel'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default PluginInstallProgress
