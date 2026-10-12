import type { SortingState } from '@tanstack/react-table'

import type { DataTablePaginationState, DataTableSort } from './types'

/** FindDTO sort → TanStack sorting state. */
export function toSortingState(sort: DataTableSort | null | undefined): SortingState {
  return sort ? [{ id: sort.orderBy, desc: sort.order === 'desc' }] : []
}

/** TanStack sorting state → FindDTO sort (`null` = backend default order). */
export function fromSortingState(sorting: SortingState): DataTableSort | null {
  const [first] = sorting
  return first ? { orderBy: first.id, order: first.desc ? 'desc' : 'asc' } : null
}

/** 1-based inclusive range of the rows on the current page, e.g. `{ from: 11, to: 20 }`; `{0,0}` when empty. */
export function getPageRange({ page, size, totalElements }: Pick<DataTablePaginationState, 'page' | 'size' | 'totalElements'>): { from: number; to: number } {
  if (totalElements <= 0) return { from: 0, to: 0 }
  const from = Math.min((page - 1) * size + 1, totalElements)
  const to = Math.min(page * size, totalElements)
  return { from, to }
}
