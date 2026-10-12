import { createBrowserRouter, RouterProvider } from 'react-router-dom'

import { RouteErrorFallback } from '@/components/common/RouteErrorFallback'
import NotFoundPage from '@/pages/errors/NotFoundPage'

import authRoutes from './auth.routes'
import mainRoutes from './main.routes'

export const router = createBrowserRouter([
  {
    errorElement: <RouteErrorFallback />,
    children: [...authRoutes, ...mainRoutes, { path: '*', element: <NotFoundPage /> }],
  },
])

export default function RouteIndex() {
  return <RouterProvider router={router} />
}
