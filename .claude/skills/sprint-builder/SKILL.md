---
name: sprint-builder
description: Initialize and maintain the per-project `sprint/` tree at `<cwd>/sprint/`, shared across every stack (frontend, backend, agent, mcp, mobile). Owns `01-sprint-planning.md` and the `backlog/`, `active/`, `archive/` sprint folders. The project's blueprint is NOT authored here — it is the output of `brief-builder` (see `<cwd>/brief/`). A single sprint can include any combination of stacks; each stack has its own subfolder of detailed task files. Use after the brief and design are satisfied (before app bootstrap), or whenever the user wants to draft a new sprint, add a stack to an existing sprint, promote backlog → active, or archive a finished sprint. Triggers: "buatkan sprint plan", "/setup-plan", "/add-sprint", "buat plan untuk feature X", "tambahkan task agent ke sprint Y", "promote sprint ke active", "archive sprint NN".
---

# Sprint Builder

Owns the **per-project** sprint tree at `<cwd>/sprint/`. One plan covers the whole project — frontend, backend, agents, MCP servers, mobile — with each stack getting its own subfolder of detailed task files inside each sprint.

> **Blueprint:** sprint-builder does **not** author the blueprint. The project's blueprint is whatever `brief-builder` produced — it lives at `<cwd>/brief/00_OVERVIEW.md` (with per-feature `NN_*.md` companions). All planning artefacts here reference that brief tree; if it's missing or thin, redirect to [`brief-builder`](../brief-builder/SKILL.md) before drafting any sprint.

## Directory layout

```
<cwd>/
├── brief/                            ← brief-builder output (the blueprint lives here)
│   ├── 00_OVERVIEW.md
│   └── NN_FEATURE.md                 (one per major feature)
└── sprint/
    ├── 01-sprint-planning.md         ← master tracking table for all sprints
    ├── backlog/                      ← all sprints start here
    │   └── NN-<sprint-slug>/
    │       ├── sprint.md             ← sprint-level overview (goal, acceptance, scope)
    │       ├── frontend/             ← only created if FE tasks exist
    │       │   ├── 01-<task>.md
    │       │   └── 02-<task>.md
    │       ├── backend/              ← only created if BE tasks exist
    │       ├── agent/                ← only created if agent tasks exist
    │       ├── mcp/                  ← only created if a new MCP must be built
    │       └── mobile/               ← only created if mobile tasks exist
    ├── active/                       ← user manually moves a sprint here when ready to start
    └── archive/                      ← completed sprints (moved here on close-out)
```

A sprint is the atomic unit of work; a stack is just a partition inside it. A sprint can be FE-only, BE-only, agent-only, or any combination — only the relevant stack subfolders get created.

> **Single source of truth for feature spec is `<cwd>/brief/NN_<FEATURE>.md`.** No sprint-scoped feature-briefs layer. If a sprint needs more granular decomposition than the project brief, that detail goes into the task files themselves (`backlog/NN-*/<stack>/*.md`), not into a separate sprint-scoped brief.

> **Task files are specs; code is the deliverable.** A task file at `<cwd>/sprint/backlog/<sprint>/agent/01-foo.md` describes what to build. The actual code lives elsewhere — `<cwd>/apps/web/src/...` for FE, `<cwd>/apps/backend/...` for BE routes (`router/`, `service/`, `dto/`, `db/schema.py`, `migrations/supabase/`), `<cwd>/apps/agents/<role>/agent.py` for an agent (its own project, scaffolded from `agent-python/`), `<cwd>/apps/mcp/<server>/server.py` for a pure-tool MCP. The task file is the contract; the code is what closes it.

## Naming

- Sprint folder: `NN-<kebab-slug>` — zero-padded, ≤ 3-word slug. Example: `01-auth`, `02-dashboard`, `03-tender-crawler`.
- Sprint overview file: always `sprint.md` inside the sprint folder.
- Stack subfolder: lowercase singular — `frontend`, `backend`, `agent`, `mcp`, `mobile`.
- Task files inside a stack: `NN-<kebab-slug>.md` — sequence matters; each task is a contained checklist.

> **Language convention:** templates and procedural prose are English. Brief content (Indonesian) and any per-feature briefs follow the brief-builder language convention.

## Workflow

### Step 1 — Initialize the sprint tree

Pre-condition: `<cwd>/brief/` exists (from `brief-builder`). If it doesn't, redirect to `brief-builder` first — never draft a plan without a confirmed brief.

```bash
mkdir -p <cwd>/sprint/backlog <cwd>/sprint/active <cwd>/sprint/archive
```

Create `<cwd>/sprint/01-sprint-planning.md` from [references/sprint-planning-template.md](references/sprint-planning-template.md). The table starts empty and grows as sprints are added. The template includes a header pointer to `<cwd>/brief/00_OVERVIEW.md` so any reader knows where the blueprint actually lives.

### Changelog files

Every project has four changelog files at `<cwd>/changelog/`:

| File | Updated when |
|------|-------------|
| `changelog/web.md` | A frontend task is created or completed |
| `changelog/backend.md` | A backend or agent/MCP task is created or completed |
| `changelog/mobile.md` | A mobile task is created or completed |
| `changelog/sprint-planning.md` | A sprint is created, promoted, archived, or cancelled |

**Append entry format** (add at the top, below the header block):

```markdown
### YYYY-MM-DD · [Sprint NN — slug](../sprint/{location}/NN-slug/sprint.md) · Task: [task title](../sprint/.../stack/NN-task.md) · 📋 Added | ✅ Done

**Event:** Task created | Task completed
**Files:** `relative/path/to/file.ext`
> One-line summary of what changed or was delivered.
```

Sprint-planning entries use a simpler format:

```markdown
### YYYY-MM-DD · Sprint NN — slug · EVENT

**Event:** Sprint created | Promoted to active | Archived | Cancelled
**Sprint:** [NN-slug](../sprint/{location}/NN-slug/sprint.md)
> One-line reason or outcome.
```

**Rules:**
- Append-only — never delete or rewrite existing entries.
- Newest entry at the top (below the header block).
- `{location}` = `backlog` | `active` | `archive` depending on current sprint state.
- Agent and MCP tasks map to `changelog/backend.md` (they are backend-layer concerns).

---

### Step 2 — Draft sprints from the brief

Inputs:
- `<cwd>/brief/00_OVERVIEW.md` (the blueprint) and `<cwd>/brief/NN_*.md` (per-feature detail).
- `<cwd>/design/` (HTML mockups, if present) — especially `<cwd>/design/flow.json`.
- The boilerplate orientation report from `bootstrap-project` (when an app already exists).

For each major capability in the brief, create a sprint. Per sprint:

1. Pick a slug. Example: `auth`, `tender-crawler`, `reports`.
2. Decide which stacks the sprint touches. Examples:
   - "Login UI" → frontend only.
   - "Login API + JWT cookie" → backend only.
   - "Login + register + password reset" → frontend + backend.
   - "Tender intake from LPSE" → mcp + agent + backend (and maybe frontend for the "trigger" button).
3. Create the sprint folder `<cwd>/sprint/backlog/NN-<slug>/sprint.md` from [references/sprint-template.md](references/sprint-template.md).
4. For each stack in scope, create the subfolder and one or more task files from [references/task-template.md](references/task-template.md). Each task file lists files to touch, skills to consult, and a done-when assertion. Detail granularity beyond the project brief lives **inside these task files**, not in a separate sprint-level brief layer.
5. Append a row to `<cwd>/sprint/01-sprint-planning.md`'s table with the brief link, the backlog folder link, and `📋 Planned` status.
6. **Append to `<cwd>/changelog/sprint-planning.md`** one entry per new sprint (event: `Sprint created`).
7. **Append to the stack-specific changelog** (`web.md`, `backend.md`, `mobile.md`) one entry per task file created (event: `Task created`). Agent and MCP tasks map to `backend.md`.

Keep tasks concrete and ≤ 1 day each. If a task balloons during execution, split it inline.

#### Auto-generated FE tasks from `<cwd>/design/`

When `<cwd>/design/` exists, the **first frontend sprint** must include two extra task types — they're cheap to spec and they prevent UI/design drift later:

- **`port-design-tokens.md`** — swap `<cwd>/apps/web/src/styles/variable.css` (design tokens; Tailwind mapping in `src/styles/tailwind.css`) with values from `<cwd>/design/tokens.css`. Done-when: the dev-mode app visually matches the mockup's color/spacing/type scale.
- **`wire-<screen-id>.md`** — one task per entry in `<cwd>/design/flow.json`'s `screens[]`. Each task wires the route and nav links per `flow.json`'s `transitions[]`. Done-when: the route renders and nav transitions fire as `flow.json` describes.

If `<cwd>/design/` doesn't exist, skip both — applies only to design-driven projects.

#### Workforce-aware sprint composition

Argus apps are **agent-driven by default** — the brief's `## Workforce Manifest` at [`<cwd>/brief/00_OVERVIEW.md`](../../skills/brief-builder/SKILL.md) lists workforce members (PM/orchestrator, ops triple monitor/validator/notifier, DE, crawler, analyzer, reporter, be_service, fe_shell, etc.). Every sprint must cross-check the workforce table and add **foundation tasks** when cross-stack data sharing occurs.

##### Sprint 00 — workforce scaffold (mandatory if brief Workforce includes agents)

**Axiom "no human maintainer":** apps run via agents. Agents need a management plane to register, run, schedule, and escalate. Without an initial scaffold, downstream feature agents have no backbone to run autonomously.

#### Adapting to this repository

This repository's backend (`apps/backend`, FastAPI on port 8020) does **not** ship an agent-management (`agent_mgmt`, `/agent-mgmt/*`) module, and there is no `apps/agents/` or `apps/mcp/` yet. In `00-workforce-scaffold` the backend task therefore **creates** that module as a regular backend resource (`fastapi-crud-collection`: entities in `db/schema.py`, `migrations/supabase/00N_agent_mgmt.sql`, `router/` + `service/` + `dto/`, `RouterSpec("agent_mgmt", "router.agent_mgmt")`), protected with `require_internal_token` / `require_user_or_internal` (`core/deps.py`). The shared secret is `BE_INTERNAL_TOKEN` in `apps/backend/.env`. Pure CRUD projects skip all of this.

**Rule:** if the brief's Workforce Manifest contains **any agent role** (other than `pm`, `be_service`, `fe_shell`), the project's first sprint **MUST** be `00-workforce-scaffold` before any feature sprint is promoted to `active/`. This sprint scaffolds the management plane + ops backbone.

**Sprint `00-workforce-scaffold` content:**

```
backlog/00-workforce-scaffold/
├── sprint.md
├── backend/
│   ├── 00-agent-mgmt-enabled.md       (Foundation: yes — this boilerplate's backend has NO agent_mgmt
│   │                                   module: create it (entities in db/schema.py, migration
│   │                                   migrations/supabase/00N_agent_mgmt.sql, router/service/dto,
│   │                                   RouterSpec("agent_mgmt", ...)), verify /agent-mgmt/healthz,
│   │                                   BE_INTERNAL_TOKEN set (npm run setup:backend generates it).)
│   └── 01-agent-integration-glue.md   (Foundation: yes — apps/backend/{router,service,dto}/agent.py
│                                       call the agent_mgmt service directly, no httpx loopback.
│                                       Depends on: ./00-agent-mgmt-enabled.md)
├── agent/
│   ├── 01-pm-orchestrator.md          (Depends on: ../backend/00-agent-mgmt-enabled.md —
│   │                                   first agent registered at /agent-mgmt/agents)
│   ├── 02-monitor.md                  (ops triple — only if brief Workforce includes the triple)
│   ├── 03-validator.md                (ops triple — only if brief Workforce includes the triple)
│   └── 04-notifier.md                 (ops triple — only if brief Workforce includes the triple)
└── frontend/
    └── 00-agent-run-renderer.md       (Foundation: yes — types/agent.d.ts + useAgentRun hook + AgentOutputRenderer)
```

**Contract delivered:**
- `<cwd>/apps/backend/` running on port 8020 with an `agent_mgmt` router serving `/agent-mgmt/*` (registry/runs/schedules/webhooks/DLQ endpoints + autonomy fields in the schema). **Not shipped by this boilerplate** — the sprint creates it as a regular backend module (`fastapi-crud-collection`); no standalone be-agent service.
- Scheduler tick loop started from the backend lifespan (`core/app_factory.py`).
- `BE_INTERNAL_TOKEN` set in `<cwd>/apps/backend/.env` and propagated as `INTERNAL_API_TOKEN` to every `<cwd>/apps/agents/<role>/.env`.
- `<cwd>/apps/agents/pm/` registered as orchestrator (route requests + escalation) via `POST /agent-mgmt/agents`.
- Ops triple agents registered (if brief Workforce includes the triple), with monitor's schedule active.
- `<cwd>/apps/backend/service/agent.py` (new file) — AgentService (FE-facing camelCase DTOs) calling the agent_mgmt service directly.
- `<cwd>/apps/web/src/types/agent.d.ts` (new file) + `useAgentRun` + `AgentOutputRenderer` — consumed by downstream FE features.

**Skip conditions:** if brief Workforce only contains `pm + be_service + fe_shell` (pure CRUD app, no agents), sprint 00 reduces to a standard `00-bootstrap-fe-be.md`. If the brief explicitly declares "POC, no autonomous ops", still create the agent_mgmt module + scaffold `pm`, but skip the ops triple.

**When a sprint touches data shared across workforce members** (typical: an agent writes to the DB → BE reads → FE renders), **stacks do NOT run in parallel** until the foundation contracts are locked in:

1. Identify the **workforce members** this sprint touches (refer to `## Workforce Manifest` in the brief).
2. Identify the **data contracts** that are shared — DB tables, MCP tool signatures, API types.
3. Create a **foundation task** per contract — placed in the stack that **owns** the contract.
4. Mark dependent tasks with `Depends on: ../<stack>/00-<...>.md`.
5. Foundation must be `[x]` before dependents start.
6. After foundations `[x]`, dependent stacks run in parallel against the locked contracts.

**Canonical foundation tasks:**

| Foundation | Stack | Path output | Blocks |
|---|---|---|---|
| App-domain DB schema | backend | `<cwd>/apps/backend/db/schema.py` entity + `<cwd>/apps/backend/migrations/supabase/NNN_<feature>.sql` | agent ingest tasks (write), agent read tasks, BE read endpoints, FE wiring |
| Agent MCP tool signatures | agent | `<cwd>/apps/agents/<role>/server.py` (tool signatures + docstring; body TODO) | BE handlers calling the agent, FE buttons triggering the agent, sibling agents chaining to this role |
| Shared API types | backend | `<cwd>/apps/backend/dto/<feature>.py` + `docs/api/<feature>.md`, mirrored in `<cwd>/apps/web/src/types/models.d.ts` (or pydantic→openapi→ts) | FE typed API client |

**Foundation task bodies must include a `## Contract delivered` section** that spells out what downstream consumers will read (schema columns, server.py signatures, API type fields).

**Typical sprint structure for a shared-data sprint** (agent-first thinking):

```
backlog/NN-<feature>/
├── sprint.md
├── backend/
│   ├── 00-schema-<feature>.md      (Foundation: yes — produces apps/backend/migrations/supabase/... + db/schema.py)
│   └── 01-<feature>-routes.md      (Depends on: ../backend/00-schema-<feature>.md)
├── agent/
│   ├── 00-mcp-contract-<role>.md   (Foundation: yes — server.py signatures)
│   ├── 01-<role>.md                (Depends on: ../backend/00-schema-<feature>.md, ./00-mcp-contract-<role>.md)
│   └── 02-<sibling-role>.md        (Depends on: ./01-<role>.md for sequential agent chain)
└── frontend/
    └── 01-<feature>-list.md        (Depends on: ../backend/01-<feature>-routes.md)
```

Sprints **without** workforce sharing (FE-only login UI tweaks, BE-only rate-limit middleware) remain valid — foundation flag `no`, all stacks parallel as before.

> **Cross-reference:** the `/bootstrap-project` command (`.claude/commands/bootstrap-project.md`) and [`agent-builder`](../agent-builder/SKILL.md) read the brief's Workforce Manifest for context. [`agent-builder`](../agent-builder/SKILL.md) Pre-Step 1 check: is the schema foundation task `[x]`?

#### Step 2b — After `00-workforce-scaffold` is `[x]`, hand off to agent-builder per role

When all tasks in `00-workforce-scaffold` reach `[x]`, the project has: the backend running with the `agent_mgmt` module, PM orchestrator registered, and ops triple agents (if the brief specifies) registered with their schedules active.

**Next:** for each remaining domain agent role in the Workforce Manifest (crawler, analyzer, reporter, etc.), invoke [`agent-builder`](../agent-builder/SKILL.md) to scaffold the specialist at `<cwd>/apps/agents/<role>/`. Domain agents are scaffolded **after** the workforce-scaffold sprint, not in parallel with it. Each domain agent enters via a feature sprint task `agent/NN-<role>.md` that names the role + its dependencies.

### Step 3 — Promote a sprint to active

When the user says "let's start sprint NN":

```bash
mv <cwd>/sprint/backlog/NN-<slug> <cwd>/sprint/active/
```

Update `<cwd>/sprint/01-sprint-planning.md`: change the sprint's status from `📋 Planned` to `🚧 In Progress`, set `Started At`, update the folder link to `./active/NN-<slug>/`. Only **one** sprint should live in `active/` at a time.

**Append to `<cwd>/changelog/sprint-planning.md`** one entry (event: `Promoted to active`).

### Step 4 — Execute

For each stack subfolder in the active sprint, work the task files in order:
- Mark `- [ ]` → `- [x]` only when the **done-when** assertion passes (build green, tests green, manually verified).
- **When closing a task as done:**
  1. Re-open the task file itself — do not rely on memory of its prior state.
  2. Mark **every** `- [ ]` item in the task file's `## TODOs` section as `- [x]` — no unchecked TODO may remain in a completed task.
  3. Update the task's top-level **Status** header field to `✅ Done`.
  4. **Append to the stack's changelog** (`web.md`, `backend.md`, or `mobile.md`) one entry with event `Task completed`, listing the files touched. Agent/MCP tasks map to `backend.md`.
  5. Re-read the task file header and `## Closing checklist`, then sync the checklist to the real file state. If the header still says `📋 Planned` or `🚧 In Progress`, the line `Status field updated to \`✅ Done\`` must remain unchecked.
  6. Only after steps 1-5 are true may the task be treated as complete in the final response.
- Append-only revisions: never delete or rewrite an existing task — add a `## Revision <date>` section at the bottom if scope changes.
- Add running notes under each task's **Notes** section.
- **Foundation tasks first.** Tasks with `Foundation: yes` must be `[x]` before any dependent task starts. Once foundations are `[x]`, dependent stacks run in parallel.
- **Cross-stack parallelism after foundations done.** Backend dev works `backend/` while agent dev works `agent/` — fine as long as both depend on the same foundation and the foundation is already `[x]`.

### Step 5 — Archive

When all tasks across all stacks in `<cwd>/sprint/active/NN-<slug>/` are `[x]`:

```bash
mv <cwd>/sprint/active/NN-<slug> <cwd>/sprint/archive/
```

Update `<cwd>/sprint/01-sprint-planning.md`: status `✅ Done`, set `Completed At`, fix the link to `./archive/NN-<slug>/`. Add a one-paragraph outcome summary at the bottom of `archive/NN-<slug>/sprint.md`.

**Append to `<cwd>/changelog/sprint-planning.md`** one entry (event: `Archived`, include one-line outcome summary).

## Rules

- **Never generate plan files without an explicit confirmed brief.** If `<cwd>/brief/` is missing, stop and redirect.
- **Default: all sprints go to `backlog/`** — the user (or AI on user's confirmation) moves them to `active/` when ready.
- **Only one sprint in `active/`** at a time. If a second sprint must run in parallel, that's a signal to merge or split — flag to the user.
- **Stack subfolders only for active platforms.** Don't pre-create empty `frontend/` / `backend/` / etc.
- **Append-only revisions.** Don't overwrite existing content; add `## Revision <date>` sections.
- **No premature `[x]`.** Tasks check off only when their done-when assertion verifies (build/test/manual).
- **All TODOs must be checked when closing a task.** A task file's status may only be set to `✅ Done` once every `- [ ]` item in its `## TODOs` section has been marked `- [x]`. If a TODO was skipped or deferred, move it to a `## Revision <date>` section before closing.
- **Status/header truth beats checklist text.** The authoritative completion signal is the task file's top-level `**Status:** ✅ Done`. A checked line saying `Status field updated to \`✅ Done\`` is invalid if the header was not actually changed.
- **Closing checklist is evidence, not intent.** Never tick a closing-checklist line for work you merely plan to do next. Perform the action first, then check the line that documents it.
- **No final response before closure sync.** If implementation was driven by a sprint task file, the task is not done until the task file, changelog, and relevant sprint tracking docs are synchronized.
- **Always update the changelog.** Every task creation → domain changelog `📋 Added` entry. Every task completion → domain changelog `✅ Done` entry. Every sprint lifecycle event → `changelog/sprint-planning.md` entry.
- **Architecture references at high level only** in `01-sprint-planning.md` and `sprint.md`. Library names, ORM specifics, code-level details belong in the per-stack task files, not in the higher-level docs.
- **Cross-reference chain**: `brief → sprint-planning → sprint → task`. Changes propagate; if a brief revision changes scope, flag the affected sprints.
- **Don't author the blueprint.** Treat `<cwd>/brief/` as read-only when planning. If it needs changes, redirect to `brief-builder`.
- **Tasks always link to skills**, not external docs. A task references the project's own boilerplate skills (`.claude/skills/<skill>/SKILL.md`, e.g. `fastapi-crud-collection`, `reactjs-administrator`; agent projects may carry `<cwd>/apps/agents/<role>/skills/<domain>/SKILL.md`) or sandbox-level skills (`agent-builder`, `mcp-builder`). If the relevant skill doesn't exist, that's a finding to surface to the user.
- **Don't pre-fill `archive/`.** Sprints earn their way there.
- **Keep `01-sprint-planning.md` lean.** It's a navigation surface — detail lives in sprint folders.
- **Workforce scaffold sprint first.** If the brief Workforce contains any agent role (other than pm/be_service/fe_shell), `00-workforce-scaffold` is the first sprint. Feature sprints whose `Depends on:` references an unscaffolded agent must not be promoted to `active/`.

### Anti-pattern: human runbook tasks

Argus apps have no ops team at runtime. Task files must not generate "human runbooks" that imply manual maintenance.

❌ **Anti-pattern (do not write):**
- Task "Set up server cron job, document restart procedure"
- Task "Write runbook for on-call engineer to check Grafana logs"
- Task "Ops team reviews failed runs daily and retries manually"
- Task "Operator tunes alert threshold based on feedback"
- Task "Engineer checks webhook delivery in Slack channel"

✅ **Reframe to agent-driven (always do this):**
- Task "Configure scheduler agent (cron expr in `agent_schedules` table) — auto-fire crawler at 06:00"
- Task "Implement monitor agent rule: stall detection > 30 min → fire notifier"
- Task "Implement retry policy in the backend agent_mgmt module (`max_retries`, exponential backoff)"
- Task "Implement learning agent that reads `agent_runs.metrics` and proposes threshold updates via PATCH /agents/{id}"
- Task "Configure notifier agent webhook route to Slack — auto-fanout on escalation events"

**Rule:** if a task TODO contains words like "operator", "engineer review", "manual restart", "ops team", "on-call check" — that's a signal the task must be reframed to an agent. Surface to the user if ambiguous.

## Templates

- [references/sprint-planning-template.md](references/sprint-planning-template.md) — `01-sprint-planning.md` skeleton (the master table).
- [references/sprint-template.md](references/sprint-template.md) — per-sprint `sprint.md` skeleton.
- [references/task-template.md](references/task-template.md) — per-stack task file skeleton.

> No blueprint template — the blueprint is sourced from `<cwd>/brief/00_OVERVIEW.md` (output of [`brief-builder`](../brief-builder/SKILL.md)).

## Multi-session resumption

A new session can determine sprint state by reading `<cwd>/sprint/01-sprint-planning.md` (the master table) and inspecting `<cwd>/sprint/active/`, `<cwd>/sprint/backlog/`, `<cwd>/sprint/archive/` directly. No external state file is needed — the filesystem is the SSOT.
