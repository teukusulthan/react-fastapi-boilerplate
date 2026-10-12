import { cn } from '@/utils/cn'

export interface LoadingStateProps {
  label?: string
  className?: string
}

/**
 * Region-level loading (Suspense fallbacks, lazy panels). For data surfaces prefer skeletons shaped
 * like the content (DataTable `loading`, StatCard `loading`).
 */
export function LoadingState({ label = 'Loading…', className }: LoadingStateProps) {
  return (
    <div role="status" aria-live="polite" className={cn('flex min-h-40 w-full flex-col items-center justify-center gap-3 text-muted-foreground', className)}>
      <i className="ph ph-spinner size-5 animate-spin" aria-hidden="true" />
      <span className="text-sm">{label}</span>
    </div>
  )
}
