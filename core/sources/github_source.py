"""
core/sources/github_source.py
GitHub candidate sourcing using the official GitHub API.
Searches for developers by skills, location, repos.
"""
import requests
import streamlit as st
from typing import List, Dict, Optional
import time


GITHUB_API = "https://api.github.com"


def _headers(token: str = "") -> Dict:
    h = {"Accept": "application/vnd.github.v3+json"}
    if token:
        h["Authorization"] = f"token {token}"
    return h


def _search_users(query: str, token: str, max_results: int = 20) -> List[Dict]:
    """Search GitHub users by query."""
    try:
        url = f"{GITHUB_API}/search/users"
        params = {"q": query, "per_page": min(max_results, 30), "sort": "followers"}
        resp = requests.get(url, params=params, headers=_headers(token), timeout=10)

        if resp.status_code == 200:
            return resp.json().get("items", [])
        elif resp.status_code == 403:
            # Rate limited
            return []
        return []
    except Exception:
        return []


def _get_user_detail(username: str, token: str) -> Optional[Dict]:
    """Fetch detailed profile for a GitHub user."""
    try:
        url = f"{GITHUB_API}/users/{username}"
        resp = requests.get(url, headers=_headers(token), timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception:
        return None


def _get_user_repos(username: str, token: str, max_repos: int = 5) -> List[str]:
    """Get the top repo names for a user."""
    try:
        url = f"{GITHUB_API}/users/{username}/repos"
        params = {"per_page": max_repos, "sort": "stars", "direction": "desc"}
        resp = requests.get(url, params=params, headers=_headers(token), timeout=10)
        if resp.status_code == 200:
            repos = resp.json()
            return [r.get("name", "") for r in repos if not r.get("fork", False)]
        return []
    except Exception:
        return []


def _parse_github_user(user: Dict, detail: Dict = None) -> Dict:
    """Convert GitHub user data into a candidate record."""
    d = detail or user
    name = d.get("name") or user.get("login", "")
    bio = d.get("bio", "") or ""
    location = d.get("location", "") or ""
    company = d.get("company", "") or ""

    # Infer title from bio/company
    title_hints = ["engineer", "developer", "dev", "architect", "lead", "senior", "full stack",
                   "backend", "frontend", "data scientist", "ml engineer", "devops"]
    inferred_title = ""
    bio_lower = bio.lower()
    for hint in title_hints:
        if hint in bio_lower:
            inferred_title = bio.split(".")[0][:80] if bio else ""
            break
    if not inferred_title and company:
        inferred_title = f"Developer at {company.strip('@')}"

    followers = d.get("followers", 0)
    public_repos = d.get("public_repos", 0)

    # Build a credibility indicator from GitHub stats
    credibility = ""
    if followers > 100:
        credibility = f"⭐ {followers} followers"
    elif public_repos > 20:
        credibility = f"📁 {public_repos} public repos"

    summary = bio if bio else f"GitHub developer with {public_repos} public repos."
    if credibility:
        summary = f"{credibility} · {summary}"

    return {
        "full_name": name,
        "current_title": inferred_title or "Software Developer",
        "location": location,
        "source": "GitHub",
        "source_icon": "🐙",
        "profile_url": user.get("html_url", ""),
        "email": d.get("email", "") or "",
        "summary": summary,
        "skills": [],  # Will be enriched from repo languages
        "match_score": 0,
        "raw_data": {
            "username": user.get("login"),
            "followers": followers,
            "public_repos": public_repos,
            "company": company,
            "blog": d.get("blog", ""),
        }
    }


def search_github(
    skills: List[str],
    location: str = "",
    token: str = "",
    max_results: int = 20
) -> List[Dict]:
    """
    Search GitHub for candidates matching skills and location.
    Uses the GitHub Search API (free, rate limited to 10 req/min without token,
    30/min with token).
    """
    results = []

    # Build multiple targeted queries
    queries = []

    # Primary: language + location
    if skills:
        primary_skill = skills[0].lower()
        lang_map = {
            "python": "language:python",
            "javascript": "language:javascript",
            "typescript": "language:typescript",
            "java": "language:java",
            "go": "language:go",
            "rust": "language:rust",
            "ruby": "language:ruby",
            "c++": "language:c++",
            "swift": "language:swift",
            "kotlin": "language:kotlin",
        }
        lang_filter = lang_map.get(primary_skill, "")

        # Query 1: Location + language
        if location and lang_filter:
            queries.append(f"location:{location} {lang_filter} followers:>10")
        elif location:
            queries.append(f"location:{location} {' '.join(skills[:2])} in:bio followers:>5")
        elif lang_filter:
            queries.append(f"{lang_filter} followers:>50")

        # Query 2: Skills in bio
        skill_query = " ".join(f'"{s}"' for s in skills[:3])
        if location:
            queries.append(f"{skill_query} in:bio location:{location}")
        else:
            queries.append(f"{skill_query} in:bio followers:>20")

    seen_users = set()
    for query in queries[:2]:  # Max 2 queries to conserve rate limit
        if len(results) >= max_results:
            break

        users = _search_users(query, token, max_results=15)
        for user in users:
            login = user.get("login", "")
            if login in seen_users:
                continue
            seen_users.add(login)

            # Fetch detailed profile (with rate limit protection)
            detail = _get_user_detail(login, token)
            time.sleep(0.3)  # Be respectful of rate limits

            parsed = _parse_github_user(user, detail)

            # Enrich with language/skill tags
            if detail:
                repos = _get_user_repos(login, token)
                parsed["raw_data"]["top_repos"] = repos
                parsed["skills"] = [s for s in skills if s.lower() in
                                    (detail.get("bio", "") or "").lower()]
                if not parsed["skills"] and skills:
                    parsed["skills"] = skills[:3]  # Infer from search

            results.append(parsed)
            if len(results) >= max_results:
                break

        time.sleep(1)  # Rate limit buffer between queries

    return results
