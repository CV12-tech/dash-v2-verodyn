import { test, expect } from '@playwright/test';

test.describe('auth flow', () => {
  test('unauthenticated user is redirected to login', async ({ page }) => {
    await page.goto('/overview');
    await expect(page).toHaveURL(/\/login/);
  });

  test('login page renders with expected fields', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByLabel(/E-Mail|Email/)).toBeVisible();
    await expect(page.getByLabel(/Passwort|Password/)).toBeVisible();
    await expect(page.getByRole('button', { name: /Anmelden|Sign in/ })).toBeVisible();
  });

  test('rejects invalid credentials', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/E-Mail|Email/).fill('wrong@example.com');
    await page.getByLabel(/Passwort|Password/).fill('WrongPassword123!');
    await page.getByRole('button', { name: /Anmelden|Sign in/ }).click();
    // stays on login or shows error toast
    await expect(page).toHaveURL(/\/login/);
  });
});
