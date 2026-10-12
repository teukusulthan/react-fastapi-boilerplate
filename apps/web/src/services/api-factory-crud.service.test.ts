import type { InternalAxiosRequestConfig } from 'axios'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { createMockAdapter, ok, type MockReply } from '@/test/axios-mock'
import type { FindDTO } from '@/types/api'

import apiClient from './api-client'
import { createResourceService } from './api-factory-crud.service'

interface Widget {
  id: string
  name: string
}

const originalAdapter = apiClient.defaults.adapter
let requests: InternalAxiosRequestConfig[] = []
let reply: MockReply = ok(null)

beforeEach(() => {
  requests = []
  apiClient.defaults.adapter = createMockAdapter((config) => {
    requests.push(config)
    return reply
  })
})

afterEach(() => {
  apiClient.defaults.adapter = originalAdapter
})

const widgets = createResourceService<Widget, { name: string }, { id: string; name?: string }>('/widget/')

const lastRequest = () => {
  const request = requests.at(-1)
  if (!request) throw new Error('no request captured')
  return {
    method: request.method?.toUpperCase(),
    url: request.url,
    params: request.params,
    body: request.data ? JSON.parse(request.data as string) : undefined,
  }
}

describe('createResourceService', () => {
  it('add → POST {base}/add with JSON body', async () => {
    reply = ok({ id: '1', name: 'A' }, { status: 201 })
    await expect(widgets.add({ name: 'A' })).resolves.toEqual({ id: '1', name: 'A' })
    expect(lastRequest()).toEqual({ method: 'POST', url: '/widget/add', params: undefined, body: { name: 'A' } })
  })

  it('update → PUT {base}/update with id in the body', async () => {
    reply = ok({ id: '1', name: 'B' })
    await widgets.update({ id: '1', name: 'B' })
    expect(lastRequest()).toEqual({ method: 'PUT', url: '/widget/update', params: undefined, body: { id: '1', name: 'B' } })
  })

  it('delete → DELETE {base}/delete?id=', async () => {
    reply = ok(null)
    await expect(widgets.delete({ id: '1' })).resolves.toBeUndefined()
    expect(lastRequest()).toMatchObject({ method: 'DELETE', url: '/widget/delete', params: { id: '1' } })
  })

  it('getOne → GET {base}/get-one?id=', async () => {
    reply = ok({ id: '1', name: 'A' })
    await expect(widgets.getOne({ id: '1' })).resolves.toEqual({ id: '1', name: 'A' })
    expect(lastRequest()).toMatchObject({ method: 'GET', url: '/widget/get-one', params: { id: '1' } })
  })

  it('getAll → POST {base}/get-all with FindDTO and returns { items, pagination }', async () => {
    const pagination = { page: 2, size: 10, totalElements: 11, totalPages: 2 }
    reply = ok([{ id: '11', name: 'K' }], { pagination })
    const query: FindDTO = {
      page: 2,
      size: 10,
      search: 'k',
      searchBy: ['name'],
      orderBy: 'createdAt',
      order: 'desc',
      filters: [
        { field: 'status', operator: 'is one of', value: { isOneOf: ['active', 'pending'] } },
        { field: 'createdAt', operator: 'is between', value: { gte: '2026-01-01T00:00:00Z', lte: '2026-12-31T23:59:59Z' } },
      ],
    }

    await expect(widgets.getAll(query)).resolves.toEqual({ items: [{ id: '11', name: 'K' }], pagination })
    expect(lastRequest()).toEqual({ method: 'POST', url: '/widget/get-all', params: undefined, body: query })
  })

  it('getAll defaults to an empty FindDTO and synthesizes pagination when absent', async () => {
    reply = ok([{ id: '1', name: 'A' }])
    await expect(widgets.getAll()).resolves.toEqual({
      items: [{ id: '1', name: 'A' }],
      pagination: { page: 1, size: 1, totalElements: 1, totalPages: 1 },
    })
    expect(lastRequest().body).toEqual({})
  })

  it('getAll rejects when data is not an array', async () => {
    reply = ok({ not: 'a list' })
    await expect(widgets.getAll()).rejects.toMatchObject({ code: 'INVALID_RESPONSE' })
  })
})
