import { lazy } from 'react'
import type { RouteObject } from 'react-router-dom'

import AppLayout from '@/components/layouts/AppLayout'
import { DEV_TOOLS_ENABLED } from '@/config/env'
import type { IRouteHandle } from '@/types/menu'

import adminRoutes from './admin.routes'
import AuthGuard from './guards/AuthGuard'

const DashboardPage = lazy(() => import('@/pages/dashboard/DashboardPage'))

/**
 * Hidden, dev-only routes (not in the menu on purpose). `DEV_TOOLS_ENABLED` is a build-time literal,
 * so these routes and their chunks are dropped from production builds (keep `lazy()` inside the condition).
 */
function getDevRoutes(): RouteObject[] {
  if (!DEV_TOOLS_ENABLED) return []
  const UiKitPage = lazy(() => import('@/pages/ui-kit/UiKitPage'))
  return [{ path: 'ui-kit', element: <UiKitPage />, handle: { crumb: 'UI kit', title: 'UI kit' } satisfies IRouteHandle }]
}

/** Authenticated routes rendered inside the AppLayout shell. */
const mainRoutes: RouteObject[] = [
  {
    path: '/',
    element: (
      <AuthGuard>
        <AppLayout />
      </AuthGuard>
    ),
    children: [{ index: true, element: <DashboardPage /> }, ...adminRoutes, ...getDevRoutes()],
  },
]

export default mainRoutes
