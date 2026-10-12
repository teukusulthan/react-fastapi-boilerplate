# Driver.js — React (Vite / CRA)

No SSR constraints. driver.js runs client-side by default in React SPA.

---

## Installation

```bash
npm install driver.js
```

---

## CSS Import

Import once in the app entry point (`main.tsx` or `index.css`):

```ts
// main.tsx
import 'driver.js/dist/driver.css'
```

Or via CSS `@import` chain:

```css
/* index.css */
@import 'driver.js/dist/driver.css';
```

---

## useTour Hook

```ts
// src/hooks/useTour.ts
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

## Basic Usage

```tsx
// src/pages/Dashboard/parts/DashboardTour.tsx
import { useTour } from '@/hooks/useTour'
import type { DriveStep } from 'driver.js'

const STEPS: DriveStep[] = [
  {
    element: '#sidebar',
    popover: {
      title: 'Navigasi',
      description: 'Gunakan sidebar untuk berpindah halaman.',
      side: 'right',
    },
  },
  {
    element: '#search-bar',
    popover: {
      title: 'Pencarian',
      description: 'Cari konten di sini.',
      side: 'bottom',
    },
  },
  {
    element: '#profile-btn',
    popover: {
      title: 'Profil',
      description: 'Kelola akun Anda.',
      side: 'left',
    },
  },
]

export function DashboardTour() {
  const tour = useTour({ steps: STEPS })

  return (
    <button onClick={() => tour.start()}>
      Mulai Tour
    </button>
  )
}
```

---

## Auto-start on First Visit

```tsx
export function OnboardingTour() {
  const tour = useTour({
    steps: TOUR_STEPS,
    autoStart: true,
    storageKey: 'onboarding-tour-done',
  })

  return (
    // shadcn Button from '@/components/ui/button' (visual rules: reactjs-ui-design)
    <Button variant="ghost" size="sm" onClick={() => tour.start()}>
      <i className="ph ph-question" aria-hidden="true" />
      Lihat tour lagi
    </Button>
  )
}
```

---

## Trigger from Parent (Lifted State)

When the tour needs to be triggered from a menu or external button, lift the `start` function up via props or callback:

```tsx
// parent component
import { useTour } from '@/hooks/useTour'

const STEPS: DriveStep[] = [ /* ... */ ]
const TOUR_KEY = 'dashboard-tour-done'

export function DashboardPage() {
  const tour = useTour({
    steps: STEPS,
    autoStart: true,
    storageKey: TOUR_KEY,
  })

  return (
    <div>
      <Header onTourClick={() => tour.start()} />
      <DashboardContent />
    </div>
  )
}
```

```tsx
// header component
interface HeaderProps {
  onTourClick: () => void
}

export function Header({ onTourClick }: HeaderProps) {
  return (
    <header>
      <button onClick={onTourClick}>Tour</button>
    </header>
  )
}
```

---

## Step Anchors

Add `id` attributes to target elements. Keep IDs in a shared constants file to avoid typos:

```ts
// src/constants/tour.ts
export const TOUR_ANCHORS = {
  sidebar: 'tour-sidebar',
  searchBar: 'tour-search-bar',
  profileBtn: 'tour-profile-btn',
} as const
```

```tsx
// in JSX
<aside id={TOUR_ANCHORS.sidebar}>...</aside>
<input id={TOUR_ANCHORS.searchBar} />
<button id={TOUR_ANCHORS.profileBtn}>Profil</button>
```

```ts
// in steps
const STEPS: DriveStep[] = [
  { element: `#${TOUR_ANCHORS.sidebar}`, popover: { title: 'Sidebar', description: '...' } },
]
```

---

## CSS Customization (Design Token Integration)

Override driver.js popover styles with the app's shadcn semantic tokens so the tour looks like a
shadcn `Popover` (visual rules: [`reactjs-ui-design`](../../reactjs-ui-design/SKILL.md) — 12px floating
surface, 1px border, `shadow-lg`, 8px buttons):

```css
/* src/styles/components.css */
.driver-popover {
  background: var(--popover);
  color: var(--popover-foreground);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
}

.driver-popover-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--popover-foreground);
}

.driver-popover-description,
.driver-popover-progress-text,
.driver-popover-close-btn {
  font-size: 0.875rem;
  color: var(--muted-foreground);
}

.driver-popover-next-btn,
.driver-popover-prev-btn {
  background: var(--primary);
  color: var(--primary-foreground);
  border: none;
  border-radius: var(--radius-md);
  padding: 4px 12px;
  text-shadow: none;
  cursor: pointer;
}
```
