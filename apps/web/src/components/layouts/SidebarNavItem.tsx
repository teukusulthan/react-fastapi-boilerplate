import { NavLink, useLocation } from 'react-router-dom'

import { SidebarMenuButton, SidebarMenuItem, useSidebar } from '@/components/ui/sidebar'
import type { IMenu } from '@/types/menu'
import { renderIcon } from '@/utils/icon-renderer'
import { isMenuPathActive } from '@/utils/menu'

/** One navigation entry rendered from menu config (active state from the current location). */
export default function SidebarNavItem({ item }: { item: IMenu }) {
  const { pathname } = useLocation()
  const { isMobile, setOpenMobile } = useSidebar()
  const isActive = isMenuPathActive(item.path, pathname)
  const weight = isActive ? item.additional?.iconStyleActive : item.additional?.iconStyle

  return (
    <SidebarMenuItem>
      <SidebarMenuButton asChild isActive={isActive} tooltip={item.display}>
        <NavLink to={item.path} end={item.path === '/'} onClick={() => isMobile && setOpenMobile(false)}>
          {renderIcon({ icon: item.icon, iconType: item.additional?.iconType, weight })}
          <span>{item.display}</span>
        </NavLink>
      </SidebarMenuButton>
    </SidebarMenuItem>
  )
}
