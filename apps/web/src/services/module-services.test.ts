import type { InternalAxiosRequestConfig } from 'axios'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { createMockAdapter, ok, type MockReply } from '@/test/axios-mock'

import apiClient from './api-client'
import { permissionService } from './permission.service'
import { buildUploadForm, uploadService } from './upload.service'
import { userService } from './user.service'

const originalAdapter = apiClient.defaults.adapter
let requests: InternalAxiosRequestConfig[] = []
let reply: MockReply = ok(null)

beforeEach(() => {
  requests = []
  reply = ok(null)
  apiClient.defaults.adapter = createMockAdapter((config) => {
    requests.push(config)
    return reply
  })
})

afterEach(() => {
  apiClient.defaults.adapter = originalAdapter
})

const last = () => {
  const request = requests.at(-1)
  if (!request) throw new Error('no request captured')
  return { method: request.method?.toUpperCase(), url: request.url, params: request.params, data: request.data }
}

describe('module services match the backend routes', () => {
  it('user extras', async () => {
    reply = ok({ field: 'email', exists: true, available: false })
    await expect(userService.checkEmail('a@b.co')).resolves.toEqual({ field: 'email', exists: true, available: false })
    expect(last()).toMatchObject({ method: 'GET', url: '/user/check-email', params: { email: 'a@b.co' } })

    await userService.getByUsername({ username: 'jane' })
    expect(last()).toMatchObject({ method: 'GET', url: '/user/get-by-username', params: { username: 'jane' } })

    await userService.resetPassword({ id: 'u1', newPassword: 'n3w-password' })
    expect(last()).toMatchObject({ method: 'POST', url: '/user/reset-password' })
    expect(JSON.parse(last().data as string)).toEqual({ id: 'u1', newPassword: 'n3w-password' })

    await userService.updateProfile({ fullname: 'Jane' })
    expect(last()).toMatchObject({ method: 'PUT', url: '/user/settings/update-profile' })
  })

  it('permission update-partial', async () => {
    await permissionService.updatePrivileges({ id: 'p1', addPrivileges: ['a:read'], removePrivileges: ['a:write'] })
    expect(last()).toMatchObject({ method: 'PUT', url: '/permission/update-partial' })
    expect(JSON.parse(last().data as string)).toEqual({ id: 'p1', addPrivileges: ['a:read'], removePrivileges: ['a:write'] })
  })

  it('upload uses multipart field `file` and camelCase text fields', async () => {
    const form = buildUploadForm(new File(['hi'], 'notes.txt', { type: 'text/plain' }), { folder: 'docs', tags: ['a', 'b'], rescaleFile: false })
    expect((form.get('file') as File).name).toBe('notes.txt')
    expect(form.get('folder')).toBe('docs')
    expect(form.get('tags')).toBe('a,b')
    expect(form.get('rescaleFile')).toBe('false')

    await uploadService.uploadFile(new Blob(['x']), { folder: 'f' })
    expect(last()).toMatchObject({ method: 'POST', url: '/upload/upload-file' })
    expect(last().data).toBeInstanceOf(FormData)

    await uploadService.delete({ id: 'up1' })
    expect(last()).toMatchObject({ method: 'DELETE', url: '/upload/delete', params: { id: 'up1' } })
  })
})
