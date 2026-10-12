import type { ReactNode } from 'react'

import { cn } from '@/utils/cn'

export type StatusTone = 'success' | 'warning' | 'destructive' | 'info' | 'neutral'

export interface StatusBadgeProps {
  tone: StatusTone
  children: ReactNode
  className?: string
}

const TONE_CLASS: Record<StatusTone, string> = {
  success: 'bg-success/10 text-success dark:bg-success/15',
  warning: 'bg-warning/10 text-warning dark:bg-warning/15',
  destructive: 'bg-destructive/10 text-destructive dark:bg-destructive/15',
  info: 'bg-info/10 text-info dark:bg-info/15',
  neutral: 'bg-muted text-muted-foreground',
}

const DOT_CLASS: Record<StatusTone, string> = {
  success: 'bg-success',
  warning: 'bg-warning',
  destructive: 'bg-destructive',
  info: 'bg-info',
  neutral: 'bg-muted-foreground/60',
}

/** Status = colored dot + label on a subtle tint of the same tone. Use for every entity status. */
export function StatusBadge({ tone, children, className }: StatusBadgeProps) {
  return (
    <span
      data-slot="status-badge"
      data-tone={tone}
      className={cn('inline-flex w-fit items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-medium whitespace-nowrap', TONE_CLASS[tone], className)}
    >
      <span className={cn('size-1.5 shrink-0 rounded-full', DOT_CLASS[tone])} aria-hidden="true" />
      {children}
    </span>
  )
}
