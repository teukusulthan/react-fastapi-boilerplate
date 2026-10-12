---
name: reactjs-xstate
description: Model complex process and workflow state using XState v5 state machines. Use when a feature has multi-step transitions, guards, approval flows, or an incident lifecycle. Covers machine definition, useMachine, guards, actions, and integration patterns.
---

# XState

## Skill: XState (Process / Workflow State)

### Overview

XState models state as an explicit **finite state machine** — a set of named states, valid transitions, guards, and side effects (actions). Use XState when:

- The feature has **explicit invalid transitions** (e.g. cannot go from Draft → Published without passing through Review)
- The feature has **approval steps** that require guards (e.g. only an approver can trigger `APPROVE`)
- Multiple actors or roles interact with the same process lifecycle
- You need to **audit which transitions happened and why**

If the state is just a string enum with no transition rules, use Zustand instead.

---

### Decision: XState vs Zustand

| Scenario | Use |
|----------|-----|
| `status` field cycles through predictable steps with business rules | XState |
| UI toggle (open/closed, selected/deselected) | Zustand |
| Approval workflow (Draft → Review → Approved → Published) | XState |
| Active tab, sidebar state, modal visibility | Zustand |
| Incident lifecycle (Open → Triage → Mitigation → Recovery → Postmortem) | XState |
| Loading flag for a single API call | TanStack Query |
| Data collection pipeline with validation gates | XState |

---

### Setup

```bash
npm install xstate @xstate/react
```

---

### Machine Definition — Approval Workflow

Define machines in `src/features/{domain}/machines/{name}.machine.ts`.

```typescript
// src/features/reports/machines/report-approval.machine.ts
import { createMachine, assign } from 'xstate';

export type ReportStatus = 'draft' | 'review' | 'approved' | 'published' | 'rejected';

interface ReportContext {
  reportId: string;
  reviewNote: string;
  rejectionReason: string;
  reviewedBy: string | null;
}

type ReportEvent =
  | { type: 'SUBMIT_FOR_REVIEW' }
  | { type: 'APPROVE'; reviewedBy: string }
  | { type: 'REJECT'; reason: string }
  | { type: 'PUBLISH' }
  | { type: 'REVISE' };

export const reportApprovalMachine = createMachine({
  id: 'reportApproval',
  initial: 'draft',
  types: {} as {
    context: ReportContext;
    events: ReportEvent;
  },
  context: {
    reportId: '',
    reviewNote: '',
    rejectionReason: '',
    reviewedBy: null,
  },
  states: {
    draft: {
      on: {
        SUBMIT_FOR_REVIEW: { target: 'review' },
      },
    },
    review: {
      on: {
        APPROVE: {
          target: 'approved',
          actions: assign({
            reviewedBy: ({ event }) => event.reviewedBy,
          }),
        },
        REJECT: {
          target: 'rejected',
          actions: assign({
            rejectionReason: ({ event }) => event.reason,
          }),
        },
      },
    },
    approved: {
      on: {
        PUBLISH: { target: 'published' },
      },
    },
    rejected: {
      on: {
        REVISE: { target: 'draft' },
      },
    },
    published: {
      type: 'final',
    },
  },
});
```

---

### Machine Definition — Incident Lifecycle

```typescript
// src/features/incidents/machines/incident.machine.ts
import { createMachine, assign } from 'xstate';

type IncidentState = 'open' | 'triage' | 'mitigation' | 'recovery' | 'postmortem' | 'closed';

interface IncidentContext {
  incidentId: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | null;
  assignedTo: string | null;
  resolvedAt: string | null;
}

type IncidentEvent =
  | { type: 'START_TRIAGE'; assignedTo: string }
  | { type: 'START_MITIGATION' }
  | { type: 'START_RECOVERY' }
  | { type: 'COMPLETE_RECOVERY'; resolvedAt: string }
  | { type: 'START_POSTMORTEM' }
  | { type: 'CLOSE' };

export const incidentMachine = createMachine({
  id: 'incident',
  initial: 'open',
  types: {} as { context: IncidentContext; events: IncidentEvent },
  context: {
    incidentId: '',
    severity: null,
    assignedTo: null,
    resolvedAt: null,
  },
  states: {
    open: {
      on: { START_TRIAGE: { target: 'triage', actions: assign({ assignedTo: ({ event }) => event.assignedTo }) } },
    },
    triage: {
      on: { START_MITIGATION: 'mitigation' },
    },
    mitigation: {
      on: { START_RECOVERY: 'recovery' },
    },
    recovery: {
      on: {
        COMPLETE_RECOVERY: {
          target: 'postmortem',
          actions: assign({ resolvedAt: ({ event }) => event.resolvedAt }),
        },
      },
    },
    postmortem: {
      on: { CLOSE: 'closed' },
    },
    closed: { type: 'final' },
  },
});
```

---

### Use in a React Component

```typescript
// src/features/reports/components/ReportApprovalPanel.tsx
import { useMachine } from '@xstate/react';
import { reportApprovalMachine } from '../machines/report-approval.machine';

interface Props {
  reportId: string;
  currentUserRole: 'author' | 'reviewer' | 'publisher';
}

export function ReportApprovalPanel({ reportId, currentUserRole }: Props) {
  const [state, send] = useMachine(reportApprovalMachine, {
    input: { reportId },
  });

  const canSubmit = state.matches('draft') && currentUserRole === 'author';
  const canApprove = state.matches('review') && currentUserRole === 'reviewer';
  const canPublish = state.matches('approved') && currentUserRole === 'publisher';

  return (
    <div>
      <p>Status: <strong>{state.value as string}</strong></p>

      {canSubmit && (
        <button onClick={() => send({ type: 'SUBMIT_FOR_REVIEW' })}>
          Submit for Review
        </button>
      )}

      {canApprove && (
        <>
          <button onClick={() => send({ type: 'APPROVE', reviewedBy: 'user-123' })}>
            Approve
          </button>
          <button onClick={() => send({ type: 'REJECT', reason: 'Needs revision' })}>
            Reject
          </button>
        </>
      )}

      {canPublish && (
        <button onClick={() => send({ type: 'PUBLISH' })}>
          Publish
        </button>
      )}

      {state.matches('rejected') && (
        <div>
          <p>Rejected: {state.context.rejectionReason}</p>
          <button onClick={() => send({ type: 'REVISE' })}>
            Revise
          </button>
        </div>
      )}
    </div>
  );
}
```

---

### Guards — Conditional Transitions

Use guards when a transition is only valid under a specific condition.

```typescript
export const reportApprovalMachine = createMachine({
  // ...
  states: {
    review: {
      on: {
        APPROVE: {
          target: 'approved',
          guard: ({ context, event }) =>
            event.reviewedBy !== context.reportId, // reviewer cannot be the author
          actions: assign({ reviewedBy: ({ event }) => event.reviewedBy }),
        },
      },
    },
  },
});
```

---

### Persist Machine State to Backend

When the process state must be stored server-side (e.g. approval is per-document), initialize the machine from the persisted status and persist on each transition.

```typescript
function useReportApproval(reportId: string, initialStatus: ReportStatus) {
  const { mutate: persistStatus } = useMutation({
    mutationFn: (status: string) => reportService.updateStatus(reportId, status),
  });

  const [state, send] = useMachine(reportApprovalMachine, {
    // Initialize machine to the current server state
    snapshot: reportApprovalMachine.resolveState({ value: initialStatus, context: { reportId, reviewNote: '', rejectionReason: '', reviewedBy: null } }),
  });

  // Sync state changes to backend
  useEffect(() => {
    if (!state.matches('draft')) {
      // Only persist after the first real transition
      persistStatus(state.value as string);
    }
  }, [state.value]);

  return { state, send };
}
```

---

### File Placement

```
src/features/{domain}/machines/
├── {name}.machine.ts           ← machine definition
└── {name}.machine.test.ts      ← unit tests for transitions
```

Machines are pure functions — no React, no API calls inside the machine definition. Side effects (API calls, toast) belong in component callbacks triggered by `onSuccess`/`onError` from `useMutation`, not inside machine `actions`.

---

### State Matching Helpers

```typescript
// Check single state
state.matches('review')

// Check nested state (parallel machines)
state.matches({ review: 'pending' })

// Check multiple possible states
['review', 'approved'].some((s) => state.matches(s))
```

---

### Quick Rules

| Rule | Value |
|------|-------|
| Machine file location | `src/features/{domain}/machines/{name}.machine.ts` |
| Context mutation | Only via `assign` action — never mutate directly |
| API calls | In React callbacks (useMutation), not machine actions |
| Guard purpose | Block invalid transitions — not business logic |
| State persistence | Initialize from server; sync on transition via useMutation |
| Invalid transitions | XState silently ignores undefined transitions — test edge cases |
| vs Zustand | If there are no guard rules, use Zustand `status` instead |

> Rules & checklist: [references/xstate-rules.md](references/xstate-rules.md)
