import { type VariantProps } from 'class-variance-authority'
import { ToggleGroup as ToggleGroupPrimitive } from 'radix-ui'
import * as React from 'react'

import { toggleVariants } from '@/components/ui/toggle'
import { cn } from '@/utils/cn'

const ToggleGroupContext = React.createContext<VariantProps<typeof toggleVariants>>({ size: 'default', variant: 'default' })

/** Segmented control (joined buttons). For a muted-track segmented switch prefer `Tabs`. */
const ToggleGroup = React.forwardRef<
  React.ComponentRef<typeof ToggleGroupPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof ToggleGroupPrimitive.Root> & VariantProps<typeof toggleVariants>
>(({ className, variant, size, children, ...props }, ref) => (
  <ToggleGroupPrimitive.Root
    ref={ref}
    data-slot="toggle-group"
    data-variant={variant}
    data-size={size}
    className={cn('group/toggle-group flex w-fit items-center rounded-md data-[variant=outline]:shadow-xs', className)}
    {...props}
  >
    <ToggleGroupContext.Provider value={{ variant, size }}>{children}</ToggleGroupContext.Provider>
  </ToggleGroupPrimitive.Root>
))
ToggleGroup.displayName = 'ToggleGroup'

const ToggleGroupItem = React.forwardRef<
  React.ComponentRef<typeof ToggleGroupPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof ToggleGroupPrimitive.Item> & VariantProps<typeof toggleVariants>
>(({ className, children, variant, size, ...props }, ref) => {
  const context = React.useContext(ToggleGroupContext)
  const resolvedVariant = context.variant || variant
  return (
    <ToggleGroupPrimitive.Item
      ref={ref}
      data-slot="toggle-group-item"
      data-variant={resolvedVariant}
      data-size={context.size || size}
      className={cn(
        toggleVariants({ variant: resolvedVariant, size: context.size || size }),
        'min-w-0 shrink-0 rounded-none px-3 shadow-none first:rounded-l-md last:rounded-r-md focus:z-10 focus-visible:z-10 data-[variant=outline]:border-l-0 data-[variant=outline]:first:border-l',
        className,
      )}
      {...props}
    >
      {children}
    </ToggleGroupPrimitive.Item>
  )
})
ToggleGroupItem.displayName = 'ToggleGroupItem'

export { ToggleGroup, ToggleGroupItem }
