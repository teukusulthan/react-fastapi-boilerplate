import * as React from 'react'

import { cn } from '@/utils/cn'

/**
 * Surface: rounded-xl, 1px border, shadow-xs. Slots mirror shadcn new-york:
 * Card > CardHeader (CardTitle, CardDescription, CardAction) > CardContent > CardFooter.
 * Vertical rhythm comes from the card's `gap-6 py-6`; slots only add horizontal padding.
 * For a flush table/list inside a card use `<Card className="gap-0 py-0 overflow-hidden">`.
 */
const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div ref={ref} data-slot="card" className={cn('flex flex-col gap-6 rounded-xl border bg-card py-6 text-card-foreground shadow-xs', className)} {...props} />
))
Card.displayName = 'Card'

const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    data-slot="card-header"
    className={cn(
      '@container/card-header grid auto-rows-min grid-rows-[auto_auto] items-start gap-1.5 px-6 has-data-[slot=card-action]:grid-cols-[1fr_auto] [.border-b]:pb-6',
      className,
    )}
    {...props}
  />
))
CardHeader.displayName = 'CardHeader'

const CardTitle = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div ref={ref} data-slot="card-title" className={cn('text-base leading-snug font-semibold', className)} {...props} />
))
CardTitle.displayName = 'CardTitle'

const CardDescription = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div ref={ref} data-slot="card-description" className={cn('text-sm text-muted-foreground', className)} {...props} />
))
CardDescription.displayName = 'CardDescription'

/** Top-right slot of the header (button, menu, badge). */
const CardAction = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div ref={ref} data-slot="card-action" className={cn('col-start-2 row-span-2 row-start-1 self-start justify-self-end', className)} {...props} />
))
CardAction.displayName = 'CardAction'

const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div ref={ref} data-slot="card-content" className={cn('px-6', className)} {...props} />
))
CardContent.displayName = 'CardContent'

const CardFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div ref={ref} data-slot="card-footer" className={cn('flex items-center px-6 [.border-t]:pt-6', className)} {...props} />
))
CardFooter.displayName = 'CardFooter'

export { Card, CardAction, CardContent, CardDescription, CardFooter, CardHeader, CardTitle }
