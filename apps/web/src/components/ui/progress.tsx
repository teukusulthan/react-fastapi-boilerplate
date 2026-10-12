import { Progress as ProgressPrimitive } from 'radix-ui'
import * as React from 'react'

import { cn } from '@/utils/cn'

const Progress = React.forwardRef<React.ComponentRef<typeof ProgressPrimitive.Root>, React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root>>(
  ({ className, value, ...props }, ref) => (
    <ProgressPrimitive.Root
      ref={ref}
      data-slot="progress"
      value={value}
      className={cn('relative h-2 w-full overflow-hidden rounded-full bg-muted dark:bg-accent', className)}
      {...props}
    >
      <ProgressPrimitive.Indicator
        data-slot="progress-indicator"
        className="h-full w-full flex-1 rounded-full bg-primary transition-transform duration-300"
        style={{ transform: `translateX(-${100 - (value ?? 0)}%)` }}
      />
    </ProgressPrimitive.Root>
  ),
)
Progress.displayName = 'Progress'

export { Progress }
