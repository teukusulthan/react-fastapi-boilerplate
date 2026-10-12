import { QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { ErrorBoundary } from 'react-error-boundary'

import { ErrorFallback } from '@/components/common/ErrorFallback'
import { Toaster } from '@/components/ui/sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { useThemeSync } from '@/hooks/use-theme-sync'
import { queryClient } from '@/lib/query-client'

/** App-wide providers: error boundary, TanStack Query, tooltips, toasts, theme sync. */
export function AppProviders({ children }: { children: ReactNode }) {
  useThemeSync()

  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <QueryClientProvider client={queryClient}>
        <TooltipProvider delayDuration={300}>
          {children}
          <Toaster position="top-right" closeButton />
        </TooltipProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}
