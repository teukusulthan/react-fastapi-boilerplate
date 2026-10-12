# Component Modular Mode

## Layout Variants

Pages in the same project can use **different layouts**. Identify the layout variants from the task before scaffolding components:

| Variant | When to use | Typical components |
|---------|-------------|-------------------|
| `layout-default` | Dashboard, data pages | navbar + sidebar |
| `layout-fullscreen` | Login, onboarding, error pages | navbar only, or none |
| `layout-report` | Print/export pages | minimal header, no sidebar |
| Custom | Anything else | define as needed |

Name components with `{app}-{layout?}-{part}` pattern:
- `nms-navbar`, `nms-sidebar` — shared across layouts
- `nms-navbar-minimal` — variant for fullscreen layout
- `nms-sidebar-report` — variant for report layout

Each page shell declares **only the components it needs** — there is no mandatory global set.

---

## Output Structure

```
mockup/{stack}-html/
├── {stack}-{page_name}.html          ← page shell(s); loader.js registered in <head>
├── components/
│   ├── {app}-navbar.html             ← shared navbar
│   ├── {app}-sidebar.html            ← shared sidebar
│   ├── {app}-navbar-minimal.html     ← layout variant (only if needed)
│   └── {component-name}.html
├── js/
│   └── loader.js                     ← single loader, shared by all pages
└── css/
    ├── variable.css
    └── tailwind.css
```

---

## loader.js

Read implementation from `mockup/web-html/js/loader.js`.

---

## Page Shell — Include Pattern

> ⛔ `loader.js` MUST be in `<head>` — NOT at bottom of `<body>`.
> ⛔ Call `defineComponent()` in a script immediately after loader.js in `<head>`, BEFORE `<body>` is parsed.
> ⛔ Use custom element tags `<app-navbar>` directly in `<body>` — NOT `<div data-component>` wrappers.

```html
<!-- ✅ CORRECT -->
<head>
  <!-- Must be last in head, after all CDN scripts -->
  <script src="js/loader.js"></script>
  <script>
    window.defineComponent('app-navbar',  'components/navbar.html');
    window.defineComponent('app-sidebar', 'components/sidebar.html');
  </script>
</head>
<body>
  <app-navbar></app-navbar>
  <app-sidebar></app-sidebar>
  <main class="ml-[220px] pt-12 ...">...</main>
</body>
```

```html
<!-- ❌ WRONG — loader at bottom, div wrappers -->
<body>
  <div data-component="app-navbar" data-src="..."></div>
  ...
  <script src="js/loader.js"></script>
</body>
```

---

## Component File Rules

- Each `components/{name}.html` contains **only inner markup** — no `<html>/<head>/<body>` wrapper.
- Include a `<style>` block for component-scoped overrides (shadow DOM is isolated).
- **Do NOT use Tailwind utility classes inside components** — shadow DOM isolates them from CDN. Use `var()` CSS tokens directly. CSS custom properties from `:root` DO pierce shadow DOM and respond to `.dark` toggle.

```html
<!-- components/sidebar.html -->
<style>
  :host { display: block; background: var(--sidebar); }
  .nav-item { color: var(--sidebar-foreground); }
  .nav-item.active { color: var(--sidebar-primary); border-left: 2px solid var(--sidebar-primary); }
</style>
<nav>
  ...
</nav>
```

---

## Naming Convention

| Element | Pattern | Example |
|---------|---------|---------|
| Component file | `{name}.html` | `sidebar.html` |
| Custom tag in `<body>` | `app-{name}` | `<app-sidebar></app-sidebar>` |
| `defineComponent()` call | `'app-{name}', 'components/{name}.html'` | `defineComponent('app-sidebar', 'components/sidebar.html')` |
