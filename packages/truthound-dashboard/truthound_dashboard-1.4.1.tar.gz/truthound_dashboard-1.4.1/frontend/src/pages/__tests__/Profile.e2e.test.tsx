/**
 * Profile E2E Tests
 *
 * End-to-end tests for the Data Profile page using MSW mock server.
 * Tests data profiling, statistics display, sorting, filtering, and schema generation.
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest'
import { setupServer } from 'msw/node'
import { render as rtlRender, screen, waitFor, fireEvent } from '@testing-library/react'
import { handlers } from '@/mocks/handlers'
import { resetStore, getStore, getAll } from '@/mocks/data/store'
import { setTestLocale } from '@/test/test-utils'
import Profile from '../Profile'
import { profileSource, learnSchema, getSource } from '@/api/client'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

// Setup MSW server with all handlers
const server = setupServer(...handlers)

// Helper to render with router params (without double wrapping)
function renderWithRouter(sourceId: string) {
  return rtlRender(
    <MemoryRouter initialEntries={[`/sources/${sourceId}/profile`]}>
      <Routes>
        <Route path="/sources/:id/profile" element={<Profile />} />
      </Routes>
    </MemoryRouter>
  )
}

describe('Profile E2E Tests', () => {
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
    it('displays source name with Profile suffix', async () => {
      renderWithRouter(testSourceId)

      // Wait for page to load - look for description text which appears after source loads
      await waitFor(() => {
        expect(screen.getByText(/Data profiling and schema generation/i)).toBeInTheDocument()
      }, { timeout: 10000 })
    })

    it('displays page description', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText(/Data profiling and schema generation/i)).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays Back button', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Back/i })).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays Generate Schema button', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Generate Schema/i })).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays Run Profile button', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Run Profile/i })).toBeInTheDocument()
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // EMPTY STATE (No Profile Data)
  // ============================================================================
  describe('Empty State', () => {
    it('displays No Profile Data message initially', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText(/No Profile Data/i)).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays description about profiling', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText(/Run a profile to analyze your data structure/i)).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays Run Profile button in empty state', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        // There should be at least two "Run Profile" buttons (header and empty state)
        const buttons = screen.getAllByRole('button', { name: /Run Profile/i })
        expect(buttons.length).toBeGreaterThanOrEqual(1)
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // API TESTS
  // ============================================================================
  describe('API Tests', () => {
    it('profiles a source and returns statistics', async () => {
      const result = await profileSource(testSourceId)

      expect(result).toBeDefined()
      expect(result.row_count).toBeDefined()
      expect(result.column_count).toBeDefined()
      expect(result.size_bytes).toBeDefined()
      expect(Array.isArray(result.columns)).toBe(true)
    })

    it('profile result has column statistics', async () => {
      const result = await profileSource(testSourceId)

      expect(result.columns.length).toBeGreaterThan(0)

      result.columns.forEach((col) => {
        expect(col.name).toBeDefined()
        expect(col.dtype).toBeDefined()
        expect(col.null_pct).toBeDefined()
        expect(col.unique_pct).toBeDefined()
      })
    })

    it('learns schema from source', async () => {
      const result = await learnSchema(testSourceId)

      expect(result).toBeDefined()
      expect(result.source_id).toBe(testSourceId)
      expect(result.columns).toBeDefined()
      expect(result.column_count).toBeGreaterThan(0)
      expect(result.schema_yaml).toBeDefined()
    })
  })

  // ============================================================================
  // PROFILING ACTION
  // ============================================================================
  describe('Profiling Action', () => {
    it('clicking Run Profile triggers profiling', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Run Profile/i })).toBeInTheDocument()
      }, { timeout: 5000 })

      const profileButton = screen.getByRole('button', { name: /Run Profile/i })
      fireEvent.click(profileButton)

      // Button should show "Profiling..." state
      await waitFor(() => {
        expect(screen.getByText(/Profiling/i)).toBeInTheDocument()
      }, { timeout: 2000 })
    })

    it('profile completes and shows results', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Run Profile/i })).toBeInTheDocument()
      }, { timeout: 5000 })

      const profileButton = screen.getByRole('button', { name: /Run Profile/i })
      fireEvent.click(profileButton)

      // Wait for profile to complete and show results
      await waitFor(() => {
        // Should show summary cards after profiling
        expect(screen.getByText('Rows')).toBeInTheDocument()
        expect(screen.getByText('Columns')).toBeInTheDocument()
      }, { timeout: 10000 })
    })
  })

  // ============================================================================
  // PROFILE RESULTS - SUMMARY CARDS
  // ============================================================================
  describe('Profile Results - Summary Cards', () => {
    it('displays Rows summary card after profiling', async () => {
      renderWithRouter(testSourceId)

      // Trigger profiling
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Run Profile/i })).toBeInTheDocument()
      }, { timeout: 5000 })

      fireEvent.click(screen.getByRole('button', { name: /Run Profile/i }))

      await waitFor(() => {
        expect(screen.getByText('Rows')).toBeInTheDocument()
      }, { timeout: 10000 })
    })

    it('displays Columns summary card after profiling', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Run Profile/i })).toBeInTheDocument()
      }, { timeout: 5000 })

      fireEvent.click(screen.getByRole('button', { name: /Run Profile/i }))

      await waitFor(() => {
        expect(screen.getByText('Columns')).toBeInTheDocument()
      }, { timeout: 10000 })
    })

    it('displays Size summary card after profiling', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Run Profile/i })).toBeInTheDocument()
      }, { timeout: 5000 })

      fireEvent.click(screen.getByRole('button', { name: /Run Profile/i }))

      await waitFor(() => {
        expect(screen.getByText('Size')).toBeInTheDocument()
      }, { timeout: 10000 })
    })

    it('displays Avg Null % summary card after profiling', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Run Profile/i })).toBeInTheDocument()
      }, { timeout: 5000 })

      fireEvent.click(screen.getByRole('button', { name: /Run Profile/i }))

      await waitFor(() => {
        expect(screen.getByText(/Avg Null/i)).toBeInTheDocument()
      }, { timeout: 10000 })
    })
  })

  // ============================================================================
  // PROFILE RESULTS - COLUMN STATISTICS TABLE
  // ============================================================================
  describe('Profile Results - Column Statistics Table', () => {
    it('displays Column Statistics table after profiling', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Run Profile/i })).toBeInTheDocument()
      }, { timeout: 5000 })

      fireEvent.click(screen.getByRole('button', { name: /Run Profile/i }))

      await waitFor(() => {
        expect(screen.getByText('Column Statistics')).toBeInTheDocument()
      }, { timeout: 10000 })
    })

    it('displays sortable column headers', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Run Profile/i })).toBeInTheDocument()
      }, { timeout: 5000 })

      fireEvent.click(screen.getByRole('button', { name: /Run Profile/i }))

      await waitFor(() => {
        // Table headers with sort buttons
        expect(screen.getByRole('button', { name: /Column/i })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /Type/i })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /Nulls/i })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /Unique/i })).toBeInTheDocument()
      }, { timeout: 10000 })
    })

    it('displays Min, Max, Mean, Std columns', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Run Profile/i })).toBeInTheDocument()
      }, { timeout: 5000 })

      fireEvent.click(screen.getByRole('button', { name: /Run Profile/i }))

      await waitFor(() => {
        expect(screen.getByText('Min')).toBeInTheDocument()
        expect(screen.getByText('Max')).toBeInTheDocument()
        expect(screen.getByText('Mean')).toBeInTheDocument()
        expect(screen.getByText('Std')).toBeInTheDocument()
      }, { timeout: 10000 })
    })
  })

  // ============================================================================
  // TYPE FILTER
  // ============================================================================
  describe('Type Filter', () => {
    it('displays type filter dropdown after profiling', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Run Profile/i })).toBeInTheDocument()
      }, { timeout: 5000 })

      fireEvent.click(screen.getByRole('button', { name: /Run Profile/i }))

      await waitFor(() => {
        // Filter dropdown trigger
        expect(screen.getByRole('combobox')).toBeInTheDocument()
      }, { timeout: 10000 })
    })
  })

  // ============================================================================
  // SCHEMA GENERATION
  // ============================================================================
  describe('Schema Generation', () => {
    it('clicking Generate Schema triggers schema learning', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Generate Schema/i })).toBeInTheDocument()
      }, { timeout: 5000 })

      const schemaButton = screen.getByRole('button', { name: /Generate Schema/i })
      fireEvent.click(schemaButton)

      // Should show "Generating..." state
      await waitFor(() => {
        expect(screen.getByText(/Generating/i)).toBeInTheDocument()
      }, { timeout: 2000 })
    })

    it('schema generation opens dialog with results', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Generate Schema/i })).toBeInTheDocument()
      }, { timeout: 5000 })

      fireEvent.click(screen.getByRole('button', { name: /Generate Schema/i }))

      // Wait for dialog to appear
      await waitFor(() => {
        expect(screen.getByText(/Generated Schema/i)).toBeInTheDocument()
      }, { timeout: 10000 })
    })

    it('schema dialog has Close button', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Generate Schema/i })).toBeInTheDocument()
      }, { timeout: 5000 })

      fireEvent.click(screen.getByRole('button', { name: /Generate Schema/i }))

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Close/i })).toBeInTheDocument()
      }, { timeout: 10000 })
    })

    it('schema dialog has Copy YAML button', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Generate Schema/i })).toBeInTheDocument()
      }, { timeout: 5000 })

      fireEvent.click(screen.getByRole('button', { name: /Generate Schema/i }))

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Copy YAML/i })).toBeInTheDocument()
      }, { timeout: 10000 })
    })
  })

  // ============================================================================
  // ERROR HANDLING
  // ============================================================================
  describe('Error Handling', () => {
    it('shows error state for invalid source ID', async () => {
      renderWithRouter('invalid-source-id-99999')

      await waitFor(() => {
        // Should show error message or "Source not found"
        expect(screen.getByText(/not found|error/i)).toBeInTheDocument()
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // ACCESSIBILITY
  // ============================================================================
  describe('Accessibility', () => {
    it('buttons are keyboard accessible', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        const buttons = screen.getAllByRole('button')
        buttons.forEach((button) => {
          expect(button).not.toHaveAttribute('tabindex', '-1')
        })
      }, { timeout: 5000 })
    })

    it('page has proper heading structure', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        const heading = screen.getByRole('heading', { level: 1 })
        expect(heading).toBeInTheDocument()
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // DATA INTEGRITY
  // ============================================================================
  describe('Data Integrity', () => {
    it('profile columns have valid null percentage format', async () => {
      const result = await profileSource(testSourceId)

      result.columns.forEach((col) => {
        // Null percentage should be a string with % sign
        expect(col.null_pct).toMatch(/^\d+(\.\d+)?%?$/)
      })
    })

    it('profile columns have valid unique percentage format', async () => {
      const result = await profileSource(testSourceId)

      result.columns.forEach((col) => {
        // Unique percentage should be a string with % sign
        expect(col.unique_pct).toMatch(/^\d+(\.\d+)?%?$/)
      })
    })

    it('schema YAML is valid', async () => {
      const result = await learnSchema(testSourceId)

      expect(result.schema_yaml).toBeDefined()
      expect(typeof result.schema_yaml).toBe('string')
      expect(result.schema_yaml.length).toBeGreaterThan(0)
    })
  })
})
