---
name: reactjs-form
description: Build forms in apps/web with react-hook-form + zod 4 (@hookform/resolvers) + the shadcn Form primitives in src/components/ui/form.tsx, submitted through a TanStack Query mutation, with backend 422 field errors mapped onto fields via applyApiFieldErrors (src/utils/form-errors.ts) and a responsive Tailwind grid. Reference implementation: features/shared/auth (login.schema.ts, LoginForm.tsx). Use when creating a form, adding validation, or handling submission errors.
---

# Forms

> **Visual rules:** [reactjs-ui-design](../reactjs-ui-design/SKILL.md) + `.claude/rules/web/ui-design.md` win over any markup here. This skill owns form state, validation, submission and server-error mapping (playbook recipe §5.4 is the visual target).

Reference implementation (read it first):

| File | Shows |
|---|---|
| `src/features/shared/auth/schemas/login.schema.ts` | zod schemas + `z.infer` form types (`loginSchema`, `TLoginFormValues`) |
| `src/features/shared/auth/components/LoginForm.tsx` | `useForm` + `zodResolver`, `<Form>`/`<FormField>`, server error `<Alert>`, submit state |
| `src/features/shared/auth/hooks/useLoginFlow.ts` | `useMutation` around `authService` calls |
| `src/features/shared/auth/constants/auth.constants.ts` | `LOGIN_FIELDS` — fields that may receive server errors |
| `src/utils/form-errors.ts` | `applyApiFieldErrors(error, setError, fields)` — maps 422 `data: [{field, message}]` onto fields |
| `src/services/api-error.ts` | `ApiError` (`status`, `code`, `message`, `details`, `fieldErrors`), `getErrorMessage()`, `toApiError()` |

## Stack

| Layer | Library |
|---|---|
| State | `react-hook-form` 7 |
| Validation | `zod` 4 + `@hookform/resolvers/zod` |
| UI | `@/components/ui/form` (`Form`, `FormField`, `FormItem`, `FormLabel`, `FormControl`, `FormDescription`, `FormMessage`), `input`, `textarea`, `select`, `checkbox`, `radio-group`, `switch`, `button`, `alert` from `@/components/ui/*`; `SectionCard` / `ConfirmDialog` from `@/components/common/*` |
| Submit | TanStack Query `useMutation` in the feature's `hooks/` calling a service |
| Feedback | inline `<FormMessage/>`, top `<Alert variant="destructive">`, `toast` from `sonner` for success |

Check `ls apps/web/src/components/ui` first (playbook §4 lists the expected set). Any control that is
missing but exists in shadcn is **installed, never hand-built**: `cd apps/web && npx shadcn@latest add
<name>`, then run the post-install checklist in `reactjs-ui-design` §3 (Phosphor instead of
`lucide-react`, `React.forwardRef` for React 18, semantic tokens only). Never native `<select>`,
`<input type="checkbox">`/`radio`, or a hand-rolled date picker/combobox.

## Step 1 — Schema (feature `schemas/` folder)

Location: `src/features/{domain}/{feature}/schemas/{name}.schema.ts` (shared by 2+ domains →
`src/schemas/`, create on demand). Never in the component.

```ts
// src/features/settings/profile/schemas/profile.schema.ts  — example
import { z } from 'zod'

export const profileSchema = z.object({
  fullname: z.string().trim().min(1, 'Full name is required').max(100, 'Full name is too long'),
  phone: z
    .string()
    .trim()
    .regex(/^[0-9+\-\s]*$/, 'Phone number format is invalid')
    .max(32, 'Phone number is too long'),
  about: z.string().max(500, 'At most 500 characters'),
})

export type TProfileFormValues = z.infer<typeof profileSchema>

/** Fields that can receive backend 422 errors (camelCase, as returned by the API). */
export const PROFILE_FIELDS = ['fullname', 'phone', 'about'] as const
```

zod 4 notes: use `z.email()` (not `z.string().email()`), custom messages via the string
argument or `{ error: '…' }` (`errorMap` is gone), `z.enum([...], { error: '…' })`.

Name form fields **exactly like the API JSON fields** (camelCase) so backend 422 details
(`[{ "field": "fullname", "message": "…" }]`) map onto them.

## Step 2 — Mutation hook (feature `hooks/`)

```ts
// src/features/settings/profile/hooks/useUpdateProfile.ts  — example
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { AUTH_QUERY_KEYS } from '@/features/shared/auth'
import { userService, type IUpdateProfilePayload } from '@/services/user.service'

export function useUpdateProfile() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: IUpdateProfilePayload) => userService.updateProfile(payload),
    onSuccess: () => {
      toast.success('Profile updated')
      void queryClient.invalidateQueries({ queryKey: AUTH_QUERY_KEYS.me }) // refresh the session profile
    },
  })
}
```

Services reject with `ApiError`; never read `error.response.data` — use the `ApiError` fields.

## Step 3 — Form component

```tsx
// src/features/settings/profile/components/ProfileForm.tsx  — example
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'

import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { getErrorMessage } from '@/services/api-error'
import { applyApiFieldErrors } from '@/utils/form-errors'

import { useUpdateProfile } from '../hooks/useUpdateProfile'
import { PROFILE_FIELDS, profileSchema, type TProfileFormValues } from '../schemas/profile.schema'

export function ProfileForm({ initial }: { initial: TProfileFormValues }) {
  const mutation = useUpdateProfile()
  const form = useForm<TProfileFormValues>({ resolver: zodResolver(profileSchema), defaultValues: initial })

  const onSubmit = form.handleSubmit((values) =>
    mutation.mutate(values, {
      onError: (error) => applyApiFieldErrors(error, form.setError, PROFILE_FIELDS),
    }),
  )

  return (
    <Form {...form}>
      <form onSubmit={onSubmit} noValidate className="flex max-w-2xl flex-col gap-6" aria-label="Profile">
        {mutation.error != null && (
          <Alert variant="destructive">
            <i className="ph ph-warning-circle" aria-hidden="true" />
            <AlertDescription>{getErrorMessage(mutation.error)}</AlertDescription>
          </Alert>
        )}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <FormField
            control={form.control}
            name="fullname"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Full name</FormLabel>
                <FormControl>
                  <Input autoComplete="name" {...field} />
                </FormControl>
                <FormDescription>Shown on your profile and in activity logs.</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
          {/* phone … ; long fields: <div className="sm:col-span-2"> */}
        </div>

        <div className="flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={() => form.reset(initial)} disabled={mutation.isPending}>
            Cancel
          </Button>
          <Button type="submit" loading={mutation.isPending}>
            Save changes
          </Button>
        </div>
      </form>
    </Form>
  )
}
```

`LoginForm.tsx` shows the variant where the parent owns the mutation and passes
`onSubmit(values, onError)` + `isSubmitting` + `error` as props — use that when one hook
drives several forms (login → 2FA).

## Layout

| Form | Grid |
|---|---|
| Short (login, single field) | `flex flex-col gap-4` inside a centered `max-w-sm` card (playbook §5.6) |
| Medium (profile, edit dialog) | `max-w-2xl`, `grid grid-cols-1 gap-4 sm:grid-cols-2` |
| Dense (admin filters) | `grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3` |
| Settings page | stacked `SectionCard`s with `layout="split"` (title + description in the left third on `lg`, fields right) |

Label above input; helper (`FormDescription`, `text-sm text-muted-foreground`) and error below.
Long fields/textarea: `sm:col-span-2` / `col-span-full`. Server-error `Alert` sits above the
grid, full width. Actions bottom-right `flex justify-end gap-2`, primary rightmost, secondary
`variant="outline"` (full-width button on auth cards). The submit button keeps its label and gets
`loading={isPending}` (the `Button` `loading` prop shows an inline spinner, disables it and keeps its width). No full-width inputs on wide screens (`max-w-2xl`).
Create/edit: `Dialog` for ≤ 6 fields, `Sheet` for more, a dedicated page for complex flows.
Danger zone = last `SectionCard` with `tone="destructive"` + a `ConfirmDialog` (`variant="destructive"`).
Forms inside a `Dialog`/`Sheet` keep the scrollable body in `PerfectScrollArea`.

## Rules

- MUST use `useForm` + `zodResolver(schema)`; MUST define `defaultValues` for every field.
- MUST infer types with `z.infer`; never hand-write the form type.
- MUST set `noValidate` on `<form>` and wrap fields in `<Form>`/`<FormField>`/`<FormItem>`/`<FormControl>`/`<FormMessage>` (accessibility + error wiring).
- MUST submit through a mutation hook calling a service; loading from `mutation.isPending` (or `form.formState.isSubmitting` for async `handleSubmit`).
- MUST map 422 details with `applyApiFieldErrors(error, form.setError, FIELDS)`; show the rest with `getErrorMessage(error)`.
- MUST use semantic tokens through the primitives (don't restyle each `Input` with ad-hoc classes; change `components/ui/input.tsx` once).
- MUST use shadcn controls for every input type (Select, Checkbox, RadioGroup, Switch, Popover+Calendar…); never native `<select>`/checkbox or `alert()`/`confirm()`.
- MUST NOT use `useState` for field values, Yup/Valibot, manual `schema.parse` in components, `any` in error handlers, or `error.response.data`.
- MUST NOT show raw server/stack text; `ApiError.message` is already user-safe.
- Password fields: correct `autoComplete` (`current-password` / `new-password`); never log values.

## Checklist

- [ ] Schema in `features/…/schemas/*.schema.ts`, zod 4 API, descriptive messages
- [ ] Field names = API camelCase names; `*_FIELDS` list for server-error mapping
- [ ] Mutation hook in `features/…/hooks/`; success toast / invalidation there
- [ ] `<Alert>` for non-field errors, `<FormMessage/>` for field errors
- [ ] Responsive grid; keyboard + screen-reader friendly (labels, `aria-label` on the form)
- [ ] Missing shadcn primitives installed via CLI + `reactjs-ui-design` §3 post-install checklist
- [ ] Reviewed with `npm run ui:snapshot -- --route <path>` (light/dark, desktop/mobile, error state)
- [ ] Component test with `src/test/render.tsx` (see `LoginView.test.tsx`)
- [ ] `npm run typecheck && npm run lint && npm run test:ci` (apps/web) pass

Detailed rules: [references/form-rules.md](references/form-rules.md)
