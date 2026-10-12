import { Fragment } from 'react'
import { Link, useLocation } from 'react-router-dom'

import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from '@/components/ui/breadcrumb'
import { ALL_MENUS } from '@/config/menu'
import { useRouteHandle } from '@/hooks/use-route-handle'
import { getMenuTrail } from '@/utils/menu'

/** Header breadcrumb derived from the menu config (parents → current page), or the route `handle.crumb`. */
export default function AppBreadcrumb() {
  const { pathname } = useLocation()
  const handle = useRouteHandle()
  const trail = getMenuTrail(ALL_MENUS(), pathname)
  const crumbs = handle?.crumb ? [{ id: 'route', display: handle.crumb, path: pathname }] : trail.map(({ id, display, path }) => ({ id, display, path }))

  if (crumbs.length === 0) return null

  return (
    <Breadcrumb className="min-w-0">
      <BreadcrumbList className="flex-nowrap">
        {crumbs.map((crumb, index) => {
          const isLast = index === crumbs.length - 1
          return (
            <Fragment key={crumb.id}>
              {index > 0 && <BreadcrumbSeparator className="hidden sm:block" />}
              <BreadcrumbItem className={isLast ? 'min-w-0' : 'hidden sm:inline-flex'}>
                {isLast ? (
                  <BreadcrumbPage className="truncate">{crumb.display}</BreadcrumbPage>
                ) : (
                  <BreadcrumbLink asChild>
                    <Link to={crumb.path}>{crumb.display}</Link>
                  </BreadcrumbLink>
                )}
              </BreadcrumbItem>
            </Fragment>
          )
        })}
      </BreadcrumbList>
    </Breadcrumb>
  )
}
