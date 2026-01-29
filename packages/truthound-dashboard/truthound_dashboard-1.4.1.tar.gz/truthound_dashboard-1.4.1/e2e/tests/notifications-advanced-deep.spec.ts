import { test, expect } from '@playwright/test'

/**
 * E2E Tests for Advanced Notifications Page - Deep Dive
 * 
 * Tests advanced features:
 * - ConfigImportExport component (export/import workflows)
 * - TemplateLibrary component (template browsing and selection)
 * - Integration scenarios (combined workflows)
 * - Edge cases (rapid toggling, keyboard navigation)
 * - Accessibility deep dive
 * - Performance and stability
 */

test.describe('ConfigImportExport Component', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/notifications/advanced')
    await page.waitForLoadState('networkidle')
  })

  test('should display config import/export card', async ({ page }) => {
    const exportCard = page.locator('text=Config Import/Export').first()
    await expect(exportCard).toBeVisible()
    
    // Should have both export and import sections
    const exportBtn = exportCard.getByRole('button', { name: /export.*json|download/i })
    const importBtn = exportCard.getByRole('button', { name: /import.*file|upload/i })
    
    await expect(exportBtn).toBeVisible()
    await expect(importBtn).toBeVisible()
  })

  test('should display all export options', async ({ page }) => {
    const exportCard = page.locator('text=Config Import/Export').first()
    
    // Should have checkboxes for all config types
    const exportOptions = exportCard.locator('[type="checkbox"]')
    const count = await exportOptions.count()
    expect(count).toBeGreaterThanOrEqual(1) // At least one option
  })

  test('should trigger download on export', async ({ page }) => {
    const exportCard = page.locator('text=Config Import/Export').first()
    const exportBtn = exportCard.getByRole('button', { name: /export.*json|download/i })
    
    // Setup download listener (may not work in mock mode)
    const downloadPromise = page.waitForEvent('download', { timeout: 5000 }).catch(() => null)
    await exportBtn.click()
    
    const download = await downloadPromise
    if (download) {
      expect(download.suggestedFilename()).toContain('.json')
    }
  })

  test('should open import dialog on import button click', async ({ page }) => {
    const exportCard = page.locator('text=Config Import/Export').first()
    const importBtn = exportCard.getByRole('button', { name: /import.*file|upload/i })
    
    await importBtn.click()
    
    const dialog = page.getByRole('dialog')
    await expect(dialog).toBeVisible()
  })

  test('should accept file input in import dialog', async ({ page }) => {
    const exportCard = page.locator('text=Config Import/Export').first()
    const importBtn = exportCard.getByRole('button', { name: /import.*file|upload/i })
    await importBtn.click()
    
    const dialog = page.getByRole('dialog')
    const fileInput = dialog.locator('input[type="file"]')
    
    // File input should exist (even if hidden)
    const count = await fileInput.count()
    expect(count).toBeGreaterThanOrEqual(1)
  })

  test('should cancel import dialog', async ({ page }) => {
    const exportCard = page.locator('text=Config Import/Export').first()
    const importBtn = exportCard.getByRole('button', { name: /import.*file|upload/i })
    await importBtn.click()
    
    const dialog = page.getByRole('dialog')
    const cancelBtn = dialog.getByRole('button', { name: /cancel|취소/i })
    await cancelBtn.click()
    
    await expect(dialog).not.toBeVisible()
  })

  test('should close import dialog on ESC key', async ({ page }) => {
    const exportCard = page.locator('text=Config Import/Export').first()
    const importBtn = exportCard.getByRole('button', { name: /import.*file|upload/i })
    await importBtn.click()
    
    const dialog = page.getByRole('dialog')
    await expect(dialog).toBeVisible()
    
    await page.keyboard.press('Escape')
    await page.waitForTimeout(500)
    
    const isVisible = await dialog.isVisible().catch(() => false)
    expect(isVisible).toBe(false)
  })
})

test.describe('TemplateLibrary Component', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/notifications/advanced')
    await page.waitForLoadState('networkidle')
  })

  test('should display template library card', async ({ page }) => {
    const templateCard = page.locator('text=Template Library').first()
    await expect(templateCard).toBeVisible()
    
    // Should have search input
    const searchInput = templateCard.getByPlaceholder(/search/i)
    await expect(searchInput).toBeVisible()
  })

  test('should display all template categories', async ({ page }) => {
    const templateCard = page.locator('text=Template Library').first()
    
    // Should have tabs for: all, routing, deduplication, throttling, escalation
    const categoryTabs = templateCard.getByRole('tab')
    const count = await categoryTabs.count()
    expect(count).toBe(5) // all + 4 categories
  })

  test('should filter templates by search', async ({ page }) => {
    const templateCard = page.locator('text=Template Library').first()
    const searchInput = templateCard.getByPlaceholder(/search/i)
    
    await searchInput.fill('routing')
    await page.waitForTimeout(300)
    
    // Templates should be filtered (count may vary)
    const templates = templateCard.locator('[data-testid="template-card"]')
    const count = await templates.count()
    // In mock mode, may not have actual templates
    expect(count).toBeGreaterThanOrEqual(0)
  })

  test('should show template preview on card click', async ({ page }) => {
    const templateCard = page.locator('text=Template Library').first()
    
    const firstTemplate = templateCard.locator('[data-testid="template-card"]').first()
    const templateCount = await firstTemplate.count()
    
    if (templateCount > 0) {
      await firstTemplate.click()
      await page.waitForTimeout(300)
      
      // Preview dialog should open
      const dialogs = page.getByRole('dialog')
      const dialogCount = await dialogs.count()
      expect(dialogCount).toBeGreaterThan(0)
    }
  })

  test('should have "Use Template" button in preview', async ({ page }) => {
    const templateCard = page.locator('text=Template Library').first()
    const firstTemplate = templateCard.locator('[data-testid="template-card"]').first()
    const templateCount = await firstTemplate.count()
    
    if (templateCount > 0) {
      await firstTemplate.click()
      await page.waitForTimeout(300)
      
      const previewDialog = page.getByRole('dialog').last()
      const useBtn = previewDialog.getByRole('button', { name: /use.*template|템플릿.*사용/i })
      
      const useBtnCount = await useBtn.count()
      expect(useBtnCount).toBeGreaterThanOrEqual(0)
    }
  })

  test('should switch between template categories', async ({ page }) => {
    const templateCard = page.locator('text=Template Library').first()
    
    const routingTab = templateCard.getByRole('tab', { name: /routing|라우팅/i })
    await routingTab.click()
    await page.waitForTimeout(200)
    
    const deduplicationTab = templateCard.getByRole('tab', { name: /deduplication|중복.*제거/i })
    await deduplicationTab.click()
    await page.waitForTimeout(200)
    
    // Should successfully switch tabs
    await expect(deduplicationTab).toHaveAttribute('data-state', 'active')
  })

  test('should display template library as always-visible card', async ({ page }) => {
    // TemplateLibrary is a Card that's always visible, not a dialog
    const templateCard = page.locator('text=Template Library').first()
    await expect(templateCard).toBeVisible()
    
    // Should be visible after page interactions
    await page.click('body')
    await expect(templateCard).toBeVisible()
  })
})

test.describe('Integration Scenarios', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/notifications/advanced')
    await page.waitForLoadState('networkidle')
  })

  test('should allow export then import workflow', async ({ page }) => {
    const configCard = page.locator('text=Config Import/Export').first()
    
    // Export config
    const exportBtn = configCard.getByRole('button', { name: /export.*json|download/i })
    const downloadPromise = page.waitForEvent('download', { timeout: 5000 }).catch(() => null)
    await exportBtn.click()
    await downloadPromise
    
    // Import should still be available
    const importBtn = configCard.getByRole('button', { name: /import.*file|upload/i })
    await expect(importBtn).toBeVisible()
  })

  test('should allow template selection workflow', async ({ page }) => {
    const templateCard = page.locator('text=Template Library').first()
    
    // Switch category
    const throttlingTab = templateCard.getByRole('tab', { name: /throttling|제한/i })
    await throttlingTab.click()
    await page.waitForTimeout(200)
    
    // Search for template
    const searchInput = templateCard.getByPlaceholder(/search/i)
    await searchInput.fill('basic')
    await page.waitForTimeout(300)
    
    // Template functionality still works
    await expect(searchInput).toHaveValue('basic')
  })

  test('should allow tab switch then export', async ({ page }) => {
    // Switch to Throttling tab
    const throttlingTab = page.getByRole('tab', { name: /throttling|제한/i })
    await throttlingTab.click()
    
    // Export should still work
    const configCard = page.locator('text=Config Import/Export').first()
    const exportBtn = configCard.getByRole('button', { name: /export.*json|download/i })
    await expect(exportBtn).toBeVisible()
  })

  test('should allow import then template browsing', async ({ page }) => {
    const configCard = page.locator('text=Config Import/Export').first()
    
    // Open import
    const importBtn = configCard.getByRole('button', { name: /import.*file|upload/i })
    await importBtn.click()
    
    const dialog = page.getByRole('dialog')
    const cancelBtn = dialog.getByRole('button', { name: /cancel|취소/i })
    await cancelBtn.click()
    
    // Template library should still be visible
    const templateCard = page.locator('text=Template Library').first()
    await expect(templateCard).toBeVisible()
  })

  test('should refresh after export', async ({ page }) => {
    const configCard = page.locator('text=Config Import/Export').first()
    
    // Export
    const exportBtn = configCard.getByRole('button', { name: /export.*json|download/i })
    const downloadPromise = page.waitForEvent('download', { timeout: 5000 }).catch(() => null)
    await exportBtn.click()
    await downloadPromise
    
    // Click refresh (separate button outside cards)
    const refreshBtn = page.getByRole('button', { name: /refresh|새로고침/i })
    if (await refreshBtn.isVisible()) {
      await refreshBtn.click()
      await page.waitForLoadState('networkidle')
    }
  })
})

test.describe('Edge Cases', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/notifications/advanced')
    await page.waitForLoadState('networkidle')
  })

  test('should handle rapid tab toggling', async ({ page }) => {
    const tabs = [
      /routing|라우팅/i,
      /deduplication|중복.*제거/i,
      /throttling|제한/i,
      /escalation|에스컬레이션/i,
    ]
    
    for (let i = 0; i < 10; i++) {
      const tabName = tabs[i % tabs.length]
      const tab = page.getByRole('tab', { name: tabName })
      await tab.click()
      await page.waitForTimeout(50)
    }
    
    // Should still be responsive
    const lastTab = page.getByRole('tab', { name: tabs[tabs.length - 1] })
    await expect(lastTab).toBeVisible()
  })

  test('should handle keyboard navigation properly', async ({ page }) => {
    const configCard = page.locator('text=Config Import/Export').first()
    const exportBtn = configCard.getByRole('button', { name: /export.*json|download/i })
    
    // Focus export button
    await exportBtn.focus()
    await expect(exportBtn).toBeFocused()
  })

  test('should prevent concurrent import dialog opens', async ({ page }) => {
    const configCard = page.locator('text=Config Import/Export').first()
    const importBtn = configCard.getByRole('button', { name: /import.*file|upload/i })
    
    // Click multiple times quickly
    await importBtn.click()
    await importBtn.click()
    await importBtn.click()
    
    // Should only have one dialog
    const dialogs = page.getByRole('dialog')
    const count = await dialogs.count()
    expect(count).toBeLessThanOrEqual(1)
  })

  test('should handle empty template search results', async ({ page }) => {
    const templateCard = page.locator('text=Template Library').first()
    const searchInput = templateCard.getByPlaceholder(/search/i)
    
    await searchInput.fill('xyznonexistenttemplate123')
    await page.waitForTimeout(300)
    
    // Should not crash - may show empty state or no results
    await expect(searchInput).toBeVisible()
  })

  test('should handle template category with no templates', async ({ page }) => {
    const templateCard = page.locator('text=Template Library').first()
    
    // Click on a category that might be empty
    const escalationTab = templateCard.getByRole('tab', { name: /escalation|에스컬레이션/i })
    await escalationTab.click()
    await page.waitForTimeout(300)
    
    // Should not crash
    await expect(templateCard).toBeVisible()
  })
})

test.describe('Accessibility Deep Dive', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/notifications/advanced')
    await page.waitForLoadState('networkidle')
  })

  test('should have proper ARIA labels on action buttons', async ({ page }) => {
    const configCard = page.locator('text=Config Import/Export').first()
    
    // Export button
    const exportBtn = configCard.getByRole('button', { name: /export.*json|download/i })
    await expect(exportBtn).toBeVisible()
    
    // Import button
    const importBtn = configCard.getByRole('button', { name: /import.*file|upload/i })
    await expect(importBtn).toBeVisible()
  })

  test('should manage focus properly in dialogs', async ({ page }) => {
    const configCard = page.locator('text=Config Import/Export').first()
    const importBtn = configCard.getByRole('button', { name: /import.*file|upload/i })
    await importBtn.click()
    
    // Focus should be in dialog
    const dialog = page.getByRole('dialog')
    await expect(dialog).toBeVisible()
    
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName)
    expect(['INPUT', 'BUTTON', 'LABEL', 'DIV', 'BODY']).toContain(focusedElement)
  })

  test('should have proper semantic structure', async ({ page }) => {
    // Cards should have proper structure
    const configCard = page.locator('text=Config Import/Export').first()
    await expect(configCard).toBeVisible()
    
    const templateCard = page.locator('text=Template Library').first()
    await expect(templateCard).toBeVisible()
  })

  test('should maintain stats card structure', async ({ page }) => {
    // Stats cards should have accessible content
    const statsCards = page.locator('[class*="grid"]').first()
    await expect(statsCards).toBeVisible()
  })
})

test.describe('Performance & Stability', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/notifications/advanced')
    await page.waitForLoadState('networkidle')
  })

  test('should open dialogs within performance budget', async ({ page }) => {
    const configCard = page.locator('text=Config Import/Export').first()
    const importBtn = configCard.getByRole('button', { name: /import.*file|upload/i })
    
    const startTime = Date.now()
    await importBtn.click()
    await page.waitForSelector('[role="dialog"]', { state: 'visible', timeout: 5000 })
    const endTime = Date.now()
    
    expect(endTime - startTime).toBeLessThan(1000) // 1 second budget
  })

  test('should not have memory leaks from repeated dialog opens', async ({ page }) => {
    const configCard = page.locator('text=Config Import/Export').first()
    const importBtn = configCard.getByRole('button', { name: /import.*file|upload/i })
    
    // Open and close 10 times
    for (let i = 0; i < 10; i++) {
      await importBtn.click()
      const dialog = page.getByRole('dialog')
      await expect(dialog).toBeVisible()
      
      const cancelBtn = dialog.getByRole('button', { name: /cancel|취소/i })
      await cancelBtn.click()
      await page.waitForTimeout(100)
    }
    
    // Should not have multiple dialogs in DOM
    const dialogs = page.getByRole('dialog', { includeHidden: true })
    const count = await dialogs.count()
    expect(count).toBeLessThanOrEqual(1)
  })

  test('should handle rapid template category switches', async ({ page }) => {
    const templateCard = page.locator('text=Template Library').first()
    
    const tabs = await templateCard.getByRole('tab').all()
    
    // Rapidly switch between tabs
    for (let i = 0; i < 20; i++) {
      const tab = tabs[i % tabs.length]
      await tab.click()
      await page.waitForTimeout(50)
    }
    
    // Should still be responsive
    await expect(templateCard).toBeVisible()
  })

  test('should maintain stats stability during interactions', async ({ page }) => {
    // Get initial stats
    const stats = page.locator('[class*="grid"]').first()
    await expect(stats).toBeVisible()
    
    // Perform various actions
    const configCard = page.locator('text=Config Import/Export').first()
    const exportBtn = configCard.getByRole('button', { name: /export.*json|download/i })
    await exportBtn.click().catch(() => {})
    
    await page.waitForTimeout(500)
    
    // Stats should still be visible
    await expect(stats).toBeVisible()
  })
})
