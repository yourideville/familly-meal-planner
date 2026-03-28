import { test, expect } from '@playwright/test';

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
    const availabilityResponse = await page.request.get('http://127.0.0.1:8000/admin/vote-availability');
    expect(availabilityResponse.ok()).toBeTruthy();

    const slots = await availabilityResponse.json();
    const updatedSlots = slots.map((slot: { day: string; meal: string; available: boolean }) => {
      if (slot.day === 'monday' && slot.meal === 'lunch') {
        return { ...slot, available: false };
      }
      return slot;
    });

    const setResponse = await page.request.put('http://127.0.0.1:8000/admin/vote-availability', {
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
