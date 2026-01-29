import { test, expect } from '@playwright/test';

test.describe('Example E2E Tests', () => {
  test('homepage loads successfully', async ({ page }) => {
    await page.goto('/');

    // Wait for the app to load
    await expect(page.locator('body')).toBeVisible();
  });
});
