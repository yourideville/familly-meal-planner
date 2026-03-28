import { test, expect } from '@playwright/test';

test.describe('Admin Authentication', () => {
  async function signIn(page) {
    await page.goto('/admin');
    await page.locator('input[name="username"]').fill('admin');
    await page.locator('input[name="password"]').fill('password');
    await page.locator('button[type="submit"]').click();
    await expect(page.locator('h2')).toContainText('Administration');
  }

  test('should redirect anonymous users to login', async ({ page }) => {
    await page.goto('/admin');
    await expect(page.locator('h2')).toContainText('Connexion administrateur');
  });

  test('should login and show admin page', async ({ page }) => {
    await signIn(page);
    await expect(page.locator('button')).toContainText('Se déconnecter');
  });

  test('should logout and protect admin route', async ({ page }) => {
    await signIn(page);
    await page.locator('button', { hasText: 'Se déconnecter' }).click();
    await expect(page).toHaveURL('/');
    await page.goto('/admin');
    await expect(page.locator('h2')).toContainText('Connexion administrateur');
  });
});

test.describe('Admin Page', () => {
  async function signIn(page) {
    await page.goto('/admin');
    await page.locator('input[name="username"]').fill('admin');
    await page.locator('input[name="password"]').fill('password');
    await page.locator('button[type="submit"]').click();
    await expect(page.locator('h2')).toContainText('Administration');
  }

  test.beforeEach(async ({ page }) => {
    await signIn(page);
  });

  test('should display admin page title', async ({ page }) => {
    await expect(page.locator('h2')).toContainText('Administration');
  });

  test('should add a new dish', async ({ page }) => {
    const dishName = 'Test Dish ' + Date.now();

    await page.locator('input[placeholder*="Nom du plat"]').fill(dishName);
    await page.locator('input[placeholder*="Tags"]').fill('test, integration');
    await page.locator('button[type="submit"]').click();

    await expect(page.locator('.dish-list')).toContainText(dishName);
  });

  test('should delete a dish', async ({ page }) => {
    const dishName = 'Dish to Delete ' + Date.now();
    await page.locator('input[placeholder*="Nom du plat"]').fill(dishName);
    await page.locator('input[placeholder*="Tags"]').fill('delete');
    await page.locator('button[type="submit"]').click();

    await expect(page.locator('.dish-list')).toContainText(dishName);
    await page.locator('.dish-list li').filter({ hasText: dishName }).locator('button').click();
    await expect(page.locator('.dish-list')).not.toContainText(dishName);
  });

  test('should set shortlist for a day', async ({ page }) => {
    await page.locator('select').selectOption('monday');
    const checkboxes = page.locator('.shortlist-grid input[type="checkbox"]');
    const count = await checkboxes.count();
    if (count > 0) {
      await checkboxes.first().check();
      await page.locator('button').filter({ hasText: 'Enregistrer shortlist' }).click();
      await expect(page.locator('.info')).toContainText('Shortlist mise à jour');
    }
  });

  test('should validate weekly menu', async ({ page }) => {
    await page.locator('button').filter({ hasText: 'Valider menu hebdomadaire' }).click();
    await expect(page.locator('.info')).toContainText('Menu final validé');
  });
});
