"""
boolean_builder.py — converts filter config into boolean search strings
for Google X-ray, LinkedIn, Naukri, and Indeed.

All functions are pure (no side effects) — safe to call from UI on every keystroke.
"""

from typing import Optional


# ---------------------------------------------------------------------------
# Core builder
# ---------------------------------------------------------------------------

def build_boolean(
    titles:      list[str],
    must_skills: list[str],
    nice_skills: list[str],
    location:    str,
    exclude:     list[str],
    seniority:   str = "",
    experience:  str = "",
    mode:        str = "balanced",   # "balanced" | "broad" | "narrow"
) -> str:
    """
    Build a Google X-ray boolean search string.

    mode="balanced"  → good mix of precision and reach (default)
    mode="broad"     → maximum candidate discovery
    mode="narrow"    → high precision, fewer but stronger matches
    """

    parts = []

    # ---- Titles -----------------------------------------------------------
    if titles:
        if mode == "narrow":
            # Only use primary titles (first 2)
            t_list = titles[:2]
        elif mode == "broad":
            # Use all title variants
            t_list = titles
        else:
            # Balanced: first 3–4
            t_list = titles[:4]

        quoted = [f'"{t.strip()}"' for t in t_list if t.strip()]
        if quoted:
            parts.append(f"({' OR '.join(quoted)})")

    # ---- Must-have skills -------------------------------------------------
    if must_skills:
        if mode == "broad":
            # Just first 2 must-have skills
            skill_list = must_skills[:2]
        elif mode == "narrow":
            # All must-have skills
            skill_list = must_skills
        else:
            # Balanced: first 3
            skill_list = must_skills[:3]

        quoted = [f'"{s.strip()}"' for s in skill_list if s.strip()]
        if quoted:
            parts.append(" AND ".join(quoted))

    # ---- Nice-to-have (narrow only adds some, broad skips entirely) ------
    if nice_skills and mode == "narrow":
        quoted = [f'"{s.strip()}"' for s in nice_skills[:2] if s.strip()]
        if quoted:
            parts.append(f"({' OR '.join(quoted)})")

    # ---- Location ---------------------------------------------------------
    if location:
        locs = [l.strip() for l in location.split(",") if l.strip()]
        if locs:
            if len(locs) == 1:
                parts.append(f'"{locs[0]}"')
            else:
                quoted = [f'"{l}"' for l in locs[:4]]
                parts.append(f"({' OR '.join(quoted)})")

    # ---- Exclusions -------------------------------------------------------
    if exclude:
        excl = [f'-"{e.strip()}"' for e in exclude if e.strip()]
        if excl:
            parts.append(" ".join(excl))

    return " ".join(parts)


def build_linkedin_xray(
    titles:      list[str],
    must_skills: list[str],
    location:    str,
    exclude:     list[str],
    mode:        str = "balanced",
) -> str:
    """Prefix boolean with site:linkedin.com/in for Google X-ray."""
    core = build_boolean(
        titles=titles,
        must_skills=must_skills,
        nice_skills=[],
        location=location,
        exclude=exclude,
        mode=mode,
    )
    return f"site:linkedin.com/in {core}".strip()


def build_github_xray(
    must_skills: list[str],
    location:    str,
) -> str:
    """Google X-ray for GitHub profiles."""
    parts = ["site:github.com"]
    if must_skills:
        quoted = [f'"{s.strip()}"' for s in must_skills[:3] if s.strip()]
        parts.append(" OR ".join(quoted))
    if location:
        locs = [l.strip() for l in location.split(",") if l.strip()]
        if locs:
            quoted = [f'"{l}"' for l in locs[:2]]
            parts.append(f"({' OR '.join(quoted)})")
    return " ".join(parts)


def build_naukri_search(
    titles:      list[str],
    must_skills: list[str],
    experience:  str,
    location:    str,
) -> dict:
    """
    Returns a dict of Naukri search parameters (for use in the Playwright scraper).
    """
    return {
        "keywords": " ".join(titles[:2]) if titles else "",
        "skills":   ", ".join(must_skills[:5]),
        "location": location.split(",")[0].strip() if location else "",
        "experience": _parse_exp_for_naukri(experience),
    }


def _parse_exp_for_naukri(exp_range: str) -> dict:
    """Parse '5–10 years' or '8+ years' into {min, max} for Naukri filters."""
    import re
    if not exp_range:
        return {"min": 0, "max": 30}
    # Match "5–10 years", "5-10 years", "8+ years", "10 years"
    m = re.search(r"(\d+)\s*[–\-]\s*(\d+)", exp_range)
    if m:
        return {"min": int(m.group(1)), "max": int(m.group(2))}
    m = re.search(r"(\d+)\+", exp_range)
    if m:
        return {"min": int(m.group(1)), "max": 30}
    m = re.search(r"(\d+)", exp_range)
    if m:
        return {"min": max(0, int(m.group(1)) - 2), "max": int(m.group(1)) + 2}
    return {"min": 0, "max": 30}


# ---------------------------------------------------------------------------
# All-in-one: generate all 3 modes from a filter config dict
# ---------------------------------------------------------------------------

def generate_all_strings(filter_config: dict) -> dict:
    """
    Given a filter_config dict (as stored in the DB / session state),
    generate all boolean string variants.

    Returns:
        {
          "linkedin_balanced": str,
          "linkedin_broad":    str,
          "linkedin_narrow":   str,
          "github":            str,
          "naukri_params":     dict,
        }
    """
    titles      = filter_config.get("titles", [])
    must_skills = filter_config.get("must_skills", [])
    nice_skills = filter_config.get("nice_skills", [])
    location    = filter_config.get("location", "")
    exclude     = filter_config.get("exclude", [])
    experience  = filter_config.get("exp_range", "")

    return {
        "linkedin_balanced": build_linkedin_xray(titles, must_skills, location, exclude, "balanced"),
        "linkedin_broad":    build_linkedin_xray(titles, must_skills, location, exclude, "broad"),
        "linkedin_narrow":   build_linkedin_xray(titles, must_skills, location, exclude, "narrow"),
        "github":            build_github_xray(must_skills, location),
        "naukri_params":     build_naukri_search(titles, must_skills, experience, location),
    }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_filters(filter_config: dict) -> list[str]:
    """
    Returns a list of missing required fields.
    Empty list = all good, search can proceed.
    """
    missing = []
    if not filter_config.get("titles"):
        missing.append("Job titles are required")
    if not filter_config.get("exp_range"):
        missing.append("Experience range is required")
    if not filter_config.get("location"):
        missing.append("Location is required")
    return missing
