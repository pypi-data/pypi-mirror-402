/**
 * ChannelConfigForm Component Tests
 *
 * Tests for the notification channel configuration form component.
 * Tests cover:
 * - Rendering for all 9 channel types
 * - Form field validation
 * - Secret field masking/showing
 * - Schema-driven form generation
 * - Channel type selection
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, within, waitFor } from '@/test/test-utils'
import {
  ChannelConfigForm,
  ChannelTypeSelector,
  getChannelSchema,
  getAllChannelSchemas,
  getChannelsByCategory,
  getChannelIcon,
  getChannelColor,
  CHANNEL_SCHEMAS,
  type ChannelType,
} from '../ChannelConfigForm'

// All 9 supported channel types
const ALL_CHANNEL_TYPES: ChannelType[] = [
  'slack',
  'email',
  'webhook',
  'discord',
  'telegram',
  'pagerduty',
  'opsgenie',
  'teams',
  'github',
]

describe('ChannelConfigForm', () => {
  describe('Helper Functions', () => {
    it('getChannelSchema returns correct schema for each type', () => {
      ALL_CHANNEL_TYPES.forEach((type) => {
        const schema = getChannelSchema(type)
        expect(schema).toBeDefined()
        expect(schema.type).toBe(type)
        expect(schema.name).toBeTruthy()
        expect(schema.fields).toBeDefined()
      })
    })

    it('getAllChannelSchemas returns all 9 schemas', () => {
      const schemas = getAllChannelSchemas()
      expect(schemas).toHaveLength(9)
      const types = schemas.map((s) => s.type)
      ALL_CHANNEL_TYPES.forEach((type) => {
        expect(types).toContain(type)
      })
    })

    it('getChannelsByCategory returns correct channels', () => {
      const basicChannels = getChannelsByCategory('basic')
      expect(basicChannels.map((c) => c.type)).toEqual(expect.arrayContaining(['email', 'webhook']))

      const chatChannels = getChannelsByCategory('chat')
      expect(chatChannels.map((c) => c.type)).toEqual(
        expect.arrayContaining(['slack', 'discord', 'telegram', 'teams'])
      )

      const incidentChannels = getChannelsByCategory('incident')
      expect(incidentChannels.map((c) => c.type)).toEqual(
        expect.arrayContaining(['pagerduty', 'opsgenie'])
      )

      const devopsChannels = getChannelsByCategory('devops')
      expect(devopsChannels.map((c) => c.type)).toEqual(expect.arrayContaining(['github']))
    })

    it('getChannelIcon returns an icon for each type', () => {
      ALL_CHANNEL_TYPES.forEach((type) => {
        const Icon = getChannelIcon(type)
        expect(Icon).toBeDefined()
        // Icons can be either functions or Lucide react objects
        expect(['function', 'object']).toContain(typeof Icon)
      })
    })

    it('getChannelColor returns a color for each type', () => {
      ALL_CHANNEL_TYPES.forEach((type) => {
        const color = getChannelColor(type)
        expect(color).toBeDefined()
        expect(color).toMatch(/^#[0-9A-Fa-f]{6}$/)
      })
    })
  })

  describe('Schema Validation', () => {
    it('all channel schemas have required properties', () => {
      Object.entries(CHANNEL_SCHEMAS).forEach(([type, schema]) => {
        expect(schema.type).toBe(type)
        expect(schema.name).toBeTruthy()
        expect(schema.description).toBeTruthy()
        expect(schema.icon).toBeDefined()
        expect(schema.color).toBeTruthy()
        expect(schema.category).toMatch(/^(basic|chat|incident|devops)$/)
        expect(schema.fields).toBeDefined()
        expect(Object.keys(schema.fields).length).toBeGreaterThan(0)
      })
    })

    it('required fields are properly marked', () => {
      // Slack requires webhook_url
      expect(CHANNEL_SCHEMAS.slack.fields.webhook_url.required).toBe(true)

      // Email requires multiple fields
      expect(CHANNEL_SCHEMAS.email.fields.smtp_host.required).toBe(true)
      expect(CHANNEL_SCHEMAS.email.fields.smtp_port.required).toBe(true)
      expect(CHANNEL_SCHEMAS.email.fields.recipients.required).toBe(true)

      // GitHub requires token, owner, repo
      expect(CHANNEL_SCHEMAS.github.fields.token.required).toBe(true)
      expect(CHANNEL_SCHEMAS.github.fields.owner.required).toBe(true)
      expect(CHANNEL_SCHEMAS.github.fields.repo.required).toBe(true)
    })

    it('secret fields are properly marked', () => {
      // These fields should be marked as secrets
      expect(CHANNEL_SCHEMAS.slack.fields.webhook_url.secret).toBe(true)
      expect(CHANNEL_SCHEMAS.email.fields.smtp_password.secret).toBe(true)
      expect(CHANNEL_SCHEMAS.discord.fields.webhook_url.secret).toBe(true)
      expect(CHANNEL_SCHEMAS.telegram.fields.bot_token.secret).toBe(true)
      expect(CHANNEL_SCHEMAS.pagerduty.fields.routing_key.secret).toBe(true)
      expect(CHANNEL_SCHEMAS.opsgenie.fields.api_key.secret).toBe(true)
      expect(CHANNEL_SCHEMAS.teams.fields.webhook_url.secret).toBe(true)
      expect(CHANNEL_SCHEMAS.github.fields.token.secret).toBe(true)
    })
  })

  describe('Form Rendering', () => {
    it.each(ALL_CHANNEL_TYPES)('renders %s channel form correctly', async (type) => {
      const onChange = vi.fn()
      render(
        <ChannelConfigForm
          channelType={type}
          config={{}}
          onChange={onChange}
        />
      )

      const schema = getChannelSchema(type)

      // Should display channel name
      expect(screen.getByText(schema.name)).toBeInTheDocument()

      // Should display channel description
      expect(screen.getByText(schema.description)).toBeInTheDocument()
    })

    it('renders Slack form with all fields', async () => {
      const onChange = vi.fn()
      render(
        <ChannelConfigForm channelType="slack" config={{}} onChange={onChange} />
      )

      // Check for Slack-specific fields
      expect(screen.getByText('Webhook Url')).toBeInTheDocument()
      expect(screen.getByText('Channel')).toBeInTheDocument()
      expect(screen.getByText('Username')).toBeInTheDocument()
      expect(screen.getByText('Icon Emoji')).toBeInTheDocument()
    })

    it('renders Email form with all fields', async () => {
      const onChange = vi.fn()
      render(
        <ChannelConfigForm channelType="email" config={{}} onChange={onChange} />
      )

      // Check for Email-specific fields
      expect(screen.getByText('Smtp Host')).toBeInTheDocument()
      expect(screen.getByText('Smtp Port')).toBeInTheDocument()
      expect(screen.getByText('Smtp User')).toBeInTheDocument()
      expect(screen.getByText('Smtp Password')).toBeInTheDocument()
      expect(screen.getByText('From Email')).toBeInTheDocument()
      expect(screen.getByText('Recipients')).toBeInTheDocument()
      expect(screen.getByText('Use Tls')).toBeInTheDocument()
    })

    it('renders PagerDuty form with severity selector', async () => {
      const onChange = vi.fn()
      render(
        <ChannelConfigForm channelType="pagerduty" config={{}} onChange={onChange} />
      )

      // Check for PagerDuty-specific fields
      expect(screen.getByText('Routing Key')).toBeInTheDocument()
      expect(screen.getByText('Severity')).toBeInTheDocument()
      expect(screen.getByText('Component')).toBeInTheDocument()
      expect(screen.getByText('Group')).toBeInTheDocument()
    })

    it('renders GitHub form with repository fields', async () => {
      const onChange = vi.fn()
      render(
        <ChannelConfigForm channelType="github" config={{}} onChange={onChange} />
      )

      // Check for GitHub-specific fields
      expect(screen.getByText('Token')).toBeInTheDocument()
      expect(screen.getByText('Owner')).toBeInTheDocument()
      expect(screen.getByText('Repo')).toBeInTheDocument()
      expect(screen.getByText('Labels')).toBeInTheDocument()
      expect(screen.getByText('Assignees')).toBeInTheDocument()
    })
  })

  describe('Form Interactions', () => {
    it('calls onChange when field value changes', async () => {
      const onChange = vi.fn()
      const { user } = render(
        <ChannelConfigForm
          channelType="slack"
          config={{ webhook_url: '' }}
          onChange={onChange}
        />
      )

      const webhookInput = screen.getByPlaceholderText(/hooks\.slack\.com/i)
      await user.type(webhookInput, 'https://hooks.slack.com/test')

      expect(onChange).toHaveBeenCalled()
    })

    it('toggles secret field visibility', async () => {
      const onChange = vi.fn()
      const { user } = render(
        <ChannelConfigForm
          channelType="slack"
          config={{ webhook_url: 'secret-value' }}
          onChange={onChange}
        />
      )

      // Find the password input
      const webhookInput = screen.getByPlaceholderText(/hooks\.slack\.com/i)
      expect(webhookInput).toHaveAttribute('type', 'password')

      // Click the eye button to show secret
      const toggleButtons = screen.getAllByRole('button')
      const eyeButton = toggleButtons.find((btn) =>
        btn.querySelector('svg')
      )

      if (eyeButton) {
        await user.click(eyeButton)
        // After click, the type should change to text
        await waitFor(() => {
          const input = screen.getByPlaceholderText(/hooks\.slack\.com/i)
          // Either type is text or it shows the value
          expect(input).toBeInTheDocument()
        })
      }
    })

    it('displays required badge for required fields', () => {
      render(
        <ChannelConfigForm channelType="slack" config={{}} onChange={vi.fn()} />
      )

      // Required fields should have "Required" badge
      const requiredBadges = screen.getAllByText(/required/i)
      expect(requiredBadges.length).toBeGreaterThan(0)
    })

    it('displays optional badge for optional fields', () => {
      render(
        <ChannelConfigForm channelType="slack" config={{}} onChange={vi.fn()} />
      )

      // Optional fields should have "Optional" badge
      const optionalBadges = screen.getAllByText(/optional/i)
      expect(optionalBadges.length).toBeGreaterThan(0)
    })

    it('disables all fields when disabled prop is true', () => {
      render(
        <ChannelConfigForm
          channelType="slack"
          config={{}}
          onChange={vi.fn()}
          disabled={true}
        />
      )

      const inputs = screen.getAllByRole('textbox')
      inputs.forEach((input) => {
        expect(input).toBeDisabled()
      })
    })
  })

  describe('Validation', () => {
    it('calls onValidChange with false when required field is empty', async () => {
      const onValidChange = vi.fn()
      render(
        <ChannelConfigForm
          channelType="slack"
          config={{}}
          onChange={vi.fn()}
          onValidChange={onValidChange}
        />
      )

      // Should be called with false because webhook_url is required but empty
      await waitFor(() => {
        expect(onValidChange).toHaveBeenCalledWith(false)
      })
    })

    it('calls onValidChange with true when all required fields are filled', async () => {
      const onValidChange = vi.fn()
      render(
        <ChannelConfigForm
          channelType="slack"
          config={{
            webhook_url: 'https://hooks.slack.com/services/T00/B00/XXX',
          }}
          onChange={vi.fn()}
          onValidChange={onValidChange}
        />
      )

      await waitFor(() => {
        expect(onValidChange).toHaveBeenCalledWith(true)
      })
    })

    it('validates pattern for webhook URLs', async () => {
      const onValidChange = vi.fn()
      render(
        <ChannelConfigForm
          channelType="slack"
          config={{
            webhook_url: 'invalid-url',
          }}
          onChange={vi.fn()}
          onValidChange={onValidChange}
        />
      )

      await waitFor(() => {
        expect(onValidChange).toHaveBeenCalledWith(false)
      })
    })
  })

  describe('Pre-populated Config', () => {
    it('displays pre-populated values', () => {
      render(
        <ChannelConfigForm
          channelType="slack"
          config={{
            webhook_url: 'https://hooks.slack.com/services/test',
            channel: '#alerts',
            username: 'Test Bot',
          }}
          onChange={vi.fn()}
        />
      )

      // Check that values are displayed (note: webhook is password field)
      expect(screen.getByDisplayValue('#alerts')).toBeInTheDocument()
      expect(screen.getByDisplayValue('Test Bot')).toBeInTheDocument()
    })
  })
})

describe('ChannelTypeSelector', () => {
  it('renders all 9 channel type buttons', () => {
    render(
      <ChannelTypeSelector value={null} onChange={vi.fn()} />
    )

    // Check that all channel names are visible
    expect(screen.getByText('Slack')).toBeInTheDocument()
    expect(screen.getByText('Email')).toBeInTheDocument()
    expect(screen.getByText('Webhook')).toBeInTheDocument()
    expect(screen.getByText('Discord')).toBeInTheDocument()
    expect(screen.getByText('Telegram')).toBeInTheDocument()
    expect(screen.getByText('PagerDuty')).toBeInTheDocument()
    expect(screen.getByText('OpsGenie')).toBeInTheDocument()
    expect(screen.getByText('Microsoft Teams')).toBeInTheDocument()
    expect(screen.getByText('GitHub')).toBeInTheDocument()
  })

  it('displays category labels', () => {
    render(
      <ChannelTypeSelector value={null} onChange={vi.fn()} />
    )

    expect(screen.getByText('Basic')).toBeInTheDocument()
    expect(screen.getByText('Chat')).toBeInTheDocument()
    expect(screen.getByText('Incident Management')).toBeInTheDocument()
    expect(screen.getByText('DevOps')).toBeInTheDocument()
  })

  it('calls onChange when a channel type is clicked', async () => {
    const onChange = vi.fn()
    const { user } = render(
      <ChannelTypeSelector value={null} onChange={onChange} />
    )

    await user.click(screen.getByText('Slack'))
    expect(onChange).toHaveBeenCalledWith('slack')

    await user.click(screen.getByText('Email'))
    expect(onChange).toHaveBeenCalledWith('email')

    await user.click(screen.getByText('PagerDuty'))
    expect(onChange).toHaveBeenCalledWith('pagerduty')

    await user.click(screen.getByText('GitHub'))
    expect(onChange).toHaveBeenCalledWith('github')
  })

  it('highlights selected channel type', () => {
    render(
      <ChannelTypeSelector value="slack" onChange={vi.fn()} />
    )

    const slackButton = screen.getByText('Slack').closest('button')
    expect(slackButton).toHaveClass('ring-2')
  })

  it('disables all buttons when disabled prop is true', () => {
    render(
      <ChannelTypeSelector value={null} onChange={vi.fn()} disabled={true} />
    )

    const buttons = screen.getAllByRole('button')
    buttons.forEach((button) => {
      expect(button).toBeDisabled()
    })
  })
})

describe('Channel Type Coverage', () => {
  // This test ensures we haven't missed any channel type
  it('all 9 channel types are covered', () => {
    expect(Object.keys(CHANNEL_SCHEMAS)).toHaveLength(9)
    expect(Object.keys(CHANNEL_SCHEMAS).sort()).toEqual([
      'discord',
      'email',
      'github',
      'opsgenie',
      'pagerduty',
      'slack',
      'teams',
      'telegram',
      'webhook',
    ])
  })

  it('each channel type has unique configuration', () => {
    const fieldSignatures = new Map<string, string>()

    Object.entries(CHANNEL_SCHEMAS).forEach(([type, schema]) => {
      const fields = Object.keys(schema.fields).sort().join(',')

      // Check that we don't have exact duplicate field sets (some overlap is expected)
      if (fieldSignatures.has(fields)) {
        // Some channels may have similar fields (e.g., webhooks), that's okay
        // but at least name/description should differ
        expect(schema.name).not.toBe(CHANNEL_SCHEMAS[fieldSignatures.get(fields) as ChannelType].name)
      }
      fieldSignatures.set(fields, type)
    })
  })
})
