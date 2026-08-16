"""
svg_generator.py

Generates lightweight, dependency-free SVGs:
  - technology-ecosystem.svg : tree diagram of detected tech by category
  - language-distribution.svg: horizontal bar chart of language bytes
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
  .bar      { fill: url(#blueGradient); }
  @media (prefers-color-scheme: dark) {
    .bg       { fill: #0d1117; stroke: #30363d; stroke-width: 1; }
    .fg       { fill: #f0f6fc; }
    .muted    { fill: #8b949e; }
    .line     { stroke: #30363d; }
    .node     { fill: #161b22; stroke: #30363d; }
    .node-txt { fill: #58a6ff; font-weight: 600; }
    .accent   { fill: #58a6ff; }
    .bar-bg   { fill: #21262d; }
    .bar      { fill: url(#darkBlueGradient); }
  }
  text { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif; }
</style>
<defs>
  <linearGradient id="blueGradient" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="#0969da" />
    <stop offset="100%" stop-color="#2da44e" />
  </linearGradient>
  <linearGradient id="darkBlueGradient" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="#58a6ff" />
    <stop offset="100%" stop-color="#39d0d8" />
  </linearGradient>
</defs>
""".strip()

CATEGORY_TITLES = {
    "language": "Languages",
    "frontend": "Frontend",
    "backend": "Backend",
    "database": "Databases",
    "devops": "DevOps",
    "cloud": "Cloud",
    "ai_data": "AI / Data",
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
    row_h = 32
    label_w = 140
    bar_max_w = 400
    width = label_w + bar_max_w + 90
    height = 40 + row_h * len(langs) + 20

    max_pct = max((l["percentage"] for l in langs), default=1) or 1

    parts = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Repository language distribution">']
    parts.append(STYLE_BLOCK)
    parts.append(f'<rect class="bg" x="1" y="1" width="{width-2}" height="{height-2}" rx="12"/>')
    parts.append(f'<text x="20" y="28" class="fg" font-size="14" font-weight="700">Repository Language Distribution</text>')

    for i, lang in enumerate(langs):
        y = 48 + i * row_h
        bar_w = max(6, bar_max_w * (lang["percentage"] / 100))
        parts.append(f'<text x="20" y="{y+14}" class="fg" font-size="12" font-weight="500">{lang["language"]}</text>')
        parts.append(f'<rect class="bar-bg" x="{label_w}" y="{y}" width="{bar_max_w}" height="18" rx="6"/>')
        parts.append(f'<rect class="bar" x="{label_w}" y="{y}" width="{bar_w:.1f}" height="18" rx="6"/>')
        parts.append(f'<text x="{label_w + bar_max_w + 12}" y="{y+14}" class="muted" font-size="11.5" font-weight="600">{lang["percentage"]}%</text>')

    parts.append("</svg>")
    return "\n".join(parts)
