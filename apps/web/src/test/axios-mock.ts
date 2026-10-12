import { AxiosError, AxiosHeaders, type AxiosAdapter, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'

import type { ApiEnvelope, ApiPagination } from '@/types/api'

export interface MockReply {
  status: number
  data?: unknown
  headers?: Record<string, string>
}

export type MockHandler = (config: InternalAxiosRequestConfig) => MockReply | Promise<MockReply>

/** Build an axios adapter that answers through `handler` and rejects non-2xx like the real adapters. */
export function createMockAdapter(handler: MockHandler): AxiosAdapter {
  return async (config) => {
    const reply = await handler(config)
    const response: AxiosResponse = {
      data: reply.data,
      status: reply.status,
      statusText: String(reply.status),
      headers: new AxiosHeaders(reply.headers ?? {}),
      config,
      request: {},
    }
    if (reply.status >= 200 && reply.status < 300) return response
    throw new AxiosError(`Request failed with status code ${reply.status}`, AxiosError.ERR_BAD_REQUEST, config, {}, response)
  }
}

export function ok<T>(data: T, extra: { pagination?: ApiPagination | null; status?: number } = {}): MockReply {
  const envelope: ApiEnvelope<T> = {
    metaData: {
      status: true,
      responseCode: extra.status ?? 200,
      message: 'Success',
      executionTime: 1,
      requestId: 'req-ok',
      pagination: extra.pagination ?? null,
    },
    data,
  }
  return { status: extra.status ?? 200, data: envelope }
}

export function fail(status: number, message: string, errorCode: string, data: unknown = null, requestId = 'req-err'): MockReply {
  return {
    status,
    data: { metaData: { status: false, responseCode: status, message, errorCode, executionTime: 1, requestId }, data },
    headers: { 'x-request-id': requestId },
  }
}

/** Path of a request relative to the API base URL. */
export const pathOf = (config: InternalAxiosRequestConfig) => (config.url ?? '').split('?')[0]
