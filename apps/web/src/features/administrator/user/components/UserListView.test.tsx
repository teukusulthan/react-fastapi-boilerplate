import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/services/api-error'
import { userService } from '@/services/user.service'
import { useAuthStore } from '@/stores/useAuthStore'
import { renderWithProviders } from '@/test/render'
import type { UserDetail, UserProfile } from '@/types/models'

import { UserListView } from './UserListView'

const user = (id: string, fullname: string, status: UserDetail['status'] = 'active') =>
  ({
    id,
    username: fullname.toLowerCase().replace(' ', '.'),
    fullname,
    email: `${id}@example.com`,
    status,
    role: 'user',
    twoFactorEnabled: false,
    lastLoginAt: null,
    createdAt: '2026-01-01T00:00:00Z',
  }) as UserDetail

const page = (items: UserDetail[]) => ({ items, pagination: { page: 1, size: 10, totalElements: items.length, totalPages: items.length ? 1 : 0 } })

beforeEach(() => {
  useAuthStore.setState({ status: 'authenticated', user: { id: 'me', role: 'admin' } as UserProfile, endReason: null })
})

describe('UserListView', () => {
  it('lists users with their status and the total in the header', async () => {
    vi.spyOn(userService, 'getAll').mockResolvedValue(page([user('u1', 'Ada Lovelace'), user('u2', 'Alan Turing', 'blocked')]))
    renderWithProviders(<UserListView />)

    expect(await screen.findByText('Ada Lovelace')).toBeInTheDocument()
    expect(screen.getByText('Blocked')).toBeInTheDocument()
    expect(screen.getByText(/2 accounts/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Actions for Alan Turing' })).toBeInTheDocument()
  })

  it('sends the status filter and offers to clear it when nothing matches', async () => {
    const getAll = vi.spyOn(userService, 'getAll').mockResolvedValue(page([]))
    const userEv = userEvent.setup()
    renderWithProviders(<UserListView />)

    expect(await screen.findByText('No users yet')).toBeInTheDocument()
    await userEv.click(screen.getByRole('combobox', { name: /filter by status/i }))
    await userEv.click(await screen.findByRole('option', { name: 'Blocked' }))

    await waitFor(() =>
      expect(getAll).toHaveBeenLastCalledWith(expect.objectContaining({ filters: [{ field: 'status', operator: 'is', value: { is: 'blocked' } }] })),
    )
    expect(await screen.findByText('No matching users')).toBeInTheDocument()
    await userEv.click(screen.getByRole('button', { name: /clear filters/i }))
    await waitFor(() => expect(getAll).toHaveBeenLastCalledWith(expect.not.objectContaining({ filters: expect.anything() })))
  })

  it('shows the API error with a retry', async () => {
    const getAll = vi.spyOn(userService, 'getAll').mockRejectedValue(new ApiError({ status: 500, code: 'INTERNAL_ERROR', message: 'Database unavailable' }))
    renderWithProviders(<UserListView />)

    expect(await screen.findByText('Database unavailable')).toBeInTheDocument()
    await userEvent.setup().click(screen.getByRole('button', { name: /try again/i }))
    expect(getAll).toHaveBeenCalledTimes(2)
  })
})
