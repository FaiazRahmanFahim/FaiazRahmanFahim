"""
readme_generator.py

Renders README.md from templates/README.template.md.
"""

from __future__ import annotations

import re

AUTO_START = "<!-- AUTO-GENERATED:START -->"
AUTO_END = "<!-- AUTO-GENERATED:END -->"


def _bar(pct: float, width: int = 18) -> str:
    filled = round(width * pct / 100)
    return "█" * filled + "░" * (width - filled)


def render_currently_building(repos: list[dict], labels_by_repo: dict[str, list[str]], limit: int = 5) -> str:
    picks = [r for r in repos if not r["is_fork"]][:limit]
    if not picks:
        return "_No recent public activity detected yet._"

    any_manual = any(r["is_manually_current"] for r in picks)
    heading = "Currently Building" if any_manual else "Recently Active / Current Projects"

    lines = [f"**{heading}**", ""]
    for r in picks:
        badge = " ".join(labels_by_repo.get(r["name"], [])[:2])
        desc_part = f" — {r['description']}" if r.get("description") else ""
        lines.append(f"- **[{r['name']}]({r['html_url']})**{desc_part}")
        meta = []
        if r.get("language"):
            meta.append(r["language"])
        if badge:
            meta.append(badge)
        if r.get("days_since_push") is not None:
            meta.append(f"updated {int(r['days_since_push'])}d ago")
        if meta:
            lines.append(f"  <sub>{' · '.join(meta)}</sub>")
    return "\n".join(lines)


def render_featured_projects(repos: list[dict], limit: int = 6) -> str:
    picks = sorted(repos, key=lambda r: r["score"], reverse=True)
    picks = [r for r in picks if not r["is_fork"]][:limit]
    if not picks:
        return "_No repositories available yet._"

    lines = []
    for r in picks:
        topics = ", ".join(r["topics"][:5]) if r.get("topics") else ""
        lines.append(f"### 📌 [{r['name']}]({r['html_url']})")
        if r.get("description"):
            lines.append(f"{r['description']}")
        
        meta = []
        if r.get("language"):
            meta.append(f"**Language:** `{r['language']}`")
        if r.get("stars"):
            meta.append(f"⭐ {r['stars']}")
        if r.get("forks"):
            meta.append(f"🍴 {r['forks']}")
        if meta:
            lines.append(" &nbsp;·&nbsp; ".join(meta))
        if topics:
            lines.append(f"🏷️ `{topics}`")
        if r.get("homepage"):
            lines.append(f"🚀 [**Live Demo ↗**]({r['homepage']})")
        lines.append("")
    return "\n".join(lines).strip()


def render_skills(tech_categories: dict[str, list[dict]]) -> str:
    order = [
        ("language", "💻 Languages"),
        ("frontend", "🌐 Frontend"),
        ("backend", "⚙️ Backend"),
        ("database", "🗄️ Databases"),
        ("devops", "🛠️ DevOps & Tools"),
        ("cloud", "☁️ Cloud"),
        ("ai_data", "🤖 AI / Data"),
    ]
    lines = []
    for key, title in order:
        techs = tech_categories.get(key, [])
        if not techs:
            continue
        badges = " ".join(f"`{t['technology']}`" for t in techs[:10])
        lines.append(f"- **{title}:** {badges}")
    if not lines:
        return "_No technologies detected yet._"
    return "\n".join(lines)


def render_language_distribution(language_distribution: list[dict], limit: int = 6) -> str:
    rows = language_distribution[:limit]
    if not rows:
        return "_No language data available yet._"
    lines = ["```text"]
    for row in rows:
        name = row["language"].ljust(14)
        lines.append(f"{name} {_bar(row['percentage'])}  {row['percentage']}%")
    lines.append("```")
    return "\n".join(lines)


def render_analytics(stats: dict) -> str:
    cells = []
    if stats.get("public_repos") is not None:
        cells.append(("📦 Public Repos", stats["public_repos"]))
    if stats.get("followers") is not None:
        cells.append(("👥 Followers", stats["followers"]))
    if stats.get("following") is not None:
        cells.append(("🤝 Following", stats["following"]))
    if stats.get("stars_earned_total") is not None:
        cells.append(("⭐ Stars Earned", stats["stars_earned_total"]))
    if stats.get("forks_total") is not None:
        cells.append(("🍴 Forks", stats["forks_total"]))

    if not cells:
        return ""

    header = " | ".join(c[0] for c in cells)
    sep = " | ".join(":---:" for _ in cells)
    row = " | ".join(f"**{c[1]}**" for c in cells)
    return f"| {header} |\n| {sep} |\n| {row} |"


def render_config_list(items: list[str] | None, empty_message: str = "") -> str:
    items = [i for i in (items or []) if i and str(i).strip()]
    if not items:
        return f"_{empty_message}_" if empty_message else ""
    return "\n".join(f"- {i}" for i in items)


def render_social_links(social: dict) -> str:
    badge_map = {
        "portfolio": ("Portfolio", "000000", "About.me"),
        "linkedin": ("LinkedIn", "0077B5", "linkedin"),
        "email": ("Email", "EA4335", "gmail"),
        "twitter": ("Twitter / X", "000000", "x"),
        "youtube": ("YouTube", "FF0000", "youtube"),
        "devto": ("Dev.to", "0A0A0A", "devdotto"),
        "medium": ("Medium", "12100E", "medium"),
        "stackoverflow": ("Stack Overflow", "F58025", "stackoverflow"),
        "discord": ("Discord", "5865F2", "discord"),
    }
    badges = []
    for key, (label, color, icon) in badge_map.items():
        value = (social or {}).get(key)
        if not value or key == "github":
            continue
        href = f"mailto:{value}" if key == "email" else value
        target_attr = "" if key == "email" else ' target="_blank"'
        badges.append(
            f'<a href="{href}"{target_attr}>'
            f'<img src="https://img.shields.io/badge/{label.replace(" ", "%20")}-{color}?style=for-the-badge&logo={icon}&logoColor=white" alt="{label}" />'
            f'</a>'
        )
    return "&nbsp;&nbsp;".join(badges) if badges else ""


def merge_with_existing(existing_readme: str | None, rendered_auto_block: str, fallback_template: str) -> str:
    """Preserve manual content outside AUTO-GENERATED markers."""
    if existing_readme and AUTO_START in existing_readme and AUTO_END in existing_readme:
        pattern = re.compile(re.escape(AUTO_START) + r".*?" + re.escape(AUTO_END), re.DOTALL)
        return pattern.sub(f"{AUTO_START}\n{rendered_auto_block}\n{AUTO_END}", existing_readme)

    pattern = re.compile(re.escape(AUTO_START) + r".*?" + re.escape(AUTO_END), re.DOTALL)
    return pattern.sub(f"{AUTO_START}\n{rendered_auto_block}\n{AUTO_END}", fallback_template)
