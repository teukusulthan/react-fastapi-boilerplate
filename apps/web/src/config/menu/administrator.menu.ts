import type { IMenu } from '@/types/menu'

// Admin menus — rendered by AppSidebar only for users passing the admin RoleGuard (ADMIN_ROLES).
// The `qeuln` parent renders as a section label; children render as items.
// IDs come from the reserved table in .claude/skills/reactjs-menu-config/SKILL.md.

export const ADMINISTRATOR_MENU: IMenu[] = [
  {
    id: 'qeuln',
    idParent: '',
    display: 'Administrator',
    name: 'administrator',
    path: '/administrator',
    show: true,
    search: false,
    enabled: true,
    group: 'system',
    type: 'menu',
    icon: 'shield-check',
    seo: { title: 'Administrator', description: '' },
    privileges: null,
    additional: {
      container: 'full',
      iconType: 'phosphor',
      iconStyle: 'regular',
      iconStyleActive: 'fill',
      mainPage: false,
      redirectToEnabled: true,
      redirectTo: '/administrator/user',
    },
  },
  {
    id: '4sbm5a',
    idParent: 'qeuln',
    display: 'Users',
    name: 'administrator-user',
    path: '/administrator/user',
    show: true,
    search: true,
    enabled: true,
    group: 'system',
    type: 'menu',
    icon: 'users',
    seo: { title: 'Users', description: 'Manage user accounts' },
    privileges: [
      { label: 'View', value: 'view', description: 'List and view users', type: 'administrator' },
      { label: 'Create & Update', value: 'create_update', description: 'Create and edit users', type: 'administrator' },
      { label: 'Delete', value: 'delete', description: 'Delete users', type: 'administrator' },
    ],
    additional: {
      container: 'full',
      iconType: 'phosphor',
      iconStyle: 'regular',
      iconStyleActive: 'fill',
      mainPage: false,
      redirectToEnabled: false,
      redirectTo: '',
    },
  },
]
