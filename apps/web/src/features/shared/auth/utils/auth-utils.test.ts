import { describe, expect, it } from 'vitest'

import type { UserProfile } from '@/types/models'

import { hasAccess } from './access'
import { buildLoginPath, getSafeRedirect } from './redirect'

describe('getSafeRedirect', () => {
  it.each([
    [null, '/'],
    ['', '/'],
    ['/reports?tab=2#x', '/reports?tab=2#x'],
    ['//evil.example.com', '/'],
    ['/\\evil.example.com', '/'],
    ['https://evil.example.com', '/'],
    ['javascript:alert(1)', '/'],
    ['/auth/login', '/'],
    ['/reports\nx', '/'],
  ])('%s → %s', (input, expected) => {
    expect(getSafeRedirect(input)).toBe(expected)
  })
})

describe('buildLoginPath', () => {
  it('adds an encoded redirect param except for the root', () => {
    expect(buildLoginPath('/administrator/user?page=2')).toBe('/auth/login?redirect=%2Fadministrator%2Fuser%3Fpage%3D2')
    expect(buildLoginPath('/')).toBe('/auth/login')
    expect(buildLoginPath(undefined)).toBe('/auth/login')
  })
})

describe('hasAccess', () => {
  const user = (role: string | null, privileges: string[] = []) =>
    ({ role, permission: role ? { id: 'p', name: role, alias: role, privileges } : null }) as UserProfile

  it('denies without a user', () => {
    expect(hasAccess(null, {})).toBe(false)
  })

  it('checks roles and privileges, with superuser bypass', () => {
    expect(hasAccess(user('user'), { roles: ['admin'] })).toBe(false)
    expect(hasAccess(user('admin'), { roles: ['admin'] })).toBe(true)
    expect(hasAccess(user('owner'), { roles: ['admin'], privileges: ['x'] })).toBe(true)
    expect(hasAccess(user('editor', ['a', 'b']), { privileges: ['a', 'b'] })).toBe(true)
    expect(hasAccess(user('editor', ['a']), { privileges: ['a', 'b'] })).toBe(false)
    expect(hasAccess(user(null), {})).toBe(true)
  })
})
