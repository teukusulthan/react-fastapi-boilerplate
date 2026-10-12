import type { ReactNode } from 'react'
import { Outlet } from 'react-router-dom'

import { hasAccess } from '@/features/shared/auth'
import ForbiddenPage from '@/pages/errors/ForbiddenPage'
import { useAuthStore } from '@/stores/useAuthStore'

export interface RoleGuardProps {
  /** User role (permission alias) must be one of these. Superusers always pass. */
  allowedRoles?: readonly string[]
  /** User must hold all of these privileges. */
  requiredPrivileges?: readonly string[]
  children?: ReactNode
}

/** Must be nested inside AuthGuard. Renders the 403 page in place (URL is kept) when access is denied. */
export default function RoleGuard({ allowedRoles, requiredPrivileges, children }: RoleGuardProps) {
  const user = useAuthStore((state) => state.user)

  if (!hasAccess(user, { roles: allowedRoles, privileges: requiredPrivileges })) return <ForbiddenPage />
  return children ?? <Outlet />
}
