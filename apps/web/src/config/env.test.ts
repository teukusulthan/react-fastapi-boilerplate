import { describe, expect, it } from 'vitest'

import { parseEnv } from './env'

describe('parseEnv', () => {
  it('applies defaults when nothing is set', () => {
    const env = parseEnv({})
    expect(env.api.baseUrl).toBe('/api/v1/apps')
    expect(env.app.name).toBe('App')
    expect(env.app.description).toBe('')
    expect(env.map.mapboxToken).toBe('')
    expect(env.app.isDev).toBe(false)
  })

  it('treats empty / whitespace values as unset', () => {
    const env = parseEnv({ VITE_API_BASE_URL: '', VITE_APP_NAME: '   ' })
    expect(env.api.baseUrl).toBe('/api/v1/apps')
    expect(env.app.name).toBe('App')
  })

  it('accepts relative paths and absolute URLs, stripping trailing slashes', () => {
    expect(parseEnv({ VITE_API_BASE_URL: '/api/' }).api.baseUrl).toBe('/api')
    expect(parseEnv({ VITE_API_BASE_URL: 'https://api.example.com/v1/' }).api.baseUrl).toBe('https://api.example.com/v1')
    expect(parseEnv({ VITE_API_BASE_URL: '/' }).api.baseUrl).toBe('/')
  })

  it('maps Vite built-ins', () => {
    const env = parseEnv({ MODE: 'production', DEV: false, PROD: true, VITE_APP_NAME: 'Console' })
    expect(env.app).toMatchObject({ name: 'Console', mode: 'production', isProd: true, isDev: false })
  })

  it('rejects an invalid API base URL with a readable message', () => {
    expect(() => parseEnv({ VITE_API_BASE_URL: 'api.example.com' })).toThrow(/VITE_API_BASE_URL/)
    expect(() => parseEnv({ VITE_API_BASE_URL: 'ftp://example.com' })).toThrow(/Invalid environment configuration/)
  })
})
