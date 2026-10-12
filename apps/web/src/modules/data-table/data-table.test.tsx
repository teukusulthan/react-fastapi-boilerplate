import type { ColumnDef } from '@tanstack/react-table'
import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { renderWithProviders } from '@/test/render'

import { DataTable, DataTableColumnHeader, DataTableRowActions, fromSortingState, getPageRange, toSortingState } from './index'

interface Row {
  id: string
  name: string
  email: string
}

const ROWS: Row[] = [
  { id: '1', name: 'Ada Lovelace', email: 'ada@example.com' },
  { id: '2', name: 'Alan Turing', email: 'alan@example.com' },
]

const COLUMNS: ColumnDef<Row, unknown>[] = [
  { accessorKey: 'name', enableSorting: true, header: ({ column }) => <DataTableColumnHeader column={column} title="Name" /> },
  { accessorKey: 'email', header: 'Email' },
]

const PAGINATION = { page: 2, size: 10, totalElements: 24, totalPages: 3 }

describe('data-table utils', () => {
  it('maps FindDTO sort <-> TanStack sorting', () => {
    expect(toSortingState({ orderBy: 'name', order: 'desc' })).toEqual([{ id: 'name', desc: true }])
    expect(toSortingState(null)).toEqual([])
    expect(fromSortingState([{ id: 'email', desc: false }])).toEqual({ orderBy: 'email', order: 'asc' })
    expect(fromSortingState([])).toBeNull()
  })

  it('computes the visible row range', () => {
    expect(getPageRange({ page: 1, size: 10, totalElements: 24 })).toEqual({ from: 1, to: 10 })
    expect(getPageRange({ page: 3, size: 10, totalElements: 24 })).toEqual({ from: 21, to: 24 })
    expect(getPageRange({ page: 1, size: 10, totalElements: 0 })).toEqual({ from: 0, to: 0 })
  })
})

describe('DataTable', () => {
  it('renders skeleton rows while loading', () => {
    renderWithProviders(<DataTable columns={COLUMNS} data={undefined} loading skeletonRows={4} />)
    expect(screen.getAllByTestId('data-table-skeleton-row')).toHaveLength(4)
    expect(screen.getByRole('table')).toHaveAttribute('aria-busy', 'true')
  })

  it('renders the empty state when there are no rows', () => {
    renderWithProviders(
      <DataTable columns={COLUMNS} data={[]} emptyState={<p>No users yet</p>} pagination={{ ...PAGINATION, totalElements: 0 }} onPageChange={vi.fn()} />,
    )
    expect(screen.getByText('No users yet')).toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
    expect(screen.queryByRole('navigation', { name: /pagination/i })).not.toBeInTheDocument()
  })

  it('renders rows, the error slot and the toolbar', () => {
    const { unmount } = renderWithProviders(<DataTable columns={COLUMNS} data={ROWS} toolbar={<div>toolbar</div>} />)
    expect(screen.getByText('toolbar')).toBeInTheDocument()
    expect(screen.getByText('Ada Lovelace')).toBeInTheDocument()
    expect(screen.getAllByRole('row')).toHaveLength(3)
    unmount()

    renderWithProviders(<DataTable columns={COLUMNS} data={[]} error={<p role="alert">Boom</p>} />)
    expect(screen.getByRole('alert')).toHaveTextContent('Boom')
  })

  it('reports server sorting changes in FindDTO terms', async () => {
    const onSortChange = vi.fn()
    const user = userEvent.setup()
    const { rerender } = renderWithProviders(<DataTable columns={COLUMNS} data={ROWS} sort={null} onSortChange={onSortChange} />)

    await user.click(screen.getByRole('button', { name: /sort by name/i }))
    expect(onSortChange).toHaveBeenLastCalledWith({ orderBy: 'name', order: 'asc' })

    rerender(<DataTable columns={COLUMNS} data={ROWS} sort={{ orderBy: 'name', order: 'asc' }} onSortChange={onSortChange} />)
    expect(screen.getByRole('columnheader', { name: /name/i })).toHaveAttribute('aria-sort', 'ascending')
    await user.click(screen.getByRole('button', { name: /sort by name/i }))
    expect(onSortChange).toHaveBeenLastCalledWith({ orderBy: 'name', order: 'desc' })
  })

  it('shows the page range and pages through the server result', async () => {
    const onPageChange = vi.fn()
    const user = userEvent.setup()
    renderWithProviders(<DataTable columns={COLUMNS} data={ROWS} pagination={PAGINATION} onPageChange={onPageChange} />)

    const nav = screen.getByRole('navigation', { name: /pagination/i })
    expect(nav).toHaveTextContent('Showing 11–20 of 24')
    expect(nav).toHaveTextContent('Page 2 of 3')

    await user.click(within(nav).getByRole('button', { name: /next page/i }))
    expect(onPageChange).toHaveBeenLastCalledWith(3)
    await user.click(within(nav).getByRole('button', { name: /previous page/i }))
    expect(onPageChange).toHaveBeenLastCalledWith(1)
  })
})

describe('DataTableRowActions', () => {
  it('lists the actions in a menu and runs the selected one', async () => {
    const onDelete = vi.fn()
    const user = userEvent.setup()
    renderWithProviders(
      <DataTableRowActions
        label="Actions for Ada"
        actions={[
          { label: 'Copy email', icon: 'copy', onSelect: vi.fn() },
          { label: 'Delete', icon: 'trash', variant: 'destructive', separatorBefore: true, onSelect: onDelete },
        ]}
      />,
    )

    await user.click(screen.getByRole('button', { name: 'Actions for Ada' }))
    await user.click(await screen.findByRole('menuitem', { name: /delete/i }))
    expect(onDelete).toHaveBeenCalledTimes(1)
  })
})
