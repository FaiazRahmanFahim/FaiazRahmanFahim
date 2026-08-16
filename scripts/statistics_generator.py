"""
statistics_generator.py

Produces only statistics that are directly backed by GitHub API data
(SECTION 32). Nothing here is estimated or rounded up for effect.
Fields the API cannot reliably provide (e.g. total commit count
requires the GraphQL contributions calendar with auth) are included
only when available, and omitted otherwise rather than guessed.
"""

from __future__ import annotations


def generate(user: dict, repos: list[dict]) -> dict:
    non_fork = [r for r in repos if not r["is_fork"]]
    stars_total = sum(r["stars"] for r in repos)
    forks_total = sum(r["forks"] for r in repos)

    languages_seen = {}
    for r in repos:
        if r["language"]:
            languages_seen[r["language"]] = languages_seen.get(r["language"], 0) + 1

    top_languages_by_repo_count = sorted(
        languages_seen.items(), key=lambda x: x[1], reverse=True
    )

    recently_active = sorted(repos, key=lambda x: x["days_since_push"])[:5]

    return {
        "public_repos": user.get("public_repos"),
        "non_fork_repos": len(non_fork),
        "followers": user.get("followers"),
        "following": user.get("following"),
        "stars_earned_total": stars_total,
        "forks_total": forks_total,
        "top_languages_by_repo_count": [
            {"language": lang, "repo_count": count} for lang, count in top_languages_by_repo_count
        ],
        "recently_active_repos": [
            {"name": r["name"], "days_since_push": r["days_since_push"]} for r in recently_active
        ],
        "account_created_at": user.get("created_at"),
    }
