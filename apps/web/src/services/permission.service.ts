import type { Permission } from '@/types/models'

import { API_ENDPOINTS } from './api-endpoints'
import { createResourceService } from './api-factory-crud.service'
import { apiRequests } from './api-factory.service'

/** `POST /permission/add` (admin). `alias` is the role name users get (`admin`, `user`, …). */
export interface IPermissionCreatePayload {
  name: string
  /** Lowercase `[a-z0-9_-]`, unique. */
  alias?: string | null
  description?: string | null
  type?: string | null
  privileges?: string[]
  parentId?: string | null
  image?: string | null
}

/** `PUT /permission/update` (admin). PATCH semantics. */
export interface IPermissionUpdatePayload extends Partial<IPermissionCreatePayload> {
  id: string
}

/** `PUT /permission/update-partial` (admin): add/remove individual privileges. */
export interface IPermissionPrivilegesPayload {
  id: string
  addPrivileges?: string[]
  removePrivileges?: string[]
}

const crud = createResourceService<Permission, IPermissionCreatePayload, IPermissionUpdatePayload>(API_ENDPOINTS.PERMISSION.BASE)

/** `/permission/*` — reads: any signed-in user; writes: admin. */
export const permissionService = {
  ...crud,

  updatePrivileges: (data: IPermissionPrivilegesPayload) =>
    apiRequests.put<Permission, IPermissionPrivilegesPayload>(API_ENDPOINTS.PERMISSION.UPDATE_PARTIAL, data),
}
