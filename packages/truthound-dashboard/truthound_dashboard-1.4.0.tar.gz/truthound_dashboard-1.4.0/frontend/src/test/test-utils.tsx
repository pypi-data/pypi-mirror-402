/**
 * Test utilities for rendering components with providers
 *
 * This module provides:
 * - Custom render function with all necessary providers
 * - Helper functions for common test patterns
 * - Test fixtures and factories
 * - Mock API helpers
 */

import { ReactElement, ReactNode } from 'react'
import { render, RenderOptions, RenderResult, waitFor, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter, MemoryRouter } from 'react-router-dom'
// Import from the mocked module (setup.ts provides the mock)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
import * as reactIntlayer from 'react-intlayer'
import { ThemeProvider } from '@/components/theme-provider'
import { http, HttpResponse } from 'msw'
import { setupMswServer } from './msw-server'

// Get the MSW server for API mocking
const server = setupMswServer()

// ============================================================================
// Constants & Types
// ============================================================================

export const Locales = {
  ENGLISH: 'en',
  KOREAN: 'ko',
} as const

type LocaleType = 'en' | 'ko'
type ThemeType = 'light' | 'dark' | 'system'

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  /** Locale for i18n (default: 'en') */
  locale?: LocaleType
  /** Theme for the app (default: 'dark') */
  theme?: ThemeType
  /** Initial route entries for MemoryRouter */
  initialEntries?: string[]
  /** Use MemoryRouter instead of BrowserRouter */
  useMemoryRouter?: boolean
  /** Initial route for MemoryRouter (shorthand for initialEntries with single entry) */
  route?: string
}

interface CustomRenderResult extends RenderResult {
  /** User event instance for simulating user interactions */
  user: ReturnType<typeof userEvent.setup>
}

// ============================================================================
// Locale Management
// ============================================================================

// Helper to set locale in the mock
const setTestLocale = (locale: LocaleType) => {
  if ('__setTestLocale' in reactIntlayer && typeof reactIntlayer.__setTestLocale === 'function') {
    reactIntlayer.__setTestLocale(locale)
  }
}

// ============================================================================
// Provider Wrapper
// ============================================================================

interface AllProvidersProps {
  children: ReactNode
  locale?: LocaleType
  theme?: ThemeType
  initialEntries?: string[]
  useMemoryRouter?: boolean
}

function AllProviders({
  children,
  locale = 'en',
  theme = 'dark',
  initialEntries,
  useMemoryRouter = false,
}: AllProvidersProps) {
  // Set locale for the mock
  setTestLocale(locale)

  const RouterComponent = useMemoryRouter ? MemoryRouter : BrowserRouter
  const routerProps = useMemoryRouter && initialEntries ? { initialEntries } : {}

  return (
    <RouterComponent {...routerProps}>
      <ThemeProvider defaultTheme={theme} storageKey="test-theme">
        {children}
      </ThemeProvider>
    </RouterComponent>
  )
}

// ============================================================================
// Custom Render Function
// ============================================================================

/**
 * Custom render function that includes all necessary providers.
 *
 * @example
 * ```tsx
 * // Basic render
 * const { user } = render(<MyComponent />)
 * await user.click(screen.getByRole('button'))
 *
 * // With options
 * render(<MyComponent />, {
 *   locale: 'ko',
 *   route: '/dashboard',
 *   useMemoryRouter: true,
 * })
 * ```
 */
function customRender(ui: ReactElement, options: CustomRenderOptions = {}): CustomRenderResult {
  const {
    locale = 'en',
    theme = 'dark',
    initialEntries,
    useMemoryRouter = false,
    route,
    ...renderOptions
  } = options

  // Handle route shorthand
  const entries = route ? [route] : initialEntries

  // Set locale before rendering
  setTestLocale(locale)

  // Setup user event
  const user = userEvent.setup()

  const result = render(ui, {
    wrapper: ({ children }) => (
      <AllProviders
        locale={locale}
        theme={theme}
        initialEntries={entries}
        useMemoryRouter={useMemoryRouter || !!route}
      >
        {children}
      </AllProviders>
    ),
    ...renderOptions,
  })

  return {
    ...result,
    user,
  }
}

// ============================================================================
// API Mocking Helpers
// ============================================================================

/**
 * Override an API endpoint for a single test
 *
 * @example
 * ```tsx
 * mockApiResponse('/api/v1/sources', { items: [], total: 0 })
 * mockApiResponse('/api/v1/sources/123', null, { status: 404 })
 * ```
 */
export function mockApiResponse<T>(
  endpoint: string,
  data: T,
  options: { status?: number; method?: 'get' | 'post' | 'put' | 'patch' | 'delete' } = {}
) {
  const { status = 200, method = 'get' } = options
  const fullPath = endpoint.startsWith('/') ? `*${endpoint}` : `*/${endpoint}`

  server.use(
    http[method](fullPath, () => {
      return HttpResponse.json(data, { status })
    })
  )
}

/**
 * Mock an API endpoint to return an error
 *
 * @example
 * ```tsx
 * mockApiError('/api/v1/sources', 'Failed to load sources', 500)
 * ```
 */
export function mockApiError(endpoint: string, message: string, status = 500) {
  const fullPath = endpoint.startsWith('/') ? `*${endpoint}` : `*/${endpoint}`

  server.use(
    http.get(fullPath, () => {
      return HttpResponse.json({ detail: message }, { status })
    })
  )
}

/**
 * Mock an API endpoint with a delay
 *
 * @example
 * ```tsx
 * mockApiDelay('/api/v1/sources', { items: [] }, 1000)
 * ```
 */
export function mockApiDelay<T>(endpoint: string, data: T, delayMs: number) {
  const fullPath = endpoint.startsWith('/') ? `*${endpoint}` : `*/${endpoint}`

  server.use(
    http.get(fullPath, async () => {
      await new Promise((resolve) => setTimeout(resolve, delayMs))
      return HttpResponse.json(data)
    })
  )
}

// ============================================================================
// Test Helpers
// ============================================================================

/**
 * Wait for loading state to finish
 */
export async function waitForLoadingToFinish() {
  await waitFor(() => {
    const loaders = screen.queryAllByRole('status')
    expect(loaders).toHaveLength(0)
  })
}

/**
 * Wait for element to be removed
 */
export async function waitForElementToBeRemoved(element: Element | null) {
  if (!element) return
  await waitFor(() => {
    expect(element).not.toBeInTheDocument()
  })
}

/**
 * Click a button by its text content
 */
export async function clickButton(user: ReturnType<typeof userEvent.setup>, text: string | RegExp) {
  const button = screen.getByRole('button', { name: text })
  await user.click(button)
}

/**
 * Fill an input by its label
 */
export async function fillInput(
  user: ReturnType<typeof userEvent.setup>,
  label: string | RegExp,
  value: string
) {
  const input = screen.getByLabelText(label)
  await user.clear(input)
  await user.type(input, value)
}

/**
 * Select an option from a select component
 */
export async function selectOption(
  user: ReturnType<typeof userEvent.setup>,
  selectLabel: string | RegExp,
  optionText: string | RegExp
) {
  const trigger = screen.getByRole('combobox', { name: selectLabel })
  await user.click(trigger)
  const option = await screen.findByRole('option', { name: optionText })
  await user.click(option)
}

// ============================================================================
// Test Fixtures
// ============================================================================

export const testFixtures = {
  // Notification channels
  channels: [
    { id: 'ch-1', name: 'Slack #alerts', type: 'slack' as const, is_active: true },
    { id: 'ch-2', name: 'Email Team', type: 'email' as const, is_active: true },
    { id: 'ch-3', name: 'PagerDuty', type: 'pagerduty' as const, is_active: false },
  ],

  // Routing rules
  routingRules: [
    {
      id: 'rule-1',
      name: 'Critical Alerts',
      rule_config: { type: 'severity', min_severity: 'critical' },
      actions: ['ch-1', 'ch-2'],
      priority: 100,
      is_active: true,
      stop_on_match: false,
      metadata: {},
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 'rule-2',
      name: 'High Issue Count',
      rule_config: { type: 'issue_count', min_count: 10 },
      actions: ['ch-1'],
      priority: 50,
      is_active: true,
      stop_on_match: true,
      metadata: {},
      created_at: '2024-01-02T00:00:00Z',
      updated_at: '2024-01-02T00:00:00Z',
    },
  ],

  // Deduplication configs
  deduplicationConfigs: [
    {
      id: 'dedup-1',
      name: 'Sliding Window',
      strategy: 'sliding' as const,
      policy: 'basic' as const,
      window_seconds: 300,
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 'dedup-2',
      name: 'Strict Policy',
      strategy: 'tumbling' as const,
      policy: 'strict' as const,
      window_seconds: 600,
      is_active: false,
      created_at: '2024-01-02T00:00:00Z',
      updated_at: '2024-01-02T00:00:00Z',
    },
  ],

  // Escalation policies
  escalationPolicies: [
    {
      id: 'esc-1',
      name: 'On-Call Escalation',
      description: 'Default escalation policy',
      levels: [
        { level: 1, delay_minutes: 0, targets: [{ type: 'user' as const, identifier: 'oncall@example.com', channel: 'ch-1' }] },
        { level: 2, delay_minutes: 15, targets: [{ type: 'group' as const, identifier: 'engineering', channel: 'ch-2' }] },
      ],
      auto_resolve_on_success: true,
      max_escalations: 3,
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
  ],

  // Escalation incidents
  escalationIncidents: [
    {
      id: 'inc-1',
      policy_id: 'esc-1',
      incident_ref: 'validation-abc123',
      state: 'triggered' as const,
      current_level: 1,
      escalation_count: 0,
      context: { source_name: 'orders.csv', severity: 'high' },
      acknowledged_by: null,
      acknowledged_at: null,
      resolved_by: null,
      resolved_at: null,
      next_escalation_at: '2024-01-01T01:00:00Z',
      events: [],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 'inc-2',
      policy_id: 'esc-1',
      incident_ref: 'validation-def456',
      state: 'resolved' as const,
      current_level: 1,
      escalation_count: 1,
      context: { source_name: 'users.parquet', severity: 'critical' },
      acknowledged_by: 'user@example.com',
      acknowledged_at: '2024-01-01T00:30:00Z',
      resolved_by: 'user@example.com',
      resolved_at: '2024-01-01T01:00:00Z',
      next_escalation_at: null,
      events: [],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T01:00:00Z',
    },
  ],

  // Stats
  deduplicationStats: {
    total_received: 100,
    total_deduplicated: 25,
    total_passed: 75,
    dedup_rate: 25.0,
    active_fingerprints: 10,
  },

  escalationStats: {
    total_incidents: 50,
    by_state: { triggered: 5, acknowledged: 10, escalated: 2, resolved: 33 },
    active_count: 17,
    total_policies: 3,
    avg_resolution_time_minutes: 45,
  },

  throttlingStats: {
    total_received: 200,
    total_throttled: 30,
    total_passed: 170,
    throttle_rate: 15.0,
    current_window_count: 5,
  },
}

// ============================================================================
// Exports
// ============================================================================

// Re-export everything from testing-library
export * from '@testing-library/react'
export { userEvent }

// Override render with custom render
export { customRender as render }

// Export setTestLocale for tests that need to change locale dynamically
export { setTestLocale }

// Export server for direct access if needed
export { server }

// Export MSW server setup function
export { setupMswServer } from './msw-server'
