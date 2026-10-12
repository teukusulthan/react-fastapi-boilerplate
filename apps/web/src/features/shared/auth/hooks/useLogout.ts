import { useMutation } from '@tanstack/react-query'

import { endClientSession } from '@/services/api-client'
import { authService } from '@/services/auth.service'

/**
 * POST /auth/logout, then clear the client session regardless of the outcome
 * (logout is idempotent server-side; a failed call must not keep the user "logged in" locally).
 * AuthGuard redirects to /auth/login once the store is anonymous.
 */
export function useLogout() {
  return useMutation({
    mutationFn: authService.logout,
    onSettled: () => endClientSession('logout'),
  })
}
