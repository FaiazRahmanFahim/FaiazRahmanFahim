"""
svg_generator.py

Generates lightweight, dependency-free SVGs:
  - technology-ecosystem.svg : tree diagram of detected tech by category
  - language-distribution.svg: modern multi-color distribution bar & cards
"""

from __future__ import annotations

STYLE_BLOCK = """
<style>
  .bg       { fill: #ffffff; stroke: #e1e4e8; stroke-width: 1; }
  .fg       { fill: #24292f; }
  .muted    { fill: #57606a; }
  .line     { stroke: #d0d7de; }
  .node     { fill: #f6f8fa; stroke: #d0d7de; }
  .node-txt { fill: #0969da; font-weight: 600; }
  .accent   { fill: #0969da; }
  .bar-bg   { fill: #eaeef2; }
  @media (prefers-color-scheme: dark) {
    .bg       { fill: #0d1117; stroke: #30363d; stroke-width: 1; }
    .fg       { fill: #f0f6fc; }
    .muted    { fill: #8b949e; }
    .line     { stroke: #30363d; }
    .node     { fill: #161b22; stroke: #30363d; }
    .node-txt { fill: #58a6ff; font-weight: 600; }
    .accent   { fill: #58a6ff; }
    .bar-bg   { fill: #21262d; }
  }
  text { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif; }
</style>
""".strip()

CATEGORY_TITLES = {
    "language": "Languages",
    "frontend": "Frontend",
    "backend": "Backend",
    "database": "Databases",
    "devops": "DevOps & Tools",
    "cloud": "Cloud",
    "ai_data": "AI / Data",
}

LANGUAGE_COLORS = {
    "JavaScript": "#F7DF1E",
    "HTML": "#E34F26",
    "TypeScript": "#3178C6",
    "C#": "#239120",
    "C++": "#00599C",
    "Python": "#3776AB",
    "CSS": "#1572B6",
}


def technology_ecosystem_svg(categories: dict[str, list[dict]], root_label: str) -> str:
    ordered_cats = [c for c in ("language", "frontend", "backend", "database", "devops", "cloud", "ai_data") if categories.get(c)]
    if not ordered_cats:
        ordered_cats = list(categories.keys())

    col_width = 190
    width = max(720, col_width * len(ordered_cats) + 40)
    height = 100 + 28 * max((len(categories.get(c, [])) for c in ordered_cats), default=1)

    root_x = width / 2
    parts = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Technology ecosystem diagram">']
    parts.append(STYLE_BLOCK)
    parts.append(f'<rect class="bg" x="1" y="1" width="{width-2}" height="{height-2}" rx="12"/>')
    parts.append(f'<rect class="node" x="{root_x-140}" y="16" width="280" height="32" rx="16" stroke-width="1.5"/>')
    parts.append(f'<text x="{root_x}" y="37" text-anchor="middle" class="node-txt" font-size="14">{root_label}</text>')

    for i, cat in enumerate(ordered_cats):
        cx = 40 + col_width * i + col_width / 2
        parts.append(f'<line class="line" x1="{root_x}" y1="48" x2="{cx}" y2="76" stroke-width="1.5"/>')
        parts.append(f'<rect class="node" x="{cx-70}" y="76" width="140" height="26" rx="8" stroke-width="1.2"/>')
        parts.append(f'<text x="{cx}" y="93" text-anchor="middle" class="fg" font-size="12" font-weight="600">{CATEGORY_TITLES.get(cat, cat.title())}</text>')

        for j, tech in enumerate(categories.get(cat, [])[:8]):
            ty = 120 + j * 26
            parts.append(f'<line class="line" x1="{cx}" y1="102" x2="{cx}" y2="{ty+6}" stroke-width="1" stroke-dasharray="3,3"/>')
            parts.append(f'<circle cx="{cx-50}" cy="{ty+4}" r="3" class="accent"/>')
            parts.append(f'<text x="{cx-40}" y="{ty+8}" class="muted" font-size="11.5" font-weight="500">{tech["technology"]}</text>')

    parts.append("</svg>")
    return "\n".join(parts)


def language_distribution_svg(language_distribution: list[dict], max_langs: int = 6) -> str:
    langs = language_distribution[:max_langs]
    if not langs:
        return ""

    width = 720
    bar_width = width - 48
    bar_height = 14
    bar_x = 24
    bar_y = 52

    # Calculate grid layout for language pills (2 columns)
    cols = 2
    row_count = (len(langs) + 1) // 2
    height = 90 + row_count * 38

    parts = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Language Distribution">']
    parts.append(STYLE_BLOCK)
    parts.append(f'<rect class="bg" x="1" y="1" width="{width-2}" height="{height-2}" rx="12"/>')
    parts.append(f'<text x="24" y="32" class="fg" font-size="14" font-weight="700">Repository Language Breakdown</text>')

    # 1. Continuous Multi-Color Top Progress Bar
    parts.append(f'<g clip-path="url(#bar-clip)">')
    parts.append(f'<clipPath id="bar-clip"><rect x="{bar_x}" y="{bar_y}" width="{bar_width}" height="{bar_height}" rx="7"/></clipPath>')
    
    current_x = bar_x
    for lang in langs:
        pct = lang["percentage"]
        segment_w = max(2.0, (pct / 100.0) * bar_width)
        color = LANGUAGE_COLORS.get(lang["language"], "#58A6FF")
        parts.append(f'<rect x="{current_x:.1f}" y="{bar_y}" width="{segment_w:.1f}" height="{bar_height}" fill="{color}"/>')
        current_x += segment_w
    parts.append('</g>')

    # 2. Detailed Language Cards / Badges Grid Below
    col_w = (width - 48 - 20) / 2
    start_y = bar_y + bar_height + 24

    for i, lang in enumerate(langs):
        col_idx = i % 2
        row_idx = i // 2
        
        card_x = bar_x + col_idx * (col_w + 20)
        card_y = start_y + row_idx * 38
        color = LANGUAGE_COLORS.get(lang["language"], "#58A6FF")
        pct = lang["percentage"]

        # Card container
        parts.append(f'<rect class="node" x="{card_x}" y="{card_y}" width="{col_w}" height="28" rx="6" stroke-width="1"/>')
        # Color dot indicator
        parts.append(f'<circle cx="{card_x + 14}" cy="{card_y + 14}" r="5" fill="{color}"/>')
        # Language name
        parts.append(f'<text x="{card_x + 28}" y="{card_y + 18}" class="fg" font-size="12" font-weight="600">{lang["language"]}</text>')
        # Percentage text
        parts.append(f'<text x="{card_x + col_w - 12}" y="{card_y + 18}" text-anchor="end" class="muted" font-size="11.5" font-weight="600">{pct}%</text>')

    parts.append("</svg>")
    return "\n".join(parts)
