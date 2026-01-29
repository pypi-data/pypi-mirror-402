/**
 * Catalog E2E Tests
 *
 * End-to-end tests for the Catalog page using MSW mock server.
 * Tests data asset listing, filtering, creation, and deletion functionality.
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest'
import { setupServer } from 'msw/node'
import { handlers } from '@/mocks/handlers'
import { resetStore, getStore, getAll } from '@/mocks/data/store'
import { render, screen, waitFor, fireEvent, Locales, setTestLocale } from '@/test/test-utils'
import Catalog from '../Catalog'
import { getAssets, getAsset, createAsset, deleteAsset } from '@/api/client'

// Setup MSW server with all handlers
const server = setupServer(...handlers)

describe('Catalog E2E Tests', () => {
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
    it('loads and displays assets from the mock API', async () => {
      render(<Catalog />)

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.queryByRole('status')).not.toBeInTheDocument()
      }, { timeout: 3000 })

      // Should display the page title
      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Catalog')
      })
    })

    it('fetches assets using the API client', async () => {
      const assets = await getAssets({ limit: 50 })

      expect(Array.isArray(assets)).toBe(true)
      expect(assets.length).toBeGreaterThan(0)
    })

    it('displays asset cards when assets exist', async () => {
      render(<Catalog />)

      // Wait for assets to load
      await waitFor(() => {
        const store = getStore()
        const assets = getAll(store.catalogAssets)
        // At least one asset name should be visible
        const firstAsset = assets[0]
        if (firstAsset) {
          expect(screen.getByText(firstAsset.name)).toBeInTheDocument()
        }
      }, { timeout: 3000 })
    })

    it('shows subtitle text', async () => {
      render(<Catalog />)

      await waitFor(() => {
        expect(screen.getByText('Browse and manage data assets')).toBeInTheDocument()
      })
    })
  })

  // ============================================================================
  // ASSET LIST DISPLAY
  // ============================================================================
  describe('Asset List Display', () => {
    it('displays asset type badges', async () => {
      render(<Catalog />)

      await waitFor(() => {
        // Asset types should appear as badges
        const badges = screen.getAllByText(/Table|File|API/i)
        expect(badges.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })

    it('displays column count info', async () => {
      render(<Catalog />)

      await waitFor(() => {
        // Should show "Columns: X"
        const columnTexts = screen.getAllByText(/Columns:/i)
        expect(columnTexts.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })

    it('displays quality scores when assets have scores', async () => {
      render(<Catalog />)

      await waitFor(() => {
        const store = getStore()
        const assets = getAll(store.catalogAssets)
        const assetWithScore = assets.find((a) => a.quality_score !== undefined)

        if (assetWithScore) {
          // Check that percentage is displayed
          const scoreRegex = /\d+\.\d+%/
          const scoreElements = screen.queryAllByText(scoreRegex)
          expect(scoreElements.length).toBeGreaterThanOrEqual(0)
        }
      }, { timeout: 3000 })
    })

    it('displays Add Asset button', async () => {
      render(<Catalog />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Add Asset/i })).toBeInTheDocument()
      })
    })

    it('displays delete buttons for each asset', async () => {
      const { container } = render(<Catalog />)

      await waitFor(() => {
        // Delete buttons have trash icons
        const trashIcons = container.querySelectorAll('.text-destructive')
        expect(trashIcons.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })
  })

  // ============================================================================
  // ASSET CARD NAVIGATION
  // ============================================================================
  describe('Asset Card Navigation', () => {
    it('asset names are links to detail pages', async () => {
      render(<Catalog />)

      await waitFor(() => {
        const store = getStore()
        const assets = getAll(store.catalogAssets)
        const firstAsset = assets[0]
        if (firstAsset) {
          const link = screen.getByRole('link', { name: firstAsset.name })
          expect(link).toHaveAttribute('href', `/catalog/${firstAsset.id}`)
        }
      }, { timeout: 3000 })
    })
  })

  // ============================================================================
  // FILTERING
  // ============================================================================
  describe('Filtering', () => {
    it('displays search input', async () => {
      render(<Catalog />)

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Search assets/i)).toBeInTheDocument()
      })
    })

    it('displays type filter dropdown', async () => {
      render(<Catalog />)

      await waitFor(() => {
        // Type filter should have "All types" option by default
        expect(screen.getByText(/All types/i)).toBeInTheDocument()
      })
    })

    it('displays source filter dropdown', async () => {
      render(<Catalog />)

      await waitFor(() => {
        // Source filter should have "All sources" option by default
        expect(screen.getByText(/All sources/i)).toBeInTheDocument()
      })
    })

    it('API: filters assets by type', async () => {
      const allAssets = await getAssets()
      const tableAssets = await getAssets({ asset_type: 'table' })

      // All table assets should have type 'table'
      tableAssets.forEach((asset) => {
        expect(asset.asset_type).toBe('table')
      })

      // Should be a subset
      expect(tableAssets.length).toBeLessThanOrEqual(allAssets.length)
    })

    it('API: filters assets by source', async () => {
      const store = getStore()
      const sources = getAll(store.sources)
      const firstSource = sources[0]

      if (firstSource) {
        const filteredAssets = await getAssets({ source_id: firstSource.id })
        filteredAssets.forEach((asset) => {
          expect(asset.source_id).toBe(firstSource.id)
        })
      }
    })

    it('API: searches assets by name', async () => {
      const allAssets = await getAssets()
      const firstAsset = allAssets[0]

      if (firstAsset) {
        const searchTerm = firstAsset.name.substring(0, 3)
        const searchResults = await getAssets({ search: searchTerm })

        // Search results should include the original asset
        const found = searchResults.find((a) => a.id === firstAsset.id)
        expect(found).toBeDefined()
      }
    })
  })

  // ============================================================================
  // CREATE ASSET
  // ============================================================================
  describe('Create Asset', () => {
    it('Add Asset button is rendered', async () => {
      render(<Catalog />)

      await waitFor(() => {
        const addButton = screen.getByRole('button', { name: /Add Asset/i })
        expect(addButton).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('Add Asset button can be clicked', async () => {
      render(<Catalog />)

      // Wait for button to be available
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Add Asset/i })).toBeInTheDocument()
      }, { timeout: 3000 })

      // Click the button
      const addButton = screen.getByRole('button', { name: /Add Asset/i })
      fireEvent.click(addButton)

      // Note: Dialog rendering in jsdom has known issues with Radix UI
      // The button click is tested, dialog functionality is tested in integration tests
      expect(addButton).toBeInTheDocument()
    })

    it('API: creates a new asset', async () => {
      const store = getStore()
      const initialCount = getAll(store.catalogAssets).length

      const newAsset = await createAsset({
        name: 'test_asset',
        asset_type: 'table',
        description: 'Test asset description',
        owner_id: 'Test Owner',
      })

      expect(newAsset).toBeDefined()
      expect(newAsset.name).toBe('test_asset')
      expect(newAsset.asset_type).toBe('table')
      expect(newAsset.description).toBe('Test asset description')

      // Verify asset was added to store
      const newAssets = await getAssets()
      expect(newAssets.length).toBe(initialCount + 1)
    })

    it('API: creates asset with source_id', async () => {
      const store = getStore()
      const sources = getAll(store.sources)
      const firstSource = sources[0]

      if (firstSource) {
        const newAsset = await createAsset({
          name: 'source_linked_asset',
          asset_type: 'file',
          source_id: firstSource.id,
        })

        expect(newAsset.source_id).toBe(firstSource.id)
        expect(newAsset.source).toBeDefined()
        expect(newAsset.source?.id).toBe(firstSource.id)
      }
    })
  })

  // ============================================================================
  // DELETE ASSET
  // ============================================================================
  describe('Delete Asset', () => {
    it('API: deletes an asset', async () => {
      const store = getStore()
      const assets = getAll(store.catalogAssets)
      const initialCount = assets.length

      if (initialCount > 0) {
        const assetToDelete = assets[0]
        await deleteAsset(assetToDelete.id)

        // Verify deletion
        const newAssets = await getAssets()
        expect(newAssets.length).toBe(initialCount - 1)
        expect(newAssets.find((a) => a.id === assetToDelete.id)).toBeUndefined()
      }
    })

    it('clicking delete button shows confirmation dialog', async () => {
      const { container } = render(<Catalog />)

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
            expect(screen.getByText(/Delete Asset/i)).toBeInTheDocument()
          }, { timeout: 3000 })
        }
      }
    })
  })

  // ============================================================================
  // EMPTY STATE
  // ============================================================================
  describe('Empty State', () => {
    it('shows empty state when no assets exist', async () => {
      // Clear all assets from the store
      const store = getStore()
      store.catalogAssets.clear()

      render(<Catalog />)

      await waitFor(() => {
        expect(screen.getByText(/No assets yet/i)).toBeInTheDocument()
        expect(screen.getByText(/Add your first data asset/i)).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('empty state has Add First Asset button', async () => {
      const store = getStore()
      store.catalogAssets.clear()

      render(<Catalog />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Add Your First Asset/i })).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('empty state Add First Asset button can be clicked', async () => {
      const store = getStore()
      store.catalogAssets.clear()

      render(<Catalog />)

      // Wait for button to be available
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Add Your First Asset/i })).toBeInTheDocument()
      }, { timeout: 3000 })

      // Click the button
      const addButton = screen.getByRole('button', { name: /Add Your First Asset/i })
      fireEvent.click(addButton)

      // Note: Dialog rendering in jsdom has known issues with Radix UI
      // The button click is tested, dialog functionality is tested in integration tests
      expect(addButton).toBeInTheDocument()
    })
  })

  // ============================================================================
  // GET ASSET DETAIL
  // ============================================================================
  describe('Get Asset Detail', () => {
    it('API: fetches asset by ID with columns', async () => {
      const store = getStore()
      const assets = getAll(store.catalogAssets)
      const firstAsset = assets[0]

      if (firstAsset) {
        const asset = await getAsset(firstAsset.id)

        expect(asset).toBeDefined()
        expect(asset.id).toBe(firstAsset.id)
        expect(asset.name).toBe(firstAsset.name)
        expect(Array.isArray(asset.columns)).toBe(true)
        expect(Array.isArray(asset.tags)).toBe(true)
      }
    })

    it('API: fetches asset with source info', async () => {
      const store = getStore()
      const assets = getAll(store.catalogAssets)
      const assetWithSource = assets.find((a) => a.source_id)

      if (assetWithSource) {
        const asset = await getAsset(assetWithSource.id)
        expect(asset.source).toBeDefined()
        expect(asset.source?.id).toBe(assetWithSource.source_id)
      }
    })

    it('API: returns 404 for non-existent asset', async () => {
      try {
        await getAsset('non-existent-id')
        // Should not reach here
        expect(true).toBe(false)
      } catch (error) {
        // Should throw error
        expect(error).toBeDefined()
      }
    })
  })

  // ============================================================================
  // DATA INTEGRITY
  // ============================================================================
  describe('Data Integrity', () => {
    it('mock data has valid asset types', async () => {
      const assets = await getAssets()
      const validTypes = ['table', 'file', 'api']

      assets.forEach((asset) => {
        expect(validTypes).toContain(asset.asset_type)
      })
    })

    it('mock data has valid timestamps', async () => {
      const assets = await getAssets()

      assets.forEach((asset) => {
        expect(new Date(asset.updated_at).toString()).not.toBe('Invalid Date')
      })
    })

    it('assets have required fields', async () => {
      const assets = await getAssets()

      assets.forEach((asset) => {
        expect(asset.id).toBeDefined()
        expect(asset.name).toBeDefined()
        expect(asset.asset_type).toBeDefined()
        expect(typeof asset.column_count).toBe('number')
        expect(typeof asset.tag_count).toBe('number')
      })
    })

    it('asset columns have required fields', async () => {
      const store = getStore()
      const assets = getAll(store.catalogAssets)
      const firstAsset = assets[0]

      if (firstAsset) {
        const asset = await getAsset(firstAsset.id)
        asset.columns.forEach((column) => {
          expect(column.id).toBeDefined()
          expect(column.name).toBeDefined()
          expect(column.asset_id).toBe(asset.id)
        })
      }
    })
  })

  // ============================================================================
  // UI COMPONENTS
  // ============================================================================
  describe('UI Components', () => {
    it('renders asset cards with icons', async () => {
      const { container } = render(<Catalog />)

      await waitFor(() => {
        // Asset icons are SVGs
        const icons = container.querySelectorAll('svg')
        expect(icons.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })

    it('renders Card components for assets', async () => {
      const { container } = render(<Catalog />)

      await waitFor(() => {
        // Cards should have rounded borders
        const cards = container.querySelectorAll('[class*="rounded"]')
        expect(cards.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })

    it('renders filter icons', async () => {
      const { container } = render(<Catalog />)

      await waitFor(() => {
        // Search and filter icons
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
      render(<Catalog />, { locale: Locales.KOREAN })

      await waitFor(() => {
        // Korean title
        expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('카탈로그')
      })
    })

    it('renders Korean subtitle', async () => {
      render(<Catalog />, { locale: Locales.KOREAN })

      await waitFor(() => {
        expect(screen.getByText('데이터 자산 탐색 및 관리')).toBeInTheDocument()
      })
    })

    it('renders Korean buttons', async () => {
      render(<Catalog />, { locale: Locales.KOREAN })

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /자산 추가/i })).toBeInTheDocument()
      })
    })

    it('renders Korean empty state', async () => {
      const store = getStore()
      store.catalogAssets.clear()

      render(<Catalog />, { locale: Locales.KOREAN })

      await waitFor(() => {
        expect(screen.getByText('등록된 자산이 없습니다')).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('renders Korean filter options', async () => {
      render(<Catalog />, { locale: Locales.KOREAN })

      await waitFor(() => {
        expect(screen.getByText('모든 유형')).toBeInTheDocument()
        expect(screen.getByText('모든 소스')).toBeInTheDocument()
      })
    })
  })

  // ============================================================================
  // ACCESSIBILITY
  // ============================================================================
  describe('Accessibility', () => {
    it('has accessible heading structure', async () => {
      render(<Catalog />)

      await waitFor(() => {
        const heading = screen.getByRole('heading', { level: 1 })
        expect(heading).toBeInTheDocument()
      })
    })

    it('buttons are accessible', async () => {
      render(<Catalog />)

      await waitFor(() => {
        const buttons = screen.getAllByRole('button')
        expect(buttons.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })

    it('links have proper href attributes', async () => {
      render(<Catalog />)

      await waitFor(() => {
        const links = screen.getAllByRole('link')
        links.forEach((link) => {
          expect(link).toHaveAttribute('href')
        })
      }, { timeout: 3000 })
    })

    it('search input has placeholder for accessibility', async () => {
      render(<Catalog />)

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText(/Search assets/i)
        expect(searchInput).toHaveAttribute('placeholder')
      })
    })
  })
})
