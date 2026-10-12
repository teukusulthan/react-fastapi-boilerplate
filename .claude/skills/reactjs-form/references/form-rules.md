# Form — Rules & Constraints

Companion to [../SKILL.md](../SKILL.md). Reference code: `apps/web/src/features/shared/auth/`.
Visual rules (radius, spacing, states): [reactjs-ui-design](../../reactjs-ui-design/SKILL.md) §2, §5.4.

## Libraries

| ✅ Use | ❌ Don't |
|---|---|
| `react-hook-form` for state | `useState` per field, uncontrolled ad-hoc `ref`s |
| `zod` 4 + `zodResolver` | Yup, Valibot, manual `schema.parse` in components |
| `@/components/ui/form` wrappers | bare `register()` without `<FormField>` (loses aria wiring + `<FormMessage>`) |
| `useMutation` + service | `axios`/`fetch` in components |
| `ApiError` helpers (`getErrorMessage`, `applyApiFieldErrors`) | `error.response.data.message`, `catch (error: any)` |
| `toast` from `sonner` | any other toast system (there is no `use-toast`), `alert()` |
| shadcn `Select`, `Checkbox`, `RadioGroup`, `Switch`, `Popover` + `Calendar` | native `<select>`, `<input type="checkbox">` / `radio` / `date`, hand-built dropdowns |

Always: `noValidate` on `<form>`, `defaultValues` for every field, types from `z.infer`.

## Schemas

- Location: `src/features/{domain}/{feature}/schemas/{name}.schema.ts`; cross-domain →
  `src/schemas/{name}.schema.ts` (create on demand). Never inside a component, `utils/` or `types/`.
- Export `xxxSchema` and `TXxxFormValues = z.infer<typeof xxxSchema>`.
- Every rule has a human message. Trim strings that users type (`z.string().trim()`).
- zod 4: `z.email()`, `z.url()`, `{ error: 'msg' }` for custom messages; no `errorMap`.
- Mirror backend limits (lengths, password min length = `BE_PASSWORD_MIN_LENGTH`, default 8)
  so most errors are caught client-side; the backend stays authoritative.

## Server errors

Backend error envelope → `ApiError`:

| Case | Handling |
|---|---|
| 422 `VALIDATION_ERROR` with `data: [{ field, message }]` | `applyApiFieldErrors(error, form.setError, FIELDS)` → inline messages; returns `true` if any applied |
| 409 `CONFLICT` (e.g. email exists) | Usually also carries `[{ field, message }]` → same mapping; else `<Alert>` |
| 400 / 401 / 403 / 429 / 5xx / network | `<Alert variant="destructive">{getErrorMessage(error)}</Alert>` |
| Login-specific codes (`ACCOUNT_NOT_VERIFIED`) | Map to copy in the feature (`features/shared/auth/utils/login-errors.ts`) |

Field names in 422 details are API camelCase (`newPassword`, `filters[0].field`) — form
field names must use the same spelling to be mapped. Keep a `*_FIELDS` constant listing them.

## Layout

| ✅ | ❌ |
|---|---|
| `max-w-2xl` + `grid grid-cols-1 gap-4` / `sm:grid-cols-2` / `lg:grid-cols-3` | per-field widths (`w-1/2`) for layout, full-width inputs on wide screens |
| `sm:col-span-2` / `col-span-full` for long fields | margins between fields instead of `gap-*` |
| Server `Alert` above the grid, actions `flex justify-end gap-2` (primary rightmost) | multi-field forms without a layout wrapper |

## Styling

- Visuals come from the token-bound primitives (`components/ui/input.tsx`, `button.tsx`,
  `form.tsx`). Restyle the primitive once, not every usage.
- Missing primitives (select, textarea, checkbox…) are added with the shadcn CLI and then put
  through the post-install checklist in `reactjs-ui-design` §3 (Phosphor icons, `React.forwardRef`,
  semantic tokens: `border-input`, `bg-background`, `text-foreground`, `placeholder:text-muted-foreground`,
  `focus-visible:ring-ring/50`, `rounded-md`).
- Icons: Phosphor classes (`<i className="ph ph-spinner animate-spin" aria-hidden="true" />`). Never `lucide-react`.

## Definition of done

- [ ] Schema file in the feature, zod 4 API, inferred type
- [ ] `useForm({ resolver: zodResolver(schema), defaultValues })`
- [ ] `<Form>` + `<FormField>` + `<FormItem>` + `<FormLabel>` + `<FormControl>` + `<FormMessage>` for every field
- [ ] Mutation hook submits through a service; pending state disables submit
- [ ] 422/409 mapped to fields; other errors in an `Alert`; success via `toast`
- [ ] Responsive grid; works at 390px width; light + dark reviewed via `npm run ui:snapshot`
- [ ] Test covers validation + server error (see `features/shared/auth/components/LoginView.test.tsx`)
