import type { ColumnDef } from '@tanstack/react-table'
import { useState } from 'react'

import { StatusBadge } from '@/components/common/StatusBadge'
import { Avatar, AvatarFallback, AvatarGroup } from '@/components/ui/avatar'
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from '@/components/ui/breadcrumb'
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination'
import { DataTable, DataTableColumnHeader, DataTableRowActions, DataTableToolbar, type DataTableSort } from '@/modules/data-table'

import { DEMO_INVOICES, INVOICE_STATUS_TONE, type DemoInvoice } from '../ui-kit.constants'

import { KitDemo, KitSection } from './KitSection'

const CURRENCY = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })

const COLUMNS: ColumnDef<DemoInvoice, unknown>[] = [
  { accessorKey: 'id', header: 'Invoice', cell: ({ row }) => <span className="text-muted-foreground tabular-nums">{row.original.id}</span> },
  {
    id: 'customer',
    accessorKey: 'customer',
    enableSorting: true,
    header: ({ column }) => <DataTableColumnHeader column={column} title="Customer" />,
    cell: ({ row }) => (
      <div className="flex flex-col">
        <span className="font-medium">{row.original.customer}</span>
        <span className="text-xs text-muted-foreground">{row.original.email}</span>
      </div>
    ),
  },
  {
    accessorKey: 'status',
    header: 'Status',
    cell: ({ row }) => (
      <StatusBadge tone={INVOICE_STATUS_TONE[row.original.status]} className="capitalize">
        {row.original.status}
      </StatusBadge>
    ),
  },
  {
    id: 'amount',
    accessorKey: 'amount',
    enableSorting: true,
    header: ({ column }) => <DataTableColumnHeader column={column} title="Amount" className="ml-auto" />,
    cell: ({ row }) => <span className="block text-right tabular-nums">{CURRENCY.format(row.original.amount)}</span>,
    meta: { className: 'text-right' },
  },
  {
    id: 'actions',
    header: () => <span className="sr-only">Actions</span>,
    cell: ({ row }) => (
      <DataTableRowActions
        label={`Actions for ${row.original.id}`}
        actions={[
          { label: 'View', icon: 'eye', onSelect: () => undefined },
          { label: 'Void invoice', icon: 'x-circle', variant: 'destructive', separatorBefore: true, onSelect: () => undefined },
        ]}
      />
    ),
    meta: { className: 'w-12 text-right' },
  },
]

export function DataSection() {
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState<DataTableSort | null>(null)
  const rows = DEMO_INVOICES.filter((invoice) => invoice.customer.toLowerCase().includes(search.toLowerCase()))

  return (
    <KitSection id="data" title="Data display" description="DataTable from @/modules/data-table for every list; avatars, breadcrumbs and pagination.">
      <DataTable
        columns={COLUMNS}
        data={rows}
        sort={sort}
        onSortChange={setSort}
        pagination={{ page: 1, size: 10, totalElements: rows.length, totalPages: 1 }}
        onPageChange={() => undefined}
        toolbar={<DataTableToolbar searchValue={search} onSearchChange={setSearch} searchPlaceholder="Filter customers…" />}
      />
      <div className="grid gap-4 lg:grid-cols-3">
        <KitDemo title="Avatars">
          <Avatar size="sm">
            <AvatarFallback>AH</AvatarFallback>
          </Avatar>
          <Avatar>
            <AvatarFallback>NB</AvatarFallback>
          </Avatar>
          <Avatar size="lg">
            <AvatarFallback>PR</AvatarFallback>
          </Avatar>
          <AvatarGroup>
            {['AH', 'NB', 'PR', 'SA'].map((initials) => (
              <Avatar key={initials}>
                <AvatarFallback>{initials}</AvatarFallback>
              </Avatar>
            ))}
          </AvatarGroup>
        </KitDemo>
        <KitDemo title="Breadcrumb">
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbLink href="#data">Settings</BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbLink href="#data">Team</BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbPage>Members</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
        </KitDemo>
        <KitDemo title="Pagination (non-table)">
          <Pagination>
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious href="#data" />
              </PaginationItem>
              <PaginationItem>
                <PaginationLink href="#data">1</PaginationLink>
              </PaginationItem>
              <PaginationItem>
                <PaginationLink href="#data" isActive>
                  2
                </PaginationLink>
              </PaginationItem>
              <PaginationItem>
                <PaginationEllipsis />
              </PaginationItem>
              <PaginationItem>
                <PaginationNext href="#data" />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        </KitDemo>
      </div>
    </KitSection>
  )
}
