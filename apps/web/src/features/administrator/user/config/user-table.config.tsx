import type { ColumnDef } from '@tanstack/react-table'

import { RelativeTime } from '@/components/common/RelativeTime'
import { Skeleton } from '@/components/ui/skeleton'
import { DataTableColumnHeader, type DataTableColumnMeta } from '@/modules/data-table'
import type { UserDetail } from '@/types/models'
import { formatDate } from '@/utils/date-formatter'

import { UserIdentityCell } from '../components/UserIdentityCell'
import { UserRowActions } from '../components/UserRowActions'
import { UserStatusBadge } from '../components/UserStatusBadge'

const meta = (value: DataTableColumnMeta) => value

/**
 * Columns of the admin user list. Column ids of sortable columns are the backend sortable field names
 * (camelCase) — they become `orderBy` in the FindDTO.
 */
export function getUserColumns(currentUserId: string | undefined): ColumnDef<UserDetail, unknown>[] {
  return [
    {
      id: 'fullname',
      accessorKey: 'fullname',
      enableSorting: true,
      header: ({ column }) => <DataTableColumnHeader column={column} title="User" />,
      cell: ({ row }) => <UserIdentityCell user={row.original} isCurrentUser={row.original.id === currentUserId} />,
      meta: meta({
        className: 'min-w-64',
        skeleton: (
          <div className="flex items-center gap-3">
            <Skeleton className="size-8 rounded-full" />
            <div className="flex flex-col gap-1.5">
              <Skeleton className="h-3.5 w-28" />
              <Skeleton className="h-3 w-40" />
            </div>
          </div>
        ),
      }),
    },
    {
      id: 'role',
      accessorKey: 'role',
      header: 'Role',
      cell: ({ row }) => (row.original.role ? <span className="capitalize">{row.original.role}</span> : <span className="text-muted-foreground">No role</span>),
      meta: meta({ skeletonClassName: 'w-16' }),
    },
    {
      id: 'status',
      accessorKey: 'status',
      enableSorting: true,
      header: ({ column }) => <DataTableColumnHeader column={column} title="Status" />,
      cell: ({ row }) => <UserStatusBadge status={row.original.status} />,
      meta: meta({ skeletonClassName: 'h-5 w-16' }),
    },
    {
      id: 'twoFactorEnabled',
      accessorKey: 'twoFactorEnabled',
      header: '2FA',
      cell: ({ row }) =>
        row.original.twoFactorEnabled ? (
          <span className="inline-flex items-center gap-1.5 text-foreground">
            <i className="ph ph-shield-check text-success" aria-hidden="true" />
            On
          </span>
        ) : (
          <span className="inline-flex items-center gap-1.5 text-muted-foreground">
            <i className="ph ph-shield-slash" aria-hidden="true" />
            Off
          </span>
        ),
      meta: meta({ skeletonClassName: 'w-10' }),
    },
    {
      id: 'lastLoginAt',
      accessorKey: 'lastLoginAt',
      enableSorting: true,
      header: ({ column }) => <DataTableColumnHeader column={column} title="Last sign-in" />,
      cell: ({ row }) => <RelativeTime value={row.original.lastLoginAt} />,
      meta: meta({ skeletonClassName: 'w-20' }),
    },
    {
      id: 'createdAt',
      accessorKey: 'createdAt',
      enableSorting: true,
      header: ({ column }) => <DataTableColumnHeader column={column} title="Created" />,
      cell: ({ row }) => <span className="text-muted-foreground tabular-nums">{formatDate(row.original.createdAt)}</span>,
      meta: meta({ skeletonClassName: 'w-20' }),
    },
    {
      id: 'actions',
      header: () => <span className="sr-only">Actions</span>,
      cell: ({ row }) => <UserRowActions user={row.original} />,
      meta: meta({ className: 'w-12 text-right', skeletonClassName: 'ml-auto size-6' }),
    },
  ]
}
