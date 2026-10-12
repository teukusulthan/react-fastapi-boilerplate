import type { ApiList, FindDTO } from '@/types/api'

import { apiRequests } from './api-factory.service'

export interface IIdParams {
  id: string
}

/**
 * Standard CRUD contract shared by every backend module:
 *
 * | add     | POST   {base}/add           | JSON body          | 201 → T            |
 * | update  | PUT    {base}/update        | JSON body with id  | T                  |
 * | delete  | DELETE {base}/delete?id=    | query param        | —                  |
 * | getOne  | GET    {base}/get-one?id=   | query param        | T                  |
 * | getAll  | POST   {base}/get-all       | FindDTO body       | { items, pagination } |
 */
export interface IResourceService<T, TCreate, TUpdate extends IIdParams> {
  add: (data: TCreate) => Promise<T>
  update: (data: TUpdate) => Promise<T>
  delete: (params: IIdParams) => Promise<void>
  getOne: (params: IIdParams) => Promise<T>
  getAll: (query?: FindDTO) => Promise<ApiList<T>>
}

export function createResourceService<T, TCreate = Partial<T>, TUpdate extends IIdParams = Partial<TCreate> & IIdParams>(
  basePath: string,
): IResourceService<T, TCreate, TUpdate> {
  const base = basePath.replace(/\/+$/, '')
  return {
    add: (data) => apiRequests.post<T, TCreate>(`${base}/add`, data),
    update: (data) => apiRequests.put<T, TUpdate>(`${base}/update`, data),
    delete: ({ id }) => apiRequests.delete<unknown>(`${base}/delete`, { id }).then(() => undefined),
    getOne: ({ id }) => apiRequests.get<T>(`${base}/get-one`, { id }),
    getAll: (query = {}) => apiRequests.list<T>(`${base}/get-all`, query),
  }
}
