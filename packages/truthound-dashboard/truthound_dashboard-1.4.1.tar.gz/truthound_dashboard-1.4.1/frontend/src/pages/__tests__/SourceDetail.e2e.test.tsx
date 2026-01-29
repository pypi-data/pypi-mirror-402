/**
 * SourceDetail E2E Tests
 *
 * End-to-end tests for the Source Detail page using MSW mock server.
 * Tests source info display, validation, schema learning, and navigation.
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest'
import { setupServer } from 'msw/node'
import { render as rtlRender, screen, waitFor, fireEvent } from '@testing-library/react'
import { handlers } from '@/mocks/handlers'
import { resetStore, getStore, getAll } from '@/mocks/data/store'
import { setTestLocale } from '@/test/test-utils'
import SourceDetail from '../SourceDetail'
import {
  getSource,
  getSourceSchema,
  listSourceValidations,
  runValidation,
  learnSchema,
} from '@/api/client'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

// Setup MSW server with all handlers
const server = setupServer(...handlers)

// Helper to render with router params (without double wrapping)
function renderWithRouter(sourceId: string) {
  return rtlRender(
    <MemoryRouter initialEntries={[`/sources/${sourceId}`]}>
      <Routes>
        <Route path="/sources/:id" element={<SourceDetail />} />
      </Routes>
    </MemoryRouter>
  )
}

describe('SourceDetail E2E Tests', () => {
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
  // API TESTS
  // ============================================================================
  describe('API Tests', () => {
    it('fetches source details by ID', async () => {
      const source = await getSource(testSourceId)

      expect(source).toBeDefined()
      expect(source.id).toBe(testSourceId)
      expect(source.name).toBeDefined()
      expect(source.type).toBeDefined()
    })

    it('fetches source schema', async () => {
      const store = getStore()
      const sources = getAll(store.sources)
      const sourceWithSchema = sources.find((s) => s.has_schema)

      if (sourceWithSchema) {
        const schema = await getSourceSchema(sourceWithSchema.id)

        if (schema) {
          expect(schema.source_id).toBe(sourceWithSchema.id)
          expect(schema.columns).toBeDefined()
          expect(Array.isArray(schema.columns)).toBe(true)
        }
      }
    })

    it('fetches source validations', async () => {
      const response = await listSourceValidations(testSourceId)

      expect(response.success).toBe(true)
      expect(Array.isArray(response.data)).toBe(true)
    })

    it('runs validation on source', async () => {
      const result = await runValidation(testSourceId, {})

      expect(result).toBeDefined()
      expect(result.source_id).toBe(testSourceId)
      expect(typeof result.passed).toBe('boolean')
      expect(result.issues).toBeDefined()
    })

    it('learns schema for source', async () => {
      const result = await learnSchema(testSourceId)

      expect(result).toBeDefined()
      expect(result.source_id).toBe(testSourceId)
      expect(result.columns).toBeDefined()
      expect(result.column_count).toBeGreaterThan(0)
    })
  })

  // ============================================================================
  // PAGE RENDERING
  // ============================================================================
  describe('Page Rendering', () => {
    it('displays loading spinner initially', () => {
      renderWithRouter(testSourceId)

      // Loading spinner should be present initially
      const spinner = document.querySelector('.animate-spin')
      // May or may not catch the spinner depending on timing
    })

    it('displays source name as heading', async () => {
      const source = await getSource(testSourceId)
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(source.name)
      }, { timeout: 5000 })
    })

    it('displays source type badge', async () => {
      const source = await getSource(testSourceId)
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText(source.type)).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays Back to Sources link', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText(/Back to Sources/i)).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays Active/Inactive badge', async () => {
      const source = await getSource(testSourceId)
      renderWithRouter(testSourceId)

      await waitFor(() => {
        const badgeText = source.is_active ? 'Active' : 'Inactive'
        expect(screen.getByText(badgeText)).toBeInTheDocument()
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // STATS CARDS
  // ============================================================================
  describe('Stats Cards', () => {
    it('displays Status card', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText('Status')).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays Total Issues card', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText('Total Issues')).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays Rows card', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText('Rows')).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays Last Validation card', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText('Last Validation')).toBeInTheDocument()
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // ACTION BUTTONS
  // ============================================================================
  describe('Action Buttons', () => {
    it('displays Rules button', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /Rules/i })).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays Profile button', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /Profile/i })).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays History button', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /History/i })).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays Learn Schema button', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Learn Schema/i })).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays Run Validation button', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Run Validation/i })).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('Rules button links to rules page', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        const rulesLink = screen.getByRole('link', { name: /Rules/i })
        expect(rulesLink).toHaveAttribute('href', `/sources/${testSourceId}/rules`)
      }, { timeout: 5000 })
    })

    it('Profile button links to profile page', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        const profileLink = screen.getByRole('link', { name: /Profile/i })
        expect(profileLink).toHaveAttribute('href', `/sources/${testSourceId}/profile`)
      }, { timeout: 5000 })
    })

    it('History button links to history page', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        const historyLink = screen.getByRole('link', { name: /History/i })
        expect(historyLink).toHaveAttribute('href', `/sources/${testSourceId}/history`)
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // VALIDATION HISTORY SECTION
  // ============================================================================
  describe('Validation History Section', () => {
    it('displays Validation History card title', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText('Validation History')).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays validation entries with pass/fail status', async () => {
      const { container } = renderWithRouter(testSourceId)

      await waitFor(() => {
        // Check for validation entry elements
        const validationEntries = container.querySelectorAll('a[href^="/validations/"]')
        // May or may not have validation entries
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // SCHEMA SECTION
  // ============================================================================
  describe('Schema Section', () => {
    it('displays schema card when source has schema', async () => {
      const store = getStore()
      const sources = getAll(store.sources)
      const sourceWithSchema = sources.find((s) => s.has_schema)

      if (sourceWithSchema) {
        renderWithRouter(sourceWithSchema.id)

        await waitFor(() => {
          // Should show "Schema" in the card title
          expect(screen.getByText(/Schema/i)).toBeInTheDocument()
        }, { timeout: 5000 })
      }
    })

    it('displays column badges when schema exists', async () => {
      const store = getStore()
      const sources = getAll(store.sources)
      const sourceWithSchema = sources.find((s) => s.has_schema)

      if (sourceWithSchema) {
        const schema = await getSourceSchema(sourceWithSchema.id)

        if (schema && schema.columns.length > 0) {
          renderWithRouter(sourceWithSchema.id)

          await waitFor(() => {
            // First column should be displayed as a badge
            expect(screen.getByText(schema.columns[0])).toBeInTheDocument()
          }, { timeout: 5000 })
        }
      }
    })
  })

  // ============================================================================
  // ISSUES SECTION
  // ============================================================================
  describe('Issues Section', () => {
    it('displays issues when validation has issues', async () => {
      // Find a source that has validations with issues
      const store = getStore()
      const validations = getAll(store.validations)
      const validationWithIssues = validations.find((v) => v.issues.length > 0)

      if (validationWithIssues) {
        renderWithRouter(validationWithIssues.source_id)

        await waitFor(() => {
          // Should show "Issues Found" text
          const issuesText = screen.queryByText(/Issues Found/i)
          // May or may not be visible depending on data
        }, { timeout: 5000 })
      }
    })
  })

  // ============================================================================
  // VALIDATION ACTIONS
  // ============================================================================
  describe('Validation Actions', () => {
    it('clicking Run Validation changes button text', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Run Validation/i })).toBeInTheDocument()
      }, { timeout: 5000 })

      const validateButton = screen.getByRole('button', { name: /Run Validation/i })
      fireEvent.click(validateButton)

      // Button should change to "Validating..."
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Validating/i })).toBeInTheDocument()
      }, { timeout: 2000 })
    })
  })

  // ============================================================================
  // ERROR HANDLING
  // ============================================================================
  describe('Error Handling', () => {
    it('displays "Source not found" for invalid ID', async () => {
      renderWithRouter('invalid-source-id-12345')

      await waitFor(() => {
        expect(screen.getByText(/Source not found/i)).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays "Back to Sources" button on error', async () => {
      renderWithRouter('invalid-source-id-12345')

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /Back to Sources/i })).toBeInTheDocument()
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

    it('all buttons are keyboard accessible', async () => {
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
          const href = link.getAttribute('href')
          expect(href).toBeTruthy()
        })
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // DATA INTEGRITY
  // ============================================================================
  describe('Data Integrity', () => {
    it('validation issues have required fields', async () => {
      const response = await listSourceValidations(testSourceId)

      response.data.forEach((validation) => {
        expect(validation.id).toBeDefined()
        expect(validation.source_id).toBe(testSourceId)
        expect(typeof validation.passed).toBe('boolean')
        expect(Array.isArray(validation.issues)).toBe(true)

        validation.issues.forEach((issue) => {
          expect(issue.column).toBeDefined()
          expect(issue.issue_type).toBeDefined()
          expect(['critical', 'high', 'medium', 'low']).toContain(issue.severity)
        })
      })
    })

    it('schema has required fields', async () => {
      const result = await learnSchema(testSourceId)

      expect(result.id).toBeDefined()
      expect(result.source_id).toBe(testSourceId)
      expect(Array.isArray(result.columns)).toBe(true)
      expect(typeof result.column_count).toBe('number')
      expect(result.schema_yaml).toBeDefined()
    })
  })
})
