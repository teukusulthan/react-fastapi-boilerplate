import { Command as CommandPrimitive } from 'cmdk'
import * as React from 'react'

import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { cn } from '@/utils/cn'

const Command = React.forwardRef<React.ComponentRef<typeof CommandPrimitive>, React.ComponentPropsWithoutRef<typeof CommandPrimitive>>(
  ({ className, ...props }, ref) => (
    <CommandPrimitive
      ref={ref}
      data-slot="command"
      className={cn('flex h-full w-full flex-col overflow-hidden rounded-xl bg-popover text-popover-foreground', className)}
      {...props}
    />
  ),
)
Command.displayName = 'Command'

interface CommandDialogProps extends React.ComponentProps<typeof Dialog> {
  title?: string
  description?: string
  className?: string
  showCloseButton?: boolean
}

/** ⌘K-style palette in a dialog. */
const CommandDialog = ({
  title = 'Command palette',
  description = 'Search for a command to run…',
  children,
  className,
  showCloseButton = false,
  ...props
}: CommandDialogProps) => (
  <Dialog {...props}>
    <DialogContent className={cn('overflow-hidden p-0 sm:max-w-lg', className)} showCloseButton={showCloseButton}>
      <DialogHeader className="sr-only">
        <DialogTitle>{title}</DialogTitle>
        <DialogDescription>{description}</DialogDescription>
      </DialogHeader>
      <Command className="**:data-[slot=command-input-wrapper]:h-12 [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group]]:px-2 [&_[cmdk-item]]:py-2.5">
        {children}
      </Command>
    </DialogContent>
  </Dialog>
)

const CommandInput = React.forwardRef<React.ComponentRef<typeof CommandPrimitive.Input>, React.ComponentPropsWithoutRef<typeof CommandPrimitive.Input>>(
  ({ className, ...props }, ref) => (
    <div data-slot="command-input-wrapper" className="flex h-10 items-center gap-2 border-b px-3">
      <i className="ph ph-magnifying-glass text-muted-foreground" aria-hidden="true" />
      <CommandPrimitive.Input
        ref={ref}
        data-slot="command-input"
        className={cn(
          'flex h-10 w-full rounded-md bg-transparent py-3 text-sm outline-hidden placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50',
          className,
        )}
        {...props}
      />
    </div>
  ),
)
CommandInput.displayName = 'CommandInput'

const CommandList = React.forwardRef<React.ComponentRef<typeof CommandPrimitive.List>, React.ComponentPropsWithoutRef<typeof CommandPrimitive.List>>(
  ({ className, ...props }, ref) => (
    <CommandPrimitive.List ref={ref} data-slot="command-list" className={cn('max-h-72 scroll-py-1 overflow-x-hidden overflow-y-auto', className)} {...props} />
  ),
)
CommandList.displayName = 'CommandList'

const CommandEmpty = React.forwardRef<React.ComponentRef<typeof CommandPrimitive.Empty>, React.ComponentPropsWithoutRef<typeof CommandPrimitive.Empty>>(
  ({ className, ...props }, ref) => (
    <CommandPrimitive.Empty ref={ref} data-slot="command-empty" className={cn('py-6 text-center text-sm text-muted-foreground', className)} {...props} />
  ),
)
CommandEmpty.displayName = 'CommandEmpty'

const CommandGroup = React.forwardRef<React.ComponentRef<typeof CommandPrimitive.Group>, React.ComponentPropsWithoutRef<typeof CommandPrimitive.Group>>(
  ({ className, ...props }, ref) => (
    <CommandPrimitive.Group
      ref={ref}
      data-slot="command-group"
      className={cn(
        'overflow-hidden p-1 text-foreground [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-muted-foreground',
        className,
      )}
      {...props}
    />
  ),
)
CommandGroup.displayName = 'CommandGroup'

const CommandSeparator = React.forwardRef<
  React.ComponentRef<typeof CommandPrimitive.Separator>,
  React.ComponentPropsWithoutRef<typeof CommandPrimitive.Separator>
>(({ className, ...props }, ref) => (
  <CommandPrimitive.Separator ref={ref} data-slot="command-separator" className={cn('-mx-1 h-px bg-border', className)} {...props} />
))
CommandSeparator.displayName = 'CommandSeparator'

const CommandItem = React.forwardRef<React.ComponentRef<typeof CommandPrimitive.Item>, React.ComponentPropsWithoutRef<typeof CommandPrimitive.Item>>(
  ({ className, ...props }, ref) => (
    <CommandPrimitive.Item
      ref={ref}
      data-slot="command-item"
      className={cn(
        'relative flex cursor-default items-center gap-2 rounded-md px-2 py-1.5 text-sm outline-hidden select-none data-[disabled=true]:pointer-events-none data-[disabled=true]:opacity-50 data-[selected=true]:bg-accent data-[selected=true]:text-accent-foreground [&>i]:text-muted-foreground',
        className,
      )}
      {...props}
    />
  ),
)
CommandItem.displayName = 'CommandItem'

const CommandShortcut = ({ className, ...props }: React.HTMLAttributes<HTMLSpanElement>) => (
  <span data-slot="command-shortcut" className={cn('ml-auto text-xs tracking-widest text-muted-foreground', className)} {...props} />
)
CommandShortcut.displayName = 'CommandShortcut'

export { Command, CommandDialog, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList, CommandSeparator, CommandShortcut }
