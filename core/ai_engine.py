"""
core/ai_engine.py
The AI intelligence layer for The Sourcer.
All 3 prompts run silently in the background.
"""
import anthropic
import json
import streamlit as st
from typing import Dict, Optional


def _get_client(api_key: str) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=api_key)


def _call_claude(api_key: str, system_prompt: str, user_content: str, max_tokens: int = 4096) -> Optional[str]:
    """Core Claude API call with error handling."""
    try:
        client = _get_client(api_key)
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}]
        )
        return message.content[0].text
    except anthropic.AuthenticationError:
        st.error("❌ Invalid Anthropic API key. Please update it in Settings.")
        return None
    except anthropic.RateLimitError:
        st.error("⚠️ API rate limit reached. Please wait a moment and try again.")
        return None
    except Exception as e:
        st.error(f"AI engine error: {str(e)}")
        return None


# ─────────────────────────────────────────────────────────────────
# PROMPT 1 — JD UNDERSTANDING & INTENT EXTRACTION
# ─────────────────────────────────────────────────────────────────

_PROMPT_1_SYSTEM = """You are acting as the original hiring decision-maker who authored this job description, combined with the perspective of a senior talent evaluator who understands how roles are actually assessed in real hiring situations.

Your goal is to understand the job description EXACTLY as it was intended, not just what is explicitly written.

Important rules:
- Do NOT summarize the JD
- Do NOT rely on keyword matching
- Do NOT assume all listed skills are equal
- Infer intent, priorities, and expectations where required
- Assume the JD may be incomplete, imperfect, or loosely written

Analyze the Job Description and respond ONLY with a valid JSON object using this exact structure:
{
  "role_objective": {
    "problem_solved": "string",
    "why_role_exists_now": "string"
  },
  "seniority": {
    "level": "entry|mid|senior|lead|head|principal",
    "ownership_degree": "string",
    "decision_making": "string"
  },
  "primary_competencies": [
    {"name": "string", "why_essential": "string"}
  ],
  "secondary_competencies": [
    {"name": "string", "value": "string"}
  ],
  "implicit_expectations": ["string"],
  "evaluation_signals": {
    "prioritized": ["string"],
    "disqualifiers": ["string"]
  },
  "ideal_candidate_brief": "string",
  "inferred_industry": "string",
  "inferred_company_type": "string",
  "suggested_job_title": "string"
}

Return ONLY the JSON. No markdown, no explanation, no preamble."""


def analyze_jd(api_key: str, jd_text: str) -> Optional[Dict]:
    """Run Prompt 1: Deep JD analysis and intent extraction."""
    raw = _call_claude(api_key, _PROMPT_1_SYSTEM, f"Job Description:\n\n{jd_text}")
    if not raw:
        return None
    try:
        # Strip markdown code fences if present
        clean = raw.strip().strip("```json").strip("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        st.warning("AI analysis returned unexpected format. Using partial data.")
        return {"raw_analysis": raw}


# ─────────────────────────────────────────────────────────────────
# PROMPT 2 — WEIGHTED SKILL & COMPETENCY SCORING MATRIX
# ─────────────────────────────────────────────────────────────────

_PROMPT_2_SYSTEM = """You are a senior talent intelligence specialist building a structured, weighted evaluation framework from a job description analysis.

Rules:
- Total score must equal exactly 100 points
- Weight skills based on actual hiring importance, not frequency of mention
- Core role-defining competencies must carry significantly higher weight
- Adjacent or transferable skills must NOT dilute primary requirements
- Depth, ownership, and impact matter more than surface exposure

Respond ONLY with a valid JSON object using this exact structure:
{
  "skill_matrix": [
    {
      "skill": "string",
      "category": "core|secondary|implicit",
      "weight": number,
      "strong_evidence": "string",
      "weak_evidence": "string"
    }
  ],
  "weighting_rationale": "string",
  "seniority_sensitivity": {
    "junior_expectations": "string",
    "senior_differentiators": "string"
  },
  "non_negotiables": ["string"],
  "scoring_guide": {
    "strong_match": "85-100",
    "good_match": "65-84",
    "potential": "45-64",
    "weak_match": "below 45"
  }
}

Return ONLY the JSON. No markdown, no explanation."""


def build_skill_matrix(api_key: str, jd_analysis: Dict) -> Optional[Dict]:
    """Run Prompt 2: Build weighted competency scoring matrix."""
    context = json.dumps(jd_analysis, indent=2)
    raw = _call_claude(
        api_key,
        _PROMPT_2_SYSTEM,
        f"Based on this JD analysis, build the scoring matrix:\n\n{context}"
    )
    if not raw:
        return None
    try:
        clean = raw.strip().strip("```json").strip("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        return {"raw_matrix": raw}


# ─────────────────────────────────────────────────────────────────
# PROMPT 3 — SEARCH PARAMETER & BOOLEAN BUILDER
# ─────────────────────────────────────────────────────────────────

_PROMPT_3_SYSTEM = """You are a senior sourcing recruiter and talent intelligence specialist. Convert role analysis into structured search parameters and Boolean strings for candidate sourcing across multiple platforms.

Important rules:
- Do NOT restrict to any specific domain or role type
- Interpret the hiring intent, not just keywords
- Include variations, synonyms, seniority equivalents, and adjacent titles
- Avoid overly narrow searches unless the role explicitly demands it
- Maximize relevant candidate discovery while maintaining precision

Respond ONLY with a valid JSON object using this exact structure:
{
  "job_titles": {
    "primary": ["string"],
    "seniority_variants": ["string"],
    "adjacent": ["string"]
  },
  "locations": {
    "primary": "string",
    "nearby": ["string"],
    "remote_ok": boolean,
    "expansion_suggestions": "string"
  },
  "skills": {
    "core": ["string"],
    "supporting": ["string"],
    "transferable": ["string"]
  },
  "companies": {
    "industries": ["string"],
    "company_types": ["string"],
    "include_suggestions": ["string"],
    "exclude_suggestions": ["string"]
  },
  "boolean_strings": {
    "primary": "string",
    "broad": "string",
    "narrow": "string",
    "github": "string",
    "stackoverflow": "string"
  },
  "filters": {
    "seniority": ["string"],
    "functions": ["string"],
    "experience_years_min": number,
    "experience_years_max": number
  },
  "regional_job_boards": {
    "recommended_regions": ["string"],
    "board_suggestions": ["string"]
  }
}

Return ONLY the JSON. No markdown, no explanation."""


def build_search_params(api_key: str, jd_analysis: Dict, skill_matrix: Dict, location_hint: str = "") -> Optional[Dict]:
    """Run Prompt 3: Build LinkedIn RPS-style search parameters and Boolean strings."""
    context = {
        "jd_analysis": jd_analysis,
        "skill_matrix": skill_matrix,
        "location_hint": location_hint
    }
    raw = _call_claude(
        api_key,
        _PROMPT_3_SYSTEM,
        f"Build sourcing parameters from this analysis:\n\n{json.dumps(context, indent=2)}"
    )
    if not raw:
        return None
    try:
        clean = raw.strip().strip("```json").strip("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        return {"raw_params": raw}


# ─────────────────────────────────────────────────────────────────
# PROMPT 4 — CANDIDATE MATCH SCORER (bonus prompt)
# ─────────────────────────────────────────────────────────────────

_PROMPT_4_SYSTEM = """You are a talent intelligence engine. Score a candidate profile against a job requirement skill matrix.

Given the skill matrix weights and a candidate's profile snippet, return a match score from 0-100 and a brief rationale.

Respond ONLY with valid JSON:
{
  "match_score": number,
  "matched_skills": ["string"],
  "missing_skills": ["string"],
  "rationale": "string",
  "recommendation": "strong_match|good_match|potential|weak_match"
}

Return ONLY the JSON."""


def score_candidate(api_key: str, candidate_snippet: str, skill_matrix: Dict) -> Optional[Dict]:
    """Score a candidate profile against the role's skill matrix."""
    context = {
        "candidate_profile": candidate_snippet,
        "skill_matrix": skill_matrix.get("skill_matrix", []),
        "non_negotiables": skill_matrix.get("non_negotiables", [])
    }
    raw = _call_claude(
        api_key,
        _PROMPT_4_SYSTEM,
        json.dumps(context),
        max_tokens=512
    )
    if not raw:
        return None
    try:
        clean = raw.strip().strip("```json").strip("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        return {"match_score": 0, "rationale": "Could not score profile."}


# ─────────────────────────────────────────────────────────────────
# SEARCH REFINEMENT — Collaborative re-think
# ─────────────────────────────────────────────────────────────────

_REFINE_SYSTEM = """You are a senior talent sourcing expert helping a recruiter refine their candidate search.
The recruiter hasn't found the right candidates yet. Based on their feedback, suggest concrete changes to the search filters.

Respond ONLY with valid JSON:
{
  "updated_titles": ["string"],
  "updated_skills": ["string"],
  "updated_boolean": "string",
  "updated_location": "string",
  "updated_seniority": "string",
  "reasoning": "string",
  "additional_sources": ["string"]
}

Return ONLY the JSON."""


def refine_search(api_key: str, current_filters: Dict, user_feedback: str, results_so_far: int) -> Optional[Dict]:
    """Allow the user to collaborate with AI to refine their search."""
    context = {
        "current_filters": current_filters,
        "user_feedback": user_feedback,
        "results_found_so_far": results_so_far
    }
    raw = _call_claude(
        api_key,
        _REFINE_SYSTEM,
        f"Help me refine this search:\n\n{json.dumps(context, indent=2)}"
    )
    if not raw:
        return None
    try:
        clean = raw.strip().strip("```json").strip("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        return None


# ─────────────────────────────────────────────────────────────────
# OUTREACH MESSAGE GENERATOR
# ─────────────────────────────────────────────────────────────────

_OUTREACH_SYSTEM = """You are an expert recruiter crafting personalized outreach messages.
Write a compelling, professional outreach message that:
- Feels personal, not templated
- Mentions something specific about the candidate's background
- Clearly states the opportunity without being pushy
- Has a clear call to action
- Matches the requested tone and format

For LinkedIn: Keep under 300 characters for connection request note, or under 2000 for InMail.
For Email: Include a subject line, greeting, body, and sign-off.

Respond ONLY with valid JSON:
{
  "subject": "string or null",
  "message": "string",
  "character_count": number
}"""


def generate_outreach(api_key: str, candidate: Dict, jd_summary: str, tone: str, fmt: str) -> Optional[Dict]:
    """Generate a personalized outreach message for a candidate."""
    context = {
        "candidate_name": candidate.get("full_name", "the candidate"),
        "candidate_title": candidate.get("current_title", ""),
        "candidate_location": candidate.get("location", ""),
        "candidate_skills": candidate.get("skills", []),
        "candidate_source": candidate.get("source", ""),
        "job_summary": jd_summary,
        "message_tone": tone,
        "message_format": fmt,
    }
    raw = _call_claude(
        api_key,
        _OUTREACH_SYSTEM,
        f"Generate outreach for:\n\n{json.dumps(context, indent=2)}",
        max_tokens=1024
    )
    if not raw:
        return None
    try:
        clean = raw.strip().strip("```json").strip("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        return {"subject": None, "message": raw, "character_count": len(raw)}


# ─────────────────────────────────────────────────────────────────
# FULL PIPELINE — Run all 3 prompts in sequence
# ─────────────────────────────────────────────────────────────────

def run_full_jd_pipeline(api_key: str, jd_text: str, location_hint: str = "") -> Dict:
    """
    Run the complete JD intelligence pipeline:
    1. Analyze JD
    2. Build skill matrix
    3. Generate search parameters
    Returns all three results as a combined dict.
    """
    results = {}

    with st.spinner("🧠 Analyzing job description intent..."):
        jd_analysis = analyze_jd(api_key, jd_text)
        if not jd_analysis:
            return {}
        results["jd_analysis"] = jd_analysis

    with st.spinner("⚖️ Building competency scoring matrix..."):
        skill_matrix = build_skill_matrix(api_key, jd_analysis)
        if not skill_matrix:
            return results
        results["skill_matrix"] = skill_matrix

    with st.spinner("🔍 Generating search parameters and Boolean strings..."):
        search_params = build_search_params(api_key, jd_analysis, skill_matrix, location_hint)
        if not search_params:
            return results
        results["search_params"] = search_params

    return results
