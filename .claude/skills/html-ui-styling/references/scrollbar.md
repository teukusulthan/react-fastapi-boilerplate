# Scrollbar Reference — Perfect Scrollbar

Use **Perfect Scrollbar** for any scrollable container that needs a styled, OS-independent scrollbar.
Never use native browser scrollbars unless the container does not need custom styling.

---

## CDN Setup

Add to the `<head>` of every page that uses custom scrollbars:

```html
<!-- Perfect Scrollbar -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/perfect-scrollbar@1.5.5/css/perfect-scrollbar.min.css" />
<script src="https://cdn.jsdelivr.net/npm/perfect-scrollbar@1.5.5/dist/perfect-scrollbar.min.js"></script>
```

---

## Initialization Pattern

```html
<div id="sidebar-scroll" class="relative overflow-hidden h-full">
  <!-- scrollable content here -->
</div>

<script>
  document.addEventListener('DOMContentLoaded', () => {
    const ps = new PerfectScrollbar('#sidebar-scroll', {
      wheelSpeed: 1,
      wheelPropagation: false,
      minScrollbarLength: 20,
    });
  });
</script>
```

> ⚠️ The container **must** have `position: relative` (or `absolute`/`fixed`) and an explicit height — `overflow-hidden` is required so the native scrollbar is hidden.

---

## Theme-Aware Styling

> ⛔ **NEVER** inject Perfect Scrollbar CSS overrides inline. Theme overrides (`ps__rail-y`, `ps__thumb-y`, etc.) are already defined in `css/styles.css` which is linked via `<link rel>` in the `<head>`.

Just ensure `styles.css` is linked — no inline `<style>` block needed for PS overrides.

---

## Common Use Cases

### Sidebar

```html
<aside id="sidebar-scroll" class="relative overflow-hidden w-[220px] h-full flex flex-col bg-sidebar text-sidebar-foreground border-r border-sidebar-border">
  <!-- nav items -->
</aside>
```

### Table / Data Panel with Fixed Height

```html
<div id="table-scroll" class="relative overflow-hidden" style="max-height: 480px;">
  <table class="w-full">...</table>
</div>
```

### Modal / Drawer Body

```html
<div id="modal-body-scroll" class="relative overflow-hidden flex-1 p-6">
  <!-- modal content -->
</div>
```

---

## Multiple Instances

```javascript
document.addEventListener('DOMContentLoaded', () => {
  ['#sidebar-scroll', '#table-scroll', '#modal-body-scroll'].forEach(sel => {
    const el = document.querySelector(sel);
    if (el) new PerfectScrollbar(el, { wheelPropagation: false });
  });
});
```

---

## Update on Dynamic Content

If content inside a scrollable container changes at runtime, call `.update()`:

```javascript
const ps = new PerfectScrollbar('#sidebar-scroll');
// after content changes:
ps.update();
```

---

## Rules

```
✅ Add position-relative + overflow-hidden to every PS container
✅ Ensure css/styles.css is linked via <link rel> — PS theme overrides live there
✅ Uncomment Perfect Scrollbar CDN when any scrollable container exists
✅ Call ps.update() after dynamic content changes
❌ Do NOT use native ::-webkit-scrollbar CSS — use PS overrides only
❌ Do NOT use overflow-auto/overflow-scroll on PS containers — use overflow-hidden
❌ Do NOT initialize PS on the <body> or <html> element
```
