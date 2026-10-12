# Task {NN} — {Title}

**Stack:** frontend | backend | agent | mcp | mobile
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** 📋 Planned | 🚧 In Progress | ✅ Done
**Foundation:** yes | no
**Autonomous:** yes | no — {if no, explain why: one-time setup, throwaway tooling, etc.}
**Depends on:**
- [`../<stack>/<NN-task>.md`](../<stack>/<NN-task>.md) — {why this is a dependency}

> **Foundation task** = a task that produces a **contract** which downstream tasks (in other stacks) depend on. Always numbered `00-` (sorts first); lives in the stack that **owns** the contract.
> - Foundation: yes → must be `[x]` before any task whose `Depends on:` references it can start.
> - Foundation: no → default. No special blocking semantics.
>
> **Autonomous: yes** (default expectation) = the task's output auto-operates at runtime without human intervention. Output can be: agent code, scheduler config, monitor rule, validator policy, notifier route, MCP tool wrapper, BE thin glue, FE rendering.
> **Autonomous: no** = a one-time setup task (e.g., bootstrap supabase instance, populate seed data, manual schema review). A justification is REQUIRED on the same line. Must NOT be reframeable as an agent task.
>
> ❌ **Anti-pattern:** task TODOs containing "ops engineer review logs", "manual cron tuning", "on-call retry", "operator check Grafana". Argus apps have no ops team at runtime. See the sprint-builder Anti-pattern section.
>
> **Depends on:** zero or more lines linking other tasks (typically foundation tasks). Omit the section if the task is standalone.

## Goal

{One sentence — the technical outcome of this task. Concrete enough that "done" is unambiguous.}

## Contract delivered (foundation tasks only)

> **Skip this section when Foundation: no.**
>
> For foundation tasks, spell out what downstream consumers will read:
> - **Schema migration**: table columns + types + constraints + indexes + RLS policies.
> - **MCP tool signatures**: tool names + parameter signatures + return types + docstrings (the body may be TODO).
> - **API types**: pydantic models / TypeScript interfaces that FE will import.

## Files to touch

- `path/to/file1.ext` — {what changes}
- `path/to/file2.ext` — {what changes}

## Skills to consult

- `<sandbox>/skills/<domain>/SKILL.md` (or `<cwd>/apps/<role>/skills/<domain>/SKILL.md`) — {why}
- `<sandbox>/skills/<other>/SKILL.md` — {why}

## TODOs

- [ ] {Concrete sub-step. Implementation-level OK — this file is the technical layer.}
- [ ] {Sub-step.}
- [ ] {Sub-step.}

## Done when

{Observable assertion: "POST /api/auth/login with valid creds returns 200 + Set-Cookie", "form validation shows error under invalid email", "agent run on the test fixture URL returns markdown matching the structure in the spec".}

## Closing checklist

> Complete these steps **in order**. These checkboxes are evidence of work already performed in this file, not reminders of work still to do.
>
> The task is only truly complete when the header at the top of this file literally reads `**Status:** ✅ Done`.

- [ ] All `## TODOs` items above are `[x]` — no unchecked item may remain (defer via `## Revision <date>` if needed)
- [ ] Done-when assertion verified (build/test/manual)
- [ ] Top-of-file header literally reads `**Status:** ✅ Done` (change the header first, then check this line)
- [ ] Changelog entry appended to `<cwd>/changelog/{web|backend|mobile}.md` (event: Task completed)

## Notes

(Surprises, blockers, follow-ups during execution. Append-only.)
