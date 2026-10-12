import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'

import { authService, isTwoFactorChallenge, type ILoginSuccess, type ITwoFactorChallenge, type LoginResult } from '@/services/auth.service'
import { useAuthStore } from '@/stores/useAuthStore'

import type { TLoginFormValues, TTwoFactorFormValues } from '../schemas/login.schema'

/**
 * Two-step login: credentials → (optional) 2FA code. On success the auth store becomes
 * `authenticated` and GuestGuard performs the post-login redirect.
 */
export function useLoginFlow() {
  const setUser = useAuthStore((state) => state.setUser)
  const [challenge, setChallenge] = useState<ITwoFactorChallenge | null>(null)

  const completeLogin = (result: ILoginSuccess) => setUser(result.user)

  const loginMutation = useMutation({
    mutationFn: (values: TLoginFormValues) => authService.login(values),
    onSuccess: (result: LoginResult) => {
      if (isTwoFactorChallenge(result)) setChallenge(result)
      else completeLogin(result)
    },
  })

  const verifyMutation = useMutation({
    mutationFn: ({ otp }: TTwoFactorFormValues) => {
      if (!challenge) throw new Error('No pending two-factor challenge')
      return authService.verifyTwoFactor({ sessionToken: challenge.sessionToken, otp })
    },
    onSuccess: completeLogin,
  })

  const resendMutation = useMutation({
    mutationFn: () => {
      if (!challenge) throw new Error('No pending two-factor challenge')
      return authService.resendTwoFactor({ sessionToken: challenge.sessionToken })
    },
  })

  const restart = () => {
    setChallenge(null)
    loginMutation.reset()
    verifyMutation.reset()
    resendMutation.reset()
  }

  return { challenge, loginMutation, verifyMutation, resendMutation, restart }
}
