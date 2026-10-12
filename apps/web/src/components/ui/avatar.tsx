import { Avatar as AvatarPrimitive } from 'radix-ui'
import * as React from 'react'

import { cn } from '@/utils/cn'

type AvatarSize = 'sm' | 'default' | 'lg'

const Avatar = React.forwardRef<
  React.ComponentRef<typeof AvatarPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof AvatarPrimitive.Root> & { size?: AvatarSize }
>(({ className, size = 'default', ...props }, ref) => (
  <AvatarPrimitive.Root
    ref={ref}
    data-slot="avatar"
    data-size={size}
    className={cn(
      'group/avatar relative flex size-8 shrink-0 overflow-hidden rounded-full select-none data-[size=lg]:size-10 data-[size=sm]:size-6',
      className,
    )}
    {...props}
  />
))
Avatar.displayName = 'Avatar'

const AvatarImage = React.forwardRef<React.ComponentRef<typeof AvatarPrimitive.Image>, React.ComponentPropsWithoutRef<typeof AvatarPrimitive.Image>>(
  ({ className, ...props }, ref) => (
    <AvatarPrimitive.Image ref={ref} data-slot="avatar-image" className={cn('aspect-square size-full object-cover', className)} {...props} />
  ),
)
AvatarImage.displayName = 'AvatarImage'

/** Initials fallback: neutral fill with a hairline inner ring so it reads on any surface. */
const AvatarFallback = React.forwardRef<React.ComponentRef<typeof AvatarPrimitive.Fallback>, React.ComponentPropsWithoutRef<typeof AvatarPrimitive.Fallback>>(
  ({ className, ...props }, ref) => (
    <AvatarPrimitive.Fallback
      ref={ref}
      data-slot="avatar-fallback"
      className={cn(
        'flex size-full items-center justify-center rounded-full bg-muted text-xs font-medium text-muted-foreground ring-1 ring-border ring-inset group-data-[size=lg]/avatar:text-sm',
        className,
      )}
      {...props}
    />
  ),
)
AvatarFallback.displayName = 'AvatarFallback'

const AvatarGroup = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    data-slot="avatar-group"
    className={cn('group/avatar-group flex -space-x-2 *:data-[slot=avatar]:ring-2 *:data-[slot=avatar]:ring-background', className)}
    {...props}
  />
))
AvatarGroup.displayName = 'AvatarGroup'

export { Avatar, AvatarFallback, AvatarGroup, AvatarImage }
