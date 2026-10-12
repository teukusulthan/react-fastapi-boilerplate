import type { ReactNode } from 'react'

import { SectionCard } from '@/components/common/SectionCard'
import { StatusBadge } from '@/components/common/StatusBadge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { getUserDisplayName, getUserInitials } from '@/features/shared/auth'
import type { UserProfile } from '@/types/models'
import { formatDate } from '@/utils/date-formatter'

/** Read-only profile of the signed-in account (GET /auth/me) as a definition list. */
export function AccountDetailsCard({ user, className }: { user: UserProfile; className?: string }) {
  const rows: { term: string; value: ReactNode }[] = [
    { term: 'Username', value: user.username },
    { term: 'Email', value: user.email },
    { term: 'Phone', value: user.phone ?? <span className="text-muted-foreground">Not set</span> },
    { term: 'Group', value: user.group?.name ?? <span className="text-muted-foreground">No group</span> },
    {
      term: 'Role',
      value: user.role ? (
        <Badge variant="outline" className="capitalize">
          {user.role}
        </Badge>
      ) : (
        <span className="text-muted-foreground">No role assigned</span>
      ),
    },
    { term: 'Member since', value: <span className="tabular-nums">{formatDate(user.createdAt)}</span> },
  ]

  return (
    <SectionCard title="Account" description="Your profile as the server sees it." className={className}>
      <div className="flex flex-col gap-6">
        <div className="flex items-center gap-4">
          <Avatar size="lg" className="size-12">
            <AvatarFallback className="bg-primary/10 text-base text-primary ring-primary/20">{getUserInitials(user)}</AvatarFallback>
          </Avatar>
          <div className="flex min-w-0 flex-col gap-1">
            <span className="truncate text-base font-semibold">{getUserDisplayName(user)}</span>
            <StatusBadge tone={user.status === 'active' ? 'success' : 'warning'}>{user.status === 'active' ? 'Active' : user.status}</StatusBadge>
          </div>
        </div>
        <dl className="grid grid-cols-[max-content_1fr] gap-x-6 gap-y-3 text-sm sm:gap-x-8">
          {rows.map((row) => (
            <div key={row.term} className="contents">
              <dt className="text-muted-foreground">{row.term}</dt>
              <dd className="min-w-0 truncate font-medium">{row.value}</dd>
            </div>
          ))}
        </dl>
      </div>
    </SectionCard>
  )
}
