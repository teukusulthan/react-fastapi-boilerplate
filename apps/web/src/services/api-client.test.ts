import { AxiosError } from 'axios'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { useAuthStore } from '@/stores/useAuthStore'
import { createMockAdapter, fail, ok, pathOf, type MockHandler } from '@/test/axios-mock'
import type { UserProfile } from '@/types/models'

import apiClient, { __resetAuthRefreshStateForTests, endpointPath } from './api-client'
import { API_ENDPOINTS } from './api-endpoints'
import { ApiError } from './api-error'
import { apiRequests } from './api-factory.service'

const originalAdapter = apiClient.defaults.adapter

const USER = { id: 'u1', username: 'jane', fullname: 'Jane Doe', role: 'user' } as UserProfile

function useHandler(handler: MockHandler) {
  apiClient.defaults.adapter = createMockAdapter(handler)
}

async function catchError(promise: Promise<unknown>): Promise<ApiError> {
  try {
    await promise
  } catch (error) {
    return error as ApiError
  }
  throw new Error('expected promise to reject')
}

beforeEach(() => {
  __resetAuthRefreshStateForTests()
  useAuthStore.setState({ status: 'authenticated', user: USER, endReason: null })
})

afterEach(() => {
  apiClient.defaults.adapter = originalAdapter
})

describe('apiClient configuration', () => {
  it('uses the env base URL and sends cookies', () => {
    expect(apiClient.defaults.baseURL).toBe('/api/v1/apps')
    expect(apiClient.defaults.withCredentials).toBe(true)
  })

  it('normalizes request paths relative to the base URL', () => {
    expect(endpointPath('/auth/login?x=1')).toBe('/auth/login')
    expect(endpointPath('auth/login')).toBe('/auth/login')
    expect(endpointPath('http://host/api/v1/apps/auth/refresh', '/api/v1/apps')).toBe('/auth/refresh')
  })
})

describe('response envelope handling', () => {
  it('resolves with unwrapped data', async () => {
    useHandler(() => ok({ id: 'x' }))
    await expect(apiRequests.get('/thing/get-one', { id: 'x' })).resolves.toEqual({ id: 'x' })
  })

  it('normalizes an error envelope into ApiError', async () => {
    useHandler(() => fail(404, 'User not found', 'RESOURCE_NOT_FOUND', null, 'req-404'))
    const error = await catchError(apiRequests.get('/user/get-one', { id: 'missing' }))
    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 404, code: 'RESOURCE_NOT_FOUND', message: 'User not found', requestId: 'req-404', details: null })
  })

  it('exposes 422 field errors', async () => {
    useHandler(() => fail(422, 'Validation failed', 'VALIDATION_ERROR', [{ field: 'email', message: 'Invalid email' }]))
    const error = await catchError(apiRequests.post('/user/add', {}))
    expect(error.status).toBe(422)
    expect(error.fieldErrors).toEqual([{ field: 'email', message: 'Invalid email' }])
  })

  it('maps non-envelope error bodies (e.g. proxy HTML) to a generic message', async () => {
    useHandler(() => ({ status: 502, data: '<html>Bad gateway</html>', headers: { 'x-request-id': 'req-proxy' } }))
    const error = await catchError(apiRequests.get('/thing'))
    expect(error).toMatchObject({ status: 502, code: 'INTERNAL_ERROR', requestId: 'req-proxy' })
    expect(error.message).toMatch(/unavailable/i)
  })

  it('rejects 2xx responses that are not an envelope (e.g. SPA fallback HTML)', async () => {
    useHandler(() => ({ status: 200, data: '<!doctype html>' }))
    const error = await catchError(apiRequests.get('/thing'))
    expect(error).toMatchObject({ status: 200, code: 'INVALID_RESPONSE' })
  })

  it('rejects 2xx envelopes with metaData.status=false', async () => {
    useHandler(() => ({
      status: 200,
      data: { metaData: { status: false, responseCode: 409, message: 'Email already used', errorCode: 'CONFLICT', executionTime: 1 }, data: null },
    }))
    const error = await catchError(apiRequests.post('/user/add', {}))
    expect(error).toMatchObject({ status: 409, code: 'CONFLICT', message: 'Email already used' })
  })

  it('maps network errors and timeouts to client codes', async () => {
    useHandler((config) => {
      throw new AxiosError('Network Error', AxiosError.ERR_NETWORK, config, {})
    })
    expect(await catchError(apiRequests.get('/thing'))).toMatchObject({ status: 0, code: 'NETWORK_ERROR' })

    useHandler((config) => {
      throw new AxiosError('timeout of 30000ms exceeded', AxiosError.ECONNABORTED, config, {})
    })
    expect(await catchError(apiRequests.get('/thing'))).toMatchObject({ status: 0, code: 'TIMEOUT' })
  })
})

describe('401 → refresh → retry', () => {
  it('refreshes once for concurrent 401s and retries every request', async () => {
    let refreshed = false
    let refreshCalls = 0
    const calls: Record<string, number> = {}

    useHandler(async (config) => {
      const path = pathOf(config)
      calls[path] = (calls[path] ?? 0) + 1
      if (path === API_ENDPOINTS.AUTH.REFRESH) {
        refreshCalls += 1
        await new Promise((resolve) => setTimeout(resolve, 10))
        refreshed = true
        return ok({ auth: {} })
      }
      return refreshed ? ok({ path }) : fail(401, 'Token expired', 'AUTHENTICATION_ERROR')
    })

    const results = await Promise.all([apiRequests.get('/a'), apiRequests.get('/b'), apiRequests.post('/c', { x: 1 })])

    expect(results).toEqual([{ path: '/a' }, { path: '/b' }, { path: '/c' }])
    expect(refreshCalls).toBe(1)
    expect(calls).toMatchObject({ '/a': 2, '/b': 2, '/c': 2 })
    expect(useAuthStore.getState().status).toBe('authenticated')
  })

  it('replays a late 401 without refreshing again when a refresh already happened', async () => {
    let refreshCalls = 0
    let generation = 0
    useHandler(async (config) => {
      const path = pathOf(config)
      if (path === API_ENDPOINTS.AUTH.REFRESH) {
        refreshCalls += 1
        generation += 1
        return ok({})
      }
      if (path === '/slow' && generation === 0) {
        // responds 401 only after the refresh triggered by /fast completed
        await new Promise((resolve) => setTimeout(resolve, 20))
        return fail(401, 'Token expired', 'AUTHENTICATION_ERROR')
      }
      return generation > 0 ? ok({ path }) : fail(401, 'Token expired', 'AUTHENTICATION_ERROR')
    })

    const [slow, fast] = await Promise.all([apiRequests.get('/slow'), apiRequests.get('/fast')])
    expect(fast).toEqual({ path: '/fast' })
    expect(slow).toEqual({ path: '/slow' })
    expect(refreshCalls).toBe(1)
  })

  it('ends the session when the refresh is rejected', async () => {
    useHandler((config) =>
      pathOf(config) === API_ENDPOINTS.AUTH.REFRESH
        ? fail(401, 'Refresh token expired', 'AUTHENTICATION_ERROR')
        : fail(401, 'Token expired', 'AUTHENTICATION_ERROR'),
    )

    const error = await catchError(apiRequests.get('/user/get-one', { id: '1' }))
    expect(error.status).toBe(401)
    expect(useAuthStore.getState()).toMatchObject({ status: 'anonymous', user: null, endReason: 'expired' })
  })

  it('keeps the session when the refresh fails for a transient reason', async () => {
    useHandler((config) => {
      if (pathOf(config) === API_ENDPOINTS.AUTH.REFRESH) throw new AxiosError('Network Error', AxiosError.ERR_NETWORK, config, {})
      return fail(401, 'Token expired', 'AUTHENTICATION_ERROR')
    })

    const error = await catchError(apiRequests.get('/thing'))
    expect(error.code).toBe('NETWORK_ERROR')
    expect(useAuthStore.getState().status).toBe('authenticated')
  })

  it.each([
    API_ENDPOINTS.AUTH.LOGIN,
    API_ENDPOINTS.AUTH.LOGOUT,
    API_ENDPOINTS.AUTH.REFRESH,
    API_ENDPOINTS.AUTH.TWO_FACTOR_VERIFY,
    API_ENDPOINTS.AUTH.VERIFY_EMAIL,
  ])('never refreshes for %s', async (endpoint) => {
    let refreshCalls = 0
    useHandler((config) => {
      if (pathOf(config) === API_ENDPOINTS.AUTH.REFRESH) refreshCalls += 1
      return fail(401, 'Invalid credentials', 'AUTHENTICATION_ERROR')
    })

    const error = await catchError(apiRequests.post(endpoint, {}))
    expect(error).toMatchObject({ status: 401, message: 'Invalid credentials' })
    expect(refreshCalls).toBe(endpoint === API_ENDPOINTS.AUTH.REFRESH ? 1 : 0)
    expect(useAuthStore.getState().status).toBe('authenticated')
  })
})
