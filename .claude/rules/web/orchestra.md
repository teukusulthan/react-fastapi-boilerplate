# Orchestra — Rules › Web

> Read this file FIRST before any web work, then load the smallest set of rules and skills the task
> needs.

## Installed web app

| App | Template | Path |
|-----|----------|------|
| React + Vite SPA | `web-reactjs` | `apps/web/` |

Template-specific nested rule folders (such as a `reactjs/` subfolder here) are **not** used. The durable
web rules live in `.claude/rules/architecture.md`, `.claude/rules/web/ui-design.md` (visual rules, always
on) and `apps/web/AI_GUIDE.md`. React skills are flat
folders: `.claude/skills/reactjs-<topic>/SKILL.md`.

## What to read next

| Task type | Read next |
|-----------|-----------|
| **Any UI task** (create/build/design/restyle a page, screen, dashboard, form, table, dialog, component; "make it look better"; "buatkan ui/halaman") | `.claude/rules/web/ui-design.md` + `.claude/skills/reactjs-ui-design/SKILL.md` **first**, then the placement/data skills below. Finish with the review loop (`npm run ui:snapshot`). |
| Any web implementation or bug fix | `.claude/rules/architecture.md` (Web UI + Component Placement) → `apps/web/AI_GUIDE.md` §1–§4 |
| Page, route, layout or component work | `apps/web/AI_GUIDE.md` §5.1 + `.claude/skills/reactjs-architecture/SKILL.md` |
| New user-facing page/route | `.claude/skills/reactjs-app-layout/SKILL.md` and `.claude/skills/reactjs-menu-config/SKILL.md` |
| Navigation/menu work | `.claude/skills/reactjs-menu-config/SKILL.md` (+ `.claude/skills/reactjs-sidebar/SKILL.md`) |
| Calling the backend | `apps/web/AI_GUIDE.md` §5.2 + `docs/api-spec.md` + `.claude/skills/reactjs-service/SKILL.md` + `.claude/skills/reactjs-tanstack-query/SKILL.md` |
| Feature folder | `.claude/skills/reactjs-features/SKILL.md` |
| Forms | `.claude/skills/reactjs-form/SKILL.md` (visuals: `reactjs-ui-design` §5.4) |
| Guards / roles | `.claude/skills/reactjs-auth-guard/SKILL.md` |
| Admin CRUD pages | `.claude/skills/reactjs-ui-design/SKILL.md` §5.3 + `.claude/skills/reactjs-administrator/SKILL.md` |
| Tokens / re-branding / theme switch | `.claude/skills/reactjs-ui-design/SKILL.md` §2, then `.claude/skills/reactjs-design-system/SKILL.md` or `.claude/skills/reactjs-switch-theme/SKILL.md` |
| Figma / mockup → React | `.claude/skills/reactjs-ui-design/SKILL.md`, then `.claude/skills/reactjs-slicing-ui/SKILL.md` |
| Lists / tables | `.claude/skills/reactjs-ui-design/SKILL.md` §5.3 + `.claude/skills/reactjs-data-display/SKILL.md` (`src/modules/data-table/`) |
| Env variables | `.claude/skills/reactjs-manage-env/SKILL.md` |

The full skill map is in `apps/web/AI_GUIDE.md` §10.

## Navigation Contract

- Treat `src/config/menu/*` (`app.menu.ts` → `APP_MENU`, `administrator.menu.ts` → `ADMINISTRATOR_MENU`)
  as the source of truth for navigable pages.
- When you add a user-facing route, wire the route (`src/routes/*.routes.tsx`) and the menu in the same
  unit of work.
- Hidden routes are opt-in: skip menu wiring only when the task explicitly says the route is hidden,
  redirect-only, modal-only, or otherwise non-navigable. Public auth routes (`/auth/*`) are entry points
  and are not in the menu.

## UI requests

In this repo, "build/create/design a UI, page or screen" means the **React app in `apps/web`**. Use the
HTML mockup skills (`html-ui-styling`, `html-ui-slicing`) only when the user explicitly asks for an HTML
mockup/static HTML.
