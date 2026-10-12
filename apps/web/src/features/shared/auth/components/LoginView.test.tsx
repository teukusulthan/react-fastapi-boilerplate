import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/services/api-error'
import { authService, type ILoginSuccess } from '@/services/auth.service'
import { useAuthStore } from '@/stores/useAuthStore'
import { renderWithProviders } from '@/test/render'
import type { UserProfile } from '@/types/models'

import { LoginView } from './LoginView'

const USER = { id: 'u1', username: 'jane', fullname: 'Jane Doe', role: 'user' } as UserProfile
const SUCCESS: ILoginSuccess = { user: USER, auth: { accessToken: 'a', refreshToken: 'r', expiresAt: '2030-01-01T00:00:00Z' } }

beforeEach(() => {
  useAuthStore.setState({ status: 'anonymous', user: null, endReason: null })
})

describe('LoginView', () => {
  it('validates required fields before calling the API', async () => {
    const login = vi.spyOn(authService, 'login')
    const user = userEvent.setup()
    renderWithProviders(<LoginView />)

    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByText('Username or email is required')).toBeInTheDocument()
    expect(screen.getByText('Password is required')).toBeInTheDocument()
    expect(screen.getByLabelText(/username or email/i)).toHaveAttribute('aria-invalid', 'true')
    expect(login).not.toHaveBeenCalled()
  })

  it('submits identifier + password and marks the session authenticated', async () => {
    const login = vi.spyOn(authService, 'login').mockResolvedValue(SUCCESS)
    const user = userEvent.setup()
    renderWithProviders(<LoginView />)

    await user.type(screen.getByLabelText(/username or email/i), '  jane  ')
    await user.type(screen.getByLabelText(/password/i), 'secret-pass')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => expect(useAuthStore.getState().status).toBe('authenticated'))
    expect(login).toHaveBeenCalledWith({ identifier: 'jane', password: 'secret-pass' })
    expect(useAuthStore.getState().user).toEqual(USER)
  })

  it('shows the backend error message', async () => {
    vi.spyOn(authService, 'login').mockRejectedValue(new ApiError({ status: 401, code: 'AUTHENTICATION_ERROR', message: 'Invalid username or password' }))
    const user = userEvent.setup()
    renderWithProviders(<LoginView />)

    await user.type(screen.getByLabelText(/username or email/i), 'jane')
    await user.type(screen.getByLabelText(/password/i), 'wrong')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid username or password')
    expect(useAuthStore.getState().status).toBe('anonymous')
  })

  it('explains ACCOUNT_NOT_VERIFIED instead of a generic error', async () => {
    vi.spyOn(authService, 'login').mockRejectedValue(
      new ApiError({ status: 401, code: 'ACCOUNT_NOT_VERIFIED', message: 'Email address has not been verified yet' }),
    )
    const user = userEvent.setup()
    renderWithProviders(<LoginView />)

    await user.type(screen.getByLabelText(/username or email/i), 'jane')
    await user.type(screen.getByLabelText(/password/i), 'secret-pass')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent(/has not been verified yet/i)
    expect(screen.getByRole('alert')).toHaveTextContent(/administrator/i)
    expect(useAuthStore.getState().status).toBe('anonymous')
  })

  it('asks for the 2FA code when required and completes the login', async () => {
    vi.spyOn(authService, 'login').mockResolvedValue({ twoFactorRequired: true, sessionToken: 'sess-1', method: 'email' })
    const verify = vi.spyOn(authService, 'verifyTwoFactor').mockResolvedValue(SUCCESS)
    const user = userEvent.setup()
    renderWithProviders(<LoginView />)

    await user.type(screen.getByLabelText(/username or email/i), 'jane')
    await user.type(screen.getByLabelText(/password/i), 'secret-pass')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    const otpInput = await screen.findByLabelText(/verification code/i)
    expect(screen.getByRole('button', { name: /resend code/i })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /^verify$/i }))
    expect(await screen.findByText('Enter the 6-digit code')).toBeInTheDocument()
    expect(verify).not.toHaveBeenCalled()

    await user.type(otpInput, '123456')
    await user.click(screen.getByRole('button', { name: /^verify$/i }))

    await waitFor(() => expect(useAuthStore.getState().status).toBe('authenticated'))
    expect(verify).toHaveBeenCalledWith({ sessionToken: 'sess-1', otp: '123456' })
  })
})
