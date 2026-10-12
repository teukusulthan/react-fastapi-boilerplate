import { useQuery } from '@tanstack/react-query'
import { useEffect } from 'react'

import { ApiError } from '@/services/api-error'
import { authService } from '@/services/auth.service'
import { useAuthStore, type AuthStatus } from '@/stores/useAuthStore'

import { AUTH_QUERY_KEYS } from '../constants/auth.constants'

export interface SessionState {
  status: AuthStatus
  /** Set when /auth/me failed for a transient reason (network / 5xx): session is still unknown. */
  error: ApiError | null
  retry: () => void
}

const isTransient = (error: unknown) => error instanceof ApiError && (error.status === 0 || error.status >= 500)

/**
 * Resolves the session once per app load via GET /auth/me (deduplicated by TanStack Query) and
 * mirrors the result into the auth store. Used by the route guards.
 */
export function useSession(): SessionState {
  const status = useAuthStore((state) => state.status)
  const setUser = useAuthStore((state) => state.setUser)
  const clearSession = useAuthStore((state) => state.clearSession)

  const query = useQuery({
    queryKey: AUTH_QUERY_KEYS.me,
    queryFn: authService.me,
    enabled: status === 'unknown',
    retry: false,
    staleTime: Infinity,
    gcTime: 0,
  })

  const { isSuccess, isError, data, error, refetch } = query

  useEffect(() => {
    if (status !== 'unknown') return
    if (isSuccess) setUser(data)
    else if (isError && !isTransient(error)) clearSession('expired')
  }, [status, isSuccess, isError, data, error, setUser, clearSession])

  return {
    status,
    error: status === 'unknown' && isError && isTransient(error) ? (error as ApiError) : null,
    retry: () => void refetch(),
  }
}
