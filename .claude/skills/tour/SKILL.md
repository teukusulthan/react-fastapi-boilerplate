---
name: tour
description: "Implement product tours and onboarding flows using driver.js. Use when asked to add a guided tour, feature walkthrough, onboarding steps, spotlight/highlight, or step-by-step UI guide. Supports React (Vite/CRA), Next.js (App Router and Pages Router), and plain HTML (CDN/vanilla JS)."
---

# Tour with Driver.js

## Framework Decision Tree

| Framework | Read |
|-----------|------|
| React (Vite / CRA / Rsbuild) | This file — section below |
| Next.js (App Router / Pages Router) | [references/nextjs.md](references/nextjs.md) |
| Plain HTML / Vanilla JS | [references/html-vanilla.md](references/html-vanilla.md) |

---

## React Setup

```bash
npm install driver.js
```

Import CSS globally (e.g. `src/index.css` or `main.tsx`):

```ts
import 'driver.js/dist/driver.css'
```

## useTour Hook

Place in `src/hooks/useTour.ts`:

```ts
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
      if (!alreadySeen) setTimeout(() => driverRef.current?.drive(), 600)
    }

    return () => { driverRef.current?.destroy() }
  }, [])

  const start = useCallback((stepIndex?: number) => driverRef.current?.drive(stepIndex), [])
  const stop = useCallback(() => driverRef.current?.destroy(), [])
  const highlight = useCallback((step: DriveStep) => driverRef.current?.highlight(step), [])

  return { start, stop, highlight }
}
```

## Usage in a Component

```tsx
import { useTour } from '@/hooks/useTour'

const TOUR_STEPS = [
  {
    element: '#sidebar',
    popover: { title: 'Sidebar', description: 'Navigasi antar halaman.', side: 'right' },
  },
  {
    element: '#new-chat-btn',
    popover: { title: 'Chat Baru', description: 'Mulai percakapan baru.', side: 'bottom' },
  },
  {
    element: '#message-input',
    popover: { title: 'Input Pesan', description: 'Ketik pesan dan tekan Enter.', side: 'top' },
  },
]

export function MyPage() {
  const tour = useTour({
    steps: TOUR_STEPS,
    storageKey: 'my-page-tour-done',
    autoStart: true,
  })

  return (
    <div>
      <button onClick={() => tour.start()}>Mulai Tour</button>
      {/* content with id anchors */}
    </div>
  )
}
```

## Step Element Targeting

Add `id` to elements you want to highlight:

```tsx
<aside id="sidebar">...</aside>
<button id="new-chat-btn">New Chat</button>
<textarea id="message-input" />
```

Use class selectors when IDs aren't practical: `element: '.my-class'`

## Single Element Highlight

```ts
tour.highlight({
  element: '#help-btn',
  popover: { title: 'Bantuan', description: 'Klik kapan saja.', side: 'left' },
})
```

## Styling Customization

In the React app (`apps/web`), theme the popover with the shadcn semantic tokens so it matches a shadcn
`Popover` (`var(--popover)`, `var(--border)`, `var(--radius-xl)`, buttons in `var(--primary)`) — the
ready-made CSS is in [references/reactjs.md](references/reactjs.md) § CSS Customization. No hardcoded
hex colors. Plain-HTML mockups use the mockup's own CSS variables.

Use `popoverClass` on individual steps for per-step styling.

## References

- **[references/nextjs.md](references/nextjs.md)** — Next.js patterns: App Router `'use client'`, dynamic import SSR bypass, Pages Router, CSS import location
- **[references/html-vanilla.md](references/html-vanilla.md)** — Plain HTML: CDN setup (IIFE + ESM), vanilla JS tour, single highlight
- **[references/api_reference.md](references/api_reference.md)** — Full driver.js config options, DriveStep fields, Popover fields, instance methods
