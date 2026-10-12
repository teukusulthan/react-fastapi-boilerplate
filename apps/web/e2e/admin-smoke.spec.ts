import { expect, test } from '@playwright/test'

import { LoginPage } from './pages/login.page'
import { ADMIN } from './support/env'

test('admin signs in, sees the dashboard and the users list, then signs out', async ({ page }) => {
  const login = new LoginPage(page)

  await test.step('sign in as the seeded admin', async () => {
    await login.goto()
    await login.signIn(ADMIN.email, ADMIN.password)
    await expect(page, 'admin sign-in failed: E2E_ADMIN_EMAIL / E2E_ADMIN_PASSWORD must match the seeded admin').toHaveURL(/\/$/)
  })

  const nav = page.getByRole('navigation', { name: 'Main navigation' })

  await test.step('dashboard renders with the sidebar and page title', async () => {
    await expect(page.getByRole('heading', { level: 1, name: /^Welcome back, / })).toBeVisible()
    await expect(page).toHaveTitle(/Dashboard/)
    await expect(nav.getByRole('link', { name: 'Dashboard', exact: true })).toHaveAttribute('aria-current', 'page')
    await expect(nav.getByRole('link', { name: 'Users', exact: true })).toBeVisible()
  })

  await test.step('users table shows the admin row', async () => {
    await nav.getByRole('link', { name: 'Users', exact: true }).click()
    await expect(page).toHaveURL(/\/administrator\/user$/)
    await expect(page.getByRole('heading', { level: 1, name: 'Users' })).toBeVisible()

    const adminRow = page.getByRole('table', { name: 'Users' }).getByRole('row').filter({ hasText: ADMIN.email })
    await expect(adminRow).toHaveCount(1)
    await expect(adminRow).toContainText('You')
  })

  await test.step('sign out returns to the login page', async () => {
    await page.getByRole('button', { name: /^Account menu for / }).click()
    await page.getByRole('menuitem', { name: 'Sign out' }).click()
    await expect(page).toHaveURL(/\/auth\/login$/)
    await expect(login.heading).toBeVisible()
  })

  await test.step('the session is really gone', async () => {
    await page.goto('/administrator/user')
    await expect(page).toHaveURL(/\/auth\/login\?redirect=%2Fadministrator%2Fuser$/)
  })
})
