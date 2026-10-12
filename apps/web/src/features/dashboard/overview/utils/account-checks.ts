import type { UserProfile } from '@/types/models'

export interface AccountCheck {
  id: string
  label: string
  /** Shown under the label. */
  detail: string
  ok: boolean
}

/** Security posture of the signed-in account, derived only from GET /auth/me (no invented data). */
export function getAccountChecks(user: UserProfile): AccountCheck[] {
  return [
    {
      id: 'email',
      label: 'Email address verified',
      detail: user.emailVerified ? user.email : 'Use the link we emailed you to verify it.',
      ok: user.emailVerified,
    },
    {
      id: '2fa',
      label: 'Two-factor authentication',
      detail: user.twoFactorEnabled ? 'A code is required at every sign-in.' : 'Not enabled — recommended for every account.',
      ok: user.twoFactorEnabled,
    },
    {
      id: 'status',
      label: 'Account active',
      detail: user.status === 'active' ? 'You can sign in and use the app.' : `Status: ${user.status}`,
      ok: user.status === 'active',
    },
  ]
}
