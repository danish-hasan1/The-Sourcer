"""
core/sources/stackoverflow_source.py
Stack Overflow / Stack Exchange API sourcing.
Finds developers with proven expertise via their answers and profiles.
"""
import requests
from typing import List, Dict, Optional
import time


STACK_API = "https://api.stackexchange.com/2.3"


def _search_so_users(tags: List[str], location: str = "", max_results: int = 20) -> List[Dict]:
    """Search Stack Overflow users by tags and location."""
    try:
        params = {
            "pagesize": min(max_results, 30),
            "order": "desc",
            "sort": "reputation",
            "site": "stackoverflow",
            "filter": "!*236eb_eL9rai)Z",  # Include more fields
        }
        if location:
            params["location"] = location

        # Search by top answerers for specific tags
        if tags:
            tag = tags[0].lower().replace(" ", "-")
            url = f"{STACK_API}/tags/{tag}/top-answerers/month"
            resp = requests.get(url, params={"site": "stackoverflow", "pagesize": max_results}, timeout=10)
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                return [item.get("user", {}) for item in items if item.get("user")]

        # Fallback: general user search
        url = f"{STACK_API}/users"
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("items", [])
        return []
    except Exception:
        return []


def _get_user_tags(user_id: int, max_tags: int = 8) -> List[str]:
    """Get the tags a user has answered most questions about."""
    try:
        url = f"{STACK_API}/users/{user_id}/tags"
        params = {
            "pagesize": max_tags,
            "order": "desc",
            "sort": "popular",
            "site": "stackoverflow",
        }
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            items = resp.json().get("items", [])
            return [item.get("name", "") for item in items]
        return []
    except Exception:
        return []


def _parse_so_user(user: Dict, infer_skills: List[str] = None) -> Optional[Dict]:
    """Convert a Stack Overflow user into a candidate record."""
    if not user.get("user_id"):
        return None

    display_name = user.get("display_name", "")
    location = user.get("location", "") or ""
    reputation = user.get("reputation", 0)
    profile_url = user.get("link", f"https://stackoverflow.com/users/{user.get('user_id')}")
    about_me = user.get("about_me", "") or ""

    # Clean HTML from about_me
    import re
    about_me = re.sub(r"<[^>]+>", " ", about_me).strip()[:300]

    # Build reputation indicator
    rep_label = ""
    if reputation > 10000:
        rep_label = f"⚡ {reputation:,} rep (Top Expert)"
    elif reputation > 5000:
        rep_label = f"⚡ {reputation:,} rep (Senior)"
    elif reputation > 1000:
        rep_label = f"⚡ {reputation:,} rep"

    summary = about_me or f"Stack Overflow contributor with {reputation:,} reputation points."
    if rep_label and about_me:
        summary = f"{rep_label} · {about_me}"
    elif rep_label:
        summary = rep_label

    return {
        "full_name": display_name,
        "current_title": "Software Developer",  # SO doesn't expose job titles
        "location": location,
        "source": "Stack Overflow",
        "source_icon": "📚",
        "profile_url": profile_url,
        "email": "",
        "summary": summary,
        "skills": infer_skills or [],
        "match_score": 0,
        "raw_data": {
            "user_id": user.get("user_id"),
            "reputation": reputation,
            "badge_counts": user.get("badge_counts", {}),
            "accept_rate": user.get("accept_rate"),
        }
    }


def search_stackoverflow(
    skills: List[str],
    location: str = "",
    max_results: int = 15
) -> List[Dict]:
    """
    Search Stack Overflow for expert candidates.
    Uses the free Stack Exchange API (no auth needed, rate limited to 300 req/day).
    """
    results = []
    seen_ids = set()

    # Search top answerers for each skill tag
    for skill in skills[:3]:  # Top 3 skills to avoid quota exhaustion
        if len(results) >= max_results:
            break

        users = _search_so_users([skill], location, max_results=10)
        for user in users:
            uid = user.get("user_id") or user.get("account_id")
            if not uid or uid in seen_ids:
                continue
            seen_ids.add(uid)

            # Enrich with actual skill tags from their answers
            user_tags = _get_user_tags(uid, max_tags=6)
            time.sleep(0.2)

            relevant_skills = [t for t in user_tags if any(
                s.lower() in t.lower() or t.lower() in s.lower()
                for s in skills
            )]
            all_skills = list(dict.fromkeys(relevant_skills + user_tags[:5]))

            parsed = _parse_so_user(user, infer_skills=all_skills[:8])
            if parsed:
                results.append(parsed)

        time.sleep(0.5)

    return results[:max_results]
