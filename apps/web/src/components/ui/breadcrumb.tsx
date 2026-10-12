import { Slot } from 'radix-ui'
import * as React from 'react'

import { cn } from '@/utils/cn'

const Breadcrumb = React.forwardRef<HTMLElement, React.HTMLAttributes<HTMLElement>>((props, ref) => (
  <nav ref={ref} aria-label="breadcrumb" data-slot="breadcrumb" {...props} />
))
Breadcrumb.displayName = 'Breadcrumb'

const BreadcrumbList = React.forwardRef<HTMLOListElement, React.OlHTMLAttributes<HTMLOListElement>>(({ className, ...props }, ref) => (
  <ol
    ref={ref}
    data-slot="breadcrumb-list"
    className={cn('flex flex-wrap items-center gap-1.5 text-sm break-words text-muted-foreground', className)}
    {...props}
  />
))
BreadcrumbList.displayName = 'BreadcrumbList'

const BreadcrumbItem = React.forwardRef<HTMLLIElement, React.LiHTMLAttributes<HTMLLIElement>>(({ className, ...props }, ref) => (
  <li ref={ref} data-slot="breadcrumb-item" className={cn('inline-flex items-center gap-1.5', className)} {...props} />
))
BreadcrumbItem.displayName = 'BreadcrumbItem'

const BreadcrumbLink = React.forwardRef<HTMLAnchorElement, React.AnchorHTMLAttributes<HTMLAnchorElement> & { asChild?: boolean }>(
  ({ asChild, className, ...props }, ref) => {
    const Comp = asChild ? Slot.Root : 'a'
    return <Comp ref={ref} data-slot="breadcrumb-link" className={cn('rounded-sm transition-colors hover:text-foreground', className)} {...props} />
  },
)
BreadcrumbLink.displayName = 'BreadcrumbLink'

const BreadcrumbPage = React.forwardRef<HTMLSpanElement, React.HTMLAttributes<HTMLSpanElement>>(({ className, ...props }, ref) => (
  <span
    ref={ref}
    data-slot="breadcrumb-page"
    role="link"
    aria-disabled="true"
    aria-current="page"
    className={cn('font-medium text-foreground', className)}
    {...props}
  />
))
BreadcrumbPage.displayName = 'BreadcrumbPage'

const BreadcrumbSeparator = ({ children, className, ...props }: React.LiHTMLAttributes<HTMLLIElement>) => (
  <li data-slot="breadcrumb-separator" role="presentation" aria-hidden="true" className={cn('text-muted-foreground/60', className)} {...props}>
    {children ?? <i className="ph ph-caret-right size-3.5" />}
  </li>
)
BreadcrumbSeparator.displayName = 'BreadcrumbSeparator'

const BreadcrumbEllipsis = ({ className, ...props }: React.HTMLAttributes<HTMLSpanElement>) => (
  <span data-slot="breadcrumb-ellipsis" role="presentation" aria-hidden="true" className={cn('flex size-9 items-center justify-center', className)} {...props}>
    <i className="ph ph-dots-three" />
    <span className="sr-only">More</span>
  </span>
)
BreadcrumbEllipsis.displayName = 'BreadcrumbEllipsis'

export { Breadcrumb, BreadcrumbEllipsis, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator }
