import { Link } from 'react-router-dom'

import { PageHeader } from '@/components/common/PageHeader'
import { RelativeTime } from '@/components/common/RelativeTime'
import { StatCard } from '@/components/common/StatCard'
import { Button } from '@/components/ui/button'
import { ADMIN_ROLES } from '@/config/constants'
import { getUserDisplayName, hasAccess } from '@/features/shared/auth'
import { useAuthStore } from '@/stores/useAuthStore'
import { formatDateTime } from '@/utils/date-formatter'

import { AccountDetailsCard } from './AccountDetailsCard'
import { NextStepsCard } from './NextStepsCard'
import { SecurityCard } from './SecurityCard'

/** Placeholder dashboard built only from the signed-in profile — no invented metrics. */
export function DashboardOverview() {
  const user = useAuthStore((state) => state.user)

  if (!user) return null

  const firstName = getUserDisplayName(user).split(/\s+/)[0]
  const isAdmin = hasAccess(user, { roles: ADMIN_ROLES })

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title={`Welcome back, ${firstName}`}
        description="An overview of your account and where to start building."
        actions={
          isAdmin && (
            <Button asChild variant="outline">
              <Link to="/administrator/user">
                <i className="ph ph-users" aria-hidden="true" />
                Manage users
              </Link>
            </Button>
          )
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Role"
          icon="identification-badge"
          value={<span className="capitalize">{user.role ?? 'None'}</span>}
          helper={user.permission?.name ? `Permission set: ${user.permission.name}` : 'No permission set assigned'}
        />
        <StatCard
          label="Two-factor"
          icon="lock-key"
          value={user.twoFactorEnabled ? 'Enabled' : 'Off'}
          helper={user.twoFactorEnabled ? 'Required at every sign-in' : 'Recommended for every account'}
        />
        <StatCard
          label="Last sign-in"
          icon="clock-counter-clockwise"
          value={user.lastLoginAt ? <RelativeTime value={user.lastLoginAt} /> : null}
          helper={user.lastLoginAt ? formatDateTime(user.lastLoginAt) : 'First session'}
        />
        <StatCard
          label="Email"
          icon="envelope-simple"
          value={user.emailVerified ? 'Verified' : 'Unverified'}
          helper={<span className="block truncate">{user.email}</span>}
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <AccountDetailsCard user={user} className="xl:col-span-2" />
        <SecurityCard user={user} />
      </div>

      <NextStepsCard />
    </div>
  )
}
