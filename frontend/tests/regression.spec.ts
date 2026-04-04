import { test, expect, type Page } from '@playwright/test';

const API_BASE = 'http://127.0.0.1:8000';

async function signIn(page: Page) {
  await page.goto('/admin');
  await page.locator('input[name="username"]').fill('admin');
  await page.locator('input[name="password"]').fill('password');
  await page.locator('button[type="submit"]').click();
  await expect(page.locator('h2')).toContainText('Administration');
}

// ---------------------------------------------------------------------------
// Regression: vote availability must be accessible without admin login
// (previously called /admin/vote-availability which returned 401)
// ---------------------------------------------------------------------------
test.describe('Public vote availability (no admin login)', () => {
  test('voting page loads availability without admin session', async ({ page }) => {
    await page.goto('/vote');

    // The page should display day/meal selectors loaded from /votes/availability
    await expect(page.getByLabel('Jour')).toBeVisible();
    await expect(page.getByLabel('Repas')).toBeVisible();

    // Should NOT show an error about loading availability
    await expect(page.locator('body')).not.toContainText('Impossible de charger la disponibilité');
  });

  test('public /votes/availability API returns 200 without auth', async ({ page }) => {
    const response = await page.request.get(`${API_BASE}/votes/availability`);
    expect(response.ok()).toBeTruthy();
    const slots = await response.json();
    expect(slots.length).toBeGreaterThan(0);
    expect(slots[0]).toHaveProperty('day');
    expect(slots[0]).toHaveProperty('meal');
    expect(slots[0]).toHaveProperty('available');
  });
});

// ---------------------------------------------------------------------------
// Regression: admin routes must work after login (session cookie persistence)
// (previously returned 401 due to in-memory session loss on Lambda)
// ---------------------------------------------------------------------------
test.describe('Admin session persistence', () => {
  test('admin can perform multiple actions after single login', async ({ page }) => {
    await signIn(page);

    // Navigate between tabs — each one triggers an admin-protected request
    await page.getByRole('tab', { name: 'Membres' }).click();
    await expect(page.locator('.admin-body')).toBeVisible();

    await page.getByRole('tab', { name: 'Catalogue' }).click();
    await expect(page.locator('.admin-body')).toBeVisible();

    await page.getByRole('tab', { name: 'Votes' }).click();
    await expect(page.locator('.admin-body')).toBeVisible();

    await page.getByRole('tab', { name: 'Menu' }).click();
    await expect(page.locator('.admin-body')).toBeVisible();

    // No 401 error messages should appear
    await expect(page.locator('body')).not.toContainText('Accès administrateur requis');
  });

  test('admin can toggle vote availability', async ({ page }) => {
    await signIn(page);
    await page.getByRole('tab', { name: 'Votes' }).click();

    // Find and click a toggle checkbox to change availability
    const toggles = page.locator('.availability-grid input[type="checkbox"], .availability-table input[type="checkbox"]');
    const count = await toggles.count();
    if (count > 0) {
      await toggles.first().click();
      await expect(page.locator('.info')).toContainText('Disponibilité mise à jour');
    }
  });
});

// ---------------------------------------------------------------------------
// Regression: admin catalog category filter must work
// (previously AdminCatalogSection had no filtering logic)
// ---------------------------------------------------------------------------
test.describe('Admin catalog category filter', () => {
  test.beforeEach(async ({ page }) => {
    await signIn(page);
    await page.getByRole('tab', { name: 'Catalogue' }).click();
  });

  test('filter dropdown is visible and defaults to all dishes', async ({ page }) => {
    const filterSelect = page.getByLabel('Filtrer par catégorie');
    await expect(filterSelect).toBeVisible();

    // "Tous" option should be selected by default
    const selectedText = await filterSelect.locator('option:checked').textContent();
    expect(selectedText).toContain('Tous');
  });

  test('selecting a category filters the dish list', async ({ page }) => {
    const filterSelect = page.getByLabel('Filtrer par catégorie');

    // Count total dishes
    const allDishes = page.locator('.dish-list li');
    const totalCount = await allDishes.count();

    if (totalCount > 0) {
      // Select "Déjeuner" (lunch) category
      await filterSelect.selectOption('lunch');

      // After filtering, count should be <= total
      const filteredCount = await allDishes.count();
      expect(filteredCount).toBeLessThanOrEqual(totalCount);

      // Each visible dish should show the "Déjeuner" category label
      const visibleLabels = await page.locator('.dish-list .category-label').allTextContents();
      for (const label of visibleLabels) {
        expect(label).toBe('Déjeuner');
      }

      // Reset to "Tous"
      await filterSelect.selectOption('all');
      const resetCount = await allDishes.count();
      expect(resetCount).toBe(totalCount);
    }
  });
});
