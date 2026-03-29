"""
core/sources/google_xray.py
Google Custom Search API based X-Ray sourcing.
Finds candidate profiles via Google search — legal and compliant.
"""
import requests
import streamlit as st
from typing import List, Dict, Optional
import re
import time


def _google_search(query: str, api_key: str, cse_id: str, num: int = 10, start: int = 1) -> List[Dict]:
    """Execute a Google Custom Search query."""
    if not api_key or not cse_id:
        return []
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": cse_id,
            "q": query,
            "num": min(num, 10),
            "start": start,
        }
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("items", [])
        elif resp.status_code == 429:
            st.warning("Google search quota reached for today. Try again tomorrow or add a SerpAPI key.")
            return []
        return []
    except Exception:
        return []


def _parse_linkedin_result(item: Dict) -> Optional[Dict]:
    """Parse a Google result into a candidate record for LinkedIn profiles."""
    link = item.get("link", "")
    title = item.get("title", "")
    snippet = item.get("snippet", "")

    if "linkedin.com/in/" not in link:
        return None

    # Extract name and title from the Google title (format: "Name - Title | LinkedIn")
    name, current_title = "", ""
    if " - " in title:
        parts = title.split(" - ", 1)
        name = parts[0].strip()
        current_title = parts[1].replace("| LinkedIn", "").replace("- LinkedIn", "").strip()
    elif "| LinkedIn" in title:
        name = title.replace("| LinkedIn", "").strip()

    # Extract location from snippet
    location = ""
    loc_patterns = [r"\b([A-Z][a-z]+(?:,\s*[A-Z][a-z]+)*)\s*·", r"Location:\s*([^\n·]+)"]
    for pattern in loc_patterns:
        match = re.search(pattern, snippet)
        if match:
            location = match.group(1).strip()
            break

    # Extract skills from snippet keywords
    skills = []
    tech_keywords = ["Python", "Java", "React", "Node", "SQL", "AWS", "Azure", "ML", "AI",
                     "Kubernetes", "Docker", "Salesforce", "SAP", "Product", "Agile", "Scrum",
                     "Marketing", "Finance", "Strategy", "Management", "Leadership", "Data"]
    for kw in tech_keywords:
        if kw.lower() in snippet.lower() or kw.lower() in title.lower():
            skills.append(kw)

    return {
        "full_name": name,
        "current_title": current_title,
        "location": location,
        "source": "LinkedIn (X-Ray)",
        "source_icon": "🔵",
        "profile_url": link,
        "summary": snippet,
        "skills": skills[:8],
        "match_score": 0,
        "raw_data": {"title": title, "snippet": snippet, "link": link},
    }


def xray_linkedin(
    boolean_string: str,
    api_key: str,
    cse_id: str,
    location: str = "",
    max_results: int = 20
) -> List[Dict]:
    """
    X-Ray search LinkedIn profiles via Google.
    Uses: site:linkedin.com/in/ <boolean_string>
    """
    location_part = f'"{location}"' if location else ""
    query = f'site:linkedin.com/in/ {location_part} {boolean_string}'.strip()

    results = []
    for start in [1, 11]:  # Two pages of Google results
        if len(results) >= max_results:
            break
        items = _google_search(query, api_key, cse_id, num=10, start=start)
        for item in items:
            parsed = _parse_linkedin_result(item)
            if parsed:
                results.append(parsed)
        if len(items) < 10:
            break
        time.sleep(0.5)

    return results[:max_results]


def xray_job_board(
    board_domain: str,
    boolean_string: str,
    api_key: str,
    cse_id: str,
    board_name: str = "",
    max_results: int = 10
) -> List[Dict]:
    """
    X-Ray search any job board for candidate CVs/profiles.
    E.g. site:naukri.com, site:reed.co.uk, site:infojobs.net
    """
    query = f'site:{board_domain} {boolean_string} resume OR cv OR profile'

    items = _google_search(query, api_key, cse_id, num=max_results)
    results = []
    for item in items:
        link = item.get("link", "")
        title = item.get("title", "")
        snippet = item.get("snippet", "")

        results.append({
            "full_name": title.split("-")[0].strip() if "-" in title else title,
            "current_title": title.split("-")[1].strip() if "-" in title and len(title.split("-")) > 1 else "",
            "location": "",
            "source": board_name or board_domain,
            "source_icon": "📋",
            "profile_url": link,
            "summary": snippet,
            "skills": [],
            "match_score": 0,
            "raw_data": {"title": title, "snippet": snippet},
        })

    return results


def xray_cv_sites(
    boolean_string: str,
    api_key: str,
    cse_id: str,
    max_results: int = 10
) -> List[Dict]:
    """Search for CVs/resumes across the open web."""
    query = f'({boolean_string}) filetype:pdf OR filetype:doc (resume OR cv OR "curriculum vitae")'
    items = _google_search(query, api_key, cse_id, num=max_results)
    results = []
    for item in items:
        link = item.get("link", "")
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        results.append({
            "full_name": title.replace("Resume", "").replace("CV", "").strip(),
            "current_title": "",
            "location": "",
            "source": "Web CV",
            "source_icon": "📄",
            "profile_url": link,
            "summary": snippet,
            "skills": [],
            "match_score": 0,
            "raw_data": {"title": title, "snippet": snippet},
        })
    return results


# Regional job board X-Ray map
REGIONAL_BOARDS = {
    "India": [
        {"domain": "naukri.com", "name": "Naukri"},
        {"domain": "shine.com", "name": "Shine"},
        {"domain": "timesjobs.com", "name": "TimesJobs"},
    ],
    "Spain": [
        {"domain": "infojobs.net", "name": "InfoJobs"},
        {"domain": "tecnoempleo.com", "name": "Tecnoempleo"},
    ],
    "UK": [
        {"domain": "reed.co.uk", "name": "Reed"},
        {"domain": "totaljobs.com", "name": "Totaljobs"},
        {"domain": "cv-library.co.uk", "name": "CV-Library"},
    ],
    "USA": [
        {"domain": "dice.com", "name": "Dice"},
        {"domain": "ziprecruiter.com", "name": "ZipRecruiter"},
    ],
    "Middle East": [
        {"domain": "bayt.com", "name": "Bayt"},
        {"domain": "naukrigulf.com", "name": "NaukriGulf"},
    ],
    "Germany": [
        {"domain": "stepstone.de", "name": "StepStone"},
        {"domain": "xing.com", "name": "Xing"},
    ],
    "France": [
        {"domain": "apec.fr", "name": "APEC"},
        {"domain": "cadremploi.fr", "name": "Cadremploi"},
    ],
    "Global": [
        {"domain": "indeed.com", "name": "Indeed"},
        {"domain": "monster.com", "name": "Monster"},
    ],
}


def get_boards_for_regions(regions: List[str]) -> List[Dict]:
    """Get the list of job board configs for selected regions."""
    boards = []
    seen = set()
    for region in regions:
        for board in REGIONAL_BOARDS.get(region, []):
            if board["domain"] not in seen:
                boards.append(board)
                seen.add(board["domain"])
    return boards
