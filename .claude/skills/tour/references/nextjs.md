# Driver.js — Next.js Patterns

## Key Constraint

driver.js manipulates the DOM directly — it must run **client-side only**.  
In Next.js (App Router or Pages Router), always guard against SSR.

---

## App Router (Next.js 13+)

### Option A: Mark component as Client Component

```tsx
'use client'

import { useEffect, useRef, useCallback } from 'react'
import { driver, type Config, type DriveStep } from 'driver.js'
import 'driver.js/dist/driver.css'
```

Place `useTour` hook in a file that starts with `'use client'` or is imported only from client components.

### Option B: Dynamic import (keep parent as Server Component)

```tsx
// app/dashboard/page.tsx (Server Component)
import dynamic from 'next/dynamic'

const DashboardTour = dynamic(() => import('@/features/dashboard/DashboardTour'), {
  ssr: false,
})

export default function DashboardPage() {
  return (
    <main>
      {/* server-rendered content */}
      <DashboardTour />
    </main>
  )
}
```

```tsx
// features/dashboard/DashboardTour.tsx
'use client'

import { useTour } from '@/hooks/useTour'

const STEPS = [ /* ... */ ]

export default function DashboardTour() {
  const tour = useTour({ steps: STEPS })
  return <button onClick={() => tour.start()}>Tour</button>
}
```

---

## Pages Router (Next.js 12 and below)

```tsx
// pages/dashboard.tsx
import dynamic from 'next/dynamic'

const DashboardTour = dynamic(() => import('@/components/DashboardTour'), {
  ssr: false,
})

export default function Dashboard() {
  return (
    <>
      {/* page content */}
      <DashboardTour />
    </>
  )
}
```

---

## CSS Import

In Next.js, import driver.js CSS in `app/layout.tsx` (App Router) or `pages/_app.tsx` (Pages Router):

```ts
// app/layout.tsx
import 'driver.js/dist/driver.css'

// OR pages/_app.tsx
import 'driver.js/dist/driver.css'
```

Do **not** import it inside a component file — Next.js only allows CSS imports in layout/app files or global CSS.

---

## useTour Hook (Next.js safe)

Same hook as React, but ensure it's only used inside `'use client'` components:

```ts
'use client'

import { useCallback, useEffect, useRef } from 'react'
import { driver, type Config, type DriveStep } from 'driver.js'

interface UseTourOptions extends Omit<Config, 'steps'> {
  steps: DriveStep[]
  autoStart?: boolean
  storageKey?: string
}

export function useTour({ steps, autoStart = false, storageKey, ...config }: UseTourOptions) {
  const driverRef = useRef<ReturnType<typeof driver> | null>(null)

  useEffect(() => {
    driverRef.current = driver({
      showProgress: true,
      animate: true,
      smoothScroll: true,
      allowClose: true,
      ...config,
      steps,
      onDestroyed: () => {
        if (storageKey) localStorage.setItem(storageKey, '1')
        config.onDestroyed?.()
      },
    })

    if (autoStart) {
      const alreadySeen = storageKey ? localStorage.getItem(storageKey) : false
      if (!alreadySeen) {
        setTimeout(() => driverRef.current?.drive(), 600)
      }
    }

    return () => { driverRef.current?.destroy() }
  }, [])

  const start = useCallback((stepIndex?: number) => driverRef.current?.drive(stepIndex), [])
  const stop = useCallback(() => driverRef.current?.destroy(), [])

  return { start, stop }
}
```

---

## Auto-start on First Visit (App Router)

```tsx
'use client'

import { useTour } from '@/hooks/useTour'

export function OnboardingTour() {
  const tour = useTour({
    steps: TOUR_STEPS,
    autoStart: true,
    storageKey: 'onboarding-tour-done',
  })

  return (
    <button onClick={() => tour.start()} className="text-sm underline">
      Lihat tour
    </button>
  )
}
```
