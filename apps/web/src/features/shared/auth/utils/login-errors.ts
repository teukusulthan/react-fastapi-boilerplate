import { getErrorMessage, isApiError } from '@/services/api-error'

import { ACCOUNT_NOT_VERIFIED_MESSAGE } from '../constants/auth.constants'

/** User-facing message for a failed sign-in (maps auth-specific error codes to clearer copy). */
export function getLoginErrorMessage(error: unknown): string {
  if (isApiError(error) && error.code === 'ACCOUNT_NOT_VERIFIED') return ACCOUNT_NOT_VERIFIED_MESSAGE
  return getErrorMessage(error)
}
