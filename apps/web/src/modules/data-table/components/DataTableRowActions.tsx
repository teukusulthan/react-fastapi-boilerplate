import { Fragment } from 'react'

import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'

import type { DataTableRowAction } from '../types'

export interface DataTableRowActionsProps {
  actions: DataTableRowAction[]
  /** Accessible name of the trigger, e.g. `Actions for Jane Doe`. */
  label?: string
}

/** Last-column "…" menu. Put destructive actions last with `separatorBefore` and confirm them with `ConfirmDialog`. */
export function DataTableRowActions({ actions, label = 'Open row actions' }: DataTableRowActionsProps) {
  if (actions.length === 0) return null

  return (
    <DropdownMenu modal={false}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon-sm"
          className="text-muted-foreground data-[state=open]:bg-accent data-[state=open]:text-foreground"
          aria-label={label}
        >
          <i className="ph ph-dots-three size-4.5 text-lg" aria-hidden="true" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48">
        {actions.map((action) => (
          <Fragment key={action.label}>
            {action.separatorBefore && <DropdownMenuSeparator />}
            <DropdownMenuItem variant={action.variant} disabled={action.disabled} onSelect={action.onSelect}>
              {action.icon && <i className={`ph ph-${action.icon}`} aria-hidden="true" />}
              {action.label}
            </DropdownMenuItem>
          </Fragment>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
