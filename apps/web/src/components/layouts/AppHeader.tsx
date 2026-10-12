import { ThemeToggle } from '@/components/common/ThemeToggle'
import AppBrand from '@/components/layouts/AppBrand'
import AppBreadcrumb from '@/components/layouts/AppBreadcrumb'
import { Separator } from '@/components/ui/separator'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { UserMenu } from '@/features/shared/auth'

/**
 * Full-width top bar (h-12) on the shell canvas: brand (aligned with the sidebar column), sidebar toggle,
 * breadcrumb, theme menu, user menu. Navigation itself lives in AppSidebar.
 */
export default function AppHeader() {
  return (
    <header className="relative z-20 flex h-12 shrink-0 items-center gap-2 bg-sidebar pr-3 pl-2 md:pl-0">
      <a
        href="#main-content"
        className="sr-only rounded-md focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:bg-background focus:px-3 focus:py-2 focus:shadow-md"
      >
        Skip to content
      </a>
      <div className="hidden h-full w-(--sidebar-width) shrink-0 items-center px-3 transition-[width] duration-200 ease-linear group-data-[state=collapsed]/sidebar-wrapper:w-(--sidebar-width-icon) md:flex">
        <AppBrand collapsible />
      </div>
      <SidebarTrigger />
      <AppBrand className="md:hidden" />
      <Separator orientation="vertical" className="mx-1 hidden h-4! md:block" />
      <div className="hidden min-w-0 flex-1 md:block">
        <AppBreadcrumb />
      </div>
      <div className="flex-1 md:hidden" />
      <div className="flex items-center gap-1">
        <ThemeToggle />
        <UserMenu />
      </div>
    </header>
  )
}
