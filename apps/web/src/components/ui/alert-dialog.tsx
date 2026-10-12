import { AlertDialog as AlertDialogPrimitive } from 'radix-ui'
import * as React from 'react'

import { buttonVariants, type ButtonProps } from '@/components/ui/button'
import { cn } from '@/utils/cn'

const AlertDialog = AlertDialogPrimitive.Root
const AlertDialogTrigger = AlertDialogPrimitive.Trigger
const AlertDialogPortal = AlertDialogPrimitive.Portal

const AlertDialogOverlay = React.forwardRef<
  React.ComponentRef<typeof AlertDialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <AlertDialogPrimitive.Overlay
    ref={ref}
    data-slot="alert-dialog-overlay"
    className={cn(
      'fixed inset-0 z-50 bg-black/50 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:animate-in data-[state=open]:fade-in-0',
      className,
    )}
    {...props}
  />
))
AlertDialogOverlay.displayName = 'AlertDialogOverlay'

const AlertDialogContent = React.forwardRef<
  React.ComponentRef<typeof AlertDialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Content> & { size?: 'default' | 'sm' }
>(({ className, size = 'default', ...props }, ref) => (
  <AlertDialogPortal>
    <AlertDialogOverlay />
    <AlertDialogPrimitive.Content
      ref={ref}
      data-slot="alert-dialog-content"
      data-size={size}
      className={cn(
        'group/alert-dialog-content fixed top-1/2 left-1/2 z-50 grid w-full max-w-[calc(100%-2rem)] -translate-x-1/2 -translate-y-1/2 gap-4 rounded-xl border bg-popover p-6 text-popover-foreground shadow-lg duration-200',
        'data-[size=sm]:max-w-sm data-[size=default]:sm:max-w-md',
        'data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95',
        className,
      )}
      {...props}
    />
  </AlertDialogPortal>
))
AlertDialogContent.displayName = 'AlertDialogContent'

const AlertDialogHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    data-slot="alert-dialog-header"
    className={cn('flex flex-col gap-1.5 text-left has-data-[slot=alert-dialog-media]:gap-2', className)}
    {...props}
  />
))
AlertDialogHeader.displayName = 'AlertDialogHeader'

/** Optional icon tile above the title (e.g. `<i className="ph ph-trash" />` tinted destructive). */
const AlertDialogMedia = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    data-slot="alert-dialog-media"
    className={cn('mb-2 inline-flex size-10 items-center justify-center rounded-lg bg-muted text-foreground [&>i]:size-5 [&>i]:text-xl', className)}
    {...props}
  />
))
AlertDialogMedia.displayName = 'AlertDialogMedia'

const AlertDialogFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div ref={ref} data-slot="alert-dialog-footer" className={cn('flex flex-col-reverse gap-2 pt-2 sm:flex-row sm:justify-end', className)} {...props} />
))
AlertDialogFooter.displayName = 'AlertDialogFooter'

const AlertDialogTitle = React.forwardRef<
  React.ComponentRef<typeof AlertDialogPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Title>
>(({ className, ...props }, ref) => (
  <AlertDialogPrimitive.Title
    ref={ref}
    data-slot="alert-dialog-title"
    className={cn('text-lg leading-snug font-semibold tracking-tight', className)}
    {...props}
  />
))
AlertDialogTitle.displayName = 'AlertDialogTitle'

const AlertDialogDescription = React.forwardRef<
  React.ComponentRef<typeof AlertDialogPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Description>
>(({ className, ...props }, ref) => (
  <AlertDialogPrimitive.Description ref={ref} data-slot="alert-dialog-description" className={cn('text-sm text-muted-foreground', className)} {...props} />
))
AlertDialogDescription.displayName = 'AlertDialogDescription'

type AlertDialogButtonProps = Pick<ButtonProps, 'variant' | 'size'>

const AlertDialogAction = React.forwardRef<
  React.ComponentRef<typeof AlertDialogPrimitive.Action>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Action> & AlertDialogButtonProps
>(({ className, variant = 'default', size = 'default', ...props }, ref) => (
  <AlertDialogPrimitive.Action ref={ref} data-slot="alert-dialog-action" className={cn(buttonVariants({ variant, size }), className)} {...props} />
))
AlertDialogAction.displayName = 'AlertDialogAction'

const AlertDialogCancel = React.forwardRef<
  React.ComponentRef<typeof AlertDialogPrimitive.Cancel>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Cancel> & AlertDialogButtonProps
>(({ className, variant = 'outline', size = 'default', ...props }, ref) => (
  <AlertDialogPrimitive.Cancel ref={ref} data-slot="alert-dialog-cancel" className={cn(buttonVariants({ variant, size }), className)} {...props} />
))
AlertDialogCancel.displayName = 'AlertDialogCancel'

export {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogMedia,
  AlertDialogOverlay,
  AlertDialogPortal,
  AlertDialogTitle,
  AlertDialogTrigger,
}
