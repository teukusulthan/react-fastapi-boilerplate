import { DropdownMenu as DropdownMenuPrimitive } from 'radix-ui'
import * as React from 'react'

import { cn } from '@/utils/cn'

const DropdownMenu = DropdownMenuPrimitive.Root
const DropdownMenuPortal = DropdownMenuPrimitive.Portal
const DropdownMenuTrigger = DropdownMenuPrimitive.Trigger
const DropdownMenuSub = DropdownMenuPrimitive.Sub
const DropdownMenuRadioGroup = DropdownMenuPrimitive.RadioGroup

const menuItemBase =
  'relative flex cursor-default items-center gap-2 rounded-md px-2 py-1.5 text-sm outline-hidden select-none focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50 [&>i]:text-muted-foreground focus:[&>i]:text-accent-foreground'

const menuContentBase =
  'z-50 min-w-40 overflow-x-hidden overflow-y-auto rounded-lg border bg-popover p-1 text-popover-foreground shadow-md data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95'

const DropdownMenuContent = React.forwardRef<
  React.ComponentRef<typeof DropdownMenuPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Content>
>(({ className, sideOffset = 4, ...props }, ref) => (
  <DropdownMenuPrimitive.Portal>
    <DropdownMenuPrimitive.Content
      ref={ref}
      data-slot="dropdown-menu-content"
      sideOffset={sideOffset}
      className={cn(
        menuContentBase,
        'max-h-(--radix-dropdown-menu-content-available-height) origin-(--radix-dropdown-menu-content-transform-origin)',
        className,
      )}
      {...props}
    />
  </DropdownMenuPrimitive.Portal>
))
DropdownMenuContent.displayName = 'DropdownMenuContent'

const DropdownMenuGroup = React.forwardRef<
  React.ComponentRef<typeof DropdownMenuPrimitive.Group>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Group>
>((props, ref) => <DropdownMenuPrimitive.Group ref={ref} data-slot="dropdown-menu-group" {...props} />)
DropdownMenuGroup.displayName = 'DropdownMenuGroup'

const DropdownMenuItem = React.forwardRef<
  React.ComponentRef<typeof DropdownMenuPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Item> & { inset?: boolean; variant?: 'default' | 'destructive' }
>(({ className, inset, variant = 'default', ...props }, ref) => (
  <DropdownMenuPrimitive.Item
    ref={ref}
    data-slot="dropdown-menu-item"
    data-inset={inset}
    data-variant={variant}
    className={cn(
      menuItemBase,
      'data-[inset]:pl-8',
      'data-[variant=destructive]:text-destructive data-[variant=destructive]:focus:bg-destructive/10 data-[variant=destructive]:focus:text-destructive dark:data-[variant=destructive]:focus:bg-destructive/15 data-[variant=destructive]:[&>i]:text-destructive',
      className,
    )}
    {...props}
  />
))
DropdownMenuItem.displayName = 'DropdownMenuItem'

const DropdownMenuCheckboxItem = React.forwardRef<
  React.ComponentRef<typeof DropdownMenuPrimitive.CheckboxItem>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.CheckboxItem>
>(({ className, children, checked, ...props }, ref) => (
  <DropdownMenuPrimitive.CheckboxItem
    ref={ref}
    data-slot="dropdown-menu-checkbox-item"
    className={cn(menuItemBase, 'pl-8', className)}
    checked={checked}
    {...props}
  >
    <span className="pointer-events-none absolute left-2 flex size-4 items-center justify-center">
      <DropdownMenuPrimitive.ItemIndicator>
        <i className="ph ph-check text-foreground" aria-hidden="true" />
      </DropdownMenuPrimitive.ItemIndicator>
    </span>
    {children}
  </DropdownMenuPrimitive.CheckboxItem>
))
DropdownMenuCheckboxItem.displayName = 'DropdownMenuCheckboxItem'

const DropdownMenuRadioItem = React.forwardRef<
  React.ComponentRef<typeof DropdownMenuPrimitive.RadioItem>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.RadioItem>
>(({ className, children, ...props }, ref) => (
  <DropdownMenuPrimitive.RadioItem ref={ref} data-slot="dropdown-menu-radio-item" className={cn(menuItemBase, 'pl-8', className)} {...props}>
    <span className="pointer-events-none absolute left-2 flex size-4 items-center justify-center">
      <DropdownMenuPrimitive.ItemIndicator>
        <span className="block size-2 rounded-full bg-foreground" aria-hidden="true" />
      </DropdownMenuPrimitive.ItemIndicator>
    </span>
    {children}
  </DropdownMenuPrimitive.RadioItem>
))
DropdownMenuRadioItem.displayName = 'DropdownMenuRadioItem'

const DropdownMenuLabel = React.forwardRef<
  React.ComponentRef<typeof DropdownMenuPrimitive.Label>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Label> & { inset?: boolean }
>(({ className, inset, ...props }, ref) => (
  <DropdownMenuPrimitive.Label
    ref={ref}
    data-slot="dropdown-menu-label"
    data-inset={inset}
    className={cn('px-2 py-1.5 text-xs font-medium text-muted-foreground data-[inset]:pl-8', className)}
    {...props}
  />
))
DropdownMenuLabel.displayName = 'DropdownMenuLabel'

const DropdownMenuSeparator = React.forwardRef<
  React.ComponentRef<typeof DropdownMenuPrimitive.Separator>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Separator>
>(({ className, ...props }, ref) => (
  <DropdownMenuPrimitive.Separator ref={ref} data-slot="dropdown-menu-separator" className={cn('-mx-1 my-1 h-px bg-border', className)} {...props} />
))
DropdownMenuSeparator.displayName = 'DropdownMenuSeparator'

const DropdownMenuShortcut = React.forwardRef<HTMLSpanElement, React.HTMLAttributes<HTMLSpanElement>>(({ className, ...props }, ref) => (
  <span ref={ref} data-slot="dropdown-menu-shortcut" className={cn('ml-auto text-xs tracking-widest text-muted-foreground', className)} {...props} />
))
DropdownMenuShortcut.displayName = 'DropdownMenuShortcut'

const DropdownMenuSubTrigger = React.forwardRef<
  React.ComponentRef<typeof DropdownMenuPrimitive.SubTrigger>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.SubTrigger> & { inset?: boolean }
>(({ className, inset, children, ...props }, ref) => (
  <DropdownMenuPrimitive.SubTrigger
    ref={ref}
    data-slot="dropdown-menu-sub-trigger"
    data-inset={inset}
    className={cn(menuItemBase, 'data-[inset]:pl-8 data-[state=open]:bg-accent data-[state=open]:text-accent-foreground', className)}
    {...props}
  >
    {children}
    <i className="ph ph-caret-right ml-auto size-3.5" aria-hidden="true" />
  </DropdownMenuPrimitive.SubTrigger>
))
DropdownMenuSubTrigger.displayName = 'DropdownMenuSubTrigger'

const DropdownMenuSubContent = React.forwardRef<
  React.ComponentRef<typeof DropdownMenuPrimitive.SubContent>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.SubContent>
>(({ className, ...props }, ref) => (
  <DropdownMenuPrimitive.Portal>
    <DropdownMenuPrimitive.SubContent
      ref={ref}
      data-slot="dropdown-menu-sub-content"
      className={cn(menuContentBase, 'origin-(--radix-dropdown-menu-content-transform-origin) shadow-lg', className)}
      {...props}
    />
  </DropdownMenuPrimitive.Portal>
))
DropdownMenuSubContent.displayName = 'DropdownMenuSubContent'

export {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuPortal,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
}
