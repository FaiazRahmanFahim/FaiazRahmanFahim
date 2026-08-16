"""
repository_analyzer.py

Turns the raw GitHub repo list into a filtered, scored list that the
rest of the pipeline (technology_detector, project_classifier,
statistics_generator) can consume.

Scoring is intentionally simple and explainable — see SECTION 26 of
the master prompt ("Repository Priority"). Stars are never the sole
signal, because a personal-learning profile rarely has meaningful
star counts.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone


def _days_since(iso_ts: str) -> float:
    dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - dt).total_seconds() / 86400


def filter_repos(raw_repos: list, config: dict) -> list:
    repo_cfg = config.get("repositories", {})
    exclude = set(repo_cfg.get("exclude", []) or [])
    include_forks = repo_cfg.get("include_forks", False)
    include_archived = repo_cfg.get("include_archived", False)

    filtered = []
    for r in raw_repos:
        if r["name"] in exclude:
            continue
        if r.get("fork") and not include_forks:
            continue
        if r.get("archived") and not include_archived:
            continue
        filtered.append(r)
    return filtered


def score_repo(repo: dict, manual_priority: int = 0) -> float:
    recency_days = _days_since(repo["pushed_at"] or repo["updated_at"])
    # Exponential decay: a repo touched today scores ~40, a year-old ~1.
    recency_score = 40 * math.exp(-recency_days / 60)

    commit_activity_proxy = 5 if recency_days < 14 else 0  # coarse proxy
    engagement_score = (repo.get("stargazers_count", 0) * 2) + repo.get("forks_count", 0)
    description_score = 3 if (repo.get("description") or "").strip() else 0
    topics_score = min(len(repo.get("topics", []) or []), 5)

    return round(
        recency_score
        + commit_activity_proxy
        + engagement_score
        + description_score
        + topics_score
        + manual_priority,
        2,
    )


def analyze(raw_repos: list, config: dict) -> list:
    repos = filter_repos(raw_repos, config)
    manual_priorities = {
        fp["repo"]: fp.get("priority", 0)
        for fp in (config.get("featured_projects") or [])
        if fp.get("repo")
    }
    manual_current = set(config.get("current_projects") or [])

    enriched = []
    for r in repos:
        score = score_repo(r, manual_priorities.get(r["name"], 0))
        recency_days = _days_since(r["pushed_at"] or r["updated_at"])
        enriched.append(
            {
                "name": r["name"],
                "description": r.get("description"),
                "html_url": r["html_url"],
                "homepage": r.get("homepage") or None,
                "language": r.get("language"),
                "topics": r.get("topics", []) or [],
                "stars": r.get("stargazers_count", 0),
                "forks": r.get("forks_count", 0),
                "pushed_at": r["pushed_at"],
                "updated_at": r["updated_at"],
                "days_since_push": round(recency_days, 1),
                "is_fork": r.get("fork", False),
                "is_manually_featured": r["name"] in manual_priorities,
                "is_manually_current": r["name"] in manual_current,
                "score": score,
            }
        )

    enriched.sort(key=lambda x: x["score"], reverse=True)
    return enriched
