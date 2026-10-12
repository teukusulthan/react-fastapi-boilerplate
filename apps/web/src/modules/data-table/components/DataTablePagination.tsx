import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { PAGE_SIZE_OPTIONS } from '@/config/constants'
import { cn } from '@/utils/cn'

import type { DataTablePaginationState } from '../types'
import { getPageRange } from '../utils'

export interface DataTablePaginationProps {
  pagination: DataTablePaginationState
  onPageChange: (page: number) => void
  /** Omit to hide the rows-per-page select. */
  onPageSizeChange?: (size: number) => void
  pageSizeOptions?: readonly number[]
  disabled?: boolean
  className?: string
}

/** Footer: "Showing 1–10 of 42" · rows per page · page x of y · first/prev/next/last. */
export function DataTablePagination({
  pagination,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = PAGE_SIZE_OPTIONS,
  disabled = false,
  className,
}: DataTablePaginationProps) {
  const { page, size, totalElements, totalPages } = pagination
  const lastPage = Math.max(totalPages, 1)
  const { from, to } = getPageRange(pagination)
  const canPrev = !disabled && page > 1
  const canNext = !disabled && page < lastPage

  return (
    <nav aria-label="Pagination" className={cn('flex flex-col-reverse items-center justify-between gap-3 px-4 py-3 text-sm sm:flex-row', className)}>
      <p className="text-muted-foreground tabular-nums">
        {totalElements > 0 ? (
          <>
            Showing <span className="font-medium text-foreground">{from}</span>–<span className="font-medium text-foreground">{to}</span> of{' '}
            <span className="font-medium text-foreground">{totalElements}</span>
          </>
        ) : (
          'No results'
        )}
      </p>
      <div className="flex items-center gap-4 lg:gap-6">
        {onPageSizeChange && (
          <div className="hidden items-center gap-2 sm:flex">
            <span className="text-muted-foreground">Rows per page</span>
            <Select value={String(size)} onValueChange={(value) => onPageSizeChange(Number(value))} disabled={disabled}>
              <SelectTrigger size="sm" className="w-20 tabular-nums" aria-label="Rows per page">
                <SelectValue />
              </SelectTrigger>
              <SelectContent align="end">
                {pageSizeOptions.map((option) => (
                  <SelectItem key={option} value={String(option)} className="tabular-nums">
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
        <span className="text-muted-foreground tabular-nums">
          Page <span className="font-medium text-foreground">{Math.min(page, lastPage)}</span> of{' '}
          <span className="font-medium text-foreground">{lastPage}</span>
        </span>
        <div className="flex items-center gap-1">
          <Button
            variant="outline"
            size="icon-sm"
            className="hidden sm:inline-flex"
            aria-label="First page"
            disabled={!canPrev}
            onClick={() => onPageChange(1)}
          >
            <i className="ph ph-caret-double-left" aria-hidden="true" />
          </Button>
          <Button variant="outline" size="icon-sm" aria-label="Previous page" disabled={!canPrev} onClick={() => onPageChange(page - 1)}>
            <i className="ph ph-caret-left" aria-hidden="true" />
          </Button>
          <Button variant="outline" size="icon-sm" aria-label="Next page" disabled={!canNext} onClick={() => onPageChange(page + 1)}>
            <i className="ph ph-caret-right" aria-hidden="true" />
          </Button>
          <Button
            variant="outline"
            size="icon-sm"
            className="hidden sm:inline-flex"
            aria-label="Last page"
            disabled={!canNext}
            onClick={() => onPageChange(lastPage)}
          >
            <i className="ph ph-caret-double-right" aria-hidden="true" />
          </Button>
        </div>
      </div>
    </nav>
  )
}
