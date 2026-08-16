# Setup & Documentation

This repo is a **self-updating GitHub profile system**, not just a
static README. Everything below explains how it works and how to run
or customize it.

## 1. How it fits together

```text
profile.config.yml  (manual truth)
        │
        ▼
GitHub public API  ──►  scripts/main.py  ──►  generated/*.json + *.svg
        │                                              │
        └──────────────────────────────────────────────┘
                              ▼
                       README.md (rendered)
```

- `profile.config.yml` — everything GitHub cannot know about you
  (bio, focus, links, philosophy, pinned projects). This is the only
  file you should hand-edit for wording changes.
- `scripts/` — the pipeline. Each module has one job:
  - `github_client.py` — talks to the GitHub REST API (with local
    on-disk caching so repeated dev runs don't burn your rate limit).
  - `repository_analyzer.py` — filters (forks/archived/excludes) and
    scores repos by recency, engagement, and manual priority.
  - `technology_detector.py` — detects languages/frameworks/tools
    from GitHub's language stats and real manifest files
    (`package.json`, `requirements.txt`, etc.), each with a
    confidence score and evidence trail.
  - `project_classifier.py` — assigns evidence-based labels (🔥
    Active, ⭐ Featured, 🎨 Frontend, …).
  - `statistics_generator.py` — verified public stats only; nothing
    estimated.
  - `svg_generator.py` — renders the technology-ecosystem diagram and
    language-distribution chart as dark/light-adaptive SVG.
  - `readme_generator.py` — pure rendering helpers used by `main.py`.
  - `main.py` — orchestrates the above and writes `README.md` +
    `generated/*.json`.
- `templates/README.template.md` — the structural skeleton with
  `{{PLACEHOLDER}}` tokens and an `<!-- AUTO-GENERATED:START/END -->`
  region that marks the fully-automatic content.
- `.github/workflows/update-profile.yml` — runs the pipeline daily
  and on manual dispatch, and only commits when something changed.

## 2. Installing / activating the automation

1. This repo **must** be named exactly like your GitHub username
   (e.g. `FaiazRahmanFahim/FaiazRahmanFahim`) — that's what makes
   GitHub render its README on your profile page.
2. Push these files to that repo's `main` branch.
3. No extra secrets are required. The workflow uses the automatically
   provided `secrets.GITHUB_TOKEN`, which is scoped to this repo and
   raises the API rate limit to 5,000 requests/hour — plenty for a
   daily scan of all public repositories.
4. Go to **Settings → Actions → General** and confirm "Read and write
   permissions" is enabled for the default `GITHUB_TOKEN` (needed for
   the workflow to push the updated README).
5. Trigger the first run manually: **Actions → Update Profile README
   → Run workflow**.

## 3. Configuration reference

Edit `profile.config.yml`:

| Field | Purpose |
|---|---|
| `profile.name/title/tagline/location` | Hero section content |
| `about.*` | About Me bullet sections (empty lists are simply omitted) |
| `about.current_focus` / `about.learning` / `about.philosophy` | Manual lists rendered as-is |
| `social.*` | Only non-empty links are rendered |
| `repositories.exclude` | Repo names to hide entirely |
| `repositories.include_forks/include_archived` | Filtering toggles |
| `current_projects` | Force specific repos into "Currently Building" regardless of scoring |
| `featured_projects` | Pin repos with a manual priority weight added to their score |
| `theme.*` | Reserved for future SVG theming hooks |
| `automation.cron` | Human-readable record of the schedule — update the workflow file's `cron:` line to match |

## 4. Repository selection & classification

- By default **all public, non-fork, non-archived** repositories are
  scanned (`repositories.scan_all_public: true`).
- Priority score = recency decay + engagement (stars/forks) +
  description quality + topic count + manual priority. Stars are
  never used alone, since personal/learning repos rarely accumulate
  stars regardless of quality.
- A repo is labelled "🔥 Active" automatically if it was pushed to in
  the last 21 days, or always if listed in `current_projects`.
- Override any classification by adding the repo to `current_projects`
  or `featured_projects` in the config.

## 5. Running locally

```bash
pip install -r requirements.txt
export NO_CACHE=1                 # optional: skip the local dev cache
export GITHUB_TOKEN=ghp_xxx       # optional: raises the rate limit
python scripts/main.py
```

Running without `GITHUB_TOKEN` works, but is subject to GitHub's
60 requests/hour unauthenticated limit — the client will cache
successful responses under `.cache/` and degrade gracefully (fewer
detected technologies, not a crash) if it runs out.

## 6. Failure handling

- Any single failed API call returns `None`/`[]` instead of raising —
  the pipeline always finishes and never deletes existing
  `README.md` or `generated/` content on failure.
- The workflow only commits when `git diff` shows an actual change to
  `README.md` or `generated/`, so a no-op day produces zero commits.

## 7. No-fabrication guarantee

- Every displayed technology has a `confidence` score and `evidence`
  list in `generated/technologies.json` — nothing is shown that
  wasn't backed by a real file or API field.
- Statistics that GitHub's REST API can't reliably provide (e.g. a
  full lifetime commit count without GraphQL + auth) are simply
  omitted rather than estimated.
- "Detected Technology" (frequency of use) is always kept visually
  and textually distinct from a self-declared skill claim.
