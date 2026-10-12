import type { IMenu } from '@/types/menu'

// Primary navigation for every authenticated user — rendered by AppSidebar.
// IDs must be unique across ALL_MENUS (see .claude/skills/reactjs-menu-config/SKILL.md).
// `path` must match a route registered in src/routes/.

export const APP_MENU: IMenu[] = [
  {
    id: 'dk7f2q',
    idParent: '',
    display: 'Dashboard',
    name: 'dashboard',
    path: '/',
    show: true,
    search: true,
    enabled: true,
    group: 'data',
    type: 'menu',
    icon: 'squares-four',
    seo: { title: 'Dashboard', description: '' },
    privileges: null,
    additional: {
      container: 'full',
      iconType: 'phosphor',
      iconStyle: 'regular',
      iconStyleActive: 'fill',
      mainPage: true,
      redirectToEnabled: false,
      redirectTo: '',
    },
  },
]
