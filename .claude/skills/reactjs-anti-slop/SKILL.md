---
name: reactjs-anti-slop
description: Anti-AI-slop quality gate for React UI in apps/web — catches the "basic / boring / generic" look before handoff. Pre-emit self-critique, boring-UI anti-patterns, honest copy, full interaction-state coverage, no redrawn chrome, responsive check, semantic-token-only rule, and the mandatory screenshot review loop (npm run ui:snapshot). Runs alongside reactjs-ui-design (the visual playbook), which it never overrides. Adapted from the Hallmark design skill (github.com/Nutlope/hallmark), stripped of free-form token/macrostructure generation.
---

## Skill: Anti-Slop Discipline

> **Visual rules:** [`reactjs-ui-design`](../reactjs-ui-design/SKILL.md) + `.claude/rules/web/ui-design.md`
> win over any markup here. This skill owns the **quality gate**: self-critique, honest copy, state
> coverage and the pre-handoff checklist.

### Overview

This skill does not replace `reactjs-ui-design`, `reactjs-slicing-ui` or `reactjs-design-system` — it
runs **alongside** them as a quality gate. Those skills say *which component/token/folder/pattern* to use;
this skill says *how to avoid the generic, templated "AI-slop" or "boring admin template" look* while
staying inside those constraints.

Unlike the original Hallmark skill, this adaptation does **not**:
- invent design tokens or `:root` palettes per build (tokens are the shadcn semantic variables in
  `src/styles/variable.css` — see `reactjs-design-system`)
- pick from a free macrostructure catalog (page composition comes from the playbook recipes §5:
  `PageHeader` → toolbar → surfaces; `StatCard` rows; `DataTable` in a card; `SectionCard` stacks)
- write a `.hallmark/log.json` project-memory file or a CSS stamp comment

---

### When to Use

| Situation | Action |
|-----------|--------|
| About to emit a new page or component | Step 0 (anti-patterns) + Step 1 (pre-emit critique) before writing JSX |
| Component has interactive states (button, input, card action, nav item) | Step 3 (state coverage) |
| Writing any copy — headings, stat numbers, labels, empty states | Step 2 (honest copy) |
| Building a marketing/mock/browser/phone preview | Step 4 (no redrawn chrome) |
| Building multiple pages/sections in the same session | Step 5 (diversification) |
| Before marking any UI task done | Step 6 (review loop + checklist) |

---

### Step 0 — Boring-UI anti-patterns (reject on sight)

From the playbook §1. If the planned output has any of these, redesign before coding:

- Everything the same size and weight; no focal point; title indistinguishable from body.
- Raw HTML: native `<select>`, `<input type="checkbox">`, unstyled `<table>`, default buttons,
  `<ul>` dumps of data, `alert()`/`confirm()`.
- Content floating on a blank canvas with no structure, or a single "Welcome, X" line as a page.
- Square boxes with hard borders around everything (`rounded-none`), cards inside cards, double borders,
  no breathing room.
- No states: blank areas while loading, bare "No data" text, errors as plain red text.
- Random icons/colors sprinkled without meaning; brand palettes (`secondary-*`, `tertiary-*`) used as
  chrome; colored/glow shadows, gradients, glassmorphism.
- Pill-shaped buttons or bubbly 24px corners; Title Case / ALL CAPS labels.

The target instead: one title + one-line description + one primary action (`PageHeader`); a few
surfaces (`rounded-xl` cards / `DataTable`) with consistent `p-6` and `gap-6`; muted secondary info;
small deliberate details (`StatusBadge` with dot, avatar initials, `tabular-nums`, relative times with a
tooltip); designed loading / empty / error states.

---

### Step 1 — Pre-emit Self-Critique (6 axes)

Before emitting a component or page, silently score the planned output 1–5 on each axis. If any axis
scores below 3, revise before writing code — do not ship a first draft that fails its own critique.

| Axis | Question |
|------|----------|
| Philosophy | Does this composition serve the actual content/brief, or is it a generic filler layout? |
| Hierarchy | One clear page title and one primary action; one focal point per section, not three competing CTAs? |
| Execution | Is it built from shadcn primitives + `components/common` patterns + `modules/data-table`, with only semantic token classes (playbook §2–§4)? |
| Specificity | Is copy/data specific to this domain, or could it be pasted into any other app unchanged? |
| Restraint | Any decoration that adds no information (gradients, redundant icons, filler badges, extra borders)? |
| Variety | Does it differ structurally from the last 1–2 sections/pages built in this session (Step 5)? |

---

### Step 2 — Honest Copy (No Fabricated Data)

Never invent:
- Percentages, counts, or metrics not provided by the user/spec/API (`"+247% growth"`, `"10,000+ users"`)
- Testimonials, customer names, or quotes
- Fake review counts, star ratings, or "as seen in" logos

When real data isn't available yet:
- Use an explicit placeholder (`—` in a `StatCard` with a helper line, or a skeleton), never a
  plausible-looking fake number
- Or restructure the section to not require a number at all

Copy style: sentence case, buttons are verbs, one-line descriptions (playbook §7).

---

### Step 3 — Interaction-State Coverage

Any interactive primitive or module (button, input, card action, nav item, menu item, row) must cover
all applicable states — not just default + hover:

`default · hover · focus-visible · active · disabled · loading · error · success`

Not every component needs all eight (a static badge has none; a form input needs
default/focus/disabled/error at minimum). Reuse shadcn's built-in state variants (`data-[state=]`,
`aria-invalid`, `disabled:`, `focus-visible:ring-[3px]`) rather than hand-rolling new ones. Async
surfaces need designed loading (skeleton shaped like content), empty (`EmptyState`) and error
(`Alert variant="destructive"` + Retry) states (playbook §5.7).

Do not animate `:focus-visible` ring appearance/disappearance — it must be instant for accessibility.

---

### Step 4 — No Redrawn UI Chrome

Do not fabricate fake OS/browser/app chrome to "frame" content:
- No hand-drawn browser tab bars, traffic-light buttons, or address bars around screenshots/mockups
- No fake phone bezels/notches around mobile previews unless the user explicitly asked for a device frame
- No fake code-editor window chrome around code blocks

If a frame is genuinely needed, use a real image asset or an existing wrapper component.

---

### Step 5 — Structural Diversification (within existing patterns)

Within one session, do not reuse the identical section rhythm back-to-back (e.g. every section = heading
+ 3-column icon grid). Vary among the playbook's approved compositions (stat row vs. chart + list grid vs.
table card vs. `SectionCard` stack vs. tabs + definition list) and emphasis — never by inventing a new
visual language ad hoc.

---

### Step 6 — Screenshot review loop + pre-handoff checklist (mandatory)

**Look at it before you say done** (playbook §8):

```bash
cd apps/web
npm run ui:snapshot -- --route <your-route>     # light + dark, desktop + mobile PNGs → .ui-snapshots/
```

Open every PNG (Read tool), run the playbook §8 checklist, fix, re-snapshot. Then:

- [ ] Snapshots taken and reviewed (light + dark, desktop + mobile); issues fixed and re-snapshotted
- [ ] None of the Step 0 anti-patterns present
- [ ] No hardcoded/fabricated metrics, testimonials, or counts (Step 2)
- [ ] All headings roman weight — no `italic` on `h1`–`h6`; sentence case
- [ ] Every interactive element covers its required states; async surfaces have loading/empty/error (Step 3)
- [ ] No hand-drawn browser/phone/IDE chrome (Step 4)
- [ ] Layout verified at 390px, 768px and 1440px — no horizontal scroll, no clipped text, toolbars wrap,
      tables scroll inside their card
- [ ] No two consecutive sections/pages in this session share the same layout rhythm (Step 5)
- [ ] Only shadcn semantic token classes (`bg-card`, `text-muted-foreground`, `border-border`, `bg-primary`,
      status tints) and Tailwind's default scale — zero raw hex/rgb, Tailwind palette colors or arbitrary
      values. Radius: controls `rounded-md`, surfaces `rounded-xl`. If a `design/` theme exists, its
      values live in the variables, not in components.
- [ ] `npm run typecheck && npm run lint && npm run test:ci` pass

Do not report the task as done until every box is true.
