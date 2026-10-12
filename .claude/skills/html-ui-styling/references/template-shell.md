# HTML Template Shell

Use this shell for every new page. Replace `{Page Title}` and `{DEFAULT_MODE}` before saving.
The floating download/theme buttons are mockup tooling (not product UI) — keep them as-is. Page content follows the
visual direction in `coding-rules.md` (default: `.claude/rules/web/ui-design.md`).


```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{Page Title}</title>

  <!-- ⛔ MANDATORY: variable.css — never inline, never remove -->
  <link rel="stylesheet" href="css/variable.css" />
  <!-- ⛔ MANDATORY: styles.css — never remove, always after variable.css -->
  <link rel="stylesheet" href="css/styles.css" />
  <style>
    /* === page-specific additions (append only, never override base tokens) === */
    
  </style>

  <!-- Tailwind v4 CDN -->
  <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>

  <!-- Tailwind theme: fetch tailwind.css and inject as <style type="text/tailwindcss"> -->
  <!-- NOTE: requires HTTP server (npx serve). file:// protocol will fail (CORS). -->
  <!-- NOTE: @import url() inside <style type="text/tailwindcss"> does NOT work — CDN ignores it. -->
  <!-- NOTE: <link type="text/tailwindcss"> does NOT work — CDN only processes inline <style>. -->
  <script>
    fetch('css/tailwind.css')
      .then(r => r.text())
      .then(css => {
        const s = document.createElement('style');
        s.setAttribute('type', 'text/tailwindcss');
        s.textContent = css;
        document.head.appendChild(s);
      });
  </script>

  <!-- Font: Inter by default; use the font named in DESIGN.md when a design/ theme is active -->
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <!-- font link from DESIGN.md -->

  <!-- Phosphor Icons -->
  <script src="https://unpkg.com/@phosphor-icons/web"></script>

  <!-- ECharts — include ONLY if charts are needed -->
  <!-- <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script> -->

  <!-- Perfect Scrollbar CDN — uncomment when scrollable containers are present -->
  <!-- <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/perfect-scrollbar@1.5.5/css/perfect-scrollbar.min.css" /> -->
  <!-- <script src="https://cdn.jsdelivr.net/npm/perfect-scrollbar@1.5.5/dist/perfect-scrollbar.min.js"></script> -->

  <!-- Mapbox GL JS — include ONLY if map is needed -->
  <!-- <link href="https://api.mapbox.com/mapbox-gl-js/v3.3.0/mapbox-gl.css" rel="stylesheet" /> -->
  <!-- <script src="https://api.mapbox.com/mapbox-gl-js/v3.3.0/mapbox-gl.js"></script> -->
</head>
<body class="bg-background text-foreground font-sans text-sm antialiased">

  <!-- layout here -->

  <!-- ✅ MANDATORY: Download Button — always present, always floating, always above theme toggle -->
  <button
    onclick="downloadPage()"
    class="cursor-pointer fixed bottom-20 right-6 z-50 flex items-center justify-center w-10 h-10 rounded-full bg-card border border-border text-muted-foreground shadow-md hover:text-foreground transition-colors"
    title="Download HTML"
  >
    <i class="ph ph-download-simple text-base"></i>
  </button>

  <!-- ✅ MANDATORY: Dark/Light Toggle Button — always present, always floating, always persistent -->
  <button
    id="theme-toggle"
    class="cursor-pointer fixed bottom-6 right-6 z-50 flex items-center justify-center w-10 h-10 rounded-full bg-card border border-border text-muted-foreground shadow-md hover:text-foreground transition-colors"
    title="Toggle dark/light mode"
  >
    <i class="ph ph-sun icon-sun text-base"></i>
    <i class="ph ph-moon icon-moon text-base hidden"></i>
  </button>

  <!-- ✅ MANDATORY: Theme toggle + download utility — always include -->
  <!-- downloadPage() inlines the theme toggle section and removes this <script> tag from output -->
  <script src="js/script.js"></script>

</body>
</html>
```

## Dark / Light Mode Rules

- **DEFAULT MODE** comes from `**Theme:**` field in active `DESIGN.md` — never hardcode. Without a `design/` theme, default to `light`.
- If user explicitly specifies a mode in the task, that overrides DESIGN.md default.
- On page load: check `localStorage.getItem('theme')` first; fall back to DESIGN.md default.
- Toggle button: adds/removes `dark` class on `<html>`, saves to `localStorage.setItem('theme', ...)`.
- Replace `{DEFAULT_MODE}` literal with actual `'dark'` or `'light'` string in `js/script.js` — never leave it as-is.
- `js/script.js` contains both theme toggle and `downloadPage()` separated by `// --- download ---` marker.
- On export: theme toggle section (above marker) is inlined, `<script src="js/script.js">` tag is removed.

> ⛔ **NEVER add a custom theme init IIFE or a second `click` listener on `#theme-toggle` in the page `<script>`.** `js/script.js` already handles both init and the click listener. Duplicating them causes the `dark` class to toggle twice (net: no change) and breaks the toggle entirely.
>
> For page-specific side effects on theme switch (e.g. Mapbox style swap, chart reinit), use the hook that `js/script.js` already calls:
> ```js
> window.__onThemeToggle = function (isDark) {
>   // e.g. map style swap, reinit charts
> };
> ```
