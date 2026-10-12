import { Link } from 'react-router-dom'

import env from '@/config/env'
import { cn } from '@/utils/cn'

/** App mark + name. `collapsible`: the name hides when the sidebar is collapsed to icons. */
export default function AppBrand({ collapsible = false, className }: { collapsible?: boolean; className?: string }) {
  return (
    <Link
      to="/"
      className={cn('flex min-w-0 items-center gap-2.5 rounded-md text-foreground outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50', className)}
    >
      <span className="flex size-7 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-xs" aria-hidden="true">
        <i className="ph-fill ph-cube size-4" />
      </span>
      <span className={cn('truncate text-sm font-semibold tracking-tight', collapsible && 'group-data-[state=collapsed]/sidebar-wrapper:md:hidden')}>
        {env.app.name}
      </span>
    </Link>
  )
}
