import type { Role } from '@/types/models'

import { API_ENDPOINTS } from './api-endpoints'
import { createResourceService } from './api-factory-crud.service'

/** `POST /role/add` (admin). */
export interface IRoleCreatePayload {
  name: string
  alias?: string | null
  description?: string | null
  rolePosition?: number | null
  type?: string | null
  parentId?: string | null
  workspaceId?: string | null
  organizationId?: string | null
}

/** `PUT /role/update` (admin). PATCH semantics. */
export interface IRoleUpdatePayload extends Partial<IRoleCreatePayload> {
  id: string
}

/** `/role/*` — reads: any signed-in user; writes: admin. */
export const roleService = createResourceService<Role, IRoleCreatePayload, IRoleUpdatePayload>(API_ENDPOINTS.ROLE.BASE)
