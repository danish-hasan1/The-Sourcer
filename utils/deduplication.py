"""
utils/deduplication.py
Cross-source candidate deduplication logic.
"""
from typing import List, Dict
import re


def _normalize_name(name: str) -> str:
    """Normalize a name for comparison."""
    return re.sub(r"[^a-z]", "", name.lower().strip()) if name else ""


def _normalize_url(url: str) -> str:
    """Strip tracking params and normalize URL."""
    if not url:
        return ""
    url = url.split("?")[0].rstrip("/").lower()
    return url


def deduplicate_candidates(candidates: List[Dict]) -> List[Dict]:
    """
    Remove duplicate candidates across sources.
    Dedup strategy:
    1. Exact profile URL match
    2. Normalized full name + location match (fuzzy)
    """
    seen_urls = set()
    seen_names = set()
    unique = []

    for c in candidates:
        url = _normalize_url(c.get("profile_url", ""))
        name = _normalize_name(c.get("full_name", ""))
        location = _normalize_name(c.get("location", ""))
        name_loc_key = f"{name}_{location[:10]}" if name else ""

        # URL dedup (strongest signal)
        if url and url in seen_urls:
            continue

        # Name + location dedup (for same person across sources)
        if name_loc_key and len(name_loc_key) > 5 and name_loc_key in seen_names:
            continue

        if url:
            seen_urls.add(url)
        if name_loc_key and len(name_loc_key) > 5:
            seen_names.add(name_loc_key)

        unique.append(c)

    return unique
