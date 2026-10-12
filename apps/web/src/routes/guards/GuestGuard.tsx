import type { ReactNode } from 'react'
import { Navigate, Outlet, useSearchParams } from 'react-router-dom'

import { FullScreenLoader } from '@/components/common/FullScreenLoader'
import { REDIRECT_PARAM } from '@/config/constants'
import { getSafeRedirect, useSession } from '@/features/shared/auth'

/**
 * For guest-only pages (login, …). Authenticated users are sent to `?redirect=` (validated) or "/".
 * This is also where the post-login redirect happens.
 */
export default function GuestGuard({ children }: { children?: ReactNode }) {
  const { status, error } = useSession()
  const [searchParams] = useSearchParams()

  if (status === 'authenticated') return <Navigate to={getSafeRedirect(searchParams.get(REDIRECT_PARAM))} replace />
  if (status === 'unknown' && !error) return <FullScreenLoader label="Checking your session…" />
  return children ?? <Outlet />
}
