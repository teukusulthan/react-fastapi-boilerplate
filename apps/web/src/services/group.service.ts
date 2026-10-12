import type { Group, JsonObject } from '@/types/models'

import { API_ENDPOINTS } from './api-endpoints'
import { createResourceService } from './api-factory-crud.service'

/** `POST /group/add` (admin). */
export interface IGroupCreatePayload {
  name: string
  description?: string | null
  parentId?: string | null
  settings?: JsonObject | null
  filters?: JsonObject[] | null
  image?: string | null
  personalization?: JsonObject | null
}

/** `PUT /group/update` (admin). PATCH semantics. */
export interface IGroupUpdatePayload extends Partial<IGroupCreatePayload> {
  id: string
}

/** `/group/*` — reads: any signed-in user; writes: admin. */
export const groupService = createResourceService<Group, IGroupCreatePayload, IGroupUpdatePayload>(API_ENDPOINTS.GROUP.BASE)
