import { test, expect, type Page } from '@playwright/test';

const API_BASE = 'http://127.0.0.1:8000';

async function loginAdmin(page: Page) {
  const loginResp = await page.request.post(`${API_BASE}/admin/login`, {
    data: { username: 'admin', password: 'password' },
  });
  expect(loginResp.ok()).toBeTruthy();
}

test.describe('Voting Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/vote');
  });

  test('loads member options without admin login', async ({ page }) => {
    const options = page.getByLabel('Membre').locator('option');
    const count = await options.count();
    expect(count).toBeGreaterThan(1);
  });

  test('does not expose closed vote meals for the selected day', async ({ page }) => {
    await loginAdmin(page);

    const availabilityResponse = await page.request.get(`${API_BASE}/votes/availability`);
    expect(availabilityResponse.ok()).toBeTruthy();

    const slots = await availabilityResponse.json();
    const updatedSlots = slots.map((slot: { day: string; meal: string; available: boolean }) => {
      if (slot.day === 'monday' && slot.meal === 'lunch') {
        return { ...slot, available: false };
      }
      return slot;
    });

    const setResponse = await page.request.put(`${API_BASE}/admin/vote-availability`, {
      data: updatedSlots,
    });
    expect(setResponse.ok()).toBeTruthy();

    await page.reload();
    await page.getByLabel('Jour').selectOption('monday');

    const mealOptions = await page.getByLabel('Repas').locator('option').allTextContents();
    expect(mealOptions).not.toContain('Déjeuner');
    expect(mealOptions).toContain('Dîner');
  });
});
