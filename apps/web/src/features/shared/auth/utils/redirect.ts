import { LOGIN_PATH, REDIRECT_PARAM } from '@/config/constants'

const DEFAULT_REDIRECT = '/'

/**
 * Validate a post-login redirect target: same-origin absolute path only (prevents open redirects),
 * never back into /auth/*.
 */
export function getSafeRedirect(raw: string | null | undefined): string {
  if (!raw) return DEFAULT_REDIRECT
  const value = raw.trim()
  if (!value.startsWith('/') || value.startsWith('//') || value.startsWith('/\\')) return DEFAULT_REDIRECT
  if ([...value].some((char) => char.charCodeAt(0) < 0x20)) return DEFAULT_REDIRECT
  if (value === '/auth' || value.startsWith('/auth/') || value.startsWith('/auth?')) return DEFAULT_REDIRECT
  return value
}

/** `/auth/login?redirect=<current path>` (no param for "/" or when `target` is empty). */
export function buildLoginPath(target?: string | null): string {
  const safe = target ? getSafeRedirect(target) : DEFAULT_REDIRECT
  if (safe === DEFAULT_REDIRECT) return LOGIN_PATH
  return `${LOGIN_PATH}?${new URLSearchParams({ [REDIRECT_PARAM]: safe }).toString()}`
}
