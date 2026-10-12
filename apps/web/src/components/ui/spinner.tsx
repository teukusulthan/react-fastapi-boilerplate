import * as React from 'react'

import { cn } from '@/utils/cn'

/** Inline loading indicator (Phosphor `spinner`). Size with `size-*` (default 16px). */
const Spinner = React.forwardRef<HTMLElement, React.HTMLAttributes<HTMLElement> & { label?: string }>(({ className, label = 'Loading', ...props }, ref) => (
  <i ref={ref} role="status" aria-label={label} data-slot="spinner" className={cn('ph ph-spinner animate-spin', className)} {...props} />
))
Spinner.displayName = 'Spinner'

export { Spinner }
