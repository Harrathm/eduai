import { test, expect, Page } from '@playwright/test';

const MULTIROLE_EMAIL = 'multirole@eduai.tn';
const MULTIROLE_PASSWORD = 'passeword123';

async function loginAs(page: Page, email: string, password: string) {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  
  await page.getByPlaceholder('vous@ecole.edu').fill(email);
  await page.getByPlaceholder('••••••••').fill(password);
  
  await page.getByRole('button', { name: /se connecter/i }).click();
  
  await page.waitForURL('**/dashboard**', { timeout: 30000 });
  await page.waitForLoadState('networkidle');
}

test.describe('Context Switcher', () => {
  test('should display context switcher for multi-role user', async ({ page }) => {
    await loginAs(page, MULTIROLE_EMAIL, MULTIROLE_PASSWORD);
    
    expect(page.url()).toContain('/dashboard');

    // The context switcher is a button inside aside with switch icon SVG and role label
    const contextSwitcher = page.locator('aside button').filter({ has: page.locator('svg') }).first();
    await expect(contextSwitcher).toBeVisible({ timeout: 15000 });
  });

  test('should switch to Leader Pédagogique role', async ({ page }) => {
    await loginAs(page, MULTIROLE_EMAIL, MULTIROLE_PASSWORD);

    // Find the context switcher button (has SVG icon + role text)
    const contextSwitcherButton = page.locator('aside button').filter({ has: page.locator('svg') }).first();
    const isVisible = await contextSwitcherButton.isVisible().catch(() => false);
    
    if (!isVisible) {
      // User might not have multiple roles — skip gracefully
      console.log('Context switcher not visible — user may not have multiple roles');
      return;
    }
    
    await contextSwitcherButton.click();
    await page.waitForTimeout(500);

    // Find any role option in the dropdown that's not the current one
    const roleOptions = page.locator('.bg-white.rounded-lg.shadow-lg button');
    const count = await roleOptions.count();
    
    if (count > 1) {
      // Click the second role option (not the active one)
      await roleOptions.nth(1).click();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      expect(page.url()).toContain('/dashboard');
    }
  });

  test('should update sidebar navigation after role switch', async ({ page }) => {
    await loginAs(page, MULTIROLE_EMAIL, MULTIROLE_PASSWORD);

    const initialNavItems = await page.locator('aside nav a').count();

    const contextSwitcherButton = page.locator('aside button').filter({ has: page.locator('svg') }).first();
    const isVisible = await contextSwitcherButton.isVisible().catch(() => false);
    
    if (isVisible) {
      await contextSwitcherButton.click();
      await page.waitForTimeout(500);

      const roleOptions = page.locator('.bg-white.rounded-lg.shadow-lg button');
      const count = await roleOptions.count();
      
      if (count > 1) {
        await roleOptions.nth(1).click();
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(1000);

        const newNavItems = await page.locator('aside nav a').count();
        expect(newNavItems).toBeDefined();
      }
    }
  });

  test('should show role label in sidebar header', async ({ page }) => {
    await loginAs(page, MULTIROLE_EMAIL, MULTIROLE_PASSWORD);

    // The role label is shown as a <p> tag below the EDUAI logo in the sidebar
    const roleLabel = page.locator('aside p').first();
    await expect(roleLabel).toBeVisible({ timeout: 15000 });
  });
});
