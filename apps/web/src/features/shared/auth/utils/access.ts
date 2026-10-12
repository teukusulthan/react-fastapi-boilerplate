import { SUPERUSER_ROLES } from '@/config/constants'
import type { UserProfile } from '@/types/models'

export interface AccessRequirement {
  /** User role (permission alias) must be one of these. */
  roles?: readonly string[]
  /** User must hold every one of these privileges. */
  privileges?: readonly string[]
}

export function isSuperuser(user: Pick<UserProfile, 'role'> | null | undefined): boolean {
  return !!user?.role && SUPERUSER_ROLES.includes(user.role)
}

/**
 * Client-side access check mirroring the backend RBAC (superuser → everything; otherwise role and
 * privilege requirements must all match). UI convenience only — the backend enforces access.
 */
export function hasAccess(user: Pick<UserProfile, 'role' | 'permission'> | null | undefined, requirement: AccessRequirement = {}): boolean {
  if (!user) return false
  if (isSuperuser(user)) return true
  const { roles, privileges } = requirement
  if (roles && roles.length > 0 && (!user.role || !roles.includes(user.role))) return false
  if (privileges && privileges.length > 0) {
    const granted = user.permission?.privileges ?? []
    return privileges.every((privilege) => granted.includes(privilege))
  }
  return true
}
