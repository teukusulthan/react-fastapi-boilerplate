import { Suspense } from 'react'
import { Outlet, useLocation } from 'react-router-dom'

import { LoadingState } from '@/components/common/LoadingState'
import { ThemeToggle } from '@/components/common/ThemeToggle'
import env from '@/config/env'
import { usePageTitle } from '@/hooks/use-page-title'

const AUTH_PAGE_TITLES: Record<string, string> = {
  '/auth/verify-email': 'Verify email',
}

/** Public auth pages (login, verify email…): app mark + name above a centered card on a subtle canvas. */
export default function AuthLayout() {
  const { pathname } = useLocation()
  usePageTitle(AUTH_PAGE_TITLES[pathname.replace(/\/+$/, '')] ?? 'Sign in')
  const year = new Date().getFullYear()

  return (
    <div className="flex min-h-svh flex-col bg-muted/40 text-foreground dark:bg-background">
      <header className="flex h-14 shrink-0 items-center justify-end px-4">
        <ThemeToggle />
      </header>
      <main className="flex flex-1 flex-col items-center justify-center gap-8 px-4 pb-16">
        <div className="flex flex-col items-center gap-3">
          <span className="flex size-10 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm" aria-hidden="true">
            <i className="ph-fill ph-cube size-5" />
          </span>
          <span className="text-sm font-semibold tracking-tight">{env.app.name}</span>
        </div>
        <Suspense fallback={<LoadingState />}>
          <Outlet />
        </Suspense>
      </main>
      <footer className="py-6 text-center text-xs text-muted-foreground">
        © {year} {env.app.name}
      </footer>
    </div>
  )
}
