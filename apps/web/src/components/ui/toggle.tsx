import { cva, type VariantProps } from 'class-variance-authority'
import { Toggle as TogglePrimitive } from 'radix-ui'
import * as React from 'react'

import { cn } from '@/utils/cn'

const toggleVariants = cva(
  [
    'inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium whitespace-nowrap transition-[color,background-color,box-shadow] outline-none',
    'hover:bg-muted hover:text-foreground focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:pointer-events-none disabled:opacity-50',
    'data-[state=on]:bg-accent data-[state=on]:text-accent-foreground aria-invalid:border-destructive',
  ],
  {
    variants: {
      variant: {
        default: 'bg-transparent text-muted-foreground',
        outline: 'border border-input bg-background text-muted-foreground shadow-xs hover:bg-accent dark:bg-input/30',
      },
      size: {
        default: 'h-9 min-w-9 px-2',
        sm: 'h-8 min-w-8 px-1.5',
        lg: 'h-10 min-w-10 px-2.5',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
)

const Toggle = React.forwardRef<
  React.ComponentRef<typeof TogglePrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof TogglePrimitive.Root> & VariantProps<typeof toggleVariants>
>(({ className, variant, size, ...props }, ref) => (
  <TogglePrimitive.Root ref={ref} data-slot="toggle" className={cn(toggleVariants({ variant, size, className }))} {...props} />
))
Toggle.displayName = 'Toggle'

export { Toggle, toggleVariants }
