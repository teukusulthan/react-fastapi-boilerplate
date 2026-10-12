import type { IMenu, IMenuNode, IMenuSection, MenuGroup } from '@/types/menu'

const isVisible = (item: IMenu) => item.show && item.enabled

/**
 * Top-level visible entries with their visible children (one level deep), preserving config order.
 * Children whose parent is hidden are dropped.
 */
export function buildMenuTree(menus: readonly IMenu[]): IMenuNode[] {
  return menus
    .filter((item) => item.idParent === '' && isVisible(item))
    .map((parent) => ({
      ...parent,
      children: menus.filter((child) => child.idParent === parent.id && isVisible(child)),
    }))
}

/** Active when the pathname equals the item path, or is nested below it (except for "/"). */
export function isMenuPathActive(itemPath: string, pathname: string): boolean {
  if (itemPath === '/') return pathname === '/'
  return pathname === itemPath || pathname.startsWith(`${itemPath.replace(/\/+$/, '')}/`)
}

export function formatPageTitle(pageTitle: string | undefined, appName: string): string {
  return pageTitle ? `${pageTitle} — ${appName}` : appName
}

/**
 * Sidebar sections, in config order:
 * - consecutive top-level leaf entries of the same `group` form one section labelled by the group;
 * - a top-level entry with visible children forms its own section labelled by its `display`
 *   (the parent acts as a heading; its children are the items).
 */
export function buildMenuSections(menus: readonly IMenu[], groupLabels: Record<MenuGroup, string>): IMenuSection[] {
  const sections: IMenuSection[] = []
  for (const node of buildMenuTree(menus)) {
    if (node.children.length > 0) {
      sections.push({ id: node.id, label: node.display, items: node.children })
      continue
    }
    const { children: _children, ...item } = node
    const last = sections[sections.length - 1]
    if (last && last.id === `group:${node.group}`) last.items.push(item)
    else sections.push({ id: `group:${node.group}`, label: groupLabels[node.group], items: [item] })
  }
  return sections
}

/**
 * Breadcrumb trail for a pathname: the best-matching menu entry (exact path, else the deepest active
 * ancestor path) preceded by its parents. Empty when no menu entry matches.
 */
export function getMenuTrail(menus: readonly IMenu[], pathname: string): IMenu[] {
  const candidates = menus.filter((item) => isMenuPathActive(item.path, pathname))
  const match = candidates.find((item) => item.path === pathname) ?? [...candidates].sort((a, b) => b.path.length - a.path.length)[0]
  if (!match) return []
  const trail: IMenu[] = [match]
  let parentId = match.idParent
  while (parentId) {
    const parent = menus.find((item) => item.id === parentId)
    if (!parent || trail.includes(parent)) break
    trail.unshift(parent)
    parentId = parent.idParent
  }
  return trail
}
