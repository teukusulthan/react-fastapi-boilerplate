import { type Locator, type Page } from '@playwright/test'

/** Page object for /auth/login (features/shared/auth/components/LoginView + LoginForm). */
export class LoginPage {
  readonly heading: Locator
  readonly form: Locator
  readonly identifier: Locator
  readonly password: Locator
  readonly submit: Locator
  readonly errorAlert: Locator

  constructor(private readonly page: Page) {
    this.heading = page.getByRole('heading', { level: 1, name: 'Welcome back' })
    this.form = page.getByRole('form', { name: 'Sign in' })
    this.identifier = this.form.getByLabel('Username or email')
    this.password = this.form.getByLabel('Password')
    this.submit = this.form.getByRole('button', { name: 'Sign in' })
    this.errorAlert = this.form.getByRole('alert')
  }

  async goto(): Promise<void> {
    await this.page.goto('/auth/login')
    await this.identifier.waitFor()
  }

  async signIn(identifier: string, password: string): Promise<void> {
    await this.identifier.fill(identifier)
    await this.password.fill(password)
    await this.submit.click()
  }
}
