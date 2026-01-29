/**
 * Dashboard Page Tests
 *
 * Unit tests for the main Dashboard page component.
 * Tests loading states, error handling, data display, and user interactions.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@/test/test-utils'
import { Locales, setTestLocale } from '@/test/test-utils'
import Dashboard from './Dashboard'
import * as apiClient from '@/api/client'

// Mock the API client
vi.mock('@/api/client', () => ({
  listSources: vi.fn(),
}))

const mockListSources = vi.mocked(apiClient.listSources)

// Sample mock data
const mockSources: apiClient.Source[] = [
  {
    id: 'source-1',
    name: 'Sales Data',
    type: 'postgresql',
    config: { host: 'localhost', port: 5432 },
    description: 'Sales transaction data',
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-15T00:00:00Z',
    last_validated_at: '2024-01-15T10:00:00Z',
    has_schema: true,
    latest_validation_status: 'success',
  },
  {
    id: 'source-2',
    name: 'Customer Data',
    type: 'file',
    config: { path: '/data/customers.csv' },
    description: 'Customer master data',
    is_active: true,
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-14T00:00:00Z',
    last_validated_at: '2024-01-14T10:00:00Z',
    has_schema: true,
    latest_validation_status: 'failed',
  },
  {
    id: 'source-3',
    name: 'Inventory Data',
    type: 'mysql',
    config: { host: 'localhost', port: 3306 },
    description: 'Inventory levels',
    is_active: true,
    created_at: '2024-01-03T00:00:00Z',
    updated_at: '2024-01-13T00:00:00Z',
    last_validated_at: undefined,
    has_schema: false,
    latest_validation_status: undefined,
  },
  {
    id: 'source-4',
    name: 'Error Data',
    type: 'file',
    config: { path: '/data/errors.csv' },
    description: 'Error logs',
    is_active: true,
    created_at: '2024-01-04T00:00:00Z',
    updated_at: '2024-01-12T00:00:00Z',
    last_validated_at: '2024-01-12T10:00:00Z',
    has_schema: true,
    latest_validation_status: 'error',
  },
  {
    id: 'source-5',
    name: 'Pending Data',
    type: 'postgresql',
    config: { host: 'localhost', port: 5432 },
    description: 'Pending validation',
    is_active: true,
    created_at: '2024-01-05T00:00:00Z',
    updated_at: '2024-01-11T00:00:00Z',
    last_validated_at: undefined,
    has_schema: true,
    latest_validation_status: 'pending',
  },
]

describe('Dashboard', () => {
  beforeEach(() => {
    mockListSources.mockReset()
    setTestLocale('en')
  })

  describe('Loading State', () => {
    it('shows loading spinner while fetching data', async () => {
      // Create a promise that won't resolve immediately
      let resolvePromise: (value: apiClient.SourceListResponse) => void
      mockListSources.mockImplementation(
        () =>
          new Promise((resolve) => {
            resolvePromise = resolve
          })
      )

      render(<Dashboard />)

      // Should show loading spinner
      const spinner = document.querySelector('.animate-spin')
      expect(spinner).toBeInTheDocument()

      // Resolve the promise
      resolvePromise!({
        success: true,
        data: [],
        total: 0,
        offset: 0,
        limit: 10,
      })

      // Wait for loading to finish
      await waitFor(() => {
        expect(document.querySelector('.animate-spin')).not.toBeInTheDocument()
      })
    })
  })

  describe('Error State', () => {
    it('shows error message when API call fails', async () => {
      mockListSources.mockRejectedValue(new Error('Network error'))

      render(<Dashboard />)

      await waitFor(() => {
        expect(
          screen.getByText('Failed to load dashboard data')
        ).toBeInTheDocument()
      })
    })

    it('shows retry button on error', async () => {
      mockListSources.mockRejectedValue(new Error('Network error'))

      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
      })
    })

    it('retries loading data when retry button is clicked', async () => {
      mockListSources
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          success: true,
          data: mockSources,
          total: mockSources.length,
          offset: 0,
          limit: 10,
        })

      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
      })

      // Click retry button
      const retryButton = screen.getByRole('button', { name: /retry/i })
      fireEvent.click(retryButton)

      // Should call API again
      await waitFor(() => {
        expect(mockListSources).toHaveBeenCalledTimes(2)
      })
    })
  })

  describe('Empty State', () => {
    it('shows empty state when no sources exist', async () => {
      mockListSources.mockResolvedValue({
        success: true,
        data: [],
        total: 0,
        offset: 0,
        limit: 10,
      })

      render(<Dashboard />)

      await waitFor(() => {
        expect(
          screen.getByText('No data sources configured yet')
        ).toBeInTheDocument()
      })
    })

    it('shows "Add Your First Source" button when no sources exist', async () => {
      mockListSources.mockResolvedValue({
        success: true,
        data: [],
        total: 0,
        offset: 0,
        limit: 10,
      })

      render(<Dashboard />)

      await waitFor(() => {
        expect(
          screen.getByRole('link', { name: /add your first source/i })
        ).toBeInTheDocument()
      })
    })
  })

  describe('Stats Display', () => {
    it('displays stat card labels', async () => {
      mockListSources.mockResolvedValue({
        success: true,
        data: mockSources,
        total: mockSources.length,
        offset: 0,
        limit: 10,
      })

      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText('Total Sources')).toBeInTheDocument()
        // Use getAllByText since "Passed" appears in both stat card and status badges
        expect(screen.getAllByText('Passed').length).toBeGreaterThan(0)
        expect(screen.getAllByText('Failed').length).toBeGreaterThan(0)
        expect(screen.getAllByText('Pending').length).toBeGreaterThan(0)
      })
    })

    it('displays stat card descriptions', async () => {
      mockListSources.mockResolvedValue({
        success: true,
        data: mockSources,
        total: mockSources.length,
        offset: 0,
        limit: 10,
      })

      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText('Configured data sources')).toBeInTheDocument()
        expect(screen.getByText('Validation passed')).toBeInTheDocument()
        expect(screen.getByText('Validation failed')).toBeInTheDocument()
        expect(screen.getByText('Not yet validated')).toBeInTheDocument()
      })
    })
  })

  describe('Recent Sources List', () => {
    it('displays recent sources section title', async () => {
      mockListSources.mockResolvedValue({
        success: true,
        data: mockSources,
        total: mockSources.length,
        offset: 0,
        limit: 10,
      })

      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText('Recent Sources')).toBeInTheDocument()
      })
    })

    it('displays source names in the list', async () => {
      mockListSources.mockResolvedValue({
        success: true,
        data: mockSources,
        total: mockSources.length,
        offset: 0,
        limit: 10,
      })

      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText('Sales Data')).toBeInTheDocument()
        expect(screen.getByText('Customer Data')).toBeInTheDocument()
        expect(screen.getByText('Inventory Data')).toBeInTheDocument()
      })
    })

    it('displays source types', async () => {
      mockListSources.mockResolvedValue({
        success: true,
        data: mockSources,
        total: mockSources.length,
        offset: 0,
        limit: 10,
      })

      render(<Dashboard />)

      await waitFor(() => {
        // Source types should be visible in the list
        expect(screen.getAllByText(/postgresql/i).length).toBeGreaterThan(0)
        expect(screen.getAllByText(/file/i).length).toBeGreaterThan(0)
      })
    })

    it('limits displayed sources to 5', async () => {
      const sixSources = [...mockSources, {
        id: 'source-6',
        name: 'Extra Source',
        type: 'file',
        config: {},
        is_active: true,
        created_at: '2024-01-06T00:00:00Z',
        updated_at: '2024-01-10T00:00:00Z',
        has_schema: false,
      }]

      mockListSources.mockResolvedValue({
        success: true,
        data: sixSources,
        total: sixSources.length,
        offset: 0,
        limit: 10,
      })

      render(<Dashboard />)

      await waitFor(() => {
        // Only first 5 sources should be shown
        expect(screen.getByText('Sales Data')).toBeInTheDocument()
        expect(screen.getByText('Pending Data')).toBeInTheDocument()
        // 6th source should not be visible
        expect(screen.queryByText('Extra Source')).not.toBeInTheDocument()
      })
    })

    it('displays validation status badges', async () => {
      mockListSources.mockResolvedValue({
        success: true,
        data: mockSources,
        total: mockSources.length,
        offset: 0,
        limit: 10,
      })

      render(<Dashboard />)

      await waitFor(() => {
        // Check for status badges - validation labels should be present
        const pageContent = document.body.textContent || ''
        expect(pageContent.toLowerCase()).toContain('passed')
        expect(pageContent.toLowerCase()).toContain('failed')
      })
    })

    it('has "View All" button linking to sources page', async () => {
      mockListSources.mockResolvedValue({
        success: true,
        data: mockSources,
        total: mockSources.length,
        offset: 0,
        limit: 10,
      })

      render(<Dashboard />)

      await waitFor(() => {
        const viewAllLink = screen.getByRole('link', { name: /view all/i })
        expect(viewAllLink).toBeInTheDocument()
        expect(viewAllLink).toHaveAttribute('href', '/sources')
      })
    })

    it('source items link to source detail page', async () => {
      mockListSources.mockResolvedValue({
        success: true,
        data: mockSources,
        total: mockSources.length,
        offset: 0,
        limit: 10,
      })

      render(<Dashboard />)

      await waitFor(() => {
        const sourceLink = screen.getByText('Sales Data').closest('a')
        expect(sourceLink).toHaveAttribute('href', '/sources/source-1')
      })
    })
  })

  describe('Header', () => {
    it('displays dashboard title', async () => {
      mockListSources.mockResolvedValue({
        success: true,
        data: [],
        total: 0,
        offset: 0,
        limit: 10,
      })

      render(<Dashboard />)

      await waitFor(() => {
        // Dashboard page uses nav.dashboard for the main heading
        expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Dashboard')
      })
    })

    it('displays dashboard subtitle', async () => {
      mockListSources.mockResolvedValue({
        success: true,
        data: [],
        total: 0,
        offset: 0,
        limit: 10,
      })

      render(<Dashboard />)

      await waitFor(() => {
        expect(
          screen.getByText('Data quality overview and monitoring')
        ).toBeInTheDocument()
      })
    })
  })

  describe('Internationalization', () => {
    it('displays Korean text when locale is Korean', async () => {
      mockListSources.mockResolvedValue({
        success: true,
        data: [],
        total: 0,
        offset: 0,
        limit: 10,
      })

      render(<Dashboard />, { locale: Locales.KOREAN })

      await waitFor(() => {
        // Dashboard title in Korean from nav.dashboard
        expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('대시보드')
        // Subtitle in Korean
        expect(
          screen.getByText('데이터 품질 개요 및 모니터링')
        ).toBeInTheDocument()
      })
    })

    it('displays Korean stat labels when locale is Korean', async () => {
      mockListSources.mockResolvedValue({
        success: true,
        data: mockSources,
        total: mockSources.length,
        offset: 0,
        limit: 10,
      })

      render(<Dashboard />, { locale: Locales.KOREAN })

      await waitFor(() => {
        expect(screen.getByText('전체 소스')).toBeInTheDocument()
        // Use getAllByText since '통과' appears in both stat card and status badges
        expect(screen.getAllByText('통과').length).toBeGreaterThan(0)
        expect(screen.getAllByText('실패').length).toBeGreaterThan(0)
        expect(screen.getAllByText('대기 중').length).toBeGreaterThan(0)
      })
    })
  })

  describe('API Integration', () => {
    it('calls listSources with correct parameters', async () => {
      mockListSources.mockResolvedValue({
        success: true,
        data: [],
        total: 0,
        offset: 0,
        limit: 10,
      })

      render(<Dashboard />)

      await waitFor(() => {
        expect(mockListSources).toHaveBeenCalledWith({ limit: 10 })
      })
    })

    it('handles API returning partial data', async () => {
      const partialSource: apiClient.Source = {
        id: 'partial-1',
        name: 'Partial Source',
        type: 'file',
        config: {},
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        has_schema: false,
        // No last_validated_at, no latest_validation_status
      }

      mockListSources.mockResolvedValue({
        success: true,
        data: [partialSource],
        total: 1,
        offset: 0,
        limit: 10,
      })

      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText('Partial Source')).toBeInTheDocument()
      })
    })
  })

  describe('GlassCard Components', () => {
    it('renders four stat cards', async () => {
      mockListSources.mockResolvedValue({
        success: true,
        data: mockSources,
        total: mockSources.length,
        offset: 0,
        limit: 10,
      })

      const { container } = render(<Dashboard />)

      await waitFor(() => {
        // Each GlassCard has specific gradient classes
        const primaryCard = container.querySelector('.from-primary\\/10')
        const greenCard = container.querySelector('.from-green-500\\/10')
        const redCard = container.querySelector('.from-red-500\\/10')
        const yellowCard = container.querySelector('.from-yellow-500\\/10')

        expect(primaryCard).toBeInTheDocument()
        expect(greenCard).toBeInTheDocument()
        expect(redCard).toBeInTheDocument()
        expect(yellowCard).toBeInTheDocument()
      })
    })
  })

  describe('Date Formatting', () => {
    it('displays formatted last validated date', async () => {
      mockListSources.mockResolvedValue({
        success: true,
        data: mockSources,
        total: mockSources.length,
        offset: 0,
        limit: 10,
      })

      render(<Dashboard />)

      await waitFor(() => {
        // Check that "Last validated" label is present
        const lastValidatedTexts = screen.getAllByText(/last validated/i)
        expect(lastValidatedTexts.length).toBeGreaterThan(0)
      })
    })
  })
})
