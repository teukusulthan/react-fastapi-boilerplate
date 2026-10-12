import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, type RenderOptions } from '@testing-library/react'
import type { ReactElement, ReactNode } from 'react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { TooltipProvider } from '@/components/ui/tooltip'

export function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 }, mutations: { retry: false } },
  })
}

interface ProvidersOptions {
  route?: string
  /** Extra routes rendered next to the element under test (e.g. a login page to assert redirects). */
  routes?: { path: string; element: ReactNode }[]
  path?: string
  queryClient?: QueryClient
}

/** Render inside QueryClient + Tooltip + MemoryRouter providers. */
export function renderWithProviders(
  ui: ReactElement,
  { route = '/', routes = [], path = '*', queryClient = createTestQueryClient(), ...options }: ProvidersOptions & RenderOptions = {},
) {
  const result = render(
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <MemoryRouter initialEntries={[route]}>
          <Routes>
            {routes.map((entry) => (
              <Route key={entry.path} path={entry.path} element={entry.element} />
            ))}
            <Route path={path} element={ui} />
          </Routes>
        </MemoryRouter>
      </TooltipProvider>
    </QueryClientProvider>,
    options,
  )
  return { ...result, queryClient }
}
