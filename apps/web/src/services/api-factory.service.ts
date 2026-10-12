import type { AxiosRequestConfig } from 'axios'

import type { ApiEnvelope, ApiList, FindDTO } from '@/types/api'

import apiClient from './api-client'
import { ApiError } from './api-error'

type RequestOptions = Omit<AxiosRequestConfig, 'url' | 'method' | 'data' | 'params'>

/** Raw request returning the full envelope (use when `metaData` is needed). */
export function requestEnvelope<T>(config: AxiosRequestConfig): Promise<ApiEnvelope<T>> {
  // The response interceptor resolves with the envelope, so the 2nd generic is the real return type.
  return apiClient.request<ApiEnvelope<T>, ApiEnvelope<T>>(config)
}

const unwrap = <T>(promise: Promise<ApiEnvelope<T>>): Promise<T> => promise.then((envelope) => envelope.data)

/** Convert a `get-all` envelope into `{ items, pagination }`. */
export function toApiList<T>(envelope: ApiEnvelope<T[]>, query: FindDTO = {}): ApiList<T> {
  if (!Array.isArray(envelope.data)) {
    throw new ApiError({
      status: envelope.metaData.responseCode,
      code: 'INVALID_RESPONSE',
      message: 'Unexpected response from the server.',
      requestId: envelope.metaData.requestId ?? null,
    })
  }
  const items = envelope.data
  const pagination = envelope.metaData.pagination ?? {
    page: query.page ?? 1,
    size: query.size ?? items.length,
    totalElements: items.length,
    totalPages: items.length > 0 ? 1 : 0,
  }
  return { items, pagination }
}

/**
 * Typed request helpers. Each resolves with the unwrapped `data` (or `{ items, pagination }` for lists)
 * and rejects with `ApiError`. Always pass paths from `API_ENDPOINTS`.
 */
export const apiRequests = {
  get: <T>(url: string, params?: object, options?: RequestOptions): Promise<T> => unwrap(requestEnvelope<T>({ ...options, method: 'GET', url, params })),

  post: <T, P = unknown>(url: string, data?: P, options?: RequestOptions): Promise<T> => unwrap(requestEnvelope<T>({ ...options, method: 'POST', url, data })),

  put: <T, P = unknown>(url: string, data?: P, options?: RequestOptions): Promise<T> => unwrap(requestEnvelope<T>({ ...options, method: 'PUT', url, data })),

  patch: <T, P = unknown>(url: string, data?: Partial<P>, options?: RequestOptions): Promise<T> =>
    unwrap(requestEnvelope<T>({ ...options, method: 'PATCH', url, data })),

  delete: <T = null>(url: string, params?: object, options?: RequestOptions): Promise<T> =>
    unwrap(requestEnvelope<T>({ ...options, method: 'DELETE', url, params })),

  /** POST a FindDTO to a `get-all` endpoint. */
  list: <T>(url: string, query: FindDTO = {}, options?: RequestOptions): Promise<ApiList<T>> =>
    requestEnvelope<T[]>({ ...options, method: 'POST', url, data: query }).then((envelope) => toApiList(envelope, query)),

  /** multipart/form-data upload (axios sets the boundary header from the FormData body). */
  upload: <T>(url: string, formData: FormData, onProgress?: (percent: number) => void, options?: RequestOptions): Promise<T> =>
    unwrap(
      requestEnvelope<T>({
        ...options,
        method: 'POST',
        url,
        data: formData,
        onUploadProgress: (event) => {
          if (onProgress && event.total) onProgress(Math.round((event.loaded * 100) / event.total))
        },
      }),
    ),

  envelope: requestEnvelope,
}
