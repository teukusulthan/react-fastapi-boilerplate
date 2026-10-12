import type { IconType, IconWeight } from '@/types/icon'

export interface IPrivilege {
  label: string
  value: string
  description: string
  type?: string
}

export interface IMenuAdditional {
  container: 'boxed' | 'full' | 'fluid'
  iconType: IconType
  iconStyle: IconWeight
  iconStyleActive: IconWeight
  mainPage: boolean
  redirectToEnabled: boolean
  redirectTo: string
}

export interface IMenu {
  id: string
  idParent: string
  display: string
  name: string
  path: string
  show: boolean
  search: boolean
  enabled: boolean
  group: 'data' | 'system' | 'organization' | 'workspace' | 'application'
  type: 'menu'
  icon: string
  seo: { title: string; description: string }
  privileges: IPrivilege[] | null
  tactical?: boolean
  additional?: IMenuAdditional
}

/** A top-level menu entry with its visible children resolved (see utils/menu.ts). */
export interface IMenuNode extends IMenu {
  children: IMenu[]
}

export type MenuGroup = IMenu['group']

/** A labelled block of sidebar navigation (see `buildMenuSections` in utils/menu.ts). */
export interface IMenuSection {
  id: string
  label: string
  items: IMenu[]
}

/** `handle` of a route object: breadcrumb/page title for routes that are not in the menu (e.g. /ui-kit). */
export interface IRouteHandle {
  crumb?: string
  title?: string
}
