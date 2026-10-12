import { screen } from '@testing-library/react'
import { StrictMode } from 'react'
import { describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/services/api-error'
import { authService } from '@/services/auth.service'
import { renderWithProviders } from '@/test/render'

import { VerifyEmailView } from './VerifyEmailView'

describe('VerifyEmailView', () => {
  it('posts the token once (even under StrictMode) and shows the result', async () => {
    const verify = vi.spyOn(authService, 'verifyEmail').mockResolvedValue({ message: 'Your email address is verified' })
    renderWithProviders(
      <StrictMode>
        <VerifyEmailView token="tok-123" />
      </StrictMode>,
    )

    expect(await screen.findByText('Your email address is verified')).toBeInTheDocument()
    expect(verify).toHaveBeenCalledTimes(1)
    expect(verify).toHaveBeenCalledWith({ token: 'tok-123' })
    expect(screen.getByRole('link', { name: /continue/i })).toHaveAttribute('href', '/auth/login')
  })

  it('shows the backend error for an invalid or expired token', async () => {
    vi.spyOn(authService, 'verifyEmail').mockRejectedValue(new ApiError({ status: 400, code: 'BAD_REQUEST', message: 'Invalid or expired link' }))
    renderWithProviders(<VerifyEmailView token="bad" />)

    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid or expired link')
  })

  it('does not call the API without a token', () => {
    const verify = vi.spyOn(authService, 'verifyEmail')
    renderWithProviders(<VerifyEmailView token={null} />)

    expect(screen.getByRole('alert')).toHaveTextContent(/incomplete/i)
    expect(verify).not.toHaveBeenCalled()
  })
})
