import type { ReactNode } from 'react'

import { Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from '@/components/ui/empty'
import { cn } from '@/utils/cn'

export interface EmptyStateProps {
  /** Phosphor icon slug, e.g. "users", "magnifying-glass". */
  icon?: string
  title: ReactNode
  /** Small label above the title, e.g. an error code ("404"). */
  eyebrow?: ReactNode
  description?: ReactNode
  /** Primary action (and optionally a secondary one) — e.g. "Add user" or "Clear filters". */
  action?: ReactNode
  /**
   * `plain` (default): no frame — use inside a card/table.
   * `dashed`: dashed frame — use on its own in the page.
   */
  variant?: 'plain' | 'dashed'
  /** `full`: fills the viewport (route-level 404/403/crash screens). */
  size?: 'default' | 'compact' | 'full'
  /** Heading level for the title (`h1` on full-page screens). */
  titleAs?: 'h1' | 'h2' | 'h3' | 'div'
  className?: string
  children?: ReactNode
}

/** Designed empty / no-results / error placeholder: icon tile, title, one-line hint, action. Wraps shadcn `Empty`. */
export function EmptyState({
  icon,
  title,
  eyebrow,
  description,
  action,
  variant = 'plain',
  size = 'default',
  titleAs = 'h3',
  className,
  children,
}: EmptyStateProps) {
  const Title = titleAs
  return (
    <Empty
      className={cn(
        variant === 'dashed' && 'border border-dashed bg-card/50',
        size === 'compact' && 'gap-4 p-6 md:p-8',
        size === 'full' && 'min-h-svh bg-background',
        className,
      )}
    >
      <EmptyHeader>
        {icon && (
          <EmptyMedia variant="icon">
            <i className={cn('ph', `ph-${icon}`)} aria-hidden="true" />
          </EmptyMedia>
        )}
        {eyebrow && <span className="rounded-md border px-2 py-0.5 font-mono text-xs font-medium text-muted-foreground tabular-nums">{eyebrow}</span>}
        <EmptyTitle>
          <Title className={cn('font-semibold tracking-tight', size === 'full' ? 'text-xl' : 'text-base')}>{title}</Title>
        </EmptyTitle>
        {description && <EmptyDescription>{description}</EmptyDescription>}
      </EmptyHeader>
      {(action || children) && (
        <EmptyContent>
          {action && <div className="flex flex-wrap items-center justify-center gap-2">{action}</div>}
          {children}
        </EmptyContent>
      )}
    </Empty>
  )
}
