---
name: reactjs-state-management
description: State management patterns for apps/web — TanStack Query (server state), Zustand 5 (global client state; auth store NOT persisted, theme store persisted), React Hook Form + zod (form state), Context (scoped metadata), useState (local), sonner (toasts), getState() outside React. XState is an optional add-on. Use when deciding where a piece of state lives or creating a store.
---

# State Management

Keep state as local as possible; elevate only when 2+ distant components need it.

| Layer | Tool | Real example |
|-------|------|--------------|
| Server / async state | TanStack Query (`@tanstack/react-query` 5) | `features/administrator/user/hooks/useUserList.ts`, `features/shared/auth/hooks/useSession.ts` |
| Global transient client state | Zustand 5 (`create<T>()(…)`, no persist) | `src/stores/useAuthStore.ts` |
| Global persisted preference | Zustand + `persist` + `partialize` | `src/stores/useThemeStore.ts` |
| Form state | React Hook Form + zod resolver | `features/shared/auth/components/LoginForm.tsx` |
| Scoped metadata | Context API | `components/ui/form.tsx`, `components/ui/sidebar.tsx` (`useSidebar`) |
| Local component state | `useState` / custom hook | `hooks/use-mobile.ts`, `hooks/use-debounced-value.ts` |
| Notifications | `sonner` (`toast.*`), `<Toaster>` in `AppProviders` | `components/ui/sonner.tsx` |
| Outside React | `useXStore.getState()` | `services/api-client.ts` → `useAuthStore.getState().clearSession()` |
| Workflow / process state (optional) | XState — not installed; add `xstate` + `@xstate/react` when needed | `.claude/skills/reactjs-xstate/SKILL.md` |

## Decision tree

```
Data comes from the backend?                 → TanStack Query (useQuery / useMutation) — never copy it into a store
Multi-step process with guarded transitions? → XState (add the dependency) or a small reducer
Form input?                                  → React Hook Form + zod
Shared across distant components / non-React code? → Zustand store in src/stores/
Shared within one component family?          → Context with a consumer hook
Otherwise                                    → useState / useReducer in the component or a feature hook
```

- **Query vs Zustand:** server data, loading, error, cache → Query. Only small client selections (e.g. selected
  row id, panel open) go into Zustand.
- **URL state:** pagination/search that should be shareable can live in `useSearchParams`.
- **persist** only for preferences that must survive a refresh (theme, sidebar width). Always `partialize`.
  **Never persist auth/session data** — the session is httpOnly cookies + `GET /auth/me`.

---

## 1. Zustand — global transient store (the auth store)

`src/stores/useAuthStore.ts` (verbatim shape):

```ts
import { create } from 'zustand'
import type { UserProfile } from '@/types/models'

export type AuthStatus = 'unknown' | 'authenticated' | 'anonymous'
export type SessionEndReason = 'logout' | 'expired'

interface AuthState {
  status: AuthStatus
  user: UserProfile | null
  endReason: SessionEndReason | null
  setUser: (user: UserProfile) => void
  clearSession: (reason?: SessionEndReason) => void
}

/** Deliberately NOT persisted: cookies are the source of truth; /auth/me re-resolves on every load. */
export const useAuthStore = create<AuthState>()((set) => ({
  status: 'unknown',
  user: null,
  endReason: null,
  setUser: (user) => set({ user, status: 'authenticated', endReason: null }),
  clearSession: (reason = 'expired') => set({ user: null, status: 'anonymous', endReason: reason }),
}))
```

Consume with **slice selectors** (one value per call, avoids re-renders):

```tsx
const user = useAuthStore((state) => state.user)
const status = useAuthStore((state) => state.status)
```

Who writes it: `useSession` (`/auth/me`), `useLoginFlow` (login / 2FA), `endClientSession()` in
`services/api-client.ts` (refresh failure / logout). Components never call `setUser` with fabricated data.

## 2. Zustand — persisted preference (the theme store)

`src/stores/useThemeStore.ts` uses `persist` with `createJSONStorage(() => localStorage)`,
`partialize: (s) => ({ theme: s.theme })`, and `onRehydrateStorage` to apply the `.dark` class right after
hydration; `useThemeSync()` (mounted once in `AppProviders`) follows OS changes. New preference stores copy
this shape: `name: '<feature>-storage'`, `partialize` to the minimum, side effects in actions/rehydrate only.

## 3. Outside React

```ts
import { useAuthStore } from '@/stores/useAuthStore'
useAuthStore.getState().clearSession('expired')   // e.g. inside an interceptor
```

Prefer existing helpers (`endClientSession()` also clears the Query cache).

## 4. Server state (TanStack Query)

See `.claude/skills/reactjs-tanstack-query/SKILL.md`. Shared client: `src/lib/query-client.ts` (`queryClient`).
Query-key factories live in each feature's constants (`USER_QUERY_KEYS`, `AUTH_QUERY_KEYS`).

## 5. Forms (React Hook Form)

```tsx
const form = useForm<TLoginFormValues>({ resolver: zodResolver(loginSchema), defaultValues: { identifier: '', password: '' } })
// <Form {...form}> + <FormField control={form.control} name="identifier" render={({ field }) => (…<FormControl><Input {...field} /></FormControl><FormMessage />)} />
```

Server-side 422s → `applyApiFieldErrors(error, form.setError, FIELDS)` (`src/utils/form-errors.ts`).
Full patterns: `.claude/skills/reactjs-form/SKILL.md`.

## 6. Context

Only for metadata inside a tightly coupled component family (`Form*` in `components/ui/form.tsx`,
`SidebarProvider`/`useSidebar`). Always export a consumer hook that throws outside its provider.

## 7. Local state & custom hooks

`useState` for toggles/buffers; extract reusable stateful logic into `src/hooks/use-<name>.ts`
(kebab-case files, `useCamelCase` exports — e.g. `useIsMobile` in `use-mobile.ts`). Clean up every effect.

## 8. Notifications

```ts
import { toast } from 'sonner'
toast.success('Group created')
toast.error(getErrorMessage(error))
```

No custom toast reducer/pub-sub and no `use-toast` hook — `sonner` is the only toast system.

---

## Rules

- ✅ Stores in `src/stores/use<Name>Store.ts`, typed interface, actions inside `create`.
- ✅ Subscribe to slices; derive values with selectors or at the call site.
- ❌ No tokens/passwords/PII in stores or storage; never persist the auth store.
- ❌ No API responses in Zustand; no hand-rolled loading/error flags for API calls.
- ❌ No direct `localStorage`/`sessionStorage` in components (use `persist`; wrap reads in try/catch if unavoidable).
- ❌ No Redux/Recoil/Jotai; no new state library without updating this skill.
- ❌ No `useEffect` syncing two stores, no store imported inside another store's `create`.

> Full rule tables and checklist: `references/state-management-rules.md`
