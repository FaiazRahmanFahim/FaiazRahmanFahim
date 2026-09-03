"""
main.py

Pipeline entrypoint. Run daily by .github/workflows/update-profile.yml
(and manually via `python scripts/main.py`).
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import github_client as gc
import project_classifier as pc
import readme_generator as rg
import repository_analyzer as ra
import statistics_generator as sg
import svg_generator as svgg
import technology_detector as td

try:
    import yaml
except ImportError:
    print("PyYAML is required: pip install pyyaml --break-system-packages", file=sys.stderr)
    raise

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENERATED_DIR = os.path.join(ROOT, "generated")
TEMPLATE_PATH = os.path.join(ROOT, "templates", "README.template.md")
README_PATH = os.path.join(ROOT, "README.md")
CONFIG_PATH = os.path.join(ROOT, "profile.config.yml")


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def write_json(name: str, data) -> None:
    os.makedirs(GENERATED_DIR, exist_ok=True)
    with open(os.path.join(GENERATED_DIR, name), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def build_hero_links(social: dict) -> str:
    parts = []
    if social.get("portfolio"):
        parts.append(
            f'<a href="{social["portfolio"]}" target="_blank">'
            f'<img src="https://img.shields.io/badge/Portfolio-000000?style=for-the-badge&logo=About.me&logoColor=white" alt="Portfolio" />'
            f'</a>'
        )
    if social.get("linkedin"):
        parts.append(
            f'<a href="{social["linkedin"]}" target="_blank">'
            f'<img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn" />'
            f'</a>'
        )
    if social.get("email"):
        parts.append(
            f'<a href="mailto:{social["email"]}">'
            f'<img src="https://img.shields.io/badge/Email-EA4335?style=for-the-badge&logo=gmail&logoColor=white" alt="Email" />'
            f'</a>'
        )
    return "&nbsp;&nbsp;".join(parts)


def build_ai_intro(config: dict, top_langs: list[dict], top_repo_name: str | None, focus: list[str]) -> str:
    profile = config.get("profile", {})
    lines = []
    lang_names = ", ".join(l["technology"] for l in top_langs[:3]) if top_langs else None

    sentence = f"**{profile.get('name')}** is a {profile.get('title', 'developer').lower()}"
    if profile.get("location"):
        sentence += f" based in {profile['location']}"
    sentence += "."
    lines.append(sentence)

    if lang_names:
        lines.append(f"Most active with **{lang_names}** across public repositories on GitHub.")
    if top_repo_name:
        lines.append(f"Currently building in [`{top_repo_name}`](https://github.com/{profile.get('username')}/{top_repo_name}).")
    if focus:
        lines.append(f"Specialized in {', '.join(focus)}.")

    about_summary = (config.get("about", {}) or {}).get("summary", "").strip()
    if about_summary:
        lines = [about_summary]

    return " ".join(lines)


def build_about_me(config: dict) -> str:
    about = config.get("about", {}) or {}
    sections = [
        ("👨‍💻 Who I Am", about.get("who_i_am")),
        ("🔥 What I'm Building", about.get("what_im_building")),
        ("🧠 What I Care About", about.get("what_i_care_about")),
        ("🎯 What I'm Working Toward", about.get("what_im_working_toward")),
        ("🤝 What I'd Like to Collaborate On", about.get("what_id_like_to_collaborate_on")),
    ]
    blocks = []
    for title, items in sections:
        items = [i for i in (items or []) if i and str(i).strip()]
        if items:
            blocks.append(f"### {title}\n" + "\n".join(f"- {i}" for i in items))
    return "\n\n".join(blocks)


def build_auto_block(repos, tech_agg, stats, classifications, username: str) -> str:
    categories = tech_agg["categories"]

    blocks = []

    # 1. Currently building (Active work only)
    blocks.append("### 🔥 Currently Building\n\n" + rg.render_currently_building(repos, classifications))

    # 2. Analytics cards & badges (No markdown table)
    analytics_content = [
        '<div align="center">',
        '  ' + rg.render_analytics_badges(stats),
        '</div>',
        '<br/>',
        '<div align="center">',
        f'  <img src="https://github-readme-stats.vercel.app/api?username={username}&show_icons=true&theme=tokyo-night&hide_border=true&title_color=58A6FF&icon_color=39D0D8&text_color=c9d1d9&bg_color=0d1117" alt="GitHub Stats" height="175" />',
        f'  <img src="https://github-readme-stats.vercel.app/api/top-langs/?username={username}&layout=compact&theme=tokyo-night&hide_border=true&title_color=58A6FF&text_color=c9d1d9&bg_color=0d1117" alt="Top Languages" height="175" />',
        '</div>',
        '<br/>',
        '<div align="center">',
        f'  <img src="https://github-readme-streak-stats.herokuapp.com/?user={username}&theme=tokyo-night&hide_border=true&background=0d1117&ring=58A6FF&fire=39D0D8&currStreakLabel=58A6FF" alt="GitHub Streak" />',
        '</div>'
    ]
    blocks.append("### 📊 GitHub Analytics\n\n" + "\n".join(analytics_content))

    # 6. Language breakdown (Redesigned modern SVG)
    blocks.append(
        "### 📈 Repository Language Breakdown\n\n"
        f'<img src="./generated/language-distribution.svg" alt="Language distribution chart" width="100%"/>'
    )

    # 7. Contribution Activity
    contribution_content = [
        '<div align="center">',
        f'  <img src="https://github-readme-activity-graph.vercel.app/graph?username={username}&theme=tokyo-night&hide_border=true&area=true&color=58A6FF" alt="GitHub Activity Graph" width="100%" />',
        '</div>',
        "",
        '<div align="center">',
        '  <picture>',
        f'    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/{username}/{username}/output/github-contribution-grid-snake-dark.svg">',
        f'    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/{username}/{username}/output/github-contribution-grid-snake.svg">',
        f'    <img alt="GitHub Contribution Snake" src="https://raw.githubusercontent.com/{username}/{username}/output/github-contribution-grid-snake.svg">',
        '  </picture>',
        '</div>'
    ]
    blocks.append("### 🟩 Contribution Activity\n\n" + "\n".join(contribution_content))

    return "\n\n---\n\n".join(blocks)


def main():
    config = load_config()
    profile = config.get("profile", {})
    username = profile.get("username", "FaiazRahmanFahim")

    client = gc.GitHubClient(username=username)

    user = client.get_user() or {}
    raw_repos = client.list_repos() or []

    repos = ra.analyze(raw_repos, config)

    per_repo_tech = {}
    classifications = {}
    for r in repos:
        detection = td.detect_for_repo(client, r["name"])
        per_repo_tech[r["name"]] = detection
        present_categories = {t["category"] for t in detection["technologies"]}
        classifications[r["name"]] = pc.classify_repo(r, present_categories)

    tech_agg = td.aggregate(per_repo_tech)
    stats = sg.generate(user, repos)

    write_json("repositories.json", repos)
    write_json("technologies.json", tech_agg)
    write_json("statistics.json", stats)
    write_json(
        "activity.json",
        {"recently_active": stats["recently_active_repos"], "classifications": classifications},
    )

    os.makedirs(GENERATED_DIR, exist_ok=True)
    top_categories = {k: v for k, v in tech_agg["categories"].items()}
    with open(os.path.join(GENERATED_DIR, "technology-ecosystem.svg"), "w", encoding="utf-8") as f:
        f.write(svgg.technology_ecosystem_svg(top_categories, f"{profile.get('name', username)}'s Ecosystem"))
    with open(os.path.join(GENERATED_DIR, "language-distribution.svg"), "w", encoding="utf-8") as f:
        f.write(svgg.language_distribution_svg(tech_agg["language_distribution"]))

    about = config.get("about", {}) or {}
    top_langs_for_intro = tech_agg["categories"].get("language", [])
    top_repo_name = repos[0]["name"] if repos else None

    template = open(TEMPLATE_PATH, "r", encoding="utf-8").read()
    auto_block = build_auto_block(repos, tech_agg, stats, classifications, username)

    rendered = (
        template.replace("{{NAME}}", profile.get("name", ""))
        .replace("{{USERNAME}}", username)
        .replace("{{TITLE}}", profile.get("title", ""))
        .replace("{{TAGLINE}}", profile.get("tagline", ""))
        .replace("{{HERO_LINKS}}", build_hero_links(config.get("social", {})))
        .replace("{{AI_INTRO}}", build_ai_intro(config, top_langs_for_intro, top_repo_name, about.get("current_focus", [])))
        .replace("{{ABOUT_ME}}", build_about_me(config))
        .replace("{{AUTO_BLOCK}}", auto_block)
        .replace("{{PHILOSOPHY}}", rg.render_config_list(about.get("philosophy"), "Build • Break • Debug • Repeat"))
        .replace("{{SOCIAL_LINKS}}", rg.render_social_links(config.get("social", {})))
        .replace("{{COLLAB_CTA}}", "Interested in collaborating or building something impactful? Feel free to reach out!")
    )

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(rendered)

    print(f"Generated README.md ({len(repos)} repos analyzed, "
          f"{sum(len(v) for v in tech_agg['categories'].values())} technologies detected).")


if __name__ == "__main__":
    main()
