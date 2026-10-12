/**
 * Generic, domain-agnostic data table (TanStack Table + shadcn Table) for every list screen.
 * Server-driven: pagination/sorting map 1:1 to the backend FindDTO (`page`, `size`, `orderBy`, `order`).
 */
export { DataTable, type DataTableColumnMeta, type DataTableProps } from './components/DataTable'
export { DataTableColumnHeader, type DataTableColumnHeaderProps } from './components/DataTableColumnHeader'
export { DataTablePagination, type DataTablePaginationProps } from './components/DataTablePagination'
export { DataTableRowActions, type DataTableRowActionsProps } from './components/DataTableRowActions'
export { DataTableToolbar, type DataTableToolbarProps } from './components/DataTableToolbar'
export type { DataTablePaginationState, DataTableRowAction, DataTableSort } from './types'
export { fromSortingState, getPageRange, toSortingState } from './utils'
