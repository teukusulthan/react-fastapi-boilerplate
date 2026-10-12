import type { StatusTone } from '@/components/common/StatusBadge'
import type { DataTableSort } from '@/modules/data-table'
import type { UserStatus } from '@/types/models'

export const USER_QUERY_KEYS = {
  all: ['users'] as const,
  list: (query: object) => ['users', 'list', query] as const,
}

export const USER_STATUS_META: Record<UserStatus, { label: string; tone: StatusTone }> = {
  active: { label: 'Active', tone: 'success' },
  pending: { label: 'Pending', tone: 'warning' },
  blocked: { label: 'Blocked', tone: 'destructive' },
  deleted: { label: 'Deleted', tone: 'neutral' },
}

/** Status filter options; `all` = no filter. */
export const USER_STATUS_FILTER_ALL = 'all'
export const USER_STATUS_FILTER_OPTIONS: readonly { value: UserStatus | typeof USER_STATUS_FILTER_ALL; label: string }[] = [
  { value: USER_STATUS_FILTER_ALL, label: 'All statuses' },
  { value: 'active', label: 'Active' },
  { value: 'pending', label: 'Pending' },
  { value: 'blocked', label: 'Blocked' },
  { value: 'deleted', label: 'Deleted' },
]

/** Statuses an admin can pick when creating a user. */
export const USER_CREATE_STATUS_OPTIONS: readonly { value: UserStatus; label: string; description: string }[] = [
  { value: 'active', label: 'Active', description: 'Can sign in right away.' },
  { value: 'pending', label: 'Pending', description: 'Must verify their email first.' },
]

export const USER_LIST_PAGE_SIZE = 10

/** Backend default order of POST /user/get-all. */
export const USER_DEFAULT_SORT: DataTableSort = { orderBy: 'createdAt', order: 'desc' }

/** Searchable user fields (backend whitelist: username, fullname, email, phone). */
export const USER_SEARCH_FIELDS = ['username', 'fullname', 'email'] as const

/** Create-user form fields that can receive backend 422 field errors. */
export const USER_CREATE_FIELDS = ['fullname', 'username', 'email', 'password', 'status'] as const

export const PASSWORD_MIN_LENGTH = 8
