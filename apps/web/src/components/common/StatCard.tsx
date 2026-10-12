import type { ReactNode } from 'react'

import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/utils/cn'

export type StatTrend = 'up' | 'down' | 'neutral'

export interface StatCardProps {
  label: ReactNode
  /** The figure. Pass `null` when there is no data yet — renders an em dash, never a made-up number. */
  value: ReactNode | null
  /** Phosphor icon slug shown in a muted tile (e.g. "users"). */
  icon?: string
  /** Muted line under the value (context, unit, last updated…). */
  helper?: ReactNode
  /** Change vs. a previous period, e.g. `{ value: '+12%', trend: 'up' }`. */
  delta?: { value: ReactNode; trend: StatTrend }
  loading?: boolean
  className?: string
}

const TREND_CLASS: Record<StatTrend, string> = {
  up: 'bg-success/10 text-success',
  down: 'bg-destructive/10 text-destructive',
  neutral: 'bg-muted text-muted-foreground',
}

const TREND_ICON: Record<StatTrend, string> = {
  up: 'ph-arrow-up-right',
  down: 'ph-arrow-down-right',
  neutral: 'ph-minus',
}

/** KPI tile: label + icon, big tabular value, optional delta and helper. Use in a `grid gap-4 sm:grid-cols-2 xl:grid-cols-4`. */
export function StatCard({ label, value, icon, helper, delta, loading = false, className }: StatCardProps) {
  return (
    <div data-slot="stat-card" className={cn('flex flex-col gap-3 rounded-xl border bg-card p-5 text-card-foreground shadow-xs', className)}>
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-medium text-muted-foreground">{label}</p>
        {icon && (
          <span className="flex size-8 items-center justify-center rounded-lg bg-muted text-muted-foreground" aria-hidden="true">
            <i className={cn('ph', `ph-${icon}`)} />
          </span>
        )}
      </div>
      {loading ? (
        <div className="flex flex-col gap-2">
          <Skeleton className="h-8 w-24" />
          <Skeleton className="h-4 w-32" />
        </div>
      ) : (
        <div className="flex flex-col gap-1">
          <div className="flex flex-wrap items-baseline gap-2">
            <span className="text-2xl font-semibold tracking-tight tabular-nums">{value ?? '—'}</span>
            {delta && (
              <span className={cn('inline-flex items-center gap-0.5 rounded-md px-1.5 py-0.5 text-xs font-medium tabular-nums', TREND_CLASS[delta.trend])}>
                <i className={cn('ph', TREND_ICON[delta.trend], 'size-3 text-xs')} aria-hidden="true" />
                {delta.value}
              </span>
            )}
          </div>
          {helper && <p className="text-xs text-muted-foreground">{helper}</p>}
        </div>
      )}
    </div>
  )
}
