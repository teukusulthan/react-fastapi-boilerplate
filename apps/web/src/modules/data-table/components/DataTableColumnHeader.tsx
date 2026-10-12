import type { Column } from '@tanstack/react-table'

import { cn } from '@/utils/cn'

export interface DataTableColumnHeaderProps<TData, TValue> {
  column: Column<TData, TValue>
  title: string
  className?: string
}

/**
 * Header cell content. Sortable columns (enableSorting + server whitelist) become a button that cycles
 * asc → desc → default; the active direction is shown with an arrow.
 */
export function DataTableColumnHeader<TData, TValue>({ column, title, className }: DataTableColumnHeaderProps<TData, TValue>) {
  if (!column.getCanSort()) return <span className={className}>{title}</span>

  const sorted = column.getIsSorted()
  const icon = sorted === 'asc' ? 'ph-arrow-up' : sorted === 'desc' ? 'ph-arrow-down' : 'ph-caret-up-down'
  const nextLabel = sorted === 'asc' ? 'descending' : sorted === 'desc' ? 'default order' : 'ascending'

  return (
    <button
      type="button"
      onClick={column.getToggleSortingHandler()}
      aria-label={`Sort by ${title}: ${nextLabel}`}
      className={cn(
        '-mx-1.5 inline-flex h-7 items-center gap-1 rounded-md px-1.5 text-xs font-medium whitespace-nowrap transition-colors outline-none hover:bg-accent hover:text-foreground focus-visible:ring-[3px] focus-visible:ring-ring/50',
        sorted && 'text-foreground',
        className,
      )}
    >
      {title}
      <i className={cn('ph size-3.5 text-sm', icon, !sorted && 'opacity-60')} aria-hidden="true" />
    </button>
  )
}
