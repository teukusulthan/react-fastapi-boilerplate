import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useAuthStore } from '@/stores/useAuthStore'

import { useLogout } from '../hooks/useLogout'
import { getUserDisplayName, getUserInitials } from '../utils/user-display'

/** Header avatar → account menu (identity, role, sign out). */
export function UserMenu() {
  const user = useAuthStore((state) => state.user)
  const logout = useLogout()

  if (!user) return null

  const name = getUserDisplayName(user)

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon-sm" className="rounded-full" aria-label={`Account menu for ${name}`}>
          <Avatar size="sm" className="size-7">
            <AvatarFallback className="bg-primary/10 text-primary ring-primary/20">{getUserInitials(user)}</AvatarFallback>
          </Avatar>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-64">
        <DropdownMenuLabel className="flex items-center gap-3 px-2 py-2 font-normal">
          <Avatar>
            <AvatarFallback className="bg-primary/10 text-primary ring-primary/20">{getUserInitials(user)}</AvatarFallback>
          </Avatar>
          <span className="flex min-w-0 flex-1 flex-col">
            <span className="truncate text-sm font-medium text-foreground">{name}</span>
            <span className="truncate text-xs text-muted-foreground">{user.email}</span>
          </span>
          {user.role && (
            <Badge variant="outline" className="capitalize">
              {user.role}
            </Badge>
          )}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          disabled={logout.isPending}
          onSelect={(event) => {
            event.preventDefault()
            logout.mutate()
          }}
        >
          <i className={logout.isPending ? 'ph ph-spinner animate-spin' : 'ph ph-sign-out'} aria-hidden="true" />
          {logout.isPending ? 'Signing out…' : 'Sign out'}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
