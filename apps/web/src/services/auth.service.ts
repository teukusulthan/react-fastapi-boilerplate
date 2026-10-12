import type { TwoFactorMethod, UserProfile } from '@/types/models'

import { refreshSession } from './api-client'
import { API_ENDPOINTS } from './api-endpoints'
import { apiRequests } from './api-factory.service'

/* ── Payloads ───────────────────────────────────────────────────────────────── */

export interface ILoginPayload {
  /** Username or email */
  identifier: string
  password: string
}

export interface ITwoFactorVerifyPayload {
  sessionToken: string
  otp: string
}

export interface ITwoFactorResendPayload {
  sessionToken: string
}

export type { TwoFactorMethod }

export interface ITwoFactorSetupPayload {
  method: TwoFactorMethod
}

export interface ITwoFactorEnablePayload {
  otp: string
}

export interface ITwoFactorDisablePayload {
  password: string
}

export interface IRegisterPayload {
  username: string
  fullname: string
  email: string
  phone?: string
  password: string
}

export interface IRegisterVerifyPayload {
  email: string
  otp: string
}

export interface IForgotPasswordRequestPayload {
  email: string
}

export interface IForgotPasswordVerifyPayload {
  email: string
  otp: string
}

export interface IForgotPasswordResetPayload {
  email: string
  otp: string
  newPassword: string
}

export interface IChangePasswordPayload {
  currentPassword: string
  newPassword: string
}

export interface IVerifyEmailPayload {
  /** `?token=` from the verification link */
  token: string
}

export interface IGoogleCallbackPayload {
  code: string
  redirectUri: string
  /** PKCE verifier (43-128 chars) when the authorization request used PKCE. */
  codeVerifier?: string
}

/* ── Responses ──────────────────────────────────────────────────────────────── */

/** Tokens are also set as httpOnly cookies; the web app ignores the body copy. */
export interface IAuthTokens {
  accessToken: string
  refreshToken: string
  /** Access-token expiry, ISO-8601 UTC. */
  expiresAt: string
}

export interface ILoginSuccess {
  twoFactorRequired?: false
  user: UserProfile
  auth: IAuthTokens
}

export interface ITwoFactorChallenge {
  twoFactorRequired: true
  sessionToken: string
  method: TwoFactorMethod
}

export type LoginResult = ILoginSuccess | ITwoFactorChallenge

export interface IMessageResponse {
  message: string
}

export interface ITwoFactorSetupResult {
  method: TwoFactorMethod
  message: string
  /** TOTP only (pending until `/auth/2fa/enable`) */
  otpauthUri: string | null
  /** PNG, base64 without the `data:` prefix */
  qrImageBase64: string | null
  secret: string | null
}

export interface IOtpValidity {
  valid: boolean
}

export const isTwoFactorChallenge = (result: LoginResult): result is ITwoFactorChallenge => result.twoFactorRequired === true

const toVoid = (): void => undefined

/** Every auth endpoint of the backend (local provider). */
export const authService = {
  login: (data: ILoginPayload) => apiRequests.post<LoginResult, ILoginPayload>(API_ENDPOINTS.AUTH.LOGIN, data),

  verifyTwoFactor: (data: ITwoFactorVerifyPayload) => apiRequests.post<ILoginSuccess, ITwoFactorVerifyPayload>(API_ENDPOINTS.AUTH.TWO_FACTOR_VERIFY, data),

  resendTwoFactor: (data: ITwoFactorResendPayload) => apiRequests.post<IMessageResponse, ITwoFactorResendPayload>(API_ENDPOINTS.AUTH.TWO_FACTOR_RESEND, data),

  setupTwoFactor: (data: ITwoFactorSetupPayload) => apiRequests.post<ITwoFactorSetupResult, ITwoFactorSetupPayload>(API_ENDPOINTS.AUTH.TWO_FACTOR_SETUP, data),

  /** Resolves with the updated profile (`twoFactorEnabled: true`). */
  enableTwoFactor: (data: ITwoFactorEnablePayload) => apiRequests.post<UserProfile, ITwoFactorEnablePayload>(API_ENDPOINTS.AUTH.TWO_FACTOR_ENABLE, data),

  /** Wrong password → 400 (not 401), so no refresh is attempted. */
  disableTwoFactor: (data: ITwoFactorDisablePayload) => apiRequests.post<UserProfile, ITwoFactorDisablePayload>(API_ENDPOINTS.AUTH.TWO_FACTOR_DISABLE, data),

  /** Rotates the cookie pair. Shared single-flight with the 401 interceptor. */
  refresh: (): Promise<void> => refreshSession(),

  /** Idempotent: succeeds even if the session is already gone. */
  logout: () => apiRequests.post<unknown>(API_ENDPOINTS.AUTH.LOGOUT, undefined, { skipAuthRefresh: true }).then(toVoid),

  me: () => apiRequests.get<UserProfile>(API_ENDPOINTS.AUTH.ME),

  register: (data: IRegisterPayload) => apiRequests.post<IMessageResponse, IRegisterPayload>(API_ENDPOINTS.AUTH.REGISTER, data),

  verifyRegistration: (data: IRegisterVerifyPayload) => apiRequests.post<IMessageResponse, IRegisterVerifyPayload>(API_ENDPOINTS.AUTH.REGISTER_VERIFY, data),

  /** Re-send the sign-up code (generic response, rate-limited). */
  resendRegistrationCode: (data: IForgotPasswordRequestPayload) =>
    apiRequests.post<IMessageResponse, IForgotPasswordRequestPayload>(API_ENDPOINTS.AUTH.REGISTER_RESEND, data),

  /** Always resolves with a generic message (no account enumeration). */
  requestPasswordReset: (data: IForgotPasswordRequestPayload) =>
    apiRequests.post<IMessageResponse, IForgotPasswordRequestPayload>(API_ENDPOINTS.AUTH.FORGOT_PASSWORD_REQUEST, data),

  verifyPasswordResetOtp: (data: IForgotPasswordVerifyPayload) =>
    apiRequests.post<IOtpValidity, IForgotPasswordVerifyPayload>(API_ENDPOINTS.AUTH.FORGOT_PASSWORD_VERIFY, data),

  resetPassword: (data: IForgotPasswordResetPayload) =>
    apiRequests.post<IMessageResponse, IForgotPasswordResetPayload>(API_ENDPOINTS.AUTH.FORGOT_PASSWORD_RESET, data),

  /** Revokes the other sessions and sets a fresh cookie pair. Wrong current password → 400. */
  changePassword: (data: IChangePasswordPayload) => apiRequests.post<ILoginSuccess, IChangePasswordPayload>(API_ENDPOINTS.AUTH.CHANGE_PASSWORD, data),

  /** Email a verification link (`<web>/auth/verify-email?token=…`) to the signed-in user. */
  requestEmailVerification: () => apiRequests.post<IMessageResponse>(API_ENDPOINTS.AUTH.VERIFY_EMAIL_REQUEST),

  /** Public: confirm the token from the verification link. */
  verifyEmail: (data: IVerifyEmailPayload) => apiRequests.post<IMessageResponse, IVerifyEmailPayload>(API_ENDPOINTS.AUTH.VERIFY_EMAIL, data),

  /** Only available when Google sign-in is configured on the backend. */
  googleCallback: (data: IGoogleCallbackPayload) => apiRequests.post<LoginResult, IGoogleCallbackPayload>(API_ENDPOINTS.AUTH.GOOGLE_CALLBACK, data),
}
