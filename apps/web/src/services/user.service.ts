import type { AvailabilityCheck, JsonObject, UserDetail, UserStatus } from '@/types/models'

import { API_ENDPOINTS } from './api-endpoints'
import { createResourceService } from './api-factory-crud.service'
import { apiRequests } from './api-factory.service'

/* ── Payloads (dto/user.py) — unknown fields are rejected with 422 ─────────── */

/** `POST /user/add` (admin). */
export interface IUserCreatePayload {
  username: string
  fullname: string
  email: string
  phone?: string | null
  /** Required with the local auth provider; must be omitted with `BE_AUTH_PROVIDER=supabase`. */
  password?: string
  permissionId?: string | null
  groupId?: string | null
  /** Default `active`. */
  status?: UserStatus
  emailVerified?: boolean
  multiLogin?: boolean
  expiredAt?: string | null
  about?: string | null
  image?: string | null
  settings?: JsonObject | null
  personalization?: JsonObject | null
  additional?: JsonObject | null
}

/**
 * `PUT /user/update` (admin). PATCH semantics: only the fields sent change; `null` clears an
 * optional field. Passwords change through `resetPassword`.
 */
export interface IUserUpdatePayload extends Partial<Omit<IUserCreatePayload, 'password' | 'username' | 'email' | 'status'>> {
  id: string
  username?: string
  email?: string
  status?: UserStatus
}

/** `POST /user/reset-password` (admin): sets a new password and revokes the user's sessions. */
export interface IUserResetPasswordPayload {
  id: string
  newPassword: string
}

/** `PUT /user/settings/update-profile` (any signed-in user, own profile only). */
export interface IUpdateProfilePayload {
  fullname?: string | null
  phone?: string | null
  about?: string | null
  image?: string | null
  settings?: JsonObject | null
  personalization?: JsonObject | null
}

/* ── Service ────────────────────────────────────────────────────────────────── */

const crud = createResourceService<UserDetail, IUserCreatePayload, IUserUpdatePayload>(API_ENDPOINTS.USER.BASE)

/** `/user/*` — admin only, except `updateProfile` (self-service). */
export const userService = {
  ...crud,

  getByUsername: ({ username }: { username: string }) => apiRequests.get<UserDetail>(API_ENDPOINTS.USER.GET_BY_USERNAME, { username }),

  resetPassword: (data: IUserResetPasswordPayload) => apiRequests.post<{ message: string }, IUserResetPasswordPayload>(API_ENDPOINTS.USER.RESET_PASSWORD, data),

  checkEmail: (email: string) => apiRequests.get<AvailabilityCheck>(API_ENDPOINTS.USER.CHECK_EMAIL, { email }),

  checkUsername: (username: string) => apiRequests.get<AvailabilityCheck>(API_ENDPOINTS.USER.CHECK_USERNAME, { username }),

  checkPhone: (phone: string) => apiRequests.get<AvailabilityCheck>(API_ENDPOINTS.USER.CHECK_PHONE, { phone }),

  updateProfile: (data: IUpdateProfilePayload) => apiRequests.put<UserDetail, IUpdateProfilePayload>(API_ENDPOINTS.USER.UPDATE_PROFILE, data),
}
