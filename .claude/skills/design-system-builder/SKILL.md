---
name: design-system-builder
description: Generate a complete design system documentation set (DESIGN.md, variable.css, tailwind.css, brand-guideline.html) for any UI style or product brief. Use when the user asks to "buat design system baru", "buatkan design system", "buatkan design system untuk [app/brand/project]", "generate design system", "buatkan design system untuk [app/style]", "create design tokens for [project]", "buat theme baru", "bikin design system", "design system untuk [project]", "bikinin design system", "create a design system for [brand]", "build design system", "setup design system untuk [project]", "buat color palette dan typography untuk [project]", "buat token design", "generate tokens", "buat visual identity", "design token untuk [app]", or provides a product/UI brief (e.g. a brand URL, brand name, or product description) and wants a full set of design files. Also trigger when user provides a website URL and asks to create or derive a design system from it. The skill combines design-system generation with guardrails for accessibility, responsive layout, interaction states, typography, charts, and professional polish.
---

# Design System Builder

Generates 4 new design system files from a user brief by replicating the **structural DNA** of the reference template (`references/template/`) — not its content — and applying quality rules.

## Default Visual Direction

Unless the brief explicitly asks for something else, every generated system follows the app UI spec —
`.claude/rules/web/ui-design.md` and `.claude/skills/reactjs-ui-design/SKILL.md` — modern, minimal, calm:

| Decision | Default | Change only when… |
|---|---|---|
| Radius | controls 8px (`rounded-md`), inner panels 10px (`rounded-lg`), surfaces 12px (`rounded-xl`); `rounded-full` only for avatars/dots/switches | the brief names a different shape language (e.g. brutalist, square-cornered command center) |
| Palette | neutral-first: all surfaces, borders and text from the (lightly tinted) neutral ramp; **one** accent (`primary`); brands 2–5 for charts/categorical data only; shadcn `--secondary`/`--muted` are neutral fills | the brief asks for an expressive multi-color UI |
| Depth | 1px quiet borders + `shadow-xs` on resting surfaces; `shadow-md` dropdowns/popovers; `shadow-lg` dialogs/sheets/toasts; no glows, colored shadows, glassmorphism, gradient blobs | the brief asks for a flat or a high-elevation system |
| Type | one family (Inter-like sans by default), weights 400/500/600, body 14px | the brief names fonts |

Whatever the brief, `variable.css` must expose the **shadcn semantic variables** (`--background`, `--foreground`,
`--card`, `--popover`, `--primary`, `--secondary`, `--muted`, `--muted-foreground`, `--accent`, `--destructive`,
`--border`, `--input`, `--ring`, `--radius`, `--sidebar*`, `--chart-1…5`) in `:root` and `.dark` — the React app's
shadcn primitives consume only these, so a theme re-brands the app without per-component edits. Brief-driven
deviations (e.g. a "Tactical" square/flat theme) are expressed through these tokens (`--radius*`, `--shadow-*`) and
stated explicitly in DESIGN.md Do's and Don'ts.

## What This Skill Produces

Always outputs exactly **4 files** into `design/{stack}/{theme-name}/`:

| File | Role |
|---|---|
| `variable.css` | All design tokens as CSS custom properties (`:root` + `.dark`) |
| `tailwind.css` | `@theme inline {}` block mapping tokens → Tailwind v4 utilities |
| `DESIGN.md` | Human-readable style reference — the source of truth |
| `brand-guideline.html` | Self-contained visual guideline and widget preview for the generated theme |

---


## Guardrails

Apply these guardrails before writing tokens and again before delivery:

| Priority | Category | Must Do | Avoid |
|---|---|---|---|
| 1 | Accessibility | 4.5:1 body text contrast, visible focus rings, labels for icon-only controls, keyboard-safe flow | Removing focus rings, color-only meaning, unlabeled controls |
| 2 | Touch & Interaction | 44px+ targets, clear pressed/disabled/loading states, 150–300ms micro-interactions | Hover-only behavior, layout-shifting press states |
| 3 | Responsive Layout | Mobile-first breakpoints, no horizontal scroll, stable dimensions for fixed-format UI | Fixed-width containers, content hidden behind sticky bars |
| 4 | Style Fit | Match product type, audience, density, and tone; keep one coherent visual language | Mixing unrelated aesthetics or decorative effects |
| 5 | Typography & Color | 16px base body, semantic tokens, readable line-height, accessible foreground/background pairs | Raw hex in components, low-contrast gray-on-gray |
| 6 | Forms & Feedback | Visible labels, inline errors near fields, recovery path for failure, semantic disabled state | Placeholder-only labels, errors only at page top |
| 7 | Charts & Data | Accessible palettes, legends/tooltips, table fallback or text summary, responsive simplification | Relying on color alone, overloaded pie/donut charts |

Professional UI rules:
- Use SVG/icon libraries for structural icons; never use emoji as icons.
- Use one icon family, one type system, one spacing rhythm, and one elevation/radius model per theme.
- Design light and dark behavior together; verify surfaces, borders, shadows, and states in both modes.
- Every screen should have one primary action; secondary/destructive actions must be visually subordinate and spatially clear.
- Reserve space for images, charts, skeletons, and async content to avoid layout shift.

---

## Fast Mode

Activate fast mode by including `--fast` or `cepat` or `fast` anywhere in the user's prompt.

**When fast mode is ON:**
- Skip Step 1b (no `WebFetch` to extract brand colors from URL)
- Skip `WebSearch` in Step 7 (no brand history lookup)
- Use user-supplied hex as primary color directly; if no hex given, derive from brand knowledge
- Use lorem ipsum for `{{ BRAND_DESCRIPTION }}` in brand-guideline.html

**When fast mode is OFF (default):**
- Run Step 1b `WebFetch` when a URL is available
- Run `WebSearch` in Step 7 for brand profile

---

## Progress Tracking

At the **start** of every run, call `TodoWrite` to register all 8 steps before executing any of them:

```
TodoWrite([
  { id: "s1", content: "Step 1 — Parse User Brief", status: "in_progress" },
  { id: "s2", content: "Step 2 — Select Typography", status: "pending" },
  { id: "s3", content: "Step 3 — Design the Token System", status: "pending" },
  { id: "s4", content: "Step 4 — Write variable.css", status: "pending" },
  { id: "s5", content: "Step 5 — Write tailwind.css", status: "pending" },
  { id: "s6", content: "Step 6 — Write DESIGN.md", status: "pending" },
  { id: "s7", content: "Step 7 — Deploy brand-guideline.html", status: "pending" },
  { id: "s8", content: "Step 8 — Register Theme", status: "pending" }
])
```

Mark each step `completed` immediately after it finishes — before starting the next step. Never batch-complete multiple steps at once.

---

## Workflow

### Step 1 — Parse User Brief

Extract from user input:

| Input | What to derive |
|---|---|
| App type / industry | UX density and layout approach |
| Target audience / context | Interaction density, touch target needs, reading complexity |
| UI style (glassmorphism, brutalist, minimal, etc.) | Surface treatment, radius rule, shadow rule — **default: modern minimal, slightly rounded** (see Default Visual Direction) unless the brief names a style |
| Tone (premium, playful, enterprise) | Writing voice in DESIGN.md |
| Primary / brand color | Build entire palette ramp around it |
| Dark / light / auto | Whether `.dark` block inverts or extends `:root` |
| Data intensity | Chart palette, table density, metric/card hierarchy |
| Platform expectations | Determines `{stack}` — `web` (default), `mobile`, `desktop`, etc. Web-first responsive rules; include mobile constraints for touch and small screens |

**Primary color resolution — always check user prompt first:**
1. If the user's prompt contains a hex value (e.g. `#E63946`, `e63946`, `#f00`), treat it as the primary stop-500 anchor. Strip `#`, expand 3-digit shorthands, and use it verbatim — never substitute a "nicer" shade.
2. If only a color name is given (e.g. "red", "teal"), choose an appropriate base hex that fits the brand tone.
3. **If a website URL is provided (or can be inferred from the brand name), fetch the page and extract the primary brand color** using the process below — before falling back to product type defaults.
4. If no color hint is given, derive from product type / industry defaults.

**Website color extraction (Step 1b — run when URL is available AND fast mode is OFF):**

> Skip this entire step if fast mode is active. Proceed directly to Step 2.

Use `WebFetch` to load the brand's official homepage (or the URL provided):

```
WebFetch(url, prompt="Extract all CSS color values used for primary brand elements: buttons, CTAs, active navigation, header background, links, and brand logo colors. List each as a hex value with its context (e.g. '#E63946 — primary button background'). Prioritize colors used on interactive/brand elements over generic backgrounds.")
```

Then apply this priority order to pick the primary color:
1. **CTA / primary button background** — the most reliable brand signal
2. **Active nav item or selected state**
3. **Brand logo fill color** (if not black/white)
4. **Header or hero section background** (if branded, not neutral)
5. **Link color** (if not default browser blue)

Discard: pure white (`#FFF`, `#FFFFFF`), pure black (`#000`, `#000000`), near-neutral grays (saturation < 5%), and generic browser defaults.

If multiple candidates remain, pick the most saturated non-neutral color. If the page returns no usable colors (e.g. heavily image-based, JS-only render), make a best-guess approximation by combining: (1) known brand visual identity or logo color, and (2) the tone/mood/style keywords from the user's prompt. The guess must feel coherent with both the brand and the brief — not just a generic industry default. Note that it's an approximation in DESIGN.md.

After primary is set, build the full 50–900 ramp around it and pass stop-500 to `variable.py` as `--colors primary`.

If the brief is vague, choose a conservative professional default from product type:
- Enterprise/SaaS/dashboard → dense, restrained, neutral-first, slightly rounded, token-led (the default).
- Consumer/creator/lifestyle → warmer surfaces, clearer affordances, more expressive brand accents.
- Data/control room/map → compact hierarchy, strong focus states, minimal decoration, high data legibility.
- Commerce/service → clear CTA hierarchy, trust cues, readable forms, strong empty/error states.

### Step 2 — Select Typography

Run the font selection script to find the best Google Font pairing for the brief:

```bash
python3 references/scripts/brand_guideline.py "<mood/style keywords from brief>" --top 3
```

Pick the top result (highest score) unless the brief explicitly names fonts. The script returns:
- `heading_font` / `body_font` — use as the primary typeface in DESIGN.md and `--font-sans` / `--font-serif` in variable.css
- `css_import` — inject as the `@import` line at the top of variable.css
- `tailwind_config` — reference when writing the `font_family` block in tailwind.css
- `notes` — use for weight scale decisions in the Typography section of DESIGN.md

### Step 3 — Design the Token System

Before writing any file, decide:

1. **Theme slug** — short kebab-case (e.g. `aurora`, `forge`, `velvet`, `obsidian`)
2. **Palette** — derive all 5 brand ramps from primary using the color harmony formula below; then add neutral + 4 state colors, each 10 stops (50–900)
3. **Typography** — use fonts from Step 2; apply weight scale from the pairing notes
4. **Surface rules** — radius policy (default 8px controls / 12px surfaces; none or larger only if the brief asks), shadow usage (default `shadow-xs` resting, `md`/`lg` floating), depth model
5. **Component style** — button shape, border treatment, density level
6. **Interaction model** — hover, focus, pressed, disabled, loading, and reduced-motion behavior
7. **Accessibility model** — contrast targets, focus ring color, semantic state tokens, chart-safe pairings
8. **Responsive model** — small-phone, tablet, desktop layout rules and content priority

#### Color Harmony Formula — Secondary to Quinary

Once **primary** (stop 500) is set, derive the remaining 4 brand colors using the harmony formula that best fits the brand positioning:

| Formula | Rule | When to use |
|---|---|---|
| **Monokromatik** | Secondary = primary +30° sat↓, Tertiary = primary sat↓↓, Quaternary = primary lightness↑↑, Quinary = primary lightness↓ | Minimal, luxury, or highly focused single-brand products |
| **Analogus** | Secondary = primary +30°, Tertiary = primary +60°, Quaternary = primary −30°, Quinary = primary −60° (all on HSL wheel) | Lifestyle, creative, consumer apps needing warmth and visual flow |
| **Komplementer** | Secondary = primary +180°, Tertiary = midpoint between primary and secondary, Quaternary = primary +15°, Quinary = primary −15° | High-contrast enterprise, dashboards, data tools needing maximum legibility |
| **Split-Komplementer** | Secondary = primary +150°, Tertiary = primary +210°, Quaternary = primary +30°, Quinary = midpoint primary↔secondary | SaaS, productivity tools — balances variety with stability |
| **Triadik** | Secondary = primary +120°, Tertiary = primary +240°, Quaternary = primary +60°, Quinary = primary +180° | Playful, diverse consumer products, gaming, entertainment |
| **Tetradik** | Secondary = primary +90°, Tertiary = primary +180°, Quaternary = primary +270°, Quinary = midpoint primary↔tertiary | Complex dashboards, multi-category platforms needing rich color vocabulary |

**Selection logic:**

```
IF brand = luxury / minimal / focused       → Monokromatik
IF brand = lifestyle / creative / consumer  → Analogus
IF brand = enterprise / data / control room → Komplementer
IF brand = SaaS / productivity / corporate  → Split-Komplementer
IF brand = gaming / entertainment / playful → Triadik
IF brand = multi-category / complex portal  → Tetradik
```

After deriving hues, generate full 50–900 ramps for each brand color. Verify that secondary, tertiary, quaternary, and quinary stop 500 each maintain ≥ 3:1 contrast against the lightest surface token, and pass all Guardrail #1 accessibility checks before passing them to the `variable.py` script in Step 5.

#### Neutral — Derive from Primary

Do **not** use a pure gray. Tint the neutral ramp with a small amount of the primary hue to keep the palette cohesive:

| Brand tone | Neutral derivation (overall ramp) |
|---|---|
| Cool / techy / enterprise | Primary hue, saturation 4–8%, lightness 10–95% (blue-gray family) |
| Warm / lifestyle / consumer | Primary hue, saturation 4–7%, lightness 10–95% (warm-gray family) |
| Luxury / minimal | Primary hue, saturation 2–4%, lightness 5–97% (near-white to near-black) |
| Vibrant / playful | Primary hue, saturation 5–9%, lightness 15–95% (slightly tinted) |

**Dark-end saturation cap (critical for all warm hues):** For stop 900 (the darkest anchor passed to `variable.py`), saturation must **not exceed 6%** and lightness must be **6–9%** regardless of brand tone. At very low lightness, even 8–10% saturation produces a strongly visible hue cast (e.g., reddish-black instead of near-black). Use HSL to verify: `hsl(<primary-hue>, ≤4%, 4–7%)` for stop 900. Prefer 2–3% saturation when primary hue is in the red/orange range (0–40° or 320–360°). Target hex range: `#0A0909` – `#121010` for warm dark themes.

Rule: neutral stop 900 is the darkest anchor (passed as `--neutral` base to `variable.py`); the script generates lighter stops (50–800) automatically.

#### State Colors — Semantic but Brand-Aware

State colors (success, warning, error, info) are universal signals — do **not** use brand palette hues. Apply these base hues, then shift saturation/lightness to harmonize with the primary warmth/coolness:

| State | Base hue range | Adjustment |
|---|---|---|
| **Success** | Green 120–150° | Desaturate slightly for cool primaries; keep vivid for warm primaries |
| **Warning** | Amber/Yellow 35–50° | Shift warmer (40°) for cool primaries; cooler (45°) for warm primaries |
| **Error** | Red 0–15° | Shift to 5° for warm primaries; 355° (cool red) for cool primaries |
| **Info** | Blue 210–240° | Align closer to primary hue if primary is already blue-adjacent |

State colors are defined in `references/variable.yml` and **not** passed via `--colors` to `variable.py`. Only verify that:
- Each state stop 500 meets 4.5:1 against white (light mode) and dark surfaces (dark mode)
- Error is perceptually distinct from both primary and secondary at all stops
- Warning is distinguishable from success under deuteranopia simulation

### Step 4 — Write variable.css

Run the script to generate `variable.css` from the brief's color palette and fonts:

```bash
python3 references/scripts/variable.py \
  --colors '{"primary":"#HEX","secondary":"#HEX","tertiary":"#HEX","quaternary":"#HEX","quinary":"#HEX","neutral":"#HEX","success":"#HEX","warning":"#HEX","error":"#HEX","info":"#HEX"}' \
  --fonts '{"main-sans":"Font Name","main-serif":"Font Name","main-mono":"Font Name"}' \
  --output design/{stack}/{theme-name}/variable.css
```

- `--colors` — pass the hex for each color using these anchors: **brand colors** (`primary`, `secondary`, `tertiary`, `quaternary`, `quinary`) use stop **500** as base; **`neutral`** uses stop **900** (darkest/black) as base — the script generates lighter stops (50–800) automatically. State colors (`success`, `warning`, `error`, `info`) are read from `variable.yml` and do not need to be passed here.
- `--fonts` — pass all three font stacks from Step 2: `sans` (body), `serif` (heading), `mono` (code)
- `--output` — target path for the generated file

The script reads `references/template/variable.yml` for spacing, border-radius (default `--radius` 8px, `md` 8 / `lg` 10 / `xl` 12px), border-width, shadow, and typography scale, then merges in the generated palettes and font overrides. Edit the radius/shadow values in a copy of `variable.yml` (or the output) only when the brief asks for a different shape or depth language.

### Step 5 — Write tailwind.css

Run the script to generate `tailwind.css` from `references/template/tailwind.yml`:

```bash
python3 references/scripts/tailwind.py design/{stack}/{theme-name}/tailwind.css
```

The script reads `tailwind.yml`, maps every key group into the correct `@theme inline {}` CSS variable declarations, and writes the output file. No manual editing required.

### Step 6 — Write DESIGN.md

Before running the script, compose all creative decisions from Steps 1–3 into the full input JSON. The script renders a complete DESIGN.md in one pass — **no post-editing required**.

```bash
python3 references/scripts/design_md.py \
  --input '{
    "theme_name":    "{theme-name}",
    "theme_mode":    "{light|dark|system}",
    "density":       "{compact|comfortable|airy}",
    "philosophy":    "{one-line design philosophy — 3–5 core principles}",
    "narrative":     "{4–6 sentences covering: surface stack, radius philosophy, hierarchy expression, primary color discipline, and target emotion/function}",
    "fonts": {
      "sans":       "{body font}",
      "serif":      "{heading font}",
      "mono":       "{mono font}",
      "rationale":  "{one sentence: why this typeface and how its weight range drives hierarchy}",
      "substitute": "{Google Fonts name or system fallback stack}"
    },
    "surfaces": [
      { "name": "{NAME}", "hex": "{HEX}", "token": "bg-background",            "role": "Page canvas — the base all surfaces sit on" },
      { "name": "{NAME}", "hex": "{HEX}", "token": "bg-card",                  "role": "Cards, table wrappers, dialogs, popovers" },
      { "name": "{NAME}", "hex": "{HEX}", "token": "bg-muted",                 "role": "Subtle fill — hover rows, secondary buttons, skeletons" },
      { "name": "{NAME}", "hex": "{HEX}", "token": "bg-sidebar",               "role": "Sidebar nav container" },
      { "name": "{NAME}", "hex": "{HEX}", "token": "border-border",            "role": "All borders and dividers — one quiet 1px tone" },
      { "name": "{NAME}", "hex": "{HEX}", "token": "border-input / ring-ring", "role": "Input borders and focus ring" }
    ],
    "brands": [
      { "role": "Primary",    "name": "{NAME}", "hex": "{HEX}", "prefix": "primary-*",    "role_desc": "Primary action, active navigation, focus — the system'\''s sole accent" },
      { "role": "Secondary",  "name": "{NAME}", "hex": "{HEX}", "prefix": "secondary-*",  "role_desc": "Chart series 2, categorical data labels (data only)" },
      { "role": "Tertiary",   "name": "{NAME}", "hex": "{HEX}", "prefix": "tertiary-*",   "role_desc": "Chart series 3, categorical data labels (data only)" },
      { "role": "Quaternary", "name": "{NAME}", "hex": "{HEX}", "prefix": "quaternary-*", "role_desc": "Chart series 4, heat indicators (data only)" },
      { "role": "Quinary",    "name": "{NAME}", "hex": "{HEX}", "prefix": "quinary-*",    "role_desc": "Chart series 5, categorical grouping (data only)" }
    ],
    "type_scale": [
      { "role": "Caption / badge", "token": "text-label-sm", "size_px": {N}, "weight": "font-regular",  "leading": "leading-snug"    },
      { "role": "Label",           "token": "text-label-md", "size_px": {N}, "weight": "font-medium",   "leading": "leading-snug"    },
      { "role": "Body small",      "token": "text-body-sm",  "size_px": {N}, "weight": "font-regular",  "leading": "leading-normal"  },
      { "role": "Body",            "token": "text-body-lg",  "size_px": {N}, "weight": "font-regular",  "leading": "leading-relaxed" },
      { "role": "Subheading",      "token": "text-h6",       "size_px": {N}, "weight": "font-semibold", "leading": "leading-snug"    },
      { "role": "Heading small",   "token": "text-h5",       "size_px": {N}, "weight": "font-semibold", "leading": "leading-tight"   },
      { "role": "Heading",         "token": "text-h4",       "size_px": {N}, "weight": "font-bold",     "leading": "leading-tight"   },
      { "role": "Metric",          "token": "text-h2",       "size_px": {N}, "weight": "font-bold",     "leading": "leading-tight"   },
      { "role": "Display",         "token": "text-display",  "size_px": {N}, "weight": "font-bold",     "leading": "leading-none"    }
    ],
    "leading_display": "{leading-tight|leading-none}",
    "leading_body":    "{leading-normal|leading-relaxed}",
    "spacing": {
      "page_max_width":       "{tailwind size — e.g. 7xl}",
      "section_gap":          "{tailwind gap number — e.g. 6}",
      "card_header":          "{e.g. px-6 py-4}",
      "card_body":            "{e.g. px-6 pb-6}",
      "card_footer":          "{e.g. px-6 py-4}",
      "element_gap":          "{tailwind gap number — e.g. 3}",
      "sidebar_expanded_px":  {N},
      "sidebar_collapsed_px": {N}
    },
    "components": {
      "primary_button": { "padding": "{e.g. px-4 py-2}", "note": "{hover/behavior note}" },
      "border_button":  { "padding": "{e.g. px-4 py-2}", "note": "{hover/behavior note}" },
      "ghost_button":   { "note": "{hover/behavior note}" },
      "segmented":      { "padding": "{e.g. px-3 py-1.5}", "radius_note": "{radius rule note — default: container rounded-lg, items rounded-md}" },
      "panel_card":     { "header": "{e.g. px-6 py-4}", "body": "{e.g. px-6 pb-6}", "footer": "{e.g. px-6 py-4}", "shadow_note": "{shadow/elevation note — default: shadow-xs resting, md/lg only for floating layers}" },
      "data_table":     { "alternating_note": "{alternating row policy}" },
      "sidebar":        { "expanded_px": {N}, "collapsed_px": {N} },
      "tab_bar":        { "padding": "{e.g. py-1}", "gap": "{e.g. gap-1}", "style_note": "{segmented (shadcn Tabs) or underline — rationale}" },
      "header":         { "height": "{tailwind height class — e.g. h-14}" },
      "input":          { "padding": "{e.g. px-3 py-2}" }
    },
    "dos": [
      "{typography hierarchy rule}",
      "{radius rule — default: controls rounded-md 8px, surfaces rounded-xl 12px}",
      "{icon usage rule — Phosphor only, 16px in controls, 20px in headers}",
      "{surface stack rule — max N background tones per view}",
      "{any additional do rule}"
    ],
    "donts": [
      "{radius dont — default: no rounded-none, no pill buttons, no 24px+ bubbly corners}",
      "{typeface dont}",
      "{shadow dont — default: no shadow-md/lg, glows or colored shadows on resting surfaces}"
    ],
    "layout_paragraph":  "{5–8 sentences: canvas, sidebar dims, header height, grid strategy, gap values, card padding, table width, metric card columns, chart placement}",
    "layout_max_width":  "{tailwind size — e.g. 7xl}",
    "similar_brands": [
      { "product": "{Brand}", "trait": "{specific shared visual trait}" },
      { "product": "{Brand}", "trait": "{specific shared visual trait}" },
      { "product": "{Brand}", "trait": "{specific shared visual trait}" },
      { "product": "{Brand}", "trait": "{specific shared visual trait}" }
    ]
  }' \
  --output design/{stack}/{theme-name}/DESIGN.md
```

The script fills every slot and outputs a complete, final DESIGN.md. No post-editing of the output file is required.

### Step 7 — Deploy brand-guideline.html

Run the script to copy the template and inject the selected Google Font:

```bash
python3 references/scripts/brand_guideline.py "<same query from Step 2>" \
  --deploy-html design/web/{theme-name} \
  --name "{Human-Readable Design System Name}"
```

The script copies `references/template/brand-guideline.html` into the theme folder and replaces:
- `{{FONT_FAMILY}}` — with the correct Google Fonts stylesheet URL
- `{{ DESIGN_SYSTEM_NAME }}` — with the value passed via `--name` (falls back to the theme folder name if omitted)
- `{{ BRAND_TAGLINE }}` — short one-line descriptor of the design system's purpose/positioning (e.g. `Enterprise banking design language`, `Premium fintech dashboard foundation`). Derive from the product brief; if not clear, use `{Product type} design system`.

After the script runs, replace the two brand logo placeholders in the output HTML:

**Finding the official domain:**
1. If the user's prompt contains a URL — extract the domain from it directly.
2. Otherwise, identify the brand's official domain from what you know (e.g. `manutd.com`, `bsi.co.id`). If unsure, do a quick search.

**Brand description for `{{ BRAND_DESCRIPTION }}`:**

- If the user's prompt includes a brand description → use it directly.
- If fast mode is **ON** → use lorem ipsum (no search).
- If fast mode is **OFF** and no description in prompt → run WebSearch:

```
WebSearch("{brand name} company profile about history")
```

Extract: founding year, core business, brand positioning. Write 2–3 sentences, neutral professional tone. If WebSearch returns no useful results, fall back to lorem ipsum — do not block or ask the user.

**`{{ BRAND_FAVICON_URL }}`** — always use Google's favicon service:
```
https://www.google.com/s2/favicons?domain={official-domain}&sz=128
```
Example: `https://www.google.com/s2/favicons?domain=manutd.com&sz=128`

- `{{ BRAND_ABBR }}` — short uppercase abbreviation of the brand name used as fallback text (e.g. `BSI`, `PLN`, `BRI`, `MUFC`). Use 2–4 characters max.
- `{{ BRAND_SLUG }}` — lowercase kebab-case identifier used for localStorage keys (e.g. `manutd`, `bsi`, `pln`). Derive from the theme slug.
- `{{ BRAND_DESCRIPTION }}` — 2–3 sentence brand history or product context paragraph. Derive from WebSearch results or known brand facts. Falls back to lorem ipsum if brand is unknown or search returns no useful results.
**Naming brand colors — rules (apply before filling any `{{ COLOR_*_NAME }}`):**

Color names must always reflect the **actual hue** of the color, not a generic slot label. Follow this process:

1. Look at the actual hex value for each brand color from Step 3.
2. Identify the hue family: red / orange / amber / yellow / lime / green / teal / cyan / blue / indigo / violet / purple / pink / rose / neutral.
3. Combine hue with a brand-relevant word — draw from the brand's domain, geography, culture, or values.
4. Cross-check: the name must be immediately recognizable as that color. If someone reads "Biru Kepercayaan" they must expect a blue — never orange.

| Hue family | Example brand words to combine |
|---|---|
| Teal / Cyan / Green | Islami, Hijau, Nusantara, Sejuk, Subur |
| Purple / Violet | Syariah, Digital, Langit, Mulia |
| Orange / Amber | Emas, Hangat, Nusantara, Bara, Senja |
| Blue | Kepercayaan, Laut, Langit, Samudera |
| Red / Rose | Berani, Merah, Garuda, Semangat |
| Neutral / Gray | Abu, Perak, Batu, Kabut |

Apply the same logic for international brands — draw from club nicknames, team colors, geography, or product identity.

- `{{ COLOR_PRIMARY_NAME }}` — memorable name for the primary color. **Must reflect the actual hue** (e.g. `Hijau Islami` for teal, `Manchester Red` for red). Never use a generic label like "Primary Color".
- `{{ COLOR_SECONDARY_NAME }}` — memorable name for the secondary color. Must match secondary hex hue.
- `{{ COLOR_TERTIARY_NAME }}` — memorable name for the tertiary color. Must match tertiary hex hue.
- `{{ COLOR_QUATERNARY_NAME }}` — memorable name for the quaternary color. Must match quaternary hex hue.
- `{{ COLOR_QUINARY_NAME }}` — memorable name for the quinary color. Must match quinary hex hue.
- `{{ COLOR_HARMONY_TYPE }}` — name of the harmony formula used (e.g. `Analogous + Split-Complementary`, `Triadic`). From Step 3 selection.
- `{{ COLOR_HARMONY_SHORT }}` — one-line summary of the palette relationship (e.g. `warm triad balanced by two cool accents`).
- `{{ COLOR_HARMONY_REASON }}` — 1–2 sentence rationale explaining why this harmony fits the brand identity and avoids visual conflict.

No manual HTML editing required for fonts.

### Step 8 — Register Theme

Update design/design-system.md every time a new design system is created.

Rules:
- Only ONE design system can have active status.
- All previous design systems MUST automatically change to inactive.
- The newly added design system becomes the ONLY active theme.
- Never allow multiple active themes simultaneously.

If design-system.md does not exist:
- create the file first
- create the header table structure

Required table structure:

```md
| platform | theme | path | status |
|----------|-------|------|--------|
```

---

## Output Path

`{stack}` is derived from the platform in Step 1. Default: `web`. Other valid values: `mobile`, `desktop`, etc.

```
design/{stack}/{theme-name}/
├── DESIGN.md
├── variable.css
├── tailwind.css
└── brand-guideline.html
```

---

## Quality Checklist

- [ ] 4 files written to `design/{stack}/{theme-name}/`
- [ ] DESIGN.md has all sections in correct order (Colors → Typography → Spacing → Components → Do's and Don'ts → Elevation → Surfaces → Layout → Chart → Similar Brands)
- [ ] variable.css has `:root` and `.dark` blocks
- [ ] variable.css has all shadcn semantic tokens (`--background` … `--ring`, `--border`, `--radius`) in `:root` and `.dark`; `--secondary`/`--muted` are neutral
- [ ] Radius/shadow follow the default (8px controls, 12px surfaces, `shadow-xs` resting) unless the brief explicitly asked otherwise — and DESIGN.md says so
- [ ] variable.css has sidebar and chart tokens
- [ ] tailwind.css `@theme inline {}` token names match variable.css
- [ ] brand-guideline.html includes Design Token and Widget Preview tabs
- [ ] brand-guideline.html exercises light/dark mode through `.dark`
- [ ] No hex values copied
- [ ] No content, wording, or component rules copied
- [ ] Body text contrast reaches 4.5:1; secondary text reaches at least 3:1
- [ ] Focus, hover, pressed, disabled, loading, and destructive states are defined
- [ ] Touch targets are at least 44px and mobile layouts avoid horizontal scroll
- [ ] Charts use semantic/chart tokens, labels/tooltips, and non-color-only meaning
- [ ] Motion uses 150–300ms timing and respects `prefers-reduced-motion`
- [ ] `design/design-system.md` updated

---

