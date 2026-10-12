import { screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useLocation } from 'react-router-dom'

import { ApiError } from '@/services/api-error'
import { authService } from '@/services/auth.service'
import { useAuthStore } from '@/stores/useAuthStore'
import { renderWithProviders } from '@/test/render'
import type { UserProfile } from '@/types/models'

import AuthGuard from './AuthGuard'
import GuestGuard from './GuestGuard'
import RoleGuard from './RoleGuard'

const makeUser = (role: string | null, privileges: string[] = []): UserProfile =>
  ({
    id: 'u1',
    username: 'jane',
    fullname: 'Jane Doe',
    email: 'jane@example.com',
    role,
    permission: role ? { id: 'p1', name: role, alias: role, privileges } : null,
  }) as UserProfile

function LocationProbe() {
  const location = useLocation()
  return <div data-testid="location">{`${location.pathname}${location.search}`}</div>
}

beforeEach(() => {
  useAuthStore.setState({ status: 'unknown', user: null, endReason: null })
})

describe('AuthGuard', () => {
  it('shows a loader while the session is being resolved', () => {
    vi.spyOn(authService, 'me').mockReturnValue(new Promise(() => undefined))
    renderWithProviders(
      <AuthGuard>
        <p>secret</p>
      </AuthGuard>,
      { route: '/reports' },
    )
    expect(screen.getByRole('status')).toHaveTextContent(/checking your session/i)
    expect(screen.queryByText('secret')).not.toBeInTheDocument()
  })

  it('bootstraps the session with GET /auth/me and renders children', async () => {
    const me = vi.spyOn(authService, 'me').mockResolvedValue(makeUser('user'))
    renderWithProviders(
      <AuthGuard>
        <p>secret</p>
      </AuthGuard>,
    )
    expect(await screen.findByText('secret')).toBeInTheDocument()
    expect(me).toHaveBeenCalledTimes(1)
    expect(useAuthStore.getState().status).toBe('authenticated')
  })

  it('redirects anonymous users to the login page with a redirect param', async () => {
    vi.spyOn(authService, 'me').mockRejectedValue(new ApiError({ status: 401, code: 'AUTHENTICATION_ERROR', message: 'Not authenticated' }))
    renderWithProviders(
      <AuthGuard>
        <p>secret</p>
      </AuthGuard>,
      { route: '/reports?tab=2', routes: [{ path: '/auth/login', element: <LocationProbe /> }] },
    )
    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent('/auth/login?redirect=%2Freports%3Ftab%3D2'))
    expect(useAuthStore.getState().status).toBe('anonymous')
  })

  it('redirects to the plain login page after an explicit logout', async () => {
    useAuthStore.setState({ status: 'anonymous', user: null, endReason: 'logout' })
    renderWithProviders(
      <AuthGuard>
        <p>secret</p>
      </AuthGuard>,
      { route: '/reports', routes: [{ path: '/auth/login', element: <LocationProbe /> }] },
    )
    expect(await screen.findByTestId('location')).toHaveTextContent(/^\/auth\/login$/)
  })

  it('offers a retry instead of logging out when the API is unreachable', async () => {
    vi.spyOn(authService, 'me').mockRejectedValue(new ApiError({ status: 0, code: 'NETWORK_ERROR', message: 'offline' }))
    renderWithProviders(
      <AuthGuard>
        <p>secret</p>
      </AuthGuard>,
    )
    expect(await screen.findByText(/can't reach the server/i)).toBeInTheDocument()
    expect(useAuthStore.getState().status).toBe('unknown')
  })
})

describe('GuestGuard', () => {
  it('renders guest pages for anonymous users', () => {
    useAuthStore.setState({ status: 'anonymous' })
    renderWithProviders(
      <GuestGuard>
        <p>login form</p>
      </GuestGuard>,
      { route: '/auth/login' },
    )
    expect(screen.getByText('login form')).toBeInTheDocument()
  })

  it('sends authenticated users to the (validated) redirect target', async () => {
    useAuthStore.setState({ status: 'authenticated', user: makeUser('user') })
    renderWithProviders(
      <GuestGuard>
        <p>login form</p>
      </GuestGuard>,
      { route: '/auth/login?redirect=%2Freports', path: '/auth/login', routes: [{ path: '/reports', element: <LocationProbe /> }] },
    )
    expect(await screen.findByTestId('location')).toHaveTextContent('/reports')
  })

  it('ignores off-site redirect targets', async () => {
    useAuthStore.setState({ status: 'authenticated', user: makeUser('user') })
    renderWithProviders(
      <GuestGuard>
        <p>login form</p>
      </GuestGuard>,
      { route: '/auth/login?redirect=%2F%2Fevil.example.com', path: '/auth/login', routes: [{ path: '/', element: <LocationProbe /> }] },
    )
    expect(await screen.findByTestId('location')).toHaveTextContent(/^\/$/)
  })
})

describe('RoleGuard', () => {
  it('renders children for an allowed role', () => {
    useAuthStore.setState({ status: 'authenticated', user: makeUser('admin') })
    renderWithProviders(
      <RoleGuard allowedRoles={['admin']}>
        <p>admin area</p>
      </RoleGuard>,
    )
    expect(screen.getByText('admin area')).toBeInTheDocument()
  })

  it('lets superusers through regardless of the allowed roles', () => {
    useAuthStore.setState({ status: 'authenticated', user: makeUser('owner') })
    renderWithProviders(
      <RoleGuard allowedRoles={['editor']}>
        <p>editor area</p>
      </RoleGuard>,
    )
    expect(screen.getByText('editor area')).toBeInTheDocument()
  })

  it('shows the 403 page for other roles', () => {
    useAuthStore.setState({ status: 'authenticated', user: makeUser('user') })
    renderWithProviders(
      <RoleGuard allowedRoles={['admin']}>
        <p>admin area</p>
      </RoleGuard>,
    )
    expect(screen.queryByText('admin area')).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /access denied/i })).toBeInTheDocument()
    expect(screen.getByText('403')).toBeInTheDocument()
  })

  it('checks required privileges', () => {
    useAuthStore.setState({ status: 'authenticated', user: makeUser('editor', ['report:read']) })
    const { unmount } = renderWithProviders(
      <RoleGuard requiredPrivileges={['report:read']}>
        <p>reports</p>
      </RoleGuard>,
    )
    expect(screen.getByText('reports')).toBeInTheDocument()
    unmount()

    renderWithProviders(
      <RoleGuard requiredPrivileges={['report:write']}>
        <p>reports</p>
      </RoleGuard>,
    )
    expect(screen.queryByText('reports')).not.toBeInTheDocument()
  })
})
