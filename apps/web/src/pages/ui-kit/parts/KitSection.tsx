import type { ReactNode } from 'react'

import { cn } from '@/utils/cn'

/** One UI-kit section: anchor heading + description + demos. */
export function KitSection({ id, title, description, children }: { id: string; title: string; description: string; children: ReactNode }) {
  return (
    <section id={id} className="flex scroll-mt-6 flex-col gap-4">
      <div className="flex flex-col gap-1 border-b pb-3">
        <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      <div className="grid gap-4">{children}</div>
    </section>
  )
}

/** A labelled demo surface inside a section. */
export function KitDemo({ title, children, className }: { title: string; children: ReactNode; className?: string }) {
  return (
    <div className="flex flex-col overflow-hidden rounded-xl border bg-card shadow-xs">
      <div className="border-b bg-muted/40 px-4 py-2 text-xs font-medium text-muted-foreground">{title}</div>
      <div className={cn('flex flex-wrap items-center gap-3 p-5', className)}>{children}</div>
    </div>
  )
}
