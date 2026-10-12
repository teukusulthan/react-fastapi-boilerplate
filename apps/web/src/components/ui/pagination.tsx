import * as React from 'react'

import { buttonVariants, type ButtonProps } from '@/components/ui/button'
import { cn } from '@/utils/cn'

/** Numbered page links (shadcn). For tables use `DataTablePagination` from `@/modules/data-table`. */
const Pagination = ({ className, ...props }: React.HTMLAttributes<HTMLElement>) => (
  <nav role="navigation" aria-label="pagination" data-slot="pagination" className={cn('mx-auto flex w-full justify-center', className)} {...props} />
)
Pagination.displayName = 'Pagination'

const PaginationContent = React.forwardRef<HTMLUListElement, React.HTMLAttributes<HTMLUListElement>>(({ className, ...props }, ref) => (
  <ul ref={ref} data-slot="pagination-content" className={cn('flex flex-row items-center gap-1', className)} {...props} />
))
PaginationContent.displayName = 'PaginationContent'

const PaginationItem = React.forwardRef<HTMLLIElement, React.LiHTMLAttributes<HTMLLIElement>>((props, ref) => (
  <li ref={ref} data-slot="pagination-item" {...props} />
))
PaginationItem.displayName = 'PaginationItem'

type PaginationLinkProps = { isActive?: boolean } & Pick<ButtonProps, 'size'> & React.AnchorHTMLAttributes<HTMLAnchorElement>

const PaginationLink = React.forwardRef<HTMLAnchorElement, PaginationLinkProps>(({ className, isActive, size = 'icon', children, ...props }, ref) => (
  <a
    ref={ref}
    aria-current={isActive ? 'page' : undefined}
    data-slot="pagination-link"
    data-active={isActive}
    className={cn(buttonVariants({ variant: isActive ? 'outline' : 'ghost', size }), 'tabular-nums', className)}
    {...props}
  >
    {children}
  </a>
))
PaginationLink.displayName = 'PaginationLink'

const PaginationPrevious = React.forwardRef<HTMLAnchorElement, PaginationLinkProps>(({ className, ...props }, ref) => (
  <PaginationLink ref={ref} aria-label="Go to previous page" size="default" className={cn('gap-1 px-2.5 sm:pl-2.5', className)} {...props}>
    <i className="ph ph-caret-left" aria-hidden="true" />
    <span className="hidden sm:block">Previous</span>
  </PaginationLink>
))
PaginationPrevious.displayName = 'PaginationPrevious'

const PaginationNext = React.forwardRef<HTMLAnchorElement, PaginationLinkProps>(({ className, ...props }, ref) => (
  <PaginationLink ref={ref} aria-label="Go to next page" size="default" className={cn('gap-1 px-2.5 sm:pr-2.5', className)} {...props}>
    <span className="hidden sm:block">Next</span>
    <i className="ph ph-caret-right" aria-hidden="true" />
  </PaginationLink>
))
PaginationNext.displayName = 'PaginationNext'

const PaginationEllipsis = ({ className, ...props }: React.HTMLAttributes<HTMLSpanElement>) => (
  <span aria-hidden data-slot="pagination-ellipsis" className={cn('flex size-9 items-center justify-center text-muted-foreground', className)} {...props}>
    <i className="ph ph-dots-three" />
    <span className="sr-only">More pages</span>
  </span>
)
PaginationEllipsis.displayName = 'PaginationEllipsis'

export { Pagination, PaginationContent, PaginationEllipsis, PaginationItem, PaginationLink, PaginationNext, PaginationPrevious }
