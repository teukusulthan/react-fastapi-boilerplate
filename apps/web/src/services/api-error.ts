import { isAxiosError, isCancel } from 'axios'

import type { ApiEnvelope, ApiErrorCode, ApiFieldError, ClientErrorCode } from '@/types/api'

export type ApiErrorCodeValue = ApiErrorCode | ClientErrorCode | (string & Record<never, never>)

export interface ApiErrorInit {
  status: number
  code: ApiErrorCodeValue
  message: string
  details?: unknown
  requestId?: string | null
  cause?: unknown
}

/**
 * The single error type that leaves the API layer. Every rejected promise from
 * `apiClient` / `apiRequests` / services is an `ApiError`.
 *
 * - `status`    HTTP status, or `0` when no response was received (network / timeout / cancel)
 * - `code`      backend `metaData.errorCode` or a client code (NETWORK_ERROR, TIMEOUT, …)
 * - `message`   human-readable, safe to show to users
 * - `details`   backend `data` on errors (e.g. 422 → `[{ field, message }]`), otherwise null
 * - `requestId` backend request id (metaData.requestId / X-Request-ID) for support/debugging
 */
export class ApiError extends Error {
  readonly status: number
  readonly code: ApiErrorCodeValue
  readonly details: unknown
  readonly requestId: string | null

  constructor({ status, code, message, details = null, requestId = null, cause }: ApiErrorInit) {
    super(message, cause === undefined ? undefined : { cause })
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
    this.requestId = requestId
  }

  /** Field-level validation errors (422), empty otherwise. */
  get fieldErrors(): ApiFieldError[] {
    return isFieldErrorList(this.details) ? this.details : []
  }
}

export const isApiError = (error: unknown): error is ApiError => error instanceof ApiError

export function isFieldErrorList(value: unknown): value is ApiFieldError[] {
  return (
    Array.isArray(value) &&
    value.every(
      (item) =>
        typeof item === 'object' && item !== null && typeof (item as ApiFieldError).field === 'string' && typeof (item as ApiFieldError).message === 'string',
    )
  )
}

/** Runtime guard for the backend envelope `{ metaData: { status, … }, data }`. */
export function isApiEnvelope(value: unknown): value is ApiEnvelope<unknown> {
  if (typeof value !== 'object' || value === null || !('metaData' in value) || !('data' in value)) return false
  const { metaData } = value as { metaData: unknown }
  return typeof metaData === 'object' && metaData !== null && typeof (metaData as { status?: unknown }).status === 'boolean'
}

export function codeForStatus(status: number): ApiErrorCodeValue {
  if (status === 400) return 'BAD_REQUEST'
  if (status === 401) return 'AUTHENTICATION_ERROR'
  if (status === 403) return 'PERMISSION_ERROR'
  if (status === 404) return 'RESOURCE_NOT_FOUND'
  if (status === 409) return 'CONFLICT'
  if (status === 422) return 'VALIDATION_ERROR'
  if (status === 429) return 'RATE_LIMITED'
  if (status >= 500) return 'INTERNAL_ERROR'
  return 'UNKNOWN_ERROR'
}

export function messageForStatus(status: number): string {
  if (status === 400) return 'The request could not be processed.'
  if (status === 401) return 'Your session has expired. Please sign in again.'
  if (status === 403) return 'You do not have permission to perform this action.'
  if (status === 404) return 'The requested resource was not found.'
  if (status === 409) return 'This conflicts with existing data.'
  if (status === 422) return 'Some fields are invalid.'
  if (status === 429) return 'Too many requests. Please wait a moment and try again.'
  if (status === 502 || status === 503 || status === 504) return 'The server is unavailable right now. Please try again later.'
  if (status >= 500) return 'The server encountered an error. Please try again later.'
  return 'Something went wrong. Please try again.'
}

const NETWORK_MESSAGE = 'Unable to reach the server. Check your connection and try again.'
const TIMEOUT_MESSAGE = 'The server took too long to respond. Please try again.'
const UNKNOWN_MESSAGE = 'Something went wrong. Please try again.'

function readRequestId(headers: unknown): string | null {
  if (!headers || typeof headers !== 'object') return null
  const getter = (headers as { get?: (name: string) => unknown }).get
  const value = typeof getter === 'function' ? getter.call(headers, 'x-request-id') : (headers as Record<string, unknown>)['x-request-id']
  return typeof value === 'string' && value ? value : null
}

/** Build an ApiError from an error envelope (non-2xx, or 2xx with `metaData.status === false`). */
export function errorFromEnvelope(envelope: ApiEnvelope<unknown>, httpStatus: number, headers?: unknown, cause?: unknown): ApiError {
  const { metaData } = envelope
  const status = httpStatus >= 400 ? httpStatus : metaData.responseCode >= 400 ? metaData.responseCode : httpStatus
  return new ApiError({
    status,
    code: metaData.errorCode || codeForStatus(status),
    message: metaData.message || messageForStatus(status),
    details: envelope.data ?? null,
    requestId: metaData.requestId || readRequestId(headers),
    cause,
  })
}

/** Normalize anything thrown by axios (or our own code) into an ApiError. */
export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error

  if (isCancel(error)) {
    return new ApiError({ status: 0, code: 'REQUEST_CANCELLED', message: 'The request was cancelled.', cause: error })
  }

  if (isAxiosError(error)) {
    const { response } = error
    if (!response) {
      const timedOut = error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT'
      return new ApiError({
        status: 0,
        code: timedOut ? 'TIMEOUT' : 'NETWORK_ERROR',
        message: timedOut ? TIMEOUT_MESSAGE : NETWORK_MESSAGE,
        cause: error,
      })
    }
    if (isApiEnvelope(response.data)) {
      return errorFromEnvelope(response.data, response.status, response.headers, error)
    }
    return new ApiError({
      status: response.status,
      code: codeForStatus(response.status),
      message: messageForStatus(response.status),
      requestId: readRequestId(response.headers),
      cause: error,
    })
  }

  return new ApiError({ status: 0, code: 'UNKNOWN_ERROR', message: UNKNOWN_MESSAGE, cause: error })
}

/** User-facing message for any thrown value. */
export function getErrorMessage(error: unknown, fallback = UNKNOWN_MESSAGE): string {
  return toApiError(error).message || fallback
}
