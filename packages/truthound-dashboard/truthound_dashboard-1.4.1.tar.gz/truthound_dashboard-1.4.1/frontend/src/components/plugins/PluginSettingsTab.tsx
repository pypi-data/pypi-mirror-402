/**
 * PluginSettingsTab - Global plugin security settings management
 *
 * Features:
 * - Trust Store management (add/remove trusted signers)
 * - Global Security Policy configuration
 * - Security presets
 * - Module whitelist/blacklist management
 */

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { Slider } from '@/components/ui/slider'
import { Separator } from '@/components/ui/separator'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from '@/components/ui/alert'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { toast } from '@/hooks/use-toast'
import {
  Shield,
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  Key,
  UserCheck,
  Plus,
  Trash2,
  Lock,
  Unlock,
  Server,
  Cpu,
  HardDrive,
  Network,
  FileCode,
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw,
  Copy,
  Download,
  Upload,
  Info,
  Settings,
  Zap,
} from 'lucide-react'

// Types
interface TrustedSigner {
  id: string
  signer_id: string
  name: string
  organization?: string
  email?: string
  public_key: string
  algorithm: string
  fingerprint: string
  trust_level: string
  plugins_signed: number
  added_at: string
  expires_at?: string
  is_active: boolean
}

interface SecurityPolicy {
  id: string
  name: string
  description?: string
  is_default: boolean
  is_active: boolean
  isolation_level: string
  memory_limit_mb: number
  cpu_time_limit_sec: number
  wall_time_limit_sec: number
  network_enabled: boolean
  file_read_enabled: boolean
  file_write_enabled: boolean
  allowed_modules: string[]
  blocked_modules: string[]
  require_signature: boolean
  min_trust_level: string
  max_processes: number
  container_image: string
}

// Presets
const SECURITY_PRESETS: Record<string, Partial<SecurityPolicy>> = {
  development: {
    isolation_level: 'none',
    network_enabled: true,
    file_read_enabled: true,
    file_write_enabled: true,
    require_signature: false,
    memory_limit_mb: 1024,
    wall_time_limit_sec: 300,
    min_trust_level: 'unverified',
  },
  testing: {
    isolation_level: 'process',
    network_enabled: true,
    file_read_enabled: true,
    file_write_enabled: false,
    require_signature: false,
    memory_limit_mb: 512,
    wall_time_limit_sec: 120,
    min_trust_level: 'unverified',
  },
  standard: {
    isolation_level: 'process',
    network_enabled: false,
    file_read_enabled: true,
    file_write_enabled: false,
    require_signature: false,
    memory_limit_mb: 256,
    wall_time_limit_sec: 60,
    min_trust_level: 'verified',
  },
  enterprise: {
    isolation_level: 'process',
    network_enabled: false,
    file_read_enabled: true,
    file_write_enabled: false,
    require_signature: true,
    memory_limit_mb: 512,
    wall_time_limit_sec: 120,
    min_trust_level: 'trusted',
  },
  strict: {
    isolation_level: 'container',
    network_enabled: false,
    file_read_enabled: false,
    file_write_enabled: false,
    require_signature: true,
    memory_limit_mb: 128,
    wall_time_limit_sec: 30,
    min_trust_level: 'trusted',
  },
}

const DEFAULT_ALLOWED_MODULES = [
  'math', 'statistics', 'decimal', 'fractions',
  'random', 're', 'json', 'datetime',
  'collections', 'itertools', 'functools',
  'operator', 'string', 'typing', 'dataclasses',
]

const DEFAULT_BLOCKED_MODULES = [
  'os', 'sys', 'subprocess', 'socket', 'shutil',
  'importlib', 'ctypes', 'multiprocessing',
]

// Trust Level Badge Component
function TrustLevelBadge({ level }: { level: string }) {
  const config: Record<string, { icon: React.ReactNode; className: string }> = {
    trusted: {
      icon: <ShieldCheck className="w-3 h-3" />,
      className: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    },
    verified: {
      icon: <Shield className="w-3 h-3" />,
      className: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    },
    unverified: {
      icon: <ShieldAlert className="w-3 h-3" />,
      className: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    },
    revoked: {
      icon: <ShieldX className="w-3 h-3" />,
      className: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    },
  }

  const { icon, className } = config[level] || config.unverified

  return (
    <Badge variant="secondary" className={`gap-1 ${className}`}>
      {icon}
      {level.charAt(0).toUpperCase() + level.slice(1)}
    </Badge>
  )
}

// Trust Store Card Component
function TrustStoreCard({
  signers,
  onAdd,
  onRemove,
  onRevoke,
  loading,
}: {
  signers: TrustedSigner[]
  onAdd: () => void
  onRemove: (id: string) => void
  onRevoke: (id: string) => void
  loading?: boolean
}) {
  const [expandedId, setExpandedId] = useState<string | null>(null)

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base flex items-center gap-2">
              <UserCheck className="w-4 h-4" />
              Trust Store
            </CardTitle>
            <CardDescription>
              Manage trusted signing keys for plugin verification
            </CardDescription>
          </div>
          <Button onClick={onAdd}>
            <Plus className="w-4 h-4 mr-2" />
            Add Signer
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-center py-8 text-muted-foreground">
            <RefreshCw className="w-6 h-6 mx-auto animate-spin mb-2" />
            Loading...
          </div>
        ) : signers.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Key className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No trusted signers configured</p>
            <p className="text-xs mt-1">Add a signer to enable signature verification</p>
          </div>
        ) : (
          <ScrollArea className="h-[300px]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Organization</TableHead>
                  <TableHead>Algorithm</TableHead>
                  <TableHead>Trust Level</TableHead>
                  <TableHead>Signed</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {signers.map((signer) => (
                  <TableRow
                    key={signer.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => setExpandedId(expandedId === signer.id ? null : signer.id)}
                  >
                    <TableCell className="font-medium">{signer.name}</TableCell>
                    <TableCell>{signer.organization || '-'}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="font-mono text-xs">
                        {signer.algorithm.toUpperCase()}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <TrustLevelBadge level={signer.trust_level} />
                    </TableCell>
                    <TableCell>{signer.plugins_signed}</TableCell>
                    <TableCell>
                      <div className={`w-2 h-2 rounded-full ${
                        signer.is_active && signer.trust_level !== 'revoked'
                          ? 'bg-green-500'
                          : 'bg-red-500'
                      }`} />
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={(e) => {
                            e.stopPropagation()
                            navigator.clipboard.writeText(signer.fingerprint)
                            toast({ title: 'Fingerprint copied' })
                          }}
                        >
                          <Copy className="w-3 h-3" />
                        </Button>
                        {signer.trust_level !== 'revoked' && (
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-yellow-600 hover:text-yellow-700"
                            onClick={(e) => {
                              e.stopPropagation()
                              onRevoke(signer.id)
                            }}
                          >
                            <ShieldX className="w-3 h-3" />
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-destructive hover:text-destructive"
                          onClick={(e) => {
                            e.stopPropagation()
                            onRemove(signer.id)
                          }}
                        >
                          <Trash2 className="w-3 h-3" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  )
}

// Security Policy Card Component
function SecurityPolicyCard({
  policy,
  onChange,
  onSave,
  saving,
}: {
  policy: SecurityPolicy
  onChange: (policy: SecurityPolicy) => void
  onSave: () => void
  saving?: boolean
}) {
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null)

  const handlePresetChange = (preset: string) => {
    setSelectedPreset(preset)
    const presetConfig = SECURITY_PRESETS[preset]
    if (presetConfig) {
      onChange({
        ...policy,
        ...presetConfig,
        name: preset,
      })
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base flex items-center gap-2">
              <Lock className="w-4 h-4" />
              Security Policy
            </CardTitle>
            <CardDescription>
              Configure global plugin execution security settings
            </CardDescription>
          </div>
          <Button onClick={onSave} disabled={saving}>
            {saving ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : null}
            Save Policy
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Preset Selection */}
        <div className="space-y-2">
          <Label className="flex items-center gap-2">
            <Zap className="w-4 h-4" />
            Quick Preset
          </Label>
          <div className="flex flex-wrap gap-2">
            {Object.keys(SECURITY_PRESETS).map((preset) => (
              <Button
                key={preset}
                variant={selectedPreset === preset ? 'default' : 'outline'}
                size="sm"
                onClick={() => handlePresetChange(preset)}
              >
                {preset.charAt(0).toUpperCase() + preset.slice(1)}
              </Button>
            ))}
          </div>
          <p className="text-xs text-muted-foreground">
            Select a preset or customize settings below
          </p>
        </div>

        <Separator />

        {/* Isolation Level */}
        <div className="space-y-2">
          <Label className="flex items-center gap-2">
            <Server className="w-4 h-4" />
            Isolation Level
          </Label>
          <Select
            value={policy.isolation_level}
            onValueChange={(value) => onChange({ ...policy, isolation_level: value })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">
                <div className="flex items-center gap-2">
                  <Unlock className="w-4 h-4 text-red-500" />
                  None (Trusted plugins only)
                </div>
              </SelectItem>
              <SelectItem value="process">
                <div className="flex items-center gap-2">
                  <Lock className="w-4 h-4 text-yellow-500" />
                  Process (Recommended)
                </div>
              </SelectItem>
              <SelectItem value="container">
                <div className="flex items-center gap-2">
                  <Server className="w-4 h-4 text-green-500" />
                  Container (Maximum isolation)
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Container Image (if container isolation) */}
        {policy.isolation_level === 'container' && (
          <div className="space-y-2">
            <Label>Container Image</Label>
            <Input
              value={policy.container_image}
              onChange={(e) => onChange({ ...policy, container_image: e.target.value })}
              placeholder="python:3.11-slim"
            />
          </div>
        )}

        <Separator />

        {/* Signature Requirements */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="flex items-center gap-2">
                <Key className="w-4 h-4" />
                Require Signature
              </Label>
              <p className="text-xs text-muted-foreground">
                Only allow plugins with valid signatures
              </p>
            </div>
            <Switch
              checked={policy.require_signature}
              onCheckedChange={(checked) => onChange({ ...policy, require_signature: checked })}
            />
          </div>

          <div className="space-y-2">
            <Label>Minimum Trust Level</Label>
            <Select
              value={policy.min_trust_level}
              onValueChange={(value) => onChange({ ...policy, min_trust_level: value })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="unverified">Unverified (Any plugin)</SelectItem>
                <SelectItem value="verified">Verified (Checked signature)</SelectItem>
                <SelectItem value="trusted">Trusted (Known signers only)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <Separator />

        {/* Resource Limits */}
        <div className="space-y-4">
          <Label className="flex items-center gap-2">
            <Cpu className="w-4 h-4" />
            Resource Limits
          </Label>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-sm">Memory Limit (MB)</Label>
              <div className="flex items-center gap-4">
                <Slider
                  value={[policy.memory_limit_mb]}
                  onValueChange={([value]) => onChange({ ...policy, memory_limit_mb: value })}
                  min={64}
                  max={4096}
                  step={64}
                  className="flex-1"
                />
                <span className="text-sm font-mono w-16 text-right">{policy.memory_limit_mb}</span>
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-sm">CPU Time (seconds)</Label>
              <div className="flex items-center gap-4">
                <Slider
                  value={[policy.cpu_time_limit_sec]}
                  onValueChange={([value]) => onChange({ ...policy, cpu_time_limit_sec: value })}
                  min={1}
                  max={600}
                  step={5}
                  className="flex-1"
                />
                <span className="text-sm font-mono w-16 text-right">{policy.cpu_time_limit_sec}s</span>
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-sm">Wall Time (seconds)</Label>
              <div className="flex items-center gap-4">
                <Slider
                  value={[policy.wall_time_limit_sec]}
                  onValueChange={([value]) => onChange({ ...policy, wall_time_limit_sec: value })}
                  min={5}
                  max={600}
                  step={5}
                  className="flex-1"
                />
                <span className="text-sm font-mono w-16 text-right">{policy.wall_time_limit_sec}s</span>
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-sm">Max Processes</Label>
              <div className="flex items-center gap-4">
                <Slider
                  value={[policy.max_processes]}
                  onValueChange={([value]) => onChange({ ...policy, max_processes: value })}
                  min={1}
                  max={16}
                  step={1}
                  className="flex-1"
                />
                <span className="text-sm font-mono w-16 text-right">{policy.max_processes}</span>
              </div>
            </div>
          </div>
        </div>

        <Separator />

        {/* Access Permissions */}
        <div className="space-y-4">
          <Label className="flex items-center gap-2">
            <HardDrive className="w-4 h-4" />
            Access Permissions
          </Label>

          <div className="grid grid-cols-3 gap-4">
            <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
              <div className="flex items-center gap-2">
                <Network className="w-4 h-4" />
                <span className="text-sm">Network</span>
              </div>
              <Switch
                checked={policy.network_enabled}
                onCheckedChange={(checked) => onChange({ ...policy, network_enabled: checked })}
              />
            </div>

            <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
              <div className="flex items-center gap-2">
                <HardDrive className="w-4 h-4" />
                <span className="text-sm">File Read</span>
              </div>
              <Switch
                checked={policy.file_read_enabled}
                onCheckedChange={(checked) => onChange({ ...policy, file_read_enabled: checked })}
              />
            </div>

            <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
              <div className="flex items-center gap-2">
                <FileCode className="w-4 h-4" />
                <span className="text-sm">File Write</span>
              </div>
              <Switch
                checked={policy.file_write_enabled}
                onCheckedChange={(checked) => onChange({ ...policy, file_write_enabled: checked })}
              />
            </div>
          </div>
        </div>

        <Separator />

        {/* Module Configuration */}
        <Accordion type="single" collapsible>
          <AccordionItem value="modules">
            <AccordionTrigger>
              <div className="flex items-center gap-2">
                <FileCode className="w-4 h-4" />
                Module Configuration
              </div>
            </AccordionTrigger>
            <AccordionContent className="space-y-4">
              <div className="space-y-2">
                <Label className="text-sm text-green-600">Allowed Modules</Label>
                <Textarea
                  value={policy.allowed_modules.join(', ')}
                  onChange={(e) => onChange({
                    ...policy,
                    allowed_modules: e.target.value.split(',').map(m => m.trim()).filter(Boolean),
                  })}
                  placeholder="math, statistics, json, ..."
                  className="font-mono text-xs"
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onChange({ ...policy, allowed_modules: DEFAULT_ALLOWED_MODULES })}
                >
                  Reset to Defaults
                </Button>
              </div>

              <div className="space-y-2">
                <Label className="text-sm text-red-600">Blocked Modules</Label>
                <Textarea
                  value={policy.blocked_modules.join(', ')}
                  onChange={(e) => onChange({
                    ...policy,
                    blocked_modules: e.target.value.split(',').map(m => m.trim()).filter(Boolean),
                  })}
                  placeholder="os, sys, subprocess, ..."
                  className="font-mono text-xs"
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onChange({ ...policy, blocked_modules: DEFAULT_BLOCKED_MODULES })}
                >
                  Reset to Defaults
                </Button>
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </CardContent>
    </Card>
  )
}

// Add Signer Dialog Component
function AddSignerDialog({
  open,
  onOpenChange,
  onAdd,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  onAdd: (signer: Partial<TrustedSigner>) => void
}) {
  const [name, setName] = useState('')
  const [organization, setOrganization] = useState('')
  const [email, setEmail] = useState('')
  const [publicKey, setPublicKey] = useState('')
  const [algorithm, setAlgorithm] = useState('ed25519')
  const [trustLevel, setTrustLevel] = useState('verified')

  const handleSubmit = () => {
    if (!name || !publicKey) {
      toast({ title: 'Name and public key are required', variant: 'destructive' })
      return
    }
    onAdd({
      name,
      organization: organization || undefined,
      email: email || undefined,
      public_key: publicKey,
      algorithm,
      trust_level: trustLevel,
    })
    // Reset form
    setName('')
    setOrganization('')
    setEmail('')
    setPublicKey('')
    setAlgorithm('ed25519')
    setTrustLevel('verified')
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Add Trusted Signer</DialogTitle>
          <DialogDescription>
            Add a new trusted signing key for plugin verification
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Signer Name *</Label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Official Maintainer"
              />
            </div>
            <div className="space-y-2">
              <Label>Organization</Label>
              <Input
                value={organization}
                onChange={(e) => setOrganization(e.target.value)}
                placeholder="Acme Corp"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Email</Label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="signer@example.com"
            />
          </div>

          <div className="space-y-2">
            <Label>Public Key (PEM) *</Label>
            <Textarea
              value={publicKey}
              onChange={(e) => setPublicKey(e.target.value)}
              placeholder="-----BEGIN PUBLIC KEY-----&#10;...&#10;-----END PUBLIC KEY-----"
              className="font-mono text-xs h-32"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Algorithm</Label>
              <Select value={algorithm} onValueChange={setAlgorithm}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ed25519">Ed25519 (Recommended)</SelectItem>
                  <SelectItem value="rsa_sha256">RSA-SHA256</SelectItem>
                  <SelectItem value="hmac_sha256">HMAC-SHA256</SelectItem>
                  <SelectItem value="hmac_sha512">HMAC-SHA512</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Trust Level</Label>
              <Select value={trustLevel} onValueChange={setTrustLevel}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="trusted">Trusted</SelectItem>
                  <SelectItem value="verified">Verified</SelectItem>
                  <SelectItem value="unverified">Unverified</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit}>
            Add Signer
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// Main Component
export function PluginSettingsTab() {
  const [trustedSigners, setTrustedSigners] = useState<TrustedSigner[]>([])
  const [loadingSigners, setLoadingSigners] = useState(true)
  const [policy, setPolicy] = useState<SecurityPolicy>({
    id: '',
    name: 'standard',
    description: 'Standard security policy',
    is_default: true,
    is_active: true,
    isolation_level: 'process',
    memory_limit_mb: 256,
    cpu_time_limit_sec: 30,
    wall_time_limit_sec: 60,
    network_enabled: false,
    file_read_enabled: true,
    file_write_enabled: false,
    allowed_modules: DEFAULT_ALLOWED_MODULES,
    blocked_modules: DEFAULT_BLOCKED_MODULES,
    require_signature: false,
    min_trust_level: 'verified',
    max_processes: 1,
    container_image: 'python:3.11-slim',
  })
  const [savingPolicy, setSavingPolicy] = useState(false)
  const [showAddSigner, setShowAddSigner] = useState(false)

  // Load data
  useEffect(() => {
    const loadData = async () => {
      try {
        // Mock data - in production, call actual API
        setTrustedSigners([
          {
            id: '1',
            signer_id: 'official@truthound.io',
            name: 'Truthound Official',
            organization: 'Truthound',
            email: 'security@truthound.io',
            public_key: '-----BEGIN PUBLIC KEY-----\nMCowBQYDK2VwAyEA...\n-----END PUBLIC KEY-----',
            algorithm: 'ed25519',
            fingerprint: 'SHA256:abc123...',
            trust_level: 'trusted',
            plugins_signed: 12,
            added_at: new Date().toISOString(),
            is_active: true,
          },
        ])
      } finally {
        setLoadingSigners(false)
      }
    }
    loadData()
  }, [])

  const handleAddSigner = async (signer: Partial<TrustedSigner>) => {
    // In production, call actual API
    const newSigner: TrustedSigner = {
      id: Date.now().toString(),
      signer_id: signer.email || `signer-${Date.now()}`,
      name: signer.name || '',
      organization: signer.organization,
      email: signer.email,
      public_key: signer.public_key || '',
      algorithm: signer.algorithm || 'ed25519',
      fingerprint: `SHA256:${Math.random().toString(36).substring(2, 10)}...`,
      trust_level: signer.trust_level || 'verified',
      plugins_signed: 0,
      added_at: new Date().toISOString(),
      is_active: true,
    }
    setTrustedSigners((prev) => [...prev, newSigner])
    toast({ title: 'Signer added successfully' })
  }

  const handleRemoveSigner = async (id: string) => {
    if (!confirm('Are you sure you want to remove this signer?')) return
    setTrustedSigners((prev) => prev.filter((s) => s.id !== id))
    toast({ title: 'Signer removed' })
  }

  const handleRevokeSigner = async (id: string) => {
    if (!confirm('Are you sure you want to revoke this signer? This cannot be undone.')) return
    setTrustedSigners((prev) =>
      prev.map((s) =>
        s.id === id ? { ...s, trust_level: 'revoked', is_active: false } : s
      )
    )
    toast({ title: 'Signer revoked', description: 'The signer can no longer be used for verification.' })
  }

  const handleSavePolicy = async () => {
    setSavingPolicy(true)
    try {
      // In production, call actual API
      await new Promise((resolve) => setTimeout(resolve, 500))
      toast({ title: 'Security policy saved' })
    } catch {
      toast({ title: 'Failed to save policy', variant: 'destructive' })
    } finally {
      setSavingPolicy(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Security Overview */}
      <Alert>
        <Info className="w-4 h-4" />
        <AlertTitle>Plugin Security</AlertTitle>
        <AlertDescription>
          Configure global security settings for plugin execution. These settings apply to all
          plugins unless overridden at the plugin level.
        </AlertDescription>
      </Alert>

      {/* Trust Store */}
      <TrustStoreCard
        signers={trustedSigners}
        onAdd={() => setShowAddSigner(true)}
        onRemove={handleRemoveSigner}
        onRevoke={handleRevokeSigner}
        loading={loadingSigners}
      />

      {/* Security Policy */}
      <SecurityPolicyCard
        policy={policy}
        onChange={setPolicy}
        onSave={handleSavePolicy}
        saving={savingPolicy}
      />

      {/* Add Signer Dialog */}
      <AddSignerDialog
        open={showAddSigner}
        onOpenChange={setShowAddSigner}
        onAdd={handleAddSigner}
      />
    </div>
  )
}

export default PluginSettingsTab
