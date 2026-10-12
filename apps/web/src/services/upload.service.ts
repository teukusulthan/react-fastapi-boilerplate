import type { FindDTO } from '@/types/api'
import type { Upload } from '@/types/models'

import { API_ENDPOINTS } from './api-endpoints'
import type { IIdParams } from './api-factory-crud.service'
import { apiRequests } from './api-factory.service'

/** Metadata fields of `POST /upload/upload-file` (multipart; the file part is named `file`). */
export interface IUploadOptions {
  /** 1-5 segments of `[A-Za-z0-9_-]` separated by `/` (default `general`). */
  folder?: string
  /** Display name override (the extension comes from the detected content type). */
  filename?: string
  tags?: string[]
  widgetId?: string
  dashboardId?: string
  workspaceId?: string
  connectionId?: string
  /** Publish a Kafka extraction event after storing (backend must have Kafka configured). */
  extractFile?: boolean
  /** Images only: downscale (format preserved). */
  rescaleFile?: boolean
  /** With `rescaleFile`: 0 < factor <= 1. */
  scaleFactor?: number
}

/** Build the multipart body expected by the backend (`file` + camelCase text fields). */
export function buildUploadForm(file: Blob, options: IUploadOptions = {}, fileName?: string): FormData {
  const form = new FormData()
  form.append('file', file, fileName ?? (file instanceof File ? file.name : 'upload'))
  for (const [key, value] of Object.entries(options)) {
    if (value === undefined || value === null) continue
    form.append(key, Array.isArray(value) ? value.join(',') : String(value))
  }
  return form
}

/**
 * `/upload/*` — signed-in users (not internal tokens). Users see their own files, admins all.
 * Size limit and allowed types are enforced by the backend (413 / 415).
 */
export const uploadService = {
  uploadFile: (file: Blob, options?: IUploadOptions, onProgress?: (percent: number) => void) =>
    apiRequests.upload<Upload>(API_ENDPOINTS.UPLOAD.UPLOAD_FILE, buildUploadForm(file, options), onProgress),

  getAll: (query: FindDTO = {}) => apiRequests.list<Upload>(API_ENDPOINTS.UPLOAD.GET_ALL, query),

  /** Includes a short-lived `downloadUrl`. */
  getOne: ({ id }: IIdParams) => apiRequests.get<Upload>(API_ENDPOINTS.UPLOAD.GET_ONE, { id }),

  delete: ({ id }: IIdParams) => apiRequests.delete<unknown>(API_ENDPOINTS.UPLOAD.DELETE, { id }).then(() => undefined),
}
