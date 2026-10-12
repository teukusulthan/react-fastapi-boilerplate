import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { getUserDisplayName, getUserInitials } from '@/features/shared/auth'
import type { UserDetail } from '@/types/models'

/** Primary identity column: avatar + name (+ "You" marker) + muted email. */
export function UserIdentityCell({ user, isCurrentUser = false }: { user: UserDetail; isCurrentUser?: boolean }) {
  return (
    <div className="flex min-w-0 items-center gap-3">
      <Avatar>
        {user.image && <AvatarImage src={user.image} alt="" />}
        <AvatarFallback>{getUserInitials(user)}</AvatarFallback>
      </Avatar>
      <div className="flex min-w-0 flex-col">
        <span className="flex items-center gap-1.5 truncate font-medium text-foreground">
          {getUserDisplayName(user)}
          {isCurrentUser && <span className="rounded-sm bg-muted px-1.5 text-xs font-medium text-muted-foreground">You</span>}
        </span>
        <span className="truncate text-xs text-muted-foreground">{user.email}</span>
      </div>
    </div>
  )
}
