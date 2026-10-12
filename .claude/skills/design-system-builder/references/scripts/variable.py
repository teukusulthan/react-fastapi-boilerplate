"""
Generate variable.css from variable.yml template + optional AI-provided colors/fonts.

Usage:
    python variable.py
    python variable.py \
      --colors '{"primary":"#60C8F0","secondary":"#2EA38C"}' \
      --fonts '{"sans":"Inter, sans-serif"}' \
      --output path/to/variable.css \
      --template path/to/variable.yml
"""

import argparse
import colorsys
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

SCRIPT_DIR  = Path(__file__).parent
DEFAULT_TPL = SCRIPT_DIR.parent / "template" / "variable.yml"
DEFAULT_OUT = "variable.css"

STATE_NAMES = ["success", "warning", "error", "info"]

# ─── COLOR GENERATION ────────────────────────────────────────────────────────

def hex_to_rgb(hex_str):
    h = hex_str.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return '#{:02X}{:02X}{:02X}'.format(*[max(0, min(255, int(x))) for x in rgb])

def adjust_for_dark_base(hex_str: str, lightness_boost: float = 0.12) -> str:
    """Brighten a brand color slightly for use as primary-base on dark backgrounds."""
    r, g, b = [x / 255.0 for x in hex_to_rgb(hex_str)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    new_l = min(0.85, l + lightness_boost)
    r2, g2, b2 = colorsys.hls_to_rgb(h, new_l, s)
    return rgb_to_hex((round(r2*255), round(g2*255), round(b2*255)))

def generate_palette(base_hex: str, is_brand: bool = False) -> dict:
    """Generate a 10-stop palette where base_hex is stop 500.

    Lightness is computed *relative* to the base so lighter stops (50-400)
    always interpolate toward L=0.96 and darker stops (600-900) always
    interpolate toward L=0.12.  This prevents the bug where a bright base
    (L > 0.545) makes stop 400 appear darker than 500.

    t-values (fraction from base toward the light/dark anchor):
      light side: 50→1.00, 100→0.85, 200→0.68, 300→0.48, 400→0.25
      dark  side: 600→0.35, 700→0.55, 800→0.72, 900→0.88
    """
    r, g, b = [x / 255.0 for x in hex_to_rgb(base_hex)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)

    L_LIGHT = 0.96   # anchor for stop 50
    L_DARK  = 0.12   # anchor for stop 900

    # (t toward light anchor, t toward dark anchor, s_mult)
    STOPS = {
        50:  (1.00, None, 0.30),
        100: (0.85, None, 0.45),
        200: (0.68, None, 0.65),
        300: (0.48, None, 0.80),
        400: (0.25, None, 0.92),
        500: None,
        600: (None, 0.35, 1.05),
        700: (None, 0.55, 1.08),
        800: (None, 0.72, 1.10),
        900: (None, 0.88, 1.12),
    }

    # Achromatic input (gray/white/black): generate a neutral blend ramp
    # using the base as stop 500, interpolating toward white (light) and
    # black (dark) without introducing any hue.
    if s < 0.05:
        br, bg, bb = hex_to_rgb(base_hex)
        _T = {
            50:  (1.00, None),
            100: (0.85, None),
            200: (0.68, None),
            300: (0.48, None),
            400: (0.25, None),
            500: None,
            600: (None, 0.35),
            700: (None, 0.55),
            800: (None, 0.72),
            900: (None, 0.88),
        }
        palette = {}
        for stop, spec in _T.items():
            if spec is None:
                palette[stop] = base_hex.upper() if base_hex.startswith('#') else f'#{base_hex.upper()}'
                continue
            t_light, t_dark = spec
            if t_light is not None:
                nr = round(br + (255 - br) * t_light)
                ng = round(bg + (255 - bg) * t_light)
                nb = round(bb + (255 - bb) * t_light)
            else:
                nr = round(br + (0 - br) * t_dark)
                ng = round(bg + (0 - bg) * t_dark)
                nb = round(bb + (0 - bb) * t_dark)
            palette[stop] = rgb_to_hex((nr, ng, nb))
        return palette

    s_min = 0.40 if is_brand else 0.0
    palette = {}
    for stop, spec in STOPS.items():
        if spec is None:
            palette[stop] = base_hex.upper() if base_hex.startswith('#') else f'#{base_hex.upper()}'
            continue
        t_light, t_dark, s_mult = spec
        if t_light is not None:
            new_l = l + (L_LIGHT - l) * t_light
            new_h = h
        else:
            new_l = l + (L_DARK - l) * t_dark
            # slight hue shift for darker stops (warmth)
            new_h = h + (0.014 * (stop - 500) / 400)
        new_s = min(1.0, max(s_min, s * s_mult))
        r_n, g_n, b_n = colorsys.hls_to_rgb(new_h, new_l, new_s)
        palette[stop] = rgb_to_hex((round(r_n * 255), round(g_n * 255), round(b_n * 255)))
    return palette

# Blend weights: fraction of the way from white (#FFFFFF) toward base (stop 900).
# Derived by reverse-engineering a perceptual neutral scale where base is the
# darkest anchor (stop 900) and stop 50 is pure white.
# Formula per stop:  color = white + (base − white) × t
#   t=0.000 → white, t=1.000 → base
_NEUTRAL_T = {
    50:  0.000,
    100: 0.032,
    200: 0.078,
    300: 0.308,
    400: 0.392,
    500: 0.589,
    600: 0.806,
    700: 0.924,
    800: 0.967,
    900: 1.000,
}

def generate_neutral_palette(base_hex: str) -> dict:
    """Generate a neutral ramp where base_hex is stop 900 (darkest).
    Stop 50 is white; intermediate stops blend linearly in RGB space
    using perceptually-tuned t-weights (_NEUTRAL_T)."""
    br, bg, bb = hex_to_rgb(base_hex)
    palette = {}
    for stop, t in _NEUTRAL_T.items():
        r = round(255 + (br - 255) * t)
        g = round(255 + (bg - 255) * t)
        b = round(255 + (bb - 255) * t)
        palette[stop] = rgb_to_hex((r, g, b))
    return palette

def invert_palette(light: dict) -> dict:
    keys = sorted(light.keys())
    return dict(zip(keys, reversed([light[k] for k in keys])))

def relative_luminance(hex_str: str) -> float:
    """WCAG 2.1 relative luminance of a hex color."""
    def linearize(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = hex_to_rgb(hex_str)
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)

def contrast_ratio(hex_a: str, hex_b: str) -> float:
    la = relative_luminance(hex_a)
    lb = relative_luminance(hex_b)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)

def contrast_fg(hex_str: str, dark_fg: str = "#1A1A1A") -> str:
    """Return white or dark_fg, whichever has higher contrast against hex_str."""
    return "#FFFFFF" if contrast_ratio(hex_str, "#FFFFFF") >= contrast_ratio(hex_str, dark_fg) else dark_fg

def write_contrast_fg_statics(lines, tpl):
    """Emit --white-fg and --black-fg static tokens from contrast_fg in yml."""
    section(lines, "Contrast FG Statics")
    cfg = tpl.get('contrast_fg', {})
    lines.append(f"  --white-fg:  {cfg.get('white', '#FFFFFF')};")
    lines.append(f"  --black-fg:  {cfg.get('black', '#000000')};")

def write_contrast_fg_block(lines, name, ramp):
    """Emit --base-{name}-{stop}-fg for every stop in ramp."""
    section(lines, f"{name.capitalize()} Contrast FG")
    for stop in sorted(ramp.keys()):
        raw = contrast_fg(ramp[stop])
        fg = "var(--white-fg)" if raw == "#FFFFFF" else "var(--black-fg)"
        lines.append(f"  --base-{name}-{stop}-fg:  {fg};")

# ─── YAML REFERENCE RESOLVER ─────────────────────────────────────────────────

def ref_to_var(ref: str) -> str:
    """Convert YAML semantic reference to CSS var().
    Examples:
      'base-neutral-50'  → 'var(--base-neutral-50)'
      'border-primary'   → 'var(--border-primary)'
      'border-secondary' → 'var(--border-secondary)'
    """
    return f"var(--{ref})"

# ─── CSS WRITERS ─────────────────────────────────────────────────────────────

def section(lines, title):
    pad = max(1, 48 - len(title))
    lines.append(f"\n\n  /* ── {title} {'─' * pad} */")

def write_base_palette_block(lines, name, ramp):
    section(lines, name.capitalize())
    keys = sorted(ramp.keys(), reverse=(name == 'neutral'))
    for stop in keys:
        lines.append(f"  --base-{name}-{stop}:  {ramp[stop]};")

def write_surfaces_borders(lines, sem):
    section(lines, "Surfaces & Borders")
    surf = sem.get('surface', {})
    for key, ref in surf.items():
        lines.append(f"  --{key}:  {ref_to_var(ref)};")
    bord = sem.get('border', {})
    for key, ref in bord.items():
        lines.append(f"  --border-{key}:  {ref_to_var(ref)};")

def write_text(lines, sem):
    section(lines, "Text")
    for key, ref in sem.get('text', {}).items():
        lines.append(f"  --text-color-{key}:  {ref_to_var(ref)};")

def write_brand_grades(lines, sem):
    for brand, stops in sem.get('brand', {}).items():
        section(lines, f"Brand Semantic Grades — {brand.capitalize()}")
        for grade in ('light', 'soft', 'base', 'bold', 'deep'):
            stop = stops[grade]
            lines.append(f"  --{brand}-{grade}: var(--base-{brand}-{stop});")
            lines.append(f"  --{brand}-{grade}-fg: var(--base-{brand}-{stop}-fg);")

def write_neutral_grades(lines, sem):
    section(lines, "Neutral Grades")
    stops = sem.get('neutral', {})
    for grade in ('light', 'soft', 'base', 'bold', 'deep'):
        stop = stops[grade]
        lines.append(f"  --neutral-{grade}: var(--base-neutral-{stop});")
        lines.append(f"  --neutral-{grade}-fg: var(--base-neutral-{stop}-fg);")

def write_state_grades(lines, sem):
    for state, stops in sem.get('state', {}).items():
        section(lines, f"State — {state.capitalize()}")
        for grade in ('light', 'soft', 'base', 'bold', 'deep'):
            stop = stops[grade]
            lines.append(f"  --{state}-{grade}: var(--base-{state}-{stop});")
            lines.append(f"  --{state}-{grade}-fg: var(--base-{state}-{stop}-fg);")

def write_shadcn(lines, sem):
    section(lines, "shadcn/ui Semantic Aliases")
    for key, ref in sem.get('shadcn', {}).items():
        lines.append(f"  --{key}: {ref_to_var(ref)};")

def write_sidebar(lines, sem):
    section(lines, "Sidebar")
    sidebar = sem.get('sidebar', {})
    css_key_map = {
        'bg':         'sidebar',
        'foreground': 'sidebar-foreground',
        'primary':    'sidebar-primary',
        'primary-fg': 'sidebar-primary-foreground',
        'accent':     'sidebar-accent',
        'accent-fg':  'sidebar-accent-foreground',
        'border':     'sidebar-border',
        'ring':       'sidebar-ring',
    }
    for yaml_key, css_key in css_key_map.items():
        if yaml_key in sidebar:
            lines.append(f"  --{css_key}: {ref_to_var(sidebar[yaml_key])};")

def write_chart(lines, sem):
    section(lines, "Chart Series")
    for num, ref in sem.get('chart', {}).items():
        lines.append(f"  --chart-{num}: {ref_to_var(ref)};")

def write_static_tokens(lines, tpl, fonts_override=None):
    typo = tpl['typography']

    section(lines, "Spacing")
    for k, v in tpl['spacing'].items():
        lines.append(f"  --spacing-{k}:   {v};")

    section(lines, "Border Radius")
    # shadcn base radius (= md). Default 8px — see template/variable.yml border_radius.
    lines.append(f"  --radius:  {tpl['border_radius'].get('md', '8px')};")
    for k, v in tpl['border_radius'].items():
        lines.append(f"  --radius-{k}:  {v};")

    section(lines, "Shadows")
    shadow = tpl['shadow']
    color_light = shadow['color_light']
    lines.append(f"  --shadow-color: {color_light};")
    skip = {'color_light', 'color_dark', 'inset'}
    for key, val in shadow.items():
        if key in skip:
            continue
        lines.append(f"  --shadow-{key}:  {val.replace('{color}', 'var(--shadow-color)')};")
    for key, val in shadow.get('inset', {}).items():
        lines.append(f"  --inset-shadow-{key}:  {val.replace('{color}', 'var(--shadow-color)')};")

    section(lines, "Typography")
    font_family = typo['font_family']
    # Resolve main fonts — override from --fonts arg if provided
    main_fonts = dict(font_family.get('main', {}))
    if fonts_override:
        for k, v in fonts_override.items():
            # strip stack keys, only accept main-* or plain sans/serif/mono as main
            if k.startswith('main-'):
                main_fonts[k[5:]] = v
            elif k in ('sans', 'serif', 'mono') and not v.startswith('var('):
                main_fonts[k] = v
    for k, v in main_fonts.items():
        lines.append(f"  --font-main-{k}:  '{v}';")
    lines.append("")
    # Write stack tokens (use var(--font-main-*) references from yml)
    stacks = font_family.get('stacks', {})
    for k, v in stacks.items():
        lines.append(f"  --font-{k}:  {v};")
    lines.append("")
    for k, v in typo['font_weight'].items():
        lines.append(f"  --font-weight-{k}:  {v};")
    lines.append("")
    for k, v in typo['font_size'].items():
        lines.append(f"  --text-{k}:  {v};")
    lines.append("")
    for k, v in typo['line_height'].items():
        lines.append(f"  --leading-{k}:    {v};")
    lines.append("")
    for k, v in typo['letter_spacing'].items():
        lines.append(f"  --tracking-{k}: {v};")

def write_dark_shadow(lines, tpl):
    section(lines, "Shadow (dark)")
    lines.append(f"  --shadow-color: {tpl['shadow']['color_dark']};")

# ─── MAIN ────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--colors",   type=str)
    p.add_argument("--fonts",    type=str)
    p.add_argument("--output",   type=str, default=DEFAULT_OUT)
    p.add_argument("--template", type=str, default=str(DEFAULT_TPL))
    return p.parse_args()

def main():
    args = parse_args()

    tpl_path = Path(args.template)
    if not tpl_path.exists():
        print(f"Error: template not found: {tpl_path}", file=sys.stderr)
        sys.exit(1)

    with open(tpl_path) as f:
        tpl = yaml.safe_load(f)

    fonts_override = json.loads(args.fonts) if args.fonts else None
    sem_light = tpl['semantic']['light']
    sem_dark  = tpl['semantic']['dark']

    # ── Brand palettes (5 brand colors from --colors or base_palette) ──────
    brand_order = ['primary', 'secondary', 'tertiary', 'quaternary', 'quinary']
    colors_input = json.loads(args.colors) if args.colors else {}

    if colors_input:
        brand_palettes = {}
        brand_keys = [k for k in colors_input if k in brand_order]
        for i, name in enumerate(brand_order):
            src_key = brand_keys[i] if i < len(brand_keys) else brand_keys[-1]
            brand_palettes[name] = generate_palette(colors_input[src_key], is_brand=True)
    else:
        raw = tpl.get('base_palette', {})
        brand_palettes = {
            name: {int(k): v for k, v in raw[name].items()}
            for name in brand_order if name in raw
        }

    # Neutral + state palettes: from --colors if provided, else from base_palette in YAML
    raw = tpl.get('base_palette', {})

    if 'neutral' in colors_input:
        neutral_light = generate_neutral_palette(colors_input['neutral'])
    else:
        neutral_light = {int(k): v for k, v in raw['neutral'].items()} if 'neutral' in raw else {}

    state_palettes = {}
    for name in STATE_NAMES:
        if name in colors_input:
            state_palettes[name] = generate_palette(colors_input[name])
        elif name in raw:
            state_palettes[name] = {int(k): v for k, v in raw[name].items()}

    # ── :root ───────────────────────────────────────────────────────────────
    lines = []
    lines.append("/* ============================================================")
    lines.append("   Design System — CSS Custom Properties")
    lines.append("   Platform: Web | Mode: auto (light/dark)")
    lines.append("   ============================================================ */")
    lines.append("")
    lines.append(":root {")

    # Base palettes
    section(lines, "Base Palette")
    write_base_palette_block(lines, 'neutral', neutral_light)
    for name in brand_order:
        write_base_palette_block(lines, name, brand_palettes[name])
    for state, ramp in state_palettes.items():
        write_base_palette_block(lines, state, ramp)

    # Contrast FG tokens
    write_contrast_fg_statics(lines, tpl)
    write_contrast_fg_block(lines, 'neutral', neutral_light)
    for name in brand_order:
        write_contrast_fg_block(lines, name, brand_palettes[name])
    for state, ramp in state_palettes.items():
        write_contrast_fg_block(lines, state, ramp)

    # Semantic light
    write_surfaces_borders(lines, sem_light)
    write_text(lines, sem_light)
    write_brand_grades(lines, sem_light)
    write_neutral_grades(lines, sem_light)
    write_state_grades(lines, sem_light)
    write_shadcn(lines, sem_light)
    write_sidebar(lines, sem_light)
    write_chart(lines, sem_light)

    # Static tokens
    write_static_tokens(lines, tpl, fonts_override)

    lines.append("}")

    # ── .dark ───────────────────────────────────────────────────────────────
    lines.append("")
    lines.append("")
    lines.append("/* ──────────────────────────────────────────────────────────")
    lines.append("   Dark Mode Overrides")
    lines.append("   Trigger: <html class=\"dark\">")
    lines.append("────────────────────────────────────────────────────────── */")
    lines.append(".dark {")

    # Dark palette — inverted from light
    section(lines, "Dark Palette Overrides")
    neutral_dark = invert_palette(neutral_light)
    brand_dark = {name: invert_palette(brand_palettes[name]) for name in brand_order}
    state_dark = {state: invert_palette(ramp) for state, ramp in state_palettes.items()}

    write_base_palette_block(lines, 'neutral', neutral_dark)
    for name in brand_order:
        write_base_palette_block(lines, name, brand_dark[name])
    for state, ramp in state_dark.items():
        write_base_palette_block(lines, state, ramp)

    # Contrast FG tokens (dark — recalculated from inverted palette)
    write_contrast_fg_block(lines, 'neutral', neutral_dark)
    for name in brand_order:
        write_contrast_fg_block(lines, name, brand_dark[name])
    for state, ramp in state_dark.items():
        write_contrast_fg_block(lines, state, ramp)

    # Dark semantic tokens — surfaces/text/shadcn/sidebar/chart use sem_dark overrides,
    # but brand/neutral/state grades use sem_light indices (base colors already inverted above)
    write_surfaces_borders(lines, sem_dark)
    write_text(lines, sem_dark)
    write_brand_grades(lines, sem_dark)
    # Primary base only: original brand color brightened slightly for dark-bg legibility
    primary_original = brand_palettes['primary'][500]
    lines.append(f"  --primary-base: {adjust_for_dark_base(primary_original)};")
    write_neutral_grades(lines, sem_light)
    write_state_grades(lines, sem_light)
    write_shadcn(lines, sem_dark)
    write_sidebar(lines, sem_dark)
    write_chart(lines, sem_dark)
    write_dark_shadow(lines, tpl)

    lines.append("}")
    lines.append("")

    css = "\n".join(lines)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        f.write(css)

    print(f"✓ Written to {out}")

if __name__ == "__main__":
    main()
