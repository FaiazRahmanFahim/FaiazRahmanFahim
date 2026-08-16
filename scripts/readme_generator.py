"""
readme_generator.py

Renders README.md from templates/README.template.md.

Two safety rules enforced here (SECTION 29 + SECTION 30):

  1. Content between <!-- AUTO-GENERATED:START/END --> markers is the
     ONLY thing this script overwrites. If README.md already exists,
     everything outside those markers (manual sections) is copied
     forward untouched.
  2. If a data point is missing, the corresponding line/section is
     omitted — never replaced with a placeholder like "N/A" that
     could be mistaken for a real (fabricated) value.
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
        desc = r["description"] or "_No description provided._"
        badge = " ".join(labels_by_repo.get(r["name"], [])[:2])
        lines.append(f"- **[{r['name']}]({r['html_url']})** — {desc}")
        meta = []
        if r["language"]:
            meta.append(r["language"])
        if badge:
            meta.append(badge)
        meta.append(f"updated {int(r['days_since_push'])}d ago")
        lines.append(f"  <sub>{' · '.join(meta)}</sub>")
    return "\n".join(lines)


def render_featured_projects(repos: list[dict], limit: int = 6) -> str:
    picks = sorted(repos, key=lambda r: r["score"], reverse=True)
    picks = [r for r in picks if not r["is_fork"]][:limit]
    if not picks:
        return "_No repositories available yet._"

    lines = []
    for r in picks:
        desc = r["description"] or "_No description provided._"
        topics = ", ".join(r["topics"][:5]) if r["topics"] else ""
        lines.append(f"### [{r['name']}]({r['html_url']})")
        lines.append(desc)
        meta = []
        if r["language"]:
            meta.append(f"**Language:** {r['language']}")
        if r["stars"]:
            meta.append(f"⭐ {r['stars']}")
        if r["forks"]:
            meta.append(f"🍴 {r['forks']}")
        if meta:
            lines.append(" &nbsp;·&nbsp; ".join(meta))
        if topics:
            lines.append(f"`{topics}`")
        if r["homepage"]:
            lines.append(f"[Live Demo]({r['homepage']})")
        lines.append("")
    return "\n".join(lines).strip()


def render_skills(tech_categories: dict[str, list[dict]]) -> str:
    order = [
        ("language", "Languages"),
        ("frontend", "Frontend"),
        ("backend", "Backend"),
        ("database", "Databases"),
        ("devops", "DevOps"),
        ("cloud", "Cloud"),
        ("ai_data", "AI / Data"),
    ]
    lines = []
    for key, title in order:
        techs = tech_categories.get(key, [])
        if not techs:
            continue
        names = ", ".join(t["technology"] for t in techs[:10])
        lines.append(f"**{title}:** {names}")
    if not lines:
        return "_No technologies detected yet — run the analyzer against public repositories._"
    lines.append("")
    lines.append("<sub>Detected automatically from repository languages, manifests and config "
                  "files. Frequency of use, not a claim of expertise.</sub>")
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
    lines.append("<sub>Based on GitHub's language byte statistics across public, non-fork "
                  "repositories. This reflects repository language distribution, not skill level.</sub>")
    return "\n".join(lines)


def render_analytics(stats: dict) -> str:
    cells = []
    if stats.get("public_repos") is not None:
        cells.append(("Public Repos", stats["public_repos"]))
    if stats.get("followers") is not None:
        cells.append(("Followers", stats["followers"]))
    if stats.get("following") is not None:
        cells.append(("Following", stats["following"]))
    if stats.get("stars_earned_total") is not None:
        cells.append(("Stars Earned", stats["stars_earned_total"]))
    if stats.get("forks_total") is not None:
        cells.append(("Forks", stats["forks_total"]))

    if not cells:
        return "_No statistics available yet._"

    header = " | ".join(c[0] for c in cells)
    sep = " | ".join("---" for _ in cells)
    row = " | ".join(str(c[1]) for c in cells)
    return f"{header}\n{sep}\n{row}"


def render_config_list(items: list[str] | None, empty_message: str) -> str:
    items = [i for i in (items or []) if i and i.strip()]
    if not items:
        return f"_{empty_message}_"
    return "\n".join(f"- {i}" for i in items)


def render_social_links(social: dict) -> str:
    icons = {
        "github": "GitHub",
        "portfolio": "Portfolio",
        "linkedin": "LinkedIn",
        "email": "Email",
        "twitter": "Twitter / X",
        "youtube": "YouTube",
        "devto": "Dev.to",
        "medium": "Medium",
        "stackoverflow": "Stack Overflow",
        "discord": "Discord",
    }
    lines = []
    for key, label in icons.items():
        value = (social or {}).get(key)
        if not value:
            continue
        if key == "email":
            lines.append(f"[✉️ {label}](mailto:{value})")
        else:
            lines.append(f"[🔗 {label}]({value})")
    return "  \n".join(lines) if lines else "_No social links configured._"


def merge_with_existing(existing_readme: str | None, rendered_auto_block: str, fallback_template: str) -> str:
    """Preserve manual content outside AUTO-GENERATED markers."""
    if existing_readme and AUTO_START in existing_readme and AUTO_END in existing_readme:
        pattern = re.compile(re.escape(AUTO_START) + r".*?" + re.escape(AUTO_END), re.DOTALL)
        return pattern.sub(f"{AUTO_START}\n{rendered_auto_block}\n{AUTO_END}", existing_readme)

    # No existing README with markers -> use the template as the base.
    pattern = re.compile(re.escape(AUTO_START) + r".*?" + re.escape(AUTO_END), re.DOTALL)
    return pattern.sub(f"{AUTO_START}\n{rendered_auto_block}\n{AUTO_END}", fallback_template)
