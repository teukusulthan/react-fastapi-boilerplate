import { describe, expect, it } from 'vitest'

import type { UserProfile } from '@/types/models'

import { getAccountChecks } from './account-checks'

const user = (overrides: Partial<UserProfile>) =>
  ({ email: 'a@b.c', emailVerified: true, twoFactorEnabled: true, status: 'active', ...overrides }) as UserProfile

describe('getAccountChecks', () => {
  it('reports every check as passing for a secured active account', () => {
    expect(getAccountChecks(user({})).every((check) => check.ok)).toBe(true)
  })

  it('flags missing 2FA, unverified email and inactive status', () => {
    const checks = getAccountChecks(user({ emailVerified: false, twoFactorEnabled: false, status: 'pending' }))
    expect(checks.map((check) => [check.id, check.ok])).toEqual([
      ['email', false],
      ['2fa', false],
      ['status', false],
    ])
  })
})
