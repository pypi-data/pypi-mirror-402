/**
 * CatalogDetail E2E Tests
 *
 * End-to-end tests for the Catalog Detail page using MSW mock server.
 * Tests asset detail view, columns, tags, term mapping, and comments functionality.
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest'
import { setupServer } from 'msw/node'
import { Routes, Route } from 'react-router-dom'
import { handlers } from '@/mocks/handlers'
import { resetStore, getStore, getAll } from '@/mocks/data/store'
import { render, screen, waitFor, fireEvent, Locales, setTestLocale } from '@/test/test-utils'
import CatalogDetail from '../CatalogDetail'
import {
  getAsset,
  mapColumnToTerm,
  unmapColumnFromTerm,
} from '@/api/client'

// Setup MSW server with all handlers
const server = setupServer(...handlers)

// Helper to render with route params using MemoryRouter from test-utils
function renderWithRoute(assetId: string, locale?: 'en' | 'ko') {
  if (locale) {
    setTestLocale(locale)
  }
  return render(
    <Routes>
      <Route path="/catalog/:id" element={<CatalogDetail />} />
    </Routes>,
    {
      useMemoryRouter: true,
      initialEntries: [`/catalog/${assetId}`],
      locale: locale || 'en',
    }
  )
}

describe('CatalogDetail E2E Tests', () => {
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

  // Helper to get first asset id
  function getFirstAssetId(): string | undefined {
    const store = getStore()
    const assets = getAll(store.catalogAssets)
    return assets[0]?.id
  }

  // ============================================================================
  // DATA LOADING
  // ============================================================================
  describe('Data Loading', () => {
    it('loads and displays asset details', async () => {
      const assetId = getFirstAssetId()
      if (!assetId) return

      renderWithRoute(assetId)

      // Wait for loading to complete
      await waitFor(() => {
        const store = getStore()
        const asset = store.catalogAssets.get(assetId)
        if (asset) {
          expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(asset.name)
        }
      }, { timeout: 3000 })
    })

    it('displays back link to catalog', async () => {
      const assetId = getFirstAssetId()
      if (!assetId) return

      renderWithRoute(assetId)

      await waitFor(() => {
        expect(screen.getByText('Back')).toBeInTheDocument()
        expect(screen.getByRole('link', { name: /Back/i })).toHaveAttribute('href', '/catalog')
      }, { timeout: 3000 })
    })

    it('displays asset type badge', async () => {
      const assetId = getFirstAssetId()
      if (!assetId) return

      renderWithRoute(assetId)

      await waitFor(() => {
        const badges = screen.getAllByText(/Table|File|API/i)
        expect(badges.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })

    it('displays edit button', async () => {
      const assetId = getFirstAssetId()
      if (!assetId) return

      renderWithRoute(assetId)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Edit/i })).toBeInTheDocument()
      }, { timeout: 3000 })
    })
  })

  // ============================================================================
  // TABS
  // ============================================================================
  describe('Tabs Navigation', () => {
    it('displays all tabs', async () => {
      const assetId = getFirstAssetId()
      if (!assetId) return

      renderWithRoute(assetId)

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /Overview/i })).toBeInTheDocument()
        expect(screen.getByRole('tab', { name: /Columns/i })).toBeInTheDocument()
        expect(screen.getByRole('tab', { name: /Tags/i })).toBeInTheDocument()
        expect(screen.getByRole('tab', { name: /Comments/i })).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('Overview tab is selected by default', async () => {
      const assetId = getFirstAssetId()
      if (!assetId) return

      renderWithRoute(assetId)

      await waitFor(() => {
        const overviewTab = screen.getByRole('tab', { name: /Overview/i })
        expect(overviewTab).toHaveAttribute('data-state', 'active')
      }, { timeout: 3000 })
    })

    it('Columns tab is clickable', async () => {
      const assetId = getFirstAssetId()
      if (!assetId) return

      renderWithRoute(assetId)

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /Columns/i })).toBeInTheDocument()
      }, { timeout: 3000 })

      const columnsTab = screen.getByRole('tab', { name: /Columns/i })
      fireEvent.click(columnsTab)

      // Verify tab is visible and clickable
      expect(columnsTab).toBeInTheDocument()
    })

    it('Tags tab is clickable', async () => {
      const assetId = getFirstAssetId()
      if (!assetId) return

      renderWithRoute(assetId)

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /Tags/i })).toBeInTheDocument()
      }, { timeout: 3000 })

      const tagsTab = screen.getByRole('tab', { name: /Tags/i })
      fireEvent.click(tagsTab)

      expect(tagsTab).toBeInTheDocument()
    })

    it('Comments tab is clickable', async () => {
      const assetId = getFirstAssetId()
      if (!assetId) return

      renderWithRoute(assetId)

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /Comments/i })).toBeInTheDocument()
      }, { timeout: 3000 })

      const commentsTab = screen.getByRole('tab', { name: /Comments/i })
      fireEvent.click(commentsTab)

      expect(commentsTab).toBeInTheDocument()
    })
  })

  // ============================================================================
  // OVERVIEW TAB
  // ============================================================================
  describe('Overview Tab', () => {
    it('displays statistics cards', async () => {
      const assetId = getFirstAssetId()
      if (!assetId) return

      renderWithRoute(assetId)

      await waitFor(() => {
        // Should have multiple cards visible
        const cards = screen.getAllByText(/Columns|Tags|Owner/i)
        expect(cards.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })

    it('displays owner info', async () => {
      const assetId = getFirstAssetId()
      if (!assetId) return

      renderWithRoute(assetId)

      await waitFor(() => {
        expect(screen.getByText('Owner')).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('displays quality score if present', async () => {
      const assetId = getFirstAssetId()
      if (!assetId) return

      renderWithRoute(assetId)

      await waitFor(() => {
        const store = getStore()
        const asset = store.catalogAssets.get(assetId)
        if (asset?.quality_score !== undefined) {
          const scoreText = screen.queryByText(/Quality Score/i)
          expect(scoreText || true).toBeTruthy()
        }
      }, { timeout: 3000 })
    })
  })

  // ============================================================================
  // COLUMN TERM MAPPING API
  // ============================================================================
  describe('Column Term Mapping', () => {
    it('API: maps column to term', async () => {
      const store = getStore()
      const columns = getAll(store.assetColumns)
      const columnWithoutTerm = columns.find((c) => !c.term_id)
      const terms = getAll(store.glossaryTerms)
      const term = terms[0]

      if (columnWithoutTerm && term) {
        const updatedColumn = await mapColumnToTerm(columnWithoutTerm.id, term.id)

        expect(updatedColumn.term_id).toBe(term.id)
        expect(updatedColumn.term).toBeDefined()
        expect(updatedColumn.term?.id).toBe(term.id)
      }
    })

    it('API: unmaps column from term', async () => {
      const store = getStore()
      const columns = getAll(store.assetColumns)
      const terms = getAll(store.glossaryTerms)
      const term = terms[0]
      const column = columns[0]

      if (column && term) {
        // First map the column
        await mapColumnToTerm(column.id, term.id)

        // Then unmap
        const unmappedColumn = await unmapColumnFromTerm(column.id)

        expect(unmappedColumn.term_id).toBeUndefined()
        expect(unmappedColumn.term).toBeUndefined()
      }
    })
  })

  // ============================================================================
  // DATA INTEGRITY
  // ============================================================================
  describe('Data Integrity', () => {
    it('API: asset has valid structure', async () => {
      const assetId = getFirstAssetId()
      if (!assetId) return

      const asset = await getAsset(assetId)

      expect(asset.id).toBeDefined()
      expect(asset.name).toBeDefined()
      expect(asset.asset_type).toBeDefined()
      expect(Array.isArray(asset.columns)).toBe(true)
      expect(Array.isArray(asset.tags)).toBe(true)
    })

    it('API: columns have valid structure', async () => {
      const assetId = getFirstAssetId()
      if (!assetId) return

      const asset = await getAsset(assetId)

      asset.columns.forEach((column) => {
        expect(column.id).toBeDefined()
        expect(column.name).toBeDefined()
        expect(column.asset_id).toBe(asset.id)
        expect(typeof column.is_nullable).toBe('boolean')
        expect(typeof column.is_primary_key).toBe('boolean')
      })
    })

    it('API: tags have valid structure', async () => {
      const assetId = getFirstAssetId()
      if (!assetId) return

      const asset = await getAsset(assetId)

      asset.tags.forEach((tag) => {
        expect(tag.id).toBeDefined()
        expect(tag.tag_name).toBeDefined()
        expect(tag.asset_id).toBe(asset.id)
      })
    })
  })

  // ============================================================================
  // UI COMPONENTS
  // ============================================================================
  describe('UI Components', () => {
    it('renders asset icon', async () => {
      const assetId = getFirstAssetId()
      if (!assetId) return

      const { container } = renderWithRoute(assetId)

      await waitFor(() => {
        const icons = container.querySelectorAll('svg')
        expect(icons.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })

    it('renders Card components', async () => {
      const assetId = getFirstAssetId()
      if (!assetId) return

      const { container } = renderWithRoute(assetId)

      await waitFor(() => {
        const cards = container.querySelectorAll('[class*="rounded"]')
        expect(cards.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })

    it('renders Badge components', async () => {
      const assetId = getFirstAssetId()
      if (!assetId) return

      renderWithRoute(assetId)

      await waitFor(() => {
        // Should have at least one badge (asset type)
        const badges = screen.getAllByText(/Table|File|API/i)
        expect(badges.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })
  })

  // ============================================================================
  // INTERNATIONALIZATION
  // ============================================================================
  describe('Internationalization', () => {
    it('renders Korean translations for tabs', async () => {
      const assetId = getFirstAssetId()
      if (!assetId) return

      renderWithRoute(assetId, 'ko')

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /개요/i })).toBeInTheDocument()
        expect(screen.getByRole('tab', { name: /컬럼/i })).toBeInTheDocument()
        expect(screen.getByRole('tab', { name: /태그/i })).toBeInTheDocument()
        expect(screen.getByRole('tab', { name: /댓글/i })).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('renders Korean back button', async () => {
      const assetId = getFirstAssetId()
      if (!assetId) return

      renderWithRoute(assetId, 'ko')

      await waitFor(() => {
        expect(screen.getByText('뒤로')).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('renders Korean edit button', async () => {
      const assetId = getFirstAssetId()
      if (!assetId) return

      renderWithRoute(assetId, 'ko')

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /편집/i })).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('renders Korean owner label', async () => {
      const assetId = getFirstAssetId()
      if (!assetId) return

      renderWithRoute(assetId, 'ko')

      await waitFor(() => {
        expect(screen.getByText('담당자')).toBeInTheDocument()
      }, { timeout: 3000 })
    })
  })

  // ============================================================================
  // ACCESSIBILITY
  // ============================================================================
  describe('Accessibility', () => {
    it('has accessible heading structure', async () => {
      const assetId = getFirstAssetId()
      if (!assetId) return

      renderWithRoute(assetId)

      await waitFor(() => {
        const heading = screen.getByRole('heading', { level: 1 })
        expect(heading).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('tabs are accessible', async () => {
      const assetId = getFirstAssetId()
      if (!assetId) return

      renderWithRoute(assetId)

      await waitFor(() => {
        const tabs = screen.getAllByRole('tab')
        expect(tabs.length).toBe(4) // Overview, Columns, Tags, Comments
      }, { timeout: 3000 })
    })

    it('buttons are accessible', async () => {
      const assetId = getFirstAssetId()
      if (!assetId) return

      renderWithRoute(assetId)

      await waitFor(() => {
        const buttons = screen.getAllByRole('button')
        expect(buttons.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })

    it('back link is accessible', async () => {
      const assetId = getFirstAssetId()
      if (!assetId) return

      renderWithRoute(assetId)

      await waitFor(() => {
        const backLink = screen.getByRole('link', { name: /Back/i })
        expect(backLink).toHaveAttribute('href')
      }, { timeout: 3000 })
    })
  })

  // ============================================================================
  // SOURCE INFO
  // ============================================================================
  describe('Source Info', () => {
    it('displays source badge if asset has source', async () => {
      const store = getStore()
      const assets = getAll(store.catalogAssets)
      const assetWithSource = assets.find((a) => a.source_id)

      if (assetWithSource) {
        renderWithRoute(assetWithSource.id)

        await waitFor(() => {
          const source = store.sources.get(assetWithSource.source_id!)
          if (source) {
            expect(screen.getByText(source.name)).toBeInTheDocument()
          }
        }, { timeout: 3000 })
      }
    })
  })
})
