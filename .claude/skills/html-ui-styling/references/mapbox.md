# Mapbox GL JS Integration Patterns

## Theme Persistence (REQUIRED — always add before any CSS)

> ⚠️ Never hardcode `class="dark"` on `<html>`. Map style is resolved at init time from `classList.contains('dark')` — if the class is hardcoded, theme toggle state from `localStorage` is ignored and map always loads in dark mode.

Add this inline script as the **first child of `<head>`**, before any CSS or script tags:

```html
<html lang="en">
<head>
  <script>(function(){var t=localStorage.getItem('theme');if(t==='light')document.documentElement.classList.remove('dark');else document.documentElement.classList.add('dark');/* default: dark */})()</script>
  <!-- rest of head ... -->
```

This ensures `classList.contains('dark')` is correct when Mapbox reads it at init.

## Public Token

```
pk.YOUR_MAPBOX_PUBLIC_TOKEN
```

## CDN Include

```html
<link href="https://api.mapbox.com/mapbox-gl-js/v3.3.0/mapbox-gl.css" rel="stylesheet" />
<script src="https://api.mapbox.com/mapbox-gl-js/v3.3.0/mapbox-gl.js"></script>
```

## Map Container

> Always set an explicit height on the container — height is context-dependent, adjust to the page layout.

> ⚠️ **Tailwind CDN (browser) fix — REQUIRED**: Tailwind v4 CDN processes classes asynchronously via `fetch`. When Mapbox initializes at `DOMContentLoaded`, Tailwind may not have applied layout classes yet, so `absolute inset-0` resolves to 0×0.  
> Always add **redundant inline styles** on the `#map` div AND call `map.resize()` with delays:

```html
<!-- ✅ Always add inline style alongside Tailwind classes — never rely on Tailwind class alone -->
<div id="map" class="absolute inset-0"
     style="position:absolute;top:0;left:0;right:0;bottom:0;width:100%;height:100%;"></div>
```

```js
map.addControl(new mapboxgl.NavigationControl(), 'bottom-right');

// Force Mapbox to recalculate container size after Tailwind CDN async processing
setTimeout(() => map.resize(), 100);
setTimeout(() => map.resize(), 500);
```

> ⚠️ **file:// protocol**: Mapbox GL JS requires `localhost` or HTTPS — it will not render on `file://`. Always serve via `npx serve .` and open `http://localhost:3000`.

## Initialization

```js
mapboxgl.accessToken = 'pk.YOUR_MAPBOX_PUBLIC_TOKEN';

// ⛔ Never hardcode the style — always read the current theme class so refresh preserves mode
const map = new mapboxgl.Map({
  container: 'map',
  style: document.documentElement.classList.contains('dark') ? MAP_STYLE.dark : MAP_STYLE.light,
  center: [106.8456, -6.2088],               // default: Jakarta
  zoom: 11,
  attributionControl: false
});

map.addControl(new mapboxgl.NavigationControl(), 'bottom-right');
```

## Dark vs Light Map Style

| Theme    | Dark mode                               | Light mode                               |
|----------|-----------------------------------------|------------------------------------------|
| any (default, no `design/` theme) | `mapbox://styles/mapbox/dark-v11` | `mapbox://styles/mapbox/light-v11` |
| a `design/` theme that names its own Mapbox styles in DESIGN.md | that theme's dark style | that theme's light style |

Map style **must switch** when the dark/light toggle fires. Wire `map.setStyle()` into the toggle handler:

```js
const MAP_STYLE = {
  dark:  'mapbox://styles/mapbox/dark-v11',
  light: 'mapbox://styles/mapbox/light-v11',
};

// Call after map is initialized — re-add sources/layers after style switch
function setMapTheme(isDark) {
  map.setStyle(isDark ? MAP_STYLE.dark : MAP_STYLE.light);
}

// Re-add layers after setStyle (style switch removes all sources/layers)
map.on('style.load', () => {
  addMapLayers(); // extract your map.on('load', ...) logic into a named function
});
```

In the theme toggle handler (the existing IIFE), call `setMapTheme` after toggling the class:

```js
btn.addEventListener('click', function () {
  var nowDark = document.documentElement.classList.toggle('dark');
  localStorage.setItem('theme', nowDark ? 'dark' : 'light');
  this.querySelector('.icon-sun').classList.toggle('hidden', nowDark);
  this.querySelector('.icon-moon').classList.toggle('hidden', !nowDark);
  // Switch map style
  if (window.__map) setMapTheme(nowDark);
  // Reinit charts
  setTimeout(function () { if (window.__reinitCharts) window.__reinitCharts(); }, 50);
});
```

Expose map instance as `window.__map` so the toggle handler can reach it:

```js
const map = new mapboxgl.Map({ ... });
window.__map = map;
```

> ⚠️ `map.setStyle()` wipes all sources and layers. Always use a `map.on('style.load', ...)` listener — not `map.on('load', ...)` — to re-add sources/layers after a style switch.

## Marker Severity System

| Severity | Semantic token      | CSS Var                | Size | Pulse |
|----------|---------------------|------------------------|------|-------|
| critical | `--error-base`      | `var(--error-base)`    | 32px | ✅    |
| alert    | `--warning-base`    | `var(--warning-base)`  | 28px | ✅    |
| normal   | `--success-base`    | `var(--success-base)`  | 24px | ❌    |
| info     | `--info-base`       | `var(--info-base)`     | 20px | ❌    |
| offline  | `--neutral-base`    | `var(--neutral-base)`  | 20px | ❌    |

> ❌ Never use `--base-error-500` or any `--base-*` token — always use semantic tokens (`--error-base`, `--warning-base`, etc.)

### Marker HTML + CSS

```css
/* In <style> block */
@keyframes marker-pulse {
  0%   { transform: scale(1);   opacity: 0.8; }
  70%  { transform: scale(2.2); opacity: 0;   }
  100% { transform: scale(1);   opacity: 0;   }
}
.marker-wrapper { position: relative; display: flex; align-items: center; justify-content: center; }
.marker-dot     { border-radius: 50%; cursor: pointer; position: relative; z-index: 1; }
.marker-ring    {
  position: absolute; border-radius: 50%; border: 2px solid;
  animation: marker-pulse 1.8s ease-out infinite;
  z-index: 0;
}
```

### Marker Factory Function

Marker elements are regular DOM nodes — CSS custom properties resolve correctly via `var()` in inline styles.  
Always use semantic tokens, never base tokens or hardcoded hex/rgb.

```js
function createMarker(severity) {
  const cfg = {
    critical: { color: 'var(--error-base)',   size: 32, pulse: true  },
    alert:    { color: 'var(--warning-base)',  size: 28, pulse: true  },
    normal:   { color: 'var(--success-base)',  size: 24, pulse: false },
    info:     { color: 'var(--info-base)',     size: 20, pulse: false },
    offline:  { color: 'var(--neutral-base)',  size: 20, pulse: false },
  }[severity] ?? { color: 'var(--neutral-base)', size: 20, pulse: false };

  const wrapper = document.createElement('div');
  wrapper.className = 'marker-wrapper';
  wrapper.style.width = wrapper.style.height = cfg.size + 'px';

  const dot = document.createElement('div');
  dot.className = 'marker-dot';
  dot.style.cssText = `width: ${cfg.size}px; height: ${cfg.size}px; background: ${cfg.color};`;
  wrapper.appendChild(dot);

  if (cfg.pulse) {
    const ring = document.createElement('div');
    ring.className = 'marker-ring';
    ring.style.cssText = `width: ${cfg.size}px; height: ${cfg.size}px; border-color: ${cfg.color};`;
    wrapper.appendChild(ring);
  }

  return wrapper;
}
```

### Adding a Marker

Popup HTML uses inline styles with semantic CSS vars — Tailwind classes are NOT available inside Mapbox popup DOM.

```js
map.on('style.load', () => {
  const el = createMarker('critical');

  new mapboxgl.Marker(el)
    .setLngLat([106.8456, -6.2088])
    .setPopup(new mapboxgl.Popup({ offset: 20 })
      .setHTML(`
        <div style="background: var(--bg-secondary); border: 1px solid var(--border-primary); padding: 12px; font-family: Montserrat, sans-serif;">
          <p style="color: var(--text-color-primary); font-size: 13px; font-weight: 600; margin: 0 0 4px;">Asset Name</p>
          <p style="color: var(--text-color-secondary); font-size: 12px; margin: 0;">Status: Critical</p>
        </div>
      `))
    .addTo(map);
});
```

### Legend (HTML overlay — outside map canvas)

Legend panels are regular HTML — use Tailwind semantic classes, not inline colors.

```html
<!-- ✅ Tailwind semantic classes for legend items -->
<div class="flex items-center gap-3 text-p12 text-font-secondary">
  <span class="flex items-center gap-1.5">
    <span class="w-2 h-2 rounded-full bg-error-base"></span> Critical
  </span>
  <span class="flex items-center gap-1.5">
    <span class="w-2 h-2 rounded-full bg-warning-base"></span> Alert
  </span>
  <span class="flex items-center gap-1.5">
    <span class="w-2 h-2 rounded-full bg-success-base"></span> Normal
  </span>
  <span class="flex items-center gap-1.5">
    <span class="w-2 h-2 rounded-full bg-info-base"></span> Info
  </span>
</div>
```

> ❌ Never use `style="background:#BE2323"` or `style="color:var(--base-error-500)"` on legend elements — always use Tailwind semantic classes (`bg-error-base`, `text-warning-base`, etc.)
```

## Panel Overlay (Translucent — floating over map)

Define a CSS class in `<style>` — never hardcode the background color:

```css
/* ✅ uses design token, responds to dark/light toggle */
.map-overlay-panel {
  background: color-mix(in srgb, var(--bg-primary) 88%, transparent);
}
```

```html
<div class="map-overlay-panel" style="
  backdrop-filter: blur(8px);
  border: 1px solid var(--border-primary);
  padding: 16px;
  font-family: Montserrat, sans-serif;
">
  <!-- panel content -->
</div>
```

> ❌ Never use `rgba(16,20,28,0.88)` or any hardcoded hex/rgb — it breaks light mode and violates token rules.

> Rule: minimum text opacity 0.7 on any panel over the map (operational readability).

## Responsive Map Container

```html
<!-- ✅ Parent: explicit height via inline style (height adjusted per layout) -->
<div class="relative w-full" style="height: {adjust per layout};">
  <!-- ✅ Child: inline style redundant with Tailwind classes to guarantee 100% fill at init time -->
  <div id="map" class="absolute inset-0"
       style="position:absolute;top:0;left:0;right:0;bottom:0;width:100%;height:100%;"></div>
  <!-- overlay panels positioned absolute inside this container -->
</div>
```

Required CSS in `<style>` block (prevents Tailwind preflight from breaking Mapbox canvas):

```css
#map { overflow: hidden; }
#map canvas { display: block !important; max-width: none !important; }
.mapboxgl-canvas-container { width: 100% !important; height: 100% !important; }
.mapboxgl-canvas { display: block !important; max-width: none !important; }
```
