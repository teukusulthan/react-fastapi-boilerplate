import { lazy } from 'react'
import { Navigate, type RouteObject } from 'react-router-dom'

import { ADMIN_ROLES } from '@/config/constants'

import RoleGuard from './guards/RoleGuard'

const UserPage = lazy(() => import('@/pages/administrator/user/UserPage'))

/** /administrator/* — admin role only. Spread into the AppLayout children in main.routes.tsx (once). */
const adminRoutes: RouteObject[] = [
  {
    path: 'administrator',
    element: <RoleGuard allowedRoles={ADMIN_ROLES} />,
    children: [
      { index: true, element: <Navigate to="user" replace /> },
      { path: 'user', element: <UserPage /> },
    ],
  },
]

export default adminRoutes
