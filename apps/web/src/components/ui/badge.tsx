import { cva, type VariantProps } from 'class-variance-authority'
import { Slot } from 'radix-ui'
import * as React from 'react'

import { cn } from '@/utils/cn'

/**
 * Small label. Status tones are subtle tints (`bg-success/10 text-success`); use `StatusBadge`
 * (components/common) for a dot + label status. `rounded-md`, never pill-shaped.
 */
const badgeVariants = cva(
  [
    'inline-flex w-fit shrink-0 items-center justify-center gap-1 overflow-hidden rounded-md border px-2 py-0.5 text-xs font-medium whitespace-nowrap transition-[color,box-shadow]',
    'focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 [&>i]:size-3 [&>i]:text-xs [&>svg]:pointer-events-none [&>svg]:size-3',
  ],
  {
    variants: {
      variant: {
        default: 'border-transparent bg-primary text-primary-foreground [a&]:hover:bg-primary/90',
        secondary: 'border-transparent bg-secondary text-secondary-foreground [a&]:hover:bg-secondary/80',
        outline: 'border-border text-foreground [a&]:hover:bg-accent [a&]:hover:text-accent-foreground',
        destructive: 'border-transparent bg-destructive/10 text-destructive dark:bg-destructive/15',
        success: 'border-transparent bg-success/10 text-success dark:bg-success/15',
        warning: 'border-transparent bg-warning/10 text-warning dark:bg-warning/15',
        info: 'border-transparent bg-info/10 text-info dark:bg-info/15',
        neutral: 'border-transparent bg-muted text-muted-foreground',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
)

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {
  asChild?: boolean
}

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(({ className, variant, asChild = false, ...props }, ref) => {
  const Comp = asChild ? Slot.Root : 'span'
  return <Comp ref={ref} data-slot="badge" data-variant={variant ?? 'default'} className={cn(badgeVariants({ variant }), className)} {...props} />
})
Badge.displayName = 'Badge'

export { Badge, badgeVariants }
