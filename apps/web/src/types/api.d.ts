/**
 * Backend response envelope (see backend contract). Every endpoint — success or error — returns
 * `{ metaData, data }`. Services unwrap it; components only ever see `T` or `ApiList<T>`.
 */

export interface ApiPagination {
  page: number
  size: number
  totalElements: number
  totalPages: number
}

/** Known `metaData.errorCode` values. The backend may add more — treat unknown codes as generic errors. */
export type ApiErrorCode =
  | 'VALIDATION_ERROR'
  | 'AUTHENTICATION_ERROR'
  | 'PERMISSION_ERROR'
  | 'RESOURCE_NOT_FOUND'
  | 'CONFLICT'
  | 'RATE_LIMITED'
  | 'BAD_REQUEST'
  | 'CONFIGURATION_ERROR'
  | 'SERVICE_UNAVAILABLE'
  | 'METHOD_NOT_ALLOWED'
  | 'PAYLOAD_TOO_LARGE'
  | 'UNSUPPORTED_MEDIA_TYPE'
  | 'INTERNAL_ERROR'
  /** 401 from `POST /auth/login`: correct password but the email address is not verified yet. */
  | 'ACCOUNT_NOT_VERIFIED'

/** Client-side codes produced by the API layer when there is no usable server envelope. */
export type ClientErrorCode = 'NETWORK_ERROR' | 'TIMEOUT' | 'REQUEST_CANCELLED' | 'INVALID_RESPONSE' | 'UNKNOWN_ERROR'

export interface ApiMetaData {
  status: boolean
  responseCode: number
  message: string
  executionTime: number
  requestId?: string | null
  /** Present on list (`get-all`) responses, null otherwise. */
  pagination?: ApiPagination | null
  /** Present on error responses only. */
  errorCode?: ApiErrorCode | (string & Record<never, never>) | null
}

export interface ApiEnvelope<T> {
  metaData: ApiMetaData
  data: T
}

/** 422 validation details: `data = [{ field, message }]`. */
export interface ApiFieldError {
  field: string
  message: string
}

/** Unwrapped list result returned by services for every `get-all`. */
export interface ApiList<T> {
  items: T[]
  pagination: ApiPagination
}

/* ── List query (`FindDTO`, body of every POST /x/get-all) ─────────────────── */

export type SortOrder = 'asc' | 'desc'

/** Legacy operator vocabulary accepted by the backend filter parser. */
export type FilterOperator =
  | 'is'
  | 'is not'
  | 'is one of'
  | 'is not one of'
  | 'greater than equals'
  | 'less than equals'
  | 'is between'
  | 'is not between'
  | 'is exist'
  | 'is not exist'
  | 'is contains'
  | 'is not contains'
  | 'all'

/** Filter values are scalars or lists of scalars only (objects are rejected by the backend). */
export type FilterScalar = string | number | boolean | null

export interface FilterValue {
  is?: FilterScalar
  isOneOf?: FilterScalar[]
  gte?: FilterScalar
  lte?: FilterScalar
}

export interface FilterItem {
  /** camelCase API field name; must be in the resource's filterable whitelist (unknown → 422). */
  field: string
  operator: FilterOperator
  /** Omit for `is exist` / `is not exist`. */
  value?: FilterValue
  /** How this filter combines with the others (default `and`). */
  operatorType?: 'and' | 'or'
}

export interface FindDTO {
  /** >= 1, default 1 */
  page?: number
  /** 1..BE_MAX_PAGE_SIZE (default 10, max 100) */
  size?: number
  search?: string
  /** Restrict search to these (whitelisted) fields; backend default when omitted. */
  searchBy?: string[]
  /** Whitelisted sortable field; backend default `createdAt`. */
  orderBy?: string
  /** Default `desc`. */
  order?: SortOrder
  filters?: FilterItem[]
}
