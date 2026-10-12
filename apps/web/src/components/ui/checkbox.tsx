import { Checkbox as CheckboxPrimitive } from 'radix-ui'
import * as React from 'react'

import { cn } from '@/utils/cn'

const Checkbox = React.forwardRef<React.ComponentRef<typeof CheckboxPrimitive.Root>, React.ComponentPropsWithoutRef<typeof CheckboxPrimitive.Root>>(
  ({ className, ...props }, ref) => (
    <CheckboxPrimitive.Root
      ref={ref}
      data-slot="checkbox"
      className={cn(
        'peer size-4 shrink-0 rounded-xs border border-input bg-background shadow-xs transition-[color,background-color,box-shadow] outline-none dark:bg-input/30',
        'focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50',
        'aria-invalid:border-destructive aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40',
        'data-[state=checked]:border-primary data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground data-[state=indeterminate]:border-primary data-[state=indeterminate]:bg-primary data-[state=indeterminate]:text-primary-foreground',
        className,
      )}
      {...props}
    >
      <CheckboxPrimitive.Indicator data-slot="checkbox-indicator" className="grid place-content-center text-current transition-none">
        {props.checked === 'indeterminate' ? (
          <i className="ph-bold ph-minus size-3" aria-hidden="true" />
        ) : (
          <i className="ph-bold ph-check size-3" aria-hidden="true" />
        )}
      </CheckboxPrimitive.Indicator>
    </CheckboxPrimitive.Root>
  ),
)
Checkbox.displayName = 'Checkbox'

export { Checkbox }
