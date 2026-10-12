import type { ReactNode } from 'react'

import { EmptyState } from '@/components/common/EmptyState'
import { cn } from '@/utils/cn'

export interface StatusScreenProps {
  /** Phosphor icon slug */
  icon: string
  title: string
  description?: ReactNode
  /** Short code shown above the title, e.g. "404" */
  code?: string
  actions?: ReactNode
  /** Fill the viewport (outside the app shell) instead of the current region. */
  fullScreen?: boolean
  className?: string
}

/** Route-level status screen: 403, 404, crash fallback, server unavailable. Built on `EmptyState`. */
export function StatusScreen({ icon, title, description, code, actions, fullScreen = false, className }: StatusScreenProps) {
  return (
    <EmptyState
      icon={icon}
      titleAs={fullScreen ? 'h1' : 'h2'}
      size={fullScreen ? 'full' : 'default'}
      eyebrow={code}
      title={title}
      description={description}
      action={actions}
      className={cn(!fullScreen && 'min-h-[60vh]', className)}
    />
  )
}
