import type { FallbackProps } from 'react-error-boundary'

import { StatusScreen } from '@/components/common/StatusScreen'
import { Button } from '@/components/ui/button'
import { reloadPage } from '@/utils/browser'

/** Fallback for React render errors caught by <ErrorBoundary>. Never shows technical details to users. */
export function ErrorFallback({ resetErrorBoundary }: FallbackProps) {
  return (
    <StatusScreen
      fullScreen
      icon="warning-octagon"
      title="Something went wrong"
      description="An unexpected error occurred. Try again, or reload the page if the problem persists."
      actions={
        <>
          <Button onClick={resetErrorBoundary}>Try again</Button>
          <Button variant="outline" onClick={reloadPage}>
            Reload page
          </Button>
        </>
      }
    />
  )
}
