import { useMemo } from 'react'

import { EmptyState } from '@/components/common/EmptyState'
import { PageHeader } from '@/components/common/PageHeader'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { DataTable, DataTableToolbar } from '@/modules/data-table'
import { getErrorMessage } from '@/services/api-error'
import { useAuthStore } from '@/stores/useAuthStore'

import { getUserColumns } from '../config/user-table.config'
import { USER_STATUS_FILTER_OPTIONS } from '../constants/user.constants'
import { useUserList } from '../hooks/useUserList'
import { useUserListQuery, type UserStatusFilter } from '../hooks/useUserListQuery'

import { CreateUserDialog } from './CreateUserDialog'

/** Admin user list: search, status filter, server sorting + pagination, row actions, create dialog. */
export function UserListView() {
  const currentUserId = useAuthStore((state) => state.user?.id)
  const { query, search, setSearch, status, setStatus, sort, setSort, setPage, setPageSize, isFiltered, clearFilters } = useUserListQuery()
  const { data, isPending, isError, error, refetch, isFetching, isPlaceholderData } = useUserList(query)
  const columns = useMemo(() => getUserColumns(currentUserId), [currentUserId])

  const total = data?.pagination.totalElements
  const description =
    total === undefined
      ? 'Manage who can sign in and what they can access.'
      : `${total} ${total === 1 ? 'account' : 'accounts'} · Manage who can sign in and what they can access.`

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Users" description={description} actions={<CreateUserDialog />} />

      <DataTable
        caption="Users"
        columns={columns}
        data={data?.items}
        getRowId={(row) => row.id}
        loading={isPending}
        fetching={isFetching && isPlaceholderData}
        pagination={data?.pagination}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
        sort={sort}
        onSortChange={setSort}
        toolbar={
          <DataTableToolbar
            searchValue={search}
            onSearchChange={setSearch}
            searchPlaceholder="Search name, username or email…"
            filters={
              <Select value={status} onValueChange={(value) => setStatus(value as UserStatusFilter)}>
                <SelectTrigger className="w-full sm:w-40" aria-label="Filter by status">
                  <i className="ph ph-funnel-simple text-muted-foreground" aria-hidden="true" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {USER_STATUS_FILTER_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            }
            actions={
              isFiltered ? (
                <Button variant="ghost" size="sm" onClick={clearFilters}>
                  Reset
                  <i className="ph ph-x" aria-hidden="true" />
                </Button>
              ) : null
            }
          />
        }
        error={
          isError ? (
            <Alert variant="destructive">
              <i className="ph ph-warning-circle" aria-hidden="true" />
              <AlertTitle>Couldn&apos;t load users</AlertTitle>
              <AlertDescription className="flex flex-wrap items-center justify-between gap-3">
                <span>{getErrorMessage(error)}</span>
                <Button variant="outline" size="sm" onClick={() => void refetch()}>
                  <i className="ph ph-arrow-clockwise" aria-hidden="true" />
                  Try again
                </Button>
              </AlertDescription>
            </Alert>
          ) : undefined
        }
        emptyState={
          isFiltered ? (
            <EmptyState
              icon="magnifying-glass"
              title="No matching users"
              description="Try a different search term or status."
              action={
                <Button variant="outline" onClick={clearFilters}>
                  Clear filters
                </Button>
              }
            />
          ) : (
            <EmptyState icon="users" title="No users yet" description="Create the first account to give someone access." action={<CreateUserDialog />} />
          )
        }
      />
    </div>
  )
}
