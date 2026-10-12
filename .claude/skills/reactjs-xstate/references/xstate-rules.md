# XState — Rules & Constraints

## Allowed

### Machine Definition

| # | Rule |
|---|------|
| ✅ | Define machines in `src/features/{domain}/machines/{name}.machine.ts` |
| ✅ | Declare all states, events, and context types explicitly using the `types` field |
| ✅ | Use `assign` from xstate to update context — never mutate context directly |
| ✅ | Use guards to block invalid transitions based on context or event payload |
| ✅ | Initialize machine from persisted server status when the process is server-stored |
| ✅ | Export machine as a named const (`export const xyzMachine = createMachine(...)`) |

### React Integration

| # | Rule |
|---|------|
| ✅ | Use `useMachine` from `@xstate/react` to bind machines to components |
| ✅ | Derive permission-gated UI from `state.matches(...)` + role checks |
| ✅ | Persist state transitions to backend via `useMutation` in `useEffect` on `state.value` change |
| ✅ | Keep machine re-use in mind — pass context via `input` when spawning, not via closure |

### Transitions

| # | Rule |
|---|------|
| ✅ | Define only transitions that are valid business operations — omit impossible ones |
| ✅ | Use `type: 'final'` for terminal states (published, closed, archived) |
| ✅ | Cascade multi-step resets by chaining transitions (REJECT → rejected → REVISE → draft) |

---

## Forbidden

| # | Rule |
|---|------|
| ❌ | Do not put API calls inside machine `actions` — side effects belong in React mutation callbacks |
| ❌ | Do not replicate machine logic with Zustand `status` strings + ad-hoc `if` checks — that is what XState replaces |
| ❌ | Do not skip explicit typing of context and event types in `types: {}` |
| ❌ | Do not mutate `context` directly — only via `assign` |
| ❌ | Do not use XState for simple boolean toggles or UI-only open/close state — use Zustand |
| ❌ | Do not put toast or notification calls inside machine actions — put them in `onSuccess`/`onError` |
| ❌ | Do not create a new machine instance on every render — `useMachine` is stable; only reinitialize when `reportId` changes |

---

## Verification

Code is considered complete when **all** of the following are true:

### Machine Definition

- [ ] All states are named and listed in the `states` object
- [ ] Context and event types are declared in `types: {}`
- [ ] Every context mutation uses `assign` — no direct mutation
- [ ] Guards are defined for transitions with business conditions
- [ ] Terminal states use `type: 'final'`
- [ ] Machine file is in `src/features/{domain}/machines/`

### React Integration

- [ ] `useMachine` is used to bind the machine to the component
- [ ] UI actions (buttons, links) are gated by `state.matches(...)` + role checks
- [ ] No invalid event is sent — only events the current state can handle
- [ ] Server state is initialized via `snapshot` when restoring from backend
- [ ] Transitions that must persist are synced to backend via `useMutation`

### General

- [ ] No Zustand store is used to mirror the same process status
- [ ] TypeScript reports zero errors in machine files (`tsc --noEmit`)
- [ ] Edge-case transitions (guard rejection, rapid clicks) are handled
