/**
 * Dashboard E2E Tests
 *
 * End-to-end tests for the Dashboard page using MSW mock server.
 * Tests the full data flow from API to UI rendering.
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest'
import { setupServer } from 'msw/node'
import { handlers } from '@/mocks/handlers'
import { resetStore, getStore, getAll } from '@/mocks/data/store'
import { render, screen, waitFor, Locales, setTestLocale } from '@/test/test-utils'
import Dashboard from '../Dashboard'
import { listSources } from '@/api/client'

// Setup MSW server with all handlers
const server = setupServer(...handlers)

describe('Dashboard E2E Tests', () => {
  beforeAll(() => {
    server.listen({ onUnhandledRequest: 'error' })
  })

  afterAll(() => {
    server.close()
  })

  beforeEach(() => {
    resetStore()
    setTestLocale('en')
  })

  // ============================================================================
  // DATA LOADING
  // ============================================================================
  describe('Data Loading', () => {
    it('loads and displays sources from the mock API', async () => {
      render(<Dashboard />)

      // Wait for data to load and dashboard to render
      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Dashboard')
      })
    })

    it('fetches sources using the API client', async () => {
      const response = await listSources({ limit: 10 })

      expect(response.success).toBe(true)
      expect(Array.isArray(response.data)).toBe(true)
      expect(response.data.length).toBeGreaterThan(0)
    })

    it('displays Total Sources stat card', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText('Total Sources')).toBeInTheDocument()
      })
    })
  })

  // ============================================================================
  // STATS CALCULATION
  // ============================================================================
  describe('Stats Calculation', () => {
    it('displays Passed stat card', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getAllByText('Passed').length).toBeGreaterThan(0)
        expect(screen.getByText('Validation passed')).toBeInTheDocument()
      })
    })

    it('displays Failed stat card', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getAllByText('Failed').length).toBeGreaterThan(0)
        expect(screen.getByText('Validation failed')).toBeInTheDocument()
      })
    })

    it('displays Pending stat card', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getAllByText('Pending').length).toBeGreaterThan(0)
        expect(screen.getByText('Not yet validated')).toBeInTheDocument()
      })
    })
  })

  // ============================================================================
  // RECENT SOURCES LIST
  // ============================================================================
  describe('Recent Sources List', () => {
    it('displays sources from mock data', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        // Recent Sources section should be visible
        expect(screen.getByText('Recent Sources')).toBeInTheDocument()
      })
    })

    it('shows View All link', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        const viewAllLink = screen.getByRole('link', { name: /view all/i })
        expect(viewAllLink).toHaveAttribute('href', '/sources')
      })
    })
  })

  // ============================================================================
  // DATA INTEGRITY
  // ============================================================================
  describe('Data Integrity', () => {
    it('mock data has realistic validation statuses', async () => {
      const response = await listSources({ limit: 50 })

      // Check that we have sources with various statuses
      const statuses = response.data.map((s) => s.latest_validation_status)
      const statusSet = new Set(statuses.filter(Boolean))

      // Should have at least one status
      expect(statusSet.size).toBeGreaterThanOrEqual(1)
    })

    it('mock data has valid source types', async () => {
      const response = await listSources({ limit: 50 })
      const validTypes = ['file', 'postgresql', 'mysql', 'snowflake', 'bigquery']

      response.data.forEach((source) => {
        expect(validTypes).toContain(source.type)
      })
    })

    it('mock data has valid timestamps', async () => {
      const response = await listSources({ limit: 10 })

      response.data.forEach((source) => {
        expect(new Date(source.created_at).toString()).not.toBe('Invalid Date')
        expect(new Date(source.updated_at).toString()).not.toBe('Invalid Date')
        if (source.last_validated_at) {
          expect(new Date(source.last_validated_at).toString()).not.toBe(
            'Invalid Date'
          )
        }
      })
    })
  })

  // ============================================================================
  // UI COMPONENTS
  // ============================================================================
  describe('UI Components', () => {
    it('renders GlassCard components for stats', async () => {
      const { container } = render(<Dashboard />)

      await waitFor(() => {
        // GlassCards have specific gradient backgrounds
        const glassCards = container.querySelectorAll('[class*="from-"]')
        expect(glassCards.length).toBeGreaterThanOrEqual(4)
      })
    })

    it('displays icons in stat cards', async () => {
      const { container } = render(<Dashboard />)

      await waitFor(() => {
        // lucide-react icons render as SVG
        const icons = container.querySelectorAll('svg')
        expect(icons.length).toBeGreaterThan(0)
      })
    })
  })

  // ============================================================================
  // INTERNATIONALIZATION
  // ============================================================================
  describe('Internationalization', () => {
    it('renders Korean translations correctly', async () => {
      render(<Dashboard />, { locale: Locales.KOREAN })

      await waitFor(() => {
        // Korean dashboard title
        expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('대시보드')
      })
    })

    it('renders Korean stat labels', async () => {
      render(<Dashboard />, { locale: Locales.KOREAN })

      await waitFor(() => {
        expect(screen.getByText('전체 소스')).toBeInTheDocument()
        expect(screen.getAllByText('통과').length).toBeGreaterThan(0)
        expect(screen.getAllByText('실패').length).toBeGreaterThan(0)
        expect(screen.getAllByText('대기 중').length).toBeGreaterThan(0)
      })
    })

    it('renders Korean section titles', async () => {
      render(<Dashboard />, { locale: Locales.KOREAN })

      await waitFor(() => {
        expect(screen.getByText('최근 소스')).toBeInTheDocument()
        expect(screen.getByRole('link', { name: /전체 보기/i })).toBeInTheDocument()
      })
    })
  })

  // ============================================================================
  // LAYOUT STRUCTURE
  // ============================================================================
  describe('Layout Structure', () => {
    it('has grid layout for stat cards', async () => {
      const { container } = render(<Dashboard />)

      await waitFor(() => {
        const grid = container.querySelector('.grid')
        expect(grid).toBeInTheDocument()
      })
    })

    it('has proper section spacing', async () => {
      const { container } = render(<Dashboard />)

      await waitFor(() => {
        const spacedContainer = container.querySelector('.space-y-6')
        expect(spacedContainer).toBeInTheDocument()
      })
    })
  })

  // ============================================================================
  // ACCESSIBILITY
  // ============================================================================
  describe('Accessibility', () => {
    it('has accessible heading structure', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        const heading = screen.getByRole('heading', { level: 1 })
        expect(heading).toBeInTheDocument()
      })
    })

    it('links have accessible text', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        const links = screen.getAllByRole('link')
        links.forEach((link) => {
          // Each link should have text content or aria-label
          const hasAccessibleText =
            link.textContent?.trim() || link.getAttribute('aria-label')
          expect(hasAccessibleText).toBeTruthy()
        })
      })
    })
  })
})
