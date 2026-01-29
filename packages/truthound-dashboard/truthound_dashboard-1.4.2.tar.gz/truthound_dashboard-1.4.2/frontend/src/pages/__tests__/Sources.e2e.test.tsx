/**
 * Sources E2E Tests
 *
 * End-to-end tests for the Sources list page using MSW mock server.
 * Tests data source listing, validation, and deletion functionality.
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach, vi } from 'vitest'
import { setupServer } from 'msw/node'
import { handlers } from '@/mocks/handlers'
import { resetStore, getStore, getAll } from '@/mocks/data/store'
import { render, screen, waitFor, fireEvent, Locales, setTestLocale } from '@/test/test-utils'
import Sources from '../Sources'
import { listSources, deleteSource, runValidation } from '@/api/client'

// Setup MSW server with all handlers
const server = setupServer(...handlers)

describe('Sources E2E Tests', () => {
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
      render(<Sources />)

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.queryByRole('status')).not.toBeInTheDocument()
      }, { timeout: 3000 })

      // Should display the page title
      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Data Sources')
      })
    })

    it('fetches sources using the API client', async () => {
      const response = await listSources({ limit: 50 })

      expect(response.success).toBe(true)
      expect(Array.isArray(response.data)).toBe(true)
      expect(response.data.length).toBeGreaterThan(0)
    })

    it('displays source cards when sources exist', async () => {
      render(<Sources />)

      // Wait for sources to load
      await waitFor(() => {
        const store = getStore()
        const sources = getAll(store.sources)
        // At least one source name should be visible
        const firstSource = sources[0]
        if (firstSource) {
          expect(screen.getByText(firstSource.name)).toBeInTheDocument()
        }
      }, { timeout: 3000 })
    })

    it('shows subtitle text', async () => {
      render(<Sources />)

      await waitFor(() => {
        expect(screen.getByText('Manage your data sources and validations')).toBeInTheDocument()
      })
    })
  })

  // ============================================================================
  // SOURCE LIST DISPLAY
  // ============================================================================
  describe('Source List Display', () => {
    it('displays source type badges', async () => {
      render(<Sources />)

      await waitFor(() => {
        // Source types should appear as badges
        const badges = screen.getAllByText(/file|postgresql|mysql|snowflake|bigquery/i)
        expect(badges.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })

    it('displays "Last validated" info', async () => {
      render(<Sources />)

      await waitFor(() => {
        const lastValidatedTexts = screen.getAllByText(/Last validated/i)
        expect(lastValidatedTexts.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })

    it('displays validation status badges', async () => {
      render(<Sources />)

      await waitFor(() => {
        // Check for any validation status badge
        const store = getStore()
        const sources = getAll(store.sources)
        const hasValidationStatus = sources.some((s) => s.latest_validation_status)
        if (hasValidationStatus) {
          const statusBadges = screen.getAllByText(/Passed|Failed|Pending|Warning/i)
          expect(statusBadges.length).toBeGreaterThan(0)
        }
      }, { timeout: 3000 })
    })

    it('displays Add Source button', async () => {
      render(<Sources />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Add Source/i })).toBeInTheDocument()
      })
    })

    it('displays Validate buttons for each source', async () => {
      render(<Sources />)

      await waitFor(() => {
        const validateButtons = screen.getAllByRole('button', { name: /Validate/i })
        expect(validateButtons.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })

    it('displays delete buttons for each source', async () => {
      const { container } = render(<Sources />)

      await waitFor(() => {
        // Delete buttons have trash icons
        const trashIcons = container.querySelectorAll('.text-destructive')
        expect(trashIcons.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })
  })

  // ============================================================================
  // SOURCE CARD NAVIGATION
  // ============================================================================
  describe('Source Card Navigation', () => {
    it('source names are links to detail pages', async () => {
      render(<Sources />)

      await waitFor(() => {
        const store = getStore()
        const sources = getAll(store.sources)
        const firstSource = sources[0]
        if (firstSource) {
          const link = screen.getByRole('link', { name: firstSource.name })
          expect(link).toHaveAttribute('href', `/sources/${firstSource.id}`)
        }
      }, { timeout: 3000 })
    })

    it('detail buttons link to source detail pages', async () => {
      const { container } = render(<Sources />)

      await waitFor(() => {
        // FileText icon buttons should be links
        const detailLinks = container.querySelectorAll('a[href^="/sources/"]')
        expect(detailLinks.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })
  })

  // ============================================================================
  // VALIDATION ACTIONS
  // ============================================================================
  describe('Validation Actions', () => {
    it('API: run validation on a source', async () => {
      const store = getStore()
      const sources = getAll(store.sources)
      const firstSource = sources[0]

      if (firstSource) {
        const result = await runValidation(firstSource.id, {})

        expect(result).toBeDefined()
        expect(result.source_id).toBe(firstSource.id)
        expect(typeof result.passed).toBe('boolean')
        expect(typeof result.total_issues).toBe('number')
      }
    })

    it('clicking validate button triggers validation', async () => {
      render(<Sources />)

      await waitFor(() => {
        const validateButtons = screen.getAllByRole('button', { name: /Validate/i })
        expect(validateButtons.length).toBeGreaterThan(0)
      }, { timeout: 3000 })

      // Click the first validate button
      const validateButtons = screen.getAllByRole('button', { name: /Validate/i })
      fireEvent.click(validateButtons[0])

      // Should show toast with validation started
      await waitFor(() => {
        expect(screen.getByText(/Validation Started/i)).toBeInTheDocument()
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // DELETE ACTIONS
  // ============================================================================
  describe('Delete Actions', () => {
    it('API: delete a source', async () => {
      const store = getStore()
      const sources = getAll(store.sources)
      const initialCount = sources.length

      if (initialCount > 0) {
        const sourceToDelete = sources[0]
        await deleteSource(sourceToDelete.id)

        // Verify deletion
        const newSources = getAll(getStore().sources)
        expect(newSources.length).toBe(initialCount - 1)
        expect(newSources.find((s) => s.id === sourceToDelete.id)).toBeUndefined()
      }
    })

    it('clicking delete button shows confirmation dialog', async () => {
      const { container } = render(<Sources />)

      await waitFor(() => {
        const deleteButtons = container.querySelectorAll('.text-destructive')
        expect(deleteButtons.length).toBeGreaterThan(0)
      }, { timeout: 3000 })

      // Click the first delete button
      const deleteButtons = container.querySelectorAll('button .text-destructive')
      if (deleteButtons.length > 0) {
        const parentButton = deleteButtons[0].closest('button')
        if (parentButton) {
          fireEvent.click(parentButton)

          // Should show confirmation dialog
          await waitFor(() => {
            expect(screen.getByText(/Delete Source/i)).toBeInTheDocument()
          }, { timeout: 3000 })
        }
      }
    })
  })

  // ============================================================================
  // EMPTY STATE
  // ============================================================================
  describe('Empty State', () => {
    it('shows empty state when no sources exist', async () => {
      // Clear all sources from the store
      const store = getStore()
      store.sources.clear()

      render(<Sources />)

      await waitFor(() => {
        expect(screen.getByText(/No sources yet/i)).toBeInTheDocument()
        expect(screen.getByText(/Add your first data source/i)).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('empty state has Add First Source button', async () => {
      const store = getStore()
      store.sources.clear()

      render(<Sources />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Add Your First Source/i })).toBeInTheDocument()
      }, { timeout: 3000 })
    })
  })

  // ============================================================================
  // DATA INTEGRITY
  // ============================================================================
  describe('Data Integrity', () => {
    it('mock data has valid source types', async () => {
      const response = await listSources({ limit: 50 })
      const validTypes = ['file', 'postgresql', 'mysql', 'snowflake', 'bigquery']

      response.data.forEach((source) => {
        expect(validTypes).toContain(source.type)
      })
    })

    it('mock data has valid timestamps', async () => {
      const response = await listSources({ limit: 50 })

      response.data.forEach((source) => {
        expect(new Date(source.created_at).toString()).not.toBe('Invalid Date')
        expect(new Date(source.updated_at).toString()).not.toBe('Invalid Date')
        if (source.last_validated_at) {
          expect(new Date(source.last_validated_at).toString()).not.toBe('Invalid Date')
        }
      })
    })

    it('sources have required fields', async () => {
      const response = await listSources({ limit: 50 })

      response.data.forEach((source) => {
        expect(source.id).toBeDefined()
        expect(source.name).toBeDefined()
        expect(source.type).toBeDefined()
        expect(typeof source.is_active).toBe('boolean')
        expect(typeof source.has_schema).toBe('boolean')
      })
    })
  })

  // ============================================================================
  // UI COMPONENTS
  // ============================================================================
  describe('UI Components', () => {
    it('renders source cards with database icons', async () => {
      const { container } = render(<Sources />)

      await waitFor(() => {
        // Database icons are SVGs
        const icons = container.querySelectorAll('svg')
        expect(icons.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })

    it('renders Card components for sources', async () => {
      const { container } = render(<Sources />)

      await waitFor(() => {
        // Cards should have rounded borders
        const cards = container.querySelectorAll('[class*="rounded"]')
        expect(cards.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })
  })

  // ============================================================================
  // INTERNATIONALIZATION
  // ============================================================================
  describe('Internationalization', () => {
    it('renders Korean translations correctly', async () => {
      render(<Sources />, { locale: Locales.KOREAN })

      await waitFor(() => {
        // Korean title
        expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('데이터 소스')
      })
    })

    it('renders Korean subtitle', async () => {
      render(<Sources />, { locale: Locales.KOREAN })

      await waitFor(() => {
        expect(screen.getByText('데이터 소스 및 검증 관리')).toBeInTheDocument()
      })
    })

    it('renders Korean buttons', async () => {
      render(<Sources />, { locale: Locales.KOREAN })

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /소스 추가/i })).toBeInTheDocument()
      })
    })

    it('renders Korean empty state', async () => {
      const store = getStore()
      store.sources.clear()

      render(<Sources />, { locale: Locales.KOREAN })

      await waitFor(() => {
        expect(screen.getByText('소스가 없습니다')).toBeInTheDocument()
      }, { timeout: 3000 })
    })
  })

  // ============================================================================
  // ACCESSIBILITY
  // ============================================================================
  describe('Accessibility', () => {
    it('has accessible heading structure', async () => {
      render(<Sources />)

      await waitFor(() => {
        const heading = screen.getByRole('heading', { level: 1 })
        expect(heading).toBeInTheDocument()
      })
    })

    it('buttons are accessible', async () => {
      render(<Sources />)

      await waitFor(() => {
        const buttons = screen.getAllByRole('button')
        expect(buttons.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })

    it('links have proper href attributes', async () => {
      render(<Sources />)

      await waitFor(() => {
        const links = screen.getAllByRole('link')
        links.forEach((link) => {
          expect(link).toHaveAttribute('href')
        })
      }, { timeout: 3000 })
    })
  })
})
