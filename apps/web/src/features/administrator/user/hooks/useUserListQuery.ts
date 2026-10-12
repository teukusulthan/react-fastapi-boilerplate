import { useMemo, useState } from 'react'

import { useDebouncedValue } from '@/hooks/use-debounced-value'
import type { DataTableSort } from '@/modules/data-table'
import type { FindDTO } from '@/types/api'
import type { UserStatus } from '@/types/models'

import { USER_DEFAULT_SORT, USER_LIST_PAGE_SIZE, USER_SEARCH_FIELDS, USER_STATUS_FILTER_ALL } from '../constants/user.constants'

export type UserStatusFilter = UserStatus | typeof USER_STATUS_FILTER_ALL

/** Search + status filter + sorting + pagination state for the user list, as a memoized FindDTO. */
export function useUserListQuery() {
  const [search, setSearchValue] = useState('')
  const [status, setStatusValue] = useState<UserStatusFilter>(USER_STATUS_FILTER_ALL)
  const [sort, setSortValue] = useState<DataTableSort | null>(null)
  const [page, setPage] = useState(1)
  const [size, setSizeValue] = useState(USER_LIST_PAGE_SIZE)
  const debouncedSearch = useDebouncedValue(search.trim(), 300)

  const query = useMemo<FindDTO>(() => {
    const effectiveSort = sort ?? USER_DEFAULT_SORT
    return {
      page,
      size,
      orderBy: effectiveSort.orderBy,
      order: effectiveSort.order,
      ...(debouncedSearch ? { search: debouncedSearch, searchBy: [...USER_SEARCH_FIELDS] } : {}),
      ...(status !== USER_STATUS_FILTER_ALL ? { filters: [{ field: 'status', operator: 'is' as const, value: { is: status } }] } : {}),
    }
  }, [page, size, sort, debouncedSearch, status])

  const resetPage =
    <T>(setter: (value: T) => void) =>
    (value: T) => {
      setter(value)
      setPage(1)
    }

  const isFiltered = debouncedSearch !== '' || status !== USER_STATUS_FILTER_ALL

  return {
    query,
    search,
    setSearch: resetPage(setSearchValue),
    status,
    setStatus: resetPage(setStatusValue),
    sort,
    setSort: resetPage(setSortValue),
    setPage,
    setPageSize: resetPage(setSizeValue),
    isFiltered,
    clearFilters: () => {
      setSearchValue('')
      setStatusValue(USER_STATUS_FILTER_ALL)
      setPage(1)
    },
  }
}
