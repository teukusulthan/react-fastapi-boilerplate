import { ADMINISTRATOR_MENU } from './administrator.menu'
import { APP_MENU } from './app.menu'

import type { MenuGroup } from '@/types/menu'

export { ADMINISTRATOR_MENU, APP_MENU }

/** Sidebar section label for top-level entries without children, by `IMenu.group`. */
export const MENU_GROUP_LABEL: Record<MenuGroup, string> = {
  data: 'General',
  workspace: 'Workspace',
  organization: 'Organization',
  application: 'Application',
  system: 'System',
}

/** Flat list of all menus — use for page titles, permission checks, global search, etc. */
export const ALL_MENUS = () => [...APP_MENU, ...ADMINISTRATOR_MENU]
