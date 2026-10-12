import type { SortOrder } from '@/types/api'

/** Server pagination as returned by services (`ApiList.pagination`). `page` is 1-based. */
export interface DataTablePaginationState {
  page: number
  size: number
  totalElements: number
  totalPages: number
}

/** Server sorting in FindDTO terms (`orderBy` = camelCase API field, must be in the backend sortable whitelist). */
export interface DataTableSort {
  orderBy: string
  order: SortOrder
}

export interface DataTableRowAction {
  label: string
  /** Phosphor icon slug. */
  icon?: string
  onSelect: () => void
  variant?: 'default' | 'destructive'
  disabled?: boolean
  /** Draw a separator above this item (group destructive actions at the bottom). */
  separatorBefore?: boolean
}
