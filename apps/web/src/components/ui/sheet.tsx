import { cva, type VariantProps } from 'class-variance-authority'
import { Dialog as SheetPrimitive } from 'radix-ui'
import * as React from 'react'

import { cn } from '@/utils/cn'

const Sheet = SheetPrimitive.Root
const SheetTrigger = SheetPrimitive.Trigger
const SheetClose = SheetPrimitive.Close
const SheetPortal = SheetPrimitive.Portal

const SheetOverlay = React.forwardRef<React.ComponentRef<typeof SheetPrimitive.Overlay>, React.ComponentPropsWithoutRef<typeof SheetPrimitive.Overlay>>(
  ({ className, ...props }, ref) => (
    <SheetPrimitive.Overlay
      ref={ref}
      data-slot="sheet-overlay"
      className={cn(
        'fixed inset-0 z-50 bg-black/50 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:animate-in data-[state=open]:fade-in-0',
        className,
      )}
      {...props}
    />
  ),
)
SheetOverlay.displayName = 'SheetOverlay'

const sheetVariants = cva(
  'fixed z-50 flex flex-col gap-4 bg-background shadow-lg transition ease-in-out outline-none data-[state=closed]:animate-out data-[state=closed]:duration-200 data-[state=open]:animate-in data-[state=open]:duration-300',
  {
    variants: {
      side: {
        top: 'inset-x-0 top-0 h-auto border-b data-[state=closed]:slide-out-to-top data-[state=open]:slide-in-from-top',
        bottom: 'inset-x-0 bottom-0 h-auto border-t data-[state=closed]:slide-out-to-bottom data-[state=open]:slide-in-from-bottom',
        left: 'inset-y-0 left-0 h-full w-3/4 border-r data-[state=closed]:slide-out-to-left data-[state=open]:slide-in-from-left sm:max-w-sm',
        right: 'inset-y-0 right-0 h-full w-3/4 border-l data-[state=closed]:slide-out-to-right data-[state=open]:slide-in-from-right sm:max-w-md',
      },
    },
    defaultVariants: {
      side: 'right',
    },
  },
)

interface SheetContentProps extends React.ComponentPropsWithoutRef<typeof SheetPrimitive.Content>, VariantProps<typeof sheetVariants> {
  showCloseButton?: boolean
}

const SheetContent = React.forwardRef<React.ComponentRef<typeof SheetPrimitive.Content>, SheetContentProps>(
  ({ side = 'right', className, children, showCloseButton = true, ...props }, ref) => (
    <SheetPortal>
      <SheetOverlay />
      <SheetPrimitive.Content ref={ref} data-slot="sheet-content" className={cn(sheetVariants({ side }), className)} {...props}>
        {children}
        {showCloseButton && (
          <SheetPrimitive.Close
            data-slot="sheet-close"
            className="absolute top-4 right-4 inline-flex size-7 items-center justify-center rounded-md text-muted-foreground transition-colors outline-none hover:bg-accent hover:text-foreground focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:pointer-events-none"
          >
            <i className="ph ph-x" aria-hidden="true" />
            <span className="sr-only">Close</span>
          </SheetPrimitive.Close>
        )}
      </SheetPrimitive.Content>
    </SheetPortal>
  ),
)
SheetContent.displayName = 'SheetContent'

const SheetHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div ref={ref} data-slot="sheet-header" className={cn('flex flex-col gap-1.5 p-6 pr-12', className)} {...props} />
))
SheetHeader.displayName = 'SheetHeader'

const SheetFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div ref={ref} data-slot="sheet-footer" className={cn('mt-auto flex flex-col-reverse gap-2 border-t p-4 sm:flex-row sm:justify-end', className)} {...props} />
))
SheetFooter.displayName = 'SheetFooter'

const SheetTitle = React.forwardRef<React.ComponentRef<typeof SheetPrimitive.Title>, React.ComponentPropsWithoutRef<typeof SheetPrimitive.Title>>(
  ({ className, ...props }, ref) => (
    <SheetPrimitive.Title ref={ref} data-slot="sheet-title" className={cn('text-base font-semibold text-foreground', className)} {...props} />
  ),
)
SheetTitle.displayName = 'SheetTitle'

const SheetDescription = React.forwardRef<
  React.ComponentRef<typeof SheetPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof SheetPrimitive.Description>
>(({ className, ...props }, ref) => (
  <SheetPrimitive.Description ref={ref} data-slot="sheet-description" className={cn('text-sm text-muted-foreground', className)} {...props} />
))
SheetDescription.displayName = 'SheetDescription'

export { Sheet, SheetClose, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetOverlay, SheetPortal, SheetTitle, SheetTrigger }
