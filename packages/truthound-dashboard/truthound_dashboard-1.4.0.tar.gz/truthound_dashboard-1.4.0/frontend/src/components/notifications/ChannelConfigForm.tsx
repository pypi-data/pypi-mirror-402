/**
 * ChannelConfigForm - Dynamic configuration form for all notification channel types.
 *
 * Supports all 9 channel types with extensible schema-driven architecture:
 * - Slack, Email, Webhook (basic)
 * - Discord, Telegram, PagerDuty, OpsGenie, Teams, GitHub (advanced)
 *
 * Features:
 * - Schema-driven form generation
 * - Type-safe configuration
 * - Secret field masking
 * - Validation
 * - i18n support
 */

import { useState, useEffect, useMemo, useCallback } from 'react'
import {
  MessageSquare,
  Mail,
  Webhook,
  Bell,
  Send,
  Github,
  AlertTriangle,
  Eye,
  EyeOff,
  Info,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
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
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

// ============================================================================
// Types
// ============================================================================

export type ChannelType =
  | 'slack'
  | 'email'
  | 'webhook'
  | 'discord'
  | 'telegram'
  | 'pagerduty'
  | 'opsgenie'
  | 'teams'
  | 'github'

export interface FieldSchema {
  type: 'string' | 'number' | 'boolean' | 'select' | 'array' | 'textarea'
  required?: boolean
  secret?: boolean
  description?: string
  placeholder?: string
  default?: unknown
  options?: { value: string; label: string }[]
  min?: number
  max?: number
  pattern?: string
  validate?: (value: unknown) => string | null
}

export interface ChannelSchema {
  type: ChannelType
  name: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  color: string
  fields: Record<string, FieldSchema>
  category: 'basic' | 'chat' | 'incident' | 'devops'
}

export interface ChannelConfig {
  [key: string]: unknown
}

export interface ChannelConfigFormProps {
  channelType: ChannelType
  config: ChannelConfig
  onChange: (config: ChannelConfig) => void
  onValidChange?: (isValid: boolean) => void
  disabled?: boolean
  showSecrets?: boolean
  className?: string
}

// ============================================================================
// Channel Schemas (Extensible Registry)
// ============================================================================

const CHANNEL_SCHEMAS: Record<ChannelType, ChannelSchema> = {
  slack: {
    type: 'slack',
    name: 'Slack',
    description: 'Send notifications to Slack channels via webhooks',
    icon: MessageSquare,
    color: '#4A154B',
    category: 'chat',
    fields: {
      webhook_url: {
        type: 'string',
        required: true,
        secret: true,
        description: 'Slack Incoming Webhook URL',
        placeholder: 'https://hooks.slack.com/services/T.../B.../...',
        pattern: '^https://hooks\\.slack\\.com/.*',
      },
      channel: {
        type: 'string',
        required: false,
        description: 'Override channel (optional, e.g., #alerts)',
        placeholder: '#data-quality-alerts',
      },
      username: {
        type: 'string',
        required: false,
        description: 'Bot username',
        placeholder: 'Truthound Bot',
        default: 'Truthound',
      },
      icon_emoji: {
        type: 'string',
        required: false,
        description: 'Bot icon emoji',
        placeholder: ':bar_chart:',
        default: ':bar_chart:',
      },
    },
  },

  email: {
    type: 'email',
    name: 'Email',
    description: 'Send notifications via SMTP email',
    icon: Mail,
    color: '#EA4335',
    category: 'basic',
    fields: {
      smtp_host: {
        type: 'string',
        required: true,
        description: 'SMTP server hostname',
        placeholder: 'smtp.gmail.com',
      },
      smtp_port: {
        type: 'number',
        required: true,
        description: 'SMTP server port',
        placeholder: '587',
        default: 587,
        min: 1,
        max: 65535,
      },
      smtp_user: {
        type: 'string',
        required: true,
        description: 'SMTP username/email',
        placeholder: 'alerts@example.com',
      },
      smtp_password: {
        type: 'string',
        required: true,
        secret: true,
        description: 'SMTP password or app-specific password',
        placeholder: '••••••••',
      },
      from_email: {
        type: 'string',
        required: true,
        description: 'Sender email address',
        placeholder: 'alerts@example.com',
      },
      recipients: {
        type: 'textarea',
        required: true,
        description: 'Recipient email addresses (one per line)',
        placeholder: 'user1@example.com\nuser2@example.com',
      },
      use_tls: {
        type: 'boolean',
        required: false,
        description: 'Use TLS encryption',
        default: true,
      },
    },
  },

  webhook: {
    type: 'webhook',
    name: 'Webhook',
    description: 'Send notifications to custom HTTP endpoints',
    icon: Webhook,
    color: '#6366F1',
    category: 'basic',
    fields: {
      url: {
        type: 'string',
        required: true,
        description: 'Webhook endpoint URL',
        placeholder: 'https://api.example.com/webhooks/notify',
        pattern: '^https?://.*',
      },
      method: {
        type: 'select',
        required: true,
        description: 'HTTP method',
        default: 'POST',
        options: [
          { value: 'POST', label: 'POST' },
          { value: 'PUT', label: 'PUT' },
          { value: 'GET', label: 'GET' },
        ],
      },
      headers: {
        type: 'textarea',
        required: false,
        description: 'Custom headers (JSON format)',
        placeholder: '{"Authorization": "Bearer token", "X-Custom": "value"}',
      },
      include_event_data: {
        type: 'boolean',
        required: false,
        description: 'Include full event data in payload',
        default: true,
      },
    },
  },

  discord: {
    type: 'discord',
    name: 'Discord',
    description: 'Send notifications to Discord channels via webhooks',
    icon: MessageSquare,
    color: '#5865F2',
    category: 'chat',
    fields: {
      webhook_url: {
        type: 'string',
        required: true,
        secret: true,
        description: 'Discord Webhook URL',
        placeholder: 'https://discord.com/api/webhooks/...',
        pattern: '^https://discord\\.com/api/webhooks/.*',
      },
      username: {
        type: 'string',
        required: false,
        description: 'Bot username',
        placeholder: 'Truthound Bot',
        default: 'Truthound',
      },
      avatar_url: {
        type: 'string',
        required: false,
        description: 'Bot avatar URL',
        placeholder: 'https://example.com/avatar.png',
      },
    },
  },

  telegram: {
    type: 'telegram',
    name: 'Telegram',
    description: 'Send notifications via Telegram Bot API',
    icon: Send,
    color: '#0088CC',
    category: 'chat',
    fields: {
      bot_token: {
        type: 'string',
        required: true,
        secret: true,
        description: 'Telegram Bot Token (from @BotFather)',
        placeholder: '123456789:ABCdefGHIjklMNOpqrsTUVwxyz',
      },
      chat_id: {
        type: 'string',
        required: true,
        description: 'Chat ID (user, group, or channel)',
        placeholder: '-1001234567890',
      },
      parse_mode: {
        type: 'select',
        required: false,
        description: 'Message format',
        default: 'HTML',
        options: [
          { value: 'HTML', label: 'HTML' },
          { value: 'MarkdownV2', label: 'Markdown V2' },
        ],
      },
      disable_notification: {
        type: 'boolean',
        required: false,
        description: 'Send silently (no notification sound)',
        default: false,
      },
    },
  },

  pagerduty: {
    type: 'pagerduty',
    name: 'PagerDuty',
    description: 'Create incidents in PagerDuty for critical alerts',
    icon: AlertTriangle,
    color: '#06AC38',
    category: 'incident',
    fields: {
      routing_key: {
        type: 'string',
        required: true,
        secret: true,
        description: 'Events API v2 Integration Key (Routing Key)',
        placeholder: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
      },
      severity: {
        type: 'select',
        required: false,
        description: 'Default severity (can be overridden by event)',
        default: 'error',
        options: [
          { value: 'critical', label: 'Critical' },
          { value: 'error', label: 'Error' },
          { value: 'warning', label: 'Warning' },
          { value: 'info', label: 'Info' },
        ],
      },
      component: {
        type: 'string',
        required: false,
        description: 'Component name for grouping',
        placeholder: 'data-quality',
      },
      group: {
        type: 'string',
        required: false,
        description: 'Logical grouping',
        placeholder: 'production',
      },
      class_type: {
        type: 'string',
        required: false,
        description: 'Class/type of the event',
        placeholder: 'validation_failure',
      },
    },
  },

  opsgenie: {
    type: 'opsgenie',
    name: 'OpsGenie',
    description: 'Create alerts in OpsGenie for incident management',
    icon: Bell,
    color: '#2684FF',
    category: 'incident',
    fields: {
      api_key: {
        type: 'string',
        required: true,
        secret: true,
        description: 'OpsGenie API Key',
        placeholder: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
      },
      priority: {
        type: 'select',
        required: false,
        description: 'Default priority (can be overridden by event)',
        default: 'P3',
        options: [
          { value: 'P1', label: 'P1 - Critical' },
          { value: 'P2', label: 'P2 - High' },
          { value: 'P3', label: 'P3 - Moderate' },
          { value: 'P4', label: 'P4 - Low' },
          { value: 'P5', label: 'P5 - Informational' },
        ],
      },
      tags: {
        type: 'string',
        required: false,
        description: 'Tags (comma-separated)',
        placeholder: 'data-quality, production, critical',
      },
      team: {
        type: 'string',
        required: false,
        description: 'Default team to assign alerts',
        placeholder: 'data-platform',
      },
      responders: {
        type: 'textarea',
        required: false,
        description: 'Additional responders (JSON format)',
        placeholder: '[{"type": "user", "username": "john@example.com"}]',
      },
    },
  },

  teams: {
    type: 'teams',
    name: 'Microsoft Teams',
    description: 'Send notifications to Microsoft Teams channels',
    icon: MessageSquare,
    color: '#6264A7',
    category: 'chat',
    fields: {
      webhook_url: {
        type: 'string',
        required: true,
        secret: true,
        description: 'Teams Incoming Webhook URL',
        placeholder: 'https://outlook.office.com/webhook/...',
        pattern: '^https://.*\\.office\\.com/.*',
      },
      theme_color: {
        type: 'string',
        required: false,
        description: 'Card theme color (hex)',
        placeholder: '#fd9e4b',
        default: '#fd9e4b',
      },
    },
  },

  github: {
    type: 'github',
    name: 'GitHub',
    description: 'Create issues in GitHub repositories for tracking',
    icon: Github,
    color: '#24292E',
    category: 'devops',
    fields: {
      token: {
        type: 'string',
        required: true,
        secret: true,
        description: 'GitHub Personal Access Token (repo scope)',
        placeholder: 'ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
      },
      owner: {
        type: 'string',
        required: true,
        description: 'Repository owner (username or org)',
        placeholder: 'my-organization',
      },
      repo: {
        type: 'string',
        required: true,
        description: 'Repository name',
        placeholder: 'data-quality-issues',
      },
      labels: {
        type: 'string',
        required: false,
        description: 'Issue labels (comma-separated)',
        placeholder: 'data-quality, automated, truthound',
      },
      assignees: {
        type: 'string',
        required: false,
        description: 'Auto-assign to users (comma-separated)',
        placeholder: 'user1, user2',
      },
    },
  },
}

// ============================================================================
// Helper Functions
// ============================================================================

export function getChannelSchema(type: ChannelType): ChannelSchema {
  return CHANNEL_SCHEMAS[type]
}

export function getAllChannelSchemas(): ChannelSchema[] {
  return Object.values(CHANNEL_SCHEMAS)
}

export function getChannelsByCategory(category: ChannelSchema['category']): ChannelSchema[] {
  return Object.values(CHANNEL_SCHEMAS).filter((s) => s.category === category)
}

export function getChannelIcon(type: ChannelType): React.ComponentType<{ className?: string }> {
  return CHANNEL_SCHEMAS[type]?.icon || Bell
}

export function getChannelColor(type: ChannelType): string {
  return CHANNEL_SCHEMAS[type]?.color || '#6B7280'
}

// ============================================================================
// Form Field Components
// ============================================================================

interface FieldProps {
  name: string
  schema: FieldSchema
  value: unknown
  onChange: (value: unknown) => void
  disabled?: boolean
  showSecret?: boolean
  onToggleSecret?: () => void
  error?: string | null
  translations: {
    required: string
    optional: string
  }
}

function FormField({
  name,
  schema,
  value,
  onChange,
  disabled,
  showSecret,
  onToggleSecret,
  error,
  translations,
}: FieldProps) {
  const fieldLabel = name
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label htmlFor={name} className="flex items-center gap-2">
          {fieldLabel}
          {schema.required ? (
            <Badge variant="outline" className="text-xs text-red-500 border-red-500/30">
              {translations.required}
            </Badge>
          ) : (
            <Badge variant="outline" className="text-xs text-muted-foreground">
              {translations.optional}
            </Badge>
          )}
        </Label>
        {schema.description && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Info className="h-4 w-4 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent side="left" className="max-w-xs">
                {schema.description}
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>

      {schema.type === 'string' && (
        <div className="relative">
          <Input
            id={name}
            type={schema.secret && !showSecret ? 'password' : 'text'}
            value={(value as string) || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={schema.placeholder}
            disabled={disabled}
            className={cn(error && 'border-red-500')}
          />
          {schema.secret && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="absolute right-0 top-0 h-full px-3"
              onClick={onToggleSecret}
            >
              {showSecret ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </Button>
          )}
        </div>
      )}

      {schema.type === 'number' && (
        <Input
          id={name}
          type="number"
          value={(value as number) ?? schema.default ?? ''}
          onChange={(e) => onChange(e.target.value ? Number(e.target.value) : undefined)}
          placeholder={schema.placeholder}
          disabled={disabled}
          min={schema.min}
          max={schema.max}
          className={cn(error && 'border-red-500')}
        />
      )}

      {schema.type === 'boolean' && (
        <div className="flex items-center space-x-2">
          <Switch
            id={name}
            checked={(value as boolean) ?? (schema.default as boolean) ?? false}
            onCheckedChange={(checked) => onChange(checked)}
            disabled={disabled}
          />
          <Label htmlFor={name} className="text-sm text-muted-foreground">
            {schema.description}
          </Label>
        </div>
      )}

      {schema.type === 'select' && (
        <Select
          value={(value as string) || (schema.default as string)}
          onValueChange={(val) => onChange(val)}
          disabled={disabled}
        >
          <SelectTrigger className={cn(error && 'border-red-500')}>
            <SelectValue placeholder="Select..." />
          </SelectTrigger>
          <SelectContent>
            {schema.options?.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

      {schema.type === 'textarea' && (
        <Textarea
          id={name}
          value={(value as string) || ''}
          onChange={(e) => onChange(e.target.value)}
          placeholder={schema.placeholder}
          disabled={disabled}
          rows={3}
          className={cn(error && 'border-red-500')}
        />
      )}

      {schema.type === 'array' && (
        <Textarea
          id={name}
          value={Array.isArray(value) ? value.join('\n') : ''}
          onChange={(e) => onChange(e.target.value.split('\n').filter((v) => v.trim()))}
          placeholder={schema.placeholder}
          disabled={disabled}
          rows={3}
          className={cn(error && 'border-red-500')}
        />
      )}

      {error && <p className="text-sm text-red-500">{error}</p>}
    </div>
  )
}

// ============================================================================
// Main Component
// ============================================================================

export function ChannelConfigForm({
  channelType,
  config,
  onChange,
  onValidChange,
  disabled = false,
  showSecrets: initialShowSecrets = false,
  className,
}: ChannelConfigFormProps) {
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({})
  const [errors, setErrors] = useState<Record<string, string | null>>({})

  const schema = useMemo(() => getChannelSchema(channelType), [channelType])

  // Validate all fields
  const validate = useCallback(() => {
    const newErrors: Record<string, string | null> = {}
    let isValid = true

    for (const [fieldName, fieldSchema] of Object.entries(schema.fields)) {
      const value = config[fieldName]

      // Required check
      if (fieldSchema.required) {
        if (value === undefined || value === null || value === '') {
          newErrors[fieldName] = 'This field is required'
          isValid = false
          continue
        }
      }

      // Pattern check
      if (fieldSchema.pattern && typeof value === 'string' && value) {
        const regex = new RegExp(fieldSchema.pattern)
        if (!regex.test(value)) {
          newErrors[fieldName] = 'Invalid format'
          isValid = false
          continue
        }
      }

      // Number range check
      if (fieldSchema.type === 'number' && typeof value === 'number') {
        if (fieldSchema.min !== undefined && value < fieldSchema.min) {
          newErrors[fieldName] = `Minimum value is ${fieldSchema.min}`
          isValid = false
          continue
        }
        if (fieldSchema.max !== undefined && value > fieldSchema.max) {
          newErrors[fieldName] = `Maximum value is ${fieldSchema.max}`
          isValid = false
          continue
        }
      }

      // Custom validator
      if (fieldSchema.validate) {
        const error = fieldSchema.validate(value)
        if (error) {
          newErrors[fieldName] = error
          isValid = false
          continue
        }
      }

      newErrors[fieldName] = null
    }

    setErrors(newErrors)
    return isValid
  }, [config, schema.fields])

  // Validate on config change
  useEffect(() => {
    const isValid = validate()
    onValidChange?.(isValid)
  }, [config, validate, onValidChange])

  const handleFieldChange = (fieldName: string, value: unknown) => {
    const newConfig = { ...config, [fieldName]: value }
    onChange(newConfig)
  }

  const toggleSecretVisibility = (fieldName: string) => {
    setShowSecrets((prev) => ({ ...prev, [fieldName]: !prev[fieldName] }))
  }

  const Icon = schema.icon

  return (
    <div className={cn('space-y-6', className)}>
      {/* Channel Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div
          className="p-2 rounded-lg"
          style={{ backgroundColor: `${schema.color}20` }}
        >
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <h3 className="font-semibold">{schema.name}</h3>
          <p className="text-sm text-muted-foreground">{schema.description}</p>
        </div>
      </div>

      {/* Form Fields */}
      <div className="space-y-4">
        {Object.entries(schema.fields).map(([fieldName, fieldSchema]) => (
          <FormField
            key={fieldName}
            name={fieldName}
            schema={fieldSchema}
            value={config[fieldName]}
            onChange={(value) => handleFieldChange(fieldName, value)}
            disabled={disabled}
            showSecret={initialShowSecrets || showSecrets[fieldName]}
            onToggleSecret={() => toggleSecretVisibility(fieldName)}
            error={errors[fieldName]}
            translations={{
              required: 'Required',
              optional: 'Optional',
            }}
          />
        ))}
      </div>
    </div>
  )
}

// ============================================================================
// Channel Type Selector Component
// ============================================================================

interface ChannelTypeSelectorProps {
  value: ChannelType | null
  onChange: (type: ChannelType) => void
  disabled?: boolean
  className?: string
}

export function ChannelTypeSelector({
  value,
  onChange,
  disabled = false,
  className,
}: ChannelTypeSelectorProps) {
  const categories = [
    { id: 'basic', label: 'Basic' },
    { id: 'chat', label: 'Chat' },
    { id: 'incident', label: 'Incident Management' },
    { id: 'devops', label: 'DevOps' },
  ] as const

  return (
    <div className={cn('space-y-4', className)}>
      {categories.map((category) => {
        const channels = getChannelsByCategory(category.id)
        if (channels.length === 0) return null

        return (
          <div key={category.id}>
            <Label className="text-sm text-muted-foreground mb-2 block">
              {category.label}
            </Label>
            <div className="grid grid-cols-3 gap-2">
              {channels.map((schema) => {
                const Icon = schema.icon
                const isSelected = value === schema.type

                return (
                  <Button
                    key={schema.type}
                    type="button"
                    variant={isSelected ? 'default' : 'outline'}
                    className={cn(
                      'h-auto py-3 px-3 flex flex-col items-center gap-2',
                      isSelected && 'ring-2 ring-primary'
                    )}
                    onClick={() => onChange(schema.type)}
                    disabled={disabled}
                  >
                    <div
                      className="p-2 rounded-lg"
                      style={{
                        backgroundColor: isSelected ? 'white' : `${schema.color}20`,
                      }}
                    >
                      <Icon className="h-5 w-5" />
                    </div>
                    <span className="text-xs font-medium">{schema.name}</span>
                  </Button>
                )
              })}
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ============================================================================
// Exports
// ============================================================================

export { CHANNEL_SCHEMAS }
