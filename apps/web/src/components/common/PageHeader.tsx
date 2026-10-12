import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

import { cn } from '@/utils/cn'

export interface PageHeaderProps {
  title: ReactNode
  /** One line under the title (muted). */
  description?: ReactNode
  /** Right-aligned actions — at most one primary button. Wraps under the title on mobile. */
  actions?: ReactNode
  /** Inline next to the title (status badge, count). */
  meta?: ReactNode
  /** Small back link above the title, for detail pages. */
  back?: { to: string; label: string }
  className?: string
}

/** Top of every page: one clear title, a one-line description and the page's primary action. */
export function PageHeader({ title, description, actions, meta, back, className }: PageHeaderProps) {
  return (
    <header className={cn('flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between', className)}>
      <div className="flex min-w-0 flex-col gap-1">
        {back && (
          <Link
            to={back.to}
            className="mb-1 inline-flex w-fit items-center gap-1 rounded-sm text-sm text-muted-foreground transition-colors outline-none hover:text-foreground focus-visible:ring-[3px] focus-visible:ring-ring/50"
          >
            <i className="ph ph-arrow-left size-3.5" aria-hidden="true" />
            {back.label}
          </Link>
        )}
        <div className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1">
          <h1 className="truncate text-2xl font-semibold tracking-tight text-foreground">{title}</h1>
          {meta}
        </div>
        {description && <p className="text-sm text-muted-foreground">{description}</p>}
      </div>
      {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
    </header>
  )
}
