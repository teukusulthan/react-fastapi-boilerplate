import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

import env from '@/config/env'
import { ALL_MENUS } from '@/config/menu'
import { formatPageTitle } from '@/utils/menu'

/**
 * Sets `document.title` from the active menu entry's `seo.title` (or an explicit override).
 * Call once in each layout, not in pages.
 */
export function usePageTitle(override?: string): void {
  const { pathname } = useLocation()

  useEffect(() => {
    const menu = ALL_MENUS().find((item) => item.path === pathname)
    document.title = formatPageTitle(override ?? menu?.seo.title, env.app.name)
  }, [pathname, override])
}
