import * as React from 'react'

import { cn } from '@/utils/cn'

const Textarea = React.forwardRef<HTMLTextAreaElement, React.ComponentProps<'textarea'>>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    data-slot="textarea"
    className={cn(
      'flex field-sizing-content min-h-16 w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground shadow-xs transition-[color,box-shadow,border-color] outline-none dark:bg-input/30',
      'placeholder:text-muted-foreground',
      'focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50',
      'disabled:cursor-not-allowed disabled:opacity-50',
      'aria-invalid:border-destructive aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40',
      className,
    )}
    {...props}
  />
))
Textarea.displayName = 'Textarea'

export { Textarea }
