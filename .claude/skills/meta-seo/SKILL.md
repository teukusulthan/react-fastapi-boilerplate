---
name: meta-seo
description: "Replace and update HTML meta tags for SEO, social sharing, and branding. Use when user wants to update app title, description, favicon, OG tags, Twitter card, itemprop/Schema.org, keywords, author, theme-color, robots, or canonical URL. Works with any HTML file: index.html (React/Vue/Vite), _document.tsx (Next.js), plain HTML. Triggers: 'ganti nama app', 'update meta', 'ganti title', 'update favicon', 'set OG tags', 'update SEO', 'update branding', 'replace meta tags'."
argument-hint: "[app-name] [description] [url] [theme-color]"
---

# Meta SEO

Replace HTML meta tags for SEO, social sharing, favicon, and branding.

## Input Collection

Ask the user for these values (skip if already provided):

| Field | Used in |
|---|---|
| `app_name` | title, OG, Twitter, itemprop |
| `short_description` | meta description, OG, Twitter, itemprop |
| `tagline` | og:quote, property:quote |
| `url` | canonical, og:url, twitter:url, itemprop:url |
| `keywords` | meta keywords |
| `author` | meta author, itemprop:author |
| `theme_color` | meta theme-color (hex, e.g. `#0D5EBA`) |
| `locale` | og:locale (e.g. `id_ID`, `en_US`) |
| `twitter_handle` | twitter:site (e.g. `@MyApp`) |
| `hashtag` | og:hashtag |
| `favicon_32` | link rel icon 32x32 |
| `favicon_16` | link rel icon 16x16 |
| `og_image` | og:image, twitter:image, itemprop:image |
| `og_image_width` | og:image:width (default `600`) |
| `og_image_height` | og:image:height (default `400`) |

If user provides partial info, fill missing fields with sensible defaults derived from `app_name`.

## Target Files

| Framework | File |
|---|---|
| React / Vue / Vite | `apps/web/index.html` or `index.html` |
| Next.js | `app/layout.tsx` or `pages/_document.tsx` |
| Plain HTML | any `.html` file |

Read the target file first to understand current structure before replacing.

## Replacement Rules

1. Replace ALL occurrences of old app name/description — search globally, not just obvious fields.
2. Keep existing `<link>` tags for CSS/icons/manifest unless user explicitly changes them.
3. Remove duplicate tags (e.g. duplicate `<meta charset>`, duplicate `<meta viewport>`).
4. Keep `<meta name="referrer">` and `<link rel="manifest">` intact.
5. For Next.js `layout.tsx`: use the `metadata` export object, not raw HTML tags.

## Output Template (HTML)

Replace the `<head>` meta block with this pattern (adapt to match existing structure):

```html
<title>{app_name}</title>

<link rel="icon" type="image/png" sizes="32x32" href="{favicon_32}" />
<link rel="icon" type="image/png" sizes="16x16" href="{favicon_16}" />

<!-- Primary Meta -->
<meta name="description" content="{short_description}" />
<meta name="keywords" content="{keywords}" />
<meta name="author" content="{author}" />
<meta name="theme-color" content="{theme_color}" />
<meta name="robots" content="index,follow" />

<!-- Open Graph -->
<link rel="canonical" href="{url}" />
<meta property="og:site_name" content="{app_name}" />
<meta property="og:url" content="{url}" />
<meta property="og:title" content="{app_name}" />
<meta property="og:description" content="{short_description}" />
<meta property="og:quote" content="{tagline}" />
<meta property="og:hashtag" content="{hashtag}" />
<meta property="og:image" content="{og_image}" />
<meta property="og:image:width" content="{og_image_width}" />
<meta property="og:image:height" content="{og_image_height}" />
<meta property="og:locale" content="{locale}" />
<meta property="og:type" content="website" />

<!-- Schema.org / itemprop -->
<meta itemprop="name" content="{app_name}" />
<meta itemprop="description" content="{short_description}" />
<meta itemprop="url" content="{url}" />
<meta itemprop="image" content="{og_image}" />
<meta itemprop="author" content="{author}" />
<meta itemprop="headline" content="{app_name}" />
<meta itemprop="publisher" content="{author}" />
<link rel="image_src" href="{og_image}" />

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:site" content="{twitter_handle}" />
<meta name="twitter:title" content="{app_name}" />
<meta name="twitter:description" content="{short_description}" />
<meta name="twitter:url" content="{url}" />
<meta name="twitter:image" content="{og_image}" />
```

## Favicon Generation

Always generate favicon and OG image assets as part of this skill — do NOT skip. Use Python + Pillow.

### Detect public folder

| Framework | Public folder |
|---|---|
| React / Vite | `apps/web/public/` |
| Next.js | `public/` |
| Plain HTML | same folder as HTML file |

### Required sizes

| File | Size | Use |
|---|---|---|
| `images/16x16.png` | 16×16 | Browser tab |
| `images/24x24.png` | 24×24 | Toolbar |
| `images/32x32.png` | 32×32 | Standard favicon |
| `images/64x64.png` | 64×64 | High-res |
| `images/180x180.png` | 180×180 | Apple touch icon |
| `images/512x512.png` | 512×512 | PWA icon |
| `images/thumbnail/share.png` | 1200×630 | OG / Twitter card |

### Design rules

- Background: use `theme_color` from user input (default `#0D1117`)
- Accent: derive a complementary highlight color — e.g. tactical green `#00C878` for dark themes, brand primary for light themes
- Icon letter: first letter of `app_name`, centered, with outer ring ellipse
- OG image: tactical grid lines (low-opacity), border rect, corner marks, `app_name` in large text, `short_description` in smaller text, horizontal divider

### Python generation script (run via Bash tool)

```python
from PIL import Image, ImageDraw, ImageFont
import os

PUBLIC = "<detected_public_folder>"
BG     = <theme_color as RGB tuple>
ACCENT = <accent_color as RGB tuple>
LETTER = "<first letter of app_name>"
APP_NAME = "<app_name>"
SUB = "<short_description>"

def make_icon(size, out_path):
    img = Image.new("RGBA", (size, size), BG)
    draw = ImageDraw.Draw(img)
    pad = max(2, size // 12)
    ring_w = max(1, size // 16)
    draw.ellipse([pad, pad, size-pad, size-pad], outline=ACCENT, width=ring_w)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", int(size * 0.55))
    except:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0,0), LETTER, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    draw.text(((size-tw)/2 - bbox[0], (size-th)/2 - bbox[1]), LETTER, font=font, fill=ACCENT)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, "PNG")

def make_og(out_path):
    W, H = 1200, 630
    img = Image.new("RGBA", (W, H), BG)
    draw = ImageDraw.Draw(img)
    for x in range(0, W, 60):
        draw.line([(x,0),(x,H)], fill=(*ACCENT,18), width=1)
    for y in range(0, H, 60):
        draw.line([(0,y),(W,y)], fill=(*ACCENT,18), width=1)
    b = 18
    draw.rectangle([b,b,W-b,H-b], outline=ACCENT, width=2)
    for cx,cy,dx,dy in [(b,b,1,1),(W-b,b,-1,1),(b,H-b,1,-1),(W-b,H-b,-1,-1)]:
        draw.line([(cx,cy),(cx+dx*30,cy)], fill=ACCENT, width=3)
        draw.line([(cx,cy),(cx,cy+dy*30)], fill=ACCENT, width=3)
    try:
        fb = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 90)
        fs = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
    except:
        fb = fs = ImageFont.load_default()
    bb = draw.textbbox((0,0), APP_NAME, font=fb)
    draw.text(((W-(bb[2]-bb[0]))/2 - bb[0], 220), APP_NAME, font=fb, fill=ACCENT)
    bb2 = draw.textbbox((0,0), SUB, font=fs)
    draw.text(((W-(bb2[2]-bb2[0]))/2 - bb2[0], 340), SUB, font=fs, fill=(180,210,190))
    draw.line([(W//2-180,400),(W//2+180,400)], fill=ACCENT, width=2)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, "PNG")

for size, name in [(16,"16x16"),(24,"24x24"),(32,"32x32"),(64,"64x64"),(180,"180x180"),(512,"512x512")]:
    make_icon(size, f"{PUBLIC}/images/{name}.png")
make_og(f"{PUBLIC}/images/thumbnail/share.png")
```

Run via Bash tool. Install Pillow first if needed: `pip3 install pillow -q`

## Validation Checklist

After replacing, verify:
- [ ] No duplicate `<meta charset>` or `<meta viewport>`
- [ ] `<title>` matches `og:title` and `twitter:title`
- [ ] All `content=""` fields are non-empty
- [ ] `og:image` path exists in `public/` (warn if not)
- [ ] `canonical` URL is absolute (warn if empty)
