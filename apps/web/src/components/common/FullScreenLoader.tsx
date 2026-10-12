import env from '@/config/env'

/** Viewport-filling loader (session bootstrap, app-level Suspense): app mark + spinner + label. */
export function FullScreenLoader({ label = 'Loading…' }: { label?: string }) {
  return (
    <div role="status" aria-live="polite" className="flex h-svh w-full flex-col items-center justify-center gap-5 bg-background">
      <span className="flex size-10 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm" aria-hidden="true">
        <i className="ph-fill ph-cube size-5" />
      </span>
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <i className="ph ph-spinner animate-spin" aria-hidden="true" />
        <span>{label}</span>
      </div>
      <span className="sr-only">{env.app.name}</span>
    </div>
  )
}
