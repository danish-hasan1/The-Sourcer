"""
jd_analysis.py — runs the 3-prompt chain against a job description.

Each prompt is your exact prompt text, with an appended instruction
to return structured JSON so the output can be parsed into filter fields.

Usage:
    from jd_analysis import run_chain

    result = run_chain(jd_text)
    # result = {
    #   "p1": { ... role analysis dict ... },
    #   "p2": { ... skills matrix dict ... },
    #   "p3": { ... sourcing params dict ... },
    #   "filter_config": { ... ready to populate UI ... },
    #   "error": None  (or error message string)
    # }
"""

import json
import re
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL, GROQ_TEMP, GROQ_MAX_TOKENS

# ---------------------------------------------------------------------------
# Groq client
# ---------------------------------------------------------------------------

def _get_client() -> Groq:
    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY is not set. "
            "Run: export GROQ_API_KEY='gsk_...' before starting the app."
        )
    return Groq(api_key=GROQ_API_KEY)


# ---------------------------------------------------------------------------
# Your 3 prompts (system role) — exact text preserved
# ---------------------------------------------------------------------------

PROMPT_1_SYSTEM = """You are acting as the original hiring decision-maker who authored this job description, combined with the perspective of a senior talent evaluator who understands how roles are actually assessed in real hiring situations.

Your goal is to understand the job description EXACTLY as it was intended, not just what is explicitly written.

Important rules:
- Do NOT summarize the JD
- Do NOT rely on keyword matching
- Do NOT assume all listed skills are equal
- Infer intent, priorities, and expectations where required
- Assume the JD may be incomplete, imperfect, or loosely written

Analyze the Job Description using the following structure:

1. Role Objective & Business Intent
- What real-world problem is this role meant to solve?
- Why does this role exist right now?

2. Seniority, Scope & Ownership
- Expected seniority level (entry / mid / senior / lead / head / principal)
- Degree of ownership (task execution vs end-to-end responsibility)
- Decision-making authority and independence

3. Primary Competencies (Critical / Must-Have)
- Capabilities without which the candidate would fail in this role
- Explain WHY each competency is essential

4. Secondary Competencies (Value-Add / Nice-to-Have)
- Capabilities that strengthen the profile but are not mandatory

5. Implicit & Unstated Expectations
- Skills, behaviors, or experience assumed but not explicitly written
- Example: terms like "own", "drive", "lead" imply accountability, prioritization, and influence

6. Evaluation Biases & Hiring Signals
- What the hiring manager is likely to prioritize during CV screening
- What will quickly downgrade or disqualify a candidate

7. Ideal Candidate Mental Model
- Describe the ideal candidate as if briefing a recruiter or interview panel

IMPORTANT: Return your response as valid JSON with this exact structure:
{
  "role_objective": "string",
  "seniority_level": "entry|mid|senior|lead|head|principal",
  "ownership_level": "execution|mixed|end-to-end",
  "primary_competencies": [{"name": "string", "why_essential": "string"}],
  "secondary_competencies": ["string"],
  "implicit_expectations": ["string"],
  "disqualifiers": ["string"],
  "ideal_candidate_brief": "string"
}"""

PROMPT_2_SYSTEM = """Using your understanding of the job description and hiring intent, convert the role requirements into a structured, weighted evaluation framework.

Rules:
- Total score must equal exactly 100 points
- Weight skills based on actual hiring importance, not frequency of mention
- Core role-defining competencies must carry significantly higher weight
- Adjacent or transferable skills must NOT dilute primary requirements
- Depth, ownership, and impact matter more than surface exposure

IMPORTANT: Return your response as valid JSON with this exact structure:
{
  "skills_matrix": [
    {
      "skill": "string",
      "category": "core|secondary|implicit",
      "weight": number,
      "strong_evidence": "string",
      "weak_evidence": "string"
    }
  ],
  "non_negotiables": ["string"],
  "seniority_sensitivity": "string",
  "total_weight_check": 100
}

Ensure all weights sum to exactly 100."""

PROMPT_3_SYSTEM = """You are acting as a senior sourcing recruiter and talent intelligence specialist.

Your task is to convert a job description, role understanding, and competency requirements into structured search parameters and Boolean search strings suitable for candidate sourcing across LinkedIn, Naukri, Indeed, GitHub, and Google X-ray search.

Important rules:
- Do NOT restrict to any specific domain or role type
- Interpret the hiring intent, not just keywords
- Include variations, synonyms, seniority equivalents, and adjacent titles where relevant
- Avoid overly narrow searches unless the role explicitly demands it
- Assume the goal is to maximize relevant candidate discovery while maintaining precision

IMPORTANT: Return your response as valid JSON with this exact structure:
{
  "primary_titles": ["string"],
  "title_variants": ["string"],
  "adjacent_titles": ["string"],
  "primary_location": "string",
  "location_alternatives": ["string"],
  "must_have_skills": ["string"],
  "supporting_skills": ["string"],
  "transferable_skills": ["string"],
  "target_industries": ["string"],
  "target_company_types": ["string"],
  "exclude_terms": ["string"],
  "experience_range": {"min": number, "max": number},
  "seniority_filter": "string",
  "boolean_primary": "string",
  "boolean_broad": "string",
  "boolean_narrow": "string"
}"""


# ---------------------------------------------------------------------------
# Core LLM call
# ---------------------------------------------------------------------------

def _call_groq(client: Groq, system: str, user_message: str) -> str:
    """Call Groq and return the raw response text."""
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=GROQ_TEMP,
        max_tokens=GROQ_MAX_TOKENS,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user_message},
        ]
    )
    return response.choices[0].message.content.strip()


def _parse_json(raw: str) -> dict:
    """
    Robustly extract and parse JSON from a model response.
    Handles cases where the model wraps JSON in markdown code fences.
    """
    # Strip markdown fences if present
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
    cleaned = cleaned.strip()

    # Find the outermost JSON object
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)

    return json.loads(cleaned)


# ---------------------------------------------------------------------------
# Filter config builder — converts P3 output into a clean filter dict
# ---------------------------------------------------------------------------

def _build_filter_config(p1: dict, p2: dict, p3: dict) -> dict:
    """
    Merges outputs from all 3 prompts into a single filter config
    that directly maps to the Streamlit UI fields.
    """
    all_titles = (
        p3.get("primary_titles", []) +
        p3.get("title_variants", []) +
        p3.get("adjacent_titles", [])
    )

    exp = p3.get("experience_range", {})
    exp_range = ""
    if exp.get("min") is not None and exp.get("max") is not None:
        exp_range = f"{exp['min']}–{exp['max']} years"
    elif exp.get("min") is not None:
        exp_range = f"{exp['min']}+ years"

    locations = [p3.get("primary_location", "")]
    locations += p3.get("location_alternatives", [])
    locations = [l for l in locations if l]

    return {
        "titles":           all_titles[:6],           # top 6 title variants
        "must_skills":      p3.get("must_have_skills", []),
        "nice_skills":      p3.get("supporting_skills", []) + p3.get("transferable_skills", []),
        "exp_range":        exp_range,
        "seniority":        p3.get("seniority_filter", p1.get("seniority_level", "")),
        "location":         ", ".join(locations[:4]),
        "industry":         ", ".join(p3.get("target_industries", [])[:4]),
        "company_types":    p3.get("target_company_types", []),
        "exclude":          p3.get("exclude_terms", []),
        "non_negotiables":  p2.get("non_negotiables", []),
        "boolean_primary":  p3.get("boolean_primary", ""),
        "boolean_broad":    p3.get("boolean_broad", ""),
        "boolean_narrow":   p3.get("boolean_narrow", ""),
        "ideal_candidate":  p1.get("ideal_candidate_brief", ""),
        "disqualifiers":    p1.get("disqualifiers", []),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_chain(jd_text: str,
              on_step: callable = None) -> dict:
    """
    Run the full 3-prompt analysis chain against a job description.

    Args:
        jd_text:   The full job description text.
        on_step:   Optional callback(step: int, label: str) called after
                   each prompt completes — use for Streamlit progress updates.

    Returns:
        {
          "p1": dict,           # Prompt 1 structured output
          "p2": dict,           # Prompt 2 structured output
          "p3": dict,           # Prompt 3 structured output
          "p1_raw": str,        # Raw text (for saving to DB)
          "p2_raw": str,
          "p3_raw": str,
          "filter_config": dict, # Ready for UI population
          "error": None | str
        }
    """
    result = {
        "p1": {}, "p2": {}, "p3": {},
        "p1_raw": "", "p2_raw": "", "p3_raw": "",
        "filter_config": {},
        "error": None,
    }

    try:
        client = _get_client()
    except ValueError as e:
        result["error"] = str(e)
        return result

    # ---- Prompt 1: JD dissection ----------------------------------------
    try:
        p1_raw = _call_groq(client, PROMPT_1_SYSTEM,
                            f"Analyze this job description:\n\n{jd_text}")
        p1 = _parse_json(p1_raw)
        result["p1"] = p1
        result["p1_raw"] = p1_raw
        if on_step:
            on_step(1, "JD dissection complete")
    except Exception as e:
        result["error"] = f"Prompt 1 failed: {e}"
        return result

    # ---- Prompt 2: Skills matrix ----------------------------------------
    try:
        p2_input = (
            f"Job description:\n{jd_text}\n\n"
            f"Role analysis from previous step:\n{json.dumps(p1, indent=2)}"
        )
        p2_raw = _call_groq(client, PROMPT_2_SYSTEM, p2_input)
        p2 = _parse_json(p2_raw)
        result["p2"] = p2
        result["p2_raw"] = p2_raw
        if on_step:
            on_step(2, "Skills matrix complete")
    except Exception as e:
        result["error"] = f"Prompt 2 failed: {e}"
        return result

    # ---- Prompt 3: Sourcing params + boolean ----------------------------
    try:
        p3_input = (
            f"Job description:\n{jd_text}\n\n"
            f"Role analysis:\n{json.dumps(p1, indent=2)}\n\n"
            f"Skills matrix:\n{json.dumps(p2, indent=2)}"
        )
        p3_raw = _call_groq(client, PROMPT_3_SYSTEM, p3_input)
        p3 = _parse_json(p3_raw)
        result["p3"] = p3
        result["p3_raw"] = p3_raw
        if on_step:
            on_step(3, "Sourcing parameters complete")
    except Exception as e:
        result["error"] = f"Prompt 3 failed: {e}"
        return result

    # ---- Build unified filter config ------------------------------------
    result["filter_config"] = _build_filter_config(p1, p2, p3)

    return result


def validate_jd(jd_text: str) -> list[str]:
    """
    Quick validation before running the chain.
    Returns a list of warning strings (empty = all good).
    """
    warnings = []
    if not jd_text or not jd_text.strip():
        warnings.append("Job description is empty.")
        return warnings
    if len(jd_text.strip()) < 100:
        warnings.append("JD is very short — paste the full description for accurate analysis.")
    if len(jd_text.strip()) < 300:
        warnings.append("JD seems incomplete. The more detail you provide, the better the filter quality.")
    return warnings
