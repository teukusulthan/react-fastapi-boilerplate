import * as React from 'react'

import { cn } from '@/utils/cn'

const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<'input'>>(({ className, type, ...props }, ref) => (
  <input
    ref={ref}
    type={type}
    data-slot="input"
    className={cn(
      'flex h-9 w-full min-w-0 rounded-md border border-input bg-background px-3 py-1 text-sm text-foreground shadow-xs transition-[color,box-shadow,border-color] outline-none dark:bg-input/30',
      'placeholder:text-muted-foreground selection:bg-primary selection:text-primary-foreground',
      'file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground',
      'focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50',
      'disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50',
      'aria-invalid:border-destructive aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40',
      '[&::-webkit-search-cancel-button]:appearance-none',
      className,
    )}
    {...props}
  />
))
Input.displayName = 'Input'

export { Input }
