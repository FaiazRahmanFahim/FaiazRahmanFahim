"""
technology_detector.py

Detects technologies from real signals only (SECTION 8 + SECTION 27
of the master prompt):

  1. GitHub's own language statistics API      -> languages
  2. Manifest files (package.json, etc.)        -> frameworks/tools
  3. Config file presence (tailwind.config.js…) -> frameworks/tools

Every detected technology carries a confidence score and the evidence
that produced it, so the README generator can distinguish "detected"
from "self-declared skill" and can drop anything below threshold.
"""

from __future__ import annotations

CONFIDENCE_THRESHOLD = 0.5

# manifest filename -> (category, parser key)
MANIFEST_FILES = {
    "package.json": "npm",
    "requirements.txt": "pip",
    "pyproject.toml": "pip",
    "pom.xml": "maven",
    "build.gradle": "gradle",
    "composer.json": "composer",
    "Gemfile": "bundler",
    "go.mod": "go",
    "Cargo.toml": "cargo",
}

# Root-level filename presence -> technology, category, confidence
FILE_SIGNALS = {
    "Dockerfile": ("Docker", "devops", 0.95),
    "docker-compose.yml": ("Docker Compose", "devops", 0.95),
    "docker-compose.yaml": ("Docker Compose", "devops", 0.95),
    "tailwind.config.js": ("Tailwind CSS", "frontend", 0.9),
    "tailwind.config.ts": ("Tailwind CSS", "frontend", 0.9),
    "vite.config.js": ("Vite", "frontend", 0.9),
    "vite.config.ts": ("Vite", "frontend", 0.9),
    "next.config.js": ("Next.js", "frontend", 0.95),
    "next.config.ts": ("Next.js", "frontend", 0.95),
    "angular.json": ("Angular", "frontend", 0.95),
    "svelte.config.js": ("Svelte", "frontend", 0.95),
    "terraform": ("Terraform", "devops", 0.7),
    ".terraform": ("Terraform", "devops", 0.7),
    "vercel.json": ("Vercel", "cloud", 0.85),
    "netlify.toml": ("Netlify", "cloud", 0.85),
    "firebase.json": ("Firebase", "database", 0.85),
    "prisma": ("Prisma", "database", 0.7),
    "manage.py": ("Django", "backend", 0.9),
    "artisan": ("Laravel", "backend", 0.9),
}

# npm dependency name -> (technology, category, confidence)
NPM_DEP_SIGNALS = {
    "react": ("React", "frontend", 0.95),
    "react-dom": ("React", "frontend", 0.9),
    "react-router": ("React Router", "frontend", 0.85),
    "react-router-dom": ("React Router", "frontend", 0.85),
    "next": ("Next.js", "frontend", 0.95),
    "vue": ("Vue", "frontend", 0.95),
    "@angular/core": ("Angular", "frontend", 0.95),
    "svelte": ("Svelte", "frontend", 0.95),
    "tailwindcss": ("Tailwind CSS", "frontend", 0.9),
    "daisyui": ("DaisyUI", "frontend", 0.85),
    "recharts": ("Recharts", "frontend", 0.75),
    "lucide-react": ("Lucide Icons", "frontend", 0.6),
    "vite": ("Vite", "frontend", 0.9),
    "express": ("Express", "backend", 0.95),
    "fastify": ("Fastify", "backend", 0.9),
    "nestjs": ("NestJS", "backend", 0.9),
    "@nestjs/core": ("NestJS", "backend", 0.95),
    "mongoose": ("MongoDB", "database", 0.85),
    "mongodb": ("MongoDB", "database", 0.85),
    "pg": ("PostgreSQL", "database", 0.85),
    "mysql": ("MySQL", "database", 0.8),
    "mysql2": ("MySQL", "database", 0.85),
    "sequelize": ("SQL (Sequelize ORM)", "database", 0.7),
    "prisma": ("Prisma", "database", 0.85),
    "firebase": ("Firebase", "database", 0.85),
    "redis": ("Redis", "database", 0.85),
    "typescript": ("TypeScript", "language", 0.85),
    "socket.io": ("WebSockets (Socket.IO)", "backend", 0.75),
    "jsonwebtoken": ("JWT Auth", "backend", 0.7),
}

# pip requirement name -> (technology, category, confidence)
PIP_DEP_SIGNALS = {
    "django": ("Django", "backend", 0.95),
    "flask": ("Flask", "backend", 0.95),
    "fastapi": ("FastAPI", "backend", 0.95),
    "torch": ("PyTorch", "ai_data", 0.95),
    "tensorflow": ("TensorFlow", "ai_data", 0.95),
    "pandas": ("Pandas", "ai_data", 0.9),
    "numpy": ("NumPy", "ai_data", 0.9),
    "langchain": ("LangChain", "ai_data", 0.9),
    "scikit-learn": ("scikit-learn", "ai_data", 0.9),
    "psycopg2": ("PostgreSQL", "database", 0.8),
    "pymongo": ("MongoDB", "database", 0.8),
}


def _add(bucket: dict, tech: str, category: str, confidence: float, evidence: str):
    key = tech
    if key not in bucket or bucket[key]["confidence"] < confidence:
        entry = bucket.setdefault(
            key, {"technology": tech, "category": category, "confidence": confidence, "evidence": []}
        )
        entry["confidence"] = max(entry["confidence"], confidence)
    if evidence not in bucket[key]["evidence"]:
        bucket[key]["evidence"].append(evidence)


def detect_for_repo(client, repo_name: str) -> dict:
    """Returns {"languages": {...}, "technologies": [...]} for one repo."""
    languages = client.get_languages(repo_name)

    found: dict[str, dict] = {}
    for lang in languages:
        _add(found, lang, "language", 0.99, "GitHub language statistics")

    root_files = {f["name"]: f for f in client.get_root_contents(repo_name)}

    for fname, (tech, category, conf) in FILE_SIGNALS.items():
        if fname in root_files:
            _add(found, tech, category, conf, f"{fname} present")

    if "package.json" in root_files:
        content = client.get_file(repo_name, "package.json")
        if content:
            import json as _json

            try:
                pkg = _json.loads(content)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                for dep, (tech, category, conf) in NPM_DEP_SIGNALS.items():
                    if dep in deps:
                        _add(found, tech, category, conf, "package.json dependency")
            except Exception:
                pass

    if "requirements.txt" in root_files:
        content = client.get_file(repo_name, "requirements.txt") or ""
        lowered = content.lower()
        for dep, (tech, category, conf) in PIP_DEP_SIGNALS.items():
            if dep in lowered:
                _add(found, tech, category, conf, "requirements.txt dependency")

    technologies = [v for v in found.values() if v["confidence"] >= CONFIDENCE_THRESHOLD]
    technologies.sort(key=lambda x: x["confidence"], reverse=True)

    return {"languages": languages, "technologies": technologies}


def aggregate(all_repo_tech: dict[str, dict]) -> dict:
    """Combine per-repo detections into a profile-wide technology ecosystem."""
    categories: dict[str, dict[str, dict]] = {}
    language_totals: dict[str, int] = {}

    for repo_name, data in all_repo_tech.items():
        for lang, bytes_count in data["languages"].items():
            language_totals[lang] = language_totals.get(lang, 0) + bytes_count

        for tech in data["technologies"]:
            cat = tech["category"]
            categories.setdefault(cat, {})
            entry = categories[cat].setdefault(
                tech["technology"],
                {"technology": tech["technology"], "confidence": 0.0, "repos": [], "evidence": set()},
            )
            entry["confidence"] = max(entry["confidence"], tech["confidence"])
            entry["repos"].append(repo_name)
            entry["evidence"].update(tech["evidence"])

    # finalize: convert sets to lists, sort by confidence then repo count
    for cat, techs in categories.items():
        for t in techs.values():
            t["evidence"] = sorted(t["evidence"])
            t["repo_count"] = len(t["repos"])
        categories[cat] = sorted(
            techs.values(), key=lambda x: (x["confidence"], x["repo_count"]), reverse=True
        )

    total_lang_bytes = sum(language_totals.values()) or 1
    language_distribution = sorted(
        (
            {"language": lang, "bytes": b, "percentage": round(b / total_lang_bytes * 100, 1)}
            for lang, b in language_totals.items()
        ),
        key=lambda x: x["bytes"],
        reverse=True,
    )

    return {"categories": categories, "language_distribution": language_distribution}
