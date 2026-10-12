import axios, { isAxiosError, type AxiosError, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'

import env from '@/config/env'
import { queryClient } from '@/lib/query-client'
import { useAuthStore, type SessionEndReason } from '@/stores/useAuthStore'
import type { ApiEnvelope } from '@/types/api'

import { API_ENDPOINTS } from './api-endpoints'
import { ApiError, errorFromEnvelope, isApiEnvelope, toApiError } from './api-error'

declare module 'axios' {
  interface AxiosRequestConfig {
    /** Do not attempt a token refresh when this request returns 401. */
    skipAuthRefresh?: boolean
    /** @internal set once a request has been retried after a refresh */
    _authRetried?: boolean
    /** @internal refresh generation at the time the request was sent */
    _authGeneration?: number
  }
}

/**
 * The only axios instance in the app. Auth uses httpOnly cookies (`token`, `refresh_token`),
 * so `withCredentials` is on and no Authorization header is attached.
 *
 * Success interceptor returns the backend envelope (`{ metaData, data }`), never the AxiosResponse.
 * Every failure is rejected as an `ApiError` (see api-error.ts). Use `apiRequests` (api-factory.service.ts)
 * rather than this instance directly — it unwraps `data` with correct typing.
 */
const apiClient = axios.create({
  baseURL: env.api.baseUrl,
  timeout: 30_000,
  withCredentials: true,
  headers: { Accept: 'application/json' },
})

/**
 * Endpoints where a 401 means "bad credentials / no session", not "access token expired":
 * never trigger a refresh for them.
 */
const NO_REFRESH_ENDPOINTS: ReadonlySet<string> = new Set([
  API_ENDPOINTS.AUTH.LOGIN,
  API_ENDPOINTS.AUTH.REFRESH,
  API_ENDPOINTS.AUTH.LOGOUT,
  API_ENDPOINTS.AUTH.TWO_FACTOR_VERIFY,
  API_ENDPOINTS.AUTH.TWO_FACTOR_RESEND,
  API_ENDPOINTS.AUTH.REGISTER,
  API_ENDPOINTS.AUTH.REGISTER_VERIFY,
  API_ENDPOINTS.AUTH.REGISTER_RESEND,
  API_ENDPOINTS.AUTH.VERIFY_EMAIL,
  API_ENDPOINTS.AUTH.FORGOT_PASSWORD_REQUEST,
  API_ENDPOINTS.AUTH.FORGOT_PASSWORD_VERIFY,
  API_ENDPOINTS.AUTH.FORGOT_PASSWORD_RESET,
  API_ENDPOINTS.AUTH.GOOGLE_CALLBACK,
])

/** Path of a request relative to the API base URL, without query/hash (e.g. "/auth/login"). */
export function endpointPath(url: string | undefined, baseURL: string = env.api.baseUrl): string {
  let path = (url ?? '').split(/[?#]/)[0]
  if (/^https?:\/\//i.test(path)) {
    path = new URL(path).pathname
    const basePath = /^https?:\/\//i.test(baseURL) ? new URL(baseURL).pathname : baseURL
    const normalizedBase = basePath.replace(/\/+$/, '')
    if (normalizedBase && path.startsWith(normalizedBase)) path = path.slice(normalizedBase.length)
  }
  return `/${path.replace(/^\/+/, '')}`
}

/* ── Refresh (single-flight) ────────────────────────────────────────────────── */

let refreshPromise: Promise<void> | null = null
/** Incremented after every successful refresh. Requests sent before it can simply be retried. */
let authGeneration = 0

/**
 * Rotate the session via `POST /auth/refresh` (refresh cookie). Concurrent callers share one request.
 */
export function refreshSession(): Promise<void> {
  if (!refreshPromise) {
    refreshPromise = apiClient
      .post(API_ENDPOINTS.AUTH.REFRESH, undefined, { skipAuthRefresh: true })
      .then(() => {
        authGeneration += 1
      })
      .finally(() => {
        refreshPromise = null
      })
  }
  return refreshPromise
}

/**
 * Drop client-side session state and cached server data. Route guards then redirect to
 * /auth/login (with ?redirect=… unless the user logged out deliberately).
 */
export function endClientSession(reason: SessionEndReason = 'expired'): void {
  useAuthStore.getState().clearSession(reason)
  queryClient.clear()
}

/** A refresh that failed because the server was unreachable should not log the user out. */
const isTransientFailure = (error: ApiError) => error.status === 0 || error.status >= 500

/* ── Interceptors ───────────────────────────────────────────────────────────── */

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  config._authGeneration = authGeneration
  return config
})

function onFulfilled(response: AxiosResponse): ApiEnvelope<unknown> {
  const body: unknown = response.data
  if (!isApiEnvelope(body)) {
    throw new ApiError({
      status: response.status,
      code: 'INVALID_RESPONSE',
      message: 'Unexpected response from the server.',
      requestId: typeof response.headers?.['x-request-id'] === 'string' ? response.headers['x-request-id'] : null,
    })
  }
  if (!body.metaData.status) {
    throw errorFromEnvelope(body, response.status, response.headers)
  }
  return body
}

async function onRejected(error: unknown): Promise<never> {
  if (!isAxiosError(error)) throw toApiError(error)

  const config = (error as AxiosError).config
  const status = error.response?.status
  const eligible = status === 401 && config && !config.skipAuthRefresh && !NO_REFRESH_ENDPOINTS.has(endpointPath(config.url))

  if (!eligible || !config) throw toApiError(error)

  if (config._authRetried) {
    // Still unauthorized with a fresh session → the server no longer accepts us.
    endClientSession()
    throw toApiError(error)
  }
  config._authRetried = true

  // Another request already refreshed the session after this one was sent: just replay it.
  if ((config._authGeneration ?? 0) < authGeneration) {
    return apiClient.request(config)
  }

  try {
    await refreshSession()
  } catch (refreshError) {
    const normalized = toApiError(refreshError)
    if (isTransientFailure(normalized)) throw normalized
    endClientSession()
    throw toApiError(error)
  }
  return apiClient.request(config)
}

// The success handler intentionally changes the resolved value to the envelope.
apiClient.interceptors.response.use(onFulfilled as unknown as (response: AxiosResponse) => AxiosResponse, onRejected)

/** @internal test helper — resets the refresh state between tests. */
export function __resetAuthRefreshStateForTests(): void {
  refreshPromise = null
  authGeneration = 0
}

export default apiClient
