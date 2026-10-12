import * as React from 'react'

import { cn } from '@/utils/cn'

/** Keyboard key hint: <Kbd>⌘</Kbd><Kbd>K</Kbd> (wrap several in <KbdGroup>). */
const Kbd = React.forwardRef<HTMLElement, React.HTMLAttributes<HTMLElement>>(({ className, ...props }, ref) => (
  <kbd
    ref={ref}
    data-slot="kbd"
    className={cn(
      'pointer-events-none inline-flex h-5 w-fit min-w-5 items-center justify-center gap-1 rounded-sm border bg-muted px-1 font-sans text-xs font-medium text-muted-foreground select-none [&>i]:size-3 [&>i]:text-xs',
      '[[data-slot=tooltip-content]_&]:border-transparent [[data-slot=tooltip-content]_&]:bg-background/20 [[data-slot=tooltip-content]_&]:text-background',
      className,
    )}
    {...props}
  />
))
Kbd.displayName = 'Kbd'

const KbdGroup = React.forwardRef<HTMLElement, React.HTMLAttributes<HTMLElement>>(({ className, ...props }, ref) => (
  <kbd ref={ref} data-slot="kbd-group" className={cn('inline-flex items-center gap-1', className)} {...props} />
))
KbdGroup.displayName = 'KbdGroup'

export { Kbd, KbdGroup }
