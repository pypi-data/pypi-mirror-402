/**
 * RuleBuilder Component Tests
 *
 * Tests for the notification routing rule builder component.
 * Tests cover:
 * - Rule type selection
 * - Parameter configuration
 * - Rule config changes
 */

import { describe, it, expect, vi, beforeEach, beforeAll, afterAll, afterEach } from 'vitest'
import { render, screen, waitFor, setupMswServer } from '@/test/test-utils'
import { RuleBuilder, type RuleConfig } from '../RuleBuilder'

// Setup MSW server for this test file (even if not used, for consistency)
const server = setupMswServer()

beforeAll(() => server.listen({ onUnhandledRequest: 'bypass' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

// Mock onChange handler
const mockOnChange = vi.fn()

// Default rule config for testing
const defaultRuleConfig: RuleConfig = {
  type: 'severity',
  min_severity: 'medium',
}

describe('RuleBuilder', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Initial Render', () => {
    it('renders the rule builder with a severity rule', async () => {
      render(
        <RuleBuilder
          value={defaultRuleConfig}
          onChange={mockOnChange}
        />
      )

      await waitFor(() => {
        // The component should render with comboboxes (rule type and parameter)
        const comboboxes = screen.getAllByRole('combobox')
        expect(comboboxes.length).toBeGreaterThan(0)
        // Look for severity text elements (type selector and parameter)
        const severityElements = screen.getAllByText(/severity/i)
        expect(severityElements.length).toBeGreaterThan(0)
      })
    })

    it('renders different rule types', async () => {
      const issueCountConfig: RuleConfig = {
        type: 'issue_count',
        min_count: 5,
      }

      render(
        <RuleBuilder
          value={issueCountConfig}
          onChange={mockOnChange}
        />
      )

      await waitFor(() => {
        // Look for Issue Count text in the component
        const issueCountElements = screen.getAllByText(/issue count/i)
        expect(issueCountElements.length).toBeGreaterThan(0)
      })
    })

    it('renders always rule type', async () => {
      const alwaysConfig: RuleConfig = {
        type: 'always',
      }

      render(
        <RuleBuilder
          value={alwaysConfig}
          onChange={mockOnChange}
        />
      )

      // The component renders with comboboxes for rule configuration
      await waitFor(() => {
        const comboboxes = screen.getAllByRole('combobox')
        expect(comboboxes.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Combinator Rules', () => {
    it('renders all_of combinator', async () => {
      const allOfConfig: RuleConfig = {
        type: 'all_of',
        rules: [
          { type: 'severity', min_severity: 'high' },
          { type: 'issue_count', min_count: 3 },
        ],
      }

      render(
        <RuleBuilder
          value={allOfConfig}
          onChange={mockOnChange}
          maxDepth={3}
        />
      )

      await waitFor(() => {
        // Should show all_of combinator - look for "All Of" or "All conditions"
        const allOfElements = screen.getAllByText(/all/i)
        expect(allOfElements.length).toBeGreaterThan(0)
      })
    })

    it('renders any_of combinator', async () => {
      const anyOfConfig: RuleConfig = {
        type: 'any_of',
        rules: [
          { type: 'severity', min_severity: 'critical' },
        ],
      }

      render(
        <RuleBuilder
          value={anyOfConfig}
          onChange={mockOnChange}
          maxDepth={3}
        />
      )

      await waitFor(() => {
        // Look for "Any Of" text
        const anyOfElements = screen.getAllByText(/any/i)
        expect(anyOfElements.length).toBeGreaterThan(0)
      })
    })

    it('renders not combinator', async () => {
      const notConfig: RuleConfig = {
        type: 'not',
        rules: [{ type: 'always' }],
      }

      render(
        <RuleBuilder
          value={notConfig}
          onChange={mockOnChange}
          maxDepth={3}
        />
      )

      await waitFor(() => {
        // Look for "Not" text - use getAllByText since there might be multiple
        const notElements = screen.getAllByText(/not/i)
        expect(notElements.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Rule Type Selection', () => {
    it('shows rule type dropdown/selector', async () => {
      render(
        <RuleBuilder
          value={defaultRuleConfig}
          onChange={mockOnChange}
        />
      )

      await waitFor(() => {
        // Should have some interactive elements
        const buttons = screen.queryAllByRole('button')
        expect(buttons.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Configuration', () => {
    it('accepts maxDepth prop', async () => {
      const deepConfig: RuleConfig = {
        type: 'all_of',
        rules: [
          {
            type: 'any_of',
            rules: [{ type: 'severity', min_severity: 'high' }],
          },
        ],
      }

      render(
        <RuleBuilder
          value={deepConfig}
          onChange={mockOnChange}
          maxDepth={2}
        />
      )

      // Should render without errors
      await waitFor(() => {
        expect(screen.getByText(/all of/i)).toBeInTheDocument()
      })
    })

    it('accepts className prop', async () => {
      const { container } = render(
        <RuleBuilder
          value={defaultRuleConfig}
          onChange={mockOnChange}
          className="custom-class"
        />
      )

      // The custom class should be applied
      const element = container.querySelector('.custom-class')
      expect(element).toBeInTheDocument()
    })
  })

  describe('onCopyRule Callback', () => {
    it('accepts onCopyRule prop', async () => {
      const mockOnCopyRule = vi.fn()

      render(
        <RuleBuilder
          value={defaultRuleConfig}
          onChange={mockOnChange}
          onCopyRule={mockOnCopyRule}
        />
      )

      // Should render without errors - look for comboboxes
      await waitFor(() => {
        const comboboxes = screen.getAllByRole('combobox')
        expect(comboboxes.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Parameter Rendering', () => {
    it('renders severity parameter options', async () => {
      render(
        <RuleBuilder
          value={defaultRuleConfig}
          onChange={mockOnChange}
        />
      )

      await waitFor(() => {
        // Should show severity level selector or display
        const severityElements = screen.getAllByText(/severity/i)
        expect(severityElements.length).toBeGreaterThan(0)
      })
    })

    it('renders issue count input', async () => {
      const issueCountConfig: RuleConfig = {
        type: 'issue_count',
        min_count: 10,
      }

      render(
        <RuleBuilder
          value={issueCountConfig}
          onChange={mockOnChange}
        />
      )

      await waitFor(() => {
        // Should display the issue count text
        const issueCountElements = screen.getAllByText(/issue count/i)
        expect(issueCountElements.length).toBeGreaterThan(0)
      })
    })

    it('renders pass rate input', async () => {
      const passRateConfig: RuleConfig = {
        type: 'pass_rate',
        max_pass_rate: 0.9,
      }

      render(
        <RuleBuilder
          value={passRateConfig}
          onChange={mockOnChange}
        />
      )

      await waitFor(() => {
        // Should display pass rate text
        const passRateElements = screen.getAllByText(/pass rate/i)
        expect(passRateElements.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Static Rules', () => {
    it('renders never rule type', async () => {
      const neverConfig: RuleConfig = {
        type: 'never',
      }

      render(
        <RuleBuilder
          value={neverConfig}
          onChange={mockOnChange}
        />
      )

      // The component renders with comboboxes for rule configuration
      await waitFor(() => {
        const comboboxes = screen.getAllByRole('combobox')
        expect(comboboxes.length).toBeGreaterThan(0)
      })
    })
  })
})
