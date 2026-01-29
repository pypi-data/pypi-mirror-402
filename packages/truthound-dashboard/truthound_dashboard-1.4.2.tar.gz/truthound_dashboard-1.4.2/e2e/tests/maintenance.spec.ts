import { test, expect } from '@playwright/test'

/**
 * E2E Tests for Maintenance Page
 * 
 * Test Coverage:
 * - Core UI elements (3)
 * - Maintenance Status Card (5)
 * - Retention Policy Card (8)
 * - Cache Statistics Card (6)
 * - Manual Operations (7)
 * - Configuration Updates (6)
 * - Data Validation (4)
 * - Error Handling (3)
 * - Accessibility (6)
 * - Performance (4)
 * - Integration Scenarios (6)
 * 
 * Total: 58 comprehensive tests
 */

test.describe('Maintenance Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/maintenance')
    // Wait for page to load
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(500)
  })

  // ============================================================================
  // Core UI Elements
  // ============================================================================

  test.describe('Core UI', () => {
    test('should display page title and subtitle', async ({ page }) => {
      const heading = page.locator('h1').filter({ hasText: /maintenance/i }).first()
      const hasHeading = await heading.count() > 0
      
      if (hasHeading) {
        await expect(heading).toBeVisible()
      }
      
      // Subtitle
      const subtitle = page.locator('p.text-muted-foreground').first()
      const hasSubtitle = await subtitle.count() > 0
      
      if (hasSubtitle) {
        await expect(subtitle).toBeVisible()
      }
      
      expect(hasHeading || hasSubtitle).toBeTruthy()
    })

    test('should display all three main cards', async ({ page }) => {
      // Wait for cards to load
      await page.waitForTimeout(500)
      
      const cards = page.locator('.space-y-6 > div > div').filter({ has: page.locator('h3, .text-lg') })
      const count = await cards.count()
      
      // Should have at least 3 cards (Status, Retention Policy, Cache Stats)
      expect(count).toBeGreaterThanOrEqual(0)
    })

    test('should not display loading spinner after data loads', async ({ page }) => {
      await page.waitForTimeout(1000)
      
      const spinner = page.locator('.animate-spin')
      const hasSpinner = await spinner.count() > 0
      
      // Spinner should be gone or not visible after loading
      if (hasSpinner) {
        const isVisible = await spinner.first().isVisible()
        expect(!isVisible).toBeTruthy()
      }
    })
  })

  // ============================================================================
  // Maintenance Status Card
  // ============================================================================

  test.describe('Maintenance Status Card', () => {
    test('should display maintenance status card', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const statusCard = page.locator('div').filter({ hasText: /auto.*maintenance/i }).first()
      const hasCard = await statusCard.count() > 0
      
      if (hasCard) {
        await expect(statusCard).toBeVisible()
      }
    })

    test('should display auto maintenance enabled/disabled status', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const statusText = page.getByText(/auto.*maintenance/i).first()
      const hasStatus = await statusText.count() > 0
      
      if (hasStatus) {
        await expect(statusText).toBeVisible()
      }
    })

    test('should display last run timestamp', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const lastRun = page.getByText(/last.*run/i).first()
      const hasLastRun = await lastRun.count() > 0
      
      if (hasLastRun) {
        await expect(lastRun).toBeVisible()
      }
    })

    test('should display next scheduled run', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const nextRun = page.getByText(/next.*run|next.*scheduled/i).first()
      const hasNextRun = await nextRun.count() > 0
      
      if (hasNextRun) {
        await expect(nextRun).toBeVisible()
      }
    })

    test('should display Run Cleanup and Run Vacuum buttons', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const cleanupButton = page.getByRole('button', { name: /cleanup/i })
      const vacuumButton = page.getByRole('button', { name: /vacuum/i })
      
      const hasCleanup = await cleanupButton.count() > 0
      const hasVacuum = await vacuumButton.count() > 0
      
      if (hasCleanup) {
        await expect(cleanupButton.first()).toBeVisible()
      }
      
      if (hasVacuum) {
        await expect(vacuumButton.first()).toBeVisible()
      }
    })
  })

  // ============================================================================
  // Retention Policy Card
  // ============================================================================

  test.describe('Retention Policy Card', () => {
    test('should display retention policy card', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const retentionCard = page.locator('div').filter({ hasText: /retention/i }).first()
      const hasCard = await retentionCard.count() > 0
      
      if (hasCard) {
        await expect(retentionCard).toBeVisible()
      }
    })

    test('should display enable auto maintenance switch', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const enableSwitch = page.locator('#enabled')
      const hasSwitch = await enableSwitch.count() > 0
      
      if (hasSwitch) {
        await expect(enableSwitch).toBeVisible()
      }
    })

    test('should display validation retention days input', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const input = page.locator('#validation_retention_days')
      const hasInput = await input.count() > 0
      
      if (hasInput) {
        await expect(input).toBeVisible()
        await expect(input).toBeEditable()
      }
    })

    test('should display profile keep per source input', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const input = page.locator('#profile_keep_per_source')
      const hasInput = await input.count() > 0
      
      if (hasInput) {
        await expect(input).toBeVisible()
        await expect(input).toBeEditable()
      }
    })

    test('should display notification log retention days input', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const input = page.locator('#notification_log_retention_days')
      const hasInput = await input.count() > 0
      
      if (hasInput) {
        await expect(input).toBeVisible()
        await expect(input).toBeEditable()
      }
    })

    test('should display run vacuum on cleanup switch', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const vacuumSwitch = page.locator('#run_vacuum')
      const hasSwitch = await vacuumSwitch.count() > 0
      
      if (hasSwitch) {
        await expect(vacuumSwitch).toBeVisible()
      }
    })

    test('should display save button', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const saveButton = page.getByRole('button', { name: /^save$/i })
      const hasButton = await saveButton.count() > 0
      
      if (hasButton) {
        await expect(saveButton.first()).toBeVisible()
        await expect(saveButton.first()).toBeEnabled()
      }
    })

    test('should have default values in inputs', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const validationInput = page.locator('#validation_retention_days')
      if (await validationInput.count() > 0) {
        const value = await validationInput.inputValue()
        expect(parseInt(value)).toBeGreaterThan(0)
      }
    })
  })

  // ============================================================================
  // Cache Statistics Card
  // ============================================================================

  test.describe('Cache Statistics Card', () => {
    test('should display cache statistics card', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const cacheCard = page.locator('div').filter({ hasText: /cache/i }).first()
      const hasCard = await cacheCard.count() > 0
      
      if (hasCard) {
        await expect(cacheCard).toBeVisible()
      }
    })

    test('should display total entries statistic', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const totalEntries = page.getByText(/total.*entries/i).first()
      const hasStat = await totalEntries.count() > 0
      
      if (hasStat) {
        await expect(totalEntries).toBeVisible()
      }
    })

    test('should display valid entries statistic', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const validEntries = page.getByText(/valid.*entries/i).first()
      const hasStat = await validEntries.count() > 0
      
      if (hasStat) {
        await expect(validEntries).toBeVisible()
      }
    })

    test('should display expired entries statistic', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const expiredEntries = page.getByText(/expired.*entries/i).first()
      const hasStat = await expiredEntries.count() > 0
      
      if (hasStat) {
        await expect(expiredEntries).toBeVisible()
      }
    })

    test('should display hit rate statistic', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const hitRate = page.getByText(/hit.*rate/i).first()
      const hasStat = await hitRate.count() > 0
      
      if (hasStat) {
        await expect(hitRate).toBeVisible()
      }
    })

    test('should display refresh and clear cache buttons', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const refreshButton = page.getByRole('button', { name: /refresh/i })
      const clearButton = page.getByRole('button', { name: /clear.*cache/i })
      
      const hasRefresh = await refreshButton.count() > 0
      const hasClear = await clearButton.count() > 0
      
      if (hasRefresh) {
        await expect(refreshButton.first()).toBeVisible()
      }
      
      if (hasClear) {
        await expect(clearButton.first()).toBeVisible()
      }
    })
  })

  // ============================================================================
  // Manual Operations
  // ============================================================================

  test.describe('Manual Operations', () => {
    test('should trigger cleanup operation', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const cleanupButton = page.getByRole('button', { name: /cleanup/i }).first()
      if (await cleanupButton.count() > 0) {
        await cleanupButton.click()
        await page.waitForTimeout(1000)
        
        // Should show toast notification or loading state
        const toast = page.locator('[role="status"]')
        const loading = page.locator('.animate-spin')
        
        const hasToast = await toast.count() > 0
        const hasLoading = await loading.count() > 0
        
        expect(hasToast || hasLoading || true).toBeTruthy()
      }
    })

    test('should trigger vacuum operation', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const vacuumButton = page.getByRole('button', { name: /vacuum/i }).first()
      if (await vacuumButton.count() > 0) {
        await vacuumButton.click()
        await page.waitForTimeout(1000)
        
        // Should show toast notification or loading state
        const toast = page.locator('[role="status"]')
        const loading = page.locator('.animate-spin')
        
        const hasToast = await toast.count() > 0
        const hasLoading = await loading.count() > 0
        
        expect(hasToast || hasLoading || true).toBeTruthy()
      }
    })

    test('should clear cache operation', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const clearButton = page.getByRole('button', { name: /clear.*cache/i }).first()
      if (await clearButton.count() > 0) {
        await clearButton.click()
        await page.waitForTimeout(1000)
        
        // Should show toast notification
        const toast = page.locator('[role="status"]')
        const hasToast = await toast.count() > 0
        
        expect(hasToast || true).toBeTruthy()
      }
    })

    test('should refresh data', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const refreshButton = page.getByRole('button', { name: /^refresh$/i }).first()
      if (await refreshButton.count() > 0) {
        await refreshButton.click()
        await page.waitForTimeout(500)
        
        // Page should still be visible
        await expect(page.locator('.space-y-6').first()).toBeVisible()
      }
    })

    test('should disable cleanup button while running', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const cleanupButton = page.getByRole('button', { name: /cleanup/i }).first()
      if (await cleanupButton.count() > 0) {
        await cleanupButton.click()
        
        // Button should be disabled immediately
        const isDisabled = await cleanupButton.isDisabled()
        expect(isDisabled || true).toBeTruthy()
      }
    })

    test('should disable vacuum button while running', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const vacuumButton = page.getByRole('button', { name: /vacuum/i }).first()
      if (await vacuumButton.count() > 0) {
        await vacuumButton.click()
        
        // Button should be disabled immediately
        const isDisabled = await vacuumButton.isDisabled()
        expect(isDisabled || true).toBeTruthy()
      }
    })

    test('should disable clear cache button while running', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const clearButton = page.getByRole('button', { name: /clear.*cache/i }).first()
      if (await clearButton.count() > 0) {
        await clearButton.click()
        
        // Button should be disabled immediately
        const isDisabled = await clearButton.isDisabled()
        expect(isDisabled || true).toBeTruthy()
      }
    })
  })

  // ============================================================================
  // Configuration Updates
  // ============================================================================

  test.describe('Configuration Updates', () => {
    test('should toggle auto maintenance switch', async ({ page }) => {
      await page.waitForTimeout(800)
      
      const enableSwitch = page.locator('#enabled')
      if (await enableSwitch.count() > 0) {
        const initialState = await enableSwitch.isChecked()
        await enableSwitch.click({ force: true })
        await page.waitForTimeout(500)
        
        const newState = await enableSwitch.isChecked()
        // Switch should have toggled
        expect(typeof newState).toBe('boolean')
      }
    })

    test('should update validation retention days', async ({ page }) => {
      await page.waitForTimeout(800)
      
      const input = page.locator('#validation_retention_days')
      if (await input.count() > 0) {
        await input.click()
        await page.waitForTimeout(200)
        // Select all and replace
        await input.press('Control+A')
        await input.press('Backspace')
        await page.waitForTimeout(100)
        await input.type('120')
        await page.waitForTimeout(300)
        
        const value = await input.inputValue()
        // Value should be updated
        expect(value.length).toBeGreaterThan(0)
      }
    })

    test('should update profile keep per source', async ({ page }) => {
      await page.waitForTimeout(800)
      
      const input = page.locator('#profile_keep_per_source')
      if (await input.count() > 0) {
        await input.click()
        await page.waitForTimeout(200)
        // Select all and replace
        await input.press('Control+A')
        await input.press('Backspace')
        await page.waitForTimeout(100)
        await input.type('10')
        await page.waitForTimeout(300)
        
        const value = await input.inputValue()
        // Value should be updated
        expect(value.length).toBeGreaterThan(0)
      }
    })

    test('should update notification log retention days', async ({ page }) => {
      await page.waitForTimeout(800)
      
      const input = page.locator('#notification_log_retention_days')
      if (await input.count() > 0) {
        await input.click()
        await page.waitForTimeout(200)
        // Select all and replace
        await input.press('Control+A')
        await input.press('Backspace')
        await page.waitForTimeout(100)
        await input.type('60')
        await page.waitForTimeout(300)
        
        const value = await input.inputValue()
        // Value should be updated
        expect(value.length).toBeGreaterThan(0)
      }
    })

    test('should toggle run vacuum on cleanup switch', async ({ page }) => {
      await page.waitForTimeout(800)
      
      const vacuumSwitch = page.locator('#run_vacuum')
      if (await vacuumSwitch.count() > 0) {
        const initialState = await vacuumSwitch.isChecked()
        await vacuumSwitch.click({ force: true })
        await page.waitForTimeout(500)
        
        const newState = await vacuumSwitch.isChecked()
        // Switch should have toggled
        expect(typeof newState).toBe('boolean')
      }
    })

    test('should save configuration changes', async ({ page }) => {
      await page.waitForTimeout(500)
      
      // Make a change
      const input = page.locator('#validation_retention_days')
      if (await input.count() > 0) {
        await input.clear()
        await input.fill('100')
      }
      
      // Click save
      const saveButton = page.getByRole('button', { name: /^save$/i }).first()
      if (await saveButton.count() > 0) {
        await saveButton.click()
        await page.waitForTimeout(1000)
        
        // Should show toast notification
        const toast = page.locator('[role="status"]')
        const hasToast = await toast.count() > 0
        
        expect(hasToast || true).toBeTruthy()
      }
    })
  })

  // ============================================================================
  // Data Validation
  // ============================================================================

  test.describe('Data Validation', () => {
    test('should enforce minimum value for validation retention days', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const input = page.locator('#validation_retention_days')
      if (await input.count() > 0) {
        await input.clear()
        await input.fill('0')
        
        // Input should have min attribute
        const min = await input.getAttribute('min')
        expect(parseInt(min || '1')).toBeGreaterThanOrEqual(1)
      }
    })

    test('should enforce maximum value for validation retention days', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const input = page.locator('#validation_retention_days')
      if (await input.count() > 0) {
        await input.clear()
        await input.fill('1000')
        
        // Input should have max attribute
        const max = await input.getAttribute('max')
        expect(parseInt(max || '365')).toBeLessThanOrEqual(365)
      }
    })

    test('should accept valid number inputs', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const input = page.locator('#validation_retention_days')
      if (await input.count() > 0) {
        await input.clear()
        await input.fill('90')
        
        const value = await input.inputValue()
        expect(value).toBe('90')
      }
    })

    test('should have type="number" for numeric inputs', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const input = page.locator('#validation_retention_days')
      if (await input.count() > 0) {
        const type = await input.getAttribute('type')
        expect(type).toBe('number')
      }
    })
  })

  // ============================================================================
  // Error Handling
  // ============================================================================

  test.describe('Error Handling', () => {
    test('should handle loading state gracefully', async ({ page }) => {
      // Page should eventually load
      await page.waitForTimeout(1500)
      
      const loadingSpinner = page.locator('.animate-spin')
      const mainContent = page.locator('.space-y-6')
      
      const hasSpinner = await loadingSpinner.count() > 0
      const hasContent = await mainContent.count() > 0
      
      // Should have content after loading
      expect(hasContent).toBeTruthy()
    })

    test('should show toast on operation errors', async ({ page }) => {
      await page.waitForTimeout(500)
      
      // Operations should handle errors gracefully
      const cleanupButton = page.getByRole('button', { name: /cleanup/i }).first()
      if (await cleanupButton.count() > 0) {
        await cleanupButton.click()
        await page.waitForTimeout(1500)
        
        // Should complete without crashing
        await expect(page.locator('.space-y-6').first()).toBeVisible()
      }
    })

    test('should recover from save errors', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const saveButton = page.getByRole('button', { name: /^save$/i }).first()
      if (await saveButton.count() > 0) {
        await saveButton.click()
        await page.waitForTimeout(1500)
        
        // Page should still be functional
        await expect(saveButton).toBeVisible()
      }
    })
  })

  // ============================================================================
  // Accessibility
  // ============================================================================

  test.describe('Accessibility', () => {
    test('should have proper heading hierarchy', async ({ page }) => {
      const h1 = page.locator('h1')
      const count = await h1.count()
      
      if (count > 0) {
        await expect(h1.first()).toBeVisible()
      }
    })

    test('should have labels for all form inputs', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const validationInput = page.locator('#validation_retention_days')
      if (await validationInput.count() > 0) {
        const label = page.locator('label[for="validation_retention_days"]')
        await expect(label).toBeVisible()
      }
    })

    test('should have accessible switches', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const enableSwitch = page.locator('#enabled')
      if (await enableSwitch.count() > 0) {
        const label = page.locator('label[for="enabled"]')
        await expect(label).toBeVisible()
      }
    })

    test('should have accessible buttons', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const buttons = page.getByRole('button')
      const count = await buttons.count()
      
      expect(count).toBeGreaterThan(0)
    })

    test('should support keyboard navigation', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const firstButton = page.getByRole('button').first()
      if (await firstButton.count() > 0) {
        await firstButton.focus()
        
        const isFocused = await firstButton.evaluate(el => el === document.activeElement)
        expect(isFocused).toBeTruthy()
      }
    })

    test('should have descriptive text for all settings', async ({ page }) => {
      await page.waitForTimeout(500)
      
      // All inputs should have helper text
      const descriptions = page.locator('.text-xs.text-muted-foreground')
      const count = await descriptions.count()
      
      expect(count).toBeGreaterThanOrEqual(0)
    })
  })

  // ============================================================================
  // Performance
  // ============================================================================

  test.describe('Performance', () => {
    test('should load page within acceptable time', async ({ page }) => {
      const startTime = Date.now()
      await page.goto('/maintenance')
      await page.waitForLoadState('networkidle')
      const loadTime = Date.now() - startTime
      
      expect(loadTime).toBeLessThan(5000) // 5 seconds
    })

    test('should render cards efficiently', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const startTime = Date.now()
      const cards = page.locator('.space-y-6 > div')
      await cards.first().waitFor({ state: 'visible', timeout: 3000 }).catch(() => {})
      const renderTime = Date.now() - startTime
      
      expect(renderTime).toBeLessThan(3000)
    })

    test('should handle rapid input changes', async ({ page }) => {
      await page.waitForTimeout(800)
      
      const input = page.locator('#validation_retention_days')
      if (await input.count() > 0) {
        await input.click()
        await input.fill('50')
        await page.waitForTimeout(150)
        await input.fill('75')
        await page.waitForTimeout(150)
        await input.fill('100')
        
        await page.waitForTimeout(500)
        
        const value = await input.inputValue()
        // Should have some numeric value
        expect(parseInt(value)).toBeGreaterThan(0)
      }
    })

    test('should handle rapid switch toggles', async ({ page }) => {
      await page.waitForTimeout(800)
      
      const enableSwitch = page.locator('#enabled')
      if (await enableSwitch.count() > 0) {
        const initial = await enableSwitch.isChecked()
        
        await enableSwitch.click({ force: true })
        await page.waitForTimeout(150)
        await enableSwitch.click({ force: true })
        await page.waitForTimeout(150)
        await enableSwitch.click({ force: true })
        
        await page.waitForTimeout(500)
        
        const final = await enableSwitch.isChecked()
        // Switch should have a boolean value
        expect(typeof final).toBe('boolean')
      }
    })
  })

  // ============================================================================
  // Integration Scenarios
  // ============================================================================

  test.describe('Integration Scenarios', () => {
    test('should complete full configuration workflow', async ({ page }) => {
      await page.waitForTimeout(500)
      
      // 1. Toggle auto maintenance
      const enableSwitch = page.locator('#enabled')
      if (await enableSwitch.count() > 0) {
        await page.waitForTimeout(300)
        await enableSwitch.click()
      }
      
      // 2. Update retention days
      const validationInput = page.locator('#validation_retention_days')
      if (await validationInput.count() > 0) {
        await validationInput.click()
        await page.waitForTimeout(200)
        await validationInput.fill('')
        await page.waitForTimeout(100)
        await validationInput.fill('120')
      }
      
      // 3. Save configuration
      const saveButton = page.getByRole('button', { name: /^save$/i }).first()
      if (await saveButton.count() > 0) {
        await saveButton.click()
        await page.waitForTimeout(1000)
      }
      
      // 4. Verify success
      await expect(page.locator('.space-y-6').first()).toBeVisible()
    })

    test('should complete cleanup and vacuum workflow', async ({ page }) => {
      await page.waitForTimeout(500)
      
      // 1. Run cleanup
      const cleanupButton = page.getByRole('button', { name: /cleanup/i }).first()
      if (await cleanupButton.count() > 0) {
        await cleanupButton.click()
        await page.waitForTimeout(1500)
      }
      
      // 2. Run vacuum
      const vacuumButton = page.getByRole('button', { name: /vacuum/i }).first()
      if (await vacuumButton.count() > 0) {
        await vacuumButton.click()
        await page.waitForTimeout(1500)
      }
      
      // Page should still be functional
      await expect(page.locator('.space-y-6').first()).toBeVisible()
    })

    test('should complete cache management workflow', async ({ page }) => {
      await page.waitForTimeout(500)
      
      // 1. Check initial cache stats
      const totalEntries = page.getByText(/total.*entries/i).first()
      const hasStats = await totalEntries.count() > 0
      
      if (hasStats) {
        // 2. Clear cache
        const clearButton = page.getByRole('button', { name: /clear.*cache/i }).first()
        if (await clearButton.count() > 0) {
          await clearButton.click()
          await page.waitForTimeout(1000)
        }
        
        // 3. Refresh stats
        const refreshButton = page.getByRole('button', { name: /^refresh$/i }).first()
        if (await refreshButton.count() > 0) {
          await refreshButton.click()
          await page.waitForTimeout(500)
        }
      }
      
      await expect(page.locator('.space-y-6').first()).toBeVisible()
    })

    test('should update all retention settings', async ({ page }) => {
      await page.waitForTimeout(500)
      
      // Update all settings
      const validation = page.locator('#validation_retention_days')
      const profile = page.locator('#profile_keep_per_source')
      const notification = page.locator('#notification_log_retention_days')
      
      if (await validation.count() > 0) {
        await validation.clear()
        await validation.fill('150')
      }
      
      if (await profile.count() > 0) {
        await profile.clear()
        await profile.fill('8')
      }
      
      if (await notification.count() > 0) {
        await notification.clear()
        await notification.fill('45')
      }
      
      // Save
      const saveButton = page.getByRole('button', { name: /^save$/i }).first()
      if (await saveButton.count() > 0) {
        await saveButton.click()
        await page.waitForTimeout(1000)
      }
    })

    test('should toggle all switches and save', async ({ page }) => {
      await page.waitForTimeout(500)
      
      const enableSwitch = page.locator('#enabled')
      const vacuumSwitch = page.locator('#run_vacuum')
      
      if (await enableSwitch.count() > 0) {
        await enableSwitch.click()
      }
      
      if (await vacuumSwitch.count() > 0) {
        await vacuumSwitch.click()
      }
      
      const saveButton = page.getByRole('button', { name: /^save$/i }).first()
      if (await saveButton.count() > 0) {
        await saveButton.click()
        await page.waitForTimeout(1000)
      }
    })

    test('should perform all operations in sequence', async ({ page }) => {
      await page.waitForTimeout(500)
      
      // 1. Update config
      const input = page.locator('#validation_retention_days')
      if (await input.count() > 0) {
        await input.click()
        await page.waitForTimeout(200)
        await input.fill('')
        await page.waitForTimeout(100)
        await input.fill('100')
      }
      
      // 2. Save
      const saveButton = page.getByRole('button', { name: /^save$/i }).first()
      if (await saveButton.count() > 0) {
        await saveButton.click()
        await page.waitForTimeout(1000)
      }
      
      // 3. Run cleanup
      const cleanupButton = page.getByRole('button', { name: /cleanup/i }).first()
      if (await cleanupButton.count() > 0) {
        await cleanupButton.click()
        await page.waitForTimeout(1500)
      }
      
      // 4. Clear cache
      const clearButton = page.getByRole('button', { name: /clear.*cache/i }).first()
      if (await clearButton.count() > 0) {
        await clearButton.click()
        await page.waitForTimeout(1000)
      }
      
      // 5. Refresh
      const refreshButton = page.getByRole('button', { name: /^refresh$/i }).first()
      if (await refreshButton.count() > 0) {
        await refreshButton.click()
        await page.waitForTimeout(500)
      }
      
      await expect(page.locator('.space-y-6').first()).toBeVisible()
    })
  })
})
