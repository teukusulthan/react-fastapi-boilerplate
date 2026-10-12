import { cva, type VariantProps } from 'class-variance-authority'
import * as React from 'react'

import { cn } from '@/utils/cn'

/** shadcn Empty: media (icon tile) + title + description + content (actions). See `EmptyState` for the composed pattern. */
const Empty = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    data-slot="empty"
    className={cn('flex min-w-0 flex-1 flex-col items-center justify-center gap-6 rounded-xl border-dashed p-6 text-center text-balance md:p-12', className)}
    {...props}
  />
))
Empty.displayName = 'Empty'

const EmptyHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div ref={ref} data-slot="empty-header" className={cn('flex max-w-sm flex-col items-center gap-2 text-center', className)} {...props} />
))
EmptyHeader.displayName = 'EmptyHeader'

const emptyMediaVariants = cva('mb-2 flex shrink-0 items-center justify-center', {
  variants: {
    variant: {
      default: 'bg-transparent',
      icon: 'size-10 rounded-lg border bg-muted text-foreground shadow-xs [&>i]:size-5 [&>i]:text-xl',
    },
  },
  defaultVariants: {
    variant: 'default',
  },
})

const EmptyMedia = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement> & VariantProps<typeof emptyMediaVariants>>(
  ({ className, variant = 'default', ...props }, ref) => (
    <div ref={ref} data-slot="empty-icon" data-variant={variant} className={cn(emptyMediaVariants({ variant, className }))} {...props} />
  ),
)
EmptyMedia.displayName = 'EmptyMedia'

const EmptyTitle = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div ref={ref} data-slot="empty-title" className={cn('text-base font-semibold tracking-tight', className)} {...props} />
))
EmptyTitle.displayName = 'EmptyTitle'

const EmptyDescription = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    data-slot="empty-description"
    className={cn('text-sm/relaxed text-muted-foreground [&>a]:underline [&>a]:underline-offset-4 [&>a:hover]:text-primary', className)}
    {...props}
  />
))
EmptyDescription.displayName = 'EmptyDescription'

const EmptyContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    data-slot="empty-content"
    className={cn('flex w-full max-w-sm min-w-0 flex-col items-center gap-4 text-sm text-balance', className)}
    {...props}
  />
))
EmptyContent.displayName = 'EmptyContent'

export { Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle }
