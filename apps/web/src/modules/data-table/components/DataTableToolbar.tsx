import type { ReactNode } from 'react'

import { InputGroup, InputGroupAddon, InputGroupButton, InputGroupInput } from '@/components/ui/input-group'
import { cn } from '@/utils/cn'

export interface DataTableToolbarProps {
  /** Controlled search text. Omit `onSearchChange` to hide the search box. */
  searchValue?: string
  onSearchChange?: (value: string) => void
  searchPlaceholder?: string
  /** Filter controls (Selects, faceted filters…) placed after the search box. */
  filters?: ReactNode
  /** Right-aligned controls (view options, export, refresh). */
  actions?: ReactNode
  className?: string
}

/** Top bar of a list surface: search (with clear) · filters · right-aligned actions. Wraps on mobile. */
export function DataTableToolbar({ searchValue = '', onSearchChange, searchPlaceholder = 'Search…', filters, actions, className }: DataTableToolbarProps) {
  return (
    <div className={cn('flex flex-col gap-2 p-3 sm:flex-row sm:items-center sm:justify-between', className)}>
      <div className="flex flex-1 flex-col gap-2 sm:flex-row sm:items-center">
        {onSearchChange && (
          <InputGroup className="sm:max-w-xs">
            <InputGroupAddon>
              <i className="ph ph-magnifying-glass" aria-hidden="true" />
            </InputGroupAddon>
            <InputGroupInput
              type="search"
              aria-label={searchPlaceholder}
              placeholder={searchPlaceholder}
              value={searchValue}
              onChange={(event) => onSearchChange(event.target.value)}
            />
            {searchValue && (
              <InputGroupAddon align="inline-end">
                <InputGroupButton size="icon-xs" aria-label="Clear search" onClick={() => onSearchChange('')}>
                  <i className="ph ph-x" aria-hidden="true" />
                </InputGroupButton>
              </InputGroupAddon>
            )}
          </InputGroup>
        )}
        {filters && <div className="flex flex-wrap items-center gap-2">{filters}</div>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  )
}
