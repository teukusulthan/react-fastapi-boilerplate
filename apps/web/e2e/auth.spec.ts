import { expect, test } from '@playwright/test'

import { LoginPage } from './pages/login.page'

test.describe('auth guards', () => {
  test('an anonymous visit to / redirects to the login page', async ({ page }) => {
    await page.goto('/')

    await expect(page).toHaveURL(/\/auth\/login$/)
    await expect(new LoginPage(page).heading).toBeVisible()
  })

  test('wrong credentials show the error message and stay on the login page', async ({ page }) => {
    const login = new LoginPage(page)
    await login.goto()

    // A unique, non-existent account: never trips the per-identifier lockout of the real admin.
    await login.signIn(`e2e-nobody-${Date.now()}@example.invalid`, 'not-the-password')

    await expect(login.errorAlert).toHaveText('Invalid credentials')
    await expect(page).toHaveURL(/\/auth\/login$/)
    await expect(login.submit).toBeEnabled()
  })
})
