import { describe, expect, it } from 'vitest'

import type { IMenu } from '@/types/menu'

import { buildMenuSections, buildMenuTree, formatPageTitle, getMenuTrail, isMenuPathActive } from './menu'

const menu = (id: string, idParent: string, path: string, overrides: Partial<IMenu> = {}): IMenu => ({
  id,
  idParent,
  display: id,
  name: id,
  path,
  show: true,
  search: true,
  enabled: true,
  group: 'data',
  type: 'menu',
  icon: 'house',
  seo: { title: id, description: '' },
  privileges: null,
  ...overrides,
})

describe('buildMenuTree', () => {
  it('nests visible children under visible top-level entries', () => {
    const tree = buildMenuTree([
      menu('a', '', '/a'),
      menu('a1', 'a', '/a/1'),
      menu('a2', 'a', '/a/2', { show: false }),
      menu('b', '', '/b', { enabled: false }),
      menu('b1', 'b', '/b/1'),
    ])
    expect(tree.map((node) => [node.id, node.children.map((child) => child.id)])).toEqual([['a', ['a1']]])
  })
})

describe('isMenuPathActive', () => {
  it('matches exact and nested paths, root only exactly', () => {
    expect(isMenuPathActive('/', '/')).toBe(true)
    expect(isMenuPathActive('/', '/administrator')).toBe(false)
    expect(isMenuPathActive('/administrator/user', '/administrator/user/42')).toBe(true)
    expect(isMenuPathActive('/administrator/user', '/administrator/users')).toBe(false)
  })
})

describe('formatPageTitle', () => {
  it('suffixes the app name', () => {
    expect(formatPageTitle('Users', 'App')).toBe('Users — App')
    expect(formatPageTitle(undefined, 'App')).toBe('App')
  })
})

const LABELS = { data: 'General', system: 'System', organization: 'Organization', workspace: 'Workspace', application: 'Application' } as const

describe('buildMenuSections', () => {
  it('groups consecutive leaf entries by group and turns parents into labelled sections', () => {
    const sections = buildMenuSections(
      [
        menu('home', '', '/'),
        menu('reports', '', '/reports'),
        menu('admin', '', '/admin', { display: 'Administrator', group: 'system' }),
        menu('users', 'admin', '/admin/users'),
        menu('hidden', 'admin', '/admin/hidden', { show: false }),
        menu('settings', '', '/settings', { group: 'system' }),
      ],
      LABELS,
    )
    expect(sections.map((section) => [section.label, section.items.map((item) => item.id)])).toEqual([
      ['General', ['home', 'reports']],
      ['Administrator', ['users']],
      ['System', ['settings']],
    ])
  })
})

describe('getMenuTrail', () => {
  const menus = [menu('home', '', '/'), menu('admin', '', '/admin', { display: 'Administrator' }), menu('users', 'admin', '/admin/users')]

  it('returns the matching entry preceded by its parents', () => {
    expect(getMenuTrail(menus, '/admin/users').map((item) => item.id)).toEqual(['admin', 'users'])
    expect(getMenuTrail(menus, '/').map((item) => item.id)).toEqual(['home'])
  })

  it('falls back to the deepest active ancestor and to an empty trail', () => {
    expect(getMenuTrail(menus, '/admin/users/42').map((item) => item.id)).toEqual(['admin', 'users'])
    expect(getMenuTrail(menus, '/unknown')).toEqual([])
  })
})
