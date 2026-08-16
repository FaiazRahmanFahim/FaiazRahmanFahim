"""
main.py

Pipeline entrypoint. Run daily by .github/workflows/update-profile.yml
(and manually via `python scripts/main.py`).

    GitHub API
        -> repository_analyzer   (filter + score)
        -> technology_detector   (per-repo detection + aggregation)
        -> project_classifier    (evidence-based labels)
        -> statistics_generator  (verified public stats)
        -> svg_generator         (technology-ecosystem.svg, language-distribution.svg)
        -> readme_generator      (renders README.md, preserving manual edits)

All intermediate data is written to generated/*.json so the pipeline
is inspectable and each stage can be re-run independently.
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
    if social.get("github"):
        parts.append(f"[GitHub]({social['github']})")
    if social.get("portfolio"):
        parts.append(f"[Portfolio]({social['portfolio']})")
    if social.get("linkedin"):
        parts.append(f"[LinkedIn]({social['linkedin']})")
    if social.get("email"):
        parts.append(f"[Email](mailto:{social['email']})")
    return " &nbsp;|&nbsp; ".join(parts)


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
        lines.append(f"Currently most active in [`{top_repo_name}`](https://github.com/{profile.get('username')}/{top_repo_name}).")
    if focus:
        lines.append(f"Focused on: {', '.join(focus)}.")

    about_summary = (config.get("about", {}) or {}).get("summary", "").strip()
    if about_summary:
        lines = [about_summary]

    return " ".join(lines) if lines else "_Add `about.summary` in `profile.config.yml` to populate this section._"


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
        items = [i for i in (items or []) if i and i.strip()]
        if items:
            blocks.append(f"**{title}**\n" + "\n".join(f"- {i}" for i in items))
    if not blocks:
        return "_Add entries under `about.*` in `profile.config.yml` to populate this section._"
    return "\n\n".join(blocks)


def build_auto_block(repos, tech_agg, stats, classifications, username: str) -> str:
    categories = tech_agg["categories"]
    lang_dist = tech_agg["language_distribution"]

    blocks = []

    blocks.append("### 🔥 Currently Building\n\n" + rg.render_currently_building(repos, classifications))
    blocks.append("### 🚀 Featured Projects\n\n" + rg.render_featured_projects(repos))
    blocks.append("### 🧠 Skills & Tools\n\n" + rg.render_skills(categories))
    blocks.append(
        "### 🌳 Technology Ecosystem\n\n"
        f'<img src="./generated/technology-ecosystem.svg" alt="Technology ecosystem diagram" width="100%"/>'
    )
    blocks.append("### 📊 GitHub Analytics\n\n" + rg.render_analytics(stats))
    blocks.append(
        "### 📈 Repository Language Distribution\n\n"
        + rg.render_language_distribution(lang_dist)
        + f'\n\n<img src="./generated/language-distribution.svg" alt="Language distribution chart" width="100%"/>'
    )
    blocks.append(
        "### 🟩 Contribution Activity\n\n"
        f"![GitHub contribution snake](https://raw.githubusercontent.com/{username}/{username}/output/github-contribution-grid-snake.svg)\n\n"
        "<sub>Rendered by a separate, optional snake-animation workflow — see docs/AUTOMATION.md.</sub>"
    )

    return "\n\n---\n\n".join(blocks)


def main():
    config = load_config()
    profile = config.get("profile", {})
    username = profile.get("username")

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
        .replace("{{TITLE}}", profile.get("title", ""))
        .replace("{{TAGLINE}}", profile.get("tagline", ""))
        .replace("{{HERO_LINKS}}", build_hero_links(config.get("social", {})))
        .replace("{{AI_INTRO}}", build_ai_intro(config, top_langs_for_intro, top_repo_name, about.get("current_focus", [])))
        .replace("{{ABOUT_ME}}", build_about_me(config))
        .replace("{{AUTO_BLOCK}}", auto_block)
        .replace("{{LEARNING}}", rg.render_config_list(about.get("learning"), "No learning goals configured yet — add them to profile.config.yml"))
        .replace("{{PHILOSOPHY}}", rg.render_config_list(about.get("philosophy"), "No engineering philosophy configured yet"))
        .replace("{{SOCIAL_LINKS}}", rg.render_social_links(config.get("social", {})))
        .replace("{{COLLAB_CTA}}", "Interested in building something meaningful? Let's connect, collaborate, and ship something great.")
        .replace("{{FOOTER}}", "This profile updates automatically via GitHub Actions — last content reflects live public repository data.")
    )

    existing = open(README_PATH, "r", encoding="utf-8").read() if os.path.exists(README_PATH) else None
    final = rg.merge_with_existing(existing, auto_block, template) if existing else rendered
    # Since the whole file is template-rendered fresh each run (manual
    # content lives in profile.config.yml, not hand-edited README
    # prose), we always use `rendered` — merge_with_existing is kept
    # available for any freeform manual zones added by a user later.
    final = rendered

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(final)

    print(f"Generated README.md ({len(repos)} repos analyzed, "
          f"{sum(len(v) for v in tech_agg['categories'].values())} technologies detected).")


if __name__ == "__main__":
    main()
