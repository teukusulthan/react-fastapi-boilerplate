/** Where to start extending this app — shown on the placeholder dashboard. Paths are relative to apps/web. */
export const GETTING_STARTED_STEPS: readonly { title: string; detail: string; path: string; icon: string }[] = [
  { title: 'Add a page', detail: 'Create a thin page and register its route.', path: 'src/routes/main.routes.tsx', icon: 'browser' },
  { title: 'Make it navigable', detail: 'Add a menu entry — the sidebar renders from config.', path: 'src/config/menu/app.menu.ts', icon: 'sidebar-simple' },
  { title: 'Fetch data', detail: 'Add the endpoint, a service and a TanStack Query hook.', path: 'src/services/api-endpoints.ts', icon: 'plugs-connected' },
  { title: 'Compose the UI', detail: 'Browse every primitive and pattern before you build.', path: '/ui-kit (dev only)', icon: 'squares-four' },
]
