import { cva, type VariantProps } from 'class-variance-authority'
import * as React from 'react'

import { cn } from '@/utils/cn'

/**
 * Inline message. Put a Phosphor `<i>` first to get the icon column:
 * <Alert variant="destructive"><i className="ph ph-warning-circle" /><AlertTitle/><AlertDescription/></Alert>
 */
const alertVariants = cva(
  [
    'relative grid w-full grid-cols-[0_1fr] items-start gap-y-0.5 rounded-lg border px-4 py-3 text-sm',
    'has-[>i]:grid-cols-[1rem_1fr] has-[>i]:gap-x-3 has-[>svg]:grid-cols-[1rem_1fr] has-[>svg]:gap-x-3',
    '[&>i]:translate-y-0.5 [&>i]:text-current [&>svg]:size-4 [&>svg]:translate-y-0.5 [&>svg]:text-current',
  ],
  {
    variants: {
      variant: {
        default: 'bg-card text-card-foreground',
        destructive: 'border-destructive/25 bg-destructive/5 text-destructive dark:bg-destructive/10 [&_[data-slot=alert-description]]:text-destructive/90',
        success: 'border-success/25 bg-success/5 text-success dark:bg-success/10 [&_[data-slot=alert-description]]:text-success/90',
        warning: 'border-warning/25 bg-warning/5 text-warning dark:bg-warning/10 [&_[data-slot=alert-description]]:text-warning/90',
        info: 'border-info/25 bg-info/5 text-info dark:bg-info/10 [&_[data-slot=alert-description]]:text-info/90',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
)

const Alert = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement> & VariantProps<typeof alertVariants>>(
  ({ className, variant, ...props }, ref) => <div ref={ref} role="alert" data-slot="alert" className={cn(alertVariants({ variant }), className)} {...props} />,
)
Alert.displayName = 'Alert'

const AlertTitle = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div ref={ref} data-slot="alert-title" className={cn('col-start-2 line-clamp-1 min-h-4 font-medium tracking-tight', className)} {...props} />
))
AlertTitle.displayName = 'AlertTitle'

const AlertDescription = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    data-slot="alert-description"
    className={cn('col-start-2 grid justify-items-start gap-1 text-sm text-muted-foreground [&_p]:leading-relaxed', className)}
    {...props}
  />
))
AlertDescription.displayName = 'AlertDescription'

export { Alert, AlertDescription, AlertTitle, alertVariants }
