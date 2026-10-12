#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate tailwind.css from tailwind.yml template.

Usage:
    python css.py <output_path>
    python css.py design/web/mytheme/tailwind.css
"""

import sys
from pathlib import Path

TEMPLATE = Path(__file__).parent.parent / "template" / "tailwind.yml"

# Section header comments
SECTION_HEADERS = {
    "font_family":     "/* ─── FONT FAMILY — font-sans / font-serif / font-mono ──────────────────── */",
    "font_size":       "/* ─── FONT SIZE — text-display / text-h1…h6 / text-body-lg…sm / text-label-lg…sm */",
    "font_weight":     "/* ─── FONT WEIGHT — font-regular / font-medium / font-semibold / font-bold ─ */",
    "line_height":     "/* ─── LINE HEIGHT — leading-tight / leading-normal / leading-loose ────────── */",
    "letter_spacing":  "/* ─── LETTER SPACING — tracking-tight / tracking-normal / tracking-wide ───── */",
    "colors":          "/* ─── COLOR — bg-* / text-* / border-* / ring-* ────────────────────────── */",
    "spacing":         "/* ─── SPACING — p-* / m-* / gap-* / w-* / h-* ───────────────────────────── */",
    "border_radius":   "/* ─── BORDER RADIUS — rounded-* ─────────────────────────────────────────── */",
    "shadow":          "/* ─── SHADOW — shadow-* ──────────────────────────────────────────────────── */",
    "animation":       "/* ─── ANIMATION — animate-* ─────────────────────────────────────────────── */",
}

# Color group comment labels (match tailwind.yml comment lines)
COLOR_GROUPS = {
    "shadcn semantic": [
        "background", "foreground", "card", "card-foreground", "popover", "popover-foreground",
        "primary", "primary-foreground", "secondary", "secondary-foreground",
        "tertiary", "tertiary-foreground", "quaternary", "quaternary-foreground",
        "quinary", "quinary-foreground", "muted", "muted-foreground",
        "accent", "accent-foreground", "destructive", "destructive-foreground",
        "input", "ring",
    ],
    "surface": ["background-primary", "background-secondary"],
    "border": ["border-primary", "border-secondary"],
    "typography": ["font-primary", "font-secondary", "font-placeholder", "font-disabled", "font-on-accent"],
    "brand semantic — primary":    ["primary-light", "primary-soft", "primary-base", "primary-bold", "primary-deep"],
    "brand semantic — secondary":  ["secondary-light", "secondary-soft", "secondary-base", "secondary-bold", "secondary-deep"],
    "brand semantic — tertiary":   ["tertiary-light", "tertiary-soft", "tertiary-base", "tertiary-bold", "tertiary-deep"],
    "brand semantic — quaternary": ["quaternary-light", "quaternary-soft", "quaternary-base", "quaternary-bold", "quaternary-deep"],
    "brand semantic — quinary":    ["quinary-light", "quinary-soft", "quinary-base", "quinary-bold", "quinary-deep"],
    "neutral": ["neutral", "neutral-light", "neutral-soft", "neutral-base", "neutral-bold", "neutral-deep"],
    "state semantic": [
        "success", "success-light", "success-soft", "success-base", "success-bold", "success-deep",
        "error", "error-light", "error-soft", "error-base", "error-bold", "error-deep",
        "warning", "warning-light", "warning-soft", "warning-base", "warning-bold", "warning-deep",
        "info", "info-light", "info-soft", "info-base", "info-bold", "info-deep",
    ],
    "chart": ["chart-1", "chart-2", "chart-3", "chart-4", "chart-5"],
}

SIDEBAR_KEYS = ["sidebar", "sidebar-foreground", "sidebar-primary", "sidebar-primary-foreground",
                "sidebar-accent", "sidebar-accent-foreground", "sidebar-border", "sidebar-ring"]

FOOTER_COMMENTS = """\
  /* ─── BLUR — blur-* ──────────────────────────────────────────────────────── */
  /* not defined in design tokens — using Tailwind defaults */

  /* ─── OPACITY — opacity-* ────────────────────────────────────────────────── */
  /* not defined in design tokens — using Tailwind defaults */

  /* ─── Z-INDEX — z-* ──────────────────────────────────────────────────────── */
  /* not defined in design tokens — using Tailwind defaults */

  /* ─── BREAKPOINT — sm: / md: / lg: / xl: / 2xl: ─────────────────────────── */
  /* not defined in design tokens — using Tailwind defaults */

  /* ─── TRANSITION DURATION — duration-* ──────────────────────────────────── */
  /* not defined in design tokens — using Tailwind defaults */

  /* ─── TRANSITION EASING — ease-* ────────────────────────────────────────── */
  /* not defined in design tokens — using Tailwind defaults */"""


def _load_yaml(path: Path) -> dict:
    """Minimal YAML loader — no external deps, handles the tailwind.yml structure."""
    try:
        import yaml  # type: ignore
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except ImportError:
        pass
    # Fallback: manual parse for the simple key: value structure used in tailwind.yml
    return _parse_yaml_simple(path)


def _parse_yaml_simple(path: Path) -> dict:
    """Parse tailwind.yml without PyYAML — handles comments, nesting, and quoted strings."""
    result = {}
    current_section = None
    current_subsection = None
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        stripped = line.rstrip()
        if not stripped or stripped.lstrip().startswith("#"):
            # Preserve comment for color group detection
            if current_section == "colors" and stripped.lstrip().startswith("#"):
                comment_text = stripped.lstrip().lstrip("#").strip()
                if comment_text:
                    result.setdefault("colors", {})
                    result["colors"].setdefault("__comments__", [])
                    # store (comment_label, position) — position is next key inserted
            continue

        indent = len(line) - len(line.lstrip())

        if ":" not in stripped:
            continue

        colon_pos = stripped.index(":")
        key = stripped[:colon_pos].strip()
        value = stripped[colon_pos + 1:].strip().strip('"').strip("'")

        if indent == 0:
            current_section = key
            current_subsection = None
            if key not in result:
                result[key] = {}
        elif indent == 2:
            if current_section and isinstance(result.get(current_section), dict):
                if value == "":
                    # nested section (e.g. inset:, animation name:)
                    current_subsection = key
                    result[current_section][key] = {}
                else:
                    current_subsection = None
                    result[current_section][key] = value
        elif indent == 4:
            if current_section and current_subsection:
                if isinstance(result[current_section].get(current_subsection), dict):
                    result[current_section][current_subsection][key] = value
        elif indent == 6:
            # keyframes inside animation
            if current_section == "animation" and current_subsection:
                anim = result["animation"].get(current_subsection, {})
                kf = anim.get("keyframes", {})
                kf[key] = value
                anim["keyframes"] = kf
                result["animation"][current_subsection] = anim

    return result


def _css_prop(css_var: str, value: str, indent: int = 2) -> str:
    pad = " " * indent
    return f"{pad}{css_var}: {value};"


def generate(data: dict) -> str:
    lines = [
        "/* TAILWIND v4 THEME CONFIG — Maps design tokens → Tailwind utility classes. Base: 1rem = 16px */",
        "",
        "@theme inline {",
        "",
    ]

    # ── Font Family ──
    lines.append(f"  {SECTION_HEADERS['font_family']}")
    for key, val in data.get("font_family", {}).items():
        lines.append(_css_prop(f"--font-{key}", val))
    lines.append("")

    # ── Font Size ──
    lines.append(f"  {SECTION_HEADERS['font_size']}")
    for key, val in data.get("font_size", {}).items():
        lines.append(_css_prop(f"--text-{key}", val))
    lines.append("")

    # ── Font Weight ──
    lines.append(f"  {SECTION_HEADERS['font_weight']}")
    for key, val in data.get("font_weight", {}).items():
        lines.append(_css_prop(f"--font-weight-{key}", val))
    lines.append("")

    # ── Line Height ──
    lines.append(f"  {SECTION_HEADERS['line_height']}")
    for key, val in data.get("line_height", {}).items():
        lines.append(_css_prop(f"--leading-{key}", val))
    lines.append("")

    # ── Letter Spacing ──
    lines.append(f"  {SECTION_HEADERS['letter_spacing']}")
    for key, val in data.get("letter_spacing", {}).items():
        lines.append(_css_prop(f"--tracking-{key}", val))
    lines.append("")

    # ── Colors ──
    lines.append(f"  {SECTION_HEADERS['colors']}")
    colors = data.get("colors", {})

    # Emit grouped, preserving group order from COLOR_GROUPS
    emitted = set()
    for group_label, group_keys in COLOR_GROUPS.items():
        group_lines = []
        for k in group_keys:
            if k in colors and k not in emitted:
                group_lines.append(_css_prop(f"--color-{k}", colors[k]))
                emitted.add(k)
        if group_lines:
            lines.append(f"  /* {group_label} */")
            lines.extend(group_lines)

    # Sidebar (tail of colors section)
    sidebar_lines = []
    for k in SIDEBAR_KEYS:
        if k in colors and k not in emitted:
            sidebar_lines.append(_css_prop(f"--color-{k}", colors[k]))
            emitted.add(k)
    if sidebar_lines:
        lines.append("  /* sidebar */")
        lines.extend(sidebar_lines)

    # Any remaining keys not covered by groups
    remaining = [(k, v) for k, v in colors.items() if k not in emitted]
    if remaining:
        lines.append("  /* other */")
        for k, v in remaining:
            lines.append(_css_prop(f"--color-{k}", v))

    lines.append("")

    # ── Spacing ──
    lines.append(f"  {SECTION_HEADERS['spacing']}")
    for key, val in data.get("spacing", {}).items():
        # variable.css uses --spacing-{key}; tailwind.css maps --spacing-{key} → var(--spacing-{key})
        # The yml value already has the correct var() reference
        lines.append(_css_prop(f"--spacing-{key}", val))
    lines.append("")

    # ── Border Radius ──
    lines.append(f"  {SECTION_HEADERS['border_radius']}")
    for key, val in data.get("border_radius", {}).items():
        lines.append(_css_prop(f"--radius-{key}", val))
    lines.append("")

    # ── Shadow ──
    lines.append(f"  {SECTION_HEADERS['shadow']}")
    shadow = data.get("shadow", {})
    for key, val in shadow.items():
        if key == "inset":
            for ikey, ival in val.items():
                lines.append(_css_prop(f"--inset-shadow-{ikey}", ival))
        else:
            lines.append(_css_prop(f"--shadow-{key}", val))
    lines.append("")

    # ── Animation ──
    lines.append(f"  {SECTION_HEADERS['animation']}")
    animations = data.get("animation", {})
    # First pass: --animate-* declarations
    for name, anim in animations.items():
        value = anim.get("value", "") if isinstance(anim, dict) else anim
        lines.append(_css_prop(f"--animate-{name}", value))
    lines.append("")
    # Second pass: @keyframes blocks
    for name, anim in animations.items():
        if not isinstance(anim, dict):
            continue
        kf = anim.get("keyframes", {})
        if not kf:
            continue
        lines.append(f"  @keyframes {name} {{")
        for step, props in kf.items():
            if isinstance(props, dict):
                prop_str = "; ".join(f"{k}: {v}" for k, v in props.items())
                lines.append(f"    {step} {{ {prop_str}; }}")
            else:
                lines.append(f"    {step} {{ {props}; }}")
        lines.append("  }")
    lines.append("")

    # Footer comments
    lines.append(FOOTER_COMMENTS)
    lines.append("")
    lines.append("}")
    lines.append("")

    return "\n".join(lines)


def build_tailwind_css(output_path: str) -> None:
    data = _load_yaml(TEMPLATE)
    css = generate(data)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(css, encoding="utf-8")
    print(f"Written: {out}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python css.py <output_path>")
        sys.exit(1)
    build_tailwind_css(sys.argv[1])
