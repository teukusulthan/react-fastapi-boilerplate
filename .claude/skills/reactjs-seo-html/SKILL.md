---
name: reactjs-seo-html
description: Maintain the static head of apps/web/index.html (title, description, theme-color, robots, favicons, Open Graph/Twitter tags) and public/manifest.json. index.html uses Vite `%VITE_*%` env placeholders (VITE_APP_NAME, VITE_APP_DESCRIPTION) with defaults in vite.config.ts. Load when rebranding, bootstrapping a new app, making an app public (indexable), or auditing meta tags.
---

# ReactJS SEO — index.html & manifest.json

Load this skill when you need to:

- Rename/rebrand the app (title, description, theme color, icons)
- Make an internal app public (robots, canonical, Open Graph / Twitter Card)
- Add a new env-driven value to `index.html`
- Audit `index.html` / `manifest.json`

Per-page `document.title` is **not** set here — it is set at runtime by `usePageTitle()`
(`src/hooks/use-page-title.ts`, called once per layout) from the active menu entry's `seo.title`.
See `.claude/skills/reactjs-menu-config/SKILL.md` § Page title.

---

## Files (real paths)

```
apps/web/
├── index.html                 ← static head; %VITE_*% placeholders
├── vite.config.ts             ← htmlEnv() plugin + HTML_ENV_DEFAULTS for the placeholders
├── env/.env.example           ← VITE_APP_NAME, VITE_APP_DESCRIPTION, …
└── public/
    ├── manifest.json          ← web app manifest (no service worker / PWA runtime)
    ├── robots.txt             ← "Disallow: /" (internal app default)
    ├── favicon.ico
    └── images/
        ├── 16x16.png  24x24.png  32x32.png  64x64.png  180x180.png  512x512.png
        ├── avatar.png  avatar.svg  default-image.png
        └── thumbnail/share.png   ← social share image
```

Paths in `index.html` are absolute from `public/` (`/images/32x32.png`); paths in
`manifest.json` are relative (`images/32x32.png`).

---

## How values get into index.html

`index.html` uses **Vite env placeholders** — `%VITE_APP_NAME%`, `%VITE_APP_DESCRIPTION%`.
They are replaced at dev/build time by the `htmlEnv()` plugin in `vite.config.ts`, which
reads `env/.env*` and falls back to `HTML_ENV_DEFAULTS` (so a missing key never ships a
literal `%VITE_…%`). Values are HTML-escaped.

To add a new env-driven value (e.g. a canonical URL):

1. Add `VITE_APP_URL=` to `apps/web/env/.env.example` (and your local `env/.env`).
2. Add a default for it to `HTML_ENV_DEFAULTS` in `vite.config.ts` (only needed if the key may be unset).
3. Use `%VITE_APP_URL%` in `index.html`.
4. If React code also needs it, add it to the zod schema in `src/config/env.ts` and read it via
   `env` — never `import.meta.env` directly.

Do **not** use `{{APP_NAME}}`-style tokens or manual search-replace for values that come from env.
Static brand values that never change per environment (theme color, icon paths) are written
literally.

---

## Current index.html (baseline)

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>%VITE_APP_NAME%</title>
    <meta name="description" content="%VITE_APP_DESCRIPTION%" />
    <meta name="theme-color" content="#1278a8" />
    <!-- Internal application: keep it out of search engines. Remove for public sites. -->
    <meta name="robots" content="noindex, nofollow" />
    <meta name="referrer" content="strict-origin-when-cross-origin" />

    <link rel="icon" href="/favicon.ico" sizes="32x32" />
    <link rel="icon" type="image/png" sizes="32x32" href="/images/32x32.png" />
    <link rel="icon" type="image/png" sizes="16x16" href="/images/16x16.png" />
    <link rel="apple-touch-icon" sizes="180x180" href="/images/180x180.png" />
    <link rel="manifest" href="/manifest.json" />
    <!-- Google Fonts (Inter) preconnect + stylesheet -->
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Icons are **not** loaded from `index.html`: Phosphor icon fonts are bundled from
`@phosphor-icons/web` imports in `src/main.tsx` (see `.claude/skills/reactjs-icon/SKILL.md`).

---

## Making the app public (indexable + shareable)

Only when the brief says the site is public. Add to `<head>`:

```html
<meta name="robots" content="index, follow" />            <!-- replaces noindex -->
<link rel="canonical" href="%VITE_APP_URL%" />

<!-- Open Graph -->
<meta property="og:type" content="website" />
<meta property="og:site_name" content="%VITE_APP_NAME%" />
<meta property="og:title" content="%VITE_APP_NAME%" />
<meta property="og:description" content="%VITE_APP_DESCRIPTION%" />
<meta property="og:url" content="%VITE_APP_URL%" />
<meta property="og:image" content="%VITE_APP_URL%/images/thumbnail/share.png" />

<!-- Twitter / X -->
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="%VITE_APP_NAME%" />
<meta name="twitter:description" content="%VITE_APP_DESCRIPTION%" />
<meta name="twitter:image" content="%VITE_APP_URL%/images/thumbnail/share.png" />
```

…and update `public/robots.txt` (`Allow: /`, optional `Sitemap:`). `og:image` must be an
absolute URL for crawlers. Keep the description ≤ 160 characters.

---

## manifest.json

```json
{
  "short_name": "App",
  "name": "App",
  "icons": [
    { "src": "favicon.ico", "sizes": "32x32", "type": "image/x-icon" },
    { "src": "images/16x16.png", "type": "image/png", "sizes": "16x16" },
    { "src": "images/32x32.png", "type": "image/png", "sizes": "32x32" },
    { "src": "images/180x180.png", "type": "image/png", "sizes": "180x180" },
    { "src": "images/512x512.png", "type": "image/png", "sizes": "512x512" },
    { "src": "images/512x512.png", "type": "image/png", "sizes": "512x512", "purpose": "maskable" }
  ],
  "start_url": "/",
  "display": "standalone",
  "theme_color": "#1278a8",
  "background_color": "#ffffff"
}
```

`manifest.json` is static (not processed by Vite) — when rebranding, edit `short_name`,
`name` and `theme_color` by hand to match `VITE_APP_NAME` and the `theme-color` meta.
There is no service worker; do not add PWA plugins unless the brief asks for offline support.

---

## Rules

- MUST keep exactly one `<meta charset>` and one `<meta name="viewport">`. The viewport MUST stay zoomable (no `maximum-scale=1` / `user-scalable=no`).
- MUST keep `robots noindex` (and `robots.txt` `Disallow: /`) for internal/admin apps; only switch to `index, follow` for public sites.
- MUST drive the app name/description from `VITE_APP_NAME` / `VITE_APP_DESCRIPTION`, not hard-coded text.
- MUST keep `theme-color` in `index.html` and `theme_color` in `manifest.json` identical.
- MUST NOT use `react-helmet` or any runtime meta library for app-level tags; per-page titles go through `usePageTitle`.
- MUST NOT add `<link>` stylesheets for icons — icons are bundled via `src/main.tsx`.
- Replace icon files in place (same names under `public/images/`) when rebranding.

## Checklist

- [ ] `env/.env.example` (and deployment env) set `VITE_APP_NAME`, `VITE_APP_DESCRIPTION`
- [ ] `HTML_ENV_DEFAULTS` in `vite.config.ts` covers every `%VITE_*%` used in `index.html`
- [ ] `npm run build` output `build/index.html` contains no literal `%VITE_`
- [ ] `manifest.json` name/short_name/theme_color match the brand
- [ ] Icons replaced under `public/images/` (16, 32, 180, 512) + `favicon.ico`
- [ ] robots meta + `robots.txt` match the app's visibility (internal = noindex)
- [ ] Public sites only: canonical, OG, Twitter tags with absolute image URL

## Common mistakes

- Using `{{APP_NAME}}`-style placeholders — they are never replaced; use `%VITE_APP_NAME%`.
- Adding a `%VITE_X%` without a default and without setting it in `env/` — fixed by `HTML_ENV_DEFAULTS`.
- Reading `import.meta.env.VITE_X` in components — use `env` from `src/config/env.ts`.
- Pointing icons at `/img/icon-32x32.png` — the real folder is `public/images/` with `32x32.png` names.
