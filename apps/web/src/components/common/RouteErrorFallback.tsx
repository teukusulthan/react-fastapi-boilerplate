import { isRouteErrorResponse, Link, useRouteError } from 'react-router-dom'

import { StatusScreen } from '@/components/common/StatusScreen'
import { Button } from '@/components/ui/button'
import env from '@/config/env'
import { reloadPage } from '@/utils/browser'

/** Router `errorElement`: loader/render errors inside routes (incl. failed lazy chunks). */
export function RouteErrorFallback() {
  const error = useRouteError()

  if (isRouteErrorResponse(error) && error.status === 404) {
    return (
      <StatusScreen
        fullScreen
        code="404"
        icon="compass"
        title="Page not found"
        description="The page you are looking for does not exist or has been moved."
        actions={
          <Button asChild>
            <Link to="/">Go to dashboard</Link>
          </Button>
        }
      />
    )
  }

  if (env.app.isDev) console.error(error)

  return (
    <StatusScreen
      fullScreen
      icon="warning-octagon"
      title="Something went wrong"
      description="This page failed to load. If the app was just updated, reloading usually fixes it."
      actions={
        <>
          <Button onClick={reloadPage}>Reload page</Button>
          <Button asChild variant="outline">
            <Link to="/">Go to dashboard</Link>
          </Button>
        </>
      }
    />
  )
}
