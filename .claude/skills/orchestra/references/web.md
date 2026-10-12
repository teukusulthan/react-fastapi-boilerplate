# Web Agent

Handles all frontend web tasks in `apps/web/` (React 18 + Vite 7). Other `apps/web*` folders may be added by a project; detect them by content.

---

## Step 0 — Read the guides

1. **UI task?** `.claude/rules/web/ui-design.md` + the [`reactjs-ui-design`](../../reactjs-ui-design/SKILL.md) playbook first (visual direction, shadcn-first component priority, page recipes, review loop).
2. `apps/web/AI_GUIDE.md` — structure, file locations, critical rules.
3. `.claude/rules/web/orchestra.md` and `.claude/rules/architecture.md` (stack enforcement, component placement, config-driven menus, scroll areas).
4. When calling the backend: `docs/api-spec.md` + `docs/api/<module>.md` (or the live Swagger at `http://localhost:8020/docs`).

---

## Step 1 — Detect Active Web Stack

| Indicator file | Stack |
|----------------|-------|
| `vite.config.ts` + `react` in `package.json` | React + Vite (this boilerplate) |
| `rsbuild.config.ts` or `rspack.config.ts` | React + Rsbuild/Rspack |
| `next.config.js` or `next.config.ts` | Next.js |

---

## Step 2 — Pick the skill(s)

| Task | Skill |
|------|-------|
| **Any UI** — page, screen, dashboard, form, table, dialog, restyle, "make it look better" | **`reactjs-ui-design` first**, then the placement/behavior skills below |
| Where a file goes / naming | `reactjs-architecture`, then `reactjs-features` or `reactjs-modules` |
| New page / route | `reactjs-app-layout` + `reactjs-menu-config` (route and menu in the same change) |
| Sidebar / header shell | `reactjs-sidebar`, `reactjs-app-layout` |
| Calling an endpoint (service, endpoint constants, types) | `reactjs-service`, `reactjs-api-design` |
| Server state (queries, mutations, cache) | `reactjs-tanstack-query` |
| Client state (Zustand) | `reactjs-state-management` |
| Login / guards / roles | `reactjs-auth-guard` |
| Errors, toasts (sonner), error boundaries | `reactjs-error-handling` |
| Forms (react-hook-form + zod 4) | `reactjs-form` |
| Admin CRUD list page under `/administrator/*` | `reactjs-ui-design` §5.3 + `reactjs-administrator` (+ `reactjs-data-display` → `src/modules/data-table/`, `reactjs-dynamic-filter`) |
| Charts (ECharts) | `reactjs-chart` |
| Maps (Mapbox) | `reactjs-map`, `reactjs-tactical-map` |
| Icons | `reactjs-icon` |
| Env vars (`VITE_*`) | `reactjs-manage-env` |
| `index.html` meta / SEO | `reactjs-seo-html`, `meta-seo` |
| Responsive layout / scroll areas | `reactjs-responsive` |
| Visual design / theme | `reactjs-ui-design` (always), then `reactjs-design-system` (tokens/re-brand), `reactjs-switch-theme`, `reactjs-slicing-ui` (Figma/mockup → React), `reactjs-anti-slop` (quality gate) |
| HTML mockup → React | `html-to-react` |

---

## Step 3 — Verify

From the repo root: `npm run typecheck`, `npm run lint`, `npm run format:check`, `npm run test`, `npm run build` (or everything with `npm run ci`).
Inside `apps/web`: `npm run typecheck`, `npm run lint`, `npm run test:ci`, `npm run build`.
Manual check: `npm run dev` (web on http://localhost:3000, backend on :8020 behind the `/api/v1/apps` proxy).
UI review (mandatory for UI work): `npm run ui:snapshot -- --route <path>` in `apps/web`, open every PNG and check it against `reactjs-ui-design` §8. `/ui-kit` (dev builds) shows every primitive and pattern.

---

## HTML-only deliverables (mockup / slicing, no app bundle)

Only when the user **explicitly** asks for **static HTML** at repo level (an "HTML mockup" or workspace PoC, not React under `apps/web`) — use the **[`/html-ui-slicing`](../../../commands/html-ui-slicing.md)** command and run **Step 0** to pick Mode A vs B; for Mode B follow **[`workspace-spec-poc.md`](../../html-ui-slicing/references/workspace-spec-poc.md)**.

Skip Step 1 stack detection if the user scope is explicitly static HTML only; resume normal web routing if they ask to port that HTML into `apps/web`.

---

## Never

- Apply Next.js patterns to a Vite project or vice versa
- Import from non-approved libraries — check `.claude/rules/architecture.md` first
- Use inline styles — use semantic token classes (`bg-card`, `text-muted-foreground`, `border-border`, …)
- Hand-build a control shadcn provides (select, dropdown, dialog, tabs, tooltip, checkbox, date picker…) — use or install the shadcn primitive
- Call `axios`/`fetch` from components — all API calls go through `src/services/*` and TanStack Query hooks
- Read env vars anywhere except `src/config/env.ts`
- Load `design/design-system.md` for non-UI tasks
