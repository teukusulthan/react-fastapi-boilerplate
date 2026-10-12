import { Suspense } from 'react'
import { Outlet } from 'react-router-dom'

import { LoadingState } from '@/components/common/LoadingState'
import AppHeader from '@/components/layouts/AppHeader'
import AppSidebar from '@/components/layouts/AppSidebar'
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar'
import { PerfectScrollArea } from '@/components/wrappers/PerfectScrollArea'
import { usePageTitle } from '@/hooks/use-page-title'
import { useRouteHandle } from '@/hooks/use-route-handle'

/**
 * Authenticated shell. Regions never overlap:
 *   root   flex h-svh flex-col overflow-hidden (shell canvas = bg-sidebar)
 *   header h-12 shrink-0, full width
 *   body   flex min-h-0 flex-1 overflow-hidden → sidebar (fixed, offset top-12, in-flow gap reserves its width)
 *          + main (SidebarInset: rounded inset panel on md+, PerfectScrollArea inside)
 * Page padding and max width are owned here — pages never add outer padding.
 */
export default function AppLayout() {
  const handle = useRouteHandle()
  usePageTitle(handle?.title)

  return (
    <SidebarProvider className="h-svh flex-col overflow-hidden bg-sidebar text-foreground">
      <AppHeader />
      <div className="flex min-h-0 flex-1 overflow-hidden">
        <AppSidebar />
        <SidebarInset id="main-content" tabIndex={-1} className="min-h-0 outline-none">
          <PerfectScrollArea className="h-full" contentClassName="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
            <Suspense fallback={<LoadingState />}>
              <Outlet />
            </Suspense>
          </PerfectScrollArea>
        </SidebarInset>
      </div>
    </SidebarProvider>
  )
}
