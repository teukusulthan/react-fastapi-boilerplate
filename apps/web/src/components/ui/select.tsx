import { Select as SelectPrimitive } from 'radix-ui'
import * as React from 'react'

import { cn } from '@/utils/cn'

const Select = SelectPrimitive.Root
const SelectGroup = SelectPrimitive.Group
const SelectValue = SelectPrimitive.Value

const SelectTrigger = React.forwardRef<
  React.ComponentRef<typeof SelectPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Trigger> & { size?: 'sm' | 'default' }
>(({ className, size = 'default', children, ...props }, ref) => (
  <SelectPrimitive.Trigger
    ref={ref}
    data-slot="select-trigger"
    data-size={size}
    className={cn(
      'flex w-fit items-center justify-start gap-2 rounded-md border border-input bg-background px-3 py-2 text-sm whitespace-nowrap shadow-xs transition-[color,box-shadow,border-color] outline-none dark:bg-input/30 dark:hover:bg-input/50',
      'focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50',
      'aria-invalid:border-destructive aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40',
      'data-[placeholder]:text-muted-foreground data-[size=default]:h-9 data-[size=sm]:h-8',
      '*:data-[slot=select-value]:line-clamp-1 *:data-[slot=select-value]:flex *:data-[slot=select-value]:items-center *:data-[slot=select-value]:gap-2',
      className,
    )}
    {...props}
  >
    {children}
    <SelectPrimitive.Icon asChild>
      <i className="ph ph-caret-up-down ml-auto size-3.5 text-sm text-muted-foreground" aria-hidden="true" />
    </SelectPrimitive.Icon>
  </SelectPrimitive.Trigger>
))
SelectTrigger.displayName = 'SelectTrigger'

const SelectScrollUpButton = React.forwardRef<
  React.ComponentRef<typeof SelectPrimitive.ScrollUpButton>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.ScrollUpButton>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.ScrollUpButton
    ref={ref}
    data-slot="select-scroll-up-button"
    className={cn('flex cursor-default items-center justify-center py-1', className)}
    {...props}
  >
    <i className="ph ph-caret-up size-3.5" aria-hidden="true" />
  </SelectPrimitive.ScrollUpButton>
))
SelectScrollUpButton.displayName = 'SelectScrollUpButton'

const SelectScrollDownButton = React.forwardRef<
  React.ComponentRef<typeof SelectPrimitive.ScrollDownButton>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.ScrollDownButton>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.ScrollDownButton
    ref={ref}
    data-slot="select-scroll-down-button"
    className={cn('flex cursor-default items-center justify-center py-1', className)}
    {...props}
  >
    <i className="ph ph-caret-down size-3.5" aria-hidden="true" />
  </SelectPrimitive.ScrollDownButton>
))
SelectScrollDownButton.displayName = 'SelectScrollDownButton'

const SelectContent = React.forwardRef<React.ComponentRef<typeof SelectPrimitive.Content>, React.ComponentPropsWithoutRef<typeof SelectPrimitive.Content>>(
  ({ className, children, position = 'popper', align = 'start', ...props }, ref) => (
    <SelectPrimitive.Portal>
      <SelectPrimitive.Content
        ref={ref}
        data-slot="select-content"
        className={cn(
          'relative z-50 max-h-(--radix-select-content-available-height) min-w-32 origin-(--radix-select-content-transform-origin) overflow-x-hidden overflow-y-auto rounded-lg border bg-popover text-popover-foreground shadow-md',
          'data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2',
          'data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95',
          position === 'popper' &&
            'data-[side=bottom]:translate-y-1 data-[side=left]:-translate-x-1 data-[side=right]:translate-x-1 data-[side=top]:-translate-y-1',
          className,
        )}
        position={position}
        align={align}
        {...props}
      >
        <SelectScrollUpButton />
        <SelectPrimitive.Viewport
          className={cn('p-1', position === 'popper' && 'h-(--radix-select-trigger-height) w-full min-w-(--radix-select-trigger-width) scroll-my-1')}
        >
          {children}
        </SelectPrimitive.Viewport>
        <SelectScrollDownButton />
      </SelectPrimitive.Content>
    </SelectPrimitive.Portal>
  ),
)
SelectContent.displayName = 'SelectContent'

const SelectLabel = React.forwardRef<React.ComponentRef<typeof SelectPrimitive.Label>, React.ComponentPropsWithoutRef<typeof SelectPrimitive.Label>>(
  ({ className, ...props }, ref) => (
    <SelectPrimitive.Label ref={ref} data-slot="select-label" className={cn('px-2 py-1.5 text-xs font-medium text-muted-foreground', className)} {...props} />
  ),
)
SelectLabel.displayName = 'SelectLabel'

const SelectItem = React.forwardRef<React.ComponentRef<typeof SelectPrimitive.Item>, React.ComponentPropsWithoutRef<typeof SelectPrimitive.Item>>(
  ({ className, children, ...props }, ref) => (
    <SelectPrimitive.Item
      ref={ref}
      data-slot="select-item"
      className={cn(
        'relative flex w-full cursor-default items-center gap-2 rounded-md py-1.5 pr-8 pl-2 text-sm outline-hidden select-none focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50',
        '[&_i]:text-muted-foreground *:[span]:last:flex *:[span]:last:items-center *:[span]:last:gap-2',
        className,
      )}
      {...props}
    >
      <span data-slot="select-item-indicator" className="absolute right-2 flex size-4 items-center justify-center">
        <SelectPrimitive.ItemIndicator>
          <i className="ph ph-check text-foreground!" aria-hidden="true" />
        </SelectPrimitive.ItemIndicator>
      </span>
      <SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>
    </SelectPrimitive.Item>
  ),
)
SelectItem.displayName = 'SelectItem'

const SelectSeparator = React.forwardRef<
  React.ComponentRef<typeof SelectPrimitive.Separator>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Separator>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.Separator ref={ref} data-slot="select-separator" className={cn('pointer-events-none -mx-1 my-1 h-px bg-border', className)} {...props} />
))
SelectSeparator.displayName = 'SelectSeparator'

export {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectScrollDownButton,
  SelectScrollUpButton,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
}
