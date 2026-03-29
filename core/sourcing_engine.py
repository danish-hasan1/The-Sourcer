"""
core/sourcing_engine.py
Orchestrates all candidate sourcing sources.
Deduplicates and merges results from LinkedIn X-Ray, GitHub, Stack Overflow, and Job Boards.
"""
import streamlit as st
from typing import List, Dict, Optional
from core.sources.google_xray import xray_linkedin, xray_job_board, xray_cv_sites, get_boards_for_regions, REGIONAL_BOARDS
from core.sources.github_source import search_github
from core.sources.stackoverflow_source import search_stackoverflow
from utils.deduplication import deduplicate_candidates
from core.ai_engine import score_candidate


def run_sourcing(
    search_params: Dict,
    filters: Dict,
    selected_sources: List[str],
    google_api_key: str,
    google_cse_id: str,
    github_token: str = "",
    anthropic_key: str = "",
    skill_matrix: Dict = None,
    max_per_source: int = 20,
) -> List[Dict]:
    """
    Main sourcing orchestrator. Runs all selected sources and returns
    a unified, deduplicated, scored candidate list.
    """
    all_candidates = []

    boolean_strings = search_params.get("boolean_strings", {})
    primary_boolean = filters.get("boolean_string") or boolean_strings.get("primary", "")
    broad_boolean = boolean_strings.get("broad", primary_boolean)
    location = filters.get("location", "") or search_params.get("locations", {}).get("primary", "")
    skills_core = filters.get("skills", []) or search_params.get("skills", {}).get("core", [])

    # ── LinkedIn X-Ray ──────────────────────────────────────────
    if "LinkedIn (X-Ray)" in selected_sources and google_api_key and google_cse_id:
        with st.spinner("🔵 Searching LinkedIn profiles via X-Ray..."):
            linkedin_string = filters.get("boolean_string") or boolean_strings.get("narrow", primary_boolean)
            results = xray_linkedin(
                boolean_string=linkedin_string,
                api_key=google_api_key,
                cse_id=google_cse_id,
                location=location,
                max_results=max_per_source,
            )
            for r in results:
                r["source_group"] = "LinkedIn"
            all_candidates.extend(results)
            st.toast(f"✅ LinkedIn: {len(results)} profiles found", icon="🔵")

    # ── GitHub ──────────────────────────────────────────────────
    if "GitHub" in selected_sources:
        with st.spinner("🐙 Searching GitHub developer profiles..."):
            gh_skills = skills_core[:5] if skills_core else []
            results = search_github(
                skills=gh_skills,
                location=location,
                token=github_token,
                max_results=max_per_source,
            )
            for r in results:
                r["source_group"] = "GitHub"
            all_candidates.extend(results)
            st.toast(f"✅ GitHub: {len(results)} profiles found", icon="🐙")

    # ── Stack Overflow ───────────────────────────────────────────
    if "Stack Overflow" in selected_sources:
        with st.spinner("📚 Searching Stack Overflow expert profiles..."):
            results = search_stackoverflow(
                skills=skills_core[:4] if skills_core else [],
                location=location,
                max_results=max_per_source,
            )
            for r in results:
                r["source_group"] = "Stack Overflow"
            all_candidates.extend(results)
            st.toast(f"✅ Stack Overflow: {len(results)} profiles found", icon="📚")

    # ── Regional Job Boards ──────────────────────────────────────
    selected_regions = filters.get("regions", []) or _infer_regions(location)
    if "Job Boards" in selected_sources and google_api_key and google_cse_id:
        boards = get_boards_for_regions(selected_regions)
        if not boards:
            boards = get_boards_for_regions(["Global"])

        for board in boards[:4]:  # Limit to 4 boards to conserve quota
            with st.spinner(f"📋 Searching {board['name']}..."):
                results = xray_job_board(
                    board_domain=board["domain"],
                    boolean_string=broad_boolean,
                    api_key=google_api_key,
                    cse_id=google_cse_id,
                    board_name=board["name"],
                    max_results=8,
                )
                for r in results:
                    r["source_group"] = "Job Boards"
                all_candidates.extend(results)
                if results:
                    st.toast(f"✅ {board['name']}: {len(results)} found", icon="📋")

    # ── Web CVs ──────────────────────────────────────────────────
    if "Web CVs" in selected_sources and google_api_key and google_cse_id:
        with st.spinner("📄 Searching for CVs across the web..."):
            results = xray_cv_sites(
                boolean_string=broad_boolean,
                api_key=google_api_key,
                cse_id=google_cse_id,
                max_results=10,
            )
            for r in results:
                r["source_group"] = "Web CVs"
            all_candidates.extend(results)
            if results:
                st.toast(f"✅ Web CVs: {len(results)} found", icon="📄")

    # ── Deduplication ────────────────────────────────────────────
    with st.spinner("🔄 Deduplicating results..."):
        candidates = deduplicate_candidates(all_candidates)

    # ── AI Scoring ───────────────────────────────────────────────
    if anthropic_key and skill_matrix and candidates:
        with st.spinner(f"🎯 AI scoring {len(candidates)} candidates..."):
            scored = []
            for candidate in candidates:
                snippet = f"""
Name: {candidate.get('full_name', '')}
Title: {candidate.get('current_title', '')}
Location: {candidate.get('location', '')}
Skills: {', '.join(candidate.get('skills', []))}
Summary: {candidate.get('summary', '')[:500]}
"""
                score_result = score_candidate(anthropic_key, snippet, skill_matrix)
                if score_result:
                    candidate["match_score"] = score_result.get("match_score", 0)
                    candidate["ai_rationale"] = score_result.get("rationale", "")
                    candidate["recommendation"] = score_result.get("recommendation", "")
                    candidate["matched_skills"] = score_result.get("matched_skills", [])
                    candidate["missing_skills"] = score_result.get("missing_skills", [])
                scored.append(candidate)
            candidates = scored

    # ── Sort by match score ──────────────────────────────────────
    candidates.sort(key=lambda x: x.get("match_score", 0), reverse=True)

    return candidates


def _infer_regions(location: str) -> List[str]:
    """Infer likely job board regions from location string."""
    location_lower = location.lower()
    region_map = {
        "india": "India", "delhi": "India", "mumbai": "India", "bangalore": "India",
        "spain": "Spain", "madrid": "Spain", "barcelona": "Spain",
        "uk": "UK", "london": "UK", "manchester": "UK", "england": "UK",
        "us": "USA", "usa": "USA", "new york": "USA", "san francisco": "USA",
        "dubai": "Middle East", "uae": "Middle East", "riyadh": "Middle East",
        "germany": "Germany", "berlin": "Germany", "munich": "Germany",
        "france": "France", "paris": "France",
    }
    for key, region in region_map.items():
        if key in location_lower:
            return [region, "Global"]
    return ["Global"]


def get_source_options() -> List[str]:
    """Return all available sourcing channels."""
    return [
        "LinkedIn (X-Ray)",
        "GitHub",
        "Stack Overflow",
        "Job Boards",
        "Web CVs",
    ]


def get_all_regions() -> List[str]:
    return list(REGIONAL_BOARDS.keys())
