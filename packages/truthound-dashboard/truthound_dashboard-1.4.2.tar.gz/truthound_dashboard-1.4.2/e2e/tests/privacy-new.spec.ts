import { test, expect } from '@playwright/test';

test.describe('Privacy Page E2E', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/privacy');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(1500);
    });

    test('should load page structure', async ({ page }) => {
        await expect(page.getByRole('heading', { level: 1 })).toContainText(/Privacy/i);
        await expect(page.getByText('Total Scans')).toBeVisible();
    });

    test('should handle no sources', async ({ page }) => {
        const hasNoSources = await page.getByText('No data sources available').isVisible().catch(() => false);
        const hasSources = await page.getByRole('combobox').isVisible().catch(() => false);
        expect(hasNoSources || hasSources).toBeTruthy();
    });
});
