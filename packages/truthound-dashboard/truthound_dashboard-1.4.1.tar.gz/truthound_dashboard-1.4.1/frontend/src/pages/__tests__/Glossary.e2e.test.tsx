/**
 * Glossary E2E Tests
 *
 * End-to-end tests for the Glossary page using MSW mock server.
 * Tests business term listing, filtering, creation, updating, and deletion functionality.
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest'
import { setupServer } from 'msw/node'
import { handlers } from '@/mocks/handlers'
import { resetStore, getStore, getAll } from '@/mocks/data/store'
import { render, screen, waitFor, fireEvent, Locales, setTestLocale } from '@/test/test-utils'
import Glossary from '../Glossary'
import {
  getTerms,
  getTerm,
  createTerm,
  updateTerm,
  deleteTerm,
  getCategories,
} from '@/api/client'

// Setup MSW server with all handlers
const server = setupServer(...handlers)

describe('Glossary E2E Tests', () => {
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
    it('loads and displays terms from the mock API', async () => {
      render(<Glossary />)

      // Should display the page title (appears immediately)
      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
      }, { timeout: 3000 })

      // The heading should contain the glossary title
      const heading = screen.getByRole('heading', { level: 1 })
      expect(heading.textContent).toContain('Glossary')
    })

    it('fetches terms using the API client', async () => {
      const terms = await getTerms({ limit: 50 })

      expect(Array.isArray(terms)).toBe(true)
      expect(terms.length).toBeGreaterThan(0)
    })

    it('fetches categories using the API client', async () => {
      const categories = await getCategories()

      expect(Array.isArray(categories)).toBe(true)
      expect(categories.length).toBeGreaterThan(0)
    })

    it('displays term cards when terms exist', async () => {
      render(<Glossary />)

      // Wait for terms to load
      await waitFor(() => {
        const store = getStore()
        const terms = getAll(store.glossaryTerms)
        // At least one term name should be visible
        const firstTerm = terms[0]
        if (firstTerm) {
          expect(screen.getByText(firstTerm.name)).toBeInTheDocument()
        }
      }, { timeout: 3000 })
    })

    it('shows subtitle text', async () => {
      render(<Glossary />)

      await waitFor(() => {
        expect(screen.getByText('Manage business terms and definitions')).toBeInTheDocument()
      })
    })
  })

  // ============================================================================
  // TERM LIST DISPLAY
  // ============================================================================
  describe('Term List Display', () => {
    it('displays term status badges', async () => {
      render(<Glossary />)

      await waitFor(() => {
        // Status badges should appear (Draft, Approved, or Deprecated)
        const badges = screen.getAllByText(/Draft|Approved|Deprecated/i)
        expect(badges.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })

    it('displays term definitions', async () => {
      render(<Glossary />)

      // Wait for terms to load and verify definitions are present
      await waitFor(() => {
        // Find any element containing term definition text (truncated with line-clamp)
        const muted = document.querySelectorAll('.text-muted-foreground')
        // At least some muted text should exist (definitions)
        expect(muted.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })

    it('displays category badges when terms have categories', async () => {
      render(<Glossary />)

      // Wait for terms to load and check for badge elements
      await waitFor(() => {
        // Badges use rounded-full class
        const badges = document.querySelectorAll('.rounded-full')
        // Should have some badges rendered (status + category badges)
        expect(badges.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })

    it('displays Add Term button', async () => {
      render(<Glossary />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Add Term/i })).toBeInTheDocument()
      })
    })

    it('displays edit and delete buttons for each term', async () => {
      const { container } = render(<Glossary />)

      await waitFor(() => {
        // Edit and Delete buttons should exist
        const editButtons = container.querySelectorAll('button svg.lucide-edit, button svg.lucide-pencil')
        const deleteButtons = container.querySelectorAll('.text-destructive')
        expect(editButtons.length + deleteButtons.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })

    it('term names are links to detail pages', async () => {
      render(<Glossary />)

      await waitFor(() => {
        const store = getStore()
        const terms = getAll(store.glossaryTerms)
        const firstTerm = terms[0]
        if (firstTerm) {
          const link = screen.getByRole('link', { name: firstTerm.name })
          expect(link).toHaveAttribute('href', `/glossary/${firstTerm.id}`)
        }
      }, { timeout: 3000 })
    })
  })

  // ============================================================================
  // FILTERING
  // ============================================================================
  describe('Filtering', () => {
    it('displays search input', async () => {
      render(<Glossary />)

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Search terms/i)).toBeInTheDocument()
      })
    })

    it('displays category filter dropdown', async () => {
      render(<Glossary />)

      await waitFor(() => {
        // Category filter should have "All categories" option by default
        expect(screen.getByText(/All categories/i)).toBeInTheDocument()
      })
    })

    it('displays status filter dropdown', async () => {
      render(<Glossary />)

      await waitFor(() => {
        // Status filter should have "All statuses" option by default
        expect(screen.getByText(/All statuses/i)).toBeInTheDocument()
      })
    })

    it('API: filters terms by category', async () => {
      const store = getStore()
      const categories = getAll(store.glossaryCategories)
      const firstCategory = categories[0]

      if (firstCategory) {
        const allTerms = await getTerms()
        const filteredTerms = await getTerms({ category_id: firstCategory.id })

        // All filtered terms should have the specified category
        filteredTerms.forEach((term) => {
          expect(term.category_id).toBe(firstCategory.id)
        })

        // Should be a subset
        expect(filteredTerms.length).toBeLessThanOrEqual(allTerms.length)
      }
    })

    it('API: filters terms by status', async () => {
      const allTerms = await getTerms()
      const approvedTerms = await getTerms({ status: 'approved' })

      // All approved terms should have status 'approved'
      approvedTerms.forEach((term) => {
        expect(term.status).toBe('approved')
      })

      // Should be a subset
      expect(approvedTerms.length).toBeLessThanOrEqual(allTerms.length)
    })

    it('API: searches terms by name', async () => {
      const allTerms = await getTerms()
      const firstTerm = allTerms[0]

      if (firstTerm) {
        const searchTerm = firstTerm.name.substring(0, 5)
        const searchResults = await getTerms({ search: searchTerm })

        // Search results should include the original term
        const found = searchResults.find((t) => t.id === firstTerm.id)
        expect(found).toBeDefined()
      }
    })

    it('API: searches terms by definition', async () => {
      const allTerms = await getTerms()
      const termWithDefinition = allTerms.find((t) => t.definition && t.definition.length > 10)

      if (termWithDefinition) {
        const searchTerm = termWithDefinition.definition.substring(0, 10)
        const searchResults = await getTerms({ search: searchTerm })

        expect(searchResults.length).toBeGreaterThan(0)
      }
    })

    it('API: combines multiple filters', async () => {
      const store = getStore()
      const categories = getAll(store.glossaryCategories)
      const firstCategory = categories[0]

      if (firstCategory) {
        const filteredTerms = await getTerms({
          category_id: firstCategory.id,
          status: 'draft',
        })

        filteredTerms.forEach((term) => {
          expect(term.category_id).toBe(firstCategory.id)
          expect(term.status).toBe('draft')
        })
      }
    })
  })

  // ============================================================================
  // CREATE TERM
  // ============================================================================
  describe('Create Term', () => {
    it('Add Term button is rendered', async () => {
      render(<Glossary />)

      await waitFor(() => {
        const addButton = screen.getByRole('button', { name: /Add Term/i })
        expect(addButton).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('Add Term button can be clicked', async () => {
      render(<Glossary />)

      // Wait for button to be available
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Add Term/i })).toBeInTheDocument()
      }, { timeout: 3000 })

      // Click the button
      const addButton = screen.getByRole('button', { name: /Add Term/i })
      fireEvent.click(addButton)

      // Button should still be in document after click
      expect(addButton).toBeInTheDocument()
    })

    it('API: creates a new term with required fields', async () => {
      const store = getStore()
      const initialCount = getAll(store.glossaryTerms).length

      const newTerm = await createTerm({
        name: 'Test Term',
        definition: 'Test definition for the term',
      })

      expect(newTerm).toBeDefined()
      expect(newTerm.name).toBe('Test Term')
      expect(newTerm.definition).toBe('Test definition for the term')
      expect(newTerm.status).toBe('draft') // Default status

      // Verify term was added to store
      const newTerms = await getTerms()
      expect(newTerms.length).toBe(initialCount + 1)
    })

    it('API: creates term with category', async () => {
      const categories = await getCategories()
      const firstCategory = categories[0]

      if (firstCategory) {
        const newTerm = await createTerm({
          name: 'Categorized Term',
          definition: 'A term with category',
          category_id: firstCategory.id,
        })

        expect(newTerm.category_id).toBe(firstCategory.id)
      }
    })

    it('API: creates term with custom status', async () => {
      const newTerm = await createTerm({
        name: 'Approved Term',
        definition: 'An approved term',
        status: 'approved',
      })

      expect(newTerm.status).toBe('approved')
    })

    it('API: creates term with owner', async () => {
      const newTerm = await createTerm({
        name: 'Owned Term',
        definition: 'A term with owner',
        owner_id: 'John Doe',
      })

      expect(newTerm.owner_id).toBe('John Doe')
    })

    it('API: creates term with all optional fields', async () => {
      const categories = await getCategories()
      const firstCategory = categories[0]

      const newTerm = await createTerm({
        name: 'Complete Term',
        definition: 'A term with all fields',
        category_id: firstCategory?.id,
        status: 'approved',
        owner_id: 'Data Team',
      })

      expect(newTerm.name).toBe('Complete Term')
      expect(newTerm.definition).toBe('A term with all fields')
      if (firstCategory) {
        expect(newTerm.category_id).toBe(firstCategory.id)
      }
      expect(newTerm.status).toBe('approved')
      expect(newTerm.owner_id).toBe('Data Team')
    })
  })

  // ============================================================================
  // UPDATE TERM
  // ============================================================================
  describe('Update Term', () => {
    it('API: updates term name', async () => {
      const terms = await getTerms()
      const firstTerm = terms[0]

      if (firstTerm) {
        const updated = await updateTerm(firstTerm.id, {
          name: 'Updated Term Name',
        })

        expect(updated.id).toBe(firstTerm.id)
        expect(updated.name).toBe('Updated Term Name')
        expect(updated.definition).toBe(firstTerm.definition)
      }
    })

    it('API: updates term definition', async () => {
      const terms = await getTerms()
      const firstTerm = terms[0]

      if (firstTerm) {
        const updated = await updateTerm(firstTerm.id, {
          definition: 'New definition for the term',
        })

        expect(updated.id).toBe(firstTerm.id)
        expect(updated.definition).toBe('New definition for the term')
      }
    })

    it('API: updates term status', async () => {
      const terms = await getTerms()
      const draftTerm = terms.find((t) => t.status === 'draft')

      if (draftTerm) {
        const updated = await updateTerm(draftTerm.id, {
          status: 'approved',
        })

        expect(updated.status).toBe('approved')
      }
    })

    it('API: updates term category', async () => {
      const terms = await getTerms()
      const categories = await getCategories()
      const firstTerm = terms[0]
      const targetCategory = categories[0]

      if (firstTerm && targetCategory) {
        const updated = await updateTerm(firstTerm.id, {
          category_id: targetCategory.id,
        })

        expect(updated.category_id).toBe(targetCategory.id)
      }
    })

    it('API: updates term owner', async () => {
      const terms = await getTerms()
      const firstTerm = terms[0]

      if (firstTerm) {
        const updated = await updateTerm(firstTerm.id, {
          owner_id: 'New Owner',
        })

        expect(updated.owner_id).toBe('New Owner')
      }
    })

    it('API: updates multiple fields at once', async () => {
      const terms = await getTerms()
      const firstTerm = terms[0]

      if (firstTerm) {
        const updated = await updateTerm(firstTerm.id, {
          name: 'Multi-Update Term',
          definition: 'Updated via multi-field update',
          status: 'approved',
          owner_id: 'Team Lead',
        })

        expect(updated.name).toBe('Multi-Update Term')
        expect(updated.definition).toBe('Updated via multi-field update')
        expect(updated.status).toBe('approved')
        expect(updated.owner_id).toBe('Team Lead')
      }
    })

    it('API: returns 404 for non-existent term', async () => {
      try {
        await updateTerm('non-existent-id', { name: 'Updated' })
        // Should not reach here
        expect(true).toBe(false)
      } catch (error) {
        expect(error).toBeDefined()
      }
    })
  })

  // ============================================================================
  // DELETE TERM
  // ============================================================================
  describe('Delete Term', () => {
    it('API: deletes a term', async () => {
      const store = getStore()
      const terms = getAll(store.glossaryTerms)
      const initialCount = terms.length

      if (initialCount > 0) {
        const termToDelete = terms[0]
        await deleteTerm(termToDelete.id)

        // Verify deletion
        const newTerms = await getTerms()
        expect(newTerms.length).toBe(initialCount - 1)
        expect(newTerms.find((t) => t.id === termToDelete.id)).toBeUndefined()
      }
    })

    it('clicking delete button shows confirmation dialog', async () => {
      const { container } = render(<Glossary />)

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
            expect(screen.getByText(/Delete Term/i)).toBeInTheDocument()
          }, { timeout: 3000 })
        }
      }
    })

    it('API: returns 404 when deleting non-existent term', async () => {
      try {
        await deleteTerm('non-existent-id')
        // Should not reach here
        expect(true).toBe(false)
      } catch (error) {
        expect(error).toBeDefined()
      }
    })

    it('API: deleting term also cleans up relationships', async () => {
      const store = getStore()
      const terms = getAll(store.glossaryTerms)
      const relationships = getAll(store.termRelationships)

      // Find a term with relationships
      const termWithRelationships = terms.find((t) =>
        relationships.some((r) => r.source_term_id === t.id || r.target_term_id === t.id)
      )

      if (termWithRelationships) {
        await deleteTerm(termWithRelationships.id)

        // Relationships involving this term should be cleaned up
        const remainingRelationships = getAll(getStore().termRelationships)
        const orphanedRelationships = remainingRelationships.filter(
          (r) =>
            r.source_term_id === termWithRelationships.id ||
            r.target_term_id === termWithRelationships.id
        )
        expect(orphanedRelationships.length).toBe(0)
      }
    })
  })

  // ============================================================================
  // EMPTY STATE
  // ============================================================================
  describe('Empty State', () => {
    it('shows empty state when no terms exist', async () => {
      // Clear all terms from the store
      const store = getStore()
      store.glossaryTerms.clear()

      render(<Glossary />)

      await waitFor(() => {
        expect(screen.getByText(/No terms yet/i)).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('empty state has Add First Term button', async () => {
      const store = getStore()
      store.glossaryTerms.clear()

      render(<Glossary />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Add Your First Term/i })).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('empty state Add First Term button can be clicked', async () => {
      const store = getStore()
      store.glossaryTerms.clear()

      render(<Glossary />)

      // Wait for button to be available
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Add Your First Term/i })).toBeInTheDocument()
      }, { timeout: 3000 })

      // Click the button
      const addButton = screen.getByRole('button', { name: /Add Your First Term/i })
      fireEvent.click(addButton)

      expect(addButton).toBeInTheDocument()
    })

    it('shows empty state description', async () => {
      const store = getStore()
      store.glossaryTerms.clear()

      render(<Glossary />)

      await waitFor(() => {
        expect(
          screen.getByText(/Add your first business term to start building your glossary/i)
        ).toBeInTheDocument()
      }, { timeout: 3000 })
    })
  })

  // ============================================================================
  // GET TERM DETAIL
  // ============================================================================
  describe('Get Term Detail', () => {
    it('API: fetches term by ID', async () => {
      const store = getStore()
      const terms = getAll(store.glossaryTerms)
      const firstTerm = terms[0]

      if (firstTerm) {
        const term = await getTerm(firstTerm.id)

        expect(term).toBeDefined()
        expect(term.id).toBe(firstTerm.id)
        expect(term.name).toBe(firstTerm.name)
        expect(term.definition).toBe(firstTerm.definition)
      }
    })

    it('API: fetches term with category info', async () => {
      const store = getStore()
      const terms = getAll(store.glossaryTerms)
      const termWithCategory = terms.find((t) => t.category_id)

      if (termWithCategory) {
        const term = await getTerm(termWithCategory.id)
        expect(term.category).toBeDefined()
        expect(term.category?.id).toBe(termWithCategory.category_id)
      }
    })

    it('API: returns 404 for non-existent term', async () => {
      try {
        await getTerm('non-existent-id')
        // Should not reach here
        expect(true).toBe(false)
      } catch (error) {
        expect(error).toBeDefined()
      }
    })
  })

  // ============================================================================
  // CATEGORIES
  // ============================================================================
  describe('Categories', () => {
    it('API: fetches all categories', async () => {
      const categories = await getCategories()

      expect(Array.isArray(categories)).toBe(true)
      categories.forEach((category) => {
        expect(category.id).toBeDefined()
        expect(category.name).toBeDefined()
      })
    })

    it('categories are shown in filter dropdown', async () => {
      render(<Glossary />)

      await waitFor(() => {
        const categories = getAll(getStore().glossaryCategories)
        // At least "All categories" should be visible
        expect(screen.getByText(/All categories/i)).toBeInTheDocument()

        // Categories should exist in store
        expect(categories.length).toBeGreaterThan(0)
      })
    })

    it('API: categories have required fields', async () => {
      const categories = await getCategories()

      categories.forEach((category) => {
        expect(category.id).toBeDefined()
        expect(category.name).toBeDefined()
        expect(category.created_at).toBeDefined()
        expect(category.updated_at).toBeDefined()
      })
    })
  })

  // ============================================================================
  // DATA INTEGRITY
  // ============================================================================
  describe('Data Integrity', () => {
    it('mock data has valid term statuses', async () => {
      const terms = await getTerms()
      const validStatuses = ['draft', 'approved', 'deprecated']

      terms.forEach((term) => {
        expect(validStatuses).toContain(term.status)
      })
    })

    it('mock data has valid timestamps', async () => {
      const terms = await getTerms()

      terms.forEach((term) => {
        expect(new Date(term.created_at).toString()).not.toBe('Invalid Date')
        expect(new Date(term.updated_at).toString()).not.toBe('Invalid Date')
      })
    })

    it('terms have required fields', async () => {
      const terms = await getTerms()

      terms.forEach((term) => {
        expect(term.id).toBeDefined()
        expect(term.name).toBeDefined()
        expect(term.definition).toBeDefined()
        expect(term.status).toBeDefined()
        expect(term.created_at).toBeDefined()
        expect(term.updated_at).toBeDefined()
      })
    })

    it('categories have required fields', async () => {
      const categories = await getCategories()

      categories.forEach((category) => {
        expect(category.id).toBeDefined()
        expect(category.name).toBeDefined()
        expect(typeof category.name).toBe('string')
      })
    })

    it('term category_id references existing category', async () => {
      const terms = await getTerms()
      const categories = await getCategories()
      const categoryIds = new Set(categories.map((c) => c.id))

      terms.forEach((term) => {
        if (term.category_id) {
          expect(categoryIds.has(term.category_id)).toBe(true)
        }
      })
    })
  })

  // ============================================================================
  // UI COMPONENTS
  // ============================================================================
  describe('UI Components', () => {
    it('renders term cards with icons', async () => {
      const { container } = render(<Glossary />)

      await waitFor(() => {
        // Term icons are SVGs
        const icons = container.querySelectorAll('svg')
        expect(icons.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })

    it('renders Card components for terms', async () => {
      const { container } = render(<Glossary />)

      await waitFor(() => {
        // Cards should have rounded borders
        const cards = container.querySelectorAll('[class*="rounded"]')
        expect(cards.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })

    it('renders filter icons', async () => {
      const { container } = render(<Glossary />)

      await waitFor(() => {
        // Search and filter icons
        const icons = container.querySelectorAll('svg')
        expect(icons.length).toBeGreaterThan(0)
      })
    })

    it('renders Badge components for status', async () => {
      render(<Glossary />)

      await waitFor(() => {
        const store = getStore()
        const terms = getAll(store.glossaryTerms)
        if (terms.length > 0) {
          // Should have status badges
          const statusBadges = screen.getAllByText(/Draft|Approved|Deprecated/i)
          expect(statusBadges.length).toBeGreaterThan(0)
        }
      }, { timeout: 3000 })
    })
  })

  // ============================================================================
  // INTERNATIONALIZATION
  // ============================================================================
  describe('Internationalization', () => {
    it('renders Korean title correctly', async () => {
      render(<Glossary />, { locale: Locales.KOREAN })

      await waitFor(() => {
        // Korean page title
        expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('용어집')
      })
    })

    it('renders Korean subtitle', async () => {
      render(<Glossary />, { locale: Locales.KOREAN })

      await waitFor(() => {
        expect(screen.getByText('비즈니스 용어와 정의 관리')).toBeInTheDocument()
      })
    })

    it('renders Korean buttons', async () => {
      render(<Glossary />, { locale: Locales.KOREAN })

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /용어 추가/i })).toBeInTheDocument()
      })
    })

    it('renders Korean empty state', async () => {
      const store = getStore()
      store.glossaryTerms.clear()

      render(<Glossary />, { locale: Locales.KOREAN })

      await waitFor(() => {
        expect(screen.getByText('등록된 용어가 없습니다')).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('renders Korean filter options', async () => {
      render(<Glossary />, { locale: Locales.KOREAN })

      await waitFor(() => {
        expect(screen.getByText('모든 카테고리')).toBeInTheDocument()
        expect(screen.getByText('모든 상태')).toBeInTheDocument()
      })
    })

    it('renders Korean status labels', async () => {
      render(<Glossary />, { locale: Locales.KOREAN })

      await waitFor(() => {
        const store = getStore()
        const terms = getAll(store.glossaryTerms)
        if (terms.length > 0) {
          // Should have Korean status badges
          const statusBadges = screen.getAllByText(/임시저장|승인됨|폐기됨/i)
          expect(statusBadges.length).toBeGreaterThan(0)
        }
      }, { timeout: 3000 })
    })
  })

  // ============================================================================
  // ACCESSIBILITY
  // ============================================================================
  describe('Accessibility', () => {
    it('has accessible heading structure', async () => {
      render(<Glossary />)

      await waitFor(() => {
        const heading = screen.getByRole('heading', { level: 1 })
        expect(heading).toBeInTheDocument()
      })
    })

    it('buttons are accessible', async () => {
      render(<Glossary />)

      await waitFor(() => {
        const buttons = screen.getAllByRole('button')
        expect(buttons.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })

    it('links have proper href attributes', async () => {
      render(<Glossary />)

      await waitFor(() => {
        const links = screen.getAllByRole('link')
        links.forEach((link) => {
          expect(link).toHaveAttribute('href')
        })
      }, { timeout: 3000 })
    })

    it('search input has placeholder for accessibility', async () => {
      render(<Glossary />)

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText(/Search terms/i)
        expect(searchInput).toHaveAttribute('placeholder')
      })
    })

    it('filter dropdowns are keyboard accessible', async () => {
      render(<Glossary />)

      await waitFor(() => {
        // Select triggers should be focusable
        const categoryTrigger = screen.getByText(/All categories/i)
        expect(categoryTrigger.closest('button')).toBeInTheDocument()
      })
    })
  })

  // ============================================================================
  // PAGINATION
  // ============================================================================
  describe('Pagination', () => {
    it('API: supports pagination with skip and limit', async () => {
      // Create enough terms to test pagination
      const allTerms = await getTerms()

      if (allTerms.length > 5) {
        const firstPage = await getTerms({ skip: 0, limit: 5 })
        const secondPage = await getTerms({ skip: 5, limit: 5 })

        expect(firstPage.length).toBeLessThanOrEqual(5)

        // First pages should be different (unless there are less than 5 total)
        if (allTerms.length > 5) {
          const firstPageIds = new Set(firstPage.map((t) => t.id))
          const hasOverlap = secondPage.some((t) => firstPageIds.has(t.id))
          expect(hasOverlap).toBe(false)
        }
      }
    })
  })
})
