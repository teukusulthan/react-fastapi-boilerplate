# Driver.js — Plain HTML (Vanilla JS)

No npm, no bundler. Use CDN.

---

## Setup via CDN

```html
<head>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/driver.js@1/dist/driver.css" />
</head>
<body>
  <!-- page content with id anchors -->

  <button id="start-tour">Mulai Tour</button>

  <script src="https://cdn.jsdelivr.net/npm/driver.js@1/dist/driver.iife.js"></script>
  <script>
    const { driver } = window.driver.js ?? window.driver

    const driverObj = driver({
      showProgress: true,
      animate: true,
      smoothScroll: true,
      allowClose: true,
      steps: [
        {
          element: '#sidebar',
          popover: {
            title: 'Navigasi',
            description: 'Gunakan sidebar untuk berpindah halaman.',
            side: 'right',
          },
        },
        {
          element: '#search-bar',
          popover: {
            title: 'Pencarian',
            description: 'Cari konten di sini.',
            side: 'bottom',
          },
        },
        {
          element: '#profile-btn',
          popover: {
            title: 'Profil',
            description: 'Kelola akun Anda.',
            side: 'left',
          },
        },
      ],
      onDestroyed: () => {
        localStorage.setItem('tour-done', '1')
      },
    })

    document.getElementById('start-tour').addEventListener('click', () => {
      driverObj.drive()
    })

    // Auto-start on first visit
    if (!localStorage.getItem('tour-done')) {
      setTimeout(() => driverObj.drive(), 600)
    }
  </script>
</body>
```

---

## IIFE Global Access

The CDN build exposes driver.js as an IIFE. Access it via:

```js
// v1.x
const { driver } = window.driver.js

// fallback if namespace differs
const driverFn = window.driver?.js?.driver ?? window.driver
```

---

## ES Module via CDN (modern browsers)

```html
<script type="module">
  import { driver } from 'https://cdn.jsdelivr.net/npm/driver.js@1/dist/driver.esm.js'

  const driverObj = driver({ steps: [ /* ... */ ] })
  document.getElementById('start-tour').onclick = () => driverObj.drive()
</script>
```

---

## Single Highlight (no full tour)

```js
const { driver } = window.driver.js

const driverObj = driver({})

driverObj.highlight({
  element: '#help-icon',
  popover: {
    title: 'Butuh bantuan?',
    description: 'Klik ikon ini kapan saja.',
    side: 'left',
  },
})
```

---

## CSS Customization

```css
.driver-popover {
  background: #1e1e2e;
  color: #cdd6f4;
  border-radius: 8px;
}
.driver-popover-title {
  font-size: 1rem;
  font-weight: 700;
}
.driver-popover-description {
  font-size: 0.875rem;
  color: #a6adc8;
}
```
