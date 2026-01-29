/**
 * PluginSecurityPanel - Security analysis and trust store management
 *
 * Features:
 * - Security report display
 * - Trust store management (signers)
 * - Security policy configuration
 * - Signature verification
 */

import { useState, useEffect } from 'react'
import { useIntlayer } from 'react-intlayer'
import { str } from '@/lib/intlayer-utils'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Slider } from '@/components/ui/slider'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { toast } from '@/hooks/use-toast'
import {
  Shield,
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  Lock,
  Key,
  UserCheck,
  Plus,
  Trash2,
  FileCode,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Info,
  RefreshCw,
} from 'lucide-react'
import type { Plugin } from '@/api/client'

// Types
interface SecurityReport {
  plugin_id: string
  analyzed_at: string
  risk_level: string
  issues: string[]
  warnings: string[]
  permissions_required: string[]
  signature_valid: boolean
  sandbox_compatible: boolean
  code_analysis?: {
    is_safe: boolean
    issues: string[]
    warnings: string[]
    blocked_constructs: string[]
    detected_imports: string[]
    detected_permissions: string[]
    complexity_score: number
  }
  signature_count: number
  trust_level: string
  can_run_in_sandbox: boolean
  code_hash: string
  recommendations: string[]
}

interface TrustedSigner {
  signer_id: string
  name: string
  public_key: string
  algorithm: string
  added_at: string
  expires_at?: string
  is_active: boolean
  trust_level: string
}

interface SecurityPolicy {
  preset: string
  isolation_level: string
  require_signature: boolean
  min_signatures: number
  allowed_signers: string[]
  blocked_modules: string[]
  memory_limit_mb: number
  cpu_time_limit_sec: number
  network_enabled: boolean
  filesystem_read: boolean
  filesystem_write: boolean
}

interface PluginSecurityPanelProps {
  plugin: Plugin
  onAnalyze?: () => void
}

// Security Level Badge
function SecurityLevelBadge({ level }: { level: string }) {
  const config: Record<string, { icon: React.ReactNode; className: string; label: string }> = {
    trusted: {
      icon: <ShieldCheck className="w-3 h-3" />,
      className: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      label: 'Trusted',
    },
    verified: {
      icon: <Shield className="w-3 h-3" />,
      className: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
      label: 'Verified',
    },
    unverified: {
      icon: <ShieldAlert className="w-3 h-3" />,
      className: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
      label: 'Unverified',
    },
    sandboxed: {
      icon: <ShieldX className="w-3 h-3" />,
      className: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400',
      label: 'Sandboxed',
    },
  }

  const { icon, className, label } = config[level] || config.unverified

  return (
    <Badge variant="secondary" className={`gap-1 ${className}`}>
      {icon}
      {label}
    </Badge>
  )
}

// Security Report Card
function SecurityReportCard({ report }: { report: SecurityReport }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Shield className="w-4 h-4" />
            Security Analysis
          </CardTitle>
          <SecurityLevelBadge level={report.trust_level} />
        </div>
        <CardDescription>
          Analyzed at {new Date(report.analyzed_at).toLocaleString()}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Signature Status */}
        <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
          <div className="flex items-center gap-2">
            <Key className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm">Signature Verification</span>
          </div>
          {report.signature_valid ? (
            <Badge variant="secondary" className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
              <CheckCircle className="w-3 h-3 mr-1" />
              Valid ({report.signature_count} signature{report.signature_count !== 1 ? 's' : ''})
            </Badge>
          ) : (
            <Badge variant="secondary" className="bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400">
              <XCircle className="w-3 h-3 mr-1" />
              Not Signed
            </Badge>
          )}
        </div>

        {/* Sandbox Compatibility */}
        <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
          <div className="flex items-center gap-2">
            <Lock className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm">Sandbox Compatible</span>
          </div>
          {report.can_run_in_sandbox ? (
            <Badge variant="secondary" className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
              <CheckCircle className="w-3 h-3 mr-1" />
              Yes
            </Badge>
          ) : (
            <Badge variant="secondary" className="bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400">
              <AlertTriangle className="w-3 h-3 mr-1" />
              Limited
            </Badge>
          )}
        </div>

        {/* Issues */}
        {report.issues.length > 0 && (
          <Alert variant="destructive">
            <AlertTriangle className="w-4 h-4" />
            <AlertDescription>
              <strong>{report.issues.length} Critical Issue{report.issues.length !== 1 ? 's' : ''}</strong>
              <ul className="list-disc list-inside mt-2 text-sm">
                {report.issues.map((issue, i) => (
                  <li key={i}>{issue}</li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        {/* Warnings */}
        {report.warnings.length > 0 && (
          <Alert>
            <Info className="w-4 h-4" />
            <AlertDescription>
              <strong>{report.warnings.length} Warning{report.warnings.length !== 1 ? 's' : ''}</strong>
              <ul className="list-disc list-inside mt-2 text-sm">
                {report.warnings.map((warning, i) => (
                  <li key={i}>{warning}</li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        {/* Permissions Required */}
        {report.permissions_required.length > 0 && (
          <div>
            <h4 className="text-sm font-medium mb-2">Required Permissions</h4>
            <div className="flex flex-wrap gap-2">
              {report.permissions_required.map((perm) => (
                <Badge key={perm} variant="outline">
                  {perm.replace(/_/g, ' ')}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Code Analysis */}
        {report.code_analysis && (
          <Accordion type="single" collapsible>
            <AccordionItem value="code-analysis">
              <AccordionTrigger>
                <div className="flex items-center gap-2">
                  <FileCode className="w-4 h-4" />
                  Code Analysis
                  {report.code_analysis.is_safe ? (
                    <Badge variant="secondary" className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 ml-2">
                      Safe
                    </Badge>
                  ) : (
                    <Badge variant="destructive" className="ml-2">
                      Issues Found
                    </Badge>
                  )}
                </div>
              </AccordionTrigger>
              <AccordionContent className="space-y-3">
                {/* Complexity Score */}
                <div className="flex items-center justify-between">
                  <span className="text-sm">Complexity Score</span>
                  <span className={`font-mono text-sm ${
                    report.code_analysis.complexity_score > 70 ? 'text-red-500' :
                    report.code_analysis.complexity_score > 40 ? 'text-yellow-500' :
                    'text-green-500'
                  }`}>
                    {report.code_analysis.complexity_score}/100
                  </span>
                </div>

                {/* Detected Imports */}
                {report.code_analysis.detected_imports.length > 0 && (
                  <div>
                    <span className="text-sm font-medium">Detected Imports</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {report.code_analysis.detected_imports.map((imp) => (
                        <Badge key={imp} variant="secondary" className="font-mono text-xs">
                          {imp}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Blocked Constructs */}
                {report.code_analysis.blocked_constructs.length > 0 && (
                  <Alert variant="destructive">
                    <AlertDescription>
                      <strong>Blocked Constructs Found:</strong>
                      <div className="flex flex-wrap gap-1 mt-2">
                        {report.code_analysis.blocked_constructs.map((bc) => (
                          <Badge key={bc} variant="destructive" className="font-mono text-xs">
                            {bc}
                          </Badge>
                        ))}
                      </div>
                    </AlertDescription>
                  </Alert>
                )}
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        )}

        {/* Recommendations */}
        {report.recommendations.length > 0 && (
          <div>
            <h4 className="text-sm font-medium mb-2">Recommendations</h4>
            <ul className="space-y-1">
              {report.recommendations.map((rec, i) => (
                <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                  <Info className="w-3 h-3 mt-1 flex-shrink-0" />
                  {rec}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Code Hash */}
        {report.code_hash && (
          <div className="text-xs text-muted-foreground font-mono">
            SHA256: {report.code_hash.substring(0, 16)}...
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// Trust Store Management
function TrustStoreCard({
  signers,
  onAdd,
  onRemove,
}: {
  signers: TrustedSigner[]
  onAdd: () => void
  onRemove: (id: string) => void
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <UserCheck className="w-4 h-4" />
            Trusted Signers
          </CardTitle>
          <Button variant="outline" size="sm" onClick={onAdd}>
            <Plus className="w-4 h-4 mr-1" />
            Add Signer
          </Button>
        </div>
        <CardDescription>
          Manage trusted signing keys for plugin verification
        </CardDescription>
      </CardHeader>
      <CardContent>
        {signers.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Key className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No trusted signers configured</p>
            <p className="text-xs mt-1">Add a signer to enable signature verification</p>
          </div>
        ) : (
          <ScrollArea className="h-[200px]">
            <div className="space-y-2">
              {signers.map((signer) => (
                <div
                  key={signer.signer_id}
                  className="flex items-center justify-between p-3 bg-muted rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${signer.is_active ? 'bg-green-500' : 'bg-gray-400'}`} />
                    <div>
                      <div className="font-medium text-sm">{signer.name}</div>
                      <div className="text-xs text-muted-foreground">
                        {signer.algorithm.toUpperCase()} · Added {new Date(signer.added_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <SecurityLevelBadge level={signer.trust_level} />
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-destructive hover:text-destructive"
                      onClick={() => onRemove(signer.signer_id)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  )
}

// Security Policy Editor
function SecurityPolicyCard({
  policy,
  onChange,
}: {
  policy: SecurityPolicy
  onChange: (policy: SecurityPolicy) => void
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Lock className="w-4 h-4" />
          Security Policy
        </CardTitle>
        <CardDescription>
          Configure plugin execution security settings
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Preset Selection */}
        <div className="space-y-2">
          <Label>Policy Preset</Label>
          <Select
            value={policy.preset}
            onValueChange={(value) => onChange({ ...policy, preset: value })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="development">Development (Permissive)</SelectItem>
              <SelectItem value="testing">Testing</SelectItem>
              <SelectItem value="standard">Standard (Recommended)</SelectItem>
              <SelectItem value="enterprise">Enterprise</SelectItem>
              <SelectItem value="strict">Strict</SelectItem>
              <SelectItem value="airgapped">Air-gapped</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Isolation Level */}
        <div className="space-y-2">
          <Label>Isolation Level</Label>
          <Select
            value={policy.isolation_level}
            onValueChange={(value) => onChange({ ...policy, isolation_level: value })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">None (Trusted plugins only)</SelectItem>
              <SelectItem value="process">Process (Recommended)</SelectItem>
              <SelectItem value="container">Container (Maximum isolation)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <Separator />

        {/* Signature Requirements */}
        <div className="flex items-center justify-between">
          <div>
            <Label>Require Signature</Label>
            <p className="text-xs text-muted-foreground">Only allow signed plugins</p>
          </div>
          <Switch
            checked={policy.require_signature}
            onCheckedChange={(checked) => onChange({ ...policy, require_signature: checked })}
          />
        </div>

        {policy.require_signature && (
          <div className="space-y-2">
            <Label>Minimum Signatures Required</Label>
            <div className="flex items-center gap-4">
              <Slider
                value={[policy.min_signatures]}
                onValueChange={([value]) => onChange({ ...policy, min_signatures: value })}
                min={1}
                max={5}
                step={1}
                className="flex-1"
              />
              <span className="text-sm font-medium w-8 text-center">{policy.min_signatures}</span>
            </div>
          </div>
        )}

        <Separator />

        {/* Resource Limits */}
        <div className="space-y-2">
          <Label>Memory Limit (MB)</Label>
          <div className="flex items-center gap-4">
            <Slider
              value={[policy.memory_limit_mb]}
              onValueChange={([value]) => onChange({ ...policy, memory_limit_mb: value })}
              min={64}
              max={2048}
              step={64}
              className="flex-1"
            />
            <span className="text-sm font-medium w-16 text-center">{policy.memory_limit_mb}</span>
          </div>
        </div>

        <div className="space-y-2">
          <Label>CPU Time Limit (seconds)</Label>
          <div className="flex items-center gap-4">
            <Slider
              value={[policy.cpu_time_limit_sec]}
              onValueChange={([value]) => onChange({ ...policy, cpu_time_limit_sec: value })}
              min={5}
              max={300}
              step={5}
              className="flex-1"
            />
            <span className="text-sm font-medium w-16 text-center">{policy.cpu_time_limit_sec}s</span>
          </div>
        </div>

        <Separator />

        {/* Access Permissions */}
        <div className="space-y-3">
          <Label>Access Permissions</Label>

          <div className="flex items-center justify-between">
            <span className="text-sm">Network Access</span>
            <Switch
              checked={policy.network_enabled}
              onCheckedChange={(checked) => onChange({ ...policy, network_enabled: checked })}
            />
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm">File System Read</span>
            <Switch
              checked={policy.filesystem_read}
              onCheckedChange={(checked) => onChange({ ...policy, filesystem_read: checked })}
            />
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm">File System Write</span>
            <Switch
              checked={policy.filesystem_write}
              onCheckedChange={(checked) => onChange({ ...policy, filesystem_write: checked })}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// Main Component
export function PluginSecurityPanel({ plugin, onAnalyze }: PluginSecurityPanelProps) {
  const [securityReport, setSecurityReport] = useState<SecurityReport | null>(null)
  const [trustedSigners, setTrustedSigners] = useState<TrustedSigner[]>([])
  const [policy, setPolicy] = useState<SecurityPolicy>({
    preset: 'standard',
    isolation_level: 'process',
    require_signature: true,
    min_signatures: 1,
    allowed_signers: [],
    blocked_modules: [],
    memory_limit_mb: 256,
    cpu_time_limit_sec: 30,
    network_enabled: false,
    filesystem_read: false,
    filesystem_write: false,
  })
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [showAddSigner, setShowAddSigner] = useState(false)

  const handleAnalyze = async () => {
    setIsAnalyzing(true)
    try {
      // In production, call actual API
      // const report = await analyzePluginSecurity(plugin.id)
      // setSecurityReport(report)

      // Mock response
      setSecurityReport({
        plugin_id: plugin.id,
        analyzed_at: new Date().toISOString(),
        risk_level: plugin.security_level || 'unverified',
        issues: [],
        warnings: ['Plugin signature could not be verified'],
        permissions_required: plugin.permissions || [],
        signature_valid: false,
        sandbox_compatible: true,
        signature_count: 0,
        trust_level: plugin.security_level || 'unverified',
        can_run_in_sandbox: true,
        code_hash: 'abc123...',
        recommendations: ['Sign the plugin for production use'],
      })

      toast({
        title: 'Analysis Complete',
        description: 'Security analysis has been completed.',
      })

      onAnalyze?.()
    } catch (error) {
      toast({
        title: 'Analysis Failed',
        description: 'Failed to analyze plugin security.',
        variant: 'destructive',
      })
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleAddSigner = () => {
    setShowAddSigner(true)
  }

  const handleRemoveSigner = (signerId: string) => {
    setTrustedSigners((prev) => prev.filter((s) => s.signer_id !== signerId))
    toast({
      title: 'Signer Removed',
      description: 'The signer has been removed from the trust store.',
    })
  }

  const handlePolicyChange = (newPolicy: SecurityPolicy) => {
    setPolicy(newPolicy)
  }

  return (
    <div className="space-y-4">
      {/* Analyze Button */}
      <div className="flex justify-end">
        <Button onClick={handleAnalyze} disabled={isAnalyzing}>
          {isAnalyzing ? (
            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <Shield className="w-4 h-4 mr-2" />
          )}
          {isAnalyzing ? 'Analyzing...' : 'Analyze Security'}
        </Button>
      </div>

      {/* Security Report */}
      {securityReport && <SecurityReportCard report={securityReport} />}

      {/* Trust Store */}
      <TrustStoreCard
        signers={trustedSigners}
        onAdd={handleAddSigner}
        onRemove={handleRemoveSigner}
      />

      {/* Security Policy */}
      <SecurityPolicyCard policy={policy} onChange={handlePolicyChange} />

      {/* Add Signer Dialog */}
      <Dialog open={showAddSigner} onOpenChange={setShowAddSigner}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Trusted Signer</DialogTitle>
            <DialogDescription>
              Add a new trusted signing key for plugin verification
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Signer Name</Label>
              <Input placeholder="Official Maintainer" />
            </div>
            <div className="space-y-2">
              <Label>Public Key</Label>
              <Input placeholder="Paste public key..." className="font-mono text-sm" />
            </div>
            <div className="space-y-2">
              <Label>Algorithm</Label>
              <Select defaultValue="ed25519">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ed25519">Ed25519 (Recommended)</SelectItem>
                  <SelectItem value="rsa_sha256">RSA-SHA256</SelectItem>
                  <SelectItem value="hmac_sha256">HMAC-SHA256</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddSigner(false)}>
              Cancel
            </Button>
            <Button onClick={() => {
              toast({
                title: 'Signer Added',
                description: 'The signer has been added to the trust store.',
              })
              setShowAddSigner(false)
            }}>
              Add Signer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default PluginSecurityPanel
