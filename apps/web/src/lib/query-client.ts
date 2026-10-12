import { QueryClient } from '@tanstack/react-query'

import { ApiError } from '@/services/api-error'

const MAX_QUERY_RETRIES = 1

/** Retry only transient failures (network / 5xx / 429); never 4xx client errors. */
export function shouldRetryQuery(failureCount: number, error: unknown): boolean {
  if (failureCount >= MAX_QUERY_RETRIES) return false
  if (error instanceof ApiError) return error.status === 0 || error.status === 429 || error.status >= 500
  return true
}

/** App-wide TanStack Query client (singleton so non-React code can reset the cache, e.g. on logout). */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000,
      gcTime: 5 * 60 * 1000,
      retry: shouldRetryQuery,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: false,
    },
  },
})
