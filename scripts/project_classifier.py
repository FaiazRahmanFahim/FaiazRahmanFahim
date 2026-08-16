"""
project_classifier.py

Assigns evidence-based labels to repositories (SECTION 25). Multiple
labels can apply. Manual overrides in profile.config.yml always win.
"""

from __future__ import annotations

CATEGORY_LABELS = {
    "frontend": "🎨 Frontend",
    "backend": "⚙️ Backend",
    "database": "🗄️ Database",
    "devops": "🔧 DevOps",
    "cloud": "☁️ Cloud",
    "ai_data": "🤖 AI / Data",
    "language": None,  # languages alone don't drive a category label
}


def classify_repo(repo: dict, tech_categories_present: set[str]) -> list[str]:
    labels = []

    if repo["is_manually_current"]:
        labels.append("🔥 Active")
    elif repo["days_since_push"] <= 21:
        labels.append("🔥 Active")

    if repo["is_manually_featured"]:
        labels.append("⭐ Featured")

    for cat in ("frontend", "backend", "database", "devops", "cloud", "ai_data"):
        if cat in tech_categories_present:
            label = CATEGORY_LABELS[cat]
            if label:
                labels.append(label)

    name_lower = repo["name"].lower()
    desc_lower = (repo["description"] or "").lower()
    if any(k in name_lower or k in desc_lower for k in ("learn", "tutorial", "practice", "course")):
        labels.append("📚 Learning")
    if any(k in name_lower for k in ("test", "demo", "experiment", "poc", "sandbox")):
        labels.append("🧪 Experimental")

    # de-duplicate, preserve order
    seen = set()
    ordered = []
    for l in labels:
        if l not in seen:
            seen.add(l)
            ordered.append(l)
    return ordered
