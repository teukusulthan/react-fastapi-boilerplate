import { useMutation } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'

import { authService } from '@/services/auth.service'

/**
 * Confirms an email-verification token (`POST /auth/verify-email`) exactly once per token.
 * Tokens are single-use, so the request must not be repeated by StrictMode's double effects.
 */
export function useVerifyEmail(token: string | null) {
  const mutation = useMutation({ mutationFn: (value: string) => authService.verifyEmail({ token: value }) })
  const submitted = useRef<string | null>(null)
  const { mutate } = mutation

  useEffect(() => {
    if (!token || submitted.current === token) return
    submitted.current = token
    mutate(token)
  }, [token, mutate])

  return mutation
}
