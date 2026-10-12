#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
brand_guideline.py — Select the best Google Font pairing and deploy brand-guideline.html.

Usage:
    python brand_guideline.py "<query>" [--top 3]
    python brand_guideline.py "<query>" --deploy-html <dest_dir>

--deploy-html copies the template brand-guideline.html into <dest_dir> and
replaces {{FONT_FAMILY}} with the resolved Google Fonts stylesheet URL.
"""

import csv
import json
import re
import sys
from math import log
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent / "data"
TEMPLATE_DIR = Path(__file__).parent.parent / "template"
TYPOGRAPHY_CSV = DATA_DIR / "typography.csv"
HTML_TEMPLATE = TEMPLATE_DIR / "brand-guideline.html"
MAX_RESULTS = 3


# ── BM25 ─────────────────────────────────────────────────────────────────────

SEARCH_COLS = ["Font Pairing Name", "Category", "Heading Font", "Body Font",
               "Mood/Style Keywords", "Best For", "Notes"]

def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())

def load_rows() -> list[dict]:
    with open(TYPOGRAPHY_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def build_index(rows: list[dict]) -> tuple[dict, dict, list[list[str]]]:
    doc_tokens: list[list[str]] = []
    df: dict[str, int] = defaultdict(int)
    for row in rows:
        text = " ".join(row.get(c, "") for c in SEARCH_COLS)
        tokens = tokenize(text)
        doc_tokens.append(tokens)
        for t in set(tokens):
            df[t] += 1
    tf: dict[int, dict[str, int]] = {}
    for i, tokens in enumerate(doc_tokens):
        counts: dict[str, int] = defaultdict(int)
        for t in tokens:
            counts[t] += 1
        tf[i] = dict(counts)
    return tf, df, doc_tokens

def bm25_score(query_tokens: list[str], doc_idx: int,
               tf: dict, df: dict, doc_tokens: list[list[str]],
               n_docs: int, k1: float = 1.5, b: float = 0.75) -> float:
    dl = len(doc_tokens[doc_idx])
    avg_dl = sum(len(d) for d in doc_tokens) / n_docs
    score = 0.0
    for t in query_tokens:
        if t not in df:
            continue
        idf = log((n_docs - df[t] + 0.5) / (df[t] + 0.5) + 1)
        f = tf[doc_idx].get(t, 0)
        score += idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * dl / avg_dl))
    return score

def search(query: str, top_n: int = MAX_RESULTS) -> list[dict]:
    rows = load_rows()
    if not rows:
        return []
    tf, df, doc_tokens = build_index(rows)
    q_tokens = tokenize(query)
    scores = [(bm25_score(q_tokens, i, tf, df, doc_tokens, len(rows)), i)
              for i in range(len(rows))]
    scores.sort(reverse=True)
    results = []
    for score, idx in scores[:top_n]:
        row = rows[idx]
        results.append({
            "rank": len(results) + 1,
            "score": round(score, 4),
            "pairing_name": row.get("Font Pairing Name", ""),
            "category": row.get("Category", ""),
            "heading_font": row.get("Heading Font", ""),
            "body_font": row.get("Body Font", ""),
            "mood_keywords": row.get("Mood/Style Keywords", ""),
            "best_for": row.get("Best For", ""),
            "css_import": row.get("CSS Import", ""),
            "tailwind_config": row.get("Tailwind Config", ""),
            "google_fonts_url": row.get("Google Fonts URL", ""),
            "notes": row.get("Notes", ""),
        })
    return results


# ── variable.css font patch ───────────────────────────────────────────────────

def patch_variable_css(css_path: str, pairing: dict) -> str:
    """
    Read an existing variable.css and replace --font-sans / --font-serif /
    --font-mono values with the selected Google Font pairing.

    Returns the patched CSS string (does NOT write the file).
    """
    path = Path(css_path)
    css = path.read_text(encoding="utf-8")

    heading = pairing["heading_font"]
    body = pairing["body_font"]
    category = pairing.get("category", "").lower()

    # Determine which font var maps to heading vs body
    MONO_GOOGLE_FONT = "JetBrains Mono"
    MONO_WEIGHTS = "wght@400;500;700"

    if "mono" in category:
        font_sans = f"'{body}', ui-monospace, monospace"
        font_mono = f"'{heading}', ui-monospace, monospace"
        font_serif = "ui-serif, Georgia, Cambria, serif"
    elif "serif" in category and heading != body:
        font_sans = f"'{body}', system-ui, sans-serif"
        font_serif = f"'{heading}', ui-serif, Georgia, serif"
        font_mono = f"'{MONO_GOOGLE_FONT}', ui-monospace, monospace"
    else:
        font_sans = f"'{body}', system-ui, sans-serif"
        font_serif = f"'{heading}', ui-serif, Georgia, serif" if heading != body else "ui-serif, Georgia, Cambria, serif"
        font_mono = f"'{MONO_GOOGLE_FONT}', ui-monospace, monospace"

    def replace_var(css: str, var_name: str, new_value: str) -> str:
        pattern = rf"(--{var_name}\s*:\s*)([^;]+)(;)"
        return re.sub(pattern, rf"\g<1>{new_value}\3", css)

    css = replace_var(css, "font-sans", font_sans)
    css = replace_var(css, "font-serif", font_serif)
    css = replace_var(css, "font-mono", font_mono)

    # Inject Google Fonts @import at the top, including mono font in the URL
    import_line = pairing.get("css_import", "")
    if import_line:
        mono_family = f"family={MONO_GOOGLE_FONT.replace(' ', '+')}:{MONO_WEIGHTS}"
        # Append mono family to the Google Fonts URL before &display= or at the end
        if mono_family not in import_line:
            import_line = re.sub(
                r"(&display=[^'\")\s]+)",
                rf"&{mono_family}\1",
                import_line,
            )
            if mono_family not in import_line:
                # fallback: append before closing quote/paren
                import_line = re.sub(r"(['\"]?\))", rf"&{mono_family}\1", import_line, count=1)
        if import_line not in css:
            css = import_line + "\n\n" + css

    return css


# ── brand-guideline.html deploy ──────────────────────────────────────────────

def _extract_font_href(css_import: str) -> str:
    """Extract the bare URL from '@import url(...)' for use in <link href="">."""
    m = re.search(r"url\(['\"]?(https?://[^'\")\s]+)['\"]?\)", css_import)
    return m.group(1) if m else ""

def copy_brand_guideline(dest_dir: str, pairing: dict, design_system_name: str = "") -> str:
    """
    Copy template brand-guideline.html to <dest_dir>/brand-guideline.html,
    replacing {{FONT_FAMILY}} with the Google Fonts stylesheet href and
    {{ DESIGN_SYSTEM_NAME }} with the provided design system name.

    Returns the destination path as a string.
    """
    html = HTML_TEMPLATE.read_text(encoding="utf-8")
    font_href = _extract_font_href(pairing.get("css_import", ""))
    html = html.replace("{{FONT_FAMILY}}", font_href)
    name = design_system_name or Path(dest_dir).name
    html = html.replace("{{ DESIGN_SYSTEM_NAME }}", name)
    dest = Path(dest_dir) / "brand-guideline.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html, encoding="utf-8")
    return str(dest)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Find best Google Font pairing for a design brief")
    parser.add_argument("query", help="Design brief or style keywords")
    parser.add_argument("--top", type=int, default=MAX_RESULTS, help="Number of results")
    parser.add_argument("--patch-css", metavar="PATH",
                        help="Path to variable.css to patch with top result fonts")
    parser.add_argument("--deploy-html", metavar="DEST_DIR",
                        help="Copy brand-guideline.html template into DEST_DIR with fonts applied")
    parser.add_argument("--name", metavar="NAME",
                        help="Design system name to inject as DESIGN_SYSTEM_NAME in brand-guideline.html")
    parser.add_argument("--write", action="store_true",
                        help="Write patched CSS back to file (requires --patch-css)")
    args = parser.parse_args()

    results = search(args.query, args.top)
    top = results[0] if results else None
    output: dict = {"results": results}

    if args.patch_css and top:
        patched = patch_variable_css(args.patch_css, top)
        if args.write:
            Path(args.patch_css).write_text(patched, encoding="utf-8")
            output["css_patched"] = True
        else:
            output["css_preview"] = patched[:500] + "..."
        output["font_applied"] = top

    if args.deploy_html and top:
        dest = copy_brand_guideline(args.deploy_html, top, args.name or "")
        output["html_deployed"] = dest
        output.setdefault("font_applied", top)

    print(json.dumps(output if (args.patch_css or args.deploy_html) else results, indent=2))


if __name__ == "__main__":
    main()
