#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Design System Builder Search - BM25 search engine for UI/UX style guides
Usage: python search.py "<query>" [--domain <domain>] [--stack <stack>] [--max-results 3]
       python search.py "<query>" --design-system [-p "Project Name"]
       python search.py "<query>" --design-system --persist [-p "Project Name"] [--platform web] [--theme tactical]

Domains: style, prompt, color, chart, landing, product, ux, typography, google-fonts
Stacks: react, nextjs, vue, svelte, astro, swiftui, react-native, flutter, nuxtjs, nuxt-ui, html-tailwind, shadcn, jetpack-compose, threejs

File output (--persist):
  Writes 3 files to design/<platform>/<theme>/:
    variable.yml  — base palette + semantic token mappings
    tailwind.yml  — Tailwind v4 @theme mapping (static, references CSS vars)
    DESIGN.md     — human-readable style reference
"""

import argparse
import sys
import io
from core import CSV_CONFIG, AVAILABLE_STACKS, MAX_RESULTS, search, search_stack
from design_system import generate_design_system, persist_design_system

# Force UTF-8 for stdout/stderr to handle emojis on Windows (cp1252 default)
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def format_output(result):
    """Format results for Claude consumption (token-optimized)"""
    if "error" in result:
        return f"Error: {result['error']}"

    output = []
    if result.get("stack"):
        output.append(f"## UI Pro Max Stack Guidelines")
        output.append(f"**Stack:** {result['stack']} | **Query:** {result['query']}")
    else:
        output.append(f"## UI Pro Max Search Results")
        output.append(f"**Domain:** {result['domain']} | **Query:** {result['query']}")
    output.append(f"**Source:** {result['file']} | **Found:** {result['count']} results\n")

    for i, row in enumerate(result['results'], 1):
        output.append(f"### Result {i}")
        for key, value in row.items():
            value_str = str(value)
            if len(value_str) > 300:
                value_str = value_str[:300] + "..."
            output.append(f"- **{key}:** {value_str}")
        output.append("")

    return "\n".join(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UI Pro Max Search")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--domain", "-d", choices=list(CSV_CONFIG.keys()), help="Search domain")
    parser.add_argument("--stack", "-s", choices=AVAILABLE_STACKS, help=f"Stack-specific search. Available: {', '.join(AVAILABLE_STACKS)}")
    parser.add_argument("--max-results", "-n", type=int, default=MAX_RESULTS, help="Max results (default: 3)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    # Design system generation
    parser.add_argument("--design-system", "-ds", action="store_true", help="Generate complete design system recommendation")
    parser.add_argument("--project-name", "-p", type=str, default=None, help="Project name for design system output")
    parser.add_argument("--format", "-f", choices=["ascii", "markdown"], default="ascii", help="Output format for design system")
    # File output
    parser.add_argument("--persist", action="store_true",
                        help="Write variable.yml + tailwind.yml + DESIGN.md to design/<platform>/<theme>/")
    parser.add_argument("--platform", type=str, default="web",
                        help="Target platform folder (default: web)")
    parser.add_argument("--theme", type=str, default=None,
                        help="Theme folder name (default: slugified project name)")
    parser.add_argument("--output-dir", "-o", type=str, default=None,
                        help="Root output directory (default: current directory)")

    args = parser.parse_args()

    # Design system takes priority
    if args.design_system:
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
            import os
            base = args.output_dir or os.getcwd()
            theme_name = args.theme or (args.project_name or args.query).lower().replace(' ', '-')
            dest = f"{base}/design/{args.platform}/{theme_name}"
            print("\n" + "=" * 60)
            print(f"✅ Files written to: {dest}/")
            for fname in ["variable.yml", "tailwind.yml", "DESIGN.md"]:
                print(f"   ✓ {fname}")
            print("=" * 60)
    # Stack search
    elif args.stack:
        result = search_stack(args.query, args.stack, args.max_results)
        if args.json:
            import json
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(format_output(result))
    # Domain search
    else:
        result = search(args.query, args.domain, args.max_results)
        if args.json:
            import json
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(format_output(result))
