"""
svg_generator.py

Generates lightweight, dependency-free SVGs:

  - technology-ecosystem.svg : tree diagram of detected tech by category
  - language-distribution.svg: horizontal bar chart of language bytes

Both use `prefers-color-scheme` media queries inside an embedded
<style> block so they automatically adapt to GitHub Dark/Light
without needing separate -dark/-light asset files or any JavaScript.
"""

from __future__ import annotations

STYLE_BLOCK = """
<style>
  .bg   { fill: #ffffff; }
  .fg   { fill: #1f2328; }
  .muted{ fill: #57606a; }
  .line { stroke: #d0d7de; }
  .node { fill: #f6f8fa; stroke: #d0d7de; }
  .accent { fill: #58A6FF; }
  .bar  { fill: #58A6FF; }
  @media (prefers-color-scheme: dark) {
    .bg   { fill: #0d1117; }
    .fg   { fill: #e6edf3; }
    .muted{ fill: #8b949e; }
    .line { stroke: #30363d; }
    .node { fill: #161b22; stroke: #30363d; }
    .accent { fill: #79c0ff; }
    .bar  { fill: #79c0ff; }
  }
  text { font-family: 'Segoe UI', Helvetica, Arial, sans-serif; }
</style>
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
    width = max(700, col_width * len(ordered_cats) + 40)
    height = 90 + 26 * max((len(categories.get(c, [])) for c in ordered_cats), default=1)

    root_x = width / 2
    parts = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Technology ecosystem diagram">']
    parts.append(STYLE_BLOCK)
    parts.append(f'<rect class="bg" x="0" y="0" width="{width}" height="{height}" rx="10"/>')
    parts.append(f'<text x="{root_x}" y="30" text-anchor="middle" class="fg" font-size="15" font-weight="600">{root_label}</text>')

    for i, cat in enumerate(ordered_cats):
        cx = 40 + col_width * i + col_width / 2
        parts.append(f'<line class="line" x1="{root_x}" y1="38" x2="{cx}" y2="60" stroke-width="1.2"/>')
        parts.append(f'<rect class="node" x="{cx-70}" y="60" width="140" height="24" rx="6" stroke-width="1"/>')
        parts.append(f'<text x="{cx}" y="76" text-anchor="middle" class="fg" font-size="12" font-weight="600">{CATEGORY_TITLES.get(cat, cat.title())}</text>')

        for j, tech in enumerate(categories.get(cat, [])[:8]):
            ty = 100 + j * 24
            parts.append(f'<line class="line" x1="{cx}" y1="84" x2="{cx}" y2="{ty+6}" stroke-width="1" stroke-dasharray="2,2"/>')
            parts.append(f'<text x="{cx}" y="{ty+10}" text-anchor="middle" class="muted" font-size="11">{tech["technology"]}</text>')

    parts.append("</svg>")
    return "\n".join(parts)


def language_distribution_svg(language_distribution: list[dict], max_langs: int = 6) -> str:
    langs = language_distribution[:max_langs]
    row_h = 30
    label_w = 130
    bar_max_w = 380
    width = label_w + bar_max_w + 90
    height = 30 + row_h * len(langs) + 20

    max_pct = max((l["percentage"] for l in langs), default=1) or 1

    parts = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Repository language distribution">']
    parts.append(STYLE_BLOCK)
    parts.append(f'<rect class="bg" x="0" y="0" width="{width}" height="{height}" rx="10"/>')
    parts.append(f'<text x="16" y="22" class="fg" font-size="13" font-weight="600">Repository Language Distribution</text>')

    for i, lang in enumerate(langs):
        y = 40 + i * row_h
        bar_w = max(4, bar_max_w * (lang["percentage"] / max_pct))
        parts.append(f'<text x="16" y="{y+14}" class="fg" font-size="12">{lang["language"]}</text>')
        parts.append(f'<rect class="bar" x="{label_w}" y="{y}" width="{bar_w:.1f}" height="16" rx="4"/>')
        parts.append(f'<text x="{label_w + bar_w + 8}" y="{y+13}" class="muted" font-size="11">{lang["percentage"]}%</text>')

    parts.append("</svg>")
    return "\n".join(parts)
