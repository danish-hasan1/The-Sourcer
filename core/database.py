"""
core/database.py
All Supabase database operations for The Sourcer.
"""
import streamlit as st
from supabase import create_client, Client
from typing import Optional, Dict, Any, List
import json


def get_supabase() -> Client:
    """Get or create a Supabase client using Streamlit secrets."""
    if "supabase_client" not in st.session_state:
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_ANON_KEY", "")
        if not url or not key:
            st.error("⚠️ Supabase credentials missing. Add them to `.streamlit/secrets.toml`")
            st.stop()
        st.session_state.supabase_client = create_client(url, key)
    return st.session_state.supabase_client


# ─────────────────────────────────────────────
# PROFILES
# ─────────────────────────────────────────────

def get_profile(user_id: str) -> Optional[Dict]:
    try:
        sb = get_supabase()
        res = sb.table("profiles").select("*").eq("id", user_id).single().execute()
        return res.data
    except Exception:
        return None


def update_profile(user_id: str, data: Dict) -> bool:
    try:
        sb = get_supabase()
        sb.table("profiles").update(data).eq("id", user_id).execute()
        return True
    except Exception as e:
        st.error(f"Profile update failed: {e}")
        return False


def get_all_profiles_admin() -> List[Dict]:
    """Admin only - get all user profiles."""
    try:
        sb = get_supabase()
        res = sb.table("profiles").select("*").order("created_at", desc=True).execute()
        return res.data or []
    except Exception:
        return []


# ─────────────────────────────────────────────
# API KEYS
# ─────────────────────────────────────────────

def get_api_keys(user_id: str) -> Dict:
    try:
        sb = get_supabase()
        res = sb.table("api_keys").select("*").eq("user_id", user_id).single().execute()
        return res.data or {}
    except Exception:
        return {}


def save_api_keys(user_id: str, keys: Dict) -> bool:
    try:
        sb = get_supabase()
        existing = get_api_keys(user_id)
        keys["user_id"] = user_id
        if existing:
            sb.table("api_keys").update(keys).eq("user_id", user_id).execute()
        else:
            sb.table("api_keys").insert(keys).execute()
        return True
    except Exception as e:
        st.error(f"Failed to save API keys: {e}")
        return False


# ─────────────────────────────────────────────
# JD LIBRARY
# ─────────────────────────────────────────────

def save_jd(user_id: str, title: str, jd_text: str, ai_analysis: Dict = None, skill_matrix: Dict = None) -> Optional[str]:
    try:
        sb = get_supabase()
        res = sb.table("jd_library").insert({
            "user_id": user_id,
            "title": title,
            "jd_text": jd_text,
            "ai_analysis": ai_analysis,
            "skill_matrix": skill_matrix,
        }).execute()
        return res.data[0]["id"] if res.data else None
    except Exception as e:
        st.error(f"Failed to save JD: {e}")
        return None


def get_jd_library(user_id: str) -> List[Dict]:
    try:
        sb = get_supabase()
        res = sb.table("jd_library").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return res.data or []
    except Exception:
        return []


def get_jd(jd_id: str) -> Optional[Dict]:
    try:
        sb = get_supabase()
        res = sb.table("jd_library").select("*").eq("id", jd_id).single().execute()
        return res.data
    except Exception:
        return None


def delete_jd(jd_id: str) -> bool:
    try:
        sb = get_supabase()
        sb.table("jd_library").delete().eq("id", jd_id).execute()
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────
# SEARCHES
# ─────────────────────────────────────────────

def save_search(user_id: str, name: str, jd_id: str, filters: Dict, sources: List, boolean_strings: Dict = None) -> Optional[str]:
    try:
        sb = get_supabase()
        res = sb.table("searches").insert({
            "user_id": user_id,
            "name": name,
            "jd_id": jd_id,
            "filters": filters,
            "sources": sources,
            "boolean_strings": boolean_strings,
            "status": "completed",
        }).execute()
        return res.data[0]["id"] if res.data else None
    except Exception as e:
        st.error(f"Failed to save search: {e}")
        return None


def get_searches(user_id: str) -> List[Dict]:
    try:
        sb = get_supabase()
        res = sb.table("searches").select("*, jd_library(title)").eq("user_id", user_id).order("created_at", desc=True).execute()
        return res.data or []
    except Exception:
        return []


def update_search_count(search_id: str, count: int):
    try:
        sb = get_supabase()
        sb.table("searches").update({"result_count": count}).eq("id", search_id).execute()
    except Exception:
        pass


def delete_search(search_id: str) -> bool:
    try:
        sb = get_supabase()
        sb.table("searches").delete().eq("id", search_id).execute()
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────
# CANDIDATES
# ─────────────────────────────────────────────

def save_candidate(user_id: str, candidate: Dict, search_id: str = None, team_id: str = None) -> Optional[str]:
    try:
        sb = get_supabase()
        payload = {
            "user_id": user_id,
            "search_id": search_id,
            "team_id": team_id,
            "full_name": candidate.get("full_name"),
            "current_title": candidate.get("current_title"),
            "location": candidate.get("location"),
            "source": candidate.get("source", "unknown"),
            "profile_url": candidate.get("profile_url"),
            "email": candidate.get("email"),
            "skills": candidate.get("skills", []),
            "experience_years": candidate.get("experience_years"),
            "summary": candidate.get("summary"),
            "match_score": candidate.get("match_score", 0),
            "stage": "sourced",
            "raw_data": candidate.get("raw_data", {}),
        }
        res = sb.table("candidates").insert(payload).execute()
        return res.data[0]["id"] if res.data else None
    except Exception as e:
        st.error(f"Failed to save candidate: {e}")
        return None


def get_candidates(user_id: str, search_id: str = None, team_id: str = None, include_shared: bool = True) -> List[Dict]:
    try:
        sb = get_supabase()
        query = sb.table("candidates").select("*").eq("user_id", user_id)
        if search_id:
            query = query.eq("search_id", search_id)
        res = query.order("match_score", desc=True).execute()
        return res.data or []
    except Exception:
        return []


def update_candidate_stage(candidate_id: str, stage: str) -> bool:
    try:
        sb = get_supabase()
        sb.table("candidates").update({"stage": stage}).eq("id", candidate_id).execute()
        return True
    except Exception:
        return False


def update_candidate_notes(candidate_id: str, notes: str) -> bool:
    try:
        sb = get_supabase()
        sb.table("candidates").update({"notes": notes}).eq("id", candidate_id).execute()
        return True
    except Exception:
        return False


def delete_candidate(candidate_id: str) -> bool:
    try:
        sb = get_supabase()
        sb.table("candidates").delete().eq("id", candidate_id).execute()
        return True
    except Exception:
        return False


def get_candidate_stats(user_id: str) -> Dict:
    try:
        candidates = get_candidates(user_id)
        stats = {
            "total": len(candidates),
            "sourced": sum(1 for c in candidates if c.get("stage") == "sourced"),
            "reviewed": sum(1 for c in candidates if c.get("stage") == "reviewed"),
            "contacted": sum(1 for c in candidates if c.get("stage") == "contacted"),
            "responded": sum(1 for c in candidates if c.get("stage") == "responded"),
            "interview": sum(1 for c in candidates if c.get("stage") == "interview"),
        }
        return stats
    except Exception:
        return {"total": 0, "sourced": 0, "reviewed": 0, "contacted": 0, "responded": 0, "interview": 0}


# ─────────────────────────────────────────────
# OUTREACH
# ─────────────────────────────────────────────

def save_outreach(user_id: str, candidate_id: str, message: str, fmt: str, tone: str) -> bool:
    try:
        sb = get_supabase()
        sb.table("outreach_log").insert({
            "user_id": user_id,
            "candidate_id": candidate_id,
            "message_text": message,
            "message_format": fmt,
            "tone": tone,
        }).execute()
        return True
    except Exception:
        return False


def get_outreach_log(user_id: str) -> List[Dict]:
    try:
        sb = get_supabase()
        res = sb.table("outreach_log").select("*, candidates(full_name, current_title)").eq("user_id", user_id).order("created_at", desc=True).execute()
        return res.data or []
    except Exception:
        return []


# ─────────────────────────────────────────────
# ONBOARDING
# ─────────────────────────────────────────────

def get_onboarding(user_id: str) -> Dict:
    try:
        sb = get_supabase()
        res = sb.table("onboarding").select("*").eq("user_id", user_id).single().execute()
        return res.data or {}
    except Exception:
        return {}


def complete_onboarding_step(user_id: str, step: str):
    try:
        sb = get_supabase()
        current = get_onboarding(user_id)
        steps = current.get("completed_steps", []) or []
        if step not in steps:
            steps.append(step)
        sb.table("onboarding").update({"completed_steps": steps}).eq("user_id", user_id).execute()
    except Exception:
        pass


def mark_onboarding_complete(user_id: str):
    try:
        sb = get_supabase()
        from datetime import datetime
        sb.table("onboarding").update({
            "completed_at": datetime.utcnow().isoformat()
        }).eq("user_id", user_id).execute()
        update_profile(user_id, {"onboarding_completed": True})
    except Exception:
        pass


# ─────────────────────────────────────────────
# TEAMS
# ─────────────────────────────────────────────

def create_team(name: str, owner_id: str) -> Optional[str]:
    try:
        sb = get_supabase()
        res = sb.table("teams").insert({"name": name, "owner_id": owner_id}).execute()
        team_id = res.data[0]["id"]
        # Add owner as member
        sb.table("team_members").insert({
            "team_id": team_id,
            "user_id": owner_id,
            "role": "owner"
        }).execute()
        update_profile(owner_id, {"team_id": team_id})
        return team_id
    except Exception as e:
        st.error(f"Failed to create team: {e}")
        return None


def get_team(team_id: str) -> Optional[Dict]:
    try:
        sb = get_supabase()
        res = sb.table("teams").select("*, team_members(*, profiles(full_name, email))").eq("id", team_id).single().execute()
        return res.data
    except Exception:
        return None
