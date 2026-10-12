import type { ReactNode } from 'react'

import { Card, CardAction, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/utils/cn'

export interface SectionCardProps {
  title: ReactNode
  description?: ReactNode
  /** Top-right of the header: a link button, a menu or a badge. */
  actions?: ReactNode
  footer?: ReactNode
  /**
   * `stacked` (default): header above content.
   * `split`: settings layout — title/description on the left third, content on the right (lg+).
   */
  layout?: 'stacked' | 'split'
  /** Remove content padding (flush lists/tables inside the card). */
  flush?: boolean
  /** Destructive "danger zone" styling. */
  tone?: 'default' | 'destructive'
  className?: string
  contentClassName?: string
  children?: ReactNode
}

/** A titled surface for one group of content (details, settings section, list preview). Never nest cards. */
export function SectionCard({
  title,
  description,
  actions,
  footer,
  layout = 'stacked',
  flush = false,
  tone = 'default',
  className,
  contentClassName,
  children,
}: SectionCardProps) {
  const toneClass = tone === 'destructive' && 'border-destructive/30'

  if (layout === 'split') {
    return (
      <section className={cn('grid gap-4 lg:grid-cols-3 lg:gap-8', className)}>
        <div className="flex flex-col gap-1 lg:pt-1">
          <h2 className="text-base font-semibold">{title}</h2>
          {description && <p className="text-sm text-muted-foreground">{description}</p>}
        </div>
        <Card className={cn('lg:col-span-2', toneClass)}>
          <CardContent className={cn('flex flex-col gap-6', contentClassName)}>{children}</CardContent>
          {footer && <CardFooter className="justify-end gap-2 border-t pt-6">{footer}</CardFooter>}
        </Card>
      </section>
    )
  }

  return (
    <Card className={cn(flush && 'gap-0 pb-0', toneClass, className)}>
      <CardHeader className={cn(flush && 'border-b pb-4')}>
        <CardTitle>
          <h2>{title}</h2>
        </CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
        {actions && <CardAction>{actions}</CardAction>}
      </CardHeader>
      <CardContent className={cn(flush && 'px-0', contentClassName)}>{children}</CardContent>
      {footer && <CardFooter className={cn('gap-2 border-t pt-6', flush && 'pb-6')}>{footer}</CardFooter>}
    </Card>
  )
}
