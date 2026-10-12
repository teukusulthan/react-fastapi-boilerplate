import { lazy } from 'react'
import { Navigate, type RouteObject } from 'react-router-dom'

import AuthLayout from '@/components/layouts/AuthLayout'

import GuestGuard from './guards/GuestGuard'

const LoginPage = lazy(() => import('@/pages/auth/LoginPage'))
const VerifyEmailPage = lazy(() => import('@/pages/auth/VerifyEmailPage'))

/**
 * Public auth routes (not in the menu: they are entry points, not navigation targets).
 * - `/auth/login` is guest-only (signed-in users are redirected).
 * - `/auth/verify-email?token=` works signed in or not (target of the backend's verification email,
 *   `BE_EMAIL_VERIFY_PATH`).
 * Register / forgot-password pages can be added here (auth.service has every endpoint).
 */
const authRoutes: RouteObject[] = [
  {
    path: 'auth',
    element: <AuthLayout />,
    children: [
      { index: true, element: <Navigate to="login" replace /> },
      {
        path: 'login',
        element: (
          <GuestGuard>
            <LoginPage />
          </GuestGuard>
        ),
      },
      { path: 'verify-email', element: <VerifyEmailPage /> },
    ],
  },
]

export default authRoutes
