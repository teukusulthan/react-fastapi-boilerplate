import { useMemo } from 'react'

import AppBrand from '@/components/layouts/AppBrand'
import SidebarNavItem from '@/components/layouts/SidebarNavItem'
import { Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarGroupLabel, SidebarHeader, SidebarMenu } from '@/components/ui/sidebar'
import { PerfectScrollArea } from '@/components/wrappers/PerfectScrollArea'
import { ADMIN_ROLES } from '@/config/constants'
import { ADMINISTRATOR_MENU, APP_MENU, MENU_GROUP_LABEL } from '@/config/menu'
import { hasAccess } from '@/features/shared/auth'
import { useAuthStore } from '@/stores/useAuthStore'
import { buildMenuSections } from '@/utils/menu'

/**
 * Config-driven navigation (src/config/menu/*), grouped into labelled sections (see buildMenuSections).
 * Desktop: fixed panel offset below the h-12 header, collapsible to icons (⌘/Ctrl+B);
 * mobile: off-canvas sheet with the brand on top.
 */
export default function AppSidebar() {
  const user = useAuthStore((state) => state.user)
  const canAdminister = hasAccess(user, { roles: ADMIN_ROLES })

  const sections = useMemo(() => buildMenuSections(canAdminister ? [...APP_MENU, ...ADMINISTRATOR_MENU] : APP_MENU, MENU_GROUP_LABEL), [canAdminister])

  return (
    <Sidebar variant="inset" collapsible="icon" className="top-12 h-[calc(100svh-3rem)]">
      <SidebarHeader className="h-12 justify-center border-b px-4 md:hidden">
        <AppBrand />
      </SidebarHeader>
      <SidebarContent>
        <PerfectScrollArea className="h-full" contentClassName="pt-1 pb-4">
          <nav aria-label="Main navigation" className="flex flex-col gap-1">
            {sections.map((section) => (
              <SidebarGroup key={section.id}>
                <SidebarGroupLabel>{section.label}</SidebarGroupLabel>
                <SidebarGroupContent>
                  <SidebarMenu>
                    {section.items.map((item) => (
                      <SidebarNavItem key={item.id} item={item} />
                    ))}
                  </SidebarMenu>
                </SidebarGroupContent>
              </SidebarGroup>
            ))}
          </nav>
        </PerfectScrollArea>
      </SidebarContent>
    </Sidebar>
  )
}
