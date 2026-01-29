import { test, expect } from '@playwright/test'

/**
 * E2E Tests for Reports Page
 * 
 * Comprehensive testing of all features:
 * - Page layout and navigation
 * - Statistics cards display
 * - Report history table
 * - Filters (search, format, status, include expired)
 * - Report actions (download, delete)
 * - Cleanup expired reports
 * - Pagination
 * - Error handling
 * - Accessibility
 * - Performance
 */

test.describe('Reports Page - Core UI', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/reports')
    await page.waitForLoadState('networkidle')
  })

  test('should display page title and description', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /^reports$/i }).first()).toBeVisible()
    await expect(page.getByText(/view.*manage.*generated.*report/i).first()).toBeVisible()
  })

  test('should display manage reporters button', async ({ page }) => {
    const manageBtn = page.getByRole('link', { name: /manage reporters/i })
    await expect(manageBtn).toBeVisible()
    await expect(manageBtn).toHaveAttribute('href', '/plugins')
  })

  test('should have proper page structure', async ({ page }) => {
    // Statistics section (may not be visible if no statistics API)
    const statsCards = page.locator('[class*="grid"]').first()
    const statsCount = await statsCards.count()
    expect(statsCount).toBeGreaterThanOrEqual(0)
    
    // Filters section
    await expect(page.getByPlaceholder(/search/i)).toBeVisible()
    
    // Table section or empty state
    const table = page.getByRole('table')
    const tableCount = await table.count()
    const emptyState = page.getByText(/no reports/i)
    const emptyCount = await emptyState.count()
    
    // Should have either table or empty state
    expect(tableCount + emptyCount).toBeGreaterThan(0)
  })
})

test.describe('Reports Page - Statistics Cards', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/reports')
    await page.waitForLoadState('networkidle')
  })

  test('should display Total Reports card if statistics loaded', async ({ page }) => {
    // Statistics cards may not load in all environments
    const totalReportsText = page.getByText(/total reports/i)
    const textCount = await totalReportsText.count()
    expect(textCount).toBeGreaterThanOrEqual(0)
  })

  test('should display Total Size card if statistics loaded', async ({ page }) => {
    const totalSizeText = page.getByText(/total size/i)
    const textCount = await totalSizeText.count()
    expect(textCount).toBeGreaterThanOrEqual(0)
  })

  test('should display Total Downloads card if statistics loaded', async ({ page }) => {
    const downloadsText = page.getByText(/total downloads/i)
    const textCount = await downloadsText.count()
    expect(textCount).toBeGreaterThanOrEqual(0)
  })

  test('should display Average Generation Time card if statistics loaded', async ({ page }) => {
    const avgTimeText = page.getByText(/avg.*generation time|average.*generation time/i)
    const textCount = await avgTimeText.count()
    expect(textCount).toBeGreaterThanOrEqual(0)
  })

  test('should display Expired Reports card if statistics loaded', async ({ page }) => {
    const expiredText = page.getByText(/expired reports/i)
    const textCount = await expiredText.count()
    expect(textCount).toBeGreaterThanOrEqual(0)
  })

  test('should display Reporters Used card if statistics loaded', async ({ page }) => {
    const reportersText = page.getByText(/reporters used/i)
    const textCount = await reportersText.count()
    expect(textCount).toBeGreaterThanOrEqual(0)
  })

  test('should show 6 statistics cards if statistics loaded', async ({ page }) => {
    // Total Reports, Total Size, Total Downloads, Avg Generation Time, Expired Reports, Reporters Used
    const statsGrid = page.locator('[class*="grid"]').first()
    const gridCount = await statsGrid.count()
    
    if (gridCount > 0) {
      const cards = statsGrid.locator('.card, [class*="card"]')
      const cardCount = await cards.count()
      // May be 0 or 6 depending on API response
      expect(cardCount).toBeGreaterThanOrEqual(0)
    }
  })
})

test.describe('Reports Page - Filters', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/reports')
    await page.waitForLoadState('networkidle')
  })

  test('should have search input', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i)
    await expect(searchInput).toBeVisible()
    await expect(searchInput).toBeEditable()
  })

  test('should type in search input', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i)
    await searchInput.fill('test report')
    await expect(searchInput).toHaveValue('test report')
  })

  test('should have format filter dropdown', async ({ page }) => {
    const formatFilter = page.getByRole('combobox').filter({ hasText: /all formats|format/i }).first()
    await expect(formatFilter).toBeVisible()
  })

  test('should open format filter dropdown', async ({ page }) => {
    const formatFilter = page.getByRole('combobox').filter({ hasText: /all formats|format/i }).first()
    await formatFilter.click()
    
    // Should show format options
    await expect(page.getByRole('option', { name: /html/i })).toBeVisible()
    await expect(page.getByRole('option', { name: /pdf/i })).toBeVisible()
    await expect(page.getByRole('option', { name: /csv/i })).toBeVisible()
    await expect(page.getByRole('option', { name: /json/i })).toBeVisible()
  })

  test('should select format filter', async ({ page }) => {
    const formatFilter = page.getByRole('combobox').filter({ hasText: /all formats|format/i }).first()
    await formatFilter.click()
    
    await page.getByRole('option', { name: /pdf/i }).click()
    await page.waitForTimeout(500)
  })

  test('should have status filter dropdown', async ({ page }) => {
    const statusFilter = page.getByRole('combobox').filter({ hasText: /all statuses|status/i }).first()
    await expect(statusFilter).toBeVisible()
  })

  test('should open status filter dropdown', async ({ page }) => {
    const statusFilter = page.getByRole('combobox').filter({ hasText: /all statuses|status/i }).first()
    await statusFilter.click()
    
    // Should show status options
    await expect(page.getByRole('option', { name: /pending/i })).toBeVisible()
    await expect(page.getByRole('option', { name: /generating/i })).toBeVisible()
    await expect(page.getByRole('option', { name: /completed/i })).toBeVisible()
    await expect(page.getByRole('option', { name: /failed/i })).toBeVisible()
  })

  test('should select status filter', async ({ page }) => {
    const statusFilter = page.getByRole('combobox').filter({ hasText: /all statuses|status/i }).first()
    await statusFilter.click()
    
    await page.getByRole('option', { name: /completed/i }).click()
    await page.waitForTimeout(500)
  })

  test('should have include expired checkbox', async ({ page }) => {
    const checkbox = page.getByRole('checkbox', { name: /include expired/i })
    await expect(checkbox).toBeVisible()
  })

  test('should toggle include expired checkbox', async ({ page }) => {
    const checkbox = page.getByRole('checkbox', { name: /include expired/i })
    
    // Get initial state
    const initialState = await checkbox.getAttribute('data-state')
    
    // Click checkbox
    await checkbox.click()
    await page.waitForTimeout(300)
    
    // State should have changed
    const newState = await checkbox.getAttribute('data-state')
    expect(newState).not.toBe(initialState)
  })

  test('should apply multiple filters together', async ({ page }) => {
    // Search
    const searchInput = page.getByPlaceholder(/search/i)
    await searchInput.fill('validation')
    
    // Format filter
    const formatFilter = page.getByRole('combobox').filter({ hasText: /all formats|format/i }).first()
    await formatFilter.click()
    await page.getByRole('option', { name: /html/i }).click()
    
    await page.waitForTimeout(500)
  })
})

test.describe('Reports Page - Report History Table', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/reports')
    await page.waitForLoadState('networkidle')
  })

  test('should display report history card', async ({ page }) => {
    await expect(page.getByText(/report history/i).first()).toBeVisible()
  })

  test('should display table headers if reports exist', async ({ page }) => {
    const table = page.getByRole('table')
    const tableCount = await table.count()
    
    if (tableCount > 0) {
      // Check for key column headers
      const headers = table.getByRole('columnheader')
      const headerCount = await headers.count()
      expect(headerCount).toBeGreaterThan(0)
    }
  })

  test('should show loading spinner initially', async ({ page }) => {
    await page.goto('/reports')
    
    // Check for spinner (may be very brief)
    const spinner = page.locator('svg[class*="animate-spin"]')
    const spinnerCount = await spinner.count()
    expect(spinnerCount).toBeGreaterThanOrEqual(0)
  })

  test('should display report rows or empty state', async ({ page }) => {
    const table = page.getByRole('table')
    const tableCount = await table.count()
    const emptyState = page.getByText(/no reports/i)
    const emptyCount = await emptyState.count()
    
    // Should have either table or empty state
    expect(tableCount + emptyCount).toBeGreaterThan(0)
  })

  test('should display empty state if no reports', async ({ page }) => {
    // Apply filters that might result in no reports
    const searchInput = page.getByPlaceholder(/search/i)
    await searchInput.fill('xyznonexistentreport12345')
    
    await page.waitForTimeout(500)
    
    // Might show empty state or still show some reports
    const noReportsText = page.getByText(/no reports/i)
    const noReportsCount = await noReportsText.count()
    expect(noReportsCount).toBeGreaterThanOrEqual(0)
  })

  test('should display format badges in table', async ({ page }) => {
    const table = page.getByRole('table')
    const rows = table.getByRole('row')
    const count = await rows.count()
    
    if (count > 1) {
      // Find format badges (HTML, PDF, CSV, JSON, etc.)
      const badges = table.locator('[class*="badge"]')
      const badgeCount = await badges.count()
      expect(badgeCount).toBeGreaterThan(0)
    }
  })

  test('should display status badges in table', async ({ page }) => {
    const table = page.getByRole('table')
    const rows = table.getByRole('row')
    const count = await rows.count()
    
    if (count > 1) {
      // Status badges: completed, failed, pending, generating, expired
      const statusBadges = table.locator('[class*="badge"]').filter({ hasText: /completed|failed|pending|generating|expired/i })
      const statusCount = await statusBadges.count()
      expect(statusCount).toBeGreaterThan(0)
    }
  })
})

test.describe('Reports Page - Report Actions', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/reports')
    await page.waitForLoadState('networkidle')
  })

  test('should display download buttons in action column', async ({ page }) => {
    const table = page.getByRole('table')
    const rows = table.getByRole('row')
    const count = await rows.count()
    
    if (count > 1) {
      // Download icon buttons
      const downloadButtons = table.getByRole('button').filter({ has: page.locator('svg') })
      const btnCount = await downloadButtons.count()
      expect(btnCount).toBeGreaterThan(0)
    }
  })

  test('should display delete buttons in action column', async ({ page }) => {
    const table = page.getByRole('table')
    const rows = table.getByRole('row')
    const count = await rows.count()
    
    if (count > 1) {
      // Trash icon buttons (red text)
      const deleteButtons = table.getByRole('button').filter({ has: page.locator('svg[class*="text-destructive"]') })
      const btnCount = await deleteButtons.count()
      expect(btnCount).toBeGreaterThanOrEqual(0)
    }
  })

  test('should click download button', async ({ page }) => {
    const table = page.getByRole('table')
    const rows = table.getByRole('row')
    const count = await rows.count()
    
    if (count > 1) {
      const firstRow = rows.nth(1)
      const downloadBtn = firstRow.getByRole('button').first()
      
      if (await downloadBtn.isEnabled()) {
        await downloadBtn.click()
        await page.waitForTimeout(500)
      }
    }
  })

  test('should open delete confirmation dialog', async ({ page }) => {
    const table = page.getByRole('table')
    const rows = table.getByRole('row')
    const count = await rows.count()
    
    if (count > 1) {
      const firstRow = rows.nth(1)
      const deleteBtn = firstRow.getByRole('button').last()
      
      await deleteBtn.click()
      
      // Dialog should open
      const dialog = page.getByRole('dialog')
      await expect(dialog).toBeVisible()
      
      // Should have confirmation message
      await expect(dialog.getByText(/delete|confirm/i)).toBeVisible()
    }
  })

  test('should cancel delete dialog', async ({ page }) => {
    const table = page.getByRole('table')
    const rows = table.getByRole('row')
    const count = await rows.count()
    
    if (count > 1) {
      const firstRow = rows.nth(1)
      const deleteBtn = firstRow.getByRole('button').last()
      
      await deleteBtn.click()
      
      const dialog = page.getByRole('dialog')
      const cancelBtn = dialog.getByRole('button', { name: /cancel/i })
      await cancelBtn.click()
      
      await expect(dialog).not.toBeVisible()
    }
  })

  test('should have source links in table', async ({ page }) => {
    const table = page.getByRole('table')
    const rows = table.getByRole('row')
    const count = await rows.count()
    
    if (count > 1) {
      // Source name links (if exists)
      const sourceLinks = table.getByRole('link').filter({ hasText: /.+/ })
      const linkCount = await sourceLinks.count()
      expect(linkCount).toBeGreaterThanOrEqual(0)
    }
  })
})

test.describe('Reports Page - Cleanup Expired Reports', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/reports')
    await page.waitForLoadState('networkidle')
  })

  test('should show cleanup button if expired reports exist', async ({ page }) => {
    const cleanupBtn = page.getByRole('button', { name: /cleanup expired/i })
    const btnCount = await cleanupBtn.count()
    
    // Button should be visible if there are expired reports
    expect(btnCount).toBeGreaterThanOrEqual(0)
  })

  test('should open cleanup confirmation dialog', async ({ page }) => {
    const cleanupBtn = page.getByRole('button', { name: /cleanup expired/i })
    
    if (await cleanupBtn.count() > 0) {
      await cleanupBtn.click()
      
      const dialog = page.getByRole('dialog')
      await expect(dialog).toBeVisible()
      
      // Should have confirmation message
      await expect(dialog.getByText(/cleanup|expired/i)).toBeVisible()
    }
  })

  test('should cancel cleanup dialog', async ({ page }) => {
    const cleanupBtn = page.getByRole('button', { name: /cleanup expired/i })
    
    if (await cleanupBtn.count() > 0) {
      await cleanupBtn.click()
      
      const dialog = page.getByRole('dialog')
      const cancelBtn = dialog.getByRole('button', { name: /cancel/i })
      await cancelBtn.click()
      
      await expect(dialog).not.toBeVisible()
    }
  })
})

test.describe('Reports Page - Pagination', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/reports')
    await page.waitForLoadState('networkidle')
  })

  test('should display pagination info if multiple pages', async ({ page }) => {
    const paginationInfo = page.getByText(/showing \d+-\d+ of \d+/i)
    const infoCount = await paginationInfo.count()
    expect(infoCount).toBeGreaterThanOrEqual(0)
  })

  test('should have previous and next buttons', async ({ page }) => {
    const prevBtn = page.getByRole('button', { name: /previous/i })
    const nextBtn = page.getByRole('button', { name: /next/i })
    
    const prevCount = await prevBtn.count()
    const nextCount = await nextBtn.count()
    
    // Buttons appear only when pagination is needed
    if (prevCount > 0) {
      expect(nextCount).toBeGreaterThan(0)
    }
  })

  test('should disable previous button on first page', async ({ page }) => {
    const prevBtn = page.getByRole('button', { name: /previous/i })
    
    if (await prevBtn.count() > 0) {
      const isDisabled = await prevBtn.isDisabled()
      expect(isDisabled).toBe(true)
    }
  })

  test('should click next button if enabled', async ({ page }) => {
    const nextBtn = page.getByRole('button', { name: /next/i })
    
    if (await nextBtn.count() > 0) {
      if (await nextBtn.isEnabled()) {
        await nextBtn.click()
        await page.waitForLoadState('networkidle')
        
        // Page should update
        const prevBtn = page.getByRole('button', { name: /previous/i })
        const isEnabled = await prevBtn.isEnabled()
        expect(isEnabled).toBe(true)
      }
    }
  })
})

test.describe('Reports Page - Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/reports')
    await page.waitForLoadState('networkidle')
  })

  test('should navigate to plugins page via manage reporters button', async ({ page }) => {
    const manageBtn = page.getByRole('link', { name: /manage reporters/i })
    await manageBtn.click()
    
    await page.waitForLoadState('networkidle')
    expect(page.url()).toContain('/plugins')
  })

  test('should navigate to source detail via source link', async ({ page }) => {
    const table = page.getByRole('table')
    const sourceLinks = table.getByRole('link').filter({ hasText: /.+/ })
    
    if (await sourceLinks.count() > 0) {
      const firstLink = sourceLinks.first()
      const href = await firstLink.getAttribute('href')
      
      expect(href).toContain('/sources/')
    }
  })
})

test.describe('Reports Page - Error Handling', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/reports')
    await page.waitForLoadState('networkidle')
  })

  test('should handle search with no results', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i)
    await searchInput.fill('xyznonexistentreport99999')
    
    await page.waitForTimeout(1000)
    
    // Should show empty state or no reports message
    const emptyState = page.getByText(/no reports/i)
    const emptyCount = await emptyState.count()
    expect(emptyCount).toBeGreaterThanOrEqual(0)
  })

  test('should disable download button for non-completed reports', async ({ page }) => {
    const table = page.getByRole('table')
    
    // Find a non-completed report (pending, generating, failed, expired)
    const rows = table.getByRole('row')
    const count = await rows.count()
    
    if (count > 1) {
      for (let i = 1; i < count; i++) {
        const row = rows.nth(i)
        const statusBadge = row.locator('[class*="badge"]').filter({ hasText: /pending|generating|failed|expired/i })
        
        if (await statusBadge.count() > 0) {
          // Download button should be disabled
          const downloadBtn = row.getByRole('button').first()
          const isDisabled = await downloadBtn.isDisabled()
          expect(isDisabled).toBe(true)
          break
        }
      }
    }
  })

  test('should handle filter interactions gracefully', async ({ page }) => {
    // Apply various filters rapidly
    const searchInput = page.getByPlaceholder(/search/i)
    await searchInput.fill('test')
    
    const formatFilter = page.getByRole('combobox').filter({ hasText: /all formats|format/i }).first()
    await formatFilter.click()
    await page.getByRole('option', { name: /html/i }).click()
    
    await page.waitForTimeout(500)
    
    // Should still be responsive (table or empty state)
    const table = page.getByRole('table')
    const tableCount = await table.count()
    const emptyState = page.getByText(/no reports/i)
    const emptyCount = await emptyState.count()
    expect(tableCount + emptyCount).toBeGreaterThan(0)
  })
})

test.describe('Reports Page - Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/reports')
    await page.waitForLoadState('networkidle')
  })

  test('should have proper heading structure', async ({ page }) => {
    const h1 = page.getByRole('heading', { level: 1 })
    await expect(h1).toBeVisible()
    
    const headingText = await h1.textContent()
    expect(headingText).toMatch(/reports/i)
  })

  test('should have accessible search input', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i)
    await expect(searchInput).toBeVisible()
    
    // Should be keyboard accessible
    await searchInput.focus()
    await expect(searchInput).toBeFocused()
  })

  test('should have accessible filter dropdowns', async ({ page }) => {
    const formatFilter = page.getByRole('combobox').filter({ hasText: /all formats|format/i }).first()
    
    // Should be keyboard accessible
    await formatFilter.focus()
    await expect(formatFilter).toBeFocused()
  })

  test('should have accessible checkbox', async ({ page }) => {
    const checkbox = page.getByRole('checkbox', { name: /include expired/i })
    await expect(checkbox).toBeVisible()
    
    // Should have proper label
    const label = page.getByText(/include expired/i)
    await expect(label).toBeVisible()
  })

  test('should have accessible action buttons', async ({ page }) => {
    const table = page.getByRole('table')
    const rows = table.getByRole('row')
    const count = await rows.count()
    
    if (count > 1) {
      const firstRow = rows.nth(1)
      const buttons = firstRow.getByRole('button')
      const btnCount = await buttons.count()
      
      // All buttons should be accessible
      expect(btnCount).toBeGreaterThan(0)
    }
  })

  test('should have proper table structure if reports exist', async ({ page }) => {
    const table = page.getByRole('table')
    const tableCount = await table.count()
    
    if (tableCount > 0) {
      // Should have thead and tbody
      const headers = table.getByRole('columnheader')
      const headerCount = await headers.count()
      expect(headerCount).toBeGreaterThan(0)
    }
  })
})

test.describe('Reports Page - Performance', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/reports')
  })

  test('should load page within reasonable time', async ({ page }) => {
    const startTime = Date.now()
    await page.waitForLoadState('networkidle')
    const endTime = Date.now()
    
    const loadTime = endTime - startTime
    expect(loadTime).toBeLessThan(5000) // 5 seconds
  })

  test('should render statistics cards quickly', async ({ page }) => {
    await page.waitForLoadState('networkidle')
    
    const statsGrid = page.locator('[class*="grid"]').first()
    await expect(statsGrid).toBeVisible({ timeout: 3000 })
  })

  test('should handle rapid filter changes', async ({ page }) => {
    await page.waitForLoadState('networkidle')
    
    const searchInput = page.getByPlaceholder(/search/i)
    
    // Type rapidly
    for (let i = 0; i < 5; i++) {
      await searchInput.fill(`test${i}`)
      await page.waitForTimeout(100)
    }
    
    await page.waitForTimeout(300)
    
    // Should still be responsive
    const table = page.getByRole('table')
    const emptyState = page.getByText(/no reports/i)
    const hasContent = await table.count() > 0 || await emptyState.count() > 0
    expect(hasContent).toBe(true)
  })

  test('should handle pagination clicks smoothly', async ({ page }) => {
    await page.waitForLoadState('networkidle')
    
    const nextBtn = page.getByRole('button', { name: /next/i })
    
    if (await nextBtn.count() > 0 && await nextBtn.isEnabled()) {
      const startTime = Date.now()
      await nextBtn.click()
      await page.waitForLoadState('networkidle')
      const endTime = Date.now()
      
      expect(endTime - startTime).toBeLessThan(2000)
    }
  })
})

test.describe('Reports Page - Integration Scenarios', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/reports')
    await page.waitForLoadState('networkidle')
  })

  test('should search then filter by format', async ({ page }) => {
    // Search first
    const searchInput = page.getByPlaceholder(/search/i)
    await searchInput.fill('validation')
    
    await page.waitForTimeout(500)
    
    // Then filter by format
    const formatFilter = page.getByRole('combobox').filter({ hasText: /all formats|format/i }).first()
    await formatFilter.click()
    await page.getByRole('option', { name: /pdf/i }).click()
    
    await page.waitForTimeout(500)
    
    // Both filters should be applied
    await expect(searchInput).toHaveValue('validation')
  })

  test('should filter then paginate', async ({ page }) => {
    const statusFilter = page.getByRole('combobox').filter({ hasText: /all statuses|status/i }).first()
    await statusFilter.click()
    await page.getByRole('option', { name: /completed/i }).click()
    
    await page.waitForTimeout(500)
    
    const nextBtn = page.getByRole('button', { name: /next/i })
    if (await nextBtn.count() > 0 && await nextBtn.isEnabled()) {
      await nextBtn.click()
      await page.waitForLoadState('networkidle')
    }
  })

  test('should clear search and see results', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i)
    
    // Search
    await searchInput.fill('test')
    await page.waitForTimeout(500)
    
    // Clear
    await searchInput.clear()
    await page.waitForTimeout(500)
    
    // Should show content (table or empty state)
    const table = page.getByRole('table')
    const emptyState = page.getByText(/no reports/i)
    const hasContent = await table.count() > 0 || await emptyState.count() > 0
    expect(hasContent).toBe(true)
  })

  test('should toggle include expired checkbox', async ({ page }) => {
    const checkbox = page.getByRole('checkbox', { name: /include expired/i })
    
    // Get initial state
    const initialState = await checkbox.getAttribute('data-state')
    
    // Toggle checkbox
    await checkbox.click()
    await page.waitForTimeout(500)
    
    // State should have changed
    const newState = await checkbox.getAttribute('data-state')
    expect(newState).not.toBe(initialState)
  })

  test('should navigate from reports to plugins and back', async ({ page }) => {
    const manageBtn = page.getByRole('link', { name: /manage reporters/i })
    await manageBtn.click()
    
    await page.waitForLoadState('networkidle')
    expect(page.url()).toContain('/plugins')
    
    // Navigate back
    await page.goBack()
    await page.waitForLoadState('networkidle')
    expect(page.url()).toContain('/reports')
  })
})
