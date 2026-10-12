/**
 * API path constants — relative to `env.api.baseUrl` (default `/api/v1/apps`, stripped by the proxy).
 * Paths mirror the backend routers exactly. CRUD modules expose `BASE`; the CRUD factory appends
 * `/add`, `/update`, `/delete`, `/get-one`, `/get-all`.
 */
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
    ME: '/auth/me',
    REGISTER: '/auth/register',
    REGISTER_VERIFY: '/auth/register/verify',
    REGISTER_RESEND: '/auth/register/resend',
    FORGOT_PASSWORD_REQUEST: '/auth/forgot-password/request',
    FORGOT_PASSWORD_VERIFY: '/auth/forgot-password/verify',
    FORGOT_PASSWORD_RESET: '/auth/forgot-password/reset',
    CHANGE_PASSWORD: '/auth/change-password',
    /** Authenticated: email a verification link to the current user. */
    VERIFY_EMAIL_REQUEST: '/auth/verify-email/request',
    /** Public: confirm the `?token=` from that link. */
    VERIFY_EMAIL: '/auth/verify-email',
    TWO_FACTOR_VERIFY: '/auth/2fa/verify',
    TWO_FACTOR_RESEND: '/auth/2fa/resend',
    TWO_FACTOR_SETUP: '/auth/2fa/setup',
    TWO_FACTOR_ENABLE: '/auth/2fa/enable',
    TWO_FACTOR_DISABLE: '/auth/2fa/disable',
    /** Only mounted when Google sign-in is configured on the backend. */
    GOOGLE_CALLBACK: '/auth/google/callback',
  },
  USER: {
    BASE: '/user',
    GET_BY_USERNAME: '/user/get-by-username',
    RESET_PASSWORD: '/user/reset-password',
    CHECK_EMAIL: '/user/check-email',
    CHECK_USERNAME: '/user/check-username',
    CHECK_PHONE: '/user/check-phone',
    UPDATE_PROFILE: '/user/settings/update-profile',
  },
  GROUP: {
    BASE: '/group',
  },
  PERMISSION: {
    BASE: '/permission',
    UPDATE_PARTIAL: '/permission/update-partial',
  },
  ROLE: {
    BASE: '/role',
  },
  UPLOAD: {
    UPLOAD_FILE: '/upload/upload-file',
    GET_ALL: '/upload/get-all',
    GET_ONE: '/upload/get-one',
    DELETE: '/upload/delete',
  },
  HEALTH: {
    LIVE: '/health/live',
    READY: '/health/ready',
  },
} as const

export type ApiEndpoints = typeof API_ENDPOINTS
