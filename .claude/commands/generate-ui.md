# Command: /generate-ui

Generates a React UI component, view or page in `apps/web` (React 18 + Vite) that looks modern,
minimal and slightly rounded, built shadcn-first.

## Trigger
`/generate-ui [component_or_page_name] [short description]`

## Read first
1. `.claude/rules/web/ui-design.md` (always-on visual rules).
2. `.claude/skills/reactjs-ui-design/SKILL.md` (the playbook: tokens, component priority, page recipes,
   states, review loop).
3. `.claude/rules/architecture.md` § Component Placement — decide where the file goes before writing.

## Execution Steps
1. `<thinking>` Classify the target: shadcn primitive (`src/components/ui/`), generic page pattern
   (`src/components/common/`), generic system (`src/modules/<name>/`), or domain UI
   (`src/features/<domain>/<feature>/components/`). Pick the matching page recipe from the playbook §5
   (dashboard, list/CRUD, form, detail, auth) if it is a view.
2. Check `src/components/ui/` for the primitives you need. If shadcn has one that is missing, install it
   (`cd apps/web && npx shadcn@latest add <name>`) and apply the post-install checklist (Phosphor icons
   instead of `lucide-react`, `React.forwardRef` for React 18, semantic tokens, `@/utils/cn`).
3. Compose from `PageHeader`, `StatCard`, `EmptyState`, `SectionCard`, `StatusBadge`, `ConfirmDialog`
   (`src/components/common/`) and `DataTable` (`src/modules/data-table/`) before writing new markup.
4. Write the component with a typed `Props` interface (types/constants in their own files, not inline).
   Style only with shadcn semantic classes (`bg-card`, `text-muted-foreground`, `border-border`, …),
   `rounded-md` controls / `rounded-xl` surfaces, Phosphor icons.
5. Cover every state: skeleton loading shaped like the content, `EmptyState`, destructive `Alert` with
   retry, disabled, focus-visible.
6. If it is a page: route **and** menu entry (`src/config/menu/*`).
7. Review loop: `npm run ui:snapshot -- --route <path>` (use `/ui-kit` for a standalone component),
   open the PNGs (light/dark, desktop/mobile), fix against the playbook §8 checklist, then
   `npm run typecheck && npm run lint && npm run test:ci`.

## Output Format
The `.tsx` file(s), an `index.ts` export if the folder uses one, and a short note of what you reviewed
in the snapshots.
