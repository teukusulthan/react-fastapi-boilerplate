import type { ReactNode } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { FullScreenLoader } from '@/components/common/FullScreenLoader'
import { LOGIN_PATH } from '@/config/constants'
import { buildLoginPath, useSession } from '@/features/shared/auth'
import { useAuthStore } from '@/stores/useAuthStore'

import ServerUnavailable from './ServerUnavailable'

/**
 * Protects authenticated routes. While the session is being resolved (GET /auth/me) it shows a
 * full-screen loader; anonymous users go to /auth/login?redirect=<current location>.
 */
export default function AuthGuard({ children }: { children?: ReactNode }) {
  const { status, error, retry } = useSession()
  const endReason = useAuthStore((state) => state.endReason)
  const location = useLocation()

  if (error) return <ServerUnavailable onRetry={retry} />
  if (status === 'unknown') return <FullScreenLoader label="Checking your session…" />
  if (status === 'anonymous') {
    const target = endReason === 'logout' ? LOGIN_PATH : buildLoginPath(`${location.pathname}${location.search}${location.hash}`)
    return <Navigate to={target} replace />
  }
  return children ?? <Outlet />
}
