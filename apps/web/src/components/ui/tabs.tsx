import { cva, type VariantProps } from 'class-variance-authority'
import { Tabs as TabsPrimitive } from 'radix-ui'
import * as React from 'react'

import { cn } from '@/utils/cn'

const Tabs = React.forwardRef<React.ComponentRef<typeof TabsPrimitive.Root>, React.ComponentPropsWithoutRef<typeof TabsPrimitive.Root>>(
  ({ className, orientation = 'horizontal', ...props }, ref) => (
    <TabsPrimitive.Root
      ref={ref}
      data-slot="tabs"
      data-orientation={orientation}
      orientation={orientation}
      className={cn('group/tabs flex gap-4 data-[orientation=horizontal]:flex-col', className)}
      {...props}
    />
  ),
)
Tabs.displayName = 'Tabs'

/** `default`: segmented control on a muted track. `line`: underline tabs for page sections. */
const tabsListVariants = cva(
  'group/tabs-list inline-flex w-fit items-center justify-center text-muted-foreground group-data-[orientation=vertical]/tabs:h-fit group-data-[orientation=vertical]/tabs:flex-col',
  {
    variants: {
      variant: {
        default: 'h-9 rounded-lg bg-muted p-[3px]',
        line: 'h-9 gap-4 border-b bg-transparent group-data-[orientation=horizontal]/tabs:w-full group-data-[orientation=horizontal]/tabs:justify-start',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
)

const TabsList = React.forwardRef<
  React.ComponentRef<typeof TabsPrimitive.List>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.List> & VariantProps<typeof tabsListVariants>
>(({ className, variant = 'default', ...props }, ref) => (
  <TabsPrimitive.List ref={ref} data-slot="tabs-list" data-variant={variant} className={cn(tabsListVariants({ variant }), className)} {...props} />
))
TabsList.displayName = 'TabsList'

const TabsTrigger = React.forwardRef<React.ComponentRef<typeof TabsPrimitive.Trigger>, React.ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger>>(
  ({ className, ...props }, ref) => (
    <TabsPrimitive.Trigger
      ref={ref}
      data-slot="tabs-trigger"
      className={cn(
        'relative inline-flex h-full flex-1 items-center justify-center gap-1.5 rounded-md border border-transparent px-2.5 py-1 text-sm font-medium whitespace-nowrap text-muted-foreground transition-[color,background-color,box-shadow] outline-none',
        'hover:text-foreground focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:pointer-events-none disabled:opacity-50 group-data-[orientation=vertical]/tabs:w-full group-data-[orientation=vertical]/tabs:justify-start',
        'group-data-[variant=default]/tabs-list:data-[state=active]:bg-background group-data-[variant=default]/tabs-list:data-[state=active]:text-foreground group-data-[variant=default]/tabs-list:data-[state=active]:shadow-sm',
        'dark:group-data-[variant=default]/tabs-list:data-[state=active]:border-input dark:group-data-[variant=default]/tabs-list:data-[state=active]:bg-input/30',
        'group-data-[variant=line]/tabs-list:flex-none group-data-[variant=line]/tabs-list:rounded-none group-data-[variant=line]/tabs-list:px-0.5 group-data-[variant=line]/tabs-list:data-[state=active]:text-foreground',
        'after:absolute after:inset-x-0 after:-bottom-px after:h-0.5 after:rounded-full after:bg-foreground after:opacity-0 after:transition-opacity group-data-[variant=line]/tabs-list:data-[state=active]:after:opacity-100',
        className,
      )}
      {...props}
    />
  ),
)
TabsTrigger.displayName = 'TabsTrigger'

const TabsContent = React.forwardRef<React.ComponentRef<typeof TabsPrimitive.Content>, React.ComponentPropsWithoutRef<typeof TabsPrimitive.Content>>(
  ({ className, ...props }, ref) => <TabsPrimitive.Content ref={ref} data-slot="tabs-content" className={cn('flex-1 outline-none', className)} {...props} />,
)
TabsContent.displayName = 'TabsContent'

export { Tabs, TabsContent, TabsList, tabsListVariants, TabsTrigger }
