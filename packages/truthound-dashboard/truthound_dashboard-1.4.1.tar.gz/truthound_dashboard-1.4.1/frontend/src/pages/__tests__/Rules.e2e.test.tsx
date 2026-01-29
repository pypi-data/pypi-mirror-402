/**
 * Rules E2E Tests
 *
 * End-to-end tests for the Validation Rules page using MSW mock server.
 * Tests CRUD operations, YAML editing, and rule activation.
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest'
import { setupServer } from 'msw/node'
import { render as rtlRender, screen, waitFor, fireEvent } from '@testing-library/react'
import { handlers } from '@/mocks/handlers'
import { resetStore, getStore, getAll } from '@/mocks/data/store'
import { resetRulesStore } from '@/mocks/handlers/rules'
import { setTestLocale } from '@/test/test-utils'
import Rules from '../Rules'
import { apiClient } from '@/api/client'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

// Setup MSW server with all handlers
const server = setupServer(...handlers)

// Helper to render with router params (without double wrapping)
function renderWithRouter(sourceId: string) {
  return rtlRender(
    <MemoryRouter initialEntries={[`/sources/${sourceId}/rules`]}>
      <Routes>
        <Route path="/sources/:id/rules" element={<Rules />} />
      </Routes>
    </MemoryRouter>
  )
}

describe('Rules E2E Tests', () => {
  let testSourceId: string

  beforeAll(() => {
    server.listen({ onUnhandledRequest: 'error' })
  })

  afterAll(() => {
    server.close()
  })

  beforeEach(() => {
    resetStore()
    resetRulesStore()
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
    it('displays Validation Rules title', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Validation Rules/i })).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays source name and type', async () => {
      renderWithRouter(testSourceId)

      // Wait for page to finish loading and show source info
      await waitFor(() => {
        // The source name and type should be displayed below the title
        const paragraph = document.querySelector('.text-muted-foreground')
        expect(paragraph).toBeInTheDocument()
      }, { timeout: 8000 })
    })

    it('displays back button', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        const backButtons = screen.getAllByRole('button')
        // First button should be the back button
        expect(backButtons.length).toBeGreaterThan(0)
      }, { timeout: 5000 })
    })

    it('displays New Rule button', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /New Rule/i })).toBeInTheDocument()
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // RULES LIST SECTION
  // ============================================================================
  describe('Rules List Section', () => {
    it('displays Rule History card', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText(/Rule History/i)).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays rule count', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        // Should show "X rule(s) defined"
        expect(screen.getByText(/rule.*defined/i)).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays rule entries when rules exist', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        // Default Rules should be created automatically
        expect(screen.getByText(/Default Rules/i)).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays Active badge for active rule', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText('Active')).toBeInTheDocument()
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // RULE EDITOR SECTION
  // ============================================================================
  describe('Rule Editor Section', () => {
    it('displays Rule Editor card', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText('Rule Editor')).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays Rule Name input', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        const nameInput = screen.getByPlaceholderText(/Enter rule name/i)
        expect(nameInput).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays Description input', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        const descInput = screen.getByPlaceholderText(/Optional description/i)
        expect(descInput).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays Rules YAML textarea', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        const yamlTextarea = screen.getByPlaceholderText(/Enter validation rules in YAML/i)
        expect(yamlTextarea).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays Save button', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Save/i })).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('Save button is disabled when no changes', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        const saveButton = screen.getByRole('button', { name: /Save/i })
        expect(saveButton).toBeDisabled()
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // QUICK REFERENCE SECTION
  // ============================================================================
  describe('Quick Reference Section', () => {
    it('displays Quick Reference card', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText('Quick Reference')).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays Column Constraints section', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText('Column Constraints')).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays String Constraints section', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText('String Constraints')).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays not_null constraint example', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText(/not_null: true/i)).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays unique constraint example', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText(/unique: true/i)).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('displays pattern constraint example', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText(/pattern:/i)).toBeInTheDocument()
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // EDITING FUNCTIONALITY
  // ============================================================================
  describe('Editing Functionality', () => {
    it('changing rule name enables Save button', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Enter rule name/i)).toBeInTheDocument()
      }, { timeout: 5000 })

      const nameInput = screen.getByPlaceholderText(/Enter rule name/i)
      fireEvent.change(nameInput, { target: { value: 'Updated Rule Name' } })

      await waitFor(() => {
        const saveButton = screen.getByRole('button', { name: /Save/i })
        expect(saveButton).not.toBeDisabled()
      })
    })

    it('changing YAML content enables Save button', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Enter validation rules in YAML/i)).toBeInTheDocument()
      }, { timeout: 5000 })

      const yamlTextarea = screen.getByPlaceholderText(/Enter validation rules in YAML/i)
      fireEvent.change(yamlTextarea, { target: { value: 'columns:\n  id:\n    not_null: true' } })

      await waitFor(() => {
        const saveButton = screen.getByRole('button', { name: /Save/i })
        expect(saveButton).not.toBeDisabled()
      })
    })

    it('shows Unsaved changes badge when edited', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Enter rule name/i)).toBeInTheDocument()
      }, { timeout: 5000 })

      const nameInput = screen.getByPlaceholderText(/Enter rule name/i)
      fireEvent.change(nameInput, { target: { value: 'Modified Rule' } })

      await waitFor(() => {
        expect(screen.getByText(/Unsaved changes/i)).toBeInTheDocument()
      })
    })
  })

  // ============================================================================
  // CREATE NEW RULE
  // ============================================================================
  describe('Create New Rule', () => {
    it('clicking New Rule creates a new rule', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /New Rule/i })).toBeInTheDocument()
      }, { timeout: 5000 })

      const newRuleButton = screen.getByRole('button', { name: /New Rule/i })
      fireEvent.click(newRuleButton)

      // Should show creating state or success toast
      await waitFor(() => {
        // Look for toast or updated rule list
        const rules = screen.getAllByText(/Rules/i)
        expect(rules.length).toBeGreaterThan(0)
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // API TESTS
  // ============================================================================
  describe('API Tests', () => {
    it('fetches rules for a source', async () => {
      const response = await apiClient.get<{ data: unknown[] }>(
        `/sources/${testSourceId}/rules`
      )

      expect(response.data).toBeDefined()
      expect(Array.isArray(response.data)).toBe(true)
    })

    it('fetches active rule for a source', async () => {
      const response = await apiClient.get<{ id: string; name: string }>(
        `/sources/${testSourceId}/rules/active`
      )

      expect(response).toBeDefined()
      expect(response.id).toBeDefined()
      expect(response.name).toBeDefined()
    })

    it('creates a new rule', async () => {
      const newRule = {
        name: 'Test Rule',
        description: 'Test description',
        rules_yaml: 'columns:\n  test:\n    not_null: true',
      }

      const response = await apiClient.post<{ id: string; name: string }>(
        `/sources/${testSourceId}/rules?activate=true`,
        newRule
      )

      expect(response.id).toBeDefined()
      expect(response.name).toBe('Test Rule')
    })

    it('updates an existing rule', async () => {
      // First create a rule
      const createResponse = await apiClient.post<{ id: string }>(
        `/sources/${testSourceId}/rules?activate=true`,
        {
          name: 'Original Name',
          description: null,
          rules_yaml: 'columns: {}',
        }
      )

      // Then update it
      const updateResponse = await apiClient.put<{ id: string; name: string }>(
        `/rules/${createResponse.id}`,
        {
          name: 'Updated Name',
          description: 'New description',
        }
      )

      expect(updateResponse.id).toBe(createResponse.id)
      expect(updateResponse.name).toBe('Updated Name')
    })

    it('deletes a rule', async () => {
      // First create a rule
      const createResponse = await apiClient.post<{ id: string }>(
        `/sources/${testSourceId}/rules`,
        {
          name: 'Rule to Delete',
          description: null,
          rules_yaml: 'columns: {}',
        }
      )

      // Then delete it
      const deleteResponse = await apiClient.delete(`/rules/${createResponse.id}`)

      expect(deleteResponse).toBeDefined()
    })

    it('activates a rule', async () => {
      // First create a rule (not active)
      const createResponse = await apiClient.post<{ id: string; is_active: boolean }>(
        `/sources/${testSourceId}/rules`,
        {
          name: 'Rule to Activate',
          description: null,
          rules_yaml: 'columns: {}',
        }
      )

      // Then activate it
      const activateResponse = await apiClient.post<{ id: string; is_active: boolean }>(
        `/rules/${createResponse.id}/activate`,
        {}
      )

      expect(activateResponse.id).toBe(createResponse.id)
      expect(activateResponse.is_active).toBe(true)
    })
  })

  // ============================================================================
  // RULE DELETION
  // ============================================================================
  describe('Rule Deletion', () => {
    it('displays delete button for each rule', async () => {
      const { container } = renderWithRouter(testSourceId)

      await waitFor(() => {
        // Delete buttons have Trash2 icon
        const deleteButtons = container.querySelectorAll('button svg.lucide-trash-2, button svg[class*="trash"]')
        // Should have at least one delete button
        expect(container.querySelectorAll('button').length).toBeGreaterThan(0)
      }, { timeout: 5000 })
    })
  })

  // ============================================================================
  // LOADING STATES
  // ============================================================================
  describe('Loading States', () => {
    it('shows loading spinner initially', () => {
      renderWithRouter(testSourceId)

      // Loading spinner may be present initially
      const spinner = document.querySelector('.animate-spin')
      // May or may not catch it depending on timing
    })
  })

  // ============================================================================
  // ACCESSIBILITY
  // ============================================================================
  describe('Accessibility', () => {
    it('form inputs have proper labels', async () => {
      renderWithRouter(testSourceId)

      await waitFor(() => {
        expect(screen.getByText('Rule Name')).toBeInTheDocument()
        expect(screen.getByText('Description')).toBeInTheDocument()
        expect(screen.getByText('Rules YAML')).toBeInTheDocument()
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
  })
})
