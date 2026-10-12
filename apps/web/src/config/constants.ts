/** Global, cross-domain constants. Domain constants live in their feature folder. */

/**
 * Permission aliases treated as superusers (mirror of backend `BE_SUPERUSER_ALIASES`, default "admin,owner").
 * Superusers pass every RoleGuard / privilege check on the client. The backend remains the authority.
 */
export const SUPERUSER_ROLES: readonly string[] = ['admin', 'owner']

/** Roles allowed into /administrator/* */
export const ADMIN_ROLES: readonly string[] = ['admin']

export const LOGIN_PATH = '/auth/login'

/** Query-string key carrying the post-login destination. */
export const REDIRECT_PARAM = 'redirect'

export const DEFAULT_PAGE_SIZE = 10
export const PAGE_SIZE_OPTIONS: readonly number[] = [10, 25, 50, 100]
