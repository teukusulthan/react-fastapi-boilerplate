#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Design System Generator - Aggregates search results and applies reasoning
to generate comprehensive design system recommendations.

Usage:
    from design_system import generate_design_system
    result = generate_design_system("SaaS dashboard", "My Project")

    # With file output (writes variable.css, tailwind.css, DESIGN.md)
    result = generate_design_system("SaaS dashboard", "My Project",
                                    persist=True, platform="web", theme="tactical")

Output files (design/<platform>/<theme>/):
    variable.css  — CSS custom properties (:root + .dark)
    tailwind.css  — Tailwind v4 @theme inline block (static, references CSS vars)
    DESIGN.md     — Human-readable style reference

Note: variable.yml / tailwind.yml in references/template/ are schema references only.
      They define the key structure; actual output is always .css files.
"""

import csv
import json
import os
import shutil
from pathlib import Path
from core import search, DATA_DIR


# ============ CONFIGURATION ============
REASONING_FILE = "ui-reasoning.csv"

SEARCH_CONFIG = {
    "product": {"max_results": 1},
    "style": {"max_results": 3},
    "color": {"max_results": 2},
    "landing": {"max_results": 2},
    "typography": {"max_results": 2}
}

TEMPLATE_DIR = Path(__file__).parent.parent / "references" / "template"


# ============ COLOR UTILITIES ============

def _hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip('#')
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return '#{:02X}{:02X}{:02X}'.format(
        max(0, min(255, round(r))),
        max(0, min(255, round(g))),
        max(0, min(255, round(b)))
    )


def _rgb_to_hsl(r: int, g: int, b: int) -> tuple:
    r, g, b = r / 255, g / 255, b / 255
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2
    if mx == mn:
        h = s = 0.0
    else:
        d = mx - mn
        s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
        if mx == r:
            h = (g - b) / d + (6 if g < b else 0)
        elif mx == g:
            h = (b - r) / d + 2
        else:
            h = (r - g) / d + 4
        h /= 6
    return h * 360, s * 100, l * 100


def _hsl_to_rgb(h: float, s: float, l: float) -> tuple:
    h, s, l = h / 360, s / 100, l / 100

    def _hue(p, q, t):
        if t < 0: t += 1
        if t > 1: t -= 1
        if t < 1/6: return p + (q - p) * 6 * t
        if t < 1/2: return q
        if t < 2/3: return p + (q - p) * (2/3 - t) * 6
        return p

    if s == 0:
        r = g = b = l
    else:
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = _hue(p, q, h + 1/3)
        g = _hue(p, q, h)
        b = _hue(p, q, h - 1/3)
    return round(r * 255), round(g * 255), round(b * 255)


def _hsl_to_hex(h: float, s: float, l: float) -> str:
    return _rgb_to_hex(*_hsl_to_rgb(h, s, l))


def generate_color_ramp(base_hex: str) -> dict:
    """
    Generate a 9-stop (50–900) color ramp from a base hex treated as the ~500 stop.
    Lighter stops interpolate toward white; darker stops reduce lightness while
    preserving hue and saturation.
    """
    r, g, b = _hex_to_rgb(base_hex)
    h, s, l = _rgb_to_hsl(r, g, b)

    # Lightness targets relative to base (l at 500)
    # Stops 50-400: lerp from 97% toward base; Stops 600-900: darken from base
    stop_lightness = {
        50:  97.0,
        100: 93.0,
        200: 86.0,
        300: 76.0,
        400: 64.0,
        500: l,
        600: l * 0.84,
        700: l * 0.65,
        800: l * 0.48,
        900: l * 0.34,
    }

    ramp = {}
    for stop, target_l in stop_lightness.items():
        if stop <= 400:
            # Reduce saturation slightly as it gets lighter
            ratio = (target_l - l) / (97.0 - l) if (97.0 - l) != 0 else 0
            adj_s = s * (1 - ratio * 0.5)
        else:
            adj_s = s
        ramp[stop] = _hsl_to_hex(h, max(0, min(100, adj_s)), max(2, min(98, target_l)))

    # Always keep exact base at 500
    ramp[500] = base_hex.upper() if base_hex.startswith('#') else f'#{base_hex.upper()}'
    return ramp


def _shift_hue(hex_color: str, degrees: float) -> str:
    """Return a hex with hue rotated by `degrees`."""
    r, g, b = _hex_to_rgb(hex_color)
    h, s, l = _rgb_to_hsl(r, g, b)
    return _hsl_to_hex((h + degrees) % 360, s, l)


def _generate_palette(primary_hex: str, secondary_hex: str) -> dict:
    """
    Generate full brand + state palette from primary and secondary base hex values.
    Tertiary/quaternary/quinary are derived as hue-shifted variants of primary.
    State colors use standard semantic hues.
    """
    # Neutral: slight cool-gray tint from primary hue
    r, g, b = _hex_to_rgb(primary_hex)
    h_p, _, _ = _rgb_to_hsl(r, g, b)
    neutral_base = _hsl_to_hex(h_p, 6, 50)

    return {
        "neutral":    generate_color_ramp(neutral_base),
        "primary":    generate_color_ramp(primary_hex),
        "secondary":  generate_color_ramp(secondary_hex),
        "tertiary":   generate_color_ramp(_shift_hue(primary_hex, 150)),
        "quaternary": generate_color_ramp(_shift_hue(primary_hex, 210)),
        "quinary":    generate_color_ramp(_shift_hue(primary_hex, 60)),
        "success":    generate_color_ramp("#16A086"),
        "warning":    generate_color_ramp("#FFAF05"),
        "error":      generate_color_ramp("#D12727"),
        "info":       generate_color_ramp("#0177AD"),
    }


# ============ VARIABLE.CSS GENERATOR ============

_STOPS = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900]


def _invert_ramp(light_ramp: dict) -> dict:
    """Invert a light-mode ramp for dark mode (stop 50 ↔ 900, etc.)."""
    rev = _STOPS[::-1]
    return {stop: light_ramp[rev[i]] for i, stop in enumerate(_STOPS)}


def _css_palette_block(palette: dict) -> str:
    """Render all base-{color}-{stop} vars from palette dict."""
    lines = []
    labels = {
        "neutral": "Neutral", "primary": "Primary", "secondary": "Secondary",
        "tertiary": "Tertiary", "quaternary": "Quaternary", "quinary": "Quinary",
        "success": "Success", "warning": "Warning", "error": "Error", "info": "Info",
    }
    for color, label in labels.items():
        ramp = palette.get(color, {})
        if not ramp:
            continue
        lines.append(f"\n  /* {label} */")
        for stop in _STOPS:
            lines.append(f"  --base-{color}-{stop}: {ramp[stop]};")
    return "\n".join(lines)


_SEMANTIC_LIGHT = """\

  --bg-primary: var(--base-neutral-50);
  --bg-secondary: var(--base-neutral-100);
  --border-primary: var(--base-neutral-200);
  --border-secondary: var(--base-neutral-300);
  --text-color-primary: var(--base-neutral-900);
  --text-color-secondary: var(--base-neutral-600);
  --text-color-placeholder: var(--base-neutral-500);
  --text-color-disabled: var(--base-neutral-400);
  --text-color-on-accent: var(--base-neutral-50);

  --primary-light: var(--base-primary-50);
  --primary-soft: var(--base-primary-200);
  --primary-base: var(--base-primary-500);
  --primary-bold: var(--base-primary-700);
  --primary-deep: var(--base-primary-900);
  --secondary-light: var(--base-secondary-50);
  --secondary-soft: var(--base-secondary-200);
  --secondary-base: var(--base-secondary-500);
  --secondary-bold: var(--base-secondary-700);
  --secondary-deep: var(--base-secondary-900);
  --tertiary-light: var(--base-tertiary-50);
  --tertiary-soft: var(--base-tertiary-200);
  --tertiary-base: var(--base-tertiary-500);
  --tertiary-bold: var(--base-tertiary-700);
  --tertiary-deep: var(--base-tertiary-900);
  --quaternary-light: var(--base-quaternary-50);
  --quaternary-soft: var(--base-quaternary-200);
  --quaternary-base: var(--base-quaternary-500);
  --quaternary-bold: var(--base-quaternary-700);
  --quaternary-deep: var(--base-quaternary-900);
  --quinary-light: var(--base-quinary-50);
  --quinary-soft: var(--base-quinary-200);
  --quinary-base: var(--base-quinary-500);
  --quinary-bold: var(--base-quinary-700);
  --quinary-deep: var(--base-quinary-900);
  --neutral-light: var(--base-neutral-50);
  --neutral-soft: var(--base-neutral-200);
  --neutral-base: var(--base-neutral-500);
  --neutral-bold: var(--base-neutral-700);
  --neutral-deep: var(--base-neutral-900);

  --success-light: var(--base-success-50);
  --success-soft: var(--base-success-200);
  --success-base: var(--base-success-500);
  --success-bold: var(--base-success-700);
  --success-deep: var(--base-success-900);
  --error-light: var(--base-error-50);
  --error-soft: var(--base-error-200);
  --error-base: var(--base-error-500);
  --error-bold: var(--base-error-700);
  --error-deep: var(--base-error-900);
  --info-light: var(--base-info-50);
  --info-soft: var(--base-info-200);
  --info-base: var(--base-info-500);
  --info-bold: var(--base-info-700);
  --info-deep: var(--base-info-900);
  --warning-light: var(--base-warning-50);
  --warning-soft: var(--base-warning-200);
  --warning-base: var(--base-warning-500);
  --warning-bold: var(--base-warning-700);
  --warning-deep: var(--base-warning-900);"""


_SPACING_STATIC = """\

  --spacing-1: 0.25rem;
  --spacing-1-5: 0.375rem;
  --spacing-2: 0.5rem;
  --spacing-2-5: 0.625rem;
  --spacing-3: 0.75rem;
  --spacing-3-5: 0.875rem;
  --spacing-4: 1rem;
  --spacing-5: 1.25rem;
  --spacing-6: 1.5rem;
  --spacing-8: 2rem;
  --spacing-10: 2.5rem;"""


_SHADOW_STATIC = """\

  --shadow-color: 0 0 0;

  --shadow-2xs: 0 0.0625rem rgb(var(--shadow-color) / 0.05);
  --shadow-xs: 0 0.0625rem 0.125rem 0 rgb(var(--shadow-color) / 0.05);
  --shadow-sm: 0 0.0625rem 0.1875rem 0 rgb(var(--shadow-color) / 0.1), 0 0.0625rem 0.125rem -0.0625rem rgb(var(--shadow-color) / 0.1);
  --shadow-md: 0 0.25rem 0.375rem -0.0625rem rgb(var(--shadow-color) / 0.1), 0 0.125rem 0.25rem -0.125rem rgb(var(--shadow-color) / 0.1);
  --shadow-lg: 0 0.625rem 0.9375rem -0.1875rem rgb(var(--shadow-color) / 0.1), 0 0.25rem 0.375rem -0.25rem rgb(var(--shadow-color) / 0.1);
  --shadow-xl: 0 1.25rem 1.5625rem -0.3125rem rgb(var(--shadow-color) / 0.1), 0 0.5rem 0.625rem -0.375rem rgb(var(--shadow-color) / 0.1);
  --shadow-2xl: 0 1.5625rem 3.125rem -0.75rem rgb(var(--shadow-color) / 0.25);
  --inset-shadow-2xs: inset 0 0.0625rem rgb(var(--shadow-color) / 0.05);
  --inset-shadow-xs: inset 0 0.0625rem 0.125rem 0 rgb(var(--shadow-color) / 0.05);
  --inset-shadow-sm: inset 0 0.125rem 0.25rem 0 rgb(var(--shadow-color) / 0.05);"""


_RADIUS_STATIC = """\

  --radius: 0.5rem;
  --radius-sm: 0.375rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.625rem;
  --radius-xl: 0.75rem;
  --radius-2xl: 1rem;
  --radius-3xl: 1.25rem;
  --radius-full: 9999px;"""


_TYPOGRAPHY_SCALE_STATIC = """\

  --text-display: 3.75rem;
  --text-h1: 2.75rem;
  --text-h2: 2.25rem;
  --text-h3: 1.75rem;
  --text-h4: 1.5rem;
  --text-h5: 1.25rem;
  --text-h6: 1.125rem;
  --text-body-lg: 1rem;
  --text-body-md: 0.875rem;
  --text-body-sm: 0.75rem;
  --text-label-lg: 1rem;
  --text-label-md: 0.875rem;
  --text-label-sm: 0.75rem;

  --font-weight-thin: 100;
  --font-weight-extralight: 200;
  --font-weight-light: 300;
  --font-weight-normal: 400;
  --font-weight-regular: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;
  --font-weight-extrabold: 800;
  --font-weight-black: 900;

  --leading-none: 1;
  --leading-tight: 1.25;
  --leading-snug: 1.375;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;
  --leading-loose: 2;

  --tracking-tighter: -0.05em;
  --tracking-tight: -0.025em;
  --tracking-normal: 0em;
  --tracking-wide: 0.025em;
  --tracking-wider: 0.05em;
  --tracking-widest: 0.1em;"""


_SHADCN_LIGHT = """\

  --background: var(--base-neutral-100);
  --foreground: var(--text-color-primary);
  --card: var(--bg-primary);
  --card-foreground: var(--text-color-primary);
  --popover: var(--bg-primary);
  --popover-foreground: var(--text-color-primary);
  --primary: var(--primary-base);
  --primary-foreground: var(--text-color-on-accent);
  --secondary: var(--bg-secondary);
  --secondary-foreground: var(--text-color-primary);
  --tertiary: var(--tertiary-base);
  --tertiary-foreground: var(--text-color-on-accent);
  --quaternary: var(--quaternary-base);
  --quaternary-foreground: var(--text-color-on-accent);
  --quinary: var(--quinary-base);
  --quinary-foreground: var(--text-color-on-accent);
  --muted: var(--bg-secondary);
  --muted-foreground: var(--text-color-placeholder);
  --accent: var(--primary-light);
  --accent-foreground: var(--primary-bold);
  --destructive: var(--error-base);
  --destructive-foreground: var(--text-color-on-accent);
  --border: var(--border-primary);
  --input: var(--border-primary);
  --ring: var(--primary-soft);

  --sidebar: var(--bg-primary);
  --sidebar-foreground: var(--text-color-primary);
  --sidebar-primary: var(--primary-base);
  --sidebar-primary-foreground: var(--text-color-on-accent);
  --sidebar-accent: var(--primary-light);
  --sidebar-accent-foreground: var(--primary-bold);
  --sidebar-border: var(--border-primary);
  --sidebar-ring: var(--primary-soft);

  --chart-1: var(--primary-base);
  --chart-2: var(--secondary-base);
  --chart-3: var(--tertiary-base);
  --chart-4: var(--quaternary-base);
  --chart-5: var(--quinary-base);"""


_SEMANTIC_DARK = """\

  --bg-primary: var(--base-neutral-50);
  --bg-secondary: var(--base-neutral-100);
  --border-primary: var(--base-neutral-300);
  --border-secondary: var(--base-neutral-400);
  --text-color-primary: var(--base-neutral-900);
  --text-color-secondary: var(--base-neutral-600);
  --text-color-placeholder: var(--base-neutral-500);
  --text-color-disabled: var(--base-neutral-400);
  --text-color-on-accent: var(--base-neutral-900);

  --primary-light: var(--base-primary-50);
  --primary-soft: var(--base-primary-200);
  --primary-base: var(--base-primary-500);
  --primary-bold: var(--base-primary-700);
  --primary-deep: var(--base-primary-900);
  --secondary-light: var(--base-secondary-50);
  --secondary-soft: var(--base-secondary-200);
  --secondary-base: var(--base-secondary-500);
  --secondary-bold: var(--base-secondary-700);
  --secondary-deep: var(--base-secondary-900);
  --tertiary-light: var(--base-tertiary-50);
  --tertiary-soft: var(--base-tertiary-200);
  --tertiary-base: var(--base-tertiary-500);
  --tertiary-bold: var(--base-tertiary-700);
  --tertiary-deep: var(--base-tertiary-900);
  --quaternary-light: var(--base-quaternary-50);
  --quaternary-soft: var(--base-quaternary-200);
  --quaternary-base: var(--base-quaternary-500);
  --quaternary-bold: var(--base-quaternary-700);
  --quaternary-deep: var(--base-quaternary-900);
  --quinary-light: var(--base-quinary-50);
  --quinary-soft: var(--base-quinary-200);
  --quinary-base: var(--base-quinary-500);
  --quinary-bold: var(--base-quinary-700);
  --quinary-deep: var(--base-quinary-900);
  --neutral-light: var(--base-neutral-50);
  --neutral-soft: var(--base-neutral-300);
  --neutral-base: var(--base-neutral-500);
  --neutral-bold: var(--base-neutral-700);
  --neutral-deep: var(--base-neutral-900);

  --success-light: var(--base-success-50);
  --success-soft: var(--base-success-200);
  --success-base: var(--base-success-500);
  --success-bold: var(--base-success-700);
  --success-deep: var(--base-success-900);
  --error-light: var(--base-error-50);
  --error-soft: var(--base-error-200);
  --error-base: var(--base-error-500);
  --error-bold: var(--base-error-700);
  --error-deep: var(--base-error-900);
  --info-light: var(--base-info-50);
  --info-soft: var(--base-info-200);
  --info-base: var(--base-info-500);
  --info-bold: var(--base-info-700);
  --info-deep: var(--base-info-900);
  --warning-light: var(--base-warning-50);
  --warning-soft: var(--base-warning-200);
  --warning-base: var(--base-warning-500);
  --warning-bold: var(--base-warning-700);
  --warning-deep: var(--base-warning-900);"""


_SHADCN_DARK = """\

  --background: var(--bg-primary);
  --foreground: var(--text-color-primary);
  --card: var(--bg-secondary);
  --card-foreground: var(--text-color-primary);
  --popover: var(--bg-primary);
  --popover-foreground: var(--text-color-primary);
  --primary: var(--primary-base);
  --primary-foreground: var(--text-color-on-accent);
  --secondary: var(--bg-secondary);
  --secondary-foreground: var(--text-color-primary);
  --tertiary: var(--tertiary-base);
  --tertiary-foreground: var(--text-color-on-accent);
  --quaternary: var(--quaternary-base);
  --quaternary-foreground: var(--text-color-on-accent);
  --quinary: var(--quinary-base);
  --quinary-foreground: var(--text-color-on-accent);
  --muted: var(--bg-secondary);
  --muted-foreground: var(--text-color-placeholder);
  --accent: var(--primary-light);
  --accent-foreground: var(--primary-bold);
  --destructive: var(--error-base);
  --destructive-foreground: var(--text-color-on-accent);
  --input: var(--border-primary);
  --ring: var(--primary-soft);

  --sidebar: var(--bg-secondary);
  --sidebar-foreground: var(--text-color-primary);
  --sidebar-primary: var(--primary-base);
  --sidebar-primary-foreground: var(--text-color-on-accent);
  --sidebar-accent: var(--primary-light);
  --sidebar-accent-foreground: var(--primary-bold);
  --sidebar-border: var(--border-primary);
  --sidebar-ring: var(--primary-soft);

  --chart-1: var(--primary-base);
  --chart-2: var(--secondary-base);
  --chart-3: var(--tertiary-base);
  --chart-4: var(--quaternary-base);
  --chart-5: var(--quinary-base);

  --shadow-color: 255 255 255;"""


def _font_stack(heading: str, body: str) -> str:
    base = "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    if heading != body:
        return f"'{heading}', '{body}', {base}"
    return f"'{heading}', {base}"


def _write_variable_css(palette: dict, typography: dict, output_path: Path) -> None:
    """Generate variable.css with :root and .dark blocks."""
    heading = typography.get("heading", "Inter")
    body    = typography.get("body", "Inter")
    font_sans = _font_stack(heading, body)
    font_mono = "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace"

    dark_palette = {color: _invert_ramp(ramp) for color, ramp in palette.items()}

    root_block = (
        ":root {"
        + _css_palette_block(palette)
        + _SEMANTIC_LIGHT
        + _SPACING_STATIC
        + _SHADOW_STATIC
        + _RADIUS_STATIC
        + _TYPOGRAPHY_SCALE_STATIC
        + f"\n\n  --font-sans: {font_sans};"
        + f"\n  --font-serif: {font_sans};"
        + f"\n  --font-mono: {font_mono};"
        + _SHADCN_LIGHT
        + "\n}\n"
    )

    dark_block = (
        "\n.dark {"
        + _css_palette_block(dark_palette)
        + _SEMANTIC_DARK
        + _SHADCN_DARK
        + "\n}\n"
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(root_block)
        f.write(dark_block)


def _write_tailwind_css(output_path: Path) -> None:
    """Copy the static tailwind.css template to the output path."""
    src = TEMPLATE_DIR / "tailwind.css"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, output_path)


# ============ DESIGN.MD BUILDER ============

def _fill_design_md(design_system: dict, palette: dict, output_path: Path) -> None:
    """Fill DESIGN.md template placeholders from design system + generated palette."""
    tpl_path = TEMPLATE_DIR / "DESIGN.md"
    with open(tpl_path, "r", encoding="utf-8") as f:
        content = f.read()

    typography = design_system.get("typography", {})
    style      = design_system.get("style", {})
    project    = design_system.get("project_name", "Default")

    def _p(color: str, stop: int) -> str:
        return palette.get(color, {}).get(stop, "")

    # Dark neutral: inverted from light neutral ramp
    dark_neutral = _invert_ramp(palette.get("neutral", {}))

    has_dark  = style.get("dark_mode", "").strip()

    replacements = {
        "{{THEME_NAME}}":             project,
        "{{THEME_DESCRIPTION}}":      f"{style.get('name', 'Minimal')} design system for {project}",
        "{{THEME_MODE}}":             "Light + Dark" if has_dark else "Light",
        "{{FONT_FAMILY}}":            typography.get("heading", "Inter"),
        "{{RADIUS_SM}}":              "0.25rem",
        "{{RADIUS_MD}}":              "0.375rem",
        "{{DENSITY}}":                "Comfortable",
        "{{BG_PRIMARY_LIGHT}}":       _p("neutral", 50),
        "{{BG_PRIMARY_DARK}}":        dark_neutral.get(50, _p("neutral", 900)),
        "{{BG_SECONDARY_LIGHT}}":     _p("neutral", 100),
        "{{BG_SECONDARY_DARK}}":      dark_neutral.get(100, _p("neutral", 800)),
        "{{BORDER_PRIMARY_LIGHT}}":   _p("neutral", 200),
        "{{BORDER_PRIMARY_DARK}}":    dark_neutral.get(300, _p("neutral", 700)),
        "{{BORDER_SECONDARY_LIGHT}}": _p("neutral", 300),
        "{{BORDER_SECONDARY_DARK}}":  dark_neutral.get(400, _p("neutral", 600)),
        "{{TEXT_PRIMARY_LIGHT}}":     _p("neutral", 900),
        "{{TEXT_PRIMARY_DARK}}":      dark_neutral.get(900, _p("neutral", 50)),
        "{{TEXT_SECONDARY_LIGHT}}":   _p("neutral", 600),
        "{{TEXT_SECONDARY_DARK}}":    dark_neutral.get(600, _p("neutral", 300)),
        "{{TEXT_PLACEHOLDER_LIGHT}}": _p("neutral", 500),
        "{{TEXT_PLACEHOLDER_DARK}}":  dark_neutral.get(500, _p("neutral", 400)),
        "{{TEXT_DISABLED_LIGHT}}":    _p("neutral", 400),
        "{{TEXT_DISABLED_DARK}}":     dark_neutral.get(400, _p("neutral", 500)),
        "{{TEXT_ON_ACCENT_LIGHT}}":   _p("neutral", 50),
        "{{TEXT_ON_ACCENT_DARK}}":    dark_neutral.get(900, _p("neutral", 50)),
        "{{SIZE_DISPLAY}}":           "3.75rem",
        "{{SIZE_BODY_LG}}":           "1rem",
        "{{SIZE_BODY_MD}}":           "0.875rem",
        "{{SIZE_BODY_SM}}":           "0.75rem",
        "{{SIZE_LABEL_LG}}":          "1rem",
        "{{SIZE_LABEL_MD}}":          "0.875rem",
        "{{SIZE_LABEL_SM}}":          "0.75rem",
        "{{SPACE_BASE}}":             "0.5rem",
        "{{SPACE_1}}":                "0.25rem",
        "{{SPACE_10}}":               "2.5rem",
    }

    for placeholder, value in replacements.items():
        content = content.replace(placeholder, str(value))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


# ============ DESIGN SYSTEM GENERATOR ============
class DesignSystemGenerator:
    """Generates design system recommendations from aggregated searches."""

    def __init__(self):
        self.reasoning_data = self._load_reasoning()

    def _load_reasoning(self) -> list:
        filepath = DATA_DIR / REASONING_FILE
        if not filepath.exists():
            return []
        with open(filepath, 'r', encoding='utf-8') as f:
            return list(csv.DictReader(f))

    def _multi_domain_search(self, query: str, style_priority: list = None) -> dict:
        results = {}
        for domain, config in SEARCH_CONFIG.items():
            if domain == "style" and style_priority:
                priority_query = " ".join(style_priority[:2]) if style_priority else query
                combined_query = f"{query} {priority_query}"
                results[domain] = search(combined_query, domain, config["max_results"])
            else:
                results[domain] = search(query, domain, config["max_results"])
        return results

    def _find_reasoning_rule(self, category: str) -> dict:
        category_lower = category.lower()
        for rule in self.reasoning_data:
            if rule.get("UI_Category", "").lower() == category_lower:
                return rule
        for rule in self.reasoning_data:
            ui_cat = rule.get("UI_Category", "").lower()
            if ui_cat in category_lower or category_lower in ui_cat:
                return rule
        for rule in self.reasoning_data:
            ui_cat = rule.get("UI_Category", "").lower()
            keywords = ui_cat.replace("/", " ").replace("-", " ").split()
            if any(kw in category_lower for kw in keywords):
                return rule
        return {}

    def _apply_reasoning(self, category: str, search_results: dict) -> dict:  # noqa: ARG002
        rule = self._find_reasoning_rule(category)
        if not rule:
            return {
                "pattern": "Hero + Features + CTA",
                "style_priority": ["Minimalism", "Flat Design"],
                "color_mood": "Professional",
                "typography_mood": "Clean",
                "key_effects": "Subtle hover transitions",
                "anti_patterns": "",
                "decision_rules": {},
                "severity": "MEDIUM"
            }
        decision_rules = {}
        try:
            decision_rules = json.loads(rule.get("Decision_Rules", "{}"))
        except json.JSONDecodeError:
            pass
        return {
            "pattern": rule.get("Recommended_Pattern", ""),
            "style_priority": [s.strip() for s in rule.get("Style_Priority", "").split("+")],
            "color_mood": rule.get("Color_Mood", ""),
            "typography_mood": rule.get("Typography_Mood", ""),
            "key_effects": rule.get("Key_Effects", ""),
            "anti_patterns": rule.get("Anti_Patterns", ""),
            "decision_rules": decision_rules,
            "severity": rule.get("Severity", "MEDIUM")
        }

    def _select_best_match(self, results: list, priority_keywords: list) -> dict:
        if not results:
            return {}
        if not priority_keywords:
            return results[0]
        for priority in priority_keywords:
            priority_lower = priority.lower().strip()
            for result in results:
                style_name = result.get("Style Category", "").lower()
                if priority_lower in style_name or style_name in priority_lower:
                    return result
        scored = []
        for result in results:
            result_str = str(result).lower()
            score = 0
            for kw in priority_keywords:
                kw_lower = kw.lower().strip()
                if kw_lower in result.get("Style Category", "").lower():
                    score += 10
                elif kw_lower in result.get("Keywords", "").lower():
                    score += 3
                elif kw_lower in result_str:
                    score += 1
            scored.append((score, result))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1] if scored and scored[0][0] > 0 else results[0]

    def _extract_results(self, search_result: dict) -> list:
        return search_result.get("results", [])

    def generate(self, query: str, project_name: str = None) -> dict:
        product_result = search(query, "product", 1)
        product_results = product_result.get("results", [])
        category = "General"
        if product_results:
            category = product_results[0].get("Product Type", "General")

        reasoning = self._apply_reasoning(category, {})
        style_priority = reasoning.get("style_priority", [])

        search_results = self._multi_domain_search(query, style_priority)
        search_results["product"] = product_result

        style_results      = self._extract_results(search_results.get("style", {}))
        color_results      = self._extract_results(search_results.get("color", {}))
        typography_results = self._extract_results(search_results.get("typography", {}))
        landing_results    = self._extract_results(search_results.get("landing", {}))

        best_style      = self._select_best_match(style_results, reasoning.get("style_priority", []))
        best_color      = color_results[0] if color_results else {}
        best_typography = typography_results[0] if typography_results else {}
        best_landing    = landing_results[0] if landing_results else {}

        style_effects   = best_style.get("Effects & Animation", "")
        reasoning_effects = reasoning.get("key_effects", "")
        combined_effects = style_effects if style_effects else reasoning_effects

        return {
            "project_name": project_name or query.upper(),
            "category": category,
            "pattern": {
                "name": best_landing.get("Pattern Name", reasoning.get("pattern", "Hero + Features + CTA")),
                "sections": best_landing.get("Section Order", "Hero > Features > CTA"),
                "cta_placement": best_landing.get("Primary CTA Placement", "Above fold"),
                "color_strategy": best_landing.get("Color Strategy", ""),
                "conversion": best_landing.get("Conversion Optimization", "")
            },
            "style": {
                "name": best_style.get("Style Category", "Minimalism"),
                "type": best_style.get("Type", "General"),
                "effects": style_effects,
                "keywords": best_style.get("Keywords", ""),
                "best_for": best_style.get("Best For", ""),
                "performance": best_style.get("Performance", ""),
                "accessibility": best_style.get("Accessibility", ""),
                "light_mode": best_style.get("Light Mode ✓", ""),
                "dark_mode": best_style.get("Dark Mode ✓", ""),
            },
            "colors": {
                "primary":     best_color.get("Primary", "#2563EB"),
                "on_primary":  best_color.get("On Primary", ""),
                "secondary":   best_color.get("Secondary", "#3B82F6"),
                "accent":      best_color.get("Accent", "#F97316"),
                "background":  best_color.get("Background", "#F8FAFC"),
                "foreground":  best_color.get("Foreground", "#1E293B"),
                "muted":       best_color.get("Muted", ""),
                "border":      best_color.get("Border", ""),
                "destructive": best_color.get("Destructive", ""),
                "ring":        best_color.get("Ring", ""),
                "notes":       best_color.get("Notes", ""),
                "cta":         best_color.get("Accent", "#F97316"),
                "text":        best_color.get("Foreground", "#1E293B"),
            },
            "typography": {
                "heading":          best_typography.get("Heading Font", "Inter"),
                "body":             best_typography.get("Body Font", "Inter"),
                "mood":             best_typography.get("Mood/Style Keywords", reasoning.get("typography_mood", "")),
                "best_for":         best_typography.get("Best For", ""),
                "google_fonts_url": best_typography.get("Google Fonts URL", ""),
                "css_import":       best_typography.get("CSS Import", "")
            },
            "key_effects":    combined_effects,
            "anti_patterns":  reasoning.get("anti_patterns", ""),
            "decision_rules": reasoning.get("decision_rules", {}),
            "severity":       reasoning.get("severity", "MEDIUM")
        }


# ============ OUTPUT FORMATTERS ============
BOX_WIDTH = 90


def hex_to_ansi(hex_color: str) -> str:
    if not hex_color or not hex_color.startswith('#'):
        return ""
    colorterm = os.environ.get('COLORTERM', '')
    if colorterm not in ('truecolor', '24bit'):
        return ""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        return ""
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"\033[38;2;{r};{g};{b}m██\033[0m "


def ansi_ljust(s: str, width: int) -> str:
    import re
    visible_len = len(re.sub(r'\033\[[0-9;]*m', '', s))
    pad = width - visible_len
    return s + (" " * max(0, pad))


def section_header(name: str, width: int) -> str:
    label = f"─── {name} "
    fill = "─" * (width - len(label) - 1)
    return f"├{label}{fill}┤"


def format_ascii_box(design_system: dict) -> str:
    project      = design_system.get("project_name", "PROJECT")
    pattern      = design_system.get("pattern", {})
    style        = design_system.get("style", {})
    colors       = design_system.get("colors", {})
    typography   = design_system.get("typography", {})
    effects      = design_system.get("key_effects", "")
    anti_patterns = design_system.get("anti_patterns", "")

    def wrap_text(text: str, prefix: str, width: int) -> list:
        if not text:
            return []
        words = text.split()
        lines = []
        current_line = prefix
        for word in words:
            if len(current_line) + len(word) + 1 <= width - 2:
                current_line += (" " if current_line != prefix else "") + word
            else:
                if current_line != prefix:
                    lines.append(current_line)
                current_line = prefix + word
        if current_line != prefix:
            lines.append(current_line)
        return lines

    sections = pattern.get("sections", "").split(">")
    sections = [s.strip() for s in sections if s.strip()]

    lines = []
    w = BOX_WIDTH - 1

    lines.append("╔" + "═" * w + "╗")
    lines.append(ansi_ljust(f"║  TARGET: {project} - RECOMMENDED DESIGN SYSTEM", BOX_WIDTH) + "║")
    lines.append("╚" + "═" * w + "╝")
    lines.append("┌" + "─" * w + "┐")

    lines.append(section_header("PATTERN", BOX_WIDTH + 1))
    lines.append(f"│  Name: {pattern.get('name', '')}".ljust(BOX_WIDTH) + "│")
    if pattern.get('conversion'):
        lines.append(f"│     Conversion: {pattern.get('conversion', '')}".ljust(BOX_WIDTH) + "│")
    if pattern.get('cta_placement'):
        lines.append(f"│     CTA: {pattern.get('cta_placement', '')}".ljust(BOX_WIDTH) + "│")
    lines.append("│     Sections:".ljust(BOX_WIDTH) + "│")
    for i, section in enumerate(sections, 1):
        lines.append(f"│       {i}. {section}".ljust(BOX_WIDTH) + "│")

    lines.append(section_header("STYLE", BOX_WIDTH + 1))
    lines.append(f"│  Name: {style.get('name', '')}".ljust(BOX_WIDTH) + "│")
    light = style.get("light_mode", "")
    dark  = style.get("dark_mode", "")
    if light or dark:
        lines.append(f"│     Mode Support: Light {light}  Dark {dark}".ljust(BOX_WIDTH) + "│")
    if style.get("keywords"):
        for line in wrap_text(f"Keywords: {style.get('keywords', '')}", "│     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "│")
    if style.get("best_for"):
        for line in wrap_text(f"Best For: {style.get('best_for', '')}", "│     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "│")
    if style.get("performance") or style.get("accessibility"):
        perf_a11y = f"Performance: {style.get('performance', '')} | Accessibility: {style.get('accessibility', '')}"
        lines.append(f"│     {perf_a11y}".ljust(BOX_WIDTH) + "│")

    lines.append(section_header("COLORS", BOX_WIDTH + 1))
    color_entries = [
        ("Primary",     "primary",     "--color-primary"),
        ("On Primary",  "on_primary",  "--color-on-primary"),
        ("Secondary",   "secondary",   "--color-secondary"),
        ("Accent/CTA",  "accent",      "--color-accent"),
        ("Background",  "background",  "--color-background"),
        ("Foreground",  "foreground",  "--color-foreground"),
        ("Muted",       "muted",       "--color-muted"),
        ("Border",      "border",      "--color-border"),
        ("Destructive", "destructive", "--color-destructive"),
        ("Ring",        "ring",        "--color-ring"),
    ]
    for label, key, css_var in color_entries:
        hex_val = colors.get(key, "")
        if not hex_val:
            continue
        swatch = hex_to_ansi(hex_val)
        content = f"│     {swatch}{label + ':':14s} {hex_val:10s} ({css_var})"
        lines.append(ansi_ljust(content, BOX_WIDTH) + "│")
    if colors.get("notes"):
        for line in wrap_text(f"Notes: {colors.get('notes', '')}", "│     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "│")

    lines.append(section_header("TYPOGRAPHY", BOX_WIDTH + 1))
    lines.append(f"│  {typography.get('heading', '')} / {typography.get('body', '')}".ljust(BOX_WIDTH) + "│")
    if typography.get("mood"):
        for line in wrap_text(f"Mood: {typography.get('mood', '')}", "│     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "│")
    if typography.get("best_for"):
        for line in wrap_text(f"Best For: {typography.get('best_for', '')}", "│     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "│")
    if typography.get("google_fonts_url"):
        lines.append(f"│     Google Fonts: {typography.get('google_fonts_url', '')}".ljust(BOX_WIDTH) + "│")
    if typography.get("css_import"):
        lines.append(f"│     CSS Import: {typography.get('css_import', '')[:70]}...".ljust(BOX_WIDTH) + "│")

    if effects:
        lines.append(section_header("KEY EFFECTS", BOX_WIDTH + 1))
        for line in wrap_text(effects, "│     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "│")

    if anti_patterns:
        lines.append(section_header("AVOID", BOX_WIDTH + 1))
        for line in wrap_text(anti_patterns, "│     ", BOX_WIDTH):
            lines.append(line.ljust(BOX_WIDTH) + "│")

    lines.append(section_header("PRE-DELIVERY CHECKLIST", BOX_WIDTH + 1))
    for item in [
        "[ ] No emojis as icons (use Phosphor icons — the only icon set in apps/web)",
        "[ ] cursor-pointer on all clickable elements",
        "[ ] Hover states with smooth transitions (150-300ms)",
        "[ ] Light mode: text contrast 4.5:1 minimum",
        "[ ] Focus states visible for keyboard nav",
        "[ ] prefers-reduced-motion respected",
        "[ ] Responsive: 375px, 768px, 1024px, 1440px"
    ]:
        lines.append(f"│     {item}".ljust(BOX_WIDTH) + "│")

    lines.append("└" + "─" * w + "┘")
    return "\n".join(lines)


def format_markdown(design_system: dict) -> str:
    project      = design_system.get("project_name", "PROJECT")
    pattern      = design_system.get("pattern", {})
    style        = design_system.get("style", {})
    colors       = design_system.get("colors", {})
    typography   = design_system.get("typography", {})
    effects      = design_system.get("key_effects", "")
    anti_patterns = design_system.get("anti_patterns", "")

    lines = [f"## Design System: {project}", ""]

    lines += ["### Pattern", ""]
    lines.append(f"- **Name:** {pattern.get('name', '')}")
    if pattern.get('conversion'):
        lines.append(f"- **Conversion Focus:** {pattern.get('conversion', '')}")
    if pattern.get('cta_placement'):
        lines.append(f"- **CTA Placement:** {pattern.get('cta_placement', '')}")
    if pattern.get('color_strategy'):
        lines.append(f"- **Color Strategy:** {pattern.get('color_strategy', '')}")
    lines.append(f"- **Sections:** {pattern.get('sections', '')}")
    lines.append("")

    lines += ["### Style", ""]
    lines.append(f"- **Name:** {style.get('name', '')}")
    light, dark = style.get("light_mode", ""), style.get("dark_mode", "")
    if light or dark:
        lines.append(f"- **Mode Support:** Light {light} | Dark {dark}")
    if style.get('keywords'):
        lines.append(f"- **Keywords:** {style.get('keywords', '')}")
    if style.get('best_for'):
        lines.append(f"- **Best For:** {style.get('best_for', '')}")
    if style.get('performance') or style.get('accessibility'):
        lines.append(f"- **Performance:** {style.get('performance', '')} | **Accessibility:** {style.get('accessibility', '')}")
    lines.append("")

    lines += ["### Colors", "| Role | Hex | CSS Variable |", "|------|-----|--------------|"]
    md_color_entries = [
        ("Primary",     "primary",     "--color-primary"),
        ("On Primary",  "on_primary",  "--color-on-primary"),
        ("Secondary",   "secondary",   "--color-secondary"),
        ("Accent/CTA",  "accent",      "--color-accent"),
        ("Background",  "background",  "--color-background"),
        ("Foreground",  "foreground",  "--color-foreground"),
        ("Muted",       "muted",       "--color-muted"),
        ("Border",      "border",      "--color-border"),
        ("Destructive", "destructive", "--color-destructive"),
        ("Ring",        "ring",        "--color-ring"),
    ]
    for label, key, css_var in md_color_entries:
        hex_val = colors.get(key, "")
        if hex_val:
            lines.append(f"| {label} | `{hex_val}` | `{css_var}` |")
    if colors.get("notes"):
        lines.append(f"\n*Notes: {colors.get('notes', '')}*")
    lines.append("")

    lines += ["### Typography", ""]
    lines.append(f"- **Heading:** {typography.get('heading', '')}")
    lines.append(f"- **Body:** {typography.get('body', '')}")
    if typography.get("mood"):
        lines.append(f"- **Mood:** {typography.get('mood', '')}")
    if typography.get("best_for"):
        lines.append(f"- **Best For:** {typography.get('best_for', '')}")
    if typography.get("google_fonts_url"):
        lines.append(f"- **Google Fonts:** {typography.get('google_fonts_url', '')}")
    if typography.get("css_import"):
        lines += ["- **CSS Import:**", "```css", typography.get("css_import", ""), "```"]
    lines.append("")

    if effects:
        lines += ["### Key Effects", f"{effects}", ""]

    if anti_patterns:
        nb = '\n- '
        lines += ["### Avoid (Anti-patterns)", f"- {anti_patterns.replace(' + ', nb)}", ""]

    lines += [
        "### Pre-Delivery Checklist",
        "- [ ] No emojis as icons (use Phosphor icons — the only icon set in apps/web)",
        "- [ ] cursor-pointer on all clickable elements",
        "- [ ] Hover states with smooth transitions (150-300ms)",
        "- [ ] Light mode: text contrast 4.5:1 minimum",
        "- [ ] Focus states visible for keyboard nav",
        "- [ ] prefers-reduced-motion respected",
        "- [ ] Responsive: 375px, 768px, 1024px, 1440px",
        ""
    ]
    return "\n".join(lines)


# ============ MAIN ENTRY POINT ============
def generate_design_system(query: str, project_name: str = None, output_format: str = "ascii",
                           persist: bool = False, platform: str = "web", theme: str = None,
                           output_dir: str = None) -> str:
    """
    Main entry point for design system generation.

    Args:
        query:         Search query (e.g., "SaaS dashboard", "e-commerce luxury")
        project_name:  Optional project name for output header
        output_format: "ascii" (default) or "markdown"
        persist:       If True, write DESIGN.md + tailwind.yml + variable.yml to output_dir
        platform:      Target platform folder, e.g. "web" or "mobile" (used when persist=True)
        theme:         Theme folder name, e.g. "tactical" (defaults to slugified project_name)
        output_dir:    Root directory for output (defaults to cwd); files go to
                       <output_dir>/design/<platform>/<theme>/

    Returns:
        Formatted design system string (ascii box or markdown)
    """
    generator = DesignSystemGenerator()
    design_system = generator.generate(query, project_name)

    if persist:
        persist_design_system(design_system, platform=platform, theme=theme, output_dir=output_dir)

    if output_format == "markdown":
        return format_markdown(design_system)
    return format_ascii_box(design_system)


# ============ PERSISTENCE ============
def persist_design_system(design_system: dict, platform: str = "web", theme: str = None,
                          output_dir: str = None) -> dict:
    """
    Write the three design system files to design/<platform>/<theme>/:
      - variable.css  — CSS custom properties (:root light + .dark)
      - tailwind.css  — Tailwind v4 @theme inline block (static, references CSS vars)
      - DESIGN.md     — human-readable style reference (filled template)

    Args:
        design_system: The generated design system dictionary
        platform:      Target platform (e.g. "web", "mobile")
        theme:         Theme folder name (defaults to slugified project_name)
        output_dir:    Root output directory (defaults to cwd)

    Returns:
        dict with output_dir and created file paths

    Note:
        If `colors` contains all of primary, secondary, tertiary, quaternary, quinary,
        and neutral keys, each is used directly as the ramp anchor (stop 500 for brand
        colors, stop 900 for neutral). Otherwise falls back to deriving tertiary–quinary
        from the primary hue automatically.
    """
    colors = design_system.get("colors", {})
    typography = design_system.get("typography", {})

    _full_keys = {"primary", "secondary", "tertiary", "quaternary", "quinary", "neutral"}
    if _full_keys.issubset(colors.keys()):
        palette = {
            "neutral":    generate_color_ramp(colors["neutral"]),
            "primary":    generate_color_ramp(colors["primary"]),
            "secondary":  generate_color_ramp(colors["secondary"]),
            "tertiary":   generate_color_ramp(colors["tertiary"]),
            "quaternary": generate_color_ramp(colors["quaternary"]),
            "quinary":    generate_color_ramp(colors["quinary"]),
            "success":    generate_color_ramp(colors.get("success", "#16A086")),
            "warning":    generate_color_ramp(colors.get("warning", "#FFAF05")),
            "error":      generate_color_ramp(colors.get("error", "#D12727")),
            "info":       generate_color_ramp(colors.get("info", "#0177AD")),
        }
    else:
        primary_hex   = colors.get("primary", "#2563EB")
        secondary_hex = colors.get("accent") or colors.get("secondary", "#F97316")
        palette = _generate_palette(primary_hex, secondary_hex)

    base_dir = Path(output_dir) if output_dir else Path.cwd()

    if theme is None:
        project_name = design_system.get("project_name", "default")
        theme = project_name.lower().replace(' ', '-')

    dest = base_dir / "design" / platform / theme
    dest.mkdir(parents=True, exist_ok=True)

    _write_variable_css(palette, typography, dest / "variable.css")
    _write_tailwind_css(dest / "tailwind.css")
    _fill_design_md(design_system, palette, dest / "DESIGN.md")

    brand_src = TEMPLATE_DIR / "brand-guideline.html"
    brand_dest = dest / "brand-guideline.html"
    if brand_src.exists():
        shutil.copy2(brand_src, brand_dest)

    created = [
        str(dest / "variable.css"),
        str(dest / "tailwind.css"),
        str(dest / "DESIGN.md"),
        str(brand_dest),
    ]
    return {"status": "success", "output_dir": str(dest), "created_files": created}


# ============ CLI ============
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate Design System")
    parser.add_argument("query", help="Search query (e.g., 'SaaS dashboard')")
    parser.add_argument("--project-name", "-p", type=str, default=None, help="Project name")
    parser.add_argument("--format", "-f", choices=["ascii", "markdown"], default="ascii",
                        help="Display output format")
    parser.add_argument("--persist", action="store_true",
                        help="Write variable.css + tailwind.css + DESIGN.md to output-dir")
    parser.add_argument("--platform", type=str, default="web",
                        help="Target platform folder (default: web)")
    parser.add_argument("--theme", type=str, default=None,
                        help="Theme folder name (default: slugified project name)")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Root output directory (default: current working directory)")

    args = parser.parse_args()

    result = generate_design_system(
        args.query,
        args.project_name,
        args.format,
        persist=args.persist,
        platform=args.platform,
        theme=args.theme,
        output_dir=args.output_dir,
    )
    print(result)

    if args.persist:
        from pathlib import Path as _Path
        base = _Path(args.output_dir) if args.output_dir else _Path.cwd()
        theme_name = args.theme or (args.project_name or args.query).lower().replace(' ', '-')
        dest = base / "design" / args.platform / theme_name
        print(f"\nFiles written to: {dest}")
        for f in ["variable.css", "tailwind.css", "DESIGN.md"]:
            print(f"  ✓ {f}")
