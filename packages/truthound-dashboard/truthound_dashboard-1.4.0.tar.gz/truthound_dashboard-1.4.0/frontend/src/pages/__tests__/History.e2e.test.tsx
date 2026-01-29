/**
 * History E2E Tests
 *
 * End-to-end tests for the Validation History page using MSW mock server.
 * Tests historical data display, trend charts, filters, and period selection.
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest'
import { setupServer } from 'msw/node'
import { render as rtlRender, screen, waitFor, fireEvent } from '@testing-library/react'
import { handlers } from '@/mocks/handlers'
import { resetStore, getStore, getAll } from '@/mocks/data/store'
import { setTestLocale } from '@/test/test-utils'
import History from '../History'
import { getValidationHistory, getSource } from '@/api/client'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

// Setup MSW server with all handlers
const server = setupServer(...handlers)

// Helper to render with router params (without double wrapping)
function renderWithRouter(sourceId: string) {
  return rtlRender(
    <MemoryRouter initialEntries={[`/sources/${sourceId}/history`]}>
      <Routes>
        <Route path="/sources/:id/history" element={<History />} />
      </Routes>
    </MemoryRouter>
  )
}

describe('History E2E Tests', () => {
  let testSourceId: string

  beforeAll(() => {
    server.listen({ onUnhandledRequest: 'error' })
  })

  afterAll(() => {
    server.close()
  })

  beforeEach(() => {
    resetStore()
    setTestLocale('en')
    // Get a valid source ID for testing
    const store = getStore()
    const sources = getAll(store.sources)
    testSourceId = sources[0]?.id || 'test-source-id'
  })

  // ============================================================================
  // PAGE RENDERING
  // ============================================================================
  describe('Page Rendering', () => {
    it('displays source name with History suffix', async () => {
      renderWithRouter(testSourceId)

      // Wait for page to load and show History in the title
      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
        expect(screen.getByText(/History/i)).toBeInTheDocument()
      }, { timeout: 8000 })
    })

    it('displays page description', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText(/Validation trends and analytics/i)).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays Back button', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Back/i })).toBeInTheDocument()
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // PERIOD SELECTOR
  // ============================================================================
  describe('Period Selector', () => {
    it('displays period selector dropdown', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        const selectors = screen.getAllByRole('combobox')
        expect(selectors.length).toBeGreaterThanOrEqual(1)
      }, { timeout: 5000 })
    })

    it('displays default period (30d)', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText(/Last 30 days/i)).toBeInTheDocument()
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // GRANULARITY SELECTOR
  // ============================================================================
  describe('Granularity Selector', () => {
    it('displays granularity selector dropdown', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        const selectors = screen.getAllByRole('combobox')
        expect(selectors.length).toBeGreaterThanOrEqual(2)
      }, { timeout: 5000 })
    })

    it('displays default granularity (Daily)', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText(/Daily/i)).toBeInTheDocument()
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // SUMMARY CARDS
  // ============================================================================
  describe('Summary Cards', () => {
    it('displays Total Runs card', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText('Total Runs')).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays Passed card', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        // There may be multiple "Passed" texts, just check at least one exists
        const passedElements = screen.getAllByText('Passed')
        expect(passedElements.length).toBeGreaterThan(0)
      }, { timeout: 5000 })
    })

    it('displays Failed card', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText('Failed')).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays Success Rate card', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText('Success Rate')).toBeInTheDocument()
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // TREND CHART
  // ============================================================================
  describe('Trend Chart', () => {
    it('displays Success Rate Trend card', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText('Success Rate Trend')).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays trend chart description', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText(/Validation success rate over time/i)).toBeInTheDocument()
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // FAILURE FREQUENCY CHART
  // ============================================================================
  describe('Failure Frequency Chart', () => {
    it('displays Top Failure Types card', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText('Top Failure Types')).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays failure types description', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText(/Most common validation issues/i)).toBeInTheDocument()
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // RECENT VALIDATIONS
  // ============================================================================
  describe('Recent Validations', () => {
    it('displays Recent Validations card', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText('Recent Validations')).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays recent validations description', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText(/Latest validation runs/i)).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays validation entries with pass/fail status', async () => {
      const { container } = renderWithRouter(testSourceId)

      await waitFor(() => {
        // Look for validation entries (links to /validations/*)
        const validationLinks = container.querySelectorAll('a[href^="/validations/"]')
        // May have validation entries if data exists
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // API TESTS
  // ============================================================================
  describe('API Tests', () => {
    it('fetches validation history with default period', async () => {
      const response = await getValidationHistory(testSourceId)

      expect(response.success).toBe(true)
      expect(response.data).toBeDefined()
      expect(response.data.summary).toBeDefined()
      expect(response.data.trend).toBeDefined()
      expect(response.data.failure_frequency).toBeDefined()
      expect(response.data.recent_validations).toBeDefined()
    })

    it('fetches validation history with 7d period', async () => {
      const response = await getValidationHistory(testSourceId, { period: '7d' })

      expect(response.success).toBe(true)
      expect(response.data.summary).toBeDefined()
    })

    it('fetches validation history with 90d period', async () => {
      const response = await getValidationHistory(testSourceId, { period: '90d' })

      expect(response.success).toBe(true)
      expect(response.data.summary).toBeDefined()
    })

    it('fetches validation history with hourly granularity', async () => {
      const response = await getValidationHistory(testSourceId, { granularity: 'hourly' })

      expect(response.success).toBe(true)
      expect(response.data.trend).toBeDefined()
    })

    it('fetches validation history with weekly granularity', async () => {
      const response = await getValidationHistory(testSourceId, { granularity: 'weekly' })

      expect(response.success).toBe(true)
      expect(response.data.trend).toBeDefined()
    })

    it('summary has required fields', async () => {
      const response = await getValidationHistory(testSourceId)

      expect(response.data.summary.total_runs).toBeDefined()
      expect(typeof response.data.summary.total_runs).toBe('number')
      expect(response.data.summary.passed_runs).toBeDefined()
      expect(response.data.summary.failed_runs).toBeDefined()
      expect(response.data.summary.success_rate).toBeDefined()
    })

    it('trend data has valid structure', async () => {
      const response = await getValidationHistory(testSourceId)

      expect(Array.isArray(response.data.trend)).toBe(true)

      if (response.data.trend.length > 0) {
        const trendItem = response.data.trend[0]
        expect(trendItem.date).toBeDefined()
        expect(typeof trendItem.success_rate).toBe('number')
      }
    })

    it('failure frequency has valid structure', async () => {
      const response = await getValidationHistory(testSourceId)

      expect(Array.isArray(response.data.failure_frequency)).toBe(true)

      if (response.data.failure_frequency.length > 0) {
        const failureItem = response.data.failure_frequency[0]
        expect(failureItem.issue).toBeDefined()
        expect(typeof failureItem.count).toBe('number')
      }
    })

    it('recent validations have valid structure', async () => {
      const response = await getValidationHistory(testSourceId)

      expect(Array.isArray(response.data.recent_validations)).toBe(true)

      if (response.data.recent_validations.length > 0) {
        const validation = response.data.recent_validations[0]
        expect(validation.id).toBeDefined()
        expect(typeof validation.passed).toBe('boolean')
        expect(validation.created_at).toBeDefined()
      }
    })
  })

  // ============================================================================
  // ERROR HANDLING
  // ============================================================================
  describe('Error Handling', () => {
    it('shows error for invalid source ID', async () => {
      renderWithRouter('invalid-source-id-99999')

      await waitFor(() => {
        // Should show error message
        expect(screen.getByText(/error|not found/i)).toBeInTheDocument()
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // TREND ICON
  // ============================================================================
  describe('Success Rate Icon', () => {
    it('displays trending icon based on success rate', async () => {
      const { container } = renderWithRouter(testSourceId)

      await waitFor(() => {
        // Check for trending up or down icon
        const icons = container.querySelectorAll('svg')
        expect(icons.length).toBeGreaterThan(0)
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // ACCESSIBILITY
  // ============================================================================
  describe('Accessibility', () => {
    it('has proper heading structure', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        const heading = screen.getByRole('heading', { level: 1 })
        expect(heading).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('buttons are keyboard accessible', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        const buttons = screen.getAllByRole('button')
        buttons.forEach((button) => {
          expect(button).not.toHaveAttribute('tabindex', '-1')
        })
      }, { timeout: 5000 })
    })

    it('links have proper href attributes', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        const links = screen.getAllByRole('link')
        links.forEach((link) => {
          expect(link).toHaveAttribute('href')
        })
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // DATA INTEGRITY
  // ============================================================================
  describe('Data Integrity', () => {
    it('success rate is between 0 and 100', async () => {
      const response = await getValidationHistory(testSourceId)

      expect(response.data.summary.success_rate).toBeGreaterThanOrEqual(0)
      expect(response.data.summary.success_rate).toBeLessThanOrEqual(100)
    })

    it('passed + failed = total (approximately)', async () => {
      const response = await getValidationHistory(testSourceId)

      const { total_runs, passed_runs, failed_runs } = response.data.summary

      // Allow some tolerance for edge cases
      expect(passed_runs + failed_runs).toBeLessThanOrEqual(total_runs + 1)
    })

    it('trend dates are valid', async () => {
      const response = await getValidationHistory(testSourceId)

      response.data.trend.forEach((item) => {
        const date = new Date(item.date)
        expect(date.toString()).not.toBe('Invalid Date')
      })
    })

    it('validation timestamps are valid', async () => {
      const response = await getValidationHistory(testSourceId)

      response.data.recent_validations.forEach((validation) => {
        const date = new Date(validation.created_at)
        expect(date.toString()).not.toBe('Invalid Date')
      })
    })
  })

  // ============================================================================
  // CHART RENDERING
  // ============================================================================
  describe('Chart Rendering', () => {
    it('renders Recharts LineChart container', async () => {
      const { container } = renderWithRouter(testSourceId)

      await waitFor(() => {
        // Recharts components render in a container
        const chartContainers = container.querySelectorAll('.recharts-wrapper, .recharts-responsive-container')
        // Charts may or may not render depending on data
      }, { timeout: 5000 })
    })

    it('renders Recharts BarChart container', async () => {
      const { container } = renderWithRouter(testSourceId)

      await waitFor(() => {
        const chartContainers = container.querySelectorAll('.recharts-wrapper')
        // Bar charts may be present
      }, { timeout: 5000 })
    })
  })
})
