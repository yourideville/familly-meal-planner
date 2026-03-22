import { test, expect } from '@playwright/test';

test.describe('Admin Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin');
  });

  test('should display admin page title', async ({ page }) => {
    await expect(page.locator('h2')).toContainText('Administration');
  });

  test('should add a new dish', async ({ page }) => {
    const dishName = 'Test Dish ' + Date.now();

    // Fill the form
    await page.locator('input[placeholder*="Nom du plat"]').fill(dishName);
    await page.locator('input[placeholder*="Tags"]').fill('test, integration');

    // Submit the form
    await page.locator('button[type="submit"]').click();

    // Check if the dish appears in the catalogue
    await expect(page.locator('.dish-list')).toContainText(dishName);
  });

  test('should delete a dish', async ({ page }) => {
    // First add a dish
    const dishName = 'Dish to Delete ' + Date.now();
    await page.locator('input[placeholder*="Nom du plat"]').fill(dishName);
    await page.locator('input[placeholder*="Tags"]').fill('delete');
    await page.locator('button[type="submit"]').click();

    // Wait for it to appear
    await expect(page.locator('.dish-list')).toContainText(dishName);

    // Click delete button
    await page.locator('.dish-list li').filter({ hasText: dishName }).locator('button').click();

    // Check it's gone
    await expect(page.locator('.dish-list')).not.toContainText(dishName);
  });

  test('should set shortlist for a day', async ({ page }) => {
    // Select Monday
    await page.locator('select').selectOption('monday');

    // Check some checkboxes
    const checkboxes = page.locator('.shortlist-grid input[type="checkbox"]');
    const count = await checkboxes.count();
    if (count > 0) {
      await checkboxes.first().check();

      // Click save
      await page.locator('button').filter({ hasText: 'Enregistrer shortlist' }).click();

      // Check message
      await expect(page.locator('.info')).toContainText('Shortlist mise à jour');
    }
  });

  test('should validate weekly menu', async ({ page }) => {
    await page.locator('button').filter({ hasText: 'Valider menu hebdomadaire' }).click();
    await expect(page.locator('.info')).toContainText('Menu final validé');
  });
});