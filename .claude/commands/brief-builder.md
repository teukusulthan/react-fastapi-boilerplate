# /brief-builder

Build or revise the project brief — `<cwd>/brief/00_OVERVIEW.md` (with Workforce Manifest) and per-feature `<cwd>/brief/NN_FEATURE.md`.

Trigger the [`brief-builder`](../skills/brief-builder/SKILL.md) skill.

## Usage

```
/brief-builder
/brief-builder klien minta dashboard untuk monitoring belanja daerah, mereka kemendagri…
```

## Action

Open `.claude/skills/brief-builder/SKILL.md` and follow Phase 1–7 (Opening → Discovery → Synthesis → Feature Decomposition → Deep-Dive Loop → Mini Blind Spot Review → Output Generation). Stop after filesystem write. Do **not** auto-trigger downstream skills.

## Next step

When brief is satisfied, user invokes `/uiux` (design tokens + mockups) → `/bootstrap-project` → `/sprint-builder`.
