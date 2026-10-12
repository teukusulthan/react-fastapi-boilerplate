import type { UserProfile } from '@/types/models'

export function getUserDisplayName(user: Pick<UserProfile, 'fullname' | 'username'>): string {
  return user.fullname?.trim() || user.username
}

export function getUserInitials(user: Pick<UserProfile, 'fullname' | 'username'>): string {
  const parts = getUserDisplayName(user).split(/\s+/).filter(Boolean)
  const initials = parts.length > 1 ? `${parts[0][0]}${parts[parts.length - 1][0]}` : (parts[0] ?? '?').slice(0, 2)
  return initials.toUpperCase()
}
