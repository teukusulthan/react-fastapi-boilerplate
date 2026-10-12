/**
 * Global entity types shared across domains (camelCase, as serialized by the backend).
 * Field-by-field mirrors of the backend response DTOs (`apps/backend/dto/*.py`); timestamps are
 * ISO-8601 UTC strings.
 */

export type UserStatus = 'pending' | 'active' | 'blocked' | 'deleted'

export type AuthProvider = 'local' | 'google' | 'supabase'

export type TwoFactorMethod = 'email' | 'totp'

/** Free-form JSON object columns (settings, personalization, …). */
export type JsonObject = Record<string, unknown>

/** `dto/user_profile.py::PermissionSummary` */
export interface PermissionSummary {
  id: string
  name: string
  alias: string | null
  privileges: string[]
}

/** `dto/user_profile.py::GroupSummary` */
export interface GroupSummary {
  id: string
  name: string
}

/**
 * `dto/user_profile.py::UserProfile` — `GET /auth/me`, login responses.
 * Never contains password / 2FA secrets.
 */
export interface UserProfile {
  id: string
  username: string
  fullname: string | null
  email: string
  phone: string | null
  status: UserStatus
  emailVerified: boolean
  twoFactorEnabled: boolean
  /** Permission alias (e.g. "admin", "user") or null. */
  role: string | null
  permissionId: string | null
  permission: PermissionSummary | null
  groupId: string | null
  group: GroupSummary | null
  lastLoginAt: string | null
  createdAt: string | null
  updatedAt: string | null
}

/** `dto/user_profile.py::UserResponse` — admin view (`/user/*`, `PUT /user/settings/update-profile`). */
export interface UserDetail extends UserProfile {
  about: string | null
  image: string | null
  multiLogin: boolean
  expiredAt: string | null
  twoFactorMethod: TwoFactorMethod | null
  authProvider: AuthProvider | null
  settings: JsonObject | null
  personalization: JsonObject | null
  additional: JsonObject | null
  createdBy: string | null
}

/** `dto/user.py::CheckAvailabilityResponse` — `GET /user/check-{email,username,phone}`. */
export interface AvailabilityCheck {
  field: 'email' | 'username' | 'phone'
  /** Already taken. */
  exists: boolean
  available: boolean
}

/** `dto/permission.py::PermissionResponse` */
export interface Permission {
  id: string
  name: string
  alias: string | null
  description: string | null
  type: string | null
  privileges: string[]
  parentId: string | null
  image: string | null
  createdBy: string | null
  createdAt: string
  updatedAt: string
}

/** `dto/group.py::GroupResponse` */
export interface Group {
  id: string
  name: string
  description: string | null
  parentId: string | null
  settings: JsonObject | null
  /** Saved filter presets (free-form JSON objects). */
  filters: JsonObject[] | null
  image: string | null
  personalization: JsonObject | null
  createdBy: string | null
  createdAt: string
  updatedAt: string
}

/** `dto/role.py::RoleResponse` */
export interface Role {
  id: string
  name: string
  alias: string | null
  description: string | null
  rolePosition: number | null
  type: string | null
  parentId: string | null
  workspaceId: string | null
  organizationId: string | null
  createdBy: string | null
  createdAt: string
  updatedAt: string
}

/** `dto/upload.py::UploadResponse` */
export interface Upload {
  id: string
  objectKey: string
  filename: string
  mimeType: string | null
  filesize: number | null
  folder: string | null
  tags: string[]
  widgetId: string | null
  dashboardId: string | null
  workspaceId: string | null
  connectionId: string | null
  createdBy: string | null
  createdAt: string
  updatedAt: string
  /** Only on `get-one` / `upload-file`: short-lived presigned download URL. */
  downloadUrl: string | null
}
