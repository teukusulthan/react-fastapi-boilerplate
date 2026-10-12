import { flexRender, getCoreRowModel, useReactTable, type ColumnDef, type SortingState, type Updater } from '@tanstack/react-table'
import { type ReactNode } from 'react'

import { EmptyState } from '@/components/common/EmptyState'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { cn } from '@/utils/cn'

import type { DataTablePaginationState, DataTableSort } from '../types'
import { fromSortingState, toSortingState } from '../utils'

import { DataTablePagination } from './DataTablePagination'

export interface DataTableColumnMeta {
  /** Classes for both the header and body cells of this column (width, alignment). */
  className?: string
  /** Skeleton placeholder width while loading (default `w-24`). */
  skeletonClassName?: string
  /** Custom loading placeholder for this column's cells (e.g. avatar + two lines). */
  skeleton?: ReactNode
}

export interface DataTableProps<TData> {
  columns: ColumnDef<TData, unknown>[]
  data: TData[] | undefined
  /** First load: renders skeleton rows shaped like the table. */
  loading?: boolean
  /** Background refetch (page change, search): dims the rows and marks the table busy. */
  fetching?: boolean
  /** Rendered instead of the table when there are no rows (default: a generic "No results" EmptyState). */
  emptyState?: ReactNode
  /** Rendered above the table inside the same surface (usually `DataTableToolbar`). */
  toolbar?: ReactNode
  /** Rendered in place of the rows (e.g. an inline `Alert` with retry). */
  error?: ReactNode

  /** Server pagination (`ApiList.pagination`). Omit to hide the footer. */
  pagination?: DataTablePaginationState
  onPageChange?: (page: number) => void
  onPageSizeChange?: (size: number) => void
  pageSizeOptions?: readonly number[]

  /** Server sorting. Columns opt in with `enableSorting: true` and use `DataTableColumnHeader`. */
  sort?: DataTableSort | null
  onSortChange?: (sort: DataTableSort | null) => void

  getRowId?: (row: TData, index: number) => string
  /** Number of skeleton rows (default: page size, max 10). */
  skeletonRows?: number
  /** Accessible table caption (visually hidden). */
  caption?: string
  className?: string
}

/**
 * The list surface: one rounded card containing toolbar → table → pagination, wired for server-side
 * pagination and sorting (FindDTO). Covers loading (skeleton rows), empty, error and refetching states.
 */
export function DataTable<TData>({
  columns,
  data,
  loading = false,
  fetching = false,
  emptyState,
  toolbar,
  error,
  pagination,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions,
  sort = null,
  onSortChange,
  getRowId,
  skeletonRows,
  caption,
  className,
}: DataTableProps<TData>) {
  const sorting = toSortingState(sort)

  const table = useReactTable({
    data: data ?? [],
    columns,
    getCoreRowModel: getCoreRowModel(),
    getRowId,
    manualPagination: true,
    manualSorting: true,
    enableSorting: Boolean(onSortChange),
    enableSortingRemoval: true,
    sortDescFirst: false,
    pageCount: pagination?.totalPages ?? -1,
    state: { sorting },
    onSortingChange: (updater: Updater<SortingState>) => {
      const next = typeof updater === 'function' ? updater(sorting) : updater
      onSortChange?.(fromSortingState(next))
    },
  })

  const rows = table.getRowModel().rows
  const columnCount = table.getVisibleLeafColumns().length
  const skeletonCount = skeletonRows ?? Math.min(pagination?.size ?? 10, 10)
  const isEmpty = !loading && !error && rows.length === 0
  const metaClass = (meta: unknown) => (meta as DataTableColumnMeta | undefined)?.className

  return (
    <div data-slot="data-table" className={cn('overflow-hidden rounded-xl border bg-card text-card-foreground shadow-xs', className)}>
      {toolbar && <div className="border-b">{toolbar}</div>}

      {isEmpty ? (
        (emptyState ?? <EmptyState icon="magnifying-glass" title="No results" description="Nothing matches the current filters." />)
      ) : (
        <Table aria-busy={loading || fetching} className={cn(fetching && !loading && 'opacity-60 transition-opacity')}>
          {caption && <caption className="sr-only">{caption}</caption>}
          <TableHeader className="bg-muted/50">
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead
                    key={header.id}
                    className={metaClass(header.column.columnDef.meta)}
                    aria-sort={header.column.getIsSorted() === 'asc' ? 'ascending' : header.column.getIsSorted() === 'desc' ? 'descending' : undefined}
                  >
                    {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {error ? (
              <TableRow className="hover:bg-transparent">
                <TableCell colSpan={columnCount} className="p-4 whitespace-normal">
                  {error}
                </TableCell>
              </TableRow>
            ) : loading ? (
              Array.from({ length: skeletonCount }, (_, rowIndex) => (
                <TableRow key={`skeleton-${rowIndex}`} className="hover:bg-transparent" data-testid="data-table-skeleton-row">
                  {table.getVisibleLeafColumns().map((column) => {
                    const meta = column.columnDef.meta as DataTableColumnMeta | undefined
                    return (
                      <TableCell key={column.id} className={meta?.className}>
                        {meta?.skeleton ?? <Skeleton className={cn('h-4 w-24', meta?.skeletonClassName)} />}
                      </TableCell>
                    )
                  })}
                </TableRow>
              ))
            ) : (
              rows.map((row) => (
                <TableRow key={row.id} data-state={row.getIsSelected() ? 'selected' : undefined}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id} className={metaClass(cell.column.columnDef.meta)}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      )}

      {pagination && onPageChange && !isEmpty && !error && !loading && (
        <div className="border-t">
          <DataTablePagination
            pagination={pagination}
            onPageChange={onPageChange}
            onPageSizeChange={onPageSizeChange}
            pageSizeOptions={pageSizeOptions}
            disabled={loading || fetching}
          />
        </div>
      )}
    </div>
  )
}
