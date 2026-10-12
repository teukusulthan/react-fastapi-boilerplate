Copy design token CSS files into a target folder. Resolves source from `design/{platform}/{source}/`.

## Usage

```
/design-apply [--source=<theme>] [--platform=<web|mobile>] [--target=<path>]
```

All arguments are optional — defaults are resolved automatically.

Examples:
```
/design-apply
/design-apply --source={theme} --platform=web --target=mockup/web-html
/design-apply --source={theme} --platform=mobile --target=mockup/mobile-html
/design-apply --source={theme} --platform=web --target=apps/web
/design-apply --skip-ui
```

`{theme}` is a folder under `design/{platform}/` created by `design-system-builder`. If `design/` does not exist,
there is no theme to apply — the app already ships the default modern-minimal tokens
(`.claude/rules/web/ui-design.md`). For a mockup folder in that case, copy `apps/web/src/styles/variable.css` and
`tailwind.css` as the `{SRC}` files and continue with Step 3A.

---

## Arguments

| Arg | Required | Default |
|-----|----------|---------|
| `--source` | no | active theme from `design/design-system.md` |
| `--platform` | no | active platform from `design/design-system.md` |
| `--target` | no | see Step 2 |
| `--skip-ui` | no | `false` (UI component update runs by default) |

---

## Todo Checklist Processing

Before executing, create a TodoWrite task list based on the resolved mode:

**Mockup mode tasks:**
1. Resolve source + platform from `design/design-system.md`
2. Resolve target folder
3. Create `css/` and `js/` directories
4. Copy `variable.css`
5. Copy `tailwind.css`
6. Generate `css/styles.css`
7. Generate `js/script.js`
8. Generate `js/loader.js`

**App mode tasks:**
1. Resolve source + platform from `design/design-system.md`
2. Resolve target folder
3. Create `src/styles/` directory
4. Copy `variable.css`
5. Copy `tailwind.css`
6. Note the active theme in `AI_GUIDE.md`
7. Check UI components in `{target}/src/components/ui/` still use semantic tokens only *(skip if `--skip-ui` passed)*
8. Review with `npm run ui:snapshot` (light + dark)

Mark each task `in_progress` before executing it, then `completed` immediately after. Use TodoWrite throughout execution.

---

## Execution

### Step 1 — Resolve source + platform

If `--source` or `--platform` not provided, read `design/design-system.md` and extract the active `platform` and `theme` from the Active Config table.

```
SRC = design/{platform}/{source}
```

Verify `{SRC}/variable.css` and `{SRC}/tailwind.css` exist. If not, abort and tell the user.

---

### Step 2 — Resolve target (if not provided)

If `--target` not provided:

1. Check if any `apps/web*` directory exists (e.g. `apps/web`, `apps/web-dashboard`).
   - If found → use the first match as target → **App mode**
2. If no `apps/web*` found → use `mockup/{platform}-html` as target → **Mockup mode**

If `--target` is provided:
- Starts with `mockup/` → **Mockup mode**
- Starts with `apps/` → **App mode**

---

### Step 3A — Mockup mode (`mockup/*`)

CSS destination: `{target}/css/`
JS destination: `{target}/js/`

Run:
```bash
mkdir -p "{target}/css" "{target}/js"

# Copy token files (always overwrite)
cp "{SRC}/variable.css" "{target}/css/variable.css"
cp "{SRC}/tailwind.css" "{target}/css/tailwind.css"
```

Generate `{target}/css/styles.css` — always overwrite.

**Before writing:** read `design/{platform}/{source}/DESIGN.md` and find the **Typography** section. Extract the font family name and its weights (e.g. `Montserrat` with weights `400,500,600,700`). Prepend a Google Fonts `@import` for those exact weights as the first line of `styles.css`. Without a `design/` theme, use `Inter` with weights `400,500,600`.

Write exactly:
```css
@import url('https://fonts.googleapis.com/css2?family={FontFamily}:wght@{w1};{w2};{w3};{w4}&display=swap');

/* Global base styles */
html { font-size: 14px; }

/** Scroll **/
.ps__rail-y { width:4px!important; background:transparent!important; right:2px!important; opacity:0!important; transition:opacity 0.2s ease!important; }
.ps:hover>.ps__rail-y,.ps--focus>.ps__rail-y,.ps--scrolling-y>.ps__rail-y { opacity:1!important; }
.ps__rail-y:hover,.ps__rail-y.ps--clicking { background:var(--color-border-primary)!important; width:6px!important; opacity:1!important; }
.ps__thumb-y { width:4px!important; right:0!important; background:var(--color-border-primary)!important; transition:width 0.2s ease,background 0.2s ease!important; }
.ps__thumb-y:hover,.ps__rail-y:hover>.ps__thumb-y,.ps__rail-y.ps--clicking>.ps__thumb-y { width:6px!important; background:var(--color-primary-base)!important; }

/* Cursor pointer for all interactive elements */
a,
button,
label,
select,
summary,
[role="button"],
[role="tab"],
[role="menuitem"],
[role="option"],
[onclick],
[data-ui="tab-trigger"],
[data-ui="switch-field"],
[data-ui="checkbox-field"],
[data-ui="label-field"],
[data-ui="badge"],
[data-ui="badge-secondary"],
[data-ui="accordion"],
[data-ui="breadcrumb"],
[data-ui="pagination"],
[data-ui="dropdown-menu"],
[data-ui="avatar"],
[data-ui="nav-menu"],
[data-ui="table-row"],
[data-ui="table-head"],
[data-ui="tooltip"],
[data-ui="nav-item"],
[data-ui="chip"],
[data-ui="radio-card"],
[data-ui="stepper-item"],
[data-ui="dropzone"] {
  cursor: pointer;
}
```

Generate `{target}/js/script.js` — always overwrite — write exactly:
```js
// --- theme ---
(function () {
  var DEFAULT_MODE = 'dark';
  var saved = localStorage.getItem('theme');
  var isDark = saved ? saved === 'dark' : DEFAULT_MODE === 'dark';

  if (isDark) {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }

  var btn = document.getElementById('theme-toggle');
  btn.querySelector('.icon-sun').classList.toggle('hidden', isDark);
  btn.querySelector('.icon-moon').classList.toggle('hidden', !isDark);

  btn.addEventListener('click', function () {
    var nowDark = document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme', nowDark ? 'dark' : 'light');
    this.querySelector('.icon-sun').classList.toggle('hidden', nowDark);
    this.querySelector('.icon-moon').classList.toggle('hidden', !nowDark);
    setTimeout(function () {
      if (window.__reinitCharts) window.__reinitCharts();
      if (window.__onThemeToggle) window.__onThemeToggle(nowDark);
    }, 50);
  });
})();

// --- download ---
async function downloadPage() {
  const pageName = location.pathname.split('/').pop() || 'page.html';
  const [variableCss, stylesCss, tailwindCss, scriptJs] = await Promise.all([
    fetch('css/variable.css').then(r => r.text()),
    fetch('css/styles.css').then(r => r.text()),
    fetch('css/tailwind.css').then(r => r.text()),
    fetch('js/script.js').then(r => r.text()),
  ]);

  const clone = document.documentElement.cloneNode(true);

  const dlBtn = clone.querySelector('button[onclick="downloadPage()"]');
  if (dlBtn) dlBtn.remove();

  const linkEl = clone.querySelector('link[href="css/variable.css"]');
  if (linkEl) {
    const s = document.createElement('style');
    s.textContent = variableCss;
    linkEl.replaceWith(s);
  }

  const stylesLinkEl = clone.querySelector('link[href="css/styles.css"]');
  if (stylesLinkEl) {
    const s = document.createElement('style');
    s.textContent = stylesCss;
    stylesLinkEl.replaceWith(s);
  }

  clone.querySelectorAll('script').forEach(s => {
    if (s.textContent.includes("fetch('css/tailwind.css')")) {
      const el = document.createElement('style');
      el.setAttribute('type', 'text/tailwindcss');
      el.textContent = tailwindCss;
      s.replaceWith(el);
    }
  });

  const scriptSrcEl = clone.querySelector('script[src="js/script.js"]');
  if (scriptSrcEl) {
    const themeJs = scriptJs.split('// --- download ---')[0].trim();
    const el = document.createElement('script');
    el.textContent = themeJs;
    scriptSrcEl.replaceWith(el);
  }

  const html = '<!DOCTYPE html>\n' + clone.outerHTML;
  const blob = new Blob([html], { type: 'text/html' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = pageName;
  a.click();
  URL.revokeObjectURL(url);
}
```

Generate `{target}/js/loader.js` — always overwrite — write exactly:
```js
(function () {
  const registry = {};

  function define(tag, src) {
    registry[tag] = src;
    customElements.define(tag, class extends HTMLElement {
      async connectedCallback() {
        const res = await fetch(registry[this.tagName.toLowerCase()]);
        const html = await res.text();
        const shadow = this.attachShadow({ mode: 'open' });
        shadow.innerHTML = html;
      }
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-component]').forEach(el => {
      const tag = el.dataset.component;
      const src = el.dataset.src;
      if (tag && src && !registry[tag]) define(tag, src);
    });
  });

  window.defineComponent = define;
})();
```

Mockup mode checklist:
- [ ] `{target}/css/variable.css` copied (overwrite)
- [ ] `{target}/css/tailwind.css` copied (overwrite)
- [ ] `{target}/css/styles.css` generated (overwrite)
- [ ] `{target}/js/script.js` generated (overwrite)
- [ ] `{target}/js/loader.js` generated (overwrite)

---

### Step 3B — App mode (`apps/*`)

CSS destination: `{target}/src/styles/`

Before overwriting, diff the incoming files against the app's current ones:

```bash
diff <(grep -oE -- '--[a-z0-9-]+:' "{target}/src/styles/variable.css" | sort -u) \
     <(grep -oE -- '--[a-z0-9-]+:' "{SRC}/variable.css" | sort -u)
```

Every variable the app defines must still exist after the copy — in particular the shadcn semantic layer
(`--background`, `--foreground`, `--card`, `--popover`, `--primary`, `--secondary`, `--muted`, `--muted-foreground`,
`--accent`, `--destructive`, `--border`, `--input`, `--ring`, `--radius`, `--radius-*`, `--shadow-*`, `--sidebar*`,
`--chart-1…5`, status `--success/--warning/--info`) and their `.dark` overrides. If the theme file lacks any of them,
merge: take the theme's palette/font/radius/shadow values and keep the app's semantic mapping. Then:

```bash
mkdir -p "{target}/src/styles"
cp "{SRC}/variable.css" "{target}/src/styles/variable.css"   # or the merged result
cp "{SRC}/tailwind.css" "{target}/src/styles/tailwind.css"   # only if it maps every class the app uses (bg-card, border-border, text-muted-foreground …)
```

Radius and shadow come from the theme only if its DESIGN.md explicitly chooses them (brief-driven). Otherwise keep the
default scale — controls 8px (`rounded-md`), surfaces 12px (`rounded-xl`), `shadow-xs` resting, `shadow-md/lg`
floating (`.claude/rules/web/ui-design.md`).

After copying CSS files, note the active theme in `{target}/AI_GUIDE.md` (UI section, or append a one-line note if
none exists): `Active design theme: design/{platform}/{source}/DESIGN.md — token values only; visual rules: .claude/rules/web/ui-design.md`.

### Step 4 — Verify UI Components (App mode only, skippable via `--skip-ui`)

> **Default: ON.** Pass `--skip-ui` to skip this step entirely.

The shadcn primitives in `{target}/src/components/ui/` are already themed through the semantic variables, so a new
theme reaches them automatically. **Do not rewrite their class strings from DESIGN.md** — per-component restyling
breaks the shared look and is exactly what makes generated UI inconsistent. Instead:

1. Grep `{target}/src/components/ui/` and `{target}/src/components/common/` for raw values that bypass tokens
   (hex/rgb, Tailwind palette colors like `gray-200`, arbitrary values, `rounded-none`, `rounded-[…]`, `shadow-none`
   on surfaces). Replace them with the semantic classes from `.claude/skills/reactjs-ui-design/SKILL.md` §2.
2. Only if the theme's DESIGN.md explicitly defines a different shape language (e.g. a brief-driven square-cornered
   command-center theme), express it through tokens (`--radius`, `--radius-*`, `--shadow-*`) — not per component.
3. Preserve variant keys, `cn()` composition, `asChild`, refs (`React.forwardRef`), `aria-*`/`data-*` and focus rings.
4. Look at the result: `cd {target} && npm run ui:snapshot -- --route / --route /ui-kit` and review the PNGs in light
   and dark against the checklist in `reactjs-ui-design` §8, then `npm run typecheck && npm run lint`.

App mode checklist:
- [ ] `{target}/src/styles/variable.css` copied (overwrite)
- [ ] `{target}/src/styles/tailwind.css` copied (overwrite)
- [ ] No `styles.css`, `script.js`, or `loader.js` generated (not needed in app mode)
- [ ] App-only semantic variables preserved (diff checked; shadcn layer + `.dark` intact)
- [ ] `{target}/AI_GUIDE.md` notes the active theme path
- [ ] `src/components/ui/` + `components/common/` use semantic tokens only — no per-component restyle *(skip if `--skip-ui` passed)*
- [ ] `npm run ui:snapshot` reviewed (light + dark)

---

### Step 5 — Set Default Theme Class on `index.html`

After all assets and components are updated, set the theme class on `{target}/index.html` (if it exists):

1. Read `design/{platform}/{source}/DESIGN.md` — find the **Theme:** line (e.g. `**Theme:** dark`).
2. Set `class` on the root `<html>` tag:
   - `**Theme:** dark` → `<html lang="en" class="dark">`
   - `**Theme:** light` → `<html lang="en" class="light">`
3. If `index.html` does not exist, skip silently.

---

## Notes

- Always overwrite existing files.
- For `mobile` target under `apps/`: not supported — skip and inform user.
- Print a summary of what was copied/generated when done.
