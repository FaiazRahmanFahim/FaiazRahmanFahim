"""
github_client.py

Thin wrapper around the GitHub REST API.

- Reads the token from the GITHUB_TOKEN environment variable (set by
  GitHub Actions automatically as `secrets.GITHUB_TOKEN`, or export it
  locally for manual runs). Never hardcode a token anywhere.
- Handles pagination, rate-limit backoff, and 404/403 as "no data"
  instead of crashing the whole pipeline (see SECTION 33 - Failure
  Handling in the master prompt).
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

API_ROOT = "https://api.github.com"
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".cache")


class GitHubClient:
    def __init__(self, username: str, token: str | None = None, use_cache: bool = True):
        self.username = username
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        # Caching is for local/dev runs against the unauthenticated rate
        # limit (60/hr). In GitHub Actions, GITHUB_TOKEN raises this to
        # 5,000/hr, so caching is skipped there via NO_CACHE=1.
        self.use_cache = use_cache and not os.environ.get("NO_CACHE")
        if self.use_cache:
            os.makedirs(CACHE_DIR, exist_ok=True)

    def _cache_path(self, url: str) -> str:
        import hashlib

        digest = hashlib.sha256(url.encode()).hexdigest()[:24]
        return os.path.join(CACHE_DIR, f"{digest}.json")

    # ---------------------------------------------------------- core
    def _request(self, url: str, params: dict | None = None):
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query}"

        if self.use_cache:
            cache_file = self._cache_path(url)
            if os.path.exists(cache_file):
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)

        req = urllib.request.Request(url)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("User-Agent", f"{self.username}-profile-bot")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")

        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=20) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                if self.use_cache:
                    with open(self._cache_path(url), "w", encoding="utf-8") as f:
                        json.dump(data, f)
                return data
            except urllib.error.HTTPError as e:
                if e.code in (403, 429) and attempt < 2:
                    # Likely rate-limited — back off and retry once.
                    time.sleep(2 * (attempt + 1))
                    continue
                if e.code == 404:
                    return None
                print(f"[github_client] WARN: {url} -> HTTP {e.code}", file=sys.stderr)
                return None
            except urllib.error.URLError as e:
                print(f"[github_client] WARN: {url} -> {e}", file=sys.stderr)
                return None
        return None

    def _paginated(self, url: str, params: dict | None = None):
        results = []
        page = 1
        params = dict(params or {})
        while True:
            params["page"] = page
            params.setdefault("per_page", 100)
            batch = self._request(url, params)
            if not batch:
                break
            results.extend(batch)
            if len(batch) < params["per_page"]:
                break
            page += 1
        return results

    # ------------------------------------------------------- public
    def get_user(self):
        return self._request(f"{API_ROOT}/users/{self.username}")

    def list_repos(self):
        return self._paginated(f"{API_ROOT}/users/{self.username}/repos", {"sort": "updated"})

    def get_languages(self, repo_name: str) -> dict:
        return self._request(f"{API_ROOT}/repos/{self.username}/{repo_name}/languages") or {}

    def get_root_contents(self, repo_name: str) -> list:
        data = self._request(f"{API_ROOT}/repos/{self.username}/{repo_name}/contents/")
        return data if isinstance(data, list) else []

    def get_file(self, repo_name: str, path: str) -> str | None:
        """Return decoded text content of a file, or None if unavailable."""
        data = self._request(f"{API_ROOT}/repos/{self.username}/{repo_name}/contents/{path}")
        if not data or "content" not in data:
            return None
        try:
            return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
        except Exception:
            return None

    def get_pinned_repos(self) -> list[str]:
        """Fetch list of pinned repository names via GraphQL or HTML scrape fallback."""
        if self.token:
            gql_query = """
            query($username: String!) {
              user(login: $username) {
                pinnedItems(first: 6, types: REPOSITORY) {
                  nodes {
                    ... on Repository {
                      name
                    }
                  }
                }
              }
            }
            """
            req = urllib.request.Request(f"{API_ROOT}/graphql")
            req.add_header("Authorization", f"Bearer {self.token}")
            req.add_header("User-Agent", f"{self.username}-profile-bot")
            req.add_header("Content-Type", "application/json")
            body = json.dumps({"query": gql_query, "variables": {"username": self.username}}).encode("utf-8")
            try:
                with urllib.request.urlopen(req, data=body, timeout=15) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                    nodes = res.get("data", {}).get("user", {}).get("pinnedItems", {}).get("nodes", [])
                    if nodes:
                        return [n["name"] for n in nodes if "name" in n]
            except Exception as e:
                print(f"[github_client] GraphQL pinned query failed: {e}", file=sys.stderr)

        # Fallback: scrape public profile HTML
        try:
            import re
            profile_url = f"https://github.com/{self.username}"
            req = urllib.request.Request(profile_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                pinned = re.findall(r'<span class="repo" title="([^"]+)">', html)
                if not pinned:
                    pinned = re.findall(r'class="repo"[^>]*title="([^"]+)"', html)
                if not pinned:
                    # Look inside js-pinned-items-reorder-list
                    pinned = re.findall(rf'href="/{self.username}/([a-zA-Z0-9_\-\.]+)"', html)
                    pinned = [p for p in pinned if p not in ("followers", "following", "stars", "projects", "packages", "tab=repositories", "tab=stars", "tab=projects", "tab=packages")]
                seen = set()
                deduped = [x for x in pinned if not (x in seen or seen.add(x))]
                return deduped[:6]
        except Exception as e:
            print(f"[github_client] HTML pinned scrape failed: {e}", file=sys.stderr)
            return []
