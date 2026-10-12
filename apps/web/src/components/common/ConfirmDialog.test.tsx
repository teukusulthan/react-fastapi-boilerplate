import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { Button } from '@/components/ui/button'
import { renderWithProviders } from '@/test/render'

import { ConfirmDialog } from './ConfirmDialog'

describe('ConfirmDialog', () => {
  it('runs an async confirm, then closes', async () => {
    let resolve: () => void = () => undefined
    const onConfirm = vi.fn(() => new Promise<void>((done) => (resolve = done)))
    const user = userEvent.setup()
    renderWithProviders(
      <ConfirmDialog trigger={<Button>Delete</Button>} title="Delete project?" confirmLabel="Delete project" variant="destructive" onConfirm={onConfirm} />,
    )

    await user.click(screen.getByRole('button', { name: 'Delete' }))
    expect(screen.getByRole('alertdialog', { name: 'Delete project?' })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Delete project' }))
    expect(onConfirm).toHaveBeenCalledTimes(1)
    expect(screen.getByRole('button', { name: 'Delete project' })).toBeDisabled()

    resolve()
    await waitFor(() => expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument())
  })

  it('stays open when the confirm action fails', async () => {
    const user = userEvent.setup()
    renderWithProviders(
      <ConfirmDialog trigger={<Button>Block</Button>} title="Block user?" confirmLabel="Block" onConfirm={() => Promise.reject(new Error('nope'))} />,
    )

    await user.click(screen.getByRole('button', { name: 'Block' }))
    await user.click(screen.getByRole('button', { name: 'Block', hidden: false }))
    await waitFor(() => expect(screen.getByRole('alertdialog')).toBeInTheDocument())
  })
})
