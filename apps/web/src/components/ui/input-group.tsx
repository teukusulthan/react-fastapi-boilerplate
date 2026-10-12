import { cva, type VariantProps } from 'class-variance-authority'
import * as React from 'react'

import { Button, type ButtonProps } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/utils/cn'

/**
 * Input with addons (icons, text, buttons, kbd) inside the same border:
 * <InputGroup><InputGroupAddon><i className="ph ph-magnifying-glass" /></InputGroupAddon><InputGroupInput /></InputGroup>
 */
const InputGroup = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    data-slot="input-group"
    role="group"
    className={cn(
      'group/input-group relative flex h-9 w-full min-w-0 items-center rounded-md border border-input bg-background shadow-xs transition-[color,box-shadow,border-color] outline-none dark:bg-input/30',
      'has-[>textarea]:h-auto',
      'has-[>[data-align=inline-start]]:[&>input]:pl-2 has-[>[data-align=inline-end]]:[&>input]:pr-2',
      'has-[>[data-align=block-start]]:h-auto has-[>[data-align=block-start]]:flex-col has-[>[data-align=block-start]]:[&>input]:pb-3',
      'has-[>[data-align=block-end]]:h-auto has-[>[data-align=block-end]]:flex-col has-[>[data-align=block-end]]:[&>input]:pt-3',
      'has-[[data-slot=input-group-control]:focus-visible]:border-ring has-[[data-slot=input-group-control]:focus-visible]:ring-[3px] has-[[data-slot=input-group-control]:focus-visible]:ring-ring/50',
      'has-[[data-slot][aria-invalid=true]]:border-destructive has-[[data-slot][aria-invalid=true]]:ring-destructive/20 dark:has-[[data-slot][aria-invalid=true]]:ring-destructive/40',
      className,
    )}
    {...props}
  />
))
InputGroup.displayName = 'InputGroup'

const inputGroupAddonVariants = cva(
  'flex h-auto cursor-text items-center justify-center gap-2 py-1.5 text-sm font-medium text-muted-foreground select-none group-data-[disabled=true]/input-group:opacity-50',
  {
    variants: {
      align: {
        'inline-start': 'order-first pl-3 has-[>button]:-ml-1.5 has-[>kbd]:-ml-1',
        'inline-end': 'order-last pr-3 has-[>button]:-mr-1.5 has-[>kbd]:-mr-1',
        'block-start': 'order-first w-full justify-start px-3 pt-3 group-has-[>input]/input-group:pt-2.5 [.border-b]:pb-3',
        'block-end': 'order-last w-full justify-start px-3 pb-3 group-has-[>input]/input-group:pb-2.5 [.border-t]:pt-3',
      },
    },
    defaultVariants: {
      align: 'inline-start',
    },
  },
)

const InputGroupAddon = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement> & VariantProps<typeof inputGroupAddonVariants>>(
  ({ className, align = 'inline-start', onClick, ...props }, ref) => (
    // Clicking the addon focuses the input (mouse convenience only; the input stays keyboard-reachable).
    // eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-noninteractive-element-interactions
    <div
      ref={ref}
      role="group"
      data-slot="input-group-addon"
      data-align={align}
      className={cn(inputGroupAddonVariants({ align }), className)}
      onClick={(event) => {
        onClick?.(event)
        if ((event.target as HTMLElement).closest('button')) return
        event.currentTarget.parentElement?.querySelector<HTMLElement>('input, textarea')?.focus()
      }}
      {...props}
    />
  ),
)
InputGroupAddon.displayName = 'InputGroupAddon'

const inputGroupButtonVariants = cva('flex items-center gap-2 text-sm shadow-none', {
  variants: {
    size: {
      xs: 'h-6 gap-1 rounded-sm px-2 [&>i]:size-3.5 [&>i]:text-sm',
      sm: 'h-8 gap-1.5 rounded-md px-2.5',
      'icon-xs': 'size-6 rounded-sm p-0 [&>i]:size-3.5 [&>i]:text-sm',
      'icon-sm': 'size-8 p-0',
    },
  },
  defaultVariants: {
    size: 'xs',
  },
})

const InputGroupButton = React.forwardRef<HTMLButtonElement, Omit<ButtonProps, 'size'> & VariantProps<typeof inputGroupButtonVariants>>(
  ({ className, type = 'button', variant = 'ghost', size = 'xs', ...props }, ref) => (
    <Button ref={ref} type={type} data-size={size} variant={variant} className={cn(inputGroupButtonVariants({ size }), className)} {...props} />
  ),
)
InputGroupButton.displayName = 'InputGroupButton'

const InputGroupText = React.forwardRef<HTMLSpanElement, React.HTMLAttributes<HTMLSpanElement>>(({ className, ...props }, ref) => (
  <span ref={ref} className={cn('flex items-center gap-2 text-sm text-muted-foreground', className)} {...props} />
))
InputGroupText.displayName = 'InputGroupText'

const InputGroupInput = React.forwardRef<HTMLInputElement, React.ComponentProps<'input'>>(({ className, ...props }, ref) => (
  <Input
    ref={ref}
    data-slot="input-group-control"
    className={cn('flex-1 rounded-none border-0 bg-transparent shadow-none focus-visible:ring-0 dark:bg-transparent', className)}
    {...props}
  />
))
InputGroupInput.displayName = 'InputGroupInput'

const InputGroupTextarea = React.forwardRef<HTMLTextAreaElement, React.ComponentProps<'textarea'>>(({ className, ...props }, ref) => (
  <Textarea
    ref={ref}
    data-slot="input-group-control"
    className={cn('flex-1 resize-none rounded-none border-0 bg-transparent py-3 shadow-none focus-visible:ring-0 dark:bg-transparent', className)}
    {...props}
  />
))
InputGroupTextarea.displayName = 'InputGroupTextarea'

export { InputGroup, InputGroupAddon, InputGroupButton, InputGroupInput, InputGroupText, InputGroupTextarea }
