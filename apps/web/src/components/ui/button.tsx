import { cva, type VariantProps } from 'class-variance-authority'
import { Slot } from 'radix-ui'
import * as React from 'react'

import { useButtonGroup } from '@/components/ui/button-group'
import { cn } from '@/utils/cn'

const buttonVariants = cva(
  [
    'inline-flex shrink-0 items-center justify-center gap-2 rounded-md text-sm font-medium whitespace-nowrap transition-[color,background-color,border-color,box-shadow] outline-none select-none',
    'focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50',
    'disabled:pointer-events-none disabled:opacity-50 aria-disabled:pointer-events-none aria-disabled:opacity-50',
    'aria-invalid:border-destructive aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40',
    '[&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*=size-])]:size-4',
  ],
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground shadow-xs hover:bg-primary/90',
        destructive:
          'bg-destructive text-white shadow-xs hover:bg-destructive/90 focus-visible:ring-destructive/20 dark:bg-destructive/60 dark:focus-visible:ring-destructive/40',
        outline: 'border border-input bg-background shadow-xs hover:bg-accent hover:text-accent-foreground dark:bg-input/30 dark:hover:bg-input/50',
        secondary: 'bg-secondary text-secondary-foreground shadow-xs hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground dark:hover:bg-accent/60',
        link: 'h-auto px-0 text-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-9 px-4 py-2 has-[>i]:px-3 has-[>svg]:px-3',
        xs: 'h-7 gap-1.5 px-2.5 text-xs has-[>i]:px-2 [&>i]:size-3.5 [&>i]:text-sm',
        sm: 'h-8 gap-1.5 px-3 has-[>i]:px-2.5 has-[>svg]:px-2.5',
        lg: 'h-10 px-6 has-[>i]:px-4 has-[>svg]:px-4',
        icon: 'size-9',
        'icon-sm': 'size-8',
        'icon-xs': 'size-7 [&>i]:text-sm',
        'icon-lg': 'size-10',
        /** @deprecated legacy alias of `lg` */
        md: 'h-10 px-6 has-[>i]:px-4',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
)

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {
  asChild?: boolean
  /** Shows an inline spinner (replacing a leading icon) and disables the button. Width stays stable. */
  loading?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, loading = false, disabled, children, ...props }, ref) => {
    const group = useButtonGroup()
    const resolvedVariant = variant ?? group.variant ?? 'default'
    const resolvedSize = size ?? group.size ?? 'default'
    const Comp = asChild ? Slot.Root : 'button'

    return (
      <Comp
        ref={ref}
        data-slot="button"
        data-variant={resolvedVariant}
        data-size={resolvedSize}
        className={cn(buttonVariants({ variant: resolvedVariant, size: resolvedSize, className }))}
        disabled={asChild ? undefined : disabled || loading}
        aria-busy={loading || undefined}
        {...props}
      >
        {loading && !asChild ? (
          <>
            <i className="ph ph-spinner animate-spin" aria-hidden="true" />
            {React.Children.toArray(children).filter((child) => !(React.isValidElement(child) && child.type === 'i'))}
          </>
        ) : (
          children
        )}
      </Comp>
    )
  },
)
Button.displayName = 'Button'

export { Button, buttonVariants }
