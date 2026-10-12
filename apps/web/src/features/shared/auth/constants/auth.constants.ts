export const AUTH_QUERY_KEYS = {
  all: ['auth'] as const,
  me: ['auth', 'me'] as const,
}

export const OTP_LENGTH = 6

export const TWO_FACTOR_METHOD_HINT = {
  email: 'We sent a 6-digit code to your email address.',
  totp: 'Enter the 6-digit code from your authenticator app.',
} as const

/** Login form fields that can receive backend 422 field errors. */
export const LOGIN_FIELDS = ['identifier', 'password'] as const

/** Shown when `POST /auth/login` answers 401 `ACCOUNT_NOT_VERIFIED` (correct password, email not verified yet). */
export const ACCOUNT_NOT_VERIFIED_MESSAGE =
  'Your email address has not been verified yet. Use the verification code or link we emailed you when the account was created, or ask an administrator to activate the account.'
